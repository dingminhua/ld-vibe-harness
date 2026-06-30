---
id: study-0013
type: study
title: Task Master AI 插件工具吸收调研
status: active
created: '2026-06-30T11:20:16+08:00'
updated: '2026-06-30T11:20:16+08:00'
summary: |
  本 Study 调研 TaskmasterAI / Task Master AI 最可能指向的官方对象：GitHub 仓库 `eyaltoledano/claude-task-master`、npm 包 `task-master-ai`、官方文档 `docs.task-master.dev` 及其 MCP / Claude Code 插件承载。核心判断是：Task Master AI 的可吸收价值不在于照搬一个外部任务系统，而在于它把 PRD、任务拆解、依赖、复杂度、下一步选择、状态更新和 AI coding agent 的 MCP/CLI 入口组合成一个面向 AI 的项目任务编排层。LDVH 应吸收其任务依赖图、下一可行动项选择、复杂度/拆分辅助、CLI/MCP 双入口和编辑器集成边界；但不得让外部 `.taskmaster` 文件、AI 自动拆解结果或插件运行状态替代 LDVH 的 WorkCase、Spark、ADR、Study 与 Git 文件事实源。
user_intent: |
  Human 要求联网调研 TaskmasterAI / Task Master AI 插件或工具，覆盖产品/工作流、技术实现和 LDVH 可吸收建议，并将结果写入 Study；本线程只负责该单项调研，不做三个插件的总汇总。
conclusion: |
  Task Master AI 可作为 LDVH 后续任务编排和运行时扩展设计的参考：它证明“面向 AI agent 的任务系统”应提供结构化任务、依赖阻塞、复杂度分析、任务展开、下一步选择、过程更新和 MCP/CLI/编辑器入口。但 LDVH 的事实模型已经区分 Spark、Study、WorkCase、ADR、Pitfall 和 docs，不能把 Task Master AI 的任务文件作为第二事实源，也不能把 PRD 自动拆解视为可直接执行的 WorkCase。建议后续围绕 WorkCase 依赖图、next-action selector、agent-facing MCP adapter、复杂度/拆分建议、Web 任务关系视图建立候选 WorkCase 或 ADR；代码复制还需受其 MIT WITH Commons-Clause 许可边界约束。
urls:
  - ref: https://github.com/eyaltoledano/claude-task-master
    title: GitHub - eyaltoledano/claude-task-master
    summary: |
      官方 GitHub 仓库，是确认 Task Master AI 身份、源码组织、`.taskmaster` 示例、MCP/CLI/插件承载和许可证边界的一手来源。
  - ref: https://www.npmjs.com/package/task-master-ai
    title: npm - task-master-ai
    summary: |
      npm 包页面与 `npm view` 元数据用于确认包名、最新版本、Node 版本要求、CLI/MCP bin 入口、描述、仓库和许可证信息。
  - ref: https://docs.task-master.dev/
    title: Task Master Documentation
    summary: |
      官方文档入口，用于确认 Task Master AI 的产品定位、PRD 到任务的典型流程、MCP/CLI 使用方式、配置与任务管理能力。
  - ref: https://github.com/eyaltoledano/claude-task-master/blob/main/package.json
    title: claude-task-master package.json
    summary: |
      仓库中的包清单用于核对 `task-master`、`task-master-mcp`、`task-master-ai` 三个 bin 入口、Node 版本要求和 npm 发布边界。
  - ref: https://github.com/eyaltoledano/claude-task-master/blob/main/README-task-master.md
    title: README-task-master.md
    summary: |
      官方 README 用于确认工具面向 AI 驱动开发的任务拆解、任务列表、下一任务、展开任务、更新状态等核心命令和工作流。
  - ref: https://github.com/eyaltoledano/claude-task-master/blob/main/CLAUDE_CODE_PLUGIN.md
    title: Claude Code Plugin Guide
    summary: |
      官方 Claude Code 插件说明，用于确认它不仅是 CLI/MCP 工具，也有面向 Claude Code 的插件打包与安装入口。
  - ref: https://github.com/eyaltoledano/claude-task-master/blob/main/taskmaster.mcpb
    title: taskmaster.mcpb
    summary: |
      仓库中的 MCP bundle 文件用于确认 Task Master AI 存在可安装 MCP/插件承载形态，但本报告不把该二进制包内容作为规则事实源。
