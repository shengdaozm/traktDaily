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
      type: 'pie', radius: ['38%', '70%'], center: ['50%', '50%'],
      padAngle: 3,
      itemStyle: { borderRadius: 8, borderColor: 'rgba(10,12,15,0.8)', borderWidth: 3 },
      label: { color: '#c4c9ce', fontSize: 12, formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' }, itemStyle: { shadowBlur: 16, shadowColor: 'rgba(168,197,160,0.3)' } },
      data: d.labels.map((l, i) => ({
        name: l, value: d.minutes[i],
        itemStyle: { color: GENRE_COLORS[i % GENRE_COLORS.length] },
      })),
    }],
    animationDuration: 1500, animationEasing: 'cubicOut', animationDelay: 300,
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
      type: 'bar', barMaxWidth: 20,
      data: d.map(x => x.count).reverse(),
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [{ offset: 0, color: 'rgba(168,197,160,0.3)' }, { offset: 1, color: 'rgba(168,197,160,0.8)' }] },
        borderRadius: [0, 6, 6, 0],
      },
      emphasis: { itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [{ offset: 0, color: 'rgba(168,197,160,0.5)' }, { offset: 1, color: 'rgba(196,220,188,1)' }] } } },
    }],
    animationDuration: 1200, animationEasing: 'cubicOut', animationDelay: 200,
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
      type: 'bar', barMaxWidth: 36,
      data: d.map(x => x.count),
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(212,168,87,0.8)' }, { offset: 1, color: 'rgba(212,168,87,0.1)' }] },
        borderRadius: [6, 6, 0, 0],
      },
    }],
    animationDuration: 1200, animationEasing: 'cubicOut', animationDelay: 200,
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
        <h3 class="block-title">🎭 题材偏好</h3>
        <p class="block-desc" v-if="topGenre">
          你最爱的类型是 <span class="accent">{{ topGenre }}</span>
        </p>
        <div class="chart-card bean-card">
          <div ref="genreChartRef" class="chart-box" />
        </div>
      </div>

      <!-- 地区偏好 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title">🌍 地区偏好</h3>
        <p class="block-desc">你的观影足迹遍布世界</p>
        <div class="chart-card bean-card">
          <div ref="countryChartRef" class="chart-box tall" />
        </div>
      </div>

      <!-- 年代审美 -->
      <div class="chart-block reveal-up" :class="{ visible }">
        <h3 class="block-title">📅 年代审美</h3>
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
  background: linear-gradient(180deg, var(--cinema-black) 0%, #11151a 100%);
}
.section-content { max-width: 760px; width: 100%; }

.chart-block { margin-bottom: 36px; }
.block-title {
  font-size: 1rem; color: var(--text-bright); font-weight: 700;
  margin-bottom: 6px; letter-spacing: 1px;
}
.block-desc {
  font-size: 0.88rem; color: var(--text-dim); margin-bottom: 14px;
}
.block-desc .accent { color: var(--bean-green-bright); font-weight: 700; }
.block-desc .warm { color: var(--warm-amber); font-weight: 700; }

.chart-card { padding: 20px; }
.chart-box { width: 100%; height: 300px; }
.chart-box.tall { height: 320px; }

@media (max-width: 768px) {
  .chart-box { height: 240px; }
  .chart-box.tall { height: 260px; }
}
</style>
