"""
Map homepage summary payloads / DB rows to ``HomepageSummaryResponse`` (single code path for GET /api/homepage-summary).

Signals are derived from the dynamic ``respiratory_ranking`` array (severity-sorted).
Legacy rsv/flu/covid fields are preserved for backward compatibility but are no longer
the source of truth — ``signals[]`` is the preferred output.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from app.config.pathogen_catalog import get_display_label, get_symptom_display
from app.models.trend_snapshot import TrendSnapshot
from app.schemas.homepage import (
    HomepageSignal,
    HomepageSummaryResponse,
    RespiratoryRankingEntry,
    SourceMeta,
    SourcesBundle,
    WeatherDisplayPayload,
)


def _split_level_trend(raw: str) -> tuple[str, str | None]:
    s = (raw or "").strip()
    if not s:
        return "Unknown", None
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, None


def _default_label_for_key(key: str) -> str:
    """Delegate to catalog (title-case fallback for unknown keys)."""
    return get_display_label(key)


def _enrich_signal_with_symptoms(signal: HomepageSignal) -> HomepageSignal:
    """Inject reviewed symptom info from pathogen catalog into a HomepageSignal."""
    info = get_symptom_display(signal.key, signal.label)
    return HomepageSignal(
        key=signal.key,
        label=signal.label,
        level=signal.level,
        trend=signal.trend,
        symptoms=info["symptoms"],
        symptom_disclaimer=info["disclaimer"],
        symptom_fallback_message=info["fallback_message"],
    )


def _signals_from_ranking(ranking: list[RespiratoryRankingEntry]) -> list[HomepageSignal]:
    """
    Build HomepageSignal list from the severity-sorted ranking.

    Ranking is already ordered (highest severity first) so we preserve that order
    rather than re-sorting by hardcoded key names. New pathogens from the PHAC feed
    appear automatically without any code changes.
    """
    out: list[HomepageSignal] = []
    for entry in ranking:
        level, trend = _split_level_trend(entry.severity_label)
        sig = HomepageSignal(
            key=entry.key,
            label=entry.display_name or _default_label_for_key(entry.key),
            level=level,
            trend=trend,
        )
        out.append(_enrich_signal_with_symptoms(sig))
    return out


def _signals_from_dynamic_list(raw_list: list[Any]) -> list[HomepageSignal] | None:
    """Parse signals array from a blob (API payload / static JSON)."""
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
        sig = HomepageSignal(key=k, label=label, level=level, trend=trend)
        out.append(_enrich_signal_with_symptoms(sig))
    return out if out else None


def _parse_respiratory_ranking_list(raw: Any) -> list[RespiratoryRankingEntry]:
    if not isinstance(raw, list):
        return []
    out: list[RespiratoryRankingEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            ua = item.get("updated_at")
            if isinstance(ua, datetime):
                uat = ua
            elif isinstance(ua, str) and ua.strip():
                uat = datetime.fromisoformat(ua.strip().replace("Z", "+00:00"))
            else:
                uat = datetime.now(timezone.utc)
            val = item.get("value")
            vf: float | None
            if val is None:
                vf = None
            else:
                try:
                    vf = float(val)
                except (TypeError, ValueError):
                    vf = None
            # Use catalog label if API omits display_name
            key = str(item.get("key") or "").strip().lower() or "unknown"
            display = str(item.get("display_name") or item.get("key") or "").strip()
            if not display:
                display = _default_label_for_key(key)
            out.append(
                RespiratoryRankingEntry(
                    key=key,
                    display_name=display,
                    value=vf,
                    severity_label=str(item.get("severity_label") or "Unknown"),
                    severity_score=float(item.get("severity_score") or 0.0),
                    updated_at=uat,
                )
            )
        except Exception:
            continue
    return out


def build_signals_from_blob(blob: dict[str, Any]) -> list[HomepageSignal]:
    """
    Build the ``signals`` array for the API response.

    Priority order:
    1. ``blob['signals']`` — explicit signals array (pre-sorted by severity)
    2. ``blob['respiratory_ranking']`` — derive signals from the ranking (preferred path)
    3. Legacy ``rsv``/``flu``/``covid`` fields — backward-compat fallback only

    Signals preserve the ranking's severity sort order; no hardcoded key ordering.
    """
    # 1. Explicit signals array (e.g. from a cached blob that already has signals)
    raw = blob.get("signals")
    if isinstance(raw, list) and len(raw) > 0:
        parsed = _signals_from_dynamic_list(raw)
        if parsed is not None:
            return parsed

    # 2. Derive from respiratory_ranking (dynamic, severity-sorted)
    rr = blob.get("respiratory_ranking")
    if isinstance(rr, list) and len(rr) > 0:
        ranking_entries = _parse_respiratory_ranking_list(rr)
        if ranking_entries:
            return _signals_from_ranking(ranking_entries)

    # 3. Legacy fallback: rsv / flu / covid fixed triple
    legacy_keys = [
        ("rsv", blob.get("rsv") or blob.get("rsv_level")),
        ("flu", blob.get("flu") or blob.get("flu_level")),
        ("covid", blob.get("covid") or blob.get("covid_level")),
    ]
    built: list[HomepageSignal] = []
    for key, raw_level in legacy_keys:
        level_s = str(raw_level or "").strip() or "Unknown"
        lev, trend = _split_level_trend(level_s)
        sig = HomepageSignal(
            key=key,
            label=_default_label_for_key(key),
            level=lev,
            trend=trend,
        )
        built.append(_enrich_signal_with_symptoms(sig))
    return built


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
    air_quality, weather, weather_display, outdoor_feel, summary/short_summary, updated_at, sources,
    data_quality_note, respiratory_ranking.
    """
    cid_raw = blob.get("city_id")
    cid = str(cid_raw or "vancouver").strip().lower() or "vancouver"

    region = str(blob.get("region") or "")

    # Legacy fields — kept for backward compat; prefer signals[] for all new consumers
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

    respiratory_ranking = _parse_respiratory_ranking_list(blob.get("respiratory_ranking"))
    signals = build_signals_from_blob(blob)

    return HomepageSummaryResponse(
        city_id=cid,
        region=region,
        signals=signals,
        respiratory_ranking=respiratory_ranking,
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
    rr: list[Any] = []
    raw_r = getattr(row, "respiratory_ranking_json", None)
    if raw_r:
        try:
            loaded = json.loads(raw_r)
            if isinstance(loaded, list):
                rr = loaded
        except Exception:
            rr = []
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
        "respiratory_ranking": rr,
    }
    return homepage_summary_blob_to_response(blob)
