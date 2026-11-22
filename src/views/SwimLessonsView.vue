<script setup>
/**
 * Swim Lessons Registration — municipal (city-run) swim lesson sign-up
 * dates, pools and official registration links for Metro Vancouver.
 * All dates verified against city / recreation commission websites;
 * cities that have not posted a date say so instead of guessing.
 * Information only — LittleBuggy does not register anyone.
 */
import { onMounted } from 'vue'
import { SWIM_CITIES, SWIM_UPCOMING, SWIM_CHECKED_DATE } from '../data/swimLessons'

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
  dated: 'Next round dated',
  open: 'Open now',
  rolling: 'Rolling registration',
  tba: 'Date not posted yet',
  none: 'No winter lessons',
}
</script>

<template>
  <article class="swim-page">
    <RouterLink class="swim-page__back" to="/">← Back to this week's snapshot</RouterLink>

    <h1 class="swim-page__title">Swim Lessons Registration in Metro Vancouver</h1>
    <p class="swim-page__meta">
      City-run （市政府） swim lesson sign-up dates, pools and official registration links for 15
      Metro Vancouver cities · Checked against city websites {{ SWIM_CHECKED_DATE }}
    </p>
    <p class="swim-page__intro">
      Municipal swim lessons are the cheapest lessons around — and the fastest to fill. In some
      cities the whole season can sell out the night registration opens. This page puts every
      city's next registration date, its pools, and the official sign-up link in one place, so you
      can get your account ready before the rush. 所有日期均来自各市政府官网，官网没公布的我们如实标注，不猜。
    </p>

    <section class="swim-page__card swim-page__card--next" aria-label="Next registrations">
      <h2>⏰ Next registrations — mark your calendar 最近要抢的几场</h2>
      <ul class="swim-page__next-list">
        <li v-for="item in SWIM_UPCOMING" :key="item.label">
          <strong>{{ item.when }}</strong>
          <span> — {{ item.label }} · </span>
          <a :href="'#' + item.cityAnchor">details ↓</a>
          <span> · </span>
          <a :href="item.url" target="_blank" rel="noopener noreferrer">official registration site ↗</a>
        </li>
      </ul>
      <p class="swim-page__note">
        Port Coquitlam registration is already open, and Burnaby swim lessons use rolling
        registration (30 days before each class starts) — see their cards below.
      </p>
    </section>

    <section class="swim-page__card" aria-label="Before registration day">
      <h2>Before registration day — the checklist that actually helps</h2>
      <ul>
        <li><strong>Create the account days early.</strong> Every city uses an online system (PerfectMind, ActiveNet / Active Communities, or vanrec). Some cities take days to approve new accounts or verify resident status — same-day sign-ups can miss the window entirely.</li>
        <li><strong>Add every child to the account, with birthdays.</strong> Age and level checks happen at checkout; fixing them mid-rush costs your spot.</li>
        <li><strong>Know your child's level.</strong> Most cities require the previous level on file. Report cards from another city can usually be dropped off or emailed in ahead of time.</li>
        <li><strong>Use the wish list / favourites feature</strong> where the system has one, so registration morning is just enrol → cart → pay.</li>
        <li><strong>Residents usually go first</strong> — by hours (North & West Vancouver), days (Coquitlam, Township of Langley) or a full week (Surrey aquatics, Delta). Check your city's card for its gap.</li>
        <li><strong>If your class is full, join the waitlist immediately.</strong> In Surrey, Vancouver and the Township of Langley, an emailed waitlist offer expires in 24–36 hours — watch your inbox and spam folder.</li>
        <li><strong>One set per swimmer.</strong> Most cities withdraw duplicate registrations, so pick the set you actually want.</li>
      </ul>
    </section>

    <h2 class="swim-page__section-title">Every city, in detail 各市详情</h2>

    <section
      v-for="city in SWIM_CITIES"
      :id="city.id"
      :key="city.id"
      class="swim-page__card swim-city"
      :aria-label="city.name"
    >
      <div class="swim-city__head">
        <h3>{{ city.name }} <span class="swim-city__zh">{{ city.nameZh }}</span></h3>
        <span class="swim-city__badge" :data-status="city.status">{{ STATUS_LABELS[city.status] }}</span>
      </div>

      <p class="swim-city__next"><strong>Next registration:</strong> {{ city.next }}</p>

      <p v-if="city.pools.length" class="swim-city__pools">
        <strong>Pools:</strong> {{ city.pools.join(' · ') }}
      </p>
      <p v-if="city.poolsNote" class="swim-city__note">{{ city.poolsNote }}</p>

      <ul class="swim-city__tips">
        <li v-for="tip in city.tips" :key="tip">{{ tip }}</li>
      </ul>

      <p class="swim-city__actions">
        <a class="swim-city__cta" :href="city.registerUrl" target="_blank" rel="noopener noreferrer">
          {{ city.registerLabel }} ↗
        </a>
        <span class="swim-city__source">
          Source: <a :href="city.sourceUrl" target="_blank" rel="noopener noreferrer">{{ city.sourceName }}</a>
        </span>
      </p>
    </section>

    <section class="swim-page__sources" aria-label="About this page">
      <h2>About this page</h2>
      <p>
        LittleBuggy is an information page for families — we do not run lessons and cannot register
        your child or hold a spot. Dates and rules above come from the official city pages linked
        on each card, checked {{ SWIM_CHECKED_DATE }}; cities change dates (Richmond's winter
        registration night was already postponed once), so confirm on the official site before
        registration day. Spots are never guaranteed — the checklist above is built only from the
        cities' own published rules.
      </p>
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
  max-width: 860px;
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

.swim-page__card a,
.swim-page__sources a {
  color: #0369a1;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.swim-page__next-list li {
  margin-bottom: 0.55rem;
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

.swim-city__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.swim-city__head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-ink);
}

.swim-city__zh {
  font-size: 0.95rem;
  color: var(--color-ink-soft);
}

.swim-city__badge {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  padding: 0.22rem 0.6rem;
  border-radius: 999px;
  background: #e0f2fe;
  color: #075985;
}

.swim-city__badge[data-status='open'] {
  background: #dcfce7;
  color: #166534;
}

.swim-city__badge[data-status='none'],
.swim-city__badge[data-status='tba'] {
  background: #f1f5f9;
  color: #475569;
}

.swim-city__next {
  margin: 0.7rem 0 0;
  font-size: 0.97rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink);
}

.swim-city__pools {
  margin: 0.55rem 0 0;
  font-size: 0.94rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.swim-city__note {
  margin: 0.35rem 0 0;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-soft);
}

.swim-city__tips {
  margin: 0.7rem 0 0;
  padding-left: 1.2rem;
  font-size: 0.93rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.swim-city__tips li {
  margin-bottom: 0.35rem;
}

.swim-city__actions {
  margin: 1rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.swim-city__cta {
  align-self: flex-start;
  padding: 0.55rem 1.1rem;
  border-radius: 999px;
  background: #0284c7;
  color: #fff !important;
  font-weight: 800;
  text-decoration: none !important;
}

.swim-city__source {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-ink-soft);
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
</style>
