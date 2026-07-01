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
| 6. 事实源与事实对象 | 承接真实行动状态和长期证据 | 先以 WorkCase 最小成员规范验证事实对象逐篇迁移，再迁移 spark、ADR、pitfall、study 等事实对象规则 | fact validator/CLI、对象状态测试、回写边界测试 | 不直接复制 v2 `ldvh-base` 结构为权威；不在 Hook/commit gate 和 V3 正式启用前建立正式行动模板实例 |
| 7. 受管项目接入 | 让 V3 判断当前工作归属和项目事实源 | 迁移项目治理、项目发现、跨项目边界规则 | governed projects 配置、项目解析、越界测试 | 不让项目索引替代事实源 |
| 8. 端到端闭环 | 用真实流程验证机制是否减少 AI 负担 | 只补缺口 specs | session start -> read plan -> preflight -> 修改 -> tests -> commit -> receipt -> closure 流程测试 | 不继续堆无消费方机制 |
| 9. 产品化与迁移层清理 | 收束 alpha/beta 边界，让 V3 成为 soft mainline | 把仍有效迁移决定吸收到正式 specs/tests/docs，并按 9A-9F 处理剩余 V2 内容 | 迁移层依赖审计、最小提交 Hook/commit gate、事实对象完整迁移、Web 数据契约迁移、行动模板候选后置、用户文档和最终验证 | 不保留 `_migration` 作为日常规则源；不重做 Web 表现层；不把非提交行动模板作为主线切换阻断项；不启用 hard switch |

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

当前状态：术语整治、规则/事实边界修正、5B-1/2/3/4/5、阶段 6、阶段 7 和阶段 8 均已完成。阶段 6 完成范围是：Spark、WorkCase、ADR、Pitfall、Study 五个事实对象成员已进入 V3 最小成员规范，Code/tests 可消费其成员身份、状态闭集、实例事实源位置、收口/归档/分流口径和 Human Gate。阶段 7 完成范围是：V3 已建立 `LDVH-GOVERNED-PROJECTS.yaml`、`specs/10-受管项目接入规范.md`、`10.Att.01` 和 governed project parser/resolver/tests，可静态判断 target/cwd/Git common-dir 是否命中受管项目。阶段 8 完成范围是：V3 已建立只读 e2e rehearsal，把受管项目解析、session_start、read_plan acknowledgement、pre_tool_use、validation、git_commit_msg 和 completion_claim 串成静态闭环。阶段 9A-9F 已完成迁移层依赖审计、最小提交入口、事实对象完整迁移、Web 数据契约迁移、行动模板候选后置和 soft mainline 收口；阶段 10A-10G 已完成当前 worktree 的 `git.commit-msg` 最小 hard switch、manual runtime 三件套、统一 runtime adapter、环境状态检查、外部环境入口审计和 legacy Rules/Skill 顶层机制收口。当前唯一自动入口是 `git.commit-msg`；通用 Web 写入、完整 Confirm UI、非提交行动模板实例和 session/tool/completion 自动触发仍未启用。Rules / Skill 顶层机制已取消，不作为待启用入口。

阶段 9 采用 `_migration/9-v3-mainline-transition-scope.md` 的用户校正口径：

| 子项 | 状态 | 目标 | 需要 Human 参与的边界 |
|---|---|---|---|
| 9A 迁移层依赖审计 | 已完成 | 审计 `_migration` 对正式 code/tests/review gate 的剩余依赖，划分保留、吸收、删除和归档 | 删除尚未明确废弃的 V2 能力时 |
| 9B 最小提交入口 | 已完成（Hook 未启用） | 先迁 Git 提交行动、commit-msg / commit gate、read_plan 消费证据和验证声明边界 | 启用会阻断真实提交的 Hook 或 gate 时 |
| 9C 事实对象完整迁移 | 已完成 | 完整迁移 Spark、WorkCase、ADR、Pitfall、Study 字段 schema、实例路径和真实 `ldvh-base/` 实例，编号按 V3 重构 | 字段丢失、语义冲突、编号冲突或真实实例不可逆转换时 |
| 9D Web 数据契约迁移 | 已完成 | 保留既有表现层，迁入 Web tracked 资产、API 数据契约、来源回指、独立读取、Confirm UI 边界、缓存同步、Spark quick create 轻写入边界和回归测试 | Web 写入、Confirm UI 或缓存策略改变 Human 可见状态时 |
| 9E 行动模板候选后置 | 已完成 | 记录 WorkCase 创建、方案审核、执行推进、结果复核、关闭确认、Rules 同步审查和环境入口适配候选的后置理由与准入条件 | 若要求把非提交行动模板纳入主线切换阻断范围 |
| 9F 主线切换收口 | 已完成 | 用户文档、soft switch 启用边界、测试策略收口、`_migration` 保留/归档条件和最终验证 | 启用 hard switch、Hook、Rules、runtime adapter 或接受残留风险时 |

