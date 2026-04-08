"""
Vancouver-area weather via Open-Meteo (forecast API): **today’s daily high/low** (primary) plus
optional **current** temperature for a small secondary line.

**Classification:** *third-party API* — Open-Meteo (https://open-meteo.com) aggregates models;
terms: https://open-meteo.com/en/terms . No API key for non-commercial reasonable use.

MSC remains the authoritative narrative for severe weather; this is a lightweight family snapshot.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.http_util import http_client

log = logging.getLogger(__name__)

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
# Downtown Vancouver-ish
LAT, LON = 49.2827, -123.1207


# WMO Weather interpretation codes (subset) — https://open-meteo.com/en/docs
_WMO_LABELS: dict[int, str] = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass
class WeatherBundle:
    ok: bool
    weather_summary: str
    source_name: str
    source_url: str
    source_updated_label: str | None
    fetched_at: datetime
    error: str | None = None
    extra: dict[str, Any] | None = None
    # Today’s range (daily forecast, local timezone); optional current for UI footnote
    high_c: float | None = None
    low_c: float | None = None
    current_c: float | None = None
    condition_label: str | None = None
    location_label: str = "Vancouver"


def weather_display_dict(b: WeatherBundle) -> dict[str, Any] | None:
    """Structured block for API / static JSON; None when fetch failed."""
    if not b.ok or b.high_c is None or b.low_c is None:
        return None
    out: dict[str, Any] = {
        "location_label": b.location_label,
        "high_c": round(float(b.high_c), 1),
        "low_c": round(float(b.low_c), 1),
        "condition": b.condition_label,
    }
    if b.current_c is not None:
        out["current_c"] = round(float(b.current_c), 1)
    return out


def fetch_weather_vancouver() -> WeatherBundle:
    fetched_at = datetime.now(timezone.utc)
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "America/Vancouver",
        "forecast_days": 2,
    }
    try:
        with http_client() as client:
            r = client.get(OPEN_METEO, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.exception("Open-Meteo fetch failed: %s", e)
        return WeatherBundle(
            ok=False,
            weather_summary="Unavailable",
            source_name="Open-Meteo",
            source_url="https://open-meteo.com/en/docs",
            source_updated_label=None,
            fetched_at=fetched_at,
            error=str(e),
        )

    cur = data.get("current") if isinstance(data, dict) else None
    daily = data.get("daily") if isinstance(data, dict) else None
    if not isinstance(cur, dict):
        return WeatherBundle(
            ok=False,
            weather_summary="Unavailable",
            source_name="Open-Meteo",
            source_url="https://open-meteo.com/en/docs",
            source_updated_label=None,
            fetched_at=fetched_at,
            error="missing_current",
        )

    try:
        current_temp = float(cur.get("temperature_2m"))
        p = float(cur.get("precipitation") or 0)
        cur_wcode = int(cur.get("weather_code") or 0)
        wind = float(cur.get("wind_speed_10m") or 0)
    except (TypeError, ValueError):
        return WeatherBundle(
            ok=False,
            weather_summary="Unavailable",
            source_name="Open-Meteo",
            source_url="https://open-meteo.com/en/docs",
            source_updated_label=None,
            fetched_at=fetched_at,
            error="bad_numeric_fields",
        )

    when = cur.get("time")
    high_c: float | None = None
    low_c: float | None = None
    day_wcode = cur_wcode
    label: str

    if isinstance(daily, dict):
        times = daily.get("time") or []
        maxs = daily.get("temperature_2m_max") or []
        mins = daily.get("temperature_2m_min") or []
        codes = daily.get("weather_code") or []
        if times and maxs and mins and len(times) == len(maxs) == len(mins):
            try:
                high_c = float(maxs[0])
                low_c = float(mins[0])
                if codes and len(codes) > 0:
                    day_wcode = int(codes[0])
            except (TypeError, ValueError, IndexError):
                high_c = low_c = None

    if high_c is None or low_c is None:
        high_c = low_c = current_temp
        day_wcode = cur_wcode

    label = _WMO_LABELS.get(day_wcode, f"Weather code {day_wcode}")
    # Summary for text pipelines: range first (no leading “High” — avoids i18n level collisions).
    summary = f"{low_c:.0f}°–{high_c:.0f}°C · {label}"
    if p > 0.2:
        summary = f"{summary} · precip ~{p:.1f} mm"
    if wind >= 25:
        summary = f"{summary} · breezy ~{wind:.0f} km/h"

    return WeatherBundle(
        ok=True,
        weather_summary=summary,
        source_name="Open-Meteo (forecast API, daily + current)",
        source_url="https://open-meteo.com/en/docs",
        source_updated_label=str(when) if when else None,
        fetched_at=fetched_at,
        error=None,
        extra={"latitude": LAT, "longitude": LON, "weather_code": day_wcode},
        high_c=high_c,
        low_c=low_c,
        current_c=current_temp,
        condition_label=label,
        location_label="Vancouver",
    )
