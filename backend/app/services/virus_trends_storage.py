"""File-backed persistence for the latest virus trends snapshot (no database)."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

VANCOUVER = ZoneInfo("America/Vancouver")


def _data_path() -> Path:
    # backend/app/services -> parents[2] == backend/
    return Path(__file__).resolve().parents[2] / "data" / "virus_trends_latest.json"


def vancouver_checked_at_iso() -> str:
    """ISO-8601 with Vancouver offset so clients can display accurately."""
    return datetime.now(VANCOUVER).replace(microsecond=0).isoformat()


def _fingerprint(body: dict[str, Any]) -> tuple[Any, ...]:
    return (
        body.get("source_report_date"),
        tuple((v.get("key"), v.get("level")) for v in body.get("viruses") or []),
        body.get("summary"),
        body.get("levels_method"),
    )


def load_latest() -> dict[str, Any] | None:
    p = _data_path()
    if not p.is_file():
        return None
    try:
        with p.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Could not read %s: %s", p, e)
        return None


def save_latest(payload: dict[str, Any]) -> None:
    p = _data_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(p)
    log.info("Wrote virus trends to %s", p)


def merge_and_save_after_fetch(fresh_content: dict[str, Any]) -> dict[str, Any]:
    """
    Always set checked_at to now. If scientific fingerprint unchanged vs previous file,
    keep prior source_report_date / viruses / summary / etc. but still refresh checked_at.
    If changed, use fresh_content for those fields.
    """
    checked = vancouver_checked_at_iso()
    prev = load_latest()

    new_fp = _fingerprint(fresh_content)
    if prev:
        prev_body = {k: v for k, v in prev.items() if k != "checked_at"}
        if _fingerprint(prev_body) == new_fp:
            merged = {**prev, "checked_at": checked}
            log.info("Virus trends content unchanged; updated checked_at only.")
            save_latest(merged)
            return merged

    merged = {**fresh_content, "checked_at": checked}
    save_latest(merged)
    return merged
