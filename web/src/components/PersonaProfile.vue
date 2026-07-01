<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'

const persona = inject('persona')
const diversityIndex = inject('diversityIndex')
const visible = ref(false)
const sectionRef = ref(null)
const narrativeVisible = ref(false)
const displayedNarrative = ref('')

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
      axisName: { color: '#8C949F', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      splitArea: { areaStyle: { color: ['transparent', 'rgba(255,255,255,0.01)'] } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.map(d => d.value),
        name: '观影DNA',
        areaStyle: { color: 'rgba(134,168,156,0.1)' },
        lineStyle: { color: '#86A89C', width: 1.5 },
        itemStyle: { color: '#A0BEB4' },
        symbolSize: 4,
      }],
      animationDuration: 1200, animationEasing: 'cubicOut', animationDelay: 300,
    }],
  }
}, [radarData])

const wordCloud = computed(() => {
  const words = []
  const div = diversityIndex.value || {}
  ;(div.top_genres || []).forEach(g => {
    const genreMap = { action: '动作', adventure: '冒险', animation: '动画', anime: '动漫',
      comedy: '喜剧', crime: '犯罪', documentary: '纪录片', drama: '剧情',
      fantasy: '奇幻', horror: '恐怖', mystery: '悬疑', romance: '爱情',
      'science-fiction': '科幻', thriller: '惊悚', war: '战争' }
    words.push({ text: genreMap[g.genre] || g.genre, weight: g.count })
  })
  ;(persona.value?.tags || []).forEach(t => {
    words.push({ text: t.name, weight: 50, isTag: true })
  })
  if (persona.value?.archetype) {
    words.push({ text: persona.value.archetype, weight: 100, isArchetype: true })
  }
  return words
})

const traits = computed(() => {
  const t = persona.value?.personality_traits || {}
  const labels = { openness: '开放性', conscientiousness: '尽责性', extraversion: '外向性', agreeableness: '宜人性', neuroticism: '神经质' }
  return Object.entries(t).map(([k, v]) => ({ key: k, label: labels[k] || k, value: v }))
})

function typeNarrative(text) {
  if (!text) return
  displayedNarrative.value = ''
  let i = 0
  const interval = setInterval(() => {
    if (i >= text.length) {
      clearInterval(interval)
      return
    }
    displayedNarrative.value += text[i]
    i++
  }, 30)
}

watch([visible, () => persona.value], ([v]) => {
  if (v && persona.value?.narrative) {
    setTimeout(() => {
      narrativeVisible.value = true
      typeNarrative(persona.value.narrative)
    }, 800)
  }
})

const registerResize = inject('registerResize')
onMounted(() => {
  registerResize?.(resize)
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { visible.value = true; resize() } })
  }, { threshold: 0.1 })
  if (sectionRef.value) obs.observe(sectionRef.value)
})
</script>

<template>
  <section ref="sectionRef" class="persona-section" v-if="persona">
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">个人年度观影画像</p>

      <!-- 原型 -->
      <div class="archetype reveal-scale" :class="{ visible }">
        <div class="archetype-glow" />
        <div class="archetype-name">{{ persona.archetype }}</div>
        <div class="archetype-desc" v-if="persona.archetype_description">{{ persona.archetype_description }}</div>
      </div>

      <!-- 标签 -->
      <div class="tags-row stagger" :class="{ visible }" v-if="persona.tags?.length">
        <div v-for="t in persona.tags" :key="t.name" class="tag-card bean-card">
          <span class="tag-icon">{{ t.icon }}</span>
          <span class="tag-name">{{ t.name }}</span>
          <span class="tag-desc">{{ t.desc }}</span>
        </div>
      </div>

      <!-- 雷达图 + 性格 -->
      <div class="radar-traits reveal-up" :class="{ visible }">
        <div class="radar-card bean-card">
          <h3 class="card-title">观影 DNA</h3>
          <div ref="chartRef" class="radar-chart" />
        </div>
        <div class="traits-card bean-card" v-if="traits.length">
          <h3 class="card-title">性格特质</h3>
          <div class="traits-list">
            <div v-for="t in traits" :key="t.key" class="trait-item">
              <span class="trait-label">{{ t.label }}</span>
              <span class="trait-value">{{ t.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 关键词云 -->
      <div class="word-cloud reveal-up" :class="{ visible }" v-if="wordCloud.length">
        <h3 class="card-title center">观影关键词</h3>
        <div class="cloud-container">
          <span
            v-for="(w, i) in wordCloud"
            :key="i"
            class="cloud-word"
            :class="{ archetype: w.isArchetype, tag: w.isTag }"
            :style="{
              fontSize: w.isArchetype ? '1.8rem' : w.isTag ? '1.1rem' : Math.min(0.7 + w.weight / 30, 1.6) + 'rem',
              animationDelay: (i * 0.08) + 's'
            }"
          >{{ w.text }}</span>
        </div>
      </div>

      <!-- 叙事 -->
      <div class="narrative-box bean-card reveal-up" :class="{ visible }" v-if="persona.narrative">
        <p class="narrative-text">
          <span class="cursor" v-if="narrativeVisible">{{ displayedNarrative }}<span class="cursor-blink">|</span></span>
          <span v-else>{{ persona.narrative }}</span>
        </p>
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
  padding: var(--section-gap) var(--page-margin); position: relative;
}
.section-content { max-width: 720px; width: 100%; position: relative; z-index: 1; }

