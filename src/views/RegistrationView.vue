<script setup>
/**
 * Recreation Registration Calendar — when municipal program registration
 * opens across Metro Vancouver: skating, camps, gymnastics, preschool
 * and lifeguard (Bronze) courses, with swim lessons summarized and
 * linked to the full swim page. All dates verified against official
 * city websites; unposted dates are labelled, never guessed.
 */
import { onMounted } from 'vue'
import {
  REG_CALENDAR,
  REG_OPEN_NOW,
  REG_SECTIONS,
  REG_SYSTEMS,
  REG_CHECKED_DATE,
} from '../data/registration'

onMounted(() => {
  document.title =
    'Recreation Registration Calendar — Skating, Camps, Gymnastics & Swim Lessons in Metro Vancouver | LittleBuggy'
  const desc = document.querySelector('meta[name="description"]')
  if (desc) {
    desc.setAttribute(
      'content',
      'Every Metro Vancouver city recreation registration date in one calendar: skating lessons, winter break & summer camps, gymnastics, preschool and Bronze lifeguard courses — verified against official city websites, with direct registration links.',
    )
  }
})
</script>

<template>
  <article class="reg-page">
    <RouterLink class="reg-page__back" to="/">← Back to this week's snapshot</RouterLink>

    <h1 class="reg-page__title">Recreation Registration Calendar: Metro Vancouver</h1>
    <p class="reg-page__meta">
      Skating lessons · holiday camps · gymnastics · preschool · lifeguard courses — every city's
      next registration date in one place · Checked against city websites {{ REG_CHECKED_DATE }}
    </p>
    <p class="reg-page__intro">
      Each city opens registration on its own day, in its own system, and the popular classes go in
      minutes. This calendar pulls the verified dates for 15 Metro Vancouver cities into one list —
      swim lessons have their own full page （游泳课单独一页）, and everything else is below. Dates come
      from official city pages; where a city has not posted a date, we say so instead of guessing.
    </p>

    <section class="reg-page__card reg-page__card--cal" aria-label="Registration calendar">
      <h2>📅 The calendar — every confirmed date, in order 各市报名日历</h2>
      <div class="reg-table-wrap">
        <table class="reg-table">
          <thead>
            <tr><th scope="col">When</th><th scope="col">What opens</th><th scope="col">Register</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in REG_CALENDAR" :key="row.when + row.what">
              <td class="reg-table__when">{{ row.when }}</td>
              <td>{{ row.what }}</td>
              <td>
                <a :href="REG_SYSTEMS[row.sys].url" target="_blank" rel="noopener noreferrer">
                  {{ REG_SYSTEMS[row.sys].label }} ↗
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <h3 class="reg-page__subhead">Already open now</h3>
      <ul>
        <li v-for="item in REG_OPEN_NOW" :key="item">{{ item }}</li>
      </ul>
    </section>

    <section class="reg-page__card reg-page__card--swim" aria-label="Swim lessons">
      <h2>🏊 Swim lessons 游泳课 — the full guide is its own page</h2>
      <p>
        Swim lessons are the most competitive registration of all, so they get a dedicated page:
        every city's date and time (Delta residents Nov 25, 9:00 am · Surrey aquatics Dec 13,
        9:00 pm · North Vancouver Dec 2, 7:00 am…), every pool, the official sign-up links, and
        each city's account, waiting-room and waitlist rules.
      </p>
      <p>
        <RouterLink class="reg-page__cta" to="/swim-lessons">Go to the swim lessons page →</RouterLink>
      </p>
    </section>

    <template v-for="section in REG_SECTIONS" :key="section.id">
      <h2 :id="section.id" class="reg-page__section-title">{{ section.title }} {{ section.titleZh }}</h2>
      <p class="reg-page__blurb">{{ section.blurb }}</p>
      <section
        v-for="entry in section.entries"
        :key="section.id + entry.city"
        class="reg-page__card reg-entry"
        :aria-label="entry.city"
      >
        <h3>{{ entry.city }}</h3>
        <p class="reg-entry__text">{{ entry.text }}</p>
        <p v-if="entry.venue && entry.venue !== '—'" class="reg-entry__venue">
          <strong>Where:</strong> {{ entry.venue }}
        </p>
        <p class="reg-entry__link">
          <a :href="REG_SYSTEMS[entry.sys].url" target="_blank" rel="noopener noreferrer">
            Register / check: {{ REG_SYSTEMS[entry.sys].label }} ↗
          </a>
        </p>
      </section>
    </template>

    <section class="reg-page__sources" aria-label="About this page">
      <h2>About this page</h2>
      <p>
        LittleBuggy is an information page for families — we do not run programs and cannot
        register your child or guarantee a spot. Dates and rules come from the official city
        websites, checked {{ REG_CHECKED_DATE }}; cities do change dates (Richmond's winter
        registration night was postponed this season), so confirm in the official system before
        your registration day. The universal rules still apply: create the account and add your
        children days early, know the level or category you need, and join the waitlist the moment
        a class shows full.
      </p>
    </section>
  </article>