input_refs:
  - ldvh-base/sparks/spark-0039-plugin-study-absorption.yaml
  - specs/00-LDVH理念与价值标准.md
  - specs/24-Study-研究报告.md
  - specs/34-study-research-output-研究行动产物编排.md
related_sparks:
  - spark-0039
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/00-LDVH理念与价值标准.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
  - specs/34-study-research-output-研究行动产物编排.md
archive_reason: null
---

# Task Master AI 插件工具吸收调研

## 研究问题

本报告回答一个收束问题：TaskmasterAI / Task Master AI 这个插件或工具，究竟是什么、解决什么问题、如何实现，以及 LDVH 应该从中吸收哪些能力。

具体研究问题包括：

1. 名称边界：`TaskmasterAI`、`Task Master AI`、`task-master-ai` 是否指向同一类对象；
2. 产品/工作流：它如何服务 AI coding / agent 开发，典型使用路径是什么；
3. 技术实现：它的任务文件、依赖、CLI、MCP、编辑器/插件、模型集成边界是什么；
4. LDVH 吸收：哪些能力适合进入事实模型、行动编排、Code、Web、运行时扩展，哪些不应吸收；
5. 后续分流：哪些判断需要 WorkCase、ADR、Pitfall、docs 或新的 Spark 承接。

## 输入与边界

本次调研按 Human 要求联网进行，并在收束提醒后停止横向扩展资料范围。已确认的一手来源包括官方 GitHub 仓库、npm 包元数据、官方文档入口、仓库中的 `package.json`、README、Claude Code 插件说明和 MCP bundle 文件。

名称边界如下：

- 本报告采用的最可能对象是官方仓库 `eyaltoledano/claude-task-master` 与 npm 包 `task-master-ai`。
- npm 元数据确认其描述为面向 AI 驱动开发的任务管理系统，包名是 `task-master-ai`，最新版本在本次查询时为 `0.43.1`，要求 Node `>=20.0.0`，bin 入口包括 `task-master`、`task-master-mcp` 和 `task-master-ai`。
- 仓库中存在 `.claude-plugin`、`CLAUDE_CODE_PLUGIN.md` 和 `taskmaster.mcpb`，说明它不仅是 CLI，也有 MCP / Claude Code 插件承载。
- 由于 `TaskmasterAI` 也可能被用户口头用于泛指同类任务管理产品，本报告只对上述官方对象负责，不把其它同名或近名产品纳入结论。

资料边界如下：

- 本报告只沉淀稳定研究结论，不复制官方 README 或文档原文。
- 本报告不安装或运行 Task Master AI，不评估其全部命令参数、交互细节或最新 changelog。
- 本报告不做 CodebaseMemory、Firecrawl 或三个插件之间的最后汇总。
- Task Master AI 版本、文档路径和支持模型变化较快；涉及具体命令参数、模型列表和插件市场行为时，后续落地前仍需再次核对官方文档。

## 关键发现

### 一句话判断

Task Master AI 是一个面向 AI coding agent 的任务编排工具：它把需求文档转成结构化任务，把任务拆成子任务和依赖图，再通过 CLI、MCP server 和编辑器/Claude Code 插件入口让 AI agent 查询下一步、展开任务、更新状态和保留实现上下文。

对 LDVH 来说，它最有价值的不是“任务管理软件”这个名词，而是一个清晰的 agent-facing 工作模式：把 AI 不擅长长期记住的计划、依赖、阻塞和进度，外置为可读写、可查询、可验证的项目内结构化任务层。

### 产品与工作流发现

Task Master AI 解决的问题可以概括为：AI coding agent 很容易在一个 PRD 或大型需求中丢失全局计划、重复询问上下文、跳过依赖、同时展开过多任务，或者只凭聊天历史判断下一步。Task Master AI 用项目内任务文件和工具命令把这些信息持久化。

典型工作流是：

