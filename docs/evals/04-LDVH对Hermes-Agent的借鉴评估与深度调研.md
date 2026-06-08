# LD Vibe Harness 对 Hermes-Agent 的借鉴评估与深度调研

> 创建日期：2026-06-06
> 更新日期：2026-06-09
> 定位：LD Vibe Harness 对 Hermes-Agent 的项目级借鉴评估与深度调研
> 调研边界：不直接构成强制规则
> 执行效力：无；规范规则需进入 docs/specs 正文区，决策或工作事实需进入对应工作对象后才生效
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/02-术语规范.md`、`docs/specs/01-目录说明.md`、`docs/specs/04-事实源边界与承载规范.md`
> 调研对象：NousResearch/hermes-agent
> 源码位置：`/Users/dmh2002/trae_projects/hermes-agent`
> 仓库来源：`https://github.com/NousResearch/hermes-agent.git`
> 调研 HEAD：`e375c33f7090c329e6a6a741e26fc9082b27d728`

---

## 1. 本文解决的问题

本文评估 Hermes-Agent 的调用任务生成与执行机制对 LD Vibe Harness 的借鉴价值，同时明确 LD Vibe Harness 不应简单复制通用 Agent 平台或自动化执行框架，而应保持自身"面向 Vibe Coding 的工程驾驭框架"定位。本文是内部调研，不直接构成强制规则；调研结论进入 docs/specs 正文区或 ADR 后才成为稳定规则。

---

## 2. 结论

Hermes Agent 是一个以 Python CLI 为入口的通用 AI Agent 产品。它的核心设计不是单一"任务对象事实源"，而是把用户输入、CLI 命令、LLM 工具调用、计划待办、持久记忆、Skills、Cron Job、Kanban 和 Subagent 委派组合成一个可运行的 Agent 操作系统。

从源码看，Hermes Agent 的"调用任务"主要分为四类：

| 类型 | 源码入口 | 任务表达 | 执行方式 |
|---|---|---|---|
| 即时对话任务 | `hermes_cli/main.py`、`run_agent.py`、`agent/conversation_loop.py` | 用户消息 + 会话消息列表 | `AIAgent` 调用模型，模型可连续触发工具 |
| 工具调用任务 | `model_tools.py`、`tools/registry.py`、`agent/tool_executor.py` | OpenAI-style `tool_calls` | 注册表分发，同轮多工具可并发执行 |
| 计划/任务管理 | `tools/todo_tool.py`、`tools/kanban_tools.py` | Todo 内存列表或 Kanban DB 任务 | Todo 用会话内状态，Kanban 用结构化任务生命周期 |
| 定时/自动化任务 | `tools/cronjob_tools.py`、`cron/jobs.py`、`cron/scheduler.py` | Cron Job 记录：prompt、schedule、skill、workdir 等 | 调度器按计划拉起 Agent 或脚本执行 |

对 LDVH 最有参考价值的是三点：

1. **工具注册表 + Toolset 分组**：Hermes 用 `tools/registry.py` 和 `toolsets.py` 将工具能力模块化，允许按场景限制工具范围。
2. **调用任务的多层形态**：同一产品中同时存在即时会话、Todo、Kanban、Cron、Subagent 五类任务形态，分别解决不同粒度的问题。
3. **执行过程的可观测和安全护栏**：工具执行经过 scope gate、plugin block、guardrail、checkpoint、并发执行、结果压缩/持久化等环节，而不是模型直接调用函数。

---

## 3. 项目结构与入口

### 3.1 包与定位

`pyproject.toml` 显示项目名为 `hermes-agent`，版本为 `0.16.0`，描述为：

> The self-improving AI agent — creates skills from experience, improves them during use, and runs anywhere

核心依赖包括：

- `openai`：统一模型调用接口；
- `prompt_toolkit`：交互式 CLI；
- `croniter`：Cron 调度；
- `fastapi` / `uvicorn`：Gateway/API；
- `pyyaml` / `ruamel.yaml`：配置与结构化文件；
- `pydantic`：结构化数据；
- 多个 provider / messaging / MCP / vision / honcho 等 optional extra。

这说明 Hermes Agent 不只是 CLI 聊天工具，而是面向本地、网关、定时任务、消息平台、技能生态和多环境运行的综合 Agent 平台。

### 3.2 CLI 入口

`hermes_cli/main.py` 的顶部用法列出核心命令：

- `hermes chat`：交互式聊天；
- `hermes gateway`：网关服务；
- `hermes cron`：管理定时任务；
- `hermes kanban`：任务看板；
- `hermes honcho`：外部记忆集成；
- `hermes acp`：作为 ACP server 接入编辑器。

