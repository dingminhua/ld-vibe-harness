---
id: study-0017
type: study
title: AI Agent 输出格式治理与 LDVH 审计报告吸收调研
status: active
created: '2026-07-03T14:39:55+08:00'
updated: '2026-07-03T14:39:55+08:00'
summary: |
  本 Study 调研 Trae、Cursor、Claude Code、OpenAI Codex、GitHub Copilot、Windsurf/Cascade、Devin 和 Replit 等主流 agent 产品的输出组织方式，并吸收一份 LDVH v3 specs 审计报告。结论是：Trae 输出显得更有条理，主要因为它把 agent 过程渲染成计划、任务、工具面板、命令卡片、阶段状态和结果摘要，而不是只依赖模型自然语言。Codex 可以通过明确输出契约、AGENTS/Skill、plan/progress/final discipline 达到相近的人类可读效果；在 JSONL 事件流、output schema、App Server、structured outputs 和 traces 层，Codex/OpenAI 生态还具备更先进的机器可消费格式。对 LDVH 来说，下一步不应只追求“更漂亮的聊天回复”，而应定义人类可读摘要和机器可读过程信封的双层输出，并把审计报告分流为 Human Gate 与后续 WorkCase。
user_intent: |
  Human 要求新增一个 Spark 和一个 Study：一方面在互联网上调研主流 AI agent 的输出格式，解释 Trae 输出为什么显得有条理、Codex 是否可以做到、是否存在更先进的格式；另一方面阅读一份 LDVH v3 specs 审计报告并判断如何吸收。
conclusion: |
  LDVH 应把 agent 输出分成两层治理：第一层是人类可读的简洁输出契约，用于当前 Codex 对话、review、handoff 和最终汇报；第二层是机器可读的 Agent Output Envelope，用事件、状态、计划项、工具调用、验证证据、风险、Human Gate 和事实源吸收结果支撑 Web、Code、Hook 和未来编排。Trae 的优势主要是产品化的信息架构；Codex 可以在当前交互中模仿这种结构，也可以通过 OpenAI 的 JSONL、schema、App Server 和 tracing 走向更强的系统集成。审计报告应先作为 Study 输入，不直接替代 specs 权威；高优先级冲突和失控章节应进入 Human Gate 和后续 WorkCase。
