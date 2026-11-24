/**
 * Homepage cities — ids must match ``backend/app/config/cities.py`` (``resolve_city_id``).
 */
export const CITIES = [
  {
    id: 'vancouver',
    name: 'Metro Vancouver',
    lat: 49.2827,
    lng: -123.1207,
  },
  {
    id: 'gta',
    name: 'GTA',
    lat: 43.6532,
    lng: -79.3832,
  },
]

export const DEFAULT_CITY_ID = 'vancouver'

export const SELECTED_CITY_STORAGE_KEY = 'selected_city'

/** @param {string} id */
export function getCityById(id) {
  return CITIES.find((c) => c.id === id) || CITIES[0]
}
