"""
用户评分模板生成器
-----------------
生成 data/user_ratings.json 模板文件，预填充已知剧集（评分为 null）。
用户手动编辑 JSON 填写评分后，画像系统即可读取使用。

用法：
    python -m scripts.init_ratings              # 生成空模板
    python -m scripts.init_ratings --fill       # 基于 media 表预填充已知剧集
    python -m scripts.init_ratings --limit 50   # 预填充数量限制
"""

import json
import os
import argparse
import sys
from datetime import datetime

from scripts.config import USER_RATINGS_PATH, PROJECT_ROOT
from scripts.db import get_conn, ensure_dirs


def _generate_empty_template(max_entries: int = 100) -> dict:
    """生成空模板，包含指定数量的空位。"""
    return {
        "version": "1.0",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "max_entries": max_entries,
        "ratings": [
            {
                "trakt_id": None,
                "title": "",
                "media_type": "show",
                "user_rating": None,
                "completed": False,
                "rewatched": 0,
                "notes": ""
            }
            for _ in range(max_entries)
        ]
    }


def _preload_from_db(limit: int = 100) -> list[dict]:
    """从 media 表预填充已知剧集（评分为 null，待用户填写）。"""
    conn = get_conn()

    # 获取所有看过的 show（按 trakt_id 去重）
    show_rows = conn.execute("""
        SELECT DISTINCT p.media_trakt_id AS trakt_id,
               CASE WHEN p.media_type = 'episode'
                    THEN SUBSTR(p.title, 1, INSTR(p.title, ' S') - 1)
                    ELSE p.title
               END AS title,
               m.rating AS community_rating
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.media_trakt_id
        WHERE p.media_type = 'episode'
          AND p.media_trakt_id IS NOT NULL
        ORDER BY p.media_trakt_id
    """).fetchall()

    # 获取所有看过的 movie
    movie_rows = conn.execute("""
        SELECT DISTINCT trakt_id, title, rating AS community_rating
        FROM plays
        WHERE media_type = 'movie' AND trakt_id IS NOT NULL
        ORDER BY trakt_id
    """).fetchall()

    conn.close()

    entries = []

    for r in show_rows[:limit]:
        entries.append({
            "trakt_id": r["trakt_id"],
            "title": r["title"] or "Unknown",
            "media_type": "show",
            "user_rating": None,
            "completed": None,
            "rewatched": 0,
            "notes": ""
        })

    remaining = limit - len(entries)
    if remaining > 0:
        for r in movie_rows[:remaining]:
            entries.append({
                "trakt_id": r["trakt_id"],
                "title": r["title"] or "Unknown",
                "media_type": "movie",
                "user_rating": None,
                "completed": None,
                "rewatched": 0,
                "notes": ""
            })

    # 填充剩余空位
    total = len(entries)
    if total < limit:
        for _ in range(limit - total):
            entries.append({
                "trakt_id": None,
                "title": "",
                "media_type": "show",
                "user_rating": None,
                "completed": False,
                "rewatched": 0,
                "notes": ""
            })

    return entries


def run(fill: bool = False, limit: int = 100):
    """生成用户评分 JSON 模板。"""
    ensure_dirs()

    if fill:
        print(f"[Ratings] 从数据库预填充 {limit} 条已知剧集/电影...")
        ratings = _preload_from_db(limit)
        filled = sum(1 for r in ratings if r["trakt_id"] is not None)
        print(f"[Ratings] 预填充 {filled} 条已知记录")
    else:
        ratings = [
            {
                "trakt_id": None,
                "title": "",
                "media_type": "show",
                "user_rating": None,
                "completed": False,
                "rewatched": 0,
                "notes": ""
            }
            for _ in range(limit)
        ]
        print(f"[Ratings] 生成 {limit} 个空位模板")

    data = {
        "version": "1.0",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "max_entries": limit,
        "ratings": ratings,
    }

    with open(USER_RATINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[Ratings] 已生成 {USER_RATINGS_PATH}")
    print(f"[Ratings] 请编辑该文件，填入你的评分（user_rating: 1-10）")
    print(f"[Ratings] 提示：将看过的剧的 trakt_id 填上，user_rating 打分，completed 标是否看完")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成用户评分 JSON 模板")
    parser.add_argument("--fill", action="store_true", help="基于 media 表预填充已知剧集")
    parser.add_argument("--limit", type=int, default=100, help="最大条目数（默认 100）")
    args = parser.parse_args()
    run(fill=args.fill, limit=args.limit)
