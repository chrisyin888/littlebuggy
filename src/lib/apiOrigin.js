/**
 * Build same-origin `/api/...` URLs in dev (Vite proxy) or absolute URLs when `VITE_API_BASE_URL` is set.
 * @param {string} path - e.g. `/api/status`
 */
export function apiUrl(path) {
  const raw = import.meta.env.VITE_API_BASE_URL
  const base = typeof raw === 'string' ? raw.replace(/\/$/, '') : ''
  const p = path.startsWith('/') ? path : `/${path}`
  return base ? `${base}${p}` : p
}
