---
title: AI Agent 输出格式治理与 LDVH 审计报告吸收调研
status: active
urls:
- ref: https://www.trae.ai/
  title: Trae SOLO mode
  summary: 用于确认 SOLO mode 把需求理解、任务拆解、代码生成、测试、预览和部署组织为阶段化 agent 工作流。
- ref: https://docs.trae.ai/
  title: Trae Skills
  summary: 用于确认 Skill 通过 SKILL.md、instructions、scripts 和 resources 形成按需加载的可复用能力。
- ref: https://github.com/bytedance/trae-agent
  title: bytedance/trae-agent
  summary: 用于确认 Lakeview concise step summaries、trajectory recording、工具生态和交互式 CLI 等 agent 输出组织线索。
- ref: https://docs.cursor.com/plan-mode
  title: Cursor Plan Mode
  summary: 用于确认 Plan Mode 会研究代码库、生成包含文件路径和代码引用的 Markdown 计划，并允许用户编辑和保存。
- ref: https://docs.anthropic.com/en/docs/claude-code/output-styles
  title: Claude Code output styles
  summary: 用于确认 Claude Code 支持内置与自定义 output styles，通过系统提示附加指令改变角色、语气和输出格式。
- ref: https://docs.anthropic.com/en/docs/claude-code/common-workflows
  title: Claude Code common workflows
  summary: 用于确认 Claude Code plan mode 会先读文件并提出计划，在获得批准前不修改代码。
- ref: https://github.com/features/copilot
  title: GitHub Copilot coding agent sessions
  summary: 用于确认 Copilot coding agent 使用后台 session、PR、session log 和 Human review 组织输出。
- ref: https://docs.devin.ai/
  title: Devin Desktop Cascade
  summary: 用于确认 Cascade 通过计划、Todo List、工具调用、checkpoint、lint 集成和实时上下文组织 agent 输出。
- ref: https://docs.windsurf.com/
  title: Windsurf Planning Mode
  summary: 用于确认 Planning Mode 会创建和更新本地 Markdown 计划文件，并把长期计划和短期行动分层。
- ref: https://docs.replit.com/
  title: Replit Agent Plan mode
  summary: 用于确认 Plan mode 以规划、任务列表和架构讨论为主，不直接修改代码或数据。
- ref: https://developers.openai.com/codex/noninteractive
  title: OpenAI Codex non-interactive mode
  summary: 用于确认 Codex CLI 可输出 JSONL 事件，并支持 output schema 约束最终输出。
- ref: https://developers.openai.com/codex/app-server
  title: OpenAI Codex App Server
  summary: 用于确认 Codex App Server 通过 JSON-RPC 和 thread/turn/item 事件流提供可嵌入的结构化过程接口。
- ref: https://openai.github.io/openai-agents-python/tracing/
  title: OpenAI Agents SDK tracing
  summary: 用于确认 Agents SDK tracing 可记录模型调用、工具调用、handoff、guardrail 和自定义 span 等可观测过程。
- ref: https://platform.openai.com/docs/guides/structured-outputs
  title: OpenAI Structured Outputs
  summary: 用于确认结构化输出可通过 JSON Schema 约束模型返回，适合机器消费和系统集成。
research_intent: 调研主流 AI agent 产品的输出组织方式，为 LDVH 定义人类可读的简洁输出契约和机器可读的 Agent Output Envelope。
research_question: 主流 AI agent 产品如何组织 agent 输出？为什么 Trae 的输出显得更有条理？LDVH 应如何定义自己的输出契约和过程信封？
abstract: 调研 Trae、Cursor、Claude Code、OpenAI Codex、GitHub Copilot、Windsurf/Cascade、Devin 和 Replit 等主流 agent 产品的输出组织方式。结论是：Trae 输出显得更有条理，主要因为它把 agent 过程渲染成计划、任务、工具面板、命令卡片、阶段状态和结果摘要，而不是只依赖模型自然语言。Codex 可以通过明确输出契约、AGENTS/Skill、plan/progress/final discipline 达到相近的人类可读效果；在 JSONL 事件流、output schema、App Server、structured outputs 和 traces 层，Codex/OpenAI 生态还具备更先进的机器可消费格式。
recommendation_summary: LDVH 应把 agent 输出分成两层治理：第一层是人类可读的简洁输出契约，用于 Codex 对话、review、handoff 和最终汇报；第二层是机器可读的 Agent Output Envelope，用事件、状态、计划项、工具调用、验证证据、风险、Human Gate 和事实源吸收结果支撑 Web、Code、Hook 和未来编排。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:46.417702Z'
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
  at: '2026-08-16T21:30:34.415045Z'
