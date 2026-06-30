<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import { useCountUp } from '@/composables/useTextReveal'

const monthlyStats = inject('monthlyStats')
const bingeStats = inject('bingeStats')
const hourlyStats = inject('hourlyStats')
const topMedia = inject('topMedia')
const selectedYear = inject('selectedYear')

const emit = defineEmits(['navigate'])

const visible = ref(false)
const sectionRef = ref(null)
const { animate } = useCountUp()

const cardRefs = ref([])
const year = selectedYear

const yearStats = computed(() => {
  const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(year.value)))
  return {
    count: stats.reduce((a, s) => a + s.total_count, 0),
    minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
    movies: stats.reduce((a, s) => a + s.movie_count, 0),
    episodes: stats.reduce((a, s) => a + s.episode_count, 0),
  }
})

const hours = computed(() => Math.floor(yearStats.value.minutes / 60))

const nightRatio = computed(() => {
  const hourly = hourlyStats.value || []
  const night = hourly.filter(h => h.hour != null && (h.hour >= 22 || h.hour < 2)).reduce((a, h) => a + h.count, 0)
  const total = hourly.reduce((a, h) => a + (h.count || 0), 0)
  return total > 0 ? Math.round(night / total * 100) : 0
})

const bingeRatio = computed(() => {
  const b = bingeStats.value || {}
  return b.binge_ratio ? Math.round(b.binge_ratio * 100) : 0
})

const posterStream = computed(() => {
  return (topMedia.value || []).filter(m => m.poster_url).slice(0, 12)
})

watch(visible, (v) => {
  if (v) {
    metrics.value.forEach((m, i) => {
      setTimeout(() => {
        if (cardRefs.value[i]) animate(cardRefs.value[i], m.value, 1200)
      }, 300 + i * 120)
    })
  }
})

const metrics = computed(() => [
  { label: '观影时长', value: hours.value, unit: '小时', target: 5, big: true },
  { label: '观影总量', value: yearStats.value.count, unit: '部', target: 3, big: false },
  { label: '电影', value: yearStats.value.movies, unit: '部', target: 3, big: false },
  { label: '剧集', value: yearStats.value.episodes, unit: '集', target: 3, big: false },
  { label: '连贯追剧', value: bingeRatio.value, unit: '%', target: 5, big: false },
  { label: '深夜观影', value: nightRatio.value, unit: '%', target: 5, big: false },
])

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.15 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="overview-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">核心数据总览</p>
      <p class="narrative reveal-up" :class="{ visible }">
        <span class="highlight">{{ year }}</span> 年，你的观影全景
      </p>

      <!-- 不对称错落网格：一大 + 小卡片 -->
      <div class="metrics-grid stagger" :class="{ visible }">
        <div
          v-for="(m, i) in metrics"
          :key="i"
          class="metric-card glass-card"
          :class="{ 'card-big': m.big }"
          @click="emit('navigate', m.target)"
        >
          <div class="metric-value">
            <span :ref="el => cardRefs[i] = el">0</span>
            <span class="metric-unit">{{ m.unit }}</span>
          </div>
          <div class="metric-label">{{ m.label }}</div>
        </div>
      </div>

      <!-- 横向海报流：静止展示，hover 微浮 -->
      <div class="poster-strip reveal-up" :class="{ visible }" v-if="posterStream.length">
        <div class="strip-track">
          <a v-for="(m, i) in posterStream" :key="i"
            :href="'#'" class="strip-poster"
          >
            <img :src="m.poster_url" alt="" loading="lazy" />
          </a>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.overview-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: var(--section-gap) var(--page-margin);
  background: var(--bg);
}
.section-content { max-width: 760px; width: 100%; text-align: center; }

/* 不对称网格：左大右小 */
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 12px;
  margin-top: 40px;
}
.metric-card {
  padding: var(--space-md) var(--space-sm);
  text-align: center; cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
}
.card-big {
  grid-column: span 2;
  grid-row: span 2;
  display: flex; flex-direction: column; justify-content: center; gap: 8px;
}
.metric-value {
  font-size: 1.8rem; font-weight: 800; font-variant-numeric: tabular-nums;
  line-height: 1.1; display: flex; align-items: baseline; justify-content: center; gap: 4px;
  color: var(--primary-bright);
}
.card-big .metric-value { font-size: 2.8rem; }
.metric-unit { font-size: 0.85rem; color: var(--text-3); font-weight: 600; }
.metric-label { font-size: 0.82rem; color: var(--text-3); }
.card-big .metric-label { font-size: 0.95rem; color: var(--text-2); }

/* 静止海报条 */
.poster-strip {
  margin-top: 40px; overflow: hidden;
}
.strip-track {
  display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
}
.strip-poster {
  width: 72px; height: 108px; border-radius: var(--radius-sm);
  overflow: hidden; flex-shrink: 0;
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: transform var(--transition);
}
.strip-poster:hover { transform: translateY(-4px); }
.strip-poster img { width: 100%; height: 100%; object-fit: cover; }

@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: 1fr 1fr; }
  .card-big { grid-column: span 2; grid-row: span 1; }
  .card-big .metric-value { font-size: 2.2rem; }
  .metric-value { font-size: 1.5rem; }
}
</style>
