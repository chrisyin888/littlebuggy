"""One row per calendar day (UTC) for a simple visit counter."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Visit(Base):
    """One row per UTC calendar day; ``visit_date`` is unique."""

    __tablename__ = "daily_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
