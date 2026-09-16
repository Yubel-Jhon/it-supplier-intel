"""第 2b 步:structured.json -> verified.json。白名单/转载/域名核验。纯标准库。"""
import json
import os
import sys
from datetime import date
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_sources, DATA_DIR  # noqa: E402


def domain_of(url):
    try:
        return urlparse(url).netloc.lower()
    except Exception:  # noqa: BLE001
        return ""


def main():
    cfg = load_sources()
    sources = {s["id"]: s for s in cfg.get("sources", [])}
    repost = set(cfg.get("repost_domains", []))

    today = date.today().isoformat()
    s_path = os.path.join(DATA_DIR, today, "structured.json")
    if not os.path.exists(s_path):
        print("未找到 structured.json,先跑 parse.py")
        sys.exit(1)
    recs = json.load(open(s_path, encoding="utf-8"))

    verified = []
    for rec in recs:
        src = sources.get(rec["id"], {})
        v = dict(rec)
        # 域名白名单:抓取地址的主机名必须落在 sources.yaml 该源登记的 domain 上。
        # github 源无 url(只有 repo),主机名固定 github.com;media 源无 url,不参与(标 n/a)。
        host = "github.com" if rec["type"] == "github_release" else domain_of(src.get("url", ""))
        registered = (src.get("domain") or "").lower()
        if not src:
            v["whitelist"] = "fail"          # id 不在 sources.yaml
        elif not host:
            v["whitelist"] = "n/a"           # 无 url 的源(media)不参与脚本层白名单
        else:
            v["whitelist"] = "pass" if registered in host else "fail"
        v["domain_flag"] = "unverified" if src.get("unverified_domain") else "ok"
        v["repost"] = any(rp in host for rp in repost)
        v["tier"] = src.get("tier", "unknown")
        v["needs_llm"] = (
            rec["type"] in ("official_account", "media")
            or any(x.get("needs_review") for x in rec.get("versions", []))
        )
        verified.append(v)

    out_path = os.path.join(DATA_DIR, today, "verified.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(verified, f, ensure_ascii=False, indent=2)
    flags = sum(1 for v in verified if v["repost"] or v["domain_flag"] == "unverified")
    print(f"verify 完成: {len(verified)} 源, 红旗 {flags} 条 -> {out_path}")


if __name__ == "__main__":
    main()
