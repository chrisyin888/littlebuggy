<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const DISMISS_KEY = 'littlebuggy-install-dismissed'
const deferredPrompt = ref(null)
const isIos = ref(false)
const eligible = ref(false)
const dismissed = ref(false)

try {
  dismissed.value = localStorage.getItem(DISMISS_KEY) === '1'
} catch {
  dismissed.value = false
}

function isStandalone() {
  if (typeof window === 'undefined') return false
  return (
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  )
}

function isMobileViewport() {
  if (typeof window === 'undefined') return false
  return window.matchMedia?.('(max-width: 820px)').matches || 'ontouchstart' in window
}

function onBeforeInstallPrompt(e) {
  e.preventDefault()
  deferredPrompt.value = e
  eligible.value = true
}

onMounted(() => {
  if (typeof window === 'undefined' || dismissed.value || isStandalone()) return
  if (!isMobileViewport()) return
  const ua = window.navigator.userAgent || ''
  isIos.value = /iphone|ipad|ipod/i.test(ua) && !/crios|fxios/i.test(ua)
  if (isIos.value) {
    // iOS Safari has no install event; show the Share-sheet hint instead.
    eligible.value = true
  }
  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})

onUnmounted(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})

const visible = computed(() => eligible.value && !dismissed.value && !isStandalone())

async function onInstall() {
  if (!deferredPrompt.value) return
  try {
    await deferredPrompt.value.prompt()
    await deferredPrompt.value.userChoice
  } catch {
    /* user choice is theirs; bar can be dismissed manually */
  }
  deferredPrompt.value = null
  eligible.value = false
}

function onDismiss() {
  dismissed.value = true
  try {
    localStorage.setItem(DISMISS_KEY, '1')
  } catch {
    /* private mode — dismissal just won't persist */
  }
}
</script>

<template>
  <div v-if="visible" class="install-prompt" role="dialog" :aria-label="t('app.pwaInstallTitle')">
    <img class="install-prompt__icon" src="/icons/icon-192.png" alt="" width="40" height="40" />
    <div class="install-prompt__text">
      <p class="install-prompt__title">{{ t('app.pwaInstallTitle') }}</p>
      <p v-if="isIos" class="install-prompt__body">
        {{ t('app.pwaInstallIosHint') }}
      </p>
      <p v-else class="install-prompt__body">{{ t('app.pwaInstallBody') }}</p>
    </div>
    <button
      v-if="!isIos"
      type="button"
      class="install-prompt__install"
      @click="onInstall"
    >
      {{ t('app.pwaInstallButton') }}
    </button>
    <button
      type="button"
      class="install-prompt__dismiss"
      :aria-label="t('app.pwaInstallDismiss')"
      @click="onDismiss"
    >
      ✕
    </button>
  </div>
</template>

<style scoped>
.install-prompt {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px));
  z-index: 300;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: min(26rem, calc(100vw - 1.5rem));
  padding: 0.65rem 0.75rem;
  border-radius: 18px;
  background: rgba(255, 252, 247, 0.97);
  border: 2px solid rgba(124, 58, 237, 0.35);
  box-shadow: 0 12px 32px rgba(76, 29, 149, 0.22);
}

.install-prompt__icon {
  border-radius: 10px;
  flex-shrink: 0;
}

.install-prompt__text {
  flex: 1;
  min-width: 0;
}

.install-prompt__title {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 800;
  color: var(--color-ink);
  line-height: 1.3;
}

.install-prompt__body {
  margin: 0.15rem 0 0;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.4;
}

.install-prompt__install {
  flex-shrink: 0;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 800;
  padding: 0.5rem 0.9rem;
  border: none;
  border-radius: 999px;
  background: linear-gradient(120deg, #7c3aed, #a855f7);
  color: #fff;
  cursor: pointer;
}

.install-prompt__dismiss {
  flex-shrink: 0;
  font: inherit;
  font-size: 0.8rem;
  line-height: 1;
  padding: 0.35rem 0.45rem;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-ink-muted);
  cursor: pointer;
}
</style>
