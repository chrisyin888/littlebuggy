from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WeatherDisplayPayload(BaseModel):
    """Today's daily range + optional current (Open-Meteo / snapshot)."""

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
    """
    One respiratory / health signal row.

    The set of keys is dynamic — not limited to rsv/flu/covid. New pathogens
    published by PHAC are automatically included; add entries to
    ``app.config.pathogen_catalog`` to enrich their display.
    """

    key: str = Field(description="Stable machine key, e.g. rsv, flu, covid, hmpv.")
    label: str = Field(description="Short human label for cards and screen readers.")
    level: str = Field(description="Primary level phrase (without parentheses), e.g. Medium.")
    trend: str | None = Field(
        default=None,
        description="Optional qualifier from parentheses, e.g. Stable from 'Medium (Stable)'.",
    )
    # Symptom catalog fields — informational only, never imply diagnosis.
    symptoms: list[str] | None = Field(
        default=None,
        description=(
            "Reviewed, commonly-reported symptoms for this pathogen. "
            "Informational only — not a diagnosis. "
            "None means the pathogen has no reviewed entry yet; show symptom_fallback_message instead."
        ),
    )
    symptom_disclaimer: str | None = Field(
        default=None,
        description="Disclaimer text shown alongside the symptom list when symptoms is present.",
    )
    symptom_fallback_message: str | None = Field(
        default=None,
        description="Neutral message shown when no reviewed symptoms are available for this pathogen.",
    )


class RespiratoryRankingEntry(BaseModel):
    """One dynamic wastewater measure row (BC PHAC feed), sorted by severity for full-list views."""

    model_config = ConfigDict(extra="ignore")

    key: str
    display_name: str
    value: float | None = None
    severity_label: str
    severity_score: float
    updated_at: datetime


class HomepageSummaryResponse(BaseModel):
    """Stable JSON keys for the Vue frontend."""

    city_id: str = Field(default="vancouver", description="Canonical city key (see app.config.cities).")
    region: str
    signals: list[HomepageSignal] = Field(
        default_factory=list,
        description=(
            "Ordered health signals for hero cards. Sorted by severity (highest first). "
            "Preferred over legacy rsv/flu/covid fields. "
            "Includes all pathogens discovered dynamically from the PHAC feed."
        ),
    )
    respiratory_ranking: list[RespiratoryRankingEntry] = Field(
        default_factory=list,
        description="All measures from the BC wastewater feed, severity-sorted (full ranking / trends).",
    )
    # Legacy fixed fields — kept for backward compatibility.
    # Consumers should prefer the ``signals`` array which is fully dynamic.
    rsv: str = Field(default="Unknown", description="Legacy RSV level string. Prefer signals[].")
    flu: str = Field(default="Unknown", description="Legacy composite flu level string. Prefer signals[].")
    covid: str = Field(default="Unknown", description="Legacy COVID-19 level string. Prefer signals[].")
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
