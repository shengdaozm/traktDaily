# Trakt 用户画像 + 剧集打分推荐 + 偏差校正系统
## 新增模块说明

### 数据库新表（db.py 自动创建）
- **user_ratings** — 用户显式评分（1-10 分）
- **cast_crew** — 演员/导演映射
- **cast_preference** — 演员偏好缓存（celebrity_bonus 计算结果）
- **user_profile** — 9 维画像缓存

### 新增脚本
| 脚本 | 用途 | 依赖 |
|------|------|------|
| `fetch_ratings.py` | 从 Trakt 拉取用户评分 | TRAKT_CLIENT_ID, TRAKT_USERNAME |
| `fetch_cast.py` | 从 TMDB 拉取演员/导演数据 | TMDB_API_KEY |
| `profile_builder.py` | 构建 9 维用户画像 | SQLite |
| `scoring_engine.py` | 新剧打分引擎（0-100 分） | SQLite |
| `bias_correction.py` | 演员偏差检测与校正 | SQLite |
| `render_profile.py` | 画像/推荐 JSON 生成 | 以上所有 |

### 输出 JSON（web/public/data/）
- `profile.json` — 完整用户画像
- `bias_report.json` — 偏差检测报告
- `cast_preferences.json` — 演员偏好列表
- `recommendations.json` — 新剧推荐（含打分拆解）

### CI 集成
- `fetch.yml` 新增「抓取用户评分」和「抓取演员数据」两个步骤
- `render.py` 的 `run()` 末尾自动调用 `render_profile.run()`

### 配置
- `PROFILE_REBUILD_THRESHOLD = 5`（评分 ≥ 5 部时强制重建画像）
- 已有 LLM_API_KEY / LLM_API_BASE / LLM_MODEL 用于画像分析
