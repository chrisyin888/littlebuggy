/**
 * LittleBuggy service worker (hand-written, no build plugin).
 *
 * Strategy:
 * - App shell + static assets (same-origin JS/CSS/images/fonts): cache-first,
 *   populated on the fly (Vite emits hashed names, so no precache list to rot).
 * - Live data — API origin (littlebuggy-api.onrender.com) and /data/*.json:
 *   network-first. Wait times / virus levels must never be served stale when
 *   the network is up; on network failure fall back to the single most recent
 *   cached copy of that exact URL.
 * - Navigations: network-first, falling back to the cached shell ('/').
 */
const STATIC_CACHE = 'littlebuggy-static-v1'
const DATA_CACHE = 'littlebuggy-data-v1'
const SHELL_URLS = ['/', '/manifest.webmanifest', '/favicon.svg', '/icons/icon-192.png']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== STATIC_CACHE && k !== DATA_CACHE)
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  )
})

function isDataRequest(url) {
  if (url.hostname.endsWith('onrender.com')) return true // API origin
  if (url.pathname.startsWith('/data/') && url.pathname.endsWith('.json')) return true
  if (url.pathname === '/virus-trends') return true
  return false
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)

  // Live data: network-first, cache only the latest copy per URL as fallback.
  if (isDataRequest(url)) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone()
            caches.open(DATA_CACHE).then((cache) => cache.put(request, copy))
          }
          return response
        })
        .catch(() => caches.match(request, { ignoreSearch: false })),
    )
    return
  }

  // Page navigations: fresh HTML when online, cached shell when offline.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone()
          caches.open(STATIC_CACHE).then((cache) => cache.put('/', copy))
          return response
        })
        .catch(() => caches.match('/')),
    )
    return
  }

  // Same-origin static assets: cache-first.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            if (response && response.ok) {
              const copy = response.clone()
              caches.open(STATIC_CACHE).then((cache) => cache.put(request, copy))
            }
            return response
          }),
      ),
    )
  }
})
