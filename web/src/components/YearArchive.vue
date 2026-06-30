<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { formatMinutes } from '@/utils/format'

const monthlyStats = inject('monthlyStats')
const availableYears = inject('availableYears')
const selectedYear = inject('selectedYear')

const visible = ref(false)
const sectionRef = ref(null)
const cardRefs = ref([])

function onTilt(e, idx) {
  const el = cardRefs.value[idx]
  if (!el) return
  const rect = el.getBoundingClientRect()
  const dx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2)
  const dy = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2)
  el.style.transform = `perspective(800px) rotateX(${-dy * 10}deg) rotateY(${dx * 10}deg) translateY(-6px)`
}
function onLeave(idx) {
  const el = cardRefs.value[idx]
  if (el) el.style.transform = ''
}

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
          v-for="(ys, i) in yearStats"
          :key="ys.year"
          class="year-card bean-card glow-border"
          :class="{ current: ys.isCurrent }"
          :ref="el => cardRefs[i] = el"
          @mousemove="onTilt($event, i)"
          @mouseleave="onLeave(i)"
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
            <span>·</span>
            <a href="https://pages.github.com" target="_blank" class="footer-link">GitHub Pages</a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.archive-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
  background: linear-gradient(180deg, var(--cinema-black) 0%, #0d1014 100%);
}
.section-content { max-width: 860px; width: 100%; text-align: center; }

.year-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;
  margin: 36px 0;
}
.year-card {
  padding: 28px 20px; cursor: pointer; position: relative;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  transition: transform 0.15s ease, box-shadow 0.3s ease, border-color 0.3s ease;
  will-change: transform; overflow: hidden;
}
.year-card.current {
  border-color: rgba(168,197,160,0.4);
  box-shadow: var(--glow-green);
}
.year-num {
  font-size: 2.5rem; font-weight: 900;
  background: linear-gradient(135deg, var(--bean-green-bright), var(--bean-green));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1;
}
.year-badge {
  position: absolute; top: 10px; right: 10px;
  padding: 2px 10px; border-radius: 10px;
  background: rgba(168,197,160,0.15); color: var(--bean-green-bright);
  font-size: 0.68rem; font-weight: 700;
}
.year-stats {
  display: flex; gap: 20px; justify-content: center;
}
.year-stat { display: flex; flex-direction: column; gap: 2px; }
.stat-val {
  font-size: 1.1rem; font-weight: 800; color: var(--text-bright);
  font-variant-numeric: tabular-nums;
}
.stat-lbl { font-size: 0.72rem; color: var(--text-dim); }
.year-hint {
  font-size: 0.72rem; color: var(--text-dim);
  opacity: 0; transition: opacity var(--transition);
}
.year-card:hover .year-hint { opacity: 1; }

.archive-footer {
  margin-top: 48px; padding: 32px 0;
  border-top: 1px solid var(--border);
}
.footer-text {
  font-size: 1.1rem; color: var(--text-bright); font-weight: 600;
  margin-bottom: 8px; letter-spacing: 2px;
}
.footer-sub {
  font-size: 0.88rem; color: var(--text-dim); margin-bottom: 20px;
  letter-spacing: 1px; font-style: italic;
}
.footer-links {
  display: flex; gap: 8px; justify-content: center; align-items: center;
  font-size: 0.78rem; color: var(--text-dim);
}
.footer-link { color: var(--bean-green-dim); transition: color var(--transition); }
.footer-link:hover { color: var(--bean-green-bright); }

@media (max-width: 768px) {
  .year-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .year-num { font-size: 2rem; }
  .year-stats { gap: 14px; }
}
</style>
