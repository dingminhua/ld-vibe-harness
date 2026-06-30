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

阶段 1 已完成：正式 `code/specs_validate.py` 已能解析 `ldvh_spec`、`ldvh_attachment`、H2 章节、`role_sections`、`code_consumption`、保障消费时机表和 02 AI 行为保障表，并由 `tests/code/` 覆盖。

阶段 2 已完成最小只读 Action Guide：Code 已能基于正式 specs 输出 `task_read_plan`、`next_queries`、`stop_conditions`、`validation_guard`、`missing_fields`、`capability_gap`、`impact_summary` 和 `source_refs`。该输出只作为过程指导，不成为独立事实源，也不声称运行时拦截、receipt 写入、Hook 或提交门禁已经生效。

阶段 3 已完成只读 preflight：Code 已能基于 Action Guide 和正式 specs 判断 target 类型、影响等级、必要读取、Human Gate 风险和 blocking/warning/follow_up/unverifiable 诊断分流。preflight 输出只作为诊断和阻断建议，不输出授权或 Human Gate 替代结论；无诊断时使用 `diagnostic_clear`，避免被误读为授权语义。

阶段 4 已完成最小 runtime facade：Code 已能按消费时机闭集承接 `session_start`、`acknowledge_read_plan`、`pre_tool_use`、`git_commit_msg`、`human_facing_output`、`external_output_intake`、`diagnostic_disposition` 和 `completion_claim`，生成 stdout-only receipt，并联动 Action Guide 与 preflight。`pre_tool_use` 与 `git_commit_msg` 缺少 read_plan 消费证据时阻断，`completion_claim` 缺少验证证据时阻断。该能力不声明 Hook、Rules、插件或环境已经完整接入。

当前进入阶段 5A：V2 内容吸收与语义映射。当前清单为 `_migration/stage-5-v2-absorption-checklist.md`，正式编号归口由 `_migration/v3-formal-spec-numbering-decision.md` 和 `_migration/v3-specs-absorption-index.md` 共同记录。

1. 按吸收清单逐项确认 V2 来源、当前状态、V3 归口、保留能力、废弃或后置内容、Skill 语义转换、前置 specs、前置 tests 和 Human Gate；
2. 先按吸收索引创建 `03/05/06/07/08/09` 的正式基础规范，确保每篇都有来源归口、保障措施、验证方法、Human Gate 和 Stop Conditions；
3. 再补 Code 可消费结构和负例测试，使 validator 能识别新正式 specs，而不把新增 docs 当作未验证空壳；
4. 只有在上述闭环完成后，才设计 Hook / Commit / 行动模板适配层；
5. 适配层只能调用 runtime/preflight/action-guide，不重新定义规则；
6. 明确环境未接入时的 fallback 行为和 diagnostic；
7. 为 commit gate、hook adapter、行动模板适配和环境缺口补齐回归测试。

阶段 5B：Code validator 细化路线。阶段 5B 只补正式 specs 的可消费结构和负例测试，不进入 Hook 安装、环境接入、Web 写入或 commit gate 实现。各子阶段应单独验证、单独提交。

