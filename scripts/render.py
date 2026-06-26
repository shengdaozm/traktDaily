"""
前端 JSON 数据生成器
--------------------
读取 data/trakt.db，生成 web/public/data/ 目录下的 JSON 文件供前端消费。

输出文件：
  summary.json       → 总览统计（月度趋势、类型分布、热力图数据）
  media.json         → 媒体库（每个剧/电影的详情）
  top_media.json     → 观影排行预聚合（Top 50，含海报）
  recent_meta.json   → 最近观影分页元信息（总数、总页数）
  recent_1.json ~ recent_N.json → 最近观影分页（每页 100 条）
"""

import json
import os
import glob
from scripts.config import WEB_DATA_DIR
from scripts.db import (
    get_plays_count,
    get_monthly_stats,
    get_genre_stats,
    get_all_media,
    get_daily_genre_stats,
    get_all_plays,
    get_top_media,
    ensure_dirs,
)

PAGE_SIZE = 100


def _write_json(filename, data):
    """写入 JSON 文件。"""
    path = os.path.join(WEB_DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _cleanup_old_pages():
    """清理旧的 recent_*.json 分页文件（防止页数减少后残留旧文件）。"""
    pattern = os.path.join(WEB_DATA_DIR, "recent_*.json")
    for f in glob.glob(pattern):
        os.remove(f)


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

    _write_json("summary.json", summary)
    print(f"[Render] 已生成 summary.json（{summary['total_plays']} 条记录）")

    # ── 媒体库数据 ──
    all_media = get_all_media(500)
    _write_json("media.json", all_media)
    print(f"[Render] 已生成 media.json（{len(all_media)} 个媒体）")

    # ── 观影排行预聚合 ──
    top_media = get_top_media(50)
    _write_json("top_media.json", top_media)
    print(f"[Render] 已生成 top_media.json（{len(top_media)} 个媒体）")

    # ── 最近观影记录（分页） ──
    all_plays = get_all_plays()
    total_plays = len(all_plays)
    total_pages = max(1, (total_plays + PAGE_SIZE - 1) // PAGE_SIZE)

    _cleanup_old_pages()

    for page in range(1, total_pages + 1):
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_data = all_plays[start:end]
        _write_json(f"recent_{page}.json", page_data)

    _write_json("recent_meta.json", {
        "total": total_plays,
        "total_pages": total_pages,
        "page_size": PAGE_SIZE,
    })
    print(f"[Render] 已生成 recent 分页（{total_plays} 条，{total_pages} 页，每页 {PAGE_SIZE} 条）")


if __name__ == "__main__":
    run()
