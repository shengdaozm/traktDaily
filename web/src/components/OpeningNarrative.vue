<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import { useCountUp } from '@/composables/useTextReveal'
import FloatingLights from '@/components/FloatingLights.vue'

const monthlyStats = inject('monthlyStats')
const firstWatched = inject('firstWatched')
const lastWatched = inject('lastWatched')
const totalStats = inject('totalStats')
const selectedYear = inject('selectedYear')

const visible = ref(false)
const sectionRef = ref(null)
const { animate } = useCountUp()

const numHours = ref(null)
const numDays = ref(null)
const numCount = ref(null)

const yearStats = computed(() => {
  const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(selectedYear.value)))
  return {
    count: stats.reduce((a, s) => a + s.total_count, 0),
    minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
    movies: stats.reduce((a, s) => a + s.movie_count, 0),
    episodes: stats.reduce((a, s) => a + s.episode_count, 0),
  }
})

const hours = computed(() => Math.floor(yearStats.value.minutes / 60))
const days = computed(() => (yearStats.value.minutes / (60 * 24)).toFixed(1))

const monthCount = computed(() => {
  return (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(selectedYear.value))).length
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}月${d.getDate()}日`
  } catch { return '' }
}

watch(visible, (v) => {
  if (v) {
    setTimeout(() => {
      animate(numHours.value, hours.value, 1800)
      animate(numDays.value, parseFloat(days.value), 1800)
      animate(numCount.value, yearStats.value.count, 1500)
    }, 300)
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
  <section ref="sectionRef" class="narrative-section">
    <FloatingLights :count="3" />
    <div class="bg-glow" />
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">{{ selectedYear }} · 光影之旅</p>

      <div class="story-block reveal-up" :class="{ visible }">
        <p class="story-text">
          这一年，你在
          <span class="accent">{{ monthCount }}</span>
          个月里
        </p>
        <p class="story-text">
          一共观看了
        </p>
      </div>

      <div class="big-counter reveal-scale" :class="{ visible }">
        <span ref="numCount" class="counter-num">0</span>
        <span class="counter-unit">部作品</span>
      </div>

      <div class="time-block reveal-up" :class="{ visible }">
        <div class="time-item">
          <span ref="numHours" class="time-num">0</span>
          <span class="time-label">小时</span>
        </div>
        <div class="time-divider">≈</div>
        <div class="time-item">
          <span ref="numDays" class="time-num">0</span>
          <span class="time-label">个日夜</span>
        </div>
      </div>

      <div class="first-last stagger" :class="{ visible }" v-if="firstWatched || lastWatched">
        <div class="media-card bean-card" v-if="firstWatched">
          <div class="card-label">🎬 年度第一部</div>
          <img v-if="firstWatched.poster_url" class="card-poster" :src="firstWatched.poster_url" alt="" loading="lazy" />
          <div class="card-poster placeholder" v-else>🎥</div>
          <div class="card-title">{{ firstWatched.title }}</div>
          <div class="card-date">{{ formatDate(firstWatched.watched_at) }}</div>
        </div>
        <div class="media-card bean-card" v-if="lastWatched">
          <div class="card-label">🏁 年度最新一部</div>
          <img v-if="lastWatched.poster_url" class="card-poster" :src="lastWatched.poster_url" alt="" loading="lazy" />
          <div class="card-poster placeholder" v-else>📺</div>
          <div class="card-title">{{ lastWatched.title }}</div>
          <div class="card-date">{{ formatDate(lastWatched.watched_at) }}</div>
        </div>
      </div>

      <p class="story-ending reveal-up" :class="{ visible }">
        每一次按下播放，都是一次新的旅程
      </p>
    </div>
  </section>
</template>

<style scoped>
.narrative-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px; position: relative; overflow: hidden;
  background: linear-gradient(180deg, var(--cinema-black) 0%, #0d1410 100%);
}
.bg-glow {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 600px; height: 600px; border-radius: 50%;
  background: radial-gradient(circle, rgba(168,197,160,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.section-content { max-width: 680px; width: 100%; text-align: center; position: relative; z-index: 1; }

.story-text {
  font-size: 1.15rem; color: var(--text); line-height: 2;
  letter-spacing: 1px;
}
.story-text .accent { color: var(--bean-green-bright); font-weight: 700; font-size: 1.3rem; }

.big-counter {
  margin: 24px 0; display: flex; align-items: baseline; justify-content: center; gap: 8px;
}
.counter-num {
  font-size: 5.5rem; font-weight: 900; font-variant-numeric: tabular-nums;
  background: linear-gradient(135deg, var(--bean-green-bright), var(--bean-green));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1;
}
.counter-unit { font-size: 1.2rem; color: var(--text-dim); }

.time-block {
  display: flex; align-items: center; justify-content: center; gap: 24px;
  margin: 32px 0;
}
.time-item { display: flex; flex-direction: column; gap: 4px; }
.time-num {
  font-size: 2.2rem; font-weight: 800; color: var(--warm-amber);
  font-variant-numeric: tabular-nums; line-height: 1;
}
.time-label { font-size: 0.85rem; color: var(--text-dim); }
.time-divider { font-size: 1.5rem; color: var(--text-dim); }

.first-last {
  display: flex; gap: 20px; justify-content: center; margin: 36px 0;
  flex-wrap: wrap;
}
.media-card {
  padding: 16px; border-radius: var(--radius); width: 180px;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.card-label { font-size: 0.75rem; color: var(--bean-green); font-weight: 600; }
.card-poster {
  width: 100px; height: 150px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.04);
}
.card-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; color: var(--text-dim);
}
.card-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text-bright);
  text-align: center; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-date { font-size: 0.75rem; color: var(--text-dim); }

.story-ending {
  font-size: 0.95rem; color: var(--text-dim); margin-top: 24px;
  letter-spacing: 2px; font-style: italic;
}

@media (max-width: 768px) {
  .counter-num { font-size: 3.5rem; }
  .time-num { font-size: 1.6rem; }
  .media-card { width: 150px; }
  .card-poster { width: 80px; height: 120px; }
}
</style>
