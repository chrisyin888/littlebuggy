<script setup>
/**
 * Fever in Children: What to Do by Age — a standing guide page.
 * General information only, structured the way the playbook recommends:
 * takeaway card first, then red flags by age band, home care basics,
 * local resources (8-1-1 / ER), and first-hand sources with a date.
 * No individual dosing, no diagnosis. Under 3 months = seek care now.
 */
const LAST_UPDATED = 'November 14, 2026'

const SOURCES = [
  {
    name: 'HealthLink BC — Fever or Chills, Age 11 and Younger',
    url: 'https://www.healthlinkbc.ca/healthwise/fever-or-chills-age-11-and-younger',
  },
  {
    name: 'AboutKidsHealth (SickKids) — Fever',
    url: 'https://www.aboutkidshealth.ca/fever',
  },
  {
    name: 'Caring for Kids (Canadian Paediatric Society) — Fever and your child',
    url: 'https://caringforkids.cps.ca/handouts/health-conditions-and-treatments/fever_and_your_child',
  },
  {
    name: 'BC Children\'s Hospital — Emergency Department wait times',
    url: 'https://www.bcchildrens.ca',
  },
]
</script>

<template>
  <article class="fever-guide">
    <RouterLink class="fever-guide__back" to="/">← Back to this week's snapshot</RouterLink>

    <h1 class="fever-guide__title">Fever in Children: What to Do by Age</h1>
    <p class="fever-guide__meta">A general guide for Metro Vancouver families · Updated {{ LAST_UPDATED }}</p>

    <section class="fever-guide__card fever-guide__card--takeaway" aria-label="The short version">
      <h2>The short version</h2>
      <ul>
        <li><strong>Under 3 months old:</strong> any fever of 38.0 °C (100.4 °F) or higher means <strong>seek medical care right away</strong> — go to emergency or call 911.</li>
        <li><strong>How your child looks and acts matters more than the number.</strong> A child who drinks, plays between fever spikes, and responds to you is usually less worrying than the thermometer suggests.</li>
        <li><strong>Fever itself is not dangerous</strong> — it is the body's normal response to infection. What matters is the cause, your child's age, and the warning signs below.</li>
        <li><strong>Not sure?</strong> Call <a href="tel:811">8-1-1 (HealthLink BC)</a> — free nurse advice, 24/7, interpreters available.</li>
      </ul>
    </section>

    <section class="fever-guide__card fever-guide__card--red" aria-label="Red flags by age">
      <h2>Red flags — get help now, by age</h2>

      <h3>0–3 months</h3>
      <ul>
        <li>Temperature 38.0 °C (100.4 °F) or higher — <strong>always seek care immediately</strong>, even if your baby otherwise looks well.</li>
        <li>Hard to wake, very floppy, or a weak/high-pitched cry.</li>
        <li>Not feeding, or far fewer wet diapers than usual.</li>
      </ul>

      <h3>3–12 months</h3>
      <ul>
        <li>Fever that lasts more than 24–48 hours, or keeps coming back.</li>
        <li>Breathing that looks hard: ribs showing with each breath, flaring nostrils, blue lips.</li>
        <li>Signs of dehydration: dry mouth, no tears, no wet diaper for 8+ hours.</li>
        <li>Unusually sleepy, irritable in a way you can't settle, or a rash that doesn't fade when pressed.</li>
      </ul>

      <h3>Over 1 year</h3>
      <ul>
        <li>Fever lasting more than 3 days, or a new fever after it had gone away.</li>
        <li>Trouble breathing, severe headache, stiff neck, confusion, or a seizure.</li>
        <li>Not drinking, vomiting nonstop, or severe belly pain.</li>
        <li>Your gut says something is wrong — trust it and get checked.</li>
      </ul>
      <p class="fever-guide__call">
        For any emergency sign — hard breathing, blue lips, unresponsive, seizure — call
        <a href="tel:911"><strong>911</strong></a> or go to the nearest emergency department.
      </p>
    </section>

    <section class="fever-guide__card" aria-label="Home care basics">
      <h2>At home: general care basics</h2>
      <ul>
        <li>Offer fluids often, in small amounts — water, breast milk, formula, or an oral rehydration drink. Wet diapers / regular peeing is the sign it's working.</li>
        <li>Dress your child lightly and keep the room comfortable; heavy blankets and bundling can push the temperature up.</li>
        <li>Rest is fine and normal. You don't need to wake a sleeping child just to re-check the temperature unless a clinician told you to.</li>
        <li>Fever medicines (acetaminophen / ibuprofen) are dosed <strong>by weight</strong>, and the right product and amount depend on your child — follow the package directions or the official guidance linked below, or ask a pharmacist or 8-1-1. We don't give individual doses here.</li>
        <li>Never give aspirin to children or teens.</li>
        <li>Skip cold baths and alcohol rubs — they don't help and can cause shivering, which raises temperature.</li>
      </ul>
    </section>

    <section class="fever-guide__card" aria-label="Local resources">
      <h2>Where to get help in BC</h2>
      <ul>
        <li><strong>Emergency:</strong> call <a href="tel:911">911</a> or go to the nearest emergency department.</li>
        <li><strong>Not sure where to go:</strong> call <a href="tel:811">8-1-1 (HealthLink BC)</a> — nurses 24/7, interpreters in 130+ languages.</li>
        <li><strong>Urgent but not an emergency:</strong> an Urgent and Primary Care Centre (UPCC) — check the wait times on our <RouterLink to="/wait-times">wait times page</RouterLink> and on the home page before you head out.</li>
        <li><strong>Poison questions:</strong> BC Drug and Poison Information Centre, <a href="tel:+18005678911">1-800-567-8911</a>.</li>
      </ul>
    </section>

    <section class="fever-guide__sources" aria-label="Sources">
      <h2>Sources</h2>
      <ul>
        <li v-for="s in SOURCES" :key="s.url">
          <a :href="s.url" target="_blank" rel="noopener noreferrer">{{ s.name }}</a>
        </li>
      </ul>
      <p class="fever-guide__disclaimer">
        LittleBuggy shares general information for families and does not replace professional
        medical care. This page is not a diagnosis and does not judge your child's situation —
        if you are worried, call 8-1-1, your clinician, or 911. Guide last updated {{ LAST_UPDATED }}.
      </p>
    </section>
  </article>
