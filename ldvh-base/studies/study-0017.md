---
title: Kiro 与 Beads 对照 H1–H6 Human 价值标准调研
status: active
urls:
- ref: https://kiro.dev/
  title: Kiro 官方网站
  summary: 用于确认 Kiro 的自我定位（agentic engineering、prompt 转可执行 spec、正确性验证）；属于产品自述，只能证明其宣称的设计意图，不能证明实际效果。
- ref: https://effloow.com/articles/aws-kiro-spec-driven-development-ide-scout-2026
  title: AWS Kiro — Spec-Driven Development IDE Scout 2026
  summary: 用于确认 Kiro 基于 Code OSS、预览与 GA 时间线、Q Developer 替代关系与停用日程、spec 三文件工作流、MCP Powers；属于第三方综述，发布数字与日程未经独立复核。
- ref: https://byteiota.com/aws-kiro-the-spec-driven-ide-that-plans-before-it-codes/
  title: AWS Kiro — The Spec-Driven IDE That Plans Before It Codes
  summary: 用于确认 EARS 需求语法示例、steering files 跨界面共享、spec 前置不可跳过的工作流；其中"2026-05-07 国际发布"说法与 effloow 的"2025-07 预览、2025-11 GA"存在时间线冲突，本报告按冲突处理不采信单一来源。
- ref: https://felipefontoura.com/articles/what-is-kiro/
  title: What Is Kiro — AWS's Agentic IDE for Spec-Driven Development
  summary: 用于确认 requirements.md/design.md/tasks.md 三文件加人工审批门、属性化测试、免费与付费额度；作者自述未在生产规模使用 Kiro，属于深度文档研究而非实测。
- ref: https://www.softwareseni.com/aws-kiro-amazons-spec-first-bet-on-agentic-development/
  title: AWS Kiro — Amazon's Spec-First Bet on Agentic Development
  summary: 用于交叉确认 Agent Hooks 与 GitHub Actions 的层次区分、自动模型路由、EARS 的作用；同样存在发布日期表述差异，仅作机制层面的佐证。
- ref: https://github.com/gastownhall/beads
  title: gastownhall/beads — A memory upgrade for your coding agent
  summary: 用于确认 Beads 当前定位（分布式图 issue tracker、Dolt 驱动）、bd create/ready/claim/close 工作流、bd remember、AGENTS.md 集成方式；这是当前维护方的一手 README，为最高权重来源。
- ref: https://ianbull.com/posts/beads/
  title: Beads — Memory for your Agent（Ian Bull）
  summary: 用于确认 Beads 由 Steve Yegge 创建、解决"50 First Dates"失忆问题、SQLite+JSONL 双存储架构、daemon 自动同步、hash ID 防冲突、多 agent worktree 协作模式；为第三方实践综述。
- ref: https://betterstack.com/community/guides/ai/beads-issue-tracker-ai-agents/
  title: A Git-Friendly Issue Tracker for AI Coding Agents（Better Stack）
  summary: 用于确认上下文窗口问题动机、四种依赖类型、Web UI、Jira 双向同步、bd compact 语义化"记忆衰减"机制；为第三方教程，架构描述与一手 README 的 Dolt 表述存在版本差异。
- ref: https://www.linuxlinks.com/beads-distributed-git-backed-graph-issue-tracker-ai-agents/
  title: Beads — distributed, git-backed graph issue tracker for AI agents
  summary: 用于交叉确认 Git-as-database、agent 优化 JSON 输出、hash ID、compaction 特性清单与 MIT 许可；为简介性质，不提供独立证据。
- ref: https://aitoolly.com/ai-news/article/2026-04-29-beads-the-dolt-powered-memory-upgrade-and-distributed-graph-issue-tracker-for-ai-programming-agents
  title: Beads — The Dolt-Powered Memory Upgrade（AIToolly）
  summary: 用于确认 Beads 从 steveyegge 原版（SQLite+JSONL）演进为 gastownhall 维护的 Dolt 驱动版本这一实现变迁；该来源为新闻分析，版本细节以 GitHub README 为准。
