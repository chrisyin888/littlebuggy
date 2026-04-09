<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { apiUrl } from '../lib/apiOrigin.js'
import LittleBuggyMascot from '../components/LittleBuggyMascot.vue'

const TOKEN_KEY = 'lb_admin_homepage_token'

const token = ref(typeof sessionStorage !== 'undefined' ? sessionStorage.getItem(TOKEN_KEY) || '' : '')
const showToken = ref(false)
const busy = ref(false)
const errorMessage = ref('')
const errorDetail = ref('')
const result = ref(null)
const downloadNotice = ref('')

const isDev = import.meta.env.DEV
const hasRemoteApi = Boolean(
  typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim(),
)

const tokenInputType = computed(() => (showToken.value ? 'text' : 'password'))

let robotsMeta = null

onMounted(() => {
  robotsMeta = document.createElement('meta')
  robotsMeta.name = 'robots'
  robotsMeta.content = 'noindex, nofollow'
  document.head.appendChild(robotsMeta)
})

onUnmounted(() => {
  if (robotsMeta?.parentNode) {
    robotsMeta.parentNode.removeChild(robotsMeta)
  }
})

function persistToken() {
  try {
    sessionStorage.setItem(TOKEN_KEY, token.value)
  } catch {
    /* ignore */
  }
}

function splitWarnings(list) {
  const disk = []
  const feed = []
  for (const w of list || []) {
    const s = String(w)
    if (/disk_write/i.test(s)) disk.push(w)
    else feed.push(w)
  }
  return { disk, feed }
}

const feedWarnings = computed(() => splitWarnings(result.value?.warnings).feed)
const diskWarnings = computed(() => splitWarnings(result.value?.warnings).disk)

const diskWriteFailed = computed(
  () => result.value?.disk_write_configured && !result.value?.written_to_disk,
)

const dbPersistFailed = computed(() =>
  (result.value?.warnings || []).some((w) => String(w).startsWith('db_persist_failed')),
)

const sourcesPartial = computed(
  () => result.value && result.value.sources_ok_count < 3,
)

/** Success = written + all sources OK + no feed warnings + no disk failure. */
const runOutcomeLabel = computed(() => {
  if (errorMessage.value && !result.value) return 'Failed'
  const r = result.value
  if (!r?.ok) return 'Failed'
  if (
    !diskWriteFailed.value &&
    !dbPersistFailed.value &&
    !sourcesPartial.value &&
    feedWarnings.value.length === 0 &&
    (r.written_to_disk || r.persisted_to_database)
  ) {
    return 'Success'
  }
  return 'Partial'
})

const runOutcomeVariant = computed(() => {
  const v = runOutcomeLabel.value
  if (v === 'Success') return 'success'
  if (v === 'Failed') return 'failed'
  return 'partial'
})

const outcomeBanner = computed(() => {
  const r = result.value
  if (!r?.ok) return null
  if (diskWriteFailed.value) {
    return {
      kind: 'danger',
      title: 'Snapshot built, but the file was not saved',
      sub: 'HOMEPAGE_SUMMARY_OUTPUT_PATH is set on the API, but writing failed (permissions or bad path).',
    }
  }
  if (dbPersistFailed.value) {
    return {
      kind: 'danger',
      title: 'Snapshot built, but the database was not updated',
      sub: 'Check DATABASE_URL on the API host and DB permissions. Production GET /api/homepage-summary still serves the previous row until a save succeeds.',
    }
  }
  if (r.written_to_disk) {
    const sub =
      feedWarnings.value.length || sourcesPartial.value
        ? 'Data was fetched and JSON was written on the machine running the API. Some feeds reported issues — see warnings.'
        : 'Data was fetched and JSON was written on the machine running the API.'
    return { kind: 'success', title: 'Snapshot saved to disk', sub }
  }
  if (r.persisted_to_database) {
    const sub =
      feedWarnings.value.length || sourcesPartial.value
        ? 'A new trend_snapshots row was saved. Some feeds reported issues — see warnings.'
        : 'A new trend_snapshots row was saved. Production loads this via GET /api/homepage-summary.'
    return { kind: 'success', title: 'Snapshot saved to database', sub }
  }
  return {
    kind: 'info',
    title: 'Snapshot built (in memory only)',
    sub:
      'The API generated fresh JSON but did not write to disk or database. Set HOMEPAGE_SUMMARY_OUTPUT_PATH and/or fix DATABASE_URL, or use Download full JSON.',
  }
})

