---
name: agent-competitive-intel-notify
description: agent-competitive-intel 的可选推送步。把看板/简报推送出去，默认接微信自动通知，也可只落盘。
---

# notify · 推送简报

可选步。默认接已有的「GitHub push → 微信自动通知」链路（wechatauto-replica），也可只把简报写到本地文件。

## 执行

```bash
python scripts/notify.py   # 读 data/raw/<今天>/brief.md 推送
```

## 三种模式（notify.py 里可配）

| 模式 | 做法 | 适合 |
|---|---|---|
| `local_file` | 简报作为 md 文件留在 `data/raw/<今天>/brief.md`（update 步已落盘），不推送 | **默认**，正式交付 = md 文档 |
| `wechat_push` | 把简报追加到触发微信的 git 仓库文件，push 触发微信 | 需设 `DAILY_BRIEFING_PUSH_FILE` |
| `stdout` | 打印到终端 | 仅调试 |

## 判断活（基本没有）

- 若今天有「红旗」条目（数字冲突 ❌ / 域名未核验），在推送消息**开头**用一句话突出，让收件人先看风险，再看增量。

## 红线

- 推送出去的内容 = 已经过 verify 的，不推「待证实」的当事实。
- 推送是「对外的动作」——发之前确认简报里没有把转载当原发、把厂商自述当实测。
