"""
Latest snapshot row for ``GET /api/homepage-summary`` (Metro Vancouver only).

Memory (Render 512MB): no live fetch/polish in this handler — that duplicated PHAC + AQHI +
weather work per request and spiked RSS. Snapshots come from cron/admin; the static site falls
back to ``public/data/homepage-summary.json`` when this returns 503.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.settings import postgres_required_message_if_misconfigured
from app.database import get_db
from app.schemas.homepage import HomepageSummaryResponse
from app.services.homepage_response_map import trend_snapshot_row_to_response
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row

router = APIRouter()

_VANCOUVER_CITY_ID = "vancouver"


@router.get("/homepage-summary", response_model=HomepageSummaryResponse)
def homepage_summary(
    db: Session = Depends(get_db),
) -> HomepageSummaryResponse:
    """Latest Vancouver snapshot from ``trend_snapshots`` only (precomputed by cron or admin)."""
    mis = postgres_required_message_if_misconfigured()
    if mis:
        raise HTTPException(status_code=503, detail=mis)

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