const whatHappened = computed(() => {
  const r = result.value
  if (!r?.ok) return []
  const lines = [
    'Fetched public feeds (respiratory, AQHI, weather) and built the same payload as npm run weekly:homepage.',
  ]
  if (r.written_to_disk && r.output_path) {
    lines.push(`Wrote homepage-summary.json to: ${r.output_path}`)
  } else if (r.disk_write_configured && !r.written_to_disk) {
    lines.push('Attempted to write HOMEPAGE_SUMMARY_OUTPUT_PATH but the write did not succeed.')
  } else if (!r.disk_write_configured) {
    lines.push('Did not write any file on the server — output path is not configured on the API.')
  }
  if (r.persisted_to_database && r.database_snapshot_id != null) {
    lines.push(
      `Saved trend_snapshots id ${r.database_snapshot_id} — production GET /api/homepage-summary will return this row.`,
    )
  } else if (dbPersistFailed.value) {
    lines.push('Database save failed — see warnings. The live API may still show the previous snapshot.')
  }
  lines.push(`Sources reporting OK in JSON: ${r.sources_ok_count} of 3.`)
  if (r.updated_at) {
    lines.push(`Build timestamp in payload (updated_at): ${r.updated_at}.`)
  }
  return lines
})

const nextSteps = computed(() => {
  const r = result.value
  if (!r?.ok) return []
  const steps = []

  if (r.written_to_disk) {
    steps.push({
      text: 'Confirm in the app: run npm run dev and hard-refresh the homepage (or open / and reload).',
    })
    steps.push({
      text: 'When you are ready to update the live site: commit the JSON, build, and deploy as usual.',
      code: 'git add public/data/homepage-summary.json && git commit -m "Update homepage summary" && git push',
    })
    steps.push({
      text: 'Remember: production visitors only see the JSON that was built into your last deploy — not this run by itself.',
    })
    return steps
  }

  if (r.persisted_to_database && !dbPersistFailed.value) {
    steps.push({
      text: 'Open the live homepage and click Refresh (or hard-reload). The production app requests GET /api/homepage-summary first, which now reads the new database row.',
    })
    steps.push({
      text: 'Optional: run npm run weekly:homepage locally and commit public/data/homepage-summary.json so the static fallback file matches production.',
      code: 'npm run weekly:homepage && git add public/data/homepage-summary.json && git commit -m "Update homepage summary" && git push',
    })
    return steps
  }

  if (diskWriteFailed.value) {
    steps.push({
      text: 'Fix the path or permissions for HOMEPAGE_SUMMARY_OUTPUT_PATH on the API machine, then run Update again.',
    })
    steps.push({
      text: 'Or use Download full JSON and replace public/data/homepage-summary.json in your repo manually.',
    })
    return steps
  }

  steps.push({
    text: 'To auto-save from this button on your laptop: set HOMEPAGE_SUMMARY_OUTPUT_PATH in backend/.env (see backend/.env.example), restart uvicorn, then click Update again.',
  })
  steps.push({
    text: 'Otherwise: click Download full JSON and save the file as public/data/homepage-summary.json in your project.',
  })
  steps.push({
    text: 'Then commit, build, and deploy. If your production build uses the live API for the homepage, also ensure POST /admin/homepage-snapshot/regenerate can write the database (see API env).',
    code: 'git add public/data/homepage-summary.json && git commit -m "Update homepage summary" && git push',
  })
  return steps
})

