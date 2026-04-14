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
from fastapi.responses import JSONResponse

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


@router.get("/wait-times")
def get_wait_times(
    city: str | None = Query(default=None, description="City id, e.g. ‘vancouver’, ‘gta’, ‘calgary’"),
):
    city_profile = resolve_city_id(city)

    # Dispatch to the right source based on city
    if city_profile.id == "gta":
        try:
            body = fetch_gta_wait_times_payload()
            return JSONResponse(content=body, headers=_NO_STORE_HEADERS)
        except Exception as e:
            logger.exception("gta wait-times fetch/parse failed: %s", e)
            return JSONResponse(
                status_code=503,
                content={"detail": "We couldn’t load GTA wait times right now. Please try again in a few minutes."},
                headers=_NO_STORE_HEADERS,
            )

    if city_profile.id == "calgary":
        try:
            body = fetch_calgary_wait_times_payload()
            return JSONResponse(content=body, headers=_NO_STORE_HEADERS)
        except Exception as e:
            logger.exception("calgary wait-times fetch/parse failed: %s", e)
            return JSONResponse(
                status_code=503,
                content={"detail": "We couldn't load Calgary wait times right now. Please try again in a few minutes."},
                headers=_NO_STORE_HEADERS,
            )

    if city_profile.id == _VANCOUVER_CITY_ID:
        try:
            body = fetch_er_wait_times_payload()
            body["city_id"] = _VANCOUVER_CITY_ID
            body["wait_times_available"] = True
            return JSONResponse(content=body, headers=_NO_STORE_HEADERS)
        except Exception as e:
            logger.exception("vancouver wait-times fetch/parse failed: %s", e)
            return JSONResponse(
                status_code=503,
                content={"detail": "We couldn’t load emergency wait times right now. Please try again in a few minutes."},
                headers=_NO_STORE_HEADERS,
            )

    # Calgary and other cities — not yet available
    checked_s = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S")
    return JSONResponse(
        content={
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
        },
        headers=_NO_STORE_HEADERS,
    )
