<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import { useCountUp } from '@/composables/useTextReveal'

const monthlyStats = inject('monthlyStats')
const firstWatched = inject('firstWatched')
const lastWatched = inject('lastWatched')
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
      animate(numHours.value, hours.value, 1500)
      animate(numDays.value, parseFloat(days.value), 1500)
      animate(numCount.value, yearStats.value.count, 1200)
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
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">{{ selectedYear }} · 光影之旅</p>

      <div class="story-block reveal-up" :class="{ visible }">
        <p class="story-text">
          这一年，你在
          <span class="accent">{{ monthCount }}</span>
          个月里
        </p>
        <p class="story-text">一共观看了</p>
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
        <div class="media-card glass-card" v-if="firstWatched">
          <div class="card-label">年度第一部</div>
          <img v-if="firstWatched.poster_url" class="card-poster" :src="firstWatched.poster_url" alt="" loading="lazy" />
          <div class="card-poster placeholder" v-else><span>{{ firstWatched.title }}</span></div>
          <div class="card-title">{{ firstWatched.title }}</div>
          <div class="card-date">{{ formatDate(firstWatched.watched_at) }}</div>
        </div>
        <div class="media-card glass-card" v-if="lastWatched">
          <div class="card-label">年度最新一部</div>
          <img v-if="lastWatched.poster_url" class="card-poster" :src="lastWatched.poster_url" alt="" loading="lazy" />
          <div class="card-poster placeholder" v-else><span>{{ lastWatched.title }}</span></div>
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
  padding: var(--section-gap) var(--page-margin);
}
.section-content { max-width: 640px; width: 100%; text-align: center; }

.story-text {
  font-size: 1.1rem; color: var(--text-2); line-height: 2; letter-spacing: 1px;
}
.story-text .accent { color: var(--primary-bright); font-weight: 700; font-size: 1.3rem; }

.big-counter {
  margin: 28px 0; display: flex; align-items: baseline; justify-content: center; gap: 8px;
}
.counter-num {
  font-size: clamp(2.8rem, 9vw, 4.5rem); font-weight: 800;
  color: var(--primary-bright); font-variant-numeric: tabular-nums;
  line-height: 1; letter-spacing: -0.02em;
}
.counter-unit { font-size: 1.1rem; color: var(--text-3); }

.time-block {
  display: flex; align-items: center; justify-content: center; gap: 28px;
  margin: 32px 0;
}
.time-item { display: flex; flex-direction: column; gap: 4px; }
.time-num {
  font-size: 2rem; font-weight: 800; color: var(--text-1);
  font-variant-numeric: tabular-nums; line-height: 1;
}
.time-label { font-size: 0.82rem; color: var(--text-3); }
.time-divider { font-size: 1.2rem; color: var(--text-dim); }

.first-last {
  display: flex; gap: 20px; justify-content: center; margin: 40px 0;
  flex-wrap: wrap;
}
.media-card {
  padding: var(--space-md); width: 170px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.card-label { font-size: 0.75rem; color: var(--primary); font-weight: 600; }
.card-poster {
  width: 100px; height: 150px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.03);
}
.card-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 8px; text-align: center; font-size: 0.72rem; color: var(--text-3);
}
.card-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text-1);
  text-align: center; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-date { font-size: 0.75rem; color: var(--text-3); }

.story-ending {
  font-size: 0.9rem; color: var(--text-3); margin-top: 28px;
  letter-spacing: 2px;
}

@media (max-width: 768px) {
  .counter-num { font-size: 2.8rem; }
  .time-num { font-size: 1.6rem; }
  .media-card { width: 145px; }
  .card-poster { width: 80px; height: 120px; }
}
</style>
