"""
SQLite 数据库封装
-----------------
提供建表、CRUD、按月聚合等操作。所有观影记录和媒体元数据统一存储在 data/trakt.db 中。
plays 表存储每次观影事件 + 核心元数据，media 表存储完整的媒体详情。
"""

import sqlite3
import json
import os
from datetime import datetime
from scripts.config import DB_PATH, REPORTS_DIR, WEB_DATA_DIR


def get_conn() -> sqlite3.Connection:
    """获取数据库连接，自动创建 data 目录（如不存在）。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果支持按列名访问
    conn.execute("PRAGMA journal_mode=WAL")  # WAL 模式提升并发写入性能
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _add_column_if_missing(conn, table: str, column: str, col_type: str):
    """安全地向已有表添加新列，列已存在时跳过（不报错）。"""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass  # 列已存在，忽略


def init_db():
    """
    初始化数据库表结构。
    使用 IF NOT EXISTS 确保幂等，多次执行不会报错。
    新增列通过 _add_column_if_missing 安全追加，兼容旧数据库升级。
    """
    conn = get_conn()
    cursor = conn.cursor()

    # ── 观影记录表 ──
    # 每条记录对应一次 Trakt 观影历史事件，同时存储 Trakt 返回的核心元数据
    # UNIQUE(trakt_id, watched_at) 防止重复写入同一条记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            trakt_id    INTEGER NOT NULL,
            tmdb_id     INTEGER,
            imdb_id     TEXT,
            title       TEXT    NOT NULL,
            year        INTEGER,
            media_type  TEXT    NOT NULL,
            season      INTEGER,
            number      INTEGER,
            runtime     INTEGER,
            genres      TEXT,
            overview    TEXT,
            rating      REAL,
            votes       INTEGER,
            action      TEXT,
            watched_at  TEXT    NOT NULL,
            watched_at_local TEXT,
            media_trakt_id INTEGER,
            created_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE(trakt_id, watched_at)
        )
    """)

    # ── 媒体元数据表 ──
    # 存储从 Trakt API 直接返回的完整媒体详情 + TMDB 补充的海报图片
    # 以 trakt_id 为主键，每个媒体只存一条（不区分单次观看）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media (
            trakt_id      INTEGER PRIMARY KEY,
            tmdb_id       INTEGER,
            imdb_id       TEXT,
            title         TEXT    NOT NULL,
            year          INTEGER,
            media_type    TEXT    NOT NULL,
            slug          TEXT,
            tagline       TEXT,
            overview      TEXT,
            poster_url    TEXT,
            backdrop_url  TEXT,
            genres        TEXT,
            runtime       INTEGER,
            rating        REAL,
            votes         INTEGER,
            certification TEXT,
            country       TEXT,
            language      TEXT,
            network       TEXT,
            status        TEXT,
            trailer_url   TEXT,
            homepage      TEXT,
            first_aired   TEXT,
            comment_count INTEGER,
            updated_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── 月度统计表（物化聚合） ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_stats (
            year_month     TEXT PRIMARY KEY,
            total_count    INTEGER DEFAULT 0,
            total_minutes  INTEGER DEFAULT 0,
            movie_count    INTEGER DEFAULT 0,
            episode_count  INTEGER DEFAULT 0,
            updated_at     TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── 索引 ──
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_plays_watched_at ON plays(watched_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_plays_media_type ON plays(media_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_plays_trakt_id ON plays(trakt_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_plays_tmdb_id ON plays(tmdb_id)")

    _add_column_if_missing(conn, "plays", "season", "INTEGER")
    _add_column_if_missing(conn, "plays", "number", "INTEGER")
    _add_column_if_missing(conn, "plays", "action", "TEXT")
    _add_column_if_missing(conn, "plays", "watched_at_local", "TEXT")
    _add_column_if_missing(conn, "plays", "media_trakt_id", "INTEGER")

    conn.commit()
    conn.close()


def insert_play(play: dict) -> bool:
    """
    插入一条观影记录，自动去重。
    参数:
        play: 包含 trakt_id, tmdb_id, imdb_id, title, year, media_type,
              season, number, runtime, genres, overview, rating, votes,
              action, watched_at 的字典
    返回:
        True 表示新增成功，False 表示已存在（重复）
    """
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO plays (trakt_id, tmdb_id, imdb_id, title, year, media_type,
                               season, number, runtime, genres, overview, rating, votes,
                               action, watched_at, watched_at_local, media_trakt_id)
            VALUES (:trakt_id, :tmdb_id, :imdb_id, :title, :year, :media_type,
                    :season, :number, :runtime, :genres, :overview, :rating, :votes,
                    :action, :watched_at, :watched_at_local, :media_trakt_id)
        """, play)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def upsert_media(media: dict):
    """
    插入或更新媒体完整元数据。
    如果 trakt_id 已存在则更新所有字段，否则新增。
    参数:
        media: 包含所有 media 表字段的字典
    """
    conn = get_conn()
    fields = [
        "trakt_id", "tmdb_id", "imdb_id", "title", "year", "media_type",
        "slug", "tagline", "overview", "poster_url", "backdrop_url",
        "genres", "runtime", "rating", "votes", "certification",
        "country", "language", "network", "status", "trailer_url",
        "homepage", "first_aired", "comment_count",
    ]
    # 只保留表中有定义的字段，避免未知字段导致 SQL 错误
    values = {k: media.get(k) for k in fields}

    columns = ", ".join(values.keys())
    placeholders = ", ".join(f":{k}" for k in values)
    update_clause = ", ".join(f"{k} = excluded.{k}" for k in values if k != "trakt_id")

    conn.execute(f"""
        INSERT INTO media ({columns}, updated_at)
        VALUES ({placeholders}, datetime('now'))
        ON CONFLICT(trakt_id) DO UPDATE SET
            {update_clause},
            updated_at = datetime('now')
    """, values)
    conn.commit()
    conn.close()


def get_latest_watched_at() -> str | None:
    """获取数据库中最新的 watched_at 时间，用于增量抓取。"""
    conn = get_conn()
    row = conn.execute("SELECT MAX(watched_at) AS latest FROM plays").fetchone()
    conn.close()
    return row["latest"] if row else None


def get_plays_count() -> int:
    """返回观影记录总数。"""
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS cnt FROM plays").fetchone()
    conn.close()
    return row["cnt"]


def get_plays_by_month(year_month: str) -> list[dict]:
    """查询指定月份 (YYYY-MM) 的观影记录。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM plays
        WHERE watched_at >= :start AND watched_at < :end
        ORDER BY watched_at DESC
    """, {
        "start": f"{year_month}-01",
        "end": f"{year_month}-31",
    }).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_stats() -> list[dict]:
    """查询所有月度统计（按月份倒序）。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM monthly_stats ORDER BY year_month DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def refresh_monthly_stats():
    """重新计算并更新所有月份的统计聚合数据。"""
    conn = get_conn()
    conn.execute("DELETE FROM monthly_stats")
    conn.execute("""
        INSERT INTO monthly_stats (year_month, total_count, total_minutes, movie_count, episode_count)
        SELECT
            substr(watched_at_local, 1, 7) AS year_month,
            COUNT(*)                  AS total_count,
            COALESCE(SUM(runtime), 0) AS total_minutes,
            COALESCE(SUM(CASE WHEN media_type = 'movie' THEN 1 ELSE 0 END), 0) AS movie_count,
            COALESCE(SUM(CASE WHEN media_type = 'episode' THEN 1 ELSE 0 END), 0) AS episode_count
        FROM plays
        GROUP BY substr(watched_at_local, 1, 7)
        ORDER BY year_month
    """)
    conn.commit()
    conn.close()


def get_media_by_trakt_id(trakt_id: int) -> dict | None:
    """按 trakt_id 快速查询媒体完整元数据（单 key 查询）。"""
    conn = get_conn()
    row = conn.execute("SELECT * FROM media WHERE trakt_id = ?", (trakt_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_top_media(limit: int = 10) -> list[dict]:
    """获取观影次数最多的 Top N 媒体（用于排行榜），关联 media 表获取海报。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            p.media_trakt_id AS trakt_id,
            CASE WHEN p.media_type = 'episode'
                 THEN SUBSTR(p.title, 1, INSTR(p.title, ' S') - 1)
                 ELSE p.title
            END AS title,
            p.media_type,
            p.genres,
            COUNT(*) AS watch_count,
            SUM(p.runtime) AS total_minutes,
            MAX(p.watched_at_local) AS last_watched,
            m.poster_url, m.rating, m.overview
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.media_trakt_id
        GROUP BY p.media_trakt_id
        ORDER BY last_watched DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_genre_stats() -> list[dict]:
    """统计各类型（genre）的观影次数分布。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT genres, COUNT(*) AS cnt, SUM(runtime) AS total_minutes
        FROM plays
        WHERE genres IS NOT NULL AND genres != ''
        GROUP BY media_trakt_id, genres
    """).fetchall()
    result = {}
    for r in rows:
        try:
            genre_list = json.loads(r["genres"])
        except (json.JSONDecodeError, TypeError):
            genre_list = []
        for g in genre_list:
            if g not in result:
                result[g] = {"genre": g, "cnt": 0, "total_minutes": 0}
            result[g]["cnt"] += 1
            result[g]["total_minutes"] += r["total_minutes"] or 0
    conn.close()
    return sorted(result.values(), key=lambda x: x["cnt"], reverse=True)


def get_all_media(limit: int = 500) -> list[dict]:
    """获取所有媒体元数据列表（用于前端展示媒体库）。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM media ORDER BY updated_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_genre_stats() -> list[dict]:
    """按日期+类型统计每日观看集数和时长，用于前端图表。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            DATE(watched_at_local) AS date,
            genres,
            runtime
        FROM plays
        WHERE genres IS NOT NULL AND genres != '' AND watched_at_local IS NOT NULL
    """).fetchall()
    conn.close()

    result = {}
    for r in rows:
        try:
            genre_list = json.loads(r["genres"])
        except (json.JSONDecodeError, TypeError):
            continue
        date = r["date"]
        runtime_per = (r["runtime"] or 0) / max(len(genre_list), 1)
        for g in genre_list:
            key = (date, g)
            if key not in result:
                result[key] = {"date": date, "genre": g, "count": 0, "minutes": 0}
            result[key]["count"] += 1
            result[key]["minutes"] += runtime_per

    return list(result.values())


def get_all_plays() -> list[dict]:
    """获取所有观影记录（按观看时间倒序），关联媒体表获取海报。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*, m.poster_url
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.media_trakt_id
        ORDER BY p.watched_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ensure_dirs():
    """确保 data 和 web 相关目录存在。"""
    os.makedirs(DB_PATH.replace("trakt.db", ""), exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(WEB_DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# 人格画像分析查询
# ═══════════════════════════════════════════════════════════


def get_hourly_stats() -> list[dict]:
    """按小时统计观影量（0-23点），用于分析作息偏好。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT CAST(strftime('%H', watched_at_local) AS INTEGER) AS hour,
               COUNT(*) AS count,
               COALESCE(SUM(runtime), 0) AS total_minutes
        FROM plays
        WHERE watched_at_local IS NOT NULL
        GROUP BY hour ORDER BY hour
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_weekday_stats() -> list[dict]:
    """按星期统计观影量（0=周日, 6=周六），用于分析生活节奏。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT CAST(strftime('%w', watched_at_local) AS INTEGER) AS weekday,
               COUNT(*) AS count
        FROM plays
        WHERE watched_at_local IS NOT NULL
        GROUP BY weekday ORDER BY weekday
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_binge_stats() -> dict:
    """检测 binge-watching 行为（同一剧集间隔<2小时的连续观看）。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT media_trakt_id, watched_at_local, title
        FROM plays
        WHERE watched_at_local IS NOT NULL AND media_trakt_id IS NOT NULL
        ORDER BY media_trakt_id, watched_at_local
    """).fetchall()
    conn.close()

    if not rows:
        return {"binge_count": 0, "total_sessions": 0, "binge_ratio": 0.0}

    binge_count = 0
    total_sessions = 0
    prev_mid = None
    prev_time = None

    for r in rows:
        mid = r["media_trakt_id"]
        try:
            t = datetime.fromisoformat(r["watched_at_local"])
        except (ValueError, TypeError):
            continue

        if prev_mid == mid and prev_time:
            gap = (t - prev_time).total_seconds() / 3600
            if gap < 2:
                binge_count += 1
        total_sessions += 1
        prev_mid = mid
        prev_time = t

    binge_ratio = binge_count / max(total_sessions, 1)
    return {
        "binge_count": binge_count,
        "total_sessions": total_sessions,
        "binge_ratio": round(binge_ratio, 3),
    }


def get_rating_preference() -> dict:
    """分析评分偏好：平均评分、评分分布、精品度。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT rating, votes FROM media
        WHERE rating IS NOT NULL AND rating > 0
    """).fetchall()
    conn.close()

    if not rows:
        return {"avg_rating": 0, "rating_dist": {}, "quality_score": 0}

    ratings = [r["rating"] for r in rows]
    avg = sum(ratings) / len(ratings)
    dist = {}
    for r in ratings:
        bucket = f"{int(r)}-{int(r)+1}"
        dist[bucket] = dist.get(bucket, 0) + 1

    return {
        "avg_rating": round(avg, 2),
        "rating_dist": dist,
        "quality_score": round(min(avg / 10 * 100, 100)),
    }


def get_country_stats() -> list[dict]:
    """统计国别/语言分布。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT country, language, COUNT(*) AS count
        FROM media
        WHERE country IS NOT NULL AND country != ''
        GROUP BY country ORDER BY count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_freshness_stats() -> dict:
    """分析内容新鲜度：首播年份分布。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT first_aired FROM media
        WHERE first_aired IS NOT NULL
    """).fetchall()
    conn.close()

    if not rows:
        return {"avg_year": 0, "year_dist": {}, "freshness_score": 0}

    years = []
    for r in rows:
        try:
            y = int(r["first_aired"][:4])
            years.append(y)
        except (ValueError, TypeError, IndexError):
            continue

    if not years:
        return {"avg_year": 0, "year_dist": {}, "freshness_score": 0}

    avg_year = sum(years) / len(years)
    current_year = datetime.now().year
    freshness = round(min((avg_year - 2000) / (current_year - 2000) * 100, 100))

    year_dist = {}
    for y in years:
        decade = (y // 5) * 5
        key = f"{decade}s"
        year_dist[key] = year_dist.get(key, 0) + 1

    return {
        "avg_year": round(avg_year),
        "year_dist": year_dist,
        "freshness_score": max(0, freshness),
    }


def get_watch_pattern() -> dict:
    """分析月度观影波动：稳定型 vs 脉冲型。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT substr(watched_at_local, 1, 7) AS month, COUNT(*) AS count
        FROM plays
        WHERE watched_at_local IS NOT NULL
        GROUP BY month ORDER BY month
    """).fetchall()
    conn.close()

    if len(rows) < 2:
        return {"stability": 100, "pattern_type": "stable", "std_dev": 0, "mean": 0}

    counts = [r["count"] for r in rows]
    mean = sum(counts) / len(counts)
    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    std_dev = variance ** 0.5
    cv = std_dev / mean if mean > 0 else 0

    stability = round(max(0, 100 - cv * 50))
    pattern_type = "pulse" if cv > 0.8 else "balanced" if cv > 0.4 else "stable"

    return {
        "stability": stability,
        "pattern_type": pattern_type,
        "std_dev": round(std_dev, 1),
        "mean": round(mean, 1),
    }


def get_diversity_index() -> dict:
    """计算类型多样性指数（香农熵），反映观影广度。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT genres, COUNT(*) AS cnt
        FROM plays
        WHERE genres IS NOT NULL AND genres != ''
        GROUP BY media_trakt_id, genres
    """).fetchall()
    conn.close()

    genre_counts = {}
    total = 0
    for r in rows:
        try:
            gl = json.loads(r["genres"])
        except (json.JSONDecodeError, TypeError):
            continue
        for g in gl:
            genre_counts[g] = genre_counts.get(g, 0) + r["cnt"]
            total += r["cnt"]

    if not genre_counts or total == 0:
        return {"diversity_score": 0, "top_genres": [], "genre_count": 0}

    import math
    entropy = 0
    for cnt in genre_counts.values():
        p = cnt / total
        if p > 0:
            entropy -= p * math.log2(p)

    max_entropy = math.log2(len(genre_counts)) if len(genre_counts) > 1 else 1
    normalized = round((entropy / max_entropy * 100) if max_entropy > 0 else 0)

    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    top_genres = [{"genre": g, "count": c} for g, c in sorted_genres[:5]]

    return {
        "diversity_score": normalized,
        "top_genres": top_genres,
        "genre_count": len(genre_counts),
    }


def get_monthly_posters() -> list[dict]:
    """按月聚合全部观影海报，用于前端月度海报墙展示。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            substr(p.watched_at_local, 1, 7) AS year_month,
            p.media_trakt_id AS trakt_id,
            CASE WHEN p.media_type = 'episode'
                 THEN SUBSTR(p.title, 1, INSTR(p.title, ' S') - 1)
                 ELSE p.title
            END AS title,
            p.media_type,
            m.poster_url,
            COUNT(*) AS watch_count
        FROM plays p
        LEFT JOIN media m ON m.trakt_id = p.media_trakt_id
        WHERE p.watched_at_local IS NOT NULL AND p.media_trakt_id IS NOT NULL
        GROUP BY substr(p.watched_at_local, 1, 7), p.media_trakt_id
        ORDER BY year_month DESC, watch_count DESC
    """).fetchall()
    conn.close()

    months = {}
    for r in rows:
        ym = r["year_month"]
        if ym not in months:
            months[ym] = {"year_month": ym, "posters": []}
        months[ym]["posters"].append({
            "trakt_id": r["trakt_id"],
            "title": r["title"],
            "media_type": r["media_type"],
            "poster_url": r["poster_url"],
            "watch_count": r["watch_count"],
        })

    return list(months.values())


def get_runtime_preference() -> dict:
    """分析时长偏好：电影/剧集比例、平均时长。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT media_type, runtime, COUNT(*) AS count, SUM(runtime) AS total_minutes
        FROM plays
        WHERE runtime IS NOT NULL AND runtime > 0
        GROUP BY media_type
    """).fetchall()
    conn.close()

    if not rows:
        return {"avg_runtime": 0, "movie_ratio": 0, "total_minutes": 0}

    total_count = sum(r["count"] for r in rows)
    total_minutes = sum(r["total_minutes"] or 0 for r in rows)
    movie_count = sum(r["count"] for r in rows if r["media_type"] == "movie")
    avg_runtime = total_minutes / max(total_count, 1)

    return {
        "avg_runtime": round(avg_runtime),
        "movie_ratio": round(movie_count / max(total_count, 1), 3),
        "total_minutes": total_minutes,
    }