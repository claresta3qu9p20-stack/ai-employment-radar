#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 summary.json 渲染成竖屏长页 HTML。

用法:
    python render.py <summary.json> <输出.html>

模板与样式在 ../assets/ 下：
    assets/style.css    页面样式（两份页面共用）
    assets/page.html    单份摘要页骨架
改版式只需改这两个文件，不必动本脚本。
"""
import html
import json
import sys
from pathlib import Path
from string import Template

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=False)


def clean_note(s):
    """把啰嗦的页码说明压成短标签。"""
    s = str(s or "").strip()
    if not s:
        return ""
    s = s.replace("PDF 文件页序；", "").replace("PDF 文件页序", "")
    s = s.replace("印刷页码 ", "印刷 ").replace("；", " · ")
    s = s.replace("，", " · ")
    return s.strip(" ·")


def load_template(name):
    path = ASSETS / name
    if not path.exists():
        raise SystemExit("找不到模板 %s。scripts/ 与 assets/ 必须一起搬运，不能只拷脚本。" % path)
    return path.read_text(encoding="utf-8")


def render(data):
    css = load_template("style.css")
    tpl = Template(load_template("page.html"))

    meta = data.get("meta", {})
    r = data.get("reasoning", {}) or {}

    points_html = []
    for i, p in enumerate(data.get("points", []) or [], 1):
        note = clean_note(p.get("page_note"))
        tail = "　·　" + note if note else ""
        quote = p.get("quote")
        quote_html = (
            '<details><summary>原文摘句</summary><div class="q">%s</div></details>' % esc(quote)
            if quote else ""
        )
        points_html.append(
            '<div class="point"><div class="n">%02d　p.%s%s</div>'
            '<div class="t">%s</div>%s</div>'
            % (i, esc(p.get("page", "")), esc(tail), esc(p.get("text")), quote_html)
        )

    steps_html = []
    for key, label in (("premise", "前提"), ("mechanism", "机制"),
                       ("evidence", "证据"), ("conclusion", "结论")):
        s = r.get(key) or {}
        if not s.get("text"):
            continue
        steps_html.append(
            '<div class="step"><div class="h">%s</div><div class="t">%s</div>'
            '<div class="p">%s</div></div>'
            % (label, esc(s.get("text")), esc(s.get("page_note") or ("p.%s" % s.get("page", ""))))
        )

    lims = "".join("<li>%s</li>" % esc(x) for x in (data.get("limitations") or [])) \
        or "<li>原文未提供局限性说明</li>"
    adds = "".join('<div class="add">%s</div>' % esc(x) for x in (data.get("additions") or []))

    details = ""
    susp = data.get("suspicious") or []
    if susp:
        rows = "".join("<div>· %s（%s）</div>" % (esc(s.get("text")), esc(s.get("reason"))) for s in susp)
        details = ('<details><summary>可疑句清单（机器三测试命中，供核对）</summary>'
                   '<div class="body">%s</div></details>' % rows)

    date, pages = meta.get("date"), meta.get("pages")
    if date and pages:
        date_line = "%s　共 %s 页" % (esc(date), esc(pages))
    else:
        date_line = esc(date) or "报告未提供"

    return tpl.substitute(
        css=css,
        title=esc(data.get("title")) or "未命名报告",
        title_zh=esc(data.get("title_zh")),
        type=esc(meta.get("type")) or "类型待核",
        author=esc(meta.get("author")) or "报告未提供",
        institution=esc(meta.get("institution")) or "报告未提供",
        date_line=date_line,
        url_line=esc(meta.get("url")) or "报告未提供",
        brief=esc(data.get("source_brief")),
        points="".join(points_html),
        notice=esc(r.get("notice")),
        steps="".join(steps_html),
        limitations=lims,
        additions=adds,
        details=details,
    )


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    out = render(data)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成 %s（%.1f KB）" % (sys.argv[2], len(out.encode("utf-8")) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
