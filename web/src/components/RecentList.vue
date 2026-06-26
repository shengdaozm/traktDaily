<script setup>
import { inject, ref, computed, watch } from 'vue'
import { relativeDate } from '@/utils/format'
import { traktUrl } from '@/utils/genres'

const recentMeta = inject('recentMeta')
const fetchRecentPage = inject('fetchRecentPage')
const getRecentPage = inject('getRecentPage')
const mediaMap = inject('mediaMap')

const PAGE_SIZE = 10
const currentPage = ref(1)
const loadingPage = ref(false)

const totalPlays = computed(() => recentMeta.value?.total || 0)
const totalPages = computed(() => Math.ceil(totalPlays.value / PAGE_SIZE))

const pageItems = computed(() => {
  const allPageSize = recentMeta.value?.page_size || 100
  const start = (currentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE

  const bigPageNum = Math.floor(start / allPageSize) + 1
  const bigPageData = getRecentPage(bigPageNum)

  const localStart = start % allPageSize
  return bigPageData.slice(localStart, localStart + (end - start))
})

watch(currentPage, async (page) => {
  const allPageSize = recentMeta.value?.page_size || 100
  const bigPageNum = Math.floor(((page - 1) * PAGE_SIZE) / allPageSize) + 1
  if (!getRecentPage(bigPageNum)) {
    loadingPage.value = true
    await fetchRecentPage(bigPageNum)
    loadingPage.value = false
  }
})
</script>

<template>
  <div>
    <div class="recent-list">
      <div v-if="loadingPage" class="loading-hint">加载中...</div>
      <div v-if="!pageItems.length && !loadingPage" class="empty-state">
        <div class="icon">🎬</div><p>暂无观影记录</p>
      </div>
      <a
        v-for="item in pageItems" :key="item.id"
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

    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="currentPage <= 1" @click="currentPage--">← 上一页</button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button :disabled="currentPage >= totalPages" @click="currentPage++">下一页 →</button>
    </div>
  </div>
</template>

<style scoped>
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
.recent-type.episode { background: rgba(139,92,246,0.15); color: var(--purple); }
.recent-date {
  margin-left: auto; font-size: 0.78rem; color: var(--muted);
  white-space: nowrap; flex-shrink: 0;
}

.pagination {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border);
}
.pagination button {
  padding: 6px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface); color: var(--text); font-size: 0.85rem;
  cursor: pointer; transition: all var(--transition);
}
.pagination button:hover:not(:disabled) {
  border-color: var(--primary); color: var(--text-bright);
  background: rgba(88,166,255,0.08);
}
.pagination button:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-size: 0.85rem; color: var(--muted); }

.loading-hint { text-align: center; padding: 20px; color: var(--muted); font-size: 0.85rem; }
.empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.4; }

@media (max-width: 768px) {
  .recent-poster, .recent-poster-placeholder { width: 52px; height: 78px; }
}
</style>
