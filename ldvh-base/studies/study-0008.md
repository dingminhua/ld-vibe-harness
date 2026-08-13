---
title: Firecrawl 外部网页证据获取能力调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: Firecrawl 当前 API 如何提供 Search、Scrape、Crawl、Map、Extract 等网页证据获取能力，其可靠性、隐私与许可边界是什么？
abstract: 调研 Firecrawl v2 API 文档与官方仓库。API 将网页搜索、单页抓取、整站 Crawl、URL Map 和自然语言 Extract 分成不同入口，并可返回 Markdown/HTML/JSON 等格式；官方同时提示认证、限流、错误码、robots/网站政策和 AGPL/云服务差异。它可作为证据获取候选，不是证据真实性或许可自动通过器。
object_id: study-0008
object_uid: 019ffb52-ebb5-7155-b0e0-24092ac61053
fact_type_key: study
created_at: '2026-07-19T11:17:55.692023+08:00'
updated_at: '2026-08-13T14:03:29.788456Z'
urls:
- ref: https://docs.firecrawl.dev/api-reference/introduction
  title: docs.firecrawl.dev/api-reference/introduction
  summary: 曾用于旧研究的 Firecrawl API 总览；不单独证明服务可用性或成本。
- ref: https://docs.firecrawl.dev/api-reference/endpoint/scrape
  title: docs.firecrawl.dev/api-reference/endpoint/scrape
  summary: 曾用于旧研究的 Scrape 接口文档；不单独保证抓取结果。
- ref: https://docs.firecrawl.dev/api-reference/endpoint/crawl-post
  title: docs.firecrawl.dev/api-reference/endpoint/crawl-post
  summary: 曾用于旧研究的 Crawl 接口文档；不单独保证整站抓取行为。
- ref: https://docs.firecrawl.dev/api-reference/endpoint/map
  title: docs.firecrawl.dev/api-reference/endpoint/map
  summary: 曾用于旧研究的 Map 接口文档；不单独保证 URL 发现结果。
- ref: https://docs.firecrawl.dev/api-reference/endpoint/search
  title: docs.firecrawl.dev/api-reference/endpoint/search
  summary: 曾用于旧研究的 Search 接口文档；不单独保证搜索结果。
- ref: https://docs.firecrawl.dev/api-reference/endpoint/extract
  title: docs.firecrawl.dev/api-reference/endpoint/extract
  summary: 曾用于旧研究的 Extract 接口文档；不单独保证抽取质量。
- ref: https://github.com/firecrawl/firecrawl
  title: github.com/firecrawl/firecrawl
  summary: 曾用于旧研究的 Firecrawl 仓库；不单独代表当前 API 契约。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:29.788456Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
---

## 研究问题

Firecrawl 当前 API 如何提供 Search、Scrape、Crawl、Map、Extract 等网页证据获取能力，其可靠性、隐私与许可边界是什么？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://docs.firecrawl.dev/api-reference/introduction、https://docs.firecrawl.dev/api-reference/endpoint/scrape、https://docs.firecrawl.dev/api-reference/endpoint/crawl-post、https://docs.firecrawl.dev/api-reference/endpoint/map、https://docs.firecrawl.dev/api-reference/endpoint/search、https://docs.firecrawl.dev/api-reference/endpoint/extract、https://github.com/firecrawl/firecrawl。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

官方文档把 Scrape、Crawl、Map、Search、Extract 明确分层；Scrape 可输出 Markdown、HTML、截图或结构化数据，Crawl 面向站点，Map 面向 URL 发现，Search 返回搜索结果内容，Extract 面向结构化抽取。文档明确 2xx/4xx/5xx、408/429 等失败类别和认证要求；仓库说明开源核心为 AGPL-3.0，SDK/部分组件可能不同许可，并提醒遵守网站政策。
### 旧研究的限制

LDVH 若采用，应把“请求、原始响应、解析产物、来源 URL、观察时间、版本、失败状态和许可判断”分开保存；429、超时、反爬或空结果必须是 unknown/evidence incomplete，而不是研究通过。限制是本次只读文档，没有验证实际页面可抓取性、成本或服务 SLA。
## 建议

先把 Firecrawl 当作可插拔 Web 证据获取适配器，补齐许可/robots/隐私、限流、重试、原始响应保存和失败回传契约；Study 仍由 AI 负责外部证据判断。
## 后续分流

供 Spark-0017；若接入 Web，先建 WorkCase 做最小受控抓取和证据回读，不绕过现有 Web direct capture 与 Human 边界。