阶段 5B 子阶段状态：

| 顺序 | 子阶段 | 目标 | 主要对象 | 验证方式 | 不做事项 |
|---|---|---|---|---|---|
| 5B-1 | `05` 事实模型优先迁移 | 已完成。增强 05 可消费结构，覆盖事实实例不得定义规则、测试夹具/迁移材料不得写成事实实例、准入 AI 负担说明、字段术语边界和成员规范后置判断条件 | `specs/05-事实模型基础规范.md`、V2 `02.Att.*` 筛选结果、`code/ldvh_specs.py`、`tests/code` | 已补 05 负例；validator 0 diagnostics；tests 63 passed | 未批量复制 Spark/WorkCase/ADR/Pitfall/Study 完整字段表或状态机 |
| 5B-2 | 附件迁移筛选与授权闭环 | 已完成。48 个 V2 附件分流记录见 `_migration/5B-2-attachment-disposition.md`；正式迁入 `03.Att.01`、`05.Att.01`、`09.Att.01` | V2 `02.Att.*`、`04.Att.*`、`05.Att.*`、`07.Att.*`、`08.Att.*`、`specs/attachments`、`tests/code` | 已补附件解析与负例；validator 0 diagnostics；tests 68 passed | 未整批搬运附件；知识地图附件废弃为 legacy_alias；Web 和成员专属附件后置 |
| 5B-3 | `03/09` 证据与验证边界专项 validator | 已完成。增强非事实源误用、过程输出回写、测试证据边界、失败阻断和验证声明字段检查 | `specs/03-事实源与Git溯源规范.md`、`specs/09-测试与验证规范.md`、`code/ldvh_specs.py`、`tests/code` | 已补 03/09 正反例；validator 0 diagnostics；tests 73 passed | 未实现 Hook、commit gate 或环境接入；未输出授权语义 |
| 5B-4 | `06` Git 提交行动模板示范 | 已完成。以 Git 提交行动作为第一个行动模板示范，验证 Context、Scenario、Gate、执行、验证、回写和交还结构；同时确认 Action Guide 取代知识地图、行动模板去 Skill 化 | `specs/06-行动模板基础规范.md`、V2 `31-git-commit-action` 迁移证据、`skills/ldvh-git-commit/SKILL.md`、commit 契约附件、Action Guide 相关 Code、`tests/code` | 已补 `validate_git_commit_action_template` 和负例测试；validator 0 diagnostics；tests 80 passed | 未安装 commit hook；未实现 commit gate；未把 commit validator 输出当授权；未恢复 Skill 顶层机制；未让模板本身定义 commit 规则 |
| 5B-5 | `08` Web 同源独立读取与展示边界检查 | 已完成。明确 Web 与 Code 分开实现：Web 页面/API 自行读取同一 Git 文件事实源、正式 specs、事实对象或 Web 自有 API 聚合，Code 输出只作诊断、验证或测试对照 | `specs/08-Web信息同步规范.md`、`specs/07-Code确定性执行规范.md`、`validate_web_sync_boundaries`、`tests/code` | 已补 Web/Code 分离 validator 与负例；validator 0 diagnostics；tests 84 passed | 不要求 Web 必须由 Code 喂数据；不允许 Web 把 Code 输出/DTO/validator 内部对象作为主数据源；不启动真实 Web 写入；不把 Confirm UI 当作 Human Gate 完成 |

阶段 6A 子阶段状态：

