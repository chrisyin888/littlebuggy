"""GET /virus-trends (public) and POST /api/admin/virus-trends/refresh (token)."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse

from app.settings import settings
from app.services.virus_trends_fetch import BCCDC_RESPIRATORY_URL
from app.services.virus_trends_refresh import run_virus_trends_refresh
from app.services.virus_trends_storage import load_latest

logger = logging.getLogger(__name__)

public_router = APIRouter()
admin_router = APIRouter()

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

_DEFAULT_VIRUSES: list[dict[str, str]] = [
    {"key": "rsv", "name": "RSV", "level": "Unknown"},
    {"key": "flu_a", "name": "Influenza A", "level": "Unknown"},
    {"key": "flu_b", "name": "Influenza B", "level": "Unknown"},
    {"key": "covid", "name": "COVID-19", "level": "Unknown"},
]


def _default_payload() -> dict[str, Any]:
    return {
        "checked_at": None,
        "source_report_date": None,
        "source_name": "BCCDC",
        "summary": (
            "No successful automated refresh has been written yet. "
            "Levels appear after the scheduled job or admin refresh runs."
        ),
        "viruses": [dict(v) for v in _DEFAULT_VIRUSES],
        "source_url": BCCDC_RESPIRATORY_URL,
    }


def _verify_admin_token(header_value: str | None) -> None:
    expected = (settings.admin_homepage_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin refresh is disabled (set ADMIN_HOMEPAGE_TOKEN on the API).",
        )
    got = (header_value or "").strip()
    if not got:
        raise HTTPException(status_code=401, detail="Missing X-Admin-Token header.")
    if not secrets.compare_digest(got.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid admin token.")


@public_router.get("/virus-trends")
def get_virus_trends():
    raw = load_latest()
    if not raw:
        body = _default_payload()
    else:
        body = raw
        viruses = body.get("viruses")
        if not isinstance(viruses, list) or len(viruses) == 0:
            body = {**body, "viruses": [dict(v) for v in _DEFAULT_VIRUSES]}
    return JSONResponse(content=body, headers=_NO_STORE_HEADERS)


@admin_router.post("/admin/virus-trends/refresh")
def post_admin_virus_trends_refresh(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _verify_admin_token(x_admin_token)
    code, msg = run_virus_trends_refresh()
    if code != 0:
        logger.warning("admin virus-trends refresh failed: %s", msg)
        return JSONResponse(
            status_code=502,
            content={"ok": False, "detail": msg},
            headers=_NO_STORE_HEADERS,
        )
    # Omit snapshot body: avoids loading JSON from disk again and duplicating a large dict in the
    # response (saves RSS on small Render instances). Clients use GET /virus-trends after refresh.
    return JSONResponse(
        content={"ok": True, "message": msg},
        headers=_NO_STORE_HEADERS,
    )
