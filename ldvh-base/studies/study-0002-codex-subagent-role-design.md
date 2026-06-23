---
id: study-0002
type: study
title: Codex 子 Agent 创建调用与 LDVH 多角色设定调研
status: active
created: '2026-06-18T07:59:11'
updated: '2026-06-23T09:22:10+08:00'
summary: |
  Codex 子 Agent 适合承接可并行、边界清晰、噪音较高或需要专业视角的运行期工作。Codex 官方资料显示，子 Agent 不会自动生成，必须由用户明确要求并行委派；Codex 可使用内置 default、worker、explorer，也可通过个人或项目级 TOML 文件定义自定义 agent。当前 Codex App 工具面还暴露了 spawn_agent、wait_agent、send_input 和 close_agent 这类管理动作。
user_intent: 用户要求调研 Codex 中如何创建子 Agent 与调用子 Agent，为后续 00 文档多角色设定做前期准备。
conclusion: |
  LDVH 应把多角色设定抽象为环境无关的 Role Contract，而不是把它绑定为 Codex 子 Agent 配置。Codex 子 Agent 可以作为支持环境中的运行期委派实现：由 WorkCase execution item 给出角色、输入和输出要求，由 Human 或主控 AI 在明确授权下触发子 Agent。00 文档应强调角色契约、证据回收和主控整合责任；具体 Codex 创建、调用和自定义 agent 配置应放入环境适配、能力资产或后续专门规范。
urls:
- ref: https://developers.openai.com/codex/concepts/subagents
  title: Codex Subagent Concepts
  summary: 用于说明 Codex 子 Agent 的定位、适用场景和上下文隔离价值。
- ref: https://developers.openai.com/codex/subagents
  title: Codex Subagents
  summary: 用于说明 Codex 子 Agent 的创建、配置和调用方式，支撑 LDVH 角色契约映射判断。
related_sparks:
- spark-0007
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
- specs/00-LD-Vibe-Harness理念与纲要.md
- specs/04.02-LDVH能力资产与保障机制规范.md
- specs/06-行动编排基础规范.md
- specs/21-WorkCase-工作项.md
archive_reason: null
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

这与 LDVH 当前 WorkCase / ExecutionItem 方向一致：长期事实源只保留可恢复、可验证、可关闭的最小证据，不保存 AI 的完整运行期过程。

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
6. Subagent workflow 承载一次 WorkCase 执行中的运行期并行委派。

## 建议

后续 00 文档可以引入“多角色协作”的理念，但建议使用环境无关表述：

1. LDVH 的角色是契约，不是线程。角色契约应描述目的、输入、权限、输出、证据、交还条件和停止条件。
2. WorkCase 的 `orchestration.execution_items[*].role` 可以声明需要的专业视角，但不等于必须创建 Codex 子 Agent。
3. 当环境支持子 Agent 且 Human 明确授权时，主控 AI 可以把 execution item 委派给对应角色的子 Agent。
4. 主控 AI 负责整合结果、去噪、验证和回写事实源；子 Agent 只交回摘要、证据引用和风险提示。
5. 子 Agent 的中间日志、临时计划和未采纳草稿不进入长期事实源。
6. 并行写入需要 disjoint write set；否则应保持串行或只委派只读审查。
7. 自定义 Codex agent TOML 属于环境适配资产；00 文档只定义理念和边界，不规定具体文件必须存在。

一个可供 00 后续吸收的候选表述是：

```text
LDVH 支持多角色 AI 协作，但角色首先是事实源治理中的责任契约，而不是某个运行环境的固定线程形态。支持子 Agent 的环境可以把 WorkCase 中边界清晰的 ExecutionItem 委派给专业子 Agent；不支持子 Agent 的环境仍可由同一 AI 按角色契约完成串行自检、复检和证据整理。
```

## 后续分流

