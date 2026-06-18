"""
前端 JSON 数据生成器
--------------------
读取 data/trakt.db，生成 web/data/ 目录下的 JSON 文件供前端消费。
输出包含完整的媒体元数据（海报、标签、评分、简介等）。
"""

import json
from scripts.config import WEB_DATA_DIR
from scripts.db import (
    get_plays_count,
    get_monthly_stats,
    get_genre_stats,
    get_all_media,
    get_daily_genre_stats,
    ensure_dirs,
)


def run():
    """生成前端所需的全部 JSON 数据文件。"""
    ensure_dirs()

    # ── 总览数据 ──
    monthly_stats = get_monthly_stats()
    total_minutes = sum(m.get("total_minutes", 0) for m in monthly_stats)
    total_movies = sum(m.get("movie_count", 0) for m in monthly_stats)
    total_episodes = sum(m.get("episode_count", 0) for m in monthly_stats)

    summary = {
        "total_plays": get_plays_count(),
        "total_minutes": total_minutes,
        "total_movies": total_movies,
        "total_episodes": total_episodes,
        "monthly_stats": monthly_stats,
        "genre_stats": get_genre_stats(),
        "daily_genre_stats": get_daily_genre_stats(),
    }

    with open(f"{WEB_DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[Render] 已生成 summary.json（{summary['total_plays']} 条记录）")

    # ── 媒体库数据 ──
    # 包含所有媒体详情（海报、标签、评分、简介等）供前端展示
    all_media = get_all_media(500)
    with open(f"{WEB_DATA_DIR}/media.json", "w", encoding="utf-8") as f:
        json.dump(all_media, f, ensure_ascii=False, indent=2)
    print(f"[Render] 已生成 media.json（{len(all_media)} 个媒体）")


if __name__ == "__main__":
    run()