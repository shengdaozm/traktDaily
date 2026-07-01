<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const hourlyStats = inject('hourlyStats')
const weekdayStats = inject('weekdayStats')
const watchPattern = inject('watchPattern')
const bingeStats = inject('bingeStats')
const monthlyStats = inject('monthlyStats')
const selectedYear = inject('selectedYear')

const visible = ref(false)
const sectionRef = ref(null)

const year = selectedYear

const hourData = computed(() => {
  const map = {}
  ;(hourlyStats.value || []).forEach(h => {
    if (h.hour != null) map[h.hour] = h.count
  })
  return Array.from({ length: 24 }, (_, i) => map[i] || 0)
})

const peakHour = computed(() => {
  const data = hourData.value
  let max = 0, idx = 0
  data.forEach((v, i) => { if (v > max) { max = v; idx = i } })
  return { hour: idx, count: max }
})

const { chartRef: hourChartRef, resize: hourResize } = useECharts(() => {
  const data = hourData.value
  const hours = Array.from({ length: 24 }, (_, i) => `${i}点`)
  const maxVal = Math.max(...data, 1)
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis',
      formatter(p) { return `${p[0].axisValue}<br/>观影 ${p[0].value} 次` }
    },
    grid: { left: 35, right: 15, top: 15, bottom: 30 },
    xAxis: { type: 'category', data: hours,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#6a6f78', fontSize: 10, interval: 2 },
      axisTick: { show: false } },
    yAxis: { type: 'value', axisLine: { show: false },
      axisLabel: { color: '#6a6f78' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
    visualMap: { show: false, min: 0, max: maxVal,
      inRange: { color: ['rgba(255,255,255,0.04)', 'rgba(134,168,156,0.3)', 'rgba(134,168,156,0.7)', '#86A89C'] } },
    series: [{
      type: 'bar', barMaxWidth: 14,
      data: data.map((v, i) => ({
        value: v,
        itemStyle: { borderRadius: [3, 3, 0, 0] },
      })),
      animationDelay: (idx) => idx * 40,
      animationDuration: 600,
      animationEasing: 'cubicOut',
    }],
    animationDuration: 0,
  }
}, [hourData])

const WEEKDAY_NAMES = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const weekdayData = computed(() => {
  const map = {}
  ;(weekdayStats.value || []).forEach(w => {
    const d = typeof w.weekday === 'number' ? w.weekday : parseInt(w.weekday)
    map[d] = w.count
  })
  return [1, 2, 3, 4, 5, 6, 0].map(d => ({ name: WEEKDAY_NAMES[d], count: map[d] || 0 }))
})

