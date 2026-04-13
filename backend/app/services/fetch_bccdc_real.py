"""
BC respiratory *signals* for LittleBuggy.

**Source labelling (read carefully)**

- BCCDC publishes human-readable weekly respiratory surveillance (dashboard + PDFs) at
  https://www.bccdc.ca/health-professionals/data-reports/respiratory-virus-data
  but **does not expose a documented public JSON/CSV API** for that combined product.

- This module therefore uses the **Public Health Agency of Canada (PHAC) Health Infobase
  official wastewater SQL API** for **British Columbia (pruid=59)** — a stable, structured,
  government-hosted feed that includes SARS-CoV-2, RSV, and influenza (flu A / flu B)
  viral signals at participating sites (e.g. Metro Vancouver).

**Classification:** *official API* (Health Infobase `/api/wastewater/query`) — **not** the
BCCDC clinical-positivity dashboard. BCCDC’s page is linked in metadata as the parent-facing
clinical surveillance reference.

Wastewater signals are **environmental proxies**, not diagnoses. Copy on the site must stay
non-clinical (already true for LittleBuggy).
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from app.services.http_util import http_client

log = logging.getLogger(__name__)

HEALTH_INFOBASE_WASTEWATER_QUERY_URL = "https://health-infobase.canada.ca/api/wastewater/query"
BCCDC_RESPIRATORY_HUMAN_URL = (
    "https://www.bccdc.ca/health-professionals/data-reports/respiratory-virus-data"
)
PHAC_INFOBASE_API_LANDING = "https://health-infobase.canada.ca/api/"

# Smaller LIMIT than 800: cuts peak RSS from PHAC JSON + Python object overhead on 512MB hosts;
# ~200 rows still spans many weeks across BC sites for percentile/trend logic.
_SQL_HISTORY = """
SELECT "Date", measureid, "Location", seven_day_rolling_avg
FROM wastewater_daily
WHERE pruid = 59 AND measureid IN ('covN2', 'rsv', 'fluA', 'fluB')
ORDER BY "Date" DESC
LIMIT 200
"""


def _level_from_percentile(pct: float) -> str:
    if pct >= 66.0:
        return "High"
    if pct >= 33.0:
        return "Medium"
    return "Low"


def _trend_word(current: float, previous: float | None) -> str | None:
    if previous is None or previous <= 0:
        return None
    ratio = current / previous
    if ratio > 1.12:
        return "Rising"
    if ratio < 0.88:
        return "Falling"
    return "Stable"


def _percentile_rank(value: float, series: list[float]) -> float:
    """0–100 rank of *value* within *series* (inclusive)."""
    if not series:
        return 50.0
    s = sorted(series)
    below = sum(1 for x in s if x < value)
    return 100.0 * below / len(s)


@dataclass
class RespiratoryBundle:
    ok: bool
    virus: dict[str, str]
    source_name: str
    source_url: str
    source_updated_label: str | None
    fetched_at: datetime
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _aggregate_by_date(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """
    Build date -> {covN2, rsv, flu_combined} using mean across BC sites for that day.
    flu_combined = max(fluA, fluB) per site, then mean across sites.
    """
    # site_key -> {date -> {measure -> val}}
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
        cov = measures.get("covN2")
        rsv = measures.get("rsv")
        fa = measures.get("fluA")
        fb = measures.get("fluB")
        flu_parts = [x for x in (fa, fb) if x is not None]
        flu_c = max(flu_parts) if flu_parts else None
        bucket = by_date.setdefault(d, {"covN2": [], "rsv": [], "flu": []})
        if cov is not None:
            bucket["covN2"].append(cov)
        if rsv is not None:
            bucket["rsv"].append(rsv)
        if flu_c is not None:
            bucket["flu"].append(flu_c)

    out: dict[str, dict[str, float]] = {}
    for d, b in by_date.items():
        out[d] = {
            "covN2": float(statistics.mean(b["covN2"])) if b["covN2"] else 0.0,
            "rsv": float(statistics.mean(b["rsv"])) if b["rsv"] else 0.0,
            "flu": float(statistics.mean(b["flu"])) if b["flu"] else 0.0,
        }
    return out


def fetch_respiratory_bc_signals() -> RespiratoryBundle:
    """
    Pull latest BC (pruid 59) wastewater signals and map to parent-friendly levels.

    Returns ok=False on transport/parse failure (caller should retain last-known-good).
    """
    fetched_at = datetime.now(timezone.utc)
    url = f"{HEALTH_INFOBASE_WASTEWATER_QUERY_URL}?q={quote(_SQL_HISTORY.strip())}"
    try:
        with http_client() as client:
            r = client.get(url)
            r.raise_for_status()
            rows = r.json()
    except Exception as e:
        log.exception("Respiratory (PHAC wastewater) fetch failed: %s", e)
        return RespiratoryBundle(
            ok=False,
            virus={"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"},
            source_name="Public Health Agency of Canada — Health Infobase (wastewater, BC)",
            source_url=PHAC_INFOBASE_API_LANDING,
            source_updated_label=None,
            fetched_at=fetched_at,
            error=str(e),
            extra={"bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL},
        )

    if not isinstance(rows, list) or not rows:
        log.error("Unexpected wastewater payload (not a non-empty list)")
        return RespiratoryBundle(
            ok=False,
            virus={"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"},
            source_name="Public Health Agency of Canada — Health Infobase (wastewater, BC)",
            source_url=PHAC_INFOBASE_API_LANDING,
            source_updated_label=None,
            fetched_at=fetched_at,
            error="empty_or_invalid_payload",
            extra={"bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL},
        )

    by_date = _aggregate_by_date(rows)
    del rows  # release large API list before further work (helps GC under memory pressure)

    if not by_date:
        return RespiratoryBundle(
            ok=False,
            virus={"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"},
            source_name="Public Health Agency of Canada — Health Infobase (wastewater, BC)",
            source_url=PHAC_INFOBASE_API_LANDING,
            source_updated_label=None,
            fetched_at=fetched_at,
            error="no_bc_rows_after_aggregate",
            extra={"bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL},
        )

    dates_sorted = sorted(by_date.keys(), reverse=True)
    latest_d = dates_sorted[0]
    prev_d = dates_sorted[1] if len(dates_sorted) > 1 else None

    def series_for(key: str) -> list[float]:
        return [by_date[d][key] for d in sorted(by_date.keys()) if key in by_date[d]]

    def level_for(key: str) -> str:
        hist = series_for(key)
        cur = by_date[latest_d][key]
        pct = _percentile_rank(cur, hist)
        lev = _level_from_percentile(pct)
        prev_v = by_date[prev_d][key] if prev_d else None
        tr = _trend_word(cur, prev_v)
        if tr:
            return f"{lev} ({tr})"
        return lev

    rsv_s = level_for("rsv")
    flu_s = level_for("flu")
    cov_s = level_for("covN2")

    virus = {"rsv": rsv_s, "flu": flu_s, "covid": cov_s}

    return RespiratoryBundle(
        ok=True,
        virus=virus,
        source_name="Public Health Agency of Canada — Health Infobase (wastewater, BC)",
        source_url=PHAC_INFOBASE_API_LANDING,
        source_updated_label=f"Latest sample date in feed: {latest_d} (7-day rolling average)",
        fetched_at=fetched_at,
        error=None,
        extra={
            "metric": "wastewater_seven_day_rolling_avg",
            "latest_aggregate_date": latest_d,
            "bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL,
            "disclaimer": (
                "Wastewater viral signal is a population-level indicator, not a clinical test result. "
                "See BCCDC for weekly clinical respiratory surveillance context."
            ),
        },
    )
