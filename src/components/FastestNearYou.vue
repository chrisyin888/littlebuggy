<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  useErWaitTimes,
  waitMinutesFromText,
  hasPublishedWait,
} from '../composables/useErWaitTimes.js'

const { t } = useI18n()
const { payload } = useErWaitTimes()

// Privacy: the visitor's location is used ONLY in this browser tab to rank the
// facilities below. It is never sent to our server, never stored, and never
// included in analytics. The city fallback uses a fixed city-centre point.

// Rough drive model (labelled as an estimate in the UI): straight-line distance
// × 1.3 road detour factor ÷ ~35 km/h average urban speed.
const ROAD_FACTOR = 1.3
const AVG_SPEED_KMH = 35

// Fallback origins: approximate city centres for the manual picker.
const CITY_CENTRES = [
  { id: 'vancouver', label: 'Vancouver', lat: 49.2827, lng: -123.1207 },
  { id: 'richmond', label: 'Richmond', lat: 49.1666, lng: -123.1336 },
  { id: 'burnaby', label: 'Burnaby', lat: 49.2488, lng: -122.9805 },
  { id: 'surrey', label: 'Surrey', lat: 49.1913, lng: -122.849 },
  { id: 'delta', label: 'Delta', lat: 49.09, lng: -123.06 },
  { id: 'coquitlam', label: 'Coquitlam', lat: 49.2838, lng: -122.7932 },
  { id: 'langley', label: 'Langley', lat: 49.1044, lng: -122.6604 },
  { id: 'north_vancouver', label: 'North Vancouver', lat: 49.32, lng: -123.0724 },
]

/** @type {import('vue').Ref<{lat:number,lng:number,kind:'geo'|'city',cityLabel?:string}|null>} */
const origin = ref(null)
const locating = ref(false)
const locationNote = ref('')
const pickedCity = ref('')

function haversineKm(aLat, aLng, bLat, bLng) {
  const R = 6371
  const dLat = ((bLat - aLat) * Math.PI) / 180
  const dLng = ((bLng - aLng) * Math.PI) / 180
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((aLat * Math.PI) / 180) * Math.cos((bLat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(s))
}

const facilitiesWithWaits = computed(() => {
  const rows = []
  const push = (r, kind) => {
    const waitMin = waitMinutesFromText(r?.wait_text)
    if (waitMin === null) return
    if (typeof r?.lat !== 'number' || typeof r?.lng !== 'number') return
    rows.push({ ...r, kind, waitMin })
  }
  for (const h of payload.value?.hospitals ?? []) push(h, 'er')
  // UPCC rows join the same ranking automatically whenever the source posts waits for them.
  for (const c of payload.value?.upcc_centres ?? []) push(c, 'upcc')
  return rows
})

const ranked = computed(() => {
  if (!origin.value) return []
  const o = origin.value
  return facilitiesWithWaits.value
    .map((f) => {
      const roadKm = haversineKm(o.lat, o.lng, f.lat, f.lng) * ROAD_FACTOR
      const driveMin = Math.round((roadKm / AVG_SPEED_KMH) * 60)
      return { ...f, roadKm, driveMin, totalMin: driveMin + f.waitMin }
    })
    .sort((a, b) => a.totalMin - b.totalMin)
    .slice(0, 3)
})

// Facilities the source lists but is not publishing a wait for right now.
// They can't join the total-time ranking, so once an origin is chosen they
// are shown separately, nearest first — a parent may still prefer the
// closest door and call ahead.
const facilitiesWithoutWaits = computed(() => {
  const rows = []
  const push = (r, kind) => {
    if (hasPublishedWait(r)) return
    if (typeof r?.lat !== 'number' || typeof r?.lng !== 'number') return
    rows.push({ ...r, kind })
  }
  for (const h of payload.value?.hospitals ?? []) push(h, 'er')
  for (const c of payload.value?.upcc_centres ?? []) push(c, 'upcc')
  return rows
})

const closestUnpublished = computed(() => {
  if (!origin.value) return []
  const o = origin.value
  return facilitiesWithoutWaits.value
    .map((f) => {
      const roadKm = haversineKm(o.lat, o.lng, f.lat, f.lng) * ROAD_FACTOR
      const driveMin = Math.round((roadKm / AVG_SPEED_KMH) * 60)
      return { ...f, roadKm, driveMin }
    })
    .sort((a, b) => a.driveMin - b.driveMin)
    .slice(0, 3)
})

const hasRankable = computed(() => facilitiesWithWaits.value.length > 0)
const hasClosest = computed(() => facilitiesWithoutWaits.value.length > 0)

function formatDuration(totalMin) {
  const m = Math.max(0, Math.round(totalMin))
  const h = Math.floor(m / 60)
  const r = m % 60
  return h > 0 ? `${h}h ${String(r).padStart(2, '0')}m` : `${r}m`
}

function useMyLocation() {
  locationNote.value = ''
  if (!('geolocation' in navigator)) {
    locationNote.value = t('waitTimes.fastest.locationUnavailable')
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      locating.value = false
      // Used locally only — see privacy note at the top of this file.
      origin.value = { lat: pos.coords.latitude, lng: pos.coords.longitude, kind: 'geo' }
    },
    () => {
      locating.value = false
      locationNote.value = t('waitTimes.fastest.locationUnavailable')
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 },
  )
}

