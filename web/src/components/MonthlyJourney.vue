<script setup>
import { inject, ref, computed, onMounted } from 'vue'

const monthlyPosters = inject('monthlyPosters')
const monthlyStats = inject('monthlyStats')
const selectedYear = inject('selectedYear')
const visible = ref(false)
const sectionRef = ref(null)
const activeMonthIdx = ref(0)

const year = selectedYear

const yearMonths = computed(() => {
  const all = monthlyStats.value || []
  const ym = all.filter(s => s.year_month?.startsWith(String(year.value)))
  return ym.length ? ym : all.slice(-12)
})

const yearPosters = computed(() => {
  const all = monthlyPosters.value || []
  const yp = all.filter(m => m.year_month?.startsWith(String(year.value)))
  return yp.length ? yp : all.slice(-12)
})

const peakMonth = computed(() => {
  const m = yearMonths.value
  if (!m.length) return null
  return m.reduce((a, b) => a.total_count > b.total_count ? a : b)
})

const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月']

function monthLabel(ym) {
  if (!ym) return ''
  const m = parseInt(ym.substring(5))
  return monthNames[m - 1] || ym
}

function monthShort(ym) {
  return ym ? ym.substring(5) + '月' : ''
}

const activeMonthData = computed(() => {
  const posters = yearPosters.value
  if (!posters.length) return null
  return posters[Math.min(activeMonthIdx.value, posters.length - 1)]
})

const activeMonthStat = computed(() => {
  const stats = yearMonths.value
  if (!stats.length || !activeMonthData.value) return null
  return stats.find(s => s.year_month === activeMonthData.value.year_month)
})

function selectMonth(idx) {
  activeMonthIdx.value = idx
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.05 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="monthly-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">月度旅程</p>
      <p class="narrative reveal-up" :class="{ visible }">
        <template v-if="peakMonth">
          <span class="highlight">{{ monthLabel(peakMonth.year_month) }}</span> 是你最爱看的一个月<br/>
          看了 <span class="accent">{{ peakMonth.total_count }}</span> 部作品
        </template>
        <template v-else>每月的观影记录</template>
      </p>

      <!-- 月份选择条 -->
      <div class="month-tabs reveal-up" :class="{ visible }" v-if="yearPosters.length">
        <button
          v-for="(m, i) in yearPosters"
          :key="m.year_month"
          class="month-tab"
          :class="{ active: activeMonthIdx === i }"
          @click="selectMonth(i)"
        >
          {{ monthShort(m.year_month) }}
        </button>
      </div>

      <!-- 当前月份海报墙 -->
      <div class="month-display reveal-up" :class="{ visible }" v-if="activeMonthData">
        <div class="month-header">
          <div class="month-big-label">{{ monthLabel(activeMonthData.year_month) }}</div>
          <div class="month-stats" v-if="activeMonthStat">
            <span class="stat-pill">{{ activeMonthStat.total_count }} 次</span>
            <span class="stat-pill">{{ activeMonthStat.movie_count }} 部电影</span>
            <span class="stat-pill">{{ activeMonthStat.episode_count }} 集剧集</span>
          </div>
        </div>

        <div class="poster-grid" :class="'grid-' + Math.min(activeMonthData.posters.length, 10)">
          <div
            v-for="(p, i) in activeMonthData.posters"
            :key="p.trakt_id"
            class="poster-item"
            :style="{ animationDelay: (i * 0.06) + 's' }"
          >
            <img
              v-if="p.poster_url"
              :src="p.poster_url"
              alt=""
              loading="lazy"
              class="poster-img"
              @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
            />
            <div v-if="!p.poster_url" class="poster-img placeholder">
              <span class="placeholder-text">{{ p.title }}</span>
            </div>
            <div v-if="p.poster_url" class="poster-img placeholder" style="display:none">
              <span class="placeholder-text">{{ p.title }}</span>
            </div>
            <div class="poster-overlay">
              <div class="poster-title">{{ p.title }}</div>
              <div class="poster-count" v-if="p.watch_count > 1">{{ p.watch_count }} 次观看</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 月度柱状迷你图 -->
      <div class="mini-trend reveal-up" :class="{ visible }" v-if="yearMonths.length">
        <div class="trend-bars">
          <div
            v-for="(s, i) in yearMonths"
            :key="s.year_month"
            class="trend-bar-wrapper"
            :class="{ active: activeMonthData && s.year_month === activeMonthData.year_month }"
            @click="selectMonth(yearPosters.findIndex(p => p.year_month === s.year_month))"
          >
            <div
              class="trend-bar"
              :style="{
                height: Math.max(4, (s.total_count / Math.max(...yearMonths.map(y => y.total_count)) * 100)) + '%'
              }"
            />
            <div class="trend-bar-label">{{ monthShort(s.year_month) }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.monthly-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 80px 32px;
  background: linear-gradient(180deg, #0d1117 0%, #1a1208 100%);
}
.section-content { max-width: 1100px; width: 100%; }
.section-label { font-size: 0.82rem; color: var(--bean-green); text-align: center; margin-bottom: 12px; font-weight: 600; letter-spacing: 2px; }

/* 月份选择条 */
.month-tabs {
  display: flex; gap: 6px; justify-content: center; flex-wrap: wrap;
  margin-bottom: 36px;
}
.month-tab {
  padding: 8px 20px; border-radius: 24px;
  background: rgba(255,255,255,0.04); border: 1px solid var(--border);
  color: var(--text-dim); font-size: 0.85rem; cursor: pointer;
  transition: all var(--transition);
}
.month-tab:hover {
  background: rgba(168,197,160,0.08);
  color: var(--bean-green-bright);
  border-color: rgba(168,197,160,0.2);
}
.month-tab.active {
  background: linear-gradient(135deg, rgba(168,197,160,0.2), rgba(168,197,160,0.08));
  color: var(--bean-green-bright);
  border-color: rgba(168,197,160,0.4);
  font-weight: 700;
}

/* 当前月份展示 */
.month-display { margin-bottom: 40px; }
.month-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}
.month-big-label {
  font-size: 2.2rem; font-weight: 900; color: var(--text-bright);
  letter-spacing: 4px;
}
.month-stats { display: flex; gap: 8px; }
.stat-pill {
  padding: 5px 14px; border-radius: 16px;
  background: rgba(255,255,255,0.05); border: 1px solid var(--border);
  font-size: 0.8rem; color: var(--text-dim);
}

