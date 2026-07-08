// ============================================
// 前端配置 — 按需修改
// ============================================

// TMDB API Key（Vite 构建时通过 VITE_TMDB_API_KEY 注入）
const tmdbApiKey = import.meta.env?.VITE_TMDB_API_KEY || ''

/** 兼容旧调用，无需异步加载 */
export async function loadTmdbConfig() {}

export function getTmdbApiKey() {
  return tmdbApiKey
}

export const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w185'
export const TMDB_IMAGE_HD = 'https://image.tmdb.org/t/p/w780'
export const TMDB_API = 'https://api.themoviedb.org/3'
