<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CITIES, selectedCityId, setSelectedCityId } from '../composables/useSelectedCity.js'

const { t } = useI18n()

const CITY_META = {
  vancouver: { province: 'BC', emoji: '🌊', color: 'sky' },
  gta:       { province: 'ON', emoji: '🏙️', color: 'violet' },
  calgary:   { province: 'AB', emoji: '🏔️', color: 'amber' },
}

const cities = computed(() =>
  CITIES.map(c => ({
    ...c,
    ...(CITY_META[c.id] || { province: '', emoji: '📍', color: 'teal' }),
    active: selectedCityId.value === c.id,
  }))
)
</script>

<template>
  <div class="city-picker" role="group" :aria-label="t('app.citySwitcher')">
    <button
      v-for="city in cities"
      :key="city.id"
      type="button"
      class="city-card"
      :class="[`city-card--${city.color}`, { 'city-card--active': city.active }]"
      :aria-pressed="city.active"
      @click="setSelectedCityId(city.id)"
    >
      <span class="city-card__emoji" aria-hidden="true">{{ city.emoji }}</span>
      <span class="city-card__name">{{ city.name }}</span>
      <span class="city-card__province">{{ city.province }}</span>
    </button>
  </div>
</template>

<style scoped>
.city-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  justify-content: center;
  padding: 0.25rem 0 1.5rem;
}

.city-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  padding: 0.7rem 1.25rem 0.6rem;
  border-radius: var(--radius-md);
  border: 2.5px solid transparent;
  background: rgba(255, 255, 255, 0.82);
  cursor: pointer;
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: var(--color-ink-muted);
  box-shadow: 3px 3px 0 rgba(255, 200, 140, 0.3), 0 4px 14px rgba(61, 53, 64, 0.06);
  transition:
    transform 0.18s var(--ease-bounce),
    box-shadow 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
  min-width: 100px;
}

.city-card:hover:not(.city-card--active) {
  transform: translateY(-2px);
  box-shadow: 3px 5px 0 rgba(255, 200, 140, 0.35), 0 8px 20px rgba(61, 53, 64, 0.1);
}

.city-card__emoji {
  font-size: 1.5rem;
  line-height: 1;
}

.city-card__name {
  font-size: 0.88rem;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}

.city-card__province {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.65;
}

/* Sky — Vancouver */
.city-card--sky.city-card--active {
  background: linear-gradient(145deg, #e0f7ff 0%, #bae6fd 100%);
  border-color: #38bdf8;
  color: #0369a1;
  box-shadow: 3px 3px 0 rgba(56, 189, 248, 0.35), 0 6px 18px rgba(56, 189, 248, 0.2);
  transform: translateY(-1px);
}
.city-card--sky:hover:not(.city-card--active) {
  border-color: rgba(56, 189, 248, 0.4);
}

/* Violet — GTA */
.city-card--violet.city-card--active {
  background: linear-gradient(145deg, #f3e8ff 0%, #ddd6fe 100%);
  border-color: #a78bfa;
  color: #5b21b6;
  box-shadow: 3px 3px 0 rgba(167, 139, 250, 0.35), 0 6px 18px rgba(167, 139, 250, 0.2);
  transform: translateY(-1px);
}
.city-card--violet:hover:not(.city-card--active) {
  border-color: rgba(167, 139, 250, 0.4);
}

/* Amber — Calgary */
.city-card--amber.city-card--active {
  background: linear-gradient(145deg, #fffbeb 0%, #fde68a 100%);
  border-color: #f59e0b;
  color: #92400e;
  box-shadow: 3px 3px 0 rgba(245, 158, 11, 0.35), 0 6px 18px rgba(245, 158, 11, 0.2);
  transform: translateY(-1px);
}
.city-card--amber:hover:not(.city-card--active) {
  border-color: rgba(245, 158, 11, 0.4);
}
</style>
