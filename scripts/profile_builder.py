"""
用户画像构建引擎
----------------
从 SQLite + user_ratings.json 构建 9 维用户画像。

画像维度：
  1. genre_profile       — 类型偏好（加权评分 × 完成率 × 重刷）
  2. network_profile     — 出品方偏好
  3. structure_profile   — 季数/集数/时长偏好
  4. temporal_profile    — 年代偏好 + 衰减
  5. behavioral_profile  — 完成率、binge、耐心阈值、弃剧模式
  6. content_profile     — 关键词/主题偏好
  7. taste_calibration   — 打分分布、vs 社区相关性
  8. rewatch_profile     — 重刷行为
  9. exploration_profile — 舒适区覆盖率、探索率

用法：
    python -m scripts.profile_builder            # 正常模式（缓存优先）
    python -m scripts.profile_builder --force    # 强制重建
"""

import json
import math
import sys
import hashlib
from collections import defaultdict
from datetime import datetime

from scripts.config import PROFILE_VERSION, PROFILE_REBUILD_THRESHOLD
from scripts.db import (
    get_conn,
    init_db,
    ensure_dirs,
    load_user_ratings,
    get_rated_shows,
    get_media_cast_map,
    save_user_profile,
    get_latest_cached_profile,
    upsert_cast_preference,
)


# ═══════════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════════


def _load_plays() -> list[dict]:
    """加载全部观影记录。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*, m.genres AS media_genres, m.network, m.rating AS community_rating,
               m.votes AS community_votes, m.first_aired, m.overview AS media_overview,
               m.poster_url, m.title AS media_title, m.status
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.media_trakt_id
        ORDER BY p.watched_at
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _load_media_map() -> dict[int, dict]:
    """按 trakt_id 索引媒体元数据。"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM media").fetchall()
    conn.close()
    return {r["trakt_id"]: dict(r) for r in rows}


def _parse_genres(genre_str: str | None) -> list[str]:
    """解析 genres JSON 字符串为列表。"""
    if not genre_str:
        return []
    try:
        return json.loads(genre_str)
    except (json.JSONDecodeError, TypeError):
        return []


def _get_user_rating_for_show(rated_shows: list[dict], media_trakt_id: int) -> float | None:
    """查找某 media_trakt_id 对应的用户评分。"""
    for r in rated_shows:
        if r.get("trakt_id") == media_trakt_id:
            return r.get("user_rating")
    return None


# ═══════════════════════════════════════════════════════════
# 9 维画像计算
# ═══════════════════════════════════════════════════════════


def build_genre_profile(plays: list[dict], media_map: dict, rated_shows: list[dict]) -> dict:
    """
    类型偏好画像。
    对每个 genre，计算：
      score = mean_rating * 0.5 + completion_rate * 10 * 0.3 + rewatch_score * 10 * 0.2
    """
    # 按 show 分组（episode 聚合到 show）
    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    genre_data: dict[str, dict] = {}

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media:
            continue

        genres = _parse_genres(media.get("genres"))
        if not genres:
            continue

        user_rating = _get_user_rating_for_show(rated_shows, show_id)
        rewatch_count = sum(1 for e in episodes if e.get("rewatched", 0) > 0)
        ep_count = len(episodes)

        # 估算该剧总集数（用 media 表的 rating 和 votes 估算知名度）
        # 如果用户评分 > 7 且重刷过，给额外加分
        rewatch_score = min(rewatch_count / 3.0, 1.0)

        # 完成率（简化：假设 10 季以内，每季 10-24 集为正常）
        # 用实际观看集数来近似
        completion_rate = min(ep_count / 24.0, 1.0)  # 简化估算

        for g in genres:
            if g not in genre_data:
                genre_data[g] = {
                    "ratings": [],
                    "completion_rates": [],
                    "rewatch_scores": [],
                    "count": 0,
                    "total_episodes": 0,
                }

            genre_data[g]["count"] += 1
            genre_data[g]["total_episodes"] += ep_count

            if user_rating:
                genre_data[g]["ratings"].append(user_rating)
            genre_data[g]["completion_rates"].append(completion_rate)
            genre_data[g]["rewatch_scores"].append(rewatch_score)

    vectors = {}
    for genre, data in genre_data.items():
        mean_rating = sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else 5.0
        avg_completion = sum(data["completion_rates"]) / len(data["completion_rates"])
        avg_rewatch = sum(data["rewatch_scores"]) / len(data["rewatch_scores"])

        # 加权评分
        weighted_score = round(
            mean_rating * 0.5 + avg_completion * 10 * 0.3 + avg_rewatch * 10 * 0.2,
            2
        )

        vectors[genre] = {
            "mean_rating": round(mean_rating, 1),
            "count": data["count"],
            "completion_rate": round(avg_completion, 2),
            "total_episodes": data["total_episodes"],
            "weighted_score": weighted_score,
        }

    # 按 weighted_score 降序排列
    affinity_rank = sorted(vectors.keys(), key=lambda g: vectors[g]["weighted_score"], reverse=True)

    return {"vectors": vectors, "affinity_rank": affinity_rank}


