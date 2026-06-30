# V3 正式 specs 吸收索引

> 文件状态：temporary migration index。本文只记录 V2/旧 specs/现有迁移材料进入 V3 正式 `03/05/06/07/08/09` 的吸收判断，不授权正式规则、Code 行为、Hook 安装、提交门禁、Web 行为、Human Gate 或环境支持声明。正式规则仍以 `specs/` 正文为准。

## 1. 索引定位

本文用于把 V2 来源、现有 `_migration/inventory`、第 5 阶段吸收清单和 V3 编号决策转成后续正式 specs 的迁移依据。

本文不复制 V2 正文，不恢复 V2 的六类构成要素，不恢复 Skill 顶层机制，也不把 Hook、Rules、知识地图、Web 状态、测试输出或迁移清单升级为事实源。

吸收顺序遵守：

1. 先确认来源和 V3 归口；
2. 再写正式 specs；
3. 再补 Code 可消费结构和 tests；
4. 最后才考虑 adapter、dispatcher、commit gate、Hook、Web 或行动模板实现。

## 2. 正式 specs 吸收索引

| V3 编号 | 正式规范 | 主要吸收来源 | 应吸收内容 | 不直接吸收内容 | 首批 Code/tests 关注点 |
|---|---|---|---|---|---|
| 03 | 事实源与 Git 溯源规范 | V2 `07-事实源边界与Git追溯规范.md`、`07.Att.01` 至 `07.Att.12`、`31-git-commit-action` 中的提交证据边界 | Git 可追踪文件作为事实源；非事实源排除；过程输出、receipt、evidence、diagnostic 的回写边界；Git commit records 的溯源性质；commit message 契约的上位边界 | Git 提交流程步骤、commit hook 实现、Web 提交记录页面、知识地图派生展示、历史提交列表手写维护 | commit 契约可解析性、非事实源边界、completion evidence 回指、提交前 read_plan 消费证据 |
| 05 | 事实模型基础规范 | V2 `02-事实模型基础规范.md`、20-24 事实模型成员、`02.Att.*`、`v2-03-work-object-responsibility-map.yaml`、spec-bloat fact member scan | 事实模型/事实实例边界；事实对象准入；字段契约、状态、证据、关系的共同规则；warning/follow-up/evidence/next_queries 的稳定承接位置；成员模板的上位要求；旧“工作模型”术语统一校正为事实模型 | Spark/WorkCase/ADR/Pitfall/Study 的完整字段表、完整状态机、旧 TaskPlan/Task/SubTask 兼容、具体实例迁移、未授权附件整批复制 | 对象身份、事实实例不得定义规则、成员模板骨架、过程输出和证据分流到对象或 specs；优先迁移 `02.Att.*` 中可被正文授权和 Code/tests 消费的字段/模板信息 |
| 06 | 行动模板基础规范 | V2 `03-行动编排规范.md`、`31-git-commit-action`、30/32/34/35/36 行动成员、`v2-04-orchestration-responsibility-map.yaml`、stage-5 checklist | Context、Scenario、Gate、执行、验证、回写、缺口分流的行动模板基本结构；主控 AI 与能力输出交还边界；以 Git 提交行动作为首个行动模板示范；Rules 同步、环境适配等作为后续模板或候选归口；V2 Skill 中有价值的工作流内容转写为普通行动步骤或 Action Guide 提示 | V2 30-59 成员全文、Skill 顶层身份、Skill registry、Skill 执行闭环、具体 Hook/Rules 安装、完整流程目录、行动模板替代 Human Gate | Git 提交行动模板示范、模板 read_plan、Gate 分流、能力输出不得成为事实源、行动完成声明需要验证证据；行动模板去 Skill 化 |
| 07 | Code 确定性执行规范 | V2 `04-Code确定性执行规范.md`、`04.Att.*`、V2 `06` 中 dispatcher/adapter/payload 边界、现有 `code/specs_validate.py` 与 `code/ldvh_specs.py` | Code 读取、解析、校验、聚合、诊断、投影、preflight、runtime facade、stdout-only receipt、payload/adapter/dispatcher 的实现边界；Code 不授权、不替代 AI/Human/事实源 | 具体技术栈细节、Hook 安装、用户环境写入、Web API 细节、测试治理本体、未进入正式 specs 的候选规则 | validator 覆盖、诊断等级、unknown event、read_plan evidence、target 分类、environment_integrated=false |
| 08 | Web 信息同步规范 | V2 `05-Web信息同步规范.md`、`05.Att.*`、Web 回归材料 | Web 作为 Human-facing 派生展示；Web 与 Code 分开实现，并自行从同一 Git 文件事实源、正式 specs、事实对象或 Web 自有 API 聚合读取页面/API 数据；Code 输出只作诊断、验证或测试对照；状态、风险、证据、待确认事项、提交记录、诊断和验证状态展示边界；Web 状态不成为事实源；受控轻写入必须回写并验证 | 具体页面设计、API 实现、缓存实现、旧知识地图展示细节、未授权的通用写入、Web 作为项目管理看板优先、Web 只能由 Code 喂数据的实现假设、Web 消费 Code 输出/DTO/validator 内部对象作为主数据源 | source_refs/来源回指、Confirm UI 不替代 Human Gate、Web cache 不替代事实源、同源独立读取边界、Code 输出不得成为 Web 数据契约、轻写入白名单测试 |
| 09 | 测试与验证规范 | V2 `08-测试基础规范.md`、`08.Att.*`、现有 `tests/code` 和 `_migration/tests` | 自动化测试、命令校验、等价验证、Human 验收、回归验证的分层；验证声明字段；测试证据边界；失败阻断；同步触发；测试不得反向定义规则 | 具体测试框架绑定、测试输出长期落盘、fixture 当事实源、用测试通过替代 Human Gate、Web/Hook 未实现时的虚假覆盖 | `python3 -m pytest tests/code`、`specs_validate all`、runtime/preflight/action-guide 负例、review hash gate |

