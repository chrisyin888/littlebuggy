"""
Fetch structured respiratory virus trend signals for the public /virus-trends endpoint.

**Sources**

1. **BCCDC respiratory virus data page** — scraped for context (meta description, ISO dates).

2. **PHAC Health Infobase BC wastewater** — all ``measureid`` values published for BC (pruid=59);
   levels are percentile buckets vs history (see ``wastewater_signals``). Population-level proxies only.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup

from app.services.fetch_bccdc_real import fetch_respiratory_bc_signals
from app.services.http_util import http_client
from app.services.wastewater_signals import PHAC_INFOBASE_API_LANDING

log = logging.getLogger(__name__)

BCCDC_RESPIRATORY_URL = (
    "https://www.bccdc.ca/health-professionals/data-reports/respiratory-virus-data"
)
# Backward-compatible alias used in stored JSON.
PHAC_LANDING = PHAC_INFOBASE_API_LANDING


def _scrape_bccdc_report_date(html: str) -> str | None:
    """ISO date only if clearly present in page meta (avoid guessing from random HTML dates)."""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", meta["content"])
        if m:
            return m.group(1)
    return None


def _build_summary_from_ranking(ranking: list[dict[str, Any]]) -> str:
    if not ranking:
        return "No BC wastewater measures were available from the public feed this run."
    parts = [f"{e.get('display_name', 'Signal')}: {e.get('severity_label', 'Unknown')}" for e in ranking]
    return "Latest BC respiratory signals (PHAC wastewater + lab detections, stronger signal shown): " + "; ".join(parts) + "."


def _viruses_legacy_shape(ranking: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Strips ranking to the older {key, name, level} list for clients that expect ``viruses``."""
    out: list[dict[str, str]] = []
    for e in ranking:
        out.append(
            {
                "key": str(e.get("key") or ""),
                "name": str(e.get("display_name") or e.get("key") or "Signal"),
                "level": str(e.get("severity_label") or "Unknown"),
            }
        )
    return out


@dataclass
class VirusTrendsFetchResult:
    ok: bool
    source_report_date: str | None
    summary: str
    viruses: list[dict[str, str]]
    ranking: list[dict[str, Any]]
    source_url: str
    levels_detail: str
    error: str | None = None


def fetch_virus_trends() -> VirusTrendsFetchResult:
    """
    Pull BCCDC page (metadata) + PHAC BC wastewater rows; dynamic measures + sorted ranking.
    """
    viruses_unknown: list[dict[str, str]] = []

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

    # Merged ranking: PHAC BC wastewater (4 pathogens) + PHAC RVDSS BC lab
    # detections (9 series) — see respiratory_merge for the merge口径.
    bundle = fetch_respiratory_bc_signals()
    if not bundle.ok:
        log.warning("Respiratory bundle fetch failed: %s", bundle.error)
        return VirusTrendsFetchResult(
            ok=False,
            source_report_date=source_report_date,
            summary="Unable to refresh virus signal levels from public feeds right now.",
            viruses=viruses_unknown,
            ranking=[],
            source_url=BCCDC_RESPIRATORY_URL,
            levels_detail="Levels normally come from PHAC Health Infobase (BC wastewater + RVDSS lab data).",
            error=str(bundle.error),
        )

    ranking = bundle.ranking
    viruses = _viruses_legacy_shape(ranking)
    summary = _build_summary_from_ranking(ranking)
    detail = (
        "Levels merge PHAC BC wastewater (7-day rolling average, percentile vs history) with "
        "PHAC RVDSS lab percent-positive for BC; per pathogen the stronger signal is shown. "
        f"{bundle.source_updated_label or ''}".strip()
    )

    return VirusTrendsFetchResult(
        ok=True,
        source_report_date=source_report_date,
        summary=summary,
        viruses=viruses,
        ranking=ranking,
        source_url=BCCDC_RESPIRATORY_URL,
        levels_detail=detail,
        error=None,
    )


def payload_from_ranking(
    ranking: list[dict[str, Any]],
    source_report_date: str | None = None,
) -> dict[str, Any]:
    """
    Build a virus-trends payload dict from an already-computed merged ranking.

    Used by the snapshot pipeline (a cron that provably runs daily) to keep
    ``virus_trends_latest`` populated even if the dedicated virus-trends cron
    is missing or failing on the host.
    """
    return {
        "source_report_date": source_report_date,
        "source_name": "BCCDC",
        "summary": _build_summary_from_ranking(ranking),
        "viruses": _viruses_legacy_shape(ranking),
        "ranking": ranking,
        "source_url": BCCDC_RESPIRATORY_URL,
        "levels_method": (
            "Levels merge PHAC BC wastewater (percentile vs history) with PHAC RVDSS "
            "lab percent-positive for BC; per pathogen the stronger signal is shown."
        ),
        "phac_reference_url": PHAC_LANDING,
    }


def fetch_result_to_payload_dict(result: VirusTrendsFetchResult) -> dict[str, Any]:
    """Shape written to JSON / returned from refresh (without checked_at)."""
    return {
        "source_report_date": result.source_report_date,
        "source_name": "BCCDC",
        "summary": result.summary,
        "viruses": result.viruses,
        "ranking": result.ranking,
        "source_url": result.source_url,
        "levels_method": result.levels_detail,
        "phac_reference_url": PHAC_LANDING,
    }
