---
title: Codebase Memory MCP 插件调研与 LDVH 吸收建议
status: active
urls:
- ref: https://github.com/DeusData/codebase-memory-mcp
  title: DeusData/codebase-memory-mcp
  summary: 用于确认 Codebase Memory MCP 的工具定位、安装方式、依赖树、tree-sitter 解析器列表、LSP 语言覆盖和已知问题。
- ref: https://github.com/modelcontextprotocol/specification
  title: MCP Specification
  summary: 用于确认 MCP 协议的能力边界、资源/工具/提示词模型和工具调用生命周期，支撑 LDVH 对 MCP 作为运行时扩展的判断。
- ref: https://tree-sitter.github.io/tree-sitter/
  title: tree-sitter
  summary: 用于确认 tree-sitter 的解析范围、语法查询能力和语言覆盖，支撑本地索引可行性判断。
- ref: https://microsoft.github.io/language-server-protocol/
  title: LSP Specification
  summary: 用于确认 LSP 的语义令牌、跳转定义、引用查找和诊断能力，支撑 Hybrid LSP 方案的可行性。
- ref: https://www.sqlite.org/
  title: SQLite
  summary: 用于确认 SQLite 的本地存储、全文搜索和并发控制能力，支撑本地图谱索引底层存储的判断。
research_intent: 调研 Codebase Memory MCP 插件的能力和限制，判断 LDVH 是否可以吸收其本地代码知识图谱能力。
research_question: Codebase Memory MCP 的本地代码知识图谱能力对 LDVH 的代码探索和事实源组织有什么启发？哪些可以吸收，哪些不应吸收？
abstract: Codebase Memory MCP 通过 tree-sitter、Hybrid LSP、SQLite 图存储、BM25/语义/结构查询、变更影响分析，把代码探索从文件级 grep/read 转为图谱级结构查询。对 LDVH 的核心启发不是直接引入该工具作为事实源，而是吸收"本地图谱索引 + 查询工具 + 非阻塞发现提醒 + 可提交图谱快照 + 明确事实源边界"的能力形态。
recommendation_summary: Codebase Memory MCP 适合被视为 AI 代码探索的运行时扩展和 Code 辅助索引，而不是 LDVH 的最终事实源。LDVH 可吸收其结构化代码图谱、跨仓库索引、影响分析、Agent 接入安装、非阻塞 hook、团队共享索引快照、图谱 UI 和本地隐私边界；不应吸收其"运行时索引即事实"的隐含风险，也不应让 MCP 查询结果替代 specs、ldvh-base 工作对象、Git 提交记录或现有 validator。
object_id: study-01KZXN5TXNE1ZA203F5Y0N1KH4
object_uid: 019ffb52-ebb5-707e-a100-6f2f8150ce24
fact_type_key: study
created_at: '2026-07-24T13:30:00+08:00'
updated_at: '2026-08-16T21:42:45.620720Z'
action_relevance: 设计或评估代码探索、事实源组织方案时，考虑本地图谱索引而非直接引入外部工具作为事实源
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:40.672963Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
---

## 研究问题

本报告调研 Codebase Memory MCP 插件，回答两个问题：

1. Codebase Memory MCP 的能力和限制是什么，尤其是本地代码知识图谱的构建和查询方式；
2. LDVH 是否可以吸收其能力，哪些应该吸收，哪些不应吸收，以及如何在事实源边界内消化。

## 输入与边界

本报告输入来自 Codebase Memory MCP 的 GitHub 仓库文档、MCP 协议规范、tree-sitter 文档、LSP 规范和 SQLite 文档。

边界如下：

- 本报告不进行源码级审计和本地安装验证；
- 性能、语言覆盖与安全承诺均按上游文档作为来源边界；
- 本报告不评估其他 MCP 插件或知识图谱工具。

## 关键发现

### Codebase Memory MCP 的核心能力

Codebase Memory MCP 是把代码探索从文件级 grep/read 转为图谱级结构查询的 MCP 工具。它通过 tree-sitter 进行语法解析、Hybrid LSP 提供语义信息、SQLite 图存储建立本地索引，支持 BM25 全文搜索、语义搜索和结构化查询，并提供变更影响分析。它支持多 Agent 自动配置和团队共享索引快照。

### 对 LDVH 的启发

Codebase Memory MCP 最值得吸收的不是工具本身，而是它的能力形态：本地图谱索引可以让 AI 的代码探索从"读文件"变为"查结构"，这对 V4 的代码相关研究和核验工作有加速作用。非阻塞发现提醒可以在不打断主线程的情况下提示相关代码变更。可提交的图谱快照让索引状态可以像代码一样被版本管理。

但不应吸收的是"运行时索引即事实"的隐含风险。MCP 查询结果是派生视图，不是事实源。LDVH 的事实源边界（00 §5）要求稳定事实必须由 Git Working Tree 中的当前文件承载，MCP 索引不能替代。

### 与 V4 当前做法的关系

V4 当前使用 localFactReader 直读 YAML/Markdown 文件，没有建立代码知识图谱。Codebase Memory MCP 可以补充代码层面的快速检索能力，但不改变事实源的读取方式。它适合作为运行时扩展（05 规范中的 Helper 能力补充），而不是新的事实类型。

## 建议

### 吸收本地图谱索引的能力形态

建议在 Code 层面考虑引入类似 tree-sitter 的本地解析能力，用于加速代码探索和影响分析。这不要求引入完整的 MCP 工具，可以在 V4 的 Helper CLI 中增加一个轻量的代码结构查询操作。

### 明确 MCP 与事实源的边界

建议在 05 事实模型基础规范或 06 运行时扩展规范中明确：MCP 查询结果、图谱索引和派生视图不替代事实源。事实源只能是 Git Working Tree 中的当前文件。

### 暂不引入 MCP 作为依赖

当前 V4 的代码探索需求可以通过 localFactReader 和 Helper CLI 覆盖。引入 MCP 需要额外的安装、配置和维护成本，建议在 V4 的代码检索需求增长到现有能力无法覆盖时再考虑。

## 后续分流

| 分流目标 | 建议动作 | 理由 |
|---|---|---|
| 无需对象化 | 当前暂不引入 MCP | V4 的代码探索需求可通过现有能力覆盖 |
| Spark | 如果后续代码检索需求增长到现有能力无法覆盖 | 记录触发的具体场景和需求 |
| WorkCase | 如果决定引入轻量代码结构查询能力 | 以有界行动验证技术方案 |
