from datetime import datetime

from pydantic import BaseModel, Field


class WeatherDisplayPayload(BaseModel):
    """Today’s daily range + optional current (Open-Meteo / snapshot)."""

    location_label: str = "Vancouver"
    high_c: float | None = None
    low_c: float | None = None
    current_c: float | None = None
    condition: str | None = None


class SourceMeta(BaseModel):
    name: str
    url: str
    refreshed_label: str | None = None
    status: str | None = None  # e.g. "ok" | "error" | "unavailable"


class SourcesBundle(BaseModel):
    respiratory: SourceMeta
    aqhi: SourceMeta
    weather: SourceMeta


class HomepageSummaryResponse(BaseModel):
    """Stable JSON keys for the Vue frontend."""

    city_id: str = Field(default="vancouver", description="Canonical city key (see app.config.cities).")
    region: str
    rsv: str
    flu: str
    covid: str
    air_quality: str
    weather: str = Field(
        description="Short weather phrase: daily range + condition when available (may be missing)."
    )
    weather_display: WeatherDisplayPayload | None = None
    outdoor_feel: str
    summary: str
    updated_at: datetime
    sources: SourcesBundle
    data_quality_note: str | None = None
