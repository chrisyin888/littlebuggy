"""
Build the homepage summary dict from live public fetches only.

No SQLAlchemy, no database, no snapshot persistence. Used by ``scripts/update_homepage_summary.py``
and (for source metadata shape) by ``snapshot_pipeline.run_snapshot_job`` via ``build_sources_bundle``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from app.services.build_summary import build_summary
from app.services.fetch_aqhi_real import fetch_aqhi_metro_vancouver
from app.services.fetch_bccdc_real import (
    PHAC_INFOBASE_API_LANDING,
    fetch_respiratory_bc_signals,
)
from app.services.fetch_weather_real import fetch_weather_vancouver, weather_display_dict

log = logging.getLogger("littlebuggy.homepage_builder")

DEFAULT_RESP_NAME = "Public Health Agency of Canada — Health Infobase (wastewater, BC)"
DEFAULT_AQHI_NAME = "Environment and Climate Change Canada — MSC GeoMet (AQHI)"
DEFAULT_WX_NAME = "Open-Meteo (forecast API, current)"


def _failed_respiratory(exc: str) -> Any:
    return SimpleNamespace(
        ok=False,
        virus={"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"},
        source_name=DEFAULT_RESP_NAME,
        source_url=PHAC_INFOBASE_API_LANDING,
        source_updated_label=None,
        error=exc,
    )


def _failed_aqhi(exc: str) -> Any:
    return SimpleNamespace(
        ok=False,
        air_quality="Unavailable",
        source_name=DEFAULT_AQHI_NAME,
        source_url="https://open.canada.ca/data/en/dataset/28936e1b-681f-4c73-b04a-e86d4b3917c6",
        source_updated_label=None,
        error=exc,
    )


def _failed_weather(exc: str) -> Any:
    return SimpleNamespace(
        ok=False,
        weather_summary="Unavailable",
        source_name=DEFAULT_WX_NAME,
        source_url="https://open-meteo.com/en/docs",
        source_updated_label=None,
        error=exc,
    )


def build_sources_bundle(resp: Any, aqhi: Any, wx: Any) -> dict[str, Any]:
    """Plain dict for JSON storage + API response (matches prior ``_build_sources`` shape)."""

    def pack(bundle: Any, fallback_name: str, fallback_url: str) -> dict[str, Any]:
        ok = getattr(bundle, "ok", False)
        return {
            "name": getattr(bundle, "source_name", fallback_name),
            "url": getattr(bundle, "source_url", fallback_url),
            "refreshed_label": getattr(bundle, "source_updated_label", None),
            "status": "ok" if ok else "error",
        }

    return {
        "respiratory": {
            "name": resp.source_name,
            "url": resp.source_url,
            "refreshed_label": resp.source_updated_label,
            "status": "ok" if resp.ok else "error",
        },
        "aqhi": pack(aqhi, "AQHI", "https://open.canada.ca"),
        "weather": pack(wx, "Weather", "https://open-meteo.com"),
    }


def build_emergency_payload(*, region: str = "Metro Vancouver") -> dict[str, Any]:
    """Last-resort shape if the whole merge fails (still valid for the Vue normalizer)."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    resp = _failed_respiratory("merge_failed")
    aqhi = _failed_aqhi("merge_failed")
    wx = _failed_weather("merge_failed")
    virus = {"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"}
    env = {"air_quality": "Unavailable", "weather": "Unavailable"}
    built = build_summary(virus, env)
    return {
        "region": region,
        "rsv": virus["rsv"],
        "flu": virus["flu"],
        "covid": virus["covid"],
        "air_quality": env["air_quality"],
        "weather": env["weather"],
        "weather_display": None,
        "outdoor_feel": built["outdoor_feel"],
        "summary": built["summary_text"],
        "updated_at": now.isoformat().replace("+00:00", "Z"),
        "sources": build_sources_bundle(resp, aqhi, wx),
        "data_quality_note": "Snapshot build failed—re-run the weekly script when you can.",
    }


def build_homepage_summary_dict(*, region: str = "Metro Vancouver") -> tuple[dict[str, Any], list[str]]:
    """
    Fetch public feeds, merge, return payload for ``homepage-summary.json``.

    Returns ``(payload, fetch_warnings)``. Warnings are for the terminal only (not written to JSON).
    """
    warnings: list[str] = []

    try:
        resp = fetch_respiratory_bc_signals()
    except Exception as e:
        log.exception("Respiratory fetch raised: %s", e)
        warnings.append(f"respiratory: exception ({e})")
        resp = _failed_respiratory(str(e))

    try:
        aqhi = fetch_aqhi_metro_vancouver()
    except Exception as e:
        log.exception("AQHI fetch raised: %s", e)
        warnings.append(f"aqhi: exception ({e})")
        aqhi = _failed_aqhi(str(e))

    try:
        wx = fetch_weather_vancouver()
    except Exception as e:
        log.exception("Weather fetch raised: %s", e)
        warnings.append(f"weather: exception ({e})")
        wx = _failed_weather(str(e))

    if not resp.ok:
        warnings.append(f"respiratory: feed error ({getattr(resp, 'error', 'unknown')})")
    if not aqhi.ok:
        warnings.append(f"aqhi: feed error ({getattr(aqhi, 'error', 'unknown')})")
    if not wx.ok:
        warnings.append(f"weather: feed error ({getattr(wx, 'error', 'unknown')})")

    virus = resp.virus if resp.ok else {"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"}
    env = {
        "air_quality": aqhi.air_quality if aqhi.ok else "Unavailable",
        "weather": wx.weather_summary if wx.ok else "Unavailable",
    }
    weather_display = weather_display_dict(wx) if wx.ok else None
    sources = build_sources_bundle(resp, aqhi, wx)
    notes: list[str] = []
    if not resp.ok:
        notes.append(f"Respiratory: {getattr(resp, 'error', 'fetch failed')}.")
    if not aqhi.ok:
        notes.append(f"AQHI: {getattr(aqhi, 'error', 'fetch failed')}.")
    if not wx.ok:
        notes.append(f"Weather: {getattr(wx, 'error', 'fetch failed')}.")
    data_quality_note = " ".join(notes) if notes else None

    try:
        built = build_summary(virus, env)
    except Exception as e:
        log.exception("build_summary failed: %s", e)
        warnings.append(f"build_summary: {e}")
        built = {"outdoor_feel": "Unavailable", "summary_text": "We couldn’t build a full summary this run."}

    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "region": region,
        "rsv": virus["rsv"],
        "flu": virus["flu"],
        "covid": virus["covid"],
        "air_quality": env["air_quality"],
        "weather": env["weather"],
        "weather_display": weather_display,
        "outdoor_feel": built["outdoor_feel"],
        "summary": built["summary_text"],
        "updated_at": now.isoformat().replace("+00:00", "Z"),
        "sources": sources,
        "data_quality_note": data_quality_note,
    }
    return payload, warnings


def build_full_homepage_dict(*, region: str = "Metro Vancouver") -> dict[str, Any]:
    """Backward-compatible: returns dict only (warnings dropped)."""
    d, _ = build_homepage_summary_dict(region=region)
    return d
