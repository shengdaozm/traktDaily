"""
画像 & 推荐 JSON 生成器
----------------------
调用 profile_builder 生成画像 → 输出 profile.json
调用 bias_correction 生成偏差报告 → 输出 bias_report.json
输出 cast_preferences.json
可选：对热门新剧批量打分 → 输出 recommendations.json

所有输出写入 web/public/data/ 目录。

用法：
    python -m scripts.render_profile              # 生成全部 JSON
    python -m scripts.render_profile --force      # 强制重建画像
    python -m scripts.render_profile --no-rec     # 不生成推荐
"""

import json
import os
import sys
import argparse
from datetime import datetime

from scripts.config import WEB_DATA_DIR, REPORTS_DIR
from scripts.db import (
    init_db,
    ensure_dirs,
    get_all_cast_preferences,
    load_user_ratings,
    get_conn,
    get_rated_shows,
)
from scripts.profile_builder import build_profile
from scripts.bias_correction import compute_cast_preferences, generate_bias_report, get_media_cast_map
from scripts.scoring_engine import batch_score


def _write_json(filename: str, data: dict):
    """写入 JSON 到 web/public/data/ 目录。"""
    path = os.path.join(WEB_DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_trending_shows(limit: int = 20) -> list[dict]:
    """
    从数据库获取近期添加的剧集（作为推荐候选池）。
    实际生产环境可从 Trakt/TMDB API 拉取热门新剧。
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM media
        WHERE media_type IN ('show', 'movie')
          AND rating IS NOT NULL
          AND rating > 0
        ORDER BY updated_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_media_map() -> dict[int, dict]:
    """获取所有媒体的映射表。"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM media").fetchall()
    conn.close()
    return {r["trakt_id"]: dict(r) for r in rows}


def run(force: bool = False, with_recommendations: bool = True, rec_limit: int = 20):
    """
    生成画像相关的全部 JSON 文件。
    参数:
        force: 是否强制重建画像
        with_recommendations: 是否生成推荐列表
        rec_limit: 推荐数量上限
    """
    ensure_dirs()
    init_db()

    print("[RenderProfile] 开始生成画像 JSON...")

    # ── 1. 用户画像 ──
    profile = build_profile(force=force)
    if not profile:
        print("[RenderProfile] 画像为空，跳过")
        return

    _write_json("profile.json", profile)
    print(f"[RenderProfile] 已生成 profile.json（v{profile.get('profile_version', '?')}）")

    # ── 2. 演员偏好 ──
    rated_shows = get_rated_shows()
    cast_map = get_media_cast_map()

    if rated_shows and cast_map:
        print("[RenderProfile] 计算演员偏好...")
        preferences = compute_cast_preferences(rated_shows, cast_map)

        # 输出 cast_preferences.json
        cast_pref_output = {
            "generated_at": datetime.now().isoformat(),
            "total_analyzed": len(preferences),
            "preferences": [
                {
                    "person_id": p["person_id"],
                    "person_name": p["person_name"],
                    "role": p["role"],
                    "appearances_in_rated": p["appearances_in_rated"],
                    "avg_user_rating": p["avg_user_rating"],
                    "community_avg": p["community_avg"],
                    "celebrity_bonus": p["celebrity_bonus"],
                    "affinity_score": p["affinity_score"],
                }
                for p in preferences
            ],
        }
        _write_json("cast_preferences.json", cast_pref_output)
        print(f"[RenderProfile] 已生成 cast_preferences.json（{len(preferences)} 位演员）")

        # ── 3. 偏差报告 ──
        bias_report = generate_bias_report(preferences, rated_shows)
        _write_json("bias_report.json", bias_report)
        print(f"[RenderProfile] 已生成 bias_report.json")
    else:
        print("[RenderProfile] 缺少评分或演员数据，跳过偏差分析")

    # ── 4. 推荐列表 ──
    if with_recommendations:
        print("[RenderProfile] 生成推荐列表...")
        media_map = _get_media_map()

        # 获取推荐候选池
        candidates = _get_trending_shows(limit=rec_limit * 3)  # 多取一些以便筛选

        # 排除用户已经看过的剧
        watched_ids = set()
        for play in rated_shows:
            watched_ids.add(play.get("trakt_id"))
        # 也从 plays 表获取看过的
        conn = get_conn()
        rows = conn.execute("SELECT DISTINCT media_trakt_id FROM plays WHERE media_trakt_id IS NOT NULL").fetchall()
        conn.close()
        for r in rows:
            watched_ids.add(r["media_trakt_id"])

        # 过滤未看过的剧
        unseen = [c for c in candidates if c.get("trakt_id") not in watched_ids]

        if unseen:
            recommendations = batch_score(profile, unseen)
            # 取 Top N
            top_recs = recommendations[:rec_limit]

            rec_output = {
                "generated_at": datetime.now().isoformat(),
                "profile_version": profile.get("profile_version", "unknown"),
                "total_candidates": len(unseen),
                "recommendations": top_recs,
            }
            _write_json("recommendations.json", rec_output)
            print(f"[RenderProfile] 已生成 recommendations.json（{len(top_recs)} 部推荐）")

            # 打印 Top 5
            print("\n[RenderProfile] Top 5 推荐:")
            for i, rec in enumerate(top_recs[:5], 1):
                title = rec.get("show", {}).get("title", "Unknown")
                score = rec.get("total_score", 0)
                reasons = ", ".join(rec.get("reason", [])[:2])
                print(f"  {i}. {title} — {score}分 ({reasons})")
        else:
            print("[RenderProfile] 没有未看过的候选剧，跳过推荐")

    print("[RenderProfile] 全部完成")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成画像 & 推荐 JSON")
    parser.add_argument("--force", action="store_true", help="强制重建画像")
    parser.add_argument("--no-rec", action="store_true", help="不生成推荐")
    parser.add_argument("--limit", type=int, default=20, help="推荐数量上限")
    args = parser.parse_args()

    run(force=args.force, with_recommendations=not args.no_rec, rec_limit=args.limit)
