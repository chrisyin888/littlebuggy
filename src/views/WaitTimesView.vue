<script setup>
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ErWaitTimesSection from '../components/ErWaitTimesSection.vue'
import UpccWaitTimesSection from '../components/UpccWaitTimesSection.vue'

const { t } = useI18n()
</script>

<template>
  <div class="wait-page-standalone">
    <RouterLink to="/" class="wait-page-standalone__back">{{ t('waitTimes.backHome') }}</RouterLink>
    <ErWaitTimesSection />
    <UpccWaitTimesSection />
  </div>
</template>

<style scoped>
.wait-page-standalone {
  max-width: var(--layout-max);
  margin: 0 auto;
}

.wait-page-standalone__back {
  display: inline-block;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-teal-dark);
  text-decoration: none;
  border-bottom: 2px dashed rgba(13, 155, 138, 0.35);
}

.wait-page-standalone__back:hover {
  border-bottom-color: var(--color-teal-dark);
}
</style>
