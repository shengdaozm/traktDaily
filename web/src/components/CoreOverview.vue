<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import { useCountUp } from '@/composables/useTextReveal'

const monthlyStats = inject('monthlyStats')
const bingeStats = inject('bingeStats')
const hourlyStats = inject('hourlyStats')
const selectedYear = inject('selectedYear')

const emit = defineEmits(['navigate'])

const visible = ref(false)
const sectionRef = ref(null)
const { animate } = useCountUp()

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

const metrics = computed(() => [
  { icon: '⏱️', label: '观影时长', value: hours.value, unit: '小时', color: 'var(--bean-green)', target: 4 },
  { icon: '🎬', label: '观影总量', value: yearStats.value.count, unit: '部', color: 'var(--warm-amber)', target: 4 },
  { icon: '🔥', label: '连贯追剧', value: bingeRatio.value, unit: '%', color: 'var(--soft-pink)', target: 4 },
  { icon: '🌙', label: '深夜观影', value: nightRatio.value, unit: '%', color: 'var(--haze-blue)', target: 4 },
  { icon: '📺', label: '完结剧集', value: yearStats.value.episodes, unit: '集', color: 'var(--purple)', target: 4 },
])

const numRefs = ref([])

watch(visible, (v) => {
  if (v) {
    metrics.value.forEach((m, i) => {
      setTimeout(() => {
        if (numRefs.value[i]) animate(numRefs.value[i], m.value, 1500)
      }, 200 + i * 150)
    })
  }
})

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

      <div class="metrics-grid stagger" :class="{ visible }">
        <div
          v-for="(m, i) in metrics"
          :key="i"
          class="metric-card bean-card"
          @click="emit('navigate', m.target)"
        >
          <div class="metric-icon">{{ m.icon }}</div>
          <div class="metric-value">
            <span :ref="el => numRefs[i] = el">0</span>
            <span class="metric-unit">{{ m.unit }}</span>
          </div>
          <div class="metric-label">{{ m.label }}</div>
          <div class="metric-hint">点击查看详情 →</div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.overview-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
  background: linear-gradient(180deg, #0d1410 0%, var(--cinema-black) 100%);
}
.section-content { max-width: 860px; width: 100%; text-align: center; }

.metrics-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;
  margin-top: 40px;
}
.metric-card {
  padding: 28px 18px; text-align: center; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.metric-icon { font-size: 2rem; margin-bottom: 4px; }
.metric-value {
  font-size: 2.4rem; font-weight: 900; font-variant-numeric: tabular-nums;
  line-height: 1.1; display: flex; align-items: baseline; gap: 4px;
  background: linear-gradient(135deg, var(--bean-green-bright), var(--bean-green));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-unit { font-size: 0.9rem; color: var(--text-dim); font-weight: 600; }
.metric-label { font-size: 0.88rem; color: var(--text); font-weight: 600; }
.metric-hint {
  font-size: 0.72rem; color: var(--text-dim); opacity: 0;
  transition: opacity var(--transition);
}
.metric-card:hover .metric-hint { opacity: 1; }

@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .metric-value { font-size: 1.8rem; }
  .metric-card { padding: 20px 12px; }
}
</style>