urls:
  - ref: https://docs.trae.ai/ide/solo-mode
    title: "Trae SOLO mode"
    summary: |
      Trae 官方文档，用于确认 SOLO mode 把需求理解、任务拆解、代码生成、测试、预览和部署组织为阶段化 agent 工作流。
  - ref: https://docs.trae.ai/ide/changelog?_lang=zh
    title: "Trae IDE changelog"
    summary: |
      Trae 官方变更记录，用于确认 Agent、SOLO Agent、/plan、/spec、工具面板、命令卡片、任务状态提醒和代码变更总结等输出组织能力。
  - ref: https://docs.trae.ai/ide/skills?_lang=en
    title: "Trae Skills"
    summary: |
      Trae 官方文档，用于确认 Skill 通过 SKILL.md、instructions、scripts 和 resources 形成按需加载的可复用能力。
  - ref: https://github.com/bytedance/trae-agent
    title: "bytedance/trae-agent"
    summary: |
      Trae Agent 开源仓库，用于确认 Lakeview concise step summaries、trajectory recording、工具生态和交互式 CLI 等 agent 输出组织线索。
  - ref: https://github.com/bytedance/trae-agent/blob/main/docs/TRAJECTORY_RECORDING.md
    title: "Trae Agent Trajectory Recording"
    summary: |
      Trae Agent 文档，用于确认 trajectory 记录 LLM 交互、执行步骤、工具调用、结果、反思和错误等结构化过程信息。
  - ref: https://cursor.com/blog/plan-mode
    title: "Cursor Plan Mode"
    summary: |
      Cursor 官方博客，用于确认 Plan Mode 会研究代码库、生成包含文件路径和代码引用的 Markdown 计划，并允许用户编辑和保存。
  - ref: https://cursor.com/blog/agent-best-practices
    title: "Cursor Agent best practices"
    summary: |
      Cursor 官方博客，用于确认 agent harness、计划优先、可验证目标、Debug Mode、Cloud Agent、PR 和 review workflow 的输出组织方式。
  - ref: https://docs.anthropic.com/en/docs/claude-code/output-styles
    title: "Claude Code output styles"
    summary: |
      Anthropic 官方文档，用于确认 Claude Code 支持内置与自定义 output styles，通过系统提示附加指令改变角色、语气和输出格式。
  - ref: https://docs.anthropic.com/en/docs/claude-code/common-workflows
    title: "Claude Code common workflows"
    summary: |
      Anthropic 官方文档，用于确认 Claude Code plan mode 会先读文件并提出计划，在获得批准前不修改代码。
  - ref: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/start-copilot-sessions
    title: "GitHub Copilot coding agent sessions"
    summary: |
      GitHub 官方文档，用于确认 Copilot coding agent 使用后台 session、PR、session log 和 Human review 组织输出。
  - ref: https://github.blog/ai-and-ml/github-copilot/assigning-and-completing-issues-with-coding-agent-in-github-copilot/
    title: "Assigning and completing issues with GitHub Copilot coding agent"
    summary: |
      GitHub 官方博客，用于确认 coding agent 可从 issue 分配进入计划、实现、测试、PR 和 review 流程。
  - ref: https://docs.devin.ai/desktop/cascade/cascade
    title: "Devin Desktop Cascade"
    summary: |
      Devin 官方文档，用于确认 Cascade 通过计划、Todo List、工具调用、checkpoint、lint 集成和实时上下文组织 agent 输出。
  - ref: https://devin.ai/blog/windsurf-wave-10-planning-mode/
    title: "Windsurf Planning Mode"
    summary: |
      Devin/Windsurf 官方博客，用于确认 Planning Mode 会创建和更新本地 Markdown 计划文件，并把长期计划和短期行动分层。
  - ref: https://docs.devin.ai/api-reference/v1/structured-output
    title: "Devin Structured Output"
    summary: |
      Devin 官方 API 文档，用于确认 Devin 支持在 session 中维护结构化输出 notepad，并通过 JSON schema 和 API 获取进展、测试或 PR review 结果。
  - ref: https://docs.devin.ai/desktop/agent-command-center
    title: "Devin Agent Command Center"
    summary: |
      Devin 官方文档，用于确认多 agent 工作可通过 Kanban 式状态视图展示 blocked、ready for review 等信息。
  - ref: https://docs.replit.com/references/agent/plan-mode
    title: "Replit Agent Plan mode"
    summary: |
      Replit 官方文档，用于确认 Plan mode 以规划、任务列表和架构讨论为主，不直接修改代码或数据，并可转入 Build mode。
  - ref: https://developers.openai.com/codex/noninteractive
    title: "OpenAI Codex non-interactive mode"
    summary: |
      OpenAI 官方文档，用于确认 Codex CLI 可输出 JSONL 事件，并支持 output schema 约束最终输出。
  - ref: https://developers.openai.com/codex/app-server
    title: "OpenAI Codex App Server"
    summary: |
      OpenAI 官方文档，用于确认 Codex App Server 通过 JSON-RPC 和 thread/turn/item 事件流提供可嵌入的结构化过程接口。
  - ref: https://developers.openai.com/api/docs/guides/agents/integrations-observability
    title: "OpenAI Agents SDK tracing"
    summary: |
      OpenAI 官方文档，用于确认 Agents SDK tracing 可记录模型调用、工具调用、handoff、guardrail 和自定义 span 等可观测过程。
  - ref: https://developers.openai.com/api/docs/guides/structured-outputs
    title: "OpenAI Structured Outputs"
    summary: |
      OpenAI 官方文档，用于确认结构化输出可通过 JSON Schema 约束模型返回，适合机器消费和系统集成。
