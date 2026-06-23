---
id: study-0003
type: study
title: TRAE CN 智能体创建调用与 LDVH 多角色设定调研
status: active
created: '2026-06-18T07:59:11'
updated: '2026-06-18T22:31:24+08:00'
summary: |
  TRAE CN 把智能体定位为面向不同开发场景的编程助手。TRAE IDE 支持内置 Chat、Agent、SOLO Agent，也支持通过智能生成或手动创建自定义智能体；自定义智能体可以配置提示词、MCP Server 和内置工具，并可开启“可被其他智能体调用”。当前官方文档显示，TRAE IDE 中仅 SOLO Agent 可调用自定义智能体。TRAE CLI 则支持通过 `/agent-new` 创建子智能体，保存到 `.traecli/agents`，并可由 TRAE CLI 自动拆分任务调用，或由用户通过 `@{智能体名称}` 手动调用。
user_intent: 用户要求补充 TRAE CN 关于子 Agent / 自定义智能体创建调用机制的同主题调研，为后续 00 文档多角色设定提供对照。
conclusion: |
  TRAE CN 对 LDVH 的启发是：多角色在 Trae 环境中更接近“可配置、可被主控 SOLO Agent 或 CLI 调度的专业智能体”，而不是 Codex 式必须显式请求 spawn 的子 Agent。LDVH 00 仍应抽象为 Role Contract；Trae 适配层可把 Role Contract 映射为自定义智能体配置、SOLO Agent 可调用设置、CLI `.traecli/agents` 文件、Skill 和 MCP 配置。TRAE 的 Spec / Plan 文档和 SOLO 任务管理可以作为执行过程和协作界面，但不应替代 LDVH 的 WorkCase、Spark、Study、ADR 等事实源。
urls:
- ref: https://docs.trae.cn/ide_agent-overview
  title: TRAE IDE Agent Overview
  summary: 用于说明 TRAE IDE 中智能体的总体定位、内置类型和面向开发场景的协作边界。
- ref: https://docs.trae.cn/ide_agent
  title: TRAE IDE Agent
  summary: 用于说明 TRAE IDE 自定义智能体的创建方式、配置项和可被其他智能体调用的条件。
- ref: https://docs.trae.cn/ide_solo-coder
  title: TRAE SOLO Agent
  summary: 用于说明 SOLO Agent 在复杂开发任务中的主控、规划和多智能体协作能力。
- ref: https://docs.trae.cn/cli_agent
  title: TRAE CLI Agent
  summary: 用于说明 TRAE CLI 子智能体的创建、保存位置、自动拆分调用和手动调用方式。
- ref: https://docs.trae.cn/cli_skills
  title: TRAE CLI Skills
  summary: 用于说明 TRAE CLI Skill 与子智能体组合时如何承接可复用能力。
- ref: https://docs.trae.cn/cli_model-context-protocol
  title: TRAE CLI MCP
  summary: 用于说明 TRAE CLI 通过 MCP Server 扩展工具能力的机制。
- ref: https://docs.trae.cn/cli_permission-mode
  title: TRAE CLI Permission Mode
  summary: 用于说明 TRAE CLI 权限模式对智能体执行边界和安全控制的影响。
related_sparks:
- spark-0007
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
- history/specs-v1/00-LD-Vibe-Harness理念与纲要.md
- history/specs-v1/04.02-LDVH能力资产与保障机制规范.md
- history/specs-v1/06-行动编排基础规范.md
- specs/21-WorkCase-工作项.md
archive_reason: null
---

# TRAE CN 智能体创建调用与 LDVH 多角色设定调研

## 研究问题

本报告回答三个问题：

1. TRAE CN 中如何创建自定义智能体或子智能体；
2. TRAE CN 中如何调用这些智能体；
3. 这些机制对 LDVH 后续 `history/specs-v1/00-LD-Vibe-Harness理念与纲要.md` 中多角色设定有什么启发。

这里的“TRAE CN”覆盖官方文档中的 TRAE IDE / SOLO 模式 / TRAE CLI。三者能力不完全相同，因此本报告按环境分层整理。

## 输入与边界

本次调研使用 TRAE CN 官方文档，访问时间为 2026-06-18：

- https://docs.trae.cn/ide_agent-overview
- https://docs.trae.cn/ide_agent
- https://docs.trae.cn/ide_solo-coder
- https://docs.trae.cn/cli_agent
- https://docs.trae.cn/cli_skills
- https://docs.trae.cn/cli_model-context-protocol
- https://docs.trae.cn/cli_permission-mode

本报告只记录公开文档中的稳定机制，不推断未公开 API 或内部调度实现。

## 关键发现

### TRAE IDE 智能体定位

