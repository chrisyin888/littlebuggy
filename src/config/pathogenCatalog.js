/**
 * Frontend pathogen catalog — display labels, stickers, and symptom info.
 *
 * This is the single authoritative frontend config for pathogen presentation.
 * When a new pathogen appears from the API, it automatically uses the generic
 * fallback (🦠 sticker, title-cased label, no symptoms listed). Add an entry
 * here to give it a richer appearance — no other code changes are needed.
 *
 * IMPORTANT: All symptom wording is informational only, never diagnostic.
 */

// ---------------------------------------------------------------------------
// Stickers
// ---------------------------------------------------------------------------

/** Emoji sticker for each known pathogen key. Unknown keys fall back to 🦠. */
export const PATHOGEN_STICKERS = {
  rsv: '🐞',
  flu: '🤒',
  flu_a: '🤒',
  flu_b: '🤒',
  covid: '😷',
  hmpv: '🫁',
  norovirus: '🦠',
  entero: '🤧',
  mpox: '🔬',
}

/**
 * Get the emoji sticker for a pathogen key.
 * Returns 🦠 for any unknown key — future pathogens work automatically.
 * @param {string} key
 * @returns {string}
 */
export function stickerForPathogen(key) {
  return PATHOGEN_STICKERS[String(key || '').toLowerCase()] ?? '🦠'
}

// ---------------------------------------------------------------------------
// Display labels
// ---------------------------------------------------------------------------

/**
 * Short display labels for known pathogen keys.
 * Falls back to title-cased API label when not listed.
 */
export const PATHOGEN_LABELS = {
  rsv: 'RSV',
  flu: 'Influenza',
  flu_a: 'Influenza A',
  flu_b: 'Influenza B',
  covid: 'COVID-19',
  hmpv: 'hMPV',
  norovirus: 'Norovirus',
  entero: 'Enterovirus',
  mpox: 'Mpox',
}

/**
 * Get display label for a pathogen key.
 * @param {string} key
 * @param {string} [apiLabel] - label provided by the API (used as secondary fallback)
 * @returns {string}
 */
export function labelForPathogen(key, apiLabel) {
  const k = String(key || '').toLowerCase()
  if (PATHOGEN_LABELS[k]) return PATHOGEN_LABELS[k]
  if (apiLabel && String(apiLabel).trim()) return String(apiLabel).trim()
  if (!k) return 'Signal'
  return k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

// ---------------------------------------------------------------------------
// Symptom catalog
// ---------------------------------------------------------------------------

/**
 * Reviewed, commonly-reported symptoms for each pathogen.
 * Informational only — never implies diagnosis.
 * Keys match the API's pathogen key (e.g. rsv, flu, covid).
 * Pathogens without an entry show SYMPTOM_FALLBACK_MESSAGE instead.
 *
 * @type {Record<string, string[]>}
 */
export const PATHOGEN_SYMPTOMS = {
  covid: [
    'Fever or chills',
    'Cough',
    'Shortness of breath or difficulty breathing',
    'Fatigue',
    'New loss of taste or smell',
    'Sore throat',
    'Runny or stuffy nose',
    'Muscle or body aches',
  ],
  rsv: [
    'Runny nose',
    'Decreased appetite',
    'Coughing',
    'Sneezing',
    'Fever',
    'Wheezing (especially in infants)',
  ],
  flu: [
    'Fever or feeling feverish/chills',
    'Cough',
    'Sore throat',
    'Runny or stuffy nose',
    'Muscle or body aches',
    'Headaches',
    'Fatigue',
    'Vomiting and diarrhea (more common in children)',
  ],
  flu_a: [
    'Fever or feeling feverish/chills',
    'Cough',
    'Sore throat',
    'Muscle or body aches',
    'Headaches',
    'Fatigue',
  ],
  flu_b: [
    'Fever or feeling feverish/chills',
    'Cough',
    'Sore throat',
    'Muscle or body aches',
    'Headaches',
    'Fatigue',
  ],
  hmpv: [
    'Cough',
    'Fever',
    'Nasal congestion',
    'Shortness of breath',
    'Wheezing',
  ],
  norovirus: [
    'Nausea',
    'Vomiting',
    'Diarrhea',
    'Stomach cramps or pain',
    'Low-grade fever',
    'Chills',
    'Headache',
    'Muscle aches',
  ],
  entero: [
    'Fever',
    'Runny nose',
    'Skin rash',
    'Mouth blisters',
    'Body and muscle aches',
  ],
}

/**
 * Neutral fallback shown when a pathogen has no reviewed symptom entry.
 * Informational only.
 */
export const SYMPTOM_FALLBACK_MESSAGE =
  "Symptom information for this pathogen hasn't been reviewed yet. " +
  'Check with your local health authority for the latest guidance.'

/**
 * Disclaimer shown alongside any symptom list.
 * Must never imply diagnosis.
 */
export const SYMPTOM_DISCLAIMER =
  'Commonly reported symptoms — informational only, not a diagnosis. ' +
  'If you have health concerns, please speak with a healthcare provider.'

/**
 * Get symptom display info for a pathogen key.
 *
 * Returns an object with:
 *   symptoms: string[] | null — null when not yet reviewed
 *   fallbackMessage: string | null — set when symptoms is null
 *   disclaimer: string | null — set when symptoms is present
 *
 * @param {string} key
 * @returns {{ symptoms: string[] | null, fallbackMessage: string | null, disclaimer: string | null }}
 */
export function symptomsForPathogen(key) {
  const k = String(key || '').toLowerCase()
  const symptoms = PATHOGEN_SYMPTOMS[k] ?? null
  return {
    symptoms,
    fallbackMessage: symptoms ? null : SYMPTOM_FALLBACK_MESSAGE,
    disclaimer: symptoms ? SYMPTOM_DISCLAIMER : null,
  }
}