/** Friendly next-step box copy when JSON landed on disk (local-style). */
const nextStepHelperIntro = computed(() => {
  if (!result.value?.ok) return ''
  if (result.value.written_to_disk) {
    return 'If this was a local update and the file path looks right, your next steps are:'
  }
  if (diskWriteFailed.value) {
    return 'The snapshot was generated, but nothing was saved on the API machine. Next:'
  }
  if (result.value?.persisted_to_database && !dbPersistFailed.value) {
    return 'The database was updated. Next:'
  }
  return 'The snapshot was built in memory only — your repo file was not updated automatically. Next:'
})

function parseHttpError(status, data) {
  const d = data?.detail
  const msg =
    typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg || JSON.stringify(x)).join(' ') : ''
  if (status === 503) {
    return {
      title: 'API could not complete regeneration',
      detail:
        msg ||
        'Common causes: ADMIN_HOMEPAGE_TOKEN not set (admin disabled), or DATABASE_URL / Postgres unreachable so the snapshot row could not be saved.',
    }
  }
  if (status === 401) {
    return {
      title: 'Token rejected',
      detail: msg || 'Check that the token matches ADMIN_HOMEPAGE_TOKEN exactly (no extra spaces).',
    }
  }
  return {
    title: `Request failed (${status})`,
    detail: msg || 'See browser network tab for the raw response.',
  }
}

