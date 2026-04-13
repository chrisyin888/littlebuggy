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

from app.database import Base, SessionLocal, engine
from app.jobs.db_runtime import exit_if_render_database_not_postgres
from app.services.db_schema import ensure_trend_snapshot_columns
from app.services.snapshot_pipeline import run_snapshot_job
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger("littlebuggy.daily_env")


def main() -> int:
    exit_if_render_database_not_postgres("run_daily_environment")
    Base.metadata.create_all(bind=engine)
    ensure_trend_snapshot_columns(engine)
    db = SessionLocal()
    try:
        has_row = get_latest_homepage_snapshot_row(db, "vancouver") is not None
        if not has_row:
            log.info("No prior Vancouver snapshot — running full pipeline once.")
            return run_snapshot_job(db, city_id="vancouver", mode="full")
        return run_snapshot_job(db, city_id="vancouver", mode="environment_only")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"OK — snapshot id={main()}")