1. 修改 `specs/00-LD-Vibe-Harness理念与纲要.md` 时，吸收“角色是契约，不是线程”的理念层表述。
2. 修改 `specs/06-行动编排基础规范.md` 时，定义主控、执行者、审查者、Human Gate 等流程角色边界。
3. 修改 `specs/21-WorkCase-工作项.md` 时，只保留 execution item 需要的最小 `role` 和证据字段，避免把 Codex custom agent schema 写入 WorkCase。
4. 修改 `specs/04.02-LDVH能力资产与保障机制规范.md` 时，再判断是否需要把 Codex custom agent TOML、Skills、MCP、AGENTS.md 的关系纳入能力资产分层。
5. 如需长期维护 Codex 子 Agent 示例，应另建环境适配文档或 Skill，而不是塞进 00。

## 2026-06-22 讨论补充：Codex 子 Agent 需求与 v1 规范落点

本次后续讨论确认了一个更具体的落地判断：在 Codex 环境下用好子 Agent，不能只写成 Codex 配置或 prompt 技巧；应先在 LDVH v1 体系中明确“为什么需要子 Agent、何时需要、由谁调度、输入输出如何回收”，再把 Codex 的具体能力作为环境适配承接。

当前 Codex 子 Agent 的一个重要产品边界是：主控不会默认自动 spawn 子 Agent，通常需要用户明确要求 subagents、delegate 或 parallel agent work。这个边界不是缺陷，而是成本、权限、上下文隔离、并行写入冲突和责任归属的综合权衡。LDVH 若希望 AI 在特定场景下更稳定地使用子 Agent，应把触发条件、输入包、输出格式、主控整合责任和降级方式写入自己的行动编排与能力资产边界，而不是期待 Codex 主控形成隐式习惯。

本次还确认了一个 Codex App 工具层约束：启动子 Agent 时，普通文本任务使用 `message`，结构化输入使用 `items`，两者应二选一；`fork_context` 只表示是否继承当前线程历史，不是另一个可混用的 context 参数。LDVH 后续如果写 Codex 适配，应把这个约束归入环境适配层，作为 Codex 输入包构造注意事项，而不是上升为所有环境的 Role Contract 规则。

按现有 specs v1 分层，建议落点如下：

1. `specs/02-术语规范.md`：保留并必要时补强 `Agent`、`Role Contract`、`ExecutionItem` 的概念边界。子 Agent 是环境中的 Agent 能力或实体；Role Contract 是 LDVH 的环境无关角色契约，不等于 Codex subagent 本身。
2. `specs/06-行动编排基础规范.md`：承载主控调度 Agent 的通用规则，包括何时考虑子 Agent、谁能调度、输入包最小要求、输出必须交还主控、哪些情况触发 Human Gate，以及 Agent 输出不得直接生效。
3. `specs/21-WorkCase-工作项.md`：只记录实例层最小事实，例如 `orchestration.execution_items[*].role`、`input_refs`、`expected_output`、审核条目的 `prompt_context`、`agent_name` 和 `controller_resolution`。WorkCase 不应写入 Codex spawn schema，也不维护完整 Role Contract。
4. `specs/04.02-LDVH能力资产与保障机制规范.md` 和 `agents/`：当 LDVH 需要固定 Agent 能力资产时，在 04.02 中按固定资产规则登记，并在 `agents/` 中维护权威定义摘要。Agent 资产应说明角色边界、输入摘要、工具权限、是否允许写入、输出格式、主控复核、Human Gate 和证据回写位置。
5. `specs/04.03-环境入口适配与部署规范.md`：承接 Codex 专属适配，包括 `spawn_agent`、`fork_context`、`message` / `items` 二选一、Codex custom agent TOML、`agents.max_threads`、`agents.max_depth`、`SubagentStart` / `SubagentStop` Hook 候选，以及非 Codex 环境的降级边界。
6. `specs/30-59` 具体行动编排：如果要把子 Agent 复查变成稳定流程，应优先把 `spark-0021-subagent-review-orchestration-gap` 收敛为一个 active 行动编排，例如“子 Agent 复核编排”。该流程应定义 Scenario、Context 输入包、并行等待、结果回收、硬问题处理、Agent 关闭、WorkCase 回写、Human Gate 和失败降级。

