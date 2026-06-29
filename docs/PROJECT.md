# traktDaily — 项目工程文档

> 自动化观影数据可视化站点，基于 Trakt API 抓取观影历史，生成 GitHub Pages 前端展示页，含 LLM（DeepSeek）驱动的观影人格画像分析。

---

## 项目架构

```
traktDaily/                    # 公开仓库（代码 + CI 配置，不含数据）
├── .github/workflows/
│   ├── fetch.yml              # 每 2h 增量抓取 Trakt 数据
│   └── deploy.yml             # 构建前端 → 部署到 GitHub Pages
├── scripts/                   # Python 后端脚本
│   ├── config.py              # 环境变量 / 路径 / LLM 配置
│   ├── db.py                  # SQLite 封装（建表、CRUD、聚合查询）
│   ├── fetch.py               # Trakt API 抓取主入口（增量 + TMDB 海报）
│   ├── tmdb.py                # TMDB API 封装
│   ├── render.py              # 生成前端 JSON 数据文件
│   ├── persona.py             # 观影人格画像（LLM + 规则引擎降级）
│   └── backfill_posters.py    # TMDB 海报补全回填工具
├── web/                       # Vue 3 + Vite 前端
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── style.css
│       ├── composables/
│       │   ├── useTraktData.js   # 数据加载 & 状态管理
│       │   └── useEcharts.js     # ECharts 生命周期管理
│       ├── utils/
│       │   ├── genres.js         # 类型颜色 / 中文翻译
│       │   └── format.js         # 日期/分钟格式化
│       └── components/           # 各版块组件
│           ├── HeroIntro.vue
│           ├── TotalStats.vue
│           ├── PersonaSection.vue   # ★ 观影人格画像展示
│           ├── MonthlyJourney.vue
│           ├── TopWatched.vue
│           ├── GenreSection.vue
│           ├── HeatmapSection.vue
│           ├── LibrarySection.vue
│           ├── ClosingSection.vue
│           ├── TrendChart.vue
│           ├── TopMedia.vue
│           ├── RecentList.vue
│           ├── CalendarHeatmap.vue
│           ├── GenrePies.vue
│           ├── TypePieChart.vue
│           ├── RatingChart.vue
│           ├── YearlyCompare.vue
│           ├── TabNav.vue
│           ├── ScrollSection.vue
│           ├── HeroHeader.vue
│           ├── StatsSection.vue
│           ├── OverviewTab.vue
│           ├── HeatmapTab.vue
│           ├── ChartsTab.vue
│           └── LibraryTab.vue
├── requirements.txt           # Python 依赖
├── dev.md                     # 观影人格画像设计文档
└── docs/
    └── PROJECT.md             # 本文档
```

---

## 双仓库架构

| 仓库 | 作用 | 可见性 |
|------|------|--------|
| `shengdaozm/traktDaily` | 代码 + CI 配置 + 前端源码 | Public |
| `shengdaozm/traktData` | SQLite DB + JSON 数据文件 + persona.json | Private |

**数据文件从不进入公开仓库**（`.gitignore` 排除了 `data/` 和 `web/public/data/`），所有数据存储在私有仓库中，CI 运行时通过 `GH_PAT` 拉取和推送。

---

## 数据流

```
Trakt API (历史记录)
    │
    ▼
scripts/fetch.py         增量抓取（只取新增记录）
    │  │
    │  ▼ TMDB API         补充海报/背景图
    │  │
    ▼  ▼
data/trakt.db            SQLite（plays 表 + media 表）
    │
    ├─→ scripts/persona.py   收集统计数据 → LLM 生成人格画像
    │   └─→ persona.json     缓存 7 天
    │
    └─→ scripts/render.py    聚合查询 → 生成前端 JSON
        ├─→ summary.json
        ├─→ media.json
        ├─→ top_media.json
        ├─→ recent_meta.json
        └─→ recent_1.json ~ recent_N.json
                │
                ▼
         web/public/data/    推送至私有仓库
                │
        deploy.yml           从私有仓库拉取 → Vite 构建 → GitHub Pages
```

---

## CI/CD 调度

### fetch.yml — 每 2 小时（`0 */2 * * *`）

