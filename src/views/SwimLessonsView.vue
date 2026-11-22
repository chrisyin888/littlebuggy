<script setup>
/**
 * Swim Lessons Registration — municipal (city-run) swim lesson sign-up
 * dates, pools and official registration links for Metro Vancouver.
 * One table, one row per city: date, pools, status and the key rules are
 * all visible without clicking through. All dates verified against city
 * / recreation commission websites; cities that have not posted a date
 * say so instead of guessing. Information only — LittleBuggy does not
 * register anyone.
 */
import { onMounted } from 'vue'
import { SWIM_CITIES, SWIM_UPCOMING, SWIM_TABLE, SWIM_CHECKED_DATE } from '../data/swimLessons'

onMounted(() => {
  document.title =
    'Swim Lessons Registration in Metro Vancouver — Dates, Pools & Sign-Up Links | LittleBuggy'
  const desc = document.querySelector('meta[name="description"]')
  if (desc) {
    desc.setAttribute(
      'content',
      'When does swim lessons registration open in Vancouver, Burnaby, Surrey, Richmond, Delta, Coquitlam and the rest of Metro Vancouver? Verified city dates, pools, and official registration links — plus the account and waitlist steps to do before the day.',
    )
  }
})

const STATUS_LABELS = {
  dated: 'Date set',
  open: 'Open now',
  rolling: 'Rolling',
  tba: 'Not posted yet',
  none: 'No winter lessons',
}
</script>

