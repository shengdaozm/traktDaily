"""
TMDB 海报补全脚本
-----------------
查找 media 表中 poster_url 为空的记录，重新调 TMDB API 补全海报和背景图。
用法: python -m scripts.backfill_posters
"""

import time
from scripts.db import get_conn
from scripts.tmdb import get_tmdb_images


def run():
    conn = get_conn()
    rows = conn.execute("""
        SELECT trakt_id, tmdb_id, title, year, media_type
        FROM media
        WHERE poster_url IS NULL OR poster_url = ''
    """).fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        print("[Backfill] 所有媒体已有海报，无需补全")
        return

    print(f"[Backfill] 发现 {total} 个媒体缺少海报，开始补全...")

    success = 0
    fail = 0

    for i, row in enumerate(rows, 1):
        title = row["title"]
        tmdb_id = row["tmdb_id"]
        media_type = row["media_type"]
        year = row["year"]

        print(f"  [{i}/{total}] {title} (tmdb_id={tmdb_id}, type={media_type})")

        try:
            images = get_tmdb_images(
                tmdb_id=tmdb_id,
                title=title,
                media_type=media_type,
                year=year,
            )
            if images and images.get("poster_url"):
                conn = get_conn()
                conn.execute("""
                    UPDATE media
                    SET poster_url = ?, backdrop_url = ?, updated_at = datetime('now')
                    WHERE trakt_id = ?
                """, (
                    images.get("poster_url"),
                    images.get("backdrop_url"),
                    row["trakt_id"],
                ))
                conn.commit()
                conn.close()
                success += 1
                print(f"    ✓ poster: {images['poster_url'][:60]}...")
            else:
                fail += 1
                print(f"    ✗ 未找到图片")
        except Exception as e:
            fail += 1
            print(f"    ✗ 错误: {e}")

        time.sleep(0.3)

    print(f"\n[Backfill] 完成！成功 {success}，失败 {fail}，共 {total}")


if __name__ == "__main__":
    run()