1. 在项目中初始化 Task Master AI，生成 `.taskmaster` 相关目录、配置和示例材料；
2. 提供 PRD 或需求说明，让工具调用模型解析为任务列表；
3. 对任务做复杂度分析，识别需要展开的高复杂度项；
4. 将任务展开为子任务，并记录依赖、优先级、测试策略和实现细节；
5. 通过 CLI 或 MCP 查询任务列表、查看某个任务、选择下一可行动任务；
6. AI agent 实施代码变更时，把发现、实现说明或状态更新回任务；
7. 在 Cursor、Claude Code、Windsurf、Roo 等编辑器或 agent 环境中，通过 MCP/规则/插件把同一套任务上下文暴露给 AI。

这套工作流与 AI coding 的关系很直接：它不是替 AI 写代码的完整 IDE，而是给 AI coding agent 提供“项目任务记忆”和“下一步选择器”。它把 agent 的工作粒度从自由聊天约束到具体任务、子任务、依赖和状态，从而降低上下文漂移。

### 技术实现发现

Task Master AI 的当前可确认承载包括：

| 维度 | 观察结论 | 对 LDVH 的含义 |
|---|---|---|
| 包与入口 | npm 包 `task-master-ai` 暴露 `task-master` CLI、`task-master-mcp` 和 `task-master-ai` MCP server bin | 一个能力可同时有 CLI 和 MCP 入口，LDVH 后续运行时扩展可参考这种双入口设计 |
| 项目文件 | 仓库示例和文档围绕 `.taskmaster` 目录组织任务、配置、文档和报告 | 项目内文件可作为 agent 共享状态，但 LDVH 必须明确谁是权威事实源 |
| 任务结构 | 任务通常包含 id、title、description、details、testStrategy、priority、dependencies、status 和 subtasks 等字段 | LDVH WorkCase 可吸收依赖、测试策略、状态和子任务表达，但要映射到现有事实模型 |
| 依赖关系 | 工具支持任务依赖和下一任务选择，避免 agent 抢跑被阻塞任务 | LDVH 可考虑为 WorkCase / 子任务增加依赖图和 next-action selector |
| 复杂度分析 | 工具可分析任务复杂度并建议展开 | LDVH 可吸收为 AI 辅助拆分建议，但不能让复杂度分数直接决定事实流转 |
| CLI/MCP | 同一任务能力通过命令行和 MCP 暴露给不同 agent 客户端 | LDVH 可把 MCP 看成运行时适配层，而不是新事实源 |
| 编辑器/插件 | 仓库包含 Claude Code 插件说明、MCP bundle、Cursor/Claude 等环境相关目录 | LDVH 可参考“环境入口适配”，但不应绑定单一编辑器 |
| 模型集成 | 工具通过配置和环境变量连接模型提供方，包含主模型、研究模型、回退模型这类角色边界 | LDVH 可吸收模型角色分工概念，但 API key、provider 选择和计费不应进入事实模型 |
| 许可证 | npm 元数据和仓库显示为 `MIT WITH Commons-Clause` | 后续只宜吸收设计模式，不应直接复制代码或资源，除非单独评估许可证 |

Task Master AI 的核心架构可以理解为三层：

1. **事实承载层**：项目内 `.taskmaster` 文件保存任务、配置、PRD 或报告等资料；
2. **能力执行层**：CLI 命令和 MCP tools 对任务进行创建、解析、展开、查询、更新、状态流转和复杂度分析；
3. **agent 入口层**：Cursor、Claude Code、Windsurf、Roo 等环境通过 MCP、规则文件或插件调用这些能力。

它的边界也很清楚：Task Master AI 能帮助 agent 维护任务上下文和计划，但它本身不等同于代码验证系统、产品决策系统或长期架构治理系统。任务状态变成 `done` 不天然证明代码已经满足规格，也不天然证明 Human Gate、测试、CI 或 Git 追溯已经完成。

### LDVH 可吸收能力

#### 1. 事实模型可吸收：任务依赖和下一可行动项

LDVH 已有 Spark、Study、WorkCase、ADR、Pitfall 等事实模型。Task Master AI 的任务对象提示 LDVH：对可执行工作而言，单个 WorkCase 的状态还不够，系统还应能表达依赖、阻塞、拆分层级和下一可行动项。

