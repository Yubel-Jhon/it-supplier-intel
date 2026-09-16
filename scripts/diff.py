"""第 3 步:verified.json vs baseline.json -> delta.json(增量)。纯标准库。"""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, BASELINE_FILE, LATEST_DELTA_FILE  # noqa: E402


def latest_version(rec):
    """取某源解析出的最新版本(第一条例证)。"""
    vs = rec.get("versions") or []
    if not vs:
        return None, None
    top = vs[0]
    return top.get("version"), top.get("published_at") or top.get("title") or ""


def main():
    today = date.today().isoformat()
    v_path = os.path.join(DATA_DIR, today, "verified.json")
    if not os.path.exists(v_path):
        print("未找到 verified.json,先跑 verify.py")
        sys.exit(1)
    recs = json.load(open(v_path, encoding="utf-8"))

    if not os.path.exists(BASELINE_FILE):
        print("未找到 baseline.json")
        sys.exit(1)
    base = json.load(open(BASELINE_FILE, encoding="utf-8"))
    base_products = base.get("products", {})

    delta = []
    for rec in recs:
        if rec.get("status") != "ok":
            continue
        product = rec.get("product")
        ver, date_str = latest_version(rec)
        if not ver:
            continue
        # 基线按源 id 对齐(不是 product 显示名),避免「阿里云百炼 vs 百炼」这类字符串不匹配
        known = base_products.get(rec["id"], {})
        known_ver = known.get("latest_version", "")
        if ver != known_ver:
            delta.append({
                "product": product,
                "id": rec["id"],
                "category": rec.get("category", ""),
                "channel": rec.get("channel", ""),
                "type": rec["type"],
                "old_version": known_ver,
                "new_version": ver,
                "date": date_str,
                "tier": rec.get("tier"),
                "repost": rec.get("repost"),
                "domain_flag": rec.get("domain_flag"),
                "versions": rec.get("versions", []),
            })

    out_path = os.path.join(DATA_DIR, today, "delta.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(delta, f, ensure_ascii=False, indent=2)
    # 同步一份 lightweight 的 data/latest_delta.json(data/raw/ 被 gitignore,这个才入库)
    with open(LATEST_DELTA_FILE, "w", encoding="utf-8") as f:
        json.dump(delta, f, ensure_ascii=False, indent=2)
    print(f"diff 完成: {len(delta)} 条增量 -> {out_path}")
    print(f"  同步 lightweight -> {LATEST_DELTA_FILE}")
    if not delta:
        print("无增量,可静默结束")


if __name__ == "__main__":
    main()
