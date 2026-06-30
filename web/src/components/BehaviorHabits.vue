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
      inRange: { color: ['#1a1f1a', '#3a5a34', '#7a9a72', '#a8c5a0', '#c4dcbc'] } },
    series: [{
      type: 'bar', barMaxWidth: 18,
      data: data.map((v, i) => ({
        value: v,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      })),
      animationDelay: (idx) => idx * 60,
      animationDuration: 800,
      animationEasing: 'elasticOut',
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
      type: 'bar', barMaxWidth: 30,
      data: d.map(x => x.count),
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(107,140,175,0.8)' }, { offset: 1, color: 'rgba(107,140,175,0.1)' }] },
        borderRadius: [6, 6, 0, 0],
      },
      animationDelay: (idx) => idx * 80,
      animationDuration: 1000,
      animationEasing: 'elasticOut',
    }],
    animationDuration: 1000, animationEasing: 'cubicOut', animationDelay: 200,
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
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
      data: data.map(s => s.total_count),
      lineStyle: { color: '#a8c5a0', width: 2.5 },
      itemStyle: { color: '#c4dcbc', borderColor: '#a8c5a0', borderWidth: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(168,197,160,0.25)' }, { offset: 1, color: 'rgba(168,197,160,0.01)' }] } },
    }],
    animationDuration: 1500, animationEasing: 'cubicOut', animationDelay: 300,
  }
}, [yearMonths])

const patternLabel = computed(() => {
  const p = watchPattern.value || {}
  const type = p.pattern_type || 'stable'
  const labels = {
    stable: { icon: '🌊', name: '佛系稳定型', desc: '你的观影节奏如涓涓细流，稳定而持久' },
    balanced: { icon: '⚖️', name: '张弛有度型', desc: '你有自己的节奏，忙时少看，闲时补上' },
    pulse: { icon: '⚡', name: '脉冲爆发型', desc: '你追剧如洪水，来一波停一波' },
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
        <div class="pace-icon">{{ patternLabel.icon }}</div>
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
        <h3 class="block-title">🕐 24小时观影分布</h3>
        <p class="block-desc" v-if="peakHour.count > 0">
          你的观影高峰在 <span class="accent">{{ peakHour.hour }}点</span>，共看了 <span class="warm">{{ peakHour.count }}</span> 次
        </p>
        <div class="chart-card bean-card">
          <div ref="hourChartRef" class="chart-box" />
        </div>
      </div>

      <!-- 星期分布 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title">📅 一周观影节奏</h3>
        <p class="block-desc">工作日与周末的观影分布</p>
        <div class="chart-card bean-card">
          <div ref="weekdayChartRef" class="chart-box" />
        </div>
      </div>

      <!-- 月度趋势 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title">📈 月度观影趋势</h3>
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
  background: linear-gradient(180deg, #11151a 0%, var(--cinema-black) 100%);
}
.section-content { max-width: 760px; width: 100%; }

.pace-card {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 24px; margin-bottom: 32px;
}
.pace-icon { font-size: 2.5rem; }
.pace-info { flex: 1; }
.pace-name { font-size: 1.1rem; font-weight: 700; color: var(--text-bright); margin-bottom: 4px; }
.pace-desc { font-size: 0.85rem; color: var(--text-dim); }
.pace-stat { text-align: center; }
.pace-stat-num {
  font-size: 2rem; font-weight: 900;
  background: linear-gradient(135deg, var(--bean-green-bright), var(--bean-green));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.pace-stat-label { font-size: 0.72rem; color: var(--text-dim); }

.chart-block { margin-bottom: 32px; }
.block-title { font-size: 1rem; color: var(--text-bright); font-weight: 700; margin-bottom: 6px; letter-spacing: 1px; }
.block-desc { font-size: 0.88rem; color: var(--text-dim); margin-bottom: 14px; }
.block-desc .accent { color: var(--bean-green-bright); font-weight: 700; }
.block-desc .warm { color: var(--warm-amber); font-weight: 700; }
.chart-card { padding: 18px; }
.chart-box { width: 100%; height: 220px; }

@media (max-width: 768px) {
  .pace-card { flex-direction: column; text-align: center; gap: 12px; }
  .chart-box { height: 180px; }
}
</style>