可吸收方向：

- 为 WorkCase 或 WorkCase 子结构补充依赖关系、阻塞原因和可行动条件；
- 建立 `next-action` 派生视图：只推荐未被依赖阻塞、资料边界清楚、验证入口明确的项；
- 为任务拆分保留 AI 建议与 Human 确认的边界，不把建议直接写成 active 事实；
- 把任务的 `testStrategy` 思路转译为 LDVH 的验证证据字段或关闭前检查。

不应吸收的部分：

- 不应把 `.taskmaster/tasks/tasks.json` 这类外部格式并列为 LDVH 的事实源；
- 不应把 Task Master AI 的任务状态枚举直接覆盖 WorkCase 状态机；
- 不应让 AI 解析 PRD 后自动创建大量 active WorkCase，而没有 Human Gate 或分流审查。

#### 2. 行动编排可吸收：PRD 到任务、复杂度到拆分、执行到更新

Task Master AI 的 workflow 可转译为 LDVH 行动编排候选：

- 从 Spark / Study / docs 输入中提取候选 WorkCase；
- 对候选事项做复杂度、依赖和风险评估；
- 将过大的 WorkCase 拆成子项或后续 WorkCase；
- 每次执行前读取下一可行动项和相关事实源；
- 执行后把实现发现、验证结果和残留风险回写到正确对象。

这里最值得吸收的是“下一步不是凭聊天感觉决定，而是由依赖、状态、复杂度、验证入口和事实源边界共同决定”。这与 LDVH 的 AI 第一目标一致：降低 AI 在长任务中反复恢复上下文、错误选择入口和越界执行的负担。

#### 3. Code 可吸收：确定性检查与派生选择器

Task Master AI 的任务依赖图适合转成 LDVH 的确定性 Code 能力：

- 检查 WorkCase 依赖是否引用存在对象；
- 检查依赖图是否有环；
- 检查已完成项是否仍被标为阻塞；
- 派生“下一可行动项”列表；
- 检查大任务是否缺少拆分理由或验证入口；
- 将复杂度分析输出保存为建议，而非权威状态；
- 对 agent 回写做 schema 校验，避免自由文本污染事实源。

这些能力属于 Code 派生与验证，不应替代 AI/Human 对任务价值、优先级和分流边界的判断。

#### 4. Web 可吸收：任务图、阻塞链和执行视图

Task Master AI 的可视化价值不是页面装饰，而是让 agent 与 Human 快速看到“为什么现在做这个”。LDVH Web 可吸收：

- WorkCase / Spark / Study 的关系图；
- WorkCase 依赖阻塞链；
- 下一可行动项列表；
- 每个可执行项的输入资料、验收标准、验证命令和关联 Study；
- 大任务拆分树；
- AI 建议与已确认事实的视觉区分。

Web 只能展示和辅助定位，不能在当前阶段直接把 AI 建议写回事实源，也不能维护第二套任务状态。

#### 5. 运行时扩展可吸收：MCP adapter 和环境入口

Task Master AI 的 MCP/CLI/插件形态对 LDVH 运行时扩展很有启发：

- 同一能力应有脚本/CLI 入口，便于确定性验证和 CI 调用；
- 同一能力也可暴露 MCP 入口，便于 Codex、Claude Code、Cursor 等 agent 查询；
- MCP server 不应拥有独立事实；它应读取 LDVH Git 文件事实源并通过受控命令写回；
- 插件或环境入口应声明权限、可写范围、Human Gate 和验证要求；
- 模型配置应区分主执行、研究、回退等角色，但这属于运行时策略，不属于事实模型字段。

### 不应吸收的内容

