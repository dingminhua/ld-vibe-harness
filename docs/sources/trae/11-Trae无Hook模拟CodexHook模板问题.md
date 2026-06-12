# Trae 无 Hook 模拟 Codex Hook 模板问题

> 创建日期：2026-06-10
> 来源：Trae 官方文档、OpenAI Codex 官方文档、OpenAI Codex GitHub 仓库文档、LDVH 既有 refs 调研
> 定位：外部资料引用和机制对照，不直接成为 LDVH 强制规则
> 官方地址：https://docs.trae.cn/ide/rules | https://docs.trae.cn/ide/skills | https://docs.trae.cn/ide/auto-run-and-security | https://developers.openai.com/codex/hooks | https://developers.openai.com/codex/config-advanced | https://github.com/openai/codex

---

## 1. 结论摘要

Trae 当前没有与 Codex lifecycle hooks 等价的用户可配置 Hook 机制。Trae 可用的相近能力是 Rules、Skills、Commands、自动运行 MCP、自动运行命令、AskUserQuestion/Human Gate 和外部脚本/CI，但这些机制都不是“工具调用生命周期拦截器”。因此，在 LDVH 中不能把 Trae 模板写成 Codex Hook 或 Claude Code Hook 的直接移植版本，而应写成“无 Hook 环境下的显式工作流模板”：用入口规则触发、用 Skill 或 Command 承接步骤、用 checklist 驱动、用 Human Gate 和校验命令收口。

Codex 当前已有 lifecycle hooks。Codex hooks 默认启用，可通过 `hooks.json` 或 `.codex/config.toml` 的 `[hooks]` 表配置，支持 `PreToolUse`、`PermissionRequest`、`PostToolUse`、`SessionStart`、`UserPromptSubmit`、`Stop`、`SubagentStart`、`SubagentStop`、`PreCompact`、`PostCompact` 等事件。Codex `PreToolUse` 可在部分工具调用前阻断或改写输入，`PermissionRequest` 可决定是否放行审批请求，`Stop` 可推动 agent 继续执行。这些能力在 Trae 中没有直接对应物。

“Trae 无 Hook 模拟 Codex Hook”模板的核心问题是：不要声称 Trae 能自动拦截每次工具调用；只能把 Hook 想完成的治理意图拆成若干可显式执行、可人工确认、可命令校验、可事实源回写的步骤。模板应明确标注“模拟范围”“不可模拟能力”“触发入口”“人工降级”和“校验收口”。

## 2. 调研依据

### 2.1 Trae 可用机制

Trae 官方文档显示，Trae 可通过 Rules 规范 AI 行为，包括全局规则和项目规则。项目规则支持 4 种生效方式：始终生效、指定文件生效、智能生效和手动触发生效，并通过 `alwaysApply`、`globs`、`description` 等字段控制。Trae 还支持在 `.trae/rules/` 下多层嵌套规则，至多支持 3 层嵌套；子目录下的 `.trae/rules/` 可在相关文件被读取或提及时生效。

Trae Skills 通过 `SKILL.md` 定义，采用按需加载机制。Skill 适合封装专业能力、SOP、模板、脚本和注意事项，但 Skill 本质是“任务执行说明书”，不是生命周期拦截器。Skill 可以让 AI 在相关任务中按流程执行，但不能保证在每次工具调用前后自动触发。

Trae Commands 是斜杠命令，用于封装常用 Prompt、规范输出格式和自动化常见流程。Commands 可结合 `#File`、`#Folder`、`#Rule`、`#Workspace` 等上下文工具使用，但命令需要用户或对话显式触发，不是工具调用级 Hook。

Trae 自动运行机制分为“自动运行 MCP”和“自动运行命令”。自动运行 MCP 启用后可自动运行已授权 MCP Server 工具；自动运行命令支持始终手动运行、白名单、黑名单和始终自动运行四种模式。该机制用于控制是否需要用户逐次批准命令或 MCP 工具，不提供 `PreToolUse`、`PostToolUse`、`Stop` 这类可编程 Hook 事件。

### 2.2 Codex Hook 能力

Codex 官方 Hooks 文档将 hooks 定义为 extensibility framework，可把用户脚本注入 agentic loop，用于日志、Prompt 扫描、记忆生成、回合停止后的校验、目录特定上下文定制等。

Codex hooks 默认启用，可通过以下位置配置：

1. `~/.codex/hooks.json`；
2. `~/.codex/config.toml`；
3. `<repo>/.codex/hooks.json`；
4. `<repo>/.codex/config.toml`。