async function runRegenerate() {
  errorMessage.value = ''
  errorDetail.value = ''
  result.value = null
  downloadNotice.value = ''
  persistToken()
  if (!token.value.trim()) {
    errorMessage.value = 'Enter your admin token first.'
    errorDetail.value = 'Use the same value as ADMIN_HOMEPAGE_TOKEN on the FastAPI process.'
    return
  }
  busy.value = true
  try {
    const res = await fetch(apiUrl('/api/admin/homepage-snapshot/regenerate'), {
      method: 'POST',
      headers: {
        'X-Admin-Token': token.value.trim(),
        Accept: 'application/json',
      },
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const parsed = parseHttpError(res.status, data)
      errorMessage.value = parsed.title
      errorDetail.value = parsed.detail
      return
    }
    result.value = data
  } catch (e) {
    errorMessage.value = 'Could not reach the API'
    errorDetail.value =
      e instanceof Error
        ? `${e.message} — Start the API (cd backend && uvicorn …). For a hosted API, set VITE_API_BASE_URL in .env and rebuild.`
        : String(e)
  } finally {
    busy.value = false
  }
}

async function downloadFullJson() {
  errorMessage.value = ''
  errorDetail.value = ''
  downloadNotice.value = ''
  persistToken()
  if (!token.value.trim()) {
    errorMessage.value = 'Enter your admin token first.'
    errorDetail.value = 'Required for Download full JSON.'
    return
  }
  busy.value = true
  try {
    const res = await fetch(apiUrl('/api/admin/homepage-snapshot/regenerate/raw'), {
      method: 'POST',
      headers: {
        'X-Admin-Token': token.value.trim(),
        Accept: 'application/json',
      },
    })
    const data = await res.json().catch(() => null)
    if (!res.ok) {
      const parsed = parseHttpError(res.status, data)
      errorMessage.value = parsed.title
      errorDetail.value = parsed.detail
      return
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'homepage-summary.json'
    a.rel = 'noopener'
    a.click()
    URL.revokeObjectURL(url)
    downloadNotice.value =
      'Download started. Move or copy the file to public/data/homepage-summary.json in your repo, then commit.'
  } catch (e) {
    errorMessage.value = 'Download failed'
    errorDetail.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="adm">
    <div class="adm__inner">
      <header class="adm-header">
        <div class="adm-header__brand" aria-hidden="true">
          <LittleBuggyMascot class="adm-header__mascot" pose="calm" size="sm" />
        </div>
        <div class="adm-header__text">
          <h1 class="adm-header__title">Homepage Snapshot Update</h1>
          <p class="adm-header__subtitle">
            Refresh this week’s LittleBuggy homepage data and review the result before publishing.
          </p>
          <div class="adm-header__meta">
            <span class="adm-badge" :class="{ 'adm-badge--accent': isDev }">{{ isDev ? 'Local' : 'Build' }}</span>
            <span class="adm-badge adm-badge--muted">{{
              hasRemoteApi ? 'API via VITE_API_BASE_URL' : 'API via dev proxy'
            }}</span>
          </div>
        </div>
      </header>

      <section class="adm-card adm-card--compact" aria-labelledby="adm-token-label">
        <div class="adm-card__head">
          <h2 id="adm-token-label" class="adm-card__title">Access</h2>
        </div>
        <label class="adm-field-label" for="adm-token-input">Private admin token</label>
        <div class="adm-token-row">
          <input
            id="adm-token-input"
            v-model="token"
            class="adm-input"
            :type="tokenInputType"
            autocomplete="off"
            placeholder="Enter token"
          />
          <button type="button" class="adm-toggle" @click="showToken = !showToken">
            {{ showToken ? 'Hide' : 'Show' }}
          </button>
        </div>
        <p class="adm-field-hint">
          This private token is required to regenerate the homepage snapshot. It is kept in session storage for
          this tab only — never committed to Git. Match <code class="adm-code">ADMIN_HOMEPAGE_TOKEN</code> on your
          API.
        </p>
      </section>

      <section class="adm-card adm-card--action" aria-labelledby="adm-action-title">
        <h2 id="adm-action-title" class="adm-sr-only">Actions</h2>
        <p class="adm-action__lead">Generate fresh data from public feeds, same as <code class="adm-code">npm run weekly:homepage</code>.</p>
        <div class="adm-action__buttons">
          <button type="button" class="adm-btn adm-btn--primary" :disabled="busy" @click="runRegenerate">
            {{ busy ? 'Updating…' : 'Update Homepage Snapshot' }}
          </button>
          <button type="button" class="adm-btn adm-btn--ghost" :disabled="busy" @click="downloadFullJson">
            Download Full JSON
          </button>
        </div>
      </section>

      <div v-if="errorMessage" class="adm-alert adm-alert--error" role="alert">
        <div class="adm-alert__icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </div>
        <div>
          <p class="adm-alert__title">{{ errorMessage }}</p>
          <p v-if="errorDetail" class="adm-alert__text">{{ errorDetail }}</p>
        </div>
      </div>

      <div v-if="downloadNotice" class="adm-alert adm-alert--success">
        <div class="adm-alert__icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </div>
        <p class="adm-alert__text adm-alert__text--solo">{{ downloadNotice }}</p>
      </div>

      <section v-if="result && outcomeBanner" class="adm-results" aria-live="polite">
        <div class="adm-card">
          <div class="adm-results__head">
            <h2 class="adm-card__title adm-card__title--lg">Last run</h2>
            <span
              class="adm-status"
              :class="{
                'adm-status--success': runOutcomeVariant === 'success',
                'adm-status--partial': runOutcomeVariant === 'partial',
                'adm-status--failed': runOutcomeVariant === 'failed',
              }"
            >
              {{ runOutcomeLabel }}
            </span>
          </div>

          <div
            class="adm-results__banner"
            :class="{
              'adm-results__banner--ok': outcomeBanner.kind === 'success',
              'adm-results__banner--info': outcomeBanner.kind === 'info',
              'adm-results__banner--bad': outcomeBanner.kind === 'danger',
            }"
          >
            <p class="adm-results__banner-title">{{ outcomeBanner.title }}</p>
            <p class="adm-results__banner-text">{{ outcomeBanner.sub }}</p>
          </div>

          <div class="adm-metrics">
            <div class="adm-metric">
              <span class="adm-metric__label">Updated at</span>
              <span class="adm-metric__value">{{ result.updated_at || '—' }}</span>
            </div>
            <div class="adm-metric">
              <span class="adm-metric__label">Region</span>
              <span class="adm-metric__value">{{ result.region || '—' }}</span>
            </div>
            <div class="adm-metric">
              <span class="adm-metric__label">Sources OK</span>
              <span class="adm-metric__value" :class="{ 'adm-metric__value--warn': sourcesPartial }">
                {{ result.sources_ok_count }} / 3
              </span>
            </div>
            <div class="adm-metric adm-metric--full">
              <span class="adm-metric__label">Database (trend_snapshots)</span>
              <span
                class="adm-metric__value"
                :class="{
                  'adm-metric__value--ok': result.persisted_to_database,
                  'adm-metric__value--bad': dbPersistFailed,
                  'adm-metric__value--muted': !result.persisted_to_database && !dbPersistFailed,
                }"
              >
                <template v-if="result.persisted_to_database">Yes — row id {{ result.database_snapshot_id }}</template>
                <template v-else-if="dbPersistFailed">No — save failed</template>
                <template v-else>No new row (check DATABASE_URL)</template>
              </span>
            </div>
            <div class="adm-metric adm-metric--full">
              <span class="adm-metric__label">JSON on API disk</span>
              <span
                class="adm-metric__value"
                :class="{
                  'adm-metric__value--ok': result.written_to_disk,
                  'adm-metric__value--bad': diskWriteFailed,
                  'adm-metric__value--muted': !result.written_to_disk && !diskWriteFailed,
                }"
              >
                <template v-if="result.written_to_disk">Yes — file written</template>
                <template v-else-if="diskWriteFailed">No — write failed</template>
                <template v-else>No — path not configured (in-memory only)</template>
              </span>
            </div>
            <div v-if="result.output_path" class="adm-metric adm-metric--full">
              <span class="adm-metric__label">Path</span>
              <code class="adm-metric__code">{{ result.output_path }}</code>
            </div>
          </div>

          <div v-if="result.short_summary_preview" class="adm-summary">
            <h3 class="adm-summary__label">Short summary preview</h3>
            <p class="adm-summary__text">{{ result.short_summary_preview }}</p>
          </div>

          <div v-if="feedWarnings.length" class="adm-warn-block">
            <h3 class="adm-warn-block__label">Warnings</h3>
            <ul class="adm-warn-block__list">
              <li v-for="(w, i) in feedWarnings" :key="'f' + i">{{ w }}</li>
            </ul>
          </div>

          <div v-if="diskWarnings.length" class="adm-warn-block adm-warn-block--disk">
            <h3 class="adm-warn-block__label">Disk</h3>
            <ul class="adm-warn-block__list">
              <li v-for="(w, i) in diskWarnings" :key="'d' + i">{{ w }}</li>
            </ul>
          </div>

          <p v-if="result.hint" class="adm-results__hint">{{ result.hint }}</p>

          <details class="adm-details">
            <summary>Run details</summary>
            <ul class="adm-details__list">
              <li v-for="(line, i) in whatHappened" :key="i">{{ line }}</li>
            </ul>
          </details>
        </div>

        <div class="adm-nextbox">
          <h3 class="adm-nextbox__title">What to do next</h3>
          <p class="adm-nextbox__intro">{{ nextStepHelperIntro }}</p>
          <ol class="adm-nextbox__steps">
            <template v-if="result.written_to_disk">
              <li>Review the homepage in the app (hard refresh).</li>
              <li>Commit the updated <code class="adm-code">public/data/homepage-summary.json</code>.</li>
              <li>Push and deploy so visitors get the new snapshot.</li>
            </template>
            <template v-else-if="result.persisted_to_database && !dbPersistFailed">
              <li>Hard-refresh the live homepage (or tap Refresh) so it refetches <code class="adm-code">GET /api/homepage-summary</code>.</li>
              <li>
                Optional: run <code class="adm-code">npm run weekly:homepage</code> and commit the JSON so dev / static fallback match production.
              </li>
            </template>
            <template v-else-if="diskWriteFailed">
              <li>Fix <code class="adm-code">HOMEPAGE_SUMMARY_OUTPUT_PATH</code> or permissions, then run Update again.</li>
              <li>Or use <strong>Download Full JSON</strong> and replace the file in your repo manually.</li>
            </template>
            <template v-else>
              <li>
                Set <code class="adm-code">HOMEPAGE_SUMMARY_OUTPUT_PATH</code> in <code class="adm-code">backend/.env</code>
                if you want one-click saves from this page (restart the API).
              </li>
              <li>Or download the JSON and place it at <code class="adm-code">public/data/homepage-summary.json</code>.</li>
              <li>
                For production with the live API: ensure <code class="adm-code">DATABASE_URL</code> works so this button can insert a snapshot row.
              </li>
            </template>
          </ol>
          <template v-for="(step, i) in nextSteps" :key="'c' + i">
            <pre v-if="step.code" class="adm-nextbox__code">{{ step.code }}</pre>
          </template>
        </div>
      </section>

      <footer class="adm-footer">
        <router-link to="/" class="adm-footer__link">← Back to site</router-link>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.adm {
  --adm-ink: #0f172a;
  --adm-muted: #64748b;
  --adm-border: #e2e8f0;
  --adm-surface: #ffffff;
  --adm-canvas: #f1f5f9;
  --adm-accent: #5b21b6;
  --adm-accent-soft: #ede9fe;
  --adm-success: #047857;
  --adm-success-bg: #ecfdf5;
  --adm-warn: #b45309;
  --adm-warn-bg: #fffbeb;
  --adm-danger: #b91c1c;
  --adm-danger-bg: #fef2f2;
  --adm-radius: 14px;
  --adm-radius-sm: 10px;
  --adm-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 32px rgba(15, 23, 42, 0.06);

  min-height: 100vh;
  padding: clamp(1.5rem, 5vw, 3rem) clamp(1rem, 4vw, 1.5rem);
  background: var(--adm-canvas);
  color: var(--adm-ink);
  font-family: var(--font-body, 'Inter', system-ui, -apple-system, sans-serif);
  -webkit-font-smoothing: antialiased;
}