def build_network_profile(plays: list[dict], media_map: dict, rated_shows: list[dict]) -> dict:
    """出品方偏好画像。"""
    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    network_data: dict[str, dict] = {}

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media or not media.get("network"):
            continue

        network = media["network"]
        user_rating = _get_user_rating_for_show(rated_shows, show_id)

        if network not in network_data:
            network_data[network] = {"ratings": [], "count": 0, "total_episodes": 0}

        network_data[network]["count"] += 1
        network_data[network]["total_episodes"] += len(episodes)
        if user_rating:
            network_data[network]["ratings"].append(user_rating)

    vectors = {}
    for net, data in network_data.items():
        vectors[net] = {
            "mean_rating": round(sum(data["ratings"]) / len(data["ratings"]), 1) if data["ratings"] else None,
            "count": data["count"],
            "total_episodes": data["total_episodes"],
        }

    return {"vectors": vectors}


def build_structure_profile(plays: list[dict], media_map: dict, rated_shows: list[dict]) -> dict:
    """叙事结构偏好：季数、集数、单集时长。"""
    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    seasons_list = []
    episodes_list = []
    runtime_list = []

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media:
            continue

        # 估算季数：按 season 字段去重
        unique_seasons = set()
        for ep in episodes:
            if ep.get("season"):
                unique_seasons.add(ep["season"])

        seasons_list.append(len(unique_seasons))
        episodes_list.append(len(episodes))

        if media.get("runtime"):
            runtime_list.append(media["runtime"])

    def _stats(lst: list[float]) -> dict:
        if not lst:
            return {"mean": 0, "median": 0, "min": 0, "max": 0}
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        return {
            "mean": round(sum(lst) / n, 1),
            "median": sorted_lst[n // 2],
            "min": sorted_lst[0],
            "max": sorted_lst[-1],
        }

    return {
        "seasons": _stats(seasons_list),
        "episodes_per_show": _stats(episodes_list),
        "runtime_per_episode": _stats(runtime_list),
    }


def build_temporal_profile(plays: list[dict], media_map: dict) -> dict:
    """年代偏好画像（带衰减权重：越近权重越高）。"""
    now_year = datetime.now().year
    decade_data: dict[str, dict] = {}

    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media or not media.get("first_aired"):
            continue

        try:
            year = int(media["first_aired"][:4])
        except (ValueError, TypeError, IndexError):
            continue

        decade = f"{(year // 10) * 10}s"
        age = now_year - year
        weight = 1.0 / (1 + age * 0.05)  # 轻微衰减

        if decade not in decade_data:
            decade_data[decade] = {"count": 0, "total_weight": 0.0}

        decade_data[decade]["count"] += 1
        decade_data[decade]["total_weight"] += weight

    for d in decade_data.values():
        d["weighted_count"] = round(d["total_weight"], 1)

    era_rank = sorted(decade_data.keys(), key=lambda d: decade_data[d]["weighted_count"], reverse=True)

    return {
        "decade_distribution": decade_data,
        "preferred_eras": era_rank[:3],
    }


def build_behavioral_profile(plays: list[dict], media_map: dict, rated_shows: list[dict]) -> dict:
    """行为分析画像。"""
    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    # 完成率
    completed = 0
    dropped = 0
    patience_thresholds = []

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media:
            continue

        # 简化：假设 watched 的 season 最大值代表看到哪一季
        max_season = max((ep.get("season", 0) for ep in episodes), default=0)
        max_number = max((ep.get("number", 0) for ep in episodes if ep.get("season") == max_season), default=0)

        # 估算该剧总集数（粗略）
        unique_seasons = set(ep.get("season", 0) for ep in episodes)
        estimated_total = len(unique_seasons) * 12  # 每季约 12 集

        watched_episodes = len(episodes)

        if watched_episodes >= estimated_total * 0.9:
            completed += 1
        elif watched_episodes < 3:
            dropped += 1
            patience_thresholds.append(watched_episodes)

    total_shows = len(show_episodes)
    completion_rate = completed / max(total_shows, 1)
    drop_rate = dropped / max(total_shows, 1)

    # Binge 倾向：统计同一剧连续观看间隔 < 2 小时的次数
    binge_count = 0
    total_pairs = 0
    for show_id, episodes in show_episodes.items():
        sorted_eps = sorted(episodes, key=lambda e: e.get("watched_at", ""))
        for i in range(1, len(sorted_eps)):
            try:
                t1 = datetime.fromisoformat(sorted_eps[i - 1].get("watched_at", ""))
                t2 = datetime.fromisoformat(sorted_eps[i].get("watched_at", ""))
                gap = (t2 - t1).total_seconds() / 3600
                total_pairs += 1
                if gap < 2:
                    binge_count += 1
            except (ValueError, TypeError):
                continue

    binge_tendency = round(binge_count / max(total_pairs, 1), 2)
    avg_patience = round(sum(patience_thresholds) / max(len(patience_thresholds), 1), 1)

    return {
        "completion_rate": round(completion_rate, 2),
        "drop_rate": round(drop_rate, 2),
        "binge_tendency": binge_tendency,
        "patience_threshold_episodes": avg_patience,
        "completed_count": completed,
        "dropped_count": dropped,
    }


def build_content_profile(plays: list[dict], media_map: dict, rated_shows: list[dict]) -> dict:
    """
    内容偏好画像。
    用简单的文本分析方法（关键词重叠）估算主题偏好。
    """
    # 收集高分剧（user_rating >= 7）的 overview 和 title 关键词
    high_rated_texts = []
    low_rated_texts = []

    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    # 常见停用词（中英文）
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "is", "are", "was", "were", "it", "this", "that",
        "the", "一个", "一种", "一部", "之后", "之间", "他的", "她的", "他的",
        "他们", "故事", "系列", "讲述", "开始", "生活", "世界", "时间",
    }

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media:
            continue

        user_rating = _get_user_rating_for_show(rated_shows, show_id)
        if not user_rating:
            continue

        text = (media.get("overview") or "") + " " + (media.get("title") or "")
        # 提取关键词
        words = [w.lower() for w in text.replace(".", " ").replace(",", " ").split() if len(w) > 2]
        words = [w for w in words if w not in stop_words]

        if user_rating >= 7:
            high_rated_texts.extend(words)
        elif user_rating <= 5:
            low_rated_texts.extend(words)

    def _keyword_freq(word_list: list[str]) -> dict[str, int]:
        freq: dict[str, int] = {}
        for w in word_list:
            freq[w] = freq.get(w, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:20])

    # 计算关键词偏好
    high_freq = _keyword_freq(high_rated_texts)
    low_freq = _keyword_freq(low_rated_texts)

    # 偏好关键词 = 高频出现在高分剧但少出现在低分剧的词
    preference = {}
    for word, count in high_freq.items():
        low_count = low_freq.get(word, 0)
        if count > low_count:
            preference[word] = count - low_count

    top_keywords = sorted(preference.keys(), key=lambda w: preference[w], reverse=True)[:10]
    avoid_keywords = [w for w, c in low_freq.items() if w not in high_freq][:5]

    # 简单主题估算（基于 genre 关键词映射）
    theme_keywords = {
        "existential": ["death", "life", "meaning", "exist", "alone", "god", "soul"],
        "moral_ambiguity": ["crime", "moral", "dark", "corrupt", "evil", "justice"],
        "power_struggle": ["power", "king", "throne", "rule", "war", "politics"],
        "survival": ["survive", "danger", "escape", "trap", "hunt"],
        "romance": ["love", "heart", "relationship", "marriage"],
        "comedy": ["funny", "comedy", "laugh", "humor"],
    }

    theme_vectors = {}
    all_words = set(high_rated_texts)
    for theme, keywords in theme_keywords.items():
        matches = sum(1 for k in keywords if k in all_words)
        theme_vectors[theme] = round(matches / max(len(keywords), 1), 2)

    return {
        "keyword_affinity": {
            "high": top_keywords,
            "low": avoid_keywords,
        },
        "theme_vectors": theme_vectors,
        "top_keywords_detail": {k: preference[k] for k in top_keywords},
    }


