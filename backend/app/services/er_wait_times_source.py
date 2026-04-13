"""
Live BC Lower Mainland ER wait times from the public edwaittimes.ca dashboard.

Primary source: JSON API (stable for parsing). Fallback: legacy HTML page (no-JS view).
Adjust EDWAITTIMES_* constants if the upstream layout changes.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Default off: drops per-row _debug from JSON and avoids per-hospital log lines (lower RSS + allocator churn on 512MB workers). Set WAIT_TIMES_DEBUG=1 for local troubleshooting.
_WAIT_TIMES_DEBUG = os.environ.get("WAIT_TIMES_DEBUG", "").strip().lower() in ("1", "true", "yes")

EDWAITTIMES_JSON_URL = "https://www.edwaittimes.ca/api/wait-times"
EDWAITTIMES_LEGACY_URL = "https://www.edwaittimes.ca/legacy"
REQUEST_TIMEOUT_S = 18.0
VANCOUVER_TZ = ZoneInfo("America/Vancouver")

# Canonical keys and display metadata (order preserved in API responses).
TARGET_HOSPITALS: tuple[dict[str, str], ...] = (
    {"key": "delta", "match_name": "Delta Hospital", "name": "Delta Hospital", "city": "Delta"},
    {"key": "richmond", "match_name": "Richmond Hospital", "name": "Richmond Hospital", "city": "Richmond"},
    {"key": "burnaby", "match_name": "Burnaby Hospital", "name": "Burnaby Hospital", "city": "Burnaby"},
    {
        "key": "vgh",
        "match_name": "Vancouver General Hospital",
        "name": "Vancouver General Hospital",
        "city": "Vancouver",
    },
    {
        "key": "bc_children",
        "match_name": "BC Children's Hospital",
        "name": "BC Children's Hospital",
        "city": "Vancouver",
    },
    {
        "key": "royal_columbian",
        "match_name": "Royal Columbian Hospital",
        "name": "Royal Columbian Hospital",
        "city": "New Westminster",
    },
)

# Urgent and Primary Care Centres (type ``upcc`` in the same JSON API).
# ``address`` lines are for parent-facing UI (VCH / Fraser Health public listings; verify if sites move).
TARGET_UPCC_CENTRES: tuple[dict[str, str], ...] = (
    {
        "key": "van_city_centre_upcc",
        "match_name": "Vancouver City Centre Urgent and Primary Care Centre",
        "name": "Vancouver City Centre Urgent and Primary Care Centre",
        "city": "Vancouver",
        "address": "188 Nelson St, Vancouver, BC V6B 1A9",
    },
    {
        "key": "ubc_upcc",
        "match_name": "UBC Urgent and Primary Care Centre",
        "name": "UBC Urgent and Primary Care Centre",
        "city": "Vancouver",
        "address": "6165 Agronomy Rd, Vancouver, BC V6T 1Z3",
    },
    {
        "key": "north_van_upcc",
        "match_name": "North Vancouver Centre Urgent and Primary Care Centre",
        "name": "North Vancouver Centre Urgent and Primary Care Centre",
        "city": "North Vancouver",
        "address": "200-221 W Esplanade, North Vancouver, BC V7L 1A5",
    },
    {
        "key": "richmond_city_upcc",
        "match_name": "Richmond City Centre Urgent and Primary Care Centre",
        "name": "Richmond City Centre Urgent and Primary Care Centre",
        "city": "Richmond",
        "address": "110-4671 No. 3 Rd, Richmond, BC V6X 2C3",
    },
    {
        "key": "metrotown_upcc",
        "match_name": "Metrotown UPCC",
        "name": "Metrotown UPCC",
        "city": "Burnaby",
        "address": "102-4555 Kingsway, Burnaby, BC V5H 4V8",
    },
    {
        "key": "edmonds_upcc",
        "match_name": "Edmonds UPCC",
        "name": "Edmonds UPCC",
        "city": "Burnaby",
        "address": "201-7315 Edmonds St, Burnaby, BC V3N 1A7",
    },
    {
        "key": "port_moody_upcc",
        "match_name": "Port Moody UPCC",
        "name": "Port Moody UPCC",
        "city": "Port Moody",
        "address": "3105 Murray St, Port Moody, BC V3H 1X3",
    },
    {
        "key": "richmond_east_upcc",
        "match_name": "Richmond East Urgent and Primary Care Centre",
        "name": "Richmond East Urgent and Primary Care Centre",
        "city": "Richmond",
        "address": "95-10551 Shellbridge Way, Richmond, BC V6X 2W9",
    },
    {
        "key": "surrey_whalley_upcc",
        "match_name": "Surrey Whalley UPCC",
        "name": "Surrey Whalley UPCC",
        "city": "Surrey",
        "address": "G2-9639 137A St, Surrey, BC V3T 0M1",
    },
    {
        "key": "surrey_newton_upcc",
        "match_name": "Surrey Newton UPCC",
        "name": "Surrey Newton UPCC",
        "city": "Surrey",
        "address": "6830 King George Blvd, Surrey, BC V3W 4Z9",
    },
    {
        "key": "northeast_upcc",
        "match_name": "Northeast Urgent and Primary Care Centre",
        "name": "Northeast Urgent and Primary Care Centre",
        "city": "Vancouver",
        "address": "102-2788 E Hastings St, Vancouver, BC V5K 1Z9",
    },
    {
        "key": "southeast_upcc",
        "match_name": "Southeast Urgent and Primary Care Centre",
        "name": "Southeast Urgent and Primary Care Centre",
        "city": "Vancouver",
        "address": "5880 Victoria Dr, Vancouver, BC V5P 3W9",
    },
    {
        "key": "reach_upcc",
        "match_name": "REACH Urgent and Primary Care Centre",
        "name": "REACH Urgent and Primary Care Centre",
        "city": "Vancouver",
        "address": "1145 Commercial Dr, Vancouver, BC V5L 3X3",
    },
    {
        "key": "langley_upcc",
        "match_name": "Langley UPCC",
        "name": "Langley UPCC",
        "city": "Langley",
        "address": "202-20434 64 Ave, Langley, BC V2Y 1N4",
    },
    {
        "key": "ridge_meadows_upcc",
        "match_name": "Ridge Meadows UPCC",
        "name": "Ridge Meadows UPCC",
        "city": "Maple Ridge",
        "address": "121-11900 Haney Place, Maple Ridge, BC V2X 8R9",
    },
    {
        "key": "abbotsford_upcc",
        "match_name": "Abbotsford UPCC",
        "name": "Abbotsford UPCC",
        "city": "Abbotsford",
        "address": "100-2692 Clearbrook Rd, Abbotsford, BC V2Y 4N8",
    },
    {
        "key": "mission_upcc",
        "match_name": "Mission UPCC",
        "name": "Mission UPCC",
        "city": "Mission",
        "address": "304-32555 London Ave, Mission, BC V2V 6M7",
    },
    {
        "key": "chilliwack_upcc",
        "match_name": "Chilliwack UPCC",
        "name": "Chilliwack UPCC",
        "city": "Chilliwack",
        "address": "104-7955 Evans Rd, Chilliwack, BC V2R 5R7",
    },
)


def _normalize_hospital_name(name: str) -> str:
    return " ".join(name.split())


def _wait_text_is_missing(text: str | None) -> bool:
    """True when upstream gave no usable wait (we still use 'Unavailable' internally until filtering)."""
    if text is None:
        return True
    s = str(text).strip().lower()
    return not s or s == "unavailable"


def _filter_rows_with_waits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if not _wait_text_is_missing(r.get("wait_text"))]


def minutes_to_wait_text(total_minutes: int) -> str:
    if total_minutes < 0:
        total_minutes = 0
    h, m = divmod(total_minutes, 60)
    return f"{h}h {m:02d}m"


def _parse_iso_to_vancouver_naive(iso: str | None) -> datetime | None:
    if not iso or not isinstance(iso, str):
        return None
    try:
        # API uses Z suffix
        if iso.endswith("Z"):
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(VANCOUVER_TZ).replace(tzinfo=None)
    except ValueError:
        return None


def _format_ts_vancouver_naive(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def _upstream_no_cache_headers() -> dict[str, str]:
    """Ask CDNs and caches not to serve stale API/HTML to our backend."""
    return {
        "Cache-Control": "no-cache, no-store, max-age=0",
        "Pragma": "no-cache",
    }


def _wait_minutes_from_api_entry(entry: dict[str, Any]) -> int | None:
    wt = entry.get("waitTime")
    if not isinstance(wt, dict):
        return None
    if entry.get("showWaitTimes") is False:
        return None
    raw = wt.get("waitTimeMinutes")
    if raw is None:
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return None
    return n


def _build_from_json_list(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], datetime | None]:
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        n = row.get("name")
        if isinstance(n, str) and n.strip():
            by_name[_normalize_hospital_name(n)] = row

    hospitals: list[dict[str, Any]] = []
    latest: datetime | None = None

    for meta in TARGET_HOSPITALS:
        match = meta["match_name"]
        rec = by_name.get(_normalize_hospital_name(match))
        wait_text = "Unavailable"
        raw_before_format: Any = None
        created_iso: str | None = None
        slug: str | None = None
        up_id: str | None = None
        if rec is not None:
            wt = rec.get("waitTime") if isinstance(rec.get("waitTime"), dict) else None
            if wt:
                created_iso = wt.get("createdAt") if isinstance(wt.get("createdAt"), str) else None
                raw_before_format = wt.get("waitTimeMinutes")
            mins = _wait_minutes_from_api_entry(rec)
            if mins is not None:
                wait_text = minutes_to_wait_text(mins)
            slug = rec.get("slug") if isinstance(rec.get("slug"), str) else None
            up_id = rec.get("id") if isinstance(rec.get("id"), str) else None
            if wt:
                parsed = _parse_iso_to_vancouver_naive(wt.get("createdAt"))
                if parsed and (latest is None or parsed > latest):
                    latest = parsed

        dbg: dict[str, Any] = {
            "raw_before_format": raw_before_format,
            "raw_before_format_kind": "waitTimeMinutes (JSON API)",
            "source_timestamp_raw": created_iso,
            "upstream_slug": slug,
            "upstream_id": up_id,
        }

        row_out: dict[str, Any] = {
            "key": meta["key"],
            "name": meta["name"],
            "city": meta["city"],
            "wait_text": wait_text,
        }
        if _WAIT_TIMES_DEBUG:
            row_out["_debug"] = dbg
        hospitals.append(row_out)

    return hospitals, latest


def _legacy_parse_card(h3: Any) -> tuple[str, str | None, str | None, str | None]:
    """
    Returns (wait_text, raw_div_text, last_updated_tail, li_element_id).
    """
    card = h3.find_parent("li")
    if card is None:
        return "Unavailable", None, None, None
    li_id = card.get("id") if isinstance(card.get("id"), str) else None
    div = card.find(
        "div",
        class_=lambda c: isinstance(c, str) and "text-2xl" in c and "font-bold" in c,
    )
    raw_div = div.get_text(separator=" ", strip=True) if div is not None else None
    wait_text = "Unavailable"
    if raw_div:
        m = re.search(r"(\d+)\s*h\s*(\d+)\s*m", raw_div, re.I)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            wait_text = minutes_to_wait_text(h * 60 + mi)
        else:
            wait_text = raw_div
    last_tail: str | None = None
    for li in card.find_all("li"):
        row = li.get_text(" ", strip=True)
        if row.lower().startswith("last updated"):
            last_tail = row.split("Last Updated", 1)[-1].strip()
            break
    return wait_text, raw_div, last_tail, li_id


def _build_from_legacy_html(html: str) -> tuple[list[dict[str, Any]], datetime | None]:
    soup = BeautifulSoup(html, "html.parser")
    h3_by_title: dict[str, Any] = {}
    for h3 in soup.find_all("h3"):
        title = h3.get_text(strip=True)
        if title:
            h3_by_title[_normalize_hospital_name(title)] = h3

    hospitals: list[dict[str, Any]] = []
    latest: datetime | None = None

    for meta in TARGET_HOSPITALS:
        match = meta["match_name"]
        h3 = h3_by_title.get(_normalize_hospital_name(match))
        wait_text = "Unavailable"
        raw_div: str | None = None
        last_tail: str | None = None
        li_id: str | None = None
        if h3 is not None:
            wait_text, raw_div, last_tail, li_id = _legacy_parse_card(h3)
            card = h3.find_parent("li")
            if card and last_tail:
                for fmt in ("%m/%d/%Y, %I:%M:%S %p", "%m/%d/%Y, %H:%M:%S"):
                    try:
                        dt = datetime.strptime(last_tail, fmt)
                        dt = dt.replace(tzinfo=VANCOUVER_TZ).replace(tzinfo=None)
                        if latest is None or dt > latest:
                            latest = dt
                        break
                    except ValueError:
                        continue

        dbg: dict[str, Any] = {
            "raw_before_format": raw_div,
            "raw_before_format_kind": "legacy HTML wait div text",
            "source_timestamp_raw": last_tail,
            "upstream_slug": None,
            "upstream_id": li_id,
        }

        row_out: dict[str, Any] = {
            "key": meta["key"],
            "name": meta["name"],
            "city": meta["city"],
            "wait_text": wait_text,
        }
        if _WAIT_TIMES_DEBUG:
            row_out["_debug"] = dbg
        hospitals.append(row_out)

    return hospitals, latest


def _build_upcc_from_json_list(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], datetime | None]:
    """Match published UPCC rows from the same API list as emergency departments."""
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("type") != "upcc":
            continue
        n = row.get("name")
        if isinstance(n, str) and n.strip():
            by_name[_normalize_hospital_name(n)] = row

    centres: list[dict[str, Any]] = []
    latest: datetime | None = None

    for meta in TARGET_UPCC_CENTRES:
        match = meta["match_name"]
        rec = by_name.get(_normalize_hospital_name(match))
        wait_text = "Unavailable"
        raw_before_format: Any = None
        created_iso: str | None = None
        slug: str | None = None
        up_id: str | None = None
        if rec is not None:
            wt = rec.get("waitTime") if isinstance(rec.get("waitTime"), dict) else None
            if wt:
                created_iso = wt.get("createdAt") if isinstance(wt.get("createdAt"), str) else None
                raw_before_format = wt.get("waitTimeMinutes")
            mins = _wait_minutes_from_api_entry(rec)
            if mins is not None:
                wait_text = minutes_to_wait_text(mins)
            slug = rec.get("slug") if isinstance(rec.get("slug"), str) else None
            up_id = rec.get("id") if isinstance(rec.get("id"), str) else None
            if wt:
                parsed = _parse_iso_to_vancouver_naive(wt.get("createdAt"))
                if parsed and (latest is None or parsed > latest):
                    latest = parsed

        dbg: dict[str, Any] = {
            "raw_before_format": raw_before_format,
            "raw_before_format_kind": "waitTimeMinutes (JSON API, UPCC)",
            "source_timestamp_raw": created_iso,
            "upstream_slug": slug,
            "upstream_id": up_id,
        }

        row_out: dict[str, Any] = {
            "key": meta["key"],
            "name": meta["name"],
            "city": meta["city"],
            "address": meta.get("address", ""),
            "wait_text": wait_text,
        }
        if _WAIT_TIMES_DEBUG:
            row_out["_debug"] = dbg
        centres.append(row_out)

    return centres, latest


def _latest_of(a: datetime | None, b: datetime | None) -> datetime | None:
    if a is None:
        return b
    if b is None:
        return a
    return a if a > b else b


def fetch_er_wait_times_payload() -> dict[str, Any]:
    """
    Performs a fresh upstream fetch + parse on every call (no in-process reuse).

    Returns:
      checked_at: when this server finished reading the source (Vancouver local, naive ISO).
      source_updated_at: newest timestamp from the upstream payload for our hospitals, or null.
      hospitals: list of hospital rows.
      upcc_centres: list of Urgent and Primary Care Centre rows (JSON mode only; empty when using legacy HTML).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
        **_upstream_no_cache_headers(),
    }

    hospitals: list[dict[str, Any]] | None = None
    upcc_centres: list[dict[str, Any]] = []
    source_latest: datetime | None = None
    upcc_latest: datetime | None = None
    fetched_url_used = ""
    parse_mode = ""

    # Bust shared caches between requests (ignored by origin but honored by many CDNs).
    cache_bust = int(time.time() * 1000)
    json_url = f"{EDWAITTIMES_JSON_URL}?_={cache_bust}"
    legacy_url = f"{EDWAITTIMES_LEGACY_URL}?_={cache_bust}"

    with httpx.Client(timeout=REQUEST_TIMEOUT_S, follow_redirects=True, headers=headers) as client:
        data: Any = None
        try:
            r = client.get(json_url)
            r.raise_for_status()
            data = r.json()
        except (httpx.HTTPError, json.JSONDecodeError, ValueError, TypeError):
            data = None

        if isinstance(data, list):
            hospitals, source_latest = _build_from_json_list(data)
            upcc_centres, upcc_latest = _build_upcc_from_json_list(data)
            del data  # provincial list can be large; release before optional legacy HTML fetch
            source_latest = _latest_of(source_latest, upcc_latest)
            fetched_url_used = json_url
            parse_mode = "json"

        any_real_wait = bool(
            hospitals and any(h["wait_text"] != "Unavailable" for h in hospitals)
        )

        if not any_real_wait:
            try:
                lr = client.get(legacy_url)
                lr.raise_for_status()
                hospitals, source_latest = _build_from_legacy_html(lr.text)
                upcc_centres = []
                fetched_url_used = legacy_url
                parse_mode = "legacy_html"
            except (httpx.HTTPError, OSError):
                pass

        if not hospitals:
            raise RuntimeError("empty hospital list")

        if not any(h["wait_text"] != "Unavailable" for h in hospitals):
            raise RuntimeError("no wait times parsed")

        checked = datetime.now(VANCOUVER_TZ).replace(tzinfo=None)
        checked_s = _format_ts_vancouver_naive(checked)
        source_s = _format_ts_vancouver_naive(source_latest) if source_latest else None

        logger.info(
            "wait-times ok parse_mode=%s hospitals=%d upcc=%d checked_at=%s",
            parse_mode,
            len(hospitals),
            len(upcc_centres),
            checked_s,
        )
        if _WAIT_TIMES_DEBUG:
            logger.debug(
                "wait-times url=%s source_updated_at=%s",
                fetched_url_used,
                source_s,
            )
            for h in hospitals:
                d = h.get("_debug") or {}
                logger.debug(
                    "wait-times hospital key=%s raw=%r source_ts=%r",
                    h.get("key"),
                    d.get("raw_before_format"),
                    d.get("source_timestamp_raw"),
                )
            for c in upcc_centres:
                d = c.get("_debug") or {}
                logger.debug(
                    "wait-times upcc key=%s raw=%r source_ts=%r",
                    c.get("key"),
                    d.get("raw_before_format"),
                    d.get("source_timestamp_raw"),
                )

        hospitals_out = _filter_rows_with_waits(hospitals)
        upcc_out = _filter_rows_with_waits(upcc_centres)

        return {
            "checked_at": checked_s,
            "source_updated_at": source_s,
            "hospitals": hospitals_out,
            "upcc_centres": upcc_out,
            "debug": {
                "temporary": True,
                "fetched_url": fetched_url_used,
                "parse_mode": parse_mode,
            },
        }
