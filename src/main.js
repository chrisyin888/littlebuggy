import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import { initHumanBeacon } from './lib/humanBeacon.js'

createApp(App).use(router).use(i18n).mount('#app')

// Behavior-verified human visit counting (POST /api/track-human on a real
// interaction signal; see src/lib/humanBeacon.js). Page-view signals are
// wired in src/router/index.js.
initHumanBeacon()

// Deep-link rescue: the static host serves real files before the SPA rewrite,
// so standalone landing pages under public/ (e.g. /guides/fever/) bounce here
// with ?go=<key> and we route client-side to the real page.
try {
  const params = new URLSearchParams(window.location.search)
  const go = params.get('go')
  const GO_ROUTES = { fever: '/guides/fever', 'wait-times': '/wait-times' }
  if (go && GO_ROUTES[go]) {
    // Facility landing pages (public/wait-times/<slug>/) bounce here with
    // &facility=<key>; the wait-times list consumes it once to highlight and
    // scroll to that hospital's card.
    const facility = params.get('facility')
    if (facility) {
      try {
        sessionStorage.setItem('lb_facility', facility)
      } catch {
        /* storage unavailable — landing still works, just no highlight */
      }
    }
    router.replace(GO_ROUTES[go])
  }
} catch {
  /* non-fatal */
}

// PWA: register the service worker in production builds only (dev stays cache-free).
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      /* offline support is best-effort; the site works without it */
    })
  })
}
