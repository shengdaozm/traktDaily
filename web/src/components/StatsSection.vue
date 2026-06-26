<script setup>
import { ref, watch, onMounted, computed } from 'vue'

const props = defineProps({
  stats: { type: Object, required: true },
  monthlyStats: { type: Array, default: () => [] },
})

function animateValue(el, start, end, duration) {
  if (start === end) { el.textContent = end.toLocaleString(); return }
  const range = end - start
  const increment = range > 100 ? Math.ceil(range / 60) : 1
  let current = start
  const stepTime = Math.max(Math.floor(duration / (range / increment)), 16)
  const timer = setInterval(() => {
    current += increment
    if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
      el.textContent = end.toLocaleString()
      clearInterval(timer)
    } else {
      el.textContent = current.toLocaleString()
    }
  }, stepTime)
}

const statRefs = ref([])
const cards = computed(() => [
  { icon: '📊', value: props.stats.total, label: '总观影记录', color: 'var(--primary)' },
  { icon: '⏱️', value: props.stats.hours, label: '总时长（小时）', color: 'var(--accent)' },
  { icon: '🎥', value: props.stats.movies, label: '电影', color: 'var(--success)' },
  { icon: '📺', value: props.stats.episodes, label: '剧集', color: 'var(--purple)' },
])

function runAnimation() {
  const durations = [1000, 1000, 800, 800]
  cards.value.forEach((c, i) => {
    const el = statRefs.value[i]
    if (el) animateValue(el, 0, c.value, durations[i])
  })
}

onMounted(runAnimation)
watch(() => props.stats, runAnimation, { deep: true })

const monthBarData = computed(() => {
  const stats = props.monthlyStats
  if (!stats.length) return null
  const now = new Date()
  const thisMonth = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0')
  const curr = stats.find(s => s.year_month === thisMonth)
  if (!curr) return null
  const prevDate = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  const prevMonth = prevDate.getFullYear() + '-' + String(prevDate.getMonth() + 1).padStart(2, '0')
  const prev = stats.find(s => s.year_month === prevMonth)
  const dayOfMonth = now.getDate()
  const dailyAvg = (curr.total_count / dayOfMonth).toFixed(1)
  let trend = null
  if (prev) {
    const pct = ((curr.total_count - prev.total_count) / prev.total_count * 100).toFixed(0)
    if (pct > 0) trend = { type: 'up', text: `↑${pct}%` }
    else if (pct < 0) trend = { type: 'down', text: `↓${Math.abs(pct)}%` }
    else trend = { type: 'flat', text: '—' }
  }
  return { thisMonth, curr, dailyAvg, trend }
})
</script>

<template>
  <div class="stats-section">
    <div class="stats-row">
      <div
        v-for="(card, i) in cards" :key="i"
        class="stat-card"
        :style="{ '--card-color': card.color }"
      >
        <div class="stat-icon">{{ card.icon }}</div>
        <div class="stat-value" :ref="el => statRefs[i] = el" :style="{ color: card.color }">0</div>
        <div class="stat-label">{{ card.label }}</div>
      </div>
    </div>

    <div v-if="monthBarData" class="month-bar">
      <span class="month-label">📅 本月（{{ monthBarData.thisMonth }}）</span>
      <div class="divider" />
      <span class="month-stat">📊 <b>{{ monthBarData.curr.total_count }}</b> 次
        <span v-if="monthBarData.trend" class="trend" :class="monthBarData.trend.type">
          {{ monthBarData.trend.text }}
        </span>
      </span>
      <div class="divider" />
      <span class="month-stat">⏱️ <b>{{ Math.round(monthBarData.curr.total_minutes / 60) }}</b> 小时</span>
      <div class="divider" />
      <span class="month-stat">📈 日均 <b>{{ monthBarData.dailyAvg }}</b> 次</span>
      <div class="divider" />
      <span class="month-stat">🎥 <b>{{ monthBarData.curr.movie_count }}</b> 部电影</span>
      <div class="divider" />
      <span class="month-stat">📺 <b>{{ monthBarData.curr.episode_count }}</b> 集剧集</span>
    </div>
  </div>
</template>

<style scoped>
.stats-section { margin-bottom: 24px; }
.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  margin-bottom: 16px;
}
.stat-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px 20px; text-align: center;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  transition: transform var(--transition), border-color var(--transition), box-shadow var(--transition);
  position: relative; overflow: hidden;
  animation: fadeInUp 0.5s ease both;
}
.stat-card:nth-child(1) { animation-delay: 0.05s; }
.stat-card:nth-child(2) { animation-delay: 0.1s; }
.stat-card:nth-child(3) { animation-delay: 0.15s; }
.stat-card:nth-child(4) { animation-delay: 0.2s; }
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--card-color), transparent); opacity: 0.8;
}
.stat-card:hover {
  transform: translateY(-4px); border-color: var(--border-bright);
  box-shadow: var(--shadow-hover);
}
.stat-icon { font-size: 1.5rem; margin-bottom: 8px; }
.stat-value {
  font-size: 2.1rem; font-weight: 800; color: var(--text-bright);
  font-variant-numeric: tabular-nums; line-height: 1.2;
}
.stat-label { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }

.month-bar {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; flex-wrap: wrap; padding: 14px 20px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  animation: fadeInUp 0.5s ease 0.25s both;
}
.month-label { font-size: 0.85rem; color: var(--muted); font-weight: 600; }
.month-stat { font-size: 0.88rem; color: var(--text); }
.month-stat b { color: var(--text-bright); font-weight: 700; font-variant-numeric: tabular-nums; }
.trend { display: inline-flex; margin-left: 4px; font-size: 0.78rem; font-weight: 600; }
.trend.up { color: var(--success); }
.trend.down { color: var(--danger); }
.trend.flat { color: var(--muted); }
.divider { width: 1px; height: 16px; background: var(--border); }

@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .stat-card { padding: 16px 14px; }
  .stat-value { font-size: 1.5rem; }
  .month-bar { gap: 10px; }
  .divider { display: none; }
}
</style>
