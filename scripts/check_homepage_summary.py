#!/usr/bin/env python3
"""Validate existing ``public/data/homepage-summary.json`` (no network). Used by ``npm run weekly:homepage:check``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "data" / "homepage-summary.json"

REQUIRED_KEYS = (
    "region",
    "rsv",
    "flu",
    "covid",
    "air_quality",
    "weather",
    "outdoor_feel",
    "updated_at",
    "sources",
    "short_summary",
)


def main() -> int:
    if not OUT.is_file():
        print(f"MISSING: {OUT}\nRun: npm run weekly:homepage")
        return 1
    try:
        data = json.loads(OUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"INVALID JSON: {e}")
        return 1
    if not isinstance(data, dict):
        print("INVALID: root must be an object")
        return 1
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        print(f"MISSING KEYS: {', '.join(missing)}")
        return 1
    src = data.get("sources")
    if not isinstance(src, dict) or not all(k in src for k in ("respiratory", "aqhi", "weather")):
        print("INVALID: sources.respiratory / aqhi / weather required")
        return 1
    print(f"OK — {data.get('updated_at')} · {data.get('region')}")
    print(f"     schema_version: {data.get('schema_version', '(unset)')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