Codex 支持从活动配置层旁边发现 `hooks.json` 或 `config.toml` 中的内联 `[hooks]` 表。项目本地 hooks 只在项目 `.codex/` 层被信任时加载；用户级 hooks 独立于项目 trust。非托管 command hook 在运行前需要用户审查并信任当前 hook 定义。多个匹配 hook 会运行，且同一事件的多个匹配 command hook 会并发启动。

Codex 当前 Hook 事件包括：

| 事件 | 典型用途 | matcher 过滤对象 |
|---|---|---|
| `SessionStart` | 会话启动或恢复时注入上下文 | `startup`、`resume`、`clear`、`compact` |
| `UserPromptSubmit` | Prompt 发送前检查或补充上下文 | 当前不使用 matcher |
| `PreToolUse` | 工具调用前检查、阻断或改写部分工具输入 | 工具名，如 `Bash`、`apply_patch`、MCP 工具名 |
| `PermissionRequest` | Codex 即将请求权限时放行或拒绝 | 工具名 |
| `PostToolUse` | 工具调用后审查输出或反馈 | 工具名 |
| `Stop` | 回合停止时决定是否继续 | 当前不使用 matcher |
| `SubagentStart` | 子智能体启动时补充上下文 | 子智能体类型 |
| `SubagentStop` | 子智能体停止时要求继续或收口 | 子智能体类型 |
| `PreCompact` | 上下文压缩前处理 | `manual`、`auto` |
| `PostCompact` | 上下文压缩后处理 | `manual`、`auto` |

其中 `PreToolUse` 可通过返回 JSON 阻断工具调用、补充模型可见上下文，或在 `permissionDecision: "allow"` 时用 `updatedInput` 改写支持的工具输入。Codex 文档也明确提示其仍是 guardrail 而非完整 enforcement boundary，因为并非所有 shell 调用、WebSearch 或非 shell/非 MCP 工具都被完整拦截。

`PermissionRequest` 在 Codex 准备请求审批时运行，可允许、拒绝或不决定并交回正常审批流程。多个匹配 hooks 返回决策时，任意 deny 优先于 allow。

`PostToolUse` 在工具产出后运行，不能撤销已经发生的副作用，但可以替换工具结果反馈给模型或停止正常处理。`Stop` 可通过 block/continuation 语义要求 Codex 再执行一轮，例如继续跑失败测试。

## 3. Trae 与 Codex Hook 能力差异

| 维度 | Trae 当前机制 | Codex lifecycle hooks | 对模板设计的影响 |
|---|---|---|---|
| 生命周期事件 | 无公开等价 Hook 事件 | 支持会话、Prompt、工具前、权限请求、工具后、停止、压缩、子智能体事件 | Trae 模板不能写成事件监听配置 |
| 工具调用前拦截 | 依赖审批、自动运行配置、AI 遵循规则和人工确认 | `PreToolUse` 可阻断或改写部分工具输入 | Trae 只能前置约束和人工 Gate，不能保证自动拦截 |
| 权限请求决策 | 由界面审批、自动运行模式和用户授权控制 | `PermissionRequest` 可由脚本 allow/deny | Trae 无法用脚本替代用户审批流 |
| 工具调用后审查 | 依赖 AI 主动检查、命令输出、测试和人工复核 | `PostToolUse` 可自动审查工具输出 | Trae 应把“工具后审查”写成每步后的显式检查项 |
| 回合结束继续 | 依赖 AI 遵循任务要求或用户继续要求 | `Stop` 可让 Codex 自动继续一轮 | Trae 应用 checklist 防止过早结束 |
| 配置位置 | `.trae/rules/`、`.trae/skills/`、命令管理、设置项 | `.codex/hooks.json`、`.codex/config.toml`、用户级配置、托管配置 | Trae 模板应输出 Rules/Skills/Commands/脚本建议，而非 `.codex/hooks.json` |
| 信任模型 | MCP 首次授权、命令自动运行白/黑名单、手动批准 | 项目 trust、hook 审查与信任、managed hooks | Trae 模板必须强调自动运行风险和 Human Gate |
| 强制性 | 主要依赖上下文遵循和平台审批边界 | 在支持事件内可执行脚本 guardrail | Trae 模拟属于“软约束 + 人工/命令闭环” |

## 4. 模板问题定义

“Trae 无 Hook 模拟 Codex Hook”模板问题，不是要在 Trae 中生成一份伪 `.codex/hooks.json`，而是要回答：当外部实践建议用 Codex Hook 或 Claude Code Hook 做自动化治理时，LDVH 在 Trae 环境中应该如何降级表达，避免把不存在的平台能力写成已落地机制。

