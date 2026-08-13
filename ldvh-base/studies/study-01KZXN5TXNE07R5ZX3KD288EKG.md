---
title: 代码智能索引与知识图谱实践调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: Codebase Memory MCP 等公开工具如何建立代码知识索引、提供 Agent 查询和团队共享，哪些限制对 LDVH 有意义？
abstract: 调研 DeusData/codebase-memory-mcp、Tree-sitter 公开资料。Codebase Memory MCP 以 AST/LSP 等索引建立持久知识图谱，通过 MCP 工具提供代码关系查询，支持本地处理和可选团队图谱工件；其自身说明不内置 LLM。它适合作为派生索引参考，不是权威事实源。
object_id: study-01KZXN5TXNE07R5ZX3KD288EKG
object_uid: 019ffb52-ebb5-700f-82ff-a39b44843a70
fact_type_key: study
created_at: '2026-07-19T11:17:49.581725+08:00'
updated_at: '2026-08-13T15:03:57Z'
urls:
- ref: https://github.com/DeusData/codebase-memory-mcp
  title: github.com/DeusData/codebase-memory-mcp
  summary: 曾用于旧研究的 Codebase Memory MCP 仓库；不单独证明索引适用于 LDVH。
- ref: https://tree-sitter.github.io/tree-sitter/
  title: tree-sitter.github.io/tree-sitter/
  summary: 曾用于旧研究的 Tree-sitter 文档；不单独保证解析覆盖或质量。
- ref: https://github.com/tree-sitter/tree-sitter
  title: github.com/tree-sitter/tree-sitter
  summary: 曾用于旧研究的 Tree-sitter 仓库；不单独支持当前索引实现。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:24.371066Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
---

## 研究问题

Codebase Memory MCP 等公开工具如何建立代码知识索引、提供 Agent 查询和团队共享，哪些限制对 LDVH 有意义？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://github.com/DeusData/codebase-memory-mcp、https://tree-sitter.github.io/tree-sitter/、https://github.com/tree-sitter/tree-sitter。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Codebase Memory MCP 公开描述了本地代码解析、持久图谱、MCP 查询工具、可选 graph artifact 和无内置 LLM 的分工。Tree-sitter 提供增量语法树基础。图谱适合回答“代码关系是什么”，但不能单独回答“当前规范是什么”“是否获 Human 授权”或“某建议是否成立”。
### 旧研究的限制

LDVH 可以吸收“索引是可重建的导航层、查询接口应有明确边界、共享图谱应可追溯版本”的原则。限制包括解析误差、语言/版本覆盖、图谱过期和工具仓库声明未独立验证；任何索引命中都需要回到当前文件和来源复核。
## 建议

把索引定位为非权威关系导航，记录生成版本与失效条件，不写回 canonical facts；Web/Agent 结果必须显示“索引推断”与原始文件链接。
## 后续分流

供 Spark-0016；如要引入具体 MCP 或索引器，另建 WorkCase 做许可、隐私、性能和回读验证。
