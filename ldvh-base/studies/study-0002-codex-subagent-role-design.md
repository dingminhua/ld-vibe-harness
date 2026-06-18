---
id: study-0002
type: study
title: Codex 子 Agent 创建调用与 LDVH 多角色设定调研
status: active
created: '2026-06-18T07:59:11'
updated: '2026-06-18T22:31:24+08:00'
summary: |
  Codex 子 Agent 适合承接可并行、边界清晰、噪音较高或需要专业视角的运行期工作。Codex 官方资料显示，子 Agent 不会自动生成，必须由用户明确要求并行委派；Codex 可使用内置 default、worker、explorer，也可通过个人或项目级 TOML 文件定义自定义 agent。当前 Codex App 工具面还暴露了 spawn_agent、wait_agent、send_input 和 close_agent 这类管理动作。
user_intent: 用户要求调研 Codex 中如何创建子 Agent 与调用子 Agent，为后续 00 文档多角色设定做前期准备。
conclusion: |
  LDVH 应把多角色设定抽象为环境无关的 Role Contract，而不是把它绑定为 Codex 子 Agent 配置。Codex 子 Agent 可以作为支持环境中的运行期委派实现：由 WorkPlan execution item 给出角色、输入和输出要求，由 Human 或主控 AI 在明确授权下触发子 Agent。00 文档应强调角色契约、证据回收和主控整合责任；具体 Codex 创建、调用和自定义 agent 配置应放入环境适配、能力资产或后续专门规范。
urls:
  - ref: https://developers.openai.com/codex/concepts/subagents
    title: Codex Subagent Concepts
    summary: 用于说明 Codex 子 Agent 的定位、适用场景和上下文隔离价值。
  - ref: https://developers.openai.com/codex/subagents
    title: Codex Subagents
    summary: 用于说明 Codex 子 Agent 的创建、配置和调用方式，支撑 LDVH 角色契约映射判断。
related_memos:
  - memo-0007
related_workareas: []
related_workplans: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/00-LD-Vibe-Harness理念与纲要.md
  - specs/04.02-LDVH能力资产与落地保障规范.md
  - specs/06-工作流程基础规范.md
  - specs/21-WorkPlan-工作计划.md
archive_reason:
---

# Codex 子 Agent 创建调用与 LDVH 多角色设定调研

## 研究问题

本报告回答三个问题：

1. Codex 中如何创建子 Agent；
2. Codex 中如何调用和管理子 Agent；
3. 这些机制对 LDVH 后续 `specs/00-LD-Vibe-Harness理念与纲要.md` 中的多角色设定有什么启发。

这里的“子 Agent”特指 Codex 官方文档中的 subagent workflow：主 Agent 在运行期启动一个或多个专业代理，让它们并行探索、执行、审查或分析，然后把摘要结果交回主线程。它不是 LDVH 工作对象，也不是长期事实源。

## 输入与边界

本次调研使用以下资料：

1. Codex 官方手册，2026-06-18 通过 `openai-docs` 技能刷新到本地缓存；
2. 官方手册中的 `Subagent concepts` 页面：`/codex/concepts/subagents`；
3. 官方手册中的 `Subagents` 设置页面：`/codex/subagents`；
4. 官方手册中的 `Customization`、`Agent Skills`、`AGENTS.md`、`config.toml` 相关章节；
5. 当前 Codex App 会话中实际暴露的 `multi_agent_v1` 工具元数据。

本报告不把当前会话工具元数据视为公开产品文档；它只说明“当前环境可操作形态”。公开稳定说法仍以 Codex 官方手册为准。

## 关键发现

### Codex 子 Agent 解决什么问题

Codex 官方资料把子 Agent 的价值放在两个方向：

