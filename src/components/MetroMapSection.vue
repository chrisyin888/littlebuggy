<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import metroMapIllustration from '../assets/metro-vancouver-map.png'

/**
 * English-only names for map UI (matches illustration labels; not translated on overlay).
 */
const CITY_NAMES_EN = {
  vancouver: 'Vancouver',
  burnaby: 'Burnaby',
  richmond: 'Richmond',
  surrey: 'Surrey',
}

/**
 * Key cities — % of map stage (responsive). Tweak x/y if art shifts.
 */
const HOTSPOTS = [
  { id: 'vancouver', x: '30%', y: '56%', delay: '0s' },
  { id: 'burnaby', x: '46%', y: '46%', delay: '0.15s' },
  { id: 'richmond', x: '24%', y: '74%', delay: '0.3s' },
  { id: 'surrey', x: '71%', y: '71%', delay: '0.45s' },
]

const { t } = useI18n()

const openId = ref(null)
/** Desktop / fine pointer: open card on hover; touch-first: tap only. */
const canHoverOpen = ref(false)

let mqHover = null
let mqFine = null

function updateCanHoverOpen() {
  if (typeof window === 'undefined') return
  canHoverOpen.value =
    window.matchMedia('(hover: hover)').matches && window.matchMedia('(pointer: fine)').matches
}

function onHotspotEnter(id) {
  if (!canHoverOpen.value) return
  openId.value = id
}

function onHotspotLeave(e) {
  if (!canHoverOpen.value) return
  const to = e.relatedTarget
  if (to && typeof to.closest === 'function' && to.closest('.metro-hotspot')) return
  openId.value = null
}

function onHotspotClick(id) {
  if (canHoverOpen.value) return
  openId.value = openId.value === id ? null : id
}

function onHotspotFocusIn(id) {
  openId.value = id
}

function onHotspotFocusOut(e) {
  const li = e.currentTarget
  requestAnimationFrame(() => {
    if (!li.contains(document.activeElement)) openId.value = null
  })
}

function onDocumentPointerDown(e) {
  const el = e.target
  if (typeof el.closest === 'function' && el.closest('.metro-hotspot')) return
  openId.value = null
}

onMounted(() => {
  updateCanHoverOpen()
  mqHover = window.matchMedia('(hover: hover)')
  mqFine = window.matchMedia('(pointer: fine)')
  mqHover.addEventListener('change', updateCanHoverOpen)
  mqFine.addEventListener('change', updateCanHoverOpen)
  document.addEventListener('pointerdown', onDocumentPointerDown, true)
})

onBeforeUnmount(() => {
  if (mqHover) mqHover.removeEventListener('change', updateCanHoverOpen)
  if (mqFine) mqFine.removeEventListener('change', updateCanHoverOpen)
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
})
</script>

