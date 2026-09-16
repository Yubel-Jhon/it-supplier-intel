"""三方比价小工具:读报价 JSON -> 出比价表 + 议价点 + 合规红旗。纯标准库。
用法: python scripts/compare_quotes.py [报价.json]
缺省读 data/quotes/sample_quotes.json,输出 markdown 与 json 同目录。
只做算术和规则判定,不编造:算不出的字段标「未填」,不猜。
"""
import json
import os
import re
import sys
from datetime import date

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT = os.path.join(ROOT, "data", "quotes", "sample_quotes.json")

# 启发式评分权重(透明可调,不是"AI 打分")
W_PRICE, W_SLA, W_SUPPORT, W_COMMERCE, W_BG = 0.40, 0.20, 0.15, 0.15, 0.10
CASH_ANNUAL = 0.05  # 年化资金成本,预付年付的机会成本近似


def load(path):
    """读报价 JSON,返回 (demand, quotes)。不校验数量——校验交给调用方(CLI 退出/接口报 400)。"""
    data = json.load(open(path, encoding="utf-8"))
    return data.get("demand", {}), data.get("quotes", [])


def eff_unit_price(q):
    """折算有效单价:总价 / (席位+赠送席位) / 年限。缺字段返回 None,不猜。"""
    total = q.get("total_price")
    if total is None:
        unit, seats, years = q.get("unit_price"), q.get("seats"), q.get("years") or 1
        if unit is None or seats is None:
            return None
        total = unit * seats * years
    base = (q.get("seats") or 0) + (q.get("free_seats") or 0)
    if not base:
        return None
    return total / base / (q.get("years") or 1)


def support_score(text):
    t = (text or "") + " "
    if "7" in t and ("24" in t or "全天" in t):
        return 3
    if "工作日" in t or "工单" in t:
        return 2
    if "社区" in t:
        return 1
    return 2  # 未写明按常规支持对待,并在红旗区提示补条款


def bg_score(channel_type):
    return 3 if channel_type == "原厂" else (2 if channel_type == "代理商" else 1)


def commerce_score(q):
    """商务条件:后付/月付优于预付年付(现金流),赠项数量加分。"""
    pay = q.get("payment", "")
    s = 3 if ("月付" in pay or "后付" in pay or "验收后" in pay) else (1 if "预付" in pay or "年付" in pay else 2)
    return s + min(len(q.get("extras") or []), 3)


def minmax(vals, lower_better=True):
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {v: 1.0 for v in vals}
    out = {}
    for v in vals:
        out[v] = (hi - v) / (hi - lo) if lower_better else (v - lo) / (hi - lo)
    return out


def sla_threshold(demand):
    """从必达项里解析 SLA 门槛(如「SLA ≥ 99.9%」-> 99.9)。先过门槛再评分。"""
    for m in demand.get("must", []):
        mt = re.search(r"SLA\s*[≥>=]*\s*([0-9]+(?:\.[0-9]+)?)", str(m))
        if mt:
            return float(mt.group(1))
    return None


def score_quotes(quotes, demand):
    thr = sla_threshold(demand)
    # 先把单价×席位×年限折成总价,再建价格归一化表(顺序反了价格分会全成默认 0.5)
    for q in quotes:
        if q.get("total_price") is None and q.get("unit_price") is not None and q.get("seats"):
            q["total_price"] = q["unit_price"] * q["seats"] * (q.get("years") or 1)
    prices = [q["total_price"] for q in quotes if q.get("total_price") is not None]
    pmap = minmax(prices) if prices else {}
    slas = [float(q["sla"]) for q in quotes if q.get("sla")]
    smap = minmax(slas, lower_better=False) if slas else {}
    rows = []
    for q in quotes:
        total = q.get("total_price")
        if total is None and q.get("unit_price") is not None and q.get("seats"):
            total = q["unit_price"] * q["seats"] * (q.get("years") or 1)
            q["total_price"] = total
        p = pmap.get(total, 0.5) if total is not None else 0.5
        # SLA 先过门槛:达标拿基本分 0.6,超出门槛的部分再比(避免"达标却垫底")
        sla = float(q["sla"]) if q.get("sla") else None
        if sla is None or (thr is not None and sla < thr):
            s = 0.0
        else:
            s = 0.6 + 0.4 * smap.get(sla, 0.5)
        sup = support_score(q.get("support"))
        com = commerce_score(q)
        bg = bg_score(q.get("channel_type", ""))
        score = 100 * (W_PRICE * p + W_SLA * s + W_SUPPORT * sup / 3
                       + W_COMMERCE * com / 6 + W_BG * bg / 3)
        rows.append({"q": q, "score": round(score, 1)})
    rows.sort(key=lambda r: -r["score"])
    return rows


