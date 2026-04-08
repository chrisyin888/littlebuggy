<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import TrendDetailModal from '../components/TrendDetailModal.vue'
import LittleBuggyMascot from '../components/LittleBuggyMascot.vue'
import ErWaitTimesSection from '../components/ErWaitTimesSection.vue'
import UpccWaitTimesSection from '../components/UpccWaitTimesSection.vue'
import { useHomepageSnapshot } from '../composables/useHomepageSnapshot.js'
import { isTrendDetailKey, heroRowToDetailKey, envRowToDetailKey } from '../content/trendDetails.js'
import { translateApiLevel } from '../utils/apiLabelMap.js'

const { t, tm, locale } = useI18n()
const { snapshot, snapshotLoading, snapshotError, formatSnapshotUpdatePhrase } = useHomepageSnapshot()

const provenanceRows = computed(() => {
  void locale.value
  const bundle = snapshot.value?.sources
  if (!bundle) return []
  const keys = [
    { key: 'respiratory', kind: 'respiratory' },
    { key: 'aqhi', kind: 'aqhi' },
    { key: 'weather', kind: 'weather' },
  ]
  return keys
    .map(({ key, kind }) => {
      const meta = bundle[key]
      if (!meta?.name) return null
      return {
        key,
        kindLabel: t(`home.provenance.kinds.${kind}`),
        name: meta.name,
        url: meta.url,
        refreshed: meta.refreshed_label,
        status: meta.status,
      }
    })
    .filter(Boolean)
})

const staleErrorShort = computed(() => {
  const e = snapshotError.value
  if (!e) return ''
  const s = String(e)
  return s.length > 160 ? `${s.slice(0, 157)}…` : s
})

const SNAPSHOT_STALE_MS = 10 * 24 * 60 * 60 * 1000
const snapshotLooksOutdated = computed(() => {
  const raw = snapshot.value?.updated_at
  if (!raw) return false
  const t0 = new Date(raw).getTime()
  if (Number.isNaN(t0)) return false
  return Date.now() - t0 > SNAPSHOT_STALE_MS
})

function levelToTone(level) {
  const L = String(level || '').toLowerCase()
  if (/very\s*high|^high|severe|rough/i.test(L)) return 'hot'
  if (/low|minimal|quiet|calm|good|nice/i.test(L)) return 'rise'
  return 'watch'
}

function severityScoreFromLabel(label, kind = 'virus') {
  const L = String(label || '').toLowerCase()
  if (kind === 'air') {
    if (/unhealthy|hazardous|very\s*poor|high\s*risk|severe|red|purple/i.test(L)) return 4
    if (/moderate|medium|fair|yellow|orange/i.test(L)) return 2.5
    if (/low\s*risk|good|great|excellent|clean|green/i.test(L)) return 1
    return 2
  }
  if (kind === 'weather') {
    if (/unavailable/i.test(L)) return 0.5
    if (/storm|snow|rain|drizzle|shower|thunder/i.test(L)) return 2.4
    return 1.4
  }
  if (/very\s*high|severe|extreme/i.test(L)) return 4
  if (/^high\b|high\s|spiking/i.test(L)) return 3
  if (/medium|moderate|rising|elevated|watch|busy/i.test(L)) return 2
  if (/low|minimal|quiet|calm|quieter|trickling/i.test(L)) return 1
  return 2
}

function levelToToneAir(air) {
  const L = String(air || '').toLowerCase()
  if (/unhealthy|hazard|high\s*risk|poor|very|severe/i.test(L)) return 'hot'
  if (/moderate|medium|fair/i.test(L)) return 'watch'
  return 'rise'
}

function sortRowsBySeverity(rows, scoreFn) {
  const enriched = rows.map((row, origIdx) => ({
    row,
    score: scoreFn(row, origIdx),
    origIdx,
  }))
  enriched.sort((a, b) => b.score - a.score || a.origIdx - b.origIdx)
  return enriched.map(({ row }, i) => ({
    ...row,
    priorityTop: i === 0,
  }))
}

function virusCardLabel(s, kind) {
  const raw = s[`${kind}_label`]
  if (typeof raw === 'string' && raw.trim()) return raw.trim()
  return t(`home.hero.virusLabels.${kind}`)
}

const liveHeroCards = computed(() => {
  void locale.value
  const s = snapshot.value
  if (!s) return null
  return [
    {
      kind: 'rsv',
      label: virusCardLabel(s, 'rsv'),
      value: translateApiLevel(s.rsv, t),
      blurb: '',
      tone: levelToTone(s.rsv),
      sticker: '🐞',
    },
    {
      kind: 'flu',
      label: virusCardLabel(s, 'flu'),
      value: translateApiLevel(s.flu, t),
      blurb: '',
      tone: levelToTone(s.flu),
      sticker: '🤒',
    },
    {
      kind: 'covid',
      label: virusCardLabel(s, 'covid'),
      value: translateApiLevel(s.covid, t),
      blurb: '',
      tone: levelToTone(s.covid),
      sticker: '😷',
    },
  ]
})

const fallbackHeroSummary = computed(() => [
  {
    kind: 'rsv',
    label: t('home.hero.virusLabels.rsv'),
    value: '—',
    blurb: '',
    tone: 'watch',
    sticker: '🐞',
  },
  {
    kind: 'flu',
    label: t('home.hero.virusLabels.flu'),
    value: '—',
    blurb: '',
    tone: 'watch',
    sticker: '🤒',
  },
  {
    kind: 'covid',
    label: t('home.hero.virusLabels.covid'),
    value: '—',
    blurb: '',
    tone: 'watch',
    sticker: '😷',
  },
])

const heroCards = computed(() => {
  void locale.value
  const live = liveHeroCards.value
  const s = snapshot.value
  if (live && s) {
    return sortRowsBySeverity(live, (row) => {
      if (row.kind === 'rsv') return severityScoreFromLabel(s.rsv, 'virus')
      if (row.kind === 'flu') return severityScoreFromLabel(s.flu, 'virus')
      if (row.kind === 'covid') return severityScoreFromLabel(s.covid, 'virus')
      return 2
    })
  }
  return sortRowsBySeverity(fallbackHeroSummary.value, () => 2)
})

function weatherWeekSummaryLine(s) {
  const wd = s?.weather_display
  if (wd && Number.isFinite(wd.high_c) && Number.isFinite(wd.low_c)) {
    const parts = [
      t('home.weather.weekSummaryRange', {
        high: Math.round(wd.high_c),
        low: Math.round(wd.low_c),
      }),
    ]
    if (wd.condition) parts.push(String(wd.condition))
    return parts.join(', ')
  }
  return translateApiLevel(s.weather, t)
}

const envSnapshotCards = computed(() => {
  void locale.value
  const s = snapshot.value
  if (!s) return []
  const wd = s.weather_display
  const weatherDetail =
    wd && Number.isFinite(wd.high_c) && Number.isFinite(wd.low_c) ? wd : null
  return sortRowsBySeverity(
    [
      {
        kind: 'weather',
        label: t('home.hero.labels.weather'),
        weatherUseDetail: !!weatherDetail,
        weatherCardTitle: weatherDetail
          ? t('home.weather.cardTitle', {
              place: weatherDetail.location_label || t('home.weather.defaultLocation'),
            })
          : t('home.hero.labels.weather'),
        weatherHigh: weatherDetail ? weatherDetail.high_c : null,
        weatherLow: weatherDetail ? weatherDetail.low_c : null,
        weatherCurrent:
          weatherDetail && Number.isFinite(weatherDetail.current_c) ? weatherDetail.current_c : null,
        weatherCondition: weatherDetail && weatherDetail.condition ? String(weatherDetail.condition) : '',
        value: weatherWeekSummaryLine(s),
        blurb: '',
        tone: levelToTone(s.weather),
        sticker: '☀️',
        sortValue: s.weather,
      },
      {
        kind: 'air',
        label: t('home.hero.labels.airQuality'),
        value: translateApiLevel(s.air_quality, t),
        blurb: '',
        tone: levelToToneAir(s.air_quality),
        sticker: '💨',
        sortValue: s.air_quality,
      },
    ],
    (row) => {
      if (row.kind === 'air') return severityScoreFromLabel(row.sortValue, 'air')
      return severityScoreFromLabel(row.sortValue, 'weather')
    },
  )
})