.adm__inner {
  max-width: 38rem;
  margin: 0 auto;
}

@media (min-width: 640px) {
  .adm__inner {
    max-width: 42rem;
  }
}

.adm-sr-only {
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

.adm-header {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1.75rem;
}

.adm-header__brand {
  flex-shrink: 0;
  padding: 0.35rem;
  border-radius: 12px;
  background: var(--adm-surface);
  border: 1px solid var(--adm-border);
  box-shadow: var(--adm-shadow);
}

.adm-header__mascot {
  display: block;
  opacity: 0.92;
}

.adm-header__text {
  min-width: 0;
  flex: 1;
  padding-top: 0.15rem;
}

.adm-header__title {
  margin: 0 0 0.4rem;
  font-size: clamp(1.35rem, 4vw, 1.65rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.2;
  color: var(--adm-ink);
}

.adm-header__subtitle {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--adm-muted);
  font-weight: 450;
}

.adm-header__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.adm-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-radius: 999px;
  background: #e2e8f0;
  color: #475569;
}

.adm-badge--accent {
  background: var(--adm-accent-soft);
  color: var(--adm-accent);
}

.adm-badge--muted {
  background: #f8fafc;
  color: #64748b;
  border: 1px solid var(--adm-border);
}

.adm-card {
  background: var(--adm-surface);
  border: 1px solid var(--adm-border);
  border-radius: var(--adm-radius);
  box-shadow: var(--adm-shadow);
  padding: 1.25rem 1.35rem;
  margin-bottom: 1rem;
}