const { chartRef: weekdayChartRef, resize: weekdayResize } = useECharts(() => {
  const d = weekdayData.value
  if (!d.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 30, right: 15, top: 15, bottom: 25 },
    xAxis: { type: 'category', data: d.map(x => x.name),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#6a6f78', fontSize: 11 },
      axisTick: { show: false } },
    yAxis: { type: 'value', axisLine: { show: false },
      axisLabel: { color: '#6a6f78' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
    series: [{
      type: 'bar', barMaxWidth: 26,
      data: d.map(x => x.count),
      itemStyle: {
        color: 'rgba(140,148,159,0.35)',
        borderRadius: [4, 4, 0, 0],
      },
      animationDelay: (idx) => idx * 60,
      animationDuration: 800,
      animationEasing: 'cubicOut',
    }],
    animationDuration: 800, animationEasing: 'cubicOut', animationDelay: 200,
  }
}, [weekdayData])

const yearMonths = computed(() => {
  const sorted = [...(monthlyStats.value || [])].reverse()
  const ym = sorted.filter(s => s.year_month?.startsWith(String(year.value)))
  return ym.length ? ym : sorted.slice(-12)
})

const { chartRef: monthChartRef, resize: monthResize } = useECharts(() => {
  const data = yearMonths.value
  if (!data.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis',
      formatter(p) {
        const v = p[0]
        return `<b>${v.axisValue}</b><br/>观影 ${v.value} 次`
      }
    },
    grid: { left: 35, right: 15, top: 15, bottom: 30 },
    xAxis: { type: 'category', data: data.map(s => s.year_month.substring(5)),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#6a6f78', fontSize: 11 },
      axisTick: { show: false } },
    yAxis: { type: 'value', axisLine: { show: false },
      axisLabel: { color: '#6a6f78' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
    series: [{
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
      data: data.map(s => s.total_count),
      lineStyle: { color: '#86A89C', width: 1.5 },
      itemStyle: { color: '#A0BEB4' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(134,168,156,0.12)' }, { offset: 1, color: 'rgba(134,168,156,0.01)' }] } },
    }],
    animationDuration: 1000, animationEasing: 'cubicOut', animationDelay: 300,
  }
}, [yearMonths])

const patternLabel = computed(() => {
  const p = watchPattern.value || {}
  const type = p.pattern_type || 'stable'
  const labels = {
    stable: { icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 12c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/></svg>', name: '佛系稳定型', desc: '你的观影节奏如涓涓细流，稳定而持久' },
    balanced: { icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="3" x2="12" y2="21"/><line x1="3" y1="12" x2="21" y2="12"/></svg>', name: '张弛有度型', desc: '你有自己的节奏，忙时少看，闲时补上' },
    pulse: { icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>', name: '脉冲爆发型', desc: '你追剧如洪水，来一波停一波' },
  }
  return labels[type] || labels.stable
})

const bingePercent = computed(() => {
  const b = bingeStats.value || {}
  return b.binge_ratio ? Math.round(b.binge_ratio * 100) : 0
})

const registerResize = inject('registerResize')
onMounted(() => {
  registerResize?.(hourResize)
  registerResize?.(weekdayResize)
  registerResize?.(monthResize)
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { visible.value = true; hourResize(); weekdayResize(); monthResize() } })
  }, { threshold: 0.1 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="behavior-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">观影行为习惯</p>

      <!-- 观影节奏标签 -->
      <div class="pace-card bean-card reveal-scale" :class="{ visible }">
        <div class="pace-icon" v-html="patternLabel.icon"></div>
        <div class="pace-info">
          <div class="pace-name">{{ patternLabel.name }}</div>
          <div class="pace-desc">{{ patternLabel.desc }}</div>
        </div>
        <div class="pace-stat">
          <div class="pace-stat-num">{{ bingePercent }}%</div>
          <div class="pace-stat-label">连贯追剧率</div>
        </div>
      </div>

      <!-- 24小时分布 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> 24小时观影分布</h3>
        <p class="block-desc" v-if="peakHour.count > 0">
          你的观影高峰在 <span class="accent">{{ peakHour.hour }}点</span>，共看了 <span class="warm">{{ peakHour.count }}</span> 次
        </p>
        <div class="chart-card bean-card">
          <div ref="hourChartRef" class="chart-box" />
        </div>
      </div>

      <!-- 星期分布 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/></svg> 一周观影节奏</h3>
        <p class="block-desc">工作日与周末的观影分布</p>
        <div class="chart-card bean-card">
          <div ref="weekdayChartRef" class="chart-box" />
        </div>
      </div>

      <!-- 月度趋势 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> 月度观影趋势</h3>
        <p class="block-desc">全年观影热度变化</p>
        <div class="chart-card bean-card">
          <div ref="monthChartRef" class="chart-box" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.behavior-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
}
.section-content { max-width: 760px; width: 100%; }

.pace-card {
  display: flex; align-items: center; gap: 16px;
  padding: var(--space-md) var(--space-lg); margin-bottom: 32px;
}
.pace-icon { color: var(--primary); display: flex; align-items: center; }
.pace-name { font-size: 1.05rem; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.pace-desc { font-size: 0.85rem; color: var(--text-3); }
.pace-stat { text-align: center; }
.pace-stat-num {
  font-size: 1.8rem; font-weight: 800; color: var(--primary-bright);
  font-variant-numeric: tabular-nums;
}
.pace-stat-label { font-size: 0.72rem; color: var(--text-3); }

.chart-block { margin-bottom: 32px; }
.block-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.95rem; color: var(--text-1); font-weight: 700;
  margin-bottom: 6px; letter-spacing: 1px;
}
.block-title svg { color: var(--primary); }
.block-desc { font-size: 0.85rem; color: var(--text-3); margin-bottom: 14px; }
.block-desc .accent { color: var(--primary-bright); font-weight: 700; }
.block-desc .warm { color: var(--primary-bright); font-weight: 700; }
.chart-card { padding: var(--space-md); }
.chart-box { width: 100%; height: 200px; }

@media (max-width: 768px) {
  .pace-card { flex-direction: column; text-align: center; gap: 12px; }
  .chart-box { height: 180px; }
}
</style>
