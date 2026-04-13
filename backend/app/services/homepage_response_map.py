"""
Map homepage summary payloads / DB rows to ``HomepageSummaryResponse`` (single code path for GET /api/homepage-summary).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.models.trend_snapshot import TrendSnapshot
from app.schemas.homepage import (
    HomepageSummaryResponse,
    SourceMeta,
    SourcesBundle,
    WeatherDisplayPayload,
)

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


def _parse_weather_display(raw: Any) -> WeatherDisplayPayload | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
    else:
        return None
    try:
        return WeatherDisplayPayload.model_validate(data)
    except Exception:
        return None


def _parse_sources(raw: Any) -> SourcesBundle:
    if raw is None:
        return _FALLBACK_SOURCES
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
        except Exception:
            return _FALLBACK_SOURCES
        if not isinstance(data, dict):
            return _FALLBACK_SOURCES
    else:
        return _FALLBACK_SOURCES
    try:
        return SourcesBundle(
            respiratory=SourceMeta(**data["respiratory"]),
            aqhi=SourceMeta(**data["aqhi"]),
            weather=SourceMeta(**data["weather"]),
        )
    except Exception:
        return _FALLBACK_SOURCES


def homepage_summary_blob_to_response(blob: dict[str, Any]) -> HomepageSummaryResponse:
    """
    One mapping from a normalized blob (DB row fields or live payload dict) to the API model.

    Expected keys overlap both shapes: city_id, region, rsv/flu/covid (or rsv_level-style via aliases below),
    air_quality, weather, weather_display, outdoor_feel, summary/short_summary, updated_at, sources, data_quality_note.
    """
    cid_raw = blob.get("city_id")
    cid = str(cid_raw or "vancouver").strip().lower() or "vancouver"

    region = str(blob.get("region") or "")

    rsv = str(blob.get("rsv") or blob.get("rsv_level") or "Unknown")
    flu = str(blob.get("flu") or blob.get("flu_level") or "Unknown")
    covid = str(blob.get("covid") or blob.get("covid_level") or "Unknown")
    air_quality = str(blob.get("air_quality") or blob.get("air_quality_level") or "Unavailable")
    weather = str(blob.get("weather") or blob.get("weather_summary") or "Unavailable")

    wd = blob.get("weather_display")
    if wd is None and blob.get("weather_display_json"):
        wd = blob.get("weather_display_json")
    weather_display = _parse_weather_display(wd)

    outdoor_feel = str(blob.get("outdoor_feel") or "Unavailable")
    summary = str(blob.get("summary") or blob.get("short_summary") or "")

    raw_u = blob.get("updated_at")
    updated_at: datetime
    if isinstance(raw_u, datetime):
        updated_at = raw_u
    elif isinstance(raw_u, str) and raw_u.strip():
        try:
            updated_at = datetime.fromisoformat(raw_u.strip().replace("Z", "+00:00"))
        except ValueError:
            updated_at = datetime.now(timezone.utc)
    else:
        updated_at = datetime.now(timezone.utc)

    src = blob.get("sources")
    if src is None and blob.get("sources_json"):
        src = blob.get("sources_json")
    sources = _parse_sources(src)

    dq = blob.get("data_quality_note")
    dq_out = dq.strip() if isinstance(dq, str) and dq.strip() else None

    return HomepageSummaryResponse(
        city_id=cid,
        region=region,
        rsv=rsv,
        flu=flu,
        covid=covid,
        air_quality=air_quality,
        weather=weather,
        weather_display=weather_display,
        outdoor_feel=outdoor_feel,
        summary=summary,
        updated_at=updated_at,
        sources=sources,
        data_quality_note=dq_out,
    )


def trend_snapshot_row_to_response(row: TrendSnapshot) -> HomepageSummaryResponse:
    """Thin wrapper: ORM row → blob → response."""
    cid = (row.city_id or "vancouver").strip().lower() or "vancouver"
    blob: dict[str, Any] = {
        "city_id": cid,
        "region": row.region,
        "rsv_level": row.rsv_level,
        "flu_level": row.flu_level,
        "covid_level": row.covid_level,
        "air_quality_level": row.air_quality_level,
        "weather_summary": row.weather_summary,
        "weather_display_json": row.weather_display_json,
        "outdoor_feel": row.outdoor_feel,
        "summary": row.summary_text,
        "updated_at": row.created_at,
        "sources_json": row.sources_json,
        "data_quality_note": row.data_quality_note,
    }
    return homepage_summary_blob_to_response(blob)
