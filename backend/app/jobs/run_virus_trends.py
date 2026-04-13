"""
Refresh virus-trends JSON on disk (PHAC + BCCDC fetch). Run as a Render **cron** job so the
web dyno is not woken to do heavy HTTP + aggregation — avoids OOM spikes on 512MB instances.

    python3 -m app.jobs.run_virus_trends
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[2]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.database import Base, engine
from app.models import VirusTrendsLatest  # noqa: F401 — register model for create_all
from app.services.virus_trends_refresh import run_virus_trends_refresh

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("littlebuggy.virus_trends_job")


def main() -> int:
    # Ensure virus_trends_latest exists when cron uses Postgres (web service may not have started yet).
    Base.metadata.create_all(bind=engine)
    code, msg = run_virus_trends_refresh()
    if code != 0:
        log.error("virus-trends refresh failed: %s", msg)
        return code
    log.info("virus-trends refresh OK: %s", msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
