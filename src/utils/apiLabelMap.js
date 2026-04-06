/**
 * Map English API / snapshot labels to i18n keys for display.
 * Matching is case-insensitive; unknown strings pass through unchanged.
 */

function norm(s) {
  return String(s || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
}

/**
 * @param {string} raw - value from API (e.g. "High", "Very High")
 * @param {(key: string) => string} t - vue-i18n translate function
 * @returns {string}
 */
export function translateApiLevel(raw, t) {
  const s = norm(raw)
  if (!s) return raw || ''

  if (/\bvery\s*high\b/.test(s) || s === 'very high') return t('levels.veryHigh')
  if (/\bvery\s*poor\b/.test(s)) return t('levels.veryPoor')
  if (/\blow\s*risk\b/.test(s) || /\bminimal\s*risk\b/.test(s)) return t('levels.lowRisk')
  if (/\brising\b/.test(s)) return t('levels.rising')
  if (/^watch\b|\bwatch\s/.test(s)) return t('levels.watch')
  if (/^high\b|\bhigh\s|risk.*high|spiking|severe|extreme|unhealthy|hazardous|hazard/.test(s))
    return t('levels.high')
  if (/\bmedium\b|\bmoderate\b|\belevated\b|\bbusy\b|\bfair\b/.test(s)) return t('levels.medium')
  if (/^low\b|\blow\s|quiet|calm|minimal|quieter|trickling|good|great|excellent|clean|green|nice\b/.test(s))
    return t('levels.low')

  return String(raw)
}
