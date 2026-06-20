---
id: study-0004
type: study
title: Claude Code CLI Subagents 创建调用与 LDVH 多角色设定调研
status: active
created: '2026-06-18T07:59:11'
updated: '2026-06-18T22:31:24+08:00'
summary: |
  Claude Code CLI 的 subagents 是专门 AI 助手，用于隔离会污染主上下文的搜索、日志、文件阅读、测试和专业审查等任务。Claude Code 支持通过 `/agents` 管理界面创建管理 subagents，也支持手动编写带 YAML frontmatter 的 Markdown 文件、通过 `--agents` CLI JSON 动态定义、通过 plugin 分发，或用 `--agent` 把某个 agent 作为整个会话的主代理。调用方式包括自动委派、自然语言命名、@ mention 保证调用、`--agent` 会话级默认，以及 `/fork` 分叉当前对话。
user_intent: 用户要求补充 Claude Code CLI 关于子 Agent / subagents 创建调用机制的同主题调研，为后续 00 文档多角色设定提供对照。
conclusion: |
  Claude Code CLI 对 LDVH 的启发是：它已经把 subagent 设计成“角色提示词 + 工具权限 + 模型 + MCP + Skills + hooks + memory + 调用方式”的完整运行期角色系统，但它仍是会话执行机制，不是项目长期事实源。LDVH 00 应抽象“Role Contract”，Claude Code 适配层可把 Role Contract 映射为 `.claude/agents/*.md`、`~/.claude/agents/*.md`、`--agents` JSON、plugin agents 或 `--agent` 主会话代理。主控必须负责委派边界、结果整合、验证和事实源回写。
urls:
  - ref: https://docs.anthropic.com/en/docs/claude-code/sub-agents
    title: Claude Code Subagents
    summary: 用于说明 Claude Code subagents 的定位、配置文件结构、工具权限和调用方式。
  - ref: https://docs.anthropic.com/zh-CN/docs/claude-code/sub-agents
    title: Claude Code Subagents 中文文档
    summary: 用于对照中文表述，确认 subagents 的概念边界和使用场景。
  - ref: https://docs.anthropic.com/en/docs/claude-code/cli-reference
    title: Claude Code CLI Reference
    summary: 用于说明 CLI 参数、会话级 agent 选择和命令入口对角色映射的影响。
  - ref: https://docs.anthropic.com/en/docs/claude-code/common-workflows
    title: Claude Code Common Workflows
    summary: 用于说明 Claude Code 常见工作流如何组织开发、审查和上下文管理。
  - ref: https://docs.anthropic.com/en/docs/claude-code/skills
    title: Claude Code Skills
    summary: 用于说明 Skills 如何补充 subagents，承接可复用流程和专业能力。
  - ref: https://docs.anthropic.com/en/docs/claude-code/hooks
    title: Claude Code Hooks
    summary: 用于说明 hooks 如何在工具执行前后提供自动化约束和检查。
related_sparks:
  - spark-0007
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

# Claude Code CLI Subagents 创建调用与 LDVH 多角色设定调研

## 研究问题

本报告回答三个问题：

1. Claude Code CLI 中如何创建 subagents；
2. Claude Code CLI 中如何调用和管理 subagents；
3. 这些机制对 LDVH 后续 `specs/00-LD-Vibe-Harness理念与纲要.md` 中多角色设定有什么启发。

这里的 subagent 指 Claude Code 官方文档中的 specialized AI assistant，而不是 Anthropic Agent SDK 中的任意应用级 agent。

## 输入与边界

本次调研使用 Claude Code 官方文档，访问时间为 2026-06-18：

- https://docs.anthropic.com/en/docs/claude-code/sub-agents
- https://docs.anthropic.com/zh-CN/docs/claude-code/sub-agents
- https://docs.anthropic.com/en/docs/claude-code/cli-reference
- https://docs.anthropic.com/en/docs/claude-code/common-workflows
- https://docs.anthropic.com/en/docs/claude-code/skills
- https://docs.anthropic.com/en/docs/claude-code/hooks

官方英文页面当前重定向到 `code.claude.com/docs/...`，内容仍为 Claude Code 官方文档。

## 关键发现

### Claude Code Subagents 解决什么问题

Claude Code 官方文档说明，当辅助任务会用搜索结果、日志或文件内容充斥主对话，而后续又不需要反复引用这些细节时，应使用 subagent。subagent 在自己的上下文中完成任务，只把摘要返回主对话。

Subagents 的价值包括：

- 保留主上下文，把探索和实现过程放到主对话之外；
- 通过工具限制强制执行约束；
- 通过用户级 subagents 跨项目复用配置；
- 为特定领域使用专注系统提示；
- 把任务路由到更快或更便宜的模型以控制成本。

官方文档也强调，subagents 在单个会话中工作；如果要并行运行许多独立会话并统一监控，应看 background agents；如果要多个会话互相通信，应看 agent teams。

这对 LDVH 的关键启发是：subagent 是上下文隔离和专业化执行机制，不能直接等同于长期事实源。

### 如何创建 Subagents

