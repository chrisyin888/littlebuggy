"""
Weekly job: refresh BC respiratory wastewater signals only; reuse last snapshot for environment.

    python3 -m app.jobs.run_weekly_respiratory
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[2]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.database import Base, SessionLocal, engine
from app.models import TrendSnapshot  # noqa: F401
from app.services.db_schema import ensure_trend_snapshot_columns
from app.services.snapshot_pipeline import run_snapshot_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)


def main() -> int:
    Base.metadata.create_all(bind=engine)
    ensure_trend_snapshot_columns(engine)
    db = SessionLocal()
    try:
        return run_snapshot_job(db, city_id="vancouver", mode="respiratory_only")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"OK — snapshot id={main()}")
