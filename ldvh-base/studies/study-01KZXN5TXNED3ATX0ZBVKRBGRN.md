---
title: WorkBuddy 专家团团队交互模式与 LDVH 学习方向调研
status: active
urls:
- ref: https://workbuddy.ai/
  title: WorkBuddy 官网
  summary: 用于确认 WorkBuddy 的专家团定位、100+ 领域专家、自然语言创建专家团和 leader/总监角色结构。
- ref: https://workbuddy.ai/features
  title: WorkBuddy Features
  summary: 用于确认专家中心、专家广场、自然语言创建专家团、专家绑定工具链和企业资产沉淀等产品能力。
research_intent: 调研 WorkBuddy 专家团团队交互模式，分析 LDVH 后续在行动编排和 Web 表达方面应学习和吸收的方向。
research_question: WorkBuddy 的专家团团队交互模式对 LDVH 有什么学习价值？LDVH 应如何吸收其角色契约、任务编排和结果整合能力？
abstract: WorkBuddy 值得学习的不是"多开几个 Agent"，而是把专家角色、方法论、工具链、团队席位、共享任务列表、成员状态、直接沟通、计划审批、后台任务和结果整合显性化。LDVH 应吸收为"团队编排层"的设计方向：角色契约、任务卡、计划门禁、成员消息、状态投影、质量复核和成本/权限边界都应成为可追踪结构；但 WorkBuddy 的专家团运行状态、截图 UI 或外部工具输出不能替代 LDVH 的事实源。
recommendation_summary: LDVH 应把 WorkBuddy 式团队交互作为下一阶段行动编排和 Web 表达的重要参考。优先学习方向包括 Role Contract、Team Session/Task List、Result Review、TaskOutput 状态投影、专家/Skill/MCP 组合边界、Human Gate 与权限分层。正式落地前应先形成 WorkCase 或 ADR，避免把外部产品的专家团直接写成 LDVH 事实模型规则。
object_id: study-01KZXN5TXNED3ATX0ZBVKRBGRN
object_uid: 019ffb52-ebb5-7346-ad74-1f5ee785c315
fact_type_key: study
created_at: '2026-07-24T13:30:00+08:00'
updated_at: '2026-08-13T15:03:57Z'
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:43.462053Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
---

## 研究问题

本报告调研 WorkBuddy 专家团团队交互模式，回答两个问题：

1. WorkBuddy 的专家团模式有什么值得 LDVH 学习的设计；
2. LDVH 应如何吸收这些设计，哪些可以直接参考，哪些需要转化，哪些不应吸收。

## 输入与边界

本报告输入来自 WorkBuddy 官网和公开资料。

边界如下：

- 本报告不评估 WorkBuddy 的产品质量或市场表现；
- 本报告不把 WorkBuddy 的专家团运行状态、截图 UI 或外部工具输出作为 LDVH 事实源；
- 本报告只关注角色契约、任务编排、结果整合和团队协作这类可抽象的设计模式。

## 关键发现

### WorkBuddy 值得学习的是团队编排的显性化

WorkBuddy 的产品设计把专家角色、方法论、工具链、团队席位、共享任务列表、成员状态、直接沟通、计划审批、后台任务和结果整合全部显性化。这不是"多开几个 Agent"，而是把团队协作从隐式对话变为显式结构。

对 LDVH 的启发是：当前 V4 的行动编排（03 规范）和 WorkCase 流程定义了基本的执行秩序，但缺少团队编排层。角色契约、任务卡、计划门禁、成员消息、状态投影、质量复核和成本/权限边界都应成为可追踪结构。

### 主控角色应显式存在

WorkBuddy 的 leader/总监角色印证了 LDVH 需要把主控定义为调度者、仲裁者、证据回收者和事实源写回责任主体。当前 V4 的 03 行动编排规范没有定义主控角色的职责，这是一个缺口。

### 创建角色团队可以交互式进行

WorkBuddy 支持用自然语言逐步创建专家团，而不是要求用户一次性写完完整配置。LDVH 后续可以让 AI 逐步询问领域、目标、角色、工具、权限、输出格式、审查规则和 Human Gate 条件，而不是要求 Human 一次性定义完整 Role Contract。

## 建议

### 在 03 行动编排规范中补充主控角色定义

建议在 03 规范中定义主控角色的职责：调度者、仲裁者、证据回收者和事实源写回责任主体。这不是新增顶层组件，而是在现有行动编排框架中补充一个角色定义。

### 通过 WorkCase 验证团队编排实践

在通过 WorkCase 实践团队编排之前，不把 WorkBuddy 的专家团模式直接写成规范。建议先创建一个 WorkCase 试点，定义角色契约、任务卡和结果整合的最小可行实践。

### 角色契约不绑定特定环境

WorkBuddy 的专家团是产品化实现，LDVH 的角色契约应是环境无关的。Codex 环境下可以通过显式 subagent 委派模拟，Trae 环境下可以通过 SOLO Agent 调用自定义智能体模拟。角色契约本身不绑定任何一种实现。

## 后续分流

| 分流目标 | 建议动作 | 理由 |
|---|---|---|
| WorkCase | 建立"团队编排试点"工作项 | 验证角色契约、任务卡和结果整合的最小可行实践 |
| ADR | 决策"主控角色是否应纳入 03 规范" | 涉及行动编排规范的设计归属 |
| 无需对象化 | 当前不创建新的事实类型 | 角色契约可以纳入现有 WorkCase 结构 |
