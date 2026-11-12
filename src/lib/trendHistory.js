/**
 * Homepage 7-day trend history:
 * Fetches ``GET /api/homepage-trend-history`` — daily respiratory levels read
 * back from the ``trend_snapshots`` rows the existing crons already persist
 * (one entry per Vancouver calendar day, oldest first). Returns ``null`` on
 * any failure so the homepage can fall back to its non-chart preview.
 */

import { apiUrl } from './apiOrigin.js'

const TREND_HISTORY_TIMEOUT_MS = 15_000

/**
 * @param {string} [cityId]
 * @returns {Promise<{ city_id: string, region: string, days: Array<{ date: string, signals: Array<object> }> } | null>}
 */
export async function fetchTrendHistory(cityId) {
  const q = new URLSearchParams()
  if (cityId) q.set('city', cityId)
  q.set('days', '7')
  const url = `${apiUrl('/api/homepage-trend-history')}?${q.toString()}`
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TREND_HISTORY_TIMEOUT_MS)
  try {
    const res = await fetch(url, { signal: ctrl.signal, cache: 'no-store' })
    if (!res.ok) return null
    const data = await res.json()
    if (!data || !Array.isArray(data.days)) return null
    return data
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}