.adm-card--compact {
  padding: 1rem 1.2rem 1.1rem;
}

.adm-card--action {
  padding: 1.35rem 1.4rem 1.4rem;
  border-color: #ddd6fe;
  background: linear-gradient(165deg, #fafaff 0%, #fff 55%);
}

.adm-card__head {
  margin-bottom: 0.65rem;
}

.adm-card__title {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--adm-muted);
}

.adm-card__title--lg {
  font-size: 0.75rem;
}

.adm-field-label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--adm-ink);
  margin-bottom: 0.4rem;
}

.adm-token-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.adm-input {
  flex: 1;
  min-width: 0;
  padding: 0.55rem 0.75rem;
  font-size: 0.9375rem;
  border: 1px solid var(--adm-border);
  border-radius: var(--adm-radius-sm);
  background: #f8fafc;
  color: var(--adm-ink);
  transition: border-color 0.15s ease, background 0.15s ease;
}

.adm-input:focus {
  outline: none;
  border-color: #a78bfa;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.adm-toggle {
  flex-shrink: 0;
  padding: 0 0.85rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--adm-accent);
  background: var(--adm-surface);
  border: 1px solid var(--adm-border);
  border-radius: var(--adm-radius-sm);
  cursor: pointer;
}

.adm-toggle:hover {
  background: #fafafa;
}

