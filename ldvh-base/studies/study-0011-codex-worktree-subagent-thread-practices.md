---
id: study-0011
type: study
title: Codex 工作树、子 Agent 与新建对话并行实践调研
status: active
created: '2026-06-25T03:31:32+08:00'
updated: '2026-06-25T03:31:32+08:00'
summary: |
  Codex App 的 Worktree 适合承载会写文件、需要独立验证、可能产生 Git 提交或需要长期回收的并行任务；同目录新线程适合轻量咨询、同一工作区下的只读复核和需要延续现场环境的短任务；子 Agent 适合读多写少、边界清晰、可并行且会污染主线程上下文的调查、审查、测试日志分析和局部复核。LDVH 应把这三者吸收为行动编排的调度层：主线程保留事实源边界、任务卡、Human Gate 和合并顺序，worktree 线程承接可提交闭环，子 Agent 输出只作为过程材料交还主控。
user_intent: |
  用户要求独立线程研究 LDVH 如何利用 Codex 工作树、新建对话、线程间委派、子 Agent，以及 `agents.max_depth = 2` 后可能支持的一层嵌套子 Agent，并形成可追溯 Study。
conclusion: |
  可直接进入后续 WorkCase 的内容包括：建立 LDVH 并行任务卡模板、工作树线程交还格式、子 Agent 输出摘要格式、合并前验证清单和 Spark/Study/WorkCase 分流规则。需要 ADR 的内容包括：是否正式允许子 Agent 再 spawn 一层 child、是否允许执行型子 Agent 写入文件、主控线程能否把合并顺序和冲突处理作为单一权威调度。仅作为实践建议的内容包括：优先把 read-heavy 任务交给子 Agent、把 write-heavy 任务放入独立 worktree、每个 worktree 使用一个主承载对象和一个提交闭环。
urls:
  - ref: https://developers.openai.com/codex/app/worktrees
    title: Codex app Worktrees
    summary: 用于确认 Codex App worktree 的定位、Local/Worktree/Handoff 差异、detached HEAD、分支限制、`.worktreeinclude` 和清理机制。
  - ref: https://developers.openai.com/codex/app/features
    title: Codex app features
    summary: 用于确认 Codex App 支持 Local、Worktree、Cloud 模式、并行项目、内置 Git 工具、线程和工作树能力。
  - ref: https://developers.openai.com/codex/app/commands
    title: Codex app commands
    summary: 用于确认新建线程快捷键、深链接能力和线程导航能力。
  - ref: https://developers.openai.com/codex/subagents
    title: Codex Subagents
    summary: 用于确认子 Agent 的可用性、显式触发、沙箱继承、内置 agent、自定义 agent、`agents.max_threads` 和 `agents.max_depth` 语义。
  - ref: https://developers.openai.com/codex/concepts/subagents
    title: Codex Subagent concepts
    summary: 用于确认子 Agent 用于降低 context pollution / context rot、并行探索、测试、日志分析和摘要回收的官方定位。
  - ref: https://developers.openai.com/codex/learn/best-practices
    title: Codex best practices
    summary: 用于确认 Codex 任务提示应包含 Goal、Context、Constraints、Done when，以及用 AGENTS.md、测试、review 和配置提升可靠性的实践。
  - ref: https://git-scm.com/docs/git-worktree
    title: Git worktree documentation
    summary: 用于确认 Git worktree 的底层语义：同一仓库支持多个工作树、可并行 checkout、linked worktree 与主工作树共享仓库元数据。
  - ref: https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests
    title: GitHub About pull requests
    summary: 用于确认 PR 作为讨论、review、merge 变更的协作机制，以及 draft PR 和临时 PR refs 的实践边界。
  - ref: https://docs.github.com/articles/about-status-checks
    title: GitHub About status checks
    summary: 用于确认状态检查基于 CI 等外部过程，并显示在提交或 PR 上，支撑 LDVH 合并前验证命令要求。
  - ref: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts
    title: GitHub Addressing merge conflicts
    summary: 用于确认合并冲突来自竞争提交，PR 合并前必须处理冲突。
  - ref: https://google.github.io/eng-practices/review/reviewer/standard.html
    title: "Google Engineering Practices: The Standard of Code Review"
    summary: 用于支持代码审查应关注整体代码健康、所有权和可维护性的通用工程实践推论。
  - ref: https://developers.openai.com/api/docs/guides/agents/orchestration
    title: OpenAI Agents SDK orchestration and handoffs
    summary: 用于支持 manager-style workflow 中主 Agent 保持最终回答责任、专家 Agent 作为工具提供结果的通用多 Agent 编排推论。
  - ref: https://openai.github.io/openai-agents-python/tracing/
    title: OpenAI Agents SDK tracing
    summary: 用于支持多 Agent 工作流需要 tracing / 事件记录以便调试、可视化和监控的推论。
  - ref: https://www.anthropic.com/engineering/multi-agent-research-system
    title: Anthropic multi-agent research system
    summary: 用于补充多 Agent 系统在协调、评估和可靠性方面会引入新挑战的外部一手工程经验。
