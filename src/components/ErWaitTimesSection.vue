<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useErWaitTimes, waitSeverityFromText } from '../composables/useErWaitTimes.js'
import { localeToDateLocale } from '../utils/localeDisplay.js'

const { t, locale } = useI18n()
const { payload, loading, refreshing, userRefreshInFlight, error, loadWaitTimes } = useErWaitTimes()

const showWaitDebug = import.meta.env.DEV

function hasPostedWait(row) {
  const s = String(row?.wait_text ?? '')
    .trim()
    .toLowerCase()
  return s && s !== 'unavailable'
}

const hospitals = computed(() => (payload.value?.hospitals ?? []).filter(hasPostedWait))

function formatTsLabel(raw) {
  if (!raw || typeof raw !== 'string') return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return raw
  try {
    return d.toLocaleString(localeToDateLocale(locale.value), {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return raw
  }
}

const checkedAtLabel = computed(() => {
  void locale.value
  return formatTsLabel(payload.value?.checked_at)
})

const sourceUpdatedLabel = computed(() => {
  void locale.value
  return formatTsLabel(payload.value?.source_updated_at)
})

const sectionDebug = computed(() => payload.value?.debug ?? null)

function debugRawDisplay(d) {
  if (!d || d.raw_before_format === undefined || d.raw_before_format === null) return '—'
  const v = d.raw_before_format
  return typeof v === 'object' ? JSON.stringify(v) : String(v)
}

function debugSourceTs(d) {
  if (!d || d.source_timestamp_raw == null || d.source_timestamp_raw === '') return '—'
  return String(d.source_timestamp_raw)
}

function severityClass(w) {
  const sev = waitSeverityFromText(w.wait_text)
  if (sev === 'short') return 'er-wait-card__tag--short'
  if (sev === 'medium') return 'er-wait-card__tag--medium'
  if (sev === 'long') return 'er-wait-card__tag--long'
  return 'er-wait-card__tag--na'
}
</script>

<template>
  <section
    id="emergency-wait-times"
    class="er-waits-section"
    aria-labelledby="er-waits-title"
  >
    <div class="er-waits-section__inner">
      <header class="er-waits-section__intro">
        <h2 id="er-waits-title" class="er-waits-section__title">{{ t('waitTimes.title') }}</h2>
        <p class="er-waits-section__lead">{{ t('waitTimes.lead') }}</p>
      </header>

      <div v-if="loading && !payload" class="er-waits-section__state" role="status">
        {{ t('waitTimes.loading') }}
      </div>

      <p v-else-if="error && !payload" class="er-waits-section__error" role="alert">
        {{ error }}
      </p>

      <template v-else>
        <p v-if="error" class="er-waits-section__warn" role="status">
          {{ error }}
        </p>

        <p
          v-if="!hospitals.length"
          class="er-waits-section__empty"
          role="status"
        >
          {{ t('waitTimes.nonePosted') }}
        </p>

        <div
          v-else
          class="er-waits-section__grid"
          :class="{ 'er-waits-section__grid--dim': refreshing }"
        >
          <article
            v-for="h in hospitals"
            :key="h.key"
            class="er-wait-card"
          >
            <div class="er-wait-card__top">
              <h3 class="er-wait-card__name">{{ h.name }}</h3>
              <span class="er-wait-card__tag" :class="severityClass(h)">
                {{ t(`waitTimes.severity.${waitSeverityFromText(h.wait_text) || 'unknown'}`) }}
              </span>
            </div>
            <p class="er-wait-card__city">{{ h.city }}</p>
            <p class="er-wait-card__wait" aria-live="polite">
              <span class="er-wait-card__wait-label">{{ t('waitTimes.estimatedWait') }}</span>
              <span class="er-wait-card__wait-value">{{ h.wait_text }}</span>
            </p>
            <p v-if="showWaitDebug && h._debug" class="er-wait-card__debug" aria-label="Temporary debug">
              <span class="er-wait-card__debug-line">raw: {{ debugRawDisplay(h._debug) }}</span>
              <span class="er-wait-card__debug-line">source ts: {{ debugSourceTs(h._debug) }}</span>
            </p>
          </article>
        </div>

        <div v-if="checkedAtLabel" class="er-waits-section__times">
          <p class="er-waits-section__time-line">
            {{ t('waitTimes.lastChecked', { time: checkedAtLabel }) }}
          </p>
          <p v-if="sourceUpdatedLabel" class="er-waits-section__time-line">
            {{ t('waitTimes.sourceUpdated', { time: sourceUpdatedLabel }) }}
          </p>
          <p class="er-waits-section__time-note">{{ t('waitTimes.nearTimestampsNote') }}</p>
          <p class="er-waits-section__time-note er-waits-section__time-note--soft">
            {{ t('waitTimes.refreshHonestyNote') }}
          </p>
        </div>

        <p class="er-waits-section__disclaimer">
          {{ t('waitTimes.disclaimer') }}
        </p>

        <p class="er-waits-section__source">
          {{ t('waitTimes.sourceNote') }}
        </p>

        <div v-if="showWaitDebug && sectionDebug" class="er-waits-section__debug-footer" aria-label="Temporary debug">
          <p class="er-waits-section__debug-line">fetched from: {{ sectionDebug.fetched_url || '—' }}</p>
          <p class="er-waits-section__debug-line">parse mode: {{ sectionDebug.parse_mode || '—' }}</p>
        </div>

        <button
          type="button"
          class="er-waits-section__retry"
          :disabled="loading || refreshing"
          @click="loadWaitTimes({ fromUser: true })"
        >
          {{ userRefreshInFlight ? t('waitTimes.refreshing') : t('waitTimes.refreshNow') }}
        </button>
      </template>
    </div>
  </section>
</template>

<style scoped>
.er-waits-section {
  margin: 0 auto clamp(1.5rem, 4vw, 2.5rem);
  padding: clamp(1.35rem, 3.5vw, 2rem) clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
  border-radius: var(--radius-lg);
  background: linear-gradient(
    145deg,
    rgba(255, 252, 247, 0.98) 0%,
    rgba(232, 244, 252, 0.55) 48%,
    rgba(255, 248, 240, 0.95) 100%
  );
  border: 3px solid rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-soft);
}

.er-waits-section__inner {
  max-width: 920px;
  margin: 0 auto;
}

.er-waits-section__intro {
  margin-bottom: 1.35rem;
}

.er-waits-section__title {
  margin: 0 0 0.45rem;
  font-family: var(--font-display);
  font-size: clamp(1.35rem, 3.2vw, 1.75rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.2;
  background: linear-gradient(115deg, #ff6b4a 0%, #c084fc 42%, #38bdf8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.er-waits-section__lead {
  margin: 0;
  font-size: 0.98rem;
  color: var(--color-ink-muted);
  line-height: 1.55;
  max-width: 40rem;
}

.er-waits-section__state {
  padding: 2rem 0.5rem;
  text-align: center;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.er-waits-section__error {
  margin: 0;
  padding: 1.1rem 1.2rem;
  border-radius: var(--radius-md);
  background: rgba(255, 232, 222, 0.95);
  border: 2px solid rgba(251, 146, 60, 0.45);
  color: var(--color-ink);
  font-weight: 600;
  line-height: 1.5;
}

.er-waits-section__warn {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: rgba(254, 243, 199, 0.65);
  border: 2px dashed rgba(250, 204, 21, 0.5);
  color: var(--color-ink-muted);
  font-size: 0.9rem;
  font-weight: 600;
}

.er-waits-section__empty {
  margin: 0 0 1rem;
  padding: 1rem 1.1rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
  font-weight: 600;
  text-align: center;
  border-radius: var(--radius-md);
  background: rgba(241, 245, 249, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.4);
}

.er-waits-section__grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
}

/* Tablet: 2 columns */
@media (min-width: 640px) {
  .er-waits-section__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
  .er-waits-section__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.er-waits-section__grid--dim {
  opacity: 0.72;
  transition: opacity 0.2s ease;
}

.er-wait-card {
  padding: 1rem 1.15rem 1.15rem;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 2px solid rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-soft);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-height: 7.75rem;
}

.er-wait-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.55rem;
}

.er-wait-card__name {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.02rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-ink);
  flex: 1;
  min-width: 0;
}

.er-wait-card__tag {
  flex-shrink: 0;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.26rem 0.48rem;
  border-radius: var(--radius-pill);
  border: 2px solid transparent;
}

.er-wait-card__tag--short {
  background: rgba(74, 222, 128, 0.22);
  border-color: rgba(34, 197, 94, 0.45);
  color: #166534;
}

.er-wait-card__tag--medium {
  background: rgba(250, 204, 21, 0.28);
  border-color: rgba(234, 179, 8, 0.5);
  color: #854d0e;
}

.er-wait-card__tag--long {
  background: rgba(251, 146, 60, 0.22);
  border-color: rgba(249, 115, 22, 0.5);
  color: #9a3412;
}

.er-wait-card__tag--na {
  background: rgba(237, 233, 254, 0.65);
  border-color: rgba(196, 181, 253, 0.55);
  color: var(--color-ink-muted);
}

.er-wait-card__city {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.er-wait-card__wait {
  margin: 0.25rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
}

.er-wait-card__wait-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.er-wait-card__wait-value {
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 700;
  color: var(--color-teal-dark);
  line-height: 1.1;
}

.er-wait-card__debug {
  margin: 0.5rem 0 0;
  padding-top: 0.45rem;
  border-top: 1px dashed rgba(148, 163, 184, 0.65);
  font-size: 0.65rem;
  line-height: 1.35;
  font-family: ui-monospace, monospace;
  color: #64748b;
  word-break: break-word;
}

.er-wait-card__debug-line {
  display: block;
}

.er-waits-section__debug-footer {
  margin: 0.65rem 0 0;
  padding: 0.5rem 0.65rem;
  border-radius: var(--radius-sm);
  background: rgba(241, 245, 249, 0.95);
  border: 1px dashed rgba(100, 116, 139, 0.45);
  font-size: 0.68rem;
  line-height: 1.4;
  font-family: ui-monospace, monospace;
  color: #475569;
  word-break: break-all;
}

.er-waits-section__debug-line {
  margin: 0;
}

.er-waits-section__times {
  margin: 1.15rem 0 0;
  text-align: center;
}

.er-waits-section__time-line {
  margin: 0 0 0.25rem;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.45;
}

.er-waits-section__time-note {
  margin: 0.55rem 0 0;
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-soft);
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
}

.er-waits-section__time-note--soft {
  margin-top: 0.35rem;
  font-weight: 500;
  color: var(--color-ink-soft);
  opacity: 0.95;
}

.er-waits-section__disclaimer {
  margin: 1.1rem 0 0;
  padding: 0.9rem 1rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
  background: rgba(255, 251, 243, 0.9);
  border-radius: var(--radius-sm);
  border: 2px dashed rgba(255, 193, 120, 0.45);
}

.er-waits-section__source {
  margin: 0.75rem 0 0;
  font-size: 0.78rem;
  color: var(--color-ink-soft);
  text-align: center;
  line-height: 1.45;
}

.er-waits-section__retry {
  display: block;
  margin: 1.1rem auto 0;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-pill);
  border: 2px solid rgba(196, 181, 253, 0.65);
  background: rgba(255, 255, 255, 0.95);
  color: #5b21b6;
  cursor: pointer;
  box-shadow: 2px 2px 0 rgba(255, 200, 140, 0.35);
}

.er-waits-section__retry:hover:not(:disabled) {
  background: #fff;
}

.er-waits-section__retry:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
