"""
BC respiratory *signals* for LittleBuggy — PHAC Health Infobase BC wastewater (dynamic measures).

See ``wastewater_signals`` for aggregation details. This module exposes
``fetch_respiratory_bc_signals`` and stable URL constants for callers.

``virus`` dict keeps legacy rsv/flu/covid strings for callers that still need them
(e.g. build_summary fallback path). The primary output for all new consumers is the
``ranking`` list, which is fully dynamic and includes whatever pathogens PHAC publishes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.clinical_signals import RVD_LANDING_URL, fetch_clinical_bc_signals
from app.services.respiratory_merge import merge_rankings
from app.services.wastewater_signals import (
    PHAC_INFOBASE_API_LANDING,
    compute_bc_wastewater,
    fetch_bc_wastewater_rows,
)

log = logging.getLogger(__name__)

# Backward-compatible exports (other modules import these names).
HEALTH_INFOBASE_WASTEWATER_QUERY_URL = "https://health-infobase.canada.ca/api/wastewater/query"
BCCDC_RESPIRATORY_HUMAN_URL = (
    "https://www.bccdc.ca/health-professionals/data-reports/respiratory-virus-data"
)


@dataclass
class RespiratoryBundle:
    ok: bool
    virus: dict[str, str]
    """Severity-sorted dynamic measure rows (may include pathogens beyond the homepage triple)."""

    ranking: list[dict[str, Any]]
    source_name: str
    source_url: str
    source_updated_label: str | None
    fetched_at: datetime
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def fetch_respiratory_bc_signals() -> RespiratoryBundle:
    """
    Pull latest BC respiratory signals from BOTH PHAC feeds and merge them into one
    dynamic ranking (see ``respiratory_merge`` for the merge口径):

    * wastewater (pruid 59, measures discovered dynamically) — 4 pathogens;
    * RVDSS clinical lab detections for BC — 9 display series incl. entero/rhinovirus.

    Either feed failing is non-fatal: the ranking is built from whichever succeeded.
    ``virus`` keeps legacy rsv / flu (composite) / covid strings (wastewater-derived)
    for summaries and hero cards.
    """
    fetched_at = datetime.now(timezone.utc)
    source_name = (
        "Public Health Agency of Canada — Health Infobase "
        "(BC wastewater + RVDSS lab detections)"
    )

    # --- wastewater arm ---
    ww_ranking: list = []
    virus_triple = {"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"}
    ww_error: str | None = None
    latest_d = ""
    rows, err = fetch_bc_wastewater_rows()
    if err:
        log.warning("Respiratory (PHAC wastewater) fetch failed: %s", err)
        ww_error = str(err)
    else:
        comp = compute_bc_wastewater(rows)
        if comp.ok:
            ww_ranking = comp.ranking
            virus_triple = comp.virus_triple
            latest_d = comp.latest_aggregate_date or ""
        else:
            ww_error = comp.error or "compute_failed"

    # --- clinical arm (RVDSS) ---
    clinical = fetch_clinical_bc_signals()
    if not clinical.ok:
        log.warning("Respiratory (RVDSS clinical) fetch failed: %s", clinical.error)

    if not ww_ranking and not clinical.ok:
        return RespiratoryBundle(
            ok=False,
            virus=virus_triple,
            ranking=[],
            source_name=source_name,
            source_url=PHAC_INFOBASE_API_LANDING,
            source_updated_label=None,
            fetched_at=fetched_at,
            error=ww_error or (clinical.error or "both_feeds_failed"),
            extra={"bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL},
        )

    ranking = merge_rankings(ww_ranking, clinical.entries if clinical.ok else [])
    label_parts = []
    if latest_d:
        label_parts.append(f"Wastewater latest sample: {latest_d}")
    if clinical.ok and clinical.latest_week_ending:
        label_parts.append(f"Lab detections week ending: {clinical.latest_week_ending}")
    return RespiratoryBundle(
        ok=True,
        virus=virus_triple,
        ranking=ranking,
        source_name=source_name,
        source_url=PHAC_INFOBASE_API_LANDING,
        source_updated_label="; ".join(label_parts) or None,
        fetched_at=fetched_at,
        error=None,
        extra={
            "metric": "merged_wastewater_and_clinical",
            "latest_aggregate_date": latest_d,
            "clinical_ok": clinical.ok,
            "clinical_latest_week_ending": clinical.latest_week_ending,
            "clinical_source_url": RVD_LANDING_URL,
            "bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL,
            "disclaimer": (
                "Wastewater is a population-level indicator and lab percent-positive "
                "reflects tested patients; neither is a test result for your child. "
                "See BCCDC for weekly clinical respiratory surveillance context."
            ),
        },
    )
