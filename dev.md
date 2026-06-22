# 数据私有化改造计划

## 目标

将 `data/trakt.db` 从公开仓库迁移到私有仓库，流程和触发仍在公开仓库，数据存储到私有仓库。

## 当前架构

```
公开仓库 (traktDaily)
├── fetch.yml          → 抓取数据 → 写入 data/trakt.db → commit & push 到公开仓库
├── deploy.yml         → 读 data/trakt.db → render.py 生成 web/data/*.json → GitHub Pages
└── data/trakt.db      → 被提交到公开仓库 ❌
```

## 目标架构

```
公开仓库 (traktDaily)                                    私有仓库 (traktDaily-data)
┌──────────────────────────────────────────┐         ┌──────────────────────────┐
│ fetch.yml                                │         │                          │
│  ① git clone 私有仓库 → 拿到            │         │  data/trakt.db           │
│     data/trakt.db（增量基准）             │         │  data/reports/           │
│  ② python fetch.py → 增量抓取           │         │                          │
│  ③ git push data/trakt.db → 私有仓库    │  ──>    │  🔒 完全私有             │
│  ④ python render.py → web/data/*.json   │         │                          │
│  ⑤ git push web/data/*.json → 公开仓库  │         └──────────────────────────┘
│                                          │
│ deploy.yml（不变）                        │
│  → 部署 web/ 到 GitHub Pages             │
└──────────────────────────────────────────┘
```

## 数据流

```
cron 每2小时触发公开仓库 fetch.yml
        │
        ├── git clone 私有仓库 (用 PAT) → 获得 data/trakt.db
        ├── python fetch.py 增量抓取 → 更新 data/trakt.db
        ├── git push data/trakt.db → 私有仓库 🔒
        ├── python render.py → 生成 web/data/*.json
        └── git push web/data/*.json → 公开仓库 → 触发 deploy.yml → GitHub Pages
```

## 实施步骤

### 1. 创建私有仓库

- 创建私有仓库 `traktDaily-data`
- 将当前 `data/trakt.db` 及 `data/reports/` 迁移到私有仓库
- 私有仓库只需要 `data/` 目录，不需要 scripts 和 web

### 2. 配置 GitHub PAT

在公开仓库 `traktDaily` 的 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 |
|--------|------|
| `GH_PAT` | 具有私有仓库 `traktDaily-data` 读写权限的 Personal Access Token |

### 3. 修改 fetch.yml

```yaml
# 新增步骤：
# ① 拉取私有仓库数据（增量基准）
- name: 拉取私有仓库数据
  run: |
    git clone https://x-access-token:${{ secrets.GH_PAT }}@github.com/<用户名>/traktDaily-data.git /tmp/data-repo
    cp /tmp/data-repo/data/trakt.db data/trakt.db
    cp -r /tmp/data-repo/data/reports data/reports 2>/dev/null || true

# ② 执行抓取（原有步骤，不变）
- name: 抓取 Trakt 数据
  run: python -m scripts.fetch

# ③ 推送数据回私有仓库
- name: 推送数据到私有仓库
  run: |
    cp data/trakt.db /tmp/data-repo/data/trakt.db
    cp -r data/reports /tmp/data-repo/data/ 2>/dev/null || true
    cd /tmp/data-repo
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/
    git diff --cached --quiet || git commit -m "data: 自动更新 $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    git push

# ④ 生成前端数据（原有步骤，移到 render 中）
- name: 生成前端数据
  run: python -m scripts.render

# ⑤ 提交 JSON 到公开仓库（原有步骤，改为只提交 web/data/）
- name: 提交前端数据变更
  run: |
    git add web/data/
    if git diff --cached --quiet; then
      echo "前端数据无变更，跳过提交"
    else
      git commit -m "data: 自动更新前端数据 $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
      git push
    fi
```

### 4. 修改 deploy.yml

`deploy.yml` 不需要修改，但可移除 `scripts/render.py` 的触发条件（因为 render 已在 fetch 中执行）。

### 5. 更新 .gitignore

```gitignore
# 数据库文件不再提交到公开仓库
data/trakt.db
data/reports/
```

### 6. 清理公开仓库

- 删除 `data/trakt.db` 和 `data/reports/` 从公开仓库
- 清理 git 历史中的敏感数据

```bash
# 从 git 缓存中移除
git rm --cached data/trakt.db
git rm --cached -r data/reports/

# 清理历史记录（可选，但推荐）
# 使用 git filter-repo 或谨慎操作
```

### 7. 删除公开仓库中的敏感数据历史

```bash
# 安装 git-filter-repo（推荐）
pip install git-filter-repo

# 从历史中移除 data/trakt.db
git filter-repo --path data/trakt.db --path data/reports/ --force
```

## 变更文件清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `.github/workflows/fetch.yml` | 修改 | 新增 clone 私有仓库、push 数据到私有仓库 |
| `.github/workflows/deploy.yml` | 修改 | 移除 render.py 触发条件（可选） |
| `.gitignore` | 修改 | 新增 `data/trakt.db`、`data/reports/` |
| `data/trakt.db` | 删除 | 不再提交到公开仓库 |
| `data/reports/` | 删除 | 不再提交到公开仓库 |
| 私有仓库 `traktDaily-data` | 新建 | 仅存放 `data/trakt.db` 和 `data/reports/` |

## 注意事项

1. `GH_PAT` 需要 `repo` 权限（能读写私有仓库）
2. `web/data/*.json` 仍然公开（网站需要展示数据），但原始数据库 `trakt.db` 完全私有
3. 公开仓库的 git 历史中仍可能残留 `data/trakt.db` 的内容，需要 `git filter-repo` 彻底清理
4. 首次运行时建议先手动将私有仓库的 `data/trakt.db` 复制到公开仓库本地，确保增量抓取正常