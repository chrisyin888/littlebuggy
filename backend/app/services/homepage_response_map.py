"""
Map homepage summary payloads / DB rows to ``HomepageSummaryResponse`` (single code path for GET /api/homepage-summary).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from app.models.trend_snapshot import TrendSnapshot
from app.schemas.homepage import (
    HomepageSignal,
    HomepageSummaryResponse,
    SourceMeta,
    SourcesBundle,
    WeatherDisplayPayload,
)

# Stable ordering for known keys; unknown keys sort after, then alphabetically by key.
_SIGNAL_ORDER = ("rsv", "flu", "covid")

_DEFAULT_LABELS: dict[str, str] = {
    "rsv": "RSV",
    "flu": "Flu",
    "covid": "COVID-19",
}


def _split_level_trend(raw: str) -> tuple[str, str | None]:
    s = (raw or "").strip()
    if not s:
        return "Unknown", None
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, None


def _default_label_for_key(key: str) -> str:
    return _DEFAULT_LABELS.get(key, key.replace("_", " ").strip().title() or "Signal")


def _label_for_triple(blob: dict[str, Any], key: str, field: str) -> str:
    raw = blob.get(field)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return _default_label_for_key(key)


def _sort_signals(signals: list[HomepageSignal]) -> list[HomepageSignal]:
    def sort_key(s: HomepageSignal) -> tuple[int, str]:
        try:
            i = _SIGNAL_ORDER.index(s.key)
        except ValueError:
            i = len(_SIGNAL_ORDER)
        return (i, s.key)

    return sorted(signals, key=sort_key)


def _signals_from_dynamic_list(raw_list: list[Any]) -> list[HomepageSignal] | None:
    out: list[HomepageSignal] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        k = str(item.get("key") or "").strip().lower()
        if not k:
            continue
        label = str(item.get("label") or "").strip() or _default_label_for_key(k)
        level_raw = str(item.get("level") or "").strip() or "Unknown"
        trend_raw = item.get("trend")
        trend = str(trend_raw).strip() if trend_raw is not None and str(trend_raw).strip() else None
        if trend is not None:
            level, _ = _split_level_trend(level_raw)
        else:
            level, trend = _split_level_trend(level_raw)
        out.append(HomepageSignal(key=k, label=label, level=level, trend=trend))
    return out if out else None


def build_signals_from_blob(blob: dict[str, Any]) -> list[HomepageSignal]:
    """
    Preferred ``signals`` array for the API. Uses ``blob['signals']`` when present and valid;
    otherwise derives from legacy rsv/flu/covid (or *_level) fields.
    """
    raw = blob.get("signals")
    if isinstance(raw, list) and len(raw) > 0:
        parsed = _signals_from_dynamic_list(raw)
        if parsed is not None:
            return _sort_signals(parsed)

    triples: list[tuple[str, str, Any]] = [
        ("rsv", _label_for_triple(blob, "rsv", "rsv_label"), blob.get("rsv") or blob.get("rsv_level")),
        ("flu", _label_for_triple(blob, "flu", "flu_label"), blob.get("flu") or blob.get("flu_level")),
        ("covid", _label_for_triple(blob, "covid", "covid_label"), blob.get("covid") or blob.get("covid_level")),
    ]
    built: list[HomepageSignal] = []
    for key, label, raw_level in triples:
        level_s = str(raw_level or "").strip() or "Unknown"
        lev, trend = _split_level_trend(level_s)
        built.append(HomepageSignal(key=key, label=label, level=lev, trend=trend))
    return _sort_signals(built)

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

    signals = build_signals_from_blob(blob)

    return HomepageSummaryResponse(
        city_id=cid,
        region=region,
        signals=signals,
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