TRAE IDE 官方文档把智能体定义为面向不同开发场景的编程助手。它们具有自主运行、工具访问、上下文理解和多步骤规划能力。内置智能体包括：

- `Chat`：快速技术咨询和问答；
- `Agent`：可从 0 到 1 开发完整项目，可调用文件分析、编辑、命令运行等工具；
- `SOLO Agent`：面向复杂项目开发，支持需求迭代、架构重构、计划确认后推进开发，并可编排多个智能体组成 AI 团队。

这说明 Trae 的“多角色”不是只靠一个单独的子线程工具实现，而是由内置 Agent、SOLO Agent、自定义智能体、工具配置和模式化工作流共同构成。

### TRAE IDE 如何创建自定义智能体

TRAE IDE 支持两种创建方式：

1. 智能生成；
2. 手动创建。

入口是 AI 对话输入框中的 `@`，再点击创建智能体。智能生成方式要求用户描述智能体的功能、使用场景和使用时机，然后系统生成智能体配置；手动创建则逐项填写配置。

自定义智能体核心配置包括：

- 头像；
- 名称；
- 提示词，用于规定人设、回答口吻、工作流程、工具使用时机和需要遵守的规范；
- 是否“可被其他智能体调用”；
- 英文标识名，例如 `project-analyzer`；
- 何时调用，用于描述其他智能体调用该智能体的场景和时机；
- 工具配置。

工具配置包括 MCP Server 和内置工具。内置工具包括阅读、文件系统、终端、联网搜索和预览。

重要边界：官方文档明确说明，目前在 TRAE IDE 中仅 SOLO Agent 可调用自定义智能体。也就是说，一个普通自定义智能体开启“可被其他智能体调用”后，并不意味着任意智能体都能任意调用它；实际主控是 SOLO Agent。

### TRAE IDE 如何调用智能体

用户可以在 AI 对话输入框输入 `@`，或点击 `@智能体`，然后从智能体列表中选择要使用的智能体。

SOLO Agent 则是更接近 LDVH “主控 + 专业角色”设想的入口。官方文档说明，SOLO Agent 可以配置其可调用的自定义智能体、MCP Server 和内置工具。配置好可调用智能体后，SOLO Agent 作为主控智能体，可以在处理复杂长上下文任务时自动调用相应智能体，将任务拆分和隔离，使不同智能体在独立上下文中专注处理各自任务。用户也可以在提示词中明确指定要调用的智能体，SOLO Agent 会根据上下文在合适时机调用。

这与 LDVH 的 WorkCase / ExecutionItem 有自然映射：

- SOLO Agent 类似运行期主控；
- 自定义智能体类似专业执行角色；
- “何时调用”类似角色触发条件；
- 英文标识名类似角色 ID；
- 工具配置类似角色权限；
- 独立上下文类似子 Agent 过程隔离。

但它仍是 Trae 运行期机制，不是 LDVH 长期事实源。

### SOLO Agent 与 Plan / Spec 模式

SOLO Agent 支持 Plan 和 Spec 模式。

Plan 模式适用于中小型功能开发和模块级重构。SOLO Agent 收到需求后生成规划文档，等待用户确认后执行。

Spec 模式面向复杂系统级任务，会生成三阶段文档组：`spec.md`、`tasks.md` 和 `checklist.md`，存储在项目根目录 `.trae/specs/` 下。官方文档说明这些文档可纳入版本控制，作为项目知识资产长期保留。

对 LDVH 的判断是：Trae Spec / Plan 文档是 Trae 环境中的工作流产物，可以作为输入资料或运行期执行界面；但不应替代 LDVH 的 WorkCase、Spark、Study、ADR、Change 等事实源。若两者共存，LDVH 应定义映射和回写边界，而不是把 `.trae/specs` 直接视为 LDVH 权威事实源。

### TRAE CLI 如何创建子智能体

TRAE CLI 官方文档提供了更接近“子智能体配置文件”的机制。

创建方式是向 TRAE CLI 发送 `/agent-new` 指令，发起创建自定义智能体流程。用户提供必要信息后，TRAE CLI 会设计智能体配置文件，并保存到 `.traecli/agents` 目录。

支持的 frontmatter 包括：

```yaml
---
name: tui-implementer
description: |
  A specialized agent for implementing terminal user interface components and applications.
tools: Read,Write,mcp__server__tool
model: model-name
---
```

字段含义：

- `name`：智能体名称；
- `description`：智能体描述，用于说明使用场景；
- `tools`：智能体可使用的工具，多个工具用逗号分隔；
- `model`：模型名称。

frontmatter 之后的 Markdown 正文是智能体角色提示词。这一点与 Claude Code subagent 和 Codex custom agent 的基本模式相近：配置层定义角色元数据和权限，正文定义行为。

