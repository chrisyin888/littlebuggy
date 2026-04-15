import json
from typing import Any

from sqlalchemy.orm import Session

from app.config.pathogen_catalog import virus_triple_from_ranking
from app.models.trend_snapshot import TrendSnapshot


def save_snapshot(
    db: Session,
    *,
    city_id: str = "vancouver",
    region: str,
    virus_data: dict[str, str],
    env_data: dict[str, str],
    outdoor_feel: str,
    summary_text: str,
    sources: dict[str, Any] | None = None,
    data_quality_note: str | None = None,
    weather_display: dict[str, Any] | None = None,
    respiratory_ranking: list[dict[str, Any]] | None = None,
) -> TrendSnapshot:
    """
    Persist one trend_snapshots row. Called after fetch + build_summary.

    Legacy rsv_level / flu_level / covid_level columns are populated from the
    ranking (via virus_triple_from_ranking) so existing DB consumers still work.
    ``virus_data`` is used as a secondary source when ranking is unavailable.
    """
    # Derive legacy triple from ranking (preferred) or fall back to virus_data
    if respiratory_ranking:
        triple = virus_triple_from_ranking(respiratory_ranking)
    else:
        triple = {
            "rsv": virus_data.get("rsv", "Unknown"),
            "flu": virus_data.get("flu", "Unknown"),
            "covid": virus_data.get("covid", "Unknown"),
        }

    row = TrendSnapshot(
        city_id=city_id,
        region=region,
        rsv_level=triple.get("rsv", "Unknown"),
        flu_level=triple.get("flu", "Unknown"),
        covid_level=triple.get("covid", "Unknown"),
        pollen_level="",
        air_quality_level=env_data["air_quality"],
        weather_summary=env_data.get("weather", "Unavailable"),
        weather_display_json=json.dumps(weather_display, ensure_ascii=False) if weather_display else None,
        outdoor_feel=outdoor_feel,
        summary_text=summary_text,
        sources_json=json.dumps(sources, ensure_ascii=False) if sources else None,
        data_quality_note=data_quality_note,
        respiratory_ranking_json=json.dumps(respiratory_ranking, ensure_ascii=False)
        if respiratory_ranking
        else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
