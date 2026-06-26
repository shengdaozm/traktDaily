"""
观影人格画像分析
---------------
收集观影行为数据，调用大模型（DeepSeek）生成人格画像。
API 不可用时降级为规则引擎生成基础版。

输出: web/public/data/persona.json
"""

import json
import os
import math
from datetime import datetime

from scripts.config import (
    WEB_DATA_DIR, LLM_API_KEY, LLM_API_BASE, LLM_MODEL, PERSONA_CACHE_DAYS,
)
from scripts.db import (
    get_hourly_stats, get_weekday_stats, get_binge_stats,
    get_rating_preference, get_country_stats, get_freshness_stats,
    get_watch_pattern, get_diversity_index, get_runtime_preference,
    get_monthly_stats, get_plays_count,
)


def _persona_path():
    return os.path.join(WEB_DATA_DIR, "persona.json")


def _is_cache_valid():
    path = _persona_path()
    if not os.path.exists(path):
        return False
    mtime = os.path.getmtime(path)
    age_days = (datetime.now().timestamp() - mtime) / 86400
    return age_days < PERSONA_CACHE_DAYS


# ═══════════════════════════════════════════════════════════
# 数据收集
# ═══════════════════════════════════════════════════════════

def collect_data():
    hourly = get_hourly_stats()
    weekday = get_weekday_stats()
    binge = get_binge_stats()
    rating = get_rating_preference()
    country = get_country_stats()
    freshness = get_freshness_stats()
    pattern = get_watch_pattern()
    diversity = get_diversity_index()
    runtime = get_runtime_preference()
    monthly = get_monthly_stats()
    total = get_plays_count()

    night_count = sum(h["count"] for h in hourly if h["hour"] and h["hour"] >= 22 or h["hour"] == 0)
    night_count = sum(h["count"] for h in hourly if h["hour"] is not None and (h["hour"] >= 22 or h["hour"] < 2))
    total_hourly = sum(h["count"] for h in hourly if h["hour"] is not None)
    night_ratio = night_count / max(total_hourly, 1)

    weekend_count = sum(w["count"] for w in weekday if str(w["weekday"]) in ("0", "6"))
    total_weekday = sum(w["count"] for w in weekday)
    weekend_ratio = weekend_count / max(total_weekday, 1)

    non_en_cn = sum(c["count"] for c in country if c["country"] not in ("us", "cn", "gb", ""))
    total_country = sum(c["count"] for c in country)
    global_ratio = non_en_cn / max(total_country, 1)

    return {
        "total_plays": total,
        "hourly": hourly,
        "weekday": weekday,
        "binge": binge,
        "rating": rating,
        "country": country,
        "freshness": freshness,
        "pattern": pattern,
        "diversity": diversity,
        "runtime": runtime,
        "monthly": monthly,
        "night_ratio": round(night_ratio, 3),
        "weekend_ratio": round(weekend_ratio, 3),
        "global_ratio": round(global_ratio, 3),
    }


# ═══════════════════════════════════════════════════════════
# 规则标签引擎
# ═══════════════════════════════════════════════════════════