| 顺序 | 子阶段 | 目标 | 主要对象 | 验证方式 | 不做事项 |
|---|---|---|---|---|---|
| 6A | WorkCase 最小成员规范 | 已完成。选 WorkCase 作为首个事实对象成员，迁入对象定位、准入、未来事实源位置、最小状态闭集、执行项内部边界、四层完成口径和 Human Gate | `specs/21-WorkCase-工作项.md`、`specs/05-事实模型基础规范.md`、`_migration/6A-fact-object-member-admission.md`、`code/ldvh_specs.py`、`tests/code` | 已补 `parse_workcase_member_contract`、`validate_workcase_member_contract` 和缺状态/缺事实源/缺关闭口径/缺 Human Gate/缺 legacy 状态边界负例 | 不迁入 V2 `21.Att.01` 长字段表、完整 WorkCase schema、真实实例目录、Web 写入、Hook、commit gate、runtime adapter 或正式行动模板实例 |
| 6B | 事实对象成员规范完成 | 已完成。迁入 Spark、ADR、Pitfall、Study 最小成员规范，并将 20-24 全部纳入 Code 可消费成员集合 | `specs/20-Spark-火花.md`、`specs/22-ADR-决策.md`、`specs/23-Pitfall-踩坑经验.md`、`specs/24-Study-研究报告.md`、`_migration/6B-fact-object-member-completion.md`、`code/ldvh_specs.py`、`tests/code` | 已补 `parse_fact_model_member_contracts`、`validate_fact_model_member_contracts` 和缺状态/缺事实源/缺 Human Gate/缺 legacy/缺 Study 正文骨架负例 | 不迁真实 `ldvh-base` 实例；不迁完整字段表；不迁 Web 写入；不迁 WorkCase `21.Att.01`；不建立正式行动模板实例 |
| 7 | 受管项目接入 | 已完成。迁入 V2 受管项目静态治理能力，建立 V3 配置契约、target-first resolver、Git common-dir/worktree 匹配、多 target 边界和 no-op 语义 | `LDVH-GOVERNED-PROJECTS.yaml`、`specs/10-受管项目接入规范.md`、`specs/attachments/10.Att.01-受管项目配置字段表.md`、`_migration/7-governed-project-admission.md`、`code/ldvh_specs.py`、`tests/code` | 已补配置字段闭集/重复 ID/越界字段、target-first、非受管 no-op、受管/非受管混合阻断、Git worktree common-dir 和 CLI 测试；validator 0 diagnostics | 不安装 Hook；不声明环境入口生效；不恢复知识地图；不迁真实 `ldvh-base` 实例；不建立 Web 写入 |
| 8 | 端到端闭环 | 已完成。用只读 e2e rehearsal 验证现有 V3 机制能形成静态行动闭环，并记录仍后置的真实环境边界 | `code/ldvh_specs.py`、`code/specs_validate.py`、`tests/code/test_ldvh_specs_validate.py`、`_migration/8-end-to-end-closure.md` | 已补 `build_e2e_rehearsal`、`specs_validate.py e2e`、e2e workflow/无授权语义/CLI JSON 测试；CLI 演练 diagnostics 0 | 不执行真实写入；不创建提交；不安装 Hook；不启用 commit gate；不声称环境入口生效 |

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

5B-5 完成记录：

1. `08` 已从“同源读取”收紧为“同源独立读取”，Web 页面/API 数据路径不得依赖 Code 输出、Code DTO 或 validator 内部对象；
2. `07` 已补反向边界：Code 输出可以供 AI、tests、审计或 Web 诊断展示对照使用，但不得成为 Web 页面/API 主数据源、字段契约或页面状态机；
3. `code/ldvh_specs.py` 已新增 `validate_web_sync_boundaries`，覆盖 Web/Code 分离、诊断引用边界和 Web 原生实现 source_refs 边界；
4. `tests/code` 已补 Web/Code 分离负例，最终验证为 validator 0 diagnostics，tests 84 passed。

6A 完成记录：

1. 事实对象成员准入记录见 `_migration/6A-fact-object-member-admission.md`，WorkCase 被选为首个迁移对象，Spark/ADR/Pitfall/Study 后置；
2. `specs/21-WorkCase-工作项.md` 已建立最小成员规范，只承接对象定位、事实源位置、状态闭集、关闭口径和 Human Gate；
3. `05` 已说明 WorkCase 首批迁入，但完整字段表、`orchestration` 长表、实例目录和其它成员仍后置；
4. 正式行动模板实例未建立；该工作等待 Hook / commit gate 接入与 V3 正式启用前再做，避免纸面模板与真实执行入口脱节。

6B 完成记录：

1. `specs/20-Spark-火花.md` 已建立 Spark 最小成员规范，覆盖分流前对象定位、`pending/resolved/discarded` 状态、分流/废弃口径和 Human Gate；
2. `specs/22-ADR-决策.md` 已建立 ADR 最小成员规范，覆盖长期决策、`active/archived/deprecated` 状态、规范吸收边界、legacy 状态禁用和 Human Gate；
3. `specs/23-Pitfall-踩坑经验.md` 已建立 Pitfall 最小成员规范，覆盖已解决已验证经验、`active/archived` 状态、经验吸收边界和 Human Gate；
4. `specs/24-Study-研究报告.md` 已建立 Study 最小成员规范，覆盖 Markdown frontmatter/正文事实对象、`active/archived` 状态、URL 结构边界、正文骨架和 Human Gate；
5. `21.Att.01-orchestration字段契约表` 明确不在阶段 6 迁入；后续绑定 Hook / commit gate、正式行动模板实例、真实 WorkCase 实例和 Code/tests schema 后再判断。

阶段 7 完成记录：

