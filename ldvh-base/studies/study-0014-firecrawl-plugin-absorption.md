---
id: study-0014
type: study
title: Firecrawl 插件能力吸收调研
status: active
created: '2026-06-30T11:20:38+08:00'
updated: '2026-06-30T11:20:38+08:00'
summary: |
  Firecrawl 是面向 AI agent、RAG、研究和结构化抽取工作流的 Web context API：它把搜索、单页抓取、站点映射、站点爬取、结构化抽取、浏览器交互和 MCP 工具封装为统一服务，输出 Markdown、JSON、截图、元数据或 schema 化数据。LDVH 可以吸收的是“外部网页资料获取与证据归一化”的编排模式、事实源记录字段、成本/权限门禁和可插拔运行时适配；不应吸收的是把 Firecrawl 结果直接当权威事实、把外部商业服务变成核心依赖、绕过 robots / rate limit 的爬取策略，或把 API key、MCP URL、网页全文写入事实模型。
user_intent: |
  用户要求针对 spark-0039 进行并行调研，联网核验 Firecrawl 的产品、工作流、技术实现、SDK、MCP、云服务/自托管边界、成本/限流/合规风险，并形成可供 LDVH 吸收的 Study。主线程会负责最终关联，本线程只创建指定 Study，不修改 spark-0039。
conclusion: |
  建议把 Firecrawl 作为 LDVH “可选外部 Web 资料获取运行时”研究，而不是作为事实模型或验证系统的内核依赖。近期可分流为 WorkCase：设计 Web source ingestion 的最小适配层、来源快照字段、调用预算和 fact_validate 前置检查；需要 ADR 判断是否允许 LDVH 正式引入第三方爬取服务、云端 API 与自托管路径如何分级；需要 Pitfall 记录 MCP URL/API key 泄漏、动态网页抽取误判、成本失控和 robots 合规风险。按 2026-06-30 当前一手资料，Firecrawl API 文档以 v2 为主，官方 Git tag 观察到最高标准 v2 tag 为 v2.11.51；GitHub 未认证 release API 被限流，因此本报告不依赖 release notes 细节。
