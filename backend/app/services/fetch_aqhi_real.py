"""
Air Quality Health Index (AQHI) via Environment and Climate Change Canada MSC GeoMet-OGC-API.

**Classification:** *official API* (OGC Features — `api.weather.gc.ca`)

We query recent observations inside a bounding box over Metro Vancouver and summarize
the **maximum** latest AQHI among stations (conservative for sensitive groups).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.http_util import http_client

log = logging.getLogger(__name__)

GEOMET_AQHI_ITEMS = (
    "https://api.weather.gc.ca/collections/aqhi-observations-realtime/items"
)

# Approximate Metro Vancouver envelope (CRS84 lon, lat)
MV_BBOX = "-123.45,49.05,-122.55,49.45"

OPEN_GOV_AQHI_DATASET = (
    "https://open.canada.ca/data/en/dataset/"
    "28936e1b-681f-4c73-b04a-e86d4b3917c6"
)


def _aqhi_bucket(value: float) -> str:
    v = int(round(value))
    if v <= 3:
        return "Low Risk"
    if v <= 6:
        return "Moderate"
    if v <= 10:
        return "High Risk"
    return "Very High Risk"


@dataclass
class AQHIBundle:
    ok: bool
    air_quality: str  # parent phrase for LittleBuggy card
    air_quality_value: float | None
    air_quality_level: str | None
    location_label: str | None
    source_name: str
    source_url: str
    source_updated_label: str | None
    fetched_at: datetime
    error: str | None = None
    extra: dict[str, Any] | None = None


def fetch_aqhi_metro_vancouver() -> AQHIBundle:
    fetched_at = datetime.now(timezone.utc)
    params = {
        "bbox": MV_BBOX,
        "sortby": "-observation_datetime",
        "limit": "80",
        "f": "json",
    }
    try:
        with http_client() as client:
            r = client.get(GEOMET_AQHI_ITEMS, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.exception("AQHI GeoMet fetch failed: %s", e)
        return AQHIBundle(
            ok=False,
            air_quality="Unavailable",
            air_quality_value=None,
            air_quality_level=None,
            location_label=None,
            source_name="Environment and Climate Change Canada — MSC GeoMet (AQHI)",
            source_url=OPEN_GOV_AQHI_DATASET,
            source_updated_label=None,
            fetched_at=fetched_at,
            error=str(e),
        )

    feats = data.get("features") if isinstance(data, dict) else None
    if not isinstance(feats, list):
        return AQHIBundle(
            ok=False,
            air_quality="Unavailable",
            air_quality_value=None,
            air_quality_level=None,
            location_label=None,
            source_name="Environment and Climate Change Canada — MSC GeoMet (AQHI)",
            source_url=OPEN_GOV_AQHI_DATASET,
            source_updated_label=None,
            fetched_at=fetched_at,
            error="invalid_geojson",
        )

    latest_true = [f for f in feats if (f.get("properties") or {}).get("latest") is True]
    pool = latest_true if latest_true else feats

    best: dict[str, Any] | None = None
    max_aqhi = -1.0
    for f in pool:
        props = f.get("properties") or {}
        try:
            aqhi = float(props.get("aqhi"))
        except (TypeError, ValueError):
            continue
        if aqhi > max_aqhi:
            max_aqhi = aqhi
            best = props

    if best is None:
        return AQHIBundle(
            ok=False,
            air_quality="Unavailable",
            air_quality_value=None,
            air_quality_level=None,
            location_label=None,
            source_name="Environment and Climate Change Canada — MSC GeoMet (AQHI)",
            source_url=OPEN_GOV_AQHI_DATASET,
            source_updated_label=None,
            fetched_at=fetched_at,
            error="no_observations_in_bbox",
        )

    bucket = _aqhi_bucket(max_aqhi)
    loc = best.get("location_name_en") or best.get("location_name_fr")
    phrase = f"AQHI ~{max_aqhi:.0f} ({bucket}) — {loc}" if loc else f"AQHI ~{max_aqhi:.0f} ({bucket})"

    return AQHIBundle(
        ok=True,
        air_quality=phrase,
        air_quality_value=max_aqhi,
        air_quality_level=bucket,
        location_label=str(loc) if loc else None,
        source_name="Environment and Climate Change Canada — MSC GeoMet (AQHI)",
        source_url=OPEN_GOV_AQHI_DATASET,
        source_updated_label=best.get("observation_datetime_text_en")
        or best.get("observation_datetime"),
        fetched_at=fetched_at,
        error=None,
        extra={"geomet_collection": GEOMET_AQHI_ITEMS, "bbox": MV_BBOX},
    )
