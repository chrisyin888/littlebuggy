"""
Latest snapshot row for ``GET /api/homepage-summary``.

The production Vue bundle requests this first; Render crons refresh the underlying DB daily
(environment) and weekly (respiratory). If the API is unreachable, the client falls back to
bundled ``/data/homepage-summary.json`` (see ``src/lib/homepageSummary.js``).
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trend_snapshot import TrendSnapshot
from app.schemas.homepage import (
    HomepageSummaryResponse,
    SourceMeta,
    SourcesBundle,
    WeatherDisplayPayload,
)

router = APIRouter()

_FALLBACK_SOURCES = SourcesBundle(
    respiratory=SourceMeta(
        name="Not recorded",
        url="https://www.bccdc.ca/health-professionals/data-reports/respiratory-virus-data",
        refreshed_label=None,
        status="unknown",
    ),
    aqhi=SourceMeta(
        name="Environment and Climate Change Canada — MSC GeoMet (AQHI)",
        url="https://open.canada.ca/data/en/dataset/28936e1b-681f-4c73-b04a-e86d4b3917c6",
        refreshed_label=None,
        status="unknown",
    ),
    weather=SourceMeta(
        name="Open-Meteo",
        url="https://open-meteo.com/en/docs",
        refreshed_label=None,
        status="unknown",
    ),
)


def _parse_weather_display(raw: str | None) -> WeatherDisplayPayload | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return WeatherDisplayPayload.model_validate(data)
    except Exception:
        return None


def _parse_sources(raw: str | None) -> SourcesBundle:
    if not raw:
        return _FALLBACK_SOURCES
    try:
        data = json.loads(raw)
        return SourcesBundle(
            respiratory=SourceMeta(**data["respiratory"]),
            aqhi=SourceMeta(**data["aqhi"]),
            weather=SourceMeta(**data["weather"]),
        )
    except Exception:
        return _FALLBACK_SOURCES


@router.get("/homepage-summary", response_model=HomepageSummaryResponse)
def homepage_summary(db: Session = Depends(get_db)) -> HomepageSummaryResponse:
    """Latest automated snapshot for the LittleBuggy homepage."""
    row = db.scalars(select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(1)).first()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No snapshot yet. From backend/: python3 -m app.jobs.run_update",
        )
    return HomepageSummaryResponse(
        region=row.region,
        rsv=row.rsv_level,
        flu=row.flu_level,
        covid=row.covid_level,
        air_quality=row.air_quality_level,
        weather=row.weather_summary,
        weather_display=_parse_weather_display(row.weather_display_json),
        outdoor_feel=row.outdoor_feel,
        summary=row.summary_text,
        updated_at=row.created_at,
        sources=_parse_sources(row.sources_json),
        data_quality_note=row.data_quality_note,
    )