urls:
  - ref: https://docs.firecrawl.dev/api-reference/introduction.md
    title: Firecrawl API Reference Introduction
    summary: 用于确认 Firecrawl API 的 v2 基础能力、Base URL、Bearer API key 鉴权、HTTP 状态码、429 rate limit、402 payment required 和错误码边界。
  - ref: https://docs.firecrawl.dev/api-reference/endpoint/scrape.md
    title: Firecrawl Scrape API
    summary: 用于确认 `POST /v2/scrape` 单页抓取能力、Markdown/JSON/截图等输出、缓存、headers、waitFor、mobile、timeout、PDF parser、zero data retention 等参数边界。
  - ref: https://docs.firecrawl.dev/api-reference/endpoint/crawl-post.md
    title: Firecrawl Crawl API
    summary: 用于确认 `POST /v2/crawl` 站点爬取能力、include/exclude path、sitemap、深度、limit、外链/子域、robots 企业参数、delay、concurrency、webhook 和 scrapeOptions。
  - ref: https://docs.firecrawl.dev/api-reference/endpoint/map.md
    title: Firecrawl Map API
    summary: 用于确认 `POST /v2/map` 站点 URL 发现能力、sitemap 模式、相关性排序、includeSubdomains、ignoreQueryParameters、缓存、limit 和 location 参数。
  - ref: https://docs.firecrawl.dev/api-reference/endpoint/search.md
    title: Firecrawl Search API
    summary: 用于确认 `POST /v2/search` 将 Web search 与可选抓取结合，支持 query operators、location/country、categories、domain filters、time based search、sources 和 scrapeOptions。
  - ref: https://docs.firecrawl.dev/api-reference/endpoint/extract.md
    title: Firecrawl Extract API
    summary: 用于确认 `POST /v2/extract` 以 URLs、prompt、JSON Schema、enableWebSearch、showSources、scrapeOptions 等参数做结构化抽取。
  - ref: https://docs.firecrawl.dev/developer-guides/usage-guides/choosing-the-data-extractor.md
    title: Choosing the Data Extractor
    summary: 用于确认 `/agent`、`/extract`、`/scrape` JSON mode 的取舍：官方建议新结构化抽取优先考虑 `/agent`，`/extract` 偏已知 URL 多页抽取，`/scrape` JSON mode 偏单页同步抽取，并记录当期成本口径。
  - ref: https://docs.firecrawl.dev/quickstarts/python.md
    title: Firecrawl Python Quickstart
    summary: 用于确认 Python 官方 SDK `firecrawl-py`、Python 3.8+、API key、search/scrape/interact 示例和 `FIRECRAWL_API_KEY` 环境变量入口。
  - ref: https://docs.firecrawl.dev/quickstarts/codex-cli.md
    title: MCP Web Search & Scrape in Codex CLI
    summary: 用于确认 Codex CLI 通过 MCP 接入 Firecrawl 的 `npx firecrawl-mcp` 配置、远程 hosted MCP URL、API key 需求和 `firecrawl_search`、`firecrawl_scrape`、`firecrawl_crawl`、`firecrawl_extract` 工具边界。
  - ref: https://docs.firecrawl.dev/use-cases/developers-mcp.md
    title: Firecrawl Developers & MCP
    summary: 用于确认 MCP 用例、可暴露的 scrape/batch scrape/map/crawl/search 工具、15 分钟缓存说明和 MCP 请求沿用标准 API rate limit 的边界。
  - ref: https://github.com/firecrawl/firecrawl
    title: firecrawl/firecrawl GitHub Repository
    summary: 用于确认 Firecrawl 的官方开源仓库、产品定位、核心端点总览、SDK/CLI 示例、agent ready、media parsing、actions 和 hosted service 边界。
  - ref: https://raw.githubusercontent.com/firecrawl/firecrawl/main/SELF_HOST.md
    title: Firecrawl Self-hosting Guide
    summary: 用于确认自托管适用场景、Docker/Redis/Playwright 配置、云端 API key 与自托管 API key 差异、Fire-engine 不随自托管开放、AI features 需额外配置模型 key 的边界。
  - ref: https://raw.githubusercontent.com/firecrawl/firecrawl/main/LICENSE
    title: Firecrawl License
    summary: 用于确认官方仓库许可证为 GNU AGPL v3，自托管或二次分发时需要额外评估许可证影响。
  - ref: https://docs.firecrawl.dev/api-reference/endpoint/credit-usage.md
    title: Firecrawl Credit Usage API
    summary: 用于确认 `GET /v2/team/credit-usage` 可查询团队剩余 credits、plan credits 和 billing period，是成本门禁可消费的官方端点。
  - ref: https://www.firecrawl.dev/pricing
    title: Firecrawl Pricing
    summary: 用于确认 Firecrawl 采用 usage-based pricing、free tier、pay-as-you-go credits 和 enterprise plans；具体价格随产品变化，不作为 LDVH 稳定事实写死。
  - ref: https://github.com/firecrawl/firecrawl/tags
    title: Firecrawl GitHub Tags
    summary: 用于按 2026-06-30 当前官方仓库 tag 观察版本边界；本次通过 `git ls-remote` 看到最高标准 v2 tag 为 `v2.11.51`，未认证 release API 被限流，未核验 release notes 正文。
input_refs:
  - spark-0039
  - specs/24-Study-研究报告.md
  - specs/00-LDVH理念与价值标准.md
related_sparks:
  - spark-0039
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/24-Study-研究报告.md
  - specs/00-LDVH理念与价值标准.md
archive_reason: null
---

# Firecrawl 插件能力吸收调研

## 研究问题

本报告回答 spark-0039 下 Firecrawl 方向的并行调研问题：LDVH 是否应该吸收 Firecrawl 的某些产品理念、工作流、技术能力或运行时扩展形态；如果吸收，应吸收在哪里、如何设置门禁；如果不吸收，应把边界和风险记录到哪里。

具体问题包括：

1. Firecrawl 解决什么问题，它和 AI crawling、research、RAG、agent 工作流是什么关系；
2. 当前官方资料中 Firecrawl 的核心 API、SDK、CLI、MCP、云服务与自托管边界是什么；
3. `scrape`、`crawl`、`map`、`search`、`extract`、`agent`、`interact` 等能力如何分工；
4. 输出格式、认证、限流、成本、缓存、zero data retention、robots 和许可证有哪些边界；
5. LDVH 可吸收到事实模型、行动编排、Code、Web、运行时扩展的内容是什么；
6. 哪些内容不应吸收，哪些需要后续 WorkCase、ADR、Pitfall、docs 或 Spark 分流。

