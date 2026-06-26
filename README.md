# traktDaily

定时抓取 [Trakt](https://trakt.tv/) 观影数据，按月聚合统计，以精美静态网页展示月度/年度观影报告。运行在 GitHub Actions 上，每 2 小时自动更新。

## 架构

```
公开仓库 (traktDaily)                           私有仓库 (traktData)
┌──────────────────────────────┐       ┌──────────────────────────────┐
│ fetch.yml（每 2 小时）       │       │                              │
│  ① 拉取私有仓库数据库        │ ←─── │  data/trakt.db 🔒            │
│  ② 抓取 Trakt → 写入 SQLite  │       │  data/reports/ 🔒           │
│  ③ render.py 生成前端 JSON   │       │  web/public/data/*.json 🔒  │
│  ④ 推送数据库 + JSON 回私有库│ ───→ │                              │
│  ⑤ 触发 deploy 工作流        │       └──────────────────────────────┘
│                              │              ↑
│ deploy.yml                   │              │
│  ① 检出公开仓库代码（无数据） │              │
│  ② 从私有仓库拉取 JSON 数据  │ ─────────────┘
│  ③ npm build + 部署到 Pages  │
└──────────────────────────────┘
```

> 公开仓库不包含任何数据文件。SQLite 数据库和前端 JSON 均存储在私有仓库，deploy 时从私有仓库拉取注入构建产物。

## 技术栈

- **前端**：Vue 3 + Vite + ECharts
- **后端**：Python 3（SQLite + Trakt API + TMDB API）
- **部署**：GitHub Actions + GitHub Pages
- **架构**：双仓库（公开前端 + 私有数据）

## 功能概览

- **自动抓取**：每 2 小时通过 GitHub Actions 定时拉取 Trakt 观影历史
- **数据隐私**：SQLite 数据库存储在私有仓库，公开仓库仅包含前端页面
- **月度/年度报告**：自动统计观影时长、数量、类型分布
- **精美网页展示**：Vue 3 + ECharts，毛玻璃风格，动画流畅
- **海报展示**：通过 TMDB API 获取影片海报和背景图
- **本月概览**：实时显示当月观影统计与环比趋势
- **观影排行**：按观看次数排序的 Top 媒体卡片（横向滚动 + 左右按钮）
- **年度热力图**：支持按年度切换的观影日历热力图
- **剧库浏览**：按整部剧/电影展示，支持类型筛选与排序
- **Trakt 跳转**：标题与海报均为超链接，一键跳转 Trakt 页面
- **隐私保护**：最近观影隐藏精确时间，仅显示相对日期
- **智能部署**：仅当 `web/` 有实际变更时才触发 Pages 重建
- **人格画像**：接入 DeepSeek 大模型，分析观影行为生成人格原型、标签、雷达图、叙事文案和大五人格特质

## 快速开始

### 1. Fork 本仓库

点击右上角 Fork 按钮，将仓库复制到你的 GitHub 账号下。

### 2. 创建私有数据仓库

创建一个**私有**仓库（如 `traktData`），用于存储观影数据库。

### 3. 配置 Secrets

在 Fork 后的仓库中，进入 **Settings → Secrets and variables → Actions**，添加以下 Secrets：

| Secret 名称 | 必填 | 说明 | 获取方式 |
|---|---|---|---|
| `TRAKT_CLIENT_ID` | ✅ | Trakt API 的 Client ID | [Trakt API Settings](https://trakt.tv/oauth/applications) 创建应用获取 |
| `TRAKT_USERNAME` | ✅ | Trakt 用户名 | 你的 Trakt 账号名 |
| `TMDB_API_KEY` | ✅ | TMDB API Key（获取海报） | [TMDB API Settings](https://www.themoviedb.org/settings/api) 申请 |
| `GH_PAT` | ✅ | GitHub Personal Access Token | [GitHub Token Settings](https://github.com/settings/tokens) 创建，勾选 `repo` 权限 |
| `LLM_API_KEY` | 可选 | DeepSeek API Key（人格画像分析） | [DeepSeek Platform](https://platform.deepseek.com/) 创建 API Key |
| `LLM_API_BASE` | 可选 | 大模型 API 地址 | 默认 `https://api.deepseek.com/v1`，也可换 OpenAI 等 |
| `LLM_MODEL` | 可选 | 模型名称 | 默认 `deepseek-chat`，也可填 `gpt-4o` 等 |

> **人格画像**：`LLM_*` 为可选配置。未配置时自动降级为规则引擎生成基础版人格画像，配
> 置后由 DeepSeek 大模型生成有温度、有洞察力的深度分析。

### 4. 启用 GitHub Pages

进入 **Settings → Pages**：
- **Source**：选择 `GitHub Actions`

### 5. 开启定时任务

GitHub Actions 定时任务默认开启。如需手动触发首次运行：

1. 进入 **Actions** 标签页
2. 点击左侧 **Fetch Trakt Data**
3. 点击 **Run workflow** → **Run workflow**

首次运行后，自动部署网页到 `https://<你的用户名>.github.io/traktDaily/`。

## 本地开发

### 环境要求

- Python 3.10+
- Node.js 18+
- Git

### 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd web && npm install
```

### 本地运行抓取

```bash
# 设置环境变量
export TRAKT_CLIENT_ID="你的_Client_ID"
export TRAKT_USERNAME="你的_Trakt_用户名"
export TMDB_API_KEY="你的_TMDB_API_Key"

# 执行抓取
python scripts/fetch.py

# 生成前端 JSON 数据
python scripts/render.py
```

### 本地预览网页

```bash
cd web

# 开发模式（热更新）
npm run dev

# 或生产构建预览
npm run build && npm run preview
```

浏览器打开 `http://localhost:5173` 即可预览。

## 项目结构

```
traktDaily/（公开仓库）
├── .github/workflows/
│   ├── fetch.yml              # 定时抓取工作流（每 2 小时）
│   └── deploy.yml             # 前端构建 + 部署工作流（GitHub Pages）
├── scripts/
│   ├── fetch.py               # 主入口：拉取 Trakt API → 写入 SQLite
│   ├── db.py                  # SQLite 封装：建表、插入、查询、聚合
│   ├── tmdb.py                # TMDB API 封装：搜索、海报下载
│   ├── render.py              # 渲染 JSON 数据供前端消费
│   └── config.py              # 配置文件（API Key、路径等）
├── web/                       # Vue 3 + Vite 前端项目
│   ├── index.html             # Vite 入口
│   ├── package.json           # 前端依赖
│   ├── vite.config.js         # Vite 配置
│   ├── public/data/           # 前端 JSON 数据（render.py 生成）
│   └── src/
│       ├── main.js            # 应用入口
│       ├── App.vue            # 根组件（Tab 路由）
│       ├── style.css          # 全局样式
│       ├── composables/       # Vue Composables
│       │   ├── useTraktData.js    # 数据加载与状态管理
│       │   └── useEcharts.js      # ECharts 生命周期管理
│       ├── utils/             # 工具函数
│       │   ├── genres.js          # 类型颜色、翻译、Trakt 链接
│       │   └── format.js          # 日期、时长格式化
│       └── components/        # Vue 组件
│           ├── HeroHeader.vue     # Hero 区域
│           ├── StatsSection.vue   # 统计卡片 + 本月概览
│           ├── TabNav.vue         # Tab 导航
│           ├── OverviewTab.vue    # 概览页（趋势 + 排行 + 最近）
│           ├── HeatmapTab.vue     # 热力图页
│           ├── ChartsTab.vue      # 图表页
│           ├── LibraryTab.vue     # 剧库页（按整部剧展示）
│           ├── TrendChart.vue     # 月度趋势图
│           ├── TopMedia.vue       # 观影排行卡片
│           ├── RecentList.vue     # 最近观影列表
│           ├── CalendarHeatmap.vue # 日历热力图
│           ├── GenrePies.vue      # 类型分布饼图
│           ├── TypePieChart.vue   # 媒体类型饼图
│           ├── RatingChart.vue    # 评分分布图
│           └── YearlyCompare.vue  # 年度对比图
├── requirements.txt
└── README.md

traktData/（私有仓库，数据存储）
├── data/
│   ├── trakt.db               # SQLite 数据库
│   └── reports/               # 统计报告
└── web/
    └── public/
        └── data/              # 前端 JSON 备份
```

## 工作流程

```
每 2 小时 cron 触发
       │
       ▼
  fetch.yml 运行
       │
       ├── 从私有仓库拉取 data/trakt.db（增量基准）
       ├── Python 脚本拉取 Trakt API
       ├── 写入 SQLite（去重）
       ├── 下载新增媒体的海报（TMDB）
       ├── render.py 生成 web/public/data/*.json
       ├── 推送数据库 + 前端 JSON 到私有仓库
       └── 推送 JSON 到公开仓库（仅当有变更时）
                        │
                        ▼
                   push 触发 deploy.yml
                        │
                        ├── npm install
                        ├── npm run build（Vite 构建）
                        └── 部署 dist/ 到 GitHub Pages
```

> deploy.yml 仅在 `web/` 目录有实际文件变更并推送到 main 分支时触发，避免无数据更新时的无效重建。

## License

MIT
