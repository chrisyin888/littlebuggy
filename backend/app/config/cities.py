"""
Canonical homepage city profiles (id, display name, coordinates, local timezone).

Used by ``build_homepage_summary_dict`` for weather (Open-Meteo) and AQHI (GeoMet bbox).
Respiratory signals use the same national/BC-facing feed for all cities until per-region feeds are wired.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CityProfile:
    id: str
    name: str
    lat: float
    lng: float
    timezone: str
    """Short label for weather cards (Open-Meteo local context)."""
    weather_location_label: str


# Order preserved for API validation and admin tooling.
CITIES: tuple[CityProfile, ...] = (
    CityProfile(
        id="vancouver",
        name="Metro Vancouver",
        lat=49.2827,
        lng=-123.1207,
        timezone="America/Vancouver",
        weather_location_label="Vancouver",
    ),
    CityProfile(
        id="gta",
        name="GTA",
        lat=43.6532,
        lng=-79.3832,
        timezone="America/Toronto",
        weather_location_label="Toronto",
    ),
    CityProfile(
        id="calgary",
        name="Calgary",
        lat=51.0447,
        lng=-114.0719,
        timezone="America/Edmonton",
        weather_location_label="Calgary",
    ),
)

_CITY_BY_ID: dict[str, CityProfile] = {c.id: c for c in CITIES}


def resolve_city_id(raw: str | None) -> CityProfile:
    """
    Resolve query/body city parameter. Unknown or empty → Vancouver (default).
    """
    if raw is None or not str(raw).strip():
        return _CITY_BY_ID["vancouver"]
    key = str(raw).strip().lower()
    return _CITY_BY_ID.get(key, _CITY_BY_ID["vancouver"])


def default_city() -> CityProfile:
    return _CITY_BY_ID["vancouver"]