.adm-field-hint {
  margin: 0.55rem 0 0;
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--adm-muted);
}

.adm-code {
  font-family: ui-monospace, monospace;
  font-size: 0.85em;
  padding: 0.08em 0.35em;
  border-radius: 4px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}

.adm-action__lead {
  margin: 0 0 1.1rem;
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--adm-muted);
}

.adm-action__buttons {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

@media (min-width: 480px) {
  .adm-action__buttons {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
  }
}

.adm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.65rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: var(--adm-radius-sm);
  cursor: pointer;
  border: 1px solid transparent;
  transition: opacity 0.15s ease, transform 0.1s ease;
}

.adm-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.adm-btn--primary {
  background: linear-gradient(135deg, #5b21b6 0%, #6d28d9 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(91, 33, 182, 0.25);
}

.adm-btn--primary:hover:not(:disabled) {
  filter: brightness(1.05);
}

.adm-btn--ghost {
  background: var(--adm-surface);
  color: var(--adm-ink);
  border-color: var(--adm-border);
}

.adm-btn--ghost:hover:not(:disabled) {
  background: #f8fafc;
}

.adm-alert {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 1rem 1.15rem;
  border-radius: var(--adm-radius-sm);
  margin-bottom: 1rem;
  border: 1px solid transparent;
}

.adm-alert--error {
  background: var(--adm-danger-bg);
  border-color: #fecaca;
  color: var(--adm-danger);
}

.adm-alert--success {
  background: var(--adm-success-bg);
  border-color: #a7f3d0;
  color: var(--adm-success);
}

.adm-alert__icon {
  flex-shrink: 0;
  margin-top: 0.05rem;
  opacity: 0.9;
}

.adm-alert__title {
  margin: 0 0 0.25rem;
  font-size: 0.9rem;
  font-weight: 700;
}

.adm-alert__text {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.5;
  opacity: 0.95;
}

.adm-alert__text--solo {
  margin: 0;
  font-weight: 600;
}

.adm-results {
  margin-bottom: 2rem;
}

.adm-results__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  margin-bottom: 1rem;
}

.adm-status {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.65rem;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-radius: 999px;
  border: 1px solid transparent;
}

.adm-status--success {
  background: var(--adm-success-bg);
  color: var(--adm-success);
  border-color: #6ee7b7;
}

.adm-status--partial {
  background: var(--adm-warn-bg);
  color: var(--adm-warn);
  border-color: #fcd34d;
}

.adm-status--failed {
  background: var(--adm-danger-bg);
  color: var(--adm-danger);
  border-color: #fca5a5;
}

.adm-results__banner {
  padding: 0.9rem 1rem;
  border-radius: var(--adm-radius-sm);
  margin-bottom: 1.15rem;
  border: 1px solid transparent;
}

.adm-results__banner--ok {
  background: var(--adm-success-bg);
  border-color: #a7f3d0;
}

.adm-results__banner--info {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.adm-results__banner--bad {
  background: var(--adm-danger-bg);
  border-color: #fecaca;
}

.adm-results__banner-title {
  margin: 0 0 0.35rem;
  font-size: 0.9rem;
  font-weight: 700;
}

.adm-results__banner-text {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--adm-muted);
}

.adm-results__banner--ok .adm-results__banner-text,
.adm-results__banner--bad .adm-results__banner-text {
  color: #334155;
}