这意味着 Hermes 的任务入口不是单一 command，而是一组"运行面"：CLI 会话、Gateway、Cron、Kanban、编辑器协议。

### 3.3 Agent 主体

`run_agent.py` 定义 `AIAgent`，负责模型调用、工具定义、系统提示、上下文压缩、会话状态、Todo 状态、工具执行封装等。`agent/conversation_loop.py` 承担核心对话循环：模型响应后，如果存在 `tool_calls`，则将 assistant 消息加入历史，执行工具，再继续下一轮；如果没有工具调用，则得到最终回答。

---

## 4. 调用任务生成与执行流程

### 4.1 即时任务：用户消息进入 AIAgent

Hermes 的即时任务通常来自 CLI 或网关中的用户输入。用户消息被放入消息列表，由 `AIAgent` 构建系统提示和工具 schema 后调用模型。

执行循环的核心特征：

1. 模型生成 assistant 响应；
2. 如果响应包含 `tool_calls`，说明模型把用户目标拆成了一个或多个工具调用；
3. Hermes 将 assistant 消息追加到上下文；
4. 执行工具调用并把工具结果作为 `role: tool` 消息追加；
5. 回到模型继续推理；
6. 直到模型不再调用工具，输出最终回答。

这是一种"模型驱动任务生成"模式：任务并不一定先落到文件或数据库，而是在模型响应中即时生成工具调用。

### 4.2 工具调用：注册表分发

`model_tools.py` 明确说明它是工具编排层：导入所有 `tools/` 模块完成发现，然后提供：

- `get_tool_definitions(...)`：生成模型可见的工具定义；
- `handle_function_call(...)`：执行某个工具调用；
- `TOOL_TO_TOOLSET_MAP`、`TOOLSET_REQUIREMENTS`：维护工具与工具集关系。

`tools/registry.py` 则提供注册和分发能力。每个工具模块通过注册表声明：

- 工具名；
- schema；
- handler；
- 所属 toolset；
- check function / requirement 等元数据。

这种方式的优势是工具能力天然可裁剪：同一 Agent 在不同场景中可只暴露 web/file/terminal/kanban/cron 等部分工具，降低提示词负担，也降低误调用风险。

### 4.3 工具执行：并发、护栏、结果回填

`agent/tool_executor.py` 将工具执行拆成两个路径：顺序执行和并发执行。并发路径的核心逻辑包括：

1. 解析每个 tool call 的 function name 和 JSON 参数；
2. 如果模型调用的是 tool search bridge，则先解析真实底层工具；
3. 做 scope gate，确保底层工具在当前 session 的授权范围内；
4. 触发 plugin pre-tool-call block；
5. 触发 tool guardrail；
6. 对文件写入、patch、破坏性 terminal 命令建立 checkpoint；
7. 使用 thread pool 并发执行多个工具；
8. 按原 tool call 顺序收集结果；
9. 将结果作为 tool message 回填给模型。

这说明 Hermes 的工具执行不是简单 `eval function(args)`，而是完整的执行管线。对 LDVH 的启发是：如果未来引入更多工具型 Skill 或自动执行能力，应把"工具授权范围、执行前阻断、执行后证据、结果回填"作为统一层，而不是分散在每个 Skill 内部。

---

## 5. 任务形态一：Todo 会话内计划

`tools/todo_tool.py` 提供轻量计划工具：

- `TodoStore` 是每个 `AIAgent` 一个实例；
- Todo item 只有 `id`、`content`、`status`；
- 状态包括 `pending`、`in_progress`、`completed`、`cancelled`；
- 写入模式支持整体替换或按 id merge；
- 压缩上下文后只注入 pending / in_progress 项，避免模型重做已完成任务。

Todo 的定位不是事实源，而是单会话内工作记忆。它解决的是"长对话中模型忘记当前步骤"的问题。

对 LDVH 的启发：LDVH 已有正式 Task YAML，语义更强、可跨会话、可审计；但仍可以保留轻量 Todo 作为执行期 scratchpad。二者边界应清晰：

| 维度 | Hermes Todo | LDVH Task |
|---|---|---|
| 生命周期 | 会话内 | 跨会话事实源 |
| 字段 | id/content/status | acceptance、verification、deliverables、blocked_by 等 |
| 审计 | 弱 | 强 |
| 适用 | 当前执行步骤 | 正式任务承诺 |

---

## 6. 任务形态二：Kanban 多 Agent 协作任务

`tools/kanban_tools.py` 是 Hermes 更接近"正式任务系统"的部分。源码说明它用于 worker + orchestrator agents，支持：

