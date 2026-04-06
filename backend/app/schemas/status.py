from datetime import datetime

from pydantic import BaseModel, Field


class SourceHealth(BaseModel):
    """Per-feed health from the latest snapshot’s `sources_json`."""

    present: bool = Field(description="Whether this key existed in stored metadata.")
    status: str | None = Field(None, description='Usually "ok", "error", or "unknown".')
    ok: bool = Field(description="True when status is ok.")


class SystemStatusResponse(BaseModel):
    """Operator-facing snapshot of pipeline + latest row (read-only)."""

    database_ok: bool = True
    last_snapshot_at: datetime | None = Field(
        None, description="created_at of the newest trend_snapshots row."
    )
    homepage_summary_ready: bool = Field(
        False, description="True when at least one snapshot exists (GET /api/homepage-summary would be 200)."
    )
    respiratory: SourceHealth = Field(description="PHAC / wastewater proxy row metadata.")
    environment: SourceHealth = Field(
        description="True when both AQHI and weather report ok in the latest snapshot."
    )
    aqhi: SourceHealth
    weather: SourceHealth
    message: str | None = Field(
        None, description="Short hint for operators (e.g. no rows yet, or bootstrap instructions)."
    )
