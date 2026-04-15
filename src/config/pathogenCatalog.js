/**
 * Frontend pathogen catalog — display labels, stickers, and symptom resolution.
 *
 * Future pathogens should flow without UI hardcoding: we resolve by exact key,
 * alias, family fallback, then generic respiratory fallback.
 */

// ---------------------------------------------------------------------------
// Key normalization + aliases
// ---------------------------------------------------------------------------

export const PATHOGEN_ALIASES = {
  covn2: 'covid',
  'sars-cov-2': 'covid',
  sars_cov_2: 'covid',
  covid19: 'covid',
  covid_19: 'covid',
  influenza: 'flu',
  influenza_a: 'flu_a',
  influenza_b: 'flu_b',
  flua: 'flu_a',
  flub: 'flu_b',
  metapneumovirus: 'hmpv',
  human_metapneumovirus: 'hmpv',
}

function normToken(v) {
  return String(v || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

/**
 * Normalize raw key/label into a canonical pathogen key.
 * @param {string} key
 * @param {string} [label]
 * @returns {string}
 */
export function normalizePathogenKey(key, label = '') {
  const candidates = [normToken(key), normToken(label)].filter(Boolean)
  for (const c of candidates) {
    if (PATHOGEN_ALIASES[c]) return PATHOGEN_ALIASES[c]
    if (c.startsWith('flu') || c.includes('influenza')) return c === 'flu_a' || c === 'flu_b' ? c : 'flu'
    if (c.includes('covid') || c.startsWith('sars_cov')) return 'covid'
    if (c.includes('rsv')) return 'rsv'
    if (c) return c
  }
  return 'unknown'
}

// ---------------------------------------------------------------------------
// Stickers
// ---------------------------------------------------------------------------

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

export function stickerForPathogen(key, label = '') {
  const k = normalizePathogenKey(key, label)
  return PATHOGEN_STICKERS[k] ?? '🦠'
}

// ---------------------------------------------------------------------------
// Display labels
// ---------------------------------------------------------------------------

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

export function labelForPathogen(key, apiLabel) {
  const k = normalizePathogenKey(key, apiLabel)
  if (PATHOGEN_LABELS[k]) return PATHOGEN_LABELS[k]
  if (apiLabel && String(apiLabel).trim()) return String(apiLabel).trim()
  if (!k) return 'Signal'
  return k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

// ---------------------------------------------------------------------------
// Symptom resolution
// ---------------------------------------------------------------------------

export const PATHOGEN_SYMPTOMS = {
  covid: ['Fever or chills', 'Cough', 'Sore throat', 'Runny or stuffy nose', 'Fatigue'],
  rsv: ['Runny nose', 'Coughing', 'Fever', 'Wheezing'],
  flu: ['Fever or chills', 'Cough', 'Sore throat', 'Body aches', 'Fatigue'],
  flu_a: ['Fever or chills', 'Cough', 'Sore throat', 'Body aches'],
  flu_b: ['Fever or chills', 'Cough', 'Sore throat', 'Fatigue'],
  hmpv: ['Cough', 'Fever', 'Nasal congestion', 'Shortness of breath'],
  norovirus: ['Nausea', 'Vomiting', 'Diarrhea', 'Stomach cramps'],
  entero: ['Fever', 'Runny nose', 'Skin rash', 'Mouth sores'],
}

export const PATHOGEN_FAMILIES = {
  flu: 'influenza',
  flu_a: 'influenza',
  flu_b: 'influenza',
  influenza: 'influenza',
  covid: 'covid',
  rsv: 'rsv',
  hmpv: 'rsv',
  norovirus: 'norovirus',
}

export const FAMILY_SYMPTOMS = {
  influenza: ['Fever or chills', 'Cough', 'Sore throat', 'Body aches', 'Fatigue'],
  covid: ['Fever or chills', 'Cough', 'Sore throat', 'Runny or stuffy nose', 'Fatigue'],
  rsv: ['Runny nose', 'Cough', 'Fever', 'Wheezing'],
  norovirus: ['Nausea', 'Vomiting', 'Diarrhea', 'Stomach cramps'],
}

export const GENERIC_RESPIRATORY_SYMPTOMS = [
  'Cough',
  'Sore throat',
  'Runny or stuffy nose',
  'Fever',
  'Fatigue',
]

export const SYMPTOM_FALLBACK_MESSAGE =
  "Symptom information for this pathogen hasn't been reviewed yet. " +
  'Showing general respiratory patterns; check local health guidance for specifics.'

export const SYMPTOM_DISCLAIMER =
  'Commonly reported symptoms — informational only, not a diagnosis. ' +
  'If you have health concerns, please speak with a healthcare provider.'

function familyForPathogen(key, label = '') {
  if (PATHOGEN_FAMILIES[key]) return PATHOGEN_FAMILIES[key]
  const lk = String(key || '').toLowerCase()
  const ll = String(label || '').toLowerCase()
  if (lk.startsWith('flu') || lk.includes('influenza') || ll.includes('influenza')) return 'influenza'
  if (lk.includes('covid') || lk.includes('sars') || ll.includes('covid')) return 'covid'
  if (lk.includes('rsv') || lk.includes('metapneumo') || ll.includes('rsv')) return 'rsv'
  if (lk.includes('noro') || ll.includes('noro')) return 'norovirus'
  return null
}

/**
 * Resolve symptoms with priority:
 * 1) exact reviewed key
 * 2) alias/normalized key
 * 3) family-level fallback
 * 4) generic respiratory fallback
 *
 * @param {string} key
 * @param {string} [label]
 * @returns {{ symptoms: string[] | null, fallbackMessage: string | null, disclaimer: string | null, source: string, resolvedKey: string, family: string | null }}
 */
export function resolveSymptomsForPathogen(key, label = '') {
  const resolvedKey = normalizePathogenKey(key, label)

  const exact = PATHOGEN_SYMPTOMS[resolvedKey]
  if (exact) {
    return {
      symptoms: exact,
      fallbackMessage: null,
      disclaimer: SYMPTOM_DISCLAIMER,
      source: 'exact_or_alias',
      resolvedKey,
      family: familyForPathogen(resolvedKey, label),
    }
  }

  const family = familyForPathogen(resolvedKey, label)
  if (family && FAMILY_SYMPTOMS[family]) {
    return {
      symptoms: FAMILY_SYMPTOMS[family],
      fallbackMessage: null,
      disclaimer: SYMPTOM_DISCLAIMER,
      source: 'family',
      resolvedKey,
      family,
    }
  }

  return {
    symptoms: GENERIC_RESPIRATORY_SYMPTOMS,
    fallbackMessage: SYMPTOM_FALLBACK_MESSAGE,
    disclaimer: SYMPTOM_DISCLAIMER,
    source: 'generic',
    resolvedKey,
    family: null,
  }
}

/** Backward-compatible wrapper for existing call sites. */
export function symptomsForPathogen(key, label = '') {
  const r = resolveSymptomsForPathogen(key, label)
  return {
    symptoms: r.symptoms,
    fallbackMessage: r.fallbackMessage,
    disclaimer: r.disclaimer,
  }
}
