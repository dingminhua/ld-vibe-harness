---
id: study-0001
type: study
title: WorkCase 与执行编排模型演变研究
status: active
created: '2026-06-18T04:16:49'
updated: '2026-06-24T03:20:00+08:00'
summary: |
  本报告整理本轮从 TaskPlan / Task / SubTask 体系，收敛到 WorkCase / ExecutionItem / Role Contract 方向的完整来龙去脉。核心结论是：LDVH 应把 Human 需要长期追踪的目标、范围、成功标准、验证和关闭证据保留在 WorkCase；AI 的执行拆解、并行安排、角色分派和临时步骤应作为 WorkCase 内部编排或运行期上下文处理，不再提升为独立 Task 工作模型。
user_intent: 用户要求将本轮关于 specs 工作流程、WorkCase、ExecutionItem、Spark 分流和事实源边界的长对话整理为 Study。
conclusion: |
  WorkCase 是面向 Human 与 AI 对齐的一次工作事实契约；ExecutionItem 是 WorkCase 内部的最小恢复与编排节点，不是工作对象；Role Contract 应承接专业 AI 角色的输入、权限、输出和交还边界，但其规范归属仍需继续判断。后续应优先逐段核对 specs/21，再回看 05、05.01、06 和 40-43，最后同步 Code / Web 中旧 TaskPlan、Task、SubTask 实现。
urls: []
input_refs:
- spark-0005
- spark-0006
related_sparks:
- spark-0005
- spark-0006
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
- history/specs-v1/00-LD-Vibe-Harness理念与纲要.md
- history/specs-v1/05-事实模型基础规范.md
- history/specs-v1/05.02-字段内容与格式规范.md
- history/specs-v1/06-行动编排基础规范.md
- specs/21-WorkCase-工作项.md
- specs/20-Spark-火花.md
- specs/24-Study-研究报告.md
archive_reason: null
---

# WorkCase 与执行编排模型演变研究

## 研究问题

本轮讨论要回答的核心问题是：LDVH 是否应该把 AI 执行过程中的任务拆分、子 Agent 分派、复检和中间步骤都变成长期工作对象，还是只保留 Human 和未来 AI 需要复读的事实源。

这个问题最初来自对 `specs/20-23`、`specs/05` 和 `specs/05.01` 的疑问：旧体系里存在 TaskPlan、Task、SubTask 等层级，但实际 vibe coding 中，AI 自己已经会在当前上下文中制定计划、拆分步骤、调用工具、调整路线。若 LDVH 再把这些过程全部对象化，会导致事实源膨胀、Human 审核负担增加，也容易把运行期过程误当作长期事实。

因此，本轮研究围绕以下问题展开：

1. Human 真正关心的对象是计划，还是计划下的每个任务；
2. Task 是否应该作为独立工作模型存在；
3. SubTask 是否还有必要；
4. 并行和串行应该作为任务属性，还是由计划内部关系推导；
5. 子 Agent、主控自检、独立复检、Human Gate 应如何归位；
6. 执行过程不作为历史事实源时，仍应保留哪些恢复、验证和关闭证据；
7. Spark、Study、ADR、Pitfall、WorkCase 在讨论收敛后的分流边界是什么。

## 输入与边界

本报告基于 2026-06-18 本轮 Human/AI 对话、相关 specs、工作对象事实源和已生效变更整理。报告只记录已经形成稳定复读价值的模型演变结论，不复制完整对话流水，也不把执行过程中的临时计划提升为长期事实源。

## 关键发现

### 对话演变脉络

#### 阶段一：从 TaskPlan / Task / SubTask 的边界问题开始

早期讨论仍以 TaskPlan、Task 和 SubTask 为基础。一个典型问题是：“分别审查 20、21、22、23，然后合并结论”到底应表达为一个 TaskPlan 下的四个 Task，还是一个 Task 下的四个 SubTask。

当时形成过一个候选口径：

- TaskPlan 承载目标、范围、成功标准和任务编排；
- Task 是可委派、可验证、可关闭的执行单元；
- SubTask 不再作为 active 模型；
- 并行工作用同一 TaskPlan 下的 sibling Task 表达；
- 串行工作由 Task 之间的依赖表达；
- 子 Agent 执行 Task，但不再调用下级子 Agent；
- Review 默认是流程动作，复杂时可以作为并列 Task。

