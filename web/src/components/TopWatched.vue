<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { traktUrl, translateGenre } from '@/utils/genres'
import { relativeDate, formatMinutes } from '@/utils/format'

const topMedia = inject('topMedia')
const mediaMap = inject('mediaMap')
const visible = ref(false)
const sectionRef = ref(null)

const year = new Date().getFullYear()
const topList = computed(() => (topMedia.value || []).slice(0, 12))

function getPoster(m) {
  return m.poster_url || mediaMap.value?.get(m.trakt_id)?.poster_url
}

function getUrl(m) {
  return traktUrl(m, mediaMap)
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.1 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="top-section">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">🏆 最爱看的</p>
      <p class="narrative reveal-up" :class="{ visible }">
        这些作品，陪你度过了 <span class="highlight">{{ year }}</span> 年
      </p>

      <div class="poster-scroll" :class="{ visible }">
        <a v-for="(m, i) in topList" :key="m.trakt_id"
          :href="getUrl(m)" target="_blank"
          class="poster-card"
          :style="{ animationDelay: (i * 0.08) + 's' }"
        >
          <div class="poster-rank">{{ i + 1 }}</div>
          <img v-if="getPoster(m)" class="poster-img"
            :src="getPoster(m)" alt="" loading="lazy"
            @error="$event.target.style.display='none'; $event.target.nextElementSibling?.style.setProperty('display','flex')"
          />
          <div v-if="!getPoster(m)" class="poster-img placeholder">
            {{ m.media_type === 'episode' ? '📺' : '🎥' }}
          </div>
          <div v-if="getPoster(m)" class="poster-img placeholder" style="display:none">
            {{ m.media_type === 'episode' ? '📺' : '🎥' }}
          </div>
          <div class="poster-info">
            <div class="poster-title">{{ m.title }}</div>
            <div class="poster-meta">{{ m.watch_count }} 次 · {{ formatMinutes(m.total_minutes) }}</div>
          </div>
        </a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.top-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
  background: linear-gradient(180deg, #0d1117 0%, #14122a 100%);
}
.section-content { max-width: 900px; width: 100%; }
.section-label { font-size: 0.85rem; color: var(--accent); text-align: center; margin-bottom: 12px; font-weight: 600; }

.poster-scroll {
  display: flex; gap: 16px; overflow-x: auto; padding: 20px 0;
  scroll-snap-type: x mandatory;
}
.poster-scroll::-webkit-scrollbar { height: 4px; }
.poster-card {
  flex-shrink: 0; width: 160px; scroll-snap-align: start;
  opacity: 0; animation: fadeInUp 0.6s ease forwards;
  transition: transform var(--transition);
}
.poster-card:hover { transform: translateY(-8px); }
.poster-rank {
  position: absolute; top: 6px; left: 6px; z-index: 1;
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; font-weight: 800; color: var(--accent);
}
.poster-img {
  width: 160px; height: 240px; border-radius: var(--radius-sm);
  object-fit: cover; background: rgba(255,255,255,0.05);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  transition: box-shadow var(--transition), border-color var(--transition);
  position: relative;
}
.poster-img.placeholder { display: flex; align-items: center; justify-content: center; font-size: 2.5rem; }
.poster-card:hover .poster-img { box-shadow: var(--shadow-hover); border-color: var(--border-bright); }
.poster-info { padding: 10px 4px 0; }
.poster-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.poster-meta { font-size: 0.74rem; color: var(--text-dim); margin-top: 3px; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