def negotiation_points(quotes, demand):
    pts = []
    totals = sorted(q["total_price"] for q in quotes if q.get("total_price") is not None)
    if len(totals) >= 2:
        spread = (totals[-1] - totals[0]) / totals[0] * 100
        if spread > 15:
            pts.append(f"报价极差 {spread:.0f}%:>15%,用最低价({totals[0]:,.0f} 元)为锚,压中间与最高报价,要求书面重报")
        else:
            pts.append(f"报价极差 {spread:.0f}%:报价集中,竞争杠杆弱,转而谈账期/赠项/续约涨幅")
    prepaid = [q for q in quotes if "预付" in (q.get("payment") or "") or "年付" in (q.get("payment") or "")]
    for q in prepaid:
        save = (q.get("total_price") or 0) * CASH_ANNUAL
        if save:
            pts.append(f"{q['supplier']} 预付年付:资金成本约 {save:,.0f} 元/年(按 {CASH_ANNUAL:.0%} 年化),可要折扣或改季付")
    for q in quotes:
        if q.get("free_seats"):
            pts.append(f"{q['supplier']} 送 {q['free_seats']} 席:折算有效折扣约 "
                       f"{q['free_seats'] / (q['seats'] + q['free_seats']) * 100:.0f}%,比直接降价易争取,优先要")
    pts.append("续约涨幅没锁的话,到期没有议价筹码:合同写入「续约涨幅 ≤5%(或 CPI+2%)」")
    d = [q for q in quotes if q.get("channel_type") == "代理商"]
    if d and any(q.get("channel_type") == "原厂" for q in quotes):
        pts.append("代理商与原厂并存:合同写明服务责任链——代理商履约失败由原厂兜底,避免扯皮")
    return pts


def red_flags(quotes, demand):
    flags = []
    if len(quotes) < 3:
        flags.append(f"仅 {len(quotes)} 家报价,不满足三方比价,补齐第 3 家再上会")
    budget = demand.get("budget")
    lows = min((q.get("total_price") or float("inf")) for q in quotes)
    if budget and lows > budget:
        flags.append(f"最低总价 {lows:,.0f} 元已超预算 {budget:,.0f} 元,先砍范围或追加预算")
    # 口径一致性:含税/不含税混报,比价无效
    taxes = {q.get("tax_included") for q in quotes if q.get("tax_included") is not None}
    if len(taxes) > 1:
        flags.append("各家含税口径不一致:统一按含税(或不含税)重报,否则比价无效")
    for q in quotes:
        pre = q.get("prepay_pct")
        if pre is not None and pre > 50:
            flags.append(f"{q['supplier']} 预付 {pre}%:资金占用过大,改季付/验收后付,或按 {CASH_ANNUAL:.0%} 年化要折扣")
        if not q.get("valid_until"):
            flags.append(f"{q['supplier']} 报价未标有效期:限期补,过期重报防价格锚死")
    thr = sla_threshold(demand)
    for q in quotes:
        if not q.get("sla"):
            flags.append(f"{q['supplier']} 未给 SLA:缺硬指标,别只比价格,要求书面补齐")
        elif thr is not None and float(q["sla"]) < thr:
            flags.append(f"{q['supplier']} SLA {q['sla']} 低于需求门槛 {thr}:直接出局或要求升级承诺")
        if not q.get("support"):
            flags.append(f"{q['supplier']} 未写支持等级:按常规工单对待,合同里补 SLA 响应时效")
    for m in demand.get("must", []):
        flags.append(f"必达项「{m}」需供应商书面确认,口头承诺不算")
    return flags


_NUM_KEYS = ("unit_price", "seats", "free_seats", "years",
             "total_price", "prepay_pct", "sla")


