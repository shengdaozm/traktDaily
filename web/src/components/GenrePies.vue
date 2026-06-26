<script setup>
import { inject, computed } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'
import { GENRE_COLORS, translateGenre } from '@/utils/genres'

const dailyGenreStats = inject('dailyGenreStats')

const genreData = computed(() => {
  const stats = dailyGenreStats.value || []
  const counts = {}, minutes = {}
  stats.forEach(s => {
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

function makePieOption(data, values, total, unit) {
  return {
    tooltip: {
      ...TOOLTIP_STYLE, trigger: 'item',
      formatter(p) { return `${p.name}<br/>${p.value} ${unit} (${(p.value / total * 100).toFixed(1)}%)` },
    },
    legend: {
      type: 'scroll', orient: 'vertical', right: 0, top: 10, bottom: 10,
      textStyle: { color: '#8b949e', fontSize: 11 },
      pageTextStyle: { color: '#8b949e' },
    },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['35%', '50%'],
      avoidLabelOverlap: false, padAngle: 2,
      itemStyle: { borderRadius: 6, borderColor: 'rgba(10,14,20,0.8)', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#e6edf3' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' },
      },
      data: data.labels.map((l, i) => ({
        name: l, value: values[i],
        itemStyle: { color: GENRE_COLORS[i % GENRE_COLORS.length] },
      })),
    }],
    animationDuration: 1000, animationEasing: 'cubicOut',
  }
}

const totalCounts = computed(() => genreData.value.counts.reduce((a, b) => a + b, 0))
const totalMinutes = computed(() => genreData.value.minutes.reduce((a, b) => a + b, 0))

const { chartRef: chartRef1 } = useECharts(
  () => makePieOption(genreData.value, genreData.value.counts, totalCounts.value, '集'),
  [genreData]
)
const { chartRef: chartRef2 } = useECharts(
  () => makePieOption(genreData.value, genreData.value.minutes, totalMinutes.value, '小时'),
  [genreData]
)
</script>

<template>
  <div class="genre-pies">
    <div class="chart-card">
      <h3>按集数</h3>
      <div ref="chartRef1" class="chart-box" />
    </div>
    <div class="chart-card">
      <h3>按时长（小时）</h3>
      <div ref="chartRef2" class="chart-box" />
    </div>
  </div>
</template>

<style scoped>
.genre-pies { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.chart-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
}
.chart-card h3 { font-size: 1rem; color: var(--text-bright); margin-bottom: 16px; }
.chart-box { width: 100%; height: 320px; }

@media (max-width: 768px) { .genre-pies { grid-template-columns: 1fr; } }
</style>
