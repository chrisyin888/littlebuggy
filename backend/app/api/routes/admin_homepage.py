"""
Protected trigger for homepage snapshot generation (optional).

Requires ``ADMIN_HOMEPAGE_TOKEN`` on the API. Runs the same fetch+polish pipeline as
``npm run weekly:homepage`` and **persists one ``trend_snapshots`` row** so
``GET /api/homepage-summary`` (production) serves the new data. Optional disk write
when ``HOMEPAGE_SUMMARY_OUTPUT_PATH`` is set.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import postgres_required_message_if_misconfigured, settings
from app.config.cities import resolve_city_id
from app.database import get_db
from app.models.trend_snapshot import TrendSnapshot
from app.services.homepage_static_generate import (
    generate_homepage_summary_payload,
    sources_ok_count,
    write_homepage_summary_json,
)
from app.services.trend_snapshot_homepage import (
    persist_static_homepage_payload,
    verify_row_readable_after_commit,
)

router = APIRouter()


class HomepageSnapshotRegenerateResponse(BaseModel):
    ok: bool = True
    updated_at: str | None = None
    region: str | None = None
    sources_ok_count: int = Field(0, ge=0, le=3)
    short_summary_preview: str = ""
    warnings: list[str] = Field(default_factory=list)
    persisted_to_database: bool = Field(
        False, description="A new trend_snapshots row was committed for GET /api/homepage-summary."
    )
    database_snapshot_id: int | None = None
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


def _persist_and_verify(db: Session, payload: dict[str, Any]) -> tuple[TrendSnapshot, str]:
    """
    Write one row to ``trend_snapshots`` and confirm it is readable on the same DB connection.

    Returns ``(row, updated_at_iso)`` where ``updated_at_iso`` matches what
    ``GET /api/homepage-summary`` exposes as ``updated_at`` (``row.created_at``).
    """
    try:
        row = persist_static_homepage_payload(db, payload)
        verify_row_readable_after_commit(db, row.id)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Could not persist homepage snapshot to table trend_snapshots: {e}. "
                "Check DATABASE_URL on this API service (Render: internal Postgres URL) and DB connectivity."
            ),
        ) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return row, row.created_at.isoformat()


@router.post(
    "/admin/homepage-snapshot/regenerate",
    response_model=HomepageSnapshotRegenerateResponse,
)
def regenerate_homepage_snapshot(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    city: str | None = Query(None, description="City id: vancouver, gta, calgary"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Run the same fetch + polish pipeline as ``npm run weekly:homepage`` / ``update_homepage_summary.py``.

    Inserts a new ``trend_snapshots`` row so production ``GET /api/homepage-summary`` updates immediately.

    Optionally writes JSON when ``HOMEPAGE_SUMMARY_OUTPUT_PATH`` is set and the process can write there
    (typical: local dev). Hosted APIs usually cannot update your static CDN — use the preview in the
    response or run the script / CI.
    """
    _verify_admin_token(x_admin_token)

    mis = postgres_required_message_if_misconfigured()
    if mis:
        raise HTTPException(status_code=503, detail=mis)

    profile = resolve_city_id(city)
    payload, warnings = generate_homepage_summary_payload(city_id=profile.id)
    n_ok = sources_ok_count(payload)
    preview = (payload.get("short_summary") or "")[: 360]

    row, updated_at_for_api = _persist_and_verify(db, payload)
    snap_id = row.id

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
        "updated_at": updated_at_for_api,
        "region": payload.get("region"),
        "sources_ok_count": n_ok,
        "short_summary_preview": preview,
        "warnings": warnings,
        "persisted_to_database": True,
        "database_snapshot_id": snap_id,
        "written_to_disk": written,
        "disk_write_configured": disk_write_configured,
        "output_path": out_path,
        "hint": hint,
    }


@router.post("/admin/homepage-snapshot/regenerate/raw")
def regenerate_homepage_snapshot_raw_json(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    city: str | None = Query(None, description="City id: vancouver, gta, calgary"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Same auth as regenerate; persists to ``trend_snapshots`` then returns the full JSON (large)."""
    _verify_admin_token(x_admin_token)

    mis = postgres_required_message_if_misconfigured()
    if mis:
        raise HTTPException(status_code=503, detail=mis)

    profile = resolve_city_id(city)
    payload, _warnings = generate_homepage_summary_payload(city_id=profile.id)
    row, updated_at_iso = _persist_and_verify(db, payload)
    out = dict(payload)
    out["updated_at"] = updated_at_iso
    return out
