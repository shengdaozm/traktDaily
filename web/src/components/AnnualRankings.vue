<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { traktUrl } from '@/utils/genres'
import { formatMinutes } from '@/utils/format'

const topMedia = inject('topMedia')
const mediaMap = inject('mediaMap')
const visible = ref(false)
const sectionRef = ref(null)

const year = new Date().getFullYear()
const top3 = computed(() => (topMedia.value || []).slice(0, 3))
const topList = computed(() => (topMedia.value || []).slice(0, 12))

const mostRewatched = computed(() => {
  return (topMedia.value || [])
    .filter(m => m.watch_count > 1)
    .sort((a, b) => b.watch_count - a.watch_count)
    .slice(0, 3)
})

const nicheGems = computed(() => {
  return (topMedia.value || [])
    .filter(m => {
      const media = mediaMap.value?.get(m.trakt_id)
      const votes = media?.votes || m.votes || 0
      return votes > 0 && votes < 5000
    })
    .slice(0, 3)
})

function getPoster(m) {
  return m.poster_url || mediaMap.value?.get(m.trakt_id)?.poster_url
}
function getUrl(m) {
  return traktUrl(m, mediaMap)
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.05 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="rankings-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">年度榜单</p>
      <p class="narrative reveal-up" :class="{ visible }">
        这些作品，是 <span class="highlight">{{ year }}</span> 年的精华
      </p>

      <!-- TOP 3 -->
      <div class="top3-block stagger" :class="{ visible }">
        <a v-for="(m, i) in top3" :key="m.trakt_id"
          :href="getUrl(m)" target="_blank"
          class="top3-card glass-card"
        >
          <div class="rank-num">{{ i + 1 }}</div>
          <img v-if="getPoster(m)" class="poster-img" :src="getPoster(m)" alt="" loading="lazy"
            @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
          />
          <div v-if="!getPoster(m)" class="poster-img placeholder"><span>{{ m.title }}</span></div>
          <div v-if="getPoster(m)" class="poster-img placeholder" style="display:none"><span>{{ m.title }}</span></div>
          <div class="top3-title">{{ m.title }}</div>
          <div class="top3-meta">{{ m.watch_count }} 次 · {{ formatMinutes(m.total_minutes) }}</div>
        </a>
      </div>

      <!-- 重看最多 -->
      <div class="special-block reveal-up" :class="{ visible }" v-if="mostRewatched.length">
        <h3 class="block-title">年度重看最多</h3>
        <div class="special-list">
          <a v-for="(m, i) in mostRewatched" :key="'rw-' + i"
            :href="getUrl(m)" target="_blank" class="special-item glass-card"
          >
            <img v-if="getPoster(m)" class="special-poster" :src="getPoster(m)" alt="" loading="lazy" />
            <div v-else class="special-poster placeholder"><span>{{ m.title }}</span></div>
            <div class="special-info">
              <div class="special-title">{{ m.title }}</div>
              <div class="special-meta">重看 {{ m.watch_count }} 次 · {{ formatMinutes(m.total_minutes) }}</div>
            </div>
          </a>
        </div>
      </div>

      <!-- 小众佳作 -->
      <div class="special-block reveal-up" :class="{ visible }" v-if="nicheGems.length">
        <h3 class="block-title">小众佳作发现</h3>
        <div class="special-list">
          <a v-for="(m, i) in nicheGems" :key="'ng-' + i"
            :href="getUrl(m)" target="_blank" class="special-item glass-card"
          >
            <img v-if="getPoster(m)" class="special-poster" :src="getPoster(m)" alt="" loading="lazy" />
            <div v-else class="special-poster placeholder"><span>{{ m.title }}</span></div>
            <div class="special-info">
              <div class="special-title">{{ m.title }}</div>
              <div class="special-meta">{{ m.watch_count }} 次 · 冷门宝藏</div>
            </div>
          </a>
        </div>
      </div>

      <!-- 海报墙 -->
      <div class="poster-wall-block reveal-up" :class="{ visible }">
        <h3 class="block-title">年度片单</h3>
        <div class="poster-wall">
          <a v-for="(m, i) in topList" :key="m.trakt_id"
            :href="getUrl(m)" target="_blank"
            class="wall-card"
            :style="{ animationDelay: (i * 0.05) + 's' }"
          >
            <div class="wall-rank">{{ i + 1 }}</div>
            <img v-if="getPoster(m)" class="wall-poster" :src="getPoster(m)" alt="" loading="lazy"
              @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
            />
            <div v-if="!getPoster(m)" class="wall-poster placeholder"><span>{{ m.title }}</span></div>
            <div v-if="getPoster(m)" class="wall-poster placeholder" style="display:none"><span>{{ m.title }}</span></div>
            <div class="wall-info">
              <div class="wall-title">{{ m.title }}</div>
              <div class="wall-meta">{{ m.watch_count }} 次</div>
            </div>
          </a>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.rankings-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: var(--section-gap) var(--page-margin);
  background: var(--bg);
}
.section-content { max-width: 860px; width: 100%; }

