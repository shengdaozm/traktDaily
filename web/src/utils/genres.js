export const GENRE_COLORS = [
  '#58a6ff', '#f0c040', '#3fb950', '#8b5cf6', '#f97583',
  '#79c0ff', '#d2a8ff', '#56d4dd', '#e3b341', '#db61a2',
  '#7ee787', '#ffa657', '#a5d6ff', '#ff7b72', '#b392f0',
  '#85e89d', '#ffdf5d', '#f78166', '#96d0ff', '#d1bc6f',
  '#c9d1d9',
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
