---
id: study-0009
type: study
title: LDVH 从 Superpowers 吸收内容的火花式研究
status: active
created: '2026-06-20T11:50:00+08:00'
updated: '2026-06-20T11:50:00+08:00'
summary: |
  本 Study 以 spark 形式整理 LDVH 可以从 Superpowers 项目吸收的内容。核心判断是：Superpowers 最值得吸收的不是具体 Claude Code Skill 包本身，而是它对 AI 编码代理“合理化、抢跑、缺证据、跳过审查、上下文污染”的系统性约束设计。LDVH 应把这些机制转译为自身的事实源边界、验证铁律、Human Gate、WorkCase 审查、Skill/Agent/Hook 资产准入和错误反馈闭环，而不是照搬其会话级工作流或绝对 TDD 教条。
user_intent: 用户要求写一篇 spark，分析 LDVH 可以从 Superpowers 项目里吸收的内容，并通过 Study 的形式沉淀。
conclusion: |
  LDVH 应吸收 Superpowers 的七类稳定机制：验证前不得宣称完成、规则反合理化、两阶段审查、子代理上下文隔离与主控回收、TDD/测试优先的可调强度门禁、Skill 触发描述克制、以及失败次数触发架构讨论。吸收方式应是“理念转译 + LDVH 事实源落地”：规则进入 specs 或能力资产准入，执行进入 WorkCase / Skill / Hook / Code validator，报告和依据保留在 Study。不得把 Superpowers 的 Skill 文本、会话状态、无限子代理分派和绝对 TDD 例外规则直接搬入 LDVH。
urls: []
related_sparks: []
related_workcases:
- workcase-0044
- workcase-0046
- workcase-0047
- workcase-0048
- workcase-0060
- workcase-0074
- workcase-0080
related_adrs: []
related_pitfalls: []
related_docs:
- specs/04.02-LDVH能力资产与保障机制规范.md
- specs/06-行动编排基础规范.md
- specs/10-Git提交规范.md
- specs/21-WorkCase-工作项.md
- specs/20-Spark-火花.md
- specs/24-Study-研究报告.md
archive_reason: null
---

# LDVH 从 Superpowers 吸收内容的火花式研究

## 研究问题

本 spark 型 Study 回答一个收敛问题：在已有 Superpowers 深度调研基础上，LDVH 到底应该吸收什么，吸收到哪里，以及哪些内容只保留为参考。

具体问题包括：

1. Superpowers 中哪些机制对 LDVH 的治理目标最有价值；
2. 这些机制应转译为 LDVH 的规范、工作对象、能力资产还是执行流程；
3. 哪些内容与 LDVH 的事实源边界、跨会话治理和 Human Gate 设计不完全兼容；
4. 后续如果推进落地，应优先分流到哪些已有 WorkCase 或规范面。

## 输入与边界

本报告的主要输入是 `临时参考/studies/07-LDVH对Superpowers的借鉴评估与深度调研.md`。该临时研究已经覆盖 Superpowers 的 TDD 铁律、验证铁律、调试铁律、Skill 清单、Human Gate、两阶段审查、子代理驱动开发、安全护栏和反合理化体系。

本报告不重新做源码级逐文件调研，也不把 Superpowers 的原文规则搬入 LDVH。它只做二次吸收判断：从 LDVH 当前工作模型、事实源边界、能力资产登记制和 dogfood 治理需要出发，提炼可落地的稳定设计。

边界如下：

- Superpowers 是面向 AI 编码代理的软件开发方法论，LDVH 是 Vibe Coding 治理框架；二者目标重叠但不等同。
- Superpowers 的主要载体是 Claude Code Skill 和会话级纪律，LDVH 的权威事实源是 specs、`ldvh-base/` 工作对象、Code/Web 派生输出和 Git 提交记录。
- 本 Study 只提供吸收建议；任何强制规则必须进入 specs、ADR、WorkCase、Skill、Hook、Code validator 或其他正式事实源后才生效。
- 旧调研中的 GitHub Star、作者、完整 Skill 名录等背景信息不在本报告重复展开。