1. 检出公开仓库代码
2. 从私有仓库恢复 `trakt.db` + `reports/` + `web/public/data/`（含缓存的 persona.json）
3. `python -m scripts.fetch` — 增量抓取 Trakt 新记录
4. `python -m scripts.backfill_posters` — 补全 TMDB 海报
5. `python -m scripts.persona` — 生成/复用人格画像（**缓存 7 天，仅过期时调 LLM**）
6. `python -m scripts.render` — 生成前端 JSON
7. 推送数据回私有仓库
8. 若数据有变更 → 触发 `deploy.yml`

### deploy.yml — GitHub Pages 部署

- 触发源：`fetch.yml` 完成、`web/` 代码 push、手动 dispatch
- 从私有仓库拉取 `web/public/data/*` → `vite build` → 部署 Pages

---

## 核心脚本说明

### `scripts/fetch.py`
- 增量模式：读取 `plays` 表中最新 `watched_at`，只拉取此时间后的记录
- 分页抓取 Trakt `/users/:username/history`，限速 (5 req/s) 避免 429
- 写入时去重（按 `history_id` 唯一）
- 对新增媒体调用 TMDB 补全海报/背景图

### `scripts/db.py`
- 两张核心表：
  - `plays`：每次观影事件（title, year, media_type, watched_at_local, rating 等）
  - `media`：媒体详情（overview, poster_url, backdrop_url, genres, runtime 等）
- 聚合查询函数（供 persona 使用）：`get_hourly_stats`, `get_weekday_stats`, `get_binge_stats`, `get_rating_preference`, `get_country_stats`, `get_freshness_stats`, `get_watch_pattern`, `get_diversity_index`, `get_runtime_preference` 等

### `scripts/persona.py`
- 两种生成模式：
  - **LLM 模式**：`LLM_API_KEY` 已配 → 调用 DeepSeek `deepseek-chat` 生成结构化 JSON
  - **规则引擎降级**：`LLM_API_KEY` 未配或 API 失败 → 硬编码阈值规则生成
- **缓存策略**：`persona.json` 若存在且 mtime < 7 天则跳过，避免频繁调用 LLM
- 输出字段：`archetype`, `archetype_description`, `tags[]`, `radar{}`, `narrative`, `highlights[]`, `personality_traits{}`

### `scripts/render.py`
- 输出 6 类前端 JSON：`summary.json`, `media.json`, `top_media.json`, `recent_meta.json`, `recent_N.json`（分页，每页 100 条）
- 不触碰 `persona.json`

---

## 前端技术栈

- **框架**: Vue 3 (Composition API)
- **构建**: Vite 5
- **图表**: ECharts 5
- **样式**: 纯 CSS（CSS 变量 + 玻璃拟态 `glass-card` + 暗色主题）
- **数据获取**: `fetch()` 加载 `public/data/*.json`
- **核心 composable**: `useTraktData.js` — 管理全局状态，`useEcharts.js` — 管理图表实例

---

## 关键配置

### 环境变量（GitHub Secrets）

| 变量 | 用途 |
|------|------|
| `TRAKT_CLIENT_ID` | Trakt API 认证 |
| `TRAKT_USERNAME` | Trakt 用户名 |
| `TMDB_API_KEY` | TMDB 海报/元数据 |
| `GH_PAT` | 私有仓库 `traktData` 读写 |
| `LLM_API_KEY` | DeepSeek API Key（可选，不配则规则引擎） |
| `LLM_API_BASE` | LLM API 地址（默认 `https://api.deepseek.com/v1`） |
| `LLM_MODEL` | 模型名（默认 `deepseek-chat`） |

### `scripts/config.py` 关键常量

```python
TRAKT_PAGE_LIMIT = 100       # 每页记录数
PERSONA_CACHE_DAYS = 7        # 人格画像缓存天数
```

---

## 本地开发

```bash
# Python
pip install -r requirements.txt
python -m scripts.fetch       # 需先配环境变量
python -m scripts.persona
python -m scripts.render

# 前端
cd web
npm install
npm run dev
```

> `.env` 文件在 `.gitignore` 中，本地开发需自行创建。

---

## 相关文档

- `dev.md` — 观影人格画像功能的详细设计文档（维度定义、标签规则、LLM prompt 设计）