- at: '2026-08-17T13:05:14.362981Z'
  summary: 字段减法迁移：删除 action_relevance 字段（规范修订配套迁移）
  signature:
    product_name: WorkBuddy
    model_name:
    agent_runtime_name: codebuddy
object_uid: 019ffb52-ebb5-7ead-a694-70845998ef8c
object_id: study-01KZXN5TXNFTPTD53GGHCSHVWC
fact_type_key: study
created_at: '2026-07-24T13:30:00+08:00'
updated_at: '2026-08-17T13:05:14.362981Z'
---

## 研究问题

本报告回答两个问题：

1. 主流 AI agent 产品现在如何组织输出，尤其是计划、执行、工具调用、状态、验证和最终结果；
2. LDVH 应如何定义自己的输出契约和过程信封，才能既让 Human 容易阅读，又让 Code 和 Web 可以机器消费。

## 输入与边界

本报告调研 Trae、Cursor、Claude Code、OpenAI Codex、GitHub Copilot、Windsurf/Cascade、Devin 和 Replit 八个 Agent 产品的输出组织方式。

边界如下：

- 本报告不评测这些产品的模型能力或开发体验；
- 本报告只关注输出组织方式，不关注产品定价、部署方式或市场表现；
- 本报告的观察时点为 2026-06 至 2026-07。

## 关键发现

### Trae 输出显得更有条理是因为产品化的信息架构

Trae 的输出组织方式在产品层面最完整：SOLO mode 把需求理解、任务拆解、代码生成、测试、预览和部署组织为阶段化工作流；工具面板、命令卡片、任务状态提醒和代码变更总结让 Human 可以扫描式理解进展。计划、任务列表、工具调用和结果摘要各自有独立的渲染区域，不会混在自然语言流中。

### Codex 可以通过输出契约达到相近效果

Codex 虽然没有 Trae 那样的产品化信息架构，但通过明确的输出契约（Goal/Context/Constraints/Done When）、AGENTS.md 持久指导、Skill 可复用流程、plan/progress/final 的阶段纪律可以达到相近的人类可读效果。在机器可读性方面，Codex 生态的 JSONL 事件流、output schema、App Server 的 JSON-RPC 事件、Structured Outputs 的 JSON Schema 和 Agents SDK tracing 提供了更先进的结构化过程接口。

### 其他产品各有侧重

Cursor 的 Plan Mode 生成可编辑的 Markdown 计划；Claude Code 的 output styles 支持自定义角色和语气；Copilot 使用后台 session 和 PR 组织输出；Devin 的 Cascade 通过计划和 Todo List 组织；Windsurf 的 Planning Mode 把计划和行动分层；Replit 的 Plan mode 以规划和任务列表为主。没有一个产品同时具备 Trae 的产品化信息架构和 Codex 的机器可读性深度。

## 建议

### LDVH 应定义双层输出契约

第一层是人类可读的简洁输出契约，用于 Codex 对话、review、handoff 和最终汇报。第二层是机器可读的 Agent Output Envelope，用事件、状态、计划项、工具调用、验证证据、风险、Human Gate 和事实源吸收结果支撑 Web、Code、Hook 和未来编排。

### 输出契约不应绑定特定环境

双层输出契约是环境无关的设计。Codex 环境下可以通过 prompt 纪律和 AGENTS.md 实现；Trae 环境下可以通过 SOLO Agent 和 Skill 实现。契约本身不绑定任何一种产品。

### 过程信封不应替代事实源

Agent Output Envelope 是运行期过程记录，不是长期事实源。过程信封中的信息只有被回写到 Git Working Tree 中的事实对象后，才能成为稳定事实。

## 后续分流

| 分流目标 | 建议动作 | 理由 |
|---|---|---|
| WorkCase | 建立"Agent 输出契约试点"工作项 | 在具体 WorkCase 中验证双层输出契约 |
| Spark | 记录 Agent Output Envelope 的字段设计问题 | 需要更详细的设计讨论才能形成规范 |
| 无需对象化 | 当前不创建新的事实类型 | 输出契约可通过现有 WorkCase 结构承载 |
