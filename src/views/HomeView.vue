<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ActivityCardArt from '../components/ActivityCardArt.vue'
import TrendDetailModal from '../components/TrendDetailModal.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import LittleBuggyMascot from '../components/LittleBuggyMascot.vue'
import SymptomMiniIcon from '../components/SymptomMiniIcon.vue'
import MetroMapSection from '../components/MetroMapSection.vue'
import { useHomepageSnapshot } from '../composables/useHomepageSnapshot.js'
import {
  isTrendDetailKey,
  heroRowToDetailKey,
  envRowToDetailKey,
  activeCardToDetailKey,
} from '../content/trendDetails.js'
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

/** Warn if DB snapshot row is very old (cron / DB mismatch). */
const SNAPSHOT_STALE_MS = 10 * 24 * 60 * 60 * 1000
const snapshotLooksOutdated = computed(() => {
  const raw = snapshot.value?.updated_at
  if (!raw) return false
  const t = new Date(raw).getTime()
  if (Number.isNaN(t)) return false
  return Date.now() - t > SNAPSHOT_STALE_MS
})

const fallbackHeroSummary = computed(() => [
  {
    kind: 'active',
    label: t('home.hero.fallbackHero.active.label'),
    value: t('home.hero.fallbackHero.active.value'),
    blurb: t('home.hero.fallbackHero.active.blurb'),
    tone: 'hot',
    sticker: '🐞',
  },
  {
    kind: 'rising',
    label: t('home.hero.fallbackHero.rising.label'),
    value: t('home.hero.fallbackHero.rising.value'),
    blurb: t('home.hero.fallbackHero.rising.blurb'),
    tone: 'rise',
    sticker: '🌼',
  },
  {
    kind: 'watch',
    label: t('home.hero.fallbackHero.watch.label'),
    value: t('home.hero.fallbackHero.watch.value'),
    blurb: t('home.hero.fallbackHero.watch.blurb'),
    tone: 'watch',
    sticker: '💬',
  },
])

function levelToTone(level) {
  const L = String(level || '').toLowerCase()
  if (/very\s*high|^high|severe|rough/i.test(L)) return 'hot'
  if (/low|minimal|quiet|calm|good|nice/i.test(L)) return 'rise'
  return 'watch'
}

/** Numeric sort: higher = more worth attention (not clinical risk scoring). */
function severityScoreFromLabel(label, kind = 'virus') {
  const L = String(label || '').toLowerCase()

  if (kind === 'air') {
    if (/unhealthy|hazardous|very\s*poor|high\s*risk|severe|red|purple/i.test(L)) return 4
    if (/moderate|medium|fair|yellow|orange/i.test(L)) return 2.5
    if (/low\s*risk|good|great|excellent|clean|green/i.test(L)) return 1
    return 2
  }

  if (kind === 'outdoor') {
    if (/rough|hard|smog|poor|bad|awful/i.test(L)) return 3.8
    if (/take\s*it\s*easy|caution|careful/i.test(L)) return 3
    if (/indoor|cozy|rain/i.test(L)) return 2.2
    if (/fair|mixed|okay|ok\b/i.test(L)) return 2
    if (/nice|good|great|walk|lovely|sweet/i.test(L)) return 1.2
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

function fallbackHeroCardScore(row) {
  if (row.tone === 'hot') return 4
  if (row.tone === 'rise') return 3
  return 2.5
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

function virusBlurb(kind, level) {
  const L = String(level || '').toLowerCase()
  const branch = /high|very/i.test(L) ? 'high' : /low/i.test(L) ? 'low' : 'mid'
  if (kind === 'rsv') return t(`home.hero.blurbs.rsv.${branch}`)
  if (kind === 'flu') return t(`home.hero.blurbs.flu.${branch}`)
  return t(`home.hero.blurbs.covid.${branch}`)
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
      blurb: virusBlurb('rsv', s.rsv),
      tone: levelToTone(s.rsv),
      sticker: '🐞',
    },
    {
      kind: 'flu',
      label: virusCardLabel(s, 'flu'),
      value: translateApiLevel(s.flu, t),
      blurb: virusBlurb('flu', s.flu),
      tone: levelToTone(s.flu),
      sticker: '🤒',
    },
    {
      kind: 'covid',
      label: virusCardLabel(s, 'covid'),
      value: translateApiLevel(s.covid, t),
      blurb: virusBlurb('covid', s.covid),
      tone: levelToTone(s.covid),
      sticker: '😷',
    },
  ]
})

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
  return sortRowsBySeverity(fallbackHeroSummary.value, (row) => fallbackHeroCardScore(row))
})

const envSnapshotCards = computed(() => {
  void locale.value
  const s = snapshot.value
  if (!s) return []
  const rows = [
    {
      kind: 'air',
      label: t('home.hero.labels.airQuality'),
      value: translateApiLevel(s.air_quality, t),
      blurb: t('home.hero.envBlurbs.air'),
      tone: levelToToneAir(s.air_quality),
      sticker: '💨',
      sortValue: s.air_quality,
    },
    {
      kind: 'weather',
      label: t('home.hero.labels.weather'),
      value: translateApiLevel(s.weather, t),
      blurb: t('home.hero.envBlurbs.weather'),
      tone: levelToTone(s.weather),
      sticker: '☀️',
      sortValue: s.weather,
    },
    {
      kind: 'outdoor',
      label: t('home.hero.labels.outdoorFeel'),
      value: translateApiLevel(s.outdoor_feel, t),
      blurb: t('home.hero.envBlurbs.outdoor'),
      tone: levelToTone(s.outdoor_feel),
      sticker: '🧢',
      sortValue: s.outdoor_feel,
    },
  ]
  return sortRowsBySeverity(rows, (row) => {
    if (row.kind === 'air') return severityScoreFromLabel(row.sortValue, 'air')
    if (row.kind === 'weather') return severityScoreFromLabel(row.sortValue, 'weather')
    return severityScoreFromLabel(row.sortValue, 'outdoor')
  })
})

const formattedUpdatedAt = computed(() => {
  void locale.value
  const raw = snapshot.value?.updated_at
  if (!raw) return ''
  const phrase = formatSnapshotUpdatePhrase(raw, t, locale.value)
  return phrase ? t('snapshot.updatedPrefix', { phrase }) : ''
})

/** Short parent-facing lines — never the long backend `summary` paragraph. */
const parentWeekSummaryLines = computed(() => {
  const s = snapshot.value
  if (!s) return []
  void locale.value
  return [
    t('home.hero.weekSummary.lineOutdoor', {
      outdoor: translateApiLevel(s.outdoor_feel, t),
    }),
    t('home.hero.weekSummary.lineViruses', {
      rsv: translateApiLevel(s.rsv, t),
      flu: translateApiLevel(s.flu, t),
      covid: translateApiLevel(s.covid, t),
    }),
    t('home.hero.weekSummary.lineEnv', {
      air: translateApiLevel(s.air_quality, t),
      weather: translateApiLevel(s.weather, t),
    }),
  ]
})

/** Pre-written family copy from JSON (English); falls back to i18n lines when absent. */
const snapshotShortSummary = computed(() => {
  const s = snapshot.value?.short_summary
  return typeof s === 'string' && s.trim() ? s.trim() : ''
})

const snapshotLiveVsIllustrative = computed(() => {
  const s = snapshot.value?.live_vs_illustrative_note
  return typeof s === 'string' && s.trim() ? s.trim() : ''
})

/** First sentence of short_summary for dashboard headline (presentation only). */
const dashboardHeadline = computed(() => {
  void locale.value
  const s = snapshotShortSummary.value
  if (s) {
    const i = s.indexOf('. ')
    return (i > 0 ? s.slice(0, i + 1) : s).trim()
  }
  const lines = parentWeekSummaryLines.value
  if (lines.length) return lines[0]
  return t('home.hero.dashboardFallbackHeadline')
})

const dashboardHeadlineSub = computed(() => {
  const s = snapshotShortSummary.value
  if (!s) return ''
  const i = s.indexOf('. ')
  return i > 0 ? s.slice(i + 2).trim() : ''
})

/** Fixed column order: RSV → flu → COVID; keeps “most active” badge from severity sort. */
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

