"""
Build the polished homepage summary dict (same pipeline as ``scripts/update_homepage_summary.py``).

No database. Used by the CLI script and the optional admin API route.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config.cities import resolve_city_id
from app.services.homepage_public_polish import polish_homepage_summary_payload
from app.services.homepage_summary_builder import (
    build_emergency_payload,
    build_homepage_summary_dict,
)

HOMEPAGE_SUMMARY_SCHEMA_VERSION = 1


def _clip(s: str, n: int = 72) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def generate_homepage_summary_payload(*, city_id: str | None = None) -> tuple[dict[str, Any], list[str]]:
    """
    Fetch public feeds, polish, attach ``schema_version``.

    ``city_id`` matches ``app.config.cities`` (default Vancouver).

    Returns ``(payload, fetch_warnings)``. Warnings are operator-facing only.
    """
    city = resolve_city_id(city_id)
    fetch_warnings: list[str] = []
    try:
        raw, fetch_warnings = build_homepage_summary_dict(city=city)
    except Exception as e:
        raw = build_emergency_payload(city=city)
        fetch_warnings.append(f"full_merge_failed: {e}")

    try:
        payload = polish_homepage_summary_payload(raw)
    except Exception as e:
        payload = dict(raw)
        payload.setdefault("short_summary", _clip(str(raw.get("summary", "")), 400))
        payload.setdefault("live_vs_illustrative_note", "")
        fetch_warnings.append(f"polish_failed: {e}")

    payload["schema_version"] = HOMEPAGE_SUMMARY_SCHEMA_VERSION
    return payload, fetch_warnings


def write_homepage_summary_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sources_ok_count(payload: dict[str, Any]) -> int:
    src = payload.get("sources") or {}
    return sum(
        1
        for k in ("respiratory", "aqhi", "weather")
        if isinstance(src.get(k), dict) and src[k].get("status") == "ok"
    )
