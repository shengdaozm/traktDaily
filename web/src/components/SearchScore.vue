<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { loadTmdbConfig, getTmdbApiKey, TMDB_API, TMDB_IMAGE_BASE } from '../config'
import { computeScore } from '../utils/scoring'

const profile = inject('profile', ref(null))
const tmdbReady = ref(false)

onMounted(async () => {
  await loadTmdbConfig()
  tmdbReady.value = !!getTmdbApiKey()
})

const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const selectedShow = ref(null)
const scoreResult = ref(null)

// 搜索剧集
async function searchShow() {
  if (!searchQuery.value.trim()) return
  const apiKey = getTmdbApiKey()
  if (!apiKey) {
    console.warn('TMDB API Key 未配置')
    return
  }
  searching.value = true
  selectedShow.value = null
  scoreResult.value = null

  try {
    const resp = await fetch(
      `${TMDB_API}/search/tv?api_key=${apiKey}&query=${encodeURIComponent(searchQuery.value)}&page=1&language=zh-CN`
    )
    if (!resp.ok) throw new Error('搜索失败')
    const data = await resp.json()
    searchResults.value = (data.results || [])
      .filter(s => s.first_air_date)
      .slice(0, 8)
  } catch (e) {
    console.error('搜索失败:', e)
  } finally {
    searching.value = false
  }
}

// 选择剧集 → 打分
function selectShow(show) {
  selectedShow.value = show
  scoreResult.value = null

  // 需要完整详情（集数、季数、时长等）
  fetchShowDetail(show.id).then(detail => {
    if (profile.value) {
      scoreResult.value = computeScore(profile.value, detail)
    }
  })
}

// 获取剧集详情
async function fetchShowDetail(id) {
  const apiKey = getTmdbApiKey()
  const resp = await fetch(
    `${TMDB_API}/tv/${id}?api_key=${apiKey}&language=zh-CN`
  )
  return resp.json()
}

// 评分等级
const scoreLevel = computed(() => {
  const s = scoreResult.value?.score
  if (s == null) return null
  if (s >= 85) return { label: '强烈推荐', emoji: '🔥', color: '#4ade80' }
  if (s >= 70) return { label: '大概率喜欢', emoji: '⭐', color: '#86A89C' }
  if (s >= 55) return { label: '可以尝试', emoji: '🤔', color: '#f59e0b' }
  if (s >= 40) return { label: '兴趣一般', emoji: '😐', color: '#f97316' }
  return { label: '大概率不感兴趣', emoji: '❌', color: '#ef4444' }
})

// 清除搜索
function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
  selectedShow.value = null
  scoreResult.value = null
}

function formatYear(date) {
  return date ? date.substring(0, 4) : '—'
}

function genreNames(ids) {
  const map = {
    10759: '动作冒险', 16: '动画', 35: '喜剧', 80: '犯罪',
    99: '纪录', 18: '剧情', 10751: '家庭', 10762: '儿童',
    9648: '悬疑', 10763: '新闻', 10764: '真人秀', 10765: '科幻奇幻',
    10766: '肥皂', 10767: '脱口秀', 10768: '战争', 37: '西部',
    28: '动作', 12: '冒险', 14: '奇幻', 36: '历史',
    27: '恐怖', 53: '惊悚', 10752: '战争', 878: '科幻',
  }
  return (ids || []).map(id => map[id] || '').filter(Boolean).join(' · ')
}
</script>

