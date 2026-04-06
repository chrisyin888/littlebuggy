<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView } from 'vue-router'
import { useHomepageSnapshot } from './composables/useHomepageSnapshot.js'
import { localeToHtmlLang } from './i18n'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import LittleBuggyMascot from './components/LittleBuggyMascot.vue'
import { localeToDateLocale } from './utils/localeDisplay.js'

const { t, locale } = useI18n()

const {
  snapshot,
  snapshotLoading,
  snapshotRefreshing,
  snapshotError,
  ensureHomepageSnapshot,
  refreshHomepageSnapshot,
  formatSnapshotUpdatePhrase,
} = useHomepageSnapshot()

function onVisibilityRefresh() {
  if (typeof document === 'undefined' || document.visibilityState !== 'visible') return
  ensureHomepageSnapshot().catch(() => {})
}

onMounted(() => {
  ensureHomepageSnapshot().catch(() => {})
  document.addEventListener('visibilitychange', onVisibilityRefresh)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisibilityRefresh)
})

function onClickRefresh() {
  refreshHomepageSnapshot()
}

watch(
  locale,
  (l) => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = localeToHtmlLang(l)
    }
  },
  { immediate: true },
)

const snapshotStatusText = computed(() => {
  void locale.value
  if (snapshotLoading.value && !snapshot.value) {
    return t('snapshot.fetching')
  }
  if (snapshotRefreshing.value && snapshot.value) {
    return t('snapshot.revalidating')
  }
  if (snapshotError.value && !snapshot.value) {
    return t('snapshot.offline')
  }
  if (snapshotError.value && snapshot.value) {
    return t('snapshot.staleWhileShowing')
  }
  const s = snapshot.value
  if (!s?.updated_at) {
    return t('snapshot.noTime')
  }
  const when = formatSnapshotUpdatePhrase(s.updated_at, t, locale.value)
  const region = (s.region || t('brand.tagShort')).trim()
  if (!when) {
    return t('snapshot.regionOnly', { region })
  }
  return t('snapshot.latestLine', { when, region })
})

const snapshotBarTitle = computed(() => {
  void locale.value
  const raw = snapshot.value?.updated_at
  if (!raw) return undefined
  try {
    const d = new Date(raw)
    if (Number.isNaN(d.getTime())) return undefined
    return t('snapshot.savedTooltip', { date: d.toLocaleString(localeToDateLocale(locale.value)) })
  } catch {
    return undefined
  }
})
</script>

<template>
  <div class="app">
    <div class="app-top-stack">
      <p
        class="snapshot-status-bar"
        role="status"
        aria-live="polite"
        :title="snapshotBarTitle"
      >
        <span
          class="snapshot-status-bar__dot"
          :class="{ 'snapshot-status-bar__dot--busy': snapshotRefreshing }"
          aria-hidden="true"
        />
        <span class="snapshot-status-bar__text">{{ snapshotStatusText }}</span>
        <button
          type="button"
          class="snapshot-status-bar__refresh"
          :disabled="snapshotLoading || snapshotRefreshing"
          :aria-label="t('snapshot.refreshAria')"
          @click="onClickRefresh"
        >
          {{ t('snapshot.refresh') }}
        </button>
      </p>
      <div class="awareness-bar" role="note">
        <LittleBuggyMascot class="awareness-bar__mascot" pose="calm" size="sm" />
        <span class="awareness-bar__text">{{ t('app.awareness') }}</span>
      </div>
    </div>
    <header class="site-header">
      <div class="site-header__inner">
        <div class="site-header__row">
          <RouterLink to="/" class="brand">
            <span class="brand__mark" aria-hidden="true">
              <svg class="brand__svg" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="20" cy="22" r="14" stroke="#7dd3fc" stroke-width="1.2" stroke-dasharray="2.5 4" opacity="0.7" />
                <ellipse cx="20" cy="21" rx="9" ry="7" fill="#ff9a7a" stroke="#e85d4c" stroke-width="1.2" />
                <circle cx="20" cy="12" r="4.5" fill="#ffcf6b" stroke="#f59e0b" stroke-width="0.9" />
                <path d="M15 9 Q13 5 10 4M25 9 Q27 5 30 4" stroke="#a78bfa" stroke-width="1.3" stroke-linecap="round" />
                <circle cx="16.5" cy="20" r="1.4" fill="#3d3540" />
                <circle cx="23.5" cy="20" r="1.4" fill="#3d3540" />
                <path d="M16 24c1 1 7 1 8 0" stroke="#3d3540" stroke-width="1.1" stroke-linecap="round" />
                <circle cx="17" cy="19" r="0.45" fill="#fff" opacity="0.9" />
                <circle cx="24" cy="19" r="0.45" fill="#fff" opacity="0.9" />
              </svg>
            </span>
            <span class="brand__text">
              <span class="brand__name">LittleBuggy</span>
              <span class="brand__tag">{{ t('brand.tag') }}</span>
            </span>
          </RouterLink>

          <LanguageSwitcher variant="compact" />
        </div>
      </div>
    </header>
    <main class="site-main">
      <RouterView />
    </main>
    <footer class="site-footer">
      <p>
        {{ t('app.footer', { brand: t('app.brandName') }) }}
      </p>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-top-stack {
  position: sticky;
  top: 0;
  z-index: 220;
}

