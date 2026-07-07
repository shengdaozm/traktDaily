"""
Embedding 模块
--------------
使用 sentence-transformers 本地模型对剧集进行语义向量化。

模型：paraphrase-multilingual-MiniLM-L12-v2（支持中英文，~470MB）
- 首次运行自动下载模型，后续从缓存读取
- 对所有剧的 overview + title + genres 组合文本做 embedding
- 计算用户口味向量（高分剧 embedding 平均）
- 提供余弦相似度查询

存储：embedding 缓存到 data/embeddings.json（随私有仓库同步）
"""

import json
import os
import sys
import time
from typing import Any

from scripts.config import DB_PATH, REPORTS_DIR
from scripts.db import get_conn, init_db, load_user_ratings, get_rated_shows

# Embedding 缓存文件
EMBEDDING_CACHE = os.path.join(os.path.dirname(DB_PATH), "embeddings.json")

# 模型名称
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None


def _get_model():
    """懒加载模型（只在首次调用时下载/加载）。"""
    global _model
    if _model is not None:
        return _model

    print(f"[Embedding] 📥 加载模型: {MODEL_NAME}")
    print(f"[Embedding] ⏳ 首次运行需要下载模型（~470MB），请耐心等待...")
    t0 = time.time()
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
        elapsed = time.time() - t0
        print(f"[Embedding] ✅ 模型加载完成，耗时 {elapsed:.1f}s，维度: {_model.get_embedding_dimension()}")
    except ImportError:
        print(f"[Embedding] ❌ sentence-transformers 未安装，请 pip install sentence-transformers")
        raise
    except Exception as e:
        print(f"[Embedding] ❌ 模型加载失败: {type(e).__name__}: {e}")
        raise
    return _model


def _build_text(show: dict) -> str:
    """将剧的元数据组合成 embedding 用的文本。"""
    parts = []
    title = show.get("title") or ""
    if title:
        parts.append(title)

    overview = show.get("overview") or ""
    if overview:
        parts.append(overview)

    genres = show.get("genres")
    if genres:
        try:
            genre_list = json.loads(genres) if isinstance(genres, str) else genres
            if genre_list:
                parts.append(" ".join(genre_list))
        except (json.JSONDecodeError, TypeError):
            pass

    network = show.get("network")
    if network:
        parts.append(network)

    tagline = show.get("tagline") or ""
    if tagline:
        parts.append(tagline)

    return " ".join(parts).strip()


def _load_cache() -> dict:
    """加载 embedding 缓存。"""
    if os.path.exists(EMBEDDING_CACHE):
        with open(EMBEDDING_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"embeddings": {}, "user_taste_vector": None, "model": MODEL_NAME, "updated_at": None}


