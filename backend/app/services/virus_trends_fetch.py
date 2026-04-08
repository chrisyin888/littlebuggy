"""
Fetch structured respiratory virus trend signals for the public /virus-trends endpoint.

**Trust / sources**

1. **BCCDC respiratory virus data page** — scraped for context (meta description, any embedded
   ISO dates). Clinical dashboard data is not reliably available as parseable JSON in the HTML.

2. **Levels (RSV, Flu A, Flu B, COVID-19)** — derived from the **PHAC Health Infobase official
   wastewater SQL API** for BC (pruid=59), same family of signal as `fetch_bccdc_real.py`.
   These are **population-level environmental proxies**, not diagnoses. We never invent levels:
   if the API fails or data are insufficient, all levels are **Unknown**.

Level labels use parent-facing buckets: High, Elevated, Moderate, Low, Unknown.
"""

from __future__ import annotations

import logging
import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup

from app.services.http_util import http_client

log = logging.getLogger(__name__)

BCCDC_RESPIRATORY_URL = (
    "https://www.bccdc.ca/health-professionals/data-reports/respiratory-virus-data"
)
HEALTH_INFOBASE_WASTEWATER_QUERY_URL = "https://health-infobase.canada.ca/api/wastewater/query"
PHAC_LANDING = "https://health-infobase.canada.ca/api/"

_SQL = """
SELECT "Date", measureid, "Location", seven_day_rolling_avg
FROM wastewater_daily
WHERE pruid = 59 AND measureid IN ('covN2', 'rsv', 'fluA', 'fluB')
ORDER BY "Date" DESC
LIMIT 800
"""


def _percentile_rank(value: float, series: list[float]) -> float:
    if not series:
        return 50.0
    s = sorted(series)
    below = sum(1 for x in s if x < value)
    return 100.0 * below / len(s)


def _level_from_percentile(pct: float) -> str:
    """Map historical percentile to public-facing label (conservative buckets)."""
    if pct >= 82.0:
        return "High"
    if pct >= 58.0:
        return "Elevated"
    if pct >= 32.0:
        return "Moderate"
    return "Low"


