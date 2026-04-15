"""Latest virus-trends snapshot: Postgres row on Render (shared with web); file on local SQLite."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.settings import settings

log = logging.getLogger(__name__)

VANCOUVER = ZoneInfo("America/Vancouver")

_SINGLETON_ID = 1


def _is_sqlite() -> bool:
    return settings.database_url.strip().lower().startswith("sqlite")


def _data_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "virus_trends_latest.json"


def vancouver_checked_at_iso() -> str:
    """ISO-8601 with Vancouver offset so clients can display accurately."""
    return datetime.now(VANCOUVER).replace(microsecond=0).isoformat()


def _fingerprint(body: dict[str, Any]) -> tuple[Any, ...]:
    rk = body.get("ranking")
    if isinstance(rk, list) and rk:
        rank_fp = tuple(
            (
                r.get("key"),
                r.get("severity_label"),
                r.get("severity_score"),
            )
            for r in rk
            if isinstance(r, dict)
        )
    else:
        rank_fp = tuple((v.get("key"), v.get("level")) for v in body.get("viruses") or [])
    return (
        body.get("source_report_date"),
        rank_fp,
        body.get("summary"),
        body.get("levels_method"),
    )


def _load_latest_db() -> dict[str, Any] | None:
    from app.database import SessionLocal
    from app.models.virus_trends_latest import VirusTrendsLatest

    with SessionLocal() as db:
        row = db.get(VirusTrendsLatest, _SINGLETON_ID)
        if row is None:
            return None
        try:
            return json.loads(row.body_json)
        except json.JSONDecodeError:
            log.warning("virus_trends_latest row has invalid JSON")
            return None


def _save_latest_db(payload: dict[str, Any]) -> None:
    from app.database import SessionLocal
    from app.models.virus_trends_latest import VirusTrendsLatest

    raw = json.dumps(payload, ensure_ascii=False)
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        row = db.get(VirusTrendsLatest, _SINGLETON_ID)
        if row is None:
            db.add(VirusTrendsLatest(id=_SINGLETON_ID, body_json=raw, updated_at=now))
        else:
            row.body_json = raw
            row.updated_at = now
        db.commit()
    log.info("Wrote virus trends to virus_trends_latest (database)")


def load_latest() -> dict[str, Any] | None:
    if not _is_sqlite():
        return _load_latest_db()
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
    if not _is_sqlite():
        _save_latest_db(payload)
        return
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
    Always set checked_at to now. If scientific fingerprint unchanged vs previous,
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
