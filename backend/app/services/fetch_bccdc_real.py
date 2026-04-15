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
    Pull latest BC (pruid 59) wastewater signals; discover all published measures dynamically.
    ``virus`` keeps legacy rsv / flu (composite) / covid strings for summaries and hero cards.
    """
    fetched_at = datetime.now(timezone.utc)
    rows, err = fetch_bc_wastewater_rows()
    if err:
        log.warning("Respiratory (PHAC wastewater) fetch failed: %s", err)
        return RespiratoryBundle(
            ok=False,
            virus={"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"},
            ranking=[],
            source_name="Public Health Agency of Canada — Health Infobase (wastewater, BC)",
            source_url=PHAC_INFOBASE_API_LANDING,
            source_updated_label=None,
            fetched_at=fetched_at,
            error=str(err),
            extra={"bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL},
        )

    comp = compute_bc_wastewater(rows)
    if not comp.ok:
        return RespiratoryBundle(
            ok=False,
            virus={"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"},
            ranking=[],
            source_name="Public Health Agency of Canada — Health Infobase (wastewater, BC)",
            source_url=PHAC_INFOBASE_API_LANDING,
            source_updated_label=None,
            fetched_at=fetched_at,
            error=comp.error or "compute_failed",
            extra={"bccdc_clinical_reference_url": BCCDC_RESPIRATORY_HUMAN_URL},
        )

    latest_d = comp.latest_aggregate_date or ""
    return RespiratoryBundle(
        ok=True,
        virus=comp.virus_triple,
        ranking=comp.ranking,
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
