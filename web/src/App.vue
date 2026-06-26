<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import { useTraktData } from '@/composables/useTraktData'
import HeroIntro from '@/components/HeroIntro.vue'
import TotalStats from '@/components/TotalStats.vue'
import MonthlyJourney from '@/components/MonthlyJourney.vue'
import TopWatched from '@/components/TopWatched.vue'
import GenreSection from '@/components/GenreSection.vue'
import HeatmapSection from '@/components/HeatmapSection.vue'
import LibrarySection from '@/components/LibrarySection.vue'
import ClosingSection from '@/components/ClosingSection.vue'

const {
  summary, mediaList, topMedia, recentMeta, loading, error,
  mediaMap, lastUpdated, totalStats,
  monthlyStats, dailyGenreStats, genreStats,
} = useTraktData()

provide('summary', summary)
provide('mediaList', mediaList)
provide('topMedia', topMedia)
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

function handleScroll() {
  const scrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  scrollProgress.value = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0
  resizeCallbacks.value.forEach(fn => fn?.())
}

onMounted(() => window.addEventListener('scroll', handleScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))
</script>

<template>
  <div class="app">
    <div class="scroll-progress" :style="{ width: scrollProgress + '%' }" />

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
      </div>
    </template>

    <template v-else>
      <HeroIntro :media-list="mediaList" />
      <TotalStats />
      <MonthlyJourney />
      <TopWatched />
      <GenreSection />
      <HeatmapSection />
      <LibrarySection />
      <ClosingSection />
    </template>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; }
.scroll-progress {
  position: fixed; top: 0; left: 0; height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--accent-warm));
  z-index: 999; transition: width 0.1s ease;
}
.loading-screen {
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  background: #0d1117; color: var(--text-dim);
}
.loading-icon { font-size: 4rem; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
</style>