## 输入与边界

本报告输入来自 2026-06-30 当天联网读取的一手来源：Firecrawl 官方 API 文档、官方 quickstart / usage guide / MCP 文档、官方 GitHub 仓库 README、SELF_HOST.md、LICENSE、pricing 页面，以及官方 Git tag 观察。资料读取优先级为官方文档和官方仓库；未使用二手测评、社区文章或竞品材料。

本报告边界如下：

- 本报告只创建 `ldvh-base/studies/study-0014-firecrawl-plugin-absorption.md`，不修改 spark-0039 或其它事实源对象；
- 本报告不对三个插件做横向最终汇总，只回答 Firecrawl 方向；
- 本报告不申请、使用或测试 Firecrawl API key，因此不验证实际抓取成功率、费用扣减、账号级 rate limit 或企业功能；
- GitHub unauthenticated releases API 已触发 rate limit，本报告只用官方 Git tag 观察记录版本边界，不把 release notes 正文写成已核验事实；
- Firecrawl 文档与产品更新较快，价格、限流、MCP 工具列表、agent/extract 关系和自托管能力可能变化；后续吸收为 LDVH 规则前必须再次联网核验；
- Firecrawl 输出属于外部网页抓取结果，不自动成为 LDVH 权威事实源；进入 LDVH 前仍需来源记录、Human Gate、对象边界和 `fact_validate`。

## 关键发现

### 产品定位与工作流价值

Firecrawl 的核心定位是把“从公开网页获得 AI 可消费上下文”封装为 API 和 MCP 工具。官方仓库 README 将其描述为可搜索、抓取、交互并把网页转换为干净 Markdown 或结构化数据的 Web context API；官方 API 文档把核心能力拆为 `scrape`、`crawl`、`map`、`search` 和 `extract`。

对 AI 工作流而言，它主要减少四类负担：

| 负担 | Firecrawl 提供的减负方式 | LDVH 读取判断 |
|---|---|---|
| 网页内容清洗 | 单页 `scrape` 可输出 Markdown、JSON、截图、metadata，支持 main content 过滤、缓存、PDF parser 和 headers | 可作为外部资料进入 Study / docs 前的采集层 |
| 来源发现 | `search` 可搜索并可选抓取结果；`map` 可发现站点 URL；`crawl` 可按路径、sitemap、深度和 limit 批量抓取 | 可为研究行动编排提供“先找源、再取证”的流程模板 |
| 动态网页处理 | `interact` 和 actions 支持在抓取后通过自然语言或代码操作页面 | 可作为高风险能力候选，默认不应自动启用 |
| 结构化抽取 | `/extract`、`/agent` 和 `/scrape` JSON mode 可按 prompt 或 JSON Schema 抽取结构化数据 | 可参考 schema 化抽取思想，但结果必须标记为模型生成/外部抽取 |

Firecrawl 与 RAG 的关系不是向量库本身，而是 RAG ingest 前的 Web acquisition 和 normalization 层：它帮助把网页、文档、搜索结果和站点结构转为 Markdown、JSON、metadata 或 sources，再交给后续 chunking、embedding、知识库或报告整理。对 agent 工作流，它通过 SDK、CLI 和 MCP 把这些能力暴露为工具，使 agent 能在任务中实时获取网页上下文。

### 核心 API 与能力分工

Firecrawl API 文档当前以 v2 为主。OpenAPI 片段显示 v2 server 为 `https://api.firecrawl.dev/v2`，文档 Introduction 同时给出 Base URL `https://api.firecrawl.dev`，实际端点以 v2 路径解释更稳妥。云服务请求需要 `Authorization: Bearer fc-...`。

核心端点分工如下：