def build_taste_calibration(plays: list[dict], media_map: dict, rated_shows: list[dict]) -> dict:
    """打分分布 & vs 社区相关性分析。"""
    user_ratings = []
    community_ratings = []

    for show_id, _ in defaultdict(list).items():
        pass  # 占位

    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    for show_id in show_episodes:
        user_rating = _get_user_rating_for_show(rated_shows, show_id)
        media = media_map.get(show_id)
        if not media:
            continue

        community = media.get("rating")
        if user_rating and community and community > 0:
            user_ratings.append(user_rating)
            community_ratings.append(community)

    # 打分分布统计
    rating_dist: dict[int, int] = defaultdict(int)
    for r in user_ratings:
        rating_dist[r] += 1

    # 计算 Pearson 相关系数
    n = len(user_ratings)
    if n >= 3:
        mean_u = sum(user_ratings) / n
        mean_c = sum(community_ratings) / n
        cov = sum((u - mean_u) * (c - mean_c) for u, c in zip(user_ratings, community_ratings))
        std_u = math.sqrt(sum((u - mean_u) ** 2 for u in user_ratings))
        std_c = math.sqrt(sum((c - mean_c) ** 2 for c in community_ratings))
        correlation = round(cov / max(std_u * std_c, 0.001), 2)
    else:
        correlation = 0.0

    # 打分风格判断
    avg_user = sum(user_ratings) / max(n, 1)
    avg_community = sum(community_ratings) / max(n, 1)
    diff = avg_user - avg_community

    if diff > 0.5:
        style = "手松型"
    elif diff < -0.5:
        style = "手紧型"
    else:
        style = "中庸型"

    # 小众品味分：用户高分但社区低分的比例
    niche_count = sum(
        1 for u, c in zip(user_ratings, community_ratings)
        if u >= 8 and c < 7
    )
    niche_score = round(niche_count / max(n, 1), 2)

    return {
        "rating_distribution": dict(rating_dist),
        "mean_user_rating": round(avg_user, 1),
        "mean_community_rating": round(avg_community, 1),
        "vs_community_correlation": correlation,
        "rating_style": style,
        "niche_taste_score": niche_score,
        "total_rated": n,
    }


