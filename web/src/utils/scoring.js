/**
 * 轻量前端打分引擎
 * 输入：用户画像 JSON + TMDB 剧集元数据
 * 输出：0-100 分 + 各维度拆解 + 推荐理由
 */
export function computeScore(profile, tmdbShow) {
  if (!profile || !tmdbShow) return null

  const gp = profile.genre_profile || {}
  const np = profile.network_profile || {}
  const sp = profile.structure_profile || {}
  const cp = profile.content_profile || {}
  const tp = profile.temporal_profile || {}
  const bp = profile.behavioral_profile || {}
  const ep = profile.exploration_profile || {}

  const showGenres = (tmdbShow.genre_ids || []).map(id => genreIdToName(id))
  const showNetwork = tmdbShow.origin_country?.[0] || ''
  const showEpisodes = tmdbShow.number_of_episodes || 1
  const showSeasons = tmdbShow.number_of_seasons || 1
  const showRuntime = tmdbShow.episode_run_time?.[0] || 45
  const showYear = tmdbShow.first_air_date ? parseInt(tmdbShow.first_air_date) : null
  const showKeywords = tmdbShow.keywords || []
  const showOverview = tmdbShow.overview || ''

  const scores = {}

  // 1. 类型匹配 (20%)
  scores.genre = computeGenreMatch(showGenres, gp)

  // 2. 关键词/主题匹配 (15%)
  scores.keyword = computeKeywordMatch(showKeywords, showOverview, cp)

  // 3. 出品方/地区匹配 (10%)
  scores.network = computeNetworkMatch(showNetwork, np)

  // 4. 叙事结构匹配 (10%)
  scores.structure = computeStructureMatch(showSeasons, showEpisodes, showRuntime, sp)

  // 5. 内容相似度 (15%) — 简化版：基于类型+地区的 overlap
  scores.content = computeContentSimilarity(showGenres, showNetwork, profile)

  // 6. 弃剧风险 (10%) — 负面扣分
  scores.quitRisk = computeQuitRisk(showGenres, bp)

  // 7. 时间趋势 (5%)
  scores.trend = computeTrend(showYear, tp)

  // 8. 探索加成 (5%)
  scores.explore = computeExplore(showGenres, ep)

  // 权重
  const weights = {
    genre: 0.20, keyword: 0.15, network: 0.10,
    structure: 0.10, content: 0.15, quitRisk: 0.10,
    trend: 0.05, explore: 0.05
  }

  // 加权求和（弃剧风险是负向）
  const rawScore =
    scores.genre * weights.genre +
    scores.keyword * weights.keyword +
    scores.network * weights.network +
    scores.structure * weights.structure +
    scores.content * weights.content +
    (1 - scores.quitRisk) * weights.quitRisk +
    scores.trend * weights.trend +
    scores.explore * weights.explore

  const finalScore = Math.round(Math.max(0, Math.min(100, rawScore * 100)))

  return {
    score: finalScore,
    breakdown: {
      '类型匹配': Math.round(scores.genre * 100),
      '关键词/主题': Math.round(scores.keyword * 100),
      '出品方/地区': Math.round(scores.network * 100),
      '叙事结构': Math.round(scores.structure * 100),
      '内容相似度': Math.round(scores.content * 100),
      '弃剧风险': Math.round(scores.quitRisk * 100),
      '时间趋势': Math.round(scores.trend * 100),
      '探索加成': Math.round(scores.explore * 100),
    },
    weights,
    reasons: generateReasons(tmdbShow, scores, profile),
    confidence: getConfidence(profile),
  }
}

function computeGenreMatch(showGenres, genreProfile) {
  const vectors = genreProfile.vectors || {}
  if (!showGenres.length || !Object.keys(vectors).length) return 0.5

  let totalAffinity = 0
  let count = 0
  for (const g of showGenres) {
    const v = vectors[g]
    if (v) {
      const score = ((v.recency_weighted || v.mean_rating || 5) / 10 * 0.5) +
                    ((v.completion_rate || 0.5) * 0.3) +
                    ((v.rewatch_count || 0) > 0 ? 0.2 : 0)
      totalAffinity += Math.min(score, 1)
    } else {
      totalAffinity += 0.4
    }
    count++
  }
  return totalAffinity / count
}