模板要处理以下误区：

1. 把 Trae Rule 当成 `PreToolUse`：Rule 可以影响 AI 行为，但不能在每次工具调用前执行脚本或阻断工具。
2. 把 Trae Skill 当成 `PostToolUse`：Skill 可以指导 AI 执行检查，但不能自动监听工具结果。
3. 把 Trae Command 当成 `Stop`：Command 可封装流程，但不能在模型停止时自动追加继续提示。
4. 把自动运行命令当成权限 Hook：自动运行控制的是是否跳过人工确认，不是自定义审批决策脚本。
5. 把外部脚本当成平台 Hook：脚本只有在 AI 或用户显式运行时才生效，不能自动注入所有工具调用生命周期。

## 5. Codex Hook 到 Trae 的降级映射

| Codex Hook 意图 | Trae 可模拟方式 | 模拟强度 | 不可模拟部分 |
|---|---|---|---|
| `SessionStart` 加载项目上下文 | 工作区级薄入口、项目 Rule、AGENTS.md 导入、Skill 描述 | 中 | 不能保证每次会话按事件脚本动态生成上下文 |
| `UserPromptSubmit` 扫描 Prompt | Rule 要求先做输入澄清、AskUserQuestion、人为确认 | 低 | 不能在 Prompt 提交前自动阻断或改写 |
| `PreToolUse` 阻止危险命令 | Rule 写明危险命令需先确认、自动运行命令保持手动或白名单、必要时外部脚本检查 | 低到中 | 不能自动拦截所有工具调用，也不能返回 `updatedInput` |
| `PermissionRequest` 自动审批策略 | 关闭高风险自动运行、使用白名单/黑名单、Human Gate | 低 | 不能用自定义脚本替代审批决策 |
| `PostToolUse` 工具后校验 | Skill/Command/checklist 要求每步后读取输出、运行测试、记录证据 | 中 | 不能自动监听每次工具输出，也不能撤销副作用 |
| `Stop` 停止前验收 | 任务 checklist、最终响应前运行 lint/typecheck/test、Todo 状态检查 | 中 | 不能在模型停止事件中自动追加继续任务 |
| `SubagentStart/Stop` 子智能体治理 | 主流程明确子任务输入输出契约、要求汇总报告 | 低到中 | 不能用事件脚本自动包裹子智能体生命周期 |
| `PreCompact/PostCompact` 压缩前后处理 | 显式要求长任务阶段性总结、把稳定事实写回 Git 文件 | 低 | 不能监听上下文压缩事件 |

## 6. 推荐模板骨架

Trae 模板应使用“目的 + 可用机制 + 显式步骤 + 人工 Gate + 校验收口”的结构，而不是 Hook 配置结构。

```markdown
# Trae 无 Hook 场景下的 {治理目标} 模板

> 定位：在 Trae 无生命周期 Hook 的环境中，模拟 {Codex Hook 事件/治理意图} 的显式工作流模板
> 适用范围：{项目/目录/任务类型}
> 不承诺能力：本模板不提供工具调用级自动拦截、自动改写、自动审批或停止事件续跑

## 1. 目标

{说明要解决的治理问题，例如危险命令前确认、修改后自动验收、任务停止前检查。}

## 2. Trae 可用机制

- Rules：{哪些规则前置约束 AI 行为}
- Skills：{哪个 Skill 承接 SOP}
- Commands：{哪个命令封装重复流程}
- 自动运行设置：{是否保持手动、白名单或黑名单}
- Human Gate：{哪些情况必须人工确认}
- 校验命令：{lint/typecheck/test/build 或项目校验脚本}

## 3. 显式执行流程

1. 开始前读取 {入口/规则/文档}。
2. 执行前检查 {风险、路径、命令、范围}。
3. 高风险情况暂停并请求 Human Gate。
4. 执行修改或命令。
5. 读取工具输出并判断是否失败。
6. 运行必要校验。
7. 把稳定结论写回 {事实源/任务/报告}。
8. 最终响应前确认 checklist 全部完成。

## 4. 不可模拟能力

- 不能像 Codex `PreToolUse` 一样自动拦截每次工具调用。
- 不能像 Codex `PermissionRequest` 一样用脚本替代审批决策。
- 不能像 Codex `Stop` 一样在停止事件自动追加继续任务。
- 不能保证外部脚本在 AI 未显式调用时自动执行。

## 5. 检查清单

- [ ] 任务范围已确认。
- [ ] 高风险操作已触发人工确认。
- [ ] 修改后已运行校验命令。
- [ ] 失败输出已处理或记录为阻塞。
- [ ] 稳定结论已回写到权威事实源。
```