因此，当前更优先的建设方向不是先改 21 的字段，也不是直接创建 Codex agent 配置，而是先把 `spark-0021` 所指出的“子 Agent 复查编排流程缺口”收敛成具体行动编排。字段层已有承载点，缺的是主控何时必须发起、如何发起、如何等待、如何处理结论和如何回写的 active workflow。

## 2026-06-23 讨论补充：Trae 子 Agent 并行策略对照

本次补充调研了 Trae 的子 Agent 并行策略，用于和 Codex subagent workflow 对照。Trae 的并行能力不应简单等同于 Codex 的 `spawn_agent`。更准确地说，Trae 是由“SOLO Agent 主控 + 可调用自定义智能体 + SOLO 多任务并行”共同形成并行策略。

Trae 官方文档显示，SOLO 模式以 AI 为主导，支持自动规划并执行从需求理解、代码生成、测试到成果预览的全流程；SOLO 模式的任务管理支持在一个项目中同时管理多个任务。SOLO Agent 可以配置可调用的自定义智能体、MCP Server 和内置工具。配置好可调用智能体后，SOLO Agent 作为主控智能体，可以在处理复杂长上下文任务时自动调用相应智能体，将任务拆分和隔离，让不同智能体在独立上下文中处理各自任务；用户也可以在提示词中明确指定要调用的智能体。

因此，Trae 的并行策略至少有两层：

1. 任务级并行：SOLO 模式通过任务管理面板支持同一项目内多个任务并行推进，适合把大目标拆成多个任务容器。
2. 角色级委派：SOLO Agent 在单个复杂任务内可以自动或按用户指定调用自定义智能体，让专业角色在隔离上下文中处理模块化任务。

这和 Codex 的差异是：Codex 子 Agent 通常需要用户明确要求 subagents、delegate 或 parallel agent work；Trae SOLO 则更偏“主控自动调度配置好的专业智能体”，同时保留用户显式 `@` 指定智能体的入口。Codex 的并行容器更接近 agent thread；Trae 的并行容器则同时包括 SOLO 多任务面板和 SOLO Agent 的自定义智能体调用。

社区实践还提出了同项目并行的工程化风险：上下文污染、路径越权和执行时序冲突。该实践建议采用单 Workspace、SOLO Coder、多任务隔离、路径白名单和专属 SubAgent 调度，并把并行任务按依赖关系分为无依赖、弱依赖和强依赖三类。该内容属于社区经验，不是 Trae 官方规范；但它对 LDVH 很有参考价值，因为它补上了官方能力说明之外的冲突治理策略。

对 LDVH 的吸收判断如下：

1. Trae 适配应把 Role Contract 映射为自定义智能体配置、SOLO Agent 可调用智能体清单和必要的工具权限，而不是把 Trae 智能体配置当作 LDVH 角色本体。
2. Trae 的任务级并行应映射到 WorkCase / ExecutionItem 的任务拆分、依赖关系、输入输出和证据回收；Trae 多任务面板只是执行界面，不是 LDVH 长期事实源。
3. Trae 的角色级委派应映射到行动编排中的 Agent 调度规则：何时自动调用、何时要求 Human 显式指定、何时降级为主控串行多视角审查。
4. 同项目并行写入必须有路径或模块边界。前端、后端、测试、文档、审查等 disjoint scope 可以并行；共享配置、数据库 schema、核心接口契约、公共类型等强依赖区域应先由主控确认接口或串行处理。
5. Trae Spec / Plan 产物可以作为输入资料、执行界面或证据引用，但不得替代 LDVH WorkCase、Spark、Study、ADR、Pitfall 或 Git commit records。

可供后续 04.03 或 Trae 适配文档吸收的候选表述：

```text
Trae 环境中的并行能力由 SOLO 多任务管理和 SOLO Agent 调用自定义智能体共同承载。LDVH 可将 WorkCase 的 ExecutionItem 映射为 Trae 任务级并行，将 Role Contract 映射为可被 SOLO Agent 调用的自定义智能体；但并行执行必须保留输入、输出、路径边界、依赖关系、主控回收、Human Gate 和事实源回写规则。Trae 运行期任务、对话流和 Spec / Plan 文件不是 LDVH 最终事实源。
```

