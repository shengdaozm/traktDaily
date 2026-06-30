<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import ParticleBg from '@/components/ParticleBg.vue'
import FloatingLights from '@/components/FloatingLights.vue'
import DynamicBg from '@/components/DynamicBg.vue'

const persona = inject('persona')
const monthlyStats = inject('monthlyStats')
const topMedia = inject('topMedia')
const selectedYear = inject('selectedYear')

const visible = ref(false)
const sectionRef = ref(null)
const canvasRef = ref(null)
const posterGenerated = ref(false)
const currentTheme = ref(0)

const themes = [
  { name: '墨绿影院', bg: '#0a0c0f', accent: '#a8c5a0', text: '#e8e4d9', dim: '#6a6f78' },
  { name: '暖暮胶片', bg: '#1a1410', accent: '#d4a857', text: '#e8e4d9', dim: '#8a7a6a' },
  { name: '雾蓝记忆', bg: '#0d1118', accent: '#6b8caf', text: '#d4dce4', dim: '#5a6a7a' },
]

const year = selectedYear

const yearStats = computed(() => {
  const stats = (monthlyStats.value || []).filter(s => s.year_month?.startsWith(String(year.value)))
  return {
    count: stats.reduce((a, s) => a + s.total_count, 0),
    minutes: stats.reduce((a, s) => a + s.total_minutes, 0),
    movies: stats.reduce((a, s) => a + s.movie_count, 0),
    episodes: stats.reduce((a, s) => a + s.episode_count, 0),
  }
})

const hours = computed(() => Math.floor(yearStats.value.minutes / 60))
const top3 = computed(() => (topMedia.value || []).slice(0, 3))

function generatePoster() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const W = 750, H = 1100
  canvas.width = W
  canvas.height = H
  const theme = themes[currentTheme.value]

  // 背景
  const grad = ctx.createLinearGradient(0, 0, 0, H)
  grad.addColorStop(0, theme.bg)
  grad.addColorStop(1, theme.bg + 'ee')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, W, H)

  // 装饰光晕
  const glow = ctx.createRadialGradient(W / 2, 200, 0, W / 2, 200, 300)
  glow.addColorStop(0, theme.accent + '15')
  glow.addColorStop(1, 'transparent')
  ctx.fillStyle = glow
  ctx.fillRect(0, 0, W, 400)

  // 年份
  ctx.fillStyle = theme.accent + '40'
  ctx.font = 'bold 80px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(String(year.value), W / 2, 120)

  // 标题
  ctx.fillStyle = theme.text
  ctx.font = 'bold 32px sans-serif'
  ctx.fillText('年度观影报告', W / 2, 170)

  // 分隔线
  ctx.strokeStyle = theme.accent + '60'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(W / 2 - 40, 190)
  ctx.lineTo(W / 2 + 40, 190)
  ctx.stroke()

  // 人格原型
  if (persona.value?.archetype) {
    ctx.fillStyle = theme.accent
    ctx.font = 'bold 28px sans-serif'
    ctx.fillText(persona.value.archetype, W / 2, 250)
  }
  if (persona.value?.archetype_description) {
    ctx.fillStyle = theme.dim
    ctx.font = '14px sans-serif'
    ctx.fillText(persona.value.archetype_description, W / 2, 278)
  }

  // 核心数据
  const stats = [
    { label: '观影总量', value: yearStats.value.count + ' 部' },
    { label: '观影时长', value: hours.value + ' 小时' },
    { label: '电影', value: yearStats.value.movies + ' 部' },
    { label: '剧集', value: yearStats.value.episodes + ' 集' },
  ]
  const statY = 340
  const statW = W / 4
  stats.forEach((s, i) => {
    const x = statW * i + statW / 2
    ctx.fillStyle = theme.text
    ctx.font = 'bold 24px sans-serif'
    ctx.fillText(s.value, x, statY)
    ctx.fillStyle = theme.dim
    ctx.font = '13px sans-serif'
    ctx.fillText(s.label, x, statY + 24)
  })

  // TOP3
  if (top3.value.length) {
    ctx.fillStyle = theme.accent
    ctx.font = 'bold 16px sans-serif'
    ctx.fillText('年度 TOP 3', W / 2, 430)

    top3.value.forEach((m, i) => {
      const y = 470 + i * 40
      const medals = ['🥇', '🥈', '🥉']
      ctx.font = '20px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(medals[i], 120, y)
      ctx.fillStyle = theme.text
      ctx.font = '16px sans-serif'
      const title = m.title.length > 25 ? m.title.substring(0, 25) + '...' : m.title
      ctx.fillText(title, 155, y)
      ctx.fillStyle = theme.dim
      ctx.font = '13px sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(m.watch_count + ' 次', W - 120, y)
      ctx.textAlign = 'center'
    })
  }

  // 标签
  if (persona.value?.tags?.length) {
    const tags = persona.value.tags.slice(0, 4)
    const tagY = 620
    ctx.fillStyle = theme.accent
    ctx.font = 'bold 16px sans-serif'
    ctx.fillText('观影标签', W / 2, tagY)

    tags.forEach((t, i) => {
      const y = tagY + 40 + i * 32
      ctx.fillStyle = theme.accent + '80'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(t.icon + ' ' + t.name, 180, y)
      ctx.fillStyle = theme.dim
      ctx.font = '12px sans-serif'
      const desc = t.desc.length > 20 ? t.desc.substring(0, 20) + '...' : t.desc
      ctx.fillText(desc, 320, y)
      ctx.textAlign = 'center'
    })
  }

  // 底部
  ctx.strokeStyle = theme.accent + '30'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(100, H - 100)
  ctx.lineTo(W - 100, H - 100)
  ctx.stroke()

  ctx.fillStyle = theme.dim
  ctx.font = '13px sans-serif'
  ctx.fillText('Powered by Trakt · traktDaily', W / 2, H - 70)
  ctx.fillStyle = theme.accent + '60'
  ctx.font = '12px sans-serif'
  ctx.fillText('每一帧光影，都是你的故事', W / 2, H - 45)

  posterGenerated.value = true
}