const formattedUpdatedAt = computed(() => {
  void locale.value
  const raw = snapshot.value?.updated_at
  if (!raw) return ''
  const phrase = formatSnapshotUpdatePhrase(raw, t, locale.value)
  return phrase ? t('snapshot.updatedPrefix', { phrase }) : ''
})

const virusDashboardRowsOrdered = computed(() => {
  void locale.value
  const live = liveHeroCards.value
  if (live) {
    const byKind = Object.fromEntries(live.map((r) => [r.kind, { ...r }]))
    const order = ['rsv', 'flu', 'covid'].map((k) => byKind[k]).filter(Boolean)
    const priorityKind = heroCards.value.find((r) => r.priorityTop)?.kind
    return order.map((r) => ({ ...r, priorityTop: r.kind === priorityKind }))
  }
  return heroCards.value
})

const envDashboardRowsOrdered = computed(() => {
  void locale.value
  const rows = envSnapshotCards.value
  if (!rows.length) return []
  const byKind = Object.fromEntries(rows.map((r) => [r.kind, { ...r }]))
  const order = ['weather', 'air'].map((k) => byKind[k]).filter(Boolean)
  const priorityKind = envSnapshotCards.value.find((r) => r.priorityTop)?.kind
  return order.map((r) => ({ ...r, priorityTop: r.kind === priorityKind }))
})

const seekHelp = computed(() => {
  void locale.value
  const v = tm('home.seek.lines')
  return Array.isArray(v) ? v : []
})

const trendModalOpen = ref(false)
const trendModalKey = ref(null)

function openTrendDetail(key) {
  if (!isTrendDetailKey(key)) return
  trendModalKey.value = key
  trendModalOpen.value = true
}

function closeTrendDetail() {
  trendModalOpen.value = false
  trendModalKey.value = null
}

function onHeroCardActivate(row) {
  openTrendDetail(heroRowToDetailKey(row))
}

function onHeroCardKeydown(e, row) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    onHeroCardActivate(row)
  }
}

function onEnvCardActivate(row) {
  const k = envRowToDetailKey(row)
  if (k) openTrendDetail(k)
}

function onEnvCardKeydown(e, row) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    onEnvCardActivate(row)
  }
}
</script>
<template>
  <div class="home">
    <section class="hero hero--product" aria-labelledby="hero-title">
      <div class="hero__shell">
        <div class="hero__grid-product">
          <div class="hero__column hero__column--copy">
            <h1 id="hero-title" class="hero__headline">{{ $t('home.hero.title') }}</h1>
            <p class="hero__lede">{{ $t('home.hero.subtitle') }}</p>
            <div class="hero__cta-row">
              <a href="#weekly-snapshot" class="hero__cta hero__cta--primary">{{
                $t('home.hero.btnSeeWeek')
              }}</a>
              <button type="button" class="hero__micro-link" @click="openTrendDetail('how_it_works')">
                {{ $t('home.hero.linkHowItWorks') }}
              </button>
            </div>

            <p
              v-if="snapshotError && !snapshot && !snapshotLoading"
              class="hero__alert hero__alert--soft"
              role="status"
            >
              {{ $t('home.hero.errorBanner') }}
            </p>
            <div
              v-else-if="snapshotError && snapshot && !snapshotLoading"
              class="hero__alert hero__alert--soft hero__alert--stale"
              role="status"
              aria-live="polite"
            >
              <p class="hero__alert-main">{{ $t('home.hero.staleDataBanner') }}</p>
              <p
                v-if="staleErrorShort"
                class="hero__alert-detail"
                :title="snapshotError || undefined"
              >
                {{ staleErrorShort }}
              </p>
            </div>
          </div>
          <div class="hero__column hero__column--visual">
            <div class="hero-preview" aria-hidden="true">
              <div class="hero-preview__chrome">
                <span class="hero-preview__dots" aria-hidden="true">
                  <span /><span /><span />
                </span>
                <span class="hero-preview__brand">LittleBuggy</span>
              </div>
              <div class="hero-preview__body">
                <p v-if="snapshotLoading" class="hero-preview__headline hero-preview__headline--skeleton" />
                <p v-else class="hero-preview__headline">{{ $t('home.hero.previewKicker') }}</p>
                <ul class="hero-preview__metrics" role="list">
                  <template v-if="snapshotLoading">
                    <li v-for="n in 3" :key="'hps' + n" class="hero-preview__metric hero-preview__metric--skeleton" />
                  </template>
                  <template v-else>
                    <li
                      v-for="row in virusDashboardRowsOrdered"
                      :key="row.kind"
                      class="hero-preview__metric"
                      :data-tone="row.tone"
                    >
                      <span class="hero-preview__metric-label">{{ row.label }}</span>
                      <span class="hero-preview__metric-value">{{ row.value }}</span>
                    </li>
                  </template>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="value-strip" :aria-label="$t('home.valueStrip.a11y')">
      <div class="value-strip__inner">
        <a href="#weekly-snapshot" class="value-strip__item">{{ $t('home.valueStrip.snapshot') }}</a>
        <a href="#emergency-wait-times" class="value-strip__item">{{ $t('home.valueStrip.erWaits') }}</a>
        <a href="#urgent-care-wait-times" class="value-strip__item">{{ $t('home.valueStrip.upccWaits') }}</a>
        <a href="#littlebug-help" class="value-strip__item">{{ $t('home.valueStrip.seekHelp') }}</a>
      </div>
    </section>

    <section
      id="weekly-snapshot"
      class="snapshot-dashboard snapshot-dashboard--clean"
      aria-labelledby="snapshot-section-title"
    >
      <div class="snapshot-dashboard__inner">
        <header class="snapshot-dashboard__header">
          <h2 id="snapshot-section-title" class="snapshot-dashboard__title">
            {{ $t('home.snapshotSection.title') }}
          </h2>
          <p class="snapshot-dashboard__subtitle">{{ $t('home.snapshotSection.deckShort') }}</p>
          <p
            v-if="!snapshotLoading && snapshotLooksOutdated && snapshot"
            class="snapshot-dashboard__stale-inline"
            role="status"
          >
            {{ $t('home.hero.pipelineQuietBanner') }}
          </p>
        </header>

        <div
          class="snapshot-surface"
          :data-live="snapshot ? 'yes' : 'no'"
          :class="{ 'snapshot-surface--loading': snapshotLoading }"
        >
          <template v-if="snapshotLoading">
            <ul
              class="snapshot-dash__grid snapshot-dash__grid--virus snapshot-dash__grid--skeleton"
              aria-busy="true"
              :aria-label="$t('home.hero.loadingSnapshot')"
            >
              <li v-for="n in 3" :key="'vsk' + n" class="snapshot-dash__skeleton-card" />
            </ul>
          </template>
          <template v-else>
            <p class="snapshot-dash__row-eyebrow">{{ $t('home.hero.dashboardRowViruses') }}</p>
            <ul class="snapshot-dash__grid snapshot-dash__grid--virus" role="list">
              <li
                v-for="row in virusDashboardRowsOrdered"
                :key="row.kind"
                class="snapshot-dash__cell"
                role="listitem"
              >
                <div
                  class="snapshot-dash__card snapshot-dash__card--interactive"
                  :class="{ 'snapshot-dash__card--priority': row.priorityTop }"
                  :data-tone="row.tone"
                  role="button"
                  tabindex="0"
                  :aria-label="$t('home.common.learnMore', { topic: row.label })"
                  @click="onHeroCardActivate(row)"
                  @keydown="onHeroCardKeydown($event, row)"
                >
                  <span v-if="row.priorityTop" class="snapshot-dash__priority-badge">{{
                    $t('home.common.mostActive')
                  }}</span>
                  <span class="snapshot-dash__card-icon" aria-hidden="true">{{ row.sticker }}</span>
                  <div class="snapshot-dash__card-body">
                    <span class="snapshot-dash__card-title">{{ row.label }}</span>
                    <span class="snapshot-dash__card-level">{{ row.value }}</span>
                    <span v-if="row.blurb" class="snapshot-dash__card-note">{{ row.blurb }}</span>
                  </div>
                </div>
              </li>
            </ul>

            <template v-if="snapshot">
              <p class="snapshot-dash__row-eyebrow">{{ $t('home.snapshotSection.envEyebrow') }}</p>
              <ul class="snapshot-dash__grid snapshot-dash__grid--env" role="list">
                <li
                  v-for="row in envDashboardRowsOrdered"
                  :key="row.kind"
                  class="snapshot-dash__cell"
                  role="listitem"
                >
                  <div
                    class="snapshot-dash__card snapshot-dash__card--interactive"
                    :class="{ 'snapshot-dash__card--priority': row.priorityTop }"
                    :data-tone="row.tone"
                    role="button"
                    tabindex="0"
                    :aria-label="$t('home.common.learnMore', { topic: row.label })"
                    @click="onEnvCardActivate(row)"
                    @keydown="onEnvCardKeydown($event, row)"
                  >
                    <span v-if="row.priorityTop" class="snapshot-dash__priority-badge">{{
                      $t('home.common.mostActive')
                    }}</span>
                    <span class="snapshot-dash__card-icon" aria-hidden="true">{{ row.sticker }}</span>
                    <div class="snapshot-dash__card-body">
                      <span class="snapshot-dash__card-title">{{
                        row.weatherUseDetail ? row.weatherCardTitle : row.label
                      }}</span>
                      <template v-if="row.kind === 'weather' && row.weatherUseDetail">
                        <div class="snapshot-dash__weather-range" role="group" :aria-label="row.weatherCardTitle">
                          <span class="snapshot-dash__weather-hilo snapshot-dash__weather-hilo--high">{{
                            $t('home.weather.highTemp', { n: Math.round(row.weatherHigh) })
                          }}</span>
                          <span class="snapshot-dash__weather-hilo snapshot-dash__weather-hilo--low">{{
                            $t('home.weather.lowTemp', { n: Math.round(row.weatherLow) })
                          }}</span>
                        </div>
                        <p v-if="row.weatherCondition" class="snapshot-dash__weather-condition">
                          {{ row.weatherCondition }}
                        </p>
                        <p v-if="row.weatherCurrent != null" class="snapshot-dash__weather-current">
                          {{ $t('home.weather.currentSmall', { n: Math.round(row.weatherCurrent) }) }}
                        </p>
                      </template>
                      <span v-else class="snapshot-dash__card-level">{{ row.value }}</span>
                      <span v-if="row.blurb" class="snapshot-dash__card-note">{{ row.blurb }}</span>
                    </div>
                  </div>
                </li>
              </ul>
            </template>

            <p v-if="snapshot?.data_quality_note" class="snapshot-dash__dq" role="status">
              {{ snapshot.data_quality_note }}
            </p>

            <nav
              v-if="!snapshotLoading && (formattedUpdatedAt || provenanceRows.length)"
              class="snapshot-foot snapshot-foot--simple"
              :aria-label="$t('home.hero.sourcesFooterLabel')"
            >
              <p v-if="formattedUpdatedAt && snapshot?.updated_at" class="snapshot-foot__meta">
                <time class="snapshot-foot__time" :datetime="snapshot.updated_at">{{ formattedUpdatedAt }}</time>
              </p>
              <div class="snapshot-foot__actions">
                <button type="button" class="snapshot-foot__linkish" @click="openTrendDetail('how_it_works')">
                  {{ $t('home.hero.howSources') }}
                </button>
                <ul class="snapshot-foot__source-list" role="list">
                  <li v-for="row in provenanceRows" :key="row.key" class="snapshot-foot__source-item">
                    <a
                      v-if="row.url"
                      class="snapshot-foot__source-link"
                      :href="row.url"
                      target="_blank"
                      rel="noopener noreferrer"
                      :title="row.name"
                      :aria-label="row.name"
                      >{{ row.kindLabel }}</a
                    >
                    <span v-else class="snapshot-foot__muted" :title="row.name">{{ row.kindLabel }}</span>
                  </li>
                </ul>
              </div>
            </nav>
          </template>
        </div>
      </div>
    </section>

    <ErWaitTimesSection />

    <UpccWaitTimesSection />

    <section id="littlebug-help" class="section seek section--warm-slab" aria-labelledby="seek-heading">
      <div class="seek-card seek-card--reassuring">
        <div class="seek-card__head">
          <div class="seek-card__mascot" aria-hidden="true">
            <LittleBuggyMascot pose="help" size="md" />
          </div>
          <div>
            <h2 id="seek-heading" class="seek-card__title">{{ $t('home.seek.title') }}</h2>
            <p class="seek-card__lead">
              {{ $t('home.seek.lead') }}
            </p>
          </div>
        </div>
        <ul class="seek-card__list">
          <li v-for="(line, i) in seekHelp" :key="i">
            <span class="seek-card__check" aria-hidden="true" />
            {{ line }}
          </li>
        </ul>
      </div>
    </section>

    <TrendDetailModal
      :open="trendModalOpen"
      :topic-key="trendModalKey"
      @close="closeTrendDetail"
    />
  </div>