1. `specs/10-受管项目接入规范.md` 已定义受管项目配置契约、工作对象判定顺序、多目标/no-op 边界、事实源接入和环境未接入边界；
2. `specs/attachments/10.Att.01-受管项目配置字段表.md` 已承载配置根字段、项目字段、Git 字段和 target resolution 字段；
3. V3 根目录已新增 `LDVH-GOVERNED-PROJECTS.yaml`，登记 `ldvh-v3` 自身；
4. `code/ldvh_specs.py` 已提供 `parse_governed_projects_config`、`validate_governed_projects_config`、`resolve_governed_subject` 和 `build_governed_projects_report`；
5. `python3 code/specs_validate.py governed-projects --target-path specs/10-受管项目接入规范.md --format text --fail-on-diagnostics` 可输出当前 target 命中 `ldvh-v3`；
6. 阶段 7 只代表静态接管能力完成，不代表 Hook、commit gate、Web 写入、runtime adapter 或环境入口已经启用。

阶段 8 完成记录：

1. `code/ldvh_specs.py` 已新增 `build_e2e_rehearsal`，把受管项目解析、runtime facade、preflight、validator、git commit message 和 completion claim 聚合为只读闭环；
2. `code/specs_validate.py` 已新增 `e2e` CLI，支持 `--target-path` 输出 workflow stage、diagnostics、authorization 和 environment boundary；
3. `tests/code/test_ldvh_specs_validate.py` 已覆盖 e2e 静态 workflow、无授权语义和 CLI JSON 输出；
4. `_migration/8-end-to-end-closure.md` 已记录演练结论、交付物、验证声明和后置边界；
5. 阶段 8 验证的是静态闭环，不执行真实写入、不创建提交、不安装 Hook、不启用 commit gate、不声明 V3 正式环境接管。

9A 完成记录：

1. `_migration/9A-migration-layer-dependency-audit.md` 已记录迁移层依赖审计；
2. 稳定 `code/` 没有 import `_migration` 模块，但仍有迁移 target 分类、迁移 read_plan 和 e2e source_ref 的路径引用；
3. `tests/code/test_formal_specs.py` 仍依赖 `_migration/reviews/*-formal-review.yaml` 作为 formal review hash gate；
4. `_migration/tests` 仍依赖 `_migration/code`、fixtures、schemas、inventory 和 V2 源仓库；
5. 当前没有 tracked `_migration` 文件可安全删除，只清理未跟踪 `__pycache__`；
6. 下一步进入 9B 最小提交入口，先迁 Git 提交行动和 commit gate / Hook。

9B 完成记录：

1. `_migration/9B-minimal-commit-entry.md` 已记录最小提交入口迁移结果；
2. `code/ldvh_specs.py` 新增 `build_commit_gate`，校验 commit header、type/scope 枚举、body 必填条件、`关键变更:` 小标题和 read_plan 消费证据；
3. `code/specs_validate.py` 新增 `commit-gate` CLI；
4. `code/commit_validate.py` 新增未来 commit-msg Hook 可调用的包装器；
5. `tests/code/test_ldvh_specs_validate.py` 已覆盖 commit gate 正例、非法 scope、缺 body、缺 read_plan、CLI 和 wrapper；
6. 真实 Git Hook 未安装，`environment_integrated=false`、`hook_integrated=false`；启用 Hook 仍需 Human Gate；
7. 下一步进入 9C 事实对象完整迁移。

9C 完成记录：

1. `_migration/9C-fact-object-full-migration.md` 已记录事实对象完整迁移结果；
2. V2 39 个 Spark、21 个 WorkCase、1 个 Pitfall 和 14 个 Study 已迁入 V3 `ldvh-base/`；V3 原有 `spark-0001` 和 `workcase-0001` 保留，最终事实实例总数为 77；
3. V2 当前无 ADR 实例，V3 已建立 `ldvh-base/adrs/` 空目录和 ADR 字段 schema；
4. `code/ldvh_specs.py` 新增事实实例 layout、字段 schema、frontmatter 解析、实例校验和关系校验；
5. `tests/code/test_ldvh_specs_validate.py` 已覆盖事实实例数量、id/文件名一致性、未知字段、缺必填字段、legacy 字段、缺引用和 Study 正文骨架负例；
6. 正式 `05/20/21/22/23/24` 已同步“真实实例已迁入、字段 schema 由 Code/tests 承接、Web/Hook/行动模板仍后置”的边界；
7. 下一步进入 9F 主线切换收口。

9D 完成记录：

1. `_migration/9D-web-data-contract-migration.md` 已记录 Web 数据契约迁移结果；
2. V2 tracked `web/`、`tests/web/` 和 root `package.json` workspace 脚本已迁入 V3，生成物 `dist/`、`node_modules/` 未迁入；
3. Web facts API 保持同源独立读取，直接读取 V3 `ldvh-base/` YAML 和 Study Markdown frontmatter，不使用 Code validator 输出或 DTO 作为主数据源；
4. Web API 列表、详情和 Spark 创建响应已补 `source_refs`，`/api` 响应设置 `Cache-Control: no-store`；
5. Spark quick create 作为唯一最小轻写入保留，对齐 V3 Spark schema、回读验证并禁止 legacy 字段；
6. `tests/web` 已覆盖 facts、sparks、commit body display contract 和 project files；完整 Confirm UI、视觉回归、Hook 和通用 Web 写入继续后置。

