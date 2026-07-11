---
id: study-0008
type: study
title: AI 能力资产行业最佳实践调研
status: active
created: '2026-06-20T10:25:42+08:00'
updated: '2026-06-24T03:20:00+08:00'
summary: |
  本报告补齐并加固 workcase-0080 中此前缺失的行业最佳实践输入。调研采用多视角起草与主控合并：Codex 专业视角、Claude / Anthropic 视角、OpenAI Agents / guardrails / evals 视角、Hook / DevOps / 提交门禁视角。结论被整理为来源对照矩阵、最佳实践矩阵、反模式清单和 LDVH 吸收规则，用于支撑 04.02 对 Rules、Skill、Agent、Hook 固定能力资产的准入、审查和关闭判断。
user_intent: 用户指出 workcase-0080 中“最佳实践”目前只是 LDVH 内部规则，缺少行业最佳实践内容，要求先补齐 spark / WorkCase 相关规范基础。
conclusion: |
  行业实践并不支持把 Rules、Skill、Agent、Hook 写成厚重的第二规范。更稳的治理模型是：Rules / AGENTS / CLAUDE.md 等长期入口保持薄而可恢复；Skill 承接按需加载的可复用流程；Agent / subagent 承接隔离上下文、受限工具和主控回收；Hook 只承接生命周期触发、确定性快速反馈和证据采集；CI、server-side gate、guardrails、HITL、tracing 和 evals 作为运行期保障和质量证据，不反向成为规范事实源。LDVH 04.02 应吸收这些稳定规则，外部 URL 只保留在 Study 中作为调研依据。
urls:
- ref: https://code.claude.com/docs/en/best-practices
  title: Claude Code Best Practices
  summary: 用于对照上下文管理、先探索再计划再实现、可验证检查、hooks、skills、subagents 和权限配置等实践。
- ref: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
  title: Skill authoring best practices
  summary: 用于对照 Skill 应保持简洁、按需加载、描述清晰、渐进披露、真实场景测试和可验证中间产物。
- ref: https://code.claude.com/docs/en/skills
  title: Claude Code Skills
  summary: 用于说明 Skills 适合承接反复粘贴的流程、清单或多步程序，并通过元信息和按需加载降低上下文负担。
- ref: https://code.claude.com/docs/en/sub-agents
  title: Claude Code Subagents
  summary: 用于说明 subagents 的上下文隔离、工具权限限制、描述驱动委派、并行研究和主对话回收边界。
- ref: https://code.claude.com/docs/en/hooks-guide
  title: Claude Code Hooks Guide
  summary: 用于说明 hooks 适合确定性自动化和项目规则执行，判断型 hooks 应区别于命令型确定性检查。
- ref: https://code.claude.com/docs/en/hooks
  title: Claude Code Hooks Reference
  summary: 用于说明 agent hooks 仍带实验性，生产工作流应优先命令 hooks，并区分阻塞与异步执行。
- ref: https://developers.openai.com/api/docs/guides/agents
  title: OpenAI Agents SDK Guide
  summary: 用于对照应用拥有编排、工具执行、审批、状态和可观测性时的 agent SDK 分层。
- ref: https://openai.github.io/openai-agents-python/guardrails/
  title: OpenAI Agents SDK Guardrails
  summary: 用于对照输入、输出和工具 guardrails 的触发边界、tripwire、阻塞执行和副作用控制。
- ref: https://openai.github.io/openai-agents-python/human_in_the_loop/
  title: OpenAI Agents SDK Human-in-the-loop
  summary: 用于对照敏感工具调用的暂停、审批、拒绝、状态序列化和恢复机制。
- ref: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
  title: MCP Tools Specification
  summary: 用于对照工具暴露应具备元信息、schema、变更通知、安全提示和 Human 可拒绝调用的交互边界。
- ref: https://git-scm.com/docs/githooks
  title: Git githooks Documentation
  summary: 用于对照 Git hook 的触发时机、参数、退出码、可绕过性和 commit-msg hook 的标准行为。
