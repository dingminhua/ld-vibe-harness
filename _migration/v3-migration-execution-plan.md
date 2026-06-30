# V3 迁移执行计划

> 文件状态：temporary migration plan；本文只记录 V3 迁移执行节奏，不授权 specs、Code 行为、Action Guide 输出、Human Gate 决策、环境支持声明或事实源变更。正式规则仍以 `specs/` 正文为准。

## 1. 计划定位

本文用于回答：V2 的大量 specs、Code、Hook、外部工作流包装、事实对象和治理能力应按什么顺序进入 V3。

本文不定义新规则，不替代 `specs/00-理念与构成.md`、`specs/01-保障与衔接.md`、`specs/04-Specs基础规范.md` 或 `specs/02-AI行为规范.md`。若本文与正式 specs 冲突，以正式 specs 为准，并应更新本文或废弃对应计划项。

## 2. 总原则

大量 specs 迁移不是最后整批搬运，也不是当前一次性导入。每批迁移必须绑定一个可消费闭环：

```text
specs 迁入
  -> Code 可解析
  -> tests 覆盖
  -> Action Guide / preflight / runtime / 事实源 能消费
```

没有明确消费方的 V2 specs，应继续留在 `_migration` 作为候选证据，不进入正式 `specs/`。

迁移时只迁移 V2 能力和必要规则，不复制 V2 的目录权威、命名权威、Hook 安装方式、Skill 资产身份或派生知识地图事实层。V3 不保留 Skill 作为 LDVH 顶层机制；V2 Skill 中仍有价值的工作流能力，应进入行动模板、Action Guide、环境适配或测试。

阶段 5 之前必须先完成 V2 来源吸收清单。该清单用于判断每项 V2 specs、附件、Code、Hook registry、Skill 资产和测试在 V3 中是吸收、改名、废弃还是后置，不得跳过清单直接重写 Hook / Commit / 行动模板代码。

## 3. 阶段计划

| 阶段 | 目标 | 先迁入的 specs 能力 | Code / tests 交付 | 不做事项 |
|---|---|---|---|---|
| 0. 当前基线 | 固化 00/01/02/04 与迁移计划 | 不新增大量 specs，只稳定保障、衔接、AI 行为和 Specs 基础规则 | 现有 formal specs 测试通过 | 不迁移 Hook、行动模板、事实对象大块内容 |
| 1. Specs 解析与校验 | 让 V3 Code 能直接消费 Markdown specs | 仅补足解析所需字段、保障消费时机、AI 行为保障表 | `code/specs_validate.py`、spec parser、diagnostics、CLI、对应 tests | 不生成运行时拦截，不安装 Hook |
| 2. Action Guide / read_plan | 承接 V2 知识地图的只读导航能力 | 迁移任务导航、读取计划、停止条件、影响摘要相关规则 | Action Guide/read_plan 输出、source refs、capability gap tests | 不把派生图谱变成事实源 |
| 3. Preflight 门禁 | 写入前识别规则读取、Human Gate 和缺口分流 | 迁移写入门禁、规范变更、附件边界、Human Gate 判断相关规则 | preflight CLI、blocking/warning/follow_up diagnostics tests | 不把 Code 输出当授权或放行 |
| 4. Runtime facade | 承接消费时机和 receipt / diagnostic | 迁移 Runtime Protocol、canonical event、trigger source、receipt 边界规则 | 本地 runtime CLI、receipt 结构、事件测试 | 不声称环境已经完整支持 LDVH |
| 5. Hook / Commit / 行动模板适配 | 接入外部环境触发和可复用工作流 | 先完成 V2 吸收清单，再迁移 Git commit、Hook、行动模板和环境入口相关规则 | 吸收清单、正式 specs 候选、adapter/dispatcher、commit gate、行动模板适配 tests | 不跳过吸收清单直接重写代码；不让 Hook、外部包装或行动模板成为独立规则源 |
| 6. 事实源与事实对象 | 承接真实行动状态和长期证据 | 迁移 workcase、spark、ADR、pitfall、study 等事实对象规则 | fact validator/CLI、对象状态测试、回写边界测试 | 不直接复制 v2 `ldvh-base` 结构为权威 |
| 7. 受管项目接入 | 让 V3 判断当前工作归属和项目事实源 | 迁移项目治理、项目发现、跨项目边界规则 | governed projects 配置、项目解析、越界测试 | 不让项目索引替代事实源 |
| 8. 端到端闭环 | 用真实流程验证机制是否减少 AI 负担 | 只补缺口 specs | session start -> read plan -> preflight -> 修改 -> tests -> commit -> receipt -> closure 流程测试 | 不继续堆无消费方机制 |
| 9. 产品化与迁移层清理 | 收束 alpha/beta 边界 | 把仍有效迁移决定吸收到正式 specs/tests/docs | 清理 `_migration` 条件、用户文档、可选 Web/dashboard | 不保留 `_migration` 作为长期事实源 |

