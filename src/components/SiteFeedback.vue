<script setup>
import { onMounted } from 'vue'

// Feedback box served by the same family-board service as ParentsBoard.
// Same injection pattern: the vanilla widget boots the moment its script
// executes and scans the DOM for .family-feedback, so inside this SPA we
// inject the stylesheet + a fresh script element on mount — the container
// div below is already rendered by then. Feedback is a private suggestion
// box (what families want / what to improve); submissions are never shown
// on the page and no contact details are collected.
const BOARD_BASE = 'https://family-board-2q7q.onrender.com'

onMounted(() => {
  if (!document.querySelector('link[data-family-feedback-css]')) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = `${BOARD_BASE}/static/feedback-widget.css`
    link.setAttribute('data-family-feedback-css', '')
    document.head.appendChild(link)
  }
  const script = document.createElement('script')
  script.src = `${BOARD_BASE}/static/feedback-widget.js`
  script.defer = true
  document.body.appendChild(script)
})
</script>

<template>
  <section class="site-feedback" aria-label="Site feedback · 网站意见">
    <div class="family-feedback" data-site="littlebuggy" data-theme="light"></div>
  </section>
</template>

<style scoped>
.site-feedback {
  margin: 0 auto clamp(1.5rem, 4vw, 2.5rem);
  padding: 0 clamp(1rem, 3vw, 1.5rem);
  max-width: var(--layout-max);
}
</style>