input_refs:
  - spark-0027
  - rules/LDVH-WORKSPACE-ENTRY.md
  - rules/LDVH-MAINTAINER-ENTRY.md
  - specs/03-行动编排规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
  - specs/07-事实源边界与Git追溯规范.md
  - ldvh-base/studies/study-0002-codex-subagent-role-design.md
related_sparks:
  - spark-0027
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
  - rules/LDVH-WORKSPACE-ENTRY.md
  - rules/LDVH-MAINTAINER-ENTRY.md
  - specs/03-行动编排规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
  - specs/07-事实源边界与Git追溯规范.md
  - ldvh-base/studies/study-0002-codex-subagent-role-design.md
archive_reason: null
---

# Codex 工作树、子 Agent 与新建对话并行实践调研

## 研究问题

本报告回答 spark-0027 提出的并行协作问题：LDVH 如何系统性利用 Codex App / Codex CLI 已观察到的工作树、新建对话、线程间委派、子 Agent，以及一层嵌套子 Agent 能力，避免单一长上下文混乱，同时留下可追溯的主控与执行线程关系。

具体研究问题包括：

1. Codex worktree、新建对话和子 Agent 分别适合承担哪些职责；
2. 什么时候用同目录线程，什么时候用 worktree，什么时候用子 Agent；
3. `agents.max_depth = 2` 允许子 Agent 再调一层 child 时，LDVH 应设置哪些边界、风险控制和写入约束；
4. 多 worktree 并行时，主控线程如何维护任务卡、事实源边界、提交拆分、验证命令、合并顺序和冲突处理；
5. 这些实践应如何吸收为 LDVH 的行动编排、WorkCase、Study、Spark、ADR 或 Rules 入口实践；
6. 哪些建议可以直接进入 WorkCase，哪些需要 ADR，哪些只是实践建议。

## 输入与边界

本报告输入分为三类。

第一类是 LDVH 内部权威原文：`rules/LDVH-WORKSPACE-ENTRY.md`、`rules/LDVH-MAINTAINER-ENTRY.md`、`specs/03-行动编排规范.md`、`specs/20-Spark-火花.md`、`specs/21-WorkCase-工作项.md`、`specs/24-Study-研究报告.md`、`specs/07-事实源边界与Git追溯规范.md`、`spark-0027` 和既有 `study-0002`。

第二类是 OpenAI / Codex 官方资料：Codex App worktree、Codex App features / commands、Codex subagents、subagent concepts 和 Codex best practices。这些资料用于确认 Codex 产品层事实。

第三类是外部通用工程资料：Git 官方 worktree 文档、GitHub PR / status checks / merge conflicts 文档、Google code review 工程实践、OpenAI Agents SDK orchestration / tracing 文档，以及 Anthropic 多 Agent 研究系统工程文章。这些资料用于形成 LDVH 推论，不直接等同于 Codex App 产品承诺。

边界如下：

- 本报告不修改 active specs、Rules、Code 或 Web；
- 本报告不把 CLI 能力直接写成 Codex App 已支持能力；
- 本报告不把当前线程观察到的能力写成公共产品事实；观察仅作为 spark-0027 背景；
- 本报告不创建 WorkCase、ADR 或 Rules 入口，只提出后续分流建议；
- 本报告不替代后续主线程/Human 对并行策略的决策。

## 关键发现

### Codex worktree 的职责

