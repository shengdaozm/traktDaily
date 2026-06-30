export const GENRE_COLORS = [
  '#a8c5a0', '#d4a857', '#6b8caf', '#9a8aaf', '#d4a5a5',
  '#7a9a72', '#c4dcbc', '#6a9a92', '#c4924a', '#c4a0a8',
  '#8ab07e', '#b89a5a', '#5a7a9a', '#a87a8a', '#7a8a9a',
  '#9ab088', '#d4b85a', '#a87854', '#6a8ab0', '#a0a07a',
  '#c4c9ce',
]

export const GENRE_ZH = {
  action: '动作', adventure: '冒险', animation: '动画', anime: '动漫',
  comedy: '喜剧', crime: '犯罪', documentary: '纪录片', donghua: '国漫',
  drama: '剧情', family: '家庭', fantasy: '奇幻', history: '历史',
  horror: '恐怖', mystery: '悬疑', romance: '爱情', 'science-fiction': '科幻',
  soap: '肥皂剧', superhero: '超级英雄', suspense: '惊悚', thriller: '惊悚',
  war: '战争',
}

export function translateGenre(genre) {
  return GENRE_ZH[genre] || genre
}

export function traktUrl(item, mediaMap) {
  if (!item) return '#'
  const mid = item.media_trakt_id || item.trakt_id
  const media = mediaMap?.get(mid)
  if (media?.slug) {
    const type = media.media_type === 'movie' ? 'movies' : 'shows'
    return `https://trakt.tv/${type}/${media.slug}`
  }
  if (item.slug) {
    const type = item.media_type === 'movie' ? 'movies' : 'shows'
    return `https://trakt.tv/${type}/${item.slug}`
  }
  return '#'
}

export function cleanShowTitle(title) {
  if (!title) return 'Unknown'
  const idx = title.lastIndexOf(' S')
  if (idx > 0 && /^\d{2}E\d{2}$/.test(title.substring(idx + 2))) {
    return title.substring(0, idx)
  }
  return title
}