def build_rewatch_profile(plays: list[dict], media_map: dict) -> dict:
    """重刷行为分析。"""
    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    # 检查重复观看：同一集的 watched_at 是否有多个（plays 表只保留最新，所以需要其他方式判断）
    # 这里用 season 覆盖度来估算：如果覆盖了多个不相邻的季，可能是重刷
    rewatched_shows = []

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media:
            continue

        # 估算：如果同一集出现了多次（通过检查 plays 表中的重复）
        # 由于 plays 表 UNIQUE(trakt_id)，我们检查 episode 编号的分布
        season_numbers = defaultdict(set)
        for ep in episodes:
            if ep.get("season") and ep.get("number"):
                season_numbers[ep["season"]].add(ep["number"])

        # 如果有非连续季，可能是重刷
        seasons = sorted(season_numbers.keys())
        if len(seasons) > 1:
            gaps = [seasons[i + 1] - seasons[i] for i in range(len(seasons) - 1)]
            if any(g > 1 for g in gaps):
                rewatched_shows.append({
                    "trakt_id": show_id,
                    "title": media.get("title", "Unknown"),
                    "seasons_watched": seasons,
                    "has_gaps": True,
                })

    return {
        "rewatched_shows": rewatched_shows,
        "rewatch_count": len(rewatched_shows),
    }