/** Fixed column order: weather → air → outdoor. */
const envDashboardRowsOrdered = computed(() => {
  void locale.value
  const rows = envSnapshotCards.value
  if (!rows.length) return []
  const byKind = Object.fromEntries(rows.map((r) => [r.kind, { ...r }]))
  const order = ['weather', 'air', 'outdoor'].map((k) => byKind[k]).filter(Boolean)
  const priorityKind = envSnapshotCards.value.find((r) => r.priorityTop)?.kind
  return order.map((r) => ({ ...r, priorityTop: r.kind === priorityKind }))
})

function virusActivityFromLevel(level) {
  const L = String(level || '').toLowerCase()
  if (/very\s*high|^high/i.test(L)) {
    return { activityKey: 'lots', activityDots: 3, badgeKey: 'bigNow', badgeKind: 'hot' }
  }
  if (/medium|moderate|rising|watch/i.test(L)) {
    return { activityKey: 'some', activityDots: 2, badgeKey: 'onRadar', badgeKind: 'watch' }
  }
  return { activityKey: 'quiet', activityDots: 1, badgeKey: 'calmer', badgeKind: 'rise' }
}

const topConcerns = computed(() => {
  void locale.value
  return [
    {
      id: 'tc1',
      title: t('home.topConcerns.tc1.title'),
      text: t('home.topConcerns.tc1.text'),
      tone: 'coral',
    },
    {
      id: 'tc2',
      title: t('home.topConcerns.tc2.title'),
      text: t('home.topConcerns.tc2.text'),
      tone: 'lilac',
    },
    {
      id: 'tc3',
      title: t('home.topConcerns.tc3.title'),
      text: t('home.topConcerns.tc3.text'),
      tone: 'mint',
    },
  ]
})

const activeItemsBase = [
  {
    id: 'rsv',
    activityKey: 'lots',
    activityDots: 3,
    badgeKey: 'bigNow',
    badgeKind: 'hot',
    kind: 'virus',
  },
  {
    id: 'flu',
    activityKey: 'lots',
    activityDots: 3,
    badgeKey: 'heatingUp',
    badgeKind: 'rise',
    kind: 'virus',
  },
  {
    id: 'covid',
    activityKey: 'lots',
    activityDots: 3,
    badgeKey: 'onRadar',
    badgeKind: 'watch',
    kind: 'virus',
  },
  {
    id: 'cold',
    activityKey: 'some',
    activityDots: 2,
    badgeKey: 'trendingNearby',
    badgeKind: 'watch',
    kind: 'virus',
  },
  {
    id: 'stomach',
    activityKey: 'some',
    activityDots: 2,
    badgeKey: 'heatingUp',
    badgeKind: 'rise',
    kind: 'virus',
  },
]

function staticActiveBuzzScore(item) {
  let score = item.activityDots
  if (item.badgeKind === 'hot') score += 0.45
  if (item.badgeKind === 'rise') score += 0.25
  if (item.badgeKind === 'watch') score += 0.1
  return score
}

function activeItemSeverityScore(item, snapshot) {
  if (snapshot) {
    if (item.id === 'rsv') return severityScoreFromLabel(snapshot.rsv, 'virus')
    if (item.id === 'flu') return severityScoreFromLabel(snapshot.flu, 'virus')
    if (item.id === 'covid') return severityScoreFromLabel(snapshot.covid, 'virus')
  }
  return staticActiveBuzzScore(item)
}

const activeItems = computed(() => {
  void locale.value
  const s = snapshot.value
  const merged = activeItemsBase.map((item) => {
    let row = { ...item }
    if (s) {
      if (item.id === 'rsv') row = { ...row, ...virusActivityFromLevel(s.rsv) }
      if (item.id === 'flu') row = { ...row, ...virusActivityFromLevel(s.flu) }
      if (item.id === 'covid') row = { ...row, ...virusActivityFromLevel(s.covid) }
    }
    return {
      ...row,
      title: t(`home.active.cards.${item.id}.title`),
      symptoms: t(`home.active.cards.${item.id}.symptoms`),
      activity: t(`home.active.activity.${row.activityKey}`),
      badge: t(`home.active.badges.${row.badgeKey}`),
    }
  })
  return sortRowsBySeverity(merged, (row) => activeItemSeverityScore(row, s))
})

const compareRows = computed(() => {
  void locale.value
  return ['runny', 'fever', 'sneeze', 'night', 'energy'].map((key) => ({
    symptom: t(`home.compare.rows.${key}.symptom`),
    tip: t(`home.compare.rows.${key}.tip`),
  }))
})

const parentNotices = computed(() => {
  void locale.value
  return [
    { text: t('home.noticing.n1'), tone: 'mint' },
    { text: t('home.noticing.n2'), tone: 'sun' },
    { text: t('home.noticing.n3'), tone: 'sky' },
    { text: t('home.noticing.n4'), tone: 'lilac' },
  ]
})

const parentQuestions = computed(() => {
  void locale.value
  return [
    { id: 'q1', question: t('home.asking.q1.q'), answer: t('home.asking.q1.a') },
    { id: 'q2', question: t('home.asking.q2.q'), answer: t('home.asking.q2.a') },
    { id: 'q3', question: t('home.asking.q3.q'), answer: t('home.asking.q3.a') },
    { id: 'q4', question: t('home.asking.q4.q'), answer: t('home.asking.q4.a') },
  ]
})

const symptomOptions = computed(() => {
  void locale.value
  return [
    { id: 'cough', label: t('home.symptom.cough.label'), tip: t('home.symptom.cough.tip') },
    { id: 'fever', label: t('home.symptom.fever.label'), tip: t('home.symptom.fever.tip') },
    { id: 'sneeze', label: t('home.symptom.sneeze.label'), tip: t('home.symptom.sneeze.tip') },
    { id: 'stomach', label: t('home.symptom.stomach.label'), tip: t('home.symptom.stomach.tip') },
    { id: 'nose', label: t('home.symptom.nose.label'), tip: t('home.symptom.nose.tip') },
  ]
})

const openQuestionId = ref(null)

function toggleQuestion(id) {
  openQuestionId.value = openQuestionId.value === id ? null : id
}

const selectedSymptoms = ref([])

function toggleSymptom(id) {
  const i = selectedSymptoms.value.indexOf(id)
  if (i === -1) {
    selectedSymptoms.value = [...selectedSymptoms.value, id]
  } else {
    selectedSymptoms.value = selectedSymptoms.value.filter((x) => x !== id)
  }
}

const selectedSymptomTips = computed(() =>
  selectedSymptoms.value
    .map((id) => symptomOptions.value.find((o) => o.id === id))
    .filter(Boolean),
)

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

function onActiveCardClick(item) {
  const k = activeCardToDetailKey(item.id)
  if (k) openTrendDetail(k)
}

