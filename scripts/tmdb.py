"""
TMDB API 封装
------------
仅用于补充 Trakt 不提供的海报和背景图 URL。
Trakt 已返回完整的元数据（genres, overview, rating 等），TMDB 只负责图片。
"""

import requests
from pyrate_limiter import Duration, Limiter, RequestRate
from requests_ratelimiter import LimiterAdapter

from scripts.config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE, TMDB_LANG

# ── 请求频率控制 ──
# TMDB API 限制为每秒约 50 次，这里设为每秒 4 次留足安全边界
_tmdb_limiter = Limiter(RequestRate(4, Duration.SECOND))
_tmdb_adapter = LimiterAdapter(limiter=_tmdb_limiter)

_session = requests.Session()
_session.mount("https://", _tmdb_adapter)
_session.mount("http://", _tmdb_adapter)


def _api_request(endpoint: str, params: dict | None = None) -> dict:
    """
    通用 TMDB API 请求，自动附加 API Key 和语言参数。
    参数:
        endpoint: API 路径，如 '/movie/603'
        params: 额外的查询参数
    返回:
        API 响应的 JSON 字典
    """
    if params is None:
        params = {}
    params.setdefault("api_key", TMDB_API_KEY)
    params.setdefault("language", TMDB_LANG)

    url = f"{TMDB_BASE_URL}{endpoint}"
    resp = _session.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get_poster_url(poster_path: str | None, size: str = "w500") -> str | None:
    """
    拼接 TMDB 图片 CDN 完整 URL。
    参数:
        poster_path: TMDB 返回的路径，如 '/abc123.jpg'
        size: 图片尺寸，可选 'w92', 'w185', 'w342', 'w500', 'w780', 'original'
    返回:
        完整的 CDN URL，或 None（如果 poster_path 为空）
    """
    if not poster_path:
        return None
    base = TMDB_IMAGE_BASE.replace("w500", size)
    return f"{base}{poster_path}"


def get_tmdb_images(
    tmdb_id: int | None = None,
    title: str = "",
    media_type: str = "movie",
    year: int | None = None,
) -> dict | None:
    """
    获取媒体的海报和背景图 URL。
    优先使用 tmdb_id 直接查询，没有则按标题搜索。
    参数:
        tmdb_id: TMDB 媒体 ID（Trakt 返回的 ids.tmdb）
        title: 媒体标题（用于搜索）
        media_type: 'movie' 或 'show'/'episode'
        year: 发行年份（可选，用于精确搜索）
    返回:
        {'poster_url': str, 'backdrop_url': str} 或 None
    """
    if not TMDB_API_KEY:
        return None

    data = None

    # 优先用 TMDB ID 直接查询
    if tmdb_id:
        try:
            if media_type in ("movie",):
                endpoint = f"/movie/{tmdb_id}"
            else:
                endpoint = f"/tv/{tmdb_id}"
            data = _api_request(endpoint)
        except requests.HTTPError:
            pass  # TMDB ID 无效，回退到搜索

    # 没有 TMDB ID 或 ID 查询失败，按标题搜索
    if not data and title:
        search_type = "tv" if media_type in ("episode", "show") else "movie"
        search_query = f"{title} {year}" if year else title
        try:
            result = _api_request(f"/search/{search_type}", {"query": search_query, "page": 1})
            results = result.get("results", [])
            if results:
                data = results[0]
        except requests.HTTPError:
            return None

    if not data:
        return None

    return {
        "poster_url": _get_poster_url(data.get("poster_path")),
        "backdrop_url": _get_poster_url(data.get("backdrop_path"), "original"),
    }