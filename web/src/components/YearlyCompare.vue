<script setup>
import { inject, computed } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const monthlyStats = inject('monthlyStats')

const yearData = computed(() => {
  const stats = monthlyStats.value || []
  const yearMap = {}
  stats.forEach(s => {
    const year = s.year_month.substring(0, 4)
    if (!yearMap[year]) yearMap[year] = { year, total_count: 0, total_minutes: 0, movie_count: 0, episode_count: 0 }
    yearMap[year].total_count += s.total_count || 0
    yearMap[year].total_minutes += s.total_minutes || 0
    yearMap[year].movie_count += s.movie_count || 0
    yearMap[year].episode_count += s.episode_count || 0
  })
  const years = Object.keys(yearMap).sort()
  return { years, data: years.map(y => yearMap[y]) }
})

const { chartRef } = useECharts(() => {
  const { years, data } = yearData.value
  if (!years.length) return null
  return {
    tooltip: {
      ...TOOLTIP_STYLE, trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: '#8b949e' } },
      formatter(params) {
        const p0 = params.find(p => p.seriesName === '观影次数')
        const p1 = params.find(p => p.seriesName === '时长(小时)')
        return `<span style="font-weight:600">${params[0].axisValue} 年</span><br/>
          ${p0.marker} 观影次数：<b>${p0.value}</b> 次<br/>
          ${p1.marker} 观影时长：<b>${p1.value}</b> 小时`
      },
    },
    legend: {
      data: ['观影次数', '电影', '剧集', '时长(小时)'],
      textStyle: { color: '#8b949e' }, top: 0, itemWidth: 16, itemHeight: 3,
    },
    grid: { left: 50, right: 60, top: 40, bottom: 30 },
    xAxis: {
      type: 'category', data: years,
      axisLine: { lineStyle: { color: 'rgba(48,54,61,0.6)' } },
      axisLabel: { color: '#8b949e', fontSize: 12, fontWeight: 'bold' },
      axisTick: { show: false },
    },
    yAxis: [
      { type: 'value', name: '次数', nameTextStyle: { color: '#8b949e', padding: [0, 50, 0, 0] },
        min: 0, axisLine: { show: false }, axisLabel: { color: '#8b949e' },
        splitLine: { lineStyle: { color: 'rgba(48,54,61,0.3)' } } },
      { type: 'value', name: '小时', nameTextStyle: { color: '#8b949e', padding: [0, 0, 0, 40] },
        min: 0, axisLine: { show: false }, axisLabel: { color: '#8b949e' },
        splitLine: { show: false } },
    ],
    series: [
      {
        name: '观影次数', type: 'line', yAxisIndex: 0,
        data: data.map(d => d.total_count), symbol: 'circle', symbolSize: 10,
        lineStyle: { width: 3, color: '#58a6ff' },
        itemStyle: { color: '#58a6ff', borderColor: '#0a0e14', borderWidth: 2 },
        label: { show: true, color: '#58a6ff', fontSize: 12, fontWeight: 'bold', position: 'top', distance: 8 },
      },
      {
        name: '电影', type: 'bar', yAxisIndex: 0,
        data: data.map(d => d.movie_count), barMaxWidth: 20, barGap: '0%',
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#3fb950' }, { offset: 1, color: 'rgba(63,185,80,0.2)' }] },
          borderRadius: [4, 4, 0, 0] },
      },
      {
        name: '剧集', type: 'bar', yAxisIndex: 0,
        data: data.map(d => d.episode_count), barMaxWidth: 20, barGap: '0%',
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#8b5cf6' }, { offset: 1, color: 'rgba(139,92,246,0.2)' }] },
          borderRadius: [4, 4, 0, 0] },
      },
      {
        name: '时长(小时)', type: 'line', yAxisIndex: 1,
        data: data.map(d => Math.round(d.total_minutes / 60)),
        symbol: 'diamond', symbolSize: 10,
        lineStyle: { width: 2.5, color: '#f0c040', type: 'dashed' },
        itemStyle: { color: '#f0c040', borderColor: '#0a0e14', borderWidth: 2 },
        label: { show: true, color: '#f0c040', fontSize: 12, fontWeight: 'bold', position: 'top', distance: 8 },
      },
    ],
    animationDuration: 1200, animationEasing: 'cubicOut',
  }
}, [yearData])
</script>

<template>
  <div ref="chartRef" class="chart-box" />
</template>

<style scoped>
.chart-box { width: 100%; height: 320px; }
</style>
