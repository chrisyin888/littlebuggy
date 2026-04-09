"""
Homepage API ↔ ``trend_snapshots`` (``TrendSnapshot`` model).

``GET /api/homepage-summary`` and ``POST .../homepage-snapshot/regenerate`` use the same
``DATABASE_URL`` engine (see ``app.database``) and the same "latest row" query so admin writes
are visible immediately after commit.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trend_snapshot import TrendSnapshot
from app.services.save_snapshot import save_snapshot


def get_latest_homepage_snapshot_row(db: Session, city_id: str = "vancouver") -> TrendSnapshot | None:
    """Latest row for ``GET /api/homepage-summary`` for the given ``city_id``."""
    cid = (city_id or "vancouver").strip().lower() or "vancouver"
    return db.scalars(
        select(TrendSnapshot)
        .where(TrendSnapshot.city_id == cid)
        .order_by(TrendSnapshot.created_at.desc())
        .limit(1),
    ).first()


def persist_static_homepage_payload(db: Session, payload: dict[str, Any]) -> TrendSnapshot:
    """
    Insert one ``trend_snapshots`` row from the polished dict produced by
    ``generate_homepage_summary_payload`` (same shape as ``public/data/homepage-summary.json``).
    Commits inside ``save_snapshot``.
    """
    city_id = str(payload.get("city_id") or "vancouver").strip().lower() or "vancouver"
    region = str(payload.get("region") or "Metro Vancouver")
    virus_data = {
        "rsv": str(payload.get("rsv") or "Unknown"),
        "flu": str(payload.get("flu") or "Unknown"),
        "covid": str(payload.get("covid") or "Unknown"),
    }
    env_data = {
        "air_quality": str(payload.get("air_quality") or "Unavailable"),
        "weather": str(payload.get("weather") or "Unavailable"),
    }
    outdoor_feel = str(payload.get("outdoor_feel") or "Unavailable")
    summary_text = str(payload.get("summary") or payload.get("short_summary") or "").strip()
    if not summary_text:
        summary_text = "Summary unavailable."

    src = payload.get("sources")
    sources = src if isinstance(src, dict) else None

    dqn = payload.get("data_quality_note")
    if isinstance(dqn, str) and dqn.strip():
        data_quality_note: str | None = dqn.strip()
    else:
        data_quality_note = None

    wd = payload.get("weather_display")
    weather_display = wd if isinstance(wd, dict) else None

    return save_snapshot(
        db,
        city_id=city_id,
        region=region,
        virus_data=virus_data,
        env_data=env_data,
        outdoor_feel=outdoor_feel,
        summary_text=summary_text,
        sources=sources,
        data_quality_note=data_quality_note,
        weather_display=weather_display,
    )


def verify_row_readable_after_commit(db: Session, row_id: int) -> None:
    """
    Read-your-writes check on the same Session / connection pool after ``save_snapshot`` committed.
    Raises RuntimeError if the row is not visible (misconfigured DB, wrong schema, etc.).
    """
    found = db.scalars(select(TrendSnapshot).where(TrendSnapshot.id == row_id)).first()
    if found is None:
        raise RuntimeError(
            f"Inserted trend_snapshots id={row_id} is not visible in a follow-up SELECT. "
            "Confirm DATABASE_URL on this API process points at the same database you query for GET /api/homepage-summary."
        )
