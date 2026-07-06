"""
打分引擎
--------
输入：用户画像 + 新剧元数据
输出：0-100 分 + 各维度拆解 + 推荐理由

打分因子：
  f_genre      (20%): 类型匹配
  f_keyword    (15%): 关键词/主题（加权 Jaccard）
  f_content    (15%): 与用户高分剧的文本相似度
  f_cf         (10%): 协同过滤（用社区评分作为 proxy）
  f_network    (10%): 出品方匹配
  f_structure  (10%): 叙事结构匹配
  f_quit_pen   (-10%): 弃剧风险减分
  f_trend      (5%):  时间趋势
  f_explore    (5%):  探索加成

用法：
    python -m scripts.scoring_engine --trakt-id 12345
    python -m scripts.scoring_engine --tmdb-id 1399 --type show
"""

import json
import math
import sys
import argparse
from typing import Any

from scripts.db import (
    get_conn,
    init_db,
    load_user_ratings,
    get_rated_shows,
)
from scripts.profile_builder import build_profile


# 各因子权重
WEIGHTS = {
    "f_genre": 0.20,
    "f_keyword": 0.15,
    "f_content": 0.15,
    "f_cf": 0.10,
    "f_network": 0.10,
    "f_structure": 0.10,
    "f_quit_penalty": -0.10,  # 负权重：弃剧风险减分
    "f_trend": 0.05,
    "f_explore": 0.05,
}


def _parse_genres(genre_str: str | None) -> list[str]:
    """解析 genres JSON 字符串。"""
    if not genre_str:
        return []
    try:
        return json.loads(genre_str)
    except (json.JSONDecodeError, TypeError):
        return []