| 能力 | 官方端点 | 主要用途 | 关键边界 |
|---|---|---|---|
| Scrape | `POST /v2/scrape` | 抓取单个 URL，可选 LLM 抽取 | 同步单页；支持 `formats`、`onlyMainContent`、`onlyCleanContent`、headers、`waitFor`、mobile、timeout、PDF parser、cache、zero data retention |
| Crawl | `POST /v2/crawl` | 从一个 base URL 批量抓取站点页面 | 异步批量；支持 include/exclude path、sitemap、depth、limit、外链/子域、delay、concurrency、webhook、`scrapeOptions` |
| Map | `POST /v2/map` | 快速发现站点 URL 列表 | 默认 include sitemap 和其它发现方式；支持 relevance search、subdomains、query 参数过滤、sitemap cache、limit |
| Search | `POST /v2/search` | 搜索 Web，并可选对结果抓取全文 | 支持 query operators、domain filters、country/location、time based search、sources、categories、`scrapeOptions` |
| Extract | `POST /v2/extract` | 从已知 URL / domain 做结构化抽取 | 需要 URLs；支持 glob、prompt、JSON Schema、`enableWebSearch`、`showSources`、`scrapeOptions`；官方 usage guide 建议新场景优先看 `/agent` |
| Agent | `POST /v2/agent` | 自主搜索、导航、并行收集数据 | usage guide 称其为 `/extract` 的 successor，适合不知道 URL 的 discovery/research 任务；成本动态，需要 `maxCredits` 之类预算控制 |
| Interact | `POST /v2/scrape/{scrapeId}/interact` | 在 scrape 后对浏览器会话执行自然语言或 Playwright 风格交互 | 适合动态内容，但风险高、成本和合规更难控 |

对 LDVH 来说，`map -> 人/AI 选择范围 -> crawl/scrape -> normalize -> Study/Doc` 比“直接 crawl 整站”更符合 V3 正确判断与 V6 强制验证。`search -> scrapeOptions(markdown/summary) -> Study.urls` 适合调研入口。`extract/agent` 适合候选自动化，但必须把输出标记为“外部服务 + 模型抽取”，不能替代 Human 对事实的接受。

### SDK、CLI 与 MCP

官方 Python quickstart 要求 Python 3.8+，通过 `pip install firecrawl-py` 使用 `Firecrawl` 类，并支持 search、scrape、interact；API key 可直接传入或通过 `FIRECRAWL_API_KEY` 环境变量提供。官方 README 还展示了 Node.js SDK `import { Firecrawl } from 'firecrawl'`、cURL 和 CLI 示例。

MCP 入口有两类：

1. 本地 MCP server：Codex CLI quickstart 给出 `npx -y firecrawl-mcp` 配置，并在 `~/.codex/config.toml` 中通过环境变量传入 `FIRECRAWL_API_KEY`；
2. Remote hosted MCP：同一 quickstart 给出 `https://mcp.firecrawl.dev/fc-YOUR-API-KEY/v2/mcp` URL，免本地 Node.js，但把 API key 放进 URL，LDVH 若采用必须有密钥泄漏门禁。

官方 Codex CLI quickstart 说明 Codex 可发现 `firecrawl_search`、`firecrawl_scrape`、`firecrawl_crawl`、`firecrawl_extract` 等工具；Developers & MCP 页面进一步描述 scrape、batch scrape、map、crawl、search 作为 MCP 工具，并说明 MCP 请求使用标准 Firecrawl API rate limits，文档缓存可配置，页面 FAQ 提到默认缓存 15 分钟。

LDVH 对 MCP 的吸收判断是：可以吸收“外部 Web 采集工具以 MCP 暴露给 agent”的运行时扩展模式，但不应默认把 Firecrawl MCP 注册进所有线程。最小合理入口应是按任务启用、按域名/页数/credits 限额、禁止提交 API key、调用后回写来源摘要和验证命令。

### 云服务、自托管与许可证边界

Firecrawl 同时提供 hosted service 和开源仓库。官方 SELF_HOST.md 说明自托管适合安全和合规要求较高、希望数据留在受控环境的组织，但也列出重要限制：自托管当前没有 Fire-engine，缺少处理 IP blocks、robot detection 等高级能力；超出 basic fetch / Playwright 的 scraping methods 需要手工 `.env` 配置。

自托管依赖 Docker、Redis、Playwright service 等组件；AI features，例如 JSON format on scrape 和 `/extract` API，需要配置 OpenAI API key、Ollama 或 OpenAI-compatible API。SELF_HOST.md 还说明连接 cloud service 时 SDK API key 必需，自托管实例中 API key 可选。需要注意的是 SELF_HOST.md 示例仍出现 `http://localhost:3002/v1/crawl`，而官方 API Reference 当前以 v2 为主；后续若 LDVH 做自托管 ADR，必须实际验证自托管 API 版本和云端 v2 能力是否一致。

