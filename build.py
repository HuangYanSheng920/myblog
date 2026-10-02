#!/usr/bin/env python3
"""tiny-blog —— 一个极简的 Python 静态博客生成器。

用法:
    python build.py                 # 构建到 site/
    python build.py --serve         # 构建并启动本地预览服务器
    python build.py --clean         # 构建前清空输出目录
    python build.py --drafts        # 把草稿也一起构建

只依赖标准库 + markdown。
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 markdown，请先运行: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"

MD_EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists", "attr_list", "md_in_html"]


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    with (ROOT / "site.toml").open("rb") as f:
        return tomllib.load(f)


def parse_front_matter(text: str) -> tuple[dict, str]:
    """解析 --- 包裹的简易 front matter，返回 (meta, body)。"""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    _, raw, body = parts

    meta: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("'\"") for v in value[1:-1].split(",")]
            meta[key] = [v for v in items if v]
        elif value.lower() in {"true", "false"}:
            meta[key] = value.lower() == "true"
        else:
            meta[key] = value.strip("'\"")
    return meta, body.lstrip("\n")


def slugify(name: str) -> str:
    """文件名 -> URL 友好的 slug（保留中文）。"""
    name = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", name.strip().lower())
    return re.sub(r"-{2,}", "-", name).strip("-") or "post"


def format_date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value or ""


def render(template_name: str, **context: object) -> str:
    """把模板里的 {{ key }} / {{ obj.attr }} 替换成上下文里的值。

    值不做 HTML 转义，需要转义时由调用方在拼接时处理。
    """
    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")

    def _resolve(expr: str) -> str:
        parts = expr.strip().split(".")
        value: object = context.get(parts[0], "")
        for part in parts[1:]:
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                value = getattr(value, part, "")
        return str(value)

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", lambda m: _resolve(m.group(1)), tpl)


# --------------------------------------------------------------------------- #
# 文章加载
# --------------------------------------------------------------------------- #
def load_posts(posts_dir: Path, include_drafts: bool) -> list[dict]:
    posts: list[dict] = []
    for path in sorted(posts_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        if meta.get("draft") and not include_drafts:
            continue

        slug = slugify(meta.get("slug") or path.stem)
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        title = meta.get("title") or path.stem.replace("-", " ").replace("_", " ")
        date = format_date(str(meta.get("date", "")))

        posts.append(
            {
                "slug": slug,
                "url": f"{slug}.html",
                "title": title,
                "date": date,
                "tags": tags,
                "summary": meta.get("summary", ""),
                "body_html": markdown.markdown(body, extensions=MD_EXTENSIONS),
                "source": path,
            }
        )

    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


# --------------------------------------------------------------------------- #
# 页面片段
# --------------------------------------------------------------------------- #
def render_post_card(post: dict) -> str:
    tag_html = "".join(
        f'<a class="tag" href="tags.html#{html.escape(slugify(t))}">{html.escape(t)}</a>'
        for t in post["tags"]
    )
    summary = (
        f'<p class="card-summary">{html.escape(post["summary"])}</p>'
        if post["summary"]
        else ""
    )
    return f"""<article class="card">
  <h2 class="card-title"><a href="{post['url']}">{html.escape(post['title'])}</a></h2>
  <div class="meta"><time>{post['date']}</time>{tag_html}</div>
  {summary}
</article>"""


def build_index(posts: list[dict], site: dict) -> str:
    if posts:
        cards = "\n".join(render_post_card(p) for p in posts)
    else:
        cards = '<p class="empty">还没有文章，运行 <code>python new_post.py "标题"</code> 写第一篇吧。</p>'
    return render(
        "base.html",
        page_title=site["title"],
        page_description=site["description"],
        nav_prefix="",
        content=f'<section class="post-list">\n{cards}\n</section>',
        site=site,
    )


def build_post_page(post: dict, site: dict) -> str:
    tag_html = "".join(
        f'<a class="tag" href="tags.html#{html.escape(slugify(t))}">{html.escape(t)}</a>'
        for t in post["tags"]
    )
    content = f"""<article class="post">
  <header>
    <h1>{html.escape(post['title'])}</h1>
    <div class="meta"><time>{post['date']}</time>{tag_html}</div>
  </header>
  <div class="post-body">
{post['body_html']}
  </div>
  <p class="back"><a href="index.html">← 返回首页</a></p>
