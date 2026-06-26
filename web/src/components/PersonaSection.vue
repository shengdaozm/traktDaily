<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const persona = inject('persona')
const visible = ref(false)
const sectionRef = ref(null)

const radarData = computed(() => {
  const r = persona.value?.radar || {}
  return [
    { name: '沉浸度', value: r.immersion || 0 },
    { name: '精品度', value: r.quality || 0 },
    { name: '广度', value: r.diversity || 0 },
    { name: '深度', value: r.depth || 0 },
    { name: '夜猫', value: r.night_owl || 0 },
    { name: '新鲜度', value: r.freshness || 0 },
    { name: '国际化', value: r.global || 0 },
    { name: '连贯追剧', value: r.binge || 0 },
  ]
})

const { chartRef, resize } = useECharts(() => {
  const data = radarData.value
  if (!data.length) return null
  return {
    tooltip: { ...TOOLTIP_STYLE },
    radar: {
      indicator: data.map(d => ({ name: d.name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#8b949e', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      splitArea: { areaStyle: { color: ['transparent', 'rgba(255,255,255,0.02)'] } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.map(d => d.value),
        name: '观影DNA',
        areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5,
          colorStops: [{ offset: 0, color: 'rgba(240,192,64,0.25)' }, { offset: 1, color: 'rgba(240,192,64,0.05)' }] } },
        lineStyle: { color: '#f0c040', width: 2 },
        itemStyle: { color: '#f0c040' },
        symbolSize: 5,
      }],
      animationDuration: 1500, animationEasing: 'cubicOut', animationDelay: 300,
    }],
  }
}, [radarData])

const registerResize = inject('registerResize')
onMounted(() => {
  registerResize?.(resize)
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { visible.value = true; resize() } })
  }, { threshold: 0.15 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})

const traits = computed(() => {
  const t = persona.value?.personality_traits || {}
  const labels = { openness: '开放性', conscientiousness: '尽责性', extraversion: '外向性', agreeableness: '宜人性', neuroticism: '神经质' }
  return Object.entries(t).map(([k, v]) => ({ key: k, label: labels[k] || k, value: v }))
})
</script>

<template>
  <section ref="sectionRef" class="persona-section" v-if="persona">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">🧬 观影人格画像</p>

      <!-- 原型 -->
      <div class="archetype reveal-scale" :class="{ visible }">
        <div class="archetype-name">{{ persona.archetype }}</div>
        <div class="archetype-desc" v-if="persona.archetype_description">{{ persona.archetype_description }}</div>
      </div>

      <!-- 标签 -->
      <div class="tags-row stagger" :class="{ visible }" v-if="persona.tags?.length">
        <div v-for="t in persona.tags" :key="t.name" class="tag-card glass-card">
          <span class="tag-icon">{{ t.icon }}</span>
          <span class="tag-name">{{ t.name }}</span>
          <span class="tag-desc">{{ t.desc }}</span>
        </div>
      </div>

      <!-- 雷达图 + 性格 -->
      <div class="radar-traits reveal-up" :class="{ visible }">
        <div class="radar-card glass-card">
          <h3 class="card-title">观影 DNA</h3>
          <div ref="chartRef" class="radar-chart" />
        </div>
        <div class="traits-card glass-card" v-if="traits.length">
          <h3 class="card-title">性格特质</h3>
          <div class="traits-list">
            <div v-for="t in traits" :key="t.key" class="trait-item">
              <span class="trait-label">{{ t.label }}</span>
              <span class="trait-value">{{ t.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 叙事 -->
      <div class="narrative-box reveal-up" :class="{ visible }" v-if="persona.narrative">
        <p class="narrative-text">{{ persona.narrative }}</p>
      </div>

      <!-- 高光时刻 -->
      <div class="highlights stagger" :class="{ visible }" v-if="persona.highlights?.length">
        <div v-for="(h, i) in persona.highlights" :key="i" class="highlight-item">
          <span class="highlight-bullet">✦</span>
          <span>{{ h }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.persona-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 60px 24px;
  background: linear-gradient(180deg, #0d1117 0%, #1a1208 100%);
}
.section-content { max-width: 760px; width: 100%; }
.section-label { font-size: 0.85rem; color: var(--accent); text-align: center; margin-bottom: 16px; font-weight: 600; }

.archetype { text-align: center; margin-bottom: 28px; }
.archetype-name {
  font-size: 2.8rem; font-weight: 900;
  background: linear-gradient(135deg, var(--accent), var(--accent-warm), var(--pink));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1.2; letter-spacing: 1px;
}
.archetype-desc { font-size: 1rem; color: var(--text-dim); margin-top: 8px; }

.tags-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 28px; }
.tag-card {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 14px 18px; border-radius: 14px; min-width: 120px;
}
.tag-icon { font-size: 1.6rem; }
.tag-name { font-size: 0.9rem; font-weight: 700; color: var(--text-bright); }
.tag-desc { font-size: 0.72rem; color: var(--text-dim); text-align: center; }

.radar-traits { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 28px; }
.radar-card, .traits-card { padding: 20px; }
.card-title { font-size: 0.85rem; color: var(--text-dim); margin-bottom: 12px; font-weight: 600; }
.radar-chart { width: 100%; height: 300px; }

.traits-list { display: flex; flex-direction: column; gap: 12px; }
.trait-item { display: flex; flex-direction: column; gap: 2px; }
.trait-label { font-size: 0.78rem; color: var(--text-dim); font-weight: 600; }
.trait-value { font-size: 0.82rem; color: var(--text); }

.narrative-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px; margin-bottom: 24px;
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
}
.narrative-text {
  font-size: 1rem; line-height: 1.9; color: var(--text);
  text-align: justify;
}

.highlights { display: flex; flex-direction: column; gap: 10px; }
.highlight-item {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 0.88rem; color: var(--text-dim);
  padding: 8px 14px; border-radius: 10px;
  background: var(--surface); border: 1px solid var(--border);
}
.highlight-bullet { color: var(--accent); font-weight: bold; flex-shrink: 0; }

@media (max-width: 768px) {
  .archetype-name { font-size: 1.8rem; }
  .radar-traits { grid-template-columns: 1fr; }
  .radar-chart { height: 260px; }
  .tags-row { gap: 8px; }
  .tag-card { min-width: 100px; padding: 10px 14px; }
}
</style>