OpenAI Codex App 文档说明，worktree 让 Codex 在同一项目中运行多个互不干扰的独立任务。对 Git 仓库，Codex worktree 底层使用 Git worktree；默认从选定分支的 `HEAD` 创建，通常处于 detached HEAD，用户可以在 worktree 中创建分支、提交、推送并打开 PR。Codex 也支持 Local 与 Worktree 之间的 Handoff，用于把线程和代码移动到另一个 checkout。

Git 官方文档说明，一个 Git 仓库可以支持多个 working trees，从而同时 checkout 多个分支。Codex 文档进一步强调同一分支不能在多个 worktree 中同时 checkout，因为分支是一个可变引用，Git 需要避免多个工作树同时推进同一 branch ref 导致歧义。

对 LDVH 的结论是：worktree 线程适合承载会写文件、需要独立验证、可能形成提交、可能与其它任务冲突或需要独立回收的工作。典型任务包括：

| 任务类型 | 是否适合 worktree | 原因 |
|---|---|---|
| active specs / Rules / Code / Web 修改 | 适合，但必须按对应入口和 Human Gate | 写入范围大，需独立 diff、验证和提交 |
| Study / Spark 等工作对象整理 | 适合 | 可形成小而完整的事实源提交 |
| 外部调研且只产出 Study | 适合 | 上下文大但写入范围小，便于隔离资料噪音 |
| CI / 测试修复 | 适合 | 可在独立环境中反复运行命令，不干扰本地现场 |
| 多个互不相关改造并行 | 适合 | 每个 worktree 可以对应一个任务卡和提交闭环 |
| 单文件轻量问答 | 通常不需要 | 同目录线程或当前线程即可 |

LDVH 不应把 worktree 理解为事实源本身。worktree 只是执行隔离和 Git checkout 机制，稳定事实仍必须进入 `ldvh-base/`、`specs/`、`rules/`、`code/`、`web/` 或其它权威文件，并由 Git commit records 追溯。

### 新建对话的职责

Codex App 文档说明，新线程是 app 的基本工作单元，支持在 Local、Worktree 或 Cloud 模式下启动。App command 文档还说明可以通过快捷键或 deep link 创建新线程，并指定本地 `path` 或初始 prompt。

新建对话不必然等于新 worktree。LDVH 应区分三种线程：

| 线程形态 | 适用场景 | 写入边界 |
|---|---|---|
| 当前线程 | 主控编排、Human Gate、最终汇总、合并顺序、冲突判断 | 可写当前任务授权范围 |
| 同目录新线程 | 短时咨询、只读复核、同一现场下的日志/命令观察、无需隔离 diff 的帮助 | 默认只读或极小写入，必须避免与主线程同时改同一文件 |
| worktree 新线程 | 可独立提交的实现、研究、迁移、修复、验证和回收任务 | 只写委派任务卡授权范围，最终以 diff/commit 交还 |

同目录线程的优势是启动轻、能共享当前本地现场，适合询问或复核。风险是没有文件系统隔离，多个线程同时写同一目录会制造未追踪冲突，且 Git diff 难以归因。因此 LDVH 对同目录线程应默认限制为只读、复核或 Human 明确授权的极小修改。

worktree 线程的优势是隔离变更、独立验证和可回收提交。风险是被隔离的 `.gitignore` 文件、依赖缓存或本地配置可能不存在。Codex 文档提供 `.worktreeinclude` 用于复制被 Git 忽略但新 worktree 必需的本地文件。LDVH 后续若常用 worktree 跑 Web / Code，应考虑把必要但不含敏感内容的本地配置纳入 `.worktreeinclude` 候选，但这属于后续 WorkCase 或 ADR，不在本报告直接修改。

### 子 Agent 的职责

Codex 官方 subagent concepts 说明，子 Agent 的主要价值是把探索笔记、测试日志、stack trace、命令输出等噪音移出主线程，降低 context pollution / context rot，并让主 Agent 保持在需求、决策和最终输出上。官方建议从 read-heavy 任务开始，如探索、测试、triage 和 summarization；对 parallel write-heavy workflow 要更谨慎，因为多个 Agent 同时编辑会产生冲突和协调成本。

