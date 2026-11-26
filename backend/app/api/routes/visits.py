"""Daily visit counter (UTC calendar day) with referral-source breakdown."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.daily_visit import DailyVisitSource, Visit

router = APIRouter()

SOURCE_CATEGORIES = ("direct", "google", "bing", "social", "gnjacob", "other")


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _normalize_category(raw: str | None) -> str:
    if raw is None:
        return "other"
    value = raw.strip().lower()
    return value if value in SOURCE_CATEGORIES else "other"


# Bot / crawler UA markers (lowercase substrings). The beacon fires from
# anything that renders the page, so without this filter the "visits" are
# mostly crawlers, AI scrapers and uptime monitors. The UA is only inspected
# transiently here — it is never stored. Same list as the family-board
# counter (added 2026-11-26 at the owner's request).
_BOT_UA_MARKERS = (
    "bot", "spider", "crawler", "crawl", "headless", "phantomjs", "puppeteer",
    "playwright", "selenium", "webdriver", "python-requests", "python-httpx",
    "curl/", "wget", "go-http-client", "okhttp", "axios", "node-fetch",
    "libwww", "lighthouse", "pagespeed", "gtmetrix", "pingdom", "uptimerobot",
    "statuscake", "site24x7", "newrelic", "datadog", "ia_archiver",
    "facebookexternalhit", "meta-externalagent", "bingpreview", "slackbot",
    "telegrambot", "whatsapp", "skypeuripreview", "prerender", "preview",
    "monitor",
)


def _is_bot_ua(user_agent: str | None) -> bool:
    ua = (user_agent or "").strip().lower()
    if not ua:
        return True
    return any(marker in ua for marker in _BOT_UA_MARKERS)


class VisitCountResponse(BaseModel):
    count: int = Field(ge=0, description="Visits recorded for the current UTC day.")


class TrackVisitRequest(BaseModel):
    category: str | None = Field(
        default=None,
        description="Referral-source category (direct/google/bing/social/gnjacob/other).",
    )


class SourceCounts(BaseModel):
    direct: int = 0
    google: int = 0
    bing: int = 0
    social: int = 0
    gnjacob: int = 0
    other: int = 0


class VisitSourcesToday(BaseModel):
    date: date
    total: int = Field(ge=0, description="Total visits today (UTC), all sources.")
    sources: SourceCounts


class VisitSourcesTotals(BaseModel):
    total: int = Field(ge=0, description="Total visits over the window, all sources.")
    sources: SourceCounts


class VisitSourcesResponse(BaseModel):
    today: VisitSourcesToday
    last_7_days: VisitSourcesTotals


def _bump_visit(db: Session, today: date) -> None:
    row = db.scalar(select(Visit).where(Visit.visit_date == today))
    if row is not None:
        row.count += 1
    else:
        db.add(Visit(visit_date=today, count=1))


def _bump_source(db: Session, today: date, category: str) -> None:
    row = db.scalar(
        select(DailyVisitSource).where(
            DailyVisitSource.visit_date == today,
            DailyVisitSource.category == category,
        )
    )
    if row is not None:
        row.count += 1
    else:
        db.add(DailyVisitSource(visit_date=today, category=category, count=1))


@router.post("/track-visit", status_code=204)
def track_visit(
    request: Request,
    payload: TrackVisitRequest | None = None,
    db: Session = Depends(get_db),
) -> None:
    """Increment today's visit count (total + per-source); creates rows if missing.

    The JSON body is optional: older clients POST with no body and are counted
    under the ``other`` source category.

    Bot/crawler user agents are acknowledged (204) but NOT counted, so the
    totals approximate real people.
    """
    if _is_bot_ua(request.headers.get("user-agent")):
        return
    category = _normalize_category(payload.category if payload is not None else None)
    today = _today_utc()
    for _ in range(4):
        _bump_visit(db, today)
        _bump_source(db, today, category)
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


@router.get("/visit-sources", response_model=VisitSourcesResponse)
def visit_sources(db: Session = Depends(get_db)) -> VisitSourcesResponse:
    """Per-source visit counts: today (UTC) and the last 7 UTC days combined."""
    today = _today_utc()
    window_start = today - timedelta(days=6)
    rows = db.scalars(
        select(DailyVisitSource).where(DailyVisitSource.visit_date >= window_start)
    ).all()

    today_counts = {c: 0 for c in SOURCE_CATEGORIES}
    window_counts = {c: 0 for c in SOURCE_CATEGORIES}
    for row in rows:
        if row.category not in window_counts:
            continue
        window_counts[row.category] += int(row.count)
        if row.visit_date == today:
            today_counts[row.category] += int(row.count)

    return VisitSourcesResponse(
        today=VisitSourcesToday(
            date=today,
            total=sum(today_counts.values()),
            sources=SourceCounts(**today_counts),
        ),
        last_7_days=VisitSourcesTotals(
            total=sum(window_counts.values()),
            sources=SourceCounts(**window_counts),
        ),
    )