def _aggregate_by_date(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Date -> mean across BC sites per measure (fluA / fluB kept separate)."""
    by_site: dict[tuple[str, str], dict[str, float]] = {}
    for r in rows:
        d = str(r.get("Date") or "")
        loc = str(r.get("Location") or "")
        mid = str(r.get("measureid") or "")
        try:
            val = float(r.get("seven_day_rolling_avg") or 0.0)
        except (TypeError, ValueError):
            continue
        if not d or not mid:
            continue
        key = (d, loc)
        by_site.setdefault(key, {})[mid] = val

    by_date: dict[str, dict[str, list[float]]] = {}
    for (d, _loc), measures in by_site.items():
        bucket = by_date.setdefault(
            d,
            {"covN2": [], "rsv": [], "fluA": [], "fluB": []},
        )
        for mid, key in (("covN2", "covN2"), ("rsv", "rsv"), ("fluA", "fluA"), ("fluB", "fluB")):
            v = measures.get(mid)
            if v is not None:
                bucket[key].append(v)

    out: dict[str, dict[str, float]] = {}
    for d, b in by_date.items():
        out[d] = {
            "covN2": float(statistics.mean(b["covN2"])) if b["covN2"] else 0.0,
            "rsv": float(statistics.mean(b["rsv"])) if b["rsv"] else 0.0,
            "fluA": float(statistics.mean(b["fluA"])) if b["fluA"] else 0.0,
            "fluB": float(statistics.mean(b["fluB"])) if b["fluB"] else 0.0,
        }
    return out


def _scrape_bccdc_report_date(html: str) -> str | None:
    """ISO date only if clearly present in page meta (avoid guessing from random HTML dates)."""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", meta["content"])
        if m:
            return m.group(1)
    return None


def _build_summary(levels: dict[str, str]) -> str:
    """Short neutral summary from computed levels (no clinical claims)."""
    order = [
        ("rsv", "RSV"),
        ("flu_a", "Influenza A"),
        ("flu_b", "Influenza B"),
        ("covid", "COVID-19"),
    ]
    parts = [f"{label}: {levels[k]}" for k, label in order]
    return "Latest public BC wastewater signal (relative to this feed’s history): " + "; ".join(parts) + "."


@dataclass
class VirusTrendsFetchResult:
    ok: bool
    source_report_date: str | None
    summary: str
    viruses: list[dict[str, str]]
    source_url: str
    levels_detail: str
    error: str | None = None


def fetch_virus_trends() -> VirusTrendsFetchResult:
    """
    Pull BCCDC page (metadata) + PHAC BC wastewater rows; return structured levels or Unknown.
    """
    viruses_unknown = [
        {"key": "rsv", "name": "RSV", "level": "Unknown"},
        {"key": "flu_a", "name": "Influenza A", "level": "Unknown"},
        {"key": "flu_b", "name": "Influenza B", "level": "Unknown"},
        {"key": "covid", "name": "COVID-19", "level": "Unknown"},
    ]

    source_report_date: str | None = None
    try:
        with http_client() as client:
            br = client.get(
                BCCDC_RESPIRATORY_URL,
                headers={"Cache-Control": "no-cache"},
            )
            br.raise_for_status()
            source_report_date = _scrape_bccdc_report_date(br.text)
    except Exception as e:
        log.warning("BCCDC page fetch/metadata failed (non-fatal): %s", e)

    url = f"{HEALTH_INFOBASE_WASTEWATER_QUERY_URL}?q={quote(_SQL.strip())}"
    try:
        with http_client() as client:
            r = client.get(url)
            r.raise_for_status()
            rows = r.json()
    except Exception as e:
        log.exception("PHAC wastewater fetch failed: %s", e)
        return VirusTrendsFetchResult(
            ok=False,
            source_report_date=source_report_date,
            summary="Unable to refresh virus signal levels from public feeds right now.",
            viruses=viruses_unknown,
            source_url=BCCDC_RESPIRATORY_URL,
            levels_detail="Levels normally come from PHAC Health Infobase BC wastewater API.",
            error=str(e),
        )

    if not isinstance(rows, list) or not rows:
        return VirusTrendsFetchResult(
            ok=False,
            source_report_date=source_report_date,
            summary="Public wastewater feed returned no usable BC rows.",
            viruses=viruses_unknown,
            source_url=BCCDC_RESPIRATORY_URL,
            levels_detail="Empty or invalid PHAC payload.",
            error="empty_or_invalid_payload",
        )

    by_date = _aggregate_by_date(rows)
    if not by_date:
        return VirusTrendsFetchResult(
            ok=False,
            source_report_date=source_report_date,
            summary="Could not aggregate BC wastewater samples.",
            viruses=viruses_unknown,
            source_url=BCCDC_RESPIRATORY_URL,
            levels_detail="No BC rows after aggregation.",
            error="no_bc_rows_after_aggregate",
        )

    dates_sorted = sorted(by_date.keys(), reverse=True)
    latest_d = dates_sorted[0]
    prev_d = dates_sorted[1] if len(dates_sorted) > 1 else None

    def series_for(key: str) -> list[float]:
        return [by_date[d][key] for d in sorted(by_date.keys())]

    def level_for(key: str) -> str:
        hist = series_for(key)
        cur = by_date[latest_d][key]
        pos = [x for x in hist if x > 0]
        if cur <= 0 and not pos:
            return "Unknown"
        use = pos if pos else hist
        pct = _percentile_rank(cur, use)
        return _level_from_percentile(pct)

    levels_map = {
        "rsv": level_for("rsv"),
        "flu_a": level_for("fluA"),
        "flu_b": level_for("fluB"),
        "covid": level_for("covN2"),
    }

    viruses = [
        {"key": "rsv", "name": "RSV", "level": levels_map["rsv"]},
        {"key": "flu_a", "name": "Influenza A", "level": levels_map["flu_a"]},
        {"key": "flu_b", "name": "Influenza B", "level": levels_map["flu_b"]},
        {"key": "covid", "name": "COVID-19", "level": levels_map["covid"]},
    ]

    summary = _build_summary(levels_map)
    detail = (
        f"BC wastewater 7-day rolling average, latest sample date in feed: {latest_d}. "
        "Not a clinical test. BCCDC publishes weekly clinical surveillance separately."
    )

    return VirusTrendsFetchResult(
        ok=True,
        source_report_date=source_report_date,
        summary=summary,
        viruses=viruses,
        source_url=BCCDC_RESPIRATORY_URL,
        levels_detail=detail,
        error=None,
    )


def fetch_result_to_payload_dict(result: VirusTrendsFetchResult) -> dict[str, Any]:
    """Shape written to JSON / returned from refresh (without checked_at)."""
    return {
        "source_report_date": result.source_report_date,
        "source_name": "BCCDC",
        "summary": result.summary,
        "viruses": result.viruses,
        "source_url": result.source_url,
        "levels_method": result.levels_detail,
        "phac_reference_url": PHAC_LANDING,
    }
