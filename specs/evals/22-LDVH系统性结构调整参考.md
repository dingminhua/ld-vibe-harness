# LDVH 系统性结构调整参考

> 创建日期：2026-06-04
> 定位：LD Vibe Harness 系统性结构调整的项目级内部参考文档
> 调研边界：基于当前 LDVH 规范体系、事实模型、行动模型和产品化方向进行结构诊断，不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-LDVH目录说明.md`、`specs/03-Specs文档规范.md`、`specs/13-LDVH事实模型基础规范.md`、`specs/14-LDVH工作流基础规范.md`、`specs/20-事实模型集合索引.md`、`specs/50-行动模型集合索引.md`

---

## 1. 本文解决的问题

本文用于承接“了解 LDVH 后进行系统性结构调整”的讨论起点，先形成一份可逐步讨论、可逐步落地的参考文档。

本文不直接修改正式规范，不直接创建新的事实模型或行动模型，也不改变既有状态机、Human Gate、事实源边界或 Tools 行为。本文的作用是把当前 LDVH 的结构问题、调整方向、分层原则和落地顺序先放在一个非强制参考位置，方便后续逐项讨论、验证和回流。

本文重点覆盖四个方面：

1. 规范结构：specs 编号、主文档、子文档、Rules、Skill、Agent、Tools、Web、Contract 的层级和边界；
2. 事实模型：Intent、Task、ADR、Memo、Profile、Pitfall、Change 及已删除或降级对象的关系；
3. 行动流程：Core Loop、行动模型、Skill 入口、Human Gate、Verify、Record、Learn 的执行链路；
4. 工具产品：PyTools、校验器、Web 只读入口、Contract 消费路线和产品化边界。

本文的讨论目标不是一次性重构全部体系，而是形成一个“先诊断、再分流、再小步落地、再 Dogfood”的结构调整路径。

---

## 2. 结论

LDVH 当前最适合做的系统性结构调整，不是新增更多对象或一次性重排所有规范，而是围绕"五类构成要素"和 Core Loop 建立更清晰的层级边界：正式规范稳定定义规则，evals 承载讨论和方向，事实模型承载项目事实，工作流承载 AI 行动控制，Tools 和 Web 只消费和辅助事实源，不成为新的权威状态。

短期调整应优先服务最近一次可运行闭环：

```text
共识/需求 → ldvh-intake → Intent/Task → 执行 → ldvh-close → Change → 复盘
```

因此，后续落地应优先处理以下结构问题：

1. 规范体系是否能让 AI 快速定位入口，而不是在 specs、Rules、Skill、evals、refs 之间迷路；
2. 事实模型是否保持最小稳定对象集，避免重新引入 TaskSet、Evidence、Risk、Dependency 等过早独立对象；
3. 工作流是否能补齐 Plan、Execute、Verify、Record、Learn 的最小入口，而不是一次性扩张大量 Skill；
4. Tools 是否逐步从硬编码校验转向 Contract 消费；
5. Web 是否保持只读态势入口优先，暂不扩大写入能力。

---

## 3. 当前结构基线

### 3.1 五类构成要素

LDVH 当前顶层结构由五类构成要素共同支撑：介质、开发环境机制、工具、事实模型和工作流。

这五类不应被整理成单一上下层级。它们性质不同、职责不同，但共同服务 AI 工程驾驭闭环：

| 构成要素 | 当前承载 | 结构调整时的判断原则 |
|---|---|---|
| 介质 | Markdown、YAML、Python、JavaScript | 只定义使用要求，不重新定义介质本身 |
| 开发环境机制 | Rules、Skill、Agent、AskUserQuestion 等 | 利用环境原生机制，不把 LDVH 写成替代平台 |
| 工具 | PyTools、Web Tools、校验器、聚合器 | 辅助读取、校验、展示和受控写入，不成为权威事实源 |
| 事实模型 | specs/20-49 与 ldvh-base/ | 承载工程生产事实、状态、关系、验收和追溯 |
| 行动模型 | specs/50-79、Rules、Skill、Agent 编排 | 控制 AI 如何读取、判断、执行、停下和回写（已更名为工作流） |

后续结构调整应优先检查某个新内容属于哪一类。若无法归类，说明该内容可能只是讨论材料、模板、临时流程或尚未成熟的产品想法。

### 3.2 文档区间基线

当前 specs 编号区间已经形成基本分工：

| 区间 | 作用 | 调整原则 |
|---|---|---|
| 00 | 理念与纲要 | 保持顶层价值标准，不承载具体对象细节 |
| 01-09 | 基础规范与环境专项 | 只放跨体系基础规则和环境机制规则 |
| 10-19 | 核心基础规范 | 承载事实源、协作、工具、事实模型、工作流等基础规则 |
| 20-49 | 事实模型规范 | 每个对象必须有准入、字段、状态、关系、回写和契约边界 |
| 50-79 | 行动模型规范 | 每个行动必须有 Context、Scenario、Gate、流程、回写和协作边界 |
| 80-99 | 保留 | 未经确认不提前占用 |
| specs/evals/ | 项目评估和内部参考 | 可讨论方向，不直接构成强制规则 |
| specs/refs/ | 外部资料引用 | 只承载外部材料，不反向引用 specs |

这意味着系统性结构调整的讨论材料应优先放在 `specs/evals/`；只有当结论稳定后，才回流到正式规范或 ADR。

### 3.3 当前对象基线

当前已落地事实模型为：ADR、Change、Pitfall、Intent、Memo、Profile、Task。

当前已删除、降级或不吸收的对象边界同样重要：

| 概念 | 当前处理 | 结构调整含义 |
|---|---|---|
| Evidence | removed | 不恢复为独立事实模型，证据由 Task 关闭证据和结果物引用承接 |
| TaskSet | removed | 不恢复为独立事实模型，Intent 承接跨任务目标和约束 |
| Risk | 字段候选 | 仅当风险需要独立生命周期、负责人、缓解计划或审计时再升级 |
| Dependency | 关系字段候选 | 优先作为 Task 关系字段，不因“阻塞”概念直接建对象 |
| Artifact | 产物路径或输出字段 | 需要版本、权限、归档或复用时再升级 |
| Checklist | Task 验收项、模板或 Skill section | 不默认独立建模 |
| Roadmap | Markdown 产品方向或阶段规划 | 不进入 YAML 事实模型优先队列 |

系统性调整不应把这些已收敛的概念重新展开，除非出现明确新准入条件。

### 3.4 当前工作流基线

当前工作流区间已有 `51-multi-role-thinking-多角色思考.md`，并为 52-60 预留了项目初始化、对话转需求、需求转任务、Task 执行、阻塞处理、Review、审计、对象创建和状态更新等工作流。

当前实际 Core Loop Skill 已有入口包括：

1. `ldvh-intake`：承接 Intent 阶段；
2. `ldvh-close`：承接 Record / Task 关闭阶段；
3. `ldvh-commit`：承接 Change / commit 流程；
4. `ldvh-adr`：承接 ADR 读取、创建、更新和生命周期流转。

结构调整时应避免把工作流、Skill 和事实模型混为一谈。工作流定义"AI 如何行动"，事实模型定义"项目事实如何存在"。Skill 是工作流在开发环境机制中的一种落地入口，但不是工作流本身。

---

## 4. 主要结构问题

### 4.1 规范结构问题

当前规范结构的主要风险不是缺少文档，而是入口过多、职责分散、层级容易混淆。

典型表现包括：

1. AI 需要同时记住 L0、L1、L2、specs 主文档、子文档、Skill 文档和工具实现，容易遗漏真正权威位置；
2. Rules、Skill、Agent、Tools、Web、Contract 子文档既是机制落地材料，又容易被误认为主规范；
3. evals 中的方向性共识已经很有价值，但不能直接被正式规范消费；
4. refs、evals、docs、specs 根目录之间的效力差异需要更显性地体现在 AI 入口中；
5. 规范正文、机制落地关系和检查工具之间的同步压力正在增加；
6. Skill 部署在工作区顶层而非项目内，导致 Skill 变更无法被项目级 commit 追踪；
7. Skill 文档中复制了 specs 正文内容，形成两个事实源，同步压力持续增大。

建议后续讨论时优先判断：哪些入口是 AI 必须读的，哪些只是定位辅助，哪些只在变更或审计时读取。

### 4.2 事实模型问题

当前事实模型已经比早期收敛，但仍存在三个讨论点：

1. Change 以 Git commit 为权威事实源后，Task 的 `related_changes` 如何长期保持可追溯；
2. Evidence 取消后，Task 的 `closure_evidence`、验证命令和结果物路径是否足以支撑 Verify / Record；
3. Memo、Pitfall、Profile 的触发条件是否足够清晰，是否会被 AI 忽略或滥用。

这些问题不一定需要新增对象解决。更可能的方向是强化 Task、Change、Pitfall、Memo 的分流规则，并让 Tools 能发现引用缺口、状态缺口和关闭证据缺口。

### 4.3 行动流程问题

当前 Core Loop 的入口和出口已经出现，但中间环节仍不均衡：

| 阶段 | 当前状态 | 结构问题 |
|---|---|---|
| Intent | 已有 `ldvh-intake` | 准入判断基本可运行 |
| Plan | 尚未形成最小行动入口 | 复杂任务容易直接跳到 Execute |
| Execute | 由 Rules + Task 状态承接 | 状态变更先于执行依赖规则提醒 |
| Verify | 有关闭前审计要求，但入口弱 | lint/test/build、独立审计和 Evidence/closure 摘要需要统一 |
| Record | 有 `ldvh-close` 和 `ldvh-commit` | Change 与 Task 关闭的交接仍需增强 |
| Learn | 尚未形成稳定入口 | Pitfall / Memo / Rule 改进的触发条件仍偏经验化 |

后续不建议一次性创建所有生命周期 Skill，而应先补 Plan / Verify 的最小入口，再根据 Dogfood 结果判断 Learn 是否需要 Skill 化。

同时，行动流程需要明确“主控唯一调度”原则：Skill 只完成单个受控流程，流程结束后必须输出下一步建议并交还主控；需要并行、独立上下文、多角色判断或子 Agent 审计时，Skill 只能建议主控调度 Agent，不能自行调用 Agent 或链式调用下一个 Skill。

### 4.4 工具产品问题

当前 PyTools 已经能提供最小事实模型校验和 CLI 骨架，但产品化结构仍有几个关键边界：

1. Tools 应逐步消费 Contract，而不是长期依赖硬编码常量；
2. Web 当前应优先作为只读态势入口，帮助人理解项目状态、Core Loop 阶段、证据缺口和最近 Change；
3. Web 写入能力应晚于 Record / Change 闭环稳定；
4. Tools 不应调用 AI、Skill 或 Agent；
5. 自动化必须能解释依据、来源和影响范围。

因此，工具产品层的结构调整不应从“做一个完整产品”开始，而应从“让现有事实源更容易被读取、校验、展示和追溯”开始。

---

## 5. 建议调整原则

### 5.1 先分层，再改文件

任何结构调整前，先判断目标属于哪一层：

1. 正式规范变更：进入 specs 根目录和可能的 ADR；
2. 讨论和方向：进入 specs/evals/；
3. 外部资料：进入 specs/refs/；
4. 事实实例：进入 ldvh-base/；
5. 人类操作说明或报告：进入 docs/；
6. 工具实现：进入 tools/ 或 Web 实现目录；
7. 执行入口：进入 Rules、Skill 或 Agent。

如果一个变更同时跨多层，应先写清主变化属于哪一层，其余层只是同步或落地。

### 5.2 先收敛入口，再扩展能力

系统性调整不应先追求对象、Skill 或工具数量增长，而应先降低 AI 进入项目时的认知负担。

优先级应为：

1. 明确当前 Core Loop 阶段；
2. 明确应读哪些权威事实源；
3. 明确是否需要 Human Gate；
4. 明确应创建、更新或关闭哪类事实对象；
5. 明确是否需要 Tools 校验或 Web 展示；
6. 明确是否需要回写 Change、Pitfall 或 Memo。

### 5.3 先 Dogfood，再抽象

每新增一层抽象，都应安排一次实例化验证。若无法说明该抽象服务哪个已定义闭环，应暂缓。

建议把后续讨论中的每个结构调整建议都转换为以下问题：

1. 它是否帮助 AI 更快定位入口；
2. 它是否减少事实源混淆；
3. 它是否降低状态流转或 Human Gate 漏判概率；
4. 它是否让验证和关闭更可靠；
5. 它是否能在 LDVH 自身项目中立即 Dogfood。

### 5.4 先只读校验，再受控写入

工具和 Web 的能力应按以下顺序推进：

1. 只读解析；
2. 结构化聚合；
3. 校验和诊断；
4. 人类可读展示；
5. 受控写入；
6. 自动修复或批量迁移。

受控写入和自动修复必须晚于事实源边界、Human Gate、状态机和 Change 记录的稳定。

---

## 6. 建议落地路线

### 6.1 第一阶段：结构诊断

第一阶段不改正式规范，只围绕当前文件形成讨论结论。

建议产出：

1. 当前规范结构图；
2. 当前事实模型关系图；
3. 当前 Core Loop 缺口表；
4. 当前 Tools / Web 能力边界表；
5. 可落地调整项清单。

判断标准：是否能把结构问题分流为“立即改”“后续 Task”“需要 ADR”“只保留 Memo”“暂不处理”。

### 6.2 第二阶段：入口收敛

第二阶段优先调整 AI 入口，而不是重写大量规范。

候选动作：

1. 收敛 L0 / L1 / L2 的入口表达，减少重复正文；
2. 明确 specs/evals/、specs/refs/、docs/、ldvh-base/ 的读取效力；
3. 强化“先识别 Core Loop 阶段”的规则；
4. 把常见误判转为 Rules 或 Pitfall 检查项；
5. 梳理 Skill 触发条件和禁止条件。

### 6.3 第三阶段：Plan / Verify 最小入口

第三阶段围绕 Core Loop 中最弱的 Plan 和 Verify 建最小能力。

候选动作：

1. 讨论是否创建 `ldvh-plan`；
2. 讨论是否创建 `ldvh-verify`；
3. 明确 Task 从 `executing` 到 `verifying` 再到 `review_needed` 的最小证据要求；
4. 明确 lint、test、build、独立审计和人工审查的分工；
5. 将失败、阻塞和后续发现分流到 Task、Memo、Pitfall 或 ADR；
6. 为 `ldvh-plan`、`ldvh-verify`、`ldvh-close` 等生命周期 Skill 统一增加交还主控输出，明确下一步建议、建议调度对象、所需输入、预期输出和停止条件。

### 6.4 第四阶段：Contract 消费路线

第四阶段让 Tools 更稳定消费契约。

候选动作：

1. 统一 Contract 子文档可被 Tools 消费的结构；
2. 将 `check_fact_model.py` 中可迁移的硬编码规则逐步转为 Contract 消费；
3. 补 Reference Validator 和 State Machine Validator 的最小路线；
4. 让 Web 优先消费 PyTools 输出，而不是重复解析所有事实源；
5. 用测试锁定迁移前后的行为一致性。

### 6.5 第五阶段：Web 只读态势入口

第五阶段聚焦产品化但不扩大写入。

候选动作：

1. 展示当前 Intent / Task / ADR / Change / Pitfall / Memo / Profile 状态；
2. 展示 Task 关闭条件和证据缺口；
3. 展示最近 Change 和关联 Task；
4. 展示需要 Human Gate 的候选事项；
5. 展示 Tools 校验诊断结果。

Web 写入能力应在 Record / Change、状态机和 Human Gate 机制更稳定后再讨论。

---

## 7. 讨论清单

后续可以按以下问题逐步讨论落地：

1. 当前 `specs/evals/17` 是否继续作为产品方向主入口，还是需要拆出更稳定的路线图文档；
2. 当前 20-49 事实模型是否已经足够，是否存在必须新增对象的硬准入；
3. 当前 50-79 行动模型 planned 清单是否仍符合 Core Loop；
4. Plan / Verify 是优先做 Skill，还是先做行动模型规范；
5. `ldvh-close` 与 `ldvh-commit` 的交接是否需要进一步工具化；
6. Task 的关闭证据是否应增加更明确的结果物路径或验证摘要约定；
7. Pitfall、Memo、ADR 的分流规则是否需要被固化为行动模型或 Skill；
8. PyTools 的下一步是继续 CRUD，还是先做 Contract 消费；
9. Web 是否只做只读态势，还是需要 Human Gate 辅助界面；
10. 哪些结构调整必须先通过 ADR；
11. 生命周期 Skill 的交还主控输出是否应成为所有 Skill 的统一输出契约；
12. 需要子 Agent 的场景是否都应从 Skill 内部动作改为“Skill 建议、主控调度”。

---

## 8. 不建议立即做的事

为避免系统性调整变成新一轮结构膨胀，当前不建议立即做：

1. 一次性重排 specs 全部编号；
2. 恢复 TaskSet 或 Evidence 独立事实模型；
3. 把 Risk、Dependency、Artifact、Checklist、Roadmap 直接升级为事实模型；
4. 一次性创建大量生命周期 Skill 或角色 Skill；
5. 在 Tools 尚未稳定消费 Contract 前大规模增加复杂校验；
6. 在 Record / Change 未进一步稳定前扩大 Web 写入能力；
7. 把 evals 的讨论结论直接当作正式规范执行；
8. 让 Skill、Agent 或 Web 绕过 Human Gate 和事实源回写；
9. 把 `.trae/specs/` 或本地隐藏状态变成第二套权威状态；
10. 为未来可能需要的对象打断当前最小闭环。

---

## 9. 待补齐事项

1. 根据后续讨论补充一张正式的结构分层图；
2. 根据后续讨论形成第一批可执行调整项；
3. 判断哪些调整项需要 ADR；
4. 判断是否需要创建 Intent / Task 承接本轮结构调整；
5. 判断是否将部分稳定结论回流到 `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`；
6. 判断是否需要创建 Plan / Verify 相关行动模型或 Skill 草案；
7. 判断是否需要为 Tools Contract 消费创建独立 Task；
8. 判断 Web 只读态势入口是否作为下一轮 Dogfood 目标。
