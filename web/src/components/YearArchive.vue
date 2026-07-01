<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { formatMinutes } from '@/utils/format'

const monthlyStats = inject('monthlyStats')
const availableYears = inject('availableYears')
const selectedYear = inject('selectedYear')

const visible = ref(false)
const sectionRef = ref(null)

const yearStats = computed(() => {
  return (availableYears.value || []).map(y => {
    const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(y)))
    return {
      year: y,
      count: stats.reduce((a, s) => a + s.total_count, 0),
      minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
      movies: stats.reduce((a, s) => a + s.movie_count, 0),
      episodes: stats.reduce((a, s) => a + s.episode_count, 0),
      months: stats.length,
      isCurrent: y === selectedYear.value,
    }
  }).sort((a, b) => b.year - a.year)
})

function selectYear(y) {
  selectedYear.value = y
  document.getElementById('section-0')?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.1 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="archive-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">历年观影报告</p>
      <p class="narrative reveal-up" :class="{ visible }">
        光阴流转，每一年都有独特的故事
      </p>

      <div class="year-grid stagger" :class="{ visible }">
        <div
          v-for="ys in yearStats"
          :key="ys.year"
          class="year-card glass-card"
          :class="{ current: ys.isCurrent }"
          @click="selectYear(ys.year)"
        >
          <div class="year-num">{{ ys.year }}</div>
          <div class="year-badge" v-if="ys.isCurrent">当前</div>
          <div class="year-stats">
            <div class="year-stat">
              <span class="stat-val">{{ ys.count }}</span>
              <span class="stat-lbl">部</span>
            </div>
            <div class="year-stat">
              <span class="stat-val">{{ Math.floor(ys.minutes / 60) }}</span>
              <span class="stat-lbl">小时</span>
            </div>
            <div class="year-stat">
              <span class="stat-val">{{ ys.months }}</span>
              <span class="stat-lbl">月</span>
            </div>
          </div>
          <div class="year-hint">{{ ys.isCurrent ? '正在浏览' : '点击查看' }} →</div>
        </div>
      </div>

      <div class="archive-footer reveal-up" :class="{ visible }">
        <div class="footer-content">
          <p class="footer-text">感谢光影陪伴的每一天</p>
          <p class="footer-sub">新的一年，继续在故事中寻找世界</p>
          <div class="footer-links">
            <a href="https://trakt.tv" target="_blank" class="footer-link">Trakt</a>
            <span>·</span>
            <a href="https://themoviedb.org" target="_blank" class="footer-link">TMDB</a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.archive-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: var(--section-gap) var(--page-margin);
}
.section-content { max-width: 860px; width: 100%; text-align: center; }

.year-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
  margin: 36px 0;
}
.year-card {
  padding: var(--space-lg) var(--space-md); cursor: pointer; position: relative;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  transition: transform var(--transition), box-shadow var(--transition);
}
.year-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.year-card.current { border-color: rgba(134,168,156,0.2); }
.year-num {
  font-size: 2.2rem; font-weight: 800; color: var(--primary-bright);
  font-variant-numeric: tabular-nums; line-height: 1;
}
.year-badge {
  position: absolute; top: 10px; right: 10px;
  padding: 2px 10px; border-radius: var(--radius);
  background: rgba(134,168,156,0.1); color: var(--primary-bright);
  font-size: 0.68rem; font-weight: 700;
}
.year-stats { display: flex; gap: 20px; }
.year-stat { display: flex; flex-direction: column; gap: 2px; }
.stat-val { font-size: 1.05rem; font-weight: 700; color: var(--text-1); font-variant-numeric: tabular-nums; }
.stat-lbl { font-size: 0.72rem; color: var(--text-3); }
.year-hint { font-size: 0.72rem; color: var(--text-3); opacity: 0; transition: opacity var(--transition); }
.year-card:hover .year-hint { opacity: 1; }

.archive-footer {
  margin-top: 48px; padding-top: 32px; border-top: 1px solid var(--border);
}
.footer-text {
  font-size: 1.05rem; color: var(--text-1); font-weight: 600;
  margin-bottom: 8px; letter-spacing: 2px;
}
.footer-sub {
  font-size: 0.85rem; color: var(--text-3); margin-bottom: 20px; letter-spacing: 1px;
}
.footer-links {
  display: flex; gap: 8px; justify-content: center; align-items: center;
  font-size: 0.78rem; color: var(--text-3);
}
.footer-link { color: var(--primary-dim); transition: color var(--transition); }
.footer-link:hover { color: var(--primary-bright); }

@media (max-width: 768px) {
  .year-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .year-num { font-size: 1.8rem; }
}
</style>