1. 降低主线程上下文污染。探索记录、测试日志、栈追踪、命令输出和临时分析容易让主线程变长、变脏，影响后续判断。子 Agent 可以把这些噪音移出主线程，只把摘要和结论交回主 Agent。
2. 并行推进独立工作。安全审查、测试缺口、可维护性、日志分析、代码库探索等问题可以拆成相互独立的工作包，让多个 Agent 同时运行，再由主 Agent 汇总。

这与 LDVH 当前 WorkPlan / ExecutionItem 方向一致：长期事实源只保留可恢复、可验证、可关闭的最小证据，不保存 AI 的完整运行期过程。

### 如何创建子 Agent

Codex 有两类 agent 来源。

第一类是内置 agent：

- `default`：通用 fallback；
- `worker`：面向实现和修复；
- `explorer`：面向代码库探索和读多写少问题。

第二类是自定义 agent。Codex 官方资料说明，可以在个人级 `~/.codex/agents/` 或项目级 `.codex/agents/` 下放置独立 TOML 文件。每个文件定义一个 custom agent，必填字段是：

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
developer_instructions = """
Review code like an owner.
Prioritize correctness, security, behavior regressions, and missing test coverage.
"""
nickname_candidates = ["Atlas", "Delta", "Echo"]
```

其中：

- `name` 是 Codex 识别和调用 custom agent 的事实名称；
- `description` 说明何时使用该 agent；
- `developer_instructions` 定义该 agent 的行为边界；
- `nickname_candidates` 只是显示名候选，不改变调用名称。

自定义 agent 文件还可以包含常规 `config.toml` 支持的配置键，例如 `model`、`model_reasoning_effort`、`sandbox_mode`、`mcp_servers` 和 `skills.config`。这意味着一个角色不仅可以有不同指令，还可以有不同工具面、技能配置、沙箱策略和模型推理设置。

Codex 也有全局 `[agents]` 设置，用于控制并发和嵌套：

- `agents.max_threads`：并发打开的 agent thread 上限，默认 6；
- `agents.max_depth`：子 Agent 嵌套深度，默认 1；
- `agents.job_max_runtime_seconds`：批量 worker 作业默认超时。

对 LDVH 来说，创建 custom agent 属于环境适配或能力资产配置，不应写进 00 文档正文成为所有环境的强制规则。

### 如何调用和管理子 Agent

Codex 官方资料强调：Codex 不会自动生成子 Agent，只有在用户明确要求时才应触发。典型触发语包括：

- “spawn two agents”；
- “delegate this work in parallel”；
- “use one agent per point”；
- “spawn one subagent for security risks, one for test gaps, and one for maintainability”。

好的调用提示应包含：

1. 如何拆分工作；
2. 每个子 Agent 的职责；
3. 是否等待全部结果；
4. 每个子 Agent 应返回什么摘要；
5. 主 Agent 最终如何汇总。

例如：

```text
Review this branch with parallel subagents. Spawn one subagent for security risks,
one for test gaps, and one for maintainability. Wait for all three, then summarize
the findings by category with file references.
```

在 CLI 中，用户可以用 `/agent` 在活跃 agent thread 间切换和检查。Codex 官方资料也说明，可以直接要求 Codex 引导运行中的子 Agent、停止它，或关闭已完成的 agent thread。

当前 Codex App 会话中，工具层暴露了更具体的管理动作：

- `spawn_agent`：为边界清晰的任务启动子 Agent；
- `wait_agent`：等待一个或多个子 Agent 完成；
- `send_input`：向已有子 Agent 发送后续指令；
- `close_agent`：关闭不再需要的子 Agent；
- `resume_agent`：恢复已关闭的子 Agent。

这些工具有重要约束：不应在用户没有明确要求子 Agent、委派或并行 Agent 工作时主动启动；编码类委派应拆成互不冲突的写入范围；子 Agent 返回后，主 Agent 仍要审查、整合和验证结果。

本次调研没有实际启动子 Agent，因为用户要求的是“调研子 Agent 怎么用”，不是要求“用子 Agent 来调研”。

### 权限、沙箱和成本边界

Codex 官方资料说明，子 Agent 继承当前沙箱策略和父会话的运行时 override。交互式 CLI 中，非当前线程的 approval request 也可能浮现；非交互式流程如果无法获得新批准，需要批准的动作会失败并把错误传回父工作流。

子 Agent 的成本边界也很重要：每个子 Agent 都会独立使用模型和工具，因此 token、时间和本地资源消耗都会高于单 Agent。并行写代码还会增加冲突和协调成本。

实操上应遵循：

1. 先用于读多写少的探索、测试、审查、日志分析和总结；
2. 写代码时只委派边界明确、文件集合不重叠的任务；
3. 不让多个子 Agent 同时修改同一模块；
4. 不把子 Agent 的中间过程完整写入长期事实源；
5. 子 Agent 完成后及时关闭；
6. 主 Agent 对最终汇总、验收和事实源回写负责。

### 与 AGENTS.md、Skills、MCP 的区别

Codex 官方资料把定制能力分成互补层级：

- `AGENTS.md`：仓库或目录级持久指导；
- Skills：可复用任务工作流和领域知识；
- MCP：连接外部工具和共享系统；
- Subagents：运行期委派给专业子 Agent；
- config.toml / custom agent TOML：配置模型、沙箱、工具、技能和并发边界。

因此，LDVH 后续不能把“多角色”只写成一种载体。更合理的分层是：

1. `AGENTS.md` 承载项目通用规则；
2. Skill 承载可复用流程；
3. MCP 承载外部系统能力；
4. Role Contract 承载 LDVH 环境无关的角色契约；
5. Codex custom agent 承载 Codex 环境中的可执行角色配置；
6. Subagent workflow 承载一次 WorkPlan 执行中的运行期并行委派。

## 建议

后续 00 文档可以引入“多角色协作”的理念，但建议使用环境无关表述：

1. LDVH 的角色是契约，不是线程。角色契约应描述目的、输入、权限、输出、证据、交还条件和停止条件。
2. WorkPlan 的 `orchestration.execution_items[*].role` 可以声明需要的专业视角，但不等于必须创建 Codex 子 Agent。
3. 当环境支持子 Agent 且 Human 明确授权时，主控 AI 可以把 execution item 委派给对应角色的子 Agent。
4. 主控 AI 负责整合结果、去噪、验证和回写事实源；子 Agent 只交回摘要、证据引用和风险提示。
5. 子 Agent 的中间日志、临时计划和未采纳草稿不进入长期事实源。
6. 并行写入需要 disjoint write set；否则应保持串行或只委派只读审查。
7. 自定义 Codex agent TOML 属于环境适配资产；00 文档只定义理念和边界，不规定具体文件必须存在。

一个可供 00 后续吸收的候选表述是：

```text
LDVH 支持多角色 AI 协作，但角色首先是事实源治理中的责任契约，而不是某个运行环境的固定线程形态。支持子 Agent 的环境可以把 WorkPlan 中边界清晰的 ExecutionItem 委派给专业子 Agent；不支持子 Agent 的环境仍可由同一 AI 按角色契约完成串行自检、复检和证据整理。
```

## 后续分流

1. 修改 `specs/00-LD-Vibe-Harness理念与纲要.md` 时，吸收“角色是契约，不是线程”的理念层表述。
2. 修改 `specs/06-工作流程基础规范.md` 时，定义主控、执行者、审查者、Human Gate 等流程角色边界。
3. 修改 `specs/21-WorkPlan-工作计划.md` 时，只保留 execution item 需要的最小 `role` 和证据字段，避免把 Codex custom agent schema 写入 WorkPlan。
4. 修改 `specs/04.02-LDVH能力资产与落地保障规范.md` 时，再判断是否需要把 Codex custom agent TOML、Skills、MCP、AGENTS.md 的关系纳入能力资产分层。
5. 如需长期维护 Codex 子 Agent 示例，应另建环境适配文档或 Skill，而不是塞进 00。
