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

const centres = computed(() => (payload.value?.upcc_centres ?? []).filter(hasPostedWait))

const legacyNoUpcc = computed(() => {
  const mode = payload.value?.debug?.parse_mode
  return mode === 'legacy_html' && centres.value.length === 0
})

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
  if (sev === 'short') return 'upcc-wait-card__tag--short'
  if (sev === 'medium') return 'upcc-wait-card__tag--medium'
  if (sev === 'long') return 'upcc-wait-card__tag--long'
  return 'upcc-wait-card__tag--na'
}
</script>

<template>
  <section
    id="urgent-care-wait-times"
    class="upcc-waits-section"
    aria-labelledby="upcc-waits-title"
  >
    <div class="upcc-waits-section__inner">
      <header class="upcc-waits-section__intro">
        <h2 id="upcc-waits-title" class="upcc-waits-section__title">{{ t('upccWaitTimes.title') }}</h2>
        <p class="upcc-waits-section__lead">{{ t('upccWaitTimes.lead') }}</p>
      </header>

      <div v-if="loading && !payload" class="upcc-waits-section__state" role="status">
        {{ t('upccWaitTimes.loading') }}
      </div>

      <p v-else-if="error && !payload" class="upcc-waits-section__error" role="alert">
        {{ error }}
      </p>

      <template v-else>
        <p v-if="error" class="upcc-waits-section__warn" role="status">
          {{ error }}
        </p>

        <p v-if="legacyNoUpcc" class="upcc-waits-section__legacy-note" role="status">
          {{ t('upccWaitTimes.legacyNoUpcc') }}
        </p>

        <p
          v-else-if="!centres.length"
          class="upcc-waits-section__empty"
          role="status"
        >
          {{ t('upccWaitTimes.emptyList') }}
        </p>

        <div
          v-else
          class="upcc-waits-section__grid"
          :class="{ 'upcc-waits-section__grid--dim': refreshing }"
        >
          <article
            v-for="c in centres"
            :key="c.key"
            class="upcc-wait-card"
          >
            <div class="upcc-wait-card__top">
              <h3 class="upcc-wait-card__name">{{ c.name }}</h3>
              <span class="upcc-wait-card__tag" :class="severityClass(c)">
                {{ t(`waitTimes.severity.${waitSeverityFromText(c.wait_text) || 'unknown'}`) }}
              </span>
            </div>
            <p class="upcc-wait-card__city">{{ c.city }}</p>
            <p class="upcc-wait-card__wait" aria-live="polite">
              <span class="upcc-wait-card__wait-label">{{ t('upccWaitTimes.estimatedWait') }}</span>
              <span class="upcc-wait-card__wait-value">{{ c.wait_text }}</span>
            </p>
            <p v-if="showWaitDebug && c._debug" class="upcc-wait-card__debug" aria-label="Temporary debug">
              <span class="upcc-wait-card__debug-line">raw: {{ debugRawDisplay(c._debug) }}</span>
              <span class="upcc-wait-card__debug-line">source ts: {{ debugSourceTs(c._debug) }}</span>
            </p>
          </article>
        </div>

        <div v-if="checkedAtLabel" class="upcc-waits-section__times">
          <p class="upcc-waits-section__time-line">
            {{ t('waitTimes.lastChecked', { time: checkedAtLabel }) }}
          </p>
          <p v-if="sourceUpdatedLabel" class="upcc-waits-section__time-line">
            {{ t('waitTimes.sourceUpdated', { time: sourceUpdatedLabel }) }}
          </p>
          <p class="upcc-waits-section__time-note">{{ t('waitTimes.nearTimestampsNote') }}</p>
          <p class="upcc-waits-section__time-note upcc-waits-section__time-note--soft">
            {{ t('waitTimes.refreshHonestyNote') }}
          </p>
        </div>

        <p class="upcc-waits-section__disclaimer">
          {{ t('upccWaitTimes.disclaimer') }}
        </p>

        <p class="upcc-waits-section__source">
          {{ t('upccWaitTimes.sourceNote') }}
        </p>

        <div v-if="showWaitDebug && sectionDebug" class="upcc-waits-section__debug-footer" aria-label="Temporary debug">
          <p class="upcc-waits-section__debug-line">fetched from: {{ sectionDebug.fetched_url || '—' }}</p>
          <p class="upcc-waits-section__debug-line">parse mode: {{ sectionDebug.parse_mode || '—' }}</p>
        </div>

        <button
          type="button"
          class="upcc-waits-section__retry"
          :disabled="loading || refreshing"
          @click="loadWaitTimes({ fromUser: true })"
        >
          {{ userRefreshInFlight ? t('upccWaitTimes.refreshing') : t('upccWaitTimes.refreshNow') }}
        </button>
      </template>
    </div>
  </section>
</template>

<style scoped>
.upcc-waits-section {
  margin: 0 auto clamp(1.5rem, 4vw, 2.5rem);
  padding: clamp(1.35rem, 3.5vw, 2rem) clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
  border-radius: var(--radius-lg);
  background: linear-gradient(
    145deg,
    rgba(255, 252, 255, 0.98) 0%,
    rgba(236, 253, 245, 0.55) 48%,
    rgba(240, 249, 255, 0.92) 100%
  );
  border: 3px solid rgba(52, 211, 153, 0.45);
  box-shadow: var(--shadow-soft);
}

.upcc-waits-section__inner {
  max-width: 920px;
  margin: 0 auto;
}

