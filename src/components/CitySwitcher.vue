<script setup>
import { computed } from 'vue'
import {
  CITIES,
  DEFAULT_CITY_ID,
  selectedCityId,
  setSelectedCityId,
} from '../composables/useSelectedCity.js'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const cityModel = computed({
  get: () => selectedCityId.value,
  set: (v) => setSelectedCityId(typeof v === 'string' ? v : DEFAULT_CITY_ID),
})
</script>

<template>
  <div class="city-switcher">
    <label class="city-switcher__sr-only" for="lb-city-select">{{ t('app.citySwitcher') }}</label>
    <select id="lb-city-select" v-model="cityModel" class="city-switcher__select">
      <option v-for="c in CITIES" :key="c.id" :value="c.id">
        {{ c.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.city-switcher {
  min-width: 0;
}

.city-switcher__sr-only {
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

.city-switcher__select {
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  padding: 0.35rem 1.75rem 0.35rem 0.55rem;
  border-radius: 10px;
  border: 2px solid rgba(125, 211, 252, 0.55);
  /* Hide native dropdown arrow so it doesn’t stack on our SVG chevron */
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background: rgba(255, 255, 255, 0.92)
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%235c5360' d='M3 4.5 6 8l3-3.5'/%3E%3C/svg%3E")
    no-repeat right 0.45rem center;
  background-size: 12px;
  color: var(--color-ink-muted);
  cursor: pointer;
  max-width: min(200px, 42vw);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.city-switcher__select:hover {
  border-color: rgba(167, 139, 250, 0.65);
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.1);
}

.city-switcher__select:focus-visible {
  outline: 2px solid #a78bfa;
  outline-offset: 2px;
}

.city-switcher__select::-ms-expand {
  display: none;
}
</style>
