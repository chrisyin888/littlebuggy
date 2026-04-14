/**
 * Homepage summary:
 * - **Production:** latest row from ``GET /api/homepage-summary`` (Render crons refresh the DB daily /
 *   weekly). If ``VITE_API_BASE_URL`` is set, HTTP errors from that API (e.g. 503) surface as
 *   {@link HomepageFetchError}; we only fall back to bundled ``public/data/homepage-summary.json`` when
 *   the request does not complete (network / timeout).
 * - **Dev:** static JSON when no API base is configured; with ``VITE_API_BASE_URL`` (or proxy), uses the same
 *   ``GET /api/homepage-summary?city=`` as production so the city switcher loads real per-city data.
 */

import { CITIES, DEFAULT_CITY_ID, getCityById } from '../config/cities.js'
import { apiUrl, resolvedApiBase } from './apiOrigin.js'

/** Max wait for live API before using static fallback (cold starts / slow networks). */
const LIVE_API_TIMEOUT_MS = 15_000

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

/** Default English short names when API omits labels (matches backend). */
const DEFAULT_SIGNAL_LABELS = /** @type {Record<string, string>} */ ({
  rsv: 'RSV',
  flu: 'Flu',
  covid: 'COVID-19',
})

/** @param {string} key */
function defaultLabelForKey(key) {
  const k = String(key || '').toLowerCase()
  if (DEFAULT_SIGNAL_LABELS[k]) return DEFAULT_SIGNAL_LABELS[k]
  if (!k) return 'Signal'
  return k
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * Split "Medium (Stable)" → level + trend; otherwise full string is level.
 * @param {string} s
 * @returns {{ level: string, trend: string | null }}
 */
export function splitLevelTrend(s) {
  const t = String(s || '').trim()
  if (!t) return { level: 'Unknown', trend: null }
  const m = t.match(/^(.+?)\s*\(([^)]+)\)\s*$/)
  if (m) return { level: m[1].trim(), trend: m[2].trim() }
  return { level: t, trend: null }
}

/**
 * @param {string} level
 * @param {string | null} trend
 */
export function signalDisplayLine(level, trend) {
  const lv = String(level || '').trim() || 'Unknown'
  const tr = trend != null && String(trend).trim() ? String(trend).trim() : null
  return tr ? `${lv} (${tr})` : lv
}

const _SIGNAL_SORT_ORDER = ['rsv', 'flu', 'covid']

/**
 * @param {Array<{ key: string, label: string, level: string, trend: string | null }>} signals
 */
function sortSignalsStable(signals) {
  return [...signals].sort((a, b) => {
    const ia = _SIGNAL_SORT_ORDER.indexOf(a.key)
    const ib = _SIGNAL_SORT_ORDER.indexOf(b.key)
    const sa = ia === -1 ? _SIGNAL_SORT_ORDER.length : ia
    const sb = ib === -1 ? _SIGNAL_SORT_ORDER.length : ib
    if (sa !== sb) return sa - sb
    return a.key.localeCompare(b.key)
  })
}

/**
 * @param {Record<string, unknown>} o
 * @param {(v: unknown, fallback?: string) => string} str
 */
function normalizeSignalsFromPayload(o, str) {
  const raw = o.signals
  if (Array.isArray(raw) && raw.length > 0) {
    const out = []
    for (const item of raw) {
      if (!item || typeof item !== 'object' || Array.isArray(item)) continue
      const key = String(/** @type {Record<string, unknown>} */ (item).key || '')
        .trim()
        .toLowerCase()
      if (!key) continue
      let level = str(/** @type {Record<string, unknown>} */ (item).level, 'Unknown')
      let trend =
        /** @type {Record<string, unknown>} */ (item).trend != null
          ? str(/** @type {Record<string, unknown>} */ (item).trend, '')
          : ''
      trend = trend || null
      if (!trend && level.includes('(')) {
        const sp = splitLevelTrend(level)
        level = sp.level
        trend = sp.trend
      }
      const label = str(/** @type {Record<string, unknown>} */ (item).label, '') || defaultLabelForKey(key)
      out.push({ key, label: label.trim() || defaultLabelForKey(key), level, trend })
    }
    if (out.length) return sortSignalsStable(out)
  }

  const triples = [
    ['rsv', 'rsv_label', o.rsv],
    ['flu', 'flu_label', o.flu],
    ['covid', 'covid_label', o.covid],
  ]
  const built = []
  for (const [key, labelField, rawLevel] of triples) {
    const lv = splitLevelTrend(str(rawLevel, 'Unknown'))
    const lab = str(o[labelField], '') || defaultLabelForKey(key)
    built.push({
      key,
      label: lab.trim() || defaultLabelForKey(key),
      level: lv.level,
      trend: lv.trend,
    })
  }
  return sortSignalsStable(built)
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

  const cid = str(o.city_id, DEFAULT_CITY_ID)
  o.city_id = CITIES.some((c) => c.id === cid) ? cid : DEFAULT_CITY_ID
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
  o.signals = normalizeSignalsFromPayload(o, str)
  return o
}