## 2026-06-23 讨论补充：主控监督与角色团队设想

本次讨论进一步明确了用户对 LDVH 多角色机制的目标形态：LDVH 希望形成“一个主控 + 一群角色”的协作结构。主控不只是普通执行者，而更像监督、编排者和最终责任主体；角色则承担具体执行、查询、审查、验证、反方意见、专项风险检查等职责。主控可以自行安排角色做事，也可以调度角色互相审查，但角色输出不能直接成为最终事实源，必须回到主控整合、判断、验证和回写。

这个设想应区分两层：

1. **业务治理层**：主控围绕 WorkCase、ExecutionItem、Role Contract、Human Gate 和事实源回写组织角色。这里关注的是谁负责目标理解、谁负责执行、谁负责审查、谁能提出阻塞、谁能触发 Human Gate、谁能写回事实源。业务治理层的本体仍是 LDVH 的 Role Contract 和行动编排，不是某个环境的 agent thread。
2. **技术执行层**：为了提高速度和覆盖面，主控可以把可并行的信息收集、搜索、代码库查询、日志分析、资料对照、测试缺口扫描等工作委派给多个查询型或探索型子 Agent。技术层的子 Agent 不一定对应长期业务角色，它们更像临时并行 worker，用于快速收集证据、缩短等待时间和减少主线程上下文污染。

Trae 的 SOLO 形态比较接近这个设想：业务层可以由 SOLO Agent 承担主控，专业自定义智能体承担角色；技术层可以通过 SOLO 多任务管理、SOLO Agent 调用可用智能体、必要时专属查询或搜索智能体来并行收集材料。Trae 的优势是主控可以自动调用已配置角色，用户也可以显式指定角色；但 LDVH 仍需要规定路径边界、输入输出、依赖关系和事实源回写，避免 Trae 运行期任务或 Spec / Plan 文件变成第二事实源。

Codex 当前缺少 Trae SOLO 这种产品化“主控自动调度角色团队”的稳定习惯和界面。Codex 虽然有 subagent workflow、custom agent TOML、`spawn_agent`、`fork_context` 和并发设置，但产品边界更偏显式委派：用户通常需要明确要求 subagents、delegate 或 parallel agent work。因此，若 LDVH 想在 Codex 环境下获得类似 SOLO 的主控-角色团队效果，就需要由 LDVH 自己在机制层补齐：

1. 在行动编排中定义何时必须或建议启动角色；
2. 在 Role Contract 中定义角色目的、输入、工具权限、禁止动作、输出和停止条件；
3. 在 WorkCase / ExecutionItem 中记录本次任务需要哪些角色、输入引用、预期输出和证据回收；
4. 在 Codex 适配中把角色映射为 custom agent、`spawn_agent` 调用、`message` / `items` 输入包和可选 `fork_context`；
5. 对技术层并行查询定义轻量策略，例如多个只读 explorer 分别查不同资料源、模块、日志或风险点，主控等待摘要后统一判断；
6. 对并行写入设置更严格边界，例如 disjoint write set、接口先确认、共享配置串行处理、子 Agent 不得直接关闭 WorkCase。

这一判断对 `spark-0021-subagent-review-orchestration-gap` 有直接影响：后续的“子 Agent 复核编排”不应只定义关闭前的审查表格，还应定义主控如何在业务层组织角色、如何在技术层并行查询和搜索、如何把角色输出 intake 成 accepted / rejected / deferred / needs-human，以及 Codex 缺少 SOLO 自动调度时应如何通过 LDVH 行动编排模拟该能力。

## 2026-06-23 讨论补充：Claude 可学习机制与跨环境转换

本次讨论补充了 Claude Code 可供 LDVH 学习的机制。Claude Code 的 subagent 更接近完整角色容器：除了独立上下文和系统提示外，还可以围绕工具权限、permission mode、model、MCP、skills、hooks、memory、background 运行和工作区隔离形成边界。Claude 还区分单会话内的 subagent 和更实验性的 agent teams；后者包含 team lead、teammates、共享任务列表、mailbox、任务依赖、计划批准和 lead synthesis，更接近“主控 + 一群角色”的协作形态。

