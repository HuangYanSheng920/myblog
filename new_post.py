#!/usr/bin/env python3
"""创建一篇新文章。

用法:
    python new_post.py "我的标题"
    python new_post.py "我的标题" my-slug
    python new_post.py "我的标题" --tags python,web --summary "一句话摘要"
"""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TEMPLATE = """---
title: {title}
date: {date}
tags: [{tags}]
summary: {summary}
draft: false
---

在这里写正文（Markdown）。

## 小标题

- 要点一
- 要点二
"""


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower())
    return re.sub(r"-{2,}", "-", text).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description="创建一篇新文章")
    parser.add_argument("title", help="文章标题")
    parser.add_argument("slug", nargs="?", help="文件名 slug（默认由标题生成）")
    parser.add_argument("--tags", default="", help="逗号分隔的标签")
    parser.add_argument("--summary", default="", help="文章摘要")
    args = parser.parse_args()

    slug = args.slug or slugify(args.title) or "post"
    posts_dir = ROOT / "posts"
    posts_dir.mkdir(exist_ok=True)

    path = posts_dir / f"{slug}.md"
    if path.exists():
        raise SystemExit(f"文件已存在：{path}")

    path.write_text(
        TEMPLATE.format(
            title=args.title,
            date=date.today().isoformat(),
            tags=args.tags,
            summary=args.summary,
        ),
        encoding="utf-8",
    )
    print(f"✓ 已创建 {path}")
    print("  写完运行：python build.py --serve")


if __name__ == "__main__":
    main()
