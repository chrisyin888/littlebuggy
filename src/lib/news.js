/**
 * Homepage "daily update" news items.
 *
 * Data file: ``public/data/news.json`` (served as ``{BASE_URL}data/news.json``),
 * newest first:
 *
 * ```json
 * {
 *   "items": [
 *     {
 *       "date": "2026-11-12",
 *       "title": "Headline in plain parent-friendly English",
 *       "body": "Short body. Paragraphs separated by a blank line.",
 *       "source": "BCCDC",
 *       "url": "https://example.org/source-article"
 *     }
 *   ]
 * }
 * ```
 *
 * ``url`` is optional. The homepage renders at most the 3 newest items and
 * highlights the first one. Returns ``[]`` on any failure so the section
 * simply hides.
 */

export const NEWS_PUBLIC_PATH = 'data/news.json'

const NEWS_TIMEOUT_MS = 10_000

export function resolveNewsUrl() {
  const base = import.meta.env.BASE_URL || '/'
  return base.endsWith('/') ? `${base}${NEWS_PUBLIC_PATH}` : `${base}/${NEWS_PUBLIC_PATH}`
}

/**
 * @returns {Promise<Array<{ date: string, title: string, body: string, source: string, url?: string }>>}
 */
export async function fetchNewsItems() {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), NEWS_TIMEOUT_MS)
  try {
    const res = await fetch(resolveNewsUrl(), { signal: ctrl.signal, cache: 'no-store' })
    if (!res.ok) return []
    const data = await res.json()
    const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
    return items
      .filter(
        (it) =>
          it &&
          typeof it.date === 'string' &&
          typeof it.title === 'string' &&
          typeof it.body === 'string' &&
          typeof it.source === 'string',
      )
      .sort((a, b) => String(b.date).localeCompare(String(a.date)))
  } catch {
    return []
  } finally {
    clearTimeout(timer)
  }
}