</template>
<style scoped>
.home {
  position: relative;
  z-index: 0;
  display: flex;
  flex-direction: column;
  gap: clamp(2rem, 5.5vw, 3.75rem);
}

.section--warm-slab {
  position: relative;
  padding: clamp(1.25rem, 3vw, 1.85rem);
  margin-left: clamp(-0.5rem, -1vw, 0rem);
  margin-right: clamp(-0.5rem, -1vw, 0rem);
  border-radius: var(--radius-xl);
  background-image: var(--pattern-dots-soft),
    linear-gradient(
      168deg,
      rgba(255, 255, 255, 0.55) 0%,
      rgba(255, 251, 235, 0.35) 50%,
      rgba(237, 233, 254, 0.25) 100%
    );
  background-size: var(--pattern-dots-size-lg), auto;
  border: 3px solid rgba(255, 255, 255, 0.85);
  box-shadow: 4px 4px 0 rgba(186, 230, 253, 0.28), 0 16px 40px rgba(61, 53, 64, 0.04);
}

@media (min-width: 900px) {
  .section--warm-slab {
    margin-left: 0;
    margin-right: 0;
    padding-left: clamp(1.5rem, 2.5vw, 2.25rem);
    padding-right: clamp(1.5rem, 2.5vw, 2.25rem);
  }
}

.home__sparkles {
  position: absolute;
  inset: 0;
  top: -1rem;
  height: 140vh;
  max-height: 2200px;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
}

.home__sparkle {
  position: absolute;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fde047, #fb923c);
  opacity: 0.45;
  animation: sparkle-drift 14s ease-in-out infinite;
}

.home__sparkle--2,
.home__sparkle--5,
.home__sparkle--9 {
  background: linear-gradient(135deg, #a78bfa, #f472b6);
}

.home__sparkle--3,
.home__sparkle--7,
.home__sparkle--12 {
  width: 5px;
  height: 5px;
  background: #7dd3fc;
  opacity: 0.5;
}

.home__sparkle--1 {
  top: 4%;
  left: 6%;
  animation-delay: 0s;
}
.home__sparkle--2 {
  top: 12%;
  right: 8%;
  animation-delay: -2s;
}
.home__sparkle--3 {
  top: 22%;
  left: 18%;
  animation-delay: -4s;
}
.home__sparkle--4 {
  top: 35%;
  right: 4%;
  animation-delay: -1s;
}
.home__sparkle--5 {
  top: 48%;
  left: 3%;
  animation-delay: -3s;
}
.home__sparkle--6 {
  top: 58%;
  right: 14%;
  animation-delay: -5s;
}
.home__sparkle--7 {
  top: 68%;
  left: 12%;
  animation-delay: -2.5s;
}
.home__sparkle--8 {
  top: 78%;
  right: 22%;
  animation-delay: -4.5s;
}
.home__sparkle--9 {
  top: 88%;
  left: 28%;
  animation-delay: -1.5s;
}
.home__sparkle--10 {
  top: 15%;
  left: 45%;
  animation-delay: -6s;
}
.home__sparkle--11 {
  top: 42%;
  left: 52%;
  animation-delay: -3.5s;
}
.home__sparkle--12 {
  top: 62%;
  right: 35%;
  animation-delay: -5.5s;
}
.home__sparkle--13 {
  top: 8%;
  right: 28%;
  animation-delay: -0.5s;
}
.home__sparkle--14 {
  top: 52%;
  left: 72%;
  animation-delay: -4.2s;
}

@keyframes sparkle-drift {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.35;
  }
  50% {
    transform: translate(6px, -10px) scale(1.15);
    opacity: 0.65;
  }
}

