"""
Live Ontario / GTA emergency wait times from howlongwilliwait.com.

Source: GET https://www.howlongwilliwait.com/sample.json
Format: flat JSON { "Hospital Name": "X hr Y min" | "Not available" | "X hr Y min to A hr B min" }
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

HLWIW_JSON_URL = "https://www.howlongwilliwait.com/sample.json"
REQUEST_TIMEOUT_S = 18.0
TORONTO_TZ = ZoneInfo("America/Toronto")

# GTA hospitals to track — key must be unique, match_name must match JSON key exactly.
TARGET_GTA_HOSPITALS: tuple[dict[str, str], ...] = (
    {
        "key": "toronto_general",
        "match_name": "Toronto General (University Health Network)",
        "name": "Toronto General Hospital",
        "city": "Toronto",
    },
    {
        "key": "toronto_western",
        "match_name": "Toronto Western (University Health Network)",
        "name": "Toronto Western Hospital",
        "city": "Toronto",
    },
    {
        "key": "sunnybrook",
        "match_name": "Sunnybrook",
        "name": "Sunnybrook Health Sciences Centre",
        "city": "Toronto",
    },
    {
        "key": "st_michaels",
        "match_name": "St. Michaels (Unity) Toronto",
        "name": "St. Michael's Hospital",
        "city": "Toronto",
    },
    {
        "key": "north_york_general",
        "match_name": "North York General",
        "name": "North York General Hospital",
        "city": "Toronto",
    },
    {
        "key": "humber_river",
        "match_name": "Humber River Hospital",
        "name": "Humber River Hospital",
        "city": "Toronto",
    },
    {
        "key": "st_josephs_toronto",
        "match_name": "St. Josephs Health Centre (Unity) Toronto",
        "name": "St. Joseph's Health Centre",
        "city": "Toronto",
    },
    {
        "key": "mississauga_trillium",
        "match_name": "Mississauga (Trillium Health Partners)",
        "name": "Mississauga Hospital",
        "city": "Mississauga",
    },
    {
        "key": "credit_valley",
        "match_name": "Credit Valley (Trillium Health Partners)",
        "name": "Credit Valley Hospital",
        "city": "Mississauga",
    },
    {
        "key": "brampton_civic",
        "match_name": "Brampton Civic (William Osler Health System)",
        "name": "Brampton Civic Hospital",
        "city": "Brampton",
    },
    {
        "key": "etobicoke",
        "match_name": "Etobicoke (William Osler Health System)",
        "name": "Etobicoke General Hospital",
        "city": "Toronto",
    },
    {
        "key": "markham_stouffville",
        "match_name": "Markham Stouffville (Oak Valley Health)",
        "name": "Markham Stouffville Hospital",
        "city": "Markham",
    },
    {
        "key": "mackenzie_richmond_hill",
        "match_name": "Mackenzie Richmond Hill (Mackenzie Health)",
        "name": "Mackenzie Richmond Hill Hospital",
        "city": "Richmond Hill",
    },
    {
        "key": "cortellucci_vaughan",
        "match_name": "Cortellucci Vaughan (Mackenzie Health)",
        "name": "Cortellucci Vaughan Hospital",
        "city": "Vaughan",
    },
    {
        "key": "oshawa_lakeridge",
        "match_name": "Oshawa (Lakeridge Health)",
        "name": "Lakeridge Health Oshawa",
        "city": "Oshawa",
    },
    {
        "key": "ajax_lakeridge",
        "match_name": "Ajax (Lakeridge Health)",
        "name": "Lakeridge Health Ajax",
        "city": "Ajax",
    },
    {
        "key": "oakville_trafalgar",
        "match_name": "Oakville Trafalgar Memorial (Halton Healthcare)",
        "name": "Oakville Trafalgar Memorial Hospital",
        "city": "Oakville",
    },
    {
        "key": "joseph_brant",
        "match_name": "Joseph Brant Hospital, Burlington",
        "name": "Joseph Brant Hospital",
        "city": "Burlington",
    },
)

# Ontario Urgent Care Centres in the GTA (equivalent of BC's UPCC).
TARGET_GTA_UPCC: tuple[dict[str, str], ...] = (
    {
        "key": "peel_memorial_uc",
        "match_name": "Peel Memorial Urgent Care (William Osler Health System)",
        "name": "Peel Memorial Urgent Care Centre",
        "city": "Brampton",
        "address": "20 Lynch St, Brampton, ON L6W 2Z8",
    },
)


def _parse_wait_to_minutes(raw: str) -> int | None:
    """
    Parse strings like:
      "2 hr 42 min"             → 162
      "2 hr 15 min to 3 hr 51 min"  → 135  (take lower bound)
      "5+ hr 0 min"             → 300
      "Not available"           → None
    """
    s = str(raw or "").strip()
    if not s or s.lower() == "not available":
        return None

    # Range: take lower bound
    if " to " in s:
        s = s.split(" to ")[0].strip()

    # Strip "+"
    s = s.replace("+", "").strip()

    m = re.match(r"(\d+)\s*hr\s+(\d+)\s*min", s, re.I)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    return None


def _minutes_to_wait_text(total_minutes: int) -> str:
    h, m = divmod(total_minutes, 60)
    return f"{h}h {m:02d}m"


def fetch_gta_wait_times_payload() -> dict[str, Any]:
    """
    Fetches GTA hospital wait times from howlongwilliwait.com/sample.json.

    Returns the same shape as fetch_er_wait_times_payload():
      checked_at, source_updated_at, hospitals, upcc_centres
    """
    cache_bust = int(time.time() * 1000)
    url = f"{HLWIW_JSON_URL}?_={cache_bust}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, */*;q=0.8",
        "Referer": "https://www.howlongwilliwait.com/",
        "Cache-Control": "no-cache, no-store",
        "Pragma": "no-cache",
    }

    with httpx.Client(timeout=REQUEST_TIMEOUT_S, follow_redirects=True) as client:
        try:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            data: dict[str, str] = r.json()
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Failed to fetch GTA wait times from {HLWIW_JSON_URL}: {e}") from e

    if not isinstance(data, dict):
        raise RuntimeError("GTA wait times response is not a JSON object")

    def _build_rows(targets: tuple, include_address: bool = False) -> list[dict[str, Any]]:
        rows = []
        for meta in targets:
            raw_wait = data.get(meta["match_name"], "")
            mins = _parse_wait_to_minutes(raw_wait)
            wait_text = _minutes_to_wait_text(mins) if mins is not None else "Unavailable"

            # Preserve range: "2 hr 15 min to 3 hr 51 min" → "2h 15m–3h 51m"
            original = str(raw_wait or "").strip()
            if " to " in original and mins is not None:
                parts = original.split(" to ")
                lo = _parse_wait_to_minutes(parts[0])
                hi = _parse_wait_to_minutes(parts[1]) if len(parts) > 1 else None
                if lo is not None and hi is not None:
                    wait_text = f"{_minutes_to_wait_text(lo)}–{_minutes_to_wait_text(hi)}"

            row: dict[str, Any] = {
                "key": meta["key"],
                "name": meta["name"],
                "city": meta["city"],
                "wait_text": wait_text,
            }
            if include_address and meta.get("address"):
                row["address"] = meta["address"]
            rows.append(row)
        return rows

    hospitals: list[dict[str, Any]] = _build_rows(TARGET_GTA_HOSPITALS)
    upcc_centres: list[dict[str, Any]] = _build_rows(TARGET_GTA_UPCC, include_address=True)

    checked = datetime.now(TORONTO_TZ).replace(tzinfo=None)
    checked_s = checked.strftime("%Y-%m-%dT%H:%M:%S")

    # Filter rows that have real wait data
    hospitals_out = [h for h in hospitals if h["wait_text"] != "Unavailable"]
    upcc_out = [c for c in upcc_centres if c["wait_text"] != "Unavailable"]

    if not hospitals_out and not upcc_out:
        raise RuntimeError("No GTA wait time data available (all hospitals returned Unavailable)")

    logger.info(
        "gta-wait-times ok hospitals=%d/%d upcc=%d/%d checked_at=%s",
        len(hospitals_out),
        len(hospitals),
        len(upcc_out),
        len(upcc_centres),
        checked_s,
    )

    return {
        "checked_at": checked_s,
        "source_updated_at": None,
        "hospitals": hospitals_out,
        "upcc_centres": upcc_out,
        "wait_times_available": True,
        "city_id": "gta",
    }
