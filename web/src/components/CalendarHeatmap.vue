<script setup>
import { inject, ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const dailyGenreStats = inject('dailyGenreStats')
const registerResize = inject('registerResize')
const unregisterResize = inject('unregisterResize')

const selectedYear = ref(new Date().getFullYear())

const availableYears = computed(() => {
  const stats = dailyGenreStats.value || []
  const years = new Set()
  stats.forEach(s => { if (s.date) years.add(parseInt(s.date.substring(0, 4))) })
  return [...years].sort((a, b) => b - a)
})

const dailyMap = computed(() => {
  const stats = dailyGenreStats.value || []
  const map = {}
  stats.forEach(s => {
    const d = s.date
    if (d && d.startsWith(String(selectedYear.value))) {
      map[d] = (map[d] || 0) + (s.count || 0)
    }
  })
  return map
})

const chartData = computed(() => {
  return Object.entries(dailyMap.value).map(([date, count]) => [date, count])
})

const { chartRef, render, resize } = useECharts(() => {
  const data = chartData.value
  const year = selectedYear.value
  const maxVal = Math.max(50, ...data.map(d => d[1]))
  return {
    tooltip: {
      ...TOOLTIP_STYLE,
      formatter(params) {
        return `<span style="font-weight:600">${params.value[0]}</span><br/>观影 ${params.value[1]} 次`
      },
    },
    visualMap: {
      show: false, min: 0, max: maxVal,
      inRange: { color: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'] },
    },
    calendar: {
      top: 30, left: 40, right: 20, bottom: 10,
      range: [`${year}-01-01`, `${year}-12-31`],
      cellSize: [16, 16], splitLine: { show: false },
      itemStyle: { borderWidth: 3, borderColor: 'transparent' },
      yearLabel: { show: false },
      monthLabel: { color: '#8b949e', fontSize: 11, nameMap: 'ZH' },
      dayLabel: { show: false }, silent: false,
    },
    series: [{
      type: 'heatmap', coordinateSystem: 'calendar',
      data, emphasis: { itemStyle: { borderColor: '#58a6ff', borderWidth: 1.5 } },
    }],
    animationDuration: 800,
  }
}, [chartData, selectedYear])

watch(selectedYear, () => render())

onMounted(() => registerResize?.(resize))
onBeforeUnmount(() => unregisterResize?.(resize))
</script>

<template>
  <div class="heatmap-container">
    <div class="header-row">
      <div class="year-selector">
        <span>📅</span>
        <select v-model="selectedYear">
          <option v-for="y in availableYears" :key="y" :value="y">{{ y }} 年</option>
        </select>
      </div>
    </div>
    <div ref="chartRef" class="chart-box-heatmap" />
    <div class="heatmap-legend">
      少 <span class="lv0" /><span class="lv1" /><span class="lv2" /><span class="lv3" /><span class="lv4" /> 多
    </div>
  </div>
</template>

<style scoped>
.heatmap-container { width: 100%; }
.header-row { display: flex; justify-content: flex-end; margin-bottom: 12px; }
.year-selector {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 8px;
  background: rgba(88, 166, 255, 0.08); border: 1px solid var(--border);
  font-size: 0.85rem; transition: all var(--transition);
}
.year-selector:hover { border-color: var(--primary); }
.year-selector select {
  background: transparent; border: none; color: var(--text-bright);
  font-size: 0.85rem; font-weight: 600; cursor: pointer; outline: none;
  appearance: none; -webkit-appearance: none;
}
.year-selector select option { background: var(--surface-solid); color: var(--text-bright); }
.chart-box-heatmap { width: 100%; height: 200px; }
.heatmap-legend {
  display: flex; align-items: center; justify-content: flex-end;
  gap: 4px; margin-top: 8px; font-size: 0.75rem; color: var(--muted);
}
.heatmap-legend span { display: inline-block; width: 12px; height: 12px; border-radius: 2px; }
.lv0 { background: rgba(48,54,61,0.4); }
.lv1 { background: #0e4429; }
.lv2 { background: #006d32; }
.lv3 { background: #26a641; }
.lv4 { background: #39d353; }
</style>
