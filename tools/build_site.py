#!/usr/bin/env python3
"""Build GitHub Pages site from 正文 markdown."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "正文"
OUT = ROOT / "docs"
CH_OUT = OUT / "ch"

CN = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

NSFW = {9, 10, 11, 12, 34, 35, 36, 37, 38}

VOLUMES = [
    ("卷一 · 澜港", 1, 14),
    ("卷二 · 雾线", 15, 26),
    ("卷三 · 没有土的塔", 27, 39),
]


def cn_to_int(s: str) -> int:
    s = s.strip()
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN.get(s[1:], 0)
    if "十" in s:
        a, b = s.split("十", 1)
        return CN[a] * 10 + (CN.get(b, 0) if b else 0)
    return CN[s]


def parse_filename(name: str) -> tuple[int, str]:
    m = re.match(r"第(.+?)章[·\-—－]?(.*)\.md$", name)
    if not m:
        raise ValueError(name)
    num = cn_to_int(m.group(1))
    title = m.group(2).strip(" ·-—－")
    return num, title


def md_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


def md_to_html(src: str) -> str:
    lines = src.splitlines()
    out: list[str] = []
    buf: list[str] = []

    def flush():
        if not buf:
            return
        para = "".join(buf).strip()
        buf.clear()
        if not para:
            return
        if para == "·":
            out.append('<p class="scene">·</p>')
            return
        out.append(f"<p>{md_inline(para)}</p>")

    for line in lines:
        raw = line.rstrip()
        if raw.startswith("# "):
            flush()
            continue
        if raw.startswith("## "):
            flush()
            t = md_inline(raw[3:].strip())
            out.append(f"<h2>{t}</h2>")
            continue
        if not raw:
            flush()
            continue
        buf.append(raw)
    flush()
    return "\n".join(out)


TPL_HEAD = """<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="如月风铃 · 长夜钟">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/style.css">
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<div class="fog" aria-hidden="true"></div>
"""

TPL_FOOT = """
<script src="{root}app.js"></script>
</body>
</html>
"""


def write(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def build() -> None:
    files = sorted(SRC.glob("第*章*.md"))
    chapters = []
    for f in files:
        num, title = parse_filename(f.name)
        body_md = f.read_text(encoding="utf-8")
        # strip first heading
        body_md = re.sub(r"^# .+\n+", "", body_md)
        chapters.append(
            {
                "num": num,
                "title": title,
                "file": f"ch/{num:02d}.html",
                "nsfw": num in NSFW,
                "html": md_to_html(body_md),
            }
        )
    chapters.sort(key=lambda c: c["num"])

    OUT.mkdir(parents=True, exist_ok=True)
    CH_OUT.mkdir(parents=True, exist_ok=True)

    # index
    vol_html = []
    for vname, a, b in VOLUMES:
        items = []
        for c in chapters:
            if a <= c["num"] <= b:
                tag = '<span class="tag">NSFW</span>' if c["nsfw"] else ""
                items.append(
                    f'<li><a href="{c["file"]}" data-nsfw="{str(c["nsfw"]).lower()}">'
                    f'<span class="n">{c["num"]:02d}</span>'
                    f'<span class="t">第{c["num"]}章 · {c["title"]}</span>{tag}</a></li>'
                )
        vol_html.append(
            f'<section class="vol"><h2>{vname}</h2><ol>{"".join(items)}</ol></section>'
        )

    index = TPL_HEAD.format(title="如月风铃 · 长夜钟", root="")
    index += f"""
<header class="hero">
  <p class="kicker">Kisaragi Fuurin</p>
  <h1>长夜钟</h1>
  <p class="lead">声音不会消失，只会变淡。而铃，能把它留住。</p>
  <p class="meta">如月风铃 · 三十九章</p>
</header>
<main class="toc">
{''.join(vol_html)}
<p class="note">第九至十二章、第三十四至三十八章含成人内容。进入前会询问一次。</p>
</main>
<footer class="site-foot">愿声音能带来，一点点温柔的夜晚。</footer>
"""
    index += TPL_FOOT.format(root="")
    write(OUT / "index.html", index)

    nmap = {c["num"]: c for c in chapters}
    for i, c in enumerate(chapters):
        prev = chapters[i - 1] if i else None
        nxt = chapters[i + 1] if i + 1 < len(chapters) else None
        prev_l = (
            f'<a href="{prev["num"]:02d}.html">← {prev["num"]:02d} {prev["title"]}</a>'
            if prev
            else '<a href="../index.html">← 目录</a>'
        )
        next_l = (
            f'<a href="{nxt["num"]:02d}.html">{nxt["num"]:02d} {nxt["title"]} →</a>'
            if nxt
            else '<a href="../index.html">目录 →</a>'
        )
        warn = " nsfw" if c["nsfw"] else ""
        page = TPL_HEAD.format(
            title=f"第{c['num']}章 · {c['title']} — 长夜钟", root="../"
        )
        page += f"""
<nav class="top">
  <a href="../index.html">长夜钟</a>
  <span>第{c['num']}章</span>
</nav>
<main class="read{warn}" data-nsfw="{str(c['nsfw']).lower()}">
  <header class="ch-head">
    <p class="kicker">第{c['num']:02d}章</p>
    <h1>{c['title']}</h1>
  </header>
  <article>
{c['html']}
  </article>
  <nav class="pager">{prev_l}{next_l}</nav>
</main>
"""
        page += TPL_FOOT.format(root="../")
        write(CH_OUT / f"{c['num']:02d}.html", page)

    (OUT / "chapters.json").write_text(
        json.dumps(
            [{"num": c["num"], "title": c["title"], "nsfw": c["nsfw"]} for c in chapters],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"built {len(chapters)} chapters → {OUT}")


if __name__ == "__main__":
    build()
