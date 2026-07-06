"""
偏差检测与校正引擎
------------------
分析用户评分与演员的关联关系，计算 celebrity_bonus（某演员出现时的评分偏离）。

输出：
  - cast_preference 画像（写入 DB）
  - bias_report JSON（输出到 data/reports/）

核心函数：
  adjust_rating(raw_rating, cast_list) → 校正后的评分

用法：
    python -m scripts.bias_correction             # 计算并缓存
    python -m scripts.bias_correction --force     # 强制重算
    python -m scripts.bias_correction --report    # 输出偏差报告 JSON
"""

import json
import sys
import math
import os
from datetime import datetime
from collections import defaultdict

from scripts.db import (
    get_conn,
    init_db,
    ensure_dirs,
    load_user_ratings,
    get_rated_shows,
    get_media_cast_map,
    upsert_cast_preference,
    get_all_cast_preferences,
)
from scripts.config import REPORTS_DIR


def _get_user_rating_for_show(rated_shows: list[dict], trakt_id: int) -> float | None:
    """查找某 trakt_id 对应的用户评分。"""
    for r in rated_shows:
        if r.get("trakt_id") == trakt_id:
            return r.get("user_rating")
    return None


def compute_cast_preferences(rated_shows: list[dict], cast_map: dict[int, list[dict]]) -> list[dict]:
    """
    计算每个演员的 celebrity_bonus。

    celebrity_bonus = 该演员出现时用户的平均评分 - 用户所有评分的均值
    正值表示用户因为该演员而打更高分，负值则相反。

    参数:
        rated_shows: 用户已评分的剧集列表
        cast_map: {media_trakt_id: [{person_id, person_name, person_role, ...}, ...]}

    返回:
        演员偏好列表（已按 celebrity_bonus 排序）
    """
    # 用户所有评分的全局均值
    all_ratings = [r["user_rating"] for r in rated_shows if r.get("user_rating") is not None]
    if not all_ratings:
        return []

    global_mean = sum(all_ratings) / len(all_ratings)

    # 统计每个演员出现的剧集及其评分
    person_data: dict[int, dict] = {}

    for show in rated_shows:
        trakt_id = show.get("trakt_id")
        user_rating = show.get("user_rating")
        if not trakt_id or not user_rating:
            continue

        # 获取该剧的演员列表
        cast_list = cast_map.get(trakt_id, [])
        if not cast_list:
            continue

        # 获取社区评分（从 rated_shows 的元数据中）
        community_rating = show.get("community_rating")

        for person in cast_list:
            pid = person["person_id"]
            if pid not in person_data:
                person_data[pid] = {
                    "person_id": pid,
                    "person_name": person["person_name"],
                    "roles": set(),
                    "user_ratings": [],
                    "community_ratings": [],
                }

            person_data[pid]["roles"].add(person["person_role"])
            person_data[pid]["user_ratings"].append(user_rating)
            if community_rating:
                person_data[pid]["community_ratings"].append(community_rating)

    # 计算每个演员的指标
    results = []
    for pid, data in person_data.items():
        avg_user = sum(data["user_ratings"]) / len(data["user_ratings"])
        avg_community = (
            sum(data["community_ratings"]) / len(data["community_ratings"])
            if data["community_ratings"]
            else None
        )

        # celebrity_bonus = 用户评分均值 - 全局均值
        celebrity_bonus = round(avg_user - global_mean, 2)

        # affinity_score = 用户评分 vs 社区评分的偏离
        # 正值：用户比社区更喜欢这个演员的剧
        # 负值：用户比社区更不喜欢
        if avg_community:
            user_vs_community = round(avg_user - avg_community, 2)
        else:
            user_vs_community = celebrity_bonus  # 无社区数据时用 global 代替

        # 综合亲和度 = celebrity_bonus 的加权版本（出现次数越多越可信）
        appearances = len(data["user_ratings"])
        confidence = min(appearances / 5.0, 1.0)  # 5 次及以上认为可信
        affinity_score = round(celebrity_bonus * confidence, 2)

        main_role = "actor"
        if "director" in data["roles"]:
            main_role = "director"
        elif "writer" in data["roles"]:
            main_role = "writer"

        results.append({
            "person_id": pid,
            "person_name": data["person_name"],
            "role": main_role,
            "appearances_in_rated": appearances,
            "avg_user_rating": round(avg_user, 1),
            "community_avg": round(avg_community, 1) if avg_community else None,
            "celebrity_bonus": celebrity_bonus,
            "affinity_score": affinity_score,
        })

    # 按 celebrity_bonus 降序排列
    results.sort(key=lambda x: x["celebrity_bonus"], reverse=True)
    return results


def save_cast_preferences(preferences: list[dict]):
    """将演员偏好写入数据库缓存。"""
    for pref in preferences:
        upsert_cast_preference(pref)
    print(f"[Bias] 已缓存 {len(preferences)} 位演员偏好")