<template>
  <article class="swim-page">
    <RouterLink class="swim-page__back" to="/">← Back to this week's snapshot</RouterLink>

    <h1 class="swim-page__title">Swim Lessons Registration in Metro Vancouver</h1>
    <p class="swim-page__meta">
      City-run swim lesson sign-up dates, pools and official registration links for 15
      Metro Vancouver cities · Checked against city websites {{ SWIM_CHECKED_DATE }}
    </p>
    <p class="swim-page__intro">
      Municipal swim lessons are the cheapest lessons around — and the fastest to fill. Every
      city's next registration date, pools, status and key rules are in the table below: one row
      per city, no clicking through. All dates come from official city websites; where a city has
      not posted a date, we say so instead of guessing.
    </p>

    <section class="swim-page__card swim-page__card--next" aria-label="Next registrations">
      <h2>⏰ Next registrations — in date order</h2>
      <div class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr><th scope="col">When</th><th scope="col">What opens</th><th scope="col"></th></tr>
          </thead>
          <tbody>
            <tr v-for="item in SWIM_UPCOMING" :key="item.label">
              <td class="tbl__when">{{ item.when }}</td>
              <td>{{ item.label }}</td>
              <td class="tbl__btn-cell">
                <a class="tbl__btn" :href="item.url" target="_blank" rel="noopener noreferrer">Register ↗</a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="swim-page__note">
        Port Coquitlam registration is already open, and Burnaby swim lessons use rolling
        registration (30 days before each class starts) — see the table below.
      </p>
    </section>

    <h2 class="swim-page__section-title">All 15 cities — one table</h2>
    <div class="tbl-wrap">
      <table class="tbl tbl--cities">
        <thead>
          <tr>
            <th scope="col">City</th>
            <th scope="col">Next registration</th>
            <th scope="col">Pools</th>
            <th scope="col">Status</th>
            <th scope="col">Good to know</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="city in SWIM_CITIES" :id="city.id" :key="city.id">
            <td class="tbl__city">{{ city.name }}</td>
            <td data-label="Next registration">
              <span v-for="line in SWIM_TABLE[city.id].dates" :key="line" class="tbl__line">{{ line }}</span>
              <span v-if="SWIM_TABLE[city.id].note" class="tbl__note">{{ SWIM_TABLE[city.id].note }}</span>
            </td>
            <td data-label="Pools">
              {{ city.pools.length ? city.pools.join(' · ') : '—' }}
              <span v-if="city.poolsNote" class="tbl__note">{{ city.poolsNote }}</span>
            </td>
            <td data-label="Status">
              <span class="badge" :data-status="city.status">{{ STATUS_LABELS[city.status] }}</span>
            </td>
            <td data-label="Good to know">
              <ul class="tbl__tips">
                <li v-for="tip in SWIM_TABLE[city.id].tips" :key="tip">{{ tip }}</li>
              </ul>
            </td>
            <td class="tbl__btn-cell">
              <a class="tbl__btn" :href="city.registerUrl" target="_blank" rel="noopener noreferrer">Register ↗</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <section class="swim-page__card" aria-label="Before registration day">
      <h2>Before registration day — the checklist that actually helps</h2>
      <ul>
        <li><strong>Create the account days early.</strong> Every city uses an online system (PerfectMind, ActiveNet / Active Communities, or vanrec). Some cities take days to approve new accounts or verify resident status — same-day sign-ups can miss the window entirely.</li>
        <li><strong>Add every child to the account, with birthdays.</strong> Age and level checks happen at checkout; fixing them mid-rush costs your spot.</li>
        <li><strong>Know your child's level.</strong> Most cities require the previous level on file. Report cards from another city can usually be dropped off or emailed in ahead of time.</li>
        <li><strong>Use the wish list / favourites feature</strong> where the system has one, so registration morning is just enrol → cart → pay.</li>
        <li><strong>Residents usually go first</strong> — by hours (North & West Vancouver), days (Coquitlam, Township of Langley) or a full week (Surrey aquatics, Delta). Check your city's row for its gap.</li>
        <li><strong>If your class is full, join the waitlist immediately.</strong> In Surrey, Vancouver and the Township of Langley, an emailed waitlist offer expires in 24–36 hours — watch your inbox and spam folder.</li>
        <li><strong>One set per swimmer.</strong> Most cities withdraw duplicate registrations, so pick the set you actually want.</li>
      </ul>
    </section>

    <section class="swim-page__sources" aria-label="Sources and about this page">
      <h2>About this page &amp; sources</h2>
      <p>
        LittleBuggy is an information page for families — we do not run lessons and cannot register
        your child or hold a spot. Dates and rules above come from the official city pages listed
        below, checked {{ SWIM_CHECKED_DATE }}; cities change dates (Richmond's winter
        registration night was already postponed once), so confirm on the official site before
        registration day. Spots are never guaranteed — the checklist above is built only from the
        cities' own published rules.
      </p>
      <ul class="swim-page__source-list">
        <li v-for="city in SWIM_CITIES" :key="city.id">
          {{ city.name }} —
          <a :href="city.sourceUrl" target="_blank" rel="noopener noreferrer">{{ city.sourceName }}</a>
        </li>
      </ul>
      <p>
        Looking for a different program? See the
        <RouterLink to="/registration">recreation registration calendar</RouterLink> for skating
        lessons, holiday camps, gymnastics, preschool and lifeguard courses.
      </p>
    </section>
  </article>
</template>

<style scoped>
.swim-page {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.swim-page__back {
  font-weight: 700;
  color: var(--color-ink-muted);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.swim-page__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 4.5vw, 2.4rem);
  font-weight: 700;
  line-height: 1.15;
  color: var(--color-ink);
}

.swim-page__meta {
  margin: -0.6rem 0 0;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.swim-page__intro {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.65;
  color: var(--color-ink-muted);
}

.swim-page__card {
  padding: clamp(1.1rem, 3vw, 1.6rem);
  border-radius: var(--radius-lg);
  background: rgba(255, 252, 247, 0.97);
  border: 3px solid rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-soft);
}

.swim-page__card--next {
  background: linear-gradient(140deg, #eff6ff, #dbeafe);
  border-color: rgba(59, 130, 246, 0.45);
}

.swim-page__card h2 {
  margin: 0 0 0.7rem;
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-ink);
}

