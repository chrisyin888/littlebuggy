import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'

createApp(App).use(router).use(i18n).mount('#app')

// PWA: register the service worker in production builds only (dev stays cache-free).
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      /* offline support is best-effort; the site works without it */
    })
  })
}