- `kanban_show`：读取任务完整状态、父子关系、评论、运行记录、事件；
- `kanban_list`：面向 orchestrator 列出任务摘要；
- `kanban_complete` / `kanban_block` / `kanban_heartbeat` / `kanban_comment`：worker 生命周期操作；
- `kanban_create` / `kanban_link` / `kanban_unblock`：编排任务和依赖。

Kanban 工具带有场景门控：

- worker 环境变量 `HERMES_KANBAN_TASK` 存在时，worker 只处理自己的生命周期；
- orchestrator profile 开启 kanban toolset 时，可列任务、创建任务、解除阻塞；
- 普通 `hermes chat` 默认看不到 Kanban 工具。

这点非常值得 LDVH 参考：**工具暴露范围应跟角色绑定**。LDVH 当前的 Task YAML 和 Skill 都在同一工作区上下文中运行，如果未来有"执行 agent / 审查 agent / 规划 agent"，应考虑将可写字段和可调用 Skill 按角色分层。

---

## 7. 任务形态三：Cron 自动化任务

`tools/cronjob_tools.py` 和 `cron/jobs.py` 实现定时任务。`create_job(...)` 的参数体现了 Hermes Cron 的任务模型：

- `prompt`：要执行的自包含指令；
- `schedule`：调度表达式；
- `name`：友好名称；
- `repeat`：运行次数；
- `deliver`：结果投递方式；
- `skill` / `skills`：执行前加载的技能；
- `model` / `provider` / `base_url`：模型运行配置；
- `script`：脚本输出作为上下文，或 no-agent 模式直接执行脚本；
- `context_from`：从其他 job 最近输出注入上下文；
- `enabled_toolsets`：限制 Agent 可用工具；
- `workdir`：指定工作目录，使 Agent 读取该目录上下文文件并以此作为工具工作目录；
- `profile`：指定 Hermes profile；
- `no_agent`：跳过 LLM，仅运行脚本。

Cron 工具还有严格的 prompt 扫描逻辑：对用户提供的 cron prompt 做注入、隐藏行为、读密钥、破坏性命令、外传密钥等检测；对 assembled skill prompt 使用较窄模式，避免安全文档本身误报。

对 LDVH 的启发：LDVH 如果支持周期性任务，不应只存 cron 表达式，还应存完整"执行封包"：prompt、技能、工作目录、工具权限、输出目标、上下文来源、安全扫描结果。

---

## 8. Skills、Memory 与上下文机制

### 8.1 Skills 渐进披露

`tools/skills_tool.py` 定义 Skills 目录结构：

- 每个 Skill 是一个目录；
- `SKILL.md` 是主说明；
- 可包含 references、templates、assets；
- `skills_list` 只列 metadata；
- `skill_view` 按需读取完整内容或引用文件。

它明确采用 progressive disclosure：先让模型看到名称和简短描述，只有需要时才加载完整说明，避免系统提示无限膨胀。

LDVH 的 Skill 已经有类似机制。Hermes 的补充启发是：Skill 需要 readiness / platform / env 检查，避免模型调用当前环境不可用的技能。

### 8.2 Memory 冻结快照

`tools/memory_tool.py` 定义持久记忆：

- `MEMORY.md`：agent 的环境事实、项目约定、工具经验；
- `USER.md`：用户偏好；
- 会话启动时加载为 frozen snapshot；
- 会话中写入磁盘但不改变当前系统提示，以保持 prefix cache 稳定；
- 记忆内容进入系统提示前做 prompt injection / exfiltration 扫描。

这对 LDVH 的 Memo/Profile 有参考价值：跨会话事实源进入提示词时应有"注入前过滤"和"快照一致性"机制，避免事实源中混入恶意指令或导致同一会话系统提示漂移。

---

## 9. Subagent 委派机制

`tools/delegate_tool.py` 实现子代理架构。源码顶部说明：

- 父 Agent 可以生成 child `AIAgent`；
- 子代理有隔离上下文；
- 子代理有自己的 task_id 和 terminal session；
- 子代理工具集受限制；
- 父上下文只看到委派调用和摘要结果，看不到子代理中间推理和工具调用。

安全限制包括：

- 默认禁止递归委派；
- 子代理不可使用 `clarify`，避免向用户交互；
- 子代理不可写共享 memory；
- 子代理不可使用 `send_message`；
- 子代理不可使用 `execute_code`；
- 危险命令默认 auto-deny，除非显式配置 auto-approve。

