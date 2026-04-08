import { onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiUrl } from '../lib/apiOrigin.js'

const POLL_MS = 5 * 60 * 1000

/** Shared across ER + UPCC sections so we only poll /wait-times once. */
const payload = shallowRef(null)
const loading = ref(true)
const refreshing = ref(false)
const userRefreshInFlight = ref(false)
const error = ref('')

let pollTimerId = null
let consumerCount = 0

function buildWaitTimesRequestUrl() {
  const path = `/wait-times?ts=${Date.now()}`
  return apiUrl(path)
}

async function runLoadWaitTimes(t, fromUser) {
  const isFirst = !payload.value
  error.value = ''
  if (fromUser && payload.value) {
    userRefreshInFlight.value = true
  }
  if (isFirst) loading.value = true
  else refreshing.value = true

  let url = ''
  try {
    url = buildWaitTimesRequestUrl()
    const res = await fetch(url, { cache: 'no-store', mode: 'cors' })
    const text = await res.text()

    let data
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      console.error('[LittleBuggy] wait-times: not JSON', {
        status: res.status,
        url,
        contentType: res.headers.get('content-type'),
        snippet: text.slice(0, 240),
      })
      error.value = t('waitTimes.errorGeneric')
      return
    }

    if (!res.ok) {
      let msg = t('waitTimes.errorGeneric')
      const d = data?.detail
      if (typeof d === 'string' && d.trim()) {
        msg = d.trim()
      } else if (Array.isArray(d) && d[0]?.msg) {
        msg = String(d[0].msg)
      }
      console.warn('[LittleBuggy] wait-times: HTTP', res.status, url, msg)
      error.value = msg
      return
    }

    if (!data || typeof data !== 'object') {
      console.error('[LittleBuggy] wait-times: empty JSON object', url)
      error.value = t('waitTimes.errorGeneric')
      return
    }
    if (!Array.isArray(data.hospitals)) {
      console.error('[LittleBuggy] wait-times: missing hospitals[]', url, Object.keys(data))
      error.value = t('waitTimes.errorGeneric')
      return
    }

    const checkedAt =
      typeof data.checked_at === 'string' && data.checked_at.trim()
        ? data.checked_at.trim()
        : new Date().toISOString()

    payload.value = {
      ...data,
      hospitals: data.hospitals,
      upcc_centres: Array.isArray(data.upcc_centres) ? data.upcc_centres : [],
      checked_at: checkedAt,
    }
  } catch (err) {
    console.error('[LittleBuggy] wait-times: fetch error', url || buildWaitTimesRequestUrl(), err)
    error.value = t('waitTimes.errorNetwork')
  } finally {
    loading.value = false
    refreshing.value = false
    userRefreshInFlight.value = false
  }
}

/**
 * Fetches GET /wait-times (FastAPI). Multiple components share one poll timer.
 */
export function useErWaitTimes() {
  const { t } = useI18n()

  /**
   * @param {{ fromUser?: boolean }} [opts]
   */
  async function loadWaitTimes(opts = {}) {
    await runLoadWaitTimes(t, opts.fromUser === true)
  }

  onMounted(() => {
    consumerCount += 1
    if (consumerCount === 1) {
      runLoadWaitTimes(t, false)
      pollTimerId = window.setInterval(() => {
        runLoadWaitTimes(t, false)
      }, POLL_MS)
    }
  })

  onUnmounted(() => {
    consumerCount -= 1
    if (consumerCount <= 0) {
      consumerCount = 0
      if (pollTimerId != null) {
        window.clearInterval(pollTimerId)
        pollTimerId = null
      }
    }
  })

  return {
    payload,
    loading,
    refreshing,
    userRefreshInFlight,
    error,
    loadWaitTimes,
  }
}

/**
 * Map wait_text like "2h 45m" to severity for UI accent. "Unavailable" → null.
 */
export function waitSeverityFromText(waitText) {
  const s = String(waitText || '').trim()
  if (!s || /^unavailable/i.test(s)) return null
  const m = s.match(/^(\d+)\s*h\s*(\d{1,2})\s*m$/i)
  if (!m) return null
  const mins = parseInt(m[1], 10) * 60 + parseInt(m[2], 10)
  if (mins < 120) return 'short'
  if (mins < 240) return 'medium'
  return 'long'
}
