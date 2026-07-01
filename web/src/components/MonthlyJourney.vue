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
  return monthNames[parseInt(ym.substring(5)) - 1] || ym
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

      <div class="month-tabs reveal-up" :class="{ visible }" v-if="yearPosters.length">
        <button
          v-for="(m, i) in yearPosters"
          :key="m.year_month"
          class="month-tab"
          :class="{ active: activeMonthIdx === i }"
          @click="selectMonth(i)"
        >{{ monthShort(m.year_month) }}</button>
      </div>

      <div class="month-display reveal-up" :class="{ visible }" v-if="activeMonthData">
        <div class="month-header">
          <div class="month-big-label">{{ monthLabel(activeMonthData.year_month) }}</div>
          <div class="month-stats" v-if="activeMonthStat">
            <span class="stat-pill">{{ activeMonthStat.total_count }} 次</span>
            <span class="stat-pill">{{ activeMonthStat.movie_count }} 电影</span>
            <span class="stat-pill">{{ activeMonthStat.episode_count }} 集</span>
          </div>
        </div>

        <div class="poster-grid">
          <div
            v-for="(p, i) in activeMonthData.posters"
            :key="p.trakt_id"
            class="poster-item"
            :style="{ animationDelay: (i * 0.04) + 's' }"
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
              <span>{{ p.title }}</span>
            </div>
            <div v-if="p.poster_url" class="poster-img placeholder" style="display:none">
              <span>{{ p.title }}</span>
            </div>
            <div class="poster-info">
              <div class="poster-title">{{ p.title }}</div>
              <div class="poster-count" v-if="p.watch_count > 1">{{ p.watch_count }} 次</div>
            </div>
          </div>
        </div>
      </div>

      <div class="mini-trend reveal-up" :class="{ visible }" v-if="yearMonths.length">
        <div class="trend-bars">
          <div
            v-for="(s, i) in yearMonths"
            :key="s.year_month"
            class="trend-bar-wrapper"
            :class="{ active: activeMonthData && s.year_month === activeMonthData.year_month }"
            @click="selectMonth(yearPosters.findIndex(p => p.year_month === s.year_month))"
          >
            <div class="trend-bar" :style="{ height: Math.max(4, (s.total_count / Math.max(...yearMonths.map(y => y.total_count)) * 100)) + '%' }" />
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
  padding: var(--section-gap) var(--page-margin);
}
.section-content { max-width: 900px; width: 100%; }

.month-tabs {
  display: flex; gap: 6px; justify-content: center; flex-wrap: wrap;
  margin-bottom: 32px;
}
.month-tab {
  padding: 6px 16px; border-radius: var(--radius);
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  color: var(--text-3); font-size: 0.82rem; cursor: pointer;
  transition: all var(--transition);
}
.month-tab:hover { color: var(--text-2); border-color: var(--border-bright); }
.month-tab.active {
  background: rgba(134, 168, 156, 0.1);
  color: var(--primary-bright);
  border-color: rgba(134, 168, 156, 0.25);
}

.month-display { margin-bottom: 40px; }
.month-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}
.month-big-label {
  font-size: 1.6rem; font-weight: 800; color: var(--text-1); letter-spacing: 2px;
}
.month-stats { display: flex; gap: 8px; }
.stat-pill {
  padding: 4px 12px; border-radius: var(--radius);
  background: rgba(255,255,255,0.04); border: 1px solid var(--border);
  font-size: 0.78rem; color: var(--text-3);
}

.poster-grid {
  display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
}
.poster-item {
  opacity: 0; animation: fadeIn 0.4s ease forwards;
  transition: transform var(--transition);
}
.poster-item:hover { transform: translateY(-3px); }
.poster-img {
  width: 100%; aspect-ratio: 2/3; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.03);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: box-shadow var(--transition);
}
.poster-img.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 8px; text-align: center; font-size: 0.72rem; color: var(--text-3);
}
.poster-item:hover .poster-img { box-shadow: var(--shadow-hover); }
.poster-info { padding: 6px 2px 0; }
.poster-title {
  font-size: 0.75rem; font-weight: 600; color: var(--text-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.poster-count { font-size: 0.65rem; color: var(--primary); }

.mini-trend { margin-top: 8px; }
.trend-bars {
  display: flex; gap: 6px; align-items: flex-end; height: 72px; padding: 0 4px;
}
.trend-bar-wrapper {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: 4px; cursor: pointer; height: 100%; justify-content: flex-end;
}
.trend-bar {
  width: 100%; max-width: 28px; border-radius: 3px 3px 0 0;
  background: rgba(255,255,255,0.08); min-height: 4px;
  transition: background var(--transition);
}
.trend-bar-wrapper:hover .trend-bar { background: rgba(134,168,156,0.3); }
.trend-bar-wrapper.active .trend-bar { background: var(--primary); }
.trend-bar-label { font-size: 0.62rem; color: var(--text-3); white-space: nowrap; }

@media (max-width: 768px) {
  .poster-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
  .month-big-label { font-size: 1.3rem; }
}
</style>