这个阶段的价值在于明确了 SubTask 的问题：它会制造多余层级，而且与当前子 Agent 不能再调用子 Agent 的执行能力不匹配。

#### 阶段二：从 Task 中心转向 WorkCase 中心

后续讨论进一步指出：即使保留 Task，Human 其实也不关心每个 Task 的长期历史。Human 关心的是计划是否对齐目标、成功标准是否可验收、最终是否可以关闭，以及风险和经验有没有被正确分流。

这推动了关键语义变化：

- `TaskPlan` 改名为 `WorkCase`，避免与 Codex、Claude、Trae 等环境中的运行时 plan 混淆；
- 独立 `Task` 移出 active 工作模型；
- `SubTask` 不再作为 active 工作模型；
- 原 Task 的执行编排职责迁入 `WorkCase.orchestration.execution_items`；
- ExecutionItem 只作为 WorkCase 内部恢复和编排节点；
- Review、Audit、Decision Review 是流程环节，不是工作模型；
- Human 主要审 WorkCase 的目标、范围、成功标准、关闭判断和证据，不直接管理 AI 的内部执行项。

这个阶段的核心转折是：LDVH 不再尝试把 AI 的每个执行步骤变成项目事实源，而是把长期事实源收敛到 WorkCase 层。

#### 阶段三：明确 ExecutionItem 不是更小的工作对象

一个重要追问是：如果 WorkCase 里有 `execution_items`，那么每个 execution item 是否又要拆成工作对象。

当前结论是否定的。ExecutionItem 不是更小的工作对象，也不应被其他对象长期引用。它只服务以下目的：

- 让主控 AI 知道当前工作分成哪些执行项；
- 支持并行、串行或混合执行安排；
- 记录执行项所需角色、输入、预期输出和结果摘要；
- 在上下文恢复时知道工作推进到哪里；
- 为最终验证和关闭证据提供线索。

执行者拿到 ExecutionItem 后，仍然可以在自己的运行时上下文中继续拆分步骤、列 checklist、调用工具或调整路径。但这些二级拆分属于 AI 内部执行过程，不进入 LDVH 长期事实源。

当一个 ExecutionItem 需要独立目标、独立范围、独立 Human Gate、独立关闭判断，或者已经超出当前 WorkCase 的关闭边界时，它应被分流为新的 WorkCase，而不是升级为 Task。

#### 阶段四：区分过程记录与事实源证据

讨论中最容易混淆的一点是“执行过程不作为历史事实源”。

这里并不是说过程完全不重要，而是说不应记录无复读价值的过程噪音，例如：

- AI 搜了哪些文件、按什么顺序读；
- 子 Agent 的中间思考；
- 临时 todo；
- 未采纳草稿；
- 已被最终结论吸收的重复分析；
- 一次性命令输出或工具缓存；
- 只服务当前上下文的局部选择。

但 WorkCase 仍必须保留最小恢复、验证和关闭证据：

- 恢复证据：当前推进到哪里、下一步是什么、哪个执行项由哪个角色处理、依赖关系是什么、最近结果是什么；
- 验证证据：执行了哪些测试或检查、独立复检发现了什么、Human Gate 确认了什么、哪些验收项已满足；
- 关闭证据：为什么可以关闭、改了什么、还有什么残余风险、哪些未完成项被分流、经验是否进入 ADR / Pitfall / Spark / specs / Change。

这使 LDVH 与普通 vibe coding 拉开边界：普通 vibe coding 往往只留下代码结果和聊天上下文；LDVH 要留下未来仍能判断“为什么这样做、是否完成、还有什么风险”的事实源。

### 行业实践复核

本轮讨论中做过一次联网复核，用于判断 LDVH 的方向是否违背主流 AI 编程趋势。复核结果支持当前收敛方向，但资料只作为研究依据，不直接替代 specs。

主要观察如下：

1. 主线程保持干净、过程噪音下沉是明确趋势。Codex Subagents 文档强调可以把探索、测试、日志分析等 noisy work 移出主线程，让 main agent 聚焦 requirements、decisions 和 final outputs。
   来源：https://developers.openai.com/codex/concepts/subagents

