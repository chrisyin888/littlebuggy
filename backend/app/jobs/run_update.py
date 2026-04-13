"""
Full refresh: respiratory (BC wastewater API) + environment (AQHI, weather) → snapshot.

Correct invocation (working directory = `backend/`):

    python3 -m app.jobs.run_update
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[2]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.database import Base, SessionLocal, engine
from app.models import TrendSnapshot  # noqa: F401 — register model
from app.services.db_schema import ensure_trend_snapshot_columns
from app.services.snapshot_pipeline import run_snapshot_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("littlebuggy.update")


def run_update() -> int:
    Base.metadata.create_all(bind=engine)
    ensure_trend_snapshot_columns(engine)

    db = SessionLocal()
    try:
        sid = run_snapshot_job(db, city_id="vancouver", mode="full")
        log.info("Full snapshot id=%s (Metro Vancouver)", sid)
        return sid
    finally:
        db.close()


if __name__ == "__main__":
    snapshot_id = run_update()
    print(f"OK — snapshot id={snapshot_id}")