## 3. 只能留在 `_migration` 的内容

以下内容当前只能作为迁移证据或历史材料，不进入正式 specs 正文：

1. V2 全量目录清单、阶段计划、扫描报告和一次性审查结论；
2. V2 的 30-59 成员全文、20-24 成员完整字段表和完整状态机；
3. V2 `06` 的 Rules/Skills/Agents/Hooks 类型体系作为顶层构成要素的表达；
4. Skill 文件本身、Skill 调用事实、环境安装状态、Hook registry 存在性；
5. Web 页面截图、缓存状态、派生知识地图视图和本机环境观察；
6. 测试原始输出、coverage、trace、临时报告和迁移 fixture；
7. 旧编号、旧路径、旧 active 状态和历史兼容判断。

这些内容若有长期价值，必须先按 03/05/06/07/08/09 归口转写为正式规则、Code 输入、tests 或事实对象，不得整段搬入。

## 4. 应转为 Code 或 tests 的内容

附件迁移口径：

1. V2 附件不得整批搬入 V3；每个附件必须先确认正文授权、V3 归口、Code/tests 消费方和 Human Gate 风险。
2. 附件内容应先分流为：转写正式 spec 正文、迁入正式附件候选、转为 Code/tests、留在 `_migration`、后置到成员规范或实现域、废弃。
3. 字段闭集、枚举、纯表、机器契约可以迁为正式附件候选；核心规则、行动流程、Human Gate、大段解释、迁移过程和一次性清单不得进入附件，若有长期价值必须先转写到对应 spec 正文。
4. `02.Att.*` 优先服务事实模型；`07.Att.*` 优先服务事实源/Git 溯源和 Git 提交行动示范；`08.Att.*` 优先服务测试与验证；`05.Att.*` 后置到 Web 同源读取和展示边界；`04.Att.*` 仅筛选可进入 Code 确定性执行的命令/诊断/schema 信息。
5. 无法获得正文授权、source_refs、测试闭环或未迁入去向的附件，应暂停迁入并继续留在 `_migration`，不得声称已迁入或已生效。

以下内容不应写成正式 specs 规则正文的长表，应由 Code 或 tests 承接：

