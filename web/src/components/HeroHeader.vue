<script setup>
import { computed, ref, onMounted, watch } from 'vue'

const props = defineProps({
  lastUpdated: { type: String, default: '' },
  mediaList: { type: Array, default: () => [] },
})

const backdropUrl = computed(() => {
  const item = props.mediaList.find(m => m.backdrop_url)
  return item?.backdrop_url || ''
})

const formattedDate = computed(() => {
  if (!props.lastUpdated) return ''
  return props.lastUpdated.substring(0, 16)
})

const showBadge = ref(false)
watch(() => props.lastUpdated, (v) => { showBadge.value = !!v })
onMounted(() => { showBadge.value = !!props.lastUpdated })
</script>

<template>
  <header class="hero">
    <div class="hero-backdrop" v-if="backdropUrl">
      <img :src="backdropUrl" alt="" @error="$event.target.parentElement.style.display='none'" />
    </div>
    <div class="hero-icon">🎬</div>
    <h1>trakt<span>Daily</span></h1>
    <div class="subtitle">
      <span>观影数据自动同步 · 每 2 小时更新</span>
      <span v-if="showBadge" class="updated-badge">
        {{ formattedDate }}
      </span>
    </div>
  </header>
</template>

<style scoped>
.hero {
  text-align: center; padding: 56px 0 36px; position: relative;
}
.hero-backdrop {
  position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 100%; max-width: 800px; height: 200px;
  border-radius: var(--radius); overflow: hidden;
  opacity: 0.12; z-index: -1;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 30%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 30%, transparent 100%);
}
.hero-backdrop img { width: 100%; height: 100%; object-fit: cover; }
.hero-icon {
  display: inline-block; width: 68px; height: 68px;
  background: linear-gradient(135deg, var(--primary), var(--purple));
  border-radius: 20px; margin-bottom: 20px;
  box-shadow: 0 8px 32px var(--primary-glow), inset 0 1px 0 rgba(255,255,255,0.15);
  font-size: 34px; line-height: 68px;
  animation: fadeInUp 0.5s ease both;
}
.hero h1 {
  font-size: 2.6rem; font-weight: 800; color: var(--text-bright);
  letter-spacing: -0.5px; margin-bottom: 6px;
  animation: fadeInUp 0.5s ease 0.1s both;
}
.hero h1 span {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.subtitle {
  font-size: 0.95rem; color: var(--muted);
  display: flex; align-items: center; justify-content: center;
  gap: 8px; flex-wrap: wrap;
  animation: fadeInUp 0.5s ease 0.2s both;
}
.updated-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  background: rgba(63, 185, 80, 0.1); border: 1px solid rgba(63, 185, 80, 0.2);
  font-size: 0.78rem; color: var(--success);
}
.updated-badge::before {
  content: ''; width: 6px; height: 6px; border-radius: 50%;
  background: var(--success); animation: pulse 2s ease-in-out infinite;
}

@media (max-width: 768px) {
  .hero { padding: 36px 0 24px; }
  .hero h1 { font-size: 1.7rem; }
}
</style>
