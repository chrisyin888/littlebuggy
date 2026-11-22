<script setup>
/**
 * Site index — a compact directory of everything on LittleBuggy, placed
 * near the top of the homepage so parents can jump straight to a section
 * (in-page anchor) or page (route) in one tap. Deliberately hardcoded
 * English like CourseRegistrationGlance (owner order 2026-11-22): the
 * directory renders in English under every locale, and it doubles as the
 * mobile wayfinding fix — big tap targets, no menu to dig through.
 */
const ITEMS = [
  { icon: '🦠', label: 'Virus rankings — this week', href: '#weekly-snapshot', route: false },
  { icon: '🌡️', label: 'Weather & air quality', href: '#weather-air', route: false },
  { icon: '🏥', label: 'ER wait times', href: '#emergency-wait-times', route: false },
  { icon: '🚑', label: 'Urgent care (UPCC) waits', href: '#urgent-care-wait-times', route: false },
  { icon: '⏱️', label: 'All wait times — full page', href: '/wait-times', route: true },
  { icon: '📰', label: 'Daily updates', href: '#daily-news', route: false },
  { icon: '🏊', label: 'Swim lessons — all 15 cities', href: '/swim-lessons', route: true },
  { icon: '📅', label: 'Registration calendar', href: '/registration', route: true },
  { icon: '🤒', label: 'Fever guide', href: '/guides/fever', route: true },
  { icon: '💬', label: 'Parents board', href: '#parents-board', route: false },
  { icon: '✉️', label: 'Feedback', href: '#site-feedback', route: false },
  { icon: '🆘', label: 'When to seek help', href: '#littlebug-help', route: false },
]
</script>

<template>
  <nav class="site-index" aria-labelledby="site-index-title">
    <div class="site-index__inner">
      <h2 id="site-index-title" class="site-index__title">Everything on LittleBuggy</h2>
      <p class="site-index__hint">Tap a topic to jump straight to it.</p>
      <ul class="site-index__grid" role="list">
        <li v-for="item in ITEMS" :key="item.label" class="site-index__cell">
          <RouterLink v-if="item.route" :to="item.href" class="site-index__link">
            <span class="site-index__icon" aria-hidden="true">{{ item.icon }}</span>
            <span class="site-index__label">{{ item.label }}</span>
            <span class="site-index__arrow" aria-hidden="true">→</span>
          </RouterLink>
          <a v-else :href="item.href" class="site-index__link">
            <span class="site-index__icon" aria-hidden="true">{{ item.icon }}</span>
            <span class="site-index__label">{{ item.label }}</span>
            <span class="site-index__arrow" aria-hidden="true">→</span>
          </a>
        </li>
      </ul>
    </div>
  </nav>
</template>

<style scoped>
.site-index {
  padding: 0 clamp(1rem, 3vw, 1.5rem);
  margin: 0 auto clamp(1.25rem, 3.5vw, 2rem);
  max-width: var(--layout-max);
}

.site-index__inner {
  padding: clamp(1rem, 3vw, 1.4rem);
  border-radius: var(--radius-lg);
  background: rgba(255, 252, 247, 0.97);
  border: 3px solid rgba(186, 230, 253, 0.55);
  box-shadow: var(--shadow-soft);
}

.site-index__title {
  margin: 0 0 0.25rem;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-ink);
}

.site-index__hint {
  margin: 0 0 0.8rem;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--color-ink-muted);
}

.site-index__grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 0.55rem;
}

.site-index__link {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-height: 48px;
  padding: 0.55rem 0.8rem;
  border-radius: 12px;
  background: rgba(239, 246, 255, 0.9);
  border: 2px solid rgba(147, 197, 253, 0.5);
  color: var(--color-ink) !important;
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.3;
  text-decoration: none !important;
}

.site-index__link:hover {
  background: rgba(219, 234, 254, 0.95);
}

.site-index__icon {
  font-size: 1.15rem;
  flex: none;
}

.site-index__label {
  flex: 1;
}

.site-index__arrow {
  color: #0284c7;
  font-weight: 900;
  flex: none;
}

@media (max-width: 560px) {
  .site-index__grid {
    grid-template-columns: 1fr 1fr;
    gap: 0.45rem;
  }

  .site-index__link {
    font-size: 0.88rem;
    padding: 0.5rem 0.6rem;
    gap: 0.4rem;
  }
}
</style>
