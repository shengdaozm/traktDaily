<script setup>
import { inject, computed, onMounted, onBeforeUnmount } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const summary = inject('summary')
const registerResize = inject('registerResize')
const unregisterResize = inject('unregisterResize')

const data = computed(() => ({
  movies: summary.value?.total_movies || 0,
  episodes: summary.value?.total_episodes || 0,
}))

const { chartRef, resize } = useECharts(() => {
  const d = data.value
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      bottom: 0, textStyle: { color: '#8b949e' },
      itemWidth: 12, itemHeight: 12, itemGap: 20,
    },
    series: [{
      type: 'pie', radius: ['45%', '72%'], center: ['50%', '45%'],
      padAngle: 3,
      itemStyle: { borderRadius: 8, borderColor: 'rgba(10,14,20,0.8)', borderWidth: 3 },
      label: { show: true, color: '#e6edf3', fontSize: 13, formatter: '{b}\n{c}' },
      emphasis: {
        label: { fontSize: 16, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 16, shadowColor: 'rgba(0,0,0,0.4)' },
      },
      data: [
        { name: '电影', value: d.movies, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1,
          colorStops: [{ offset: 0, color: '#58a6ff' }, { offset: 1, color: '#79c0ff' }] } } },
        { name: '剧集', value: d.episodes, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1,
          colorStops: [{ offset: 0, color: '#8b5cf6' }, { offset: 1, color: '#d2a8ff' }] } } },
      ],
    }],
    animationDuration: 1200, animationEasing: 'elasticOut',
  }
}, [data])

onMounted(() => registerResize?.(resize))
onBeforeUnmount(() => unregisterResize?.(resize))
</script>

<template>
  <div ref="chartRef" class="chart-box-sm" />
</template>

<style scoped>
.chart-box-sm { width: 100%; height: 260px; }
</style>
