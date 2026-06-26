<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'
import { GENRE_COLORS, translateGenre } from '@/utils/genres'

const monthlyStats = inject('monthlyStats')
const visible = ref(false)
const sectionRef = ref(null)

const year = new Date().getFullYear()
const yearMonths = computed(() => {
  const sorted = [...(monthlyStats.value || [])].reverse()
  const ym = sorted.filter(s => s.year_month?.startsWith(String(year)))
  return ym.length ? ym : sorted.slice(-12)
})

const peakMonth = computed(() => {
  const m = yearMonths.value
  if (!m.length) return null
  return m.reduce((a, b) => a.total_count > b.total_count ? a : b)
})

const { chartRef, resize } = useECharts(() => {
  const data = yearMonths.value
  if (!data.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis',
      formatter(p) {
        const v = p[0]
        return `<b>${v.axisValue}</b><br/>观影 ${v.value} 次<br/>电影 ${data[p[0].dataIndex].movie_count} · 剧集 ${data[p[0].dataIndex].episode_count}`
      }
    },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category', data: data.map(s => s.year_month.substring(5)),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#8b949e', fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
    series: [{
      type: 'bar', barMaxWidth: 40,
      data: data.map(s => s.total_count),
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#f0c040' }, { offset: 1, color: 'rgba(240,192,64,0.1)' }] },
        borderRadius: [6, 6, 0, 0],
      },
      emphasis: { itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: '#ff8c42' }, { offset: 1, color: 'rgba(255,140,66,0.2)' }] } } },
    }],
    animationDuration: 1500, animationEasing: 'cubicOut', animationDelay: 300,
  }
}, [yearMonths])

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
  <section ref="sectionRef" class="monthly-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">📅 月度旅程</p>
      <p class="narrative reveal-up" :class="{ visible }">
        <template v-if="peakMonth">
          <span class="highlight">{{ peakMonth.year_month }}</span> 是你最爱看的一个月<br/>
          看了 <span class="accent">{{ peakMonth.total_count }}</span> 部作品
        </template>
        <template v-else>每月的观影记录</template>
      </p>
      <div class="chart-container reveal-up" :class="{ visible }">
        <div ref="chartRef" class="chart-box" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.monthly-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
  background: linear-gradient(180deg, #0d1117 0%, #1a1208 100%);
}
.section-content { max-width: 800px; width: 100%; }
.section-label { font-size: 0.85rem; color: var(--accent); text-align: center; margin-bottom: 12px; font-weight: 600; }
.chart-container { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; backdrop-filter: blur(16px); }
.chart-box { width: 100%; height: 300px; }
@media (max-width: 768px) { .chart-box { height: 220px; } }
</style>
