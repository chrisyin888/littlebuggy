<script setup>
defineProps({
  id: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <!-- Soft “sticker icon” style — rounded, warm fills, consistent 28×28 frame -->
  <span class="symptom-mini" aria-hidden="true">
    <svg v-if="id === 'cough'" class="symptom-mini__svg" viewBox="0 0 28 28" fill="none">
      <circle cx="14" cy="14" r="13" fill="#fff5eb" stroke="#fdba74" stroke-width="1.6" />
      <ellipse cx="14" cy="15" rx="7" ry="5.5" fill="#ffedd5" stroke="#fb923c" stroke-width="1.2" />
      <path d="M9 15h10" stroke="#ea580c" stroke-width="1.8" stroke-linecap="round" />
      <circle cx="10" cy="11.5" r="1.8" fill="#3d3540" />
      <circle cx="18" cy="11.5" r="1.8" fill="#3d3540" />
      <circle cx="10.6" cy="10.8" r="0.55" fill="#fff" />
      <circle cx="18.6" cy="10.8" r="0.55" fill="#fff" />
      <path
        d="M6 19c1.5-2 4-2.2 5.5-1M16.5 18c1.5-.8 4 0 5.5 2"
        stroke="#93c5fd"
        stroke-width="1.3"
        stroke-linecap="round"
        opacity="0.85"
      />
    </svg>
    <svg v-else-if="id === 'fever'" class="symptom-mini__svg" viewBox="0 0 28 28" fill="none">
      <circle cx="14" cy="14" r="13" fill="#fff1f2" stroke="#fda4af" stroke-width="1.6" />
      <path
        d="M14 5.5v2.2a2.8 2.8 0 00-1.8 2.6v6.8a3.6 3.6 0 107.2 0v-6.8a2.8 2.8 0 00-1.8-2.6V5.5"
        fill="#fecdd3"
        stroke="#f43f5e"
        stroke-width="1.3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle cx="14" cy="16.2" r="2" fill="#fb7185" />
      <path
        d="M14 3.5l.6 1.8h1.9l-1.5 1.1.6 1.8-1.6-1.1-1.6 1.1.6-1.8-1.5-1.1h1.9z"
        fill="#fde047"
        stroke="#eab308"
        stroke-width="0.6"
      />
    </svg>
    <svg v-else-if="id === 'sneeze'" class="symptom-mini__svg" viewBox="0 0 28 28" fill="none">
      <circle cx="14" cy="14" r="13" fill="#ecfeff" stroke="#67e8f9" stroke-width="1.6" />
      <circle cx="14" cy="14" r="7.5" fill="#cffafe" stroke="#22d3ee" stroke-width="1.2" />
      <circle cx="11" cy="13" r="1.5" fill="#3d3540" />
      <circle cx="17" cy="13" r="1.5" fill="#3d3540" />
      <ellipse cx="14" cy="16.5" rx="2.5" ry="1.8" fill="#fda4af" opacity="0.65" />
      <path
        d="M4 9l-1.2-1.2M24 9l1.2-1.2M7 5.5L5.8 4.2M21 5.5l1.2-1.3"
        stroke="#7dd3fc"
        stroke-width="1.2"
        stroke-linecap="round"
      />
    </svg>
    <svg v-else-if="id === 'stomach'" class="symptom-mini__svg" viewBox="0 0 28 28" fill="none">
      <circle cx="14" cy="14" r="13" fill="#fefce8" stroke="#fde047" stroke-width="1.6" />
      <ellipse cx="14" cy="15" rx="9" ry="7" fill="#fef9c3" stroke="#eab308" stroke-width="1.2" />
      <path
        d="M9 14.5c2 2 8 2 10 0"
        stroke="#ca8a04"
        stroke-width="1.3"
        stroke-linecap="round"
      />
      <circle cx="14" cy="7.5" r="2.2" fill="#fde047" stroke="#f59e0b" stroke-width="0.8" />
    </svg>
    <svg v-else-if="id === 'nose'" class="symptom-mini__svg" viewBox="0 0 28 28" fill="none">
      <circle cx="14" cy="14" r="13" fill="#f0fdf4" stroke="#86efac" stroke-width="1.6" />
      <ellipse cx="14" cy="13" rx="5.5" ry="7" fill="#dcfce7" stroke="#4ade80" stroke-width="1.2" />
      <ellipse cx="12" cy="12" rx="1.2" ry="1.6" fill="#3d3540" opacity="0.7" />
      <ellipse cx="16" cy="12" rx="1.2" ry="1.6" fill="#3d3540" opacity="0.7" />
      <path d="M11 17h6" stroke="#22c55e" stroke-width="1.5" stroke-linecap="round" />
      <circle cx="8" cy="9" r="1" fill="#bfdbfe" opacity="0.9" />
      <circle cx="20" cy="9" r="1" fill="#bfdbfe" opacity="0.9" />
    </svg>
  </span>
</template>

<style scoped>
.symptom-mini {
  display: inline-flex;
  width: 1.5rem;
  height: 1.5rem;
  flex-shrink: 0;
}

.symptom-mini__svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 1px 0 rgba(255, 255, 255, 0.9));
}
</style>
