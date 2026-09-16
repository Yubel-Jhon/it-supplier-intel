# it-supplier-intel · IT 供应商寻源情报 + 三方比价

面向 **IT 采购执行位**的「软件云服务供应商」情报系统:跟踪云资源 / 软件席位 / 开源自部署三类供应商的产品发布、价格变动、资本动态、安全合规信号,每条信号落到采购动作(询价/锁价/分级/备选)。配套采购工作流工具:**三方比价**(报价 JSON → 比价表 + 议价点 + 合规红旗)、**需求单模板**(JD1)、**QCDS 绩效评分表**(JD5)、**寻源 SOP** 含 1688 可选工具层(JD3)。

## 与 agent-competitive-intel 的关系

同一套「脚本先跑、有增量才上 LLM」管线(`fetch → parse → verify → diff`,纯标准库零依赖)的**架构复用**:

| 不变的 | 换掉的 |
|---|---|
| 管线与依赖链 | 跟踪对象:AI Agent 厂商 → IT 品类供应商(带 category 品类字段) |
| 域名白名单/转载降级核验 | 输出口径:竞品差异 → 信号→采购动作 |
| 两层基线(事实层季度核对/变化层每次刷新) | 新增:QCDS 供应商分级 + compare_quotes.py 比价工具 |

## 快速开始

```bash
python scripts/pipeline.py                                  # 周更:抓取→解析→核验→diff
python scripts/compare_quotes.py data/quotes/sample_quotes.json   # 三方比价 demo
```

- diff 为空 → 静默结束;有增量 → 读 `references/signals.md` 合成寻源周报(模板 `templates/sourcing_brief.md`),回写 `data/baseline.json`。
- 比价工具只做算术和规则判定:SLA 先过门槛再评分、送席折算有效单价、账期按年化折算、不足三家出红旗。权重透明可调。

## 采购职责映射

| 采购职责 | 对应能力 |
|---|---|
| 采购需求收集分析 | 需求摘要 + 信号按决策影响分类 |
| 采购招采(询报价/三方比价) | compare_quotes.py |
| 采购寻源(供应商/渠道/排名) | sources.yaml 品类×供应商注册表 + 备选池 |
| 采购交付(节点监控) | release/changelog 跟踪 = 交付节奏信号 |
| 供应商绩效/分级 | QCDS 口径 + grade 回写 baseline(查不到依据保持「未评级」) |