def generate_bias_report(preferences: list[dict], rated_shows: list[dict]) -> dict:
    """生成偏差分析报告。"""
    all_ratings = [r["user_rating"] for r in rated_shows if r.get("user_rating") is not None]
    global_mean = sum(all_ratings) / len(all_ratings) if all_ratings else 0

    # 分类演员
    strong_positive = [p for p in preferences if p["celebrity_bonus"] >= 1.0]
    mild_positive = [p for p in preferences if 0 < p["celebrity_bonus"] < 1.0]
    neutral = [p for p in preferences if p["celebrity_bonus"] == 0]
    negative = [p for p in preferences if p["celebrity_bonus"] < 0]

    return {
        "generated_at": datetime.now().isoformat(),
        "global_mean_rating": round(global_mean, 2),
        "total_rated_shows": len(rated_shows),
        "total_analyzed_cast": len(preferences),
        "summary": {
            "strong_positive_count": len(strong_positive),
            "mild_positive_count": len(mild_positive),
            "neutral_count": len(neutral),
            "negative_count": len(negative),
        },
        "top_influencers": [
            {
                "name": p["person_name"],
                "celebrity_bonus": p["celebrity_bonus"],
                "appearances": p["appearances_in_rated"],
                "avg_user_rating": p["avg_user_rating"],
                "community_avg": p["community_avg"],
            }
            for p in preferences[:10]
        ],
        "negative_influencers": [
            {
                "name": p["person_name"],
                "celebrity_bonus": p["celebrity_bonus"],
                "appearances": p["appearances_in_rated"],
            }
            for p in sorted(negative, key=lambda x: x["celebrity_bonus"])[:5]
        ],
        "bias_detected": len(strong_positive) > 0 or len(negative) > 0,
    }


def adjust_rating(raw_rating: float, cast_list: list[dict], preferences: list[dict] | None = None) -> float:
    """
    根据演员阵容校正评分。

    参数:
        raw_rating: 原始评分（0-10）
        cast_list: 演员列表 [{"person_id": 123, "person_name": "..."}, ...]
        preferences: 演员偏好缓存（None 时从 DB 读取）

    返回:
        校正后的评分
    """
    if preferences is None:
        preferences = get_all_cast_preferences()

    if not preferences or not cast_list:
        return raw_rating

    # 查找 cast 中有哪些演员在偏好列表中
    pref_map = {p["person_id"]: p for p in preferences}
    bonuses = []
    for person in cast_list:
        pid = person.get("person_id")
        if pid and pid in pref_map:
            pref = pref_map[pid]
            # 只考虑可信度足够的演员（出现 >= 2 次）
            if pref.get("appearances_in_rated", 0) >= 2:
                bonuses.append(pref["celebrity_bonus"])

    if not bonuses:
        return raw_rating

    # 取平均 celebrity_bonus 作为校正量
    avg_bonus = sum(bonuses) / len(bonuses)

    # 校正后的评分（限制在 1-10 范围）
    adjusted = raw_rating - avg_bonus  # 减去 bonus 得到"去除演员滤镜"的评分
    return round(max(1, min(10, adjusted)), 1)


def run(force: bool = False, report: bool = False):
    """主函数：计算演员偏差。"""
    ensure_dirs()
    init_db()

    rated_shows = get_rated_shows()
    if not rated_shows:
        print("[Bias] 没有已评分的剧集，跳过偏差分析")
        return

    cast_map = get_media_cast_map()
    if not cast_map:
        print("[Bias] 没有演员数据，请先运行 fetch_cast.py")
        return

    print(f"[Bias] 分析 {len(rated_shows)} 部已评分剧集的演员偏差...")

    preferences = compute_cast_preferences(rated_shows, cast_map)
    save_cast_preferences(preferences)

    if report:
        report_data = generate_bias_report(preferences, rated_shows)
        report_path = os.path.join(REPORTS_DIR, "bias_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"[Bias] 偏差报告已输出到 {report_path}")

        # 打印摘要
        print(f"\n[Bias] 摘要：")
        print(f"  全局均分: {report_data['global_mean_rating']}")
        print(f"  强正向影响演员: {report_data['summary']['strong_positive_count']} 位")
        print(f"  负向影响演员: {report_data['summary']['negative_count']} 位")
        if report_data["top_influencers"]:
            print(f"\n  Top 影响力演员:")
            for inf in report_data["top_influencers"][:5]:
                print(f"    {inf['name']}: bonus={inf['celebrity_bonus']:+.1f} "
                      f"(出现 {inf['appearances']} 次, 均分 {inf['avg_user_rating']})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="演员偏差检测与校正")
    parser.add_argument("--force", action="store_true", help="强制重算")
    parser.add_argument("--report", action="store_true", help="输出偏差报告 JSON")
    args = parser.parse_args()

    run(force=args.force, report=args.report)