.home__clouds {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
}

.home__cloud {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.55);
  filter: blur(2px);
}

.home__cloud--1 {
  width: min(120px, 28vw);
  height: 48px;
  top: 8%;
  right: -2%;
  opacity: 0.7;
}

.home__cloud--2 {
  width: min(180px, 40vw);
  height: 64px;
  bottom: 18%;
  left: -5%;
  opacity: 0.5;
}

/* —— Hero —— */
.hero {
  position: relative;
  padding: clamp(1.65rem, 4vw, 2.45rem);
  padding-bottom: clamp(2rem, 4.8vw, 2.85rem);
  border-radius: calc(var(--radius-xl) + 4px);
  background-image: var(--pattern-dots-soft),
    linear-gradient(
      152deg,
      rgba(255, 252, 247, 0.99) 0%,
      rgba(255, 236, 214, 0.72) 26%,
      rgba(252, 231, 243, 0.4) 52%,
      rgba(212, 239, 255, 0.55) 78%,
      rgba(255, 249, 240, 0.92) 100%
    );
  background-size: var(--pattern-dots-size-lg), auto;
  border: 5px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  outline: 3px dashed rgba(253, 186, 116, 0.38);
  outline-offset: 5px;
  overflow: hidden;
}

.hero.hero--product {
  position: relative;
  padding: clamp(2.25rem, 5.5vw, 4rem) clamp(1.25rem, 4vw, 2rem);
  margin: 0;
  border-radius: 0;
  background: linear-gradient(165deg, #fbfcfe 0%, #f1f5f9 52%, #eef2ff 100%);
  background-image: none;
  border: none;
  box-shadow: none;
  outline: none;
  outline-offset: 0;
  overflow: visible;
}

.hero.hero--product::before {
  display: none;
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.65) inset, 0 -20px 50px rgba(255, 200, 140, 0.12) inset;
}

.hero__wave {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 18px;
  background: repeating-linear-gradient(
    90deg,
    transparent,
    transparent 12px,
    rgba(251, 182, 206, 0.35) 12px,
    rgba(251, 182, 206, 0.35) 14px
  );
  mask-image: radial-gradient(ellipse 120% 100% at 50% 100%, #000 55%, transparent 55.5%);
  -webkit-mask-image: radial-gradient(ellipse 120% 100% at 50% 100%, #000 55%, transparent 55.5%);
  opacity: 0.85;
  pointer-events: none;
}

.hero__blobs {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.hero__blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.55;
  animation: blob-drift 18s ease-in-out infinite;
}

.hero__blob--a {
  width: 180px;
  height: 180px;
  top: -60px;
  right: -40px;
  background: #a7f3d0;
}

.hero__blob--b {
  width: 220px;
  height: 220px;
  bottom: -80px;
  left: -60px;
  background: #e9d5ff;
  animation-delay: -6s;
}

.hero__blob--c {
  width: 140px;
  height: 140px;
  top: 40%;
  left: 35%;
  background: #fde68a;
  opacity: 0.35;
  animation-delay: -12s;
}

.hero__blob--d {
  width: 100px;
  height: 100px;
  top: 8%;
  left: 8%;
  background: #ffc9d8;
  opacity: 0.4;
  animation-delay: -3s;
}

.hero__micro {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.hero__dot {
  position: absolute;
  border-radius: 50%;
  opacity: 0.55;
  animation: dot-bob 5s ease-in-out infinite;
}

.hero__dot--1 {
  width: 8px;
  height: 8px;
  top: 12%;
  left: 18%;
  background: #7dd3fc;
  animation-delay: 0s;
}
.hero__dot--2 {
  width: 6px;
  height: 6px;
  top: 22%;
  right: 12%;
  background: #fda4af;
  animation-delay: -0.8s;
}
.hero__dot--3 {
  width: 5px;
  height: 5px;
  top: 38%;
  left: 8%;
  background: #fde047;
  animation-delay: -1.2s;
}
.hero__dot--4 {
  width: 7px;
  height: 7px;
  bottom: 28%;
  right: 20%;
  background: #c4b5fd;
  animation-delay: -2s;
}
.hero__dot--5 {
  width: 5px;
  height: 5px;
  bottom: 18%;
  left: 22%;
  background: #6ee7b7;
  animation-delay: -1.5s;
}
.hero__dot--6 {
  width: 6px;
  height: 6px;
  top: 55%;
  right: 8%;
  background: #fcd34d;
  animation-delay: -2.8s;
}
.hero__dot--7 {
  width: 4px;
  height: 4px;
  top: 68%;
  left: 14%;
  background: #f9a8d4;
  animation-delay: -0.4s;
}
.hero__dot--8 {
  width: 8px;
  height: 8px;
  top: 8%;
  right: 35%;
  background: #93c5fd;
  animation-delay: -3.2s;
}
.hero__dot--9 {
  width: 5px;
  height: 5px;
  bottom: 42%;
  left: 4%;
  background: #fdba74;
  animation-delay: -1.8s;
}
.hero__dot--10 {
  width: 6px;
  height: 6px;
  top: 48%;
  left: 42%;
  background: #a5b4fc;
  animation-delay: -2.2s;
}
.hero__dot--11 {
  width: 5px;
  height: 5px;
  bottom: 8%;
  right: 42%;
  background: #67e8f9;
  animation-delay: -0.9s;
}
.hero__dot--12 {
  width: 7px;
  height: 7px;
  top: 30%;
  right: 28%;
  background: #fbbf24;
  animation-delay: -2.5s;
}

@keyframes dot-bob {
  0%,
  100% {
    transform: translate(0, 0);
    opacity: 0.45;
  }
  50% {
    transform: translate(4px, -6px);
    opacity: 0.75;
  }
}

@keyframes blob-drift {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(12px, -10px) scale(1.05);
  }
}

.hero__grid {
  position: relative;
  display: grid;
  gap: clamp(1.5rem, 4.5vw, 2.35rem);
  align-items: center;
  z-index: 1;
}

.hero__shell {
  width: 100%;
  max-width: min(1120px, 100%);
  margin: 0 auto;
}

.hero__grid-product {
  display: grid;
  gap: clamp(2rem, 5vw, 3.25rem);
  align-items: center;
}

@media (min-width: 900px) {
  .hero__grid-product {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr);
    gap: clamp(2.5rem, 5vw, 4rem);
  }
}

@media (max-width: 899px) {
  .hero__column--visual {
    order: -1;
  }
}

.hero__column--copy {
  min-width: 0;
}

.hero__headline {
  margin: 0 0 0.65rem;
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 4.2vw, 2.65rem);
  font-weight: 700;
  line-height: 1.18;
  letter-spacing: -0.02em;
  color: var(--color-ink);
  text-shadow: none;
  max-width: 20ch;
}

.hero__lede {
  margin: 0 0 1.75rem;
  font-size: clamp(0.98rem, 2vw, 1.125rem);
  line-height: 1.55;
  font-weight: 500;
  color: #64748b;
  max-width: 26rem;
}

.hero__cta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem 1rem;
}

.hero__cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.72rem 1.4rem;
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  text-decoration: none;
  border-radius: 999px;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease,
    border-color 0.18s ease;
}