9E 完成记录：

1. `_migration/9E-action-template-candidate-deferral.md` 已记录行动模板候选后置结论；
2. `specs/06-行动模板基础规范.md` 已补充 WorkCase 创建、方案审核、结果复核和关闭确认的后置候选边界；
3. Git 提交行动仍是当前唯一正式模板示范；
4. WorkCase 创建、方案审核、执行推进、结果复核、关闭确认、Rules 同步审查和环境入口适配均不阻断 V3 主线切换；
5. 这些候选后续必须满足来源规则、Context/Scenario/Gate、事实对象字段、Code/Web 写入或等价入口、Human Gate、测试和环境边界后，才能重新判断是否迁入正式模板。

9F 完成记录：

1. `_migration/9F-mainline-soft-switch-closure.md` 已记录 V3 soft mainline 收口结论；
2. 根 `README.md` 已更新为日常使用说明，明确 `specs/`、`ldvh-base/`、`code/`、`web/` 和 `_migration` 的当前职责；
3. V3 当前可作为日常规则和事实维护主线，但 `environment_integrated=false`、`hook_integrated=false`、`authorization=none` 仍是预期边界；
4. `_migration` 当前保留为历史审计、formal review hash gate 和迁移测试证据，不作为日常规则源或事实维护入口；
5. 测试策略开始采用 `code/test_runner.py` 的 `smoke` / `targeted` / `full` 分层入口，runner 提供阶段进度和耗时 summary；
6. hard switch、Hook / Rules / runtime adapter、完整 Confirm UI、通用 Web 写入和非提交正式行动模板仍后置，启用前必须进入 Human Gate。

10A 完成记录：

1. `_migration/10A-commit-msg-hard-switch.md` 已记录当前 worktree 的 `commit-msg` 最小 hard switch；
2. `hooks/commit-msg` 已成为 V3 tracked Hook 模板，调用 `code/commit_validate.py --hook-integrated`；
3. `code/install_git_hooks.py` 已提供 worktree-local Hook `status`、`install` 和 `uninstall`，通过 `core.hooksPath=hooks` 避免覆盖 common `.git/hooks`；
4. `code/ldvh_specs.py` 已能从提交正文 `读取依据:` 段提取 read_plan 消费路径，`specs/attachments/03.Att.01-Commit-Message契约字段表.md` 已登记该小标题；
5. 当前状态更新为 `switch_mode=commit_msg_hard_switch_minimal`、`environment_integrated=partial`、`hook_integrated=git.commit-msg`、`authorization=none`；
6. session start、pre tool use、completion claim 的自动触发、Rules、通用 Web 写入、外部受管项目 Hook adapter 和非提交正式行动模板仍后置。

10B 完成记录：

1. `_migration/10B-session-start-manual-entry.md` 已记录 `session_start` 最小可用入口和未自动接管边界；
2. `code/session_start.py` 已提供 text/json CLI，输出 P0/P1 `task_read_plan`、stdout-only runtime receipt、stop conditions、diagnostics 和 `authorization=none`；
3. 当前环境没有可安装的真实会话启动 Hook，因此 `session_start_entry=manual.session_start`、`session_start_integrated=false`；
4. `tests/code/test_ldvh_specs_validate.py` 已覆盖 session_start CLI JSON 输出、00/01/02 read_plan、manual integration scope 和 receipt 边界；
5. 下一步若继续环境接入，应进入 10C `pre_tool_use`，且不得在缺少真实工具前置拦截能力时声明自动阻断。

10C 完成记录：

1. `_migration/10C-pre-tool-use-manual-entry.md` 已记录 `pre_tool_use` 最小可用入口和未自动接管边界；
2. `code/pre_tool_use.py` 已提供 text/json CLI，输出 read_plan 消费证据检查、target preflight、required read plan、Human Gate risks、stdout-only runtime receipt 和 `authorization=none`；
3. 当前环境没有真实工具调用前置 Hook，因此 `pre_tool_use_entry=manual.pre_tool_use`、`pre_tool_use_integrated=false`；
4. 入口要求显式传入 `--acknowledged-path`，不会自动补齐 00/01/02；
5. `tests/code/test_ldvh_specs_validate.py` 已覆盖 pre_tool_use CLI JSON 正例、缺 read_plan 消费证据、缺 target 阻断和 manual integration scope；
6. 下一步若继续环境接入，应进入 10D `completion_claim` 手动入口，真实工具前置拦截仍需单独环境 adapter。

10D 完成记录：