function onActiveCardKeydown(e, item) {
  if (!activeCardToDetailKey(item.id)) return
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    onActiveCardClick(item)
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
              <a href="#how-read-snapshot" class="hero__cta hero__cta--secondary">{{ $t('home.hero.btnHowRead') }}</a>
            </div>
            <p class="hero__lang-hint">{{ $t('home.hero.langHint') }}</p>

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
                <p v-else-if="dashboardHeadline" class="hero-preview__headline">{{ dashboardHeadline }}</p>
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
        <a href="#how-read-snapshot" class="value-strip__item">{{ $t('home.valueStrip.howRead') }}</a>
        <a href="#language-intro" class="value-strip__item">{{ $t('home.valueStrip.languages') }}</a>
      </div>
    </section>

    <section id="weekly-snapshot" class="snapshot-dashboard snapshot-dashboard--clean" aria-labelledby="snapshot-section-title">
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
            <div class="snapshot-dash__headline snapshot-dash__headline--skeleton" aria-hidden="true" />
            <ul
              class="snapshot-dash__grid snapshot-dash__grid--virus snapshot-dash__grid--skeleton"
              aria-busy="true"
              :aria-label="$t('home.hero.loadingSnapshot')"
            >
              <li v-for="n in 3" :key="'vsk' + n" class="snapshot-dash__skeleton-card" />
            </ul>
          </template>
          <template v-else>
            <p v-if="dashboardHeadline" class="snapshot-dash__headline">{{ dashboardHeadline }}</p>
            <p v-if="dashboardHeadlineSub" class="snapshot-dash__sub">{{ dashboardHeadlineSub }}</p>

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
                    <span class="snapshot-dash__card-note">{{ row.blurb }}</span>
                  </div>
                </div>
              </li>
            </ul>

            <template v-if="snapshot">
              <p class="snapshot-dash__row-eyebrow">{{ $t('home.hero.dashboardRowEnv') }}</p>
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
                      <span class="snapshot-dash__card-title">{{ row.label }}</span>
                      <span class="snapshot-dash__card-level">{{ row.value }}</span>
                      <span class="snapshot-dash__card-note">{{ row.blurb }}</span>
                    </div>
                  </div>
                </li>
              </ul>
            </template>

            <p v-if="snapshot?.data_quality_note" class="snapshot-dash__dq" role="status">
              {{ snapshot.data_quality_note }}
            </p>

            <div class="snapshot-foot">
              <details class="snapshot-foot__drawer">
                <summary class="snapshot-foot__summary">{{ $t('home.snapshotSection.dataInfoSummary') }}</summary>
                <div class="snapshot-foot__drawer-body">
                  <p class="snapshot-foot__p">
                    {{
                      snapshot ? $t('home.trustPanel.cadenceLive') : $t('home.trustPanel.cadenceFallback')
                    }}
                  </p>
                  <p class="snapshot-foot__p">{{ $t('home.trustPanel.mixedBody') }}</p>
                  <p v-if="!snapshot" class="snapshot-foot__p">{{ $t('home.hero.trustDefault') }}</p>
                  <p v-if="snapshot" class="snapshot-foot__p">{{ $t('home.hero.trustSnapshot') }}</p>
                  <p v-if="snapshotLiveVsIllustrative" class="snapshot-foot__p">{{ snapshotLiveVsIllustrative }}</p>
                  <p class="snapshot-foot__p">{{ $t('home.hero.trustAware') }}</p>
                  <details
                    v-if="snapshot && !snapshotShortSummary && parentWeekSummaryLines.length"
                    class="snapshot-foot__nested"
                  >
                    <summary>{{ $t('home.snapshotSection.moreDetail') }}</summary>
                    <p
                      v-for="(line, idx) in parentWeekSummaryLines"
                      :key="idx"
                      class="snapshot-foot__p"
                    >
                      {{ line }}
                    </p>
                  </details>
                </div>
              </details>

              <nav
                v-if="!snapshotLoading"
                class="snapshot-foot__links"
                :aria-label="$t('home.hero.sourcesFooterLabel')"
              >
                <time v-if="formattedUpdatedAt" class="snapshot-foot__time" :datetime="snapshot.updated_at">{{
                  formattedUpdatedAt
                }}</time>
                <button type="button" class="snapshot-foot__linkish" @click="openTrendDetail('how_it_works')">
                  {{ $t('home.hero.howSources') }}
                </button>
                <template v-for="row in provenanceRows" :key="row.key">
                  <a
                    v-if="row.url"
                    class="snapshot-foot__linkish"
                    :href="row.url"
                    target="_blank"
                    rel="noopener noreferrer"
                  >{{ row.name }}</a>
                  <span v-else class="snapshot-foot__muted">{{ row.name }}</span>
                </template>
              </nav>
            </div>
          </template>
        </div>
      </div>
    </section>

    <section
      id="how-read-snapshot"
      class="home-read-guide"
      aria-labelledby="read-guide-heading"
    >
      <div class="home-read-guide__inner">
        <h2 id="read-guide-heading" class="home-read-guide__title">{{ $t('home.readGuide.title') }}</h2>
        <p class="home-read-guide__deck">{{ $t('home.readGuide.deck') }}</p>
        <ol class="home-read-guide__steps">
          <li>{{ $t('home.readGuide.step1') }}</li>
          <li>{{ $t('home.readGuide.step2') }}</li>
          <li>{{ $t('home.readGuide.step3') }}</li>
        </ol>
        <div class="home-read-guide__actions">
          <a href="#language-intro" class="home-read-guide__link">{{ $t('home.readGuide.linkLanguages') }}</a>
          <span class="home-read-guide__dot" aria-hidden="true">·</span>
          <a href="#littlebug-help" class="home-read-guide__link">{{ $t('home.readGuide.linkHelp') }}</a>
          <span class="home-read-guide__dot" aria-hidden="true">·</span>
          <button type="button" class="home-read-guide__btn" @click="openTrendDetail('how_it_works')">
            {{ $t('home.readGuide.linkData') }}
          </button>
        </div>
      </div>
    </section>

    <MetroMapSection />

    <section
      id="language-intro"
      class="home-language-section section--warm-slab"
      aria-labelledby="language-intro-heading"
    >
      <div class="home-language-section__inner">
        <h2 id="language-intro-heading" class="section__title">{{ $t('home.languageSection.title') }}</h2>
        <p class="section__deck section__deck--tight">{{ $t('home.languageSection.deck') }}</p>
        <p class="home-language-section__value">{{ $t('home.languageSection.valueNote') }}</p>
        <p class="home-language-section__hint">{{ $t('home.languageSection.hint') }}</p>
        <div class="home-language-section__switcher">
          <LanguageSwitcher variant="hero" />
        </div>
      </div>
    </section>

    <section class="section top-concerns section--warm-slab" aria-labelledby="top-concerns-heading">
      <div class="top-concerns__head">
        <h2 id="top-concerns-heading" class="section__title">{{ $t('home.topConcerns.title') }}</h2>
        <p class="section__editorial-kicker">{{ $t('home.topConcerns.editorialKicker') }}</p>
        <p class="section__deck section__deck--tight">
          {{ $t('home.topConcerns.deck') }}
        </p>
      </div>
      <ul class="top-concerns__grid">
        <li
          v-for="c in topConcerns"
          :key="c.id"
          class="top-concern-card"
          :data-tone="c.tone"
        >
          <span class="top-concern-card__spark" aria-hidden="true" />
          <h3 class="top-concern-card__title">{{ c.title }}</h3>
          <p class="top-concern-card__text">{{ c.text }}</p>
        </li>
      </ul>
    </section>

    <section class="section active section--warm-slab" aria-labelledby="active-heading">
      <div class="section__head">
        <h2 id="active-heading" class="section__title">{{ $t('home.active.title') }}</h2>
        <p class="section__editorial-kicker">{{ $t('home.active.editorialKicker') }}</p>
        <p class="section__deck">
          {{ $t('home.active.deck') }}
        </p>
        <p class="section__sort-hint">{{ $t('home.hero.sortHint') }}</p>
        <button type="button" class="section__sources-btn" @click="openTrendDetail('how_it_works')">
          {{ $t('home.hero.howSources') }}
        </button>
      </div>
      <ul class="active-grid">
        <li v-for="(item, index) in activeItems" :key="item.id" class="active-grid__cell">
          <div
            class="active-card"
            :class="{
              'active-card--priority': item.priorityTop,
              'active-card--tilt-a': index % 2 === 0,
              'active-card--tilt-b': index % 2 === 1,
              'active-card--clickable': !!activeCardToDetailKey(item.id),
            }"
            :data-card="item.id"
            :data-kind="item.kind"
            :tabindex="activeCardToDetailKey(item.id) ? 0 : undefined"
            :role="activeCardToDetailKey(item.id) ? 'button' : undefined"
            :aria-label="activeCardToDetailKey(item.id) ? $t('home.common.learnMore', { topic: item.title }) : undefined"
            @click="onActiveCardClick(item)"
            @keydown="onActiveCardKeydown($event, item)"
          >
          <div class="active-card__art">
            <span v-if="item.priorityTop" class="active-card__active-pill">{{ $t('home.common.mostActive') }}</span>
            <div class="active-card__icon-wrap">
              <ActivityCardArt :name="item.id" />
            </div>
            <span
              class="active-card__badge"
              :class="{ 'active-card__badge--soft-pulse': item.priorityTop }"
              :data-kind="item.badgeKind"
            >{{ item.badge }}</span>
          </div>
          <h3 class="active-card__title">{{ item.title }}</h3>
          <p class="active-card__symptoms">{{ item.symptoms }}</p>
          <div class="active-card__foot">
            <span class="active-card__act-label">{{ $t('home.common.neighbourChatter') }}</span>
            <div class="active-card__meter">
              <div class="active-card__dots" :aria-label="$t('home.common.parentBuzz', { level: item.activity })">
                <span
                  v-for="n in 3"
                  :key="n"
                  class="active-card__dot"
                  :class="{ 'active-card__dot--on': n <= item.activityDots }"
                />
              </div>
              <span class="active-card__act">{{ item.activity }}</span>
            </div>
          </div>
          <p
            v-if="activeCardToDetailKey(item.id)"
            class="active-card__tap-hint"
            aria-hidden="true"
          >
            {{ $t('home.common.tapForTips') }}
          </p>
        </div>
        </li>
      </ul>
    </section>

    <section class="section compare section--warm-slab" aria-labelledby="compare-heading">
      <div class="compare__intro">
        <h2 id="compare-heading" class="section__title">{{ $t('home.compare.title') }}</h2>
        <p class="section__deck">
          {{ $t('home.compare.deck') }}
        </p>
      </div>
      <div class="compare__grid">
        <article v-for="row in compareRows" :key="row.symptom" class="compare-card">
          <h3 class="compare-card__symptom">
            <span class="compare-card__dot" aria-hidden="true" />
            {{ row.symptom }}
          </h3>
          <div class="compare-card__body">
            <p>{{ row.tip }}</p>
          </div>
        </article>
      </div>
    </section>

    <section id="parents-pulse" class="section noticing" aria-labelledby="noticing-heading">
      <div class="noticing__shell">
        <div class="noticing__head">
          <h2 id="noticing-heading" class="section__title">{{ $t('home.noticing.title') }}</h2>
          <p class="section__deck section__deck--tight">
            {{ $t('home.noticing.deck') }}
          </p>
        </div>
        <ul class="noticing__bento">
          <li
            v-for="(n, i) in parentNotices"
            :key="i"
            class="noticing-card"
            :data-tone="n.tone"
          >
            <span class="noticing-card__wave" aria-hidden="true">“</span>
            <p class="noticing-card__text">{{ n.text }}</p>
            <span class="noticing-card__tag">{{ $t('home.noticing.tag') }}</span>
          </li>
        </ul>
      </div>
    </section>

    <section class="section asking section--warm-slab" aria-labelledby="asking-heading">
      <div class="asking__head">
        <div class="asking__head-row">
          <LittleBuggyMascot class="asking__head-mascot" pose="think" size="md" />
          <div class="asking__head-text">
            <h2 id="asking-heading" class="section__title">{{ $t('home.asking.title') }}</h2>
            <p class="section__deck section__deck--tight">
              {{ $t('home.asking.deck') }}
            </p>
          </div>
        </div>
      </div>
      <ul class="asking__list">
        <li v-for="q in parentQuestions" :key="q.id" class="asking__item">
          <button
            type="button"
            class="asking-card"
            :class="{ 'asking-card--open': openQuestionId === q.id }"
            :aria-expanded="openQuestionId === q.id"
            :aria-controls="`asking-ans-${q.id}`"
            @click="toggleQuestion(q.id)"
          >
            <span class="asking-card__icon" aria-hidden="true">
              <span class="asking-card__qmark">?</span>
            </span>
            <span class="asking-card__q">{{ q.question }}</span>
            <span class="asking-card__chev" aria-hidden="true" />
          </button>
          <div
            v-show="openQuestionId === q.id"
            :id="`asking-ans-${q.id}`"
            class="asking-card__answer"
            role="region"
          >
            <p>{{ q.answer }}</p>
          </div>
        </li>
      </ul>
    </section>

    <section class="section symptom" aria-labelledby="symptom-heading">
      <div class="symptom__shell">
        <h2 id="symptom-heading" class="section__title">{{ $t('home.symptom.title') }}</h2>
        <p class="section__deck section__deck--tight">
          {{ $t('home.symptom.deck') }}
        </p>
        <div
          class="symptom__chips"
          role="group"
          :aria-label="$t('home.symptom.groupLabel')"
        >
          <button
            v-for="o in symptomOptions"
            :key="o.id"
            type="button"
            class="symptom-chip"
            :class="{ 'symptom-chip--on': selectedSymptoms.includes(o.id) }"
            :aria-pressed="selectedSymptoms.includes(o.id)"
            @click="toggleSymptom(o.id)"
          >
            <span class="symptom-chip__icon" aria-hidden="true">
              <SymptomMiniIcon :id="o.id" />
            </span>
            {{ o.label }}
          </button>
        </div>
        <div v-if="selectedSymptomTips.length" class="symptom__panel">
          <p class="symptom__panel-kicker">{{ $t('home.symptom.panelKicker') }}</p>
          <ul class="symptom__tips">
            <li v-for="row in selectedSymptomTips" :key="row.id">
              <span class="symptom__tips-label">{{ row.label }}</span>
              {{ row.tip }}
            </li>
          </ul>
        </div>
        <p v-else class="symptom__hint">
          {{ $t('home.symptom.hint') }}
        </p>
      </div>
    </section>

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