.hero__cta--primary {
  color: #fff;
  background: linear-gradient(135deg, #fb7185 0%, #e879f9 48%, #a78bfa 100%);
  border: none;
  box-shadow: 0 4px 20px rgba(244, 114, 182, 0.26);
}

.hero__cta--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 26px rgba(167, 139, 250, 0.3);
}

.hero__cta--secondary {
  color: var(--color-ink);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.42);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.hero__cta--secondary:hover {
  background: #fff;
  border-color: rgba(100, 116, 139, 0.5);
}

.hero__cta:focus-visible {
  outline: 2px solid #a78bfa;
  outline-offset: 2px;
}

.hero__lang-hint {
  margin: 1rem 0 0;
  max-width: 28rem;
  font-size: 0.75rem;
  line-height: 1.45;
  font-weight: 500;
  color: #94a3b8;
}

.hero-preview {
  width: 100%;
  max-width: min(26rem, 100%);
  margin-left: auto;
  margin-right: auto;
  border-radius: 14px;
  background: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 22px 48px rgba(15, 23, 42, 0.09),
    0 0 0 1px rgba(15, 23, 42, 0.055);
  overflow: hidden;
}

@media (min-width: 900px) {
  .hero-preview {
    margin-right: 0;
    margin-left: auto;
  }
}

.hero-preview__chrome {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.hero-preview__dots {
  display: flex;
  gap: 5px;
}

.hero-preview__dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e2e8f0;
}

.hero-preview__dots span:nth-child(1) {
  background: #fda4af;
}

.hero-preview__dots span:nth-child(2) {
  background: #fcd34d;
}

.hero-preview__dots span:nth-child(3) {
  background: #86efac;
}

.hero-preview__brand {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
}

.hero-preview__body {
  padding: 1rem 1.05rem 1.1rem;
}

.hero-preview__headline {
  margin: 0 0 0.8rem;
  font-family: var(--font-display);
  font-size: clamp(0.95rem, 2.2vw, 1.05rem);
  font-weight: 800;
  line-height: 1.32;
  letter-spacing: -0.01em;
  color: var(--color-ink);
}

.hero-preview__headline--skeleton {
  height: 1.35rem;
  max-width: 92%;
  border-radius: 7px;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: hero-shimmer 1.35s ease-in-out infinite;
}

.hero-preview__metrics {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.hero-preview__metric {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.65rem;
  padding: 0.5rem 0.6rem;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.75);
}

.hero-preview__metric[data-tone='hot'] {
  background: rgba(254, 242, 242, 0.55);
  border-color: rgba(252, 165, 165, 0.32);
}

.hero-preview__metric[data-tone='watch'] {
  background: rgba(254, 252, 232, 0.55);
  border-color: rgba(253, 224, 71, 0.28);
}

.hero-preview__metric[data-tone='rise'] {
  background: rgba(236, 253, 245, 0.55);
  border-color: rgba(110, 231, 183, 0.28);
}

.hero-preview__metric--skeleton {
  height: 2.35rem;
  border: none;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: hero-shimmer 1.35s ease-in-out infinite;
}

.hero-preview__metric-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--color-ink-soft);
}

.hero-preview__metric-value {
  flex-shrink: 0;
  font-family: var(--font-display);
  font-size: 0.92rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-ink);
}

.value-strip {
  padding: 0.75rem 1.25rem;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  background: rgba(255, 255, 255, 0.65);
}

.value-strip__inner {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.35rem;
  max-width: min(1120px, 100%);
  margin: 0 auto;
  text-align: center;
}

@media (min-width: 640px) {
  .value-strip__inner {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem 1.25rem;
    align-items: center;
  }
}

.value-strip__item {
  display: block;
  padding: 0.4rem 0.35rem;
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1.35;
  color: #475569;
  text-decoration: none;
  border-radius: 8px;
  transition:
    color 0.15s ease,
    background 0.15s ease;
}

.value-strip__item:hover {
  color: #4c1d95;
  background: rgba(99, 102, 241, 0.07);
}

.value-strip__item:focus-visible {
  outline: 2px solid #a78bfa;
  outline-offset: 2px;
}

.hero__figure {
  margin: 0;
}

.hero__shot {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 14px;
  box-shadow:
    0 24px 48px rgba(15, 23, 42, 0.09),
    0 0 0 1px rgba(255, 255, 255, 0.75) inset;
}

.hero__alert {
  margin: 1.5rem 0 0;
  padding: 0;
  max-width: 32rem;
  font-size: 0.875rem;
  line-height: 1.5;
  font-weight: 500;
  color: #9a3412;
}

.hero__alert-main {
  margin: 0 0 0.35rem;
  font-weight: 600;
  color: var(--color-ink);
}

.hero__alert-detail {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  word-break: break-word;
}

.hero__grid--intro {
  width: 100%;
  max-width: min(1180px, 100%);
  margin-inline: auto;
}

.hero__intro-shell {
  position: relative;
  padding: clamp(0.85rem, 2.5vw, 1.15rem);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.42);
  border: 3px solid rgba(255, 255, 255, 0.88);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    3px 3px 0 rgba(186, 230, 253, 0.35);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

@media (min-width: 900px) {
  .hero__grid--intro {
    grid-template-columns: minmax(0, 1.12fr) minmax(0, 1fr);
    gap: clamp(1.75rem, 3.5vw, 3rem);
    align-items: center;
  }
}

.hero__copy {
  text-align: center;
}

@media (min-width: 900px) {
  .hero__copy {
    text-align: left;
  }
}

.hero__copy--intro .hero__subtitle,
.hero__copy--intro .hero__value-line {
  max-width: none;
}

.hero__intro {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 0;
}

@media (min-width: 640px) {
  .hero__intro {
    flex-direction: row;
    align-items: flex-start;
    text-align: left;
  }
}

.hero__intro-mascot {
  flex-shrink: 0;
  padding: 0.4rem 0.45rem;
  border-radius: var(--radius-lg);
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 228, 230, 0.45) 45%, rgba(254, 243, 199, 0.55) 100%);
  border: 3px solid #fff;
  box-shadow: var(--shadow-toy-lift);
  transform: rotate(-2deg);
}

.hero__intro-text {
  flex: 1;
  min-width: 0;
  text-align: center;
}

@media (min-width: 640px) {
  .hero__intro-text {
    text-align: left;
  }
}

.hero__eyebrow {
  margin: 0 0 1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 1.15rem;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #7c3aed;
  background: rgba(255, 255, 255, 0.92);
  border-radius: var(--radius-pill);
  border: 3px solid rgba(186, 230, 253, 0.85);
  box-shadow: 3px 3px 0 rgba(255, 200, 140, 0.35);
}

.hero__title {
  margin: 0 0 0.85rem;
  font-family: var(--font-display);
  font-size: clamp(2.05rem, 5.2vw, 3.05rem);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: 0.01em;
  color: var(--color-ink);
  text-shadow:
    0 2px 0 rgba(255, 255, 255, 0.95),
    0 8px 28px rgba(251, 182, 206, 0.15);
}

.hero__subtitle {
  margin: 0 auto 1rem;
  font-size: 1.12rem;
  line-height: 1.68;
  font-weight: 600;
  color: var(--color-ink-muted);
  max-width: 32rem;
}

.hero__value-line {
  margin: 0 auto 1.35rem;
  padding: 0.75rem 1rem;
  max-width: 34rem;
  font-size: 0.98rem;
  line-height: 1.62;
  font-weight: 600;
  color: var(--color-ink);
  background: rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-md);
  border: 2px dashed rgba(167, 243, 208, 0.75);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

@media (min-width: 900px) {
  .hero__subtitle {
    margin-left: 0;
    margin-right: 0;
  }

  .hero__value-line {
    margin-left: 0;
    margin-right: 0;
  }
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  margin-bottom: 1.35rem;
}

@media (min-width: 900px) {
  .hero__actions {
    justify-content: flex-start;
  }
}

.hero__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.72rem 1.35rem;
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-decoration: none;
  border-radius: var(--radius-pill);
  border: 3px solid #fff;
  transition:
    transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.22s ease;
}

