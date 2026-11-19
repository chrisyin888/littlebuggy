"""GET /wait-times — live ER wait times for selected city hospitals (proxy + parse public source).

Currently only Metro Vancouver (edwaittimes.ca) is supported. Other cities return an empty list
with a ``wait_times_available: false`` flag so the frontend can show a friendly message instead
of an error.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config.cities import resolve_city_id
from app.services.er_wait_times_source import fetch_er_wait_times_payload
from app.services.gta_wait_times_source import fetch_gta_wait_times_payload
from app.services.calgary_wait_times_source import fetch_calgary_wait_times_payload

logger = logging.getLogger(__name__)

router = APIRouter()

_VANCOUVER_CITY_ID = "vancouver"

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _fetch_payload(city_profile) -> dict:
    """Build the success payload for a city (raises on upstream failure)."""
    if city_profile.id == "gta":
        return fetch_gta_wait_times_payload()

    if city_profile.id == "calgary":
        return fetch_calgary_wait_times_payload()

    if city_profile.id == _VANCOUVER_CITY_ID:
        body = fetch_er_wait_times_payload()
        body["city_id"] = _VANCOUVER_CITY_ID
        body["wait_times_available"] = True
        return body

    # Other cities — not yet available
    checked_s = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "city_id": city_profile.id,
        "region": city_profile.name,
        "hospitals": [],
        "upcc_centres": [],
        "checked_at": checked_s,
        "source_updated_at": None,
        "wait_times_available": False,
        "wait_times_note": (
            f"Live ER wait times are not yet available for {city_profile.name}. "
            "We’re working on adding more cities."
        ),
    }


def _error_detail(city_profile) -> str:
    if city_profile.id == "gta":
        return "We couldn’t load GTA wait times right now. Please try again in a few minutes."
    if city_profile.id == "calgary":
        return "We couldn't load Calgary wait times right now. Please try again in a few minutes."
    return "We couldn’t load emergency wait times right now. Please try again in a few minutes."


@router.get("/wait-times")
def get_wait_times(
    city: str | None = Query(default=None, description="City id, e.g. ‘vancouver’, ‘gta’, ‘calgary’"),
):
    city_profile = resolve_city_id(city)

    try:
        body = _fetch_payload(city_profile)
    except Exception as e:
        logger.exception("%s wait-times fetch/parse failed: %s", city_profile.id, e)
        return JSONResponse(
            status_code=503,
            content={"detail": _error_detail(city_profile)},
            headers=_NO_STORE_HEADERS,
        )
    return JSONResponse(content=body, headers=_NO_STORE_HEADERS)


def _fmt_ts(raw: str | None) -> str:
    """'2026-11-19T15:42:00' (Vancouver local, naive ISO) → '2026-11-19 15:42'."""
    if not raw:
        return "not available"
    return str(raw).replace("T", " ")[:16]


def _wait_display(row: dict) -> str:
    text = (row.get("wait_text") or "").strip()
    if row.get("wait_status") == "live" and text:
        return text
    if row.get("wait_status") == "not_published":
        return "Not currently published"
    return text or "Not currently published"


def _render_wait_times_text(body: dict) -> str:
    """Plain-text snapshot of the live payload — readable without JavaScript.

    Rendered fresh on every request from the same payload as ``GET /wait-times``,
    so crawlers and AI assistants see real numbers with their timestamps.
    Facilities whose health authority is not publishing stay explicitly
    'Not currently published' — never estimated or back-filled.
    """
    region = body.get("region") or "Metro Vancouver"
    lines = [
        f"LittleBuggy — ER & UPCC wait times for {region}",
        "",
        f"Snapshot generated: {_fmt_ts(body.get('checked_at'))} Pacific Time (America/Vancouver)",
        f"Source data last updated: {_fmt_ts(body.get('source_updated_at'))} Pacific Time",
        "Source: official provincial wait-times feed, fetched live by LittleBuggy for this request.",
        "Wait times are estimates and change through the day. In an emergency, call 911. "
        "For health advice, call HealthLink BC at 8-1-1.",
        "",
    ]
    if body.get("wait_times_note"):
        lines += [str(body["wait_times_note"]), ""]

    hospitals = body.get("hospitals") or []
    lines.append(f"EMERGENCY DEPARTMENTS ({len(hospitals)})")
    for h in hospitals:
        city = (h.get("city") or "").strip()
        suffix = f" ({city})" if city else ""
        lines.append(f"- {h.get('name', '')}{suffix}: {_wait_display(h)}")
    lines.append("")

    upccs = body.get("upcc_centres") or []
    lines.append(f"URGENT & PRIMARY CARE CENTRES — UPCC ({len(upccs)})")
    for u in upccs:
        city = (u.get("city") or "").strip()
        suffix = f" ({city})" if city else ""
        lines.append(f"- {u.get('name', '')}{suffix}: {_wait_display(u)}")
    lines.append("")

    lines += [
        "Note: facilities marked \"Not currently published\" are not publishing a wait time "
        "right now. Fraser Health paused publishing ER wait times on August 17, 2026; "
        "LittleBuggy shows that honestly instead of an old number, and times reappear here "
        "as soon as publishing resumes.",
        "",
        "Live page: https://littlebuggy.ca/wait-times/",
        "JSON API: https://littlebuggy-api.onrender.com/wait-times",
        "About LittleBuggy and its data: https://littlebuggy.ca/llms.txt",
        "",
    ]
    return "\n".join(lines)


@router.get("/wait-times.txt")
def get_wait_times_text(
    city: str | None = Query(default=None, description="City id, e.g. ‘vancouver’, ‘gta’, ‘calgary’"),
):
    """Plain-text live wait times — same payload as /wait-times, no JavaScript needed."""
    city_profile = resolve_city_id(city)

    try:
        body = _fetch_payload(city_profile)
    except Exception as e:
        logger.exception("%s wait-times.txt fetch/parse failed: %s", city_profile.id, e)
        return PlainTextResponse(
            status_code=503,
            content="We couldn't load wait times right now. Please try again in a few minutes.\n",
            headers=_NO_STORE_HEADERS,
        )
    return PlainTextResponse(content=_render_wait_times_text(body), headers=_NO_STORE_HEADERS)
