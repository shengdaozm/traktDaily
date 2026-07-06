"""
前端 JSON 数据生成器
--------------------
读取 data/trakt.db，生成 web/public/data/ 目录下的 JSON 文件供前端消费。

输出文件：
  summary.json         → 总览统计（月度趋势、类型分布、热力图数据）
  media.json           → 媒体库（每个剧/电影的详情）
  top_media.json       → 观影排行预聚合（Top 50，含海报）
  recent_meta.json     → 最近观影月度索引（总数、各月条数）
  recent_YYYY-MM.json  → 按月分文件的观影记录（仅当前月会更新）
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
    get_hourly_stats,
    get_weekday_stats,
    get_binge_stats,
    get_rating_preference,
    get_country_stats,
    get_freshness_stats,
    get_watch_pattern,
    get_diversity_index,
    get_runtime_preference,
    get_monthly_posters,
    ensure_dirs,
)


def _write_json(filename, data):
    """写入 JSON 文件。"""
    path = os.path.join(WEB_DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _cleanup_old_recent_files():
    """清理旧的 recent_*.json 文件（包括数字分页和月份格式）。"""
    pattern = os.path.join(WEB_DATA_DIR, "recent_*.json")
    for f in glob.glob(pattern):
        if not f.endswith("recent_meta.json"):
            os.remove(f)


def run():
    """生成前端所需的全部 JSON 数据文件。"""
    ensure_dirs()

    # ── 总览数据 ──
    monthly_stats = get_monthly_stats()
    total_minutes = sum(m.get("total_minutes", 0) for m in monthly_stats)
    total_movies = sum(m.get("movie_count", 0) for m in monthly_stats)
    total_episodes = sum(m.get("episode_count", 0) for m in monthly_stats)

    # ── 行为分析数据 ──
    hourly_stats = get_hourly_stats()
    weekday_stats = get_weekday_stats()
    binge_stats = get_binge_stats()
    rating_pref = get_rating_preference()
    country_stats = get_country_stats()
    freshness_stats = get_freshness_stats()
    watch_pattern = get_watch_pattern()
    diversity = get_diversity_index()
    runtime_pref = get_runtime_preference()

    # 首末观影记录
    all_plays_for_range = get_all_plays()
    first_watched = all_plays_for_range[-1] if all_plays_for_range else None
    last_watched = all_plays_for_range[0] if all_plays_for_range else None

    summary = {
        "total_plays": get_plays_count(),
        "total_minutes": total_minutes,
        "total_movies": total_movies,
        "total_episodes": total_episodes,
        "monthly_stats": monthly_stats,
        "genre_stats": get_genre_stats(),
        "daily_genre_stats": get_daily_genre_stats(),
        # 行为分析
        "hourly_stats": hourly_stats,
        "weekday_stats": weekday_stats,
        "binge_stats": binge_stats,
        "rating_preference": rating_pref,
        "country_stats": country_stats,
        "freshness_stats": freshness_stats,
        "watch_pattern": watch_pattern,
        "diversity_index": diversity,
        "runtime_preference": runtime_pref,
        # 首末观影
        "first_watched": {
            "title": first_watched["title"] if first_watched else "",
            "watched_at": first_watched["watched_at"] if first_watched else "",
            "poster_url": first_watched.get("poster_url") if first_watched else None,
            "media_type": first_watched["media_type"] if first_watched else "",
        } if first_watched else None,
        "last_watched": {
            "title": last_watched["title"] if last_watched else "",
            "watched_at": last_watched["watched_at"] if last_watched else "",
            "poster_url": last_watched.get("poster_url") if last_watched else None,
            "media_type": last_watched["media_type"] if last_watched else "",
        } if last_watched else None,
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

    # ── 最近观影记录（按月分文件） ──
    all_plays = get_all_plays()

    months_map = {}
    for play in all_plays:
        ym = (play.get("watched_at_local") or "")[:7]
        if ym:
            months_map.setdefault(ym, []).append(play)

    sorted_months = sorted(months_map.keys(), reverse=True)

    _cleanup_old_recent_files()

    month_info = []
    for ym in sorted_months:
        plays = months_map[ym]
        _write_json(f"recent_{ym}.json", plays)
        month_info.append({"month": ym, "count": len(plays)})

    _write_json("recent_meta.json", {
        "total": len(all_plays),
        "months": month_info,
    })
    print(f"[Render] 已生成 recent 月度文件（{len(all_plays)} 条，{len(sorted_months)} 个月）")

    # ── 月度海报数据 ──
    monthly_posters = get_monthly_posters()
    _write_json("monthly_posters.json", monthly_posters)
    print(f"[Render] 已生成 monthly_posters.json（{len(monthly_posters)} 个月）")

    # ── TMDB API 配置（前端搜索打分用） ──
    tmdb_key = os.environ.get('TMDB_API_KEY', '')
    if tmdb_key:
        _write_json("tmdb_config.json", {"api_key": tmdb_key})
        print("[Render] 已生成 tmdb_config.json")

    # ── 画像 & 推荐数据 ──
    try:
        from scripts.render_profile import run as render_profile_run
        render_profile_run()
    except Exception as e:
        print(f"[Render] 画像生成跳过（{e}）")


if __name__ == "__main__":
    run()
