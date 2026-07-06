"""
项目配置文件
-----------
从环境变量读取 API 密钥，定义数据目录路径和 Trakt/TMDB API 基础 URL。
"""

import os

# ── Trakt API 配置 ─────────────────────────────────────────
# 从环境变量读取，GitHub Actions 中通过 Secrets 注入
TRAKT_CLIENT_ID = os.environ.get("TRAKT_CLIENT_ID", "")
# Trakt 用户名，用于查询公开观影历史（无需 OAuth）
TRAKT_USERNAME = os.environ.get("TRAKT_USERNAME", "")
# Trakt API v2 基础地址
TRAKT_BASE_URL = "https://api.trakt.tv"
# 每页数据量，Trakt 默认 10，最大可按需调整
TRAKT_PAGE_LIMIT = 100

# ── TMDB API 配置 ──────────────────────────────────────────
# TMDB API Key，用于获取海报、背景图、元数据
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
# TMDB API v3 基础地址
TMDB_BASE_URL = "https://api.themoviedb.org/3"
# TMDB 图片 CDN 基础地址，拼接 poster_path 即可得到完整海报 URL
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
# TMDB API 请求语言，zh-CN 优先获取中文元数据
TMDB_LANG = "zh-CN"

# ── 本地数据路径 ───────────────────────────────────────────
# 项目根目录（脚本所在目录的上一级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SQLite 数据库文件路径
DB_PATH = os.path.join(PROJECT_ROOT, "data", "trakt.db")
# 用户评分数据（手动维护的 JSON 文件）
USER_RATINGS_PATH = os.path.join(PROJECT_ROOT, "data", "user_ratings.json")
# 报告 JSON 输出目录
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "reports")
# 前端 JSON 数据目录
WEB_DATA_DIR = os.path.join(PROJECT_ROOT, "web", "public", "data")

# ── 大模型配置 ─────────────────────────────────────────────
# 用于生成观影人格画像分析
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
# persona.json 缓存天数，避免每次都调用大模型
PERSONA_CACHE_DAYS = 7

# ── 画像构建配置 ──────────────────────────────────────────
# 用户评分数达到此阈值时，强制重建画像（确保画像质量）
PROFILE_REBUILD_THRESHOLD = 5
# 画像版本号，表结构变更时递增
PROFILE_VERSION = "2.0"