许可证方面，官方仓库 LICENSE 为 GNU AGPL v3。若 LDVH 只是调用 Firecrawl 云 API 或通过 MCP 使用第三方服务，主要风险是数据、密钥、成本与合规；若 LDVH 自托管、修改、再分发或把其作为网络服务提供给其他用户，则需要额外评估 AGPL v3 义务。

### 输出、成本、限流与合规风险

Firecrawl 对 LDVH 有价值的输出不是“网页全文越多越好”，而是带 provenance 的最小证据包。官方资料显示输出形态至少包括 Markdown、HTML/原始内容、JSON、截图、metadata、sources、search result title/description/url、map links、crawl webhook page payload，以及 schema 化 data。

成本和限流边界应独立建模：

- API Introduction 明确 402 表示 payment required，429 表示 rate limit exceeded，per-plan rate/concurrency limits 需看 Rate Limits；
- Credit Usage API 可读取团队剩余 credits、plan credits 和 billing period，可作为自动化预算门禁输入；
- Crawl 支持 `delay` 和 `maxConcurrency`，可用于尊重站点限制；MCP 请求使用标准 API rate limits；
- Scrape 的 PDF parser 文档写到 PDF 默认按页计费，usage guide 写到 `/scrape` JSON mode 当前为 5 credits/page、`/extract` 为 token-based、`/agent` 为 dynamic pricing 且有每日免费运行口径；这些价格口径可能变化，不能写入 LDVH 长期规则；
- Pricing 页面只应作为“usage-based pricing、free tier、pay-as-you-go、enterprise plans”边界来源，具体数字需每次执行前重新确认。

合规与安全风险主要有四类：

1. robots 与站点条款：Crawl 的 `ignoreRobotsTxt` 和 `robotsUserAgent` 标注为 Enterprise only；LDVH 不应把绕过 robots 当默认能力；
2. 数据保留：Scrape/Crawl 有 `zeroDataRetention` 参数，但需联系 Firecrawl 启用，且某些选项可能冲突；敏感网页不应默认发送给第三方云；
3. 密钥泄漏：remote MCP URL 把 API key 放在 URL 路径中，本地 config 也含密钥，不能进入 Git、Study、日志或截图；
4. 模型抽取误差：`extract`、`agent`、JSON mode、`onlyCleanContent` 等包含 LLM 处理或自动导航，输出必须保留来源和不确定性。

## 建议

### 可吸收到事实模型

LDVH 可吸收 Firecrawl 的“来源证据结构”而非产品对象本身。建议后续为外部网页资料建立统一字段或 docs 约定：

- `source_url`、`source_title`、`source_type`、`fetched_at`、`fetch_tool`、`fetch_mode`、`output_format`、`cache_policy`、`status_code_or_error`；
- 对 Firecrawl 特有结果记录 `scrape_id`、`crawl_id`、`map_limit`、`search_query`、`search_filters`、`crawl_scope`、`source_count`、`credit_budget`、`credit_usage_observed`；
- Study 的 `urls` 继续只写结构化 URL 与中文用途摘要，不写抓取全文；网页正文可进入 docs/sources 或后续专门 SourceSnapshot 对象候选；
- 对 `extract/agent` 输出增加 `extraction_schema`、`model_or_service`、`confidence_notes`、`human_accepted` 等字段候选，避免把结构化 JSON 直接当事实。

不建议把 Firecrawl 自身建成事实模型成员。它更像运行时工具和资料采集 provider；LDVH 事实模型应描述“外部资料证据”和“吸收状态”，而不是绑定某一家服务。

### 可吸收到行动编排

建议把 Firecrawl 能力拆成一个受控行动模式：

1. 研究问题收敛：先写清楚要找什么事实、目标域名、时间范围和禁止抓取范围；
2. 来源发现：优先 `search` 或 `map`，生成候选 URL，不直接整站 `crawl`；
3. 范围门禁：Human/AI 根据域名可信度、页数、成本、robots、敏感性和是否需要登录决定继续；
4. 资料获取：单页用 `scrape`，已知站点小范围用 `crawl`，动态页面单独申请 `interact`；
5. 结构化抽取：只有在 schema 明确、可追溯、可复核时使用 `extract`、`agent` 或 JSON mode；
6. 事实回写：只把摘要、结论边界、URL 列表和验证结果写入 Study；原始材料另放资料区；
7. 强制验证：运行 `fact_validate` 或对应对象校验，记录失败和残留不确定性。

