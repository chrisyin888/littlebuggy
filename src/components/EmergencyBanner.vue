<script setup>
/**
 * Red-line safety banner — sits above all data sections on the home page.
 * English only, regardless of UI locale (owner order 2026-11-22: no Chinese
 * copy in this banner — the 8-1-1 line itself offers interpreters).
 */
</script>

<template>
  <section class="emergency-banner" role="alert" aria-label="Emergency help">
    <p class="emergency-banner__line">
      <strong>Emergency? Call <a href="tel:911">911</a>.</strong>
      Not sure where to go? Call
      <a href="tel:811">8-1-1 (HealthLink BC)</a> — free nurse advice, interpreters available.
    </p>
  </section>
</template>

<style scoped>
.emergency-banner {
  margin: 0 auto clamp(1.25rem, 3.5vw, 2rem);
  padding: clamp(0.85rem, 2.5vw, 1.1rem) clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
  border-radius: var(--radius-lg);
  background: linear-gradient(140deg, #fef2f2 0%, #fee2e2 55%, #fecaca 100%);
  border: 3px solid #dc2626;
  box-shadow: 0 8px 24px rgba(220, 38, 38, 0.16);
  text-align: center;
}

.emergency-banner__line {
  margin: 0;
  font-size: clamp(0.95rem, 2.6vw, 1.08rem);
  font-weight: 700;
  line-height: 1.5;
  color: #7f1d1d;
}

.emergency-banner a {
  color: #b91c1c;
  font-weight: 900;
  text-decoration: underline;
  text-underline-offset: 3px;
  white-space: nowrap;
}

.emergency-banner a:hover {
  color: #7f1d1d;
}
</style>