1. `_migration/10D-completion-claim-manual-entry.md` 已记录 `completion_claim` 最小可用入口和未自动接管边界；
2. `code/completion_claim.py` 已提供 text/json CLI，输出 verification evidence、diagnostics、source refs、stdout-only runtime receipt 和 `authorization=none`；
3. 当前环境没有真实完成前 Hook，因此 `completion_claim_entry=manual.completion_claim`、`completion_claim_integrated=false`；
4. 入口要求显式传入 `--verification-evidence`，缺失时保持阻断；
5. `tests/code/test_ldvh_specs_validate.py` 已覆盖 completion_claim CLI JSON 正例、缺 verification evidence 阻断和 manual integration scope；
6. 10B-10D 已形成 manual runtime 三件套；下一步若继续推进，应评估真实 runtime adapter / 外部环境接入。

10E 完成记录：

1. `_migration/10E-runtime-adapter-feasibility.md` 已记录 runtime adapter 可行性、两类接入方式和未自动接管边界；
2. `code/runtime_adapter.py` 已提供统一 payload/CLI adapter，支持 `session-start`、`pre-tool-use` 和 `completion-claim` 三类事件转发；
3. adapter payload 至少包含 `event`、`session_id`、`target_path`、`operation`、`task`、`acknowledged_paths` 和 `verification_evidence`；
4. 当前环境仍没有真实 session/tool/completion 触发点，因此 `runtime_adapter_entry=manual.runtime_adapter`、`runtime_adapter_integrated=false`；
5. `tests/code/test_ldvh_specs_validate.py` 已覆盖三类事件转发、unknown event、缺 payload 字段和无授权语义；
6. 下一步若继续推进，应进入 10F 环境接入状态检查；没有真实触发能力时不得声明自动接管。

10F 完成记录：

1. `_migration/10F-environment-status-check.md` 已记录环境接入状态检查入口、当前 partial 接入状态和未自动接管边界；
2. `code/environment_status.py` 已提供 text/json CLI，统一报告 `git.commit-msg`、`manual.runtime_adapter`、`manual.session_start`、`manual.pre_tool_use` 和 `manual.completion_claim`；
3. 状态检查确认当前唯一 integrated 自动入口是 `git.commit-msg`，manual runtime entrypoints 仅 `available=true`、`integrated=false`；
4. 若目标 repo 未安装 V3 managed `commit-msg` Hook，状态检查返回 `ENV_COMMIT_MSG_HOOK_NOT_INSTALLED` 阻断诊断；
5. `tests/code/test_ldvh_specs_validate.py` 已覆盖已安装 Hook 的 partial 状态和缺 Hook 阻断；
6. 10G 已继续完成外部环境入口审计和 legacy Rules/Skill 顶层机制收口，用于判断是否存在真实可接入入口，并避免把已取消机制写成后置项。

10G 完成记录：

1. `_migration/10G-rules-environment-entry-audit.md` 已记录 tool hook、completion hook、Codex repo 指令、外部 runtime adapter 和 legacy Rules/Skill 顶层机制审计结论；
2. `code/environment_entry_audit.py` 已提供 text/json CLI，读取 10F 状态并扫描 `AGENTS.md`、`.codex`、`.codex-plugin` 等 repo-local 入口信号，同时把 legacy Rules/Skill 顶层机制标记为 `removed_top_level`；
3. 审计确认当前 integrated entrypoints 只有 `git.commit-msg`；
4. `runtime.session_start.auto`、`runtime.pre_tool_use.auto`、`runtime.completion_claim.auto` 和 `runtime.adapter.auto` 均为 deferred；`rules.top_level_mechanism` 和 `skills.top_level_mechanism` 均为 removed_top_level；
5. `codex.repo-instructions` 当前为 absent；即便后续出现 `AGENTS.md`，也只能先标记为 available，不得直接声明 runtime 自动接入；
6. 已删除早期骨架遗留的 `rules/.gitkeep` 和 `skills/.gitkeep`，避免误解为待启用目录；
7. 后续只有在真实触发、稳定 payload、失败处理、安装状态、回滚方式和用户同意同时满足时，才进入接入实现；否则这些入口保持后置。Rules / Skill 顶层机制不得恢复。

11A-11G 完成记录：

