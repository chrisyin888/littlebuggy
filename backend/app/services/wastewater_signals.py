"""
BC (pruid 59) PHAC wastewater: dynamic measure discovery — no fixed measureid IN list.

Builds per-measure levels (percentile vs history), composite flu for legacy homepage triple,
and a severity-sorted ranking list for API consumers.
New pathogens published by PHAC are automatically ingested; add entries to
``app.config.pathogen_catalog`` to enrich their display labels and symptoms.
"""

from __future__ import annotations

import logging
import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from urllib.parse import quote

from app.config.pathogen_catalog import get_display_label, virus_triple_from_ranking
from app.services.http_util import http_client

log = logging.getLogger(__name__)

HEALTH_INFOBASE_WASTEWATER_QUERY_URL = "https://health-infobase.canada.ca/api/wastewater/query"
PHAC_INFOBASE_API_LANDING = "https://health-infobase.canada.ca/api/"

# Wide net: all measures published for BC; cap rows for small dyno memory.
_SQL_BC_ALL_MEASURES = """
SELECT "Date", measureid, "Location", seven_day_rolling_avg
FROM wastewater_daily
WHERE pruid = 59
ORDER BY "Date" DESC
LIMIT 8000
"""


def measure_id_to_key(measureid: str) -> str:
    """Normalize upstream measureid to a stable snake_case API key."""
    raw = (measureid or "").strip()
    if not raw:
        return "unknown"
    low = raw.lower()
    if low in ("covn2", "sars-cov-2", "sars_cov_2"):
        return "covid"
    if low == "flua":
        return "flu_a"
    if low == "flub":
        return "flu_b"
    cleaned = re.sub(r"[^a-z0-9]+", "_", low).strip("_")
    return cleaned or "unknown"


def display_name_for_measure(measureid: str, key: str) -> str:
    """Return display label from the pathogen catalog (or auto-generated title-case)."""
    return get_display_label(key, measureid)


def _split_level_trend(s: str) -> tuple[str, str | None]:
    t = (s or "").strip()
    if not t:
        return "Unknown", None
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", t)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return t, None


def severity_score_from_label(full_label: str) -> float:
    """Aligns loosely with frontend card ordering: higher = more concerning."""
    level, trend = _split_level_trend(full_label)
    L = level.lower()
    if "unknown" in L:
        base = 0.0
    elif "very" in L and "high" in L:
        base = 4.2
    elif "high" in L or "severe" in L or "extreme" in L:
        base = 3.8
    elif "elevated" in L:
        base = 3.1
    elif "medium" in L or "moderate" in L:
        base = 2.5
    elif "low" in L or "minimal" in L:
        base = 1.0
    else:
        base = 2.0
    if trend:
        tl = trend.lower()
        if "rising" in tl or "spiking" in tl:
            base += 0.12
        elif "falling" in tl or "declining" in tl:
            base -= 0.08
    return base


def _percentile_rank(value: float, series: list[float]) -> float:
    if not series:
        return 50.0
    s = sorted(series)
    below = sum(1 for x in s if x < value)
    return 100.0 * below / len(s)


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


