/**
 * API URL builder for browser `fetch`.
 *
 * - **Dev:** same-origin paths (`/api/...`, `/wait-times`) → Vite proxy → local FastAPI.
 * - **Production:** `VITE_API_BASE_URL` at build time (see `render.yaml`). If it was missing from an older
 *   static build, we fall back to the default Render API hostname so `/wait-times` does not hit the
 *   static host (which would return HTML and break JSON parsing).
 *
 * @param {string} path - e.g. `/api/status`, `/wait-times`
 */

/** Must match `name: littlebuggy-api` → https://littlebuggy-api.onrender.com */
export const DEFAULT_PUBLIC_API_ORIGIN = 'https://littlebuggy-api.onrender.com'

/**
 * Resolved API origin for outbound browser requests (no trailing slash), or '' in dev for proxy mode.
 */
export function resolvedApiBase() {
  const raw = import.meta.env.VITE_API_BASE_URL
  const trimmed = typeof raw === 'string' ? raw.trim().replace(/\/$/, '') : ''
  if (trimmed) return trimmed
  if (import.meta.env.PROD) {
    console.warn(
      '[LittleBuggy] VITE_API_BASE_URL missing — using default API host:',
      DEFAULT_PUBLIC_API_ORIGIN,
    )
    return DEFAULT_PUBLIC_API_ORIGIN.replace(/\/$/, '')
  }
  return ''
}

export function apiUrl(path) {
  const base = resolvedApiBase()
  const p = path.startsWith('/') ? path : `/${path}`

  if (import.meta.env.PROD && base && /localhost|127\.0\.0\.1/i.test(base)) {
    console.warn('[LittleBuggy] API base points at localhost in a production build — fix VITE_API_BASE_URL.')
  }

  return base ? `${base}${p}` : p
}
