"""GET /api/status — lightweight operator / frontend health for the data pipeline."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trend_snapshot import TrendSnapshot
from app.schemas.status import SourceHealth, SystemStatusResponse

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
    try:
        row = db.scalars(select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(1)).first()
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
            message="No snapshots yet. From backend/: python3 -m app.jobs.run_update (or run_weekly_respiratory, then run_daily_environment).",
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
