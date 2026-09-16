---
name: agent-competitive-intel-fetch
description: agent-competitive-intel 的第 1 步。按 sources.yaml 抓取官方 changelog / GitHub / 官方账号页面，落盘 data/raw/YYYY-MM-DD/raw.json。
---

# fetch · 抓取网络数据

机械活为主。目标：把 `sources.yaml` 里每个 `enabled` 的源抓下来，落成结构化原始数据，供后续 parse/verify 用。

## 执行

```bash
cd <skill 根目录>
python scripts/fetch.py
```

产出：`data/raw/<今天>/raw.json`，每源一条记录：

```json
{"id":"qoder-changelog","product":"Qoder","type":"changelog_html","status":"ok","html":"<原文>"}
{"id":"dsh","product":"DeepSeek Harness","type":"github_release","status":"ok","data":[{"tag_name":"v0.1","published_at":"..."}]}
{"id":"kukuai","product":"库库AI","type":"official_account","status":"error","error":"..."}
```

## 分类型抓取策略

| type | 脚本做法 | 备注 |
|---|---|---|
| `github_release` | `urllib` 打 `api.github.com/repos/<repo>/releases`(无 release 回退 tags) | 不依赖 gh CLI |
| `changelog_html` | `urllib` 抓整页 HTML | 国内站可能反爬/需登录，失败就记 `error` |
| `rss` | `urllib` 抓 XML | 备用 |
| `official_account` | 尝试抓首页 HTML，抓不到记 `error`（正文靠 LLM 补） | 微博/公众号 JS 渲染，抓不到正文是常态 |
| `media` | **不在此步抓** | 走 WebSearch，归 `verify`/`update` 步 |

## 判断活（Claude 在 fetch 里只做三件事）

1. **官方账号盲区**：对 `official_account` 且 `unverified_domain: true` 的源，用 WebSearch 找「<产品名> 官方 官网/公众号」，确认或修正 `domain`，把结果写进当次 raw.json 的 `llm_note` 字段。
2. **抓失败的源**：判断是「暂时性失败（重试）」还是「URL 变了（改 sources.yaml）」，在 `llm_note` 里记录。
3. 别在 fetch 里做核验和判断真假——那是 verify 的活。

## 红线

- 不伪造 fetch 结果。抓不到就 `status: error`，不编 HTML。
- 不改 `sources.yaml` 里非盲区的 URL，除非抓到 404 明确证明它变了。
