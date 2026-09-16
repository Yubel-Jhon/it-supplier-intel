"""第 2a 步:raw.json -> structured.json。解析成可 diff 的条目。纯标准库。"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR  # noqa: E402


def parse_github(rec):
    """GitHub release JSON -> 结构化版本条目。"""
    out = []
    for rel in rec.get("data", []):
        out.append({
            "version": rel.get("tag_name"),
            "published_at": (rel.get("published_at") or "")[:10],
            "title": rel.get("name") or rel.get("tag_name"),
            "body": (rel.get("body") or "")[:2000],
        })
    return out


def parse_rss(html):
    root = ET.fromstring(html)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        link = (item.findtext("link") or "").strip()
        out.append({"version": title, "published_at": pub, "title": title, "link": link})
    return out


def parse_changelog_html(html):
    """通用 changelog 页解析:去标签,抓以版本号开头的行。最佳努力,留 LLM 复核。
    锚定行首(可选 v 前缀)过滤页面标题/「下载 vX」/「Release vX」/纯日期等噪声。"""
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    out = []
    seen = set()
    ver_re = re.compile(r"^v?\d+(?:\.\d+){1,3}")
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 300:
            continue
        if not ver_re.match(line):
            continue
        if line in seen:
            continue
        seen.add(line)
        out.append({"version": line[:120], "title": line[:120], "needs_review": True})
    return out[:60]  # 上限防爆


def main():
    today = date.today().isoformat()
    raw_path = os.path.join(DATA_DIR, today, "raw.json")
    if not os.path.exists(raw_path):
        print("未找到 raw.json,先跑 fetch.py")
        sys.exit(1)
    recs = json.load(open(raw_path, encoding="utf-8"))

    structured = []
    for rec in recs:
        entry = {"id": rec["id"], "product": rec["product"], "category": rec.get("category", ""),
                 "channel": rec.get("channel", ""), "type": rec["type"],
                 "status": rec["status"], "versions": []}
        if rec["status"] != "ok":
            structured.append(entry)
            continue
        t = rec["type"]
        try:
            if t == "github_release":
                entry["versions"] = parse_github(rec)
            elif t == "rss":
                entry["versions"] = parse_rss(rec["html"])
            elif t == "changelog_html":
                entry["versions"] = parse_changelog_html(rec["html"])
            else:
                entry["versions"] = []  # official_account 正文抓不到,等 LLM
        except Exception as e:  # noqa: BLE001
            entry["parse_error"] = str(e)
        if not entry["versions"] and rec["status"] == "ok" and t in ("changelog_html", "rss", "github_release"):
            print(f"  警告: {rec['id']} ({rec['product']}) 抓取成功但解析出 0 条版本(无 semver 版本号或 JS 渲染),需 LLM 补盲区")
        structured.append(entry)

    out_path = os.path.join(DATA_DIR, today, "structured.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)
    print(f"parse 完成 -> {out_path}")


if __name__ == "__main__":
    main()