</article>"""
    title = f"{post['title']} · {site['title']}"
    return render(
        "base.html",
        page_title=title,
        page_description=post["summary"] or site["description"],
        nav_prefix="",
        content=content,
        site=site,
    )


def build_tags_page(posts: list[dict], site: dict) -> str:
    grouped: dict[str, list[dict]] = {}
    for post in posts:
        for tag in post["tags"]:
            grouped.setdefault(tag, []).append(post)

    if not grouped:
        body = '<p class="empty">暂无标签。</p>'
    else:
        blocks = []
        for tag in sorted(grouped, key=lambda t: (-len(grouped[t]), t)):
            links = "\n".join(
                f'      <li><a href="{p["url"]}">{html.escape(p["title"])}</a>'
                f' <time>{p["date"]}</time></li>'
                for p in grouped[tag]
            )
            blocks.append(
                f'<section class="tag-section" id="{html.escape(slugify(tag))}">'
                f'<h2>{html.escape(tag)} <span class="count">{len(grouped[tag])}</span></h2>'
                f"<ul>\n{links}\n</ul></section>"
            )
        body = "\n".join(blocks)

    return render(
        "base.html",
        page_title=f"标签 · {site['title']}",
        page_description=f"{site['title']} 的全部标签",
        nav_prefix="",
        content=f'<h1 class="page-title">标签</h1>\n{body}',
        site=site,
    )


def build_feed(posts: list[dict], site: dict) -> str:
    base = site.get("base_url", "").rstrip("/")
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for post in posts[:20]:
        url = f"{base}/{post['url']}" if base else post["url"]
        try:
            pub = datetime.strptime(post["date"], "%Y-%m-%d").strftime(
                "%a, %d %b %Y 00:00:00 +0000"
            )
        except ValueError:
            pub = now
        items.append(
            f"""  <item>
    <title>{html.escape(post['title'])}</title>
    <link>{html.escape(url)}</link>
    <guid>{html.escape(url)}</guid>
    <pubDate>{pub}</pubDate>
    <description>{html.escape(post['summary'])}</description>
  </item>"""
        )
    home = f"{base}/index.html" if base else "index.html"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{html.escape(site['title'])}</title>
  <link>{html.escape(home)}</link>
  <description>{html.escape(site['description'])}</description>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""


# --------------------------------------------------------------------------- #
# 构建入口
# --------------------------------------------------------------------------- #
def build(args: argparse.Namespace) -> Path:
    config = load_config()
    site = {
        "title": config.get("title", "我的博客"),
        "description": config.get("description", ""),
        "author": config.get("author", ""),
        "lang": config.get("lang", "zh-CN"),
        "base_url": config.get("base_url", ""),
        "year": datetime.now().year,
    }

    posts_dir = ROOT / config.get("posts_dir", "posts")
    out_dir = ROOT / config.get("output_dir", "site")
    posts_dir.mkdir(exist_ok=True)

    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    posts = load_posts(posts_dir, include_drafts=args.drafts)

    # 静态资源
    if STATIC.exists():
        shutil.copytree(STATIC, out_dir / "static", dirs_exist_ok=True)

    # 页面
    (out_dir / "index.html").write_text(build_index(posts, site), encoding="utf-8")
    (out_dir / "tags.html").write_text(build_tags_page(posts, site), encoding="utf-8")
    (out_dir / "feed.xml").write_text(build_feed(posts, site), encoding="utf-8")
    for post in posts:
        (out_dir / post["url"]).write_text(build_post_page(post, site), encoding="utf-8")

    print(f"✓ 已生成 {len(posts)} 篇文章 -> {out_dir}")
    return out_dir


def serve(out_dir: Path, port: int) -> None:
    import functools
    import http.server
    import socketserver

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out_dir))
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"→ 本地预览: http://127.0.0.1:{port}/  (Ctrl+C 停止)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止。")


def main() -> None:
    parser = argparse.ArgumentParser(description="构建静态博客")
    parser.add_argument("--serve", action="store_true", help="构建后启动本地预览服务器")
    parser.add_argument("--port", type=int, default=8000, help="预览端口（默认 8000）")
    parser.add_argument("--clean", action="store_true", help="构建前清空输出目录")
    parser.add_argument("--drafts", action="store_true", help="包含草稿")
    args = parser.parse_args()

    out_dir = build(args)
    if args.serve:
        serve(out_dir, args.port)


if __name__ == "__main__":
    main()
