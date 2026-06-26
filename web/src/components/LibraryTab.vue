<script setup>
import { inject, ref, computed } from 'vue'
import { traktUrl, translateGenre, cleanShowTitle } from '@/utils/genres'
import { relativeDate, formatMinutes } from '@/utils/format'

const recentPlays = inject('recentPlays')
const mediaMap = inject('mediaMap')

const filter = ref('all')
const sortBy = ref('watched')
const visibleCount = ref(24)

const library = computed(() => {
  const plays = recentPlays.value || []
  const map = {}
  plays.forEach(p => {
    const key = p.media_trakt_id || p.trakt_id
    if (!map[key]) {
      const media = mediaMap.value?.get(key)
      map[key] = {
        key,
        title: cleanShowTitle(p.title),
        poster_url: p.poster_url,
        backdrop_url: media?.backdrop_url,
        media_type: p.media_type,
        year: p.year || media?.year,
        rating: media?.rating || p.rating,
        genres: media?.genres ? JSON.parse(media.genres) : (p.genres ? JSON.parse(p.genres) : []),
        slug: media?.slug,
        overview: media?.overview || p.overview,
        count: 0,
        total_minutes: 0,
        last_watched: p.watched_at_local,
        item: p,
        media,
      }
    }
    map[key].count++
    map[key].total_minutes += p.runtime || 0
    if (p.watched_at_local > map[key].last_watched) {
      map[key].last_watched = p.watched_at_local
    }
  })
  return Object.values(map)
})

const filtered = computed(() => {
  let list = library.value
  if (filter.value !== 'all') {
    list = list.filter(m => m.media_type === filter.value)
  }
  const sorted = [...list]
  if (sortBy.value === 'watched') {
    sorted.sort((a, b) => b.count - a.count)
  } else if (sortBy.value === 'recent') {
    sorted.sort((a, b) => b.last_watched.localeCompare(a.last_watched))
  } else if (sortBy.value === 'rating') {
    sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0))
  } else if (sortBy.value === 'time') {
    sorted.sort((a, b) => b.total_minutes - a.total_minutes)
  }
  return sorted
})

const displayed = computed(() => filtered.value.slice(0, visibleCount.value))
const hasMore = computed(() => visibleCount.value < filtered.value.length)

function loadMore() {
  visibleCount.value += 24
}

function onImgError(e) {
  e.target.style.display = 'none'
  const sib = e.target.nextElementSibling
  if (sib) sib.style.display = 'flex'
}

const showCounts = computed(() => {
  const lib = library.value
  return {
    all: lib.length,
    movie: lib.filter(m => m.media_type === 'movie').length,
    episode: lib.filter(m => m.media_type === 'episode').length,
  }
})
</script>

<template>
  <div class="library-tab">
    <div class="library-controls">
      <div class="filter-group">
        <button :class="{ active: filter === 'all' }" @click="filter = 'all'">
          全部 <span class="badge">{{ showCounts.all }}</span>
        </button>
        <button :class="{ active: filter === 'episode' }" @click="filter = 'episode'">
          📺 剧集 <span class="badge">{{ showCounts.episode }}</span>
        </button>
        <button :class="{ active: filter === 'movie' }" @click="filter = 'movie'">
          🎥 电影 <span class="badge">{{ showCounts.movie }}</span>
        </button>
      </div>
      <div class="sort-group">
        <select v-model="sortBy">
          <option value="watched">观看次数最多</option>
          <option value="recent">最近观看</option>
          <option value="time">观看时长最长</option>
          <option value="rating">评分最高</option>
        </select>
      </div>
    </div>

    <div class="library-grid">
      <a
        v-for="(m, i) in displayed" :key="m.key"
        :href="traktUrl(m.item, mediaMap)" target="_blank"
        class="lib-card animate-in"
        :style="{ animationDelay: (i % 24) * 0.02 + 's' }"
      >
        <div class="lib-poster-wrapper">
          <img v-if="m.poster_url" class="lib-poster"
            :src="m.poster_url" alt="" loading="lazy" @error="onImgError"
          />
          <div v-if="!m.poster_url" class="lib-poster placeholder">
            {{ m.media_type === 'movie' ? '🎥' : '📺' }}
          </div>
          <div v-if="m.poster_url" class="lib-poster placeholder" style="display:none">
            {{ m.media_type === 'movie' ? '🎥' : '📺' }}
          </div>
          <div class="lib-count-badge">{{ m.count }} 次</div>
          <div v-if="m.rating" class="lib-rating-badge">⭐ {{ Number(m.rating).toFixed(1) }}</div>
        </div>
        <div class="lib-info">
          <div class="lib-title" :title="m.title">{{ m.title }}</div>
          <div class="lib-meta">
            <span class="lib-type" :class="m.media_type">
              {{ m.media_type === 'movie' ? '电影' : '剧集' }}
            </span>
            <span v-if="m.year">{{ m.year }}</span>
          </div>
          <div class="lib-genres" v-if="m.genres && m.genres.length">
            <span v-for="g in m.genres.slice(0, 3)" :key="g" class="genre-tag">
              {{ translateGenre(g) }}
            </span>
          </div>
          <div class="lib-stats">
            <span>⏱️ {{ formatMinutes(m.total_minutes) }}</span>
            <span>·</span>
            <span>{{ relativeDate(m.last_watched) }}</span>
          </div>
        </div>
      </a>
    </div>

    <div v-if="hasMore" class="load-more">
      <button @click="loadMore">加载更多（{{ filtered.length - visibleCount }} 个）</button>
    </div>
  </div>
