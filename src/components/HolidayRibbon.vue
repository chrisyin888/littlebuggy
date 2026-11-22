<script setup>
/**
 * Seasonal Christmas dressing (added 2026-11-18, owner order).
 * Two variants:
 *  - "bar"  : slim festive ribbon across the very top of every page (App.vue).
 *  - "pill" : small "Happy Holidays" accent pill for the homepage hero (HomeView.vue).
 * To revert the whole seasonal look, remove this component and its two usages
 * (App.vue top stack, HomeView hero) in a single commit.
 */
defineProps({
  variant: { type: String, default: 'bar' }, // 'bar' | 'pill'
})
</script>

<template>
  <div v-if="variant === 'bar'" class="holiday-ribbon" role="note">
    <span class="holiday-ribbon__text">🎄 Merry Christmas — from LittleBuggy</span>
  </div>
  <p v-else class="holiday-pill">
    <span class="holiday-pill__flake" aria-hidden="true">❄</span>
    <span class="holiday-pill__text">Happy Holidays</span>
    <span class="holiday-pill__flake" aria-hidden="true">❄</span>
  </p>
</template>

<style scoped>
.holiday-ribbon {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem clamp(1rem, 4vw, 2rem);
  background: linear-gradient(92deg, #14532d 0%, #166534 55%, #14532d 100%);
  border-bottom: 2px solid rgba(251, 191, 36, 0.55);
  text-align: center;
}

.holiday-ribbon__text {
  font-size: clamp(0.8rem, 2.4vw, 0.92rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.4;
  color: #fef3c7;
}

.holiday-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin: 0 0 0.85rem;
  padding: 0.32rem 0.85rem;
  border-radius: 999px;
  border: 1.5px solid rgba(20, 83, 45, 0.4);
  background: rgba(20, 83, 45, 0.08);
  color: #14532d;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  line-height: 1.3;
}

.holiday-pill__flake {
  color: #b91c1c;
  font-size: 0.85rem;
  line-height: 1;
}
</style>
