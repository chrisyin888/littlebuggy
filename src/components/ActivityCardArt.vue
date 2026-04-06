<script setup>
defineProps({
  name: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <!-- Compact playful SVGs — rounded, soft “app sticker” style -->
  <svg
    v-if="name === 'rsv'"
    class="art"
    viewBox="0 0 72 72"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <circle cx="36" cy="36" r="34" fill="#fff" opacity="0.55" />
    <path
      d="M36 14c-8 0-14 6-14 14 0 10 8 18 14 26 6-8 14-16 14-26 0-8-6-14-14-14z"
      fill="#99f6e4"
      stroke="#14b8a6"
      stroke-width="2"
      stroke-linejoin="round"
    />
    <path
      d="M28 34h16M32 28v12M40 28v12"
      stroke="#0f766e"
      stroke-width="2.2"
      stroke-linecap="round"
    />
    <circle cx="26" cy="22" r="3" fill="#fda4af" opacity="0.9" />
    <circle cx="48" cy="24" r="2.5" fill="#fda4af" opacity="0.85" />
  </svg>

  <svg
    v-else-if="name === 'flu'"
    class="art"
    viewBox="0 0 72 72"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <circle cx="36" cy="36" r="34" fill="#fff" opacity="0.5" />
    <rect x="22" y="18" width="28" height="38" rx="14" fill="#fee2e2" stroke="#f87171" stroke-width="2" />
    <circle cx="36" cy="52" r="7" fill="#fca5a5" stroke="#ef4444" stroke-width="1.5" />
    <rect x="33" y="26" width="6" height="14" rx="3" fill="#f97316" opacity="0.35" />
  </svg>

  <svg
    v-else-if="name === 'covid'"
    class="art"
    viewBox="0 0 72 72"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <circle cx="36" cy="36" r="34" fill="#fff" opacity="0.52" />
    <path
      d="M36 20c-6 0-11 5-11 11v10c0 6 5 11 11 11s11-5 11-11V31c0-6-5-11-11-11z"
      fill="#e9d5ff"
      stroke="#a78bfa"
      stroke-width="2"
      stroke-linejoin="round"
    />
    <path
      d="M28 34h16M32 28v12M40 28v12"
      stroke="#7c3aed"
      stroke-width="2"
      stroke-linecap="round"
      opacity="0.85"
    />
    <ellipse cx="36" cy="48" rx="10" ry="5" fill="#ddd6fe" stroke="#c4b5fd" stroke-width="1.5" />
  </svg>

  <svg
    v-else-if="name === 'cold'"
    class="art"
    viewBox="0 0 72 72"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <circle cx="36" cy="36" r="34" fill="#fff" opacity="0.55" />
    <rect x="18" y="22" width="36" height="32" rx="10" fill="#f8fafc" stroke="#94a3b8" stroke-width="2.2" />
    <circle cx="28" cy="36" r="3.5" fill="#3d3540" />
    <circle cx="44" cy="36" r="3.5" fill="#3d3540" />
    <path d="M30 44 Q36 49 42 44" stroke="#3d3540" stroke-width="2" stroke-linecap="round" fill="none" />
    <path d="M24 28h24M24 34h16" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round" opacity="0.7" />
    <path d="M46 48l8 12" stroke="#7dd3fc" stroke-width="3" stroke-linecap="round" />
  </svg>

  <svg
    v-else-if="name === 'stomach'"
    class="art"
    viewBox="0 0 72 72"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <circle cx="36" cy="36" r="34" fill="#fff" opacity="0.5" />
    <ellipse cx="36" cy="38" rx="22" ry="18" fill="#fef9c3" stroke="#eab308" stroke-width="2" />
    <path
      d="M28 36c4-6 12-6 16 0M30 42c3 4 10 4 12 0"
      stroke="#ca8a04"
      stroke-width="2"
      stroke-linecap="round"
    />
    <circle cx="36" cy="22" r="4" fill="#fde047" />
  </svg>

  <svg v-else class="art" viewBox="0 0 72 72" aria-hidden="true">
    <circle cx="36" cy="36" r="34" fill="#fff" opacity="0.5" />
    <circle cx="36" cy="36" r="18" fill="#e0f2fe" stroke="#38bdf8" stroke-width="2" />
  </svg>
</template>

<style scoped>
.art {
  width: 100%;
  height: 100%;
  display: block;
  filter: drop-shadow(0 2px 0 rgba(255, 255, 255, 0.85));
}
</style>
