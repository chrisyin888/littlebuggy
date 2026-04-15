"""
Pathogen catalog — single source of truth for display metadata, severity rules, and symptom info.

When the PHAC wastewater feed introduces a new measureid, the backend auto-ingests it via dynamic
measure discovery. Add an entry here to enrich that pathogen with labels, reviewed symptoms, and
custom severity thresholds. No code changes are needed elsewhere for a new pathogen to appear.

IMPORTANT: This is informational context, not medical advice or diagnosis.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Display labels
# ---------------------------------------------------------------------------

DISPLAY_LABELS: dict[str, str] = {
    "covid": "COVID-19",
    "rsv": "RSV",
    "flu": "Influenza",        # composite signal (max of flu_a / flu_b per site)
    "flu_a": "Influenza A",
    "flu_b": "Influenza B",
    "hmpv": "hMPV",
    "norovirus": "Norovirus",
    "entero": "Enterovirus",
    "mpox": "Mpox",
}

# ---------------------------------------------------------------------------
# Severity percentile thresholds
# ---------------------------------------------------------------------------
# "_default" is used for all pathogens unless a key-specific entry exists.
# high_pct: percentile at or above which the level is "High"
# medium_pct: percentile at or above which the level is "Medium" (else "Low")

SEVERITY_PERCENTILE_THRESHOLDS: dict[str, dict[str, float]] = {
    "_default": {"high_pct": 66.0, "medium_pct": 33.0},
    # Example override — uncomment to tune a specific pathogen:
    # "norovirus": {"high_pct": 75.0, "medium_pct": 40.0},
}


def get_severity_thresholds(key: str) -> dict[str, float]:
    """Return percentile thresholds for a pathogen key (falls back to _default)."""
    return SEVERITY_PERCENTILE_THRESHOLDS.get(key, SEVERITY_PERCENTILE_THRESHOLDS["_default"])


# ---------------------------------------------------------------------------
# Symptom catalog
# ---------------------------------------------------------------------------
# Lists are reviewed common symptoms for informational display only.
# A key absent from this dict → None returned → UI shows neutral fallback.
# All wording must remain informational; never imply diagnosis.

SYMPTOM_CATALOG: dict[str, list[str]] = {
    "covid": [
        "Fever or chills",
        "Cough",
        "Shortness of breath or difficulty breathing",
        "Fatigue",
        "New loss of taste or smell",
        "Sore throat",
        "Runny or stuffy nose",
        "Muscle or body aches",
    ],
    "rsv": [
        "Runny nose",
        "Decreased appetite",
        "Coughing",
        "Sneezing",
        "Fever",
        "Wheezing (especially in infants)",
    ],
    "flu": [
        "Fever or feeling feverish/chills",
        "Cough",
        "Sore throat",
        "Runny or stuffy nose",
        "Muscle or body aches",
        "Headaches",
        "Fatigue",
        "Vomiting and diarrhea (more common in children)",
    ],
    "flu_a": [
        "Fever or feeling feverish/chills",
        "Cough",
        "Sore throat",
        "Muscle or body aches",
        "Headaches",
        "Fatigue",
    ],
    "flu_b": [
        "Fever or feeling feverish/chills",
        "Cough",
        "Sore throat",
        "Muscle or body aches",
        "Headaches",
        "Fatigue",
    ],
    "hmpv": [
        "Cough",
        "Fever",
        "Nasal congestion",
        "Shortness of breath",
        "Wheezing",
    ],
    "norovirus": [
        "Nausea",
        "Vomiting",
        "Diarrhea",
        "Stomach cramps or pain",
        "Low-grade fever",
        "Chills",
        "Headache",
        "Muscle aches",
    ],
    "entero": [
        "Fever",
        "Runny nose",
        "Skin rash",
        "Mouth blisters (hand, foot, and mouth disease pattern)",
        "Body and muscle aches",
    ],
}

# Neutral fallback when a pathogen has no reviewed symptom entry.
SYMPTOM_FALLBACK_MESSAGE: str = (
    "Symptom information for this pathogen hasn't been reviewed yet. "
    "Check with your local health authority for the latest guidance."
)

# Disclaimer appended to all symptom displays — never imply diagnosis.
SYMPTOM_DISCLAIMER: str = (
    "Commonly reported symptoms — for informational purposes only. "
    "This is not a diagnosis. If you have health concerns, please consult a healthcare provider "
    "or call 8-1-1 (BC HealthLink)."
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_display_label(key: str, measureid: str = "") -> str:
    """Return the best display label for a pathogen key."""
    if key in DISPLAY_LABELS:
        return DISPLAY_LABELS[key]
    base = (measureid or key or "").strip()
    if not base:
        return "Signal"
    return base.replace("_", " ").strip().title()


def get_symptoms(key: str) -> list[str] | None:
    """
    Return reviewed symptom list for a key, or None if not yet catalogued.
    None means 'not reviewed' — callers should show the fallback message instead.
    """
    return SYMPTOM_CATALOG.get(key)


def get_symptom_display(key: str) -> dict[str, Any]:
    """
    Symptom display bundle for API consumers.

    Returns a dict with:
    - symptoms: list[str] | None  — None when not yet reviewed
    - fallback_message: str | None — set when symptoms is None
    - disclaimer: str | None — set when symptoms is present
    """
    symptoms = get_symptoms(key)
    return {
        "symptoms": symptoms,
        "fallback_message": None if symptoms is not None else SYMPTOM_FALLBACK_MESSAGE,
        "disclaimer": SYMPTOM_DISCLAIMER if symptoms is not None else None,
    }


def virus_triple_from_ranking(ranking: list[dict[str, Any]]) -> dict[str, str]:
    """
    Derive a {key: severity_label} dict from the ranked list.

    Provides backward-compatible rsv/flu/covid values when those pathogens are
    present, while also carrying any additional pathogen keys discovered in the feed.
    Falls back to 'Unknown' for rsv/flu/covid when not present in the ranking.
    """
    out: dict[str, str] = {}
    for entry in ranking:
        k = str(entry.get("key") or "").strip()
        if k:
            out[k] = str(entry.get("severity_label") or "Unknown")
    # Ensure backward-compat keys are always present
    for legacy in ("rsv", "flu", "covid"):
        out.setdefault(legacy, "Unknown")
    return out
