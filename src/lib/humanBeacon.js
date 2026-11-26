/**
 * Behavior-verified "real human" visit beacon.
 *
 * The plain /api/track-visit counter fires on page load, so anything that
 * renders the page (including browser-like crawlers) inflates it. This beacon
 * instead waits for a human-like behavior signal and then fires
 * POST /api/track-human at most once per session:
 *
 *   - scroll depth >= 25% of the page, or
 *   - a pointerdown / keydown interaction, or
 *   - 10 seconds of dwell while the tab is visible, or
 *   - a second route/page view within the same session.
 *
 * The backend additionally applies the same bot user-agent filter as
 * /api/track-visit, so a counted "human visit" approximates a real person.
 */
import { apiUrl } from './apiOrigin.js'

const HUMAN_SESSION_KEY = 'lb_human_counted_session'
const PAGE_VIEWS_SESSION_KEY = 'lb_page_views_session'
const DWELL_THRESHOLD_SECONDS = 10
const SCROLL_DEPTH_THRESHOLD = 0.25

let armed = false
let fired = false
let dwellSeconds = 0
let dwellTimer = null
let cleanupFns = []

function sessionGet(key) {
  try {
    if (typeof sessionStorage === 'undefined') return null
    return sessionStorage.getItem(key)
  } catch {
    return null
  }
}

function sessionSet(key, value) {
  try {
    if (typeof sessionStorage === 'undefined') return
    sessionStorage.setItem(key, value)
  } catch {
    /* non-fatal */
  }
}

function alreadyCounted() {
  return fired || sessionGet(HUMAN_SESSION_KEY) === '1'
}

function cleanup() {
  for (const fn of cleanupFns) {
    try {
      fn()
    } catch {
      /* non-fatal */
    }
  }
  cleanupFns = []
  if (dwellTimer !== null) {
    clearInterval(dwellTimer)
    dwellTimer = null
  }
}

function fireHuman() {
  if (alreadyCounted()) {
    cleanup()
    return
  }
  fired = true
  cleanup()
  void (async () => {
    try {
      const r = await fetch(apiUrl('/api/track-human'), {
        method: 'POST',
        keepalive: true,
      })
      if (r.ok) {
        sessionSet(HUMAN_SESSION_KEY, '1')
      } else {
        fired = false
      }
    } catch {
      fired = false
      /* non-fatal */
    }
  })()
}

function onScroll() {
  try {
    const doc = document.documentElement
    const scrollable = doc.scrollHeight - window.innerHeight
    if (scrollable <= 0) return
    const depth = window.scrollY / scrollable
    if (depth >= SCROLL_DEPTH_THRESHOLD) fireHuman()
  } catch {
    /* non-fatal */
  }
}

function onDwellTick() {
  try {
    if (typeof document !== 'undefined' && document.visibilityState !== 'visible') return
    dwellSeconds += 1
    if (dwellSeconds >= DWELL_THRESHOLD_SECONDS) fireHuman()
  } catch {
    /* non-fatal */
  }
}

/**
 * Arm the behavior listeners (idempotent; safe to call once at app start).
 * If the session was already counted, this is a no-op.
 */
export function initHumanBeacon() {
  if (armed || alreadyCounted()) return
  if (typeof window === 'undefined' || typeof document === 'undefined') return
  armed = true

  window.addEventListener('scroll', onScroll, { passive: true })
  cleanupFns.push(() => window.removeEventListener('scroll', onScroll))

  const onInteract = () => fireHuman()
  window.addEventListener('pointerdown', onInteract)
  window.addEventListener('keydown', onInteract)
  cleanupFns.push(() => {
    window.removeEventListener('pointerdown', onInteract)
    window.removeEventListener('keydown', onInteract)
  })

  dwellTimer = setInterval(onDwellTick, 1000)
}

/**
 * Record one route/page view for this session; the second view counts as a
 * human signal. Wire this to the router (afterEach) so it covers every route.
 */
export function notePageView() {
  if (alreadyCounted()) return
  let views = 0
  try {
    views = Number.parseInt(sessionGet(PAGE_VIEWS_SESSION_KEY) || '0', 10) || 0
  } catch {
    views = 0
  }
  views += 1
  sessionSet(PAGE_VIEWS_SESSION_KEY, String(views))
  if (views >= 2) fireHuman()
}
