import { ref, shallowRef, computed } from 'vue'

const summary = shallowRef(null)
const mediaList = ref([])
const topMedia = ref([])
const persona = shallowRef(null)
const recentMeta = ref({ total: 0, total_pages: 0, page_size: 100 })
const recentPageCache = ref(new Map())
const loading = ref(true)
const error = ref(null)

let loaded = false

async function safeFetch(url) {
  try {
    const resp = await fetch(url)
    if (!resp.ok) return null
    const ct = resp.headers.get('content-type') || ''
    if (!ct.includes('application/json')) return null
    return resp
  } catch {
    return null
  }
}

export function useTraktData() {
  async function loadData() {
    loading.value = true
    error.value = null
    try {
      const [sumResp, mediaResp, topResp, metaResp, personaResp] = await Promise.all([
        safeFetch('data/summary.json'),
        safeFetch('data/media.json'),
        safeFetch('data/top_media.json'),
        safeFetch('data/recent_meta.json'),
        safeFetch('data/persona.json'),
      ])
      if (!sumResp) throw new Error('核心数据文件 (summary.json) 加载失败，请先运行数据抓取')
      summary.value = await sumResp.json()
      mediaList.value = mediaResp ? await mediaResp.json() : []
      topMedia.value = topResp ? await topResp.json() : []
      if (metaResp) recentMeta.value = await metaResp.json()
      if (personaResp) persona.value = await personaResp.json()

      const firstPage = await fetchRecentPage(1)
      recentPageCache.value.set(1, firstPage)

      loaded = true
    } catch (err) {
      error.value = err
      console.error('Failed to load data:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchRecentPage(page) {
    if (recentPageCache.value.has(page)) {
      return recentPageCache.value.get(page)
    }
    const resp = await safeFetch(`data/recent_${page}.json`)
    if (!resp) return []
    try {
      const data = await resp.json()
      recentPageCache.value.set(page, data)
      return data
    } catch {
      return []
    }
  }

  function getRecentPage(page) {
    return recentPageCache.value.get(page) || []
  }

  const mediaMap = computed(() => {
    const m = new Map()
    for (const item of mediaList.value) {
      m.set(item.trakt_id, item)
    }
    return m
  })

  const lastUpdated = computed(() => {
    const stats = summary.value?.monthly_stats || []
    return stats[0]?.updated_at || ''
  })

  const totalStats = computed(() => ({
    total: summary.value?.total_plays || 0,
    hours: Math.floor((summary.value?.total_minutes || 0) / 60),
    movies: summary.value?.total_movies || 0,
    episodes: summary.value?.total_episodes || 0,
  }))

  const monthlyStats = computed(() => summary.value?.monthly_stats || [])
  const dailyGenreStats = computed(() => summary.value?.daily_genre_stats || [])
  const genreStats = computed(() => summary.value?.genre_stats || [])

  if (!loaded) loadData()

  return {
    summary, mediaList, topMedia, persona, recentMeta, loading, error,
    mediaMap, lastUpdated, totalStats,
    monthlyStats, dailyGenreStats, genreStats,
    loadData, fetchRecentPage, getRecentPage,
  }
}
