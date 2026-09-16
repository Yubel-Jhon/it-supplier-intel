---
name: it-supplier-intel
theme: procurement
description: 面向 IT 采购执行位的「软件云服务供应商寻源情报」:跟踪云资源/软件席位/开源自部署三类供应商的产品发布、价格变动、资本动态、安全合规信号,周更产出「寻源周报(变化→采购动作)」;带三方比价工具(报价 JSON → 比价表+议价点+合规红旗)、需求单模板、QCDS 绩效评分表、寻源 SOP(含 1688 可选工具层)与采购知识库。当用户要"供应商动态 / 寻源 / 比价 / 询价 / 需求单 / 供应商评估 / 绩效评分 / 分级 / 续约锁价 / 采购信号"时使用。
---

# it-supplier-intel · IT 供应商寻源情报

给采购执行位看的,不是新闻罗列。核心回答:「**我负责的供应商这周变了什么、对我要做的采购动作(询价/比价/续约/分级)意味着什么**」。

架构复用自 agent-competitive-intel(竞品情报),同一套「脚本先跑、有增量才上 LLM」管线,把跟踪对象从 AI Agent 厂商换成 IT 品类供应商,把"竞品差异"口径换成"信号→采购动作"口径。

## 与采购职责的对照(为什么这些能力是采购需要的)

| 采购职责 | 本 skill 对应能力 |
|---|---|
| 采购需求收集分析 | `templates/demand_brief.md` 需求单(寻源关键词/渠道初判/比价方式);信号按"影响哪类决策"分类 |
| 采购招采(询报价/三方比价) | `compare_quotes.py`:报价 JSON → 比价表 + 议价点 + 合规红旗(不足三家/超预算/含税口径/预付比例/SLA 门槛) |
| 采购寻源(供应商排名/渠道) | `references/sourcing_sop.md` 寻源五步 + 品类→渠道→比价方式映射 + 1688 可选工具层;sources.yaml 带 category/channel 字段 |
| 采购交付(节点监控) | 版本/release 跟踪 = 供应商交付节奏的最客观信号 |
| 协助管理供应商(绩效/分级) | `templates/supplier_scorecard.md` QCDS 评分表(证据透明)+ 分级口径 + grade 回写 baseline |

## 交付物与顺序(固定)

1. **寻源周报(主)**:本周供应商变化 → 每条落到采购动作。模板 `templates/sourcing_brief.md`。
2. **比价表(按需)**:拿到 ≥2 家真实报价时跑 `scripts/compare_quotes.py`,出比价表+议价点+合规红旗。
3. **重大事件即时(辅)**:调价/安全事件/停服当天出即时简报,不等周更。

## 信号口径(合成前必读 `references/signals.md`)

- 每条信号必须落到「采购动作」:降价→重询三家;涨价→续约前锁价;裁员/收购→分级复审+备选;安全/合规→红旗;旧版停维→升级或替代寻源。
- 可信三档:📋 更新日志(原发)/ 🎙️ 官方自述 / 📊 第三方;数字冲突标 ❌ 保留多口径。
- 分级用 QCDS(A 优先/B 合格/C 观察/D 淘汰),查不到依据保持「未评级」,禁止拍脑袋。

## 核心原则(不可违背)

1. **脚本先跑,有增量才上 LLM**。抓取/解析/白名单/diff 是脚本活;有增量才做语义合成。
2. **每条信号给动作**,不给动作的不进简报。
3. **查不到就标「未查到」,禁止编造**;价格必须区分单价/总价/有效单价(送席、账期都折算)。
4. **只改变化层,不碰事实层**。品类/渠道/授权模式是第一层事实(季度核对);版本/价格/动态是第二层(每次刷新)。
5. 比价工具只做算术和规则判定,不装"AI 打分":权重透明(价格 40/SLA 20/支持 15/商务 15/背景 10),可按项目调。

## 跟踪范围(见 `sources.yaml`,唯一事实源)

- **云资源/AI平台**:阿里云百炼(发布页)、阿里云调价公告(盲区,LLM 搜)。
- **云上研发工具**:华为云 CodeArts。
- **AI 工具席位**(按席位订阅,续约占比高):Qoder / Kimi Code / CodeBuddy / ZCode / MiniMax / Trae / 讯飞 AstronClaw。
- **办公套件 / ERP**:钉钉、飞书、金蝶云(官网无稳定 changelog,盲区,LLM 搜)。
- **开源自部署**(软件 0 元但要采购实施/支持):Trae-Agent、DeepSeek Harness(GitHub release)。
- 行业媒体(排名/格局/舆情):新浪科技、中国政府采购网(白名单),36氪、InfoQ(LLM 搜)。

## 目录地图

- `sources.yaml` —— 供应商源注册表(唯一事实源,带 category 品类 + channel 渠道 + price_page 定价页字段)
- `scripts/` —— 机械活:`fetch.py → parse.py → verify.py → diff.py` + `compare_quotes.py`(比价)
- `steps/` —— 判断活:`fetch` / `verify` / `events` / `update`
- `references/signals.md` —— 信号→采购动作 + QCDS 分级口径
- `references/sourcing_sop.md` —— 寻源五步 SOP + 品类→渠道→比价方式 + 1688 可选工具层
- `references/procurement_basics.md` —— 采购知识库(询价流程/软件条款/信创/TCO/QCDS/阿里语境)
- `data/baseline.json` —— 第一层事实基线(品类/渠道/授权模式/分级 + latest_version)
- `data/quotes/` —— 报价 JSON 与比价表输出
- `templates/sourcing_brief.md` —— 寻源周报模板
- `templates/demand_brief.md` —— 需求单模板(JD1)
- `templates/supplier_scorecard.md` —— QCDS 绩效评分表(JD5)

## 编排流程

### 周更(主)

1. 跑脚本层(顺序不可变,依赖链 `raw.json → structured.json → verified.json → delta.json`):
   ```bash
   python scripts/pipeline.py   # = fetch → parse → verify → diff
   ```
2. 看 `data/raw/<今天>/delta.json`:空 → 静默结束;非空 → 读 `references/signals.md`,按序做 steps/verify(能力三档+数字冲突 ❌)→ steps/events(搜价格/资本/安全大事)→ steps/update(合成寻源周报,回写 baseline 的 latest_version 与 grade)。
3. 交付:`data/raw/<周>/sourcing_brief.md`。

### 比价(按需)

```bash
python scripts/compare_quotes.py data/quotes/sample_quotes.json
```
输入需求+报价 JSON,输出 `*_比价表.md`:比价表(含送席折算的有效单价)+ 议价点(锚定最低价/账期折算/送席折算/续约锁价)+ 合规红旗(不足三家/超预算/含税口径不一致/预付>50%/无报价有效期/SLA 不过门槛)。

### 寻源(按需,新需求进来)

从需求单开始,走 `references/sourcing_sop.md` 五步:需求单(demand_brief)→ 圈渠道 → 扫格局(政采中标价/排名报告)→ 统一口径发 RFQ → 比价定商。实物/定制类寻源走 1688 可选工具层(SOP 内有命令)。

### 大事即时(辅)

`steps/events` 独立跑,重大事件(调价/收购/安全事件)当天出即时简报,不等周更。
