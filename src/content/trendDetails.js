/**
 * Trend topic keys for modals / routing. Copy lives in locale files (trends.*).
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

/** Live hero rows use ``kind`` = signal key (``rsv`` | ``flu`` | ``covid`` | unknown). */
export function heroRowToDetailKey(row) {
  const k = row.kind
  if (k === 'rsv' || k === 'flu' || k === 'covid') return k
  return 'how_it_works'
}

export function envRowToDetailKey(row) {
  const m = { air: 'air_quality', weather: 'outdoor', outdoor: 'outdoor' }
  return m[row.kind] || null
}

export function activeCardToDetailKey(id) {
  if (id === 'rsv' || id === 'flu' || id === 'covid') return id
  return null
}
