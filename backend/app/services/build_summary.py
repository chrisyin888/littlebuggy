"""
Parent-friendly outdoor feel + summary paragraph from real (or partially missing) inputs.
"""


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


def build_summary(virus_data: dict[str, str], env_data: dict[str, str]) -> dict[str, str]:
    """
    Returns keys: outdoor_feel, summary_text

    env_data expects: air_quality, weather (string labels; "Unavailable" allowed).
    """
    rsv = virus_data.get("rsv", "Unknown")
    flu = virus_data.get("flu", "Unknown")
    covid = virus_data.get("covid", "Unknown")
    air_quality = env_data.get("air_quality", "Unavailable")
    weather = env_data.get("weather", "Unavailable")

    if _air_is_concerning(air_quality):
        outdoor_feel = "Take it easy outside"
    elif _weather_is_wet(weather):
        outdoor_feel = "Better for indoor play"
    else:
        outdoor_feel = "Nice for a walk outside"

    sentences: list[str] = []

    if not str(rsv).lower().startswith("unknown"):
        sentences.append(
            f"BC wastewater surveillance (a population-level signal, not a clinic test) is showing "
            f"RSV activity around {rsv}, flu around {flu}, and COVID-related signal around {covid}. "
            f"Clinical trends are summarized separately by BCCDC in their weekly respiratory updates."
        )
    else:
        sentences.append(
            "We couldn’t refresh respiratory wastewater signals this run — the data sources panel "
            "has the technical note."
        )

    if "unavailable" not in air_quality.lower():
        sentences.append(f"Air quality: {air_quality}.")
    else:
        sentences.append("Air quality didn’t load this run.")

    sentences.append(f"For most kids we’d call the outdoors “{outdoor_feel}” today.")

    if "unavailable" not in weather.lower():
        sentences.append(f"Weather snapshot: {weather}.")

    sentences.append(
        "It’s a neighbourhood snapshot, not medical advice — talk to your care team if you’re worried."
    )

    summary_text = " ".join(sentences)

    return {
        "outdoor_feel": outdoor_feel,
        "summary_text": summary_text,
    }