对 LDVH 的启发：独立 agent 验证 acceptance 或专业审查时，应采用"隔离上下文 + 限权工具 + 摘要回传"的模式。尤其是 ADR-0006 提出的 Task 评审机制，如果后续 accepted，可以借鉴 Hermes 的 delegate 工具限制：评审 agent 不应能修改事实源，只返回审查意见和证据。

---

## 10. 与 LDVH 当前机制的对比

| 维度 | Hermes Agent | LDVH 当前机制 | 可借鉴点 |
|---|---|---|---|
| 正式任务 | Kanban DB + worker 生命周期 | `ldvh-base/tasks/*.yaml` | 角色化工具权限、worker 生命周期事件 |
| 执行期计划 | TodoStore 会话内状态 | 当前对话 Todo + Task YAML | 保持 scratchpad 与事实源边界 |
| 自动化 | Cron Job 执行封包 | 尚未作为核心事实模型展开 | prompt + skill + workdir + toolsets + delivery |
| 工具体系 | registry + toolsets + check_fn | Skill + CLI 工具 | 建立统一工具授权与可用性检查层 |
| 子代理 | delegate_task 隔离上下文 | 独立 agent 验证较松散 | 限权评审 agent / 验证 agent |
| 记忆 | frozen snapshot + 注入扫描 | Intent/Memo/Profile 事实源 | 事实源注入提示词前做安全过滤 |
| 上下文 | context files + compression | 规范读取 + 会话摘要 | 将上下文注入层与执行层显式分开 |

---

## 11. 对 LDVH 的建议

### 11.1 为 Task 执行引入"工具权限面"概念

Hermes 的 toolset 机制说明：不同角色不应看到同一套工具。LDVH 可考虑在 Task 执行计划中增加非事实字段或规范约定：

- 规划阶段可读写 Task 草案；
- 执行阶段可修改目标文件；
- 验证 agent 只读目标文件和运行验证命令；
- review agent 只读事实源、diff 和产物，不直接修改；
- close 阶段才允许写 closure_evidence 和状态流转。

这能强化 ADR-0006 所指出的"专业知识视角评审"。

### 11.2 将自动化任务作为独立能力而非普通 Task 字段

Hermes Cron Job 包含 prompt、skill、workdir、context_from、enabled_toolsets、deliver 等执行封包。LDVH 若后续引入周期性工作，不宜只在 Task 中加 `cron` 字段，而应考虑单独 Automation/Cron 模型，或在 Task 中引用 Automation 对象。

### 11.3 让独立评审 agent 更像 Hermes delegate_task

LDVH 现有 independent agent 验证 acceptance 时，应该明确：

- 输入只包含 Task、产物、相关规范；
- 输出只包含审查摘要；
- 不允许修改事实源；
- 不允许直接关闭任务；
- 必须说明覆盖了哪些专业视角。

### 11.4 参考 Skills 渐进披露优化规范读取

Hermes Skills 的 list/view 两层加载可用于 LDVH specs：先通过索引识别相关规范，再按标题行范围读取，不把全部规范注入上下文。这与当前 LDVH 工作区规则一致，可进一步固化为工具层能力。

### 11.5 建立工具执行证据层

Hermes 工具执行管线记录了 tool call、结果、阻断、guardrail、checkpoint。LDVH 的 `closure_evidence` 当前是文本摘要，后续可考虑更结构化：

- 执行命令；
- 输出摘要；
- 产物路径；
- 审查 agent 输出；
- Human Gate 时间和选择；
- 关联 Change。

---

## 12. 风险与限制

1. 本调研基于下载到工作区的 `e375c33f7090c329e6a6a741e26fc9082b27d728` 源码快照，不代表后续版本。
2. 本次没有运行 Hermes Agent，只做静态源码调研，因此不评价实际 CLI 体验、模型兼容性或运行稳定性。
3. Hermes Agent 源码规模较大，本报告聚焦"调用任务生成与执行机制"，没有展开 UI、Gateway、消息平台、Honcho、ACP、MCP 等全部子系统。
4. Hermes 源码中有大量安全和兼容性注释，说明其设计经过多轮生产问题修正；LDVH 借鉴时应关注机制，不应直接复制实现。

---

## 13. 待补齐事项

1. 本文结论如何影响 Task 执行的"工具权限面"设计待行动模型规范稳定后确定；
2. 本文结论如何影响自动化任务模型设计待事实模型规范稳定后确定；
3. 本文结论如何影响独立评审 agent 机制待 ADR-0006 后续状态确定后跟进；
4. 本文结论如何影响 Skills 渐进披露和工具执行证据层待工具规范稳定后确定。