<template>
  <section id="metro-vancouver-map" class="metro-map-feature" aria-labelledby="metro-map-heading">
    <div class="metro-map-feature__inner">
      <header class="metro-map-feature__head">
        <p class="metro-map-feature__eyebrow">{{ $t('home.metroMap.eyebrow') }}</p>
        <h2 id="metro-map-heading" class="metro-map-feature__title">{{ $t('home.metroMap.title') }}</h2>
        <p class="metro-map-feature__lede">{{ $t('home.metroMap.lede') }}</p>
      </header>

      <figure class="metro-map-feature__figure">
        <div class="metro-map-feature__card">
          <p class="metro-map-feature__hotspot-hint">{{ $t('home.metroMap.hotspot.hint') }}</p>
          <div class="metro-map-feature__stage">
            <img
              class="metro-map-feature__img"
              :src="metroMapIllustration"
              :alt="$t('home.metroMap.imgAlt')"
              width="1024"
              height="682"
              decoding="async"
              fetchpriority="low"
            />
            <ul class="metro-map-feature__hotspots" :aria-label="$t('home.metroMap.hotspot.layerAria')">
              <li
                v-for="h in HOTSPOTS"
                :key="h.id"
                class="metro-hotspot"
                :class="{ 'metro-hotspot--open': openId === h.id }"
                :style="{ left: h.x, top: h.y, '--hotspot-delay': h.delay }"
                @mouseenter="onHotspotEnter(h.id)"
                @mouseleave="onHotspotLeave"
                @focusin="onHotspotFocusIn(h.id)"
                @focusout="onHotspotFocusOut"
              >
                <button
                  type="button"
                  class="metro-hotspot__btn"
                  :aria-expanded="openId === h.id ? 'true' : 'false'"
                  :aria-controls="`hotspot-card-${h.id}`"
                  :aria-label="$t('home.metroMap.hotspot.pinAria', { city: CITY_NAMES_EN[h.id] })"
                  @click.stop="onHotspotClick(h.id)"
                >
                  <span class="metro-hotspot__dot" />
                  <span class="metro-hotspot__pulse metro-hotspot__pulse--a" aria-hidden="true" />
                  <span class="metro-hotspot__pulse metro-hotspot__pulse--b" aria-hidden="true" />
                  <span class="metro-hotspot__active-ring" aria-hidden="true" />
                </button>
                <div
                  :id="`hotspot-card-${h.id}`"
                  class="metro-hotspot__card"
                  role="region"
                  :aria-labelledby="`hotspot-card-city-${h.id}`"
                >
                  <p :id="`hotspot-card-city-${h.id}`" class="metro-hotspot__title">
                    {{ CITY_NAMES_EN[h.id] }}
                  </p>
                  <p class="metro-hotspot__line">
                    {{ t(`home.metroMap.hotspot.spots.${h.id}.thisWeek`) }}
                  </p>
                  <p class="metro-hotspot__line metro-hotspot__line--soft">
                    {{ t(`home.metroMap.hotspot.spots.${h.id}.chatter`) }}
                  </p>
                </div>
              </li>
            </ul>
          </div>
        </div>
        <figcaption v-if="$t('home.metroMap.note')" class="metro-map-feature__note">
          {{ $t('home.metroMap.note') }}
        </figcaption>
      </figure>
    </div>
  </section>
</template>

