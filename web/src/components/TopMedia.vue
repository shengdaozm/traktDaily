<script setup>
import { inject, computed } from 'vue'
import { traktUrl, cleanShowTitle } from '@/utils/genres'

const topMedia = inject('topMedia')
const mediaMap = inject('mediaMap')

const displayList = computed(() => (topMedia.value || []).slice(0, 15))

function getItemUrl(item) {
  if (item.slug) {
    const type = item.media_type === 'movie' ? 'movies' : 'shows'
    return `https://trakt.tv/${type}/${item.slug}`
  }
  const media = mediaMap.value?.get(item.trakt_id)
  if (media?.slug) {
    const type = media.media_type === 'movie' ? 'movies' : 'shows'
    return `https://trakt.tv/${type}/${media.slug}`
  }
  return '#'
}

function getItemPoster(item) {
  return item.poster_url || mediaMap.value?.get(item.trakt_id)?.poster_url
}

function scrollBy(dir) {
  const el = document.getElementById('top-media-scroll')
  if (el) el.scrollBy({ left: dir * 320, behavior: 'smooth' })
}
</script>

<template>
  <div class="top-media-wrapper" v-if="displayList.length">
    <button class="scroll-btn left" @click="scrollBy(-1)">‹</button>
    <div id="top-media-scroll" class="top-media-scroll">
      <a
        v-for="(m, i) in displayList" :key="m.trakt_id"
        :href="getItemUrl(m)" target="_blank" class="top-media-card"
      >
        <div class="top-media-card-wrapper">
          <div class="top-media-rank">{{ i + 1 }}</div>
          <img v-if="getItemPoster(m)" class="top-media-poster"
            :src="getItemPoster(m)" alt="" loading="lazy"
            @error="$event.target.style.display='none'; $event.target.nextElementSibling.style.display='flex'"
          />
          <div v-if="!getItemPoster(m)" class="top-media-poster placeholder">
            {{ m.media_type === 'episode' ? '📺' : '🎥' }}
          </div>
          <div v-if="getItemPoster(m)" class="top-media-poster placeholder" style="display:none">
            {{ m.media_type === 'episode' ? '📺' : '🎥' }}
          </div>
        </div>
        <div class="top-media-info">
          <div class="top-media-title" :title="m.title">{{ m.title }}</div>
          <div class="top-media-count">
            {{ m.media_type === 'episode' ? '📺' : '🎥' }} {{ m.watch_count }} 次
          </div>
        </div>
      </a>
    </div>
    <button class="scroll-btn right" @click="scrollBy(1)">›</button>
  </div>
  <div v-else class="empty-state"><div class="icon">🎬</div><p>暂无数据</p></div>
</template>

<style scoped>
.top-media-wrapper { position: relative; display: flex; align-items: center; gap: 8px; }
.top-media-scroll {
  display: flex; gap: 14px; overflow-x: auto;
  padding: 4px 4px 12px; scroll-snap-type: x mandatory;
  scroll-behavior: smooth; flex: 1;
}
.top-media-card {
  flex-shrink: 0; width: 150px; scroll-snap-align: start;
  text-decoration: none; transition: transform var(--transition);
}
.top-media-card:hover { transform: translateY(-6px); }
.top-media-card-wrapper { position: relative; }
.top-media-rank {
  position: absolute; top: 6px; left: 6px;
  width: 26px; height: 26px; border-radius: 50%;
  background: rgba(10, 14, 20, 0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 800; color: var(--accent); z-index: 1;
}
.top-media-poster {
  width: 150px; height: 225px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(48,54,61,0.4);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: box-shadow var(--transition), border-color var(--transition);
}
.top-media-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; color: var(--muted);
}
.top-media-card:hover .top-media-poster {
  box-shadow: var(--shadow-hover); border-color: var(--border-bright);
}
.top-media-info { padding: 8px 2px 0; }
.top-media-title {
  font-size: 0.84rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.top-media-count { font-size: 0.74rem; color: var(--muted); margin-top: 2px; }

.scroll-btn {
  flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text); font-size: 1.4rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition); z-index: 2;
  backdrop-filter: blur(10px);
}
.scroll-btn:hover { border-color: var(--primary); color: var(--primary); background: rgba(88,166,255,0.1); }

.empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.4; }

@media (max-width: 768px) {
  .scroll-btn { display: none; }
  .top-media-card, .top-media-poster { width: 120px; }
  .top-media-poster { height: 180px; }
}
</style>
