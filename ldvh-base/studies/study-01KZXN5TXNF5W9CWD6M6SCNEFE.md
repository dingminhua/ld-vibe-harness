---
title: OpenAI Codex Harness Engineering 与 Symphony 调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: OpenAI 的 Harness Engineering 与 Symphony 公开实践如何把 Agent 工作变成可验证、可编排的工程控制面？
abstract: 调研 OpenAI Harness Engineering 文章与 Symphony 开源编排介绍。两者都强调环境、脚手架、反馈循环、结构化工具和可观察性；Symphony 进一步把 issue tracker 作为控制面，为任务分配隔离工作区并要求人工审查。结论是过程控制和证明材料比“让 Agent 自由写代码”更关键。
object_id: study-01KZXN5TXNF5W9CWD6M6SCNEFE
object_uid: 019ffb52-ebb5-7978-9671-a6a1b2cab9ee
fact_type_key: study
created_at: '2026-07-19T11:17:42.310359+08:00'
updated_at: '2026-08-13T15:03:57Z'
urls:
- ref: https://openai.com/index/harness-engineering/
  title: openai.com/index/harness-engineering/
  summary: 曾用于旧研究的 Harness Engineering 文章；不单独证明 LDVH 的编排闭环。
- ref: https://openai.com/index/open-source-codex-orchestration-symphony/
  title: openai.com/index/open-source-codex-orchestration-symphony/
  summary: 曾用于旧研究的 Symphony 文章；不单独支持本项目的任务模型。
- ref: https://github.com/openai/symphony
  title: github.com/openai/symphony
  summary: 曾用于旧研究的 Symphony 仓库；不单独证明其行为适用于 LDVH。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:16.205134Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
---

## 研究问题

OpenAI 的 Harness Engineering 与 Symphony 公开实践如何把 Agent 工作变成可验证、可编排的工程控制面？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://openai.com/index/harness-engineering/、https://openai.com/index/open-source-codex-orchestration-symphony/、https://github.com/openai/symphony。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Harness Engineering 把人的主要工作放到环境、脚手架、反馈循环、工具/文档/可观测性和机械边界上，并用自定义 linter/结构测试约束架构边界。Symphony 以 issue tracker 作为控制面，为每项工作创建 Agent 与 workspace，要求人工 review，并明确并非所有任务都适合自动编排。
### 旧研究的限制

对 LDVH 最有价值的不是复制一个编排器，而是把“目标、状态、工作区、反馈、证明、人工复核”串成闭环，并保留任务不适合自动化时的退出路径。限制是公开文章展示的是特定组织和工具上下文，不能证明同一闭环在 LDVH 上已经成立。
## 建议

把 WorkCase 作为可观察控制面，补齐工作项状态、验证证据、停止条件和“不适合自动编排”的分流；把 linter/结构测试作为候选机械门禁而非 AI 判断替代物。
## 后续分流

供 Spark-0008、Spark-0009；具体字段和运行时接入必须另开 WorkCase，并通过现有 Git/Hook/Human Gate。
