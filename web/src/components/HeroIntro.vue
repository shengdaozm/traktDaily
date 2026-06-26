<script setup>
import { computed } from 'vue'

const props = defineProps({
  mediaList: { type: Array, default: () => [] },
})

const year = new Date().getFullYear()

const backdropUrl = computed(() => {
  const item = props.mediaList.find(m => m.backdrop_url)
  return item?.backdrop_url || ''
})
</script>

<template>
  <section class="hero-section" :style="backdropUrl ? { backgroundImage: `linear-gradient(135deg, rgba(13,17,23,0.85), rgba(13,17,23,0.7)), url(${backdropUrl})` } : {}">
    <div class="hero-content">
      <div class="hero-year">{{ year }}</div>
      <div class="hero-line"></div>
      <h1 class="hero-title">我的观影报告</h1>
      <p class="hero-subtitle">这一年，光影陪伴的每一刻</p>
      <div class="hero-badge">🎬 traktDaily</div>
    </div>
    <div class="scroll-hint">
      <span>向下滑动</span>
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M5 8L10 13L15 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
  </section>
</template>

<style scoped>
.hero-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; text-align: center;
  background: linear-gradient(135deg, #0d1117, #1a2e1a);
  background-size: cover; background-position: center;
}
.hero-section::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(ellipse 60% 50% at 50% 40%, rgba(88,166,255,0.1) 0%, transparent 70%);
  pointer-events: none;
}
.hero-content {
  position: relative; z-index: 1;
  animation: fadeIn 1.2s ease both;
}
.hero-year {
  font-size: 6rem; font-weight: 900;
  background: linear-gradient(135deg, #58a6ff, #8b5cf6, #f0c040);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1; margin-bottom: 6px;
  letter-spacing: -3px;
}
.hero-line {
  width: 60px; height: 3px; border-radius: 2px;
  background: linear-gradient(90deg, var(--accent), transparent);
  margin: 0 auto 24px;
}
.hero-title {
  font-size: 2rem; font-weight: 700; color: var(--text-bright);
  margin-bottom: 8px; letter-spacing: 2px;
}
.hero-subtitle {
  font-size: 1rem; color: var(--text-dim); margin-bottom: 32px;
}
.hero-badge {
  display: inline-block; padding: 6px 16px; border-radius: 20px;
  background: rgba(255,255,255,0.05); border: 1px solid var(--border);
  font-size: 0.82rem; color: var(--text-dim);
}
.scroll-hint {
  position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
  color: var(--text-dim); font-size: 0.78rem;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  animation: bounce 2s ease-in-out infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateX(-50%) translateY(0); opacity: 0.4; }
  50% { transform: translateX(-50%) translateY(8px); opacity: 0.9; }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 768px) {
  .hero-year { font-size: 4.5rem; }
  .hero-title { font-size: 1.5rem; }
}
</style>