relations:
- relation_key: inspired-by
  target:
    governed_project_id: ldvh
    fact_type_key: spark
    object_id: spark-0037
- relation_key: informs
  target:
    governed_project_id: ldvh
    fact_type_key: spark
    object_id: spark-0037
research_intent: spark-0037 已确立 H1–H6 Human 价值评判标准，并将据此对 00 根规范做整体性重梳理。Human 在讨论中点名 Kiro 与 Beads 是"最接近"的两个外部项目——Kiro 强在 H2/H4 但按特性组织、无全项目方向锚定，Beads 是 H1/H6 近邻但把人当 agent 记忆的旁观者。本轮研究要把这一判断从对话印象升级为可复读的外部参照：核实两个项目的真实机制，逐项对照 H1–H6，为 00 重梳理提供 H2（决定依据完备）所要求的外部最佳实践依据，并检验六项标准的覆盖性与辨识度。
research_question: Kiro（AWS 的 spec-driven agentic IDE）与 Beads（git-backed 的 agent 记忆与图结构 issue tracker）各自的实际机制是什么？以 LDVH 的 H1–H6 Human 价值评判标准逐项衡量，两者分别满足了什么、缺失什么？两者共同留下的空白对 LDVH 的差异化定位和 00 根规范重梳理意味着什么？
abstract: 在 2026-07-29 对 Kiro 官网与四篇第三方综述、Beads 当前维护方 README 与三篇第三方实践资料的检查中：Kiro 把"spec 是事实源、代码是构建产物"落成 requirements/design/tasks 三文件加人工审批门的强制工作流，配合 steering files、EARS 需求语法与 Agent Hooks，在 H2（决定依据完备）与 H4（人机理解对齐）上确有机制，但其组织单位是单个 feature，不存在全项目级方向锚（H5 缺位），Human 只在 spec 审批点出现。Beads 以 git 为同步层、以依赖图组织 issue，bd ready 给出无阻塞工作、hash ID 防多 agent 冲突、discovered-from 捕获顺路发现、compaction 做记忆衰减，在 H1（项目认知接续）与 H6（提及事项闭环）上是真正的近邻，但其世界观中 issue 由 agent 创建、认领、关闭，Human 是旁观者，H2–H5 全面缺位。两者的共同空白——Human 作为项目认知主体的位置——正是 spark-0037 识别出的 LDVH 差异化定位，H1–H6 六项标准在外部对照中未发现冗余或漏项。
recommendation_summary: 不采用 Kiro 或 Beads 本身，也不照搬其机制为 LDVH 规则；本研究的主要价值是作为 00 根规范重梳理的外部参照输入。建议在重梳理 spark-0037 时引用本对照结论：Kiro 证明"形式化契约+审批门"只能做到 feature 粒度的对齐，H5 需要独立的全项目方向锚机制；Beads 证明"结构化持久记忆"可以不以 Human 为中心，LDVH 的事实对象体系必须把 Human 的决定位、认知接续与方向锚定写进设计目标而非交由 agent 自治。若未来 WorkCase/Spark 依赖组织或"顺路发现"捕获出现真实痛点，可再开一轮针对 Beads discovered-from 与 compaction 细节的专题研究。
object_id: study-0017
fact_type_key: study
created_at: '2026-07-29T12:40:00.000000+08:00'
updated_at: '2026-07-29T12:40:00.000000+08:00'
---

## 研究问题

本报告围绕两个外部项目回答一组边界一致的问题：

