"""
Trakt 数据抓取主入口
--------------------
每 2 小时由 GitHub Actions 定时触发，执行以下流程：
1. 初始化数据库表结构
2. 获取数据库中最新观影时间，作为增量抓取的起点
3. 分页拉取 Trakt /history 接口，只获取晚于该时间的新记录
4. 去重写入 SQLite（plays 表，含完整元数据）
5. 对新增的媒体，将 Trakt 返回的完整详情写入 media 表
6. 从 TMDB 补充海报/背景图 URL
7. 刷新月度统计表
8. 输出新增记录数，供 Actions 判断是否需要 commit
"""

import json
import sys
import requests
from pyrate_limiter import Duration, Limiter, RequestRate
from requests_ratelimiter import LimiterAdapter

from scripts.config import (
    TRAKT_CLIENT_ID,
    TRAKT_USERNAME,
    TRAKT_BASE_URL,
    TRAKT_PAGE_LIMIT,
)
from scripts.db import (
    init_db,
    insert_play,
    upsert_media,
    get_latest_watched_at,
    get_plays_count,
    refresh_monthly_stats,
    ensure_dirs,
)
from scripts.tmdb import get_tmdb_images

# ── 请求频率控制 ──
# Trakt API 限制为每分钟约 1000 次（非 OAuth 更低），这里设为每秒 2 次
_trakt_limiter = Limiter(RequestRate(2, Duration.SECOND))
_trakt_adapter = LimiterAdapter(limiter=_trakt_limiter)

_session = requests.Session()
_session.mount("https://", _trakt_adapter)
_session.mount("http://", _trakt_adapter)


def _trakt_request(endpoint: str, params: dict | None = None) -> dict:
    """
    通用 Trakt API 请求，自动附加认证头和 API 版本。
    参数:
        endpoint: API 路径，如 '/users/xxx/history'
        params: 查询参数
    返回:
        API 响应的 JSON 字典
    """
    if params is None:
        params = {}

    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
    }

    url = f"{TRAKT_BASE_URL}{endpoint}"
    resp = _session.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_history() -> list[dict]:
    """
    分页拉取 Trakt 全部观影历史。
    Trakt 按 watched_at 倒序返回，最新数据在第一页。
    返回:
        所有历史记录的列表，每条包含完整的 movie/show/episode 元数据
    """
    page = 1
    all_history = []

    while True:
        params = {
            "page": page,
            "limit": TRAKT_PAGE_LIMIT,
        }

        data = _trakt_request(f"/users/{TRAKT_USERNAME}/history", params)

        if not data:
            break

        all_history.extend(data)
        print(f"  [Trakt] 已拉取第 {page} 页，共 {len(data)} 条，累计 {len(all_history)} 条")

        if len(data) < TRAKT_PAGE_LIMIT:
            break

        page += 1

    return all_history


def _extract_play_info(entry: dict) -> dict | None:
    """
    从 Trakt history 条目中提取完整的观影记录字段。
    从 Trakt API 返回的 movie/show/episode 中提取所有可用元数据。
    参数:
        entry: 单条 Trakt history 条目
    返回:
        包含所有 plays 表字段的字典，或 None（解析失败）
    """
    watched_at = entry.get("watched_at", "")
    entry_type = entry.get("type", "")

    if entry_type == "movie":
        m = entry.get("movie", {})
        ids = m.get("ids", {})
        genres = m.get("genres", [])
        return {
            "trakt_id": ids.get("trakt", 0),
            "tmdb_id": ids.get("tmdb"),
            "imdb_id": ids.get("imdb"),
            "title": m.get("title", "Unknown"),
            "year": m.get("year"),
            "media_type": "movie",
            "runtime": m.get("runtime"),
            "genres": json.dumps(genres, ensure_ascii=False) if genres else None,
            "overview": m.get("overview"),
            "rating": m.get("rating"),
            "votes": m.get("votes"),
            "watched_at": watched_at,
        }

    elif entry_type == "episode":
        show = entry.get("show", {})
        episode = entry.get("episode", {})
        show_ids = show.get("ids", {})
        ep_ids = episode.get("ids", {})
        season = episode.get("season", 0)
        number = episode.get("number", 0)
        genres = show.get("genres", [])
        return {
            "trakt_id": ep_ids.get("trakt", 0),
            "tmdb_id": ep_ids.get("tmdb") or show_ids.get("tmdb"),
            "imdb_id": ep_ids.get("imdb") or show_ids.get("imdb"),
            "title": f"{show.get('title', 'Unknown')} S{season:02d}E{number:02d}",
            "year": show.get("year"),
            "media_type": "episode",
            "runtime": episode.get("runtime"),
            "genres": json.dumps(genres, ensure_ascii=False) if genres else None,
            "overview": episode.get("overview") or show.get("overview"),
            "rating": episode.get("rating") or show.get("rating"),
            "votes": episode.get("votes") or show.get("votes"),
            "watched_at": watched_at,
        }

    return None