- ref: https://developers.openai.com/codex/guides/agents-md
  title: Codex AGENTS.md Guide
  summary: 用于说明 Codex 持久项目指导的加载顺序、薄入口、嵌套覆盖和验证方式。
- ref: https://developers.openai.com/codex/skills
  title: Codex Agent Skills
  summary: 用于说明 Codex Skill 的渐进披露、触发描述、目录层级和插件分发边界。
- ref: https://developers.openai.com/codex/subagents
  title: Codex Subagents
  summary: 用于说明 Codex subagents 的显式触发、上下文隔离、权限继承、并行成本和 custom agent schema。
- ref: https://developers.openai.com/codex/hooks
  title: Codex Hooks
  summary: 用于说明 Codex lifecycle hooks 的事件、matcher、并发、信任、timeout 和压缩恢复辅助边界。
- ref: https://developers.openai.com/codex/rules
  title: Codex Rules
  summary: 用于消除 LDVH Rules 与 Codex `.rules` 命令执行策略之间的同名歧义。
- ref: https://pre-commit.com/
  title: pre-commit
  summary: 用于对照多语言 Git hook 管理、配置版本化、stage 选择、精细跳过和 CI 复跑实践。
- ref: https://typicode.github.io/husky/
  title: Husky
  summary: 用于对照 Node 项目 Git hook 管理、`core.hooksPath`、安装脚本、POSIX shell、禁用和 opt-in/opt-out 边界。
- ref: https://github.com/lint-staged/lint-staged
  title: lint-staged
  summary: 用于对照 staged-file 门禁、轻量格式化 / lint、Git 操作备份和不适合全项目检查的边界。
- ref: https://commitlint.js.org/guides/local-setup.html
  title: commitlint local setup
  summary: 用于对照本地 commit-msg 校验的配置和可绕过边界。
- ref: https://commitlint.js.org/guides/ci-setup.html
  title: commitlint CI setup
  summary: 用于对照提交消息在 CI 中检查 commit range 的兜底实践。
- ref: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
  title: GitHub protected branches
  summary: 用于对照 required status checks、required reviews 和合并门禁边界。
- ref: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks
  title: GitHub status checks
  summary: 用于对照 CI/status check 如何成为受保护分支的合并条件。
- ref: https://docs.gitlab.com/administration/server_hooks/
  title: GitLab server hooks
  summary: 用于对照 server-side hook 作为 push 门禁的确定性和部署边界。
input_refs:
- spark-0018
related_sparks:
- spark-0018
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
- history/specs-v1/04.02-LDVH能力资产与保障机制规范.md
- history/specs-v1/10-Git提交规范.md
archive_reason: null
---

# AI 能力资产行业最佳实践调研

## 研究问题

本报告回答：

1. 外部 AI 工程生态中，类似 Rules、Skill、Agent、Hook 的能力资产通常如何设计；
2. 哪些实践可以吸收到 LDVH 固定能力资产登记制；
3. 这些实践对 `workcase-0080` 和 `history/specs-v1/04.02-LDVH能力资产与保障机制规范.md` 的关闭条件有什么影响。

## 输入与边界

本次调研范围限定为公开官方或准官方资料，访问时间为 2026-06-20：

- OpenAI Codex：AGENTS.md、Agent Skills、Subagents、Hooks、Rules、权限 / 沙箱 / 插件和最佳实践；
- Anthropic / Claude Code：best practices、Skills、subagents、hooks guide、hooks reference；
- Anthropic Claude API：Skill authoring best practices；
- OpenAI：Agents SDK guide、Tools、Handoffs、Guardrails、Human-in-the-loop、Tracing、Agent evals；
- Model Context Protocol：Tools specification；
- DevOps / 提交门禁：Git githooks、pre-commit、Husky、lint-staged、commitlint、GitHub protected branches / status checks、GitLab server hooks。

本报告不把外部资料原文复制为 LDVH 规范。外部资料只用于提炼可复用设计原则；正式约束应吸收到 `history/specs-v1/04.02-LDVH能力资产与保障机制规范.md`，并按 LDVH 自身术语和事实源边界表达。

