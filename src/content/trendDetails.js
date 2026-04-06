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

/** Live hero rows use kind rsv | flu | covid */
export function heroRowToDetailKey(row) {
  if (row.kind === 'rsv' || row.kind === 'flu' || row.kind === 'covid') return row.kind
  const v = String(row.value || '')
  if (/rsv/i.test(v)) return 'rsv'
  if (/fever|cough/i.test(v)) return 'cough_patterns'
  return 'cough_patterns'
}

export function envRowToDetailKey(row) {
  const m = { air: 'air_quality', weather: 'outdoor', outdoor: 'outdoor' }
  return m[row.kind] || null
}

export function activeCardToDetailKey(id) {
  if (id === 'rsv' || id === 'flu' || id === 'covid') return id
  return null
}
