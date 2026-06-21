# traktDaily

定时抓取 [Trakt](https://trakt.tv/) 观影数据，按月聚合统计，以精美静态网页展示月度/年度观影报告。运行在 GitHub Actions 上，每 2 小时自动更新。

## 功能概览

- **自动抓取**：每 2 小时通过 GitHub Actions 定时拉取 Trakt 观影历史
- **本地数据库**：SQLite 持久化存储，支持按日期、媒体类型等快速查询
- **月度/年度报告**：自动统计观影时长、数量、类型分布、Top 作品排行
- **精美网页展示**：纯静态 HTML + Chart.js 图表，部署在 GitHub Pages
- **海报展示**：通过 TMDB API 获取影片海报和背景图
- **未来接入大模型**：自动生成月度影评总结和年度回顾文案

## 快速开始

### 1. Fork 本仓库

点击右上角 Fork 按钮，将仓库复制到你的 GitHub 账号下。

### 2. 配置 Secrets

在 Fork 后的仓库中，进入 **Settings → Secrets and variables → Actions**，添加以下 Secrets：

| Secret 名称 | 说明 | 获取方式 |
|---|---|---|
| `TRAKT_CLIENT_ID` | Trakt API 的 Client ID | [Trakt API Settings](https://trakt.tv/oauth/applications) 创建应用获取 |
| `TMDB_API_KEY` | TMDB API Key（获取海报） | [TMDB API Settings](https://www.themoviedb.org/settings/api) 申请 |

> 如果你已有 Trakt 账号，在 Trakt API 页面创建应用时选择 `urn:ietf:wg:oauth:2.0:oob` 作为 Redirect URI，然后复制 Client ID 即可。

### 3. 启用 GitHub Pages

进入 **Settings → Pages**：
- **Source**：选择 `GitHub Actions`

### 4. 开启定时任务

GitHub Actions 定时任务默认开启。如需手动触发首次运行：

1. 进入 **Actions** 标签页
2. 点击左侧 **Fetch Trakt Data**
3. 点击 **Run workflow** → **Run workflow**

首次运行后，你的观影数据会被写入 `data/trakt.db`，并自动部署网页到 `https://<你的用户名>.github.io/traktDaily/`。

## 本地开发

### 环境要求

- Python 3.10+
- Git

### 安装依赖

```bash
pip install -r requirements.txt
```

### 本地运行抓取

```bash
# 设置环境变量
export TRAKT_CLIENT_ID="你的_Client_ID"
export TMDB_API_KEY="你的_TMDB_API_Key"

# 执行抓取
python scripts/fetch.py
```

### 本地预览网页

```bash
# 生成前端 JSON 数据
python scripts/render.py

# 启动本地 HTTP 服务
python -m http.server 8080 --directory web/
```

浏览器打开 `http://localhost:8080` 即可预览。

## 项目结构

```
traktDaily/
├── .github/workflows/
│   ├── fetch.yml              # 定时抓取工作流（每 2 小时）
│   └── deploy.yml             # 前端部署工作流（GitHub Pages）
├── scripts/
│   ├── fetch.py               # 主入口：拉取 Trakt API → 写入 SQLite
│   ├── db.py                  # SQLite 封装：建表、插入、查询、聚合
│   ├── tmdb.py                # TMDB API 封装：搜索、海报下载
│   ├── stats.py               # 统计模块：月度/年度报告数据生成
│   ├── render.py              # 渲染 JSON 数据供前端消费
│   └── config.py              # 配置文件（API Key、路径等）
├── data/                      # 数据存储（随 Git 提交）
│   ├── trakt.db               # SQLite 数据库
│   └── reports/               # 统计报告 JSON
├── web/                       # 前端页面（GitHub Pages 部署目录）
│   ├── index.html             # 主页面
│   ├── data/                  # 前端 JSON 数据（deploy 时生成）
│   ├── assets/
│   │   ├── style.css          # 样式
│   │   └── posters/           # 下载的海报图片
├── dev.plan                   # 开发计划
├── requirements.txt
└── README.md
```

## 工作流程

```
每 2 小时 cron 触发
       │
       ▼
  fetch.yml 运行
       │
       ├── Python 脚本拉取 Trakt API
       ├── 写入 SQLite（去重）
       ├── 下载本次新增媒体的海报（TMDB）
       ├── 按月更新统计表
       └── 有变更 → git commit & push
                         │
                         ▼
                    deploy.yml 被触发
                         │
                         ├── render.py 生成 web/data/*.json
                         └── 部署到 GitHub Pages
```

## 未来计划

- [ ] 接入大模型，自动生成月度/年度观影视总结
- [ ] 年度 Wrapped 风格回顾页面

## License

MIT