def build_exploration_profile(plays: list[dict], media_map: dict, genre_profile: dict) -> dict:
    """探索率分析：舒适区覆盖率 vs 探索新类型。"""
    # 舒适区 = affinity_rank 前 3 的 genre
    comfort_genres = set(genre_profile.get("affinity_rank", [])[:3])

    show_episodes: dict[int, list[dict]] = defaultdict(list)
    for p in plays:
        if p["media_type"] == "episode" and p.get("media_trakt_id"):
            show_episodes[p["media_trakt_id"]].append(p)

    comfort_count = 0
    exploration_count = 0

    for show_id, episodes in show_episodes.items():
        media = media_map.get(show_id)
        if not media:
            continue

        genres = set(_parse_genres(media.get("genres")))
        if genres & comfort_genres:
            comfort_count += 1
        else:
            exploration_count += 1

    total = comfort_count + exploration_count
    return {
        "comfort_zone_coverage": round(comfort_count / max(total, 1), 2),
        "exploration_rate": round(exploration_count / max(total, 1), 2),
        "comfort_genres": list(comfort_genres),
        "explored_genres_count": exploration_count,
    }


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════


def build_profile(force: bool = False) -> dict:
    """
    构建完整的 9 维用户画像。
    参数:
        force: True 则强制重建，False 则优先使用缓存
    返回:
        完整的画像 dict
    """
    ensure_dirs()
    init_db()

    # 检查缓存
    if not force:
        cached = get_latest_cached_profile()
        if cached:
            rated = load_user_ratings()
            if len(rated["ratings"]) < PROFILE_REBUILD_THRESHOLD:
                print("[Profile] 评分数不足，使用缓存画像")
            else:
                print("[Profile] 使用缓存画像")
                return cached["profile"]

    print("[Profile] 开始构建用户画像...")

    # 加载数据
    plays = _load_plays()
    media_map = _load_media_map()
    rated_shows = get_rated_shows()
    cast_map = get_media_cast_map()

    print(f"[Profile] 数据加载完成: {len(plays)} 条观影记录, {len(media_map)} 个媒体, {len(rated_shows)} 条评分")

    if not plays:
        print("[Profile] 没有观影记录，无法构建画像")
        return {}

    # 计算各维度
    meta = {
        "total_shows_rated": len(rated_shows),
        "total_episodes_watched": sum(1 for p in plays if p["media_type"] == "episode"),
        "rating_mean": round(
            sum(r["user_rating"] for r in rated_shows) / max(len(rated_shows), 1), 1
        ),
        "total_movies_watched": sum(1 for p in plays if p["media_type"] == "movie"),
        "generated_at": datetime.now().isoformat(),
    }

    genre_profile = build_genre_profile(plays, media_map, rated_shows)
    network_profile = build_network_profile(plays, media_map, rated_shows)
    structure_profile = build_structure_profile(plays, media_map, rated_shows)
    temporal_profile = build_temporal_profile(plays, media_map)
    behavioral_profile = build_behavioral_profile(plays, media_map, rated_shows)
    content_profile = build_content_profile(plays, media_map, rated_shows)
    taste_calibration = build_taste_calibration(plays, media_map, rated_shows)
    rewatch_profile = build_rewatch_profile(plays, media_map)
    exploration_profile = build_exploration_profile(plays, media_map, genre_profile)

    profile = {
        "profile_version": PROFILE_VERSION,
        "meta": meta,
        "genre_profile": genre_profile,
        "network_profile": network_profile,
        "structure_profile": structure_profile,
        "temporal_profile": temporal_profile,
        "behavioral_profile": behavioral_profile,
        "content_profile": content_profile,
        "taste_calibration": taste_calibration,
        "rewatch_profile": rewatch_profile,
        "exploration_profile": exploration_profile,
    }

    # 缓存到数据库
    profile_str = json.dumps(profile, ensure_ascii=False)
    content_hash = hashlib.md5(profile_str.encode()).hexdigest()[:8]
    save_user_profile(PROFILE_VERSION, profile_str, content_hash)
    print(f"[Profile] 画像构建完成（hash: {content_hash}）")

    return profile


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="构建用户画像")
    parser.add_argument("--force", action="store_true", help="强制重建（忽略缓存）")
    args = parser.parse_args()

    profile = build_profile(force=args.force)
    if profile:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