def _save_cache(cache: dict):
    """保存 embedding 缓存。"""
    os.makedirs(os.path.dirname(EMBEDDING_CACHE), exist_ok=True)
    with open(EMBEDDING_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """计算两个向量的余弦相似度。"""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def generate_embeddings(force: bool = False) -> dict:
    """
    对数据库中所有剧生成 embedding。
    增量模式：只对没有 embedding 的剧生成新的。
    force=True 时重新生成所有。

    返回: cache dict
    """
    print("[Embedding] ============================")
    print("[Embedding] 🧠 开始生成语义 Embedding")
    print("[Embedding] ============================")

    init_db()
    cache = _load_cache()

    # 检查模型一致性
    if cache.get("model") != MODEL_NAME:
        print(f"[Embedding] ⚠️ 模型变更（{cache.get('model')} → {MODEL_NAME}），重新生成全部")
        force = True
        cache["embeddings"] = {}

    conn = get_conn()
    rows = conn.execute("SELECT * FROM media").fetchall()
    conn.close()

    all_media = [dict(r) for r in rows]
    print(f"[Embedding] 📊 数据库中共 {len(all_media)} 部媒体")

    existing_ids = set(cache.get("embeddings", {}).keys())
    media_ids = {str(m["trakt_id"]) for m in all_media}

    # 清理已不存在的剧的 embedding
    removed = existing_ids - media_ids
    if removed:
        print(f"[Embedding] 🧹 清理 {len(removed)} 部已不存在的剧的 embedding")
        for rid in removed:
            cache["embeddings"].pop(rid, None)

    # 确定需要生成 embedding 的剧
    if force:
        to_embed = all_media
        cache["embeddings"] = {}
    else:
        to_embed = [m for m in all_media if str(m["trakt_id"]) not in cache.get("embeddings", {})]

    print(f"[Embedding] 📝 需要 embedding: {len(to_embed)} 部（已有: {len(all_media) - len(to_embed)} 部）")

    if to_embed:
        model = _get_model()

        # 批量生成
        texts = [_build_text(m) for m in to_embed]
        # 过滤空文本
        valid = [(i, t) for i, t in enumerate(texts) if t]
        if not valid:
            print("[Embedding] ⚠️ 没有有效的文本内容可 embedding")
        else:
            valid_indices = [i for i, _ in valid]
            valid_texts = [t for _, t in valid]
            print(f"[Embedding] 🔄 正在生成 {len(valid_texts)} 部剧的 embedding...")
            t0 = time.time()
            vectors = model.encode(valid_texts, show_progress_bar=False, batch_size=32)
            elapsed = time.time() - t0
            print(f"[Embedding] ✅ Embedding 生成完成，耗时 {elapsed:.1f}s")

            for idx, vec in zip(valid_indices, vectors):
                trakt_id = str(to_embed[idx]["trakt_id"])
                cache["embeddings"][trakt_id] = {
                    "title": to_embed[idx]["title"],
                    "vector": vec.tolist(),
                }

    # 计算用户口味向量
    cache["user_taste_vector"] = _compute_user_taste_vector(cache)
    cache["model"] = MODEL_NAME
    cache["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    _save_cache(cache)

    print(f"[Embedding] 📦 缓存已保存: {EMBEDDING_CACHE}")
    print(f"[Embedding] 📊 总计 embedding: {len(cache['embeddings'])} 部")
    print(f"[Embedding] 📊 用户口味向量: {'✅ 已生成' if cache['user_taste_vector'] else '❌ 未生成（需要打分数据）'}")
    print("[Embedding] ============================")

    return cache


def _compute_user_taste_vector(cache: dict) -> list[float] | None:
    """
    计算用户口味向量 = 用户打分≥7的剧的 embedding 加权平均。
    权重 = 用户评分（归一化）。
    """
    rated_data = load_user_ratings()
    if not rated_data:
        print("[Embedding] ⚠️ 无评分数据，无法计算用户口味向量")
        return None
    
    rated = rated_data.get("ratings", []) if isinstance(rated_data, dict) else rated_data
    if not rated:
        print("[Embedding] ⚠️ 无评分数据，无法计算用户口味向量")
        return None

    # 筛选有 embedding 且有评分的剧
    valid = []
    for r in rated:
        tid = str(r.get("trakt_id"))
        rating = r.get("user_rating")
        emb = cache.get("embeddings", {}).get(tid)
        if emb and rating and rating > 0:
            # 评分已在 load_user_ratings 中归一化到 0-10
            norm_rating = rating
            if norm_rating >= 7:
                valid.append((emb["vector"], norm_rating))

    if not valid:
        print("[Embedding] ⚠️ 没有评分≥7且有 embedding 的剧，无法计算口味向量")
        return None

    print(f"[Embedding] 🎯 计算用户口味向量，基于 {len(valid)} 部高分剧")

    # 加权平均
    dim = len(valid[0][0])
    result = [0.0] * dim
    total_weight = 0.0
    for vec, weight in valid:
        for i in range(dim):
            result[i] += vec[i] * weight
        total_weight += weight

    if total_weight > 0:
        result = [v / total_weight for v in result]

    print(f"[Embedding] ✅ 用户口味向量已生成（维度: {dim}）")
    return result


def get_similarity(trakt_id: int, cache: dict | None = None) -> float:
    """
    获取某部剧与用户口味向量的余弦相似度。
    返回 0-1 的相似度分数。
    """
    if cache is None:
        cache = _load_cache()

    user_vec = cache.get("user_taste_vector")
    emb = cache.get("embeddings", {}).get(str(trakt_id))

    if not user_vec or not emb:
        return 0.0

    return _cosine_similarity(user_vec, emb["vector"])


def get_similar_shows(trakt_id: int, top_n: int = 10, cache: dict | None = None) -> list[dict]:
    """
    获取与某部剧最相似的其他剧。
    """
    if cache is None:
        cache = _load_cache()

    target_emb = cache.get("embeddings", {}).get(str(trakt_id))
    if not target_emb:
        return []

    target_vec = target_emb["vector"]
    scores = []
    for tid, emb in cache.get("embeddings", {}).items():
        if tid == str(trakt_id):
            continue
        sim = _cosine_similarity(target_vec, emb["vector"])
        scores.append({"trakt_id": int(tid), "title": emb["title"], "similarity": round(sim, 4)})

    scores.sort(key=lambda x: x["similarity"], reverse=True)
    return scores[:top_n]


def run(force: bool = False):
    """CLI 入口。"""
    generate_embeddings(force=force)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="生成语义 Embedding")
    parser.add_argument("--force", action="store_true", help="强制重新生成所有 embedding")
    args = parser.parse_args()
    run(force=args.force)