def generate_tags(data):
    tags = []

    if data["night_ratio"] > 0.4:
        tags.append({"icon": "🌙", "name": "深夜追剧人", "desc": "夜深了，你的故事才刚开始", "strength": min(data["night_ratio"] / 0.6, 1.0)})
    if data["rating"]["avg_rating"] > 7.5:
        tags.append({"icon": "🎯", "name": "精品猎人", "desc": "你的时间只留给好故事", "strength": min(data["rating"]["avg_rating"] / 9, 1.0)})
    if data["diversity"]["diversity_score"] > 70:
        tags.append({"icon": "📚", "name": "杂食观众", "desc": "什么类型都看，什么故事都体验", "strength": data["diversity"]["diversity_score"] / 100})
    if data["binge"]["binge_ratio"] > 0.4:
        tags.append({"icon": "🔥", "name": "一口气追完党", "desc": "开了头就停不下来", "strength": min(data["binge"]["binge_ratio"] / 0.7, 1.0)})
    if data["global_ratio"] > 0.3:
        tags.append({"icon": "🌍", "name": "国际化口味", "desc": "你的视界没有国界", "strength": min(data["global_ratio"] / 0.5, 1.0)})
    if data["weekend_ratio"] > 0.45:
        tags.append({"icon": "📅", "name": "周末型", "desc": "工作日攒着，周末一次性释放", "strength": min(data["weekend_ratio"] / 0.6, 1.0)})
    if data["pattern"]["pattern_type"] == "pulse":
        tags.append({"icon": "⚡", "name": "脉冲型", "desc": "追剧像发洪水，来一波停一波", "strength": 1.0 - data["pattern"]["stability"] / 100})
    if data["freshness"]["freshness_score"] > 70:
        tags.append({"icon": "🆕", "name": "追新一族", "desc": "永远在追最新最热的剧", "strength": data["freshness"]["freshness_score"] / 100})
    if data["runtime"]["movie_ratio"] < 0.1:
        tags.append({"icon": "📺", "name": "剧集至上", "desc": "长线叙事才是你的菜", "strength": 1.0 - data["runtime"]["movie_ratio"]})

    return sorted(tags, key=lambda t: t["strength"], reverse=True)[:5]


# ═══════════════════════════════════════════════════════════
# 雷达图评分
# ═══════════════════════════════════════════════════════════

def calc_radar(data):
    return {
        "immersion": min(int(data["binge"]["binge_ratio"] * 120), 100),
        "quality": data["rating"]["quality_score"],
        "diversity": data["diversity"]["diversity_score"],
        "depth": min(int((1 - data["runtime"]["movie_ratio"]) * 100), 100),
        "night_owl": min(int(data["night_ratio"] * 130), 100),
        "freshness": data["freshness"]["freshness_score"],
        "global": min(int(data["global_ratio"] * 150), 100),
        "binge": min(int(data["binge"]["binge_ratio"] * 120), 100),
    }


# ═══════════════════════════════════════════════════════════
# 规则引擎降级版
# ═══════════════════════════════════════════════════════════

