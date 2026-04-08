#!/usr/bin/env python3
"""
Fetch public Metro Vancouver signals → parent-friendly copy → ``public/data/homepage-summary.json``.

This is the **offline generation** step only. The website does **not** re-fetch these APIs on each page load;
it only reads the JSON file produced here.

无数据库；浏览器端不调用本脚本。在仓库根目录运行：``npm run weekly:homepage``

Requires network. **Homepage JSON only** (no SQLAlchemy / Postgres):

  pip install -r scripts/requirements-homepage.txt

Full backend API development still uses ``backend/requirements.txt``.

The same pipeline is exposed as ``POST /api/admin/homepage-snapshot/regenerate`` when ``ADMIN_HOMEPAGE_TOKEN`` is set.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OUT = ROOT / "public" / "data" / "homepage-summary.json"


def _clip(s: str, n: int = 72) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def print_health(payload: dict[str, Any], fetch_warnings: list[str]) -> None:
    """Terminal-only snapshot health (not written to JSON)."""
    from app.services.homepage_static_generate import sources_ok_count

    print()
    print("── Homepage summary health check ──")
    print(f"  updated_at:   {payload.get('updated_at', '(missing)')}")
    print(f"  region:       {payload.get('region', '(missing)')}")
    print(f"  short_summary: {_clip(str(payload.get('short_summary', '')), 100)}")
    virus_ok = all(
        str(payload.get(k, "Unknown")).lower() not in ("", "unknown")
        for k in ("rsv", "flu", "covid")
    )
    env_ok = str(payload.get("air_quality", "")).lower() not in ("", "unavailable") and str(
        payload.get("weather", "")
    ).lower() not in ("", "unavailable")
    print(f"  virus cards:  {'OK' if virus_ok else 'partial/placeholder (Unknown)'}")
    print(f"  env cards:    {'OK' if env_ok else 'partial / placeholder'}")
    n_ok = sources_ok_count(payload)
    print(f"  sources:      {n_ok}/3 feeds marked ok in JSON")
    if payload.get("data_quality_note"):
        print(f"  note:         {_clip(str(payload['data_quality_note']), 90)}")
    if fetch_warnings:
        print()
        print("  Warnings (terminal only; see JSON status fields):")
        for w in fetch_warnings:
            print(f"    ! {w}")
    print("────────────────────────────────────")


def main() -> None:
    sys.path.insert(0, str(BACKEND))
    from app.services.homepage_static_generate import (
        generate_homepage_summary_payload,
        write_homepage_summary_json,
    )

    payload, fetch_warnings = generate_homepage_summary_payload(region="Metro Vancouver")

    write_homepage_summary_json(OUT, payload)
    print(f"Wrote {OUT}")
    print_health(payload, fetch_warnings)
    print()
    print("Next (weekly workflow):")
    print("  1. Preview:  npm run dev     (or: npm run build && npm run preview)")
    print("  2. Ship:     git add public/data/homepage-summary.json && git commit -m \"Update homepage summary\" && git push")
    print("  3. Deploy your static site so dist/data/homepage-summary.json is live.")


if __name__ == "__main__":
    main()
