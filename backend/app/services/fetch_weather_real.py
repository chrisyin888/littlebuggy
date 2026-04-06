"""
Current weather for Vancouver core via Open-Meteo (forecast API, current conditions).

**Classification:** *third-party API* — Open-Meteo (https://open-meteo.com) aggregates models;
terms: https://open-meteo.com/en/terms . No API key for non-commercial reasonable use.

Environment Canada GeoMet weather layers exist, but Open-Meteo is simpler for a solo-founder V1
current-conditions read. MSC remains the authoritative narrative for severe weather; this is
a lightweight “what it feels like now” input for `outdoor_feel`.
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


def fetch_weather_vancouver() -> WeatherBundle:
    fetched_at = datetime.now(timezone.utc)
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
        "timezone": "America/Vancouver",
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
        t = float(cur.get("temperature_2m"))
        p = float(cur.get("precipitation") or 0)
        wcode = int(cur.get("weather_code") or 0)
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

    label = _WMO_LABELS.get(wcode, f"Weather code {wcode}")
    when = cur.get("time")
    bits = [f"{label}", f"{t:.0f}°C"]
    if p > 0.2:
        bits.append(f"precip ~{p:.1f} mm")
    if wind >= 25:
        bits.append(f"breezy ~{wind:.0f} km/h")
    summary = " · ".join(bits)

    return WeatherBundle(
        ok=True,
        weather_summary=summary,
        source_name="Open-Meteo (forecast API, current)",
        source_url="https://open-meteo.com/en/docs",
        source_updated_label=str(when) if when else None,
        fetched_at=fetched_at,
        error=None,
        extra={"latitude": LAT, "longitude": LON, "weather_code": wcode},
    )
