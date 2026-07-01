<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'
import { GENRE_COLORS, translateGenre } from '@/utils/genres'

const dailyGenreStats = inject('dailyGenreStats')
const countryStats = inject('countryStats')
const freshnessStats = inject('freshnessStats')
const selectedYear = inject('selectedYear')

const visible = ref(false)
const sectionRef = ref(null)

const year = selectedYear

const genreData = computed(() => {
  const stats = (dailyGenreStats.value || []).filter(s => s.date?.startsWith(String(year.value)))
  const useStats = stats.length ? stats : (dailyGenreStats.value || [])
  const counts = {}, minutes = {}
  useStats.forEach(s => {
    counts[s.genre] = (counts[s.genre] || 0) + (s.count || 0)
    minutes[s.genre] = (minutes[s.genre] || 0) + (s.minutes || 0)
  })
  const genres = Object.keys(counts).sort((a, b) => counts[b] - counts[a])
  return {
    genres,
    minutes: genres.map(g => Math.round(minutes[g] / 60)),
    labels: genres.map(g => translateGenre(g)),
  }
})

const topGenre = computed(() => genreData.value.genres[0] ? translateGenre(genreData.value.genres[0]) : '')

const { chartRef: genreChartRef, resize: genreResize } = useECharts(() => {
  const d = genreData.value
  if (!d.genres.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'item',
      formatter(p) { return `${p.name}<br/>${p.value} 小时 (${p.percent}%)` }
    },
    series: [{
      type: 'pie', radius: ['40%', '68%'], center: ['50%', '50%'],
      padAngle: 2,
      startAngle: 90,
      itemStyle: { borderRadius: 6, borderColor: 'rgba(14,16,20,0.8)', borderWidth: 2 },
      label: { color: '#C8C8C8', fontSize: 12, formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      emphasis: { label: { fontSize: 13, fontWeight: 'bold' }, scale: true, scaleSize: 6 },
      data: d.labels.map((l, i) => ({
        name: l, value: d.minutes[i],
        itemStyle: {
          color: i === 0
            ? '#86A89C'
            : `rgba(140,148,159,${0.25 + (1 - i / d.labels.length) * 0.5})`,
        },
      })),
      animationType: 'expansion',
      animationDuration: 1200,
      animationEasing: 'cubicOut',
      animationDelay: (idx) => idx * 100,
    }],
    animationDuration: 1000, animationEasing: 'cubicOut', animationDelay: 200,
  }
}, [genreData])

const COUNTRY_NAMES = {
  us: '美国', gb: '英国', cn: '中国', jp: '日本', kr: '韩国',
  fr: '法国', de: '德国', ca: '加拿大', au: '澳大利亚', in: '印度',
  es: '西班牙', it: '意大利', tw: '台湾', hk: '香港', th: '泰国',
  nl: '荷兰', se: '瑞典', dk: '丹麦', no: '挪威', ie: '爱尔兰',
  mx: '墨西哥', br: '巴西', ar: '阿根廷', ru: '俄罗斯', tr: '土耳其',
}

const countryData = computed(() => {
  const stats = (countryStats.value || []).slice(0, 8)
  return stats.map(c => ({
    name: COUNTRY_NAMES[c.country] || c.country?.toUpperCase() || '未知',
    count: c.count,
  }))
})

const { chartRef: countryChartRef, resize: countryResize } = useECharts(() => {
  const d = countryData.value
  if (!d.length) return null
  const maxVal = Math.max(...d.map(x => x.count))
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', axisLine: { show: false },
      axisLabel: { color: '#6a6f78', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
    yAxis: { type: 'category', data: d.map(x => x.name).reverse(),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#c4c9ce', fontSize: 12 },
      axisTick: { show: false } },
    series: [{
      type: 'bar', barMaxWidth: 16,
      data: d.map(x => x.count).reverse(),
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [{ offset: 0, color: 'rgba(134,168,156,0.2)' }, { offset: 1, color: 'rgba(134,168,156,0.6)' }] },
        borderRadius: [0, 4, 4, 0],
      },
      emphasis: { itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [{ offset: 0, color: 'rgba(134,168,156,0.4)' }, { offset: 1, color: 'rgba(134,168,156,0.8)' }] } } },
      animationDelay: (idx) => idx * 80,
      animationDuration: 800,
      animationEasing: 'cubicOut',
    }],
    animationDuration: 800, animationEasing: 'cubicOut', animationDelay: 200,
  }
}, [countryData])