.home-language-section__inner {
  max-width: min(42rem, 100%);
  margin: 0 auto;
  text-align: center;
}

.home-language-section__value {
  margin: 0 auto 1rem;
  padding: 0;
  max-width: 38rem;
  font-size: 0.98rem;
  line-height: 1.62;
  font-weight: 600;
  color: var(--color-ink-muted);
  background: none;
  border: none;
  box-shadow: none;
}

.home-language-section__hint {
  margin: 0 auto 1.1rem;
  max-width: 34rem;
  font-size: 0.9rem;
  line-height: 1.55;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.home-language-section__switcher {
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

.hero-snapshot-panel__main .hero-summary,
.hero-snapshot-panel__main .hero__trend-meta,
.hero-snapshot-panel__main .hero__live-heading,
.hero-snapshot-panel__main .hero__env-sort-hint,
.hero-snapshot-panel__main .hero__live-meta {
  max-width: none;
  width: 100%;
  margin-left: 0;
  margin-right: 0;
}

.hero-snapshot-panel__main .hero__sort-hint,
.hero-snapshot-panel__main .hero__env-sort-hint {
  text-align: left;
}

.hero-snapshot-panel__main .hero-summary--virus {
  grid-template-columns: 1fr;
}

@media (min-width: 540px) {
  .hero-snapshot-panel__main .hero-summary--virus {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.hero-snapshot-panel__main .hero-summary--env-grid {
  grid-template-columns: 1fr;
}

@media (min-width: 540px) {
  .hero-snapshot-panel__main .hero-summary--env-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.hero__trend-meta--panel {
  margin-top: 0.35rem;
  margin-bottom: 0.45rem;
}

.hero-week-summary {
  margin-top: 1rem;
  padding: 1.05rem 1.15rem 1.1rem;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 2px 16px rgba(15, 23, 42, 0.045);
}

.hero-week-summary__title {
  margin: 0 0 0.7rem;
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.hero-week-summary__short {
  margin: 0 0 0.65rem;
  font-size: 0.96rem;
  font-weight: 600;
  line-height: 1.62;
  color: var(--color-ink);
}

.hero-week-summary__live-note {
  margin: 0 0 0.55rem;
  padding: 0.55rem 0.65rem;
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-ink-muted);
  background: rgba(248, 250, 252, 0.95);
  border-radius: var(--radius-md);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.hero-week-summary__para {
  margin: 0 0 0.55rem;
  font-size: 0.94rem;
  font-weight: 600;
  line-height: 1.62;
  color: var(--color-ink);
}

.hero-week-summary__meta {
  margin: 0.65rem 0 0.4rem;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink-soft);
}

.hero-week-summary__trust {
  margin: 0.45rem 0 0;
  padding-top: 0.55rem;
  border-top: 1px solid rgba(226, 232, 240, 0.85);
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-ink-muted);
}

.hero-snapshot-panel__aside {
  min-width: 0;
}

.trust-stack {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.trust-card {
  padding: 0.85rem 0.95rem;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
}

.trust-card--soft {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(241, 245, 249, 0.75) 100%);
  border-color: rgba(226, 232, 240, 0.9);
}

.trust-card--warm {
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.5) 100%);
  border-color: rgba(253, 186, 116, 0.35);
}

.trust-card--caution {
  background: linear-gradient(135deg, rgba(255, 247, 237, 0.98) 0%, rgba(254, 215, 170, 0.35) 100%);
  border-color: rgba(251, 146, 60, 0.35);
}

.trust-card__h {
  margin: 0 0 0.4rem;
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.trust-card__p {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  line-height: 1.52;
  color: var(--color-ink-muted);
}

.trust-card__p--tight {
  flex: 1;
  min-width: 0;
}

.trust-card__mascot-row {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
}

.trust-sources-block__h {
  margin: 0 0 0.55rem;
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.trust-sources-block__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.trust-source-card {
  padding: 0.75rem 0.8rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset;
}

.trust-source-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.trust-source-card__emoji {
  font-size: 1.1rem;
  line-height: 1;
}

.trust-source-card__pill {
  flex-shrink: 0;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.2rem 0.45rem;
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.85);
  color: var(--color-ink-soft);
}

.trust-source-card__pill[data-status='ok'] {
  background: rgba(167, 243, 208, 0.65);
  color: #065f46;
}

.trust-source-card__pill[data-status='error'],
.trust-source-card__pill[data-status='unavailable'] {
  background: rgba(254, 202, 202, 0.65);
  color: #991b1b;
}

.trust-source-card__kind {
  display: block;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #6d28d9;
  margin-bottom: 0.2rem;
}

.trust-source-card__link,
.trust-source-card__name {
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.4;
  color: var(--color-ink);
}

.trust-source-card__link {
  text-decoration: none;
  border-bottom: 1px solid rgba(124, 58, 237, 0.35);
}

.trust-source-card__link:hover {
  color: #5b21b6;
  border-bottom-color: rgba(91, 33, 182, 0.55);
}

.trust-source-card__refresh {
  margin: 0.4rem 0 0;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-ink-muted);
}

.trust-panel-cta {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.2rem;
  width: 100%;
  margin: 0.15rem 0 0;
  padding: 0.75rem 0.95rem;
  font: inherit;
  cursor: pointer;
  text-align: left;
  border: none;
  border-radius: var(--radius-md);
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 48%, #a855f7 100%);
  box-shadow:
    0 2px 0 rgba(255, 255, 255, 0.22) inset,
    0 8px 22px rgba(99, 102, 241, 0.28);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.trust-panel-cta:hover {
  transform: translateY(-2px);
  box-shadow:
    0 2px 0 rgba(255, 255, 255, 0.25) inset,
    0 12px 28px rgba(99, 102, 241, 0.32);
}

.trust-panel-cta:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 3px;
}

.trust-panel-cta__main {
  font-family: var(--font-display);
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.trust-panel-cta__sub {
  font-size: 0.74rem;
  font-weight: 600;
  opacity: 0.92;
  line-height: 1.35;
}

.trust-panel-mascot {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
  padding: 0.65rem 0.5rem 0.15rem;
}

.trust-panel-mascot__bug {
  flex-shrink: 0;
}

.trust-panel-mascot__text {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-muted);
}

.hero-snapshot-panel__aside--skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.trust-skeleton-card {
  height: 4.25rem;
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, rgba(241, 245, 249, 0.9) 0%, rgba(248, 250, 252, 0.5) 50%, rgba(241, 245, 249, 0.9) 100%);
  background-size: 200% 100%;
  animation: trust-skel 1.2s ease-in-out infinite;
}

@keyframes trust-skel {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .trust-skeleton-card {
    animation: none;
    background: rgba(241, 245, 249, 0.85);
  }
}

.hero-summary {
  list-style: none;
  margin: 0 auto 1.15rem;
  padding: 0;
  display: grid;
  gap: 0.65rem;
  max-width: 26rem;
}

.hero-summary__cell {
  list-style: none;
  margin: 0;
  padding: 0;
}

.hero-summary__card--interactive {
  cursor: pointer;
}

.hero-summary__card--interactive:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 3px;
}

