import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.trend_snapshot import TrendSnapshot


def save_snapshot(
    db: Session,
    *,
    region: str,
    virus_data: dict[str, str],
    env_data: dict[str, str],
    outdoor_feel: str,
    summary_text: str,
    sources: dict[str, Any] | None = None,
    data_quality_note: str | None = None,
    weather_display: dict[str, Any] | None = None,
) -> TrendSnapshot:
    """
    Persist one trend_snapshots row. Called after fetch + build_summary.
    """
    row = TrendSnapshot(
        region=region,
        rsv_level=virus_data["rsv"],
        flu_level=virus_data["flu"],
        covid_level=virus_data["covid"],
        pollen_level="",
        air_quality_level=env_data["air_quality"],
        weather_summary=env_data.get("weather", "Unavailable"),
        weather_display_json=json.dumps(weather_display, ensure_ascii=False) if weather_display else None,
        outdoor_feel=outdoor_feel,
        summary_text=summary_text,
        sources_json=json.dumps(sources, ensure_ascii=False) if sources else None,
        data_quality_note=data_quality_note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