input_refs:
  - spark-0044
  - /Users/dmh2002/.codex/attachments/0dea0eb3-0ee7-4e21-ac77-3d54c0b3172d/pasted-text.txt
  - specs/01-保障与衔接.md
  - specs/02-AI行为规范.md
  - specs/03-事实源与Git溯源规范.md
  - specs/04-Specs基础规范.md
  - specs/05-事实模型基础规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/22-ADR-决策.md
  - specs/23-Pitfall-踩坑经验.md
  - specs/24-Study-研究报告.md
  - specs/30-安装配置与验证行动模板.md
related_sparks:
  - spark-0044
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/01-保障与衔接.md
  - specs/02-AI行为规范.md
  - specs/03-事实源与Git溯源规范.md
  - specs/04-Specs基础规范.md
  - specs/05-事实模型基础规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/22-ADR-决策.md
  - specs/23-Pitfall-踩坑经验.md
  - specs/24-Study-研究报告.md
  - specs/30-安装配置与验证行动模板.md
  - specs/attachments/01.Att.06-环境安装回滚检查表.md
  - specs/attachments/04.Att.04-保障要求字段表.md
  - specs/attachments/09.Att.01-验证声明字段表.md
archive_reason: null
---

# AI Agent 输出格式治理与 LDVH 审计报告吸收调研

## 研究问题

本报告回答 `spark-0044` 的两个问题：

1. 主流 AI agent 产品现在如何组织输出，尤其是计划、执行、工具调用、状态、验证和最终结果；
2. 为什么 Trae 的输出信息让 Human 感觉更有条理；
3. Codex 能否做到类似结构，是否存在比 Trae 式聊天整理更先进的输出格式；
4. LDVH 应如何吸收本次审计报告，哪些内容进入 Human Gate，哪些内容后续分流为 WorkCase、ADR、Pitfall、docs 或 specs 修改。

本报告的重点不是评测模型智力，而是评估 agent 输出的信息架构：什么内容给 Human 看，什么内容给机器消费，什么内容进入事实源，什么内容只是过程证据。

## 输入与边界

本次输入包括 Trae、Cursor、Claude Code、OpenAI Codex、GitHub Copilot、Windsurf/Cascade、Devin、Replit 等官方文档或官方仓库资料，以及 Human 提供的 LDVH v3 specs 审计报告。

边界如下：

1. 本报告只沉淀调研结论和吸收建议，不直接修改正文 specs、附件、Code、Web、Hook 或事实模型字段；
2. 外部产品文档只作为学习资料，不自动成为 LDVH 规则；
3. 审计报告是高价值输入，但在 Human Gate 前不替代 specs 权威；
4. Study 不替代 Spark 的 pending 分流，也不替代 WorkCase 的执行承接；
5. 产品能力会变化，后续正式实现前应重新核对官方文档。

## 关键发现

### 总体结论

主流 agent 输出正在从“模型写一段答复”演进为四层结构：

| 层级 | 作用 | 典型表现 |
|---|---|---|
| 人类可读叙事 | 让 Human 快速知道现在做什么、做了什么、还差什么 | 计划、进度更新、结果摘要、风险、下一步 |
| 任务/状态对象 | 把工作拆成可勾选、可阻塞、可 review 的对象 | Todo、Plan、PR、Issue、session、checkpoint |
| 工具与证据流 | 记录 agent 实际调用了什么、验证了什么、失败在哪里 | command cards、tool calls、logs、tests、screenshots、session logs |
| 机器可读结构 | 让系统可以渲染、查询、校验、回放和编排 | JSONL events、schemas、traces、structured output、trajectory |

Trae 让输出显得有条理，主要是因为它把这四层中的前三层产品化了：Human 看到的是计划、任务、工具面板、命令卡片、状态提醒和阶段结果，而不是一整段未分层的 agent prose。

更先进的方向不是把最终回复写得更长，而是把 agent 过程变成结构化状态。Codex/OpenAI 生态在这点上有可学习空间：Codex CLI 的 JSONL、output schema、App Server 事件流、Agents SDK tracing 和 structured outputs 都比纯 Markdown 答复更适合 Web、Code、Hook、审计和长期编排。

### 为什么 Trae 看起来更有条理

Trae 的优势更像“输出界面产品化”，不是单纯“模型更会写总结”。

从官方资料和 Trae Agent 开源仓库看，Trae/SOLO Agent 的组织方式包括：