### TRAE CLI 如何调用智能体

TRAE CLI 官方文档说明，TRAE CLI 会根据实际情况把一个任务拆成多个相对独立的子任务，然后分配给合适的智能体完成。用户也可以通过手动 `@{智能体名称}` 要求 TRAE CLI 调用对应智能体。

这与 Codex 的“必须明确要求子 Agent / parallel agent work”不同。Trae CLI 文档给出的口径更偏自动调度：CLI 可以根据任务拆分和 agent 描述决定分配；同时保留显式 `@` 调用。

对 LDVH 来说，这意味着 00 文档不能把多角色触发条件写成某个单一环境的规则。更稳妥的表述是：

- 支持自动调度的环境，可以根据 Role Contract 和任务上下文选择角色；
- 需要显式授权的环境，必须由 Human 或主控 AI 明确触发；
- 不支持子 Agent 的环境，仍可由主控 AI 按 Role Contract 串行扮演角色并保留证据。

### Skill、MCP 和权限边界

TRAE CLI Skills 是模块化能力扩展机制，使用 `SKILL.md` 定义。Skill 按 `description` 匹配按需触发，并支持渐进式披露。目录包括：

- 全局 Skill：`~/.traecli/skills`；
- 项目 Skill：`.traecli/skills/`。

TRAE CLI 还兼容 TRAE IDE 的 Skill 目录：

- IDE 项目 Skill：`.trae/skills/`；
- IDE 全局 Skill：`~/.trae-cn/skills`。

MCP 层面，TRAE CLI 支持 stdio、SSE 和 Streamable HTTP，可通过 `traecli config edit` 编辑 `trae_cli.yaml`，并通过 `/mcp` 管理 MCP Server。

权限模式方面，TRAE CLI 支持 `default`、`plan`、`bypass_permissions`。这对 LDVH 多角色设计很重要：Role Contract 不能只写角色目标，还应写清工具权限、Human Gate 和是否允许无授权执行。

## 建议

TRAE CN 的机制支持一个更产品化的多智能体界面：SOLO Agent 作为主控，自定义智能体作为专业角色，CLI 则通过 `.traecli/agents` 文件和 `@{智能体名称}` 暴露角色配置与调用。对 LDVH 00 的建议如下：

1. 00 文档应定义“角色契约”而不是“子 Agent 实现”。Trae 中可以映射为自定义智能体，但其他环境未必如此。
2. 角色契约至少包含角色 ID、适用场景、输入、允许工具、禁止动作、输出格式、证据回收、交还条件和 Human Gate。
3. Trae IDE 适配时，Role Contract 可以映射到自定义智能体的提示词、英文标识名、何时调用和工具配置。
4. Trae SOLO 适配时，Role Contract 可以映射到 SOLO Agent 可调用智能体清单。
5. Trae CLI 适配时，Role Contract 可以映射到 `.traecli/agents` 下的 frontmatter 与正文提示。
6. Trae Spec / Plan 文档可以作为环境工作流产物和输入资料，但 LDVH 长期事实源仍应是 WorkCase / Spark / Study / ADR / Change。
7. 如果 Trae 自动拆分任务并调用智能体，LDVH 只回收摘要、证据、验证结果、关闭判断和风险，不回写每个智能体的完整过程日志。

一个可供 00 后续吸收的候选表述是：

```text
LDVH 的多角色协作可以在 Trae 环境中落地为 SOLO Agent 可调用的自定义智能体或 TRAE CLI 的 `.traecli/agents` 子智能体配置；但这些是环境适配形态。LDVH 的长期事实源只记录角色契约、任务输入、输出摘要、证据引用、验证结果和分流关系，不把 Trae 运行期对话流或 Spec / Plan 产物直接等同为 LDVH 工作对象。
```

## 后续分流

1. 修改 `history/specs-v1/00-LD-Vibe-Harness理念与纲要.md` 时，吸收“多角色可映射为环境智能体，但角色本体是契约”的表述。
2. 修改 `history/specs-v1/04.02-LDVH能力资产与保障机制规范.md` 时，判断 Trae 自定义智能体配置、Skill、MCP、Rules 是否应纳入能力资产分层。
3. 修改 `history/specs-v1/06-行动编排基础规范.md` 时，补充“主控自动调度”和“Human 显式调用”两类环境触发模式。
4. 修改 `specs/21-WorkCase-工作项.md` 时，不应把 `.traecli/agents` 或 SOLO Agent 配置写入 WorkCase 字段；WorkCase 只保留 `role`、输入、输出、证据和关闭信息。
5. 如后续要支持 Trae 环境落地，应另建环境适配文档或 Skill，说明如何从 Role Contract 生成 Trae 自定义智能体配置摘要。