def _extract_media_info(entry: dict) -> dict | None:
    """
    从 Trakt history 条目中提取完整的媒体元数据（media 表）。
    从 Trakt API 返回的数据中提取所有可用的详情字段。
    参数:
        entry: 单条 Trakt history 条目
    返回:
        包含所有 media 表字段的字典，或 None
    """
    entry_type = entry.get("type", "")

    if entry_type == "movie":
        m = entry.get("movie", {})
        ids = m.get("ids", {})
        genre_list = m.get("genres", [])
        return {
            "trakt_id": ids.get("trakt", 0),
            "tmdb_id": ids.get("tmdb"),
            "imdb_id": ids.get("imdb"),
            "title": m.get("title", "Unknown"),
            "year": m.get("year"),
            "media_type": "movie",
            "slug": ids.get("slug"),
            "tagline": m.get("tagline"),
            "overview": m.get("overview"),
            "genres": json.dumps(genre_list, ensure_ascii=False) if genre_list else None,
            "runtime": m.get("runtime"),
            "rating": m.get("rating"),
            "votes": m.get("votes"),
            "certification": m.get("certification"),
            "country": m.get("country"),
            "language": m.get("language"),
            "network": None,
            "status": m.get("status"),
            "trailer_url": m.get("trailer"),
            "homepage": m.get("homepage"),
            "first_aired": m.get("released"),
            "comment_count": m.get("comment_count"),
            # poster_url 和 backdrop_url 由 TMDB 补充
            "poster_url": None,
            "backdrop_url": None,
        }

    elif entry_type == "episode":
        show = entry.get("show", {})
        episode = entry.get("episode", {})
        show_ids = show.get("ids", {})
        genre_list = show.get("genres", [])
        # 剧集以 show 的 trakt_id 为主键，多个 episode 共享同一个 show 的元数据
        return {
            "trakt_id": show_ids.get("trakt", 0),
            "tmdb_id": show_ids.get("tmdb"),
            "imdb_id": show_ids.get("imdb"),
            "title": show.get("title", "Unknown"),
            "year": show.get("year"),
            "media_type": "show",
            "slug": show_ids.get("slug"),
            "tagline": None,
            "overview": show.get("overview"),
            "genres": json.dumps(genre_list, ensure_ascii=False) if genre_list else None,
            "runtime": show.get("runtime") or episode.get("runtime"),
            "rating": show.get("rating"),
            "votes": show.get("votes"),
            "certification": show.get("certification"),
            "country": show.get("country"),
            "language": show.get("language"),
            "network": show.get("network"),
            "status": show.get("status"),
            "trailer_url": show.get("trailer"),
            "homepage": show.get("homepage"),
            "first_aired": show.get("first_aired"),
            "comment_count": show.get("comment_count"),
            "poster_url": None,
            "backdrop_url": None,
        }

    return None


def _clean_title(title: str, media_type: str) -> str:
    """去掉剧集标题中的 SxxExx 后缀，提取纯 show 名称。"""
    if media_type in ("episode", "show"):
        parts = title.rsplit(" S", 1)
        if len(parts) == 2 and parts[1][:2].isdigit():
            return parts[0]
    return title


def run():
    """主函数：执行完整的数据抓取流程。"""
    ensure_dirs()

    print("[DB] 初始化数据库...")
    init_db()

    latest = get_latest_watched_at()
    if latest:
        print(f"[DB] 最新观影记录时间: {latest}")
    else:
        print("[DB] 数据库为空，将拉取全部历史记录")

    print(f"[Trakt] 开始拉取用户 {TRAKT_USERNAME} 的观影历史...")
    history = fetch_history()

    if not history:
        print("[Trakt] 没有观影记录，退出")
        return

    # 按 watched_at 升序排列（最早的在前面），确保写入顺序正确
    history.sort(key=lambda x: x.get("watched_at", ""))

    new_count = 0
    skip_count = 0
    processed_media = set()  # 记录已处理过的媒体 trakt_id，避免重复写入

    for entry in history:
        play = _extract_play_info(entry)
        if not play:
            continue

        # 增量模式：跳过不晚于最新记录的数据
        if latest and play["watched_at"] <= latest:
            skip_count += 1
            continue

        # 写入观影记录（自动去重）
        inserted = insert_play(play)
        if inserted:
            new_count += 1
            # 将 Trakt 返回的完整媒体详情写入 media 表（每个媒体只写一次）
            media_trakt_id = play["trakt_id"]
            # 对于剧集，media 表以 show 的 trakt_id 为主键
            if entry.get("type") == "episode":
                media_trakt_id = entry.get("show", {}).get("ids", {}).get("trakt", 0)

            if media_trakt_id not in processed_media:
                media_info = _extract_media_info(entry)
                if media_info:
                    # 从 TMDB 补充海报和背景图
                    clean_title = _clean_title(media_info["title"], media_info["media_type"])
                    tmdb_images = get_tmdb_images(
                        tmdb_id=media_info.get("tmdb_id"),
                        title=clean_title,
                        media_type=media_info["media_type"],
                        year=media_info.get("year"),
                    )
                    if tmdb_images:
                        media_info["poster_url"] = tmdb_images.get("poster_url")
                        media_info["backdrop_url"] = tmdb_images.get("backdrop_url")

                    upsert_media(media_info)
                    processed_media.add(media_trakt_id)
        else:
            skip_count += 1

    print(f"[DB] 新增 {new_count} 条记录，跳过 {skip_count} 条（已存在或早于增量起点）")

    if new_count > 0:
        print("[DB] 刷新月度统计...")
        refresh_monthly_stats()

    total = get_plays_count()
    print(f"[DB] 数据库总记录数: {total}")

    return new_count


if __name__ == "__main__":
    new = run()
    sys.exit(0)