</template>

<style scoped>
.library-controls {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; margin-bottom: 24px; flex-wrap: wrap;
}
.filter-group { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-group button {
  padding: 8px 14px; border: 1px solid var(--border); border-radius: 20px;
  background: var(--surface); color: var(--muted); font-size: 0.85rem; font-weight: 600;
  cursor: pointer; transition: all var(--transition);
  display: inline-flex; align-items: center; gap: 4px;
}
.filter-group button:hover { color: var(--text-bright); border-color: var(--border-bright); }
.filter-group button.active {
  background: rgba(88, 166, 255, 0.12); color: var(--primary);
  border-color: var(--primary);
}
.badge {
  font-size: 0.72rem; padding: 1px 6px; border-radius: 10px;
  background: rgba(48,54,61,0.6); color: var(--muted);
}
.filter-group button.active .badge { background: rgba(88,166,255,0.2); color: var(--primary); }

.sort-group select {
  padding: 8px 14px; border: 1px solid var(--border); border-radius: 20px;
  background: var(--surface); color: var(--text); font-size: 0.85rem;
  cursor: pointer; outline: none; transition: all var(--transition);
  appearance: none; -webkit-appearance: none; padding-right: 28px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b949e' d='M6 8L2 4h8z'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center;
}
.sort-group select:hover { border-color: var(--border-bright); }
.sort-group select option { background: var(--surface-solid); }

.library-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
}
.lib-card {
  text-decoration: none; transition: transform var(--transition);
  display: flex; flex-direction: column; height: 100%;
}
.lib-card:hover { transform: translateY(-6px); text-decoration: none; }

.lib-poster-wrapper { position: relative; width: 100%; aspect-ratio: 2/3; }
.lib-poster {
  width: 100%; height: 100%; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(48,54,61,0.4);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: box-shadow var(--transition), border-color var(--transition);
  position: absolute; top: 0; left: 0; display: block;
}
.lib-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  font-size: 2.5rem; color: var(--muted);
}
.lib-card:hover .lib-poster { box-shadow: var(--shadow-hover); border-color: var(--border-bright); }

.lib-count-badge {
  position: absolute; bottom: 8px; right: 8px;
  padding: 3px 8px; border-radius: 12px;
  background: rgba(10, 14, 20, 0.85); backdrop-filter: blur(4px);
  font-size: 0.72rem; font-weight: 700; color: var(--accent); z-index: 1;
}
.lib-rating-badge {
  position: absolute; top: 8px; left: 8px;
  padding: 3px 8px; border-radius: 12px;
  background: rgba(10, 14, 20, 0.85); backdrop-filter: blur(4px);
  font-size: 0.72rem; font-weight: 700; color: var(--accent); z-index: 1;
}

.lib-info {
  padding: 10px 4px 0;
  display: flex; flex-direction: column; gap: 4px;
  flex: 1;
}
.lib-title {
  font-size: 0.86rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  transition: color var(--transition);
}
.lib-card:hover .lib-title { color: var(--primary); }
.lib-meta {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.76rem; color: var(--muted);
}
.lib-type {
  padding: 1px 5px; border-radius: 4px; font-size: 0.68rem; font-weight: 600;
}
.lib-type.movie { background: rgba(88,166,255,0.15); color: var(--primary); }
.lib-type.episode { background: rgba(139,92,246,0.15); color: var(--purple); }
.lib-genres { display: flex; gap: 4px; flex-wrap: wrap; }
.genre-tag {
  font-size: 0.68rem; padding: 1px 6px; border-radius: 8px;
  background: rgba(48,54,61,0.4); color: var(--muted);
}
.lib-stats {
  font-size: 0.72rem; color: var(--muted);
  display: flex; align-items: center; gap: 4px;
  margin-top: auto;
}

.load-more { text-align: center; margin-top: 32px; }
.load-more button {
  padding: 10px 28px; border: 1px solid var(--border); border-radius: 24px;
  background: var(--surface); color: var(--text); font-size: 0.9rem; font-weight: 600;
  cursor: pointer; transition: all var(--transition);
}
.load-more button:hover {
  border-color: var(--primary); color: var(--primary);
  background: rgba(88,166,255,0.08);
}

.animate-in { animation: fadeInUp 0.4s ease both; }

@media (max-width: 1024px) {
  .library-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .library-grid { grid-template-columns: repeat(2, 1fr); gap: 14px; }
  .library-controls { flex-direction: column; align-items: stretch; }
}
@media (max-width: 480px) {
  .library-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
