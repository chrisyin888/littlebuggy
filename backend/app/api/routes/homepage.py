"""
Latest snapshot row for ``GET /api/homepage-summary``.

Supports ``?city=vancouver|gta|calgary`` (default Vancouver). Reads the newest ``trend_snapshots`` row
for that ``city_id``; if none exists, builds a live payload (same pipeline as regenerate) so new cities work
without a separate bootstrap step.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config.cities import resolve_city_id
from app.config import postgres_required_message_if_misconfigured
from app.database import get_db
from app.models.trend_snapshot import TrendSnapshot
from app.schemas.homepage import (
    HomepageSummaryResponse,
    SourceMeta,
    SourcesBundle,
    WeatherDisplayPayload,
)
from app.services.homepage_static_generate import generate_homepage_summary_payload
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row

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


def _row_to_response(row: TrendSnapshot) -> HomepageSummaryResponse:
    cid = (row.city_id or "vancouver").strip().lower() or "vancouver"
    return HomepageSummaryResponse(
        city_id=cid,
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


def _payload_to_response(payload: dict, city_id: str) -> HomepageSummaryResponse:
    wd_raw = payload.get("weather_display")
    weather_display = None
    if isinstance(wd_raw, dict):
        try:
            weather_display = WeatherDisplayPayload.model_validate(wd_raw)
        except Exception:
            weather_display = None

    src_in = payload.get("sources") if isinstance(payload.get("sources"), dict) else {}
    try:
        sources = SourcesBundle(
            respiratory=SourceMeta(**src_in["respiratory"]),
            aqhi=SourceMeta(**src_in["aqhi"]),
            weather=SourceMeta(**src_in["weather"]),
        )
    except Exception:
        sources = _FALLBACK_SOURCES

    raw_u = payload.get("updated_at")
    updated_at = datetime.now(timezone.utc)
    if isinstance(raw_u, str) and raw_u.strip():
        try:
            updated_at = datetime.fromisoformat(raw_u.strip().replace("Z", "+00:00"))
        except ValueError:
            pass

    dq = payload.get("data_quality_note")
    dq_out = dq.strip() if isinstance(dq, str) and dq.strip() else None

    return HomepageSummaryResponse(
        city_id=city_id,
        region=str(payload.get("region") or ""),
        rsv=str(payload.get("rsv") or "Unknown"),
        flu=str(payload.get("flu") or "Unknown"),
        covid=str(payload.get("covid") or "Unknown"),
        air_quality=str(payload.get("air_quality") or "Unavailable"),
        weather=str(payload.get("weather") or "Unavailable"),
        weather_display=weather_display,
        outdoor_feel=str(payload.get("outdoor_feel") or "Unavailable"),
        summary=str(payload.get("summary") or payload.get("short_summary") or ""),
        updated_at=updated_at,
        sources=sources,
        data_quality_note=dq_out,
    )


@router.get("/homepage-summary", response_model=HomepageSummaryResponse)
def homepage_summary(
    city: str | None = Query(
        None,
        description="City id: vancouver (default), gta, calgary",
    ),
    db: Session = Depends(get_db),
) -> HomepageSummaryResponse:
    """Latest snapshot for one city, or a live-built payload when no DB row exists yet."""
    mis = postgres_required_message_if_misconfigured()
    if mis:
        raise HTTPException(status_code=503, detail=mis)

    profile = resolve_city_id(city)
    row = get_latest_homepage_snapshot_row(db, profile.id)
    if row is not None:
        return _row_to_response(row)

    try:
        payload, _warnings = generate_homepage_summary_payload(city_id=profile.id)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not build homepage summary for city={profile.id}: {e}",
        ) from e

    return _payload_to_response(payload, profile.id)

