<script setup>
import { inject, ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useCountUp } from '@/composables/useTextReveal'
import FloatingLights from '@/components/FloatingLights.vue'

const monthlyStats = inject('monthlyStats')
const bingeStats = inject('bingeStats')
const hourlyStats = inject('hourlyStats')
const selectedYear = inject('selectedYear')

const emit = defineEmits(['navigate'])

const visible = ref(false)
const sectionRef = ref(null)
const { animate } = useCountUp()

const cardRefs = ref([])

const year = selectedYear

const yearStats = computed(() => {
  const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(year.value)))
  return {
    count: stats.reduce((a, s) => a + s.total_count, 0),
    minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
    movies: stats.reduce((a, s) => a + s.movie_count, 0),
    episodes: stats.reduce((a, s) => a + s.episode_count, 0),
  }
})

const hours = computed(() => Math.floor(yearStats.value.minutes / 60))

const nightRatio = computed(() => {
  const hourly = hourlyStats.value || []
  const night = hourly.filter(h => h.hour != null && (h.hour >= 22 || h.hour < 2)).reduce((a, h) => a + h.count, 0)
  const total = hourly.reduce((a, h) => a + (h.count || 0), 0)
  return total > 0 ? Math.round(night / total * 100) : 0
})

const bingeRatio = computed(() => {
  const b = bingeStats.value || {}
  return b.binge_ratio ? Math.round(b.binge_ratio * 100) : 0
})

const metrics = computed(() => [
  { icon: '⏱️', label: '观影时长', value: hours.value, unit: '小时', color: 'var(--bean-green)', target: 4 },
  { icon: '🎬', label: '观影总量', value: yearStats.value.count, unit: '部', color: 'var(--warm-amber)', target: 4 },
  { icon: '🔥', label: '连贯追剧', value: bingeRatio.value, unit: '%', color: 'var(--soft-pink)', target: 4 },
  { icon: '🌙', label: '深夜观影', value: nightRatio.value, unit: '%', color: 'var(--haze-blue)', target: 4 },
  { icon: '📺', label: '完结剧集', value: yearStats.value.episodes, unit: '集', color: 'var(--purple)', target: 4 },
])

function triggerBurst(el) {
  if (!el) return
  const rect = el.getBoundingClientRect()
  for (let i = 0; i < 8; i++) {
    const p = document.createElement('span')
    p.className = 'burst-particle'
    p.style.left = '50%'
    p.style.top = '50%'
    const angle = (Math.PI * 2 * i) / 8
    p.style.setProperty('--bx', Math.cos(angle) * 40 + 'px')
    p.style.setProperty('--by', Math.sin(angle) * 40 + 'px')
    el.appendChild(p)
    setTimeout(() => p.remove(), 800)
  }
}

watch(visible, (v) => {
  if (v) {
    metrics.value.forEach((m, i) => {
      setTimeout(() => {
        if (cardRefs.value[i]) {
          animate(cardRefs.value[i], m.value, 1500)
          triggerBurst(cardRefs.value[i]?.parentElement)
        }
      }, 300 + i * 200)
    })
  }
})

function onCardMove(e, idx) {
  const el = cardRefs.value[idx]?.parentElement
  if (!el) return
  const rect = el.getBoundingClientRect()
  const dx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2)
  const dy = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2)
  el.style.transform = `perspective(800px) rotateX(${-dy * 12}deg) rotateY(${dx * 12}deg) translateY(-6px)`
}

function onCardLeave(idx) {
  const el = cardRefs.value[idx]?.parentElement
  if (el) el.style.transform = ''
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.15 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="overview-section">
    <FloatingLights :count="3" />
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">核心数据总览</p>
      <p class="narrative reveal-up" :class="{ visible }">
        <span class="highlight">{{ year }}</span> 年，你的观影全景
      </p>

      <div class="metrics-grid stagger" :class="{ visible }">
        <div
          v-for="(m, i) in metrics"
          :key="i"
          class="metric-card bean-card glow-border tilt-card"
          @click="emit('navigate', m.target)"
          @mousemove="onCardMove($event, i)"
          @mouseleave="onCardLeave(i)"
        >
          <div class="tilt-content">
            <div class="metric-icon">{{ m.icon }}</div>
            <div class="metric-value">
              <span :ref="el => cardRefs[i] = el">0</span>
              <span class="metric-unit">{{ m.unit }}</span>
            </div>
            <div class="metric-label">{{ m.label }}</div>
            <div class="metric-hint">点击查看详情 →</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.overview-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px; position: relative; overflow: hidden;
  background: linear-gradient(180deg, #0d1410 0%, var(--cinema-black) 100%);
}
.section-content { max-width: 860px; width: 100%; text-align: center; position: relative; z-index: 1; }

.metrics-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;
  margin-top: 40px;
}
.metric-card {
  padding: 28px 18px; text-align: center; cursor: pointer;
  position: relative; overflow: hidden;
  transition: transform 0.15s ease, box-shadow 0.3s ease;
  will-change: transform;
}
.metric-card:hover {
  box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 0 30px rgba(168,197,160,0.15);
}
.tilt-content { transform: translateZ(30px); }
.metric-icon {
  font-size: 2rem; margin-bottom: 4px;
  transition: transform 0.3s ease;
}
.metric-card:hover .metric-icon { transform: scale(1.2) rotate(-5deg); }
.metric-value {
  font-size: 2.4rem; font-weight: 900; font-variant-numeric: tabular-nums;
  line-height: 1.1; display: flex; align-items: baseline; justify-content: center; gap: 4px;
  background: linear-gradient(135deg, var(--bean-green-bright), var(--bean-green));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-unit { font-size: 0.9rem; color: var(--text-dim); font-weight: 600; -webkit-text-fill-color: var(--text-dim); }
.metric-label { font-size: 0.88rem; color: var(--text); font-weight: 600; }
.metric-hint {
  font-size: 0.72rem; color: var(--text-dim); opacity: 0;
  transition: opacity var(--transition);
}
.metric-card:hover .metric-hint { opacity: 1; }

@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .metric-value { font-size: 1.8rem; }
  .metric-card { padding: 20px 12px; }
}
</style>