.hero__btn--primary {
  color: #fff;
  background: linear-gradient(135deg, #ff8f6b 0%, #f472b6 55%, #c084fc 100%);
  box-shadow: 4px 4px 0 rgba(255, 200, 120, 0.55), 0 8px 24px rgba(244, 114, 182, 0.22);
}

.hero__btn--primary:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 5px 5px 0 rgba(255, 200, 120, 0.5), 0 12px 28px rgba(244, 114, 182, 0.25);
}

.hero__btn--secondary {
  color: var(--color-ink);
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(196, 181, 253, 0.85);
  box-shadow: 4px 4px 0 rgba(186, 230, 253, 0.65);
}

.hero__btn--secondary:hover {
  transform: translateY(-3px);
  background: #fff;
  box-shadow: 5px 5px 0 rgba(167, 243, 208, 0.55);
}

.hero__copy--intro .hero__title {
  font-size: clamp(2.12rem, 5.5vw, 3.2rem);
  line-height: 1.07;
}

/* —— Standalone snapshot dashboard (below hero) —— */
.snapshot-dashboard {
  position: relative;
  padding: clamp(1.05rem, 2.8vw, 1.75rem) clamp(1rem, 4vw, 2rem) clamp(2rem, 5vw, 3.25rem);
  background: linear-gradient(180deg, #e8eef5 0%, #f1f5f9 38%, #f8fafc 100%);
  border-top: 1px solid rgba(203, 213, 225, 0.65);
}

.snapshot-dashboard.snapshot-dashboard--clean {
  padding: clamp(2rem, 5vw, 3.5rem) clamp(1.25rem, 4vw, 2rem) clamp(2.5rem, 6vw, 4rem);
  background: #f8fafc;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.snapshot-dashboard--clean .snapshot-dashboard__header {
  max-width: 38rem;
}

@media (min-width: 768px) {
  .snapshot-dashboard--clean .snapshot-dashboard__header {
    margin-left: 0;
    margin-right: auto;
    text-align: left;
  }
}

.snapshot-dashboard__stale-inline {
  margin: 0.65rem 0 0;
  max-width: 40rem;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.45;
  color: #9a3412;
}

.snapshot-surface {
  max-width: min(56rem, 100%);
  margin: 0 auto;
}

.snapshot-surface--loading {
  pointer-events: none;
  opacity: 0.9;
}

.snapshot-foot {
  margin-top: clamp(1.25rem, 3vw, 1.75rem);
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}

.snapshot-foot__drawer {
  margin: 0 0 0.85rem;
  border: none;
}

.snapshot-foot__summary {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748b;
  list-style: none;
}

.snapshot-foot__summary::-webkit-details-marker {
  display: none;
}

.snapshot-foot__summary::after {
  content: '';
  width: 0.35em;
  height: 0.35em;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: rotate(45deg);
  margin-top: -0.15em;
  opacity: 0.55;
}

.snapshot-foot__drawer[open] .snapshot-foot__summary::after {
  transform: rotate(-135deg);
  margin-top: 0.1em;
}

.snapshot-foot__drawer-body {
  margin-top: 0.65rem;
  padding: 0 0 0.15rem;
  max-width: 40rem;
}

.snapshot-foot__p {
  margin: 0 0 0.55rem;
  font-size: 0.8rem;
  line-height: 1.55;
  font-weight: 500;
  color: #64748b;
}

.snapshot-foot__p:last-child {
  margin-bottom: 0;
}

.snapshot-foot__nested {
  margin-top: 0.5rem;
  padding: 0.5rem 0 0;
  border-top: 1px dashed rgba(148, 163, 184, 0.35);
}

.snapshot-foot__nested summary {
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 700;
  color: #5b21b6;
}

.snapshot-foot__links {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.35rem 1rem;
}

.snapshot-foot__time {
  font-size: 0.74rem;
  font-weight: 600;
  color: #94a3b8;
}

.snapshot-foot__linkish {
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 0.74rem;
  font-weight: 600;
  color: #5b21b6;
  text-decoration: underline;
  text-underline-offset: 0.12em;
  cursor: pointer;
}

.snapshot-foot__linkish:hover {
  color: #4c1d95;
}

.snapshot-foot__muted {
  font-size: 0.74rem;
  font-weight: 600;
  color: #94a3b8;
}

.snapshot-dashboard--clean .snapshot-dash__headline,
.snapshot-dashboard--clean .snapshot-dash__sub {
  text-align: left;
}

.snapshot-dashboard--clean .snapshot-dash__row-eyebrow {
  margin-top: 0.15rem;
}

.snapshot-dashboard--clean .snapshot-dash__card {
  border: 1px solid rgba(226, 232, 240, 0.65);
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.snapshot-dashboard--clean .snapshot-dash__card::before {
  opacity: 0.08;
}

.snapshot-dashboard--clean .snapshot-dash__card--interactive:hover {
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}

.snapshot-dashboard--clean .snapshot-dash__skeleton-card {
  border: 1px solid rgba(226, 232, 240, 0.5);
  box-shadow: none;
}

.home-read-guide {
  padding: clamp(1.5rem, 4vw, 2.35rem) clamp(1.25rem, 4vw, 1.75rem);
  background: #fff;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  border-bottom: 1px solid rgba(15, 23, 42, 0.05);
}

.home-read-guide__inner {
  max-width: min(40rem, 100%);
  margin: 0 auto;
}

.home-read-guide__title {
  margin: 0 0 0.5rem;
  font-family: var(--font-display);
  font-size: clamp(1.2rem, 3vw, 1.5rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--color-ink);
}

.home-read-guide__deck {
  margin: 0 0 1rem;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.home-read-guide__steps {
  margin: 0 0 1.15rem;
  padding-left: 1.2rem;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.6;
  color: #475569;
}

.home-read-guide__steps li {
  margin-bottom: 0.45rem;
}

.home-read-guide__steps li:last-child {
  margin-bottom: 0;
}

.home-read-guide__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
}

.home-read-guide__link {
  font-size: 0.82rem;
  font-weight: 700;
  color: #5b21b6;
  text-decoration: underline;
  text-underline-offset: 0.14em;
}

.home-read-guide__link:hover {
  color: #4c1d95;
}

.home-read-guide__dot {
  font-size: 0.82rem;
  font-weight: 700;
  color: #cbd5e1;
  user-select: none;
}

.home-read-guide__btn {
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  color: #5b21b6;
  text-decoration: underline;
  text-underline-offset: 0.14em;
  cursor: pointer;
}

.home-read-guide__btn:hover {
  color: #4c1d95;
}

.home-read-guide__link:focus-visible,
.home-read-guide__btn:focus-visible {
  outline: 2px solid #a78bfa;
  outline-offset: 2px;
  border-radius: 2px;
}

.home-language-compact__inner {
  max-width: min(42rem, 100%);
  margin: 0 auto;
  padding: clamp(1rem, 3vw, 1.35rem) clamp(0.75rem, 3vw, 1.25rem);
  text-align: center;
}

.home-language-compact__title {
  margin: 0 0 0.4rem;
  font-family: var(--font-display);
  font-size: clamp(1.05rem, 2.5vw, 1.25rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink);
}

.home-language-compact__hint {
  margin: 0 auto 0.85rem;
  max-width: 34rem;
  font-size: 0.86rem;
  line-height: 1.5;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.home-language-compact__switcher {
  display: flex;
  justify-content: center;
}

.snapshot-dashboard__inner {
  max-width: min(72rem, 100%);
  margin: 0 auto;
}

.snapshot-dashboard__header {
  margin-bottom: clamp(1rem, 2.5vw, 1.5rem);
}

.snapshot-dashboard__title {
  margin: 0 0 0.45rem;
  font-family: var(--font-display);
  font-size: clamp(1.45rem, 3.8vw, 1.85rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--color-ink);
}

.snapshot-dashboard__subtitle {
  margin: 0;
  max-width: 44rem;
  font-size: 0.95rem;
  line-height: 1.58;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.snapshot-dashboard__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 1rem;
  align-items: flex-start;
  margin-bottom: 1.25rem;
}

.snapshot-context {
  flex: 1 1 min(100%, 320px);
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
}

.snapshot-context__label {
  display: block;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #5b21b6;
  margin-bottom: 0.25rem;
}

.snapshot-context__text {
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.5;
  color: #475569;
}

.snapshot-dashboard__stale-flag {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.65rem;
  border-radius: var(--radius-md);
  font-size: 0.78rem;
  font-weight: 700;
  color: #9a3412;
  background: rgba(255, 247, 237, 0.95);
  border: 1px solid rgba(251, 146, 60, 0.4);
}

.snapshot-dashboard__stale-flag-mascot {
  flex-shrink: 0;
}

.snapshot-dashboard__board {
  display: flex;
  flex-direction: column;
  gap: 1.35rem;
}

.snapshot-dash__fineprint {
  margin-top: 0.35rem;
  padding: 0.65rem 0 0;
  border-top: 1px solid rgba(226, 232, 240, 0.85);
}

.snapshot-dash__fineprint-line {
  margin: 0 0 0.45rem;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.5;
  color: #64748b;
}

.snapshot-dash__fineprint-line--muted {
  font-size: 0.76rem;
  color: #94a3b8;
}

.snapshot-dash__details {
  margin-bottom: 0.55rem;
  font-size: 0.82rem;
  color: #64748b;
}

.snapshot-dash__details summary {
  cursor: pointer;
  font-weight: 700;
  color: #6d28d9;
}

.snapshot-dash__details-p {
  margin: 0.4rem 0 0;
  line-height: 1.55;
}

.snapshot-dashboard__trust {
  min-width: 0;
}

.snapshot-dashboard__trust-grid {
  display: grid;
  gap: 0.55rem;
}

@media (min-width: 640px) {
  .snapshot-dashboard__trust-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1080px) {
  .snapshot-dashboard__trust-grid {
    grid-template-columns: 1fr;
  }
}

.trust-card--compact {
  padding: 0.65rem 0.75rem;
}

.trust-card--compact .trust-card__h {
  margin-bottom: 0.3rem;
}

.trust-card--compact .trust-card__p {
  font-size: 0.78rem;
  line-height: 1.45;
}

.trust-panel-cta--inline {
  width: 100%;
  margin-top: 0.65rem;
}

.snapshot-dashboard__trust-hint {
  margin: 0.55rem 0 0;
  font-size: 0.74rem;
  font-weight: 600;
  line-height: 1.45;
  color: #94a3b8;
}

.snapshot-dashboard__trust--skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.snapshot-dashboard__nextbox {
  padding: 1rem 1.15rem;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(199, 210, 254, 0.85);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
}

.snapshot-dashboard__nextbox-title {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #5b21b6;
}

.snapshot-dashboard__nextbox-intro {
  margin: 0 0 0.5rem;
  font-size: 0.84rem;
  font-weight: 600;
  color: #475569;
}

.snapshot-dashboard__nextbox-list {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 0.84rem;
  line-height: 1.58;
  color: #334155;
}

.snapshot-dashboard__aware {
  padding-top: 0.25rem;
}

.hero-snapshot-panel--wide {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

@media (min-width: 1080px) {
  .hero-snapshot-panel--wide {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(17rem, 21rem);
    grid-template-rows: auto auto;
    gap: 1.25rem 2rem;
    align-items: start;
  }

  .hero-snapshot-panel--wide .hero-snapshot-panel__main--dashboard {
    grid-column: 1;
    grid-row: 1;
  }

  .hero-snapshot-panel--wide .snapshot-dashboard__trust,
  .hero-snapshot-panel--wide .snapshot-dashboard__trust--skeleton {
    grid-column: 2;
    grid-row: 1 / span 2;
    position: sticky;
    top: 1rem;
  }

  .hero-snapshot-panel--wide .hero-snapshot-panel__sources-footer {
    grid-column: 1;
    grid-row: 2;
    margin-top: 0;
  }
}

/* --- Hero snapshot: two-column product panel --- */
.hero-snapshot-shell {
  width: 100%;
  max-width: min(56rem, 100%);
  margin-top: 0.25rem;
  text-align: left;
}

.hero-snapshot-shell__foot {
  margin-top: 1.15rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
}

.hero__aware--snapshot-foot {
  margin: 0;
  max-width: none;
}

.hero-snapshot-panel {
  display: grid;
  gap: 1.15rem;
  width: 100%;
  padding: clamp(1rem, 2.5vw, 1.5rem);
  border-radius: calc(var(--radius-lg) + 8px);
  background: linear-gradient(
    152deg,
    rgba(255, 255, 255, 0.97) 0%,
    rgba(248, 250, 252, 0.92) 42%,
    rgba(253, 242, 248, 0.45) 100%
  );
  border: 1px solid rgba(255, 255, 255, 0.98);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 16px 48px rgba(61, 53, 64, 0.08),
    0 0 0 1px rgba(186, 230, 253, 0.35);
}

.hero-snapshot-panel--loading {
  opacity: 0.92;
}

@media (min-width: 960px) {
  .hero-snapshot-panel:not(.hero-snapshot-panel--wide) {
    grid-template-columns: minmax(0, 2.08fr) minmax(12rem, 1fr);
    gap: 1.25rem 1.5rem;
    align-items: start;
  }

  .hero-snapshot-panel:not(.hero-snapshot-panel--wide) .hero-snapshot-panel__aside {
    position: sticky;
    top: 0.5rem;
  }
}

.hero-snapshot-panel__main {
  min-width: 0;
}

.hero-snapshot-panel__main--dashboard {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  text-align: left;
}

.hero-snapshot-panel__sources-footer {
  grid-column: 1 / -1;
  width: 100%;
  margin-top: 0.25rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
}

.hero-snapshot-panel--wide .hero-snapshot-panel__sources-footer {
  grid-column: unset;
}

.snapshot-sources-foot {
  padding: 0.15rem 0 0.1rem;
}

.snapshot-sources-foot__updated {
  margin: 0 0 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--color-ink-soft);
}

.snapshot-sources-foot__label {
  margin: 0 0 0.3rem;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #94a3b8;
}

.snapshot-sources-foot__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 1.25rem;
  align-items: baseline;
}

.snapshot-sources-foot__item {
  margin: 0;
  padding: 0;
  list-style: none;
  max-width: 100%;
}

.snapshot-sources-foot__link,
.snapshot-sources-foot__name {
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--color-ink-muted);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}

.snapshot-sources-foot__link {
  color: #5b21b6;
  border-bottom-color: rgba(91, 33, 182, 0.25);
}

.snapshot-sources-foot__link:hover {
  color: #4c1d95;
  border-bottom-color: rgba(76, 29, 149, 0.45);
}

.snapshot-dash__headline {
  margin: 0 0 0.45rem;
  font-family: var(--font-display);
  font-size: clamp(1.05rem, 2.4vw, 1.28rem);
  font-weight: 800;
  line-height: 1.35;
  letter-spacing: 0.01em;
  color: var(--color-ink);
}

.snapshot-dash__headline--skeleton {
  height: 2.6rem;
  max-width: 36rem;
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: hero-shimmer 1.35s ease-in-out infinite;
}

.snapshot-dash__sub {
  margin: -0.15rem 0 1rem;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.snapshot-dash__row-eyebrow {
  margin: 0 0 0.45rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.snapshot-dash__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
  width: 100%;
  max-width: none;
  margin: 0 0 1.15rem;
  padding: 0;
  list-style: none;
}

@media (min-width: 640px) {
  .snapshot-dash__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
  }
}

.snapshot-dash__grid--skeleton {
  pointer-events: none;
}

.snapshot-dash__skeleton-card {
  min-height: 5.5rem;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: linear-gradient(90deg, #fff8f0 0%, #ffe8f0 45%, #e8f7fc 90%, #fff8f0 100%);
  background-size: 220% 100%;
  animation: hero-shimmer 1.35s ease-in-out infinite;
  list-style: none;
}

.snapshot-dash__cell {
  margin: 0;
  padding: 0;
  list-style: none;
  min-width: 0;
}

.snapshot-dash__card {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 0.65rem;
  min-height: 5.25rem;
  padding: 0.85rem 0.95rem 0.85rem 0.85rem;
  text-align: left;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(226, 232, 240, 0.98);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset, 0 6px 20px rgba(15, 23, 42, 0.045);
  transition: transform 0.2s var(--ease-soft), box-shadow 0.2s var(--ease-soft);
}

.snapshot-dash__card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background-image: var(--pattern-dots);
  background-size: var(--pattern-dots-size);
  opacity: 0.22;
  pointer-events: none;
}

.snapshot-dash__card > * {
  position: relative;
  z-index: 1;
}

.snapshot-dash__card-icon {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  line-height: 1;
  filter: drop-shadow(0 1px 0 rgba(255, 255, 255, 0.85));
}

.snapshot-dash__card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  align-items: flex-start;
}

