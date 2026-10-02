---
title: 你好，世界
date: 2026-10-02
tags: [随笔, 公告]
summary: 这是用 tiny-blog 生成的第一篇文章，介绍一下这个博客怎么用。
---

欢迎来到 **我的博客**。这个站点由 `build.py` 从 Markdown 生成，没有前端框架，只有一个依赖 `markdown`。

## 引用与列表

> 写作是最好的思考方式。

- 文章放在 `posts/` 目录，一个 `.md` 一个页面
- 头部 `---` 之间是元数据（标题、日期、标签、摘要）
- 写完运行 `python build.py` 就能生成静态页面

## 一段代码

```python
def greet(name: str) -> str:
    return f"你好，{name}！"

print(greet("世界"))
```

## 一个表格

| 功能 | 是否支持 |
| --- | --- |
| Markdown | ✅ |
| 代码高亮 | ✅（基础） |
| 标签 | ✅ |
| RSS | ✅ |

> 引用块也很好看。

开始写你自己的文章吧：`python new_post.py "标题"`。
