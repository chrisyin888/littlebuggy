"""
Turn raw homepage snapshot dicts into short, family-friendly copy for static JSON.

Avoids long technical paragraphs (wastewater API jargon, etc.) on the public site.
"""

from __future__ import annotations

from typing import Any


def _t(s: str | None) -> str:
    x = (s or "").strip()
    return x if x else "Unknown"


def _is_unavailable(x: str) -> bool:
    return not x.strip() or "unavailable" in x.lower()


def simplify_air_quality_phrase(air: str) -> str:
    """Plain-language air line for parents (English)."""
    if _is_unavailable(air):
        return "we don’t have a fresh air-quality read right now"
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
        return "weather didn’t load this run"
    if len(weather) > 64:
        return weather[:61].rstrip(" ·") + "…"
    return weather


def compose_short_summary(
    *,
    region: str,
    rsv: str,
    flu: str,
    covid: str,
    air_quality: str,
    weather: str,
    outdoor_feel: str,
) -> str:
    """Two short sentences for parents (English). UI may still localize cards separately."""
    place = _t(region) or "Metro Vancouver"
    air_f = simplify_air_quality_phrase(air_quality)
    wx_f = simplify_weather_phrase(weather)
    outdoor = _t(outdoor_feel)
    if _is_unavailable(outdoor):
        outdoor = "a mixed bag—check the cards above"

    s1 = (
        f"In this week’s snapshot for {place}, RSV looks {_t(rsv).lower()}, "
        f"flu {_t(flu).lower()}, and COVID {_t(covid).lower()}—"
        "neighbourhood context, not a test result for your child."
    )
    s2 = f"Air: {air_f}. Weather: {wx_f}. For most families we’d call it “{outdoor}” outside today."
    return s1 + " " + s2


LIVE_VS_ILLUSTRATIVE_EN = (
    "What’s live in this snapshot: RSV, flu, COVID, air, and weather cards. "
    "What’s playful: the map bubbles and some story cards—they’re mood, not official area data."
)


def parent_facing_data_quality_note(raw_note: str | None) -> str | None:
    """Replace stack traces / fetch errors with one calm sentence."""
    if not raw_note or not str(raw_note).strip():
        return None
    low = raw_note.lower()
    if "respiratory" in low or "aqhi" in low or "weather" in low:
        return "We couldn’t refresh every feed perfectly this time—treat the numbers as a rough, friendly guide."
    return "Something hiccuped while refreshing sources—still fine to use this as a starting point."


def polish_homepage_summary_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Return a shallow copy suitable for ``public/data/homepage-summary.json``.

    Sets ``short_summary``, overwrites ``summary`` to match, adds ``live_vs_illustrative_note``,
    and softens ``data_quality_note`` when present.
    """
    out = dict(raw)
    region = str(out.get("region") or "Metro Vancouver")
    rsv = str(out.get("rsv") or "")
    flu = str(out.get("flu") or "")
    covid = str(out.get("covid") or "")
    air = str(out.get("air_quality") or "")
    wx = str(out.get("weather") or "")
    outdoor = str(out.get("outdoor_feel") or "")

    try:
        short = compose_short_summary(
            region=region,
            rsv=rsv,
            flu=flu,
            covid=covid,
            air_quality=air,
            weather=wx,
            outdoor_feel=outdoor,
        )
    except Exception:
        fallback = str(out.get("summary") or "").strip()
        short = (fallback[:500] + "…") if len(fallback) > 500 else (fallback or "Summary unavailable this run.")
    out["short_summary"] = short
    out["summary"] = short
    out["live_vs_illustrative_note"] = LIVE_VS_ILLUSTRATIVE_EN
    dq = out.get("data_quality_note")
    out["data_quality_note"] = parent_facing_data_quality_note(dq if isinstance(dq, str) else None)
    return out