1. Kiro 的实际机制是什么：它如何把"spec 驱动"从理念落成不可跳过的开发工作流，其组织粒度和 Human 参与点在哪里；
2. Beads 的实际机制是什么：它如何用 git 和依赖图解决 agent 跨会话记忆与长程任务连续性；
3. 以 LDVH 已确立的 H1–H6 Human 价值评判标准（见 spark-0037）逐项衡量，两者分别满足什么、缺失什么；
4. 两者共同留下的空白，对 LDVH 正在进行的 00 根规范 Human 价值重梳理意味着什么。

本报告与既有研究的分工：study-0011 讨论 Vibe Coding 从 demo 到产品级的广义工程闭环，study-0014 讨论 agent 输出组织，study-0016 研究一个具体技能库的行为契约机制；本报告是唯一以 H1–H6 为度量框架、以"Human 在 agent 工具中的位置"为比较轴的外部对照研究。

## 输入与边界

### 实际输入

观察时点为 2026-07-29（Asia/Shanghai）。本轮未安装或运行任一产品，输入全部为当次实际检索读取的文字资料：

- Kiro 侧：官方网站（产品自述定位），effloow、byteiota、felipefontoura、softwareseni 四篇第三方综述（机制描述、时间线、EARS 示例、steering/hooks 说明、定价与 Q Developer 替代日程）；
- Beads 侧：当前维护方 gastownhall/beads 的 GitHub README（一手，最高权重），ianbull、betterstack、linuxlinks 三篇第三方实践资料（创建背景、双存储架构、依赖类型、compaction），aitoolly 一篇版本变迁分析；
- 度量框架：spark-0037 中 Human 已确认的 H1–H6 标准原文（判断问题与不满足时的表现）。

### 未覆盖与限制

- 未实际安装 Kiro IDE/CLI 或运行 Beads CLI，所有机制描述来自文档与第三方转述，未做端到端行为复验；
- Kiro 发布时间在来源间存在冲突（"2025-07 预览、2025-11 GA"与"2026-05-07 国际发布"两种表述并存），本报告只采信各来源一致的部分（spec 工作流、steering、hooks、EARS），时间线细节不作为结论依据；
- Beads 存在实现变迁：steveyegge 原版为 SQLite+JSONL 双存储，当前 gastownhall 维护版以 Dolt 为引擎；不同第三方资料反映不同版本，本报告以当前 README 为准并显式标注该差异；
- 采用数字（如预览期 25 万开发者、GitHub star 数）为来源自述快照，未经独立核实，不作为质量证据；
- 两个项目均在快速演进，本报告结论只在其所述机制层面有效，后续版本可能改变对照结果；消费前应按时效规则重读一手来源。

## 关键发现

### 1. Kiro 把"spec 是事实源、代码是构建产物"落成了强制的 feature 粒度工作流

Kiro 是 AWS 基于 Code OSS（VS Code 开源底座）构建的 agentic IDE，为 Amazon Q Developer 的继任者。其不可跳过的流程是：prompt → requirements.md（EARS 形式化语法，WHEN/THE SYSTEM SHALL 句式）→ design.md → tasks.md，每段之间有人工审批门，之后由 agent 实现并可用属性化测试对照 spec 验证。配套机制包括 steering files（项目约定、编码标准、架构模式的 markdown，跨 IDE/CLI/Web 共享同一上下文）与 Agent Hooks（文件保存等本地事件触发的自动化）。

以 H1–H6 衡量：requirements/design/tasks 三文件使"为什么这么做"成为可回读的仓库工件，直接支撑 H2（决定依据完备）；审批门、EARS 消歧与 steering 共享上下文是实在的 H4（人机理解对齐）机制。Kiro 是本轮对照中唯一在 H2/H4 上有结构性设计的外部产品。

对后续项目工作的直接影响：这是对 spark-0037"规范源本身是最大的对齐工具"判断的外部印证——Kiro 独立得出了同一结论并以 steering files 实现。它可作为 00 重梳理中论证 H4 机制设计的外部参照；不需要创建新对象。

### 2. Kiro 的组织单位是单个 feature，不存在全项目方向锚

