<script setup>
import { inject, ref, watch, computed, onMounted } from 'vue'

const totalStats = inject('totalStats')
const monthlyStats = inject('monthlyStats')

const year = new Date().getFullYear()
const visible = ref(false)
const sectionRef = ref(null)

const yearStats = computed(() => {
  const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(year)))
  return {
    count: stats.reduce((a, s) => a + s.total_count, 0),
    minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
    movies: stats.reduce((a, s) => a + s.movie_count, 0),
    episodes: stats.reduce((a, s) => a + s.episode_count, 0),
  }
})

const hours = computed(() => Math.floor(yearStats.value.minutes / 60))
const days = computed(() => (yearStats.value.minutes / (60 * 24)).toFixed(1))

function animateNumber(el, target, duration = 1500) {
  if (!el) return
  const start = 0
  const startTime = performance.now()
  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    el.textContent = Math.floor(start + (target - start) * eased).toLocaleString()
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

const num1 = ref(null), num2 = ref(null), num3 = ref(null), num4 = ref(null)

watch(visible, (v) => {
  if (v) {
    setTimeout(() => {
      animateNumber(num1.value, yearStats.value.count)
      animateNumber(num2.value, hours.value)
      animateNumber(num3.value, yearStats.value.movies)
      animateNumber(num4.value, yearStats.value.episodes)
    }, 200)
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
  <section ref="sectionRef" class="stats-section">
    <div class="section-content">
      <p class="narrative reveal-up" :class="{ visible }">
        在 <span class="highlight">{{ year }}</span> 年
      </p>
      <p class="narrative reveal-up" :class="{ visible }" style="margin-top: -16px; margin-bottom: 40px;">
        你一共看了
      </p>

      <div class="big-number reveal-scale" :class="{ visible }">
        <span ref="num1">0</span>
        <span style="font-size: 1.5rem; margin-left: 8px;">部</span>
      </div>

      <p class="narrative" style="margin-top: 16px;">
        花了 <span class="accent">{{ hours }}</span> 小时
        ≈ <span class="highlight">{{ days }}</span> 个日日夜夜
      </p>

      <div class="stats-grid stagger" :class="{ visible }" style="margin-top: 48px;">
        <div class="stat-item glass-card">
          <div class="stat-num green"><span ref="num2">0</span></div>
          <div class="stat-label">小时</div>
        </div>
        <div class="stat-item glass-card">
          <div class="stat-num" style="color: var(--primary);"><span ref="num3">0</span></div>
          <div class="stat-label">部电影</div>
        </div>
        <div class="stat-item glass-card">
          <div class="stat-num purple"><span ref="num4">0</span></div>
          <div class="stat-label">集剧集</div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.stats-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 80px 24px; position: relative;
  background: linear-gradient(160deg, #1a2e1a 0%, #0d1117 60%);
}
.section-content { max-width: 700px; width: 100%; text-align: center; }
.big-number {
  font-size: 6rem; font-weight: 900;
  background: linear-gradient(135deg, var(--accent), var(--accent-warm));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1.1; font-variant-numeric: tabular-nums;
}
.stats-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
}
.stat-item { padding: 28px 16px; text-align: center; }
.stat-num {
  font-size: 2.5rem; font-weight: 800; font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.stat-num.green {
  background: linear-gradient(135deg, var(--success), var(--teal));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.stat-num.purple {
  background: linear-gradient(135deg, var(--purple), var(--pink));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.stat-label { font-size: 0.85rem; color: var(--text-dim); margin-top: 4px; }

@media (max-width: 768px) {
  .big-number { font-size: 3.5rem; }
  .stat-num { font-size: 1.8rem; }
  .stats-grid { grid-template-columns: 1fr; gap: 12px; }
}
</style>