.hero-summary__active-pill {
  position: absolute;
  top: 0.42rem;
  right: 0.5rem;
  z-index: 2;
  padding: 0.2rem 0.5rem;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #5b21b6;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border: 2px solid #fff;
  border-radius: 999px;
  box-shadow: 1px 2px 0 rgba(167, 139, 250, 0.25);
}

.hero-summary__tap-hint {
  margin-top: 0.25rem;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--color-ink-soft);
  opacity: 0.82;
}

@media (min-width: 900px) {
  .hero-summary {
    margin-left: 0;
    margin-right: 0;
  }
}

.hero-summary__card {
  position: relative;
  display: grid;
  gap: 0.2rem;
  padding: 1.05rem 1.15rem 1.05rem 3.2rem;
  text-align: left;
  border-radius: var(--radius-sticker);
  border: 4px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  transition:
    transform 0.28s var(--ease-bounce),
    box-shadow 0.28s var(--ease-soft);
}

.hero-summary__card::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background-image: var(--pattern-dots);
  background-size: var(--pattern-dots-size);
  opacity: 0.4;
  pointer-events: none;
}

.hero-summary__card > * {
  position: relative;
  z-index: 1;
}

.hero-summary__sticker {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  line-height: 1;
  filter: drop-shadow(0 2px 0 rgba(255, 255, 255, 0.9));
}

.hero-summary__card:hover {
  transform: translateY(-4px) rotate(-0.5deg);
  box-shadow: 4px 4px 0 rgba(167, 139, 250, 0.35), 0 16px 40px rgba(74, 63, 60, 0.08);
}

.hero-summary__card[data-tone='hot'] {
  background: linear-gradient(135deg, #fff1f2 0%, #fff 100%);
  border-color: rgba(251, 113, 133, 0.35);
}

.hero-summary__card[data-tone='rise'] {
  background: linear-gradient(135deg, #f5f3ff 0%, #fff 100%);
  border-color: rgba(167, 139, 250, 0.4);
}

.hero-summary__card[data-tone='watch'] {
  background: linear-gradient(135deg, #fffbeb 0%, #fff 100%);
  border-color: rgba(251, 191, 36, 0.45);
}

.hero-summary__card--priority {
  border-width: 4px;
  border-color: #fff;
  box-shadow:
    5px 5px 0 rgba(255, 200, 140, 0.52),
    0 14px 40px rgba(196, 181, 253, 0.16);
  animation: hero-summary-priority-glow 4.5s ease-in-out infinite;
}

@keyframes hero-summary-priority-glow {
  0%,
  100% {
    box-shadow:
      4px 4px 0 rgba(255, 200, 140, 0.42),
      0 10px 28px rgba(167, 139, 250, 0.1);
  }
  50% {
    box-shadow:
      5px 5px 0 rgba(251, 191, 36, 0.55),
      0 16px 42px rgba(125, 211, 252, 0.18);
  }
}

.hero-summary__card--priority:hover {
  animation: none;
}

@media (prefers-reduced-motion: reduce) {
  .hero-summary__card--priority {
    animation: none;
  }
}

.hero-summary__label {
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink-soft);
}

.hero-summary__value {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink);
  line-height: 1.2;
}

.hero-summary__blurb {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.4;
}

.hero-summary--skeleton {
  pointer-events: none;
}

.hero-summary__skeleton-card {
  min-height: 5.6rem;
  border-radius: var(--radius-lg);
  border: 4px solid #fff;
  background: linear-gradient(90deg, #fff8f0 0%, #ffe8f0 45%, #e8f7fc 90%, #fff8f0 100%);
  background-size: 220% 100%;
  animation: hero-shimmer 1.35s ease-in-out infinite;
  list-style: none;
}

@keyframes hero-shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-summary__skeleton-card {
    animation: none;
    background: #fff5eb;
  }
}

.hero__data-scope {
  margin: 0 auto 0.9rem;
  padding: 0.75rem 1rem;
  max-width: 36rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: center;
  text-align: center;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(99, 102, 241, 0.22);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.97) 0%, rgba(238, 242, 255, 0.9) 100%);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.hero__data-scope__title {
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-ink-muted);
}

.hero__data-scope__body {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1.58;
  color: var(--color-ink);
  max-width: 34rem;
}

.hero__data-scope[data-variant='fallback'] {
  border-color: rgba(251, 146, 60, 0.3);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 247, 237, 0.94) 100%);
  box-shadow: 0 2px 8px rgba(124, 45, 18, 0.06);
}

.hero__data-scope[data-variant='fallback'] .hero__data-scope__title {
  color: #b45309;
}

.hero__data-scope[data-variant='fallback'] .hero__data-scope__body {
  color: var(--color-ink);
}

.hero__pipeline-quiet-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin: 0 auto 0.75rem;
  padding: 0.55rem 0.85rem;
  max-width: 32rem;
  font-size: 0.76rem;
  font-weight: 700;
  line-height: 1.45;
  color: #9a3412;
  text-align: left;
  border-radius: var(--radius-md);
  border: 3px solid #fff;
  box-shadow: 3px 3px 0 rgba(253, 186, 116, 0.4);
  background: linear-gradient(120deg, #fff7ed 0%, #fef3c7 100%);
}

.hero__pipeline-quiet-banner__mascot {
  flex-shrink: 0;
}