.swim-page__card ul {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.swim-page__card li {
  margin-bottom: 0.4rem;
}

.swim-page__note {
  margin: 0.8rem 0 0;
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.swim-page__section-title {
  margin: 0.4rem 0 -0.4rem;
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 700;
  color: var(--color-ink);
}

/* ——— Tables ——— */
.tbl-wrap {
  overflow-x: auto;
  border-radius: 12px;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.92);
  font-size: 0.9rem;
}

.tbl th,
.tbl td {
  text-align: left;
  padding: 0.55rem 0.65rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
  vertical-align: top;
  font-weight: 600;
  color: var(--color-ink-muted);
  line-height: 1.45;
}

.tbl th {
  background: rgba(219, 234, 254, 0.85);
  color: var(--color-ink);
  font-weight: 800;
  white-space: nowrap;
}

.tbl--cities {
  min-width: 880px;
  border: 3px solid rgba(186, 230, 253, 0.55);
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
}

.tbl__when {
  white-space: nowrap;
  font-weight: 800 !important;
  color: var(--color-ink) !important;
}

.tbl__city {
  font-weight: 800 !important;
  color: var(--color-ink) !important;
  white-space: nowrap;
}

.tbl__line {
  display: block;
  margin-bottom: 0.25rem;
}

.tbl__note {
  display: block;
  margin-top: 0.3rem;
  font-size: 0.82rem;
  color: var(--color-ink-soft);
}

.tbl__tips {
  margin: 0;
  padding-left: 1.05rem;
}

.tbl__tips li {
  margin-bottom: 0.25rem;
}

.tbl__btn-cell {
  white-space: nowrap;
}

.tbl__btn {
  display: inline-block;
  padding: 0.38rem 0.8rem;
  border-radius: 999px;
  background: #0284c7;
  color: #fff !important;
  font-size: 0.82rem;
  font-weight: 800;
  text-decoration: none !important;
  white-space: nowrap;
}

.badge {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  padding: 0.22rem 0.6rem;
  border-radius: 999px;
  background: #e0f2fe;
  color: #075985;
  white-space: nowrap;
}

.badge[data-status='open'] {
  background: #dcfce7;
  color: #166534;
}

.badge[data-status='none'],
.badge[data-status='tba'] {
  background: #f1f5f9;
  color: #475569;
}

.swim-page__sources h2 {
  margin: 0 0 0.6rem;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--color-ink);
}

.swim-page__sources p {
  margin: 0 0 0.7rem;
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.swim-page__sources a {
  color: #0369a1;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.swim-page__source-list {
  margin: 0 0 0.7rem;
  padding-left: 1.2rem;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

/* ——— Mobile (≤700px): wide tables become stacked cards ———
   One card per city, every cell labelled, no sideways scrolling and
   nothing to pinch-zoom. The "next registrations" table keeps its
   3-column shape but lets the date wrap and gives the button room. */
@media (max-width: 700px) {
  .tbl {
    font-size: 0.92rem;
  }

  .tbl__btn {
    display: inline-flex;
    align-items: center;
    min-height: 40px;
    padding: 0.45rem 1rem;
    font-size: 0.88rem;
  }

  .tbl__when {
    white-space: normal;
  }

  .tbl--cities {
    min-width: 0;
    border: none;
    box-shadow: none;
    background: transparent;
  }

  .tbl--cities thead {
    display: none;
  }

  .tbl--cities tbody,
  .tbl--cities tr,
  .tbl--cities td {
    display: block;
    width: auto;
  }

  .tbl--cities tr {
    background: rgba(255, 255, 255, 0.95);
    border: 3px solid rgba(186, 230, 253, 0.55);
    border-radius: 12px;
    box-shadow: var(--shadow-soft);
    padding: 0.7rem 0.85rem 0.85rem;
    margin-bottom: 0.9rem;
  }

  .tbl--cities td {
    border-bottom: none;
    padding: 0.28rem 0;
  }

  .tbl--cities td[data-label]::before {
    content: attr(data-label);
    display: block;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--color-ink-soft);
    margin-bottom: 0.12rem;
  }

  .tbl--cities .tbl__city {
    font-size: 1.12rem;
    padding-bottom: 0.35rem;
  }

  .tbl--cities .tbl__btn-cell {
    padding-top: 0.55rem;
  }
}
</style>
