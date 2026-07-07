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
        tags.append({"icon": "夜", "name": "深夜追剧人", "desc": "夜深了，你的故事才刚开始", "strength": min(data["night_ratio"] / 0.6, 1.0)})
    if data["rating"]["avg_rating"] > 7.5:
        tags.append({"icon": "精", "name": "精品猎人", "desc": "你的时间只留给好故事", "strength": min(data["rating"]["avg_rating"] / 9, 1.0)})
    if data["diversity"]["diversity_score"] > 70:
        tags.append({"icon": "杂", "name": "杂食观众", "desc": "什么类型都看，什么故事都体验", "strength": data["diversity"]["diversity_score"] / 100})
    if data["binge"]["binge_ratio"] > 0.4:
        tags.append({"icon": "追", "name": "一口气追完党", "desc": "开了头就停不下来", "strength": min(data["binge"]["binge_ratio"] / 0.7, 1.0)})
    if data["global_ratio"] > 0.3:
        tags.append({"icon": "界", "name": "国际化口味", "desc": "你的视界没有国界", "strength": min(data["global_ratio"] / 0.5, 1.0)})
    if data["weekend_ratio"] > 0.45:
        tags.append({"icon": "末", "name": "周末型", "desc": "工作日攒着，周末一次性释放", "strength": min(data["weekend_ratio"] / 0.6, 1.0)})
    if data["pattern"]["pattern_type"] == "pulse":
        tags.append({"icon": "冲", "name": "脉冲型", "desc": "追剧像发洪水，来一波停一波", "strength": 1.0 - data["pattern"]["stability"] / 100})
    if data["freshness"]["freshness_score"] > 70:
        tags.append({"icon": "新", "name": "追新一族", "desc": "永远在追最新最热的剧", "strength": data["freshness"]["freshness_score"] / 100})
    if data["runtime"]["movie_ratio"] < 0.1:
        tags.append({"icon": "剧", "name": "剧集至上", "desc": "长线叙事才是你的菜", "strength": 1.0 - data["runtime"]["movie_ratio"]})

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
    top_tag = tags[0] if tags else {"icon": "影", "name": "观影爱好者", "desc": "你热爱故事"}

    top_genres = data["diversity"].get("top_genres", [])
    genre_text = "、".join(g["genre"] for g in top_genres[:2]) if top_genres else "各种类型"

    narrative = (
        f"这一年你一共看了 {data['total_plays']} 部作品。"
        f"你是{top_tag['name']}——{top_tag['desc']}。"
        f"你偏好 {genre_text} 的组合，"
        f"平均评分 {data['rating']['avg_rating']}，"
        f"binge 指数 {data['binge']['binge_ratio']}。"
    )

    highlights = [f"{t['name']}：{t['desc']}" for t in tags[:4]]

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

    # 找出最活跃的时段
    peak_hours = sorted(hourly_dist.items(), key=lambda x: x[1], reverse=True)[:3]
    peak_hours_str = ", ".join(f"{h}点({c}次)" for h, c in peak_hours if h is not None)

    prompt = f"""你是一个有趣的灵魂，同时也是一位深谙人性的观影行为分析大师。你看过无数人的观影数据，但你不会用模板化的方式解读——每个人在你眼里都是独一无二的故事。

现在，请根据下面这位用户的观影数据，用你自己的方式画出 ta 的「观影灵魂画像」。

不要给我千篇一律的标签和评分。我想看到的是：
- 一个让人眼前一亮的「观影原型」——不是"深夜追剧人"这种烂大街的词，而是真正从数据里长出来的独特定义
- 用讲故事的方式写一段叙事文案，像你在跟朋友聊这个人一样自然，有细节、有洞察、有惊喜发现，别像报告
- 几个有趣的标签和雷达图维度，但名字和描述要有创意，别太正经
- 如果数据里有什么矛盾或有趣的点（比如自称杂食但其实偏科严重，或者深夜 binge 却给低分），大胆点出来

返回 JSON，字段如下（但内容请自由发挥，别被字段名限制住）：
{{
  "archetype": "观影原型名称（4-8字，要有画面感）",
  "archetype_description": "一句话点题",
  "tags": [{{"icon": "一个中文字", "name": "标签名", "desc": "描述"}}],
  "radar": {{
    "immersion": 0, "quality": 0, "diversity": 0, "depth": 0,
    "night_owl": 0, "freshness": 0, "global": 0, "binge": 0
  }},
  "narrative": "100-200字的叙事文案，像聊天一样",
  "highlights": ["高光时刻1", "高光时刻2"],
  "personality_traits": {{
    "openness": "高/中/低 — 解释",
    "conscientiousness": "高/中/低 — 解释",
    "extraversion": "高/中/低 — 解释",
    "agreeableness": "高/中/低 — 解释",
    "neuroticism": "高/中/低 — 解释"
  }}
}}

radar 各维度 0-100 整数。返回纯 JSON，不要 markdown 代码块。

---
用户观影数据 ---
- 总观影次数: {data['total_plays']}
- 总时长: {data['runtime']['total_minutes']} 分钟（约 {data['runtime']['total_minutes'] // 60} 小时）
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
- 最活跃时段: {peak_hours_str}
- 小时分布: {json.dumps(hourly_dist, ensure_ascii=False)}
"""

    return prompt


