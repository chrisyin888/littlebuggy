from datetime import datetime

from pydantic import BaseModel, Field


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

    region: str
    rsv: str
    flu: str
    covid: str
    air_quality: str
    weather: str = Field(description="Short current-weather phrase (may be Unavailable).")
    outdoor_feel: str
    summary: str
    updated_at: datetime
    sources: SourcesBundle
    data_quality_note: str | None = None