| 顺序 | 子阶段 | 目标 | 主要对象 | 验证方式 | 不做事项 |
|---|---|---|---|---|---|
| 5B-0 | 术语整治与术语表同步门禁 | 在事实模型、附件、行动模板和 Web 继续迁移前，先收束 V2->V3 术语变化和 Human 确认类含糊表达，建立 AI 语义排查与 Code 检查分工 | `specs/attachments/04.Att.06-术语表.md`、`_migration/v3-specs-absorption-index.md`、`_migration/inventory/v2-terminology-to-v3-04-att-06-map.yaml`、正式 specs、`code/ldvh_specs.py`、`tests/code` | 先产出术语 inventory、AI 语义裁决、Human 确认清单和术语表同步；再补 Code 机械检查与负例测试；运行 `python3 -m pytest tests/code _migration/tests -q` 和 `python3 code/specs_validate.py all --format text --fail-on-diagnostics` | 不先把未确认术语硬编码进 Code；不把旧术语恢复成 V3 正式概念；不让 Code/test 输出替代 Human Gate、术语确认或正式 specs |
| 5B-0A | 规则/事实边界整治 | 作为 5B-0 的最高优先子项，先审计并拆开规则系统、事实系统、Human 机制、过程输出和证据，避免把 Specs 规则、事实对象、Human Gate 决定和过程输出都塞进“事实源”概念 | `specs/00-理念与构成.md`、`specs/03-事实源与Git溯源规范.md`、`specs/04-Specs基础规范.md`、`specs/05-事实模型基础规范.md`、`specs/attachments/04.Att.06-术语表.md`、`_migration/v3-specs-absorption-index.md`、正式 specs 全文术语扫描 | 先产出规则/事实边界审计清单、误导性表述清单、Human 待确认术语和 00/03/04/05 修改建议；待 Human 确认后再同步术语表和 Code 机械检查 | 不直接全局替换；不把 `specs/` 写成事实源；不把事实对象写成规则源；不把 Human Gate 决定、过程输出或证据写成规则或稳定事实 |
| 5B-1 | `05` 事实模型优先迁移 | 先迁移事实模型父层可消费结构，解析事实对象准入、事实实例边界、字段状态和证据分流规则 | `specs/05-事实模型基础规范.md`、V2 `02.Att.*` 筛选结果、20-24 成员迁移证据、`code/ldvh_specs.py`、`tests/code` | 覆盖对象准入、实例不得定义规则、测试夹具/迁移材料/临时输出不得成为事实实例的负例；运行 `python3 -m pytest tests/code _migration/tests -q` 和 `python3 code/specs_validate.py all --format text --fail-on-diagnostics` | 不新增事实源格式；不批量复制 Spark/WorkCase/ADR/Pitfall/Study 完整字段表或状态机；不让事实实例反向定义模型规则 |
| 5B-2 | 附件迁移筛选与授权闭环 | 系统处理 V2 大量附件，按 `03/05/06/07/08/09` 归口分流为：转写正式 spec 正文、迁入正式附件候选、转为 Code/tests、留在 `_migration`、后置到成员规范或实现域、废弃 | `_migration/stage-5-v2-absorption-checklist.md`、V2 `02.Att.*`、`04.Att.*`、`05.Att.*`、`07.Att.*`、`08.Att.*`、`specs/attachments`、`tests/code` | 每个迁入附件必须有正文授权、identity block、Code 可解析字段和负例测试；核心规则类内容必须先进入对应 spec 正文授权；未迁入附件必须记录去向 | 不整批搬运附件；不让附件承载核心规则、行动流程或 Human Gate；不让附件或 Code/tests 输出反向定义规则；不把 V2 附件清单恢复成目录权威 |
| 5B-3 | `03/09` 证据与验证边界专项 validator | 检查非事实源误用、过程输出和证据回写、验证声明字段、失败阻断和证据回指，并为后续 Git 提交行动示范提供验证边界 | `specs/03-事实源与Git溯源规范.md`、`specs/09-测试与验证规范.md`、`code/ldvh_specs.py`、`code/specs_validate.py`、`tests/code` | 补正反例测试；验证 completion evidence、测试证据边界、未验证范围和 source_refs | 不实现 Hook、commit gate 或环境接入；不输出 `approved`、`human_gate_passed` 等授权语义 |
| 5B-4 | `06` Git 提交行动模板示范 | 在 5B-3 证据与验证边界、commit 契约附件候选清楚后，以 Git 提交行动作为第一个行动模板示范，验证 Context、Scenario、Gate、执行、验证、回写和交还结构；同时确认 Action Guide 取代知识地图、行动模板去 Skill 化 | `specs/06-行动模板基础规范.md`、`31-git-commit-action` 迁移证据、commit 契约附件候选、Action Guide 相关 Code、`tests/code` | 测试提交模板缺少 status/diff、验证证据、提交拆分、Human Gate 风险或交还字段时输出 diagnostic；测试 Action Guide 输出不替代主控 AI 判断；commit 契约字段只能来自 `03` 正文授权附件、Code/tests 负例或后续 Human Gate | 不安装 commit hook；不把 commit validator 输出当授权；不恢复 Skill 顶层机制；不让模板本身定义 commit 规则；不把行动模板写成第二规则源 |
| 5B-5 | `08` Web 同源读取与展示边界检查 | 明确 Web 可以自行读取同一 Git 文件事实源，并校验展示、缓存、Confirm UI 和受控交互边界 | `specs/08-Web信息同步规范.md`、Web 边界 validator、`tests/code` 或后续 Web contract tests | 测试 Web 状态、缓存、按钮点击、派生视图不能替代事实源或 Human Gate；测试 source_refs/回指缺失时输出 diagnostic | 不要求 Web 必须由 Code 喂数据；不启动真实 Web 写入；不把 Confirm UI 当作 Human Gate 完成 |

