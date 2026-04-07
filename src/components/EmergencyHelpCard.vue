<script setup>
/**
 * BC-focused urgent / non-emergency lines. Copy is English-only for now (product request).
 */
const LINES = [
  { textBefore: 'Call ', tel: '911', telDisplay: '911', textAfter: ' for any medical emergency.' },
  {
    textBefore: 'For non-emergency health advice in BC, call ',
    tel: '811',
    telDisplay: '8-1-1',
    textAfter: '.',
  },
  {
    textBefore: 'Poison emergency: ',
    tel: '+18005678911',
    telDisplay: '1-800-567-8911',
    textAfter: '',
  },
]
</script>

<template>
  <section class="emergency-help" aria-labelledby="emergency-help-title">
    <div class="emergency-help__card">
      <div class="emergency-help__header">
        <span class="emergency-help__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M3 5.5C3 4.12 4.12 3 5.5 3h1.4c.63 0 1.2.38 1.45.97l1.2 2.9a1.5 1.5 0 01-.35 1.56l-1.02 1.02a12 12 0 006.36 6.36l1.02-1.02c.42-.42 1.08-.52 1.56-.35l2.9 1.2c.59.25.97.82.97 1.45V18.5c0 1.38-1.12 2.5-2.5 2.5C11.3 21 3 12.7 3 5.5z"
              stroke="currentColor"
              stroke-width="1.25"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <h2 id="emergency-help-title" class="emergency-help__title">Need urgent help?</h2>
      </div>

      <div class="emergency-help__body">
        <p v-for="(row, i) in LINES" :key="i" class="emergency-help__line">
          <template v-if="row.textBefore">{{ row.textBefore }}</template>
          <a class="emergency-help__tel" :href="`tel:${row.tel}`">{{ row.telDisplay }}</a>
          <template v-if="row.textAfter">{{ row.textAfter }}</template>
        </p>
        <p class="emergency-help__disclaimer">
          LittleBuggy shares general local health information and does not replace professional medical care.
        </p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.emergency-help {
  width: 100%;
}

.emergency-help__card {
  max-width: 32rem;
  margin: 0 auto 1.25rem;
  padding: 0.85rem 1rem 0.95rem;
  border-radius: var(--radius-sm, 24px);
  background: linear-gradient(165deg, rgba(255, 252, 248, 0.98) 0%, rgba(230, 250, 243, 0.55) 45%, rgba(237, 244, 255, 0.75) 100%);
  border: 1px solid rgba(186, 230, 253, 0.55);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 10px 28px rgba(61, 53, 64, 0.06),
    0 2px 8px rgba(125, 211, 252, 0.12);
}

.emergency-help__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.55rem;
}

.emergency-help__icon {
  display: flex;
  flex-shrink: 0;
  width: 1.85rem;
  height: 1.85rem;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #5ab0c9;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(186, 230, 253, 0.65);
}

.emergency-help__icon svg {
  width: 1.15rem;
  height: 1.15rem;
}

.emergency-help__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(0.95rem, 2.4vw, 1.05rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--color-ink);
}

.emergency-help__body {
  padding-left: 0.15rem;
}

@media (min-width: 480px) {
  .emergency-help__body {
    padding-left: 2.35rem;
  }
}

.emergency-help__line {
  margin: 0 0 0.4rem;
  font-size: clamp(0.8rem, 2.1vw, 0.88rem);
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-muted);
}

.emergency-help__line:last-of-type {
  margin-bottom: 0.5rem;
}

.emergency-help__tel {
  font-weight: 700;
  color: #2d8ba5;
  text-decoration: underline;
  text-decoration-color: rgba(45, 139, 165, 0.35);
  text-underline-offset: 0.12em;
}

.emergency-help__tel:hover {
  color: #237a92;
  text-decoration-color: rgba(35, 122, 146, 0.5);
}

.emergency-help__disclaimer {
  margin: 0;
  padding-top: 0.45rem;
  border-top: 1px dashed rgba(196, 181, 253, 0.35);
  font-size: clamp(0.72rem, 1.9vw, 0.78rem);
  font-weight: 600;
  line-height: 1.45;
  color: var(--color-ink-soft);
}
</style>