1. `_migration/11A-human-gate-constitutional-remediation.md` 已记录构成体系变更的 Human Gate 补救边界：不伪造早期确认，只把阶段 11 之后继续推进的 V3 基线明确下来；
2. `_migration/11B-spec-status-activation.md` 已记录 specs 和正式附件激活：正式规范正文和已迁入附件不再停留在 candidate 状态；
3. `_migration/11C-environment-adaptation-admission.md` 已记录 `specs/11-环境适配规范.md` 和 11 附件迁入，补齐 01 中悬空的环境适配归口；
4. `_migration/11D-runtime-automatic-integration-boundary.md` 已记录 runtime 自动入口审计：当前除 `git.commit-msg` 外没有可升级为 integrated 的自动入口；
5. `_migration/11E-v2-v3-capability-coverage-matrix.md` 已记录 V2 到 V3 能力覆盖矩阵，区分已迁入、转归口、后置和废弃；
6. `_migration/11F-action-template-minimal-closure.md` 已记录行动模板最小闭环：Git 提交行动是唯一正式模板示范，WorkCase 非提交模板继续后置；
7. `_migration/11G-migration-dependency-independence.md` 已记录 formal review hash gate 从 `_migration/reviews` 迁入 `reviews/formal`；
8. README 已更新 `reviews/formal/` 和 `_migration/` 职责边界；
9. 阶段 11 完成后，V3 主体以 active specs、V3 facts、Web 独立读取、commit-msg hard switch、环境适配规范和稳定 formal review ledger 为主线；仍后置的是非提交行动模板、外部环境自动 Hook、稳定 receipt 存储和通用 Web 写入。

12-19 后续计划记录：

1. `_migration/12-19-v3-post-mainline-work-plan.md` 已记录 V3 主线验收后的后续工作顺序；
2. 阶段 12 优先补齐 specs 与 Code/Web/Tests 实现域实践边界；
3. 阶段 13 进入 WorkCase 最小行动模板；
4. 阶段 14 处理测试性能与分层；
5. 阶段 15-18 分别评估 runtime 自动入口、稳定 receipt、Web Confirm UI 和外部受管项目 Hook adapter；
6. 阶段 19 再判断 `_migration` 是否可以归档或删除。

12A 完成记录：

1. `specs/04-Specs基础规范.md` 已声明 specs 只定义需求、规则、契约、边界、Human Gate、Stop Conditions 和验证要求；
2. `specs/07-Code确定性执行规范.md` 已声明 Code 实践由 `code/` 和 `code/docs/` 承接；
3. `specs/08-Web信息同步规范.md` 已声明 Web 实践由 `web/` 和 `web/docs/` 承接；
4. `specs/09-测试与验证规范.md` 已声明测试实践由 `tests/` 承接，且 V3 不强制要求 `tests/docs/`；
5. `code/ldvh_specs.py` 和 `tests/code/test_ldvh_specs_validate.py` 已增加实现域实践边界检查和正反例；
6. `_migration/12A-implementation-domain-boundary.md` 已记录本阶段承接、边界和验证要求；
7. 本阶段不新增 Code/Web/Tests 具体实践文档，不改变 runtime、Hook、Web 写入或测试分层能力。

13A 完成记录：

1. `specs/06-行动模板基础规范.md` 已新增 WorkCase 最小手动行动模板，覆盖 Context、Scenario、Gate、执行、验证、回写和交还；
2. `specs/21-WorkCase-工作项.md` 已说明 WorkCase 行动模板归 06 承接，21 仍只定义事实对象状态、证据、关闭口径和 Human Gate；
3. `code/ldvh_specs.py` 和 `tests/code/test_ldvh_specs_validate.py` 已增加 WorkCase 行动模板解析、检查和正反例；
4. `_migration/13A-workcase-minimal-action-template.md` 已记录本阶段承接、边界和验证要求；
5. 本阶段只支持 `manual_equivalent_execution`，不启用 Web 写入、Hook、runtime 自动触发、完整 Confirm UI、字段表细化或批量状态迁移。

14A 完成记录：

1. `specs/09-测试与验证规范.md` 已补充分层测试入口契约，区分 smoke、targeted、runtime 和 full；
2. `code/test_runner.py` 已新增 runtime profile，并为 targeted 增加 `--slow auto|skip|include`；
3. `pyproject.toml` 和 `tests/code/conftest.py` 已建立 `slow`、`runtime`、`e2e` markers；
4. `package.json` 和 README 已补充 `test:runtime` 与 slow policy 用法；
5. `_migration/14A-test-tiering-performance.md` 已记录本阶段承接、边界和验证要求；
6. 本阶段不删除慢测试、不降低 full regression、不新增并行依赖、不默认并行化 slow 层。

15A 完成记录：

1. `_migration/15A-runtime-auto-entry-assessment.md` 已记录 runtime 自动入口复核；
2. `code/environment_entry_audit.py --format json` 确认 integrated 入口只有 `git.commit-msg`；
3. `runtime.session_start.auto`、`runtime.pre_tool_use.auto`、`runtime.completion_claim.auto` 和 `runtime.adapter.auto` 继续为 deferred；
4. `manual.runtime_adapter`、`manual.session_start`、`manual.pre_tool_use` 和 `manual.completion_claim` 仍是 manual-ready，不是自动触发；
5. `rules.top_level_mechanism` 和 `skills.top_level_mechanism` 继续为 removed_top_level；
6. 本阶段不新增代码能力、不安装 Hook、不创建 repo instruction、不恢复 Rules / Skill 顶层机制。

16A 完成记录：