## 7. LDVH 推荐写法

在 LDVH 中引用该类模板时，建议使用以下写法：

1. 标题使用“Trae 无 Hook 场景下的显式流程模板”，避免写成“Trae Hook 配置模板”。
2. 正文第一节必须说明“Trae 当前无 Codex lifecycle hooks 等价能力”。
3. 对每个 Hook 意图给出 Trae 降级路径，同时列出不可模拟能力。
4. 涉及安全、审批、自动执行时，优先使用 Human Gate 和 Trae 自动运行安全设置，不建议开启“始终自动运行”。
5. 涉及质量保障时，优先用项目真实 lint/typecheck/test/build 命令收口。
6. 涉及长期稳定事实时，必须回写到 LDVH 正式事实源，而不是只保存在会话或模板中。
7. 模板输出不得暗示 Trae 能自动监听 `PreToolUse`、`PostToolUse`、`Stop` 等事件。

## 8. 示例：模拟 Codex Stop Hook 的 Trae 验收模板

Codex `Stop` Hook 可在回合停止时让 Codex 继续执行，例如“测试失败时再跑一轮修复”。Trae 无法监听停止事件，因此只能把 Stop Hook 意图改写为最终响应前 checklist。

```markdown
# Trae 最终响应前验收模板

## 1. 适用场景

当任务涉及代码修改、文档规范修改、事实源回写或高影响判断时使用。

## 2. 执行要求

1. 最终响应前检查任务列表是否全部完成。
2. 若存在代码修改，运行项目约定的 lint、typecheck、test 或 build。
3. 若校验失败，不得宣称完成；应继续修复或记录阻塞。
4. 若涉及 LDVH 事实源，确认稳定结论已写回 Git 文件。
5. 若遇到 Human Gate 条件，暂停并请求确认。

## 3. 不可模拟声明

本模板不是 Trae Stop Hook。它不会在模型停止事件自动运行，只能依赖 AI 在最终响应前显式执行。
```

## 9. 示例：模拟 Codex PreToolUse Hook 的 Trae 危险命令模板

Codex `PreToolUse` 可在工具执行前阻断危险命令。Trae 无同等 Hook，因此应使用 Rule、自动运行设置和人工确认组合。

```markdown
# Trae 危险命令前置确认模板

## 1. 风险命令范围

以下命令或等价操作必须先请求 Human Gate：

- 删除、移动或覆盖大量文件；
- 修改 Git 历史、强推、清理工作区；
- 运行未知来源脚本；
- 修改密钥、凭证、生产配置或权限文件；
- 开启始终自动运行命令。

## 2. 执行流程

1. 说明拟执行命令、工作目录、影响范围和回滚方式。
2. 请求 Human 确认。
3. 未确认前不得执行。
4. 执行后读取输出并判断副作用。
5. 若输出异常，停止后续高风险操作并报告。

## 3. 不可模拟声明

本模板不能像 Codex `PreToolUse` 一样自动拦截每次 Bash 或 MCP 工具调用。若 AI 未遵守模板，平台不会自动执行此检查。
```

## 10. 安全建议

1. Trae 中不建议为模拟 Hook 而开启“始终自动运行”。该模式会跳过所有安全检查，风险高于收益。
2. 对命令自动运行，优先使用“始终手动运行”或严格白名单；白名单只能作为基础防护，不能替代人工审查。
3. 对 MCP 自动运行，只有在 MCP Server 来源可信、工具行为明确且已完成首次授权后才考虑启用。
4. 对危险命令、外部脚本和批量写入，使用 Human Gate，而不是依赖 AI 自我约束。
5. 对质量保障，使用项目内真实校验命令，不用“看起来没问题”替代测试。
6. 对事实源回写，使用 Git 可追踪文件，不把聊天上下文、工具输出或 refs 文档当成最终事实。

## 11. 待进一步调研

1. Trae 后续是否会提供类似 lifecycle hooks、任务后置动作、命令前置策略脚本或工具调用事件订阅能力。
2. Trae 自动运行命令白名单/黑名单的匹配细节、边界和绕过风险是否有更细官方说明。
3. Trae Commands 是否可与项目级配置文件形成更稳定的可版本化承载方式。
4. Codex hooks 在 unified exec、WebSearch、非 shell/非 MCP 工具拦截方面的覆盖范围是否继续扩大。
5. LDVH 是否需要把“无 Hook 降级模板”吸收到正式平台适配清单或工作流程规范中。
