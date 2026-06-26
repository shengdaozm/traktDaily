<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { traktUrl, translateGenre } from '@/utils/genres'
import { relativeDate, formatMinutes } from '@/utils/format'

const topMedia = inject('topMedia')
const mediaMap = inject('mediaMap')
const visible = ref(false)
const sectionRef = ref(null)

const filter = ref('all')
const sortBy = ref('recent')
const visibleCount = ref(24)

const library = computed(() => {
  const items = topMedia.value || []
  return items.map(m => {
    const media = mediaMap.value?.get(m.trakt_id)
    return {
      key: m.trakt_id, title: m.title || 'Unknown',
      poster_url: m.poster_url || media?.poster_url,
      media_type: m.media_type === 'episode' ? 'episode' : m.media_type,
      year: media?.year, rating: m.rating || media?.rating,
      genres: media?.genres ? JSON.parse(media.genres) : (m.genres ? JSON.parse(m.genres) : []),
      slug: media?.slug, count: m.watch_count || 0,
      total_minutes: m.total_minutes || 0, last_watched: m.last_watched || '',
      item: m,
    }
  })
})

const filtered = computed(() => {
  let list = library.value
  if (filter.value !== 'all') list = list.filter(m => m.media_type === filter.value)
  const sorted = [...list]
  if (sortBy.value === 'recent') sorted.sort((a, b) => (b.last_watched || '').localeCompare(a.last_watched || ''))
  else if (sortBy.value === 'rating') sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0))
  else if (sortBy.value === 'time') sorted.sort((a, b) => b.total_minutes - a.total_minutes)
  return sorted
})

const displayed = computed(() => filtered.value.slice(0, visibleCount.value))
const hasMore = computed(() => visibleCount.value < filtered.value.length)
const showCounts = computed(() => ({
  all: library.value.length,
  movie: library.value.filter(m => m.media_type === 'movie').length,
  episode: library.value.filter(m => m.media_type === 'episode').length,
}))

