import { ref } from 'vue'
import {
  CITIES,
  DEFAULT_CITY_ID,
  SELECTED_CITY_STORAGE_KEY,
  getCityById,
} from '../config/cities.js'

function readStoredCityId() {
  if (typeof localStorage === 'undefined') return DEFAULT_CITY_ID
  try {
    const v = localStorage.getItem(SELECTED_CITY_STORAGE_KEY)
    if (v && CITIES.some((c) => c.id === v)) return v
  } catch {
    /* ignore */
  }
  return DEFAULT_CITY_ID
}

/** Reactive selected homepage city id (synced with localStorage). */
export const selectedCityId = ref(readStoredCityId())

/** @param {string} id */
export function setSelectedCityId(id) {
  const next = CITIES.some((c) => c.id === id) ? id : DEFAULT_CITY_ID
  selectedCityId.value = next
  try {
    localStorage.setItem(SELECTED_CITY_STORAGE_KEY, next)
  } catch {
    /* ignore */
  }
}

export { getCityById, CITIES, DEFAULT_CITY_ID }
