"""
Live BC Lower Mainland ER wait times from the public edwaittimes.ca dashboard.

Primary source: JSON API (stable for parsing). Fallback: legacy HTML page (no-JS view).
Adjust EDWAITTIMES_* constants if the upstream layout changes.

Display policy: we ingest EVERY facility the source publishes (all ``ed`` rows as
hospitals, all ``upcc`` rows as centres). Facilities the source is not currently
publishing a wait for (``showWaitTimes`` false / no ``waitTimeMinutes``) are kept
and flagged ``wait_status="not_published"`` with an empty ``wait_text`` — the
frontend lists them with an honest "not published" label instead of hiding them.
TARGET_* below are no longer whitelists: they only provide canonical keys,
curated display names/cities, fallback coordinates, and a familiar sort order
(canonical facilities first, then the rest in upstream order).
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

# Canonical keys and display metadata for our longest-tracked hospitals. NOT a
# whitelist — every upstream ``ed`` row is returned; these only pin the key,
# display name/city, and lead the ordering for facilities we already know.
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

# Urgent and Primary Care Centres (type ``upcc`` in the same JSON API). Same role
# as TARGET_HOSPITALS: canonical metadata + ordering, not a whitelist.
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


# Coordinates for every facility above, keyed by our canonical ``key``.
# Source: each facility's public street address (VCH / Fraser Health public listings,
# as also published on edwaittimes.ca) geocoded to the building. Used by the frontend
# "Fastest near you" ranking to estimate drive time; coordinates only — no visitor
# location ever leaves the visitor's browser.
FACILITY_COORDS: dict[str, tuple[float, float]] = {
    # Hospitals (public addresses in TARGET_HOSPITALS order)
    "delta": (49.085866, -123.061768),  # 5800 Mountain View Blvd, Delta
    "richmond": (49.168873, -123.146325),  # 7000 Westminster Hwy, Richmond
    "burnaby": (49.248776, -123.016837),  # 3935 Kincaid St, Burnaby
    "vgh": (49.262407, -123.124461),  # 920 W 10th Ave, Vancouver
    "bc_children": (49.245417, -123.123578),  # 4480 Oak St, Vancouver
    "royal_columbian": (49.226603, -122.892266),  # 330 E Columbia St, New Westminster
    # UPCCs (public addresses in TARGET_UPCC_CENTRES above)
    "van_city_centre_upcc": (49.275794, -123.118055),
    "ubc_upcc": (49.2617, -123.24611),
    "north_van_upcc": (49.31233, -123.083585),
    "richmond_city_upcc": (49.182207, -123.136267),
    "metrotown_upcc": (49.230061, -123.002786),
    "edmonds_upcc": (49.218947, -122.951261),
    "port_moody_upcc": (49.278416, -122.840097),
    "richmond_east_upcc": (49.187095, -123.107718),
    "surrey_whalley_upcc": (49.177995, -122.842549),
    "surrey_newton_upcc": (49.126539, -122.845132),
    "northeast_upcc": (49.281145, -123.047057),
    "southeast_upcc": (49.230575, -123.06518),
    "reach_upcc": (49.274416, -123.069684),
    "langley_upcc": (49.105003, -122.652244),
    "ridge_meadows_upcc": (49.21798, -122.599999),
    "abbotsford_upcc": (49.050858, -122.337022),
    "mission_upcc": (49.130221, -122.318125),
    "chilliwack_upcc": (49.146009, -121.98077),
}


def _coords_for(key: str) -> dict[str, float]:
    lat_lng = FACILITY_COORDS.get(key)
    if lat_lng is None:
        return {}
    return {"lat": lat_lng[0], "lng": lat_lng[1]}


def _normalize_hospital_name(name: str) -> str:
    return " ".join(name.split())


def _city_from_address(address: str) -> str:
    """
    Best-effort city from a Canadian street address, e.g.
    "920 West 10th Ave, Vancouver, BC, V5Z 1M9" -> "Vancouver";
    "5800 Mountain View Blvd, Delta BC, V4K 3V6" -> "Delta".
    Returns "" when the shape is not recognised.
    """
    if not address or not isinstance(address, str):
        return ""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    for i, part in enumerate(parts):
        if re.match(r"BC\b", part, re.I):
            # Province (+ postal) segment: city is the previous segment,
            # unless that segment itself carries a trailing " BC".
            if i == 0:
                return ""
            prev = parts[i - 1]
            if re.search(r"\sBC$", prev, re.I):
                return re.sub(r"\sBC$", "", prev, flags=re.I).strip()
            return prev
        if re.search(r"\sBC$", part, re.I):
            return re.sub(r"\sBC$", "", part, flags=re.I).strip()
    return ""


def _key_from_upstream(rec: dict[str, Any], name: str) -> str:
    """Stable row key for a non-canonical facility: upstream slug, else slugified name."""
    slug = rec.get("slug")
    base = slug if isinstance(slug, str) and slug.strip() else name
    key = re.sub(r"[^a-z0-9]+", "_", str(base).lower()).strip("_")
    return key or "facility"


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


def _build_rows_from_json_list(
    rows: list[dict[str, Any]],
    *,
    kind: str,
    targets: tuple[dict[str, str], ...],
) -> tuple[list[dict[str, Any]], datetime | None]:
    """
    Ingest EVERY upstream row of one kind (``kind`` = "ed" hospitals or "upcc"
    centres). Canonical targets (matched by name) keep their curated key, name
    and city and sort first; all other published facilities follow in upstream
    order with source name, address-parsed city, and source coordinates.

    Each row gets ``wait_status``: "live" when the source is publishing a wait
    (``wait_text`` formatted from it), else "not_published" with an empty
    ``wait_text`` — never a fabricated number.
    """
    meta_by_norm = {_normalize_hospital_name(m["match_name"]): m for m in targets}
    canonical_rank = {m["key"]: i for i, m in enumerate(targets)}

    picked: list[tuple[int, int, dict[str, Any]]] = []
    seen_names: set[str] = set()
    used_keys: set[str] = set()
    latest: datetime | None = None

    for pos, rec in enumerate(rows):
        if not isinstance(rec, dict):
            continue
        rtype = rec.get("type")
        if kind == "upcc":
            if rtype != "upcc":
                continue
        elif rtype == "upcc":
            continue
        status = rec.get("status")
        if isinstance(status, str) and status and status != "published":
            continue
        name_raw = rec.get("name")
        if not isinstance(name_raw, str) or not name_raw.strip():
            continue
        norm = _normalize_hospital_name(name_raw)
        if norm in seen_names:
            continue
        seen_names.add(norm)

        meta = meta_by_norm.get(norm)
        address = rec.get("address") if isinstance(rec.get("address"), str) else ""

        wt = rec.get("waitTime") if isinstance(rec.get("waitTime"), dict) else None
        created_iso = wt.get("createdAt") if wt and isinstance(wt.get("createdAt"), str) else None
        if wt:
            parsed = _parse_iso_to_vancouver_naive(wt.get("createdAt"))
            if parsed and (latest is None or parsed > latest):
                latest = parsed

        mins = _wait_minutes_from_api_entry(rec)
        if mins is not None:
            wait_text = minutes_to_wait_text(mins)
            wait_status = "live"
        else:
            wait_text = ""
            wait_status = "not_published"

        # Coordinates: source values win; canonical constant table is the fallback.
        coords: dict[str, float] = {}
        lat, lng = rec.get("latitude"), rec.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            coords = {"lat": float(lat), "lng": float(lng)}
        elif meta is not None:
            coords = _coords_for(meta["key"])

        if meta is not None:
            key = meta["key"]
            bucket, rank = 0, canonical_rank[key]
        else:
            key = _key_from_upstream(rec, name_raw)
            bucket, rank = 1, pos
        base_key = key
        suffix = 2
        while key in used_keys:
            key = f"{base_key}_{suffix}"
            suffix += 1
        used_keys.add(key)

        row_out: dict[str, Any] = {
            "key": key,
            "name": meta["name"] if meta is not None else name_raw.strip(),
            "city": meta["city"] if meta is not None else _city_from_address(address),
            "address": address or (meta.get("address", "") if meta is not None else ""),
            "wait_text": wait_text,
            "wait_status": wait_status,
            "phone": rec.get("phone") if isinstance(rec.get("phone"), str) else "",
            "website": rec.get("website") if isinstance(rec.get("website"), str) else "",
            **coords,
        }
        if _WAIT_TIMES_DEBUG:
            row_out["_debug"] = {
                "raw_before_format": wt.get("waitTimeMinutes") if wt else None,
                "raw_before_format_kind": f"waitTimeMinutes (JSON API, {kind})",
                "source_timestamp_raw": created_iso,
                "upstream_slug": rec.get("slug") if isinstance(rec.get("slug"), str) else None,
                "upstream_id": rec.get("id") if isinstance(rec.get("id"), str) else None,
            }
        picked.append((bucket, rank, row_out))

    picked.sort(key=lambda t: (t[0], t[1]))
    return [r for _, _, r in picked], latest


def _build_from_json_list(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], datetime | None]:
    """All upstream emergency departments (type ``ed``), canonical six first."""
    return _build_rows_from_json_list(rows, kind="ed", targets=TARGET_HOSPITALS)


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
            "address": "",
            "wait_text": "" if wait_text == "Unavailable" else wait_text,
            "wait_status": "not_published" if wait_text == "Unavailable" else "live",
            "phone": "",
            "website": "",
            **_coords_for(meta["key"]),
        }
        if _WAIT_TIMES_DEBUG:
            row_out["_debug"] = dbg
        hospitals.append(row_out)

    return hospitals, latest


def _build_upcc_from_json_list(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], datetime | None]:
    """All upstream Urgent and Primary Care Centres (type ``upcc``) from the same API list."""
    return _build_rows_from_json_list(rows, kind="upcc", targets=TARGET_UPCC_CENTRES)


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
      source_updated_at: newest timestamp from the upstream payload, or null.
      hospitals: EVERY emergency department the source lists. Rows carry
        ``wait_status`` — "live" with a formatted ``wait_text``, or
        "not_published" with an empty ``wait_text`` when the source is not
        publishing a wait for that facility right now.
      upcc_centres: same contract for Urgent and Primary Care Centres
        (JSON mode only; empty when using the legacy HTML fallback).
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
            if hospitals:
                # JSON is the source of truth even when it currently publishes
                # few (or zero) live waits — rows say "not_published" honestly
                # instead of us falling back or erroring.
                fetched_url_used = json_url
                parse_mode = "json"
            else:
                hospitals = None

        if not hospitals:
            # JSON fetch failed or yielded no facilities: emergency fallback to
            # the legacy no-JS page (canonical hospitals only, no UPCC rows).
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

        live_count = sum(
            1 for r in (*hospitals, *upcc_centres) if r.get("wait_status") == "live"
        )
        if live_count == 0:
            logger.warning(
                "wait-times: source lists %d facilities but publishes no live waits right now",
                len(hospitals) + len(upcc_centres),
            )

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

        return {
            "checked_at": checked_s,
            "source_updated_at": source_s,
            "hospitals": hospitals,
            "upcc_centres": upcc_centres,
            "debug": {
                "temporary": True,
                "fetched_url": fetched_url_used,
                "parse_mode": parse_mode,
            },
        }
