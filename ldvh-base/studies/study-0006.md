---
title: 代码智能索引与知识图谱实践调研
status: active
applicability: 用于 LDVH 非权威代码库索引、关系导航和 Agent 检索边界；明确 canonical facts、Specs、Code
  规则不由索引替代。
validation_summary: 已读取项目 GitHub README 和 Tree-sitter
  公开文档；工具仓库中的语言覆盖、压缩比例等是项目方声明，未在 LDVH 环境独立复测，不能当作性能承诺。
research_question: Codebase Memory MCP 等公开工具如何建立代码知识索引、提供 Agent 查询和团队共享，哪些限制对
  LDVH 有意义？
abstract: 调研 DeusData/codebase-memory-mcp、Tree-sitter 公开资料。Codebase Memory MCP 以
  AST/LSP 等索引建立持久知识图谱，通过 MCP 工具提供代码关系查询，支持本地处理和可选团队图谱工件；其自身说明不内置
  LLM。它适合作为派生索引参考，不是权威事实源。
object_id: study-0006
fact_type_key: study
created_at: '2026-07-19T11:17:49.581725+08:00'
updated_at: '2026-07-23T14:21:35.783731+08:00'
urls:
- ref: https://github.com/DeusData/codebase-memory-mcp
  title: github.com/DeusData/codebase-memory-mcp
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://tree-sitter.github.io/tree-sitter/
  title: tree-sitter.github.io/tree-sitter/
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://github.com/tree-sitter/tree-sitter
  title: github.com/tree-sitter/tree-sitter
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
---

## 研究问题

Codebase Memory MCP 等公开工具如何建立代码知识索引、提供 Agent 查询和团队共享，哪些限制对 LDVH 有意义？
## 输入、方法与观察边界

本报告读取并对照了以下外部公开资料：https://github.com/DeusData/codebase-memory-mcp、https://tree-sitter.github.io/tree-sitter/、https://github.com/tree-sitter/tree-sitter。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Codebase Memory MCP 公开描述了本地代码解析、持久图谱、MCP 查询工具、可选 graph artifact 和无内置 LLM 的分工。Tree-sitter 提供增量语法树基础。图谱适合回答“代码关系是什么”，但不能单独回答“当前规范是什么”“是否获 Human 授权”或“某建议是否成立”。
## 结论与限制

LDVH 可以吸收“索引是可重建的导航层、查询接口应有明确边界、共享图谱应可追溯版本”的原则。限制包括解析误差、语言/版本覆盖、图谱过期和工具仓库声明未独立验证；任何索引命中都需要回到当前文件和来源复核。
## 建议

把索引定位为非权威关系导航，记录生成版本与失效条件，不写回 canonical facts；Web/Agent 结果必须显示“索引推断”与原始文件链接。
## 后续分流

供 Spark-0016；如要引入具体 MCP 或索引器，另建 WorkCase 做许可、隐私、性能和回读验证。