def call_llm(data):
    import requests

    prompt = build_prompt(data)

    # 截取 prompt 前 200 字用于日志预览
    prompt_preview = prompt.replace('\n', ' ')[:200]
    print(f"[Persona] 🤖 大模型调用中...")
    print(f"[Persona] 📍 API: {LLM_API_BASE}")
    print(f"[Persona] 📍 模型: {LLM_MODEL}")
    print(f"[Persona] 📍 API Key: {'已配置 (' + LLM_API_KEY[:6] + '...' + LLM_API_KEY[-4:] + ')' if LLM_API_KEY else '❌ 未配置'}")
    print(f"[Persona] 📝 Prompt 预览: {prompt_preview}...")

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
                    {"role": "system", "content": "你是一个有趣的灵魂，也是一位深谙人性的观影行为分析大师。你从不用模板化的方式解读一个人——每个人在你眼里都是独一无二的故事。你的文字像在跟朋友聊天，但洞察力像手术刀一样精准。用中文回复。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.9,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        print(f"[Persona] 📡 HTTP 状态码: {resp.status_code}")
        resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"]
        print(f"[Persona] ✅ 大模型返回成功，内容长度: {len(content)} 字")
        result = json.loads(content)
        result["source"] = "llm"
        result["model"] = LLM_MODEL
        result["generated_at"] = datetime.now().isoformat()
        print(f"[Persona] 🎭 生成原型: {result.get('archetype', '未知')}")
        print(f"[Persona] 🏷️ 标签数: {len(result.get('tags', []))}")
        return result

    except requests.exceptions.ConnectionError as e:
        print(f"[Persona] ❌ 大模型连接失败: {e}")
        return None
    except requests.exceptions.Timeout:
        print(f"[Persona] ❌ 大模型调用超时 (60s)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[Persona] ❌ 大模型 HTTP 错误: {e}")
        print(f"[Persona] ❌ 响应内容: {resp.text[:500] if resp else '无响应'}")
        return None
    except json.JSONDecodeError as e:
        print(f"[Persona] ❌ 大模型返回 JSON 解析失败: {e}")
        print(f"[Persona] ❌ 原始内容前500字: {content[:500]}")
        return None
    except Exception as e:
        print(f"[Persona] ❌ 大模型调用异常: {type(e).__name__}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def run():
    os.makedirs(WEB_DATA_DIR, exist_ok=True)

    if _is_cache_valid():
        print("[Persona] ⏭️ 缓存有效，跳过生成")
        return

    print("[Persona] ============================")
    print("[Persona] 🎬 开始生成观影人格画像")
    print("[Persona] ============================")

    print("[Persona] 📊 收集观影数据...")
    data = collect_data()
    print(f"[Persona] 📊 数据收集完成: {data['total_plays']} 条播放记录")

    result = None

    if LLM_API_KEY:
        print(f"[Persona] 🔑 检测到 LLM_API_KEY，准备调用大模型...")
        result = call_llm(data)
        if result:
            print(f"[Persona] ✅✅✅ 大模型生成成功! ✅✅✅")
        else:
            print(f"[Persona] ⚠️ 大模型调用失败，降级为规则引擎...")
    else:
        print(f"[Persona] ⚠️ LLM_API_KEY 未配置，直接使用规则引擎...")

    if not result:
        print("[Persona] 📋 使用规则引擎生成...")
        result = generate_rule_based(data)
        print(f"[Persona] ✅ 规则引擎生成完成")

    path = _persona_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    source = result.get("source", "unknown")
    print(f"[Persona] ============================")
    print(f"[Persona] 📦 输出: {path}")
    print(f"[Persona] 🏷️ 数据来源: {'🤖 大模型' if source == 'llm' else '📋 规则引擎' if source == 'rule_engine' else '❓ ' + source}")
    print(f"[Persona] ============================")


if __name__ == "__main__":
    run()
