"""
Fetch + merge + persist homepage snapshots (same signal fetches as ``homepage_summary_builder``).

Supports per-city rows (``city_id`` on ``trend_snapshots``) and modes that refresh a subset of feeds,
reusing the latest snapshot **for that city** for the rest.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.config.cities import resolve_city_id
from app.models.trend_snapshot import TrendSnapshot
from app.services.build_summary import build_summary
from app.services.fetch_weather_real import weather_display_dict
from app.services.homepage_summary_builder import (
    build_sources_bundle,
    fetch_homepage_signals,
)
from app.services.save_snapshot import save_snapshot
from app.services.trend_snapshot_homepage import get_latest_homepage_snapshot_row

log = logging.getLogger("littlebuggy.pipeline")

RefreshMode = Literal["full", "respiratory_only", "environment_only"]


def _virus_from_snapshot(row: TrendSnapshot | None) -> dict[str, str]:
    if row is None:
        return {"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"}
    return {"rsv": row.rsv_level, "flu": row.flu_level, "covid": row.covid_level}


def _env_from_snapshot(row: TrendSnapshot | None) -> dict[str, str]:
    if row is None:
        return {
            "air_quality": "Unavailable",
            "weather": "Unavailable",
        }
    return {
        "air_quality": row.air_quality_level,
        "weather": row.weather_summary,
    }


def _weather_display_from_snapshot(row: TrendSnapshot | None) -> dict[str, Any] | None:
    if row is None or not row.weather_display_json:
        return None
    try:
        d = json.loads(row.weather_display_json)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _resp_bundle_from_sources_last(last: TrendSnapshot | None) -> Any:
    if last and last.sources_json:
        try:
            prev = json.loads(last.sources_json)
            r_meta = prev.get("respiratory", {})
            return SimpleNamespace(
                ok=r_meta.get("status") == "ok",
                source_name=r_meta.get("name", ""),
                source_url=r_meta.get("url", ""),
                source_updated_label=r_meta.get("refreshed_label"),
            )
        except Exception:
            pass
    if last is None:
        return SimpleNamespace(
            ok=False,
            source_name="(no prior snapshot)",
            source_url="",
            source_updated_label=None,
        )
    return SimpleNamespace(
        ok=False,
        source_name="(carried forward)",
        source_url="",
        source_updated_label=None,
    )


def _env_bundles_from_sources_last(last: TrendSnapshot | None) -> tuple[Any, Any]:
    aqhi: Any = SimpleNamespace(
        ok=False,
        source_name="(carried forward)",
        source_url="",
        source_updated_label=None,
    )
    wx: Any = SimpleNamespace(
        ok=False,
        source_name="(carried forward)",
        source_url="",
        source_updated_label=None,
    )
    if last and last.sources_json:
        try:
            prev = json.loads(last.sources_json)

            def sn(key: str) -> Any:
                m = prev.get(key, {})
                return SimpleNamespace(
                    ok=m.get("status") == "ok",
                    source_name=m.get("name", key),
                    source_url=m.get("url", ""),
                    source_updated_label=m.get("refreshed_label"),
                    status=m.get("status"),
                )

            aqhi = sn("aqhi")
            wx = sn("weather")
        except Exception:
            pass
    return aqhi, wx


def run_snapshot_job(
    db: Session,
    *,
    city_id: str | None = None,
    mode: RefreshMode,
) -> int:
    """
    Persist one ``trend_snapshots`` row for ``resolve_city_id(city_id)`` (default Vancouver).

    Uses ``fetch_homepage_signals`` for live pulls — same inputs as ``build_homepage_summary_dict``.
    """
    city = resolve_city_id(city_id)
    last = get_latest_homepage_snapshot_row(db, city.id)

    if mode == "full":
        need_resp = need_env = True
    elif mode == "respiratory_only":
        need_resp, need_env = True, False
    else:
        need_resp, need_env = False, True

    resp, aqhi, wx, _w = fetch_homepage_signals(
        city,
        need_respiratory=need_resp,
        need_environment=need_env,
    )

    if need_resp:
        assert resp is not None
        virus = resp.virus if resp.ok else _virus_from_snapshot(last)
    else:
        resp = _resp_bundle_from_sources_last(last)
        virus = _virus_from_snapshot(last)

    if need_env:
        assert aqhi is not None and wx is not None
        env = {
            "air_quality": aqhi.air_quality if aqhi.ok else "Unavailable",
            "weather": wx.weather_summary if wx.ok else "Unavailable",
        }
    else:
        aqhi, wx = _env_bundles_from_sources_last(last)
        env = _env_from_snapshot(last)

    sources = build_sources_bundle(resp, aqhi, wx)

    notes: list[str] = []
    if need_resp and resp and not getattr(resp, "ok", False):
        notes.append(f"Respiratory: {getattr(resp, 'error', 'fetch failed')}.")
    if need_env:
        if aqhi and not aqhi.ok:
            notes.append(f"AQHI: {getattr(aqhi, 'error', 'fetch failed')}.")
        if wx and not wx.ok:
            notes.append(f"Weather: {getattr(wx, 'error', 'fetch failed')}.")
    data_quality_note = " ".join(notes) if notes else None

    built = build_summary(virus, env)
    log.info("Pipeline city=%s mode=%s virus=%s env=%s", city.id, mode, virus, env)

    weather_display: dict[str, Any] | None
    if need_env:
        weather_display = weather_display_dict(wx) if wx and wx.ok else None
    else:
        weather_display = _weather_display_from_snapshot(last)

    row = save_snapshot(
        db,
        city_id=city.id,
        region=city.name,
        virus_data=virus,
        env_data=env,
        outdoor_feel=built["outdoor_feel"],
        summary_text=built["summary_text"],
        sources=sources,
        data_quality_note=data_quality_note,
        weather_display=weather_display,
    )
    log.info("Saved trend_snapshots id=%s city_id=%s", row.id, city.id)
    return row.id
