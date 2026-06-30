<script setup>
import { computed, onMounted, ref } from 'vue'
import ParticleBg from '@/components/ParticleBg.vue'

const props = defineProps({
  mediaList: { type: Array, default: () => [] },
})
const emit = defineEmits(['start'])

const year = new Date().getFullYear()
const showContent = ref(false)

const backdropUrl = computed(() => {
  const item = props.mediaList.find(m => m.backdrop_url)
  return item?.backdrop_url || ''
})

const titleChars = '你的年度观影宇宙'.split('')

onMounted(() => {
  setTimeout(() => showContent.value = true, 300)
})
</script>

<template>
  <section class="welcome-section" :style="backdropUrl ? { backgroundImage: `linear-gradient(135deg, rgba(10,12,15,0.92), rgba(10,12,15,0.75)), url(${backdropUrl})` } : {}">
    <ParticleBg :density="80" />

    <div class="welcome-content" :class="{ show: showContent }">
      <div class="welcome-icon">🎬</div>

      <h1 class="welcome-title">
        <span
          v-for="(ch, i) in titleChars"
          :key="i"
          class="title-char"
          :style="{ animationDelay: (0.5 + i * 0.08) + 's' }"
        >{{ ch }}</span>
      </h1>

      <div class="welcome-line" />
      <p class="welcome-subtitle">{{ year }} 年度观影报告</p>
      <p class="welcome-desc">每一帧光影，都是你的故事</p>

      <button class="start-btn" @click="emit('start')">
        <span>开启年度回顾</span>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
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
  background: radial-gradient(ellipse at 50% 40%, #11151a 0%, var(--cinema-black) 70%);
  background-size: cover; background-position: center;
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

.welcome-icon {
  font-size: 3.5rem; margin-bottom: 20px;
  animation: float-slow 4s ease-in-out infinite;
}

.welcome-title {
  font-size: 3.2rem; font-weight: 900; color: var(--text-bright);
  margin-bottom: 12px; letter-spacing: 4px; line-height: 1.2;
}
.title-char {
  display: inline-block; opacity: 0; transform: translateY(20px);
  animation: fadeInUp 0.6s ease forwards;
}

.welcome-line {
  width: 50px; height: 2px; border-radius: 1px;
  background: linear-gradient(90deg, var(--bean-green), transparent);
  margin: 0 auto 20px;
}

.welcome-subtitle {
  font-size: 1.1rem; color: var(--bean-green-bright);
  margin-bottom: 8px; font-weight: 600; letter-spacing: 2px;
}
.welcome-desc {
  font-size: 0.92rem; color: var(--text-dim);
  margin-bottom: 40px; letter-spacing: 1px;
}

.start-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 36px; border-radius: 30px;
  background: linear-gradient(135deg, rgba(168,197,160,0.15), rgba(168,197,160,0.05));
  border: 1px solid rgba(168,197,160,0.3);
  color: var(--bean-green-bright); font-size: 1rem; font-weight: 600;
  cursor: pointer; transition: all var(--transition);
  animation: breathe 3s ease-in-out infinite;
  letter-spacing: 2px;
}
.start-btn:hover {
  background: linear-gradient(135deg, rgba(168,197,160,0.25), rgba(168,197,160,0.1));
  border-color: rgba(168,197,160,0.5);
  transform: scale(1.05);
}

.welcome-footer {
  position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%);
  z-index: 2; font-size: 0.75rem; color: var(--text-dim);
  letter-spacing: 1px;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 768px) {
  .welcome-title { font-size: 2.2rem; letter-spacing: 2px; }
  .welcome-icon { font-size: 2.5rem; }
}
</style>