.hero__pipeline-quiet-banner__text {
  flex: 1;
  min-width: 0;
}

@media (min-width: 900px) {
  .hero__pipeline-quiet-banner {
    margin-left: 0;
    margin-right: 0;
    justify-content: flex-start;
  }
}

@media (min-width: 900px) {
  .hero__data-scope {
    margin-left: 0;
    margin-right: 0;
    align-items: flex-start;
    text-align: left;
  }
}

.hero__live-heading {
  margin: 1.2rem auto 0.6rem;
  font-family: var(--font-display);
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
}

.hero-summary--env {
  margin-bottom: 1rem;
}

.hero__live-meta {
  margin: 0 auto 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink-soft);
  max-width: 32rem;
}

.hero__sort-hint,
.hero__env-sort-hint {
  margin: 0.5rem auto 0;
  max-width: 32rem;
  font-size: 0.78rem;
  font-weight: 600;
  font-style: italic;
  color: var(--color-ink-soft);
  line-height: 1.45;
  text-align: center;
}

.hero__env-sort-hint {
  margin-bottom: 0.65rem;
}

@media (min-width: 900px) {
  .hero__sort-hint,
  .hero__env-sort-hint {
    margin-left: 0;
    text-align: left;
  }
}

.hero__trend-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.55rem;
  margin: 0 auto 0.65rem;
  max-width: 32rem;
}

.hero__trend-meta .hero__sort-hint {
  margin: 0;
  text-align: center;
}

@media (min-width: 900px) {
  .hero__trend-meta {
    margin-left: 0;
    align-items: flex-start;
  }

  .hero__trend-meta .hero__sort-hint {
    text-align: left;
  }
}

.hero__sources-btn,
.section__sources-btn {
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  color: #5b21b6;
  background: rgba(255, 255, 255, 0.78);
  border: 2px dashed rgba(167, 139, 250, 0.55);
  border-radius: var(--radius-pill);
  padding: 0.38rem 0.9rem;
  cursor: pointer;
  box-shadow: 2px 2px 0 rgba(186, 230, 253, 0.5);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.hero__sources-btn:hover,
.section__sources-btn:hover {
  transform: translateY(-2px);
  box-shadow: 3px 3px 0 rgba(253, 186, 116, 0.45);
}

.hero__sources-btn:focus-visible,
.section__sources-btn:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 2px;
}

.section__sources-btn {
  margin-top: 0.25rem;
  align-self: flex-start;
}

@media (min-width: 900px) {
  .hero__live-heading,
  .hero__live-meta {
    margin-left: 0;
    margin-right: 0;
  }
}

.hero__aware {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0 auto 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-ink-soft);
  max-width: 34rem;
  line-height: 1.45;
}

.hero__aware__mascot {
  flex-shrink: 0;
}

.hero__aware__text {
  flex: 1;
  min-width: 12rem;
  max-width: 30rem;
}

@media (min-width: 900px) {
  .hero__aware {
    margin-left: 0;
    margin-right: 0;
    justify-content: flex-start;
  }
}

@media (max-width: 380px) {
  .hero-summary__card {
    padding: 0.85rem 0.9rem 0.85rem 2.65rem;
  }

  .hero-summary__sticker {
    left: 0.55rem;
    font-size: 1.2rem;
    width: 1.75rem;
    height: 1.75rem;
  }
}

/* Top concerns */
.top-concerns__head {
  margin-bottom: 1.25rem;
}

.top-concerns__grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .top-concerns__grid {
    grid-template-columns: repeat(3, 1fr);
    align-items: stretch;
  }
}

.top-concerns__grid > li:nth-child(odd) .top-concern-card {
  transform: rotate(-0.4deg);
}

.top-concerns__grid > li:nth-child(even) .top-concern-card {
  transform: rotate(0.5deg);
}

.top-concern-card {
  position: relative;
  padding: 1.45rem 1.35rem 1.3rem;
  border-radius: var(--radius-sticker);
  border: 4px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  overflow: hidden;
  transition:
    transform 0.28s var(--ease-bounce),
    box-shadow 0.28s var(--ease-soft);
}

.top-concern-card::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background-image: var(--pattern-dots);
  background-size: var(--pattern-dots-size);
  opacity: 0.25;
  pointer-events: none;
}

.top-concern-card__title,
.top-concern-card__text {
  position: relative;
  z-index: 1;
}

.top-concern-card__spark {
  z-index: 2;
}

.top-concerns__grid > li .top-concern-card:hover {
  transform: translateY(-6px) rotate(0deg);
  box-shadow:
    5px 5px 0 rgba(167, 139, 250, 0.22),
    0 16px 36px rgba(74, 63, 60, 0.08);
}

