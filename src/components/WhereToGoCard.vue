<script setup>
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const erLines = () => {
  const v = tm('home.whereToGo.erLines')
  return Array.isArray(v) ? v : []
}
const upccLines = () => {
  const v = tm('home.whereToGo.upccLines')
  return Array.isArray(v) ? v : []
}
</script>

<template>
  <section class="where-to-go" aria-labelledby="where-to-go-title">
    <div class="where-to-go__inner">
      <h2 id="where-to-go-title" class="where-to-go__title">{{ t('home.whereToGo.title') }}</h2>
      <p class="where-to-go__lead">{{ t('home.whereToGo.lead') }}</p>
      <div class="where-to-go__grid">
        <div class="where-to-go__card where-to-go__card--er">
          <h3 class="where-to-go__card-title">{{ t('home.whereToGo.erTitle') }}</h3>
          <ul class="where-to-go__list">
            <li v-for="(line, i) in erLines()" :key="i">{{ line }}</li>
          </ul>
        </div>
        <div class="where-to-go__card where-to-go__card--upcc">
          <h3 class="where-to-go__card-title">{{ t('home.whereToGo.upccTitle') }}</h3>
          <ul class="where-to-go__list">
            <li v-for="(line, i) in upccLines()" :key="i">{{ line }}</li>
          </ul>
        </div>
      </div>
      <p class="where-to-go__foot">
        <a class="where-to-go__cta" href="#emergency-wait-times">{{ t('home.whereToGo.waitsCta') }}</a>
        <RouterLink class="where-to-go__guide" to="/guides/fever">{{ t('home.whereToGo.feverGuide') }}</RouterLink>
      </p>
      <p class="where-to-go__fineprint">{{ t('home.whereToGo.fineprint') }}</p>
    </div>
  </section>
</template>

<style scoped>
.where-to-go {
  margin: 0 auto clamp(1.5rem, 4vw, 2.5rem);
  padding: clamp(1.35rem, 3.5vw, 2rem) clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
  border-radius: var(--radius-lg);
  background: linear-gradient(145deg, rgba(255, 252, 247, 0.98), rgba(239, 246, 255, 0.9));
  border: 3px solid rgba(125, 211, 252, 0.5);
  box-shadow: var(--shadow-soft);
}

.where-to-go__inner {
  max-width: 920px;
  margin: 0 auto;
}

.where-to-go__title {
  margin: 0 0 0.4rem;
  font-family: var(--font-display);
  font-size: clamp(1.35rem, 3.2vw, 1.75rem);
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-ink);
}

.where-to-go__lead {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-soft);
}

.where-to-go__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.where-to-go__card {
  border-radius: var(--radius-lg);
  padding: 1rem 1.15rem;
  border: 2px solid transparent;
}

.where-to-go__card--er {
  background: #fef2f2;
  border-color: rgba(220, 38, 38, 0.35);
}

.where-to-go__card--upcc {
  background: #f0fdf4;
  border-color: rgba(22, 163, 74, 0.35);
}

.where-to-go__card-title {
  margin: 0 0 0.55rem;
  font-size: 1.02rem;
  font-weight: 800;
  color: var(--color-ink);
}

.where-to-go__list {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.55;
  color: var(--color-ink-muted);
}

.where-to-go__list li {
  margin-bottom: 0.3rem;
}

.where-to-go__foot {
  margin: 1.1rem 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem 1.25rem;
  align-items: center;
}

.where-to-go__cta {
  font-weight: 800;
  color: #0369a1;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.where-to-go__guide {
  font-weight: 800;
  color: #7c3aed;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.where-to-go__fineprint {
  margin: 0.7rem 0 0;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-ink-soft);
}
</style>
