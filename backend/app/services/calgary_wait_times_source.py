"""
Live Alberta (Calgary zone) emergency wait times from Alberta Health Services.

Source: GET https://www.albertahealthservices.ca/waittimes/en.json?_={timestamp}
        (fetched by urgenthelp.js on the AHS wait times page)

Response format:
{
  "Calgary": {
    "Emergency": [{ "Name": ..., "WaitTime": "X hr Y min", "TimesUnavailable": "False", ... }],
    "Urgent":    [{ ... }]
  },
  "Edmonton": { ... },
  ...
}

SplitFacility hospitals (e.g. South Health Campus) encode multiple departments
with "[;]" as a delimiter in every field — they are expanded into separate rows.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

AHS_WAIT_TIMES_URL = "https://www.albertahealthservices.ca/Webapps/WaitTimes/api/waittimes/en"
REQUEST_TIMEOUT_S = 18.0
CALGARY_TZ = ZoneInfo("America/Edmonton")


def _parse_wait_to_minutes(raw: str) -> int | None:
    """
    Parse "X hr Y min" → total minutes.
    Returns None for "Wait times unavailable" or empty strings.
    """
    s = str(raw or "").strip()
    if not s or "unavailable" in s.lower():
        return None
    m = re.match(r"(\d+)\s*hr\s+(\d+)\s*min", s, re.I)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return None


def _minutes_to_wait_text(total_minutes: int) -> str:
    h, m = divmod(total_minutes, 60)
    return f"{h}h {m:02d}m"


def _extract_city_from_address(address: str) -> str:
    """
    Extract city name from AHS address string.
    Format: "Street Address City Province PostalCode"
    e.g. "1403 29 Street NW Calgary Alberta T2N 2T9" → "Calgary"
    """
    parts = str(address or "").split()
    # Address ends with PostalCode Province City... walk backwards
    # Skip last 3 tokens (province abbreviation + postal parts)
    # AHS format: "... City Province T0X 0X0"
    if len(parts) >= 4:
        # Province is always "Alberta", city is before it
        try:
            alberta_idx = next(i for i, p in enumerate(parts) if p.lower() == "alberta")
            if alberta_idx > 0:
                return parts[alberta_idx - 1]
        except StopIteration:
            pass
    return "Calgary"


def _build_rows_from_entry(entry: dict[str, Any], is_upcc: bool) -> list[dict[str, Any]]:
    """
    Handle both regular and split-facility entries.
    Split facilities use "[;]" delimiter in every field.
    """
    name_raw = str(entry.get("Name") or "")
    wait_raw = str(entry.get("WaitTime") or "")
    addr_raw = str(entry.get("Address") or "")
    unavailable_raw = str(entry.get("TimesUnavailable") or "False")

    rows: list[dict[str, Any]] = []

    if "[;]" in name_raw:
        # Split facility — expand into one row per sub-department
        names = name_raw.split("[;]")
        waits = wait_raw.split("[;]")
        addrs = addr_raw.split("[;]")
        unavailables = unavailable_raw.split("[;]")

        for i, name in enumerate(names):
            name = name.strip()
            if not name:
                continue
            wait_text_raw = waits[i].strip() if i < len(waits) else ""
            addr = addrs[i].strip() if i < len(addrs) else addr_raw
            unavail = (unavailables[i].strip() if i < len(unavailables) else "False").lower() == "true"

            mins = None if unavail else _parse_wait_to_minutes(wait_text_raw)
            wait_text = _minutes_to_wait_text(mins) if mins is not None else "Unavailable"

            row: dict[str, Any] = {
                "key": f"ahs_{re.sub(r'[^a-z0-9]', '_', name.lower())}",
                "name": name,
                "city": _extract_city_from_address(addr),
                "wait_text": wait_text,
            }
            if is_upcc and addr:
                row["address"] = addr
            rows.append(row)
    else:
        # Regular single-facility entry
        unavail = unavailable_raw.lower() == "true"
        mins = None if unavail else _parse_wait_to_minutes(wait_raw)
        wait_text = _minutes_to_wait_text(mins) if mins is not None else "Unavailable"

        row = {
            "key": f"ahs_{re.sub(r'[^a-z0-9]', '_', name_raw.strip().lower())}",
            "name": name_raw.strip(),
            "city": _extract_city_from_address(addr_raw),
            "wait_text": wait_text,
        }
        if is_upcc and addr_raw:
            row["address"] = addr_raw
        rows.append(row)

    return rows


def fetch_calgary_wait_times_payload() -> dict[str, Any]:
    """
    Fetches Calgary-zone wait times from the AHS JSON endpoint.
    Returns the same shape as fetch_er_wait_times_payload().
    """
    cache_bust = int(time.time() * 1000)
    url = f"{AHS_WAIT_TIMES_URL}?_={cache_bust}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, */*;q=0.8",
        "Referer": "https://www.albertahealthservices.ca/waittimes/Page14230.aspx",
        "Cache-Control": "no-cache, no-store",
        "Pragma": "no-cache",
    }

    with httpx.Client(timeout=REQUEST_TIMEOUT_S, follow_redirects=True) as client:
        try:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            all_data: dict[str, Any] = r.json()
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Failed to fetch AHS wait times from {AHS_WAIT_TIMES_URL}: {e}") from e

    if not isinstance(all_data, dict):
        raise RuntimeError("AHS wait times response is not a JSON object")

    calgary_data = all_data.get("Calgary", {})
    if not isinstance(calgary_data, dict):
        raise RuntimeError("Calgary key missing from AHS wait times response")

    hospitals: list[dict[str, Any]] = []
    upcc_centres: list[dict[str, Any]] = []

    for entry in calgary_data.get("Emergency", []):
        hospitals.extend(_build_rows_from_entry(entry, is_upcc=False))

    for entry in calgary_data.get("Urgent", []):
        upcc_centres.extend(_build_rows_from_entry(entry, is_upcc=True))

    # Filter out rows with no available wait time
    hospitals_out = [h for h in hospitals if h["wait_text"] != "Unavailable"]
    upcc_out = [c for c in upcc_centres if c["wait_text"] != "Unavailable"]

    if not hospitals_out and not upcc_out:
        raise RuntimeError("No Calgary wait time data available")

    checked = datetime.now(CALGARY_TZ).replace(tzinfo=None)
    checked_s = checked.strftime("%Y-%m-%dT%H:%M:%S")

    logger.info(
        "calgary-wait-times ok hospitals=%d/%d upcc=%d/%d checked_at=%s",
        len(hospitals_out), len(hospitals),
        len(upcc_out), len(upcc_centres),
        checked_s,
    )

    return {
        "checked_at": checked_s,
        "source_updated_at": None,
        "hospitals": hospitals_out,
        "upcc_centres": upcc_out,
        "wait_times_available": True,
        "city_id": "calgary",
    }