.upcc-waits-section__intro {
  margin-bottom: 1.35rem;
}

.upcc-waits-section__title {
  margin: 0 0 0.45rem;
  font-family: var(--font-display);
  font-size: clamp(1.35rem, 3.2vw, 1.75rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.2;
  background: linear-gradient(115deg, #059669 0%, #14b8a6 45%, #6366f1 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.upcc-waits-section__lead {
  margin: 0;
  font-size: 0.98rem;
  color: var(--color-ink-muted);
  line-height: 1.55;
  max-width: 40rem;
}

.upcc-waits-section__state {
  padding: 2rem 0.5rem;
  text-align: center;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.upcc-waits-section__error {
  margin: 0;
  padding: 1.1rem 1.2rem;
  border-radius: var(--radius-md);
  background: rgba(255, 232, 222, 0.95);
  border: 2px solid rgba(251, 146, 60, 0.45);
  color: var(--color-ink);
  font-weight: 600;
  line-height: 1.5;
}

.upcc-waits-section__warn {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: rgba(254, 243, 199, 0.65);
  border: 2px dashed rgba(250, 204, 21, 0.5);
  color: var(--color-ink-muted);
  font-size: 0.9rem;
  font-weight: 600;
}

.upcc-waits-section__legacy-note {
  margin: 0 0 1rem;
  padding: 0.85rem 1rem;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
  background: rgba(241, 245, 249, 0.95);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(148, 163, 184, 0.45);
}

.upcc-waits-section__empty {
  margin: 0 0 1rem;
  padding: 1rem 1.1rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
  font-weight: 600;
  text-align: center;
  border-radius: var(--radius-md);
  background: rgba(236, 253, 245, 0.75);
  border: 1px solid rgba(52, 211, 153, 0.35);
}

.upcc-waits-section__grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .upcc-waits-section__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .upcc-waits-section__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.upcc-waits-section__grid--dim {
  opacity: 0.72;
  transition: opacity 0.2s ease;
}

.upcc-wait-card {
  padding: 1rem 1.15rem 1.15rem;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 2px solid rgba(52, 211, 153, 0.4);
  box-shadow: var(--shadow-soft);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-height: 7.75rem;
}

.upcc-wait-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.55rem;
}

.upcc-wait-card__name {
  margin: 0;
  font-family: var(--font-display);
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-ink);
  flex: 1;
  min-width: 0;
}

.upcc-wait-card__tag {
  flex-shrink: 0;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.26rem 0.48rem;
  border-radius: var(--radius-pill);
  border: 2px solid transparent;
}

.upcc-wait-card__tag--short {
  background: rgba(74, 222, 128, 0.22);
  border-color: rgba(34, 197, 94, 0.45);
  color: #166534;
}

.upcc-wait-card__tag--medium {
  background: rgba(250, 204, 21, 0.28);
  border-color: rgba(234, 179, 8, 0.5);
  color: #854d0e;
}

.upcc-wait-card__tag--long {
  background: rgba(251, 146, 60, 0.22);
  border-color: rgba(249, 115, 22, 0.5);
  color: #9a3412;
}

.upcc-wait-card__tag--na {
  background: rgba(237, 233, 254, 0.65);
  border-color: rgba(196, 181, 253, 0.55);
  color: var(--color-ink-muted);
}

.upcc-wait-card__city {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.upcc-wait-card__wait {
  margin: 0.25rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
}

.upcc-wait-card__wait-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.upcc-wait-card__wait-value {
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 700;
  color: #0f766e;
  line-height: 1.1;
}

.upcc-wait-card__debug {
  margin: 0.5rem 0 0;
  padding-top: 0.45rem;
  border-top: 1px dashed rgba(148, 163, 184, 0.65);
  font-size: 0.65rem;
  line-height: 1.35;
  font-family: ui-monospace, monospace;
  color: #64748b;
  word-break: break-word;
}

.upcc-wait-card__debug-line {
  display: block;
}

.upcc-waits-section__debug-footer {
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

.upcc-waits-section__debug-line {
  margin: 0;
}

.upcc-waits-section__times {
  margin: 1.15rem 0 0;
  text-align: center;
}

.upcc-waits-section__time-line {
  margin: 0 0 0.25rem;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.45;
}

.upcc-waits-section__time-note {
  margin: 0.55rem 0 0;
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-soft);
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
}

.upcc-waits-section__time-note--soft {
  margin-top: 0.35rem;
  font-weight: 500;
  color: var(--color-ink-soft);
  opacity: 0.95;
}

.upcc-waits-section__disclaimer {
  margin: 1.1rem 0 0;
  padding: 0.9rem 1rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
  background: rgba(236, 253, 245, 0.85);
  border-radius: var(--radius-sm);
  border: 2px dashed rgba(16, 185, 129, 0.35);
}

.upcc-waits-section__source {
  margin: 0.75rem 0 0;
  font-size: 0.78rem;
  color: var(--color-ink-soft);
  text-align: center;
  line-height: 1.45;
}

.upcc-waits-section__retry {
  display: block;
  margin: 1.1rem auto 0;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-pill);
  border: 2px solid rgba(45, 212, 191, 0.55);
  background: rgba(255, 255, 255, 0.95);
  color: #0f766e;
  cursor: pointer;
  box-shadow: 2px 2px 0 rgba(110, 231, 183, 0.35);
}

.upcc-waits-section__retry:hover:not(:disabled) {
  background: #fff;
}

.upcc-waits-section__retry:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
