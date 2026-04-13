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


class HomepageSignal(BaseModel):
    """One respiratory / health signal row (dynamic set; keys are not limited to rsv/flu/covid)."""

    key: str = Field(description="Stable machine key, e.g. rsv, flu, covid, hmpv.")
    label: str = Field(description="Short human label for cards and screen readers.")
    level: str = Field(description="Primary level phrase (without parentheses), e.g. Medium.")
    trend: str | None = Field(
        default=None,
        description="Optional qualifier from parentheses, e.g. Stable from 'Medium (Stable)'.",
    )


class HomepageSummaryResponse(BaseModel):
    """Stable JSON keys for the Vue frontend."""

    city_id: str = Field(default="vancouver", description="Canonical city key (see app.config.cities).")
    region: str
    signals: list[HomepageSignal] = Field(
        default_factory=list,
        description="Ordered health signals for hero cards (preferred). Legacy rsv/flu/covid still set.",
    )
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
