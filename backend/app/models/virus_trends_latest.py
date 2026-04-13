"""Singleton row holding the latest virus-trends JSON for API reads (cron job writes here)."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VirusTrendsLatest(Base):
    """
    Single logical document (id always 1) so Render cron and web service share data via Postgres.
    File-based storage remains for local SQLite dev in ``virus_trends_storage``.
    """

    __tablename__ = "virus_trends_latest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
