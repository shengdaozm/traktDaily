<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import { useTraktData } from '@/composables/useTraktData'
import WelcomePage from '@/components/WelcomePage.vue'
import OpeningNarrative from '@/components/OpeningNarrative.vue'
import CoreOverview from '@/components/CoreOverview.vue'
import PreferenceSection from '@/components/PreferenceSection.vue'
import BehaviorHabits from '@/components/BehaviorHabits.vue'
import PersonaProfile from '@/components/PersonaProfile.vue'
import AnnualRankings from '@/components/AnnualRankings.vue'
import SharePoster from '@/components/SharePoster.vue'
import YearArchive from '@/components/YearArchive.vue'

const {
  summary, mediaList, topMedia, persona, recentMeta, loading, error,
  mediaMap, lastUpdated, totalStats,
  monthlyStats, dailyGenreStats, genreStats,
  hourlyStats, weekdayStats, bingeStats, ratingPreference,
  countryStats, freshnessStats, watchPattern, diversityIndex,
  runtimePreference, firstWatched, lastWatched, availableYears,
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
provide('hourlyStats', hourlyStats)
provide('weekdayStats', weekdayStats)
provide('bingeStats', bingeStats)
provide('ratingPreference', ratingPreference)
provide('countryStats', countryStats)
provide('freshnessStats', freshnessStats)
provide('watchPattern', watchPattern)
provide('diversityIndex', diversityIndex)
provide('runtimePreference', runtimePreference)
provide('firstWatched', firstWatched)
provide('lastWatched', lastWatched)
provide('availableYears', availableYears)

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
const selectedYear = ref(new Date().getFullYear())

provide('selectedYear', selectedYear)

const sections = [
  { id: 'welcome', label: '封面' },
  { id: 'narrative', label: '开篇' },
  { id: 'overview', label: '总览' },
  { id: 'preference', label: '偏好' },
  { id: 'behavior', label: '行为' },
  { id: 'persona', label: '画像' },
  { id: 'rankings', label: '榜单' },
  { id: 'poster', label: '海报' },
  { id: 'archive', label: '历年' },
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
        <p>正在生成你的观影宇宙...</p>
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
      <div :id="`section-0`"><WelcomePage :media-list="mediaList" @start="scrollToSection(1)" /></div>
      <div :id="`section-1`"><OpeningNarrative /></div>
      <div :id="`section-2`"><CoreOverview @navigate="scrollToSection" /></div>
      <div :id="`section-3`"><PreferenceSection /></div>
      <div :id="`section-4`"><BehaviorHabits /></div>
      <div :id="`section-5`"><PersonaProfile /></div>
      <div :id="`section-6`"><AnnualRankings /></div>
      <div :id="`section-7`"><SharePoster /></div>
      <div :id="`section-8`"><YearArchive /></div>
    </template>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; background: var(--cinema-black); }
.scroll-progress {
  position: fixed; top: 0; left: 0; height: 2px;
  background: linear-gradient(90deg, var(--bean-green), var(--bean-green-bright));
  z-index: 999; transition: width 0.05s linear;
}
.loading-screen {
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  background: var(--cinema-black); color: var(--text-dim);
}
.loading-icon { font-size: 4rem; animation: breathe 2s ease-in-out infinite; }
.error-detail {
  font-size: 0.85rem; color: var(--text-dim); max-width: 400px;
  text-align: center; word-break: break-all; margin-top: 8px;
}
</style>
