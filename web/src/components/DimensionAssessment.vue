<script setup>
import { inject, ref, computed, onMounted } from 'vue'

const persona = inject('persona')
const visible = ref(false)
const sectionRef = ref(null)

const DIMENSIONS = [
  { key: 'immersion',  name: '沉浸度',   icon: '🌊', desc: '连续观看的沉浸倾向' },
  { key: 'quality',    name: '精品度',   icon: '💎', desc: '对作品品质的要求' },
  { key: 'diversity',  name: '广度',     icon: '🌈', desc: '类型覆盖的多样性' },
  { key: 'depth',      name: '深度',     icon: '🔮', desc: '长篇剧集的深耕程度' },
  { key: 'night_owl',  name: '夜猫指数', icon: '🌙', desc: '深夜观影的倾向' },
  { key: 'freshness',  name: '新鲜度',   icon: '✨', desc: '追新剧的积极性' },
  { key: 'global',     name: '国际化',   icon: '🌍', desc: '非主流地区内容比例' },
  { key: 'binge',      name: '连贯追剧', icon: '🔥', desc: '一口气追完的节奏' },
]

const dimensions = computed(() => {
  const r = persona.value?.radar || {}
  return DIMENSIONS.map(d => ({ ...d, value: r[d.key] || 0 }))
})

const overallScore = computed(() => {
  const vals = dimensions.value.map(d => d.value)
  if (!vals.length) return 0
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
})

const scoreLevel = computed(() => {
  const s = overallScore.value
  if (s >= 80) return { label: '硬核观众', color: 'var(--primary-bright)' }
  if (s >= 60) return { label: '热情观众', color: 'var(--primary-bright)' }
  if (s >= 40) return { label: '休闲观众', color: 'var(--text-2)' }
  return { label: '轻度观众', color: 'var(--text-3)' }
})

function barColor(value) {
  if (value >= 75) return 'linear-gradient(90deg, var(--primary), var(--primary-bright))'
  if (value >= 50) return 'linear-gradient(90deg, var(--primary-dim), var(--primary))'
  if (value >= 25) return 'linear-gradient(90deg, var(--text-dim), var(--primary-dim))'
  return 'linear-gradient(90deg, var(--text-dim), var(--text-dim))'
}

onMounted(() => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) visible.value = true })
  }, { threshold: 0.15 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="dim-section" v-if="persona">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">📊 观影维度测评</p>

      <!-- 综合评分 -->
      <div class="overall-card bean-card reveal-scale" :class="{ visible }">
        <div class="overall-ring" :style="{ '--ring-color': scoreLevel.color }">
          <svg viewBox="0 0 120 120" class="ring-svg">
            <circle cx="60" cy="60" r="52" class="ring-track" />
            <circle
              cx="60" cy="60" r="52"
              class="ring-fill"
              :stroke-dasharray="2 * Math.PI * 52"
              :stroke-dashoffset="2 * Math.PI * 52 * (1 - overallScore / 100)"
            />
          </svg>
          <div class="ring-inner">
            <span class="ring-num">{{ overallScore }}</span>
            <span class="ring-unit">/100</span>
          </div>
        </div>
        <div class="overall-info">
          <span class="overall-label">综合观影指数</span>
          <span class="overall-tag" :style="{ color: scoreLevel.color }">{{ scoreLevel.label }}</span>
          <span class="overall-archetype" v-if="persona.archetype">{{ persona.archetype }}</span>
        </div>
      </div>

      <!-- 维度列表 -->
      <div class="dim-list stagger" :class="{ visible }">
        <div v-for="(d, i) in dimensions" :key="d.key" class="dim-item bean-card">
          <div class="dim-header">
            <span class="dim-icon">{{ d.icon }}</span>
            <span class="dim-name">{{ d.name }}</span>
            <span class="dim-value" :style="{ color: d.value >= 60 ? 'var(--primary-bright)' : 'var(--text-2)' }">{{ d.value }}</span>
          </div>
          <div class="dim-bar-bg">
            <div
              class="dim-bar-fill"
              :style="{ width: visible ? d.value + '%' : '0%', background: barColor(d.value) }"
            ></div>
          </div>
          <p class="dim-desc">{{ d.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.dim-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: var(--section-gap) var(--page-margin);
}
.section-content { max-width: 680px; width: 100%; position: relative; z-index: 1; }

/* ── 综合评分卡 ── */
.overall-card {
  display: flex; align-items: center; gap: 28px;
  padding: var(--space-lg); margin-bottom: var(--space-lg);
}
.overall-ring {
  position: relative; width: 120px; height: 120px; flex-shrink: 0;
}
.ring-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.ring-track {
  fill: none; stroke: rgba(255,255,255,0.06); stroke-width: 6;
}
.ring-fill {
  fill: none; stroke: var(--ring-color, var(--primary)); stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1) 0.3s;
}
.ring-inner {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.ring-num {
  font-size: 2.2rem; font-weight: 800; color: var(--text-1);
  line-height: 1; font-variant-numeric: tabular-nums;
}
.ring-unit { font-size: 0.78rem; color: var(--text-3); }

.overall-info {
  display: flex; flex-direction: column; gap: 6px;
}
.overall-label { font-size: 0.82rem; color: var(--text-3); letter-spacing: 1px; }
.overall-tag { font-size: 1.3rem; font-weight: 700; }
.overall-archetype {
  font-size: 0.92rem; color: var(--primary); font-weight: 600;
}

/* ── 维度列表 ── */
.dim-list {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}
.dim-item {
  padding: 18px 20px; display: flex; flex-direction: column; gap: 10px;
}
.dim-header {
  display: flex; align-items: center; gap: 8px;
}
.dim-icon { font-size: 1.1rem; }
.dim-name {
  font-size: 0.92rem; font-weight: 700; color: var(--text-1);
  flex: 1;
}
.dim-value {
  font-size: 1.4rem; font-weight: 800; font-variant-numeric: tabular-nums;
  line-height: 1;
}
.dim-bar-bg {
  height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px;
  overflow: hidden;
}
.dim-bar-fill {
  height: 100%; border-radius: 3px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  transition-delay: 0.2s;
}
.dim-desc {
  font-size: 0.76rem; color: var(--text-3); line-height: 1.5;
}

@media (max-width: 768px) {
  .dim-list { grid-template-columns: 1fr; }
  .overall-card { flex-direction: column; text-align: center; gap: 16px; padding: var(--space-md); }
  .overall-info { align-items: center; }
  .ring-num { font-size: 1.8rem; }
  .dim-value { font-size: 1.2rem; }
}
</style>