Claude Code 推荐使用 `/agents` 命令创建和管理 subagents。`/agents` 会打开管理界面，包含 Running 和 Library 两类视图：

- Running：列出实时和最近完成的 subagents，可打开或停止；
- Library：查看可用 subagents，创建新 subagents，编辑配置和工具访问，删除自定义 subagents，查看重名时哪个生效。

快速创建流程包括：

1. 在 Claude Code 中运行 `/agents`；
2. 在 Library 中选择 Create new agent；
3. 选择 Personal，保存到 `~/.claude/agents/`；
4. 选择 Generate with Claude 或手动配置；
5. 选择工具；
6. 选择模型；
7. 选择颜色；
8. 选择是否配置 memory；
9. 保存后立即可用。

除 `/agents` 外，还可以：

- 手动创建 Markdown 文件；
- 通过 `--agents` CLI 标志以 JSON 动态定义当前会话 subagents；
- 通过 plugin 的 `agents/` 目录分发；
- 通过 managed settings 部署组织范围 subagents。

Subagent 存储位置和优先级如下：

1. 托管设置，组织范围；
2. `--agents` CLI 标志，当前会话；
3. `.claude/agents/`，当前项目；
4. `~/.claude/agents/`，用户所有项目；
5. Plugin 的 `agents/` 目录。

当多个 subagents 同名时，更高优先级的位置获胜。

### Subagent 文件结构

Claude Code subagent 是带 YAML frontmatter 的 Markdown 文件。示例：

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

只有 `name` 和 `description` 必填。常见字段包括：

- `name`：唯一标识；
- `description`：Claude 何时应委托给该 subagent；
- `tools`：允许使用的工具；
- `disallowedTools`：从继承工具中移除的工具；
- `model`：`sonnet`、`opus`、`haiku`、`fable`、完整模型 ID 或 `inherit`；
- `permissionMode`：权限模式；
- `maxTurns`：最大代理轮数；
- `skills`：启动时预加载到 subagent 上下文的 Skills；
- `mcpServers`：限定给该 subagent 的 MCP Server；
- `hooks`：限定于 subagent 的生命周期 hooks；
- `memory` / memory scope 相关配置；
- `color`；
- `initialPrompt`。

文件正文成为 subagent 的系统提示。官方文档特别说明，subagent 不接收完整的 Claude Code 系统提示，只接收自身提示和基础环境信息。非 fork subagent 从新的隔离上下文开始。

### 工具、模型、MCP、Skills 和 Hooks 边界

Claude Code subagents 默认继承主对话可用工具和 MCP 工具，但可以通过 `tools` 允许列表或 `disallowedTools` 拒绝列表限制权限。例如只读审查者可以只允许 `Read`、`Grep`、`Glob` 和 `Bash`，不允许 `Edit` 或 `Write`。

模型解析顺序包括：

1. `CLAUDE_CODE_SUBAGENT_MODEL` 环境变量；
2. 每次调用的 `model` 参数；
3. subagent frontmatter 中的 `model`；
4. 主对话模型。

`mcpServers` 可以给 subagent 提供父会话中没有的 MCP Server，也可以引用已有 MCP Server。`skills` 字段可以在启动时把 Skill 内容预加载到 subagent 上下文中。Hooks 可用于在工具调用前后做确定性控制，也可在项目设置中监听 `SubagentStart` 和 `SubagentStop`。

这说明 Claude Code 的 subagent 不只是“一个新线程”，而是一个可配置工具、模型、技能、MCP、hook 和记忆边界的角色容器。

### 如何调用 Subagents

Claude Code 支持自动委派和显式调用。

自动委派依赖当前任务、subagent 的 `description` 和上下文。当 description 中写清 “use proactively” 等触发语时，Claude 更容易主动委派。

显式调用有三类：

1. 自然语言命名：例如 `Use the test-runner subagent to fix failing tests`；
2. `@` mention：从类型提示中选择 subagent，保证该 subagent 为一个任务运行；
3. 会话级默认：通过 `--agent` 标志或 `agent` 设置，让整个会话使用该 agent 的系统提示、工具限制和模型。

CLI reference 还提供了两项关键参数：

- `claude --agent my-custom-agent`：指定当前会话 agent；
- `claude --agents '{"reviewer":{"description":"Reviews code","prompt":"You are a code reviewer"}}'`：用 JSON 动态定义当前会话 subagents，字段与 subagent frontmatter 相同，另用 `prompt` 表示 agent 指令。

官方 common workflows 给出的典型用法是：让 subagent 调研认证系统如何处理 token refresh，只把探索结果返回主对话。

### 前台、后台、并行、嵌套和 Fork

Claude Code subagents 可以前台或后台运行：

- 前台 subagent 阻塞主对话直到完成，权限提示会传递给用户；
- 后台 subagent 并发运行，使用会话中已授予的权限，并自动拒绝任何会提示的工具调用。

常见模式包括：

- 隔离高容量操作，例如测试、文档抓取、日志处理；
- 并行研究，例如分别调研 authentication、database、API 模块；
- 串联 subagents，例如先让 code-reviewer 找性能问题，再让 optimizer 修复。