Codex subagents 文档说明，子 Agent 默认可用，但 Codex 只在用户明确要求时 spawn；每个子 Agent 都会独立消耗模型和工具成本。子 Agent 继承当前 sandbox 策略，父 turn 的 live runtime overrides 也会在 child 中重新应用。Codex 内置 `default`、`worker` 和 `explorer`，也允许通过 `~/.codex/agents/` 或项目 `.codex/agents/` 定义自定义 Agent。

对 LDVH 的结论是：子 Agent 是过程能力，不是长期事实源。它最适合：

- 只读知识地图、规范片段、代码片段或日志分析；
- 多视角 review，如事实源边界、测试缺口、规则同步、可维护性；
- 大量外部资料或大文件的分片摘要；
- 对主控方案或结果做独立复核；
- 在 WorkCase 的 execution item 中承担明确输入、输出和证据要求的局部任务。

子 Agent 不适合默认承担：

- 事实源状态流转的最终决定；
- Human Gate 代签；
- 多文件高耦合写入；
- 修改 active specs / Rules / Code / Web 的最终合并判断；
- 关闭 Spark、WorkCase 或 Study 的判断；
- 把中间日志、草稿或未经主控审查的结论写入长期事实源。

### 一层嵌套子 Agent 的边界

Codex subagents 文档说明，`agents.max_depth` 默认是 `1`，根会话深度从 `0` 开始；默认允许直接 child agent spawn，但防止更深嵌套。文档建议除非确实需要 recursive delegation，否则保持默认，因为提高深度可能把宽泛委派指令变成重复 fan-out，增加 token、延迟、本地资源和可预测性风险。`agents.max_threads` 仍会限制并发打开的线程数，但不能消除深层递归的成本和风险。

spark-0027 背景中已经观察到：在 `~/.codex/config.toml` 设置 `[agents] max_threads = 6, max_depth = 2` 后，新线程里已验证子 Agent 可再 spawn 一层 child。该观察说明当前环境中一层嵌套可能可用，但不应把它扩展为无限递归或默认能力。

LDVH 建议把 `max_depth = 2` 的使用限制为“主控 -> 子 Agent -> child”一层，并遵守以下边界：

| 边界 | 建议 |
|---|---|
| 触发条件 | 只有主控任务卡明确授权，或子 Agent 遇到可独立分片的只读子问题时使用 |
| 子 Agent 职责 | 子 Agent 仍是局部负责人，不把 child 结果直接交给主线程当最终事实 |
| child 职责 | 默认只读、调查、复核、摘要、测试日志分析，不直接写 Git 文件事实源 |
| 写入权限 | child 默认不得写入；若必须写入，应退回主控创建独立 worktree 线程或明确 WorkCase 执行项 |
| 深度限制 | 不允许超过一层 child；提示中应写明“不得继续 spawn” |
| 数量限制 | 每个子 Agent 默认最多 spawn 1 到 2 个 child，且必须说明原因 |
| 证据回收 | child 只返回结论、证据路径、命令和残留风险；子 Agent 汇总后交还主控 |
| 失败处理 | child 失败不自动重试 fan-out；由子 Agent 或主控判断是否缩小任务 |

需要 ADR 的关键问题是：LDVH 是否正式允许二级编排。理由是它会改变行动编排中的主控责任、成本边界、证据链和故障处理方式。若暂不做 ADR，实践上应按“默认禁用，特殊只读授权”处理。

### 多 worktree 并行的主控职责

通用工程资料给出几个稳定原则。GitHub PR 文档把 PR 定位为讨论、review、合并变更的协作机制；status checks 基于 CI 等外部过程并显示在提交或 PR 上；merge conflicts 必须在合并前处理。Google code review 指南强调 review 的目的不是追求完美，而是保证整体代码健康持续改善。OpenAI Agents SDK orchestration 文档把 manager-style workflow 中的 specialist agent 视作工具，主 Agent 仍负责最终回答；tracing 文档强调复杂 agent workflow 需要事件记录来调试、可视化和监控。Anthropic 多 Agent 研究系统文章也明确多 Agent 会引入协调、评估和可靠性挑战。

这些资料对 LDVH 的推论是：多 worktree 并行必须有主控，而不是让多个线程自由竞争。主控线程应维护以下对象：