本报告的生成方式是多视角起草与主控合并：Codex 专业视角、Claude / Anthropic 视角、OpenAI Agents 视角和 Hook / DevOps 视角分别提出草案，主控再去重、归类并压缩为 LDVH 可吸收的稳定结论。子 Agent 输出是过程输入，不直接成为最终事实；本 Study 才是保留后的报告事实源。

## 关键发现

### 生态映射矩阵

| 外部生态条目 | 对应 LDVH 层 | 可吸收结论 | 不吸收为顶层资产的理由 |
|---|---|---|---|
| Codex `AGENTS.md`、Claude `CLAUDE.md` / rules | Rules / 环境薄入口 | 长期入口应保持薄引用、入口路由、STOP 点、验证命令和恢复提示；不得复制完整 specs | 入口文件是 AI-facing 加载层，不是最终事实源 |
| Codex `.rules`、权限策略、sandbox / approval / permission profiles | 04.03 环境适配 / 运行约束 | 运行权限、命令许可、网络和文件访问需要单独治理、测试和 Human Gate | 它们控制工具执行，不承载 LDVH 正式规则正文 |
| Codex / Claude / OpenAI Skills | Skill | Skill 承接按需加载的可复用流程、清晰触发描述、输入输出、验证入口和失败处理 | Skill 不新增规范规则，不替代 specs |
| Codex / Claude subagents、OpenAI Agents / handoffs / agent-as-tool | Agent | Agent 承接隔离上下文、专项审查、受限工具、主控回收和证据摘要 | Agent 输出不能直接成为事实源或关闭结论 |
| Codex / Claude hooks、Git hooks、pre-commit、Husky | Hook / 环境适配 | Hook 承接生命周期触发、确定性快速反馈、日志和阻断；必须声明事件、参数、退出码、timeout、信任和可绕过性 | Hook 通过不等于检查通过，且本地 Hook 常可被绕过 |
| lint-staged、commitlint、CI status checks、server-side hooks | Code / Hook / CI 门禁 | 同一规则应由 specs 定义、Code 实现、本地 Hook 快速反馈、CI 或 server-side gate 兜底 | 这些是运行门禁组合，不是单一文本资产 |
| MCP tools、OpenAI tools、hosted tools | 工具能力 / 运行期构件 | 工具必须有名称、schema、用途、风险、审批和可观测输出 | 工具调用结果不反向成为规范事实 |
| Guardrails、HITL、tracing、evals | 质量保障 / 证据 | Guardrails 放在正确边界；敏感动作可暂停审批并恢复；trace/eval 支撑回归评估 | 它们是运行证据和质量门禁，不是新的 LDVH 顶层文本资产 |
| Plugins / marketplace 分发 | 部署 / 分发层 | Plugin 可以打包 Skills、Agents、Hooks、MCP 和 app 映射；安装状态、启用状态和授权状态要环境化记录 | Plugin 是分发单元，不是权威事实源 |
| Memory / compact / resume / chat summary | 运行期上下文 | 恢复后重读入口；稳定结论必须回写 Git 文件事实源 | 摘要、记忆和压缩结果会丢细节，不可替代事实源 |

### 最佳实践矩阵

