<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'
import { GENRE_COLORS, translateGenre } from '@/utils/genres'

const dailyGenreStats = inject('dailyGenreStats')
const visible = ref(false)
const sectionRef = ref(null)

const year = new Date().getFullYear()

const genreData = computed(() => {
  const stats = (dailyGenreStats.value || []).filter(s => s.date?.startsWith(String(year)))
  const useStats = stats.length ? stats : (dailyGenreStats.value || [])
  const counts = {}, minutes = {}
  useStats.forEach(s => {
    counts[s.genre] = (counts[s.genre] || 0) + (s.count || 0)
    minutes[s.genre] = (minutes[s.genre] || 0) + (s.minutes || 0)
  })
  const genres = Object.keys(counts).sort((a, b) => counts[b] - counts[a])
  return {
    genres,
    counts: genres.map(g => counts[g]),
    minutes: genres.map(g => Math.round(minutes[g] / 60)),
    labels: genres.map(g => translateGenre(g)),
  }
})

const topGenre = computed(() => genreData.value.genres[0] ? translateGenre(genreData.value.genres[0]) : '')

const totalMinutes = computed(() => genreData.value.minutes.reduce((a, b) => a + b, 0))

const { chartRef, resize } = useECharts(() => {
  const d = genreData.value
  if (!d.genres.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'item',
      formatter(p) { return `${p.name}<br/>${p.value} 小时 (${p.percent}%)` }
    },
    series: [{
      type: 'pie', radius: ['35%', '68%'], center: ['50%', '50%'],
      padAngle: 3,
      itemStyle: { borderRadius: 8, borderColor: 'rgba(13,17,23,0.8)', borderWidth: 3 },
      label: { color: '#c9d1d9', fontSize: 12, formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' }, itemStyle: { shadowBlur: 16, shadowColor: 'rgba(0,0,0,0.4)' } },
      data: d.labels.map((l, i) => ({
        name: l, value: d.minutes[i],
        itemStyle: { color: GENRE_COLORS[i % GENRE_COLORS.length] },
      })),
    }],
    animationDuration: 1500, animationEasing: 'cubicOut', animationDelay: 300,
  }
}, [genreData])

const registerResize = inject('registerResize')
const unregisterResize = inject('unregisterResize')
onMounted(() => {
  registerResize?.(resize)
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { visible.value = true; resize() } })
  }, { threshold: 0.2 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="genre-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">🎭 观影偏好</p>
      <p class="narrative reveal-up" :class="{ visible }" v-if="topGenre">
        你最爱的类型是 <span class="accent">{{ topGenre }}</span><br/>
        在光影世界中，总有一类故事让你着迷
      </p>
      <div class="chart-card reveal-up" :class="{ visible }">
        <div ref="chartRef" class="chart-box" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.genre-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 80px 24px;
  background: linear-gradient(160deg, #1e1b2e 0%, #0d1117 60%);
}
.section-content { max-width: 700px; width: 100%; }
.section-label { font-size: 0.9rem; color: var(--accent); text-align: center; margin-bottom: 16px; font-weight: 600; }
.chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; backdrop-filter: blur(20px); }
.chart-box { width: 100%; height: 400px; }
@media (max-width: 768px) { .chart-box { height: 300px; } }
</style>
