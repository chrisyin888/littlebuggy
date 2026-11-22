<script setup>
/**
 * Course Registration at a Glance — homepage section.
 * Every Metro Vancouver city's next swim-lessons registration date,
 * plus the next few openings across all recreation programs, in one
 * compact table on the homepage itself — the same "see it at a glance"
 * treatment as the ER wait times. All copy is hardcoded English on
 * purpose: this section renders in English under every locale.
 * Dates are taken verbatim from the verified course data files
 * (src/data/swimLessons.js, src/data/registration.js) — never retyped.
 */
import { SWIM_CITIES, SWIM_TABLE, SWIM_CHECKED_DATE } from '../data/swimLessons'
import { REG_CALENDAR } from '../data/registration'

const STATUS_LABELS = {
  dated: 'Date set',
  open: 'Open now',
  rolling: 'Rolling',
  tba: 'Not posted yet',
  none: 'No winter lessons',
}

// Soonest first: already open, then dated rounds in chronological
// order, then rolling / not-posted / no-winter-lessons cities.
const SWIM_ORDER = [
  'port-coquitlam',
  'coquitlam',
  'delta',
  'richmond',
  'new-westminster',
  'north-vancouver',
  'west-vancouver',
  'township-of-langley',
  'surrey',
  'maple-ridge',
  'burnaby',
  'vancouver',
  'port-moody',
  'langley-city',
  'white-rock',
]

const cityById = Object.fromEntries(SWIM_CITIES.map((c) => [c.id, c]))

const swimRows = SWIM_ORDER.map((id) => {
  const city = cityById[id]
  return {
    id,
    city: city.name,
    when: SWIM_TABLE[id].dates[0],
    where: city.pools.length
      ? city.pools[0] + (city.pools.length > 1 ? ` +${city.pools.length - 1} more` : '')
      : '—',
    status: city.status,
  }
})

const soonRows = REG_CALENDAR.slice(0, 8)
</script>

<template>
  <section class="course-glance" aria-labelledby="course-glance-title">
    <div class="course-glance__inner">
      <h2 id="course-glance-title" class="course-glance__title">
        🏊 City swim lessons &amp; program registration
      </h2>
      <p class="course-glance__intro">
        Every city's next registration date, right here on one list — which city, which
        course, when it opens and where. Checked against city websites {{ SWIM_CHECKED_DATE }}.
      </p>

      <h3 class="course-glance__subhead">Swim lessons — all 15 cities, soonest first</h3>
      <div class="course-glance__tbl-wrap">
        <table class="course-glance__tbl">
          <thead>
            <tr>
              <th scope="col">City</th>
              <th scope="col">Course</th>
              <th scope="col">Registration opens</th>
              <th scope="col">Where</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in swimRows" :key="row.id">
              <td class="course-glance__city">{{ row.city }}</td>
              <td>Swim lessons</td>
              <td>{{ row.when }}</td>
              <td>{{ row.where }}</td>
              <td>
                <span class="course-glance__badge" :data-status="row.status">
                  {{ STATUS_LABELS[row.status] }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3 class="course-glance__subhead">Also opening soon — skating, camps, gymnastics &amp; more</h3>
      <div class="course-glance__tbl-wrap">
        <table class="course-glance__tbl">
          <thead>
            <tr>
              <th scope="col">When</th>
              <th scope="col">What opens</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in soonRows" :key="row.when + row.what">
              <td class="course-glance__when">{{ row.when }}</td>
              <td>{{ row.what }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="course-glance__more">
        Full list:
        <RouterLink to="/swim-lessons">swim lessons — dates, pools &amp; sign-up links</RouterLink>
        ·
        <RouterLink to="/registration">full registration calendar</RouterLink>
      </p>
    </div>
  </section>
</template>

<style scoped>
.course-glance {
  padding: 1.1rem 1.25rem 0.2rem;
}

.course-glance__inner {
  max-width: min(1120px, 100%);
  margin: 0 auto;
  padding: clamp(1rem, 3vw, 1.5rem);
  border-radius: var(--radius-lg, 16px);
  background: linear-gradient(140deg, #eff6ff, #dbeafe);
  border: 3px solid rgba(59, 130, 246, 0.4);
  box-shadow: var(--shadow-soft);
}

.course-glance__title {
  margin: 0 0 0.5rem;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-ink);
}

.course-glance__intro {
  margin: 0 0 0.4rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.course-glance__subhead {
  margin: 1rem 0 0.45rem;
  font-size: 1rem;
  font-weight: 800;
  color: var(--color-ink);
}

.course-glance__tbl-wrap {
  overflow-x: auto;
  border-radius: 12px;
}

.course-glance__tbl {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.94);
  font-size: 0.88rem;
}

.course-glance__tbl th,
.course-glance__tbl td {
  text-align: left;
  padding: 0.45rem 0.6rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
  vertical-align: top;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.4;
}

.course-glance__tbl th {
  background: rgba(219, 234, 254, 0.85);
  color: var(--color-ink);
  font-weight: 800;
  white-space: nowrap;
}

.course-glance__city {
  font-weight: 800 !important;
  color: var(--color-ink) !important;
  white-space: nowrap;
}

.course-glance__when {
  white-space: nowrap;
  font-weight: 800 !important;
  color: var(--color-ink) !important;
}

.course-glance__badge {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: #e0f2fe;
  color: #075985;
  white-space: nowrap;
}

.course-glance__badge[data-status='open'] {
  background: #dcfce7;
  color: #166534;
}

.course-glance__badge[data-status='none'],
.course-glance__badge[data-status='tba'] {
  background: #f1f5f9;
  color: #475569;
}

.course-glance__more {
  margin: 0.9rem 0 0;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.course-glance__more a {
  color: #0369a1;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}
</style>
