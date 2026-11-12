#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从报告详情页解析并下载 PDF，校验文件头，计算指纹，写 meta.json。

用法:
    python fetch_pdf.py <页面URL> <目标目录>

成功时在目标目录写入 raw.pdf 与 meta.json，并把一行追加到
<目标目录>/../manifest.jsonl。
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
# NBER 的 10MB 级论文在慢速网络下要 80 秒以上，60 秒会被自己掐断。
TIMEOUT = 180


def get(url, referer=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type", "")


def find_pdf_links(html, base):
    """页面里所有 .pdf 链接，处理相对路径与二次编码。"""
    found = []
    for m in re.finditer(r'(?:href|src|content)\s*=\s*["\']([^"\']+?\.pdf[^"\']*)["\']', html, re.I):
        raw = m.group(1)
        for candidate in (raw, raw.replace("%25", "%")):
            url = urllib.parse.urljoin(base, candidate)
            if url not in found:
                found.append(url)
    return found


def guess_nber(url):
    """NBER 论文页可用编号拼出 PDF 直链，作为兜底。"""
    m = re.search(r'/papers/(w\d+)', url)
    if m:
        wid = m.group(1)
        return "https://www.nber.org/system/files/working_papers/%s/%s.pdf" % (wid, wid)
    return None


def download_pdf(url, referer):
    try:
        body, final, ctype = get(url, referer)
    except Exception as e:
        return None, "请求失败: %s" % e
    if body[:4] != b"%PDF":
        return None, "返回内容不是 PDF（%s，%d 字节）" % (ctype or "未知类型", len(body))
    return (body, final), None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    page_url, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    page_html = ""
    try:
        body, final_page, _ = get(page_url)
        page_html = body.decode("utf-8", "ignore")
        page_url_final = final_page
    except Exception as e:
        page_url_final = page_url
        print(json.dumps({"ok": False, "stage": "page", "error": str(e)}, ensure_ascii=False))

    candidates = []
    if page_html:
        candidates = find_pdf_links(page_html, page_url_final)
    nber = guess_nber(page_url)
    if nber and nber not in candidates:
        candidates.append(nber)

    tried = []
    got = None
    t0 = time.time()
    for url in candidates[:8]:
        res, err = download_pdf(url, page_url_final)
        tried.append({"url": url, "error": err})
        if res:
            got = (url, res[0])
            break
    elapsed = round(time.time() - t0, 1)

    if not got:
        print(json.dumps({"ok": False, "stage": "download", "tried": tried,
                          "hint": "自动下载失败，请手动把 PDF 放进 inbox/"}, ensure_ascii=False, indent=2))
        return 3

    pdf_url, blob = got
    raw_path = os.path.join(out_dir, "raw.pdf")
    with open(raw_path, "wb") as f:
        f.write(blob)
    sha = hashlib.sha256(blob).hexdigest()

    meta_path = os.path.join(out_dir, "meta.json")
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}
    meta.update({
        "pdf_url": pdf_url,
        "source_page": page_url_final,
        "sha256": sha,
        "bytes": len(blob),
        "download_seconds": elapsed,
        "fetched_at": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    manifest = os.path.join(os.path.dirname(os.path.abspath(out_dir)), "manifest.jsonl")
    row = {"dir": os.path.basename(os.path.abspath(out_dir)), "sha256": sha,
           "bytes": len(blob), "pdf_url": pdf_url, "fetched_at": meta["fetched_at"]}
    with open(manifest, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "raw": raw_path, "sha256": sha, "bytes": len(blob),
                      "download_seconds": elapsed, "pdf_url": pdf_url, "tried": tried},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