每个 Kiro spec 是一个独立的三文件包：有自己的需求、设计、任务和审批门，spec 之间没有共享的方向层——没有工件表达"整个项目要往哪走"、各 feature 的相对优先级与演进路线、以及"当前 work 是否仍在既定方向上"的对照面。steering files 承载的是"怎么写代码"的约定，不是"为什么做这些事"的方向。Human 在 Kiro 中的出现点是 feature 级 spec 的审批，而不是项目方向的设定与校准。

以 H1–H6 衡量：H5（项目方向锚定）完全缺位——长期意图无处锚定，模糊目标没有借助项目积累浮现和澄清的位置；H1（项目认知接续）只有"过去"的碎片——单个 feature 的 spec 可回溯，但项目整体的演进、现状与未来方向无认知接续工具。这正是 Human 所说的"按特性组织、无全项目方向锚定"。

对后续项目工作的直接影响：为 00 重梳理提供了反向参照——即使把 H2/H4 做到 Kiro 的程度，H5 也不会自动成立；方向锚必须是独立设计的机制，不能指望从 feature 级契约中涌现。该结论应在重梳理时明确写入 H5 的设计论证。

### 3. Beads 用 git 同步的依赖图解决了 agent 跨会话记忆，是 H1/H6 的真正近邻

Beads（CLI 为 `bd`）由 Steve Yegge 创建，现由 gastownhall 维护，定位是"coding agent 的记忆升级"。核心机制：issue 构成依赖图，依赖类型含 blocks、relates_to、parent-child、discovered-from 四种；`bd ready --json` 返回所有无阻塞的可执行任务，agent 每次会话开始只需这一问；hash 型 ID（bd-a3f2）使多 agent 并发创建不产生冲突；存储以 git 为同步层（早期版本为 SQLite 本地缓存加 git 追踪的 issues.jsonl，当前版本由 Dolt 驱动）；`bd compact` 用 LLM 把陈年已关闭 issue 压缩成摘要，实现"记忆衰减"。它明确针对 Yegge 所说的"50 First Dates"问题——agent 每天醒来不记得昨天的工作。

以 H1–H6 衡量：跨会话、跨机器、多 agent 共享的结构化持久记忆直接支撑 H1（项目认知接续）；discovered-from 依赖类型专门捕获"做 A 时顺路发现 B"这类最容易丢失的事项，`bd remember` 提供持久项目记忆入口，这是 H6（提及事项闭环）的实质机制。在全部外部对照对象中，Beads 是 H1/H6 上机制最完整的。

对后续项目工作的直接影响：Beads 的四种依赖类型与 compaction 是 LDVH WorkCase/Spark 组织可参照的候选机制，但 LDVH 事实对象已有 relations 字段、状态机与生命周期规范，不能照搬；本发现只作为 spark-0037 论证 H1/H6 外部可达性的参照，不创建新对象。

### 4. Beads 的世界观里 Human 是旁观者，H2–H5 全面缺位

Beads 的标准工作流是：agent 创建 issue、agent 认领（--claim）、agent 关闭；`bd ready` 回答的是"agent 下一步做什么"，不是"Human 需要决定什么"。其多 agent 协作设想（worktree 分工、配合 Agent Mail 让 agent 群自行协调）进一步把人的角色边缘化——典型用法描述是"你给它们一个任务，让它们自己商量着解决"。整个设计中：没有 Human 决定位与决定依据的呈现（H2 缺位）；没有打断节制与优先级组织的概念（H3 缺位）；没有人机理解对齐机制——记忆服务的是 agent 自己的连续性，对齐无从谈起（H4 缺位）；方向由 agent 在 issue 图中自行展开，无 Human 锚定点（H5 缺位）。

这不是 Beads 的缺陷——它的目标用户就是 agent。但它精确展示了 Human 所说的"把人当 agent 记忆的旁观者"：持久记忆与 Human 中心是两件独立的事，前者做好了后者可以完全不存在。

