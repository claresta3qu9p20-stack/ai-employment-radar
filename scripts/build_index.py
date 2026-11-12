#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 reports/ 下所有摘要汇总成一个总目录页。

用法:
    python build_index.py <reports目录>

读取 <reports目录>/*/summary.json，按发布日期倒序分组，写出
<reports目录>/index.html。没有摘要时也照常生成一页空目录，不报错。
"""
import html
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from string import Template

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=False)


def load_template(name):
    path = ASSETS / name
    if not path.exists():
        raise SystemExit("找不到模板 %s。scripts/ 与 assets/ 必须一起搬运，不能只拷脚本。" % path)
    return path.read_text(encoding="utf-8")


def collect(reports_dir):
    """收集每份摘要的关键信息，坏文件跳过并记录。"""
    items, broken = [], []
    for sub in sorted(p for p in reports_dir.iterdir() if p.is_dir()):
        summary = sub / "summary.json"
        if not summary.exists():
            continue
        try:
            data = json.loads(summary.read_text(encoding="utf-8"))
        except Exception as e:
            broken.append((sub.name, str(e)))
            continue
        meta = data.get("meta", {}) or {}
        items.append({
            "dir": sub.name,
            "title": (data.get("title_zh") or data.get("title") or sub.name),
            "title_orig": data.get("title") or "",
            "institution": meta.get("institution") or "",
            "type": meta.get("type") or "类型待核",
            "date": str(meta.get("date") or ""),
            "points": len(data.get("points") or []),
            "suspicious": len(data.get("suspicious") or []),
        })
    return items, broken


def item_html(it):
    bits = []
    if it["institution"]:
        bits.append("<b>%s</b>" % esc(it["institution"]))
    bits.append(esc(it["type"]))
    if it["date"]:
        bits.append(esc(it["date"]))
    if it["points"]:
        bits.append("%d 条观点" % it["points"])
    if it["suspicious"]:
        bits.append("%d 处可疑句已标" % it["suspicious"])
    return (
        '<div class="cat-item">'
        '<a href="%s/index.html">%s</a>'
        '<div class="m">%s</div>'
        "</div>" % (esc(it["dir"]), esc(it["title"]), "　·　".join(bits))
    )


def group_html(items):
    by_month = defaultdict(list)
    for it in items:
        by_month[it["date"][:7] or "未标日期"].append(it)

    months = sorted((m for m in by_month if m != "未标日期"), reverse=True)
    if "未标日期" in by_month:
        months.append("未标日期")

    chunks = []
    for month in months:
        rows = sorted(by_month[month], key=lambda x: (x["date"], x["title"]), reverse=True)
        chunks.append(
            '<div class="cat-group"><div class="cat-month">%s</div>%s</div>'
            % (esc(month), "".join(item_html(x) for x in rows))
        )
    return "".join(chunks)


def render(items, broken):
    css = load_template("style.css")
    tpl = Template(load_template("catalog.html"))

    if not items:
        groups = ('<div class="cat-empty">还没有任何摘要。放进第一份 PDF 后跑一次，'
                  "这里就会出现第一张卡片。</div>")
        summary_line = "共 0 份"
    else:
        groups = group_html(items)
        summary_line = "共 %d 份，按发布时间倒序" % len(items)

    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    footer = "目录生成于 %s。每份摘要的页码都能回到原文，摘句为原文未改写。" % stamp
    if broken:
        footer += "<br>另有 %d 份数据读取失败未列入：%s" % (
            len(broken), "、".join(esc(b[0]) for b in broken))

    return tpl.substitute(css=css, summary_line=esc(summary_line), groups=groups, footer=footer)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    reports_dir = Path(sys.argv[1]).resolve()
    if not reports_dir.is_dir():
        print("目录不存在：%s" % reports_dir)
        return 2

    items, broken = collect(reports_dir)
    out_path = reports_dir / "index.html"
    out_path.write_text(render(items, broken), encoding="utf-8")
    print("已生成 %s（%d 份）" % (out_path, len(items)))
    for name, err in broken:
        print("  跳过 %s：%s" % (name, err))
    return 0


if __name__ == "__main__":
    sys.exit(main())
