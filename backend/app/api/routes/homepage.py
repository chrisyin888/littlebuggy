"""
Latest snapshot row for ``GET /api/homepage-summary``.

Accepts an optional ``?city=`` query parameter (e.g. ``vancouver``, ``gta``, ``calgary``).
Unknown or missing city → Vancouver (default). If no snapshot exists for the requested city,
falls back to Vancouver so the UI always gets a response.

Memory (Render 512MB): no live fetch/polish in this handler — snapshots come from cron/admin;
the static site falls back to ``public/data/homepage-summary.json`` when this returns 503.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.settings import postgres_required_message_if_misconfigured
from app.config.cities import resolve_city_id
from app.database import get_db
from app.schemas.homepage import HomepageSummaryResponse
from app.services.homepage_response_map import trend_snapshot_row_to_response
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row

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