function downloadPoster() {
  const canvas = canvasRef.value
  if (!canvas) return
  const link = document.createElement('a')
  link.download = `trakt-${year.value}-poster.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

function switchTheme() {
  currentTheme.value = (currentTheme.value + 1) % themes.length
  generatePoster()
}

watch(visible, (v) => {
  if (v) setTimeout(generatePoster, 300)
})

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.15 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="poster-section">
    <DynamicBg />
    <ParticleBg :density="40" color="rgba(168, 197, 160, " />
    <FloatingLights :count="3" />
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">年度观影海报</p>
      <p class="narrative reveal-up" :class="{ visible }">
        生成你的专属年度海报，留住光影记忆
      </p>

      <div class="poster-wrapper reveal-scale" :class="{ visible }">
        <canvas ref="canvasRef" class="poster-canvas" />
      </div>

      <div class="actions stagger" :class="{ visible }">
        <button class="action-btn primary" @click="downloadPoster">
          <span>💾 保存海报</span>
        </button>
        <button class="action-btn" @click="switchTheme">
          <span>🎨 {{ themes[currentTheme].name }}</span>
        </button>
        <button class="action-btn" @click="generatePoster">
          <span>🔄 重新生成</span>
        </button>
      </div>

      <div class="share-hint reveal-up" :class="{ visible }">
        保存后可分享至朋友圈、微博等社交平台
      </div>
    </div>
  </section>
</template>

<style scoped>
.poster-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px; position: relative; overflow: hidden;
  background: linear-gradient(180deg, #11151a 0%, var(--cinema-black) 100%);
}
.section-content { max-width: 760px; width: 100%; text-align: center; position: relative; z-index: 1; }

.poster-wrapper {
  display: flex; justify-content: center; margin: 32px 0;
}
.poster-canvas {
  max-width: 100%; width: 375px; height: auto;
  border-radius: var(--radius); box-shadow: var(--shadow-hover);
  border: 1px solid var(--border);
}

.actions {
  display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
  margin-bottom: 16px;
}
.action-btn {
  padding: 12px 24px; border-radius: 24px;
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text); font-size: 0.9rem; font-weight: 600;
  cursor: pointer; transition: all var(--transition); letter-spacing: 1px;
}
.action-btn:hover {
  border-color: var(--border-bright); transform: translateY(-2px);
  box-shadow: var(--glow-green);
}
.action-btn.primary {
  background: linear-gradient(135deg, rgba(168,197,160,0.15), rgba(168,197,160,0.05));
  border-color: rgba(168,197,160,0.3);
  color: var(--bean-green-bright);
}
.action-btn.primary:hover {
  background: linear-gradient(135deg, rgba(168,197,160,0.25), rgba(168,197,160,0.1));
}

.share-hint {
  font-size: 0.8rem; color: var(--text-dim);
  letter-spacing: 1px; margin-top: 8px;
}

@media (max-width: 768px) {
  .poster-canvas { width: 300px; }
  .action-btn { padding: 10px 18px; font-size: 0.82rem; }
}
</style>
