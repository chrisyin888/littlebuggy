"""
Fetch + merge + persist homepage snapshots.

Supports:
- full refresh (respiratory + environment)
- weekly respiratory-only (reuses last snapshot for environment strings)
- daily environment-only (reuses last snapshot for respiratory levels)
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trend_snapshot import TrendSnapshot
from app.services.build_summary import build_summary
from app.services.fetch_aqhi_real import fetch_aqhi_metro_vancouver
from app.services.fetch_bccdc_real import fetch_respiratory_bc_signals
from app.services.fetch_weather_real import fetch_weather_vancouver, weather_display_dict
from app.services.homepage_summary_builder import build_sources_bundle
from app.services.save_snapshot import save_snapshot

log = logging.getLogger("littlebuggy.pipeline")

RefreshMode = Literal["full", "respiratory_only", "environment_only"]


def _latest_snapshot(db: Session) -> TrendSnapshot | None:
    return db.scalars(select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(1)).first()


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


def run_snapshot_job(db: Session, *, region: str, mode: RefreshMode) -> int:
    last = _latest_snapshot(db)

    if mode == "full":
        need_resp = True
        need_env = True
    elif mode == "respiratory_only":
        need_resp = True
        need_env = False
    else:
        need_resp = False
        need_env = True

    if need_resp:
        resp = fetch_respiratory_bc_signals()
        virus = resp.virus if resp.ok else _virus_from_snapshot(last)
    else:
        resp = None
        virus = _virus_from_snapshot(last)

    if need_env:
        aqhi = fetch_aqhi_metro_vancouver()
        wx = fetch_weather_vancouver()
        env = {
            "air_quality": aqhi.air_quality if aqhi.ok else "Unavailable",
            "weather": wx.weather_summary if wx.ok else "Unavailable",
        }
    else:
        aqhi = wx = None
        env = _env_from_snapshot(last)

    # Reconstruct minimal bundles for sources metadata when one side was skipped
    if resp is None and last and last.sources_json:
        try:
            prev = json.loads(last.sources_json)
            r_meta = prev.get("respiratory", {})

            resp = SimpleNamespace(
                ok=r_meta.get("status") == "ok",
                source_name=r_meta.get("name", ""),
                source_url=r_meta.get("url", ""),
                source_updated_label=r_meta.get("refreshed_label"),
            )
        except Exception:
            resp = SimpleNamespace(
                ok=False,
                source_name="(carried forward)",
                source_url="",
                source_updated_label=None,
            )
    elif resp is None:
        resp = SimpleNamespace(
            ok=False,
            source_name="(no prior snapshot)",
            source_url="",
            source_updated_label=None,
        )

    if aqhi is None or wx is None:
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

                aqhi = aqhi or sn("aqhi")
                wx = wx or sn("weather")
            except Exception:
                pass

        aqhi = aqhi or SimpleNamespace(
            ok=False,
            source_name="(carried forward)",
            source_url="",
            source_updated_label=None,
        )
        wx = wx or SimpleNamespace(
            ok=False,
            source_name="(carried forward)",
            source_url="",
            source_updated_label=None,
        )

    sources = build_sources_bundle(resp, aqhi, wx)

    notes: list[str] = []
    if need_resp and resp and not resp.ok:
        notes.append(f"Respiratory: {getattr(resp, 'error', 'fetch failed')}.")
    if need_env:
        if aqhi and not aqhi.ok:
            notes.append(f"AQHI: {getattr(aqhi, 'error', 'fetch failed')}.")
        if wx and not wx.ok:
            notes.append(f"Weather: {getattr(wx, 'error', 'fetch failed')}.")
    data_quality_note = " ".join(notes) if notes else None

    built = build_summary(virus, env)
    log.info("Pipeline mode=%s virus=%s env=%s", mode, virus, env)

    weather_display: dict[str, Any] | None
    if need_env:
        weather_display = weather_display_dict(wx) if wx and wx.ok else None
    else:
        weather_display = _weather_display_from_snapshot(last)

    row = save_snapshot(
        db,
        city_id="vancouver",
        region=region,
        virus_data=virus,
        env_data=env,
        outdoor_feel=built["outdoor_feel"],
        summary_text=built["summary_text"],
        sources=sources,
        data_quality_note=data_quality_note,
        weather_display=weather_display,
    )
    log.info("Saved trend_snapshots id=%s", row.id)
    return row.id
