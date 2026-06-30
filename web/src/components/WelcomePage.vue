<script setup>
import { computed, onMounted, ref, onUnmounted } from 'vue'

const props = defineProps({
  mediaList: { type: Array, default: () => [] },
})
const emit = defineEmits(['start'])

const year = new Date().getFullYear()
const showContent = ref(false)
const currentBgIdx = ref(0)

const backdrops = computed(() => {
  return props.mediaList
    .filter(m => m.backdrop_url)
    .slice(0, 6)
    .map(m => m.backdrop_url)
})

const titleChars = '你的年度观影宇宙'.split('')

let bgTimer = null

onMounted(() => {
  setTimeout(() => showContent.value = true, 200)
  if (backdrops.value.length > 1) {
    bgTimer = setInterval(() => {
      currentBgIdx.value = (currentBgIdx.value + 1) % backdrops.value.length
    }, 8000)
  }
})

onUnmounted(() => {
  if (bgTimer) clearInterval(bgTimer)
})
</script>

<template>
  <section class="welcome-section">
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

    <div class="welcome-content" :class="{ show: showContent }">
      <div class="welcome-brand">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <line x1="2" y1="8" x2="22" y2="8" />
          <path d="M10 12 L15 15 L10 18 Z" fill="currentColor" stroke="none" />
        </svg>
        <span>traktDaily</span>
      </div>

      <h1 class="welcome-title">
        <span
          v-for="(ch, i) in titleChars"
          :key="i"
          class="title-char"
          :style="{ animationDelay: (0.3 + i * 0.06) + 's' }"
        >{{ ch }}</span>
      </h1>

      <div class="welcome-line" />
      <p class="welcome-subtitle">{{ year }} 年度观影报告</p>
      <p class="welcome-desc">每一帧光影，都是你的故事</p>

      <button class="start-btn" @click="emit('start')">
        <span>开启年度回顾</span>
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
          <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <div class="welcome-footer">Powered by Trakt</div>
  </section>
</template>

<style scoped>
.welcome-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; text-align: center;
  background: var(--bg);
}

.backdrop-carousel { position: absolute; inset: 0; }
.backdrop-slide {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  opacity: 0; transition: opacity 2s ease;
}
.backdrop-slide.active { opacity: 1; }

.backdrop-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(14,16,20,0.7) 0%, rgba(14,16,20,0.55) 50%, rgba(14,16,20,0.85) 100%);
}

.welcome-content {
  position: relative; z-index: 1;
  opacity: 0; transform: translateY(12px);
  transition: opacity 0.8s ease, transform 0.8s ease;
}
.welcome-content.show { opacity: 1; transform: translateY(0); }

.welcome-brand {
  display: inline-flex; align-items: center; gap: 8px;
  margin-bottom: 32px; color: var(--primary);
  opacity: 0.7; font-size: 0.8rem; font-weight: 600; letter-spacing: 2px;
}

.welcome-title {
  font-size: clamp(2.2rem, 7vw, 3.5rem);
  font-weight: 800; color: var(--text-1);
  margin-bottom: 16px; letter-spacing: 4px; line-height: 1.2;
}
.title-char {
  display: inline-block; opacity: 0; transform: translateY(12px);
  animation: char-in 0.5s ease forwards;
}
@keyframes char-in {
  to { opacity: 1; transform: translateY(0); }
}

.welcome-line {
  width: 40px; height: 1px;
  background: var(--primary);
  margin: 0 auto 20px; opacity: 0.6;
}

.welcome-subtitle {
  font-size: 1.05rem; color: var(--primary-bright);
  margin-bottom: 8px; font-weight: 600; letter-spacing: 2px;
}
.welcome-desc {
  font-size: 0.9rem; color: var(--text-3);
  margin-bottom: 40px; letter-spacing: 1px;
}

.start-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 32px; border-radius: var(--radius);
  background: rgba(134, 168, 156, 0.1);
  border: 1px solid rgba(134, 168, 156, 0.2);
  color: var(--primary-bright); font-size: 0.95rem; font-weight: 600;
  cursor: pointer; transition: all var(--transition);
  letter-spacing: 2px;
}
.start-btn:hover {
  background: rgba(134, 168, 156, 0.15);
  border-color: rgba(134, 168, 156, 0.35);
  transform: translateY(-2px);
}
.start-btn:active { transform: translateY(0); }

.welcome-footer {
  position: absolute; bottom: 28px; left: 50%; transform: translateX(-50%);
  z-index: 1; font-size: 0.75rem; color: var(--text-dim); letter-spacing: 1px;
}
</style>
