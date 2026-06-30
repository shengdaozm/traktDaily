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

const top3Refs = ref([])
function onTilt(e, idx) {
  const el = top3Refs.value[idx]
  if (!el) return
  const rect = el.getBoundingClientRect()
  const dx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2)
  const dy = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2)
  el.style.transform = `perspective(800px) rotateX(${-dy * 15}deg) rotateY(${dx * 15}deg) translateY(-8px)`
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
      <p class="section-label reveal-up" :class="{ visible }">🏆 年度榜单</p>
      <p class="narrative reveal-up" :class="{ visible }">
        这些作品，是 <span class="highlight">{{ year }}</span> 年的精华
      </p>

      <!-- TOP 3 -->
      <div class="top3-block stagger" :class="{ visible }">
        <div v-for="(m, i) in top3" :key="m.trakt_id"
          class="top3-card bean-card glow-border"
          :class="['rank-' + (i + 1)]"
          :ref="el => top3Refs[i] = el"
          @mousemove="onTilt($event, i)"
          @mouseleave="onLeave(i)"
        >
          <div class="rank-medal">{{ ['🥇', '🥈', '🥉'][i] }}</div>
          <a :href="getUrl(m)" target="_blank" class="poster-link">
            <img v-if="getPoster(m)" class="poster-img" :src="getPoster(m)" alt="" loading="lazy"
              @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
            />
            <div v-if="!getPoster(m)" class="poster-img placeholder">{{ m.media_type === 'episode' ? '📺' : '🎥' }}</div>
            <div v-if="getPoster(m)" class="poster-img placeholder" style="display:none">{{ m.media_type === 'episode' ? '📺' : '🎥' }}</div>
          </a>
          <div class="top3-info">
            <a :href="getUrl(m)" target="_blank" class="top3-title">{{ m.title }}</a>
            <div class="top3-meta">
              <span class="watch-count">{{ m.watch_count }} 次观看</span>
              <span> · </span>
              <span>{{ formatMinutes(m.total_minutes) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 重看最多 -->
      <div class="special-block reveal-up" :class="{ visible }" v-if="mostRewatched.length">
        <h3 class="block-title">🔄 年度重看最多</h3>
        <div class="special-list">
          <a v-for="(m, i) in mostRewatched" :key="'rw-' + i"
            :href="getUrl(m)" target="_blank"
            class="special-item glass-card"
          >
            <img v-if="getPoster(m)" class="special-poster" :src="getPoster(m)" alt="" loading="lazy" />
            <div v-else class="special-poster placeholder">📺</div>
            <div class="special-info">
              <div class="special-title">{{ m.title }}</div>
              <div class="special-meta">重看 {{ m.watch_count }} 次 · {{ formatMinutes(m.total_minutes) }}</div>
            </div>
          </a>
        </div>
      </div>

      <!-- 小众佳作 -->
      <div class="special-block reveal-up" :class="{ visible }" v-if="nicheGems.length">
        <h3 class="block-title">💎 小众佳作发现</h3>
        <div class="special-list">
          <a v-for="(m, i) in nicheGems" :key="'ng-' + i"
            :href="getUrl(m)" target="_blank"
            class="special-item glass-card"
          >
            <img v-if="getPoster(m)" class="special-poster" :src="getPoster(m)" alt="" loading="lazy" />
            <div v-else class="special-poster placeholder">💎</div>
            <div class="special-info">
              <div class="special-title">{{ m.title }}</div>
              <div class="special-meta">{{ m.watch_count }} 次观看 · 冷门宝藏</div>
            </div>
          </a>
        </div>
      </div>

      <!-- 海报墙 -->
      <div class="poster-wall-block reveal-up" :class="{ visible }">
        <h3 class="block-title">🎞️ 年度片单</h3>
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
            <div v-if="!getPoster(m)" class="wall-poster placeholder">{{ m.media_type === 'episode' ? '📺' : '🎥' }}</div>
            <div v-if="getPoster(m)" class="wall-poster placeholder" style="display:none">{{ m.media_type === 'episode' ? '📺' : '🎥' }}</div>
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
.section-content { max-width: 900px; width: 100%; }

.top3-block {
  display: flex; gap: 16px; justify-content: center;
  margin: 32px 0 40px; flex-wrap: wrap;
}
.top3-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 20px 16px; width: 200px; position: relative;
}
.rank-medal { font-size: 2rem; margin-bottom: 8px; }
.poster-link { display: block; }
.poster-img {
  width: 130px; height: 195px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.04);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: all var(--transition);
}
.poster-img.placeholder { display: flex; align-items: center; justify-content: center; font-size: 2rem; color: var(--text-dim); }
.top3-card:hover .poster-img { box-shadow: var(--shadow-hover); border-color: var(--border-bright); transform: translateY(-4px); }
.top3-info { padding-top: 12px; text-align: center; }
.top3-title {
  font-size: 0.88rem; font-weight: 700; color: var(--text-bright);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.4; margin-bottom: 4px;
}
.top3-meta { font-size: 0.76rem; color: var(--text-dim); }
.watch-count { color: var(--bean-green); font-weight: 600; }

.special-block { margin-bottom: 36px; }
.block-title { font-size: 1rem; color: var(--text-bright); font-weight: 700; margin-bottom: 14px; letter-spacing: 1px; }
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
.special-poster.placeholder { display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.special-info { flex: 1; min-width: 0; }
.special-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px;
}
.special-meta { font-size: 0.72rem; color: var(--text-dim); }

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
.wall-poster.placeholder { display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: var(--text-dim); }
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
  .top3-card { width: 140px; }
  .poster-img { width: 100px; height: 150px; }
  .special-item { width: 100%; }
  .poster-wall { grid-template-columns: repeat(3, 1fr); gap: 10px; }
}
</style>
