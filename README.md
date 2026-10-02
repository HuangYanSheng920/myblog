# tiny-blog

一个极简的 Python 静态博客生成器：Markdown 写作 → 一键生成静态站点 → 本地预览 / 随便部署。

## 依赖

只需 Python 3.11+（用到 `tomllib`）和 `markdown`：

```powershell
pip install -r requirements.txt
```

## 用法

```powershell
# 新建一篇文章
python new_post.py "我的第一篇文章" --tags python,教程

# 构建到 site/
python build.py

# 构建并本地预览（默认 http://127.0.0.1:8000）
python build.py --serve

# 换端口 / 清空重建 / 包含草稿
python build.py --serve --port 5000
python build.py --clean
python build.py --drafts
```

## 目录结构

```
myblog/
├── site.toml          # 站点配置（标题、作者、目录等）
├── build.py           # 生成器
├── new_post.py        # 新建文章脚手架
├── posts/             # 文章（Markdown + front matter）
├── templates/         # HTML 模板
├── static/            # CSS/图片等静态资源
└── site/              # 构建输出（已 gitignore）
```

## Front matter

每篇文章开头用 `---` 包裹元数据：

```markdown
---
title: 文章标题
date: 2026-10-02
tags: [python, web]
summary: 一句话摘要，列表和 RSS 会用到
draft: false        # true 时默认不构建，需 --drafts
---
```

## 部署

`site/` 是纯静态文件，可直接：

- 本地长期运行：`python -m http.server 8000 --directory site`
- 任意静态托管：GitHub Pages / Cloudflare Pages / Vercel / 对象存储
- 自建 Nginx：把 root 指向 `site/` 目录

若部署在子路径（如 `https://x.github.io/blog/`），在 `site.toml` 里把
`base_url` 改成该路径即可（默认空字符串表示相对路径）。

### GitHub Pages（已内置自动部署）

仓库里的 `.github/workflows/deploy.yml` 会在每次 push 到 `main` 时自动
构建并发布。只需：

1. 推送源码到 GitHub 的 `main` 分支
2. 仓库 **Settings → Pages → Source** 选 **GitHub Actions**
3. 等 Actions 跑完，访问 `https://<用户名>.github.io/<仓库名>/`

**说明**：页面之间全部使用**相对路径**，所以放在任何子路径或根路径都能正常工作，
不需要额外配置。`site.toml` 里的 `base_url` 只影响 RSS 中的绝对链接，
填成站点的完整地址即可（如 `https://<用户名>.github.io/<仓库名>`）。

## 自定义

- 改外观：编辑 `static/style.css`（含亮/暗色模式变量）
- 改结构：编辑 `templates/base.html`
- 加 Markdown 语法：在 `build.py` 的 `MD_EXTENSIONS` 里加插件