阶段 5B-0 执行顺序：

1. 规则/事实边界审计：先执行 5B-0A，扫描 00/03/04/05 和正式 specs，区分规则系统、事实系统、Human 机制、过程输出和证据，列出把规则写成事实源、把事实对象写成规则源、把 Human Gate 决定、过程输出或证据写成权威承载的表述。
2. 术语 inventory：扫描 `specs/`、授权附件、`_migration/`、Code 和 tests，分出正式术语、旧术语、退场术语、禁止/高风险表达、结果类型和 `needs_review` 术语。
3. AI 语义裁决：判断旧词是否正在恢复 V2 结构或制造第二规则源，例如知识地图事实层、Skill 顶层机制、工作对象/事实对象混用、Human Gate 结果被普通确认替代，以及规则/事实边界被混写。
4. Human 确认清单：只把影响 Human Gate、规则源、事实源、授权、验收、风险接受和术语边界的未决项交还 Human，不由 AI 擅自定死。
5. 术语表同步：更新 `04.Att.06` 的术语、类别、含义、边界、迁移来源和状态，并按需要调整正式 specs 中的含糊表达。
6. Code validator/tests：在术语表和 Human 确认后，再补机械检查、旧词/禁词负例、授权语义负例、规则/事实混写负例和迁移材料例外。

阶段 5B-0A 初始边界模型：

| 类别 | 回答的问题 | 权威承载 | 不得替代 |
|---|---|---|---|
| 规则系统 | AI 应该按什么规则判断和行动 | `specs/` 正文 | Code、测试、附件、迁移材料、Action Guide、Web、事实对象 |
| 事实系统 | 当前状态、证据、决策、经验和缺口是什么 | 事实模型、事实对象、Git 可追踪事实文件 | 聊天、缓存、Web 状态、Runtime receipt、测试输出、迁移材料 |
| Human 机制 | 是否确认、授权、验收、接受风险、暂停或驳回 | Human 明示决定；需要长期溯源时按性质回写到规则系统或事实系统 | AI 推断、Code 通过、Web 点击、测试通过 |
| 过程输出 | 执行过程中观察到什么 | 默认非权威；被记录、有结构、可回指后才可能成为证据；经 AI 定性、必要 Human Gate、归口、回写和验证后才可被采纳 | 原始输出本身、子 agent 结论、review 收据、命令成功 |

阶段 5B-0A 初步术语方向：

1. `规则源` 或 `正式规则源` 只指 `specs/` 正文，不归入事实源。
2. `事实源` 只谈事实系统承载，不承载规则系统；不得用事实源统称 Specs 规则。
3. 带“用户”前缀或“最终”修饰的事实源旧表达统一为 `事实源`；`单一事实源` 退为 legacy_alias，不继续作为 V3 长期正式表达使用。
4. `用户掌握` 可作为所有权、可迁移、可审查原则讨论，但不得与事实源概念混写。
5. `Human Gate 决定` 是 Human 机制结果，不是规则源或事实源；需要长期溯源时应按影响回写到对应承载位置。
6. `过程输出` 默认不是规则、事实或 Human Gate；被记录、有结构、可回指后才可能成为证据；被采纳后也必须说明采纳范围、归口和回写位置。

