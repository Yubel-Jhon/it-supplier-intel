---
name: agent-competitive-intel-verify
description: agent-competitive-intel 的第 2 步。核验来源正确性(白名单/转载降级/域名未核验),并对能力标三档、媒体标四态、成本/MAU 数字标冲突。
---

# verify · 确保来源正确

分两块:**脚本先核**(自动化),**LLM 后核**(判断)。

## 执行

```bash
python scripts/parse.py    # raw.json → structured.json
python scripts/verify.py   # 白名单/转载/域名核验 → verified.json
```

## 脚本核(自动化)

| 核验项 | 规则 | 输出 |
|---|---|---|
| 域名白名单 | 抓取主机名 ∈ sources.yaml 该源 `domain` | `whitelist: pass/fail/n/a` |
| 转载降级 | 域名 ∈ `repost_domains` | `repost: true` |
| 域名未核验 | 源带 `unverified_domain: true` | `domain_flag: unverified` |
| 类型匹配 | 源 type 与抓取内容对得上 | `type_ok` |

## LLM 核(判断活,逐条过)

对每条「例证」(一个版本更新 / 一个数字 / 一条报道),标:

**能力真实性三档**(谁在说):
- 📋 更新日志/能力页/官方文档 —— 最硬
- 🎙️ 发布会/官方自述 —— 标「厂商自述」
- 📊 第三方实测/独立数据 —— 标评测方是谁

**媒体报道四态**:
- 原发 / 转载 / 转述 / 域名未核验

**成本 / MAU 数字核验**(本 skill 重点,产品决策者靠这个下判断):
- 成本:输入/输出价、缓存命中价、订阅价 —— 多源报价不一致 → 标 ❌ 保留多口径
- MAU/用户规模:必须有「来源 + 日期」,缺一不可当结论;两家说两个数 → 标 ❌
- benchmark:必须标版本口径(如 DeepSWE vs DeepSWE v1.1 不可直接比)

## 红旗上报

以下标 ❌ 写进「待核实红旗」:
- 同一数字多源冲突(成本/MAU/融资额)
- 能力只出自厂商自述、无日志/页面/第三方 → 降权「待证实」
- 报道命中转载域却当原发 → 改标转载

## 红线

- 不评「产品受不受认可/厉不厉害」,只评「这条信息真不真、从哪来、数字冲突不冲突」。
- 标「域名未核验」不丢人——宁可标出来,不假装核验过。