function onImgError(e) {
  e.target.style.display = 'none'
  e.target.nextElementSibling?.style.setProperty('display', 'flex')
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.05 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="library-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">🎬 剧库</p>
      <p class="narrative reveal-up" :class="{ visible }">
        每一部作品，都是一段独特的记忆
      </p>

      <div class="controls reveal-up" :class="{ visible }">
        <div class="filters">
          <button :class="{ active: filter === 'all' }" @click="filter = 'all'">全部 <span class="badge">{{ showCounts.all }}</span></button>
          <button :class="{ active: filter === 'episode' }" @click="filter = 'episode'">📺 剧集 <span class="badge">{{ showCounts.episode }}</span></button>
          <button :class="{ active: filter === 'movie' }" @click="filter = 'movie'">🎥 电影 <span class="badge">{{ showCounts.movie }}</span></button>
        </div>
        <select v-model="sortBy" class="sort-select">
          <option value="recent">最近观看</option>
          <option value="time">观看时长</option>
          <option value="rating">评分最高</option>
        </select>
      </div>

      <div class="grid">
        <a v-for="(m, i) in displayed" :key="m.key"
          :href="traktUrl(m.item, mediaMap)" target="_blank"
          class="card"
          :style="{ animationDelay: (i % 24) * 0.03 + 's' }"
        >
          <div class="poster-wrapper">
            <img v-if="m.poster_url" class="poster" :src="m.poster_url" alt="" loading="lazy" @error="onImgError" />
            <div v-if="!m.poster_url" class="poster placeholder">{{ m.media_type === 'movie' ? '🎥' : '📺' }}</div>
            <div v-if="m.poster_url" class="poster placeholder" style="display:none">{{ m.media_type === 'movie' ? '🎥' : '📺' }}</div>
            <div class="count-badge">{{ m.count }} 次</div>
            <div v-if="m.rating" class="rating-badge">⭐ {{ Number(m.rating).toFixed(1) }}</div>
          </div>
          <div class="info">
            <div class="title" :title="m.title">{{ m.title }}</div>
            <div class="meta">
              <span class="type" :class="m.media_type">{{ m.media_type === 'movie' ? '电影' : '剧集' }}</span>
              <span v-if="m.year">{{ m.year }}</span>
            </div>
            <div class="genres" v-if="m.genres?.length">
              <span v-for="g in m.genres.slice(0, 3)" :key="g" class="genre-tag">{{ translateGenre(g) }}</span>
            </div>
            <div class="stats">
              <span>⏱️ {{ formatMinutes(m.total_minutes) }}</span>
              <span>·</span>
              <span>{{ relativeDate(m.last_watched) }}</span>
            </div>
          </div>
        </a>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="visibleCount += 24">加载更多</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.library-section {
  min-height: 100vh; display: flex; align-items: flex-start; justify-content: center;
  padding: 100px 24px;
  background: linear-gradient(160deg, #0d1117 0%, #1a2e1a 100%);
}
.section-content { max-width: 900px; width: 100%; }
.section-label { font-size: 0.9rem; color: var(--accent); text-align: center; margin-bottom: 16px; font-weight: 600; }

.controls { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.filters button { padding: 7px 14px; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); color: var(--text-dim); font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all var(--transition); display: inline-flex; align-items: center; gap: 4px; }
.filters button:hover { color: var(--text-bright); border-color: var(--border-bright); }
.filters button.active { background: rgba(88,166,255,0.12); color: var(--primary); border-color: var(--primary); }
.badge { font-size: 0.7rem; padding: 1px 5px; border-radius: 10px; background: rgba(255,255,255,0.06); }
.filters button.active .badge { background: rgba(88,166,255,0.2); }
.sort-select { padding: 7px 14px; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); color: var(--text); font-size: 0.85rem; cursor: pointer; outline: none; appearance: none; -webkit-appearance: none; padding-right: 26px; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b949e' d='M6 8L2 4h8z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; }
.sort-select option { background: var(--surface-solid); }

.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; align-items: stretch; }
.card { text-decoration: none; transition: transform var(--transition); display: flex; flex-direction: column; opacity: 0; animation: fadeInUp 0.5s ease forwards; }
.card:hover { transform: translateY(-6px); }
.poster-wrapper { position: relative; width: 100%; padding-top: 150%; border-radius: var(--radius-sm); overflow: hidden; }
.poster { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: var(--radius-sm); object-fit: cover; background: rgba(255,255,255,0.05); box-shadow: var(--shadow); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; }
.poster.placeholder { font-size: 2.5rem; color: var(--text-dim); }
.card:hover .poster { box-shadow: var(--shadow-hover); border-color: var(--border-bright); }
.count-badge { position: absolute; bottom: 8px; right: 8px; padding: 3px 8px; border-radius: 12px; background: rgba(0,0,0,0.8); backdrop-filter: blur(4px); font-size: 0.72rem; font-weight: 700; color: var(--accent); z-index: 1; }
.rating-badge { position: absolute; top: 8px; left: 8px; padding: 3px 8px; border-radius: 12px; background: rgba(0,0,0,0.8); backdrop-filter: blur(4px); font-size: 0.72rem; font-weight: 700; color: var(--accent); z-index: 1; }
.info { padding: 10px 4px 0; display: flex; flex-direction: column; gap: 4px; flex: 1; }
.title { font-size: 0.86rem; font-weight: 600; color: var(--text-bright); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-height: 1.3em; }
.card:hover .title { color: var(--primary); }
.meta { display: flex; align-items: center; gap: 6px; font-size: 0.76rem; color: var(--text-dim); min-height: 1.3em; }
.type { padding: 1px 5px; border-radius: 4px; font-size: 0.68rem; font-weight: 600; }
.type.movie { background: rgba(88,166,255,0.15); color: var(--primary); }
.type.episode { background: rgba(139,92,246,0.15); color: var(--purple); }
.genres { display: flex; gap: 4px; flex-wrap: wrap; min-height: 1.5em; }
.genre-tag { font-size: 0.68rem; padding: 1px 6px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-dim); }
.stats { font-size: 0.72rem; color: var(--text-dim); display: flex; align-items: center; gap: 4px; margin-top: auto; min-height: 1.3em; }
.load-more { text-align: center; margin-top: 32px; }
.load-more button { padding: 10px 28px; border: 1px solid var(--border); border-radius: 24px; background: var(--surface); color: var(--text); font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all var(--transition); }
.load-more button:hover { border-color: var(--primary); color: var(--primary); background: rgba(88,166,255,0.08); }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 1024px) { .grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px) { .grid { grid-template-columns: repeat(2, 1fr); gap: 14px; } .controls { flex-direction: column; align-items: stretch; } }
</style>