.adm-metrics {
  display: grid;
  gap: 0;
  border: 1px solid var(--adm-border);
  border-radius: var(--adm-radius-sm);
  overflow: hidden;
  margin-bottom: 1.15rem;
}

.adm-metric {
  display: grid;
  grid-template-columns: minmax(7rem, 32%) 1fr;
  gap: 0.75rem;
  align-items: baseline;
  padding: 0.65rem 0.85rem;
  background: #fafafa;
  border-bottom: 1px solid var(--adm-border);
  font-size: 0.875rem;
}

.adm-metric:last-child {
  border-bottom: none;
}

.adm-metric--full {
  grid-template-columns: minmax(7rem, 32%) 1fr;
}

.adm-metric__label {
  font-weight: 600;
  color: var(--adm-muted);
  font-size: 0.78rem;
}

.adm-metric__value {
  font-weight: 600;
  color: var(--adm-ink);
  word-break: break-word;
}

.adm-metric__value--ok {
  color: var(--adm-success);
}

.adm-metric__value--bad {
  color: var(--adm-danger);
}

.adm-metric__value--muted {
  color: var(--adm-muted);
  font-weight: 500;
}

.adm-metric__value--warn {
  color: var(--adm-warn);
}

.adm-metric__code {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
  padding: 0.35rem 0.5rem;
  background: #fff;
  border: 1px solid var(--adm-border);
  border-radius: 6px;
  word-break: break-all;
}

.adm-summary {
  padding: 0.85rem 1rem;
  background: #f8fafc;
  border-radius: var(--adm-radius-sm);
  border: 1px solid var(--adm-border);
  margin-bottom: 1rem;
}

.adm-summary__label {
  margin: 0 0 0.4rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--adm-muted);
}

.adm-summary__text {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.58;
  color: #334155;
}

.adm-warn-block {
  padding: 0.85rem 1rem;
  border-radius: var(--adm-radius-sm);
  background: var(--adm-warn-bg);
  border: 1px solid #fde68a;
  margin-bottom: 0.75rem;
}

.adm-warn-block--disk {
  background: #fff7ed;
  border-color: #fed7aa;
}

.adm-warn-block__label {
  margin: 0 0 0.4rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--adm-warn);
}

.adm-warn-block--disk .adm-warn-block__label {
  color: #c2410c;
}

.adm-warn-block__list {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #78350f;
}

.adm-results__hint {
  margin: 0 0 1rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--adm-muted);
}

.adm-details {
  font-size: 0.8125rem;
  color: var(--adm-muted);
}

.adm-details summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--adm-accent);
  padding: 0.35rem 0;
}

.adm-details__list {
  margin: 0.5rem 0 0;
  padding-left: 1.15rem;
  line-height: 1.5;
}

.adm-nextbox {
  margin-top: 1rem;
  padding: 1.2rem 1.35rem;
  border-radius: var(--adm-radius);
  border: 1px solid #c4b5fd;
  background: linear-gradient(180deg, #f5f3ff 0%, #fff 70%);
  box-shadow: var(--adm-shadow);
}

.adm-nextbox__title {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--adm-ink);
}

.adm-nextbox__intro {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #475569;
}

.adm-nextbox__steps {
  margin: 0 0 1rem;
  padding-left: 1.2rem;
  font-size: 0.875rem;
  line-height: 1.65;
  color: var(--adm-ink);
}

.adm-nextbox__steps li {
  margin-bottom: 0.35rem;
}

.adm-nextbox__code {
  display: block;
  margin-top: 0.75rem;
  padding: 0.55rem 0.65rem;
  font-size: 0.72rem;
  line-height: 1.45;
  background: #1e1b4b;
  color: #e0e7ff;
  border-radius: 8px;
  overflow-x: auto;
}

.adm-nextbox__code + .adm-nextbox__code {
  margin-top: 0.5rem;
}

.adm-footer {
  padding-top: 0.5rem;
  padding-bottom: 1rem;
}

.adm-footer__link {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--adm-accent);
  text-decoration: none;
}

.adm-footer__link:hover {
  text-decoration: underline;
}
</style>