| 实践 | 理由 | 可检查验收标准 | LDVH 吸收规则 | 反模式 |
|---|---|---|---|---|
| 常驻入口薄化 | Codex / Claude 都强调上下文窗口需要治理，入口过厚会稀释关键约束 | 入口只放高频、全局、移除后会犯错的规则；不复制 specs、字段契约或长期状态 | Rules 资产只承载入口路由、事实源边界、STOP 点和恢复提示 | 把 04.02、10 号规范或工作模型字段整段复制进入口 |
| 同名术语分流 | Codex `.rules` 是命令许可策略，LDVH `rules/` 是 AI-facing 文本资产 | 文档明确“LDVH Rules ≠ Codex .rules”；命令许可归 04.03 | 04.02 保留 Rules 文本资产边界，04.03 承接环境权限配置 | 把命令 allowlist 当成 LDVH 规范入口 |
| Skill 渐进披露 | Codex / Claude Skills 都依赖名称、描述和按需加载，描述决定发现 | Skill 有稳定名称、具体 description、输入输出、失败处理、验证步骤；长参考拆支持文件 | Skill 资产承接可复用流程，不复制规范正文 | Skill 名称泛化、description 空泛，或把 Skill 当自动 Agent 调度器 |
| 风险越高，自由度越低 | 高风险流程需要确定性命令、脚本、审批和失败处理 | 提交、删除、发布、迁移、长期配置等操作有固定命令、审批点、拒绝路径和回滚说明 | 高风险 Skill / Hook 应优先脚本化和低自由度化 | 只写“请谨慎执行” |
| Agent 输出回主控 | Codex / Claude subagents 解决上下文污染，OpenAI handoff / agent-as-tool 区分最终答复归属 | Agent 声明角色、工具、是否可写、输出格式、主控复核和 Human Gate；默认不直接写事实源 | Agent 资产必须有 `handoff` / `as_tool` / `subagent_review` 式所有权边界 | 子 Agent 直接关闭 WorkCase、直接写事实源或无限分派 |
| 工具权限最小化 | Agents SDK、Codex subagents、Claude subagents 都支持或强调工具和权限边界 | 资产声明 allowed tools、风险等级、审批条件、MCP / shell / network 边界 | Agent / Skill / Hook 元信息必须暴露工具权限和审批要求 | 给所有 Agent 全量 shell、Git、网络和 MCP 权限 |
| Guardrails 放在动作边界 | OpenAI 区分 input、output、tool guardrails；工具 guardrails 才覆盖每次工具调用 | 资产声明 guardrail 类型、触发点、tripwire、阻塞或并行、误报处理 | 不能只靠入口文字自律，能机械检查的应放到 Code / Hook / tool boundary | 只在 Rules 写“不要越权” |
| HITL 可恢复审批 | OpenAI HITL 将敏感工具调用暂停、批准 / 拒绝并恢复状态 | Human Gate 记录 action、参数、风险、批准 / 拒绝、恢复状态或后续分流 | 高影响动作需要结构化审批对象，不只是一句“已确认” | Human 只批准目标，Agent 后续自由扩权 |
| Hook 只做快速反馈和确定性门禁 | Codex / Claude hooks 是生命周期触发；Git hooks 有明确事件、参数和退出码；本地 Hook 可绕过 | Hook 声明 event、matcher、inputs、command、timeout、exit code、trust、bypass、output | Hook 触发不等于通过；Hook 不能替代 Code、CI、Human Gate 或事实源 | 把 Hook 输出写成最终事实，或用判断型 Hook 放行关键门禁 |
| 本地 Hook 必须有 CI / server-side 兜底 | Git / Husky / commitlint 体系承认本地 Hook 可被绕过；GitHub required checks 才能作为合并门禁 | 本地门禁有等价 CI command 或 server-side gate；跳过本地 Hook 需证据和解释 | `commit-msg` Hook 只能做本地前置，CI / Code validator 承接可重复检查 | 只要求开发者“记得装 hook” |
| 复用同一 canonical command | 本地、CI、server-side 分叉实现会漂移 | Hook、CI 和手动命令调用同一 validator 或 wrapper | 提交规范类门禁回指 `specs/10` 和 `code/commit_validate.py`，不得复制正则 | 本地 shell 一套正则，CI 另一套正则 |
| Trace / eval 形成质量证据 | OpenAI 建议先用 traces 调试，再用 evals 固化回归判断 | 高风险 Agent / Skill / Hook 试点至少有代表性执行证据、失败样例、临时核对记录或 Human Gate 记录 | active 固定能力资产前必须有验证证据，不能只靠一次演示 | “跑过一次看起来可以”就登记 active |
| 分发层不反向成为事实源 | Codex / Claude plugins 都是打包和分发层 | 插件有 manifest、版本、依赖、启停说明；安装 / 授权状态归环境事实 | Plugin 可以包装稳定资产，但不改变权威路径和字段契约 | 把插件安装状态当成 LDVH 全局支持状态 |
| compact / memory 非事实源 | 压缩、记忆和聊天摘要会丢细节 | 恢复后重读入口；稳定结论回写 specs、WorkCase、Spark、ADR、Study 或 Git commit records | PreCompact / PostCompact 只做恢复辅助，不做最终证据 | 把 compact 摘要当 Human Gate 或关闭验收 |