## 4. Specs 迁移节奏

大量 specs 迁移贯穿阶段 2 到阶段 7：

| 迁移批次 | 进入时机 | 进入条件 |
|---|---|---|
| Action Guide（承接 V2 知识地图导航能力）相关 specs | 阶段 2 前 | 已有 parser 能读身份、章节和保障表；有 Action Guide 输出测试 |
| preflight / Human Gate / 写入门禁相关 specs | 阶段 3 前 | 能判断目标路径、规则影响、阻断类型和缺口分流 |
| Runtime Protocol / event / receipt / diagnostic 相关 specs | 阶段 4 前 | 消费时机闭集和 diagnostic 分类已经可由 Code 校验 |
| Git commit / Hook / 行动模板适配相关 specs | 阶段 5 前 | runtime facade 和 preflight 已稳定；`_migration/stage-5-v2-absorption-checklist.md` 已区分环境入口、行动模板、Hook、commit 契约、Skill 语义转换与规则事实源 |
| 事实对象 / 项目治理相关 specs | 阶段 6-7 | 有正式事实源边界、状态机校验、受管项目解析和回写测试 |

每批 specs 进入正式 `specs/` 前，都必须留下迁移证据、Code 验证命令、测试结果和 unresolved warning 的处理去向。

## 5. 当前下一步

阶段 1-4 已完成：specs parser、Action Guide、preflight、runtime facade 均已就绪，由 `tests/code/` 覆盖。

阶段 5A 已完成：V2 内容吸收清单（`_migration/stage-5-v2-absorption-checklist.md`）、正式编号决策（`_migration/v3-formal-spec-numbering-decision.md`）和吸收索引（`_migration/v3-specs-absorption-index.md`）均已建立。`03/05/06/07/08/09` 正式基础规范已全部创建并通过 review，validator 报告 `specs: 10, diagnostics: 0`，tests 59 passed。

阶段 5B-0 已完成：术语整治落地。6 个术语决策已执行：
1. `事实源`（删"用户"前缀）；
2. `事实源边界`（删"用户事实源底层原则"）；
3. 删`最终事实源`，改用`事实源`；
4. 统一`溯源`（含 03 标题改为`事实源与Git溯源规范`）；
5. `单一事实源`退为 legacy_alias；
6. `过程证据`拆分为`过程输出`（宽义）+ `证据`（窄义），三层关系：过程输出 ⊃ 证据 ⊃ 事实源。

术语表 `04.Att.06` 已同步：新增`过程输出`、`证据`条目，新增 6 个 legacy_alias 条目（知识地图/Skill/行动编排/运行时扩展/工作模型/单一事实源）。所有 specs、code、tests、review 记录已同步。

