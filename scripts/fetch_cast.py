"""
演员/导演数据抓取
-----------------
从 TMDB API 拉取剧集/电影的演员和导演信息，存入 cast_crew 表。

用法：
    python -m scripts.fetch_cast              # 增量模式（只拉缺 cast 的媒体）
    python -m scripts.fetch_cast --force      # 全量重建
    python -m scripts.fetch_cast --media 1399 # 只拉指定 trakt_id
"""

import time
import sys
import argparse

import requests
from pyrate_limiter import Duration, Limiter, Rate
from requests_ratelimiter import LimiterAdapter

from scripts.config import TMDB_API_KEY, TMDB_BASE_URL
from scripts.db import (
    get_conn,
    init_db,
    ensure_dirs,
    upsert_cast_crew,
    get_cast_for_media,
)

# ── 请求频率控制 ──
_tmdb_limiter = Limiter(Rate(4, Duration.SECOND))
_tmdb_adapter = LimiterAdapter(limiter=_tmdb_limiter)
_session = requests.Session()
_session.mount("https://", _tmdb_adapter)


def _api_request(endpoint: str, params: dict | None = None) -> dict:
    """通用 TMDB API 请求。"""
    if params is None:
        params = {}
    params.setdefault("api_key", TMDB_API_KEY)
    params.setdefault("language", "zh-CN")

    url = f"{TMDB_BASE_URL}{endpoint}"
    resp = _session.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _fetch_credits(tmdb_id: int, media_type: str) -> list[dict]:
    """
    从 TMDB 拉取某媒体的演员和导演信息。
    返回: [{"person_id": 123, "person_name": "...", "person_role": "actor", "character_name": "..."}, ...]
    """
    if media_type == "movie":
        endpoint = f"/movie/{tmdb_id}/credits"
    else:
        endpoint = f"/tv/{tmdb_id}/credits"

    try:
        data = _api_request(endpoint)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return []
        raise

    cast_list = []

    # 提取演员（取前 15 名）
    for idx, c in enumerate(data.get("cast", [])[:15]):
        cast_list.append({
            "person_id": c.get("id", 0),
            "person_name": c.get("name", c.get("original_name", "")),
            "person_role": "actor",
            "character_name": c.get("character"),
        })

    # 提取导演
    for c in data.get("crew", []):
        if c.get("job") == "Director" or c.get("department") == "Directing":
            cast_list.append({
                "person_id": c.get("id", 0),
                "person_name": c.get("name", ""),
                "person_role": "director",
                "character_name": None,
            })

    return cast_list


def _get_tmdb_id_for_media(trakt_id: int, media_type: str) -> int | None:
    """从 media 表获取对应 trakt_id 的 tmdb_id。"""
    conn = get_conn()
    row = conn.execute(
        "SELECT tmdb_id FROM media WHERE trakt_id = ?",
        (trakt_id,)
    ).fetchone()
    conn.close()
    return row["tmdb_id"] if row and row["tmdb_id"] else None


def fetch_cast_for_media(trakt_id: int, media_type: str, tmdb_id: int | None = None) -> int:
    """
    拉取单个媒体的演员数据并存入数据库。
    返回: 新增/更新的演员数量
    """
    if tmdb_id is None:
        tmdb_id = _get_tmdb_id_for_media(trakt_id, media_type)

    if not tmdb_id:
        return 0

    credits = _fetch_credits(tmdb_id, media_type)
    if not credits:
        return 0

    upsert_cast_crew(trakt_id, credits)
    return len(credits)


def run(force: bool = False, media_id: int | None = None):
    """主函数：抓取演员数据。"""
    ensure_dirs()
    init_db()

    if not TMDB_API_KEY:
        print("[Cast] 缺少 TMDB_API_KEY，跳过")
        return

    conn = get_conn()

    if media_id:
        # 只处理指定媒体
        row = conn.execute(
            "SELECT trakt_id, media_type, tmdb_id FROM media WHERE trakt_id = ?",
            (media_id,)
        ).fetchone()
        conn.close()

        if not row:
            print(f"[Cast] 未找到 trakt_id={media_id} 的媒体")
            return

        count = fetch_cast_for_media(row["trakt_id"], row["media_type"], row["tmdb_id"])
        print(f"[Cast] 已更新 {count} 位演员（{row['title']}）")
        return

    # 获取需要抓取演员的媒体列表
    if force:
        # 全量重建：拉取所有有 tmdb_id 的 media
        rows = conn.execute(
            "SELECT trakt_id, media_type, tmdb_id, title FROM media WHERE tmdb_id IS NOT NULL ORDER BY trakt_id"
        ).fetchall()
        print(f"[Cast] 全量模式：共 {len(rows)} 条媒体需要处理")
    else:
        # 增量模式：只处理 cast_crew 表中没有记录的媒体
        rows = conn.execute("""
            SELECT m.trakt_id, m.media_type, m.tmdb_id, m.title
            FROM media m
            WHERE m.tmdb_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM cast_crew cc WHERE cc.media_trakt_id = m.trakt_id
              )
            ORDER BY m.trakt_id
        """).fetchall()
        print(f"[Cast] 增量模式：共 {len(rows)} 条媒体缺少演员数据")

    conn.close()

    total_cast = 0
    for i, row in enumerate(rows):
        try:
            count = fetch_cast_for_media(row["trakt_id"], row["media_type"], row["tmdb_id"])
            total_cast += count
            if count > 0:
                print(f"  [{i+1}/{len(rows)}] {row['title']}: +{count} 位演员")
            # 避免请求过快
            if (i + 1) % 10 == 0:
                time.sleep(1)
        except Exception as e:
            print(f"  [{i+1}/{len(rows)}] {row['title']}: 失败 ({e})")

    print(f"[Cast] 完成！共处理 {len(rows)} 条媒体，{total_cast} 位演员")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 TMDB 抓取演员/导演数据")
    parser.add_argument("--force", action="store_true", help="全量重建（忽略已有数据）")
    parser.add_argument("--media", type=int, help="只处理指定 trakt_id")
    args = parser.parse_args()
    run(force=args.force, media_id=args.media)