| 机制 | 对 Human 的感受 |
|---|---|
| SOLO/Agent 模式 | 把需求理解、计划、实现、测试、预览、发布组织成连续阶段 |
| `/plan` 和 `/spec` | 先形成计划或规格，再进入实现，减少跳步感 |
| 任务管理 | 把长任务拆成可跟踪条目，Human 能看到当前进度 |
| 工具面板和命令卡片 | 把工具调用、命令执行和运行状态从正文里拆出来 |
| 阶段状态提醒 | Human 不需要从长文本里猜 agent 卡在哪里 |
| 代码变更总结 | 每轮输出能回到“改了什么、为什么、结果怎样” |
| Lakeview / trajectory | 用短摘要和轨迹记录压缩复杂执行过程 |

所以 Human 觉得 Trae 有条理，是因为 Trae 给 agent 输出套了一个稳定的 view model：阶段、任务、工具、状态、产物、总结。这比单靠 prompt 要求“请条理清晰”更可靠。

### 其他主流 agent 的输出格式

不同产品的设计取向不同，但大趋势一致：计划前置、过程结构化、证据显性、Human review 保留。

| 产品 | 输出组织方式 | 对 LDVH 的启发 |
|---|---|---|
| Trae / SOLO Agent | 计划、任务、工具面板、命令卡片、阶段状态、trajectory | 有条理来自产品化过程视图，不只是回答模板 |
| Cursor | Plan Mode 研究代码库，生成含文件路径和代码引用的 Markdown 计划，可编辑可保存 | 计划应成为可审阅对象，而不是临时聊天段落 |
| Claude Code | Plan mode、output styles、自定义 Markdown 输出风格、hook 可保存计划 | 输出格式可以作为可配置行为层，但仍需审批边界 |
| OpenAI Codex | plan/progress/final discipline、AGENTS/skills、JSONL events、output schema、App Server、traces | Codex 可做聊天层格式，也可做机器可读过程层 |
| GitHub Copilot coding agent | issue/session/PR/session log/test/review | 工作对象和 PR 是天然输出容器 |
| Windsurf/Cascade | Markdown plan、Todo List、checkpoint、长期计划 agent + 短期行动 agent | 长计划和短执行可以分离，计划应随新信息更新 |
| Devin | Ask/Agent、Agent Command Center、structured output notepad | 多 agent 状态和结构化进展可以用 schema 暴露 |
| Replit Agent | Plan mode / Build mode、任务列表、checkpoint | 规划和执行模式要分清，状态回滚是输出的一部分 |

这些产品都在把 agent 输出从“答案”变成“工作状态”。LDVH 如果只规定最终回复格式，会错过最有价值的部分。

### Codex 能不能做到

可以，但要分两层看。

第一层是当前对话里的 Human-readable 输出。Codex 可以通过以下方式接近 Trae 的可读性：

1. 固定中间更新口径：正在读什么、学到什么、下一步做什么；
2. 固定计划口径：目标、边界、步骤、验证、风险；
3. 固定最终口径：改了什么、验证了什么、还剩什么、文件在哪里；
4. 使用 AGENTS.md 或 Skill 把输出契约固化为项目行为，而不是每次聊天临时提醒；
5. 对需要长期复用的格式，沉淀为 Codex Skill 或 LDVH 行动指南。

第二层是机器可读输出。Codex/OpenAI 生态已经有比 Trae 式界面更适合治理系统的底层能力：

| 能力 | 价值 |
|---|---|
| Codex CLI JSONL | 把 thread、turn、item、tool、plan update 等事件作为流式结构输出 |
| output schema | 用 JSON Schema 约束最终输出，减少解析自然语言 |
| Codex App Server | 通过 JSON-RPC 和 item events 嵌入 Codex 线程、审批、历史和工具进度 |
| Agents SDK tracing | 记录模型调用、工具调用、handoff、guardrail 和 custom span |
| Structured Outputs | 把结果约束为机器可消费对象，适合 Web/API/审计 |