.snapshot-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0;
  padding: 0.42rem clamp(1rem, 4vw, 2rem);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: center;
  line-height: 1.35;
  color: #6b21a8;
  background: linear-gradient(
    95deg,
    rgba(237, 233, 254, 0.97) 0%,
    rgba(255, 248, 240, 0.95) 40%,
    rgba(224, 242, 254, 0.92) 100%
  );
  border-bottom: 2px solid rgba(196, 181, 253, 0.45);
  box-shadow: 0 4px 0 rgba(255, 200, 140, 0.22);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.snapshot-status-bar__dot {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(145deg, #f9a8d4, #fcd34d);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
  animation: status-pulse 2.8s ease-in-out infinite;
}

@keyframes status-pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.85;
  }
  50% {
    transform: scale(1.15);
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .snapshot-status-bar__dot {
    animation: none;
  }
}

.snapshot-status-bar__text {
  max-width: 42rem;
  flex: 1 1 12rem;
  min-width: 0;
}

.snapshot-status-bar__refresh {
  flex-shrink: 0;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  padding: 0.32rem 0.65rem;
  border-radius: var(--radius-pill, 999px);
  border: 2px solid rgba(196, 181, 253, 0.65);
  background: rgba(255, 255, 255, 0.9);
  color: #5b21b6;
  cursor: pointer;
  box-shadow: 2px 2px 0 rgba(255, 200, 140, 0.35);
}

.snapshot-status-bar__refresh:hover:not(:disabled) {
  background: #fff;
  border-color: rgba(167, 139, 250, 0.85);
}

.snapshot-status-bar__refresh:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.snapshot-status-bar__dot--busy {
  animation: status-pulse 1.2s ease-in-out infinite;
}

.awareness-bar {
  position: relative;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  flex-wrap: wrap;
  padding: 0.65rem clamp(1rem, 4vw, 2rem);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-align: center;
  color: var(--color-ink-muted);
  background: linear-gradient(
    92deg,
    rgba(255, 251, 243, 0.97) 0%,
    rgba(255, 236, 214, 0.92) 35%,
    rgba(232, 244, 252, 0.9) 70%,
    rgba(255, 251, 243, 0.97) 100%
  );
  border-bottom: 3px dashed rgba(255, 193, 120, 0.5);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.awareness-bar__mascot {
  flex-shrink: 0;
  opacity: 0.95;
}

.awareness-bar__text {
  max-width: 48rem;
  line-height: 1.45;
}

.site-header {
  padding: 1rem clamp(1rem, 4vw, 2rem);
  background: rgba(255, 252, 247, 0.88);
  border-bottom: 3px solid rgba(186, 230, 253, 0.55);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.site-header__inner {
  max-width: var(--layout-max);
  margin: 0 auto;
}

.site-header__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1rem;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: inherit;
}

.brand__mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 26px;
  background: linear-gradient(145deg, #fff9e6 0%, #ffe8f0 38%, #d4efff 100%);
  color: #0d9b8a;
  box-shadow:
    4px 4px 0 rgba(255, 200, 140, 0.45),
    inset 0 2px 0 rgba(255, 255, 255, 0.95);
  transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.brand__svg {
  width: 1.75rem;
  height: 1.75rem;
}

.brand__text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.06rem;
}

.brand__name {
  font-family: var(--font-display);
  font-size: 1.42rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.1;
  background: linear-gradient(115deg, #ff6b4a 0%, #c084fc 42%, #38bdf8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brand__tag {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--color-ink-soft);
  letter-spacing: 0.03em;
}

.brand:hover .brand__mark {
  transform: scale(1.06) rotate(-4deg);
}

.site-main {
  flex: 1;
  width: 100%;
  max-width: var(--layout-max);
  margin: 0 auto;
  padding: clamp(1.5rem, 4.5vw, 2.85rem) clamp(1rem, 4vw, 2rem);
}

.site-footer {
  padding: 1.5rem clamp(1rem, 4vw, 2rem);
  background: linear-gradient(180deg, rgba(255, 251, 243, 0.9) 0%, rgba(232, 244, 252, 0.5) 100%);
  border-top: 3px dashed rgba(186, 230, 253, 0.55);
}

.site-footer p {
  max-width: var(--layout-max);
  margin: 0 auto;
  font-size: 0.86rem;
  line-height: 1.65;
  font-weight: 600;
  color: var(--color-ink-soft);
  text-align: center;
}

.site-footer strong {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--color-ink-muted);
}
</style>