阶段 5B-0A 已完成：规则/事实边界审计与修正。审计报告见 `_migration/5B-0A-rule-fact-boundary-audit-report.md`，发现 5 高风险 + 6 中风险 + 3 低风险混写 + 2 边界缺口，全部已修正：
- 00/03 新增"`specs/` 正文是规则源，不是事实源"边界句；
- 02 字段链统一：`必读事实源`→`必读依据`、`来源事实源`→`来源依据`、`保障需求事实源`→`保障需求规则表`、`本文作为事实源`→`本文作为规则源`；
- 04 `规则事实层`→`规则承载层`、`规范事实层`→`规范结构层`、`第二规则事实源`→`第二规则源，也不是事实源`；
- 05 `决策/经验/研究事实源`→`事实对象承载位置`；
- 术语表新增`规则源`、`来源依据`、`必读依据`条目；
- code/ldvh_specs.py 同步字段名和内部键名。

当前状态：术语整治、规则/事实边界修正以及 5B-1/2/3/4 均已完成。5B-4 完成时 validator 0 diagnostics，tests 80 passed。后续可推进 5B-5 Web 同源读取与展示边界检查。

阶段 5B 子阶段状态：

| 顺序 | 子阶段 | 目标 | 主要对象 | 验证方式 | 不做事项 |
|---|---|---|---|---|---|
| 5B-1 | `05` 事实模型优先迁移 | 已完成。增强 05 可消费结构，覆盖事实实例不得定义规则、测试夹具/迁移材料不得写成事实实例、准入 AI 负担说明、字段术语边界和成员规范后置判断条件 | `specs/05-事实模型基础规范.md`、V2 `02.Att.*` 筛选结果、`code/ldvh_specs.py`、`tests/code` | 已补 05 负例；validator 0 diagnostics；tests 63 passed | 未批量复制 Spark/WorkCase/ADR/Pitfall/Study 完整字段表或状态机 |
| 5B-2 | 附件迁移筛选与授权闭环 | 已完成。48 个 V2 附件分流记录见 `_migration/5B-2-attachment-disposition.md`；正式迁入 `03.Att.01`、`05.Att.01`、`09.Att.01` | V2 `02.Att.*`、`04.Att.*`、`05.Att.*`、`07.Att.*`、`08.Att.*`、`specs/attachments`、`tests/code` | 已补附件解析与负例；validator 0 diagnostics；tests 68 passed | 未整批搬运附件；知识地图附件废弃为 legacy_alias；Web 和成员专属附件后置 |
| 5B-3 | `03/09` 证据与验证边界专项 validator | 已完成。增强非事实源误用、过程输出回写、测试证据边界、失败阻断和验证声明字段检查 | `specs/03-事实源与Git溯源规范.md`、`specs/09-测试与验证规范.md`、`code/ldvh_specs.py`、`tests/code` | 已补 03/09 正反例；validator 0 diagnostics；tests 73 passed | 未实现 Hook、commit gate 或环境接入；未输出授权语义 |
| 5B-4 | `06` Git 提交行动模板示范 | 已完成。以 Git 提交行动作为第一个行动模板示范，验证 Context、Scenario、Gate、执行、验证、回写和交还结构；同时确认 Action Guide 取代知识地图、行动模板去 Skill 化 | `specs/06-行动模板基础规范.md`、V2 `31-git-commit-action` 迁移证据、`skills/ldvh-git-commit/SKILL.md`、commit 契约附件、Action Guide 相关 Code、`tests/code` | 已补 `validate_git_commit_action_template` 和负例测试；validator 0 diagnostics；tests 80 passed | 未安装 commit hook；未实现 commit gate；未把 commit validator 输出当授权；未恢复 Skill 顶层机制；未让模板本身定义 commit 规则 |
| 5B-5 | `08` Web 同源读取与展示边界检查 | 明确 Web 可以自行读取同一 Git 文件事实源，并校验展示、缓存、Confirm UI 和受控交互边界 | `specs/08-Web信息同步规范.md`、Web 边界 validator、`tests/code` 或后续 Web contract tests | 测试 Web 状态、缓存、按钮点击、派生视图不能替代事实源或 Human Gate；测试 source_refs/回指缺失时输出 diagnostic | 不要求 Web 必须由 Code 喂数据；不启动真实 Web 写入；不把 Confirm UI 当作 Human Gate 完成 |