2. 专业角色和多 Agent 编排是主流方向。Codex、Claude Code、LangChain 和 Microsoft 都强调 specialized agents、supervisor / orchestrator、worker agents、review、human-in-the-loop 等模式。
   来源：
   - https://docs.anthropic.com/en/docs/claude-code/sub-agents
   - https://docs.langchain.com/oss/python/langchain/multi-agent
   - https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns

3. 可复用流程和专业知识应按需加载，而不是常驻上下文。Codex Skills 和 Claude Skills 都强调 reusable workflow / domain expertise，以及 progressive disclosure 或按需加载。
   来源：
   - https://developers.openai.com/codex/skills
   - https://docs.anthropic.com/en/docs/claude-code/skills

4. 长期规则和事实不应依赖 memory。Codex Memories 文档强调 required team guidance 应放在 AGENTS.md 或 checked-in documentation，memory 只是 helpful local recall layer。
   来源：
   - https://developers.openai.com/codex/memories
   - https://developers.openai.com/codex/guides/agents-md

5. Human-in-the-loop、验证、checkpoint、observability 和 output validation 是多 Agent 工程中的重要关注点。
   来源：https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns

对 LDVH 的判断是：LDVH 并不是逆行业趋势，也不是要替代 AI 自己的执行编排，而是把行业中分散的能力组织成项目事实源体系。WorkCase 对应行业工具通常缺失的“可持久计划、验收与关闭证据”层；ExecutionItem 对应运行时可恢复编排；Role Contract 对应专业子 Agent 的输入、权限、输出和交还边界。

### 已经落地的规范变化

截至本报告创建时，已经完成了若干规范和实现层面的收敛：

1. 00 已从“对象化任务管理”转向“面向 AI 协作的事实源治理”。
2. 02 已清理旧 TaskPlan / Task / SubTask 术语，改用 WorkCase 与 ExecutionItem。
3. 05 已明确当前 active 工作模型集合以 WorkCase、ADR、Pitfall、Spark、Study 等承载长期工作事实，Git 提交记录用于追溯事实源修改，ExecutionItem 不进入 20-29 集合。
4. 05.01 已明确公共字段边界，补充 `verification_evidence`、`closure_evidence`，并改用 `related_workcases`。
5. 21 已改为 WorkCase 规范，定义 WorkCase 状态机、`orchestration.execution_items`、`orchestration.review`、验证证据和关闭证据。
6. 22 / 23 已从 active 模型中移除或清理概念行混淆。
7. 24 Spark 已改为分流前工作对象，使用 `source: web | conversation`，并通过 `related_workcases` 关联 WorkCase。
8. 25 Study 已成为报告产物对象，用于承载稳定研究报告正文，避免 Spark 复制完整报告。
9. Code / Web 已局部同步 Spark / Study 字段，但旧 TaskPlan、Task、SubTask 的完整迁移尚未完成。

### 当前模型边界

#### WorkCase

WorkCase 是 Human 与 AI 围绕一次目标达成的工作事实契约。它承载：

- 目标和背景；
- 范围和约束；
- 所属 WorkCase；
- 成功标准；
- 执行编排摘要；
- 验证证据；
- 关闭证据；
- 相关 Spark、ADR、Pitfall、Change 和 docs；
- 经验分流结果。

WorkCase 是 Human 可以审核、AI 可以恢复、未来可以复读的事实源入口。

#### ExecutionItem

ExecutionItem 是 WorkCase 内部字段，不是工作对象。它承载：

- 局部唯一 ID；
- 标题；
- 角色或专业视角；
- single / sequential / parallel 等编排模式；
- 输入引用；
- 预期输出；
- 内部执行态；
- 结果摘要；
- 证据引用；
- 阻塞原因。

ExecutionItem 的目标是支持当前执行恢复和证据组织，而不是保存完整过程历史。

#### Role Contract

Role Contract 是尚未完全定型的概念。当前判断是：它应定义专业子 Agent 或专业审查视角的目的、输入、必读材料、允许动作、禁止动作、输出格式、交还对象和停止条件。

未决问题是 Role Contract 应归入哪里：

- 作为 04 能力资产的一类；
- 作为 06 工作流程基础中的角色契约规则；
- 作为 30-59 具体工作流程中的局部角色定义；
- 或者作为后续独立规范承接。