def _aggregate_by_site(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    by_site: dict[tuple[str, str], dict[str, float]] = {}
    for r in rows:
        d = str(r.get("Date") or "")
        loc = str(r.get("Location") or "")
        mid = str(r.get("measureid") or "").strip()
        if not mid:
            continue
        try:
            val = float(r.get("seven_day_rolling_avg") or 0.0)
        except (TypeError, ValueError):
            continue
        if not d:
            continue
        key = (d, loc)
        by_site.setdefault(key, {})[mid] = val
    return by_site


def _mean_by_date_per_measure(
    by_site: dict[tuple[str, str], dict[str, float]],
) -> dict[str, dict[str, float]]:
    """
    date -> measureid -> mean across BC sites for that day.
    Also builds composite 'flu' from max(fluA, fluB) per site when both exist.
    """
    by_date: dict[str, dict[str, list[float]]] = {}
    flu_by_date: dict[str, list[float]] = {}

    for (d, _loc), measures in by_site.items():
        bucket = by_date.setdefault(d, {})
        for mid, val in measures.items():
            bucket.setdefault(mid, []).append(val)

        fa = measures.get("fluA")
        fb = measures.get("fluB")
        flu_parts = [x for x in (fa, fb) if x is not None]
        if flu_parts:
            flu_by_date.setdefault(d, []).append(max(flu_parts))

    out: dict[str, dict[str, float]] = {}
    for d, mids in by_date.items():
        out[d] = {mid: float(statistics.mean(vals)) for mid, vals in mids.items() if vals}
        if d in flu_by_date and flu_by_date[d]:
            out[d]["flu"] = float(statistics.mean(flu_by_date[d]))

    return out


def _level_string_for_series(
    by_date: dict[str, dict[str, float]],
    measure_key: str,
    *,
    latest_d: str,
    prev_d: str | None,
) -> str:
    """measure_key is a key in by_date[d] (e.g. covN2, rsv, flu, fluA)."""

    def series_for(k: str) -> list[float]:
        return [by_date[d][k] for d in sorted(by_date.keys()) if k in by_date[d]]

    hist = series_for(measure_key)
    if latest_d not in by_date or measure_key not in by_date[latest_d]:
        return "Unknown"
    cur = by_date[latest_d][measure_key]
    pos = [x for x in hist if x > 0]
    if cur <= 0 and not pos:
        return "Unknown"
    use = pos if pos else hist
    pct = _percentile_rank(cur, use)
    lev = _level_from_percentile(pct)
    prev_v = by_date[prev_d][measure_key] if prev_d and prev_d in by_date and measure_key in by_date[prev_d] else None
    tr = _trend_word(cur, prev_v)
    if tr:
        return f"{lev} ({tr})"
    return lev


def _parse_date_for_updated_at(latest_d: str) -> datetime:
    try:
        return datetime.strptime(latest_d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


@dataclass
class WastewaterComputation:
    ok: bool
    latest_aggregate_date: str | None
    by_date: dict[str, dict[str, float]]
    dates_sorted: list[str]
    ranking: list[dict[str, Any]]
    virus_triple: dict[str, str]
    error: str | None = None


def compute_bc_wastewater(rows: list[dict[str, Any]] | None) -> WastewaterComputation:
    """
    From raw PHAC wastewater rows (list of dicts), compute dynamic ranking + rsv/flu/covid strings.
    """
    _EMPTY_TRIPLE = {"rsv": "Unknown", "flu": "Unknown", "covid": "Unknown"}

    if not isinstance(rows, list) or not rows:
        return WastewaterComputation(
            ok=False,
            latest_aggregate_date=None,
            by_date={},
            dates_sorted=[],
            ranking=[],
            virus_triple=_EMPTY_TRIPLE,
            error="empty_or_invalid_payload",
        )

    by_site = _aggregate_by_site(rows)
    by_date = _mean_by_date_per_measure(by_site)
    del by_site

    if not by_date:
        return WastewaterComputation(
            ok=False,
            latest_aggregate_date=None,
            by_date={},
            dates_sorted=[],
            ranking=[],
            virus_triple=_EMPTY_TRIPLE,
            error="no_bc_rows_after_aggregate",
        )

    dates_sorted = sorted(by_date.keys(), reverse=True)
    latest_d = dates_sorted[0]
    prev_d = dates_sorted[1] if len(dates_sorted) > 1 else None

    # All measure IDs seen anywhere in the series (dynamic).
    all_mids: set[str] = set()
    for d in by_date.values():
        all_mids.update(k for k in d.keys() if k != "flu")

    ranking_raw: list[dict[str, Any]] = []
    for mid in sorted(all_mids):
        key = measure_id_to_key(mid)
        label = display_name_for_measure(mid, key)
        lev_s = _level_string_for_series(
            by_date,
            mid,
            latest_d=latest_d,
            prev_d=prev_d,
        )
        val = None
        if latest_d in by_date and mid in by_date[latest_d]:
            val = float(by_date[latest_d][mid])
        score = severity_score_from_label(lev_s)
        ranking_raw.append(
            {
                "key": key,
                "display_name": label,
                "value": val,
                "severity_label": lev_s,
                "severity_score": score,
                "updated_at": _parse_date_for_updated_at(latest_d),
            }
        )

    def _rank_sort_key(e: dict[str, Any]) -> tuple[float, float, str]:
        v = e.get("value")
        val_part = -float(v) if v is not None else float("inf")
        return (-float(e["severity_score"]), val_part, str(e["key"]))

    ranking_raw.sort(key=_rank_sort_key)

    # Serialize updated_at for JSON
    ranking: list[dict[str, Any]] = []
    for e in ranking_raw:
        u = e["updated_at"]
        iso = u.isoformat().replace("+00:00", "Z") if isinstance(u, datetime) else str(u)
        ranking.append(
            {
                "key": e["key"],
                "display_name": e["display_name"],
                "value": e["value"],
                "severity_label": e["severity_label"],
                "severity_score": e["severity_score"],
                "updated_at": iso,
            }
        )

    # Derive virus_triple dynamically from the final ranking (no hardcoded keys).
    # virus_triple_from_ranking guarantees rsv/flu/covid are always present for
    # backward-compat consumers while also carrying any new pathogens.
    virus_triple = virus_triple_from_ranking(ranking)

    return WastewaterComputation(
        ok=True,
        latest_aggregate_date=latest_d,
        by_date=by_date,
        dates_sorted=dates_sorted,
        ranking=ranking,
        virus_triple=virus_triple,
        error=None,
    )


def fetch_bc_wastewater_rows() -> tuple[list[dict[str, Any]] | None, str | None]:
    """HTTP GET PHAC SQL API; returns (rows, error_message)."""
    url = f"{HEALTH_INFOBASE_WASTEWATER_QUERY_URL}?q={quote(_SQL_BC_ALL_MEASURES.strip())}"
    try:
        with http_client() as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.exception("PHAC wastewater fetch failed: %s", e)
        return None, str(e)
    if not isinstance(data, list):
        return None, "invalid_payload_type"
    return data, None
