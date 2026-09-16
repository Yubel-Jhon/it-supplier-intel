"""第 1 步:按 sources.yaml 抓取,落盘 data/raw/<今天>/raw.json。纯标准库。"""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_sources, fetch_url, fetch_json, DATA_DIR  # noqa: E402


def fetch_github(repo):
    """直接打 GitHub API 拿最新 3 条 release(不依赖 gh CLI)。无 release 回退 tags。"""
    releases = fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=3")
    if releases:
        return releases
    tags = fetch_json(f"https://api.github.com/repos/{repo}/tags?per_page=3")
    return [
        {"tag_name": t.get("name"), "published_at": "", "name": t.get("name"), "body": ""}
        for t in tags
    ]


def main():
    cfg = load_sources()
    sources = cfg.get("sources", [])
    today = date.today().isoformat()
    outdir = os.path.join(DATA_DIR, today)
    os.makedirs(outdir, exist_ok=True)

    results = []
    for s in sources:
        if not s.get("enabled", True):
            continue
        rec = {
            "id": s.get("id"),
            "product": s.get("product"),
            "category": s.get("category", ""),
            "channel": s.get("channel", ""),
            "type": s.get("type"),
            "domain": s.get("domain"),
            "tier": s.get("tier"),
            "fetched_at": today,
            "status": "ok",
        }
        t = s.get("type")
        try:
            if t == "github_release":
                rec["data"] = fetch_github(s["repo"])
                if not rec["data"]:
                    rec["note"] = "该仓库暂无 release/tag(未打版本号)"
            elif t in ("changelog_html", "rss", "official_account"):
                # official_account 也尝试抓首页,抓不到再记 error
                rec["html"] = fetch_url(s["url"])
            elif t == "media":
                rec["status"] = "skipped"
                rec["note"] = "media 源不在此步抓,走 WebSearch(见 verify/update)"
            elif t == "ai_media":
                rec["status"] = "skipped"
                rec["product"] = s.get("name")
                rec["note"] = "AI 大事源不在此步抓,走 WebSearch(见 events)"
            else:
                rec["status"] = "error"
                rec["error"] = f"未知 type: {t}"
        except Exception as e:  # noqa: BLE001
            rec["status"] = "error"
            rec["error"] = str(e)
        results.append(rec)

    out_path = os.path.join(outdir, "raw.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    print(f"fetch 完成: {len(results)} 源, ok={ok}, error={err} -> {out_path}")


if __name__ == "__main__":
    main()