def coerce_numbers(demand, quotes):
    """宽松转数值:表单/JSON 粘贴常带字符串数字('5000'),直接算术会炸。
    只动已知数字键,转不动的原样保留(日期/文本/口径不动)。"""
    def one(d, keys):
        if not isinstance(d, dict):
            return
        for k in keys:
            v = d.get(k)
            if isinstance(v, str) and v.strip():
                try:
                    f = float(v.strip().rstrip("%").replace(",", ""))
                    d[k] = int(f) if f.is_integer() else f
                except ValueError:
                    pass
    if isinstance(demand, dict):
        one(demand, ("budget",))
    for q in (quotes if isinstance(quotes, list) else []):
        one(q, _NUM_KEYS)


def build_report(demand, quotes):
    """算术 + 规则判定,产出结构化报告(dict)。CLI 与工作台接口共用这一条路径,
    保证「命令行出的表」和「面板出的表」永远是同一套算法。"""
    coerce_numbers(demand, quotes)
    rows = score_quotes(quotes, demand)
    eff = {id(r["q"]): eff_unit_price(r["q"]) for r in rows}
    out_rows = []
    for i, r in enumerate(rows, 1):
        q = r["q"]
        e = eff.get(id(q))
        out_rows.append({
            "rank": i, "supplier": q.get("supplier", "未填"),
            "channel_type": q.get("channel_type", "未填"),
            "total_price": q.get("total_price"), "eff_unit_price": e,
            "payment": q.get("payment", "未填"), "sla": q.get("sla", "未填"),
            "support": q.get("support", "未填"), "extras": q.get("extras", []),
            "score": r["score"], "prepay_pct": q.get("prepay_pct"),
            "tax_included": q.get("tax_included"),
            "free_seats": q.get("free_seats") or 0,
        })
    return {
        "date": date.today().isoformat(),
        "item": demand.get("item", "未填采购项"),
        "budget": demand.get("budget"), "need_by": demand.get("need_by"),
        "must": demand.get("must", []),
        "rows": out_rows,
        "negotiation": negotiation_points(quotes, demand),
        "flags": red_flags(quotes, demand),
        "top": out_rows[0] if out_rows else None,
    }


def _num(v, fmt="{:,.0f}"):
    return fmt.format(v) if isinstance(v, (int, float)) else "未填"


def render_md(rep):
    """结构化报告 -> markdown,与旧版 CLI 输出同一格式。"""
    L = [f"# 三方比价 · {rep['item']} · {rep['date']}", ""]
    L.append(f"需求:预算 {_num(rep['budget'])} 元 | 期望到货 {rep['need_by'] or '未填'} | "
             f"必达:{'、'.join(rep['must']) or '未填'}")
    L.append("")
    L.append("## 一、比价表")
    L.append("")
    L.append("| 排名 | 供应商 | 渠道 | 总价(元) | 折算有效单价(元/席/年) | 账期 | SLA | 支持 | 赠项 | 加权分 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rep["rows"]:
        L.append(f"| {r['rank']} | {r['supplier']} | {r['channel_type']} "
                 f"| {_num(r['total_price'])} | {_num(r['eff_unit_price'])} | {r['payment']} "
                 f"| {r['sla']} | {r['support']} "
                 f"| {'、'.join(r['extras']) or '—'} | {r['score']} |")
    L.append("")
    L.append("## 二、议价点")
    L.extend(f"- {p}" for p in rep["negotiation"])
    L.append("")
    L.append("## 三、合规红旗")
    L.extend(f"- 🚩 {f}" for f in rep["flags"])
    L.append("")
    L.append("## 四、建议动作")
    top = rep["top"]
    if top:
        L.append(f"- 综合分最高:{top['supplier']}({top['score']} 分)。加权含价格 40%/SLA 20%/支持 15%/商务 15%/背景 10%,"
                 f"权重按本项目可调,不是黑箱打分")
    L.append("- 上会前:必达项书面确认 + 续约涨幅条款落合同 + 三家报价单归档(审计留痕)")
    L.append("")
    return "\n".join(L)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        sys.exit(f"未找到 {path},先准备报价 JSON")
    demand, quotes = load(path)
    if len(quotes) < 2:
        sys.exit("报价不足 2 家,没法比。检查 data/quotes/*.json")
    out = render_md(build_report(demand, quotes))
    out_path = os.path.splitext(path)[0] + "_比价表.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(f"\n-> 已写入 {out_path}")


if __name__ == "__main__":
    main()
