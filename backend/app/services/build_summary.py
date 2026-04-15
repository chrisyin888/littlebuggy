"""
Parent-friendly outdoor feel + summary paragraph from real (or partially missing) inputs.

``build_summary`` now accepts an optional ``ranking`` list so it can generate
dynamic text that mentions whichever pathogens are actually present in the feed,
rather than always saying RSV / flu / COVID. Legacy callers that pass only
``virus_data`` still work unchanged.
"""

from __future__ import annotations

from typing import Any


def _weather_is_wet(weather: str) -> bool:
    w = weather.strip().lower()
    if "unavailable" in w:
        return False
    return any(x in w for x in ("rain", "storm", "drizzle", "showers", "shower"))


def _air_is_concerning(air_quality: str) -> bool:
    a = air_quality.strip().lower()
    if "unavailable" in a:
        return False
    return "high risk" in a or "very high" in a or "unhealthy" in a or "poor" in a


def _respiratory_sentence_from_ranking(ranking: list[dict[str, Any]]) -> str:
    """
    Build an informational sentence from the top ranked pathogens.
    Never implies diagnosis — uses population-level wastewater framing.
    """
    usable = [
        e for e in ranking
        if str(e.get("severity_label") or "").lower() not in ("unknown", "")
    ]
    if not usable:
        return (
            "We couldn't refresh respiratory wastewater signals this run — the data sources panel "
            "has the technical note."
        )
    # Mention up to the top 3 by severity (ranking is already sorted)
    top = usable[:3]
    parts = [
        f"{e['display_name']} around {e['severity_label'].split('(')[0].strip().lower()}"
        for e in top
    ]
    if len(parts) == 1:
        signal_summary = parts[0]
    elif len(parts) == 2:
        signal_summary = f"{parts[0]} and {parts[1]}"
    else:
        signal_summary = f"{parts[0]}, {parts[1]}, and {parts[2]}"

    extra = ""
    if len(usable) > 3:
        n = len(usable) - 3
        extra = f" ({n} additional pathogen{'s' if n > 1 else ''} also tracked)"

    return (
        f"BC wastewater surveillance (a population-level signal, not a clinic test) is showing "
        f"{signal_summary}{extra}. "
        f"Clinical trends are summarized separately by BCCDC in their weekly respiratory updates."
    )


def _respiratory_sentence_from_virus_dict(virus_data: dict[str, str]) -> str:
    """
    Legacy fallback: build sentence from a {key: level} dict.
    Used when no ranking list is available.
    """
    # Pick whichever keys are present and not Unknown
    known = {k: v for k, v in virus_data.items() if not str(v).lower().startswith("unknown")}
    if not known:
        return (
            "We couldn't refresh respiratory wastewater signals this run — the data sources panel "
            "has the technical note."
        )
    # Prefer showing rsv / flu / covid in that order when present, then any extras
    ordered_keys = ["rsv", "flu", "covid"] + [k for k in known if k not in ("rsv", "flu", "covid")]
    parts = [f"{k.upper() if k in ('rsv',) else k.replace('_', ' ').title()} around {known[k].split('(')[0].strip().lower()}"
             for k in ordered_keys if k in known]
    if len(parts) == 1:
        summary = parts[0]
    elif len(parts) == 2:
        summary = f"{parts[0]} and {parts[1]}"
    else:
        summary = f"{', '.join(parts[:-1])}, and {parts[-1]}"
    return (
        f"BC wastewater surveillance (a population-level signal, not a clinic test) is showing "
        f"{summary}. "
        f"Clinical trends are summarized separately by BCCDC in their weekly respiratory updates."
    )


def build_summary(
    virus_data: dict[str, str],
    env_data: dict[str, str],
    *,
    ranking: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    """
    Returns keys: outdoor_feel, summary_text

    env_data expects: air_quality, weather (string labels; "Unavailable" allowed).
    ranking: optional severity-sorted list from wastewater compute; when provided,
             generates dynamic text that mentions whatever pathogens are present.
    """
    air_quality = env_data.get("air_quality", "Unavailable")
    weather = env_data.get("weather", "Unavailable")

    if _air_is_concerning(air_quality):
        outdoor_feel = "Take it easy outside"
    elif _weather_is_wet(weather):
        outdoor_feel = "Better for indoor play"
    else:
        outdoor_feel = "Nice for a walk outside"

    sentences: list[str] = []

    # Respiratory sentence — prefer ranking list (dynamic), fall back to virus dict
    if ranking:
        sentences.append(_respiratory_sentence_from_ranking(ranking))
    else:
        sentences.append(_respiratory_sentence_from_virus_dict(virus_data))

    if "unavailable" not in air_quality.lower():
        sentences.append(f"Air quality: {air_quality}.")
    else:
        sentences.append("Air quality didn't load this run.")

    sentences.append(f"For most kids we'd call the outdoors \u201c{outdoor_feel}\u201d today.")

    if "unavailable" not in weather.lower():
        sentences.append(f"Weather snapshot: {weather}.")

    sentences.append(
        "It\u2019s a neighbourhood snapshot, not medical advice \u2014 talk to your care team if you\u2019re worried."
    )

    summary_text = " ".join(sentences)

    return {
        "outdoor_feel": outdoor_feel,
        "summary_text": summary_text,
    }