function onPickCity() {
  const c = CITY_CENTRES.find((x) => x.id === pickedCity.value)
  if (!c) return
  locationNote.value = ''
  origin.value = { lat: c.lat, lng: c.lng, kind: 'city', cityLabel: c.label }
}

function resetOrigin() {
  origin.value = null
  pickedCity.value = ''
}
</script>

<template>
  <div v-if="hasRankable || hasClosest" class="fastest">
    <div class="fastest__head">
      <h3 class="fastest__title">⚡ {{ t('waitTimes.fastest.title') }}</h3>
      <p class="fastest__lead">{{ t('waitTimes.fastest.lead') }}</p>
    </div>

    <template v-if="!origin">
      <div class="fastest__controls">
        <button type="button" class="fastest__btn" :disabled="locating" @click="useMyLocation">
          {{ locating ? t('waitTimes.fastest.locating') : `📍 ${t('waitTimes.fastest.useLocation')}` }}
        </button>
        <label class="fastest__picker">
          <span class="fastest__picker-label">{{ t('waitTimes.fastest.orPickCity') }}</span>
          <select v-model="pickedCity" class="fastest__select" @change="onPickCity">
            <option value="" disabled>{{ t('waitTimes.fastest.pickCityPlaceholder') }}</option>
            <option v-for="c in CITY_CENTRES" :key="c.id" :value="c.id">{{ c.label }}</option>
          </select>
        </label>
      </div>
      <p v-if="locationNote" class="fastest__note" role="status">{{ locationNote }}</p>
    </template>

    <template v-else>
      <p class="fastest__from">
        {{
          origin.kind === 'geo'
            ? t('waitTimes.fastest.fromYou')
            : t('waitTimes.fastest.fromCity', { city: origin.cityLabel })
        }}
        <button type="button" class="fastest__change" @click="resetOrigin">
          {{ t('waitTimes.fastest.change') }}
        </button>
      </p>

      <ol v-if="ranked.length" class="fastest__list">
        <li
          v-for="(f, i) in ranked"
          :key="f.key"
          class="fastest__card"
          :class="{ 'fastest__card--best': i === 0 }"
        >
          <div class="fastest__card-top">
            <span class="fastest__name">{{ f.name }}</span>
            <span v-if="i === 0" class="fastest__badge">{{ t('waitTimes.fastest.badge') }}</span>
          </div>
          <p class="fastest__meta">{{ f.city }}<span v-if="f.kind === 'upcc'"> · UPCC</span></p>
          <p class="fastest__numbers">
            <span>{{ t('waitTimes.fastest.driveApprox', { km: f.roadKm.toFixed(1), time: formatDuration(f.driveMin) }) }}</span>
            <span aria-hidden="true"> + </span>
            <span>{{ t('waitTimes.fastest.waitApprox', { time: f.wait_text }) }}</span>
          </p>
          <p class="fastest__total">
            {{ t('waitTimes.fastest.totalApprox', { time: formatDuration(f.totalMin) }) }}
          </p>
        </li>
      </ol>

      <div v-if="closestUnpublished.length" class="fastest__closest">
        <h4 class="fastest__closest-title">{{ t('waitTimes.fastest.closestHeading') }}</h4>
        <ol class="fastest__list">
          <li
            v-for="f in closestUnpublished"
            :key="`closest-${f.key}`"
            class="fastest__card"
          >
            <div class="fastest__card-top">
              <span class="fastest__name">{{ f.name }}</span>
            </div>
            <p class="fastest__meta">{{ f.city }}<span v-if="f.kind === 'upcc'"> · UPCC</span></p>
            <p class="fastest__numbers">
              <span>{{ t('waitTimes.fastest.driveApprox', { km: f.roadKm.toFixed(1), time: formatDuration(f.driveMin) }) }}</span>
            </p>
            <p class="fastest__closest-note">{{ t('waitTimes.fastest.waitNotPublished') }}</p>
          </li>
        </ol>
      </div>

      <p class="fastest__estimate-note">{{ t('waitTimes.fastest.estimateNote') }}</p>
    </template>
  </div>
