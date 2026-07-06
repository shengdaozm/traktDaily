<script setup>
import { ref, computed, provide, onMounted, onUnmounted } from 'vue'
import { useTraktData } from '@/composables/useTraktData'
import { useBackgroundLayer } from '@/composables/useBackgroundLayer'
import WelcomePage from '@/components/WelcomePage.vue'
import OpeningNarrative from '@/components/OpeningNarrative.vue'
import CoreOverview from '@/components/CoreOverview.vue'
import MonthlyJourney from '@/components/MonthlyJourney.vue'
import PreferenceSection from '@/components/PreferenceSection.vue'
import BehaviorHabits from '@/components/BehaviorHabits.vue'
import PersonaProfile from '@/components/PersonaProfile.vue'
import AnnualRankings from '@/components/AnnualRankings.vue'
import SharePoster from '@/components/SharePoster.vue'
import YearArchive from '@/components/YearArchive.vue'
import SearchScore from '@/components/SearchScore.vue'

const {
  summary, mediaList, topMedia, persona, recentMeta, loading, error,
  mediaMap, lastUpdated, totalStats,
  monthlyStats, dailyGenreStats, genreStats,
  hourlyStats, weekdayStats, bingeStats, ratingPreference,
  countryStats, freshnessStats, watchPattern, diversityIndex,
  runtimePreference, firstWatched, lastWatched, availableYears,
  monthlyPosters,
  fetchRecentMonth, recentMonthCache,
} = useTraktData()

// 用户画像数据（用于打分）
const userProfile = shallowRef(null)
onMounted(async () => {
  try {
    const resp = await fetch('data/profile.json')
    if (resp.ok) userProfile.value = await resp.json()
  } catch { /* 画像未生成，静默跳过 */ }
})
provide('profile', userProfile)

provide('summary', summary)
provide('mediaList', mediaList)
provide('topMedia', topMedia)
provide('persona', persona)
provide('monthlyPosters', monthlyPosters)
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
provide('fetchRecentMonth', fetchRecentMonth)
provide('recentMonthCache', recentMonthCache)

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
  { id: 'monthly', label: '月度' },
  { id: 'preference', label: '偏好' },
  { id: 'behavior', label: '行为' },
  { id: 'persona', label: '画像' },
  { id: 'rankings', label: '榜单' },
  { id: 'poster', label: '海报' },
  { id: 'archive', label: '历年' },
  { id: 'search-score', label: '打分' },
]

const sectionBackgrounds = computed(() => {
  const topM = topMedia.value || []
  const mMap = mediaMap.value
  if (!topM.length || !mMap) return []

  const sixMonthsAgo = new Date()
  sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)

  const recent = topM.filter(m => {
    if (!m.last_watched) return false
    return new Date(m.last_watched) >= sixMonthsAgo
  })

  const backdrops = recent
    .map(m => mMap.get(m.trakt_id)?.backdrop_url)
    .filter(Boolean)
  if (!backdrops.length) return []

  const genreCounts = {}
  const genreBackdropMap = {}
  for (const m of recent) {
    const backdrop = mMap.get(m.trakt_id)?.backdrop_url
    if (!backdrop) continue
    let genres = m.genres
    if (typeof genres === 'string') {
      try { genres = JSON.parse(genres) } catch { genres = [] }
    }
    if (Array.isArray(genres)) {
      for (const g of genres) {
        genreCounts[g] = (genreCounts[g] || 0) + 1
        if (!genreBackdropMap[g]) genreBackdropMap[g] = backdrop
      }
    }
  }
  const sortedGenres = Object.entries(genreCounts).sort((a, b) => b[1] - a[1])
  const topGenreBackdrop = sortedGenres[0] ? genreBackdropMap[sortedGenres[0][0]] : ''

  const top1 = recent[0]
  const top1Backdrop = top1 ? mMap.get(top1.trakt_id)?.backdrop_url || '' : ''

  const n = backdrops.length
  function pick(start, count) {
    const result = []
    for (let i = 0; i < count; i++) {
      result.push(backdrops[(start + i) % n])
    }
    return result
  }

  return [
    pick(0, Math.min(6, n)),
    pick(Math.floor(n * 0.3), 3),
    pick(Math.floor(n * 0.5), 3),
    pick(Math.floor(n * 0.7), 3),
    topGenreBackdrop ? [topGenreBackdrop] : pick(Math.floor(n * 0.1), 2),
    pick(Math.floor(n * 0.4), 2),
    pick(Math.floor(n * 0.6), 1),
    top1Backdrop ? [top1Backdrop] : pick(0, 1),
    pick(Math.floor(n * 0.8), 1),
    pick(Math.floor(n * 0.9), 1),
  ]
})

const { layerA, layerB, activeLayer } = useBackgroundLayer(sectionBackgrounds, activeSection)

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
    <div class="bg-layer">
      <div
        class="bg-layer__img"
        :class="{ active: activeLayer === 'A' }"
        :style="layerA ? { backgroundImage: `url(${layerA})` } : {}"
      />
      <div
        class="bg-layer__img"
        :class="{ active: activeLayer === 'B' }"
        :style="layerB ? { backgroundImage: `url(${layerB})` } : {}"
      />
      <div class="bg-layer__overlay" />
    </div>

    <div class="scroll-progress" :style="{ width: scrollProgress + '%' }" />

    <nav class="nav-dots" v-if="!loading && !error">
      <button
        v-for="(s, i) in sections" :key="i"
        class="nav-dot" :class="{ active: activeSection === i }"
        :title="s.label"
        @click="scrollToSection(i)"
      />
    </nav>

    <div class="content-layer">
      <template v-if="loading">
        <div class="loading-screen">
          <div class="loading-spinner" />
          <p>正在生成你的观影宇宙...</p>
        </div>
      </template>

      <template v-else-if="error">
        <div class="loading-screen">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color: var(--text-3)">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <p>数据加载失败</p>
          <p class="error-detail" v-if="error">{{ error.message || error }}</p>
        </div>
      </template>

      <template v-else>
        <div :id="`section-0`"><WelcomePage :media-list="mediaList" @start="scrollToSection(1)" /></div>
        <div :id="`section-1`"><OpeningNarrative /></div>
        <div :id="`section-2`"><CoreOverview @navigate="scrollToSection" /></div>
        <div :id="`section-3`"><MonthlyJourney /></div>
        <div :id="`section-4`"><PreferenceSection /></div>
        <div :id="`section-5`"><BehaviorHabits /></div>
        <div :id="`section-6`"><PersonaProfile /></div>
        <div :id="`section-7`"><AnnualRankings /></div>
        <div :id="`section-8`"><SharePoster /></div>
        <div :id="`section-9`"><YearArchive /></div>
        <div :id="`section-10`"><SearchScore /></div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; }

.loading-screen {
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  background: var(--bg); color: var(--text-3);
}
.loading-spinner {
  width: 32px; height: 32px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.08);
  border-top-color: var(--primary);
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-detail {
  font-size: 0.82rem; color: var(--text-3); max-width: 400px;
  text-align: center; word-break: break-all; margin-top: 8px;
}
</style>