阶段 5B-0 重点词簇：

| 词簇 | 初步方向 | 处理要求 |
|---|---|---|
| `工作模型` / `事实模型` | `工作模型` 退为历史来源名，V3 使用 `事实模型` | 进入术语表和 `05` 归口；正式 specs 不应继续使用 `工作模型` |
| `工作对象` / `事实对象` | 已确认统一改为 `事实对象` | 逐处 AI 语义排查，不做简单全局替换；正式 specs 和迁移材料逐处校正，旧术语只作为历史来源名 |
| `知识地图` / `Action Guide` / `行动指南` | Action Guide / 行动指南完全承接并取代 V2 知识地图导航能力；Action Guide 与行动指南等价 | `知识地图` 只作为历史来源名；不得保留知识地图事实层、页面或长期对象 |
| `Skill` | 去顶层化 | 只允许作为历史来源名或外部环境包装候选；行动模板中不得保留 Skill 身份或 registry |
| `行动编排` / `行动模板` | V3 使用行动模板 | 旧行动成员可作为模板候选，不恢复行动编排目录权威 |
| `放行` | 不作为 Code/test/runtime 的输出语义；正式表达尽量拆为具体 Human Gate 结果类型 | 若保留“放行”，只能指 Human 显式决定；Code/test/runtime 只能输出诊断、验证或阻断状态，不输出授权语义 |
| Human 确认词簇 | `Human Gate` 是机制名；确认、授权、验收、风险接受、方向确认是动作或结果类型 | 已确认结果类型至少包括方向确认、执行授权、风险接受、事实/术语确认、验收通过、暂停/驳回；普通“确认”不得被泛化成授权或验收 |
| `blocker` / `blocking` / `follow_up` / `follow-up` / `unverifiable` | 需要统一诊断等级与输出拼写边界 | Code 可检查拼写和闭集；语义降级需要 AI 排查 |
| `Confirm UI` / Web 确认 / Human Gate | Web/Confirm UI 不等同 Human Gate 完成 | Web 点击或页面状态不得替代 Human 明示决定 |
| 带“用户”前缀或“最终”修饰的事实源旧表达 / `单一事实源` | 统一为 `事实源`；`用户掌握` 只作为所有权说明；`单一事实源` 退为 legacy_alias | 不再把 Specs 规则、事实对象、Human 明示决定、过程输出和证据共同塞进“事实源”；00/03/04/05 需按术语整治结果同步 |

阶段 5B-0 Stop Conditions：

1. 无法判断某术语是正式术语、旧术语、结果类型还是禁止表达；
2. Human 确认、授权、验收、风险接受或放行类词语超出已确认结果类型，或可能改变 Human Gate 边界；
3. Code validator 准备检查尚未由术语表或 Human 确认稳定的术语；
4. 旧术语被写成 V3 长期对象、事实源、页面、机制或目录权威；
5. 术语表、迁移材料、Code/tests 或子 agent 输出正在反向定义正式 specs。
6. 规则系统和事实系统无法区分，或 `specs/` 被写成事实源、事实对象被写成规则源。

阶段 5B-0 当前缺口：

1. Code/tests 可落地检查角度仍需后续专项复核；本次子 agent 未完成该角度审查，不能声称已有完整 Code 方案。
2. 带“用户”前缀或“最终”修饰的事实源旧表达，以及 `单一事实源` 的正式替代表达已在 5B-0A 后续术语整治中确认，需继续由正式 specs、术语表、Code 和 tests 承接。

阶段 5B-2 前置条件：

1. 已能读取对应 V2 来源，并记录 source_refs；
2. 已确认父规范正文授权和 V3 归口；
3. 已识别是否涉及核心规则、行动流程或 Human Gate；
4. 已指定 Code/tests 消费方、负例测试和未迁入去向。

阶段 5B-2 Stop Conditions：

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
