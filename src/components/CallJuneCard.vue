<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// June — LittleBuggy's Alebex phone assistant. Number provisioned 2026-11-12.
const JUNE_TEL_HREF = 'tel:+17787438889'
const JUNE_NUMBER_DISPLAY = '(778) 743-8889'
</script>

<template>
  <section class="call-june" aria-labelledby="call-june-title">
    <div class="call-june__inner">
      <img class="call-june__avatar" src="/images/june.jpg" alt="June, LittleBuggy's phone assistant" width="72" height="72" />
      <div class="call-june__body">
        <h2 id="call-june-title" class="call-june__title">{{ t('home.callJune.title') }}</h2>
        <p class="call-june__lead">{{ t('home.callJune.lead') }}</p>
        <p class="call-june__fineprint">{{ t('home.callJune.fineprint') }}</p>
      </div>
      <a class="call-june__cta" :href="JUNE_TEL_HREF">
        <span class="call-june__cta-label">{{ t('home.callJune.ctaLabel') }}</span>
        <span class="call-june__cta-number">{{ JUNE_NUMBER_DISPLAY }}</span>
      </a>
    </div>
  </section>
</template>

<style scoped>
.call-june {
  margin: 0 auto clamp(1.5rem, 4vw, 2.5rem);
  padding: clamp(1.2rem, 3vw, 1.6rem) clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
  border-radius: var(--radius-lg);
  background: linear-gradient(140deg, rgba(220, 252, 231, 0.9), rgba(224, 242, 254, 0.75));
  border: 3px solid rgba(74, 222, 128, 0.5);
  box-shadow: var(--shadow-soft);
}

.call-june__inner {
  max-width: 920px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1rem 1.25rem;
  flex-wrap: wrap;
}

.call-june__avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 3px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 8px rgba(21, 128, 61, 0.25);
}

.call-june__body {
  flex: 1 1 16rem;
  min-width: 0;
}

.call-june__title {
  margin: 0 0 0.3rem;
  font-family: var(--font-display);
  font-size: clamp(1.15rem, 2.8vw, 1.45rem);
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-ink);
}

.call-june__lead {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--color-ink-muted);
}

.call-june__fineprint {
  margin: 0.45rem 0 0;
  font-size: 0.76rem;
  line-height: 1.45;
  color: var(--color-ink-soft);
}

.call-june__cta {
  flex-shrink: 0;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  text-decoration: none;
  padding: 0.7rem 1.3rem;
  border-radius: var(--radius-pill);
  background: #16a34a;
  border: 2px solid #15803d;
  box-shadow: 2px 2px 0 rgba(21, 128, 61, 0.35);
}

.call-june__cta:hover {
  background: #15803d;
}

.call-june__cta-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.85);
}

.call-june__cta-number {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  line-height: 1.1;
  color: #fff;
  white-space: nowrap;
}

@media (max-width: 560px) {
  .call-june__cta {
    width: 100%;
  }
}
</style>