5B-1 完成记录：
1. 术语整治（5B-0）已完成，事实源/事实源边界/过程输出/证据等术语已统一；
2. 规则/事实边界（5B-0A）已完成，specs 正文不再被写成事实源，05 的事实模型定位清晰；
3. 05 正式规范已增强并通过 review hash gate、validator 和 tests；
4. V2 `02.Att.*` 已完成优先筛选，字段注册结构迁入附件，成员专属字段/模板后置。

阶段 5B-2 完成记录：

1. 已能读取对应 V2 来源，并记录 source_refs；
2. 已确认父规范正文授权和 V3 归口；
3. 已识别是否涉及核心规则、行动流程或 Human Gate；
4. 已指定 Code/tests 消费方、负例测试和未迁入去向。

阶段 5B-2 已规避的 Stop Conditions：

1. 无法读取来源、无法判断 V3 归口或无法取得父规范正文授权；
2. 内容包含核心规则、行动流程或 Human Gate，但尚未进入对应正文；
3. 附件会形成第二规则源，或 Code/tests 输出反向定义规则；
4. 缺少 source_refs、验证闭环或未迁入去向。

阶段 5B 术语校正：

1. Action Guide / 行动指南是 V2 知识地图导航能力在 V3 中的升级承接，二者等价，后续应完全取代“知识地图”概念；迁移材料中出现“知识地图”时只作为历史来源名，不作为 V3 长期对象、页面或事实层。
2. 行动模板应去 Skill 化。V2 Skill 中有价值的内容只能被吸收为普通行动步骤、Action Guide 提示或外部环境包装候选；不得保留 Skill 身份、Skill registry、Skill 执行闭环或 Skill 顶层机制。
3. 旧“工作模型”术语在 V3 中应统一校正为“事实模型”。迁移材料中出现“工作模型”时只作为历史来源名，不作为 V3 长期正式概念；相关规则进入 `05` 事实模型归口。
4. Web 实现可以自行读取相关 Git 文件事实源，也可以使用 Code 输出、Git 查询或 API 聚合作为展示辅助。关键边界是 Web 与 AI/Code 同源读取、展示可回指、缓存和页面状态不成为事实源。
5. Code validator 的职责是提供只读解析、诊断和测试回归，不替代正式 specs、事实源、Human Gate 或完成声明。
6. `放行` 不作为 Code/test/runtime 的输出语义；正式表达尽量拆成方向确认、执行授权、风险接受、事实/术语确认、验收通过、暂停/驳回等具体 Human Gate 结果类型。若保留“放行”，只能指 Human 显式决定。
7. `Human Gate` 是机制名；`Human 确认`、授权、验收、风险接受、方向确认等是动作或结果类型，普通“确认”不得被泛化成授权、验收或风险接受。
8. 规则是 Specs 中的内容，事实是事实系统中的内容。后续必须先审计并校正 `00/03/04/05` 中可能把规则和事实混写的表达，再推进事实模型、附件、行动模板和 Web 深入迁移。

## 6. 停止条件

出现以下情况时，暂停迁移并回到正式 specs 或 Human Gate：

1. 计划要求与 `specs/00-理念与构成.md`、`specs/01-保障与衔接.md`、`specs/04-Specs基础规范.md` 或 `specs/02-AI行为规范.md` 冲突；
2. 新增 specs 没有明确 Code、Action Guide、preflight、runtime 或事实源消费方；
3. Code 输出被用作授权、放行、Human Gate 或事实源；
4. Hook、外部工作流包装、Rules 或项目索引开始形成第二规则源；
5. 迁移材料无法说明减少了什么 AI 负担，或无法说明事实源边界和验证方式。