.top-concern-card[data-tone='coral'] {
  background: linear-gradient(155deg, #fff1f2 0%, #ffe4e6 40%, #fff 100%);
}

.top-concern-card[data-tone='lilac'] {
  background: linear-gradient(155deg, #f5f3ff 0%, #ede9fe 42%, #fff 100%);
}

.top-concern-card[data-tone='mint'] {
  background: linear-gradient(155deg, #ecfdf5 0%, #d1fae5 40%, #fff 100%);
}

.top-concern-card__spark {
  position: absolute;
  top: 0.95rem;
  right: 0.95rem;
  width: 14px;
  height: 14px;
  background: linear-gradient(145deg, #fde047, #fb7185);
  clip-path: polygon(50% 0%, 63% 38%, 100% 38%, 69% 59%, 82% 100%, 50% 75%, 18% 100%, 31% 59%, 0% 38%, 37% 38%);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.85);
}

.top-concern-card__title {
  margin: 0 0 0.55rem;
  padding-right: 1.5rem;
  font-family: var(--font-display);
  font-size: 1.08rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  line-height: 1.3;
  color: var(--color-ink);
}

.top-concern-card__text {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

/* —— Sections —— */
.section__head {
  margin-bottom: 1.5rem;
}

.section__title {
  margin: 0 0 0.55rem;
  font-family: var(--font-display);
  font-size: clamp(1.55rem, 3.4vw, 2.05rem);
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--color-ink);
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
}

.section__deck {
  margin: 0;
  max-width: 42rem;
  font-size: 1.05rem;
  line-height: 1.68;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.section__deck--tight {
  margin-bottom: 1.2rem;
}

.section__editorial-kicker {
  margin: 0 0 0.5rem;
  max-width: 42rem;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  line-height: 1.45;
  color: #92400e;
  padding: 0.4rem 0.65rem;
  border-radius: var(--radius-md);
  border-left: 4px solid rgba(251, 191, 36, 0.75);
  background: rgba(255, 251, 235, 0.65);
}

.section__sort-hint {
  margin: 0.4rem 0 0;
  font-size: 0.8rem;
  font-weight: 600;
  font-style: italic;
  color: var(--color-ink-soft);
  line-height: 1.45;
  max-width: 40rem;
}

/* Activity cards */
.active-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 1.15rem;
  grid-template-columns: 1fr;
}

@media (min-width: 560px) {
  .active-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 960px) {
  .active-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.active-grid__cell {
  list-style: none;
  margin: 0;
  padding: 0;
}

.active-card--tilt-a {
  transform: rotate(-0.55deg);
}

.active-card--tilt-b {
  transform: rotate(0.45deg);
}

.active-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  padding: 1.45rem 1.35rem 1.25rem;
  border-radius: var(--radius-sticker);
  border: 4px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  overflow: hidden;
  transition:
    transform 0.3s var(--ease-bounce),
    box-shadow 0.3s var(--ease-soft);
}

.active-card::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background-image: var(--pattern-dots);
  background-size: var(--pattern-dots-size);
  opacity: 0.3;
  pointer-events: none;
}

.active-card::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background: radial-gradient(120% 80% at 10% 0%, rgba(255, 255, 255, 0.5) 0%, transparent 55%);
  pointer-events: none;
}

.active-card__art,
.active-card__title,
.active-card__symptoms,
.active-card__foot,
.active-card__tap-hint {
  position: relative;
  z-index: 1;
}

.active-card[data-card='rsv'] {
  background: linear-gradient(155deg, #ecfdf5 0%, #d1fae5 45%, #fff 100%);
}

.active-card[data-card='flu'] {
  background: linear-gradient(155deg, #fff1f2 0%, #ffe4e6 40%, #fff 100%);
}

.active-card[data-card='covid'] {
  background: linear-gradient(155deg, #faf5ff 0%, #ede9fe 42%, #fff 100%);
}

.active-card[data-card='cold'] {
  background: linear-gradient(155deg, #f0f9ff 0%, #e0f2fe 42%, #fff 100%);
}

.active-card[data-card='stomach'] {
  background: linear-gradient(155deg, #fefce8 0%, #fef9c3 40%, #fff 100%);
}

.active-grid .active-card--clickable:hover {
  transform: translateY(-8px) rotate(0deg) scale(1.01);
  box-shadow:
    5px 5px 0 rgba(251, 191, 36, 0.28),
    0 18px 40px rgba(167, 139, 250, 0.12);
}

.active-card--priority {
  border-color: #fff;
  box-shadow:
    6px 6px 0 rgba(253, 186, 116, 0.48),
    0 14px 42px rgba(196, 181, 253, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  animation: active-card-breathe 5s ease-in-out infinite;
}

@keyframes active-card-breathe {
  0%,
  100% {
    box-shadow:
      6px 6px 0 rgba(253, 186, 116, 0.42),
      0 12px 36px rgba(196, 181, 253, 0.14);
  }
  50% {
    box-shadow:
      6px 6px 0 rgba(251, 191, 36, 0.52),
      0 18px 48px rgba(125, 211, 252, 0.18);
  }
}

.active-card--priority.active-card--tilt-a {
  animation: active-card-breathe-tilt-a 5s ease-in-out infinite;
}

@keyframes active-card-breathe-tilt-a {
  0%,
  100% {
    transform: rotate(-0.55deg);
    box-shadow:
      6px 6px 0 rgba(253, 186, 116, 0.42),
      0 12px 36px rgba(196, 181, 253, 0.14);
  }
  50% {
    transform: rotate(-0.45deg) translateY(-1px);
    box-shadow:
      6px 6px 0 rgba(251, 191, 36, 0.52),
      0 18px 48px rgba(125, 211, 252, 0.18);
  }
}

.active-card--priority.active-card--tilt-b {
  animation: active-card-breathe-tilt-b 5s ease-in-out infinite;
}

@keyframes active-card-breathe-tilt-b {
  0%,
  100% {
    transform: rotate(0.45deg);
    box-shadow:
      6px 6px 0 rgba(253, 186, 116, 0.42),
      0 12px 36px rgba(196, 181, 253, 0.14);
  }
  50% {
    transform: rotate(0.38deg) translateY(-1px);
    box-shadow:
      6px 6px 0 rgba(251, 191, 36, 0.52),
      0 18px 48px rgba(125, 211, 252, 0.18);
  }
}

.active-grid .active-card--priority.active-card--clickable:hover {
  animation: none;
  transform: translateY(-8px) rotate(0deg) scale(1.02);
}

.active-card__badge--soft-pulse {
  animation: badge-soft-pulse 3.8s ease-in-out infinite;
}

@keyframes badge-soft-pulse {
  0%,
  100% {
    filter: brightness(1);
    box-shadow: 2px 2px 0 rgba(255, 255, 255, 0.65);
  }
  50% {
    filter: brightness(1.04);
    box-shadow:
      2px 3px 0 rgba(253, 186, 116, 0.4),
      0 0 12px rgba(253, 186, 116, 0.15);
  }
}

@media (prefers-reduced-motion: reduce) {
  .active-card--priority {
    animation: none;
  }

  .active-card--priority.active-card--tilt-a,
  .active-card--priority.active-card--tilt-b {
    animation: none;
  }

  .active-card__badge--soft-pulse {
    animation: none;
  }
}

.active-card--clickable {
  cursor: pointer;
}

.active-card--clickable:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 3px;
}

.active-card__active-pill {
  position: absolute;
  top: -0.12rem;
  left: 0;
  z-index: 2;
  padding: 0.18rem 0.48rem;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #7c2d12;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border: 2px solid #fff;
  border-radius: 999px;
  box-shadow: 1px 2px 0 rgba(251, 191, 36, 0.35);
}

.active-card__tap-hint {
  position: relative;
  z-index: 1;
  margin: -0.15rem 0 0;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--color-ink-soft);
  opacity: 0.82;
  text-align: center;
}

.active-card__art {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
  position: relative;
  z-index: 1;
}

.active-card__icon-wrap {
  width: 4.75rem;
  height: 4.75rem;
  flex-shrink: 0;
  border-radius: 26px;
  background-color: rgba(255, 255, 255, 0.92);
  background-image: radial-gradient(circle at 2px 2px, rgba(255, 200, 140, 0.35) 1.5px, transparent 0);
  background-size: 10px 10px;
  border: 3px solid #fff;
  box-shadow: 3px 3px 0 rgba(186, 230, 253, 0.55);
  padding: 0.4rem;
}

.active-card__badge {
  align-self: flex-start;
  padding: 0.35rem 0.72rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  border-radius: var(--radius-pill);
  border: 2px solid #fff;
  box-shadow: 2px 2px 0 rgba(255, 255, 255, 0.6);
}

.active-card__badge[data-kind='hot'] {
  background: linear-gradient(135deg, #fecaca, #fda4af);
  color: #7f1d1d;
  border-color: rgba(248, 113, 113, 0.35);
}

.active-card__badge[data-kind='rise'] {
  background: linear-gradient(135deg, #fde68a, #fcd34d);
  color: #78350f;
  border-color: rgba(245, 158, 11, 0.35);
}

.active-card__badge[data-kind='watch'] {
  background: linear-gradient(135deg, #bae6fd, #7dd3fc);
  color: #0c4a6e;
  border-color: rgba(14, 165, 233, 0.3);
}

.active-card__badge[data-kind='season'] {
  background: linear-gradient(135deg, #d8b4fe, #c4b5fd);
  color: #4c1d95;
  border-color: rgba(139, 92, 246, 0.3);
}

.active-card__title {
  margin: 0;
  position: relative;
  z-index: 1;
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: var(--color-ink);
}

.active-card__symptoms {
  margin: 0;
  flex: 1;
  position: relative;
  z-index: 1;
  font-size: 0.92rem;
  line-height: 1.55;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.active-card__foot {
  position: relative;
  z-index: 1;
  padding-top: 0.65rem;
  margin-top: 0.2rem;
  border-top: 2px dashed rgba(255, 255, 255, 0.65);
}

.active-card__act-label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink-soft);
}

.active-card__meter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.active-card__dots {
  display: flex;
  gap: 6px;
}

.active-card__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.75);
  border: 2px solid rgba(251, 182, 206, 0.5);
}

.active-card__dot--on {
  background: linear-gradient(145deg, #f9a8d4, #fbbf24);
  border-color: rgba(251, 113, 133, 0.4);
  box-shadow: 0 0 0 3px rgba(253, 186, 116, 0.35);
}

.active-card__act {
  font-size: 0.88rem;
  font-weight: 700;
  color: #be185d;
}

/* Compare */
.compare__intro {
  margin-bottom: 1.35rem;
}

.compare__grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.compare-card {
  padding: 1.35rem 1.4rem;
  border-radius: var(--radius-sticker);
  background-color: rgba(255, 252, 247, 0.96);
  background-image: var(--pattern-dots-soft), var(--pattern-dots);
  background-size: var(--pattern-dots-size-lg), var(--pattern-dots-size);
  border: 4px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  outline: 2px dashed rgba(253, 186, 116, 0.45);
  outline-offset: -6px;
}

.compare-card__symptom {
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-family: var(--font-display);
  font-size: 1.08rem;
  font-weight: 700;
  color: var(--color-ink);
}

.compare-card__dot {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  background: linear-gradient(145deg, #fde047, #fb923c);
  clip-path: polygon(
    50% 0%,
    61% 35%,
    98% 35%,
    68% 57%,
    79% 91%,
    50% 70%,
    21% 91%,
    32% 57%,
    2% 35%,
    39% 35%
  );
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.compare-card__body {
  margin: 0;
  padding: 0.85rem 0.95rem;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  line-height: 1.55;
  font-weight: 600;
  color: var(--color-ink-muted);
  background: linear-gradient(135deg, rgba(254, 226, 226, 0.5) 0%, rgba(255, 255, 255, 0.95) 100%);
  border: 2px solid rgba(251, 113, 133, 0.2);
}

.compare-card__body p {
  margin: 0;
}

/* What parents are noticing */
.noticing__shell {
  padding: clamp(1.35rem, 4vw, 2rem);
  border-radius: var(--radius-xl);
  background-image: var(--pattern-dots-soft), var(--pattern-dots),
    linear-gradient(
      145deg,
      rgba(255, 255, 255, 0.96) 0%,
      rgba(255, 244, 230, 0.42) 35%,
      rgba(224, 242, 254, 0.42) 70%,
      rgba(252, 231, 243, 0.38) 100%
    );
  background-size: var(--pattern-dots-size-lg), var(--pattern-dots-size), auto;
  border: 4px dashed rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-sticker-playful);
}

.noticing__head {
  margin-bottom: 1.35rem;
}

.noticing__bento {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.9rem;
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .noticing__bento {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: auto auto;
  }

  .noticing-card:nth-child(1) {
    grid-column: span 2;
  }
}

@media (min-width: 900px) {
  .noticing__bento {
    grid-template-columns: 1.1fr 0.9fr;
    grid-template-rows: auto auto;
  }

  .noticing-card:nth-child(1) {
    grid-column: 1;
    grid-row: span 2;
  }

  .noticing-card:nth-child(2),
  .noticing-card:nth-child(3),
  .noticing-card:nth-child(4) {
    grid-column: 2;
  }
}

.noticing-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.2rem 1.25rem 1.1rem;
  border-radius: var(--radius-lg);
  border: 3px solid #fff;
  box-shadow: var(--shadow-sticker);
  overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.noticing__bento > li:nth-child(odd) .noticing-card {
  transform: rotate(-0.35deg);
}

.noticing__bento > li:nth-child(even) .noticing-card {
  transform: rotate(0.4deg);
}

.noticing__bento > li .noticing-card:hover {
  transform: translateY(-4px) rotate(0deg);
}

.noticing-card[data-tone='mint'] {
  background: linear-gradient(155deg, #ecfdf5 0%, #d1fae5 50%, #fff 100%);
}

.noticing-card[data-tone='sun'] {
  background: linear-gradient(155deg, #fffbeb 0%, #fef3c7 45%, #fff 100%);
}

.noticing-card[data-tone='sky'] {
  background: linear-gradient(155deg, #f0f9ff 0%, #e0f2fe 45%, #fff 100%);
}

.noticing-card[data-tone='lilac'] {
  background: linear-gradient(155deg, #f5f3ff 0%, #ede9fe 45%, #fff 100%);
}

.noticing-card__wave {
  font-family: Georgia, serif;
  font-size: 2.5rem;
  line-height: 0.5;
  color: rgba(15, 37, 40, 0.12);
  font-weight: 700;
}

.noticing-card__text {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.45;
  color: var(--color-ink);
}

.noticing-card__tag {
  align-self: flex-start;
  margin-top: 0.25rem;
  padding: 0.32rem 0.72rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #9d174d;
  background: rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-pill);
  border: 2px solid rgba(251, 182, 206, 0.45);
  box-shadow: 2px 2px 0 rgba(253, 186, 116, 0.25);
}

/* Parents are asking */
.asking__head {
  margin-bottom: 1.25rem;
}

.asking__head-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.asking__head-mascot {
  flex-shrink: 0;
  padding: 0.25rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.75);
  border: 3px solid #fff;
  box-shadow: 3px 3px 0 rgba(196, 181, 253, 0.35);
}

.asking__head-text {
  flex: 1;
  min-width: 0;
}

@media (max-width: 520px) {
  .asking__head-row {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .asking__head-text .section__title,
  .asking__head-text .section__deck {
    text-align: center;
  }
}

.asking__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.asking-card {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.15rem;
  text-align: left;
  font: inherit;
  cursor: pointer;
  border-radius: var(--radius-lg);
  border: 3px solid #fff;
  background-image: var(--pattern-dots-soft),
    linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(252, 231, 243, 0.5) 55%, rgba(224, 242, 254, 0.35) 100%);
  background-size: var(--pattern-dots-size-lg), auto;
  box-shadow: var(--shadow-sticker-playful);
  transition:
    transform 0.22s var(--ease-soft),
    box-shadow 0.22s ease,
    border-color 0.2s ease;
}

.asking-card:hover {
  transform: translateY(-3px);
  box-shadow:
    4px 4px 0 rgba(251, 191, 36, 0.28),
    0 14px 32px rgba(167, 139, 250, 0.12);
}

.asking-card--open {
  border-color: rgba(196, 181, 253, 0.85);
  background: linear-gradient(135deg, #fff 0%, #faf5ff 100%);
}

.asking-card__icon {
  flex-shrink: 0;
  width: 2.35rem;
  height: 2.35rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  background: linear-gradient(145deg, #fde68a 0%, #f9a8d4 45%, #a78bfa 100%);
  border-radius: 16px;
  border: 3px solid #fff;
  box-shadow: 3px 3px 0 rgba(251, 191, 36, 0.4);
}

.asking-card__qmark {
  font-size: 1.15rem;
  font-weight: 800;
  color: #fff;
  line-height: 1;
  text-shadow: 0 1px 0 rgba(91, 33, 182, 0.25);
}

.asking-card__q {
  flex: 1;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-ink);
  line-height: 1.35;
}

.asking-card__chev {
  flex-shrink: 0;
  width: 0.55rem;
  height: 0.55rem;
  border-right: 3px solid var(--color-ink-soft);
  border-bottom: 3px solid var(--color-ink-soft);
  transform: rotate(45deg) translateY(-2px);
  transition: transform 0.25s ease;
}

.asking-card--open .asking-card__chev {
  transform: rotate(225deg) translateY(2px);
}

.asking-card__answer {
  margin-top: 0.5rem;
  padding: 0 0.25rem 0.25rem 3.1rem;
}

.asking-card__answer p {
  margin: 0;
  padding: 0.95rem 1.05rem;
  font-size: 0.93rem;
  font-weight: 600;
  line-height: 1.65;
  color: var(--color-ink-muted);
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.95) 0%, rgba(254, 249, 231, 0.65) 100%);
  border-radius: var(--radius-md);
  border: 3px solid rgba(255, 255, 255, 0.95);
  box-shadow:
    3px 3px 0 rgba(186, 230, 253, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

@media (max-width: 520px) {
  .asking-card__answer {
    padding-left: 0;
  }
}

/* Quick symptom check */
.symptom__shell {
  padding: clamp(1.35rem, 4vw, 2rem);
  border-radius: var(--radius-xl);
  background-color: rgba(255, 255, 255, 0.5);
  background-image: var(--pattern-dots-soft),
    linear-gradient(
      155deg,
      rgba(255, 255, 255, 0.96) 0%,
      rgba(254, 243, 199, 0.4) 45%,
      rgba(224, 242, 254, 0.45) 100%
    );
  background-size: var(--pattern-dots-size-lg), auto;
  border: 4px dashed rgba(253, 186, 116, 0.48);
  box-shadow: var(--shadow-sticker-playful);
}

.symptom__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 1.15rem;
}

.symptom-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 0.95rem;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-ink);
  cursor: pointer;
  border-radius: var(--radius-pill);
  border: 3px solid #fff;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 3px 3px 0 rgba(251, 182, 206, 0.32), 0 1px 0 rgba(255, 255, 255, 0.9) inset;
  transition:
    transform 0.22s var(--ease-bounce),
    box-shadow 0.22s ease,
    background 0.2s ease;
}

.symptom-chip:hover {
  transform: translateY(-2px);
}

.symptom-chip--on {
  background: linear-gradient(135deg, #f9a8d4, #c4b5fd);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.75);
  box-shadow: 3px 3px 0 rgba(251, 191, 36, 0.35);
}

.symptom-chip__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.65);
  border: 2px solid rgba(255, 255, 255, 0.9);
  color: var(--color-ink-muted);
  box-shadow: 1px 2px 0 rgba(253, 186, 116, 0.25);
}

.symptom-chip--on .symptom-chip__icon {
  background: rgba(255, 255, 255, 0.95);
  color: #7c3aed;
  border-color: rgba(255, 255, 255, 1);
}

.symptom__panel {
  padding: 1rem 1.15rem;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.88);
  border: 2px dashed rgba(45, 212, 191, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.symptom__panel-kicker {
  margin: 0 0 0.65rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #9d174d;
}

.symptom__tips {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.symptom__tips li {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.symptom__tips-label {
  display: block;
  margin-bottom: 0.2rem;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink);
}

.symptom__hint {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-soft);
  font-style: italic;
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