def generate_rule_based(data):
    tags = generate_tags(data)
    radar = calc_radar(data)
    top_tag = tags[0] if tags else {"icon": "🎬", "name": "观影爱好者", "desc": "你热爱故事"}

    top_genres = data["diversity"].get("top_genres", [])
    genre_text = "、".join(g["genre"] for g in top_genres[:2]) if top_genres else "各种类型"

    narrative = (
        f"这一年你一共看了 {data['total_plays']} 部作品。"
        f"你是{top_tag['icon']} {top_tag['name']}——{top_tag['desc']}。"
        f"你偏好 {genre_text} 的组合，"
        f"平均评分 {data['rating']['avg_rating']}，"
        f"binge 指数 {data['binge']['binge_ratio']}。"
    )

    highlights = [f"{t['icon']} {t['name']}：{t['desc']}" for t in tags[:4]]

    return {
        "archetype": top_tag["name"],
        "archetype_description": top_tag["desc"],
        "tags": [{"icon": t["icon"], "name": t["name"], "desc": t["desc"]} for t in tags],
        "radar": radar,
        "narrative": narrative,
        "highlights": highlights,
        "personality_traits": {
            "openness": f"{'高' if data['diversity']['diversity_score'] > 60 else '中'} — 你{'愿意尝试不同类型的作品' if data['diversity']['diversity_score'] > 60 else '有明确的类型偏好'}",
            "conscientiousness": f"{'高' if data['pattern']['stability'] > 60 else '中'} — 你的观影节奏{'稳定' if data['pattern']['stability'] > 60 else '有波动'}",
            "extraversion": "低 — 观影是你独处时的仪式",
            "agreeableness": f"{'高' if data['rating']['avg_rating'] > 7 else '中'} — 你倾向于给作品{'更高' if data['rating']['avg_rating'] > 7 else '客观'}的评价",
            "neuroticism": f"{'中' if data['pattern']['pattern_type'] != 'stable' else '低'} — 你的观影频率{'有波动' if data['pattern']['pattern_type'] != 'stable' else '很稳定'}",
        },
        "source": "rule_engine",
        "generated_at": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════
# 大模型调用
# ═══════════════════════════════════════════════════════════

def build_prompt(data):
    top_genres = data["diversity"].get("top_genres", [])
    top_countries = data["country"][:5]
    hourly_dist = {h["hour"]: h["count"] for h in data["hourly"] if h["hour"] is not None}

    prompt = f"""你是一位专业的观影行为分析师。请基于以下用户的观影统计数据，生成一份有温度、有洞察力的人格画像分析。

要求：
1. archetype: 用一个富有诗意的词定义用户的"观影原型"（4-8字，如"深夜故事旅人"）
2. archetype_description: 一句话描述这个原型
3. tags: 3-5个人格标签，每个包含 icon(emoji)、name(2-6字)、desc(一句话描述)
4. radar: 8个维度评分(0-100整数)，维度为 immersion(沉浸度)、quality(精品度)、diversity(广度)、depth(深度)、night_owl(夜猫)、freshness(新鲜度)、global(国际化)、binge(连贯追剧)
5. narrative: 100-200字的人格叙事文案，像朋友在跟你聊天，有洞察力，发现数据中的有趣模式
6. highlights: 3-5个观影高光时刻（简短一句话）
7. personality_traits: 基于大五人格模型(openness/conscientiousness/extraversion/agreeableness/neuroticism)，每项给出"高/中/低 — 简短解释"

语气要求：温暖、有洞察力、不机械。可以大胆推测但要有数据支撑。用中文。

请严格返回JSON格式，不要包含markdown代码块标记。

用户观影统计数据：
- 总观影次数: {data['total_plays']}
- 总时长: {data['runtime']['total_minutes']} 分钟
- 深夜观影比例(22-02点): {data['night_ratio']:.1%}
- 周末观影比例: {data['weekend_ratio']:.1%}
- Binge指数(同剧间隔<2h): {data['binge']['binge_ratio']:.1%}
- 平均评分: {data['rating']['avg_rating']}
- 类型多样性指数: {data['diversity']['diversity_score']}/100
- 最爱类型Top5: {', '.join(g['genre'] + '(' + str(g['count']) + '次)' for g in top_genres)}
- 国别分布Top5: {', '.join(c['country'] + '(' + str(c['count']) + ')' for c in top_countries)}
- 非主流国家比例: {data['global_ratio']:.1%}
- 内容新鲜度: {data['freshness']['freshness_score']}/100 (平均首播年份: {data['freshness']['avg_year']})
- 观影稳定性: {data['pattern']['stability']}/100 (模式: {data['pattern']['pattern_type']})
- 电影占比: {data['runtime']['movie_ratio']:.1%}
- 小时分布: {json.dumps(hourly_dist, ensure_ascii=False)}
"""

    return prompt


def call_llm(data):
    import requests

    prompt = build_prompt(data)

    try:
        resp = requests.post(
            f"{LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位专业的观影行为分析师，擅长从观影数据中洞察人格特质。你的分析温暖、有洞察力、不机械。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
        result["source"] = "llm"
        result["model"] = LLM_MODEL
        result["generated_at"] = datetime.now().isoformat()
        return result

    except Exception as e:
        print(f"[Persona] 大模型调用失败: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def run():
    os.makedirs(WEB_DATA_DIR, exist_ok=True)

    if _is_cache_valid():
        print("[Persona] 缓存有效，跳过生成")
        return

    print("[Persona] 收集观影数据...")
    data = collect_data()

    result = None

    if LLM_API_KEY:
        print(f"[Persona] 调用大模型 ({LLM_MODEL})...")
        result = call_llm(data)

    if not result:
        print("[Persona] 降级为规则引擎生成...")
        result = generate_rule_based(data)

    path = _persona_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[Persona] 已生成 persona.json (source: {result.get('source')})")


if __name__ == "__main__":
    run()
