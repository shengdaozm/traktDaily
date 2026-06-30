<script setup>
import { computed, onMounted, ref, onUnmounted } from 'vue'
import ParticleBg from '@/components/ParticleBg.vue'
import FloatingLights from '@/components/FloatingLights.vue'

const props = defineProps({
  mediaList: { type: Array, default: () => [] },
})
const emit = defineEmits(['start'])

const year = new Date().getFullYear()
const showContent = ref(false)
const burstParticles = ref([])
const buttonRef = ref(null)
const currentBgIdx = ref(0)

const backdrops = computed(() => {
  return props.mediaList
    .filter(m => m.backdrop_url)
    .slice(0, 8)
    .map(m => m.backdrop_url)
})

const titleChars = '你的年度观影宇宙'.split('')

let bgTimer = null

function startBgRotation() {
  if (backdrops.value.length <= 1) return
  bgTimer = setInterval(() => {
    currentBgIdx.value = (currentBgIdx.value + 1) % backdrops.value.length
  }, 6000)
}

function triggerBurst(e) {
  const rect = buttonRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  const particles = []
  for (let i = 0; i < 20; i++) {
    const angle = (Math.PI * 2 * i) / 20
    const dist = 60 + Math.random() * 80
    particles.push({
      id: Date.now() + i,
      bx: Math.cos(angle) * dist + 'px',
      by: Math.sin(angle) * dist + 'px',
      delay: i * 0.01 + 's',
    })
  }
  burstParticles.value = particles
  setTimeout(() => { burstParticles.value = [] }, 1000)
  setTimeout(() => emit('start'), 400)
}

onMounted(() => {
  setTimeout(() => showContent.value = true, 300)
  startBgRotation()
})

onUnmounted(() => {
  if (bgTimer) clearInterval(bgTimer)
})
</script>

<template>
  <section class="welcome-section">
    <!-- 轮播剧照背景 -->
    <div class="backdrop-carousel" v-if="backdrops.length">
      <div
        v-for="(url, i) in backdrops"
        :key="i"
        class="backdrop-slide"
        :class="{ active: currentBgIdx === i }"
        :style="{ backgroundImage: `url(${url})` }"
      />
    </div>
    <div class="backdrop-overlay" />

    <ParticleBg :density="80" :speed="0.3" />
    <FloatingLights :count="3" />

    <div class="welcome-content" :class="{ show: showContent }">
      <div class="welcome-brand">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <line x1="2" y1="8" x2="22" y2="8" />
          <circle cx="6" cy="6" r="0.5" fill="currentColor" />
          <circle cx="8" cy="6" r="0.5" fill="currentColor" />
          <path d="M10 12 L15 15 L10 18 Z" fill="currentColor" stroke="none" />
        </svg>
        <span class="brand-text">traktDaily</span>
      </div>

      <h1 class="welcome-title">
        <span
          v-for="(ch, i) in titleChars"
          :key="i"
          class="title-char shimmer-text"
          :style="{ animationDelay: (0.5 + i * 0.08) + 's' }"
        >{{ ch }}</span>
      </h1>

      <div class="welcome-line" />
      <p class="welcome-subtitle">{{ year }} 年度观影报告</p>
      <p class="welcome-desc">每一帧光影，都是你的故事</p>

      <div class="btn-wrapper">
        <div
          v-for="p in burstParticles"
          :key="p.id"
          class="burst-particle"
          :style="{ '--bx': p.bx, '--by': p.by, animationDelay: p.delay }"
        />
        <button ref="buttonRef" class="start-btn" @click="triggerBurst">
          <span class="btn-text">开启年度回顾</span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="welcome-footer">
      <span>Powered by Trakt</span>
    </div>
  </section>
</template>

<style scoped>
.welcome-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; text-align: center;
  background: var(--cinema-black);
}

/* 轮播剧照背景 */
.backdrop-carousel {
  position: absolute; inset: 0; z-index: 0;
}
.backdrop-slide {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  opacity: 0; transition: opacity 2s ease-in-out;
  animation: ken-burns 12s ease-in-out infinite alternate;
}
.backdrop-slide.active { opacity: 1; }

