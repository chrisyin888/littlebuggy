/**
 * Homepage summary — static JSON snapshot only (MVP invariants):
 * - Browser loads one file; no live fetch/analyze of health or weather APIs on each visit.
 * - No Postgres; generation is ``scripts/update_homepage_summary.py`` (optional later: swap URL to API).
 * - Copy is prepared offline (``homepage_summary_builder`` + ``homepage_public_polish``); not via ``snapshot_pipeline``/SQLAlchemy.
 */

/** Path under ``public/`` → URL ``{BASE_URL}data/homepage-summary.json``. */
export const HOMEPAGE_SUMMARY_PUBLIC_PATH = 'data/homepage-summary.json'

export function resolveHomepageSummaryUrl() {
  const base = import.meta.env.BASE_URL || '/'
  const path = HOMEPAGE_SUMMARY_PUBLIC_PATH
  return base.endsWith('/') ? `${base}${path}` : `${base}/${path}`
}

/** @deprecated Use ``resolveHomepageSummaryUrl``. */
export function getHomepageSummaryRequestUrl() {
  return resolveHomepageSummaryUrl()
}

function isHomepageSummaryUrl(url) {
  return url.includes('homepage-summary.json')
}

/** @param {unknown} input */
export function normalizeHomepageSummaryPayload(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return null

  const o = /** @type {Record<string, unknown>} */ ({ ...input })
  const str = (v, fallback = '') => {
    if (v == null) return fallback
    const s = String(v).trim()
    return s || fallback
  }

  const srcIn = o.sources && typeof o.sources === 'object' ? o.sources : {}
  const pack = (key, fallbackName) => {
    const m = /** @type {Record<string, unknown>} */ (srcIn)[key]
    const block = m && typeof m === 'object' ? m : {}
    return {
      name: str(block.name, fallbackName),
      url: str(block.url, ''),
      refreshed_label: block.refreshed_label != null ? String(block.refreshed_label).trim() || null : null,
      status: str(block.status, 'unknown'),
    }
  }

  o.region = str(o.region, 'Metro Vancouver')
  o.rsv = str(o.rsv, 'Unknown')
  o.flu = str(o.flu, 'Unknown')
  o.covid = str(o.covid, 'Unknown')
  /** Optional display names from JSON; when empty, UI falls back to i18n. */
  o.rsv_label = str(o.rsv_label, '')
  o.flu_label = str(o.flu_label, '')
  o.covid_label = str(o.covid_label, '')
  o.air_quality = str(o.air_quality, 'Unavailable')
  o.weather = str(o.weather, 'Unavailable')
  const wdIn = o.weather_display
  if (wdIn && typeof wdIn === 'object' && !Array.isArray(wdIn)) {
    const wd = /** @type {Record<string, unknown>} */ (wdIn)
    const num = (v) => {
      const n = Number(v)
      return Number.isFinite(n) ? n : null
    }
    const hi = num(wd.high_c)
    const lo = num(wd.low_c)
    const cur = num(wd.current_c)
    const place =
      typeof wd.location_label === 'string' && wd.location_label.trim()
        ? wd.location_label.trim()
        : 'Vancouver'
    const cond =
      wd.condition != null && String(wd.condition).trim() ? String(wd.condition).trim() : null
    if (hi != null && lo != null) {
      const block = { location_label: place, high_c: hi, low_c: lo, condition: cond }
      if (cur != null) block.current_c = cur
      o.weather_display = block
    } else {
      o.weather_display = null
    }
  } else {
    o.weather_display = null
  }
  o.outdoor_feel = str(o.outdoor_feel, 'Unavailable')
  o.updated_at = str(o.updated_at, '')
  o.short_summary = str(o.short_summary, '')
  o.summary = str(o.summary, o.short_summary)
  o.live_vs_illustrative_note = str(o.live_vs_illustrative_note, '')
  const sv = o.schema_version
  o.schema_version = typeof sv === 'number' && Number.isFinite(sv) ? sv : null
  o.sources = {
    respiratory: pack('respiratory', 'Respiratory signals'),
    aqhi: pack('aqhi', 'Air quality (AQHI)'),
    weather: pack('weather', 'Weather'),
  }
  if (o.data_quality_note != null && typeof o.data_quality_note !== 'string') {
    o.data_quality_note = null
  }
  if (typeof o.data_quality_note === 'string' && !o.data_quality_note.trim()) {
    o.data_quality_note = null
  }
  return o
}

export class HomepageFetchError extends Error {
  /**
   * @param {string} code
   * @param {string} message
   * @param {number} [status]
   */
  constructor(code, message, status) {
    super(message)
    this.name = 'HomepageFetchError'
    this.code = code
    this.status = status
  }
}

/**
 * Loads and normalizes homepage summary JSON (graceful defaults if fields are missing).
 */
export async function fetchHomepageSummary() {
  const url = resolveHomepageSummaryUrl()

  if (import.meta.env.VITE_DEBUG_API === 'true') {
    console.info('[LittleBuggy] homepage summary URL:', url)
  }

  let res
  try {
    res = await fetch(url, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
  } catch (err) {
    const hint =
      typeof window !== 'undefined' && isHomepageSummaryUrl(url)
        ? ' Ensure public/data/homepage-summary.json exists and is deployed.'
        : ''
    throw new HomepageFetchError(
      'NETWORK',
      `Network error calling ${url}.${hint} (${err instanceof Error ? err.message : 'fetch failed'})`,
      0,
    )
  }

  const contentType = res.headers.get('content-type') || ''

  if (res.ok) {
    if (!contentType.includes('application/json')) {
      const snippet = (await res.text().catch(() => '')).slice(0, 120).trim()
      const staticWrong =
        isHomepageSummaryUrl(url) &&
        (snippet.startsWith('<') || snippet.startsWith('<!DOCTYPE'))
          ? ' Hosting may be rewriting unknown paths to HTML—keep the file at public/data/homepage-summary.json.'
          : ''
      throw new HomepageFetchError(
        'NOT_JSON',
        `Expected JSON from ${url} but got ${contentType || 'unknown type'}.` +
          (snippet.startsWith('<') || snippet.startsWith('<!DOCTYPE')
            ? staticWrong || ' Response looks like HTML, not JSON.'
            : ` Body starts with: ${snippet}`),
        res.status,
      )
    }
    let raw
    try {
      raw = await res.json()
    } catch {
      throw new HomepageFetchError(
        'NOT_JSON',
        `Invalid JSON from ${url}. Run npm run weekly:homepage.`,
        res.status,
      )
    }
    let normalized = normalizeHomepageSummaryPayload(raw)
    if (!normalized) {
      normalized = normalizeHomepageSummaryPayload({})
    }
    return /** @type {Record<string, unknown>} */ (normalized)
  }

  if (res.status === 404) {
    throw new HomepageFetchError(
      'NO_SNAPSHOT',
      `Missing data/homepage-summary.json — run npm run weekly:homepage, then commit public/data/homepage-summary.json.`,
      404,
    )
  }

  const text = (await res.text().catch(() => '')).trim()
  const short =
    text.length > 200 ? `${text.slice(0, 200)}…` : text || `Request failed (${res.status})`
  throw new HomepageFetchError('HTTP_ERROR', short, res.status)
}