| 不吸收项 | 原因 | LDVH 替代做法 |
|---|---|---|
| 外部 `.taskmaster` 目录作为并列事实源 | 会与 `ldvh-base/` 和 specs 形成第二套真相 | 只吸收任务图设计，事实仍写入 LDVH 工作对象 |
| AI 自动 PRD 拆解后直接创建 active WorkCase | 容易把模型建议误当 Human 确认计划 | 先生成候选清单，经 Human Gate 或行动编排确认后入库 |
| Task Master AI 状态机直接覆盖 WorkCase | 两者对象定位不同，状态含义不同 | 只映射“阻塞、可行动、完成候选”等派生概念 |
| 插件运行记录替代验证证据 | 任务完成不等于测试通过或规格满足 | WorkCase 关闭仍需验证命令、结果和边界说明 |
| Provider/API key 配置进入事实模型 | 属于运行时环境与安全配置 | 放在运行时扩展或本地环境适配，不写入 Study/WorkCase |
| 直接复制源码或插件包 | 许可证为 MIT WITH Commons-Clause，商业/分发边界需审查 | 优先吸收模式；如需代码复用，先走 ADR/法务或许可评估 |

## 建议

1. 把 Task Master AI 作为“AI 任务编排参考模型”，而不是作为 LDVH 要嵌入的第三方任务事实源。
2. 为 WorkCase 研究依赖关系、阻塞条件、子任务/拆分和下一可行动项派生视图；这是最值得吸收的核心能力。
3. 设计 LDVH 自己的 next-action selector：输入是 WorkCase/Spark/Study/ADR/Pitfall 的 Git 文件事实源，输出只是派生建议。
4. 将复杂度分析吸收为“拆分建议”和“执行风险提示”，不作为状态流转的自动依据。
5. 参考 Task Master AI 的 CLI/MCP 双入口，为 LDVH 运行时扩展设计 agent-facing 查询工具，但所有写入必须经过 LDVH 受控命令、验证和 Human Gate。
6. Web 侧优先吸收依赖图、阻塞链、下一可行动项、验证入口和 AI 建议/事实区分，而不是复制 Task Master AI 的任务列表格式。
7. 若后续考虑安装或集成 Task Master AI，应先明确它只服务研究或临时辅助，不得把 `.taskmaster` 输出作为 LDVH 稳定事实源。
8. 许可证和版本变化需要单独门禁：当前确认的 npm 最新版本为 `0.43.1`，许可证显示为 `MIT WITH Commons-Clause`，直接复制代码、bundle 或规则文本前必须再核对。

残留不确定性：

- 官方文档和 npm 包迭代快，具体命令参数、支持模型列表、插件安装细节可能在后续版本变化。
- 本报告没有运行实际 CLI/MCP，也没有验证每个 MCP tool 的参数 schema；后续如果要落地 MCP adapter，应单独形成技术 WorkCase。
- 本报告没有把 Task Master AI 与 CodebaseMemory、Firecrawl 做横向优劣比较；这是 Human 明确要求的非目标。

## 后续分流

- **Spark**：`spark-0039` 继续作为三个插件/工具研究的总入口；本 Study 只回填 Task Master AI 单项结论，不做最终总汇总。
- **WorkCase 候选**：研究 WorkCase 依赖图、阻塞链和 next-action selector，输入必须来自 LDVH 事实源，输出只能是派生建议。
- **WorkCase 候选**：研究 AI 从 Spark/Study/docs 提取候选 WorkCase 的受控流程，要求 Human Gate 区分“候选建议”和“active 工作项”。
- **ADR 候选**：若要为 LDVH 提供 MCP server 或 agent-facing runtime adapter，应决策其权限、写入边界、事实源读取方式和环境适配策略。
- **Pitfall 候选**：记录“把外部任务管理状态当作完成证据”的风险，尤其是任务 `done` 与验证通过、规格满足、Human Gate 完成之间的差异。
- **docs 候选**：整理第三方 AI coding 工具调研来源表，记录 Task Master AI 的仓库、npm、文档、插件和许可证入口。
- **Code 候选**：增加依赖图存在性、循环依赖、阻塞状态、下一可行动项和验证入口完整性的 validator 或诊断脚本。
- **Web 候选**：增加 WorkCase 关系图、阻塞链、下一可行动项和 AI 建议/事实确认的视觉区分。

本 Study 的结论只作为吸收建议。任何正式规则、状态字段、工具入口、MCP adapter 或 Web 功能，都应进入对应 specs、ADR、WorkCase、Code、Web 或运行时扩展事实源后才生效。
