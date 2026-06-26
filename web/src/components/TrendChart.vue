<script setup>
import { inject, computed } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const monthlyStats = inject('monthlyStats')

const recent12 = computed(() => {
  const sorted = [...(monthlyStats.value || [])].reverse()
  return sorted.slice(-12)
})

const { chartRef } = useECharts(() => {
  const data = recent12.value
  if (!data.length) return null
  return {
    tooltip: {
      ...TOOLTIP_STYLE, trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: '#8b949e' } },
      formatter(params) {
        const p0 = params.find(p => p.seriesName === '观影次数')
        const p1 = params.find(p => p.seriesName === '观影时长')
        return `<span style="font-weight:600">${params[0].axisValue}</span><br/>
          ${p0.marker} 观影次数：<b>${p0.value}</b> 次<br/>
          ${p1.marker} 观影时长：<b>${p1.value}</b> 小时`
      },
    },
    legend: {
      data: ['观影次数', '电影', '剧集', '观影时长'],
      textStyle: { color: '#8b949e' }, top: 0, itemWidth: 16, itemHeight: 3,
    },
    grid: { left: 50, right: 60, top: 40, bottom: 30 },
    xAxis: {
      type: 'category', data: data.map(s => s.year_month),
      axisLine: { lineStyle: { color: 'rgba(48,54,61,0.6)' } },
      axisLabel: { color: '#8b949e', fontSize: 11 },
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
        data: data.map(s => s.total_count), smooth: true,
        symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 2.5, color: '#58a6ff' }, itemStyle: { color: '#58a6ff' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(88,166,255,0.35)' }, { offset: 1, color: 'rgba(88,166,255,0.02)' }] } },
        emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 2 } },
      },
      {
        name: '电影', type: 'line', yAxisIndex: 0,
        data: data.map(s => s.movie_count), smooth: true,
        symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 1.5, color: '#3fb950', type: 'dashed' }, itemStyle: { color: '#3fb950' },
      },
      {
        name: '剧集', type: 'line', yAxisIndex: 0,
        data: data.map(s => s.episode_count), smooth: true,
        symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 1.5, color: '#8b5cf6', type: 'dashed' }, itemStyle: { color: '#8b5cf6' },
      },
      {
        name: '观影时长', type: 'bar', yAxisIndex: 1,
        data: data.map(s => Math.round((s.total_minutes || 0) / 60)), barMaxWidth: 28,
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(240,192,64,0.5)' }, { offset: 1, color: 'rgba(240,192,64,0.05)' }] },
          borderRadius: [4, 4, 0, 0] },
        emphasis: { itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(240,192,64,0.8)' }, { offset: 1, color: 'rgba(240,192,64,0.15)' }] } } },
      },
    ],
    animationDuration: 1200, animationEasing: 'cubicOut',
  }
}, [recent12])
</script>

<template>
  <div ref="chartRef" class="chart-box" />
</template>

<style scoped>
.chart-box { width: 100%; height: 320px; }
</style>
