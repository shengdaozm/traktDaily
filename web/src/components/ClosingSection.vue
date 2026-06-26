<script setup>
import { inject, ref, computed, onMounted } from 'vue'

const monthlyStats = inject('monthlyStats')
const totalStats = inject('totalStats')
const visible = ref(false)
const sectionRef = ref(null)

const year = new Date().getFullYear()

const yearStats = computed(() => {
  const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(year)))
  return {
    count: stats.reduce((a, s) => a + s.total_count, 0),
    minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
    movies: stats.reduce((a, s) => a + s.movie_count, 0),
    episodes: stats.reduce((a, s) => a + s.episode_count, 0),
  }
})

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.2 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="closing-section">
    <div class="section-content">
      <div class="closing-content" :class="{ visible }">
        <div class="closing-icon">🎬</div>
        <h2 class="closing-title">{{ year }} 观影报告</h2>
        <div class="closing-summary">
          <div class="summary-item">
            <span class="summary-num">{{ yearStats.count }}</span>
            <span class="summary-label">部作品</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-item">
            <span class="summary-num">{{ Math.floor(yearStats.minutes / 60) }}</span>
            <span class="summary-label">小时</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-item">
            <span class="summary-num">{{ monthlyStats.filter(s => s.year_month?.startsWith(String(year))).length }}</span>
            <span class="summary-label">个月</span>
          </div>
        </div>
        <p class="closing-text">
          感谢光影陪伴的每一天<br/>
          新的一年，继续在故事中寻找世界
        </p>
        <a href="https://trakt.tv" target="_blank" class="closing-link">
          在 Trakt 查看更多 →
        </a>
      </div>
    </div>
    <footer class="closing-footer">
      数据来源 <a href="https://trakt.tv" target="_blank">Trakt</a>
      · 海报 <a href="https://themoviedb.org" target="_blank">TMDB</a>
      · <a href="https://pages.github.com" target="_blank">GitHub Pages</a>
    </footer>
  </section>
</template>

<style scoped>
.closing-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px 40px; position: relative;
  background: linear-gradient(180deg, #0d1117 0%, #14122a 100%);
}
.section-content { max-width: 600px; width: 100%; text-align: center; }
.closing-content { opacity: 0; transform: translateY(30px); transition: opacity 1s ease, transform 1s ease; }
.closing-content.visible { opacity: 1; transform: translateY(0); }
.closing-icon { font-size: 4rem; margin-bottom: 16px; }
.closing-title {
  font-size: 1.8rem; font-weight: 800; color: var(--text-bright);
  margin-bottom: 32px; letter-spacing: 1px;
}
.closing-summary {
  display: flex; align-items: center; justify-content: center; gap: 24px;
  margin-bottom: 32px;
}
.summary-item { display: flex; flex-direction: column; gap: 4px; }
.summary-num {
  font-size: 2.5rem; font-weight: 900; font-variant-numeric: tabular-nums;
  background: linear-gradient(135deg, var(--accent), var(--accent-warm));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.summary-label { font-size: 0.82rem; color: var(--text-dim); }
.summary-divider { width: 1px; height: 40px; background: var(--border); }
.closing-text {
  font-size: 1rem; color: var(--text-dim); line-height: 2;
  margin-bottom: 28px;
}
.closing-link {
  display: inline-block; padding: 8px 20px; border-radius: 20px;
  background: rgba(88,166,255,0.1); border: 1px solid rgba(88,166,255,0.3);
  color: var(--primary); font-size: 0.88rem; font-weight: 600;
  transition: all var(--transition);
}
.closing-link:hover { background: rgba(88,166,255,0.2); }
.closing-footer {
  position: absolute; bottom: 20px; left: 0; right: 0;
  text-align: center; font-size: 0.78rem; color: var(--muted);
}
.closing-footer a { color: var(--text-dim); }

@media (max-width: 768px) {
  .summary-num { font-size: 1.8rem; }
  .closing-title { font-size: 1.4rem; }
  .closing-summary { gap: 16px; }
}
</style>
