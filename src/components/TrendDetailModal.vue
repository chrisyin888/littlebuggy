<script setup>
import { computed, watch, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { isTrendDetailKey } from '../content/trendDetails.js'
import LittleBuggyMascot from './LittleBuggyMascot.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  topicKey: { type: String, default: null },
})

const emit = defineEmits(['close'])

const { t, tm, locale } = useI18n()

const panelRef = ref(null)

const show = computed(() => props.open && props.topicKey && isTrendDetailKey(props.topicKey))

const topicPrefix = computed(() => `trends.${props.topicKey}`)

/** Parent-friendly “where data comes from” — different layout from topic explainers. */
const isDataStory = computed(() => show.value && props.topicKey === 'how_it_works')

const dataStory = computed(() => {
  void locale.value
  if (!isDataStory.value) return null
  const p = 'trends.how_it_works'
  const list = (key) => {
    const v = tm(`${p}.${key}`)
    return Array.isArray(v) ? v : []
  }
  return {
    s1Title: t(`${p}.s1Title`),
    s1Intro: t(`${p}.s1Intro`),
    s1Items: list('s1Items'),
    s2Title: t(`${p}.s2Title`),
    s2Items: list('s2Items'),
    s3Title: t(`${p}.s3Title`),
    s3Items: list('s3Items'),
    s4Title: t(`${p}.s4Title`),
    s4Lead: t(`${p}.s4Lead`),
    s4Items: list('s4Items'),
  }
})

const headline = computed(() => {
  void locale.value
  if (!show.value) return ''
  return t(`${topicPrefix.value}.headline`)
})

const whatItIs = computed(() => {
  void locale.value
  if (!show.value) return ''
  return t(`${topicPrefix.value}.whatItIs`)
})

const commonSigns = computed(() => {
  void locale.value
  if (!show.value) return []
  const v = tm(`${topicPrefix.value}.commonSigns`)
  return Array.isArray(v) ? v : []
})

const prevention = computed(() => {
  void locale.value
  if (!show.value) return []
  const v = tm(`${topicPrefix.value}.prevention`)
  return Array.isArray(v) ? v : []
})

const payAttention = computed(() => {
  void locale.value
  if (!show.value) return []
  const v = tm(`${topicPrefix.value}.payAttention`)
  return Array.isArray(v) ? v : []
})

function onBackdropClick(e) {
  if (e.target === e.currentTarget) emit('close')
}