function computeKeywordMatch(keywords, overview, contentProfile) {
  const keywordAffinity = contentProfile.keyword_affinity || {}
  const high = keywordAffinity.high || []
  const medium = keywordAffinity.medium || []
  const low = keywordAffinity.low || []

  if (!keywords.length && !overview) return 0.5

  let score = 0
  let count = 0

  for (const kw of keywords) {
    const kwLower = kw.toLowerCase()
    if (high.some(h => kwLower.includes(h.toLowerCase()))) {
      score += 1.0
    } else if (medium.some(m => kwLower.includes(m.toLowerCase()))) {
      score += 0.6
    } else if (low.some(l => kwLower.includes(l.toLowerCase()))) {
      score += 0.2
    } else {
      score += 0.5
    }
    count++
  }

  if (overview) {
    const allKeywords = [...high, ...medium, ...low]
    const overviewLower = overview.toLowerCase()
    let matchCount = 0
    for (const kw of allKeywords) {
      if (overviewLower.includes(kw.toLowerCase())) matchCount++
    }
    const overviewScore = allKeywords.length > 0 ? matchCount / Math.min(allKeywords.length, 5) : 0.5
    score += overviewScore
    count++
  }

  return count > 0 ? Math.min(score / count, 1) : 0.5
}

function computeNetworkMatch(showNetwork, networkProfile) {
  const vectors = networkProfile.vectors || {}
  if (!Object.keys(vectors).length) return 0.5

  if (showNetwork && vectors[showNetwork]) {
    const v = vectors[showNetwork]
    return (v.mean_rating || 5) / 10 * 0.6 + (v.avg_completion || 0.5) * 0.4
  }

  const avgRating = Object.values(vectors).reduce((s, v) => s + (v.mean_rating || 5), 0) / Object.keys(vectors).length
  return avgRating / 10
}

function computeStructureMatch(seasons, episodes, runtime, structureProfile) {
  const seasonPref = structureProfile.season_preference || {}
  const epsPref = structureProfile.episodes_per_season || {}
  const runtimePref = structureProfile.episode_length || {}

  let seasonScore = 0.5
  if (seasons === 1 && seasonPref.miniseries_1 !== undefined) seasonScore = seasonPref.miniseries_1
  else if (seasons <= 3 && seasonPref.short_2to3 !== undefined) seasonScore = seasonPref.short_2to3
  else if (seasons <= 6 && seasonPref.medium_4to6 !== undefined) seasonScore = seasonPref.medium_4to6
  else if (seasonPref.long_7plus !== undefined) seasonScore = seasonPref.long_7plus

  const avgEps = episodes / Math.max(seasons, 1)
  let epsScore = 0.5
  if (avgEps <= 8 && epsPref.tight_6to8 !== undefined) epsScore = epsPref.tight_6to8
  else if (avgEps <= 12 && epsPref.standard_10 !== undefined) epsScore = epsPref.standard_10
  else if (epsPref.full_13to22 !== undefined) epsScore = epsPref.full_13to22

  let runtimeScore = 0.5
  if (runtime <= 35 && runtimePref.short_30min !== undefined) runtimeScore = runtimePref.short_30min
  else if (runtime <= 50 && runtimePref.standard_45 !== undefined) runtimeScore = runtimePref.standard_45
  else if (runtime <= 65 && runtimePref.long_60min !== undefined) runtimeScore = runtimePref.long_60min
  else if (runtimePref.movie_75plus !== undefined) runtimeScore = runtimePref.movie_75plus

  return seasonScore * 0.35 + epsScore * 0.35 + runtimeScore * 0.30
}

