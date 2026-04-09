import { ref, shallowRef } from 'vue'
import { fetchHomepageSummary, HomepageFetchError } from '../lib/homepageSummary.js'
import { DEFAULT_CITY_ID, getCityById } from '../config/cities.js'
import { selectedCityId } from './useSelectedCity.js'
import { i18n } from '../i18n/index.js'
import { localeToDateLocale } from '../utils/localeDisplay.js'

/** Shared homepage API payload — one in-flight fetch for App + HomeView. */
export const snapshot = shallowRef(null)

/** True until the first successful load when there was no prior snapshot. */
export const snapshotLoading = ref(true)

/** True while revalidating in the background (prior snapshot may still show). */
export const snapshotRefreshing = ref(false)

export const snapshotError = ref(null)

/** Ms since last successful fetch; used with TTL to avoid stale lock-in. */
const TTL_MS = 12 * 60 * 1000

let lastSuccessAt = 0
let lastFetchedCityId = DEFAULT_CITY_ID
let inflight = null
/** @type {string | null} */
let inflightCityId = null

function resolveSnapshotCityId(opts = {}) {
  const raw = opts.cityId != null ? opts.cityId : selectedCityId.value
  return getCityById(typeof raw === 'string' ? raw : '').id
}

/**
 * Loads homepage summary from static `/data/homepage-summary.json` (see `npm run weekly:homepage`).
 * Uses TTL so a forced refresh can pick up a redeployed JSON without a full page reload.
 * @param {{ force?: boolean, cityId?: string }} [opts] - `force: true` skips TTL and starts a new request; `cityId` overrides the global selected city for this fetch only.
 */
export async function ensureHomepageSnapshot(opts = {}) {
  const force = opts.force === true
  const cityId = resolveSnapshotCityId(opts)
  const now = Date.now()

  if (
    !force &&
    snapshot.value &&
    lastSuccessAt > 0 &&
    now - lastSuccessAt < TTL_MS &&
    lastFetchedCityId === cityId
  ) {
    return snapshot.value
  }

  if (inflight && !force && inflightCityId === cityId) {
    return inflight
  }

  if (inflight && (force || inflightCityId !== cityId)) {
    try {
      await inflight
    } catch {
      /* replaced by forced refresh or city change */
    }
    inflight = null
    inflightCityId = null
  }

  const hadData = !!snapshot.value

  if (hadData) {
    snapshotRefreshing.value = true
  } else {
    snapshotLoading.value = true
  }
  snapshotError.value = null

  inflightCityId = cityId
  inflight = fetchHomepageSummary(cityId)
    .then((data) => {
      snapshot.value = data
      lastSuccessAt = Date.now()
      lastFetchedCityId = cityId
      snapshotError.value = null
      return data
    })
    .catch((e) => {
      const t = i18n.global.t
      let msg =
        e instanceof Error ? e.message : t('snapshot.genericFetchError')
      if (e instanceof HomepageFetchError) {
        if (e.code === 'NO_SNAPSHOT') {
          msg = t('snapshot.noSnapshotYet')
        } else if (e.code === 'HTTP_ERROR' && e.status != null && e.status >= 500) {
          msg = t('snapshot.serverError')
        } else {
          msg = e.message || t('snapshot.genericFetchError')
        }
      }
      snapshotError.value = msg
      if (!hadData) {
        snapshot.value = null
      }
      throw e
    })
    .finally(() => {
      snapshotLoading.value = false
      snapshotRefreshing.value = false
      inflight = null
      inflightCityId = null
    })

  return inflight
}

/** Force a new fetch (manual refresh); keeps showing previous snapshot until the request finishes. */
export function refreshHomepageSnapshot() {
  return ensureHomepageSnapshot({ force: true }).catch(() => {})
}

/**
 * Friendly local-time chunk for the sticky bar, e.g. "Today 3:56 PM" or localized equivalent.
 * @param {string} isoString
 * @param {(key: string, values?: Record<string, unknown>) => string} t - vue-i18n translate
 * @param {string} [localeTag] - BCP 47 tag, e.g. 'zh-CN' or 'en'
 */
export function formatSnapshotUpdatePhrase(isoString, t, localeTag = 'en') {
  if (!isoString) return ''
  const d = new Date(isoString)
  if (Number.isNaN(d.getTime())) return ''

  const loc = localeToDateLocale(localeTag)

  const startOfDay = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime()
  const d0 = startOfDay(d)
  const n0 = startOfDay(new Date())
  const diffDays = Math.round((n0 - d0) / 86400000)

  const timePart = d.toLocaleTimeString(loc, {
    hour: 'numeric',
    minute: '2-digit',
  })

  if (diffDays === 0) return t('snapshot.phraseToday', { time: timePart })
  if (diffDays === 1) return t('snapshot.phraseYesterday', { time: timePart })

  return d.toLocaleString(loc, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function useHomepageSnapshot() {
  return {
    snapshot,
    snapshotLoading,
    snapshotRefreshing,
    snapshotError,
    ensureHomepageSnapshot,
    refreshHomepageSnapshot,
    formatSnapshotUpdatePhrase,
  }
}