对后续项目工作的直接影响：这是 LDVH 差异化定位的最清晰反证——"结构化持久记忆"不构成 Human 价值，LDVH 的事实对象体系必须把 Human 的决定位（Human Gate）、认知接续（F2 候选、演进视图）与方向锚定写成显式设计目标。该论证可直接用于 00 重梳理 §1 最终目标与 H 表的设计说明。

### 5. H1–H6 对照总表：两者的共同空白正是 LDVH 的定位

| 标准 | Kiro | Beads | LDVH 现状对应 |
|---|---|---|---|
| H1 项目认知接续 | 部分（feature spec 可回溯，无全项目认知面） | 强（但服务对象是 agent） | 事实对象 + F2 候选 + 演进视图 |
| H2 决定依据完备 | 较强（spec 三文件作为决定依据） | 缺位 | specs/ADR/Study + 本报告即实例 |
| H3 决定负担有界 | 部分（审批门有节制但无优先级组织） | 缺位 | Human Gate + 优先级体系 |
| H4 人机理解对齐 | 较强（审批门、EARS、steering） | 缺位 | 规范源 + Human Gate + 交还复核 |
| H5 项目方向锚定 | 缺位（feature 粒度，无方向层） | 缺位（agent 自治展开） | spark-0037 待重梳理确立 |
| H6 提及事项闭环 | 弱（hooks 捕获动作，不捕获事项） | 强（discovered-from、bd remember） | Spark 池 + 关系与处置 |

两个机制成熟、方向各异的项目，恰好在 H 表的两侧各自走强，又恰好共同留下同一块空白：Human 作为项目认知主体的位置。这为 H1–H6 提供了一个有价值的外部检验——六项标准没有冗余（每项都有"只满足它而不满足其他"的真实产品形态），也没有明显漏项（两个代表产品的所有 Human 相关机制都能落入六项之一）。

对后续项目工作的直接影响：本对照表应作为 spark-0037 重梳理 00 §6（H 表与 V 表同章）时的引用材料；同时支持"不重开标准修订、直接进入重梳理"的判断。若 Human 认为对照表揭示了新维度（例如"agent 间协作"是否值得单列），才需要回到 Spark 层讨论。

### 6. 可分离吸收的候选机制及其边界

Kiro 侧：EARS 式"WHEN 条件 / THE SYSTEM SHALL 行为"可作为行动模板与验收条件的写法参照；steering files 的"约定单一来源、多界面共享"与 LDVH 规范源的多消费面设计同构，可互为印证；Agent Hooks 的事件触发自动化与 LDVH 环境 Hook 的边界（薄引用、不冒充核心能力）原则一致。Beads 侧：`bd ready` 式"无阻塞工作"查询、discovered-from 捕获、compaction 记忆衰减是三个可分离思想。

吸收边界：这些都是机制思想，不是可直接移植的工件。LDVH 的验收条件、事实关系、生命周期已有正式来源；任何吸收都必须经相应来源准入，外部产品的价值判断不能凭本报告直接成为规则。

对后续项目工作的直接影响：当前无需对象化；仅当未来某 WorkCase 确实涉及依赖组织、验收写法或记忆衰减设计时，回本报告取相应机制作为候选输入。

### 7. 来源冲突与时效注意事项

两处需要消费时留意的来源状态：其一，Kiro 发布与 Q Developer 替代的时间线在第三方来源间不一致，本报告所有结论不依赖具体时间线；其二，Beads 的存储实现经历 SQLite+JSONL 到 Dolt 的变迁，第三方教程多描述旧架构，引用架构细节时以 gastownhall/beads README 为准。两项目演进都快，本报告的机制层结论（工作流结构、Human 角色）比细节层结论（命令清单、定价、日程）更耐久。

