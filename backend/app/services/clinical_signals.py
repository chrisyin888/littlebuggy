"""
BC clinical respiratory virus detections — PHAC RVDSS (FluWatch+) laboratory data.

**Source**: Public Health Agency of Canada, *Respiratory Virus Detections in Canada*
weekly laboratory CSV (the same file that powers the FluWatch+ "Explore the data"
charts on Health Infobase):

    https://health-infobase.canada.ca/src/data/respiratory-virus-detections/RVD_WeeklyData.csv

Columns: region, province, week, weekorder, year, date, virus, tests, detections,
percentpositive. We use ``region == "British Columbia"`` rows — weekly *lab* percent
positivity per virus, reported by BC labs (Children's & Women's, BCCDC PHL, health
authority labs, …). This is the clinical counterpart to the PHAC wastewater feed in
``wastewater_signals``: wastewater only measures 4 pathogens, while RVDSS tracks 9
display series (after dropping the combined "Influenza" total): SARS-CoV-2,
Influenza A, Influenza B, RSV, EV/RV (entero/rhinovirus), HPIV (parainfluenza),
ADV (adenovirus), HMPV, HCoV (seasonal coronavirus).

**Level口径 (bands on percent positive)**: >= 10% → High, >= 3% → Medium, otherwise
Low. Trend compares the latest week with the previous week (ratio > 1.15 Rising,
< 0.87 Falling, else Stable). ``severity_score`` is derived from the level+trend
label via ``wastewater_signals.severity_score_from_label`` so clinical entries live
on exactly the same 0–4.2 scale as wastewater entries and the two can be merged
(see ``respiratory_merge``).
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.http_util import http_client
from app.services.wastewater_signals import severity_score_from_label

log = logging.getLogger(__name__)

RVD_WEEKLY_CSV_URL = (
    "https://health-infobase.canada.ca/src/data/respiratory-virus-detections/RVD_WeeklyData.csv"
)
RVD_LANDING_URL = "https://health-infobase.canada.ca/respiratory-virus-surveillance/explore.html"

# RVDSS virus label -> (canonical key, display name). "Influenza" (A+B total) is
# intentionally skipped: flu_a / flu_b carry the same information without double counting.
VIRUS_MAP: dict[str, tuple[str, str]] = {
    "SARS-CoV-2": ("covid", "COVID-19"),
    "Influenza A": ("flu_a", "Influenza A"),
    "Influenza B": ("flu_b", "Influenza B"),
    "RSV": ("rsv", "RSV"),
    "EV/RV": ("rhinovirus", "Enterovirus / Rhinovirus"),
    "HPIV": ("parainfluenza", "Parainfluenza"),
    "ADV": ("adenovirus", "Adenovirus"),
    "HMPV": ("hmpv", "hMPV"),
    "HCoV": ("seasonal_coronavirus", "Seasonal coronavirus"),
}


def level_from_positivity(pct: float) -> str:
    """Level bands on lab percent-positive (see module docstring for口径)."""
    if pct >= 10.0:
        return "High"
    if pct >= 3.0:
        return "Medium"
    return "Low"


def _trend_word(current: float, previous: float | None) -> str | None:
    if previous is None:
        return None
    if previous <= 0:
        return "Rising" if current >= 3.0 else None
    ratio = current / previous
    if ratio > 1.15:
        return "Rising"
    if ratio < 0.87:
        return "Falling"
    return "Stable"


@dataclass
class ClinicalBundle:
    ok: bool
    entries: list[dict[str, Any]] = field(default_factory=list)
    latest_week_ending: str | None = None
    error: str | None = None


def _parse_float(raw: Any) -> float | None:
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def compute_clinical_entries(csv_text: str) -> ClinicalBundle:
    """Parse RVD weekly CSV text → per-virus latest-week entries for British Columbia."""
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = [r for r in reader if (r.get("region") or "").strip() == "British Columbia"]
    except Exception as e:
        return ClinicalBundle(ok=False, error=f"csv_parse_failed: {e}")
    if not rows:
        return ClinicalBundle(ok=False, error="no_bc_rows")

    # virus -> {(year, week): row}; weeks ordered by the CSV's own weekorder/date.
    by_virus: dict[str, dict[tuple[int, int], dict[str, Any]]] = {}
    for r in rows:
        virus = (r.get("virus") or "").strip()
        if virus not in VIRUS_MAP:
            continue
        try:
            yw = (int(r.get("year") or 0), int(r.get("week") or 0))
        except (TypeError, ValueError):
            continue
        by_virus.setdefault(virus, {})[yw] = r
    if not by_virus:
        return ClinicalBundle(ok=False, error="no_known_virus_rows")

    entries: list[dict[str, Any]] = []
    latest_date_all: str | None = None
    for virus, weeks in by_virus.items():
        key, display = VIRUS_MAP[virus]
        # Order by the row's week-ending date (ground truth across epi-year boundaries).
        ordered = sorted(weeks, key=lambda yw: str(weeks[yw].get("date") or ""))
        cur_row = weeks[ordered[-1]]
        prev_row = weeks[ordered[-2]] if len(ordered) > 1 else None
        pct = _parse_float(cur_row.get("percentpositive"))
        if pct is None:
            continue
        prev_pct = _parse_float(prev_row.get("percentpositive")) if prev_row else None
        level = level_from_positivity(pct)
        trend = _trend_word(pct, prev_pct)
        label = f"{level} ({trend})" if trend else level
        week_ending = str(cur_row.get("date") or "").strip() or None
        if week_ending and (latest_date_all is None or week_ending > latest_date_all):
            latest_date_all = week_ending
        updated = datetime.now(timezone.utc)
        if week_ending:
            try:
                updated = datetime.strptime(week_ending, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        entries.append(
            {
                "key": key,
                "display_name": display,
                "value": pct,
                "metric": "percent_positive",
                "positivity_pct": pct,
                "detections": int(_parse_float(cur_row.get("detections")) or 0),
                "tests": int(_parse_float(cur_row.get("tests")) or 0),
                "severity_label": label,
                "severity_score": severity_score_from_label(label),
                "updated_at": updated.isoformat().replace("+00:00", "Z"),
                "source": "clinical",
            }
        )
    if not entries:
        return ClinicalBundle(ok=False, error="no_usable_entries")
    return ClinicalBundle(ok=True, entries=entries, latest_week_ending=latest_date_all)


def fetch_clinical_bc_signals() -> ClinicalBundle:
    """HTTP GET the RVDSS weekly CSV and compute BC clinical entries."""
    try:
        with http_client() as client:
            r = client.get(RVD_WEEKLY_CSV_URL)
            r.raise_for_status()
            text = r.text
    except Exception as e:
        log.warning("RVDSS clinical CSV fetch failed: %s", e)
        return ClinicalBundle(ok=False, error=str(e))
    return compute_clinical_entries(text)