| 内容 | 承接位置 | 原因 |
|---|---|---|
| spec/attachment identity 一致性、canonical_path 和 role_sections 检查 | `code/ldvh_specs.py`、`tests/code` | 机械可验证，手写清单容易过期 |
| read_plan、source_refs、impact_summary 和 next_queries 派生 | Code 输出 | 应从 Markdown identity、章节和引用派生，不形成第二事实源 |
| runtime event 闭集、未知 event、acknowledged paths 和 completion evidence 负例 | Code/tests | 属于确定性执行和验证门禁 |
| commit message 正反例、body 条件、type/scope 解析 | Code/tests | 正式 specs 只定义契约，解析和负例由测试覆盖 |
| Web DTO/API 正反例、缓存边界和受控轻写入回归 | Web/tests | 不应把实现细节写成规则正文 |
| migration gate、bloat scan、Markdown extractor 原型 | `_migration/tests` 或后续正式 Code/tests | 当前只证明迁移方向，不授权正式行为 |

## 5. 编号与术语核对

当前 V3 正式编号采用：

1. `00` 理念与构成；
2. `01` 保障与衔接；
3. `02` AI 行为规范；
4. `03` 事实源与 Git 溯源规范；
5. `04` Specs 基础规范；
6. `05` 事实模型基础规范；
7. `06` 行动模板基础规范；
8. `07` Code 确定性执行规范；
9. `08` Web 信息同步规范；
10. `09` 测试与验证规范。

V3 术语使用：

| V2 或含糊术语 | V3 处理 | 状态 |
|---|---|---|
| 行动编排 | 改为行动模板；旧行动成员作为模板或候选吸收 | legacy_alias |
| 工作模型 | 改为事实模型；旧术语只作为历史来源名，相关规则进入 `05` 事实模型归口 | legacy_alias |
| 工作对象 | 已确认统一改为事实对象；旧术语只作为历史来源名，正式 specs 应逐处校正，不得直接作为 V3 对象规则名使用 | confirmed_rename |
| 运行时扩展 | 不作为第六构成要素；上位语义由 01 承接，具体实现边界分流到 07/09/06 | legacy_alias |
| Skill | 不作为 V3 顶层机制；行动模板中去掉 Skill 概念。V2 Skill 只作为历史来源名，其有效内容转写为普通行动步骤、Action Guide 提示或外部环境包装候选 | removed_top_level |
| 知识地图 | 作为 V2 历史来源名；V3 由 Action Guide / 行动指南完全承接并取代其导航能力，不保留知识地图作为长期正式概念、页面或事实层；Action Guide 与行动指南等价 | legacy_alias |
| 放行 | 不作为 Code/test/runtime 的输出语义；正式表达尽量拆为方向确认、执行授权、风险接受、事实/术语确认、验收通过、暂停/驳回等具体 Human Gate 结果类型；若保留“放行”，只能指 Human 显式决定 | confirmed_boundary |
| Human 确认 / 授权 / 验收 / 风险接受 / 方向确认 | `Human Gate` 是机制名；这些词是动作或结果类型，不得被泛化为同一种“确认”。已确认结果类型至少包括方向确认、执行授权、风险接受、事实/术语确认、验收通过、暂停/驳回 | confirmed_boundary |
| Confirm UI / Web 确认 | Web 交互或页面状态不得替代 Human Gate 完成；仅可展示或辅助 Human 明示决定 | needs_review |
| blocker / blocking / follow_up / follow-up / unverifiable | 诊断等级和输出拼写需要统一闭集；语义降级由 AI 排查，机械拼写由 Code 检查 | needs_review |
| 带“用户”前缀或“最终”修饰的事实源旧表达 / 单一事实源 | 统一为 `事实源`；`用户掌握` 只作为所有权说明；`单一事实源` 退为 legacy_alias；不得把 Specs 规则、事实对象、Human 明示决定、过程输出和证据共同塞进“事实源”概念 | confirmed |

术语整治必须先于后续事实模型、附件、行动模板和 Web 深入迁移。规则/事实边界整治是 5B-0 的最高优先子项，应先审计 00/03/04/05 中是否把规则系统和事实系统混写。术语表 `specs/attachments/04.Att.06-术语表.md` 应在 5B-0 中同步，且不得把术语表、迁移索引、Code/tests 或子 agent 输出升级为正式规则源。

## 6. 5B-1/2/3 执行结果

