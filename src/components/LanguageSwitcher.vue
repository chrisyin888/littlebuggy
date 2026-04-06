<script setup>
import { useI18n } from 'vue-i18n'
import { localeToHtmlLang, persistLocale, SUPPORTED_LOCALES } from '../i18n'
import LittleBuggyMascot from './LittleBuggyMascot.vue'

defineProps({
  variant: {
    type: String,
    default: 'compact',
    validator: (v) => ['compact', 'hero'].includes(v),
  },
})

const { t, locale } = useI18n()

function setLocale(code) {
  locale.value = code
  persistLocale(code)
}
</script>

<template>
  <div
    :class="['lang-switcher', `lang-switcher--${variant}`]"
    role="region"
    :aria-label="variant === 'hero' ? t('app.langSwitcherHero') : t('app.langSwitcher')"
  >
    <template v-if="variant === 'hero'">
      <div class="lang-switcher__buddy" aria-hidden="true">
        <LittleBuggyMascot pose="wave" size="xs" />
        <span class="lang-switcher__buddy-tag">{{ t('app.langSticker') }}</span>
      </div>
      <div class="lang-switcher__hero-head">
        <span class="lang-switcher__hero-icon" aria-hidden="true">🌐</span>
        <div class="lang-switcher__hero-titles">
          <p class="lang-switcher__hero-title">{{ t('app.langPanelTitle') }}</p>
          <p class="lang-switcher__hero-hint">{{ t('app.langPanelHint') }}</p>
        </div>
      </div>
      <ul class="lang-switcher__grid" role="list">
        <li v-for="opt in SUPPORTED_LOCALES" :key="opt.code" class="lang-switcher__cell">
          <button
            type="button"
            class="lang-switcher__pill lang-switcher__pill--hero"
            :class="{ 'lang-switcher__pill--on': locale === opt.code }"
            :aria-pressed="locale === opt.code"
            :lang="localeToHtmlLang(opt.code)"
            @click="setLocale(opt.code)"
          >
            <span class="lang-switcher__native">{{ opt.native }}</span>
            <span class="lang-switcher__short">{{ opt.short }}</span>
          </button>
        </li>
      </ul>
      <p class="lang-switcher__roadmap" role="note">{{ t('app.langRoadmap') }}</p>
    </template>

    <div v-else class="lang-switcher__compact-wrap">
      <label class="lang-switcher__sr-only" for="lb-lang-select">{{ t('app.langSwitcher') }}</label>
      <select
        id="lb-lang-select"
        class="lang-switcher__select"
        :value="locale"
        @change="setLocale($event.target.value)"
      >
        <option v-for="opt in SUPPORTED_LOCALES" :key="opt.code" :value="opt.code">
          {{ opt.native }}
        </option>
      </select>
    </div>
  </div>
</template>

<style scoped>
.lang-switcher--compact {
  min-width: 0;
}

.lang-switcher__compact-wrap {
  position: relative;
  max-width: min(100%, 14rem);
}

.lang-switcher__select {
  width: 100%;
  appearance: none;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  padding: 0.45rem 2rem 0.45rem 0.85rem;
  border-radius: var(--radius-pill);
  border: 2px solid rgba(196, 181, 253, 0.55);
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 251, 235, 0.95) 100%);
  color: var(--color-ink);
  cursor: pointer;
  box-shadow: 2px 2px 0 rgba(186, 230, 253, 0.4);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%237a7280' d='M2 4l4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.65rem center;
}

.lang-switcher__select:hover {
  border-color: rgba(167, 139, 250, 0.75);
}

.lang-switcher__select:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 2px;
}

.lang-switcher__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Hero variant */
.lang-switcher--hero {
  position: relative;
  width: 100%;
  max-width: 42rem;
  margin: 0 auto 1.15rem;
  padding: 1rem 1.1rem 1.05rem;
  border-radius: var(--radius-lg);
  background-image: var(--pattern-dots-soft), var(--pattern-grid),
    linear-gradient(
      152deg,
      rgba(255, 255, 255, 0.98) 0%,
      rgba(255, 244, 230, 0.65) 38%,
      rgba(237, 233, 254, 0.55) 62%,
      rgba(224, 242, 254, 0.48) 100%
    );
  background-size: var(--pattern-dots-size-lg), var(--pattern-grid-size), auto;
  border: 4px solid #fff;
  box-shadow: var(--shadow-sticker-playful);
  overflow: hidden;
}

.lang-switcher--hero::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  box-shadow: 0 0 0 1px rgba(253, 186, 116, 0.25) inset;
}

.lang-switcher__buddy {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.65rem;
}

.lang-switcher__buddy-tag {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #c2410c;
  padding: 0.22rem 0.55rem;
  border-radius: var(--radius-pill);
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border: 2px dashed rgba(251, 191, 36, 0.55);
  box-shadow: 2px 2px 0 rgba(254, 243, 199, 0.9);
}

@media (min-width: 900px) {
  .lang-switcher--hero {
    margin-left: 0;
    margin-right: 0;
  }
}

.lang-switcher__hero-head {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  margin-bottom: 0.85rem;
  text-align: left;
}

.lang-switcher__hero-icon {
  flex-shrink: 0;
  font-size: 1.45rem;
  line-height: 1;
  filter: drop-shadow(0 2px 0 rgba(255, 255, 255, 0.9));
}

.lang-switcher__hero-titles {
  flex: 1;
  min-width: 0;
}

.lang-switcher__hero-title {
  margin: 0 0 0.25rem;
  font-family: var(--font-display);
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-ink);
  line-height: 1.3;
}

.lang-switcher__hero-hint {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-muted);
}

.lang-switcher__grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  justify-content: flex-start;
}

.lang-switcher__cell {
  list-style: none;
  margin: 0;
  padding: 0;
}

.lang-switcher__pill {
  font: inherit;
  cursor: pointer;
  text-align: center;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.lang-switcher__pill--hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.08rem;
  min-width: 4.75rem;
  padding: 0.42rem 0.55rem 0.38rem;
  border-radius: 14px;
  border: 2px solid rgba(255, 255, 255, 0.95);
  background: rgba(255, 252, 247, 0.92);
  color: var(--color-ink);
  box-shadow: 2px 2px 0 rgba(186, 230, 253, 0.45);
}

.lang-switcher__pill--hero:hover {
  transform: translateY(-2px);
  border-color: rgba(196, 181, 253, 0.85);
}

.lang-switcher__pill--hero:focus-visible {
  outline: 3px solid #c4b5fd;
  outline-offset: 2px;
}

.lang-switcher__pill--on {
  border-color: rgba(167, 139, 250, 0.95);
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  box-shadow: 3px 3px 0 rgba(251, 191, 36, 0.35);
  color: #5b21b6;
}

.lang-switcher__native {
  font-size: 0.8rem;
  font-weight: 800;
  line-height: 1.2;
}

.lang-switcher__short {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
  opacity: 0.9;
}

.lang-switcher__pill--on .lang-switcher__short {
  color: #6d28d9;
  opacity: 1;
}

.lang-switcher__roadmap {
  margin: 0.75rem 0 0;
  padding-top: 0.65rem;
  border-top: 2px dashed rgba(196, 181, 253, 0.45);
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-soft);
  text-align: left;
}
</style>