</template>

<style scoped>
.fever-guide {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.fever-guide__back {
  font-weight: 700;
  color: var(--color-ink-muted);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.fever-guide__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 4.5vw, 2.4rem);
  font-weight: 700;
  line-height: 1.15;
  color: var(--color-ink);
}

.fever-guide__meta {
  margin: -0.6rem 0 0;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-ink-soft);
}

.fever-guide__card {
  padding: clamp(1.1rem, 3vw, 1.6rem);
  border-radius: var(--radius-lg);
  background: rgba(255, 252, 247, 0.97);
  border: 3px solid rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-soft);
}

.fever-guide__card--takeaway {
  background: linear-gradient(140deg, #fffbeb, #fef3c7);
  border-color: rgba(245, 158, 11, 0.5);
}

.fever-guide__card--red {
  background: #fef2f2;
  border-color: rgba(220, 38, 38, 0.4);
}

.fever-guide__card h2 {
  margin: 0 0 0.7rem;
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-ink);
}

.fever-guide__card h3 {
  margin: 1rem 0 0.4rem;
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--color-ink);
}

.fever-guide__card ul {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--color-ink-muted);
}

.fever-guide__card li {
  margin-bottom: 0.4rem;
}

.fever-guide__card a,
.fever-guide__sources a {
  color: #0369a1;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.fever-guide__call {
  margin: 1rem 0 0;
  font-weight: 700;
  line-height: 1.55;
  color: #7f1d1d;
}

.fever-guide__sources h2 {
  margin: 0 0 0.6rem;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--color-ink);
}

.fever-guide__sources ul {
  margin: 0 0 0.9rem;
  padding-left: 1.2rem;
  line-height: 1.6;
  font-size: 0.92rem;
  font-weight: 600;
}

.fever-guide__disclaimer {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-soft);
}
</style>
