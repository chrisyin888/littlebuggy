/**
 * Trend topic keys for modals / routing. Copy lives in locale files (trends.*).
 *
 * Pathogens with a dedicated detail page are listed in TREND_DETAIL_KEYS.
 * Unknown pathogens (future ones from the PHAC feed) fall back to 'how_it_works'
 * so the UI always has something meaningful to show when a card is tapped.
 */

export const TREND_DETAIL_KEYS = new Set([
  'rsv',
  'flu',
  'covid',
  'air_quality',
  'outdoor',
  'cough_patterns',
  'how_it_works',
])

export function isTrendDetailKey(key) {
  return typeof key === 'string' && TREND_DETAIL_KEYS.has(key)
}

/**
 * Map a live hero card row to a detail modal key.
 * Known pathogens open their dedicated page; unknown ones open 'how_it_works'.
 * This means new pathogens from the PHAC feed automatically get a fallback modal
 * without any code change here.
 */
export function heroRowToDetailKey(row) {
  const k = String(row?.kind || '').toLowerCase()
  if (TREND_DETAIL_KEYS.has(k)) return k
  // Unknown pathogen key — fall back to the general 'how it works' modal
  return 'how_it_works'
}

export function envRowToDetailKey(row) {
  const m = { air: 'air_quality', weather: 'outdoor', outdoor: 'outdoor' }
  return m[row.kind] || null
}

export function activeCardToDetailKey(id) {
  const k = String(id || '').toLowerCase()
  if (TREND_DETAIL_KEYS.has(k)) return k
  return null
}