<style scoped>
.metro-map-feature {
  padding: clamp(2rem, 5vw, 3rem) clamp(1.25rem, 4vw, 2rem);
  background: linear-gradient(180deg, #fdfcfa 0%, #f5f7fb 48%, #faf8ff 100%);
  border-top: 1px solid rgba(226, 232, 240, 0.85);
  border-bottom: 1px solid rgba(226, 232, 240, 0.75);
}

.metro-map-feature__inner {
  max-width: min(56rem, 100%);
  margin: 0 auto;
}

.metro-map-feature__head {
  margin-bottom: clamp(1.25rem, 3vw, 1.75rem);
  text-align: center;
}

.metro-map-feature__eyebrow {
  margin: 0 0 0.4rem;
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #a78bfa;
}

.metro-map-feature__title {
  margin: 0 0 0.5rem;
  font-family: var(--font-display);
  font-size: clamp(1.25rem, 3.2vw, 1.6rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--color-ink);
}

.metro-map-feature__lede {
  margin: 0 auto;
  max-width: 28rem;
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1.5;
  color: var(--color-ink-muted);
}

.metro-map-feature__figure {
  margin: 0;
  padding: 0;
}

.metro-map-feature__card {
  padding: clamp(0.5rem, 1.5vw, 0.75rem);
  border-radius: clamp(20px, 3.5vw, 32px);
  background: #fff;
  border: 1px solid rgba(241, 245, 249, 0.98);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 24px 48px rgba(15, 23, 42, 0.06),
    0 8px 24px rgba(15, 23, 42, 0.04);
}

.metro-map-feature__hotspot-hint {
  margin: 0 0 0.55rem;
  padding: 0 clamp(0.35rem, 1.5vw, 0.5rem);
  font-size: clamp(0.78rem, 2.1vw, 0.86rem);
  font-weight: 600;
  line-height: 1.45;
  text-align: center;
  color: #64748b;
}

.metro-map-feature__stage {
  position: relative;
  border-radius: clamp(14px, 2.5vw, 22px);
  overflow: hidden;
}

.metro-map-feature__img {
  display: block;
  width: 100%;
  height: auto;
  vertical-align: middle;
}

.metro-map-feature__hotspots {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 0;
  list-style: none;
  pointer-events: none;
}

.metro-hotspot {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 2;
  pointer-events: auto;
  animation: hotspot-float 5s ease-in-out infinite;
  animation-delay: var(--hotspot-delay, 0s);
}

.metro-hotspot--open {
  z-index: 8;
}

.metro-hotspot__btn {
  position: relative;
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
}

.metro-hotspot__btn:focus-visible {
  outline: 2px solid #a78bfa;
  outline-offset: 4px;
}

.metro-hotspot__dot {
  position: relative;
  z-index: 2;
  width: 0.72rem;
  height: 0.72rem;
  border-radius: 50%;
  background: linear-gradient(145deg, #7dd3fc 0%, #38bdf8 100%);
  box-shadow:
    0 0 0 3px rgba(255, 255, 255, 0.98),
    0 1px 4px rgba(15, 23, 42, 0.12);
}

.metro-hotspot__pulse {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid rgba(56, 189, 248, 0.42);
  pointer-events: none;
}

.metro-hotspot__pulse--a {
  animation: hotspot-pulse 2.6s ease-out infinite;
  animation-delay: var(--hotspot-delay, 0s);
}

.metro-hotspot__pulse--b {
  animation: hotspot-pulse 2.6s ease-out infinite;
  animation-delay: calc(var(--hotspot-delay, 0s) + 1.1s);
  border-color: rgba(125, 211, 252, 0.32);
}

.metro-hotspot__active-ring {
  position: absolute;
  inset: -2px;
  margin: auto;
  width: calc(100% + 4px);
  height: calc(100% + 4px);
  border-radius: 50%;
  border: 2px solid rgba(56, 189, 248, 0);
  pointer-events: none;
  z-index: 1;
}

.metro-hotspot--open .metro-hotspot__active-ring {
  border-color: rgba(56, 189, 248, 0.38);
  animation: hotspot-active-ripple 2s ease-out infinite;
}

.metro-hotspot__card {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 12px);
  transform: translateX(-50%) translateY(4px);
  width: min(13.5rem, calc(100vw - 2.5rem));
  padding: 0.5rem 0.62rem 0.52rem;
  text-align: left;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition:
    opacity 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    visibility 0.32s;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 14px;
  box-shadow:
    0 10px 28px rgba(15, 23, 42, 0.08),
    0 2px 10px rgba(15, 23, 42, 0.04);
}

.metro-hotspot--open .metro-hotspot__card {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0);
  pointer-events: auto;
}

.metro-hotspot__title {
  margin: 0 0 0.28rem;
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.2;
  color: var(--color-ink);
}

.metro-hotspot__line {
  margin: 0 0 0.22rem;
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1.4;
  color: #475569;
}

.metro-hotspot__line:last-child {
  margin-bottom: 0;
}

.metro-hotspot__line--soft {
  font-weight: 500;
  color: #64748b;
}

@keyframes hotspot-float {
  0%,
  100% {
    transform: translate(-50%, -50%) translateY(0);
  }
  50% {
    transform: translate(-50%, -50%) translateY(-2px);
  }
}

@keyframes hotspot-pulse {
  0% {
    transform: scale(0.48);
    opacity: 0.55;
  }
  65% {
    transform: scale(1.42);
    opacity: 0;
  }
  100% {
    transform: scale(1.42);
    opacity: 0;
  }
}

@keyframes hotspot-active-ripple {
  0% {
    transform: scale(0.92);
    opacity: 0.55;
  }
  100% {
    transform: scale(1.35);
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .metro-hotspot {
    animation: none;
  }

  .metro-hotspot__pulse--a,
  .metro-hotspot__pulse--b {
    animation: none;
    opacity: 0.28;
    transform: scale(1.05);
  }

  .metro-hotspot--open .metro-hotspot__active-ring {
    animation: none;
    opacity: 0.45;
    transform: scale(1.08);
  }

  .metro-hotspot__card {
    transition-duration: 0.12s;
  }
}

.metro-map-feature__note {
  margin: 0.75rem 0 0;
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.45;
  color: var(--color-ink-soft);
  text-align: center;
}
</style>
