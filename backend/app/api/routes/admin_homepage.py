"""
Protected trigger for homepage static JSON generation (optional).

Requires ``ADMIN_HOMEPAGE_TOKEN`` on the API. Does not use the database for homepage content.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.homepage_static_generate import (
    generate_homepage_summary_payload,
    sources_ok_count,
    write_homepage_summary_json,
)

router = APIRouter()


class HomepageSnapshotRegenerateResponse(BaseModel):
    ok: bool = True
    updated_at: str | None = None
    region: str | None = None
    sources_ok_count: int = Field(0, ge=0, le=3)
    short_summary_preview: str = ""
    warnings: list[str] = Field(default_factory=list)
    written_to_disk: bool = Field(
        False, description="HOMEPAGE_SUMMARY_OUTPUT_PATH was set and the write succeeded."
    )
    disk_write_configured: bool = Field(
        False, description="HOMEPAGE_SUMMARY_OUTPUT_PATH is set on the API."
    )
    output_path: str | None = None
    hint: str = ""


def _verify_admin_token(header_value: str | None) -> None:
    expected = (settings.admin_homepage_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin homepage regeneration is disabled (set ADMIN_HOMEPAGE_TOKEN on the API).",
        )
    got = (header_value or "").strip()
    if not got:
        raise HTTPException(status_code=401, detail="Missing X-Admin-Token header.")
    if not secrets.compare_digest(got.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid admin token.")


@router.post(
    "/admin/homepage-snapshot/regenerate",
    response_model=HomepageSnapshotRegenerateResponse,
)
def regenerate_homepage_snapshot(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict[str, Any]:
    """
    Run the same fetch + polish pipeline as ``npm run weekly:homepage`` / ``update_homepage_summary.py``.

    Optionally writes JSON when ``HOMEPAGE_SUMMARY_OUTPUT_PATH`` is set and the process can write there
    (typical: local dev). Hosted APIs usually cannot update your static CDN — use the preview in the
    response or run the script / CI.
    """
    _verify_admin_token(x_admin_token)

    payload, warnings = generate_homepage_summary_payload(region="Metro Vancouver")
    n_ok = sources_ok_count(payload)
    preview = (payload.get("short_summary") or "")[: 360]

    written = False
    out_path: str | None = None
    raw_path = (settings.homepage_summary_output_path or "").strip()
    disk_write_configured = bool(raw_path)

    if not disk_write_configured:
        hint = (
            "No disk path on the API: set HOMEPAGE_SUMMARY_OUTPUT_PATH in backend/.env if you want this "
            "button to overwrite public/data/homepage-summary.json on the machine running uvicorn "
            "(typical local dev). Otherwise use Download full JSON or npm run weekly:homepage, then commit."
        )
    else:
        hint = ""

    if raw_path:
        try:
            p = Path(raw_path)
            write_homepage_summary_json(p, payload)
            written = True
            out_path = str(p.resolve())
            hint = f"Snapshot JSON was written to: {out_path}"
        except OSError as e:
            hint = (
                f"HOMEPAGE_SUMMARY_OUTPUT_PATH is set but the file could not be written ({raw_path}): {e}"
            )
            warnings = [*warnings, f"disk_write_failed: {e}"]

    return {
        "ok": True,
        "updated_at": payload.get("updated_at"),
        "region": payload.get("region"),
        "sources_ok_count": n_ok,
        "short_summary_preview": preview,
        "warnings": warnings,
        "written_to_disk": written,
        "disk_write_configured": disk_write_configured,
        "output_path": out_path,
        "hint": hint,
    }


@router.post("/admin/homepage-snapshot/regenerate/raw")
def regenerate_homepage_snapshot_raw_json(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict[str, Any]:
    """Same auth as regenerate; returns the full payload for download / paste (large)."""
    _verify_admin_token(x_admin_token)
    payload, _warnings = generate_homepage_summary_payload(region="Metro Vancouver")
    return payload
