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
function getBackdrop(m) {
  return mediaMap.value?.get(m.trakt_id)?.backdrop_url
}
function getUrl(m) {
  return traktUrl(m, mediaMap)
}

const rankLabels = ['NO.1', 'NO.2', 'NO.3']

const top3Refs = ref([])
function onTilt(e, idx) {
  const el = top3Refs.value[idx]
  if (!el) return
  const rect = el.getBoundingClientRect()
  const dx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2)
  const dy = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2)
  el.style.transform = `perspective(1000px) rotateX(${-dy * 8}deg) rotateY(${dx * 8}deg) translateY(-8px)`
}
function onLeave(idx) {
  const el = top3Refs.value[idx]
  if (el) el.style.transform = ''
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

      <!-- TOP 3 沉浸式 -->
      <div class="top3-block stagger" :class="{ visible }">
        <div v-for="(m, i) in top3" :key="m.trakt_id"
          class="top3-card"
          :class="['rank-' + (i + 1)]"
          :ref="el => top3Refs[i] = el"
          @mousemove="onTilt($event, i)"
          @mouseleave="onLeave(i)"
        >
          <!-- 剧照背景 -->
          <div class="card-backdrop" v-if="getBackdrop(m)"
            :style="{ backgroundImage: `url(${getBackdrop(m)})` }" />
          <div class="card-backdrop-fallback" v-else />
          <div class="card-overlay" />

          <div class="rank-badge">{{ rankLabels[i] }}</div>

          <a :href="getUrl(m)" target="_blank" class="poster-link">
            <img v-if="getPoster(m)" class="poster-img" :src="getPoster(m)" alt="" loading="lazy"
              @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
            />
            <div v-if="!getPoster(m)" class="poster-img placeholder">
              <span>{{ m.title }}</span>
            </div>
            <div v-if="getPoster(m)" class="poster-img placeholder" style="display:none">
              <span>{{ m.title }}</span>
            </div>
          </a>
          <div class="top3-info">
            <a :href="getUrl(m)" target="_blank" class="top3-title">{{ m.title }}</a>
            <div class="top3-meta">
              <span class="watch-count">{{ m.watch_count }} 次观看</span>
              <span class="meta-dot"> · </span>
              <span>{{ formatMinutes(m.total_minutes) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 重看最多 -->
      <div class="special-block reveal-up" :class="{ visible }" v-if="mostRewatched.length">
        <h3 class="block-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
          年度重看最多
        </h3>
        <div class="special-list">
          <a v-for="(m, i) in mostRewatched" :key="'rw-' + i"
            :href="getUrl(m)" target="_blank"
            class="special-item glass-card"
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
        <h3 class="block-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="6 3 18 3 22 9 12 22 2 9"/></svg>
          小众佳作发现
        </h3>
        <div class="special-list">
          <a v-for="(m, i) in nicheGems" :key="'ng-' + i"
            :href="getUrl(m)" target="_blank"
            class="special-item glass-card"
          >
            <img v-if="getPoster(m)" class="special-poster" :src="getPoster(m)" alt="" loading="lazy" />
            <div v-else class="special-poster placeholder"><span>{{ m.title }}</span></div>
            <div class="special-info">
              <div class="special-title">{{ m.title }}</div>
              <div class="special-meta">{{ m.watch_count }} 次观看 · 冷门宝藏</div>
            </div>
          </a>
        </div>
      </div>

      <!-- 海报墙 -->
      <div class="poster-wall-block reveal-up" :class="{ visible }">
        <h3 class="block-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
          年度片单
        </h3>
        <div class="poster-wall">
          <a v-for="(m, i) in topList" :key="m.trakt_id"
            :href="getUrl(m)" target="_blank"
            class="wall-card"
            :style="{ animationDelay: (i * 0.06) + 's' }"
          >
            <div class="wall-rank">{{ i + 1 }}</div>
            <img v-if="getPoster(m)" class="wall-poster" :src="getPoster(m)" alt="" loading="lazy"
              @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
            />
            <div v-if="!getPoster(m)" class="wall-poster placeholder"><span>{{ m.title }}</span></div>
            <div v-if="getPoster(m)" class="wall-poster placeholder" style="display:none"><span>{{ m.title }}</span></div>
            <div class="wall-info">
              <div class="wall-title">{{ m.title }}</div>
              <div class="wall-meta">{{ m.watch_count }} 次 · {{ formatMinutes(m.total_minutes) }}</div>
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
  padding: 60px 24px;
  background: linear-gradient(180deg, #0d1410 0%, #11151a 100%);
}
.section-content { max-width: 960px; width: 100%; }

/* TOP3 沉浸式 */
.top3-block {
  display: flex; gap: 20px; justify-content: center;
  margin: 32px 0 48px; flex-wrap: wrap;
}
.top3-card {
  display: flex; flex-direction: column; align-items: center;
  width: 280px; position: relative; border-radius: var(--radius);
  overflow: hidden; transition: transform 0.2s ease;
  min-height: 380px;
}
.card-backdrop, .card-backdrop-fallback {
  position: absolute; inset: 0; background-size: cover; background-position: center;
  transform: scale(1.1); transition: transform 0.5s ease;
}
.card-backdrop-fallback {
  background: linear-gradient(135deg, rgba(168,197,160,0.08), rgba(10,12,15,0.9));
}
.top3-card:hover .card-backdrop { transform: scale(1.18); }
.card-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(10,12,15,0.5) 0%, rgba(10,12,15,0.85) 100%);
}
.rank-badge {
  position: absolute; top: 12px; left: 12px; z-index: 2;
  padding: 4px 12px; border-radius: 20px;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(8px);
  font-size: 0.78rem; font-weight: 800; color: var(--bean-green-bright);
  letter-spacing: 1px;
}
.top3-card.rank-1 .rank-badge {
  background: linear-gradient(135deg, rgba(212,168,87,0.3), rgba(212,168,87,0.1));
  color: var(--warm-amber); border: 1px solid rgba(212,168,87,0.4);
}
.poster-link { position: relative; z-index: 1; margin-top: 48px; }
.poster-img {
  width: 120px; height: 180px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.04);
  box-shadow: 0 8px 32px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1);
  transition: all var(--transition);
}
.poster-img.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 8px; text-align: center;
  font-size: 0.72rem; color: var(--text-dim);
}
.top3-card:hover .poster-img {
  box-shadow: 0 12px 48px rgba(0,0,0,0.7);
  border-color: rgba(168,197,160,0.3);
  transform: translateY(-4px);
}
.top3-info { padding: 16px 12px 20px; text-align: center; position: relative; z-index: 1; }
.top3-title {
  font-size: 0.92rem; font-weight: 700; color: var(--text-bright);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.4; margin-bottom: 6px;
  text-shadow: 0 1px 8px rgba(0,0,0,0.5);
}
.top3-meta { font-size: 0.78rem; color: var(--text-dim); }
.watch-count { color: var(--bean-green); font-weight: 600; }
.meta-dot { opacity: 0.5; }

