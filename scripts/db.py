"""
SQLite 数据库封装
-----------------
提供建表、CRUD、按月聚合等操作。所有观影记录和媒体元数据统一存储在 data/trakt.db 中。
plays 表存储每次观影事件 + 核心元数据，media 表存储完整的媒体详情。
"""

import sqlite3
import os
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
                               action, watched_at, watched_at_local)
            VALUES (:trakt_id, :tmdb_id, :imdb_id, :title, :year, :media_type,
                    :season, :number, :runtime, :genres, :overview, :rating, :votes,
                    :action, :watched_at, :watched_at_local)
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
        SELECT p.trakt_id, p.title, p.media_type, p.genres,
               COUNT(*) AS watch_count,
               SUM(p.runtime) AS total_minutes,
               m.poster_url, m.rating, m.overview
        FROM plays p
        LEFT JOIN media m ON p.trakt_id = m.trakt_id
        GROUP BY p.trakt_id
        ORDER BY watch_count DESC
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
        GROUP BY genres
        ORDER BY cnt DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_media(limit: int = 500) -> list[dict]:
    """获取所有媒体元数据列表（用于前端展示媒体库）。"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM media ORDER BY updated_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ensure_dirs():
    """确保 data 和 web 相关目录存在。"""
    os.makedirs(DB_PATH.replace("trakt.db", ""), exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(WEB_DATA_DIR, exist_ok=True)