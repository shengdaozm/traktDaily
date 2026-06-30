<script setup>
import { inject, ref, computed, onMounted, watch } from 'vue'
import { useECharts, TOOLTIP_STYLE } from '@/composables/useEcharts'
import FloatingLights from '@/components/FloatingLights.vue'

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
      axisName: { color: '#8a8f99', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(168,197,160,0.08)' } },
      splitArea: { areaStyle: { color: ['transparent', 'rgba(168,197,160,0.02)'] } },
      axisLine: { lineStyle: { color: 'rgba(168,197,160,0.08)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.map(d => d.value),
        name: '观影DNA',
        areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5,
          colorStops: [{ offset: 0, color: 'rgba(168,197,160,0.3)' }, { offset: 1, color: 'rgba(168,197,160,0.05)' }] } },
        lineStyle: { color: '#a8c5a0', width: 2 },
        itemStyle: { color: '#c4dcbc' },
        symbolSize: 5,
      }],
      animationDuration: 2000, animationEasing: 'elasticOut', animationDelay: 300,
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
    <FloatingLights :count="3" />
    <div class="bg-glow" />
    <div class="section-content">
      <p class="section-label reveal-up" :class="{ visible }">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M4 8 L4 4 L8 4 M16 4 L20 4 L20 8 M20 16 L20 20 L16 20 M8 20 L4 20 L4 16"/><circle cx="12" cy="12" r="4"/></svg>
        个人年度观影画像
      </p>

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
  padding: 60px 24px; position: relative; overflow: hidden;
  background: linear-gradient(180deg, var(--cinema-black) 0%, #0d1410 100%);
}
.bg-glow {
  position: absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);
  width: 500px; height: 500px; border-radius: 50%;
  background: radial-gradient(circle, rgba(168,197,160,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.section-content { max-width: 760px; width: 100%; position: relative; z-index: 1; }

.archetype { text-align: center; margin-bottom: 28px; position: relative; }
.archetype-glow {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 300px; height: 80px; border-radius: 50%;
  background: radial-gradient(ellipse, rgba(168,197,160,0.15) 0%, transparent 70%);
  filter: blur(20px); pointer-events: none;
}
.archetype-name {
  font-size: 2.6rem; font-weight: 900; position: relative;
  background: linear-gradient(135deg, var(--bean-green-bright), var(--bean-green), var(--warm-amber));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1.2; letter-spacing: 2px;
  animation: glow-pulse 3s ease-in-out infinite;
}
.archetype-desc { font-size: 0.95rem; color: var(--text-dim); margin-top: 8px; }

.tags-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 28px; }
.tag-card {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 14px 18px; border-radius: 14px; min-width: 120px;
}
.tag-icon {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(168,197,160,0.2), rgba(168,197,160,0.05));
  border: 1px solid rgba(168,197,160,0.2);
  font-size: 1rem; font-weight: 800; color: var(--bean-green-bright);
}
.tag-name { font-size: 0.9rem; font-weight: 700; color: var(--bean-green-bright); }
.tag-desc { font-size: 0.72rem; color: var(--text-dim); text-align: center; }

.radar-traits { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 28px; }
.radar-card, .traits-card { padding: 20px; }
.card-title { font-size: 0.85rem; color: var(--text-dim); margin-bottom: 12px; font-weight: 600; letter-spacing: 1px; }
.card-title.center { text-align: center; margin-bottom: 18px; }
.radar-chart { width: 100%; height: 300px; }

.traits-list { display: flex; flex-direction: column; gap: 12px; }
.trait-item { display: flex; flex-direction: column; gap: 2px; }
.trait-label { font-size: 0.78rem; color: var(--bean-green); font-weight: 600; }
.trait-value { font-size: 0.82rem; color: var(--text); }

.word-cloud { margin-bottom: 28px; }
.cloud-container {
  display: flex; flex-wrap: wrap; gap: 12px 16px;
  justify-content: center; align-items: center;
  padding: 24px; min-height: 120px;
}
.cloud-word {
  display: inline-block; color: var(--text); opacity: 0;
  animation: fadeInScale 0.5s ease forwards;
  transition: all var(--transition); cursor: default;
  line-height: 1.4;
}
.cloud-word:hover { color: var(--bean-green-bright); transform: scale(1.1); }
.cloud-word.archetype {
  color: var(--bean-green-bright); font-weight: 900;
  text-shadow: 0 0 15px rgba(168,197,160,0.3);
}
.cloud-word.tag { color: var(--warm-amber); font-weight: 700; }

.narrative-box { padding: 24px; margin-bottom: 24px; }
.narrative-text {
  font-size: 1rem; line-height: 2; color: var(--text);
  text-align: justify; letter-spacing: 0.5px;
}
.cursor-blink { animation: blink 1s step-end infinite; color: var(--bean-green); }
@keyframes blink { 50% { opacity: 0; } }

.highlights { display: flex; flex-direction: column; gap: 10px; }
.highlight-item {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 0.88rem; color: var(--text-dim);
  padding: 10px 16px; border-radius: 10px;
  background: var(--surface-frost); border: 1px solid var(--border);
}
.highlight-bullet { color: var(--bean-green); font-weight: bold; flex-shrink: 0; }

@media (max-width: 768px) {
  .archetype-name { font-size: 1.8rem; }
  .radar-traits { grid-template-columns: 1fr; }
  .radar-chart { height: 260px; }
  .tags-row { gap: 8px; }
  .tag-card { min-width: 100px; padding: 10px 14px; }
}
</style>