对后续项目工作的直接影响：召回本报告时只需重核机制层结论是否仍与一手来源一致；若任一项目推出"全项目方向层"或"Human 决定位"类功能（这将直接冲击本报告核心结论），应新建 Study 重新研究而非原地修订。

## 建议

### 建议一：将本对照作为 spark-0037 重梳理的外部参照输入

- 目标对象类型：更新 spark-0037（或在 Human 启动 00 重梳理时建立的 WorkCase 中引用本 Study）。
- 预期目标：把"Kiro 证明 feature 粒度契约不产生方向锚""Beads 证明 agent 记忆不以 Human 为中心"两条外部论证纳入 H4/H5 机制设计与 §1 最终目标的说明，使 H 表的设计依据同时包含内部推演与外部对照。
- 验收条件：重梳理相关段落引用本 Study 时保持其输入边界（2026-07-29 观察时点、未经实测）；不借外部产品论证任何本报告未覆盖的 H 标准结论。
- 创建/更新判断：是否更新 spark-0037 摘要由 Human 在重梳理节奏中决定；本 Study 的 informs 关系已声明该影响方向，不暗示已被采纳。

### 建议二：不采用 Kiro 或 Beads 本身，当前无需任何实施类对象

- 目标对象类型：无需对象化。
- 判断依据：LDVH 已有自己的规范源、事实对象、Human Gate 与生命周期体系，两个外部产品解决的问题（feature 契约、agent 记忆）在 LDVH 中由不同机制承担；引入任一产品都会制造第二权威与规则冲突。
- 后续监测条件：若未来出现真实的 agent 间并发协作需求（Beads 的 hash ID、依赖图可直接复用）或 Human 明确希望试用 spec 三文件工作流，再建立相应 WorkCase 评估。

### 建议三：H5 方向锚机制设计时，把"Kiro 缺什么"作为反例清单

- 目标对象类型：00 重梳理中涉及 H5 的段落修改（走 spark-0037 既定的逐段确认流程，不单独建对象）。
- 预期目标：方向锚设计显式回答 Kiro 未能回答的问题——长期意图锚定在什么稳定事实上、模糊目标如何借助项目积累浮现并经 Human 明确、如何对照锚点判断方向漂移。
- 验收条件：H5 机制不依赖任何 feature 级工件的涌现，有独立的锚点载体与对照方式。
- 创建/更新判断：随 00 重梳理整体流程进行；若重梳理暂不覆盖 H5 机制细节，本建议保留在本 Study 中待引用。

## 后续分流

| 分流类别 | 触发信号 | 下一步 | 继续无需对象化的条件 |
|---|---|---|---|
| Spark 更新：spark-0037 引用本对照 | Human 启动 00 重梳理并确认需要外部参照 | 在 spark-0037 摘要或重梳理 WorkCase 中引用本 Study 的对照表与两条反证 | 重梳理尚未启动，或 Human 判断不需要外部参照 |
| 新建 Study：Beads discovered-from 与 compaction 专题 | WorkCase/Spark 依赖组织或"顺路发现"捕获出现真实痛点 | 安装 Beads 实测四种依赖类型、bd ready 语义与 compact 行为，形成专题研究 | 无对应痛点，机制思想保留在本报告中已足够 |
| 新建 Study：Kiro steering/spec 工作流实测 | Human 希望评估 spec 三文件工作流对 LDVH 验收写法的价值 | 固定版本实测 Kiro CLI，检验 EARS 与审批门的实际约束力 | 无采用或深度评估意图 |
| 重新研究本对象 | Kiro 推出全项目方向层，或 Beads 引入 Human 决定位 | 新建 Study 重新研究，本对象按规范退役 | 未观察到冲击核心结论的产品演进 |
| 无需对象化 | 仅为理解两个外部项目或支持重梳理论证 | 保留本 Study，消费时按时效规则重核一手来源 | 结论仅用于参照，未转化为实施需求 |
