"""
Lightweight schema bumps for SQLite + PostgreSQL without Alembic (V1).
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

_TREND_SNAPSHOT_COLUMNS = [
    ("weather_summary", "TEXT"),
    ("sources_json", "TEXT"),
    ("data_quality_note", "TEXT"),
]


def ensure_trend_snapshot_columns(engine: Engine) -> None:
    insp = inspect(engine)
    if not insp.has_table("trend_snapshots"):
        return
    existing = {c["name"] for c in insp.get_columns("trend_snapshots")}
    with engine.begin() as conn:
        for col, ddl in _TREND_SNAPSHOT_COLUMNS:
            if col in existing:
                continue
            conn.execute(text(f"ALTER TABLE trend_snapshots ADD COLUMN {col} {ddl}"))
            log.info("Added column trend_snapshots.%s", col)