.archetype { text-align: center; margin-bottom: 28px; }
.archetype-name {
  font-size: clamp(1.8rem, 5vw, 2.6rem); font-weight: 800;
  color: var(--text-1); line-height: 1.2; letter-spacing: 2px;
}
.archetype-desc { font-size: 0.92rem; color: var(--text-3); margin-top: 8px; }

.tags-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 28px; }
.tag-card {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 14px 18px; border-radius: 14px; min-width: 120px;
}
.tag-icon {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(134,168,156,0.08);
  border: 1px solid rgba(134,168,156,0.15);
  font-size: 0.85rem; font-weight: 700; color: var(--primary-bright);
}
.tag-name { font-size: 0.88rem; font-weight: 700; color: var(--text-1); }
.tag-desc { font-size: 0.72rem; color: var(--text-3); text-align: center; }

.radar-traits { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 28px; }
.radar-card, .traits-card { padding: var(--space-md); }
.card-title { font-size: 0.82rem; color: var(--text-3); margin-bottom: 12px; font-weight: 600; letter-spacing: 1px; }
.card-title.center { text-align: center; margin-bottom: 18px; }
.radar-chart { width: 100%; height: 280px; }

.traits-list { display: flex; flex-direction: column; gap: 12px; }
.trait-item { display: flex; flex-direction: column; gap: 2px; }
.trait-label { font-size: 0.75rem; color: var(--primary); font-weight: 600; }
.trait-value { font-size: 0.8rem; color: var(--text-2); }

.word-cloud { margin-bottom: 28px; }
.cloud-container {
  display: flex; flex-wrap: wrap; gap: 12px 16px;
  justify-content: center; align-items: center;
  padding: 24px; min-height: 120px;
}
.cloud-word {
  display: inline-block; color: var(--text-2); opacity: 0;
  animation: fadeIn 0.4s ease forwards;
  transition: color var(--transition); cursor: default;
  line-height: 1.4;
}
.cloud-word:hover { color: var(--primary-bright); }
.cloud-word.archetype {
  color: var(--primary-bright); font-weight: 800;
}
.cloud-word.tag { color: var(--text-1); font-weight: 700; }

.narrative-box { padding: var(--space-md); margin-bottom: 24px; }
.narrative-text {
  font-size: 0.95rem; line-height: 1.9; color: var(--text-2);
  text-align: justify; letter-spacing: 0.5px;
}
.cursor-blink { animation: blink 1s step-end infinite; color: var(--primary); }
@keyframes blink { 50% { opacity: 0; } }

.highlights { display: flex; flex-direction: column; gap: 10px; }
.highlight-item {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 0.85rem; color: var(--text-3);
  padding: 10px 16px; border-radius: var(--radius);
  background: rgba(255,255,255,0.02); border: 1px solid var(--border);
}
.highlight-bullet { color: var(--primary); font-weight: bold; flex-shrink: 0; }

@media (max-width: 768px) {
  .archetype-name { font-size: 1.8rem; }
  .radar-traits { grid-template-columns: 1fr; }
  .radar-chart { height: 260px; }
  .tags-row { gap: 8px; }
  .tag-card { min-width: 100px; padding: 10px 14px; }
}
</style>
