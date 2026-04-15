"""
Turn raw homepage snapshot dicts into short, family-friendly copy for static JSON.

Avoids long technical paragraphs (wastewater API jargon, etc.) on the public site.
compose_short_summary is now dynamic — it reads from respiratory_ranking when
available, so new pathogens appear automatically without code changes here.
"""

from __future__ import annotations

import json
from typing import Any


def _t(s: str | None) -> str:
    x = (s or "").strip()
    return x if x else "Unknown"


def _is_unavailable(x: str) -> bool:
    return not x.strip() or "unavailable" in x.lower()


def simplify_air_quality_phrase(air: str) -> str:
    """Plain-language air line for parents (English)."""
    if _is_unavailable(air):
        return "we don't have a fresh air-quality read right now"
    low = air.lower()
    if "low risk" in low or "good" in low or "~1" in low or "~2" in low:
        return "comfortable for most kids (lower risk on the AQHI scale)"
    if "moderate" in low or "fair" in low or "~3" in low or "~4" in low:
        return "moderate—sensitive kiddos might feel it a bit more outside"
    if "high risk" in low or "unhealthy" in low or "poor" in low:
        return "rougher outside today—worth a lighter play plan"
    # Shorten very long AQHI strings
    if len(air) > 72:
        return air[:69].rstrip(" ,—") + "…"
    return air


def simplify_weather_phrase(weather: str) -> str:
    if _is_unavailable(weather):
        return "weather didn't load this run"
    if len(weather) > 64:
        return weather[:61].rstrip(" ·") + "…"
    return weather


def _respiratory_phrase_from_ranking(ranking: list[dict[str, Any]]) -> str:
    """
    Build a short, friendly respiratory phrase from the dynamic ranking list.
    Informational only — never implies diagnosis or clinical finding.
    """
    usable = [
        e for e in ranking
        if str(e.get("severity_label") or "").lower() not in ("unknown", "")
        and e.get("display_name")
    ]
    if not usable:
        return "respiratory wastewater signals weren't available this run"

    # Mention up to top 3 by severity (ranking is already sorted)
    top = usable[:3]
    parts = [
        f"{e['display_name']} {e['severity_label'].split('(')[0].strip().lower()}"
        for e in top
    ]
    if len(parts) == 1:
        signal_str = parts[0]
    elif len(parts) == 2:
        signal_str = f"{parts[0]} and {parts[1]}"
    else:
        signal_str = f"{parts[0]}, {parts[1]}, and {parts[2]}"

    extra = ""
    if len(usable) > 3:
        n = len(usable) - 3
        extra = f" (and {n} more pathogen{'s' if n > 1 else ''} tracked)"

    return f"wastewater signals showing {signal_str}{extra}"


def compose_short_summary(
    *,
    region: str,
    air_quality: str,
    weather: str,
    outdoor_feel: str,
    # Optional dynamic ranking (preferred over fixed rsv/flu/covid)
    ranking: list[dict[str, Any]] | None = None,
    # Legacy fixed fields — kept for backward compat; ignored when ranking is present
    rsv: str = "",
    flu: str = "",
    covid: str = "",
) -> str:
    """
    Two short sentences for parents (English). UI may still localize cards separately.
    Uses ``ranking`` when available for a fully dynamic pathogen list.
    """
    place = _t(region) or "Metro Vancouver"
    air_f = simplify_air_quality_phrase(air_quality)
    wx_f = simplify_weather_phrase(weather)
    outdoor = _t(outdoor_feel)
    if _is_unavailable(outdoor):
        outdoor = "a mixed bag—check the cards above"

    if ranking:
        resp_phrase = _respiratory_phrase_from_ranking(ranking)
        s1 = (
            f"In this week's snapshot for {place}, {resp_phrase}—"
            "neighbourhood context, not a test result for your child."
        )
    else:
        # Legacy path: use rsv/flu/covid strings
        s1 = (
            f"In this week's snapshot for {place}, RSV looks {_t(rsv).lower()}, "
            f"flu {_t(flu).lower()}, and COVID {_t(covid).lower()}—"
            "neighbourhood context, not a test result for your child."
        )

    s2 = f"Air: {air_f}. Weather: {wx_f}. For most families we'd call it \u201c{outdoor}\u201d outside today."
    return s1 + " " + s2


LIVE_VS_ILLUSTRATIVE_EN = (
    "What's live in this snapshot: respiratory wastewater signals, air quality, and weather cards. "
    "What's playful: the map bubbles and some story cards—they're mood, not official area data."
)


def parent_facing_data_quality_note(raw_note: str | None) -> str | None:
    """Replace stack traces / fetch errors with one calm sentence."""
    if not raw_note or not str(raw_note).strip():
        return None
    low = raw_note.lower()
    if "respiratory" in low or "aqhi" in low or "weather" in low:
        return "We couldn't refresh every feed perfectly this time—treat the numbers as a rough, friendly guide."
    return "Something hiccuped while refreshing sources—still fine to use this as a starting point."


def polish_homepage_summary_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Return a shallow copy suitable for ``public/data/homepage-summary.json``.

    Sets ``short_summary``, overwrites ``summary`` to match, adds ``live_vs_illustrative_note``,
    and softens ``data_quality_note`` when present.
    """
    out = dict(raw)
    region = str(out.get("region") or "Metro Vancouver")
    air = str(out.get("air_quality") or "")
    wx = str(out.get("weather") or "")
    outdoor = str(out.get("outdoor_feel") or "")

    # Use the dynamic ranking when available
    ranking_raw = out.get("respiratory_ranking")
    ranking: list[dict[str, Any]] | None = None
    if isinstance(ranking_raw, list) and ranking_raw:
        ranking = ranking_raw
    elif isinstance(ranking_raw, str) and ranking_raw.strip():
        try:
            loaded = json.loads(ranking_raw)
            if isinstance(loaded, list):
                ranking = loaded
        except Exception:
            pass

    try:
        short = compose_short_summary(
            region=region,
            air_quality=air,
            weather=wx,
            outdoor_feel=outdoor,
            ranking=ranking,
            # Legacy fallback fields
            rsv=str(out.get("rsv") or ""),
            flu=str(out.get("flu") or ""),
            covid=str(out.get("covid") or ""),
        )
    except Exception:
        fallback = str(out.get("summary") or "").strip()
        short = (fallback[:500] + "…") if len(fallback) > 500 else (fallback or "Summary not ready this run.")
    out["short_summary"] = short
    out["summary"] = short
    out["live_vs_illustrative_note"] = LIVE_VS_ILLUSTRATIVE_EN
    dq = out.get("data_quality_note")
    out["data_quality_note"] = parent_facing_data_quality_note(dq if isinstance(dq, str) else None)
    return out