| 主控材料 | 内容 |
|---|---|
| 任务卡 | 线程 ID、worktree 路径、来源 Spark/WorkCase/Study、目标、允许写入路径、禁止范围、输入原文、外部资料要求、预期产物、验证命令、交还格式 |
| 事实源边界 | 哪些是权威原文，哪些只是工具输出、线程摘要或子 Agent 输出 |
| 提交拆分 | 每个 worktree 只做一个主意图；提交 message 描述动机、影响边界、验证和风险 |
| 验证命令 | fact validate、specs validate、测试、lint、构建或手工检查，按任务风险选择 |
| 合并顺序 | 先合并事实对象和低冲突文档，再合并 specs / Rules / Code / Web 等高影响资产 |
| 冲突处理 | 冲突由主控或专门合并线程处理，不由原 worker 自行决定跨线程取舍 |
| 残留风险 | 未验证、验证失败、环境缺口、资料不足、Human Gate 未完成必须回写或报告 |

对于 LDVH，主控线程还应维护“禁止范围”。本任务就是例子：只允许处理 spark-0027 和 study-0011，不允许修改 workcase-0006、workcase-0007、workcase-0008 或 spark-0026，也不允许修改 active specs、Rules、Code 或 Web。

### 合并顺序和冲突处理

多 worktree 的合并顺序应按事实源影响和冲突概率排序：

1. 先检查每个 worktree 是否只修改授权文件；
2. 先合并纯新增 Study、Spark、Pitfall 等低冲突事实对象；
3. 再合并同一对象的追加演变记录；
4. 再合并 Code / Web / tests；
5. 最后合并 active specs、Rules 或入口资产，因为它们会影响其它线程的读取规则；
6. 如果两个 worktree 修改同一事实对象，主控必须读两边原文和 diff，形成合并判断；
7. 如果冲突涉及 Human Gate、事实源边界、状态流转或规范规则，停止自动合并并请 Human 决策。

GitHub merge conflict 文档只说明通用冲突必须处理后才能合并；LDVH 的补充推论是：冲突处理本身如果形成规则取舍、事实源状态取舍或验收取舍，应回到对应事实源或 Human Gate，而不是只在冲突文件里“选一边”。

### LDVH 吸收路径

本研究建议把 Codex worktree、新建对话和子 Agent 吸收为 LDVH 的“行动调度实践”，而不是新增事实模型。

| LDVH 承载 | 应吸收的内容 | 不应吸收的内容 |
|---|---|---|
| 行动编排 | 主控调度、Context、Scenario、Gate、子 Agent / worktree 调用、验证和回写触发 | Codex 产品细节全文 |
| WorkCase | 多 worktree 任务卡、执行项、验证证据、结果复核、关闭材料 | 每个子 Agent 的完整过程日志 |
| Study | 外部资料调研、方案比较、实践建议、来源边界 | 已经决定执行的任务清单 |
| Spark | 尚未决策的能力缺口、风险线索、后续议题 | 完整报告正文 |
| ADR | 是否允许二级子 Agent、是否允许执行型子 Agent 写入、主控合并权威等长期取舍 | 临时执行偏好 |
| Rules 入口 | 最小启动读取、STOP 点、压缩恢复重读提示、任务导航入口 | 厚流程、产品手册、完整字段契约 |

这也意味着，LDVH 不应把“Codex worktree”写成唯一运行方式。其它环境可能没有 Codex App worktree，但仍可用 Git worktree、分支、PR、CI 或手工目录隔离实现同类约束。规范层应表达环境无关的职责分工；Codex 细节应进入运行时扩展、Rules 入口提示或 Skill/Agent 能力资产。

## 建议

### 直接进入后续 WorkCase 的建议

建议创建一个后续 WorkCase，目标是把本 Study 转成最小可执行实践，不直接改 active specs。候选执行项包括：

1. 设计 LDVH 并行任务卡模板，字段至少包括来源对象、线程 ID、worktree 路径、目标、写入范围、禁止范围、输入原文、预期产物、验证命令、交还格式和合并顺序；
2. 设计 worktree worker 交还模板，要求报告修改文件、验证命令、失败/未跑原因、Human Gate、残留风险和 commit hash；
3. 设计子 Agent 摘要模板，要求返回结论、证据路径、风险、建议主控动作，不返回大段日志；
4. 设计多 worktree 合并前检查清单，覆盖 `git status`、授权文件、事实源校验、冲突检查、验证命令和提交拆分；
5. 设计同目录线程使用限制，默认只读或短任务，不承担并行写入；
6. 把 `max_depth = 2` 的实践先写成临时核对动作或候选规则，不直接默认启用。

