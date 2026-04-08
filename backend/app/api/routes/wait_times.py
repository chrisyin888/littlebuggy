"""GET /wait-times — live ER wait times for selected Metro Vancouver hospitals (proxy + parse public source)."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.er_wait_times_source import fetch_er_wait_times_payload

logger = logging.getLogger(__name__)

router = APIRouter()

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@router.get("/wait-times")
def get_wait_times():
    try:
        body = fetch_er_wait_times_payload()
        return JSONResponse(content=body, headers=_NO_STORE_HEADERS)
    except Exception as e:
        logger.exception("wait-times upstream fetch/parse failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "We couldn’t load emergency wait times right now. Please try again in a few minutes.",
            },
            headers=_NO_STORE_HEADERS,
        )