/* 海报网格 — 自适应列数 */
.poster-grid {
  display: grid; gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
}
.poster-item {
  opacity: 0; animation: fadeInScale 0.5s ease forwards;
  transition: transform 0.3s ease;
  position: relative; overflow: hidden;
  border-radius: var(--radius-sm);
}
.poster-item:hover { transform: translateY(-8px) scale(1.04); z-index: 2; }
.poster-img {
  width: 100%; aspect-ratio: 2/3; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.04);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: all var(--transition); display: block;
}
.poster-img.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 10px; text-align: center;
}
.placeholder-text {
  font-size: 0.78rem; color: var(--text-dim);
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.4;
}
.poster-item:hover .poster-img {
  box-shadow: 0 16px 48px rgba(0,0,0,0.6), 0 0 24px rgba(168,197,160,0.15);
  border-color: var(--border-bright);
}

/* hover 信息浮层 */
.poster-overlay {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 20px 12px 12px;
  background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.85) 100%);
  opacity: 0; transition: opacity var(--transition);
  pointer-events: none; border-radius: 0 0 var(--radius-sm) var(--radius-sm);
}
.poster-item:hover .poster-overlay { opacity: 1; }
.poster-title {
  font-size: 0.78rem; font-weight: 700; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 2px;
}
.poster-count {
  font-size: 0.68rem; color: var(--bean-green); font-weight: 600;
}

/* 迷你趋势图 */
.mini-trend { margin-top: 8px; }
.trend-bars {
  display: flex; gap: 6px; align-items: flex-end;
  height: 90px; padding: 0 4px;
}
.trend-bar-wrapper {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: 6px; cursor: pointer; height: 100%; justify-content: flex-end;
  transition: all var(--transition);
}
.trend-bar {
  width: 100%; max-width: 32px; border-radius: 5px 5px 0 0;
  background: linear-gradient(180deg, rgba(168,197,160,0.5), rgba(168,197,160,0.1));
  transition: all var(--transition);
  min-height: 4px;
}
.trend-bar-wrapper:hover .trend-bar {
  background: linear-gradient(180deg, rgba(168,197,160,0.8), rgba(168,197,160,0.2));
}
.trend-bar-wrapper.active .trend-bar {
  background: linear-gradient(180deg, var(--warm-amber), rgba(212,168,87,0.2));
  box-shadow: 0 0 12px rgba(212,168,87,0.3);
}
.trend-bar-label {
  font-size: 0.65rem; color: var(--text-dim);
  white-space: nowrap;
}

@keyframes fadeInScale { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }

@media (max-width: 768px) {
  .poster-grid { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px; }
  .month-big-label { font-size: 1.5rem; }
  .month-stats { flex-wrap: wrap; }
  .stat-pill { font-size: 0.72rem; padding: 4px 10px; }
  .monthly-section { padding: 60px 16px; }
}
@media (max-width: 480px) {
  .poster-grid { grid-template-columns: repeat(auto-fill, minmax(95px, 1fr)); gap: 8px; }
}
</style>
