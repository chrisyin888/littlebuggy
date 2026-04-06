"""
Daily job: AQHI + weather; reuse last snapshot for respiratory levels.

    python3 -m app.jobs.run_daily_environment
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[2]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import TrendSnapshot
from app.services.db_schema import ensure_trend_snapshot_columns
from app.services.snapshot_pipeline import run_snapshot_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger("littlebuggy.daily_env")


def main(region: str = "Metro Vancouver") -> int:
    Base.metadata.create_all(bind=engine)
    ensure_trend_snapshot_columns(engine)
    db = SessionLocal()
    try:
        has_row = db.scalars(select(TrendSnapshot).limit(1)).first() is not None
        # First deploy: environment-only would leave virus levels as "Unknown" with no prior row.
        if not has_row:
            log.info("No prior snapshot — running full pipeline once for bootstrap.")
            return run_snapshot_job(db, region=region, mode="full")
        return run_snapshot_job(db, region=region, mode="environment_only")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"OK — snapshot id={main()}")
