"""
Latest snapshot row for ``GET /api/homepage-summary``.

Accepts an optional ``?city=`` query parameter (e.g. ``vancouver``, ``gta``, ``calgary``).
Unknown or missing city → Vancouver (default). If no snapshot exists for the requested city,
falls back to Vancouver so the UI always gets a response.

Memory (Render 512MB): no live fetch/polish in this handler — snapshots come from cron/admin;
the static site falls back to ``public/data/homepage-summary.json`` when this returns 503.
"""

import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.settings import postgres_required_message_if_misconfigured
from app.config.cities import resolve_city_id
from app.database import get_db
from app.models.trend_snapshot import TrendSnapshot
from app.schemas.homepage import HomepageSummaryResponse
from app.services.homepage_response_map import trend_snapshot_row_to_response
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row
from app.services.wastewater_signals import severity_score_from_label

router = APIRouter()

_VANCOUVER_CITY_ID = "vancouver"


@router.get("/homepage-summary", response_model=HomepageSummaryResponse)
def homepage_summary(
    city: str | None = Query(default=None, description="City id, e.g. 'vancouver', 'gta', 'calgary'"),
    db: Session = Depends(get_db),
) -> HomepageSummaryResponse:
    """Latest snapshot from ``trend_snapshots`` for the requested city (precomputed by cron or admin).
    Falls back to Vancouver if no snapshot exists for the requested city.
    """
    mis = postgres_required_message_if_misconfigured()
    if mis:
        raise HTTPException(status_code=503, detail=mis)

    city_profile = resolve_city_id(city)
    row = get_latest_homepage_snapshot_row(db, city_profile.id)

    # Graceful fallback: if no snapshot for the requested city, try Vancouver
    if row is None and city_profile.id != _VANCOUVER_CITY_ID:
        row = get_latest_homepage_snapshot_row(db, _VANCOUVER_CITY_ID)

    if row is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Homepage snapshot not available yet. "
                "Use static homepage-summary.json or run cron / POST /api/admin/homepage-snapshot/regenerate."
            ),
        )
    return trend_snapshot_row_to_response(row)


_VANCOUVER_TZ = ZoneInfo("America/Vancouver")
# Note: first Render deploy of this endpoint failed on the platform side;
# the app boots and serves it fine locally (uvicorn, Python 3.12). Redeployed
# unchanged apart from this comment to retry the deploy.


def _split_level_trend(full: str) -> tuple[str, str | None]:
    t = (full or "").strip()
    if not t:
        return "Unknown", None
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", t)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return t, None


def _signals_for_snapshot_row(row: TrendSnapshot) -> list[dict]:
    """Per-pathogen levels for one snapshot row.

    Prefers the dynamic wastewater ``respiratory_ranking_json`` (same source as
    ``GET /api/homepage-summary`` signals); falls back to the legacy
    rsv/flu/covid level columns for older rows without ranking JSON.
    """
    raw = row.respiratory_ranking_json
    if raw:
        try:
            entries = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            entries = None
        if isinstance(entries, list) and entries:
            out: list[dict] = []
            for e in entries:
                if not isinstance(e, dict):
                    continue
                full = str(e.get("severity_label") or "")
                level, trend = _split_level_trend(full)
                score = e.get("severity_score")
                out.append(
                    {
                        "key": str(e.get("key") or ""),
                        "label": str(e.get("display_name") or e.get("key") or ""),
                        "level": level,
                        "trend": trend,
                        "severity_score": float(score)
                        if isinstance(score, (int, float))
                        else severity_score_from_label(full),
                    }
                )
            if out:
                return out
    legacy = [
        ("rsv", "RSV", row.rsv_level),
        ("flu", "Flu", row.flu_level),
        ("covid", "COVID-19", row.covid_level),
    ]
    out = []
    for key, label, full in legacy:
        full_s = str(full or "")
        level, trend = _split_level_trend(full_s)
        out.append(
            {
                "key": key,
                "label": label,
                "level": level,
                "trend": trend,
                "severity_score": severity_score_from_label(full_s),
            }
        )
    return out


def _recent_snapshot_days(db: Session, city_id: str, days: int) -> list[TrendSnapshot]:
    """Latest snapshot row per Vancouver calendar day, oldest → newest."""
    rows = db.scalars(
        select(TrendSnapshot)
        .where(TrendSnapshot.city_id == city_id)
        .order_by(TrendSnapshot.created_at.desc())
        .limit(60)
    ).all()
    by_date: dict[str, TrendSnapshot] = {}
    for row in rows:
        created = row.created_at
        if created is None:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=ZoneInfo("UTC"))
        day = created.astimezone(_VANCOUVER_TZ).date().isoformat()
        if day not in by_date:
            by_date[day] = row
        if len(by_date) >= days:
            break
    return [by_date[d] for d in sorted(by_date)]


@router.get("/homepage-trend-history")
def homepage_trend_history(
    city: str | None = Query(default=None, description="City id, e.g. 'vancouver', 'gta', 'calgary'"),
    days: int = Query(default=7, ge=2, le=14, description="Number of snapshot days to return."),
    db: Session = Depends(get_db),
):
    """Recent daily respiratory levels from stored ``trend_snapshots`` rows.

    Read-only over snapshots the existing crons already persist — one entry per
    Vancouver calendar day (latest run of that day), oldest first. Powers the
    homepage 7-day trend strip with real saved levels instead of a placeholder.
    """
    mis = postgres_required_message_if_misconfigured()
    if mis:
        raise HTTPException(status_code=503, detail=mis)

    city_profile = resolve_city_id(city)
    picked = _recent_snapshot_days(db, city_profile.id, days)
    used_city = city_profile.id
    if not picked and city_profile.id != _VANCOUVER_CITY_ID:
        picked = _recent_snapshot_days(db, _VANCOUVER_CITY_ID, days)
        used_city = _VANCOUVER_CITY_ID

    out_days = []
    for row in picked:
        created = row.created_at
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=ZoneInfo("UTC"))
        day = (
            created.astimezone(_VANCOUVER_TZ).date().isoformat()
            if created is not None
            else None
        )
        out_days.append({"date": day, "signals": _signals_for_snapshot_row(row)})

    return {
        "city_id": used_city,
        "region": picked[-1].region if picked else city_profile.name,
        "days": out_days,
    }