.snapshot-dash__card-title {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.snapshot-dash__card-level {
  font-family: var(--font-display);
  font-size: clamp(1rem, 2.2vw, 1.14rem);
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-ink);
}

.snapshot-dash__weather-range {
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
  margin-top: 0.1rem;
}

.snapshot-dash__weather-hilo {
  font-family: var(--font-display);
  font-size: clamp(1.05rem, 2.5vw, 1.28rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: 0.01em;
}

.snapshot-dash__weather-hilo--high {
  color: #c2410c;
}

.snapshot-dash__weather-hilo--low {
  color: #0369a1;
  font-size: clamp(0.98rem, 2.2vw, 1.12rem);
  font-weight: 700;
}

.snapshot-dash__weather-condition {
  margin: 0.35rem 0 0;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--color-ink);
}

.snapshot-dash__weather-current {
  margin: 0.2rem 0 0;
  font-size: 0.76rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--color-ink-muted);
}

.snapshot-dash__card-note {
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.42;
  color: var(--color-ink-muted);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.snapshot-dash__priority-badge {
  position: absolute;
  top: 0.4rem;
  right: 0.45rem;
  z-index: 2;
  padding: 0.15rem 0.42rem;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #92400e;
  background: rgba(254, 243, 199, 0.95);
  border: 1px solid rgba(251, 191, 36, 0.45);
  border-radius: 999px;
}

.snapshot-dash__card--interactive {
  cursor: pointer;
}

.snapshot-dash__card--interactive:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 2px;
}

