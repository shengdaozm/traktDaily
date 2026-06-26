<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import { useTraktData } from '@/composables/useTraktData'
import HeroIntro from '@/components/HeroIntro.vue'
import TotalStats from '@/components/TotalStats.vue'
import PersonaSection from '@/components/PersonaSection.vue'
import MonthlyJourney from '@/components/MonthlyJourney.vue'
import TopWatched from '@/components/TopWatched.vue'
import GenreSection from '@/components/GenreSection.vue'
import HeatmapSection from '@/components/HeatmapSection.vue'
import LibrarySection from '@/components/LibrarySection.vue'
import ClosingSection from '@/components/ClosingSection.vue'

const {
  summary, mediaList, topMedia, persona, recentMeta, loading, error,
  mediaMap, lastUpdated, totalStats,
  monthlyStats, dailyGenreStats, genreStats,
} = useTraktData()

provide('summary', summary)
provide('mediaList', mediaList)
provide('topMedia', topMedia)
provide('persona', persona)
provide('mediaMap', mediaMap)
provide('totalStats', totalStats)
provide('monthlyStats', monthlyStats)
provide('dailyGenreStats', dailyGenreStats)
provide('genreStats', genreStats)

const resizeCallbacks = ref([])
function registerResize(fn) { resizeCallbacks.value.push(fn) }
function unregisterResize(fn) {
  const i = resizeCallbacks.value.indexOf(fn)
  if (i >= 0) resizeCallbacks.value.splice(i, 1)
}
provide('registerResize', registerResize)
provide('unregisterResize', unregisterResize)

const scrollProgress = ref(0)
const activeSection = ref(0)
const sections = [
  { id: 'hero', label: '封面' },
  { id: 'stats', label: '总览' },
  { id: 'persona', label: '画像' },
  { id: 'monthly', label: '月度' },
  { id: 'top', label: '排行' },
  { id: 'genre', label: '类型' },
  { id: 'heatmap', label: '日历' },
  { id: 'library', label: '剧库' },
  { id: 'closing', label: '总结' },
]

function handleScroll() {
  const scrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  scrollProgress.value = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0

  const winH = window.innerHeight
  let bestIdx = 0
  let bestDist = Infinity
  sections.forEach((_, i) => {
    const el = document.getElementById(`section-${i}`)
    if (!el) return
    const rect = el.getBoundingClientRect()
    const dist = Math.abs(rect.top)
    if (dist < bestDist) { bestDist = dist; bestIdx = i }
  })
  activeSection.value = bestIdx

  resizeCallbacks.value.forEach(fn => fn?.())
}

function scrollToSection(idx) {
  const el = document.getElementById(`section-${idx}`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(() => window.addEventListener('scroll', handleScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))
</script>

<template>
  <div class="app">
    <div class="scroll-progress" :style="{ width: scrollProgress + '%' }" />

    <nav class="nav-dots" v-if="!loading && !error">
      <button
        v-for="(s, i) in sections" :key="i"
        class="nav-dot" :class="{ active: activeSection === i }"
        :title="s.label"
        @click="scrollToSection(i)"
      />
    </nav>

    <template v-if="loading">
      <div class="loading-screen">
        <div class="loading-icon">🎬</div>
        <p>正在生成你的观影报告...</p>
      </div>
    </template>

    <template v-else-if="error">
      <div class="loading-screen">
        <div class="loading-icon">⚠️</div>
        <p>数据加载失败</p>
        <p class="error-detail" v-if="error">{{ error.message || error }}</p>
      </div>
    </template>

    <template v-else>
      <div :id="`section-0`"><HeroIntro :media-list="mediaList" /></div>
      <div :id="`section-1`"><TotalStats /></div>
      <div :id="`section-2`"><PersonaSection /></div>
      <div :id="`section-3`"><MonthlyJourney /></div>
      <div :id="`section-4`"><TopWatched /></div>
      <div :id="`section-5`"><GenreSection /></div>
      <div :id="`section-6`"><HeatmapSection /></div>
      <div :id="`section-7`"><LibrarySection /></div>
      <div :id="`section-8`"><ClosingSection /></div>
    </template>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; }
.scroll-progress {
  position: fixed; top: 0; left: 0; height: 2px;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--accent-warm));
  z-index: 999; transition: width 0.05s linear;
}
.loading-screen {
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  background: #0d1117; color: var(--text-dim);
}
.loading-icon { font-size: 4rem; animation: pulse 1.5s ease-in-out infinite; }
.error-detail {
  font-size: 0.85rem; color: var(--text-dim); max-width: 400px;
  text-align: center; word-break: break-all; margin-top: 8px;
}
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
</style>