限制也很清楚：如果只在聊天里要求 Codex“像 Trae 一样有条理”，可以改善最终文本，但不能自动得到 Trae 的工具面板、状态卡片和任务 UI。要达到产品级效果，需要 LDVH Web/Code/Runtime 消费结构化过程输出，并渲染自己的过程视图。

### 更先进的格式：双层输出

LDVH 不应把目标定义为“让 Codex 回复更像 Trae”。更好的目标是定义双层输出：

| 层 | 面向对象 | 格式 |
|---|---|---|
| Human Narrative | Human、reviewer、handoff 接收者 | 简短 Markdown，固定为结论、计划/进展、验证、风险、下一步 |
| Agent Output Envelope | Web、Code、Hook、审计、编排器 | JSON-like structure / event stream / sidecar，记录状态、证据、工具和事实源吸收 |

一个适合 LDVH 的 `Agent Output Envelope` 候选结构如下：

| 字段 | 含义 |
|---|---|
| `intent` | 本轮目标和 Human 原始意图摘要 |
| `mode` | `ask`、`study`、`plan`、`execute`、`review`、`handoff` 等 |
| `assumptions` | 当前推断前提，避免隐藏判断 |
| `plan_items` | 可更新的任务列表、状态、依赖和阻塞点 |
| `current_step` | 正在执行或刚完成的步骤 |
| `tool_events` | 命令、文件读写、网络调研、测试、截图等工具事件摘要 |
| `file_changes` | 修改文件、变更类型、事实源影响 |
| `verification` | 运行过的检查、退出码、证据路径、未验证原因 |
| `decisions` | 本轮形成的候选判断，不直接等同 ADR |
| `risks` | 残留风险、Human Gate、权限或事实源边界 |
| `fact_absorption` | 哪些内容进入 Spark、Study、WorkCase、ADR、Pitfall、docs 或 specs |
| `next_actions` | 建议的后续分流，不伪装成已执行事实 |

这个结构比单纯 Markdown 更先进，因为它能被 UI 渲染为 Trae/Cursor/Devin 式卡片，也能被测试和审计消费；同时最终给 Human 的文字仍然可以很短。

### 对 LDVH 的输出治理建议

LDVH 当前已有 Spark、Study、WorkCase、ADR、Pitfall、specs、Code、Web、Hook 和 Git 追溯。结合本次调研，输出治理可以分三步推进：

1. 先定义 Codex 当前对话的最小输出契约：中间更新、计划、最终汇报和 review 输出；
2. 再定义 Agent Output Envelope 的字段与事实源边界：哪些是过程证据，哪些可进入事实源；
3. 最后由 Web/Code/Runtime 渲染过程视图：计划项、状态、工具事件、验证、风险、Human Gate 和事实吸收。

这条路线能吸收 Trae 的“有条理”，也能保留 Codex/OpenAI 的结构化底座。

### 审计报告吸收判断

Human 提供的审计报告总体结论是：LDVH v3 specs 体系整体架构自洽、价值锚点清楚、事实源边界较强，但存在三类主要风险：

1. 附件存在越界或冲突点，需要 Human Gate；
2. `specs/30` 第 7 章结构失控；
3. 跨 spec 字段命名、诊断类型和 V-value 声明一致性不足。

本 Study 对审计报告的吸收判断如下：

| 审计发现 | 吸收方式 |
|---|---|
| `04.Att.04` 孤立且与正文/字段版本不一致 | 高优先级 Human Gate；决定废弃、修订字段或迁移归口 |
| `01.Att.06` 与 `04 §7.3` 的 checklist 禁令冲突 | 高优先级 Human Gate；决定增加例外或迁回正文 |
| `specs/30 §7` 过长且主题混杂 | 高优先级 WorkCase；拆成多个主题章节，把验证细节迁回第 10 章 |
| `09.Att.01` 中出现过强“禁止写法” | 中优先级；移回正文规则或改成声明字段边界 |
| `01 §5.3`、`02 §6.1`、`04.Att.04` 字段命名不一致 | 中优先级；统一保障需求字段、来源字段和条件必填口径 |
| `blocking/blocker`、`follow_up/follow-up` 诊断类型不一致 | 中优先级；统一命名后同步 Code/tests |
| 20-24 V5/Human Gate 声明不均衡 | 中优先级；按成员规范实际职责补齐或解释 |
| 21 WorkCase related_specs 缺 20/22/23/24 | 中优先级；正文元数据一致性修复 |
| 23 Pitfall 准入条件措辞缺“之一” | 中优先级；降低误读风险 |
| 04.Att.03 / 04.Att.06 / 04.Att.02 状态和授权链不清 | 中优先级；附件身份与术语状态整理 |
| 30 icon 表应迁到 Code docs | 低优先级；安装向导实践文档整理 |
| 01 增加“本文地图”、04 parent_spec 解释 | 低优先级；提升导航和父子关系可读性 |

