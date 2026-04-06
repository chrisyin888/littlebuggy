<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ActivityCardArt from '../components/ActivityCardArt.vue'
import TrendDetailModal from '../components/TrendDetailModal.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import LittleBuggyMascot from '../components/LittleBuggyMascot.vue'
import SymptomMiniIcon from '../components/SymptomMiniIcon.vue'
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

const cityBubblesBase = [
  { id: 'van', issueTKey: 'issueRsv', level: 'High', x: 20, y: 38, delay: 0, hot: true, tone: 'rose' },
  { id: 'burn', issueTKey: 'issueAir', level: 'Watch', x: 44, y: 44, delay: 0.35, hot: false, tone: 'lilac' },
  { id: 'coq', issueTKey: 'issueCough', level: 'Watch', x: 78, y: 24, delay: 1.4, hot: false, tone: 'mint' },
  { id: 'rich', issueTKey: 'issueCold', level: 'Moderate', x: 22, y: 74, delay: 0.7, hot: false, tone: 'sky' },
  { id: 'surr', issueTKey: 'issueFlu', level: 'Moderate', x: 76, y: 72, delay: 1.05, hot: false, tone: 'amber' },
]

function levelLooksHigh(level) {
  return /high|very/i.test(String(level || ''))
}

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

function virusBlurb(name, level) {
  const L = String(level || '').toLowerCase()
  const branch = /high|very/i.test(L) ? 'high' : /low/i.test(L) ? 'low' : 'mid'
  if (name === 'RSV') return t(`home.hero.blurbs.rsv.${branch}`)
  if (name === 'Flu') return t(`home.hero.blurbs.flu.${branch}`)
  return t(`home.hero.blurbs.covid.${branch}`)
}