watch(
  () => props.open,
  (isOpen) => {
    if (typeof document === 'undefined') return
    document.body.style.overflow = isOpen ? 'hidden' : ''
    if (isOpen) {
      nextTick(() => panelRef.value?.focus())
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="trend-modal">
      <div class="trend-modal__backdrop" aria-hidden="true" @click="onBackdropClick" />
      <div
        ref="panelRef"
        class="trend-modal__panel"
        :class="{ 'trend-modal__panel--wide': dataStory }"
        role="dialog"
        aria-modal="true"
        tabindex="-1"
        :aria-labelledby="`trend-modal-title-${topicKey}`"
        @click.stop
        @keydown.escape="emit('close')"
      >
        <button
          type="button"
          class="trend-modal__close"
          :aria-label="t('modal.close')"
          @click="emit('close')"
        >
          ✕
        </button>

        <template v-if="dataStory">
          <div class="trend-modal__hero-row">
            <LittleBuggyMascot class="trend-modal__mascot" pose="calm" size="sm" />
            <div class="trend-modal__hero-text">
              <h2 :id="`trend-modal-title-${topicKey}`" class="trend-modal__title trend-modal__title--tight">
                {{ headline }}
              </h2>
              <p class="trend-modal__lead trend-modal__lead--tight">{{ whatItIs }}</p>
            </div>
          </div>

          <section class="trend-modal__section trend-modal__section--story">
            <h3 class="trend-modal__h">{{ dataStory.s1Title }}</h3>
            <p class="trend-modal__intro">{{ dataStory.s1Intro }}</p>
            <ul class="trend-modal__list trend-modal__list--relaxed">
              <li v-for="(line, i) in dataStory.s1Items" :key="'d1' + i">{{ line }}</li>
            </ul>
          </section>

          <section class="trend-modal__section trend-modal__section--story">
            <h3 class="trend-modal__h">{{ dataStory.s2Title }}</h3>
            <ul class="trend-modal__list trend-modal__list--relaxed">
              <li v-for="(line, i) in dataStory.s2Items" :key="'d2' + i">{{ line }}</li>
            </ul>
          </section>

          <section class="trend-modal__section trend-modal__section--story">
            <h3 class="trend-modal__h">{{ dataStory.s3Title }}</h3>
            <ul class="trend-modal__list trend-modal__list--relaxed">
              <li v-for="(line, i) in dataStory.s3Items" :key="'d3' + i">{{ line }}</li>
            </ul>
          </section>

          <section class="trend-modal__section trend-modal__section--important">
            <h3 class="trend-modal__h trend-modal__h--light">{{ dataStory.s4Title }}</h3>
            <p class="trend-modal__important-lead">{{ dataStory.s4Lead }}</p>
            <ul class="trend-modal__list trend-modal__list--relaxed trend-modal__list--important">
              <li v-for="(line, i) in dataStory.s4Items" :key="'d4' + i">{{ line }}</li>
            </ul>
          </section>

          <p class="trend-modal__foot">
            {{ t('modal.disclaimer') }}
          </p>
        </template>

        <template v-else>
          <h2 :id="`trend-modal-title-${topicKey}`" class="trend-modal__title">
            {{ headline }}
          </h2>

          <p class="trend-modal__lead">{{ whatItIs }}</p>

          <section class="trend-modal__section">
            <h3 class="trend-modal__h">{{ t('modal.commonSigns') }}</h3>
            <ul class="trend-modal__list">
              <li v-for="(line, i) in commonSigns" :key="'s' + i">{{ line }}</li>
            </ul>
          </section>

          <section class="trend-modal__section">
            <h3 class="trend-modal__h">{{ t('modal.prevention') }}</h3>
            <ul class="trend-modal__list">
              <li v-for="(line, i) in prevention" :key="'p' + i">{{ line }}</li>
            </ul>
          </section>

          <section class="trend-modal__section trend-modal__section--soft">
            <h3 class="trend-modal__h">{{ t('modal.payAttention') }}</h3>
            <ul class="trend-modal__list">
              <li v-for="(line, i) in payAttention" :key="'a' + i">{{ line }}</li>
            </ul>
          </section>

          <p class="trend-modal__foot">
            {{ t('modal.disclaimer') }}
          </p>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.trend-modal {
  position: fixed;
  inset: 0;
  z-index: 400;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0;
}

@media (min-width: 640px) {
  .trend-modal {
    align-items: center;
    padding: 1.5rem;
  }
}

.trend-modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(61, 53, 64, 0.28);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.trend-modal__panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 32rem;
  max-height: min(88vh, 720px);
  overflow-y: auto;
  margin: 0;
  padding: 1.35rem 1.35rem 1.5rem;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  background: linear-gradient(165deg, #fffcf7 0%, #fff5eb 35%, #e8f7fc 100%);
  border: 4px solid #fff;
  box-shadow:
    0 -8px 0 rgba(255, 200, 140, 0.35),
    0 20px 60px rgba(61, 53, 64, 0.18);
  -webkit-overflow-scrolling: touch;
}

@media (min-width: 640px) {
  .trend-modal__panel {
    border-radius: var(--radius-xl);
    margin: 0 auto;
    box-shadow:
      6px 6px 0 rgba(255, 200, 140, 0.4),
      0 24px 64px rgba(61, 53, 64, 0.14);
  }

  .trend-modal__panel--wide {
    max-width: 38rem;
  }
}

:lang(zh-Hans) .trend-modal__panel {
  line-height: 1.7;
}

.trend-modal__close {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  line-height: 1;
  font-weight: 700;
  color: var(--color-ink-muted);
  cursor: pointer;
  border: 3px solid #fff;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 2px 2px 0 rgba(186, 230, 253, 0.55);
  transition:
    transform 0.2s ease,
    background 0.2s ease;
}

.trend-modal__close:hover {
  transform: scale(1.06);
  background: #fff;
}

.trend-modal__close:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 2px;
}

.trend-modal__hero-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.trend-modal__mascot {
  flex-shrink: 0;
  margin-top: 0.15rem;
}

.trend-modal__hero-text {
  flex: 1;
  min-width: 0;
}

.trend-modal__title {
  margin: 0 2.5rem 0.75rem 0;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.25;
  color: var(--color-ink);
}

.trend-modal__title--tight {
  margin-right: 0;
  margin-bottom: 0.45rem;
}

.trend-modal__lead {
  margin: 0 0 1.15rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.65;
  color: var(--color-ink-muted);
}

.trend-modal__lead--tight {
  margin-bottom: 0;
}

.trend-modal__intro {
  margin: 0 0 0.65rem;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.58;
  color: var(--color-ink-muted);
}

.trend-modal__section {
  margin-bottom: 1.1rem;
  padding: 0.85rem 1rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  border: 2px dashed rgba(253, 186, 116, 0.45);
}

.trend-modal__section--soft {
  border-color: rgba(196, 181, 253, 0.5);
  background: rgba(255, 255, 255, 0.88);
}

.trend-modal__section--story {
  background-image: var(--pattern-dots-soft, radial-gradient(circle, rgba(253, 186, 116, 0.12) 1px, transparent 1px));
  background-size: var(--pattern-dots-size-lg, 18px 18px);
  border-style: solid;
  border-color: rgba(255, 200, 140, 0.35);
}

.trend-modal__section--important {
  margin-top: 0.25rem;
  padding: 1rem 1.05rem;
  border-radius: var(--radius-md);
  border: 3px solid rgba(255, 255, 255, 0.95);
  background: linear-gradient(145deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.55) 50%, rgba(252, 231, 243, 0.45) 100%);
  box-shadow: 0 4px 0 rgba(251, 191, 36, 0.22);
}

.trend-modal__important-lead {
  margin: 0 0 0.6rem;
  font-size: 0.92rem;
  font-weight: 700;
  line-height: 1.55;
  color: var(--color-ink);
}

.trend-modal__h--light {
  color: #9a3412;
}

.trend-modal__h {
  margin: 0 0 0.5rem;
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: #7c3aed;
  letter-spacing: 0.02em;
}

.trend-modal__list {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.trend-modal__list--relaxed {
  padding-left: 1.2rem;
  line-height: 1.62;
  font-size: 0.87rem;
}

.trend-modal__list--relaxed li {
  margin-bottom: 0.5rem;
}

.trend-modal__list--important {
  color: var(--color-ink);
  font-weight: 600;
}

.trend-modal__list li {
  margin-bottom: 0.35rem;
}

.trend-modal__list li:last-child {
  margin-bottom: 0;
}

.trend-modal__foot {
  margin: 0.5rem 0 0;
  font-size: 0.78rem;
  font-weight: 700;
  font-style: italic;
  text-align: center;
  color: var(--color-ink-soft);
  line-height: 1.45;
}
</style>