## 关键发现

### 一句话判断

Superpowers 对 LDVH 的最大价值，是把“AI 代理容易自我说服”的问题当作一等工程风险处理。它不是只告诉代理要谨慎，而是把谨慎拆成可触发、可审查、可回滚、可升级的工作机制。

LDVH 已经有事实源、状态机、Human Gate 和规范体系，因此不需要照搬 Superpowers 的全套 workflow。LDVH 应吸收其抗失控机制，并把这些机制放进 LDVH 自身的承载层。

### 可吸收内容矩阵

| Superpowers 机制 | LDVH 可吸收内容 | 建议承载位置 | 吸收强度 |
|---|---|---|---|
| 验证铁律 | 未有新鲜验证证据前，不得宣称完成、关闭、通过或可合并 | `specs/06`、`specs/21`、WorkCase 关闭流程、提交 Skill | 高 |
| TDD 铁律 | 高风险代码变更、修 bug、回归修复应优先测试先行；允许按项目风险分层 | `workcase-0044`、`specs/21`、测试/验证规范 | 中高 |
| 反合理化表 | 为关键禁令补充常见借口、红旗、停止条件和纠偏动作 | Rules、Skill、`specs/04.02`、`workcase-0048` | 高 |
| 两阶段审查 | 先检查“是否满足规格”，再检查“实现质量是否足够”，顺序不可倒 | WorkCase review、子 Agent 审查流程、Code review Skill | 高 |
| 子代理新鲜实例 | 用隔离上下文做研究、实现、规格审查、质量审查，主控负责合并和事实源回写 | Agent 资产准入、`specs/04.02`、多角色思考实践 | 中高 |
| Skill 触发设计 | Skill 描述只写触发条件和边界，避免把完整流程写在描述里诱导跳读 | Skill 规范、`workcase-0060` | 高 |
| 3+ 修复失败规则 | 同类问题多次修复失败时停止继续打补丁，转为根因/架构讨论 | Pitfall、Spark、WorkCase blocking、系统性调试流程 | 中高 |
| Worktree / 分支安全 | 隔离工作区、清理前确认来源、敏感丢弃需显式确认 | Git 提交规范、环境适配、提交 Skill | 中 |
| 人类伙伴定位 | Human 不是橡皮章，而是关键不确定性和高影响动作的共同决策者 | Human Gate 规则、`workcase-0046` | 中 |

### LDVH 最应该吸收的七个设计

#### 1. 验证声明分离

Superpowers 把“做完了”和“已经验证能证明做完了”严格拆开。LDVH 应将这一点变成所有关闭、提交、PR、状态流转和审查结论的基础规则。

对 LDVH 的转译：

- WorkCase 进入 `review_needed` 前，必须有新鲜验证证据；
- `closure_evidence` 不应只写“已完成”，应说明验证计划、验证命令、验证结果和结论；
- AI 不应基于子 Agent 报告、工具摘要或主观观感直接宣称成功；
- 验证失败或无法验证时，应明确降级为 blocking、follow-up、Spark、Pitfall 或 Human Gate，而不是粉饰为完成。

这与 LDVH 已有的验证字段、证据四段式和关闭审查方向高度一致，优先级应很高。

#### 2. 反合理化机制

Superpowers 的强点不是规则多，而是为规则设计“抗借口层”。例如它不仅说要 TDD，还列出“太简单不需要测试”“我会回头补测试”“这只是重构”等常见逃逸路径。

LDVH 目前的 specs 和 rules 已有很多禁止项，但部分禁止项仍偏“声明式”。后续可为高风险规则补充：

- 常见合理化借口；
- 红旗词或红旗行为；
- 触发后的停止动作；
- 允许例外的条件和 Human Gate；
- 违反后的恢复路径。