关键边界是：审计报告是外部评估输入，不能直接改写 specs 权威。正确吸收路径应是：Study 记录审计发现和分流建议，Spark 保持 pending，Human 决定是否创建 WorkCase 或直接授权 specs 修改。

### 与主流 agent 输出格式的关系

这份审计报告也反向证明了 LDVH 需要更强的输出格式治理。审计发现里很多问题不是单个文件错字，而是跨文件、跨附件、跨 Code/tests 的状态不一致。单靠最终回答“我改好了”不足以支撑治理。

LDVH 的 agent 输出应能明确回答：

1. 哪些审计发现已进入事实源；
2. 哪些只是 Study 结论；
3. 哪些需要 Human Gate；
4. 哪些已经有 WorkCase；
5. 哪些已修改 specs；
6. 哪些通过 Code/tests 验证；
7. 哪些仍是残留风险。

这正是 Agent Output Envelope 的价值：它把过程状态、证据和事实吸收边界结构化，避免 Human 只能从长文本里猜。

## 建议

1. 保持 `spark-0044` 为 `pending`，因为本次 Study 只完成调研和分流建议，尚未完成 WorkCase/ADR/specs 吸收。
2. 新建高优先级 WorkCase：处理 `04.Att.04`、`01.Att.06` 与 `04 §7.3` 的附件冲突和 Human Gate 裁决。
3. 新建高优先级 WorkCase：拆分 `specs/30 §7`，把混杂内容拆为多个主题章节，并把验证细节迁回验证章节。
4. 新建中优先级 WorkCase：统一保障需求字段命名、诊断类型、V-value 声明、related_specs 和附件身份状态。
5. 新建 ADR 候选：决定 LDVH 是否定义 `Agent Output Envelope`，以及它与 Spark/Study/WorkCase/ADR/Pitfall、Web、Code、Hook 的边界。
6. 新建 Pitfall 候选：记录“把 agent 过程输出、审计报告、Study 结论误当成正式 specs 修改或对象关闭证据”的风险。
7. 若 Human 想先改善 Codex 体感输出，可以先写一个轻量 Skill 或 AGENTS.md 段落，固定 Codex 的中间更新、计划和最终汇报格式。
8. 若 Human 想做产品级体验，应优先让 Web/Code 消费结构化过程状态，而不是继续堆 prompt。

## 后续分流

建议后续分流为五条线：

| 分流线 | 建议对象 | 说明 |
|---|---|---|
| Agent 输出格式治理 | ADR 或 WorkCase | 决定是否建立 `Agent Output Envelope` 和 Codex 输出契约 |
| Codex 体感输出优化 | Skill / AGENTS.md / 行动指南 | 固定中间更新、计划、最终汇报和 review 输出 |
| 产品级过程视图 | Web / Code WorkCase | 渲染计划项、工具事件、验证、风险、Human Gate 和事实吸收 |
| 审计高优先级修复 | WorkCase + Human Gate | 处理附件冲突和 `specs/30 §7` 失控 |
| 审计一致性批处理 | WorkCase | 字段命名、诊断类型、V-value、related_specs、附件状态等一致性整理 |

本 Study 已完成对调研材料和审计报告的稳定吸收，但不代表 `spark-0044` 已 resolved。只有当 Human 确认后续 WorkCase/ADR/Pitfall/docs/specs 分流完成，或明确不再跟踪剩余议题时，Spark 才能进入终态。
