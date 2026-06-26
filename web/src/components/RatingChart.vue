<script setup>
import { inject, computed, onMounted, onBeforeUnmount } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const mediaList = inject('mediaList')
const registerResize = inject('registerResize')
const unregisterResize = inject('unregisterResize')

const buckets = computed(() => {
  const ratings = (mediaList.value || []).map(m => m.rating).filter(r => r != null).map(Number)
  const b = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  ratings.forEach(r => { b[Math.min(Math.floor(r), 9)]++ })
  return b
})

const labels = ['0-1', '1-2', '2-3', '3-4', '4-5', '5-6', '6-7', '7-8', '8-9', '9-10']

const { chartRef, resize } = useECharts(() => {
  const data = buckets.value
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 40, right: 16, top: 16, bottom: 30 },
    xAxis: {
      type: 'category', data: labels,
      axisLine: { lineStyle: { color: 'rgba(48,54,61,0.6)' } },
      axisLabel: { color: '#8b949e', fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value', name: '数量', nameTextStyle: { color: '#8b949e' },
      minInterval: 1, axisLine: { show: false }, axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: 'rgba(48,54,61,0.3)' } },
    },
    series: [{
      type: 'bar', barMaxWidth: 32,
      data: data.map(v => ({
        value: v,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(240,192,64,0.9)' }, { offset: 1, color: 'rgba(240,192,64,0.2)' }] },
          borderRadius: [4, 4, 0, 0],
        },
      })),
      emphasis: {
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#f0c040' }, { offset: 1, color: 'rgba(240,192,64,0.5)' }] } },
      },
    }],
    animationDuration: 1000, animationEasing: 'elasticOut',
  }
}, [buckets])

onMounted(() => registerResize?.(resize))
onBeforeUnmount(() => unregisterResize?.(resize))
</script>

<template>
  <div ref="chartRef" class="chart-box-sm" />
</template>

<style scoped>
.chart-box-sm { width: 100%; height: 260px; }
</style>
