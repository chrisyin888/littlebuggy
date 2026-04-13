"""
Vancouver-area weather via Open-Meteo (forecast API): **today’s daily high/low** (primary) plus
optional **current** temperature for a small secondary line.

**Classification:** *third-party API* — Open-Meteo (https://open-meteo.com) aggregates models;
terms: https://open-meteo.com/en/terms . No API key for non-commercial reasonable use.

MSC remains the authoritative narrative for severe weather; this is a lightweight family snapshot.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.http_util import http_client

log = logging.getLogger(__name__)

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
# Default centre (Metro Vancouver) — ``fetch_weather_vancouver`` delegates here.
DEFAULT_LAT, DEFAULT_LON = 49.2827, -123.1207

# Retries + timeout: transient Open-Meteo failures are common; do not hang the snapshot build.
WEATHER_MAX_ATTEMPTS = 3
WEATHER_RETRY_DELAY_SEC = 0.75
WEATHER_HTTP_TIMEOUT = httpx.Timeout(5.0, connect=5.0)

# In-process fallback when Open-Meteo is down (per worker / script process). Not persisted across deploys.
WEATHER_CACHE_MAX_AGE_SEC = 72 * 3600

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


_cache_lock = threading.Lock()
_last_good_weather: dict[tuple[Any, ...], tuple[WeatherBundle, datetime]] = {}


def _weather_cache_key(
    lat: float,
    lon: float,
    iana_timezone: str,
    location_label: str,
) -> tuple[Any, ...]:
    return (round(lat, 6), round(lon, 6), iana_timezone, location_label)


def _weather_cache_put(key: tuple[Any, ...], bundle: WeatherBundle) -> None:
    """Store a successful bundle (call only when bundle.ok)."""
    stored_at = datetime.now(timezone.utc)
    with _cache_lock:
        _last_good_weather[key] = (bundle, stored_at)


def _weather_cache_get_fresh_copy(
    key: tuple[Any, ...],
    *,
    now: datetime,
) -> tuple[WeatherBundle, float] | None:
    """Return (shallow copy of last good bundle, age in seconds) if within max age."""
    with _cache_lock:
        entry = _last_good_weather.get(key)
    if not entry:
        return None
    bundle, stored_at = entry
    if not bundle.ok:
        return None
    age_sec = (now - stored_at).total_seconds()
    if age_sec > WEATHER_CACHE_MAX_AGE_SEC:
        return None
    extra = dict(bundle.extra) if bundle.extra else None
    return replace(bundle, extra=extra), age_sec


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


def _parse_open_meteo_payload(
    data: Any,
    *,
    lat: float,
    lon: float,
    location_label: str,
    fetched_at: datetime,
) -> WeatherBundle:
    """Turn JSON body into a bundle; returns ok=False with error set when payload is unusable."""
    if not isinstance(data, dict):
        return WeatherBundle(
            ok=False,
            weather_summary="Unavailable",
            source_name="Open-Meteo",
            source_url="https://open-meteo.com/en/docs",
            source_updated_label=None,
            fetched_at=fetched_at,
            error="response_not_object",
        )

    cur = data.get("current")
    daily = data.get("daily")
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
        extra={"latitude": lat, "longitude": lon, "weather_code": day_wcode},
        high_c=high_c,
        low_c=low_c,
        current_c=current_temp,
        condition_label=label,
        location_label=location_label,
    )


def fetch_weather_at(
    lat: float,
    lon: float,
    *,
    iana_timezone: str,
    location_label: str,
) -> WeatherBundle:
    fetched_at = datetime.now(timezone.utc)
    cache_key = _weather_cache_key(lat, lon, iana_timezone, location_label)
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": iana_timezone,
        "forecast_days": 2,
    }

    last_failure: str | None = None

    for attempt in range(1, WEATHER_MAX_ATTEMPTS + 1):
        data: Any = None
        try:
            with http_client() as client:
                r = client.get(OPEN_METEO, params=params, timeout=WEATHER_HTTP_TIMEOUT)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            last_failure = f"{type(e).__name__}: {e}"
            if attempt < WEATHER_MAX_ATTEMPTS:
                log.warning(
                    "Open-Meteo request failed (attempt %s/%s): %s; retrying in %.2fs",
                    attempt,
                    WEATHER_MAX_ATTEMPTS,
                    last_failure,
                    WEATHER_RETRY_DELAY_SEC,
                )
                time.sleep(WEATHER_RETRY_DELAY_SEC)
            continue

        bundle = _parse_open_meteo_payload(
            data,
            lat=lat,
            lon=lon,
            location_label=location_label,
            fetched_at=fetched_at,
        )
        if bundle.ok:
            _weather_cache_put(cache_key, bundle)
            return bundle

        last_failure = bundle.error or "parse_failed"
        if attempt < WEATHER_MAX_ATTEMPTS:
            log.warning(
                "Open-Meteo unusable payload (attempt %s/%s): %s; retrying in %.2fs",
                attempt,
                WEATHER_MAX_ATTEMPTS,
                last_failure,
                WEATHER_RETRY_DELAY_SEC,
            )
            time.sleep(WEATHER_RETRY_DELAY_SEC)

    log.error(
        "Open-Meteo fetch failed after %s attempts; last failure: %s",
        WEATHER_MAX_ATTEMPTS,
        last_failure,
    )
    now = datetime.now(timezone.utc)
    hit = _weather_cache_get_fresh_copy(cache_key, now=now)
    if hit is not None:
        cached, age_sec = hit
        log.warning(
            "Open-Meteo reusing in-process cached weather (age %.0fs, max %ss) after failure: %s",
            age_sec,
            WEATHER_CACHE_MAX_AGE_SEC,
            last_failure,
        )
        return cached

    return WeatherBundle(
        ok=False,
        weather_summary="Unavailable",
        source_name="Open-Meteo",
        source_url="https://open-meteo.com/en/docs",
        source_updated_label=None,
        fetched_at=fetched_at,
        error=last_failure,
    )


def fetch_weather_vancouver() -> WeatherBundle:
    return fetch_weather_at(
        DEFAULT_LAT,
        DEFAULT_LON,
        iana_timezone="America/Vancouver",
        location_label="Vancouver",
    )
