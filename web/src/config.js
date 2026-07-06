// ============================================
// 前端配置 — 按需修改
// ============================================

// TMDB API Key（运行时从 data/tmdb_config.json 加载，无需硬编码）
let tmdbApiKey = ''

/** 从 tmdb_config.json 加载 API Key（构建时由 render.py 注入） */
export async function loadTmdbConfig() {
  try {
    const resp = await fetch('data/tmdb_config.json')
    if (resp.ok) {
      const cfg = await resp.json()
      tmdbApiKey = cfg.api_key || ''
    }
  } catch { /* 静默 */ }
  // 也支持 Vite env 变量覆盖
  if (import.meta.env?.VITE_TMDB_API_KEY) {
    tmdbApiKey = import.meta.env.VITE_TMDB_API_KEY
  }
}

export function getTmdbApiKey() {
  return tmdbApiKey
}

export const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w185'
export const TMDB_IMAGE_HD = 'https://image.tmdb.org/t/p/w780'
export const TMDB_API = 'https://api.themoviedb.org/3'