@keyframes ken-burns {
  0% { transform: scale(1.0) translateX(0); }
  100% { transform: scale(1.12) translateX(-2%); }
}

.backdrop-overlay {
  position: absolute; inset: 0; z-index: 1;
  background: linear-gradient(180deg,
    rgba(10,12,15,0.75) 0%,
    rgba(10,12,15,0.6) 40%,
    rgba(10,12,15,0.85) 100%);
}
.welcome-section::after {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(ellipse 50% 40% at 50% 40%, rgba(168,197,160,0.08) 0%, transparent 70%);
  pointer-events: none; z-index: 1;
}

.welcome-content {
  position: relative; z-index: 2;
  opacity: 0; transform: translateY(20px);
  transition: opacity 1s ease, transform 1s ease;
}
.welcome-content.show { opacity: 1; transform: translateY(0); }

.welcome-brand {
  display: inline-flex; align-items: center; gap: 8px;
  margin-bottom: 28px; color: var(--bean-green);
  opacity: 0.8;
}
.brand-text {
  font-size: 0.85rem; font-weight: 600; letter-spacing: 2px;
  text-transform: uppercase;
}

.welcome-title {
  font-size: 3.2rem; font-weight: 900; color: var(--text-bright);
  margin-bottom: 12px; letter-spacing: 4px; line-height: 1.2;
}
.title-char {
  display: inline-block; opacity: 0; transform: translateY(20px) scale(0.5);
  animation: char-drop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  text-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
@keyframes char-drop {
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.welcome-line {
  width: 50px; height: 2px; border-radius: 1px;
  background: linear-gradient(90deg, var(--bean-green), transparent);
  margin: 0 auto 20px;
  animation: line-expand 1s ease 1s both;
}
@keyframes line-expand {
  from { width: 0; }
  to { width: 50px; }
}

.welcome-subtitle {
  font-size: 1.1rem; color: var(--bean-green-bright);
  margin-bottom: 8px; font-weight: 600; letter-spacing: 2px;
  text-shadow: 0 1px 10px rgba(0,0,0,0.5);
}
.welcome-desc {
  font-size: 0.92rem; color: var(--text-dim);
  margin-bottom: 40px; letter-spacing: 1px;
  text-shadow: 0 1px 8px rgba(0,0,0,0.5);
}

.btn-wrapper { position: relative; display: inline-block; }
.start-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 36px; border-radius: 30px;
  background: linear-gradient(135deg, rgba(168,197,160,0.15), rgba(168,197,160,0.05));
  border: 1px solid rgba(168,197,160,0.3);
  color: var(--bean-green-bright); font-size: 1rem; font-weight: 600;
  cursor: pointer; transition: all var(--transition);
  animation: breathe 3s ease-in-out infinite;
  letter-spacing: 2px; position: relative; overflow: visible;
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
}
.start-btn::before {
  content: ''; position: absolute; inset: 0; border-radius: 30px;
  background: linear-gradient(135deg, rgba(168,197,160,0.2), transparent);
  opacity: 0; transition: opacity var(--transition);
}
.start-btn:hover {
  background: linear-gradient(135deg, rgba(168,197,160,0.25), rgba(168,197,160,0.1));
  border-color: rgba(168,197,160,0.6);
  transform: scale(1.05);
  box-shadow: 0 0 40px rgba(168,197,160,0.3), 0 0 80px rgba(168,197,160,0.1);
}
.start-btn:hover::before { opacity: 1; }
.start-btn:active { transform: scale(0.98); }

.burst-particle {
  position: absolute; top: 50%; left: 50%;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--bean-green-bright);
  box-shadow: 0 0 8px var(--bean-green);
  pointer-events: none;
  animation: burst-fly 0.8s ease-out forwards;
}
@keyframes burst-fly {
  0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 0; transform: translate(calc(-50% + var(--bx)), calc(-50% + var(--by))) scale(0); }
}

.welcome-footer {
  position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%);
  z-index: 2; font-size: 0.75rem; color: var(--text-dim);
  letter-spacing: 1px;
}

@media (max-width: 768px) {
  .welcome-title { font-size: 2.2rem; letter-spacing: 2px; }
}
</style>
