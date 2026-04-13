"""Daily visit counter (UTC calendar day)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.daily_visit import Visit

router = APIRouter()


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


class VisitCountResponse(BaseModel):
    count: int = Field(ge=0, description="Visits recorded for the current UTC day.")


@router.post("/track-visit", status_code=204)
def track_visit(db: Session = Depends(get_db)) -> None:
    """Increment today's visit count; creates the row for today if missing."""
    today = _today_utc()
    for _ in range(4):
        row = db.scalar(select(Visit).where(Visit.visit_date == today))
        if row is not None:
            row.count += 1
            db.commit()
            return
        db.add(Visit(visit_date=today, count=1))
        try:
            db.commit()
            return
        except IntegrityError:
            db.rollback()


@router.get("/visit-count", response_model=VisitCountResponse)
def visit_count(db: Session = Depends(get_db)) -> VisitCountResponse:
    """Today's count (UTC); zero if no visits yet."""
    today = _today_utc()
    row = db.scalar(select(Visit).where(Visit.visit_date == today))
    return VisitCountResponse(count=int(row.count) if row else 0)
