import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'

createApp(App).use(router).use(i18n).mount('#app')

// Deep-link rescue: the static host serves real files before the SPA rewrite,
// so standalone landing pages under public/ (e.g. /guides/fever/) bounce here
// with ?go=<key> and we route client-side to the real page.
try {
  const go = new URLSearchParams(window.location.search).get('go')
  const GO_ROUTES = { fever: '/guides/fever', 'wait-times': '/wait-times' }
  if (go && GO_ROUTES[go]) {
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