这个模式能服务 AI 第一：让 AI 不必每次重做搜索、清洗、来源整理，但仍保留 V3 正确判断和 V6 强制验证。

### 可吸收到 Code、Web 与运行时扩展

Code 层建议只做适配器和校验，不做事实裁决：

- 增加一个可选 `web_source_provider` 适配层，抽象 `search`、`map`、`scrape`、`crawl_status`、`credit_usage`；
- 为每次调用生成机器可读 manifest，包含输入、输出路径、来源 URL、时间、成本预算和错误；
- 对抓取结果做去重、URL 规范化、标题/摘要提取、正文长度限制、敏感信息扫描和文件大小限制；
- 在 CI 或本地校验中禁止 API key、remote MCP URL、网页全文误入 Study frontmatter。

Web 层建议只展示来源、范围和状态：

- 在 Study 详情页展示结构化 `urls`、来源数量、更新时间、是否人工接受；
- 不在 Web 中提供无限 crawl 按钮，也不让 Web 直接改写事实源；
- 若未来支持资料采集 UI，应采用 job queue + budget + Human Gate + Git 回写的方式。

运行时扩展层可以吸收 MCP 模式：

- Firecrawl MCP 作为任务级可选工具，默认关闭；
- 本地 `npx firecrawl-mcp` 优先于 remote hosted URL，降低密钥出现在 URL 的风险；
- 每个任务设置域名 allowlist、页数上限、credits 上限、timeout 和是否允许 `interact`；
- MCP 工具输出只能作为临时资料，必须经 Study/WorkCase/ADR/Pitfall 等权威对象回写后才稳定。

### 不应吸收的内容

LDVH 不应吸收以下做法：

- 不把 Firecrawl API 成功返回当作事实正确性的充分条件；
- 不把云端 Firecrawl 作为 LDVH core fact_validate、spec 解析或本地运行的硬依赖；
- 不默认启用 `crawlEntireDomain`、`allowExternalLinks`、`ignoreRobotsTxt` 或大范围 crawl；
- 不把 API key、MCP remote URL、cookies、headers、登录态或 private page 内容写入 Git；
- 不复制外部网页全文进 Study；
- 不把 `/agent` 的自主搜索结果直接转为 ADR 或规范条款；
- 不在未做许可证评估前自托管修改版或把 AGPL 代码并入 LDVH 代码库。

## 后续分流

建议后续分流为以下对象，不在本 Study 中直接执行：

| 分流对象 | 建议内容 | 触发理由 |
|---|---|---|
| WorkCase | 设计 LDVH 外部 Web 资料采集最小适配层：provider interface、source manifest、预算字段、URL 去重、Study 回写模板和 fact_validate 串联 | 可直接行动，且能把 Firecrawl 作为一个 provider 测试 |
| WorkCase | 增加密钥泄漏检查：禁止 `fc-` API key、`mcp.firecrawl.dev/fc-` URL、cookies、Authorization headers 进入 Git 文件 | 安全边界明确，适合 Code 校验 |
| ADR | 是否允许 LDVH 正式引入第三方 crawling provider；云服务、MCP、本地 CLI、自托管四种形态的准入门槛 | 涉及外部服务依赖、成本、隐私和合规 |
| ADR | Firecrawl 自托管是否进入 LDVH 候选能力，以及 AGPL v3、Fire-engine 缺口、API v1/v2 差异如何处理 | 涉及许可证和运行成本 |
| Pitfall | “MCP URL 内嵌 API key 被复制到日志/Study/PR” | 高概率安全踩坑 |
| Pitfall | “LLM structured extraction 被误读为已验证事实” | 直接影响 V3 正确判断 |
| docs | 编写 `docs` 或 rules 候选片段：外部网页资料采集报告如何记录来源、时间、范围、失败和未验证项 | 可提升 AI 复读质量 |
| Spark | 保留关于“Web source provider 抽象是否只服务 Study，还是也服务知识地图/运行时扩展”的后续讨论 | 需要架构取舍，暂不宜直接写成规则 |

本报告完成后，spark-0039 的最终关联和三插件横向汇总应由主线程处理。本 Study 只提供 Firecrawl 方向的稳定输入。
