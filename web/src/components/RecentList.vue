<script setup>
import { inject, ref, computed, watch } from 'vue'
import { relativeDate } from '@/utils/format'
import { traktUrl } from '@/utils/genres'

const recentMeta = inject('recentMeta')
const fetchRecentMonth = inject('fetchRecentMonth')
const recentMonthCache = inject('recentMonthCache')
const mediaMap = inject('mediaMap')

const selectedMonth = ref(null)
const loading = ref(false)

const months = computed(() => recentMeta.value?.months || [])

const currentMonthData = computed(() => {
  if (!selectedMonth.value) return []
  return recentMonthCache?.value?.get(selectedMonth.value) || []
})

const monthLabel = (ym) => {
  const [y, m] = ym.split('-')
  return `${y}年${parseInt(m)}月`
}

watch(months, (list) => {
  if (list.length && !selectedMonth.value) {
    selectedMonth.value = list[0].month
  }
}, { immediate: true })

watch(selectedMonth, async (m) => {
  if (!m) return
  if (!recentMonthCache?.value?.has(m)) {
    loading.value = true
    await fetchRecentMonth(m)
    loading.value = false
  }
}, { immediate: true })
</script>

<template>
  <div>
    <div class="month-selector">
      <select v-model="selectedMonth" class="month-select">
        <option v-for="m in months" :key="m.month" :value="m.month">
          {{ monthLabel(m.month) }} ({{ m.count }})
        </option>
      </select>
    </div>

    <div class="recent-list">
      <div v-if="loading" class="loading-hint">加载中...</div>
      <div v-if="!currentMonthData.length && !loading" class="empty-state">
        <div class="icon">🎬</div><p>该月暂无观影记录</p>
      </div>
      <a
        v-for="item in currentMonthData" :key="item.id"
        :href="traktUrl(item, mediaMap)" target="_blank" class="recent-item"
      >
        <img v-if="item.poster_url" class="recent-poster"
          :src="item.poster_url" alt="" loading="lazy"
          @error="$event.target.style.display='none'; $event.target.nextElementSibling.style.display='flex'"
        />
        <div v-if="!item.poster_url" class="recent-poster-placeholder">
          {{ item.media_type === 'movie' ? '🎥' : '📺' }}
        </div>
        <div v-if="item.poster_url" class="recent-poster-placeholder" style="display:none">
          {{ item.media_type === 'movie' ? '🎥' : '📺' }}
        </div>
        <div class="recent-info">
          <div class="recent-title" :title="item.title">{{ item.title }}</div>
          <div class="recent-meta">
            <span class="recent-type" :class="item.media_type">
              {{ item.media_type === 'movie' ? '电影' : '剧集' }}
            </span>
            <span v-if="item.year" class="sep">·</span>
            <span v-if="item.year">{{ item.year }}</span>
            <span v-if="item.runtime" class="sep">·</span>
            <span v-if="item.runtime">{{ item.runtime }} min</span>
          </div>
        </div>
        <div class="recent-date">{{ relativeDate(item.watched_at_local) }}</div>
      </a>
    </div>
  </div>
</template>

<style scoped>
.month-selector {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
}
.month-select {
  padding: 8px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface); color: var(--text-bright); font-size: 0.9rem;
  cursor: pointer; transition: all var(--transition);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b949e' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 12px center;
  padding-right: 36px;
}
.month-select:hover { border-color: var(--primary); }
.month-select:focus { outline: none; border-color: var(--primary); }

.recent-list { display: flex; flex-direction: column; gap: 2px; }
.recent-item {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 16px; border-radius: var(--radius-sm);
  transition: all var(--transition); text-decoration: none;
  border: 1px solid transparent;
}
.recent-item:hover {
  background: var(--surface-hover); border-color: var(--border);
  text-decoration: none;
}
.recent-poster {
  width: 64px; height: 96px; border-radius: 8px;
  object-fit: cover; background: rgba(48,54,61,0.4); flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  transition: transform var(--transition);
}
.recent-item:hover .recent-poster { transform: scale(1.05); }
.recent-poster-placeholder {
  width: 64px; height: 96px; border-radius: 8px;
  background: rgba(48,54,61,0.4); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem; color: var(--muted);
}
.recent-info { flex: 1; min-width: 0; }
.recent-title {
  font-weight: 600; color: var(--text-bright); font-size: 0.95rem;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;
}
.recent-item:hover .recent-title { color: var(--primary); }
.recent-meta {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.8rem; color: var(--muted); flex-wrap: wrap;
}
.sep { color: rgba(72,79,88,0.6); }
.recent-type {
  padding: 1px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;
}
.recent-type.movie { background: rgba(88,166,255,0.15); color: var(--primary); }
.recent-type.episode { background: rgba(139,92,46,0.15); color: var(--purple); }
.recent-date {
  margin-left: auto; font-size: 0.78rem; color: var(--muted);
  white-space: nowrap; flex-shrink: 0;
}

.loading-hint { text-align: center; padding: 20px; color: var(--muted); font-size: 0.85rem; }
.empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.4; }

@media (max-width: 768px) {
  .recent-poster, .recent-poster-placeholder { width: 52px; height: 78px; }
}
</style>
