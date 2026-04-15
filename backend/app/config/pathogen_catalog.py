"""
Pathogen catalog — single source of truth for display metadata, severity rules, and symptom info.

When the PHAC wastewater feed introduces a new measureid, the backend auto-ingests it via dynamic
measure discovery. Add an entry here to enrich that pathogen with labels, reviewed symptoms, and
custom severity thresholds. No code changes are needed elsewhere for a new pathogen to appear.

IMPORTANT: This is informational context, not medical advice or diagnosis.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Display labels
# ---------------------------------------------------------------------------

DISPLAY_LABELS: dict[str, str] = {
    "covid": "COVID-19",
    "rsv": "RSV",
    "flu": "Influenza",  # composite signal (max of flu_a / flu_b per site)
    "flu_a": "Influenza A",
    "flu_b": "Influenza B",
    "hmpv": "hMPV",
    "norovirus": "Norovirus",
    "entero": "Enterovirus",
    "mpox": "Mpox",
}

# Key/measure aliases to canonical keys.
PATHOGEN_ALIASES: dict[str, str] = {
    "covn2": "covid",
    "sars_cov_2": "covid",
    "sars_cov2": "covid",
    "covid19": "covid",
    "covid_19": "covid",
    "influenza": "flu",
    "influenza_a": "flu_a",
    "influenza_b": "flu_b",
    "flua": "flu_a",
    "flub": "flu_b",
    "metapneumovirus": "hmpv",
    "human_metapneumovirus": "hmpv",
    "rhino": "rhinovirus",
    "rhinovirus_enterovirus": "rhinovirus",
}


# ---------------------------------------------------------------------------
# Severity percentile thresholds
# ---------------------------------------------------------------------------

SEVERITY_PERCENTILE_THRESHOLDS: dict[str, dict[str, float]] = {
    "_default": {"high_pct": 66.0, "medium_pct": 33.0},
}


def get_severity_thresholds(key: str) -> dict[str, float]:
    """Return percentile thresholds for a pathogen key (falls back to _default)."""
    nk = normalize_pathogen_key(key)
    return SEVERITY_PERCENTILE_THRESHOLDS.get(nk, SEVERITY_PERCENTILE_THRESHOLDS["_default"])


# ---------------------------------------------------------------------------
# Symptom catalog
# ---------------------------------------------------------------------------

SYMPTOM_CATALOG: dict[str, list[str]] = {
    "covid": [
        "Fever or chills",
        "Cough",
        "Sore throat",
        "Runny or stuffy nose",
        "Fatigue",
    ],
    "rsv": [
        "Runny nose",
        "Decreased appetite",
        "Coughing",
        "Fever",
        "Wheezing (especially in infants)",
    ],
    "flu": [
        "Fever or chills",
        "Cough",
        "Sore throat",
        "Muscle or body aches",
        "Fatigue",
    ],
    "flu_a": [
        "Fever or chills",
        "Cough",
        "Sore throat",
        "Body aches",
    ],
    "flu_b": [
        "Fever or chills",
        "Cough",
        "Sore throat",
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
        "Stomach cramps",
        "Low-grade fever",
    ],
    "entero": [
        "Fever",
        "Runny nose",
        "Skin rash",
        "Mouth sores",
    ],
}

# Family-level symptom groups for future pathogens.
FAMILY_SYMPTOMS: dict[str, list[str]] = {
    "influenza": [
        "Fever or chills",
        "Cough",
        "Sore throat",
        "Body aches",
        "Fatigue",
    ],
    "covid": [
        "Fever or chills",
        "Cough",
        "Sore throat",
        "Runny or stuffy nose",
        "Fatigue",
    ],
    "rsv": [
        "Runny nose",
        "Cough",
        "Fever",
        "Wheezing",
    ],
    "norovirus": [
        "Nausea",
        "Vomiting",
        "Diarrhea",
        "Stomach cramps",
    ],
}

# Canonical key -> family
PATHOGEN_FAMILIES: dict[str, str] = {
    "flu": "influenza",
    "flu_a": "influenza",
    "flu_b": "influenza",
    "influenza": "influenza",
    "covid": "covid",
    "sars_cov_2": "covid",
    "rsv": "rsv",
    "hmpv": "rsv",
    "norovirus": "norovirus",
}

GENERIC_RESPIRATORY_SYMPTOMS: list[str] = [
    "Cough",
    "Sore throat",
    "Runny or stuffy nose",
    "Fever",
    "Fatigue",
]

# Neutral fallback when no reviewed list is available.
SYMPTOM_FALLBACK_MESSAGE: str = (
    "Symptom information for this pathogen hasn't been reviewed yet. "
    "Check with your local health authority for the latest guidance."
)

SYMPTOM_DISCLAIMER: str = (
    "Commonly reported symptoms — for informational purposes only. "
    "This is not a diagnosis. If you have health concerns, please consult a healthcare provider."
)


def _norm_token(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", str(text or "").strip().lower()).strip("_")
    return s


def normalize_pathogen_key(key: str, label: str = "") -> str:
    """Normalize raw key/label into canonical pathogen key where possible."""
    candidates = [_norm_token(key)]
    if label:
        candidates.append(_norm_token(label))

    for c in candidates:
        if not c:
            continue
        if c in PATHOGEN_ALIASES:
            return PATHOGEN_ALIASES[c]
        if c in DISPLAY_LABELS or c in SYMPTOM_CATALOG:
            return c
        if c.startswith("flu"):
            return "flu"
        if "influenza" in c:
            return "flu"
        if "covid" in c or c.startswith("sars_cov"):
            return "covid"
        if "rsv" in c:
            return "rsv"
    return candidates[0] or "unknown"


def _family_for_pathogen(canonical_key: str, label: str = "") -> str | None:
    if canonical_key in PATHOGEN_FAMILIES:
        return PATHOGEN_FAMILIES[canonical_key]
    lk = canonical_key.lower()
    ll = str(label or "").lower()
    if lk.startswith("flu") or "influenza" in lk or "influenza" in ll:
        return "influenza"
    if "covid" in lk or "sars" in lk or "covid" in ll:
        return "covid"
    if "rsv" in lk or "metapneumo" in lk or "rsv" in ll:
        return "rsv"
    if "noro" in lk or "noro" in ll:
        return "norovirus"
    return None


def resolve_symptoms_for_pathogen(key: str, label: str = "") -> dict[str, Any]:
    """
    Resolve symptoms with priority:
    1) exact reviewed pathogen key
    2) alias/normalized key
    3) pathogen family fallback
    4) generic respiratory fallback
    """
    canonical = normalize_pathogen_key(key, label)

    # 1 + 2 exact/alias-normalized lookup
    symptoms = SYMPTOM_CATALOG.get(canonical)
    if symptoms:
        return {
            "symptoms": symptoms,
            "fallback_message": None,
            "disclaimer": SYMPTOM_DISCLAIMER,
            "resolution": "exact_or_alias",
            "resolved_key": canonical,
            "family": _family_for_pathogen(canonical, label),
        }

    # 3 family fallback
    family = _family_for_pathogen(canonical, label)
    if family and family in FAMILY_SYMPTOMS:
        return {
            "symptoms": FAMILY_SYMPTOMS[family],
            "fallback_message": None,
            "disclaimer": SYMPTOM_DISCLAIMER,
            "resolution": "family",
            "resolved_key": canonical,
            "family": family,
        }

    # 4 generic respiratory fallback for unknown future pathogens
    return {
        "symptoms": GENERIC_RESPIRATORY_SYMPTOMS,
        "fallback_message": SYMPTOM_FALLBACK_MESSAGE,
        "disclaimer": SYMPTOM_DISCLAIMER,
        "resolution": "generic",
        "resolved_key": canonical,
        "family": None,
    }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_display_label(key: str, measureid: str = "") -> str:
    """Return the best display label for a pathogen key."""
    canonical = normalize_pathogen_key(key, measureid)
    if canonical in DISPLAY_LABELS:
        return DISPLAY_LABELS[canonical]
    base = (measureid or key or "").strip()
    if not base:
        return "Signal"
    return base.replace("_", " ").strip().title()


def get_symptoms(key: str, label: str = "") -> list[str] | None:
    """Return symptom list from resolver (always safe for unknown keys)."""
    return resolve_symptoms_for_pathogen(key, label).get("symptoms")


def get_symptom_display(key: str, label: str = "") -> dict[str, Any]:
    """Symptom display bundle for API consumers."""
    info = resolve_symptoms_for_pathogen(key, label)
    return {
        "symptoms": info.get("symptoms"),
        "fallback_message": info.get("fallback_message"),
        "disclaimer": info.get("disclaimer"),
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
    for legacy in ("rsv", "flu", "covid"):
        out.setdefault(legacy, "Unknown")
    return out
