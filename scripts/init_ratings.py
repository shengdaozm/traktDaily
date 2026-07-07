"""
用户评分模板生成器
-----------------
从数据库读取已看过的剧集/电影，通过 TMDB 获取中文标题，
生成 data/user_ratings.json，评分为 null 待用户填写。
如果已有评分文件，会保留用户已填写的评分。

用法：
    python -m scripts.init_ratings              # 默认最多 200 条
    python -m scripts.init_ratings --limit 100  # 限制数量
"""

import json
import os
import argparse
import sys
from datetime import datetime

from scripts.config import USER_RATINGS_PATH, PROJECT_ROOT
from scripts.db import get_conn, ensure_dirs
from scripts.tmdb import get_chinese_title


def _load_existing_ratings() -> dict:
    """加载已有的评分文件，返回 {trakt_id: entry} 映射。"""
    if not os.path.exists(USER_RATINGS_PATH):
        return {}
    try:
        with open(USER_RATINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {r["trakt_id"]: r for r in data.get("ratings", []) if r.get("trakt_id")}
    except Exception:
        return {}


def _preload_from_db(limit: int = 200, existing: dict = None) -> list[dict]:
    """从 plays/media 表预填充已看过的剧集和电影，通过 TMDB 获取中文名。
    如果已有评分文件，保留用户已填写的评分。"""
    conn = get_conn()

    # 获取所有看过的 show（按 media_trakt_id 去重）
    show_rows = conn.execute("""
        SELECT DISTINCT p.media_trakt_id AS trakt_id,
               m.tmdb_id AS tmdb_id,
               CASE WHEN p.media_type = 'episode'
                    THEN SUBSTR(p.title, 1, INSTR(p.title, ' S') - 1)
                    ELSE p.title
               END AS title,
               m.rating AS community_rating,
               COUNT(*) AS play_count,
               MAX(p.watched_at) AS last_watched
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.media_trakt_id
        WHERE p.media_type = 'episode'
          AND p.media_trakt_id IS NOT NULL
        GROUP BY p.media_trakt_id
        ORDER BY last_watched DESC
    """).fetchall()

    # 获取所有看过的 movie
    movie_rows = conn.execute("""
        SELECT DISTINCT p.trakt_id,
               p.tmdb_id,
               p.title,
               m.rating AS community_rating,
               COUNT(*) AS play_count,
               MAX(p.watched_at) AS last_watched
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.trakt_id
        WHERE p.media_type = 'movie'
          AND p.trakt_id IS NOT NULL
        GROUP BY p.trakt_id
        ORDER BY last_watched DESC
    """).fetchall()

    conn.close()

    if existing is None:
        existing = {}

    entries = []

    def _make_entry(trakt_id, tmdb_id, title, media_type, community_rating, play_count):
        # 如果已有评分记录，保留用户填写的评分
        old = existing.get(trakt_id)
        if old and old.get("user_rating") is not None:
            # 保留用户评分，但更新标题为中文名
            chinese_title = old.get("title")  # 已有标题可能是上次获取的中文
            return {
                "trakt_id": trakt_id,
                "title": chinese_title or title,
                "original_title": old.get("original_title"),
                "media_type": "show" if media_type == "episode" else "movie",
                "user_rating": old.get("user_rating"),
                "completed": old.get("completed"),
                "rewatched": old.get("rewatched", max(0, play_count - 1)),
                "notes": old.get("notes", "")
            }

        # 尝试从 TMDB 获取中文名
        chinese_title = None
        if tmdb_id:
            try:
                chinese_title = get_chinese_title(
                    tmdb_id=tmdb_id,
                    title=title,
                    media_type=media_type,
                )
            except Exception as e:
                print(f"  [TMDB] 获取中文名失败 ({title}): {e}")

        display_title = chinese_title or title
        return {
            "trakt_id": trakt_id,
            "title": display_title,
            "original_title": title if chinese_title else None,
            "media_type": "show" if media_type == "episode" else "movie",
            "user_rating": None,
            "completed": None,
            "rewatched": max(0, play_count - 1),
            "notes": ""
        }

    # 先填充剧集
    for r in show_rows[:limit]:
        entries.append(_make_entry(
            r["trakt_id"], r["tmdb_id"], r["title"],
            "episode", r["community_rating"], r["play_count"]
        ))
        if len(entries) >= limit:
            break

    # 再填充电影
    remaining = limit - len(entries)
    if remaining > 0:
        for r in movie_rows[:remaining]:
            entries.append(_make_entry(
                r["trakt_id"], r["tmdb_id"], r["title"],
                "movie", r["community_rating"], r["play_count"]
            ))

    return entries


def run(limit: int = 200):
    """生成用户评分 JSON 文件，预填充已看过的剧集/电影（中文名）。"""
    ensure_dirs()

    # 加载已有评分，保留用户已填写的部分
    existing = _load_existing_ratings()
    if existing:
        print(f"[Ratings] 已有评分文件，{len(existing)} 条记录（将保留已填写的评分）")

    print(f"[Ratings] 从数据库预填充已看过的剧集/电影（最多 {limit} 条）...")
    ratings = _preload_from_db(limit, existing)
    filled = sum(1 for r in ratings if r["trakt_id"] is not None)
    rated = sum(1 for r in ratings if r.get("user_rating") is not None)
    print(f"[Ratings] 预填充 {filled} 条记录，其中 {rated} 条已有评分")

    data = {
        "version": "2.0",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "max_entries": limit,
        "ratings": ratings,
    }

    with open(USER_RATINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[Ratings] 已生成 {USER_RATINGS_PATH}")
    print(f"[Ratings] 请编辑该文件，填入你的评分（user_rating: 1-10）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成用户评分 JSON（预填充已看过内容 + 中文名）")
    parser.add_argument("--limit", type=int, default=200, help="最大条目数（默认 200）")
    args = parser.parse_args()
    run(limit=args.limit)