适合优先加抗合理化层的规则包括：事实源边界、不得绕过状态机、不得用 Study 替代 Spark 分流、不得用工具输出替代 Git 文件事实源、不得无验证宣称完成、不得把本地 Hook 通过当作 CI 通过。

#### 3. 两阶段审查

Superpowers 的审查顺序是：规格合规先于质量审查。这个顺序对 LDVH 很有价值，因为 LDVH 经常面对两类不同问题：

1. 做错了对象、状态、事实源或范围；
2. 范围正确，但实现质量、可维护性或体验不足。

如果把二者混在一次 review 里，AI 很容易在代码质量讨论中掩盖规格偏差。LDVH 可吸收为：

- 第一阶段：对象与规格审查，检查是否命中正确 WorkCase、specs、事实源边界、Human Gate 和验收标准；
- 第二阶段：质量审查，检查实现、文档表达、测试覆盖、Web 呈现、可维护性和残留风险；
- 第一阶段不通过时，不进入第二阶段；
- 修复后重新从第一阶段开始，而不是只补一个局部 patch。

这可以进入 WorkCase 审核流程、子 Agent 审查角色和未来的 `ldvh-close` / `ldvh-commit` 类 Skill。

#### 4. 子代理隔离与主控回收

Superpowers 的“控制器-工作者”模式可以被 LDVH 吸收，但应降低为可选能力，而不是默认无限分派。关键不是“多开多少代理”，而是：

- 子代理只拿到完成任务所需的最小上下文；
- 子代理输出必须结构化；
- 子代理不直接关闭 WorkCase、不直接写最终结论；
- 主控必须读取、合并、复核，并把稳定结论写回事实源；
- 审查子代理不信任实现子代理报告，应独立读取代码和事实源。

这与 LDVH 的能力资产登记制很契合：Agent 资产应声明角色边界、工具权限、输入输出、写权限、主控回收规则和 Human Gate。

#### 5. 测试先行的分层化，而不是绝对化

Superpowers 的 TDD 铁律非常强，适合软件实现场景。但 LDVH 不应把它无差别套到所有治理动作上。更合适的吸收方式是分层：

- 修 bug、回归问题、validator、parser、状态机、事实源迁移：强测试先行；
- Web 交互、样式、阅读体验：先定义可观察验收，再用截图、Playwright 或人工审查验证；
- 文档和规范：先写检查点、反例或审查清单，再改正文；
- 抛弃式探索和一次性分析：允许不 TDD，但不能伪装为已验证生产结论。

这样既保留 Superpowers 的纪律，又不让 LDVH 变成机械教条。

#### 6. Skill 描述克制

旧调研提到 Superpowers 的一个关键经验：如果 Skill 描述里总结了完整流程，模型可能只读描述就开始执行，跳过正文细节。

这对 LDVH 非常重要。LDVH 的 Skills、Rules 和环境入口都要处理上下文经济和渐进披露问题。建议：

- Skill description 只写触发条件、适用边界和必须读取 Skill 的理由；
- 不在 description 中放完整步骤；
- 关键流程、STOP 点、Human Gate、验证命令必须在 Skill 正文或引用规范里；
- 对高风险 Skill 做触发测试或人工压力测试，观察 AI 是否跳读正文。

该结论应进入第三方 Skill 使用规范、固定能力资产登记制和未来 LDVH 自建 Skill 模板。

#### 7. 多次失败后的架构升级

Superpowers 的 3+ 修复失败规则值得吸收。AI 代理在连续失败后容易继续局部试错，消耗上下文并扩大破坏面。LDVH 可以把它转译为：

- 同一验证失败、同一测试失败或同一审查反馈反复出现时，停止继续 patch；
- 先形成根因假设、影响范围、已尝试路径和为什么失败；
- 必要时创建 Spark、Pitfall、ADR 候选或 WorkCase blocking；
- 与 Human 讨论是否需要改架构、改规范、拆计划或降级目标。