/* 特殊榜单 */
.special-block { margin-bottom: 36px; }
.block-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 1rem; color: var(--text-bright); font-weight: 700;
  margin-bottom: 14px; letter-spacing: 1px;
}
.block-title svg { color: var(--bean-green); }
.special-list { display: flex; gap: 14px; flex-wrap: wrap; }
.special-item {
  display: flex; gap: 12px; padding: 12px; border-radius: var(--radius-sm);
  width: calc(33.33% - 10px); min-width: 200px; align-items: center;
  transition: transform var(--transition);
}
.special-item:hover { transform: translateY(-4px); }
.special-poster {
  width: 50px; height: 75px; border-radius: var(--radius-xs);
  object-fit: cover; flex-shrink: 0; background: rgba(255,255,255,0.04);
}
.special-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 4px; font-size: 0.6rem; color: var(--text-dim); text-align: center;
}
.special-info { flex: 1; min-width: 0; }
.special-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px;
}
.special-meta { font-size: 0.72rem; color: var(--text-dim); }

/* 海报墙 */
.poster-wall-block { margin-bottom: 20px; }
.poster-wall {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px;
}
.wall-card {
  position: relative; opacity: 0; animation: fadeInScale 0.5s ease forwards;
  transition: transform 0.2s ease, filter 0.3s ease;
}
.wall-card:hover { transform: translateY(-8px) scale(1.05); filter: brightness(1.15); z-index: 2; }
.wall-rank {
  position: absolute; top: 5px; left: 5px; z-index: 1;
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 800; color: var(--bean-green);
}
.wall-poster {
  width: 100%; aspect-ratio: 2/3; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.04);
  box-shadow: var(--shadow); border: 1px solid var(--border);
}
.wall-poster.placeholder {
  display: flex; align-items: center; justify-content: center;
  padding: 6px; font-size: 0.65rem; color: var(--text-dim); text-align: center;
}
.wall-card:hover .wall-poster { box-shadow: var(--shadow-hover); border-color: var(--border-bright); }
.wall-info { padding: 8px 2px 0; }
.wall-title {
  font-size: 0.78rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.wall-meta { font-size: 0.68rem; color: var(--text-dim); margin-top: 2px; }

@keyframes fadeInScale { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }

@media (max-width: 1024px) { .poster-wall { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 768px) {
  .top3-card { width: 200px; min-height: 320px; }
  .poster-img { width: 100px; height: 150px; }
  .special-item { width: 100%; }
  .poster-wall { grid-template-columns: repeat(3, 1fr); gap: 10px; }
}
</style>