.snapshot-dash__card--interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.07);
}

.snapshot-dash__card[data-tone='hot'] {
  border-color: rgba(251, 113, 133, 0.35);
  background: linear-gradient(135deg, rgba(255, 241, 242, 0.9) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.snapshot-dash__card[data-tone='rise'] {
  border-color: rgba(167, 139, 250, 0.35);
  background: linear-gradient(135deg, rgba(245, 243, 255, 0.92) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.snapshot-dash__card[data-tone='watch'] {
  border-color: rgba(251, 191, 36, 0.4);
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.95) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.snapshot-dash__card--priority {
  border-width: 2px;
  border-color: rgba(251, 191, 36, 0.55);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 0 0 1px rgba(253, 224, 71, 0.35);
}

@media (prefers-reduced-motion: reduce) {
  .snapshot-dash__card--interactive:hover {
    transform: none;
  }

  .snapshot-dash__headline--skeleton,
  .snapshot-dash__skeleton-card {
    animation: none;
  }
}

.hero-week-summary--dash {
  margin-top: 0.35rem;
  padding: 0.85rem 1rem;
  border-radius: var(--radius-lg);
  background: rgba(248, 250, 252, 0.75);
  border: 1px solid rgba(226, 232, 240, 0.85);
  box-shadow: none;
}

.hero-week-summary__para--dash {
  margin: 0 0 0.45rem;
  font-size: 0.86rem;
}

.hero-week-summary__live-note--dash {
  margin: 0 0 0.45rem;
  padding: 0;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-ink-muted);
  background: none;
  border: none;
}

.hero-week-summary__trust--dash {
  margin: 0;
  padding: 0.5rem 0 0;
  border-top: 1px solid rgba(226, 232, 240, 0.75);
  font-size: 0.78rem;
}

.snapshot-dash__dq {
  margin: 0.65rem 0 0;
  padding: 0.55rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.45;
  color: #9a3412;
  background: rgba(255, 247, 237, 0.95);
  border: 1px solid rgba(251, 146, 60, 0.35);
  border-radius: var(--radius-md);
}

.hero__micro-link {
  display: inline-block;
  margin-top: 0.65rem;
  padding: 0;
  font-size: 0.82rem;
  font-weight: 700;
  color: #0d9488;
  text-decoration: underline;
  text-underline-offset: 0.15em;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
}
.hero__micro-link:hover {
  color: #0f766e;
}

.hero__cta-row .hero__micro-link {
  flex: 1 1 100%;
  text-align: center;
}

@media (min-width: 480px) {
  .hero__cta-row .hero__micro-link {
    flex: 0 1 auto;
    text-align: left;
  }
}

.snapshot-foot--simple {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
}

.snapshot-foot__meta {
  margin: 0 0 0.5rem;
  text-align: center;
}

.snapshot-foot__actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.snapshot-foot__source-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  max-width: 100%;
}

.snapshot-foot__source-item {
  margin: 0;
  text-align: center;
}

.snapshot-foot__source-link {
  font-size: 0.74rem;
  font-weight: 600;
  color: #5b21b6;
  text-decoration: underline;
  text-underline-offset: 0.12em;
}

.snapshot-foot__source-link:hover {
  color: #4c1d95;
}

/* Seek */
.seek-card {
  padding: clamp(1.65rem, 4vw, 2.5rem);
  border-radius: var(--radius-xl);
  background-image: var(--pattern-dots-soft), var(--pattern-dots),
    linear-gradient(
      150deg,
      rgba(255, 255, 255, 0.98) 0%,
      rgba(255, 244, 230, 0.55) 28%,
      rgba(224, 242, 254, 0.52) 55%,
      rgba(252, 231, 243, 0.48) 100%
    );
  background-size: var(--pattern-dots-size-lg), var(--pattern-dots-size), auto;
  border: 5px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  outline: 3px dashed rgba(167, 243, 208, 0.5);
  outline-offset: 4px;
}

.seek-card--reassuring .seek-card__title {
  color: #5b21b6;
}

.seek-card__head {
  display: flex;
  gap: 1.1rem;
  align-items: flex-start;
  margin-bottom: 1.35rem;
}

.seek-card__mascot {
  flex-shrink: 0;
  width: 5rem;
  height: 5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.88);
  border: 3px solid #fff;
  box-shadow: 4px 4px 0 rgba(125, 211, 252, 0.4);
  filter: drop-shadow(0 10px 20px rgba(52, 211, 153, 0.2));
}

.seek-card__title {
  margin: 0 0 0.45rem;
  font-family: var(--font-display);
  font-size: clamp(1.3rem, 2.8vw, 1.6rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink);
}

.seek-card__lead {
  margin: 0;
  font-size: 0.96rem;
  line-height: 1.6;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.seek-card__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.seek-card__list li {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  font-size: 0.93rem;
  line-height: 1.55;
  font-weight: 600;
  color: var(--color-ink);
  background: rgba(255, 255, 255, 0.82);
  border-radius: var(--radius-md);
  border: 2px solid rgba(226, 232, 240, 0.65);
  box-shadow: 0 4px 14px rgba(21, 37, 40, 0.04);
}

.seek-card__check {
  flex-shrink: 0;
  width: 1.2rem;
  height: 1.2rem;
  margin-top: 0.12rem;
  border-radius: 8px;
  background: linear-gradient(145deg, #f472b6, #fbbf24);
  border: 2px solid #fff;
  box-shadow: 2px 2px 0 rgba(167, 139, 250, 0.35);
}

.seek-card__check::after {
  content: '';
  display: block;
  width: 5px;
  height: 9px;
  margin: 2px auto 0;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translate(1px, -1px);
}
</style>