</template>

<style scoped>
.fastest {
  margin: 0 0 1.35rem;
  padding: 1.05rem 1.15rem 1.15rem;
  border-radius: var(--radius-md);
  background: linear-gradient(140deg, rgba(237, 233, 254, 0.85), rgba(224, 242, 254, 0.7));
  border: 2px solid rgba(167, 139, 250, 0.5);
  box-shadow: var(--shadow-soft);
}

.fastest__title {
  margin: 0 0 0.3rem;
  font-family: var(--font-display);
  font-size: 1.12rem;
  font-weight: 700;
  color: var(--color-ink);
}

.fastest__lead {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
  max-width: 38rem;
}

.fastest__controls {
  margin-top: 0.85rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1.1rem;
}

.fastest__btn {
  font: inherit;
  font-size: 0.92rem;
  font-weight: 800;
  padding: 0.55rem 1.1rem;
  border-radius: var(--radius-pill);
  border: 2px solid #7c3aed;
  background: #7c3aed;
  color: #fff;
  cursor: pointer;
  box-shadow: 2px 2px 0 rgba(124, 58, 237, 0.3);
}

.fastest__btn:hover:not(:disabled) {
  background: #6d28d9;
}

.fastest__btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.fastest__picker {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.fastest__select {
  font: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.45rem 0.6rem;
  border-radius: var(--radius-sm);
  border: 2px solid rgba(167, 139, 250, 0.6);
  background: #fff;
  color: var(--color-ink);
}

.fastest__note {
  margin: 0.7rem 0 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #9a3412;
}

.fastest__from {
  margin: 0.8rem 0 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--color-ink-soft);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.fastest__change {
  font: inherit;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  padding: 0.28rem 0.65rem;
  border-radius: var(--radius-pill);
  border: 2px solid rgba(167, 139, 250, 0.65);
  background: rgba(255, 255, 255, 0.95);
  color: #5b21b6;
  cursor: pointer;
}

.fastest__list {
  list-style: none;
  margin: 0.85rem 0 0;
  padding: 0;
  display: grid;
  gap: 0.7rem;
  grid-template-columns: 1fr;
}

@media (min-width: 720px) {
  .fastest__list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.fastest__card {
  padding: 0.85rem 0.95rem;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 2px solid rgba(186, 230, 253, 0.55);
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
}

.fastest__card--best {
  border-color: rgba(34, 197, 94, 0.65);
  box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.35), var(--shadow-soft);
}

.fastest__card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.fastest__name {
  font-family: var(--font-display);
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-ink);
}

.fastest__badge {
  flex-shrink: 0;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.26rem 0.48rem;
  border-radius: var(--radius-pill);
  background: rgba(74, 222, 128, 0.25);
  border: 2px solid rgba(34, 197, 94, 0.5);
  color: #166534;
}

.fastest__meta {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.fastest__numbers {
  margin: 0.15rem 0 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.45;
}

.fastest__total {
  margin: 0.25rem 0 0;
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-teal-dark);
}

.fastest__closest {
  margin-top: 1rem;
}

.fastest__closest-title {
  margin: 0 0 0.55rem;
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-ink);
}

.fastest__closest-note {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-ink-soft);
}

.fastest__estimate-note {
  margin: 0.8rem 0 0;
  font-size: 0.76rem;
  line-height: 1.45;
  color: var(--color-ink-soft);
}
</style>