对 LDVH 最有价值的学习点不是复制 Claude 的文件格式，而是吸收它的分层：

1. **角色容器契约**：Role Contract 不只写角色名和职责，还应写输入包、允许工具、禁止动作、是否可写、输出 schema、交还主控、权限边界、隔离方式和失败降级。
2. **业务角色与技术 worker 分离**：业务角色负责复查、执行、风险、验收和 Human Gate；技术 worker 负责搜索、代码探索、日志分析、资料查询、测试缺口扫描等加速工作。
3. **触发条件写入角色定义**：Claude 依赖 subagent description 辅助自动委派。LDVH 的 Role Contract 也应包含何时使用、何时不使用和误触发风险，而不是只靠主控临场判断。
4. **共享任务与输出 intake**：agent teams 的 shared task list、mailbox、task dependencies 和 lead synthesis 可启发 LDVH 设计 ExecutionItem intake。角色输出应被主控标记为 accepted、rejected、deferred 或 needs-human，并形成 controller_resolution。
5. **计划批准与写入门禁**：子 Agent 先只读形成计划，主控或 Human Gate 批准后再允许写入；这比直接并行修改安全。
6. **Hooks 和确定性控制**：生命周期事件可用于要求结构化输出、检查 evidence_refs、阻止缺少 controller_resolution 的关闭动作或提醒 Human Gate。

这些机制在 Codex 和 Trae 中可以部分转换，但转换层级不同：

| Claude 机制 | Codex 转换方式 | Trae 转换方式 | LDVH 归属 |
|---|---|---|---|
| subagent 角色容器 | custom agent TOML + `spawn_agent` 输入包；部分工具、模型、sandbox 可适配 | 自定义智能体提示词、英文标识、何时调用、工具/MCP 配置 | 04.02 Agent 资产 + Role Contract |
| description 自动委派 | Codex 默认仍偏显式委派，只能通过行动编排和 prompt 触发模拟 | SOLO Agent 可按“何时调用”自动或半自动调用 | 06 行动编排 Scenario / Agent 调度 |
| Explore / 查询型 agent | `explorer` 或只读 custom agent 并行查询 | 查询/搜索型自定义智能体或 SOLO 多任务并行 | 技术 worker 模式，进入行动编排而非事实模型 |
| agent teams 的 lead / teammates | Codex 没有等价团队界面，可由主控 + 多个 subagent + WorkCase intake 模拟 | SOLO Agent + 可调用智能体 + 多任务面板较接近 | WorkCase / ExecutionItem + 子 Agent 复核编排 |
| shared task list / mailbox | 无直接等价，需由 WorkCase execution_items、临时 intake 和主控摘要模拟 | Trae 多任务与 Spec/Plan 可作为运行界面，但非最终事实源 | 21 WorkCase 字段或后续流程扩展 |
| 计划批准后写入 | 主控先要求 subagent 只读计划，再决定是否授权 worker 写入 | SOLO Plan / Spec 与用户确认可作为环境执行界面 | Human Gate + 行动编排 Gate |
| hooks 生命周期控制 | Codex Hook 候选事件如 SubagentStart/Stop、Stop、PreCompact 可适配但需实测 | Trae Hook 能力较弱或需降级为规则/命令/人工检查 | 04.03 环境适配 + 07 Code 校验 |

结论是：Claude 的机制大多可以在 LDVH 中抽象成 Role Contract、ExecutionItem、Agent 调度、输出 intake、Human Gate 和 Hook/Code 校验；但在 Codex 中需要更多由 LDVH 机制主动补齐，因为 Codex 偏显式 spawn，没有 Claude agent teams 那样的团队层，也没有 Trae SOLO 那样的产品化主控面板。Trae 对“主控 + 角色团队”的转换更自然，但仍要防止 Trae 运行期任务、Spec/Plan 和智能体配置变成 LDVH 第二事实源。

