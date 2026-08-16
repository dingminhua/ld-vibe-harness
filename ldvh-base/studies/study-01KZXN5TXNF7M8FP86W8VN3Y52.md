---
title: 主流 Agent 过程输出与 Human 可观察性调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: OpenAI 的非交互/App Server/Structured Outputs/Tracing 公开能力如何支持 Agent 过程的机器读取、人类观察和证据复核？
abstract: 调研 OpenAI Codex 非交互与 App Server 文档、Structured Outputs 指南和 Agents tracing 文档。公开模式是结构化事件/输出、稳定 schema、trace/span 关联和宿主按需呈现；机器可读性与人类可观察性是两层契约，不应把 UI 摘要当作完整证据。
object_id: study-01KZXN5TXNF7M8FP86W8VN3Y52
object_uid: 019ffb52-ebb5-79e8-87d9-06e23751f8a2
fact_type_key: study
created_at: '2026-07-19T11:17:46.933030+08:00'
updated_at: '2026-08-16T21:42:45.620720Z'
urls:
- ref: https://developers.openai.com/codex/noninteractive
  title: developers.openai.com/codex/noninteractive
  summary: 曾用于旧研究的 Codex 非交互文档；不单独支持 LDVH 的过程输出设计。
- ref: https://developers.openai.com/codex/app-server
  title: developers.openai.com/codex/app-server
  summary: 曾用于旧研究的 Codex App Server 文档；不单独支持当前观察面。
- ref: https://developers.openai.com/api/docs/guides/structured-outputs
  title: developers.openai.com/api/docs/guides/structured-outputs
  summary: 曾用于旧研究的 Structured Outputs 文档；不单独决定事实对象字段。
- ref: https://openai.github.io/openai-agents-python/tracing/
  title: openai.github.io/openai-agents-python/tracing/
  summary: 曾用于旧研究的 tracing 文档；不单独证明本项目具备追踪能力。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:21.700352Z'
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

OpenAI 的非交互/App Server/Structured Outputs/Tracing 公开能力如何支持 Agent 过程的机器读取、人类观察和证据复核？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://developers.openai.com/codex/noninteractive、https://developers.openai.com/codex/app-server、https://developers.openai.com/api/docs/guides/structured-outputs、https://openai.github.io/openai-agents-python/tracing/。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

非交互模式和 App Server 面向宿主/自动化提供结构化交互；Structured Outputs 以 schema 约束模型输出；Tracing 把运行过程组织为可关联的 trace/span。共同要求是消费者处理不完整、失败和版本差异，而不是只显示“成功”文本。
### 旧研究的限制

LDVH 应把原始事件/结果、最终终态、证据位置和人类阅读投影分层保存；Web 读模型可以友好表达，但不能成为事实源或丢失原始边界。限制是外部文档没有规定 LDVH 的字段命名、存储介质或 Human Gate。
## 建议

继续完善 run ID、原始输出、exit code、unknown/evidence incomplete 和 Web 回读；为每个机器字段保留人类解释和来源，避免摘要覆盖原始证据。
## 后续分流

供 Spark-0012、Spark-0014、Spark-0015；具体实现变更需在 Code/tests/Web 各自受控落地。