const liveHeroCards = computed(() => {
  void locale.value
  const s = snapshot.value
  if (!s) return null
  return [
    {
      kind: 'rsv',
      label: 'RSV',
      value: translateApiLevel(s.rsv, t),
      blurb: virusBlurb('RSV', s.rsv),
      tone: levelToTone(s.rsv),
      sticker: '🐞',
    },
    {
      kind: 'flu',
      label: 'Flu',
      value: translateApiLevel(s.flu, t),
      blurb: virusBlurb('Flu', s.flu),
      tone: levelToTone(s.flu),
      sticker: '🤒',
    },
    {
      kind: 'covid',
      label: 'COVID',
      value: translateApiLevel(s.covid, t),
      blurb: virusBlurb('COVID', s.covid),
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

const regionEyebrow = computed(() => {
  void locale.value
  const r = snapshot.value?.region?.trim()
  return r ? `${r} · ${t('home.pulseSuffix')}` : t('home.pulseDefault')
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

const cityBubbles = computed(() => {
  void locale.value
  const s = snapshot.value
  return cityBubblesBase.map((b) => {
    let row = {
      ...b,
      name: t(`home.cities.${b.id}`),
      issue: t(`home.cities.${b.issueTKey}`),
      level: translateApiLevel(b.level, t),
    }
    if (s && b.id === 'van') {
      row = {
        ...row,
        level: translateApiLevel(s.rsv, t),
        hot: levelLooksHigh(s.rsv),
      }
    }
    return row
  })
})

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
    <div class="home__sparkles" aria-hidden="true">
      <span v-for="n in 14" :key="n" class="home__sparkle" :class="`home__sparkle--${n}`" />
    </div>
    <div class="home__clouds" aria-hidden="true">
      <span class="home__cloud home__cloud--1" />
      <span class="home__cloud home__cloud--2" />
    </div>
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero__blobs" aria-hidden="true">
        <span class="hero__blob hero__blob--a" />
        <span class="hero__blob hero__blob--b" />
        <span class="hero__blob hero__blob--c" />
        <span class="hero__blob hero__blob--d" />
      </div>
      <div class="hero__micro" aria-hidden="true">
        <span v-for="n in 12" :key="'d' + n" class="hero__dot" :class="`hero__dot--${n}`" />
      </div>
      <div class="hero__wave" aria-hidden="true" />
      <div class="hero__grid hero__grid--intro">
        <div class="hero__copy hero__copy--intro">
          <LanguageSwitcher variant="hero" />
          <div class="hero__intro-shell">
            <div class="hero__intro">
              <div class="hero__intro-mascot">
                <LittleBuggyMascot pose="wave" size="lg" />
              </div>
              <div class="hero__intro-text">
                <p class="hero__eyebrow">{{ regionEyebrow }}</p>
                <h1 id="hero-title" class="hero__title">{{ $t('home.hero.title') }}</h1>
                <p class="hero__subtitle">
                  {{ $t('home.hero.subtitle') }}
                </p>
                <p class="hero__value-line">{{ $t('home.hero.valueLine') }}</p>
                <div class="hero__actions">
                  <a href="#littlebug-map" class="hero__btn hero__btn--primary">{{ $t('home.hero.btnMap') }}</a>
                  <a href="#weekly-snapshot" class="hero__btn hero__btn--secondary">{{
                    $t('home.snapshotSection.cta')
                  }}</a>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="snapshotError && !snapshot && !snapshotLoading"
            class="hero__live-banner"
            role="status"
          >
            <LittleBuggyMascot class="hero__live-banner__mascot" pose="cozy" size="sm" />
            <span class="hero__live-banner__text">
              {{ $t('home.hero.errorBanner') }}
            </span>
          </div>

          <div
            v-if="snapshotError && snapshot && !snapshotLoading"
            class="hero__stale-banner"
            role="status"
            aria-live="polite"
          >
            <LittleBuggyMascot class="hero__stale-banner__mascot" pose="cozy" size="sm" />
            <div class="hero__stale-banner__body">
              <p class="hero__stale-banner__main">{{ $t('home.hero.staleDataBanner') }}</p>
              <p
                v-if="staleErrorShort"
                class="hero__stale-banner__detail"
                :title="snapshotError || undefined"
              >
                {{ staleErrorShort }}
              </p>
            </div>
          </div>
        </div>

        <div id="littlebug-map" class="hero__visual hero__visual--intro">
          <div
            class="metro-radar metro-radar--playful"
            role="img"
            :aria-label="$t('home.hero.mapAria')"
          >
            <div class="metro-radar__head">
              <div class="metro-radar__head-main">
                <div class="metro-radar__live-row">
                  <span class="metro-radar__live">{{ $t('home.hero.mapNeighbourhood') }}</span>
                  <span class="metro-radar__illus-pill">{{ $t('home.hero.mapIllustrativePill') }}</span>
                </div>
                <span class="metro-radar__sub">{{ $t('home.hero.mapSub') }}</span>
              </div>
              <div class="metro-radar__legend" aria-hidden="true">
                <span class="metro-radar__pill metro-radar__pill--rsv">{{ $t('home.map.pillRsv') }}</span>
                <span class="metro-radar__pill metro-radar__pill--air">{{ $t('home.map.pillAir') }}</span>
                <span class="metro-radar__pill metro-radar__pill--cough">{{ $t('home.map.pillCough') }}</span>
              </div>
            </div>
            <div class="metro-radar__plate">
              <div class="metro-radar__float-tags" aria-hidden="true">
                <span class="metro-float-tag metro-float-tag--1">✦ sticker map</span>
                <span class="metro-float-tag metro-float-tag--2">soft signals</span>
                <span class="metro-float-tag metro-float-tag--3">local vibe</span>
              </div>
              <div class="metro-radar__pulses" aria-hidden="true">
                <span class="metro-radar__pulse" />
                <span class="metro-radar__pulse metro-radar__pulse--2" />
                <span class="metro-radar__pulse metro-radar__pulse--3" />
              </div>
              <svg
                class="metro-radar__svg"
                viewBox="0 0 320 280"
                xmlns="http://www.w3.org/2000/svg"
                preserveAspectRatio="xMidYMid meet"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient id="mvOcean" x1="0%" y1="0%" x2="60%" y2="80%">
                    <stop offset="0%" stop-color="#c8ecff" />
                    <stop offset="50%" stop-color="#a5d8ff" />
                    <stop offset="100%" stop-color="#e0f7fa" stop-opacity="0.95" />
                  </linearGradient>
                  <linearGradient id="mvRiver" x1="0%" y1="50%" x2="100%" y2="50%">
                    <stop offset="0%" stop-color="#bfdbfe" stop-opacity="0.65" />
                    <stop offset="50%" stop-color="#f0f9ff" stop-opacity="0.98" />
                    <stop offset="100%" stop-color="#93c5fd" stop-opacity="0.5" />
                  </linearGradient>
                  <linearGradient id="mvSun" x1="50%" y1="0%" x2="50%" y2="100%">
                    <stop offset="0%" stop-color="#fff59a" />
                    <stop offset="100%" stop-color="#fcd34d" stop-opacity="0.55" />
                  </linearGradient>
                </defs>
                <g opacity="0.55" aria-hidden="true">
                  <path
                    d="M 24 32 Q 38 22 52 28 Q 62 18 78 26 Q 88 20 98 30 Q 92 42 76 40 Q 58 44 42 38 Q 28 40 24 32 Z"
                    fill="#fff"
                  />
                  <path
                    d="M 248 48 Q 262 38 278 44 Q 288 36 298 48 Q 292 58 272 56 Q 252 60 248 48 Z"
                    fill="#fff"
                  />
                </g>
                <!-- Ocean / Strait (Georgia + Burrard feel) -->
                <rect width="320" height="280" fill="url(#mvOcean)" />
                <path
                  d="M0 0 L320 0 L320 95 Q 240 88 180 100 Q 120 108 70 95 Q 30 85 0 100 Z"
                  fill="#a5d8ff"
                  opacity="0.28"
                />
                <circle cx="275" cy="38" r="22" fill="url(#mvSun)" opacity="0.75" />
                <!-- North Shore (across inlet) -->
                <path
                  d="M 48 38 Q 95 28 138 36 Q 158 48 148 72 Q 125 82 88 78 Q 52 68 42 52 Q 38 44 48 38 Z"
                  fill="#a7f3d0"
                  stroke="#fff"
                  stroke-width="2.5"
                  stroke-linejoin="round"
                  opacity="0.95"
                />
                <!-- Coquitlam / northeast upland -->
                <path
                  d="M 152 58 L 248 48 Q 268 58 275 88 Q 278 118 258 138 L 188 145 Q 158 128 148 98 Q 145 72 152 58 Z"
                  fill="#86efac"
                  stroke="#fff"
                  stroke-width="2"
                  stroke-linejoin="round"
                  opacity="0.9"
                />
                <!-- Burnaby (plateau between Van & Coq) -->
                <path
                  d="M 108 95 L 158 88 Q 172 98 178 125 Q 180 152 165 168 L 118 172 Q 95 158 92 128 Q 94 105 108 95 Z"
                  fill="#bbf7d0"
                  stroke="#fff"
                  stroke-width="2"
                  stroke-linejoin="round"
                  opacity="0.92"
                />
                <!-- Vancouver peninsula + core (coast on west) -->
                <path
                  d="M 38 118 Q 28 95 48 82 Q 72 72 92 88 Q 108 102 104 128 Q 100 158 78 172 Q 52 178 38 158 Q 28 138 38 118 Z"
                  fill="#d1fae5"
                  stroke="#fff"
                  stroke-width="2.2"
                  stroke-linejoin="round"
                  opacity="0.95"
                />
                <!-- Coastline shimmer -->
                <path
                  d="M 38 118 Q 32 100 42 88 Q 55 78 72 82"
                  fill="none"
                  stroke="#fff"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  opacity="0.65"
                />
                <!-- Surrey (south of river, east) -->
                <path
                  d="M 132 178 L 278 168 Q 302 185 308 218 Q 312 252 288 268 L 148 274 Q 118 255 112 218 Q 115 190 132 178 Z"
                  fill="#a7f3d0"
                  stroke="#fff"
                  stroke-width="2"
                  stroke-linejoin="round"
                  opacity="0.88"
                />
                <!-- Richmond / Lulu island (delta, west of Surrey) -->
                <path
                  d="M 22 188 L 118 178 Q 132 192 128 228 Q 124 258 98 268 L 32 272 Q 12 248 14 212 Q 16 198 22 188 Z"
                  fill="#fef08a"
                  stroke="#fff"
                  stroke-width="2"
                  stroke-linejoin="round"
                  opacity="0.88"
                />
                <!-- Fraser River / delta water (separates Richmond from Surrey) -->
                <path
                  d="M 108 182 Q 118 205 112 232 Q 108 252 125 265 Q 132 248 138 220 Q 142 198 128 185 Q 120 178 108 182 Z"
                  fill="url(#mvRiver)"
                  stroke="#7dd3fc"
                  stroke-width="1.2"
                  stroke-linejoin="round"
                  opacity="0.88"
                />
                <path
                  d="M 115 195 Q 125 215 118 238"
                  fill="none"
                  stroke="#fff"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  opacity="0.5"
                />
                <text
                  x="114"
                  y="232"
                  fill="#0369a1"
                  opacity="0.42"
                  font-size="6.5"
                  font-weight="800"
                  font-family="system-ui, sans-serif"
                  transform="rotate(-12 114 232)"
                >
                  Fraser
                </text>
                <text
                  x="78"
                  y="56"
                  fill="#0f766e"
                  opacity="0.38"
                  font-size="7"
                  font-weight="800"
                  font-family="system-ui, sans-serif"
                >
                  N. Van
                </text>
              </svg>
              <div
                v-for="c in cityBubbles"
                :key="c.id"
                class="city-bubble"
                :class="{ 'city-bubble--hot': c.hot }"
                :style="{
                  left: c.x + '%',
                  top: c.y + '%',
                  animationDelay: c.delay + 's',
                }"
              >
                <span v-if="c.hot" class="city-bubble__glow" aria-hidden="true" />
                <div class="city-bubble__card">
                  <span class="city-bubble__name">{{ c.name }}</span>
                  <div class="city-bubble__signal">
                    <span class="city-bubble__issue">{{ c.issue }}</span>
                    <span class="city-bubble__level" :data-tone="c.tone">{{ c.level }}</span>
                  </div>
                </div>
              </div>
              <div class="map-sticker map-sticker--1" aria-hidden="true">
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M16 4l3.5 8.2L28 16l-8.5 3.8L16 28l-3.5-8.2L4 16l8.5-3.8L16 4z"
                    fill="#fef08a"
                    stroke="#f59e0b"
                    stroke-width="1.2"
                  />
                </svg>
              </div>
              <div class="map-sticker map-sticker--2" aria-hidden="true">
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M16 26c-6 0-10-4.5-10-9 0-5 4-9 10-9s10 4 10 9c0 4.5-4 9-10 9z"
                    fill="#fecdd3"
                    stroke="#fb7185"
                    stroke-width="1.2"
                  />
                </svg>
              </div>
              <div class="map-sticker map-sticker--3" aria-hidden="true">
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M8 20c4-8 12-8 16 0-4 4-12 4-16 0z"
                    fill="#bbf7d0"
                    stroke="#34d399"
                    stroke-width="1.2"
                  />
                </svg>
              </div>
            </div>
            <p class="metro-radar__foot">
              {{ $t('home.hero.mapFoot') }}
            </p>
            <p class="metro-radar__foot-note">
              {{ $t('home.hero.mapLiveDataHint') }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section id="weekly-snapshot" class="snapshot-dashboard" aria-labelledby="snapshot-section-title">
      <div class="snapshot-dashboard__inner">
        <header class="snapshot-dashboard__header">
          <h2 id="snapshot-section-title" class="snapshot-dashboard__title">
            {{ $t('home.snapshotSection.title') }}
          </h2>
          <p class="snapshot-dashboard__subtitle">{{ $t('home.snapshotSection.deck') }}</p>
        </header>

        <div v-if="!snapshotLoading" class="snapshot-dashboard__toolbar">
          <div class="snapshot-context" role="note" :data-variant="snapshot ? 'live' : 'fallback'">
            <span class="snapshot-context__label">{{
              snapshot ? $t('home.hero.heroCardsLiveTitle') : $t('home.hero.heroCardsFallbackTitle')
            }}</span>
            <span class="snapshot-context__text">{{
              snapshot ? $t('home.hero.heroCardsLiveBody') : $t('home.hero.heroCardsFallbackBody')
            }}</span>
          </div>
          <div
            v-if="snapshotLooksOutdated && snapshot"
            class="snapshot-dashboard__stale-flag"
            role="status"
          >
            <LittleBuggyMascot class="snapshot-dashboard__stale-flag-mascot" pose="think" size="xs" />
            <span>{{ $t('home.hero.pipelineQuietBanner') }}</span>
          </div>
        </div>

        <div class="snapshot-dashboard__board">
          <div
            class="hero-snapshot-panel hero-snapshot-panel--dashboard hero-snapshot-panel--wide"
            :data-live="snapshot ? 'yes' : 'no'"
            :class="{ 'hero-snapshot-panel--loading': snapshotLoading }"
          >
            <div class="hero-snapshot-panel__main hero-snapshot-panel__main--dashboard">
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

                <div class="snapshot-dash__fineprint">
                  <details
                    v-if="snapshot && !snapshotShortSummary && parentWeekSummaryLines.length"
                    class="snapshot-dash__details"
                  >
                    <summary>{{ $t('home.snapshotSection.moreDetail') }}</summary>
                    <p
                      v-for="(line, idx) in parentWeekSummaryLines"
                      :key="idx"
                      class="snapshot-dash__details-p"
                    >
                      {{ line }}
                    </p>
                  </details>
                  <p v-if="snapshotLiveVsIllustrative" class="snapshot-dash__fineprint-line">
                    {{ snapshotLiveVsIllustrative }}
                  </p>
                  <p v-if="snapshot" class="snapshot-dash__fineprint-line snapshot-dash__fineprint-line--muted">
                    {{ $t('home.hero.trustSnapshot') }}
                  </p>
                </div>

                <p v-if="snapshot?.data_quality_note" class="snapshot-dash__dq" role="status">
                  {{ snapshot.data_quality_note }}
                </p>
              </template>
            </div>

            <footer
              v-if="!snapshotLoading && snapshot && provenanceRows.length"
              class="hero-snapshot-panel__sources-footer"
            >
              <div class="snapshot-sources-foot">
                <p v-if="formattedUpdatedAt" class="snapshot-sources-foot__updated">
                  <time :datetime="snapshot.updated_at">{{ formattedUpdatedAt }}</time>
                </p>
                <p class="snapshot-sources-foot__label">{{ $t('home.hero.sourcesFooterLabel') }}</p>
                <ul class="snapshot-sources-foot__list" role="list">
                  <li
                    v-for="row in provenanceRows"
                    :key="row.key"
                    class="snapshot-sources-foot__item"
                  >
                    <a
                      v-if="row.url"
                      class="snapshot-sources-foot__link"
                      :href="row.url"
                      target="_blank"
                      rel="noopener noreferrer"
                    >{{ row.name }}</a>
                    <span v-else class="snapshot-sources-foot__name">{{ row.name }}</span>
                  </li>
                </ul>
              </div>
            </footer>

            <aside
              v-if="!snapshotLoading"
              class="snapshot-dashboard__trust"
              :aria-label="$t('home.trustPanel.asideLabel')"
            >
              <div class="snapshot-dashboard__trust-grid">
                <div class="trust-card trust-card--soft trust-card--compact">
                  <h4 class="trust-card__h">{{ $t('home.trustPanel.cadenceTitle') }}</h4>
                  <p class="trust-card__p">
                    {{
                      snapshot ? $t('home.trustPanel.cadenceLive') : $t('home.trustPanel.cadenceFallback')
                    }}
                  </p>
                </div>
                <div class="trust-card trust-card--soft trust-card--compact">
                  <h4 class="trust-card__h">{{ $t('home.trustPanel.mixedTitle') }}</h4>
                  <p class="trust-card__p">{{ $t('home.trustPanel.mixedBody') }}</p>
                </div>
                <div v-if="!snapshot" class="trust-card trust-card--warm trust-card--compact">
                  <div class="trust-card__mascot-row">
                    <LittleBuggyMascot pose="peek" size="sm" />
                    <p class="trust-card__p trust-card__p--tight">{{ $t('home.hero.trustDefault') }}</p>
                  </div>
                </div>
              </div>
              <button type="button" class="trust-panel-cta trust-panel-cta--inline" @click="openTrendDetail('how_it_works')">
                <span class="trust-panel-cta__main">{{ $t('home.hero.howSources') }}</span>
                <span class="trust-panel-cta__sub">{{ $t('home.provenance.fullStory') }}</span>
              </button>
              <p class="snapshot-dashboard__trust-hint">{{ $t('home.trustPanel.mascotHint') }}</p>
            </aside>

            <aside
              v-if="snapshotLoading"
              class="snapshot-dashboard__trust snapshot-dashboard__trust--skeleton"
              aria-hidden="true"
            >
              <div v-for="n in 3" :key="'sk-aside' + n" class="trust-skeleton-card" />
            </aside>
          </div>

          <div v-if="!snapshotLoading" class="snapshot-dashboard__nextbox">
            <h3 class="snapshot-dashboard__nextbox-title">{{ $t('home.snapshotSection.nextTitle') }}</h3>
            <p class="snapshot-dashboard__nextbox-intro">{{ $t('home.snapshotSection.nextIntro') }}</p>
            <ol class="snapshot-dashboard__nextbox-list">
              <li>{{ $t('home.snapshotSection.next1') }}</li>
              <li>{{ $t('home.snapshotSection.next2') }}</li>
              <li>{{ $t('home.snapshotSection.next3') }}</li>
            </ol>
          </div>

          <div class="snapshot-dashboard__aware">
            <p class="hero__aware hero__aware--snapshot-foot">
              <LittleBuggyMascot class="hero__aware__mascot" pose="calm" size="sm" />
              <span class="hero__aware__text">{{ $t('home.hero.trustAware') }}</span>
            </p>
          </div>
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

    <section class="section seek section--warm-slab" aria-labelledby="seek-heading">
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
  gap: clamp(2.75rem, 7vw, 4.75rem);
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
  padding: clamp(2rem, 5vw, 3.5rem) clamp(1rem, 4vw, 2rem);
  background: linear-gradient(180deg, #e8eef5 0%, #f1f5f9 38%, #f8fafc 100%);
  border-top: 1px solid rgba(203, 213, 225, 0.65);
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

.hero__live-banner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin: 0 auto 1rem;
  padding: 0.75rem 1rem 0.75rem 0.85rem;
  max-width: 32rem;
  font-size: 0.84rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-muted);
  background: rgba(255, 252, 247, 0.96);
  border-radius: var(--radius-lg);
  border: 3px dashed rgba(253, 186, 116, 0.55);
  box-shadow: var(--shadow-sticker);
}

.hero__live-banner__mascot {
  flex-shrink: 0;
}

.hero__live-banner__text {
  flex: 1;
  min-width: 0;
}

.hero__stale-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  margin: 0 auto 1rem;
  padding: 0.75rem 1rem 0.85rem 0.85rem;
  max-width: 32rem;
  font-size: 0.84rem;
  line-height: 1.45;
  color: #7c2d12;
  background-image: var(--pattern-dots-soft),
    linear-gradient(135deg, #fffbeb 0%, #ffe4e6 48%, #ffedd5 100%);
  background-size: var(--pattern-dots-size), auto;
  border-radius: var(--radius-lg);
  border: 3px solid rgba(251, 191, 36, 0.5);
  box-shadow: var(--shadow-sticker);
}

.hero__stale-banner__mascot {
  flex-shrink: 0;
  margin-top: 0.05rem;
}

.hero__stale-banner__body {
  flex: 1;
  min-width: 0;
}

.hero__stale-banner__main {
  margin: 0 0 0.35rem;
  font-weight: 700;
  color: var(--color-ink);
}

.hero__stale-banner__detail {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 600;
  font-family: ui-monospace, monospace;
  color: var(--color-ink-muted);
  word-break: break-word;
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

  .hero__stale-banner {
    margin-left: 0;
    margin-right: 0;
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
  .hero__live-meta,
  .hero__live-banner {
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

/* Metro city radar */
.hero__visual {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  width: 100%;
}

.hero__visual--intro {
  align-items: center;
}

@media (min-width: 900px) {
  .hero__visual--intro {
    align-items: stretch;
  }
}

.metro-radar {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
}

.hero__visual--intro .metro-radar {
  max-width: min(100%, 540px);
}

@media (min-width: 900px) {
  .hero__visual--intro .metro-radar {
    max-width: none;
    width: 100%;
  }
}

.metro-radar--playful {
  filter: drop-shadow(0 12px 0 rgba(255, 200, 140, 0.2));
}

.metro-radar--playful .metro-radar__plate {
  animation: metro-plate-breathe 7s ease-in-out infinite;
}

@keyframes metro-plate-breathe {
  0%,
  100% {
    box-shadow: var(--shadow-sticker-deep);
  }
  50% {
    box-shadow:
      6px 6px 0 rgba(251, 191, 36, 0.32),
      0 4px 0 rgba(255, 255, 255, 0.85) inset,
      0 20px 44px rgba(125, 211, 252, 0.14);
  }
}

@media (prefers-reduced-motion: reduce) {
  .metro-radar--playful .metro-radar__plate {
    animation: none;
  }
}

.metro-radar__head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.65rem;
  margin-bottom: 0.85rem;
  padding: 0 0.2rem;
}

.metro-radar__head-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.85rem;
  width: 100%;
  justify-content: space-between;
}

.metro-radar__live-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem 0.55rem;
}

.metro-radar__illus-pill {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  color: #78350f;
  background: rgba(255, 251, 235, 0.95);
  border: 2px dashed rgba(245, 158, 11, 0.55);
}

.metro-radar__live {
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 0.45rem 1rem;
  border-radius: var(--radius-pill);
  color: #c2410c;
  background: linear-gradient(135deg, #fff 0%, #ffedd5 100%);
  border: 3px solid rgba(253, 186, 116, 0.65);
  box-shadow: 3px 3px 0 rgba(125, 211, 252, 0.45);
}

.metro-radar__sub {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-ink-soft);
  max-width: 12rem;
  line-height: 1.35;
  text-align: right;
}

@media (max-width: 420px) {
  .metro-radar__sub {
    text-align: left;
    max-width: none;
  }
}

.metro-radar__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.metro-radar__pill {
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 0.28rem 0.55rem;
  border-radius: 10px;
  border: 2px solid #fff;
  box-shadow: 2px 2px 0 rgba(61, 53, 64, 0.08);
}

.metro-radar__pill--rsv {
  background: linear-gradient(135deg, #fecdd3, #fda4af);
  color: #9f1239;
}

.metro-radar__pill--air {
  background: linear-gradient(135deg, #bae6fd, #7dd3fc);
  color: #0c4a6e;
}

.metro-radar__pill--cough {
  background: linear-gradient(135deg, #a7f3d0, #6ee7b7);
  color: #065f46;
}

.metro-radar__plate {
  position: relative;
  width: 100%;
  min-height: min(52vw, 300px);
  max-height: 320px;
  border-radius: var(--radius-map);
  overflow: visible;
  background:
    var(--pattern-dots),
    linear-gradient(168deg, #fff9e6 0%, #d4efff 38%, #e6faf3 72%, #ffe8f0 100%);
  background-size: var(--pattern-dots-size), auto;
  border: 5px solid #fff;
  box-shadow: var(--shadow-sticker-deep);
}

.metro-radar__float-tags {
  position: absolute;
  inset: 0;
  z-index: 4;
  pointer-events: none;
}

.metro-float-tag {
  position: absolute;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.3rem 0.5rem;
  border-radius: 12px;
  border: 2px solid #fff;
  box-shadow: 3px 3px 0 rgba(253, 186, 116, 0.45);
  background: linear-gradient(135deg, #fff 0%, #fef3c7 100%);
  color: #92400e;
  white-space: nowrap;
  animation: tag-float 5s ease-in-out infinite;
}

.metro-float-tag--1 {
  top: 6%;
  left: 4%;
  animation-delay: 0s;
}

.metro-float-tag--2 {
  top: 10%;
  right: 6%;
  background: linear-gradient(135deg, #fff 0%, #e0f2fe 100%);
  color: #0369a1;
  animation-delay: -1.5s;
}

.metro-float-tag--3 {
  bottom: 14%;
  left: 8%;
  background: linear-gradient(135deg, #fff 0%, #f5f3ff 100%);
  color: #6d28d9;
  animation-delay: -3s;
  font-size: 0.52rem;
}

.metro-radar--playful .metro-float-tag {
  box-shadow: 3px 3px 0 rgba(251, 182, 206, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}

@keyframes tag-float {
  0%,
  100% {
    transform: translateY(0) rotate(-1deg);
  }
  50% {
    transform: translateY(-4px) rotate(1deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .metro-float-tag {
    animation: none;
  }
}

.metro-radar__pulses {
  position: absolute;
  left: 38%;
  top: 44%;
  width: 1px;
  height: 1px;
  z-index: 0;
  pointer-events: none;
}

.metro-radar__pulse {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 100px;
  height: 100px;
  margin: -50px 0 0 -50px;
  border-radius: 50%;
  border: 2.5px solid rgba(125, 211, 252, 0.5);
  animation: metro-ripple 4.5s ease-out infinite;
}

.metro-radar__pulse--2 {
  animation-delay: 1.4s;
}

.metro-radar__pulse--3 {
  animation-delay: 2.8s;
}

@keyframes metro-ripple {
  0% {
    transform: scale(0.55);
    opacity: 0.55;
  }
  100% {
    transform: scale(2.6);
    opacity: 0;
  }
}

.metro-radar__svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  border-radius: calc(var(--radius-map) - 6px);
  pointer-events: none;
  display: block;
}

.city-bubble {
  position: absolute;
  z-index: 2;
  transform: translate(-50%, -50%);
  animation: city-float 5.5s ease-in-out infinite;
}

@keyframes city-float {
  0%,
  100% {
    transform: translate(-50%, -50%) translateY(0);
  }
  50% {
    transform: translate(-50%, -50%) translateY(-6px);
  }
}

.city-bubble--hot .city-bubble__card {
  box-shadow:
    3px 3px 0 rgba(251, 113, 133, 0.3),
    0 0 0 2px rgba(253, 186, 116, 0.45),
    0 8px 22px rgba(74, 63, 60, 0.08);
}

.city-bubble__glow {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 72px;
  height: 72px;
  margin: -36px 0 0 -36px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(251, 113, 133, 0.45) 0%, transparent 70%);
  animation: hotspot-glow 3s ease-in-out infinite;
  z-index: -1;
}

@keyframes hotspot-glow {
  0%,
  100% {
    opacity: 0.65;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.12);
  }
}

.city-bubble__card {
  position: relative;
  padding: 0.55rem 0.75rem 0.6rem;
  min-width: 6.25rem;
  max-width: 8.5rem;
  border-radius: 26px;
  background:
    var(--pattern-dots),
    rgba(255, 252, 247, 0.98);
  background-size: var(--pattern-dots-size), auto;
  border: 3px solid #fff;
  box-shadow: var(--shadow-sticker-deep);
  backdrop-filter: blur(8px);
  transform: rotate(-1deg);
}

.city-bubble__card::before {
  content: '';
  position: absolute;
  top: -5px;
  right: 10px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fda4af, #fcd34d);
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px rgba(255, 200, 140, 0.35);
}

.city-bubble:nth-child(even) .city-bubble__card {
  transform: rotate(1.2deg);
}

.city-bubble__name {
  display: block;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--color-ink);
  line-height: 1.2;
}

.city-bubble__signal {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.2rem 0.35rem;
  margin-top: 0.2rem;
}

.city-bubble__issue {
  font-size: 0.68rem;
  font-weight: 800;
  color: var(--color-ink-muted);
  line-height: 1.2;
}

.city-bubble__level {
  font-size: 0.68rem;
  font-weight: 800;
  line-height: 1.2;
  padding: 0.08rem 0.35rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.75);
}

.city-bubble__level[data-tone='rose'] {
  color: #9f1239;
  background: rgba(254, 205, 211, 0.55);
}

.city-bubble__level[data-tone='lilac'] {
  color: #5b21b6;
  background: rgba(221, 214, 254, 0.65);
}

.city-bubble__level[data-tone='sky'] {
  color: #075985;
  background: rgba(186, 230, 253, 0.65);
}

.city-bubble__level[data-tone='amber'] {
  color: #92400e;
  background: rgba(254, 243, 199, 0.85);
}

.city-bubble__level[data-tone='mint'] {
  color: #065f46;
  background: rgba(167, 243, 208, 0.65);
}

.map-sticker {
  position: absolute;
  z-index: 3;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: rgba(255, 252, 247, 0.96);
  border: 3px solid #fff;
  box-shadow: 3px 3px 0 rgba(186, 230, 253, 0.75);
  animation: map-sticker-float 4.5s ease-in-out infinite;
}

.map-sticker svg {
  width: 22px;
  height: 22px;
}

.map-sticker--1 {
  left: 6%;
  top: 18%;
  animation-delay: 0s;
}

.map-sticker--2 {
  right: 8%;
  bottom: 28%;
  animation-delay: 0.8s;
}

.map-sticker--3 {
  right: 12%;
  top: 12%;
  animation-delay: 1.5s;
}

@keyframes map-sticker-float {
  0%,
  100% {
    transform: translateY(0) rotate(-4deg);
  }
  50% {
    transform: translateY(-5px) rotate(3deg);
  }
}

.metro-radar__foot {
  margin: 0.85rem 0 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-ink-soft);
  text-align: center;
  line-height: 1.5;
  padding: 0 0.35rem;
}

.metro-radar__foot-note {
  margin: 0.55rem 0 0;
  font-size: 0.72rem;
  font-weight: 700;
  font-style: italic;
  color: #92400e;
  text-align: center;
  line-height: 1.5;
  padding: 0 0.35rem;
}

@media (max-width: 520px) {
  .city-bubble__card {
    min-width: 5.75rem;
    max-width: 7.25rem;
    padding: 0.42rem 0.55rem 0.48rem;
  }

  .city-bubble__name {
    font-size: 0.7rem;
  }

  .city-bubble__issue,
  .city-bubble__level {
    font-size: 0.62rem;
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