### 需要 ADR 的建议

以下问题影响长期协作模型，应由 ADR 决策：

1. LDVH 是否正式允许子 Agent 再 spawn 一层 child；
2. 二级 child 是否只能只读，是否允许执行命令或写文件；
3. 主控线程是否是多 worktree 合并顺序和冲突处理的唯一调度者；
4. worktree 线程是否必须以 commit 作为交还完成条件，还是允许只交还 diff；
5. 是否把 Codex App worktree 作为 LDVH 官方推荐环境，还是只作为一种运行时适配。

### 仅作为实践建议的内容

以下内容可以立即作为操作偏好使用，但不应直接写成硬规则：

1. read-heavy 任务优先用子 Agent，write-heavy 任务优先用 worktree；
2. 一个 worktree 对应一个主任务、一个主事实对象或一个提交闭环；
3. 同一事实对象尽量由一个线程写，另一个线程只 review；
4. 子 Agent 输出越短越好，主控保留最终判断；
5. 大规模并行前先建立任务卡，不用口头提示记忆禁止范围；
6. 合并时优先低冲突新增文件，最后处理入口、规则和共享实现。

### 建议的选择矩阵

| 问题 | 当前线程 | 同目录新线程 | worktree 线程 | 子 Agent |
|---|---|---|---|---|
| 需要 Human Gate | 最适合 | 可辅助 | 需交回主控 | 不适合最终确认 |
| 只读调查 | 可做 | 可做 | 可做但偏重 | 最适合 |
| 外部调研写 Study | 可做 | 可做 | 最适合 | 可辅助资料分片 |
| 多文件实现 | 可做 | 不建议并行 | 最适合 | 仅限局部 worker 且范围清晰 |
| 代码/规范 review | 可做 | 可做 | 可做 | 最适合做独立视角 |
| CI 日志分析 | 可做 | 可做 | 可做 | 最适合 |
| 合并冲突处理 | 最适合 | 可咨询 | 可在专门合并 worktree 做 | 不适合最终取舍 |
| 事实源状态流转 | 最适合 | 不建议 | 可准备材料 | 不得最终决定 |

## 后续分流

本报告建议后续分流如下：

| 分流目标 | 建议动作 | 理由 |
|---|---|---|
| WorkCase | 建立“LDVH 并行 Codex 线程实践落地”工作项 | 可直接产出任务卡、交还模板、验证清单和合并清单 |
| ADR | 决策一层嵌套子 Agent、执行型子 Agent 写入和主控合并权威 | 这些是长期协作语义，不应由 Study 直接定规则 |
| Spark | 若后续发现 Codex App 与 CLI 能力差异、worktree 清理策略或 `.worktreeinclude` 安全边界未解决，应追加或新建 Spark | 这些仍是待研究/待决策线索 |
| 行动编排 | 在 WorkCase 验证后，考虑形成多线程/多 worktree 主控调度候选行动编排 | 该能力高频、跨事实源、需要 Gate、验证和回写 |
| Rules 入口 | 暂不直接修改；若未来行动编排 active，再评估入口薄引用和 STOP 点是否需要同步 | Rules 入口不应提前承载厚流程 |
| 运行时扩展 | 后续可考虑项目级 custom agent、`.worktreeinclude` 和 Codex config 建议 | 属于环境适配，不是本 Study 直接修改范围 |

主线程或 Human 需要决策的问题：

1. 是否接受“worktree 线程承接写入闭环、同目录线程默认只读、子 Agent 默认读多写少”的三分法；
2. 是否允许 `agents.max_depth = 2` 进入 LDVH 推荐实践，或先保持实验状态；
3. 是否要求每个 worktree 线程完成后都提交，还是允许以未提交 diff 交还；
4. 是否为多 worktree 合并建立专门 WorkCase 或行动编排；
5. 是否把 `.worktreeinclude` 纳入后续安全边界研究，尤其涉及 `.env`、本地配置和 secrets 时。
