<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Community board service (family-board on Render). The widget is vanilla JS:
// it boots the moment its script executes and scans the DOM for #family-board,
// so inside this SPA we inject the stylesheet + a fresh script element on
// mount — the container div below is already rendered by then. A fresh script
// element per mount also re-initialises the widget after client-side
// navigation back to this page (the old container is destroyed on unmount).
const BOARD_BASE = 'https://family-board-2q7q.onrender.com'

onMounted(() => {
  if (!document.querySelector('link[data-family-board-css]')) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = `${BOARD_BASE}/static/board-widget.css`
    link.setAttribute('data-family-board-css', '')
    document.head.appendChild(link)
  }
  const script = document.createElement('script')
  script.src = `${BOARD_BASE}/static/board-widget.js`
  script.defer = true
  document.body.appendChild(script)
})
</script>

<template>
  <section id="parents-board" class="parents-board" aria-labelledby="parents-board-title">
    <div class="parents-board__inner">
      <h2 id="parents-board-title" class="parents-board__title">{{ t('home.board.title') }}</h2>
      <p class="parents-board__notice" role="note">{{ t('home.board.notice') }}</p>
      <div id="family-board" data-site="littlebuggy" data-theme="light"></div>
    </div>
  </section>
</template>

<style scoped>
.parents-board {
  margin: 0 auto clamp(1.5rem, 4vw, 2.5rem);
  padding: clamp(1.35rem, 3.5vw, 2rem) clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
  border-radius: var(--radius-lg);
  background: linear-gradient(
    145deg,
    rgba(255, 252, 247, 0.98) 0%,
    rgba(253, 242, 248, 0.55) 48%,
    rgba(240, 249, 255, 0.95) 100%
  );
  border: 3px solid rgba(244, 114, 182, 0.35);
  box-shadow: var(--shadow-soft);
}

.parents-board__inner {
  max-width: 920px;
  margin: 0 auto;
}

.parents-board__title {
  margin: 0 0 0.45rem;
  font-family: var(--font-display);
  font-size: clamp(1.35rem, 3.2vw, 1.75rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.2;
  color: var(--color-ink);
}

.parents-board__notice {
  margin: 0 0 1rem;
  font-size: 0.85rem;
  line-height: 1.5;
  font-weight: 600;
  color: var(--color-ink-soft);
}
</style>