<template>
  <section class="search-score">
    <p class="section-label">🔍 新剧打分</p>
    <p class="narrative">搜索任意剧集，看看和你有多搭</p>

    <!-- TMDB 未配置提示 -->
    <div v-if="!tmdbReady" class="tmdb-warning glass-card">
      <p>⚠️ TMDB API Key 未配置，无法搜索</p>
      <p>请在 GitHub Settings → Secrets 中添加 TMDB_API_KEY，然后重新部署</p>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        @keyup.enter="searchShow"
        placeholder="输入剧名，如「人生切割术」..."
        class="search-input"
      />
      <button @click="searchShow" :disabled="!searchQuery.trim() || searching" class="search-btn">
        {{ searching ? '搜索中...' : '搜索' }}
      </button>
      <button v-if="searchResults.length || selectedShow" @click="clearSearch" class="clear-btn">
        ✕
      </button>
    </div>

    <!-- 搜索结果列表 -->
    <div v-if="searchResults.length && !selectedShow" class="results-list">
      <div
        v-for="show in searchResults"
        :key="show.id"
        class="result-item glass-card"
        @click="selectShow(show)"
      >
        <img
          v-if="show.poster_path"
          :src="`${TMDB_IMAGE_BASE}${show.poster_path}`"
          class="result-poster"
          loading="lazy"
        />
        <div v-else class="result-poster placeholder">📺</div>
        <div class="result-info">
          <div class="result-title">{{ show.name }}</div>
          <div class="result-meta">
            <span>{{ formatYear(show.first_air_date) }}</span>
            <span v-if="show.genre_ids" class="result-genre">{{ genreNames(show.genre_ids) }}</span>
          </div>
          <div v-if="show.overview" class="result-over">{{ show.overview.substring(0, 80) }}...</div>
        </div>
      </div>
    </div>

    <!-- 搜索结果空 -->
    <div v-if="!searching && !searchResults.length && searchQuery" class="empty-result">
      <p>未找到相关剧集，换个关键词试试~</p>
    </div>

    <!-- 加载中 -->
    <div v-if="searching" class="searching">
      <div class="spinner"></div>
      <p>搜索中...</p>
    </div>

    <!-- 选中剧集 + 打分结果 -->
    <div v-if="selectedShow" class="score-detail">
      <!-- 剧集信息 -->
      <div class="selected-show glass-card">
        <img
          v-if="selectedShow.poster_path"
          :src="`${TMDB_IMAGE_BASE}${selectedShow.poster_path}`"
          class="selected-poster"
        />
        <div v-else class="selected-poster placeholder">📺</div>
        <div class="selected-info">
          <h3>{{ selectedShow.name }}</h3>
          <p class="selected-meta">{{ formatYear(selectedShow.first_air_date) }} · {{ genreNames(selectedShow.genre_ids) }}</p>
          <p v-if="selectedShow.overview" class="selected-overview">{{ selectedShow.overview.substring(0, 150) }}...</p>
        </div>
      </div>

      <!-- 打分结果 -->
      <template v-if="scoreResult">
        <!-- 分数 -->
        <div class="score-display glass-card">
          <div class="score-circle" :style="{ borderColor: scoreLevel.color }">
            <span class="score-number" :style="{ color: scoreLevel.color }">{{ scoreResult.score }}</span>
            <span class="score-unit">/100</span>
          </div>
          <div class="score-label">
            <span class="score-emoji">{{ scoreLevel.emoji }}</span>
            <span class="score-text" :style="{ color: scoreLevel.color }">{{ scoreLevel.label }}</span>
          </div>
          <div v-if="scoreResult.confidence === 'low'" class="confidence-note">
            ⚠️ 数据较少，评分仅供参考
          </div>
        </div>

        <!-- 维度拆解 -->
        <div class="breakdown glass-card">
          <h4>📊 维度拆解</h4>
          <div
            v-for="(value, key) in scoreResult.breakdown"
            :key="key"
            class="breakdown-row"
          >
            <span class="breakdown-label">{{ key }}</span>
            <div class="breakdown-bar-bg">
              <div
                class="breakdown-bar"
                :style="{ width: value + '%', backgroundColor: getBarColor(value) }"
              ></div>
            </div>
            <span class="breakdown-value">{{ value }}%</span>
          </div>
        </div>

        <!-- 推荐理由 -->
        <div class="reasons glass-card">
          <h4>💬 推荐理由</h4>
          <div
            v-for="(reason, i) in scoreResult.reasons"
            :key="i"
            :class="['reason-item', `reason-${reason.type}`]"
          >
            <span class="reason-icon">{{ reason.type === 'positive' ? '✅' : reason.type === 'negative' ? '⚠️' : 'ℹ️' }}</span>
            <span class="reason-text">{{ reason.text }}</span>
          </div>
        </div>
      </template>

      <!-- 无画像 -->
      <div v-else class="no-profile glass-card">
        <p>⚠️ 用户画像数据尚未生成</p>
        <p>请先在 GitHub Actions 中运行一次完整的数据抓取</p>
      </div>

      <!-- 重新搜索 -->
      <button @click="clearSearch" class="back-btn">← 返回搜索结果</button>
    </div>
  </section>
</template>

<style scoped>
.search-score {
  max-width: 680px;
  margin: 0 auto;
  padding: 0 var(--space-sm);
}

.tmdb-warning {
  padding: 20px;
  text-align: center;
  color: var(--text-3);
  margin-bottom: 24px;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-1);
  font-size: 0.95rem;
  outline: none;
  transition: border-color var(--transition);
}