const eraData = computed(() => {
  const f = freshnessStats.value || {}
  const dist = f.year_dist || {}
  return Object.entries(dist).map(([k, v]) => ({ era: k, count: v })).sort((a, b) => a.era.localeCompare(b.era))
})

const { chartRef: eraChartRef, resize: eraResize } = useECharts(() => {
  const d = eraData.value
  if (!d.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 30, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: d.map(x => x.era),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#6a6f78', fontSize: 11 },
      axisTick: { show: false } },
    yAxis: { type: 'value', axisLine: { show: false },
      axisLabel: { color: '#6a6f78' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
    series: [{
      type: 'bar', barMaxWidth: 32,
      data: d.map(x => x.count),
      itemStyle: {
        color: 'rgba(140,148,159,0.4)',
        borderRadius: [4, 4, 0, 0],
      },
      animationDelay: (idx) => idx * 80,
      animationDuration: 800,
      animationEasing: 'cubicOut',
    }],
    animationDuration: 800, animationEasing: 'cubicOut', animationDelay: 200,
  }
}, [eraData])

const registerResize = inject('registerResize')
onMounted(() => {
  registerResize?.(genreResize)
  registerResize?.(countryResize)
  registerResize?.(eraResize)
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { visible.value = true; genreResize(); countryResize(); eraResize() } })
  }, { threshold: 0.1 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="preference-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">观影偏好分析</p>

      <!-- 题材偏好 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2 L2 7 L12 12 L22 7 Z"/><path d="M2 17 L12 22 L22 17"/><path d="M2 12 L12 17 L22 12"/></svg> 题材偏好</h3>
        <p class="block-desc" v-if="topGenre">
          你最爱的类型是 <span class="accent">{{ topGenre }}</span>
        </p>
        <div class="chart-card bean-card">
          <div ref="genreChartRef" class="chart-box" />
        </div>
      </div>

      <!-- 地区偏好 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> 地区偏好</h3>
        <p class="block-desc">你的观影足迹遍布世界</p>
        <div class="chart-card bean-card">
          <div ref="countryChartRef" class="chart-box tall" />
        </div>
      </div>

      <!-- 年代审美 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/></svg> 年代审美</h3>
        <p class="block-desc">
          <template v-if="freshnessStats?.avg_year">
            平均首播年份 <span class="warm">{{ freshnessStats.avg_year }}</span> 年
          </template>
          <template v-else>经典与新作的交织</template>
        </p>
        <div class="chart-card bean-card">
          <div ref="eraChartRef" class="chart-box" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.preference-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
}
.section-content { max-width: 760px; width: 100%; }

.chart-block { margin-bottom: 36px; }
.block-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 1rem; color: var(--text-bright); font-weight: 700;
  margin-bottom: 6px; letter-spacing: 1px;
}
.block-title svg { color: var(--bean-green); }
.block-desc {
  font-size: 0.88rem; color: var(--text-dim); margin-bottom: 14px;
}
.block-desc .accent { color: var(--bean-green-bright); font-weight: 700; }
.block-desc .warm { color: var(--warm-amber); font-weight: 700; }

.chart-card { padding: var(--space-md); }
.chart-box { width: 100%; height: 280px; }
.chart-box.tall { height: 300px; }

@media (max-width: 768px) {
  .chart-box { height: 220px; }
  .chart-box.tall { height: 240px; }
}
</style>