function computeContentSimilarity(showGenres, showNetwork, profile) {
  const gp = profile.genre_profile || {}
  const np = profile.network_profile || {}
  const genreVectors = gp.vectors || {}

  let genreSim = 0
  let genreCount = 0
  for (const g of showGenres) {
    if (genreVectors[g] && (genreVectors[g].mean_rating || 0) >= 7) {
      genreSim += 1
    } else if (genreVectors[g]) {
      genreSim += 0.5
    } else {
      genreSim += 0.3
    }
    genreCount++
  }
  genreSim = genreCount > 0 ? genreSim / genreCount : 0.5

  let networkSim = 0.5
  if (showNetwork && np.vectors?.[showNetwork]) {
    networkSim = (np.vectors[showNetwork].mean_rating || 5) / 10
  }

  return genreSim * 0.7 + networkSim * 0.3
}

function computeQuitRisk(showGenres, behavioralProfile) {
  const completionByGenre = behavioralProfile.completion_rate_by_genre || {}
  if (!showGenres.length) return 0.3

  let risk = 0
  for (const g of showGenres) {
    const cr = completionByGenre[g]
    if (cr !== undefined) {
      risk += (1 - cr)
    } else {
      risk += 0.4
    }
  }
  return Math.min(risk / showGenres.length, 1)
}

function computeTrend(showYear, temporalProfile) {
  const eraPref = temporalProfile.era_preference || {}
  if (!showYear || !Object.keys(eraPref).length) return 0.5

  let era = ''
  if (showYear < 2000) era = 'classic_pre2000'
  else if (showYear < 2010) era = 'golden_2000s'
  else if (showYear < 2020) era = 'modern_2010s'
  else era = 'current_2020s'

  return eraPref[era] !== undefined ? eraPref[era] : 0.5
}

function computeExplore(showGenres, explorationProfile) {
  const comfortZone = explorationProfile.comfort_zone_coverage || {}
  const primaryGenres = comfortZone.primary_genres || []

  const isOutside = showGenres.some(g => !primaryGenres.includes(g))
  if (!isOutside) return 0

  return (explorationProfile.exploration_success_rate || 0.3) * 0.5
}

function generateReasons(tmdbShow, scores, profile) {
  const reasons = []

  if (scores.genre >= 0.7) {
    const matchGenres = (tmdbShow.genre_ids || []).map(id => genreIdToName(id)).join('、')
    reasons.push({ type: 'positive', text: `${matchGenres}类型 — 你的强项` })
  }

  if (scores.keyword >= 0.7) {
    reasons.push({ type: 'positive', text: '主题关键词高度匹配你的偏好' })
  }

  if (scores.structure >= 0.7) {
    reasons.push({ type: 'positive', text: `${tmdbShow.number_of_seasons || '?'}季 — 正是你偏好的结构` })
  }

  if (scores.quitRisk >= 0.5) {
    const genres = (tmdbShow.genre_ids || []).map(id => genreIdToName(id)).join('、')
    reasons.push({ type: 'negative', text: `${genres}类型的完成率偏低，有弃剧风险` })
  }

  if (scores.trend < 0.4) {
    reasons.push({ type: 'neutral', text: '年代偏好略有偏差，但不影响观看体验' })
  }

  if (reasons.length === 0) {
    reasons.push({ type: 'neutral', text: '综合评估：各方面匹配度中等' })
  }

  return reasons
}

function getConfidence(profile) {
  const ratedCount = profile.meta?.total_shows_rated || 0
  if (ratedCount >= 100) return 'high'
  if (ratedCount >= 30) return 'medium'
  return 'low'
}

/** TMDB genre ID → 名称映射 */
function genreIdToName(id) {
  const map = {
    10759: '动作冒险', 16: '动画', 35: '喜剧', 80: '犯罪',
    99: '纪录', 18: '剧情', 10751: '家庭', 10762: '儿童',
    9648: '悬疑', 10763: '新闻', 10764: '真人秀', 10765: '科幻奇幻',
    10766: '肥皂', 10767: '脱口秀', 10768: '战争', 37: '西部',
    28: '动作', 12: '冒险', 14: '奇幻', 36: '历史',
    27: '恐怖', 53: '惊悚', 10752: '战争', 878: '科幻',
  }
  return map[id] || `类型${id}`
}