这能强化 LDVH 的 Learn 回路，避免“越修越乱”。

### 不应照搬的内容

| 不照搬项 | 原因 | LDVH 替代做法 |
|---|---|---|
| 绝对 TDD 铁律覆盖所有动作 | LDVH 包含文档治理、研究、规范、Web 展示和流程管理，不全是生产代码 | 按风险和对象类型分层验证 |
| 会话级状态作为事实 | LDVH 强调跨会话 Git 文件事实源 | 状态进入 `ldvh-base/`、specs 或 Git commit records |
| Skill 文本直接成为规范 | LDVH 规范权威在 specs，Skill 是执行入口 | Skill 引用 specs，不复制或替代 specs |
| 子代理直接完成闭环 | LDVH 需要主控复核、Human Gate 和事实源回写 | 子代理输出只作为过程输入 |
| 连续执行优先于暂停 | LDVH 的 Human Gate 是治理纪律，不是效率损耗 | 只有非关键节点连续执行，高影响动作暂停确认 |
| 丢弃/删除类动作照搬会话口令 | LDVH 删除、归档、移动工作对象有规范化 Human Gate | 按对象规范和 Git 追溯处理 |

### 吸收后的 LDVH 目标形态

吸收 Superpowers 后，LDVH 不应变成“更严厉的提示词集合”，而应变成更可执行的治理系统：

- 规则有反合理化说明；
- 状态流转有验证证据；
- 审查分阶段；
- 子代理有边界；
- Skill 不诱导跳读；
- Hook 和 Code validator 只承担可机械检查的部分；
- Human Gate 用于高影响判断和例外授权；
- 失败能回流为 Spark、Pitfall、ADR、WorkCase 或 specs 更新。

## 建议

1. 把“验证前不得宣称完成”作为 LDVH 横切铁律，贯穿 WorkCase 关闭、提交、PR、审查和能力资产登记。
2. 为高风险规则增加反合理化层，优先覆盖事实源边界、状态机、Human Gate、验证证据和 Hook/CI 边界。
3. 将 WorkCase 审查拆成“规格合规”和“质量合规”两个阶段，并明确第一阶段不通过时不得进入第二阶段。
4. 在 Agent / subagent 资产准入中加入最小上下文、最小工具权限、结构化输出、主控回收和不得直接关闭事实源的规则。
5. TDD 采用风险分层：对代码逻辑、validator、迁移、状态机和回归 bug 强制测试优先；对研究和文档采用检查点/反例/审查清单优先。
6. 更新 Skill 写作规则：description 只做触发和边界，不写完整流程摘要；完整流程必须在正文并按需读取。
7. 增加“重复失败升级”规则：同类修复失败达到阈值时，停止继续 patch，转为根因分析、Human Gate、Spark/Pitfall/ADR 或 WorkCase blocking。

## 后续分流

- `workcase-0044`：可吸收验证铁律、测试先行分层和关闭声明规则。
- `workcase-0046`：可吸收 Superpowers 的 Human Gate 分布思路，但应保留 LDVH 自身审批语义。
- `workcase-0047`：可吸收 3+ 修复失败、根因调查和错误反馈到规则/经验的机制。
- `workcase-0048`：可吸收反合理化表和红旗清单，用于评估规则是否真的有效。
- `workcase-0060`：可吸收 Skill 描述克制、触发条件写法和压力测试思路。
- `workcase-0074`：可吸收验证前提交、完整 diff 审阅、commit 前 fresh verification 和本地/CI 分层门禁。
- `workcase-0080`：可吸收 Agent/Skill/Hook 能力资产准入规则，包括最小权限、主控回收、可观测证据和不得替代事实源。

本 Study 只作为吸收火花和研究报告。后续任何强制规则落地，都应进入对应 specs、WorkCase、ADR、Skill、Hook、Code validator 或 Git 提交记录。