### 资产类型准入清单

| 资产类型 | 准入检查 | 最低证据 |
|---|---|---|
| Rules | 是否薄入口；是否说明事实源边界；是否包含 STOP 点、恢复后重读、交还规则；是否避免同名环境规则歧义 | 入口文件元信息、来源 specs、AI 回读核对、文件事实源核对或 Code 检查 |
| Skill | name / description 是否具体；是否说明触发和不触发条件；是否按需加载；是否有输入输出、失败处理、验证步骤；是否不新增规范规则 | `SKILL.md`、示例任务或触发测试、验证命令或 Human 审查记录 |
| Agent | 是否有角色边界、工具权限、上下文输入、输出格式、写入权限、主控回收、Human Gate 和并行写入限制 | Agent 元信息、主控合并记录、代表性审查 / trace / 临时核对证据 |
| Hook | 是否声明事件、matcher / 参数、命令、timeout、退出码、信任、可绕过性、CI / server-side 兜底和日志位置 | Hook 文件 / 配置、canonical command、失败样例、CI 或手工复跑证据 |
| 运行期保障构件 | tools / MCP / guardrails / HITL / tracing / evals 是否作为字段、证据或环境配置进入治理，而不是升级为顶层文本资产 | schema、审批记录、trace / eval 报告、Code / Web 展示或 04.03 适配记录 |

### 关键反模式

1. 把外部资料、Study、工具输出或子 Agent 草稿直接升级成规范正文；
2. 把 LDVH Rules 与 Codex `.rules`、Claude path rules、环境配置等同名机制混用；
3. 把 specs 正文复制进 AGENTS、CLAUDE.md、Rules 或 Skill，制造第二事实源；
4. Skill 描述泛化、触发条件不清，导致隐式调用误选或漏选；
5. Agent 继承所有工具、直接写事实源、直接关闭工作对象或无限再分派；
6. Hook 未声明事件、参数、退出码、timeout、信任来源和可绕过性；
7. 把本地 Hook 通过当成 CI、server-side gate 或 Human Gate 通过；
8. 本地 Hook、CI 和 server-side 各自维护一套正则或规则；
9. 自动格式化或 lint-staged 悄悄修改 specs / `ldvh-base` 事实源；
10. 把插件安装、MCP 授权、memory、compact 摘要或一次 trace 写成长期事实源。

## 建议

1. `workcase-0080` 初次进入 `review_needed` 时不应关闭，因为此前“行业实践”只作为口头审查维度存在，没有形成外部调研事实源；本 Study 形成后，该缺口可以作为已补齐项重新提交关闭审查。
2. `specs/04.02` 的 §2.2 已明确行业实践来源被提炼为 LDVH 规则，并补充上下文经济、渐进披露、触发描述、权限审批、可观测证据、确定性优先和 Hook 可绕过性等规则。
3. 后续设计 `ldvh-git-commit` Skill 和 `commit-msg` Hook 时，应直接消费本 Study 的结论：
   - Skill 承接可复用流程和验证入口；
   - Hook 只承接确定性门禁；
   - 两者都不替代 `history/specs-v1/10-Git提交规范.md`、`commit_validate.py` 或 Git 提交事实源。
4. 外部资料不进入 specs 正文作为裸 URL；Study 的 `urls` 字段保留调研依据，specs 只保留吸收后的稳定规则。

## 后续分流

- `workcase-0080`：已新增行业实践调研吸收项，并可在补齐后重新进入关闭审查。
- `history/specs-v1/04.02-LDVH能力资产与保障机制规范.md`：已吸收本报告的稳定规则。
- `workcase-0074`：后续实现 `ldvh-git-commit` Skill 和 `commit-msg` Hook 时，引用本 Study 作为设计输入之一。
- `spark-0018`：无需复制本报告正文，只需继续保留多 WorkCase 分流关系。
