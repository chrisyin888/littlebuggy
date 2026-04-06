<script setup>
defineProps({
  /** wave | think | help | peek | calm | cozy (extra friendliness for soft states) */
  pose: {
    type: String,
    default: 'calm',
    validator: (v) => ['wave', 'think', 'help', 'peek', 'calm', 'cozy'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['xs', 'sm', 'md', 'lg'].includes(v),
  },
})
</script>

<template>
  <div
    class="lb-mascot"
    :class="[`lb-mascot--${size}`, `lb-mascot--pose-${pose}`]"
    aria-hidden="true"
  >
    <svg class="lb-mascot__svg" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- soft ground shadow -->
      <ellipse cx="60" cy="108" rx="36" ry="8" fill="#3d3540" opacity="0.08" />

      <!-- antennae -->
      <path
        d="M48 28 Q42 12 36 8M72 28 Q78 12 84 8"
        stroke="#c4b5fd"
        stroke-width="3"
        stroke-linecap="round"
      />
      <circle cx="34" cy="7" r="4" fill="#fde047" stroke="#fff" stroke-width="2" />
      <circle cx="86" cy="7" r="4" fill="#fda4af" stroke="#fff" stroke-width="2" />

      <!-- body -->
      <ellipse cx="60" cy="72" rx="38" ry="34" fill="#ff9a7a" stroke="#e85d4c" stroke-width="3" />
      <ellipse cx="60" cy="72" rx="32" ry="28" fill="url(#lbBody)" opacity="0.45" />

      <!-- wing spots (friendly, not realistic) -->
      <circle cx="44" cy="68" r="7" fill="#fff" opacity="0.55" />
      <circle cx="76" cy="74" r="5.5" fill="#fff" opacity="0.45" />
      <circle cx="58" cy="84" r="4" fill="#fff" opacity="0.4" />

      <!-- head -->
      <circle cx="60" cy="38" r="22" fill="#ffcf6b" stroke="#f59e0b" stroke-width="2.5" />
      <path
        d="M42 32 Q60 24 78 32"
        stroke="#fbbf24"
        stroke-width="2"
        stroke-linecap="round"
        opacity="0.6"
      />

      <!-- eyes -->
      <ellipse cx="51" cy="38" rx="6" ry="7" fill="#fff" stroke="#3d3540" stroke-width="2" />
      <ellipse cx="69" cy="38" rx="6" ry="7" fill="#fff" stroke="#3d3540" stroke-width="2" />
      <circle cx="52" cy="39" r="3.2" fill="#3d3540" />
      <circle cx="70" cy="39" r="3.2" fill="#3d3540" />
      <circle cx="53.5" cy="36.5" r="1.2" fill="#fff" />
      <circle cx="71.5" cy="36.5" r="1.2" fill="#fff" />

      <!-- blush -->
      <ellipse cx="44" cy="44" rx="5" ry="3" fill="#fda4af" opacity="0.55" />
      <ellipse cx="76" cy="44" rx="5" ry="3" fill="#fda4af" opacity="0.55" />

      <!-- smile -->
      <path
        v-if="pose !== 'think' && pose !== 'cozy'"
        d="M50 48 Q60 56 70 48"
        stroke="#3d3540"
        stroke-width="2.2"
        stroke-linecap="round"
        fill="none"
      />
      <path
        v-else-if="pose === 'think'"
        d="M52 50 Q60 46 68 50"
        stroke="#3d3540"
        stroke-width="2"
        stroke-linecap="round"
        fill="none"
      />
      <path
        v-else
        d="M50 49 Q60 58 70 49"
        stroke="#3d3540"
        stroke-width="2.2"
        stroke-linecap="round"
        fill="none"
      />

      <!-- wave arm -->
      <g v-if="pose === 'wave'" class="lb-mascot__wave-arm">
        <path
          d="M88 62 Q108 48 112 32"
          stroke="#ff9a7a"
          stroke-width="5"
          stroke-linecap="round"
        />
        <circle cx="112" cy="28" r="8" fill="#ffcf6b" stroke="#fff" stroke-width="2" />
      </g>

      <!-- help hands -->
      <g v-if="pose === 'help'" opacity="0.95">
        <ellipse cx="28" cy="78" rx="10" ry="8" fill="#ffcf6b" stroke="#f59e0b" stroke-width="2" />
        <ellipse cx="92" cy="78" rx="10" ry="8" fill="#ffcf6b" stroke="#f59e0b" stroke-width="2" />
      </g>

      <!-- think bubble hint -->
      <g v-if="pose === 'think'" opacity="0.9">
        <circle cx="98" cy="22" r="6" fill="#e0f2fe" stroke="#7dd3fc" stroke-width="1.5" />
        <circle cx="108" cy="14" r="3.5" fill="#e0f2fe" stroke="#7dd3fc" stroke-width="1.2" />
      </g>

      <!-- peek: clip feel via translate in CSS -->
      <defs>
        <linearGradient id="lbBody" x1="30%" y1="0%" x2="70%" y2="100%">
          <stop offset="0%" stop-color="#fff" />
          <stop offset="100%" stop-color="#fb923c" stop-opacity="0" />
        </linearGradient>
      </defs>
    </svg>
    <span v-if="pose === 'calm' || pose === 'wave'" class="lb-mascot__spark lb-mascot__spark--a">✦</span>
    <span v-if="pose === 'wave'" class="lb-mascot__spark lb-mascot__spark--b">✦</span>
    <span v-if="pose === 'cozy'" class="lb-mascot__heart lb-mascot__heart--a" aria-hidden="true">♥</span>
    <span v-if="pose === 'cozy'" class="lb-mascot__heart lb-mascot__heart--b" aria-hidden="true">♥</span>
  </div>
</template>

<style scoped>
.lb-mascot {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  filter: drop-shadow(0 3px 6px rgba(255, 154, 122, 0.18));
}

.lb-mascot__svg {
  display: block;
  width: 100%;
  height: 100%;
}

.lb-mascot--xs {
  width: 2.35rem;
  height: 2.35rem;
}

.lb-mascot--sm {
  width: 3rem;
  height: 3rem;
}

.lb-mascot--md {
  width: 4.5rem;
  height: 4.5rem;
}

.lb-mascot--lg {
  width: 6.75rem;
  height: 6.75rem;
}

.lb-mascot--pose-peek {
  transform: translateX(12%);
}

.lb-mascot__wave-arm {
  animation: lb-wave 2.2s ease-in-out infinite;
  transform-origin: 88px 62px;
}

@keyframes lb-wave {
  0%,
  100% {
    transform: rotate(0deg);
  }
  40% {
    transform: rotate(14deg);
  }
  55% {
    transform: rotate(-6deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .lb-mascot__wave-arm {
    animation: none;
  }
}

.lb-mascot__spark {
  position: absolute;
  font-size: 0.65rem;
  color: #f59e0b;
  font-weight: 800;
  opacity: 0.85;
  pointer-events: none;
  text-shadow: 0 0 6px #fff;
}

.lb-mascot__spark--a {
  top: -2%;
  right: -4%;
  animation: lb-spark 3s ease-in-out infinite;
}

.lb-mascot__spark--b {
  bottom: 18%;
  right: -12%;
  font-size: 0.5rem;
  animation: lb-spark 2.4s ease-in-out infinite reverse;
}

@keyframes lb-spark {
  0%,
  100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

@media (prefers-reduced-motion: reduce) {
  .lb-mascot__spark {
    animation: none;
  }
}

.lb-mascot__heart {
  position: absolute;
  font-size: 0.55rem;
  color: #fb7185;
  font-weight: 800;
  pointer-events: none;
  text-shadow: 0 0 4px #fff;
  animation: lb-heart 2.8s ease-in-out infinite;
}

.lb-mascot__heart--a {
  top: 8%;
  right: -8%;
  animation-delay: 0s;
}

.lb-mascot__heart--b {
  bottom: 28%;
  left: -6%;
  font-size: 0.48rem;
  color: #f9a8d4;
  animation-delay: -1.2s;
}

@keyframes lb-heart {
  0%,
  100% {
    opacity: 0.55;
    transform: translateY(0) scale(1);
  }
  50% {
    opacity: 1;
    transform: translateY(-3px) scale(1.08);
  }
}

@media (prefers-reduced-motion: reduce) {
  .lb-mascot__heart {
    animation: none;
  }
}
</style>