Claude Code 也支持嵌套 subagents。文档说明从 v2.1.172 开始，subagent 可以生成自己的 subagents；但后台 subagent 有固定深度限制，避免失控并发树。若要禁止某个 subagent 继续生成其他 subagents，可以从工具列表中省略 `Agent` 或加入 `disallowedTools`。

Fork 是另一个重要形态。`/fork` 会分叉当前对话，继承目前为止的完整对话，而不是从空白上下文开始。Fork 适合需要大量背景才能有用的辅助任务，或从同一起点并行尝试多个方法。它会让自己的工具调用保持在主对话之外，只把最终结果返回。

对 LDVH 的判断是：普通 subagent 更适合执行 WorkPlan 中边界清楚的 execution item；fork 更适合同一上下文下的并行假设探索或备选方案，但更容易带入主上下文噪音，需要更严格的输出摘要和事实源回写边界。

### 上下文与持久化

非 fork subagent 的初始上下文包括：

- 自身系统提示和环境详情；
- Claude 编写的委托任务消息；
- CLAUDE.md 和 memory 层级；
- Git 状态快照；
- 预加载的 Skills。

它看不到主对话历史、已经调用的技能或已经读过的文件。Subagent 转录独立于主对话持久化，主对话 compact 不影响 subagent 转录；恢复同一会话后也可恢复 subagent。默认清理周期由设置控制。

这与 LDVH 的事实源边界很契合：subagent transcript 是环境运行记录，不应直接成为 LDVH 事实源。LDVH 只提取结论、证据引用、风险、验证和关闭信息。

### 何时不用 Subagents

官方文档给出了选择边界。

使用主对话的情况：

- 任务需要频繁来回或迭代细化；
- 多个阶段共享重要上下文；
- 正在做快速、有针对性的更改；
- 延迟重要，因为 subagent 从头收集上下文需要时间。

使用 subagents 的情况：

- 任务产生不需要进入主上下文的详细输出；
- 想强制执行工具限制或权限；
- 工作自包含，可以返回摘要。

如果想要可重用提示或在主对话上下文中运行的工作流，而不是隔离 subagent 上下文，应考虑 Skills。

## 建议

Claude Code CLI 是当前三份调研中最接近“角色契约完整运行时”的环境。它把角色拆成：

- `name`：角色 ID；
- `description`：触发条件；
- Markdown 正文：角色行为契约；
- `tools` / `disallowedTools`：权限边界；
- `model`：模型选择；
- `permissionMode`：授权模式；
- `skills`：预加载流程和知识；
- `mcpServers`：外部能力；
- `hooks`：确定性控制；
- memory：跨会话经验；
- `@`、自然语言、自动委派、`--agent`、`--agents`、`/fork`：调用形态。

LDVH 00 可以吸收这套思想，但不能把 Claude Code frontmatter 直接写成 LDVH 工作模型字段。建议：

1. 00 文档只定义环境无关 Role Contract；
2. Claude Code 适配层负责把 Role Contract 映射为 `.claude/agents/*.md`、`~/.claude/agents/*.md`、`--agents` JSON 或 plugin agents；
3. WorkPlan 的 `execution_items[*].role` 只引用角色，不复制完整 subagent 文件；
4. 主控 AI 负责决定是否委派、选择前台/后台/fork、约束工具、等待结果和整合摘要；
5. 子 Agent 中间输出和 transcript 不进入 LDVH 长期事实源；
6. 只有摘要、证据引用、验证结果、关闭判断、风险和后续分流进入 WorkPlan / Spark / Study / ADR / Change；
7. 若需要多层嵌套或 fork，应在 Role Contract 中记录防爆炸边界，例如最大深度、最大并发、只读限制和停止条件。

一个可供 00 后续吸收的候选表述是：

```text
LDVH 的多角色协作可在 Claude Code CLI 中落地为 subagent Markdown、`--agents` 动态定义、`--agent` 会话级代理或 plugin agents；但 LDVH 角色本体仍是 Role Contract。Claude Code 的 subagent transcript、fork 过程和后台任务日志属于运行期证据来源，只有经过主控整合后的摘要、验证结果、证据引用和风险分流进入 LDVH 长期事实源。
```

## 后续分流

1. 修改 `specs/00-LD-Vibe-Harness理念与纲要.md` 时，吸收 Claude Code “角色提示词 + 工具权限 + 模型 + MCP + Skill + hooks + memory”的角色契约思想。
2. 修改 `specs/04.02-LDVH能力资产与落地保障规范.md` 时，判断 `.claude/agents`、`.claude/skills`、CLAUDE.md、MCP、hooks 和 plugins 的能力资产分层。
3. 修改 `specs/06-工作流程基础规范.md` 时，定义主控是否允许自动委派、何时必须 Human Gate、何时使用前台/后台/fork。
4. 修改 `specs/21-WorkPlan-工作计划.md` 时，保留最小角色引用和证据字段，不把 Claude Code frontmatter 作为 WorkPlan schema。
5. 如要给 Claude Code 生成示例 subagent，应另建环境适配文档或 Skill，并要求项目级 agent 文件进入版本控制或保留定义摘要。
