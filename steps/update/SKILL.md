---
name: agent-competitive-intel-update
description: agent-competitive-intel 的第 4 步。对 delta 做四维语义合成,按「周报在前、看板在后」产出两份交付物,回写基线。
---

# update · 四维合成(周报在前,看板在后)

核心:**脚本 diff 出增量 → 有增量才上 LLM 合成**。合成前必读 `references/dimensions.md`。

## 执行

```bash
python scripts/diff.py   # verified.json vs data/baseline.json → delta.json
```

## 分支

- **delta 为空** → 版本无变化,不写看板;但通知层走「无变化」,大事搜索仍独立跑。
- **delta 非空** → 继续四维合成。

## 合成并落盘(两个 md 交付物,顺序固定)

交付物都是 markdown 文件:**先 `brief.md`(周报)后 `dashboard.md`(看板)**。

### 1. 把 delta 翻译成「能力差异」语言

对每条增量,别只写「升级到 xx」,要回答:**这条 release 和对手比,差异是拉大了还是缩小了?**
例:DeepSeek Harness rc.7「子代理接入 Job Panel」→「DeepSeek 在 Agent 编排侧进一步拉开与纯 IDE 型对手的差异」。
每条标能力来源三档(📋/🎙️/📊)。

### 2. 更新台账第二层「变化信息」(第一层不动)

第二层四维:`能力迭代` / `成本变化` / `MAU·规模` / `动态`。
- 能力差异对比按赛道写;版本迭代按厂商列时间线,新版本补最上。
- 成本/MAU 数字冲突:保留多口径,标 ❌,注明出处日期。

### 3. 生成周报 `data/raw/<周>/brief.md`(在前)

按 `templates/brief.md`:本周大事(维度分类 + 重点标注)+ 能力变化 + 红旗 + 无变化。只写「本周变了什么」。

### 4. 生成竞品对比看板 `data/raw/<周>/dashboard.md`(在后)

按 `templates/dashboard.md`:赛道格局总览 + 焦点赛道(通用/编程模型)四维深挖。
**每格差异化定位必须点出与对手的不同**;重大升级放大加红标、新能力加紫标。

### 5. 回写基线

把确认的最新版本写回 `data/baseline.json`:key 用**源 id**,`latest_version` 用 delta 的 `new_version` **原始字符串**(别翻译,否则下次 diff 字符串对不上)。`date` 填版本日期。segment/audience/cost 属事实层,非公司重组/改名/协议变更不动。

## 红线

- 只评「差异」不评「好坏」。
- 周报在前、看板在后,别颠倒。
- 第一层事实除非重组/改名/协议变更,一个字不动。
- 回写基线必须用已核实的版本,抓错的不进基线。