当前倾向是先不要在 WorkCase 字段契约中提前定义完整角色规则。WorkCase 只保留执行恢复所需的最小 `role` 标识，完整角色规则由工作流程、能力资产或后续专门规范承接。

#### Review / Audit

Review、Audit、Decision Review 当前不应成为工作模型。它们是流程环节或专业审查动作。

审查安排可以放在 `orchestration.review`，审查结论必须回写到：

- `verification_evidence`；
- `closure_evidence`；
- 后续 WorkCase；
- Spark；
- ADR；
- Pitfall；
- specs；
- Code / Web 变更。

审查输出不应绕过主控直接成为最终事实。主控负责整合、判断、补证和触发 Human Gate。

### Spark 与 Study 的分工

本轮也暴露出 Spark 与 Study 的边界问题。

Spark 适合记录：

- 尚未计划化但有保留价值的问题；
- 当前摘要；
- 关键语义转折；
- 待分流方向；
- 与 WorkCase、ADR、Study、Pitfall 或 docs 的关联。

Study 适合记录：

- 已经整理成稳定阅读价值的报告；
- 对话来龙去脉；
- 资料和方法；
- 关键发现；
- 结论边界；
- 残留不确定性；
- 后续分流建议。

因此，`spark-0005` 被压缩为接续入口，而本 Study 承载完整来龙去脉。`spark-0006` 则保留另一个问题：当 Spark 中部分内容已经落地或转移，但仍有未收敛内容时，AI、Code 或 Web 应如何提醒是否继续 pending、追加 evolution、分流或 resolved。

### 未决问题

以下问题仍需在新会话继续核对：

1. `specs/21-WorkCase-工作项.md` 中的 `orchestration.execution_items` 字段是否过多、过少或命名不稳；
2. `mode: single | sequential | parallel | mixed` 是否应该是 WorkCase 总体编排字段，还是只由 execution item 关系推导；
3. ExecutionItem 是否需要 `depends_on`，或者当前 `mode` 与顺序即可满足恢复；
4. `status` 作为 ExecutionItem 内部执行态是否会让它过度接近独立工作对象；
5. `orchestration.review` 是否只声明安排，还是需要标准化独立复检输出；
6. `verification_evidence` 与 `closure_evidence` 的内容边界是否足够清楚；
7. Role Contract 应由哪个规范承接；
8. 40-43 工作流程是否需要增加“对话到 WorkCase”或“Spark 分流与收敛”流程；
9. Code / Web 中旧 TaskPlan、Task、SubTask 兼容层何时移除；
10. 是否需要在 Code / Web 中提示 pending Spark 已有关联对象但未说明收敛状态。

## 建议

建议新会话按以下顺序推进：

1. 精读并逐段核对 `specs/21-WorkCase-工作项.md`；
2. 重点检查 WorkCase 准入、状态机、`orchestration`、ExecutionItem、review、验证证据和关闭证据；
3. 回看 `history/specs-v1/05-事实模型基础规范.md`，确认 ExecutionItem 不进入 active 工作模型集合；
4. 回看 `history/specs-v1/05.02-字段内容与格式规范.md`，确认公共字段和证据字段边界；
5. 回看 `history/specs-v1/06-行动编排基础规范.md`，确认计划、执行、自检、复检、Human Gate 和 Learn 的流程表达；
6. 检查 40-43 是否需要新增或调整具体工作流程；
7. 待规范稳定后，再迁移 Code / Web 中旧 TaskPlan、Task、SubTask 实现。

## 后续分流

本轮讨论的核心价值，是把 LDVH 从“把任务过程对象化”的方向，拉回到“为 AI 协作保存必要事实源”的方向。

WorkCase 应是面向人和未来 AI 的长期事实契约；ExecutionItem 应是 WorkCase 内部的运行恢复和证据组织结构；Role Contract 应是专业 AI 角色协作边界；Review 是流程环节；Spark 是待分流议题入口；Study 是稳定报告承载。

这套方向符合当前 AI 编程工具对主线程清洁、多 Agent 分工、HITL、验证、checkpoint 和 checked-in documentation 的趋势，也更符合 LDVH 00 所强调的事实源治理价值。