.search-input:focus {
  border-color: var(--primary);
}

.search-input::placeholder {
  color: var(--text-dim);
}

.search-btn {
  padding: 12px 20px;
  background: var(--primary-dim);
  color: var(--text-1);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
  white-space: nowrap;
}

.search-btn:hover:not(:disabled) {
  background: var(--primary);
}

.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.clear-btn {
  padding: 12px 14px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-3);
  cursor: pointer;
  font-size: 1rem;
  transition: all var(--transition);
}

.clear-btn:hover {
  border-color: var(--text-3);
  color: var(--text-1);
}

/* 搜索结果列表 */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  display: flex;
  gap: 14px;
  padding: 14px;
  cursor: pointer;
  transition: all var(--transition);
}

.result-item:hover {
  border-color: var(--primary-dim);
}

.result-poster {
  width: 50px;
  height: 75px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
}

.result-poster.placeholder {
  background: var(--card-solid);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-1);
  margin-bottom: 4px;
}

.result-meta {
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-3);
  margin-bottom: 6px;
}

.result-genre {
  color: var(--primary-bright);
}

.result-overview {
  font-size: 0.82rem;
  color: var(--text-3);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 空结果 */
.empty-result {
  text-align: center;
  padding: 32px 0;
  color: var(--text-3);
}

/* 搜索中 */
.searching {
  text-align: center;
  padding: 32px 0;
  color: var(--text-3);
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 选中剧集 */
.selected-show {
  display: flex;
  gap: 16px;
  padding: 16px;
  margin-bottom: 16px;
}

.selected-poster {
  width: 80px;
  height: 120px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.selected-poster.placeholder {
  background: var(--card-solid);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

.selected-info h3 {
  font-size: 1.1rem;
  color: var(--text-1);
  margin-bottom: 6px;
}

.selected-meta {
  font-size: 0.82rem;
  color: var(--text-3);
  margin-bottom: 8px;
}

.selected-overview {
  font-size: 0.85rem;
  color: var(--text-2);
  line-height: 1.6;
}

/* 分数显示 */
.score-display {
  padding: 28px;
  text-align: center;
  margin-bottom: 16px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 4px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.score-number {
  font-size: 2.8rem;
  font-weight: 800;
  line-height: 1;
}

.score-unit {
  font-size: 0.9rem;
  color: var(--text-3);
}

.score-label {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.score-emoji {
  font-size: 1.3rem;
}

.score-text {
  font-size: 1.1rem;
  font-weight: 700;
}

.confidence-note {
  margin-top: 12px;
  font-size: 0.82rem;
  color: var(--text-3);
}

/* 维度拆解 */
.breakdown {
  padding: 20px;
  margin-bottom: 16px;
}

.breakdown h4 {
  font-size: 0.95rem;
  color: var(--text-1);
  margin-bottom: 16px;
}

.breakdown-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.breakdown-label {
  width: 80px;
  font-size: 0.82rem;
  color: var(--text-3);
  flex-shrink: 0;
}

.breakdown-bar-bg {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.breakdown-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.breakdown-value {
  width: 40px;
  text-align: right;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-2);
}

/* 推荐理由 */
.reasons {
  padding: 20px;
  margin-bottom: 16px;
}

.reasons h4 {
  font-size: 0.95rem;
  color: var(--text-1);
  margin-bottom: 16px;
}

.reason-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.88rem;
}

.reason-item:last-child {
  border-bottom: none;
}

.reason-icon {
  flex-shrink: 0;
  font-size: 1rem;
}

.reason-text {
  color: var(--text-2);
  line-height: 1.5;
}

/* 无画像 */
.no-profile {
  padding: 24px;
  text-align: center;
  color: var(--text-3);
  margin-bottom: 16px;
}

/* 返回按钮 */
.back-btn {
  width: 100%;
  padding: 12px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-2);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all var(--transition);
}

.back-btn:hover {
  border-color: var(--primary-dim);
  color: var(--text-1);
}

@media (max-width: 768px) {
  .result-item {
    padding: 10px;
    gap: 10px;
  }
  .result-poster {
    width: 40px;
    height: 60px;
  }
  .score-circle {
    width: 100px;
    height: 100px;
  }
  .score-number {
    font-size: 2.2rem;
  }
}
</style>

<script>
function getBarColor(value) {
  if (value >= 80) return '#4ade80'
  if (value >= 60) return '#86A89C'
  if (value >= 40) return '#f59e0b'
  return '#ef4444'
}
</script>
