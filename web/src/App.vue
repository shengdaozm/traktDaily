<script setup>
import { ref, provide, onMounted, onUnmounted, nextTick } from 'vue'
import { useTraktData } from '@/composables/useTraktData'
import HeroHeader from '@/components/HeroHeader.vue'
import StatsSection from '@/components/StatsSection.vue'
import TabNav from '@/components/TabNav.vue'
import OverviewTab from '@/components/OverviewTab.vue'
import HeatmapTab from '@/components/HeatmapTab.vue'
import ChartsTab from '@/components/ChartsTab.vue'
import LibraryTab from '@/components/LibraryTab.vue'

const {
  summary, mediaList, topMedia, recentMeta, loading, error,
  mediaMap, lastUpdated, totalStats,
  monthlyStats, dailyGenreStats, genreStats,
  fetchRecentPage, getRecentPage,
} = useTraktData()

const activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: '概览', icon: '📈' },
  { key: 'heatmap', label: '热力图', icon: '🔥' },
  { key: 'charts', label: '图表', icon: '📊' },
  { key: 'library', label: '剧库', icon: '🎬' },
]

provide('summary', summary)
provide('mediaList', mediaList)
provide('topMedia', topMedia)
provide('recentMeta', recentMeta)
provide('mediaMap', mediaMap)
provide('monthlyStats', monthlyStats)
provide('dailyGenreStats', dailyGenreStats)
provide('genreStats', genreStats)
provide('fetchRecentPage', fetchRecentPage)
provide('getRecentPage', getRecentPage)

const resizeCallbacks = ref([])

function registerResize(fn) {
  resizeCallbacks.value.push(fn)
}

function unregisterResize(fn) {
  const i = resizeCallbacks.value.indexOf(fn)
  if (i >= 0) resizeCallbacks.value.splice(i, 1)
}

provide('registerResize', registerResize)
provide('unregisterResize', unregisterResize)

function handleResize() {
  resizeCallbacks.value.forEach(fn => fn?.())
}

function onTabChange() {
  nextTick(() => {
    setTimeout(() => {
      resizeCallbacks.value.forEach(fn => fn?.())
    }, 300)
  })
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))
</script>

<template>
  <div class="container">
    <HeroHeader :last-updated="lastUpdated" :media-list="mediaList" />

    <div v-if="loading" class="loading-state">
      <div class="skeleton" style="width:200px;height:24px;margin:0 auto 16px" />
      <div class="skeleton" style="width:120px;height:16px;margin:0 auto" />
    </div>

    <template v-else-if="error">
      <div class="empty-state">
        <div class="icon">⚠️</div>
        <p>数据加载失败</p>
      </div>
    </template>

    <template v-else>
      <StatsSection :stats="totalStats" :monthly-stats="monthlyStats" />

      <TabNav v-model="activeTab" :tabs="tabs" @change="onTabChange" />

      <Transition name="tab" mode="out-in" @after-enter="onTabChange">
        <OverviewTab v-if="activeTab === 'overview'" />
        <HeatmapTab v-else-if="activeTab === 'heatmap'" />
        <ChartsTab v-else-if="activeTab === 'charts'" />
        <LibraryTab v-else-if="activeTab === 'library'" />
      </Transition>
    </template>

    <footer>
      <p>
        数据来源 <a href="https://trakt.tv" target="_blank">Trakt</a>
        · 海报来自 <a href="https://themoviedb.org" target="_blank">TMDB</a>
        · 部署于 <a href="https://pages.github.com" target="_blank">GitHub Pages</a>
      </p>
    </footer>
  </div>
</template>

<style scoped>
.container {
  max-width: 1080px; margin: 0 auto; padding: 0 24px;
  position: relative; z-index: 1; min-height: 100vh;
}
.loading-state {
  text-align: center; padding: 80px 0;
}
.empty-state {
  text-align: center; padding: 80px 20px; color: var(--muted);
}
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.4; }

footer {
  text-align: center; margin-top: 48px; padding: 32px 20px;
  color: rgba(72, 79, 88, 0.6); font-size: 0.82rem;
}

.tab-enter-active, .tab-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.tab-enter-from { opacity: 0; transform: translateY(12px); }
.tab-leave-to { opacity: 0; transform: translateY(-8px); }

@media (max-width: 768px) {
  .container { padding: 0 16px; }
}
</style>