1. `_migration/16A-receipt-storage-decision.md` 已记录 receipt 存储判断；
2. 当前不建立独立 runtime receipt 事实源，不创建 `ldvh-base/runtime-receipts/` 或等价目录；
3. 需要长期保留的 receipt 内容必须先由 AI 定性，再分流到验证证据、WorkCase 关闭证据、Git commit records、迁移记录、Spark/Pitfall/Study/ADR 或其它既有事实对象；
4. dedicated receipt storage 只有在非 Git runtime 自动入口 integrated、现有事实对象无法承接、schema/保留/清理/测试齐备并经 Human Gate 后才重新评估；
5. 本阶段不新增事实对象类型、不改变 runtime 输出形态、不把 stdout-only receipt 升级为事实源。

17A 完成记录：

1. `_migration/17A-web-confirm-ui-write-boundary.md` 已记录 Web Confirm UI 与通用写入边界；
2. 当前 Web 正式写入能力只限 Spark quick create，写入位置为 `ldvh-base/sparks/`，初始状态为 `pending`，并返回 `source_refs`；
3. `tests/web/api/sparks.test.ts` 已覆盖 Spark 创建、字段校验、文件冲突和写后校验失败；
4. 通用事实对象写入、WorkCase 状态推进写入、ADR/Pitfall/Study Web 写入和完整 Confirm UI 继续后置；
5. 后续启用完整 Confirm UI 或扩大 Web 写入前，必须先经 Human Gate，并补齐 Web 实现域展示合同、字段白名单、状态闭集、source_refs、写后校验和 tests/web 回归。

18A 完成记录：

1. `_migration/18A-governed-project-hook-adapter.md` 已记录外部受管项目 Hook adapter；
2. `code/governed_hook_adapter.py` 已支持 `status`、`install` 和 `uninstall`，并在写操作前要求 `--confirm-human-gate`；
3. adapter 先复用 10 的受管项目解析，再调用 `code/install_git_hooks.py`，非受管、混合或多项目 target 会阻断；
4. `code/install_git_hooks.py` 支持为外部 repo Hook 嵌入 LDVH root，避免外部 repo 必须复制 V3 validator；
5. 本阶段只提供 adapter-ready 能力，不自动安装到任何外部项目，不改变当前环境唯一 integrated 自动入口是当前 worktree `git.commit-msg` 的结论。

19A 完成记录：

1. `_migration/19A-migration-archive-decision.md` 已记录 `_migration` 归档判断；
2. `reviews/formal` 的 24 份 formal review 仍回指 `_migration/` mapping evidence；
3. `tests/code/test_formal_specs.py`、`code/test_runner.py`、`code/ldvh_specs.py` 和 `_migration/tests` 仍有稳定依赖；
4. `_migration/tests` 当前 19 passed，尚未被稳定替代；
5. 本阶段决定继续保留 `_migration`，不删除 tracked 迁移材料，不移动目录，不重写 formal review evidence。

20-22 有条件审核收口记录：

1. `_migration/20-22-conditional-audit-closure.md` 已记录只读审核“有条件通过”后的两个优先收口项；
2. `06/08/09/11` 已把命令长串、当前实现状态、runner 操作策略和 hook path 实践迁到实现域文档；
3. 新增 `code/docs/01-Git-Commit-and-Hook-Practice.md`、`tests/docs/01-Test-Runner-Practice.md` 和 `web/docs/12-Web写入实践边界.md`；
4. `code/install_git_hooks.py` CLI 直接写外部 repo 默认阻断，外部受管项目必须使用 `code/governed_hook_adapter.py` 并显式 Human Gate；
5. 本阶段不新增 Web 写入、不安装外部 Hook、不启用 session/pre-tool/completion 自动触发、不删除 `_migration`。

阶段 5B 术语校正：

1. Action Guide / 行动指南是 V2 知识地图导航能力在 V3 中的升级承接，二者等价，后续应完全取代“知识地图”概念；迁移材料中出现“知识地图”时只作为历史来源名，不作为 V3 长期对象、页面或事实层。
2. 行动模板应去 Skill 化。V2 Skill 中有价值的内容只能被吸收为普通行动步骤、Action Guide 提示或外部环境包装候选；不得保留 Skill 身份、Skill registry、Skill 执行闭环或 Skill 顶层机制。
3. 旧“工作模型”术语在 V3 中应统一校正为“事实模型”。迁移材料中出现“工作模型”时只作为历史来源名，不作为 V3 长期正式概念；相关规则进入 `05` 事实模型归口。
4. Web 与 Code 是同源的并列实现，不是上下游数据依赖。Web 页面/API 数据路径必须由 Web 自行从 Git 文件事实源、正式 specs、事实对象或 Web 自有 API 聚合读取；Code 输出只能作为诊断、验证或测试对照，不作为页面数据源。
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
