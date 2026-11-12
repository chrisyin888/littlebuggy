"""
Merge the two official PHAC respiratory signals into ONE dynamic ranking.

Sources (both PHAC Health Infobase, both mapped onto the same Low/Medium/High
severity scale and the same 0–4.2 ``severity_score``):

* **Wastewater** (``wastewater_signals``) — BC wastewater 7-day averages, level =
  percentile vs that measure's own history. Only 4 pathogens are measured.
* **Clinical** (``clinical_signals``) — RVDSS lab percent-positive for BC.
  9 display series, including entero/rhinovirus, parainfluenza, adenovirus,
  hMPV and seasonal coronavirus, which wastewater never sees.

**Merge口径**: for each pathogen, the merged entry takes the *stronger* of the
available source scores (``max``) — whichever surveillance system currently
shows more activity wins the slot, and the entry's level/trend label comes from
that winning source (ties go to the clinical entry: lab detections are the more
direct measure). Both raw metrics are preserved on the entry
(``positivity_pct`` for clinical, ``wastewater_value`` for wastewater) and
``value``/``metric`` describe the winning source's number.

Sorting: severity_score desc, then clinical percent-positive desc, then
wastewater value desc, then key — so whatever is actually circulating floats
to the top and quiet pathogens sink or fall out of the homepage's visible rows.
"""

from __future__ import annotations

from typing import Any


def _f(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def merge_rankings(
    wastewater_ranking: list[dict[str, Any]] | None,
    clinical_entries: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    ww = {str(e.get("key")): e for e in (wastewater_ranking or []) if e.get("key")}
    cl = {str(e.get("key")): e for e in (clinical_entries or []) if e.get("key")}

    merged: list[dict[str, Any]] = []
    for key in sorted(set(ww) | set(cl)):
        w = ww.get(key)
        c = cl.get(key)
        w_score = _f(w.get("severity_score")) if w else None
        c_score = _f(c.get("severity_score")) if c else None
        # Winner: clinical wins ties (lab detections are the more direct measure).
        clinical_wins = c is not None and (w is None or (c_score or 0.0) >= (w_score or 0.0))
        win = c if clinical_wins else w
        assert win is not None
        entry: dict[str, Any] = {
            "key": key,
            "display_name": win.get("display_name") or (c or w).get("display_name") or key,
            "value": win.get("value"),
            "metric": win.get("metric") or ("wastewater_7d_avg" if w is win else "percent_positive"),
            "severity_label": win.get("severity_label") or "Unknown",
            "severity_score": max(x for x in (w_score, c_score) if x is not None),
            "updated_at": max(
                str(x.get("updated_at") or "") for x in (w, c) if x is not None
            )
            or win.get("updated_at"),
            "sources": [s for s, x in (("wastewater", w), ("clinical", c)) if x is not None],
        }
        if c is not None:
            entry["positivity_pct"] = _f(c.get("positivity_pct"))
        if w is not None:
            entry["wastewater_value"] = _f(w.get("value"))
        merged.append(entry)

    def _sort_key(e: dict[str, Any]) -> tuple[float, float, float, str]:
        pos = e.get("positivity_pct")
        wv = e.get("wastewater_value")
        return (
            -float(e.get("severity_score") or 0.0),
            -float(pos) if pos is not None else float("inf"),
            -float(wv) if wv is not None else float("inf"),
            str(e.get("key")),
        )

    merged.sort(key=_sort_key)
    return merged
