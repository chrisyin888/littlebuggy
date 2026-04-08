"""
Nightly (or on-demand) refresh of public respiratory virus trend JSON.

From the ``backend/`` directory:

    python3 -m app.jobs.refresh_virus_trends

Schedule target: 11:30 PM America/Vancouver. Render cron uses UTC (see ``render.yaml``);
PDT 23:30 ≈ 06:30 UTC the next calendar day. Standard time differs by one hour — adjust if needed.

On Render, the web service and a separate Cron job do not share a filesystem. Use
``POST /api/admin/virus-trends/refresh`` with ``X-Admin-Token`` (same secret as homepage admin)
from a curl-based cron, or run this script only where it shares disk with the API process.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[2]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.services.virus_trends_refresh import run_virus_trends_refresh

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger("littlebuggy.virus_trends")


def main() -> int:
    code, msg = run_virus_trends_refresh()
    if code == 0:
        log.info("%s", msg)
    else:
        log.error("%s", msg)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