.top3-block {
  display: flex; gap: 16px; justify-content: center;
  margin: 32px 0 40px; flex-wrap: wrap;
}
.top3-card {
  display: flex; flex-direction: column; align-items: center;
  padding: var(--space-md) var(--space-sm); width: 180px;
  transition: transform var(--transition), box-shadow var(--transition);
}
.top3-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.rank-num {
  font-size: 1.2rem; font-weight: 800; color: var(--primary);
  margin-bottom: 10px;
}
.poster-img {
  width: 120px; height: 180px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.03);
  border: 1px solid var(--border); box-shadow: var(--shadow);
  transition: box-shadow var(--transition);
}
.poster-img.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 8px; text-align: center; font-size: 0.72rem; color: var(--text-3);
}
.top3-card:hover .poster-img { box-shadow: var(--shadow-hover); }
.top3-title {
  padding-top: 12px; font-size: 0.85rem; font-weight: 600; color: var(--text-1);
  text-align: center; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 4px;
}
.top3-meta { font-size: 0.75rem; color: var(--text-3); text-align: center; }

.special-block { margin-bottom: 36px; }
.block-title {
  font-size: 0.95rem; color: var(--text-1); font-weight: 700;
  margin-bottom: 14px; letter-spacing: 1px;
}
.special-list { display: flex; gap: 14px; flex-wrap: wrap; }
.special-item {
  display: flex; gap: 12px; padding: 12px; border-radius: var(--radius);
  width: calc(33.33% - 10px); min-width: 200px; align-items: center;
  transition: transform var(--transition);
}
.special-item:hover { transform: translateY(-3px); }
.special-poster {
  width: 48px; height: 72px; border-radius: var(--radius-sm);
  object-fit: cover; flex-shrink: 0; background: rgba(255,255,255,0.03);
}
.special-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 4px; font-size: 0.6rem; color: var(--text-3); text-align: center;
}
.special-info { flex: 1; min-width: 0; }
.special-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px;
}
.special-meta { font-size: 0.72rem; color: var(--text-3); }

.poster-wall-block { margin-bottom: 20px; }
.poster-wall {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px;
}
.wall-card {
  position: relative; opacity: 0; animation: fadeIn 0.4s ease forwards;
  transition: transform var(--transition);
}
.wall-card:hover { transform: translateY(-3px); }
.wall-rank {
  position: absolute; top: 4px; left: 4px; z-index: 1;
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700; color: var(--primary-bright);
}
.wall-poster {
  width: 100%; aspect-ratio: 2/3; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.03);
  border: 1px solid var(--border); box-shadow: var(--shadow);
}
.wall-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 6px; font-size: 0.65rem; color: var(--text-3); text-align: center;
}
.wall-info { padding: 6px 2px 0; }
.wall-title {
  font-size: 0.75rem; font-weight: 600; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.wall-meta { font-size: 0.65rem; color: var(--text-3); margin-top: 2px; }

@media (max-width: 1024px) { .poster-wall { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 768px) {
  .top3-card { width: 140px; }
  .poster-img { width: 100px; height: 150px; }
  .special-item { width: 100%; }
  .poster-wall { grid-template-columns: repeat(3, 1fr); gap: 10px; }
}
</style>