## 2026-06-23 讨论补充：LDVH v2 中的设计归属

本次讨论进一步确认：在 LDVH v2 中，“主控调度角色 / 子 Agent 并行行动”不应被设计成一个孤立的新顶层组件，也不应把整套机制复制进每一个具体工作编排。更合适的做法是：在通用层定义一次调度机制，在每个实际工作编排中按需引用和实例化。

核心判断如下：

1. 该机制的主归属是 `03-行动编排规范`。03 应定义主控责任、角色派发、并行探索、结果回流、冲突仲裁、Human Gate、事实源写回前的主控决议，以及失败降级。
2. 该机制的承载与适配归属是 `06-运行时扩展规范`。06 应定义 Agent / Role Contract 这类运行时承载物，说明角色如何在 Codex、Trae、Claude 等环境中投影为 custom agent、SOLO 可调用智能体、subagent 或 team member。
3. `21-WorkCase` 只记录实例事实，不定义机制本体。WorkCase 可以记录本次派发了哪些角色、输入引用、输出摘要、证据引用、review item、controller resolution 和 Human Gate 结果，但不应维护完整 Role Contract，也不应写入 Codex / Trae / Claude 的专属调用 schema。
4. `04-Code` 负责确定性校验。例如校验进入复核状态时是否有 required perspectives，每个 review item 是否有输入引用、结论和证据，controller resolution 是否覆盖角色输出，主控是否把自己的判断伪装成独立 Agent 结论。
5. `05-Web` 负责人类可见的操作面和审查面。例如展示角色派发、并行任务进度、结果 intake、accepted / rejected / deferred / needs-human 状态、证据覆盖和 Human Gate 决策。
6. `07-事实源边界` 负责声明输出何时成为事实。Agent、chat、tool、Trae Spec/Plan、Claude mailbox 或 Codex subagent summary 都只是运行期过程产物；只有经主控决议并写回权威事实源后，才成为 LDVH 稳定事实。
7. `08-测试与保障` 负责验证机制可用性。例如场景测试、反例测试、缺证据阻断、并行写入冲突、环境不支持 subagent 时的串行降级。

因此，后续 v2 落地时应避免两种偏差：

1. 不要把“子 Agent 调度”做成只属于 Codex、Trae 或 Claude 的环境技巧。环境能力只是 06 的投影，LDVH 本体仍是行动编排和角色契约。
2. 不要把每个 30-59 具体行动编排都写成一套完整的子 Agent 规范。具体编排只需要声明本场景需要哪些角色、何时触发、允许并行到什么程度、输出如何回收、哪些结论必须 Human Gate。

一个较稳的 v2 分层可以表达为：

```text
03 行动编排基础规范
  定义：主控-角色调度机制、并行探索、复核、收口和写回门禁

06 运行时扩展规范
  定义：Agent / Role Contract / 环境投影 / 运行时承载物

30-59 具体行动编排
  引用：本编排需要哪些角色、何时并行、如何回收结果、何时 Human Gate

21 WorkCase
  记录：实际派发、输入、输出、证据、主控决议和人类确认
```

这也回答了“设计思想是否要融合到每一个实际工作编排里”的问题：应当融合，但融合的是调度思想和引用点，不是复制机制正文。换句话说，`Role Contract` 是角色能力本体，`03` 是调用与治理语法，`30-59` 是具体场景用法，`21` 是审计记录。

对后续 AI 研究落地的建议是：优先在 v2 草案中提出一个候选行动编排成员，例如“主控-角色调度编排”或“子 Agent 复核编排”。该候选成员应从 03 的通用机制派生，覆盖业务治理层和技术执行层两类需求：业务治理层处理稳定角色、复核和责任归属；技术执行层处理临时查询 worker、并行搜索、日志分析、代码探索和资料对照。Codex 因缺少 Trae SOLO 或 Claude agent teams 那样的产品化自动团队机制，需要由 LDVH 在 03/06 层补齐触发、输入、输出、等待、intake 和降级规则。