</template>


<style scoped>
.reg-page {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.reg-page__back {
  font-weight: 700;
  color: var(--color-ink-muted);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.reg-page__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 4.5vw, 2.4rem);
  font-weight: 700;
  line-height: 1.15;
  color: var(--color-ink);
}

.reg-page__meta {
  margin: -0.6rem 0 0;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.reg-page__intro,
.reg-page__blurb {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.65;
  color: var(--color-ink-muted);
}

.reg-page__card {
  padding: clamp(1.1rem, 3vw, 1.6rem);
  border-radius: var(--radius-lg);
  background: rgba(255, 252, 247, 0.97);
  border: 3px solid rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-soft);
}

.reg-page__card--cal {
  background: linear-gradient(140deg, #eff6ff, #dbeafe);
  border-color: rgba(59, 130, 246, 0.45);
}

.reg-page__card--swim {
  background: linear-gradient(140deg, #f0fdfa, #ccfbf1);
  border-color: rgba(13, 148, 136, 0.4);
}

.reg-page__card h2 {
  margin: 0 0 0.7rem;
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-ink);
}

.reg-page__card p {
  margin: 0 0 0.6rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.reg-page__card ul {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.reg-page__card li {
  margin-bottom: 0.4rem;
}

.reg-page__card a,
.reg-page__sources a {
  color: #0369a1;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.reg-page__subhead {
  margin: 1.1rem 0 0.5rem;
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--color-ink);
}

.reg-table-wrap {
  overflow-x: auto;
}

.reg-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 10px;
  overflow: hidden;
  font-size: 0.9rem;
}

.reg-table th,
.reg-table td {
  text-align: left;
  padding: 0.5rem 0.65rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
  vertical-align: top;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.45;
}

.reg-table th {
  background: rgba(219, 234, 254, 0.8);
  color: var(--color-ink);
  font-weight: 800;
}

.reg-table__when {
  white-space: nowrap;
  font-weight: 800 !important;
  color: var(--color-ink) !important;
}

.reg-page__cta {
  display: inline-block;
  padding: 0.55rem 1.1rem;
  border-radius: 999px;
  background: #0f766e;
  color: #fff !important;
  font-weight: 800;
  text-decoration: none !important;
}

.reg-page__section-title {
  margin: 0.6rem 0 -0.5rem;
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 700;
  color: var(--color-ink);
}

.reg-entry h3 {
  margin: 0 0 0.5rem;
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-ink);
}

.reg-entry__text {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.reg-entry__venue {
  margin: 0.45rem 0 0;
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.reg-entry__link {
  margin: 0.6rem 0 0;
  font-size: 0.92rem;
}

.reg-entry__link a {
  color: #0369a1;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.reg-page__sources h2 {
  margin: 0 0 0.6rem;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--color-ink);
}

.reg-page__sources p {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}
</style>
