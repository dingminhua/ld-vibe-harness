---
title: Task Master AI 任务编排模型调研
status: active
applicability: 用于比较 LDVH WorkCase 控制面、任务依赖、研究入口和上下文开销；不引入 Task Master 的字段或执行权。
validation_summary: 已读取项目 README 和官方文档入口，观察到其当前公开安装、MCP
  配置、PRD、依赖、研究命令及工具加载模式；未安装或运行 Task Master。
research_question: Task Master AI 当前公开文档如何把 PRD、任务依赖、研究、标签/工作流与 MCP 工具组织成 AI
  任务管理？
abstract: 调研 Task Master AI GitHub README 与官方文档入口。其公开模型以 PRD/需求解析生成任务、任务依赖与
  next/show/expand/research 等操作为核心，并通过 MCP
  接入多个编辑器；支持按模式选择工具数量以降低上下文成本。它是外部产品研究，不证明其任务状态可直接替代 LDVH WorkCase。
object_id: study-0007
fact_type_key: study
created_at: '2026-07-19T11:17:52.509274+08:00'
updated_at: '2026-07-23T14:21:35.783731+08:00'
urls:
- ref: https://github.com/eyaltoledano/claude-task-master
  title: github.com/eyaltoledano/claude-task-master
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://docs.task-master.dev/
  title: docs.task-master.dev
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://docs.task-master.dev/introduction
  title: docs.task-master.dev/introduction
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
---

## 研究问题

Task Master AI 当前公开文档如何把 PRD、任务依赖、研究、标签/工作流与 MCP 工具组织成 AI 任务管理？
## 输入、方法与观察边界

本报告读取并对照了以下外部公开资料：https://github.com/eyaltoledano/claude-task-master、https://docs.task-master.dev/、https://docs.task-master.dev/introduction。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

README 展示了 MCP/CLI 两种接入，建议以 PRD 作为复杂项目起点，并提供 parse-prd、list、next、show、expand、research、move 等任务操作。MCP 工具可按 all/standard/core/custom 模式加载，以控制上下文成本。任务依赖与标签/工作流是其组织复杂项目的重要结构。
## 结论与限制

可借鉴的是“需求文档到任务分解、显式依赖、研究动作、上下文预算”四类能力；不能直接吸收其状态、MCP 工具总数或模型配置，因为这些属于外部产品实现且需要与 LDVH WorkCase/Human Gate 对齐。
## 建议

先用 Task Master 作为比较样本，检查 LDVH 是否缺少任务依赖可视化、研究动作和上下文预算；任何字段吸收先做全局查重与单一权威设计。
## 后续分流

供 Spark-0008；若决定试用，建立独立 WorkCase，隔离 API keys、MCP 权限和数据出口。
