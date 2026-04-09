"""GET /api/status — lightweight operator / frontend health for the data pipeline."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import postgres_required_message_if_misconfigured
from app.database import get_db
from app.schemas.status import SourceHealth, SystemStatusResponse
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row

router = APIRouter()


def _source_health(blob: dict | None, key: str) -> SourceHealth:
    if not blob or key not in blob:
        return SourceHealth(present=False, status=None, ok=False)
    block = blob[key] or {}
    status = block.get("status")
    ok = status == "ok"
    return SourceHealth(present=True, status=status, ok=ok)


@router.get("/status", response_model=SystemStatusResponse)
def system_status(db: Session = Depends(get_db)) -> SystemStatusResponse:
    """
    Summarizes the latest `trend_snapshots` row: timestamps, source OK flags, and
    whether the homepage payload can be served.
    """
    mis = postgres_required_message_if_misconfigured()
    if mis:
        dead = SourceHealth(present=False, status=None, ok=False)
        return SystemStatusResponse(
            database_ok=False,
            last_snapshot_at=None,
            homepage_summary_ready=False,
            respiratory=dead,
            environment=dead,
            aqhi=dead,
            weather=dead,
            message=mis,
        )

    try:
        row = get_latest_homepage_snapshot_row(db, "vancouver")
    except Exception:
        return SystemStatusResponse(
            database_ok=False,
            last_snapshot_at=None,
            homepage_summary_ready=False,
            respiratory=SourceHealth(present=False, status=None, ok=False),
            environment=SourceHealth(present=False, status=None, ok=False),
            aqhi=SourceHealth(present=False, status=None, ok=False),
            weather=SourceHealth(present=False, status=None, ok=False),
            message="Database query failed — check DATABASE_URL and connectivity.",
        )

    if row is None:
        return SystemStatusResponse(
            database_ok=True,
            last_snapshot_at=None,
            homepage_summary_ready=False,
            respiratory=SourceHealth(present=False, status=None, ok=False),
            environment=SourceHealth(present=False, status=None, ok=False),
            aqhi=SourceHealth(present=False, status=None, ok=False),
            weather=SourceHealth(present=False, status=None, ok=False),
            message=(
                "No snapshots yet in trend_snapshots. POST /api/admin/homepage-snapshot/regenerate "
                "(X-Admin-Token), or: python3 -m app.jobs.run_update"
            ),
        )

    blob: dict | None = None
    if row.sources_json:
        try:
            blob = json.loads(row.sources_json)
        except Exception:
            blob = None

    r = _source_health(blob, "respiratory")
    a = _source_health(blob, "aqhi")
    w = _source_health(blob, "weather")
    env_ok = a.ok and w.ok

    return SystemStatusResponse(
        database_ok=True,
        last_snapshot_at=row.created_at,
        homepage_summary_ready=True,
        respiratory=r,
        environment=SourceHealth(present=a.present and w.present, status=None, ok=env_ok),
        aqhi=a,
        weather=w,
        message=None,
    )