| 子阶段 | 状态 | 正式迁入或增强 | Code/tests 闭环 | 验证结果 |
|---|---|---|---|---|
| 5B-1 | 已完成 | `05` 增强事实实例不得定义规则、测试夹具/迁移材料不得写成事实实例、对象准入说明 AI 负担、字段名术语边界、成员规范后置判断条件 | `validate_fact_model_boundaries` 与 05 负例测试 | validator 0 diagnostics；tests 63 passed |
| 5B-2 | 已完成 | 新增 `03.Att.01-Commit-Message契约字段表`、`05.Att.01-字段注册表结构`、`09.Att.01-验证声明字段表`；新增 `_migration/5B-2-attachment-disposition.md` 覆盖 48 个 V2 附件分流 | `validate_attachment_contracts` 解析 commit 契约、字段注册结构、验证声明字段并覆盖负例 | validator 0 diagnostics；tests 68 passed |
| 5B-3 | 已完成 | 保持 03/09 正文边界，增强 Code 对非事实源、过程输出回写、测试证据、失败阻断、验证声明附件字段的检查 | `validate_fact_source_and_verification_boundaries` 与 03/09 负例测试 | validator 0 diagnostics；tests 73 passed |
| 5B-4 | 已完成 | `06` 新增 Git 提交行动模板示范，覆盖 Context、Scenario、Gate、执行、验证、回写、交还；确认 Action Guide 取代知识地图导航能力，Skill 只作为外部包装候选 | `validate_git_commit_action_template` 与 Git 提交行动模板负例测试 | validator 0 diagnostics；tests 80 passed |

本轮附件分流结果：

| 处理类型 | 结果 |
|---|---|
| 迁附件 | `07.Att.02/03/04/08` 合并迁入 `03.Att.01`；`02.Att.01` 结构迁入 `05.Att.01`；`08.Att.02` 迁入 `09.Att.01` |
| 转正文 | 事实源归属、非事实源排除、过程输出回写、测试证据、失败阻断、等价验证等父层规则已由 03/09 正文承接 |
| 转Code/tests | 成员一致性、双读映射、字段矩阵、Code 诊断、preflight、commit 样例、同步触发和回归入口等进入 validator/tests 或后续实现测试 |
| 后置 | 成员模板/成员身份字段后置到事实模型成员规范；Web DTO/API/Confirm UI/缓存/回归后置到 5B-5 |
| 留_migration | 清退登记、迁移双读材料、Web 差距审计模板保留为迁移证据 |
| 废弃 | V2 知识地图输入范围表、知识地图投影 Schema 表废弃为 legacy_alias，由 Action Guide/行动指南承接 |

5B-4 执行结果：

| 对象 | 处理 |
|---|---|
| V2 `31-git-commit-action-Git提交行动编排.md` | 不整篇迁入；提取 Context、Scenario、Gate、执行、验证、回写、交还的最小结构进入 `06` 正文示范 |
| `skills/ldvh-git-commit/SKILL.md` | 不恢复 Skill 顶层机制；仅作为外部包装候选和迁移来源，06 要求区分 `skill_runtime_invoked`、`manual_equivalent_execution`、`skill_unavailable` |
| commit message 契约字段 | 不在 06 重定义；继续由 `03` 和 `03.Att.01` 授权 |
| 验证声明字段 | 不在 06 重定义；继续由 `09` 和 `09.Att.01` 授权 |
| Hook / commit gate / CI | 本阶段未实现，不声明环境接入或运行时拦截生效 |

## 7. Stop Conditions

出现以下情况时暂停并回到正式 specs 或 Human Gate：

1. 新增正式 spec 没有明确减少的 AI 负担、事实源边界或验证方式；
2. V2 内容被整段复制，导致 V3 恢复旧目录权威或第二事实源；
3. Runtime、Skill、Hook、Rules 或 Web 状态被写成独立构成要素；
4. Code、tests、review 或子 Agent 输出替代正式规则、Human Gate 或完成声明；
5. 03/05/06/07/08/09 与 00、01、02、04 的上位边界冲突，或规则系统与事实系统边界被混写；
6. 新增正式 specs 后没有同步 Code 解析、review 收据和 tests。