/**
 * When using bundled JSON (dev / API down), respiratory data may still be Vancouver-sourced;
 * still show the user's selected city name and append a short note for non-default cities.
 * @param {Record<string, unknown>} data
 * @param {string} cityId
 */
export function applyStaticCityDisplayPatch(data, cityId) {
  const cid = cityId || DEFAULT_CITY_ID
  const city = getCityById(cid)
  const out = { ...data, city_id: cid, region: city.name }
  if (cid !== DEFAULT_CITY_ID) {
    const hint =
      'Bundled snapshot uses Metro Vancouver feeds; run the API for city-specific air and weather.'
    const prev = typeof out.data_quality_note === 'string' ? out.data_quality_note.trim() : ''
    out.data_quality_note = prev ? `${prev} ${hint}` : hint
  }
  return out
}

/**
 * @param {Response} res
 * @returns {Promise<Record<string, unknown> | null>}
 */
async function normalizedPayloadFromOkJsonResponse(res) {
  const contentType = res.headers.get('content-type') || ''
  if (!res.ok || !contentType.includes('application/json')) {
    return null
  }
  let raw
  try {
    raw = await res.json()
  } catch {
    return null
  }
  let normalized = normalizeHomepageSummaryPayload(raw)
  if (!normalized) {
    normalized = normalizeHomepageSummaryPayload({})
  }
  return /** @type {Record<string, unknown>} */ (normalized)
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
 * Live homepage summary from the API.
 *
 * @returns {Promise<Record<string, unknown> | null>} Parsed payload, or `null` only when the request
 *   did not reach a response (timeout / network). Any HTTP 4xx/5xx from the API throws
 *   {@link HomepageFetchError} so we do not silently fall back to bundled JSON with a stale `updated_at`.
 */
async function tryFetchLiveHomepageSummary(cityId = DEFAULT_CITY_ID) {
  const q = new URLSearchParams({ city: cityId || DEFAULT_CITY_ID })
  const url = `${apiUrl('/api/homepage-summary')}?${q}`
  const ctrl = new AbortController()
  const tid = setTimeout(() => ctrl.abort(), LIVE_API_TIMEOUT_MS)
  try {
    const res = await fetch(url, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: ctrl.signal,
    })
    if (!res.ok) {
      // 5xx: backend down or snapshot not ready → return null so caller falls back to static JSON
      // 4xx: unexpected API error → also return null to degrade gracefully
      if (import.meta.env.VITE_DEBUG_API === 'true') {
        const detail = (await res.text().catch(() => '')).trim()
        console.warn(`[LittleBuggy] API ${res.status} for city=${cityId}:`, detail || '(no detail)')
      }
      return null
    }
    return await normalizedPayloadFromOkJsonResponse(res)
  } catch {
    // Network error / timeout / AbortError → return null, fall back to static JSON
    return null
  } finally {
    clearTimeout(tid)
  }
}

/**
 * Loads and normalizes homepage summary (live API in production when configured, else static JSON).
 */
export async function fetchHomepageSummary(cityId = DEFAULT_CITY_ID) {
  const cid = cityId || DEFAULT_CITY_ID
  // In dev, Vite proxies /api/* → local FastAPI (resolvedApiBase() returns '' but proxy still works).
  // Always try the live API so city switching returns real per-city data.
  // If the backend is not running, tryFetchLiveHomepageSummary returns null and we fall back to static JSON.
  const useLiveApi = true
  if (useLiveApi) {
    const live = await tryFetchLiveHomepageSummary(cid)
    if (live) {
      if (import.meta.env.VITE_DEBUG_API === 'true') {
        console.info('[LittleBuggy] homepage summary: live API')
      }
      return live
    }
    if (import.meta.env.VITE_DEBUG_API === 'true') {
      console.info('[LittleBuggy] homepage summary: API unreachable, falling back to static JSON')
    }
  }

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
    return /** @type {Record<string, unknown>} */ (applyStaticCityDisplayPatch(normalized, cid))
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
