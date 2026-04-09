/**
 * Human-readable relative time for "Updated … ago" (past times only).
 * Uses Intl.RelativeTimeFormat; falls back to empty string if invalid or future-dated.
 */
export function localeToRelativeTimeLocale(localeTag) {
  const t = String(localeTag || 'en').toLowerCase()
  if (t.startsWith('zh')) return 'zh-CN'
  return 'en'
}

export function formatRelativeTimePast(isoString, localeTag = 'en') {
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return ''

  const now = Date.now()
  /** Negative if date is in the past */
  let duration = Math.round((date.getTime() - now) / 1000)
  if (duration > 0) return ''

  const rtf = new Intl.RelativeTimeFormat(localeToRelativeTimeLocale(localeTag), { numeric: 'auto' })

  const divisions = [
    { amount: 60, unit: 'minute' },
    { amount: 60, unit: 'hour' },
    { amount: 24, unit: 'day' },
    { amount: 7, unit: 'week' },
    { amount: 4.34524, unit: 'month' },
    { amount: 12, unit: 'year' },
  ]

  let unit = 'second'
  for (const { amount, unit: nextUnit } of divisions) {
    if (Math.abs(duration) < amount) break
    duration /= amount
    unit = nextUnit
  }

  return rtf.format(Math.round(duration), unit)
}
