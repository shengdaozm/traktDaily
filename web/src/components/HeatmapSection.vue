<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const dailyGenreStats = inject('dailyGenreStats')
const visible = ref(false)
const sectionRef = ref(null)

const selectedYear = ref(new Date().getFullYear())

const availableYears = computed(() => {
  const stats = dailyGenreStats.value || []
  const years = new Set()
  stats.forEach(s => { if (s.date) years.add(parseInt(s.date.substring(0, 4))) })
  return [...years].sort((a, b) => b - a)
})

const chartData = computed(() => {
  const stats = (dailyGenreStats.value || []).filter(s => s.date?.startsWith(String(selectedYear.value)))
  const map = {}
  stats.forEach(s => {
    const d = s.date
    if (d && d.startsWith(String(selectedYear.value))) {
      map[d] = (map[d] || 0) + (s.count || 0)
    }
  })
  return Object.entries(map).map(([date, count]) => [date, count])
})

const totalDays = computed(() => chartData.value.length)
const maxDay = computed(() => {
  if (!chartData.value.length) return null
  const max = chartData.value.reduce((a, b) => a[1] > b[1] ? a : b)
  return max
})

const { chartRef, render, resize } = useECharts(() => {
  const data = chartData.value
  const year = selectedYear.value
  const maxVal = Math.max(50, ...data.map(d => d[1]))
  return {
    tooltip: { ...TOOLTIP_STYLE, formatter(p) { return `<b>${p.value[0]}</b><br/>观影 ${p.value[1]} 次` } },
    visualMap: { show: false, min: 0, max: maxVal,
      inRange: { color: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'] } },
    calendar: { top: 40, left: 50, right: 30, bottom: 20,
      range: [`${year}-01-01`, `${year}-12-31`],
      cellSize: ['auto', 16], splitLine: { show: false },
      itemStyle: { borderWidth: 3, borderColor: 'transparent' },
      yearLabel: { show: false },
      monthLabel: { color: '#8b949e', fontSize: 12, nameMap: 'ZH' },
      dayLabel: { show: false },
    },
    series: [{ type: 'heatmap', coordinateSystem: 'calendar', data,
      emphasis: { itemStyle: { borderColor: '#58a6ff', borderWidth: 1.5 } } }],
    animationDuration: 800,
  }
}, [chartData, selectedYear])

watch(selectedYear, () => render())

const registerResize = inject('registerResize')
onMounted(() => {
  registerResize?.(resize)
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { visible.value = true; resize() } })
  }, { threshold: 0.15 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="heatmap-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">🔥 观影日历</p>
      <p class="narrative reveal-up" :class="{ visible }" v-if="totalDays">
        这一年你有 <span class="highlight">{{ totalDays }}</span> 天在观影<br/>
        <template v-if="maxDay">
          最密集的一天是 <span class="accent">{{ maxDay[0] }}</span>，看了 <span class="accent">{{ maxDay[1] }}</span> 部
        </template>
      </p>

      <div class="year-select reveal-up" :class="{ visible }">
        <select v-model="selectedYear">
          <option v-for="y in availableYears" :key="y" :value="y">{{ y }} 年</option>
        </select>
      </div>

      <div class="chart-card reveal-up" :class="{ visible }">
        <div ref="chartRef" class="chart-box" />
        <div class="heatmap-legend">
          少 <span class="lv0" /><span class="lv1" /><span class="lv2" /><span class="lv3" /><span class="lv4" /> 多
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.heatmap-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
  background: linear-gradient(180deg, #0d1117 0%, #121a2a 100%);
}
.section-content { max-width: 900px; width: 100%; }
.section-label { font-size: 0.85rem; color: var(--accent); text-align: center; margin-bottom: 12px; font-weight: 600; }
.year-select { text-align: center; margin-bottom: 16px; }
.year-select select {
  padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text-bright); font-size: 0.85rem; font-weight: 600;
  cursor: pointer; outline: none; appearance: none; -webkit-appearance: none;
}
.year-select select option { background: var(--surface-solid); }
.chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; backdrop-filter: blur(16px); }
.chart-box { width: 100%; height: 200px; }
.heatmap-legend { display: flex; align-items: center; justify-content: flex-end; gap: 4px; margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); }
.heatmap-legend span { display: inline-block; width: 12px; height: 12px; border-radius: 2px; }
.lv0 { background: rgba(255,255,255,0.05); }
.lv1 { background: #0e4429; }
.lv2 { background: #006d32; }
.lv3 { background: #26a641; }
.lv4 { background: #39d353; }
</style>
