import { ref, shallowRef, computed } from 'vue'

const summary = shallowRef(null)
const mediaList = ref([])
const recentPlays = ref([])
const loading = ref(true)
const error = ref(null)

let loaded = false

export function useTraktData() {
  async function loadData() {
    loading.value = true
    error.value = null
    try {
      const [sumResp, mediaResp, recentResp] = await Promise.all([
        fetch('data/summary.json'),
        fetch('data/media.json').catch(() => null),
        fetch('data/recent.json').catch(() => null),
      ])
      summary.value = await sumResp.json()
      mediaList.value = mediaResp ? await mediaResp.json() : []
      recentPlays.value = recentResp ? await recentResp.json() : []
      loaded = true
    } catch (err) {
      error.value = err
      console.error('Failed to load data:', err)
    } finally {
      loading.value = false
    }
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
    summary, mediaList, recentPlays, loading, error,
    mediaMap, lastUpdated, totalStats,
    monthlyStats, dailyGenreStats, genreStats,
    loadData,
  }
}