def _get_show_from_db(trakt_id: int | None = None, tmdb_id: int | None = None) -> dict | None:
    """从数据库获取媒体详情。"""
    conn = get_conn()
    row = None
    if trakt_id:
        row = conn.execute("SELECT * FROM media WHERE trakt_id = ?", (trakt_id,)).fetchone()
    elif tmdb_id:
        row = conn.execute("SELECT * FROM media WHERE tmdb_id = ?", (tmdb_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════════
# 各因子计算
# ═══════════════════════════════════════════════════════════


def f_genre(show: dict, profile: dict) -> float:
    """类型匹配分（0-100）。"""
    show_genres = set(_parse_genres(show.get("genres")))
    if not show_genres:
        return 50.0  # 未知类型，给中性分

    genre_vectors = profile.get("genre_profile", {}).get("vectors", {})
    if not genre_vectors:
        return 50.0

    # 计算匹配类型中用户的最高 weighted_score
    matching_scores = []
    for g in show_genres:
        if g in genre_vectors:
            # weighted_score 通常在 0-10 范围，映射到 0-100
            matching_scores.append(min(genre_vectors[g]["weighted_score"] * 10, 100))

    if not matching_scores:
        return 30.0  # 完全没有匹配的类型

    # 取最高分和平均分的加权
    return round(max(matching_scores) * 0.6 + sum(matching_scores) / len(matching_scores) * 0.4, 1)


def f_keyword(show: dict, profile: dict) -> float:
    """关键词/主题匹配分（加权 Jaccard，0-100）。"""
    content = profile.get("content_profile", {})
    high_keywords = set(content.get("keyword_affinity", {}).get("high", []))
    low_keywords = set(content.get("keyword_affinity", {}).get("low", []))

    if not high_keywords and not low_keywords:
        return 50.0

    # 从 show 的 overview/title 提取关键词
    text = (show.get("overview") or "") + " " + (show.get("title") or "")
    words = set(w.lower() for w in text.replace(".", " ").replace(",", " ").split() if len(w) > 2)

    if not words:
        return 50.0

    # Jaccard 相似度（加分词 - 减分词）
    high_overlap = len(words & high_keywords) / max(len(words | high_keywords), 1)
    low_overlap = len(words & low_keywords) / max(len(words | low_keywords), 1)

    score = (high_overlap - low_overlap * 0.5) * 100
    return round(max(0, min(100, score + 50)), 1)  # 居中到 50


def f_content(show: dict, profile: dict, rated_shows: list[dict], media_map: dict) -> float:
    """内容相似度（与用户高分剧的文本重叠，0-100）。"""
    # 获取用户高分剧（rating >= 7）的关键词集合
    show_ids_in_db = {r.get("trakt_id") for r in rated_shows if r.get("user_rating", 0) >= 7}

    if not show_ids_in_db:
        return 50.0

    # 收集高分剧的关键词
    high_rated_words: set[str] = set()
    for sid in show_ids_in_db:
        media = media_map.get(sid)
        if media:
            text = (media.get("overview") or "") + " " + (media.get("title") or "")
            words = {w.lower() for w in text.replace(".", " ").replace(",", " ").split() if len(w) > 2}
            high_rated_words |= words

    if not high_rated_words:
        return 50.0

    # 新剧关键词
    show_text = (show.get("overview") or "") + " " + (show.get("title") or "")
    show_words = {w.lower() for w in show_text.replace(".", " ").replace(",", " ").split() if len(w) > 2}

    if not show_words:
        return 50.0

    # 简单重叠度
    overlap = len(show_words & high_rated_words) / max(len(show_words | high_rated_words), 1)
    return round(max(0, min(100, overlap * 100 + 30)), 1)  # 偏移 30 分


def f_cf(show: dict, profile: dict) -> float:
    """协同过滤代理分（用社区评分作为 proxy，0-100）。"""
    community_rating = show.get("rating")
    community_votes = show.get("votes", 0)

    if not community_rating or community_rating <= 0:
        return 50.0

    # 社区评分映射到 0-100
    cf_score = community_rating * 10  # 假设社区评分 0-10

    # 投票数加权（越多投票越可信）
    vote_weight = min(math.log10(max(community_votes, 1)) / 4.0, 1.0)

    return round(cf_score * (0.5 + 0.5 * vote_weight), 1)


def f_network(show: dict, profile: dict) -> float:
    """出品方匹配分（0-100）。"""
    network = show.get("network")
    if not network:
        return 50.0

    network_profile = profile.get("network_profile", {}).get("vectors", {})
    if not network_profile:
        return 50.0

    if network in network_profile:
        np_data = network_profile[network]
        rating = np_data.get("mean_rating")
        if rating:
            return round(rating * 10, 1)
        return 60.0

    return 40.0  # 新出品方，略低于中性


def f_structure(show: dict, profile: dict) -> float:
    """叙事结构匹配分（0-100）。"""
    struct = profile.get("structure_profile", {})
    if not struct:
        return 50.0

    score = 50.0

    # 时长匹配
    runtime = show.get("runtime")
    if runtime and struct.get("runtime_per_episode", {}).get("mean"):
        pref_runtime = struct["runtime_per_episode"]["mean"]
        diff_ratio = abs(runtime - pref_runtime) / max(pref_runtime, 1)
        score += (1 - diff_ratio) * 20  # ±20 分

    return round(max(0, min(100, score)), 1)


def f_quit_penalty(show: dict, profile: dict) -> float:
    """弃剧风险分（负向因子，0-100，最终用负权重）。"""
    behavioral = profile.get("behavioral_profile", {})
    if not behavioral:
        return 0.0  # 无数据不扣分

    drop_rate = behavioral.get("drop_rate", 0)
    patience = behavioral.get("patience_threshold_episodes", 3)

    # 估算该剧的"弃剧风险"
    runtime = show.get("runtime", 0)
    if runtime > 60:
        risk = min(drop_rate * 100 + 20, 100)
    elif runtime > 45:
        risk = min(drop_rate * 100 + 10, 100)
    else:
        risk = drop_rate * 50

    # 投票数间接估算：热门剧弃剧概率较低
    votes = show.get("votes", 0)
    if votes and votes > 50000:
        risk *= 0.8  # 热门剧弃剧概率较低

    return round(max(0, min(100, risk)), 1)


def f_trend(show: dict, profile: dict) -> float:
    """时间趋势分（新剧/热门加成，0-100）。"""
    temporal = profile.get("temporal_profile", {})
    preferred_eras = temporal.get("preferred_eras", [])

    # 从 first_aired 估算年代
    first_aired = show.get("first_aired", "")
    if not first_aired:
        return 50.0

    try:
        year = int(first_aired[:4])
        decade = f"{(year // 10) * 10}s"
    except (ValueError, IndexError):
        return 50.0

    # 如果该剧的年代在用户偏好年代中，加分
    if decade in preferred_eras:
        era_idx = preferred_eras.index(decade)
        return round(80 - era_idx * 10, 1)

    # 近年的剧给基础分
    from datetime import datetime
    age = datetime.now().year - year
    if age < 2:
        return 60.0
    elif age < 5:
        return 55.0
    return 45.0


def f_explore(show: dict, profile: dict) -> float:
    """探索加成（鼓励跳出舒适区，0-100）。"""
    exploration = profile.get("exploration_profile", {})
    comfort_genres = set(exploration.get("comfort_genres", []))

    if not comfort_genres:
        return 50.0

    show_genres = set(_parse_genres(show.get("genres")))
    if not show_genres:
        return 50.0

    # 如果新剧包含非舒适区类型，给探索加分
    new_genres = show_genres - comfort_genres
    if new_genres:
        return round(60 + len(new_genres) * 10, 1)

    return 40.0  # 在舒适区内，不给额外加分


# ═══════════════════════════════════════════════════════════
# 主打分函数
# ═══════════════════════════════════════════════════════════


def score_show(
    profile: dict,
    show: dict,
    rated_shows: list[dict] | None = None,
    media_map: dict | None = None,
) -> dict:
    """
    对一部剧进行综合打分。
    返回:
        {
            "total_score": 78.5,
            "breakdown": {
                "f_genre": {"score": 85.0, "weight": 0.20, "weighted": 17.0},
                ...
            },
            "reason": ["类型匹配度高", "社区评分优秀"],
        }
    """
    if rated_shows is None:
        rated_shows = get_rated_shows()
    if media_map is None:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM media").fetchall()
        conn.close()
        media_map = {r["trakt_id"]: dict(r) for r in rows}

    # 计算各因子
    scores = {}
    scores["f_genre"] = f_genre(show, profile)
    scores["f_keyword"] = f_keyword(show, profile)
    scores["f_content"] = f_content(show, profile, rated_shows, media_map)
    scores["f_cf"] = f_cf(show, profile)
    scores["f_network"] = f_network(show, profile)
    scores["f_structure"] = f_structure(show, profile)
    scores["f_quit_penalty"] = f_quit_penalty(show, profile)
    scores["f_trend"] = f_trend(show, profile)
    scores["f_explore"] = f_explore(show, profile)

    # 加权求和
    total = 0.0
    breakdown = {}

    for factor, score in scores.items():
        weight = WEIGHTS[factor]
        weighted = score * abs(weight)  # 负权重取绝对值
        if weight < 0:
            weighted = -weighted
        breakdown[factor] = {
            "score": score,
            "weight": weight,
            "weighted": round(weighted, 2),
        }
        total += weighted

    # 归一化到 0-100
    total_score = round(max(0, min(100, total + 50)), 1)  # +50 偏移

    # 生成推荐理由
    reason_parts = []
    sorted_factors = sorted(breakdown.items(), key=lambda x: x[1]["weighted"], reverse=True)
    factor_names = {
        "f_genre": "类型匹配",
        "f_keyword": "关键词契合",
        "f_content": "内容相似",
        "f_cf": "社区口碑",
        "f_network": "出品方偏好",
        "f_structure": "结构匹配",
        "f_quit_penalty": "弃剧风险",
        "f_trend": "时效性",
        "f_explore": "探索价值",
    }

    for factor, data in sorted_factors[:3]:
        if data["weighted"] > 5:
            reason_parts.append(f"{factor_names[factor]}: {data['score']}分")
        elif data["weighted"] < -5:
            reason_parts.append(f"⚠️ {factor_names[factor]}: -{abs(data['score'])}分")

    return {
        "total_score": total_score,
        "show": {
            "trakt_id": show.get("trakt_id"),
            "tmdb_id": show.get("tmdb_id"),
            "title": show.get("title"),
            "year": show.get("year"),
            "poster_url": show.get("poster_url"),
        },
        "breakdown": breakdown,
        "reason": reason_parts,
    }


def batch_score(
    profile: dict,
    show_list: list[dict],
) -> list[dict]:
    """批量打分。"""
    rated_shows = get_rated_shows()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM media").fetchall()
    conn.close()
    media_map = {r["trakt_id"]: dict(r) for r in rows}

    results = []
    for show in show_list:
        result = score_show(profile, show, rated_shows, media_map)
        results.append(result)

    # 按总分降序排列
    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="剧集打分引擎")
    parser.add_argument("--trakt-id", type=int, help="Trakt ID")
    parser.add_argument("--tmdb-id", type=int, help="TMDB ID")
    parser.add_argument("--type", choices=["show", "movie"], default="show", help="媒体类型")
    parser.add_argument("--batch", type=str, help="批量打分：JSON 文件路径")
    parser.add_argument("--force", action="store_true", help="强制重建画像")
    args = parser.parse_args()

    init_db()
    profile = build_profile(force=args.force)

    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as f:
            shows = json.load(f)
        results = batch_score(profile, shows)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        show = _get_show_from_db(args.trakt_id, args.tmdb_id)
        if not show:
            print(f"[Error] 未找到 trakt_id={args.trakt_id} 或 tmdb_id={args.tmdb_id} 的媒体")
            sys.exit(1)

        result = score_show(profile, show)
        print(json.dumps(result, ensure_ascii=False, indent=2))
