"""One row per calendar day (UTC) for a simple visit counter."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Visit(Base):
    """One row per UTC calendar day; ``visit_date`` is unique."""

    __tablename__ = "daily_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DailyHumanVisit(Base):
    """One row per UTC calendar day; behavior-verified "real human" visits.

    Incremented only by POST /track-human, which the frontend fires at most
    once per session after a human-like behavior signal (scroll, interaction,
    visible dwell, or a second page view) — and only for non-bot user agents.
    """

    __tablename__ = "daily_human_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DailyVisitSource(Base):
    """One row per (UTC calendar day, referral-source category)."""

    __tablename__ = "daily_visit_sources"
    __table_args__ = (
        UniqueConstraint("visit_date", "category", name="uq_daily_visit_sources_date_category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
