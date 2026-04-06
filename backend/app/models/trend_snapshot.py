from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrendSnapshot(Base):
    """
    One row per automated (or manual) update run.
    Levels are parent-friendly labels, not clinical scores.
    """

    __tablename__ = "trend_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(128), nullable=False, default="Metro Vancouver")

    rsv_level: Mapped[str] = mapped_column(String(64), nullable=False)
    flu_level: Mapped[str] = mapped_column(String(64), nullable=False)
    covid_level: Mapped[str] = mapped_column(String(64), nullable=False)
    # Legacy column: no longer exposed in API or summaries; kept so existing DBs need no migration.
    pollen_level: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    air_quality_level: Mapped[str] = mapped_column(String(256), nullable=False)

    weather_summary: Mapped[str] = mapped_column(String(256), nullable=False, default="Unavailable")

    outdoor_feel: Mapped[str] = mapped_column(String(128), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)

    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_quality_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
