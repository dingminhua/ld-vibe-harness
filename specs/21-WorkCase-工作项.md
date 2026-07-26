# WorkCase / 工作项

```yaml
ldvh_spec:
  spec_key: "workcase-fact-type"
  spec_id: "21"
  spec_kind: "spec"
  title: "WorkCase / 工作项"
  status: "active"
  canonical_path: "specs/21-WorkCase-工作项.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 WorkCase 事实类型的单一当前对象形状、工作责任、推进阶段、质量关口、写回、关系、消费、Human Gate 与终态收敛规则"
  scope: "管辖项目中经 Human 明确选择建立项目记录，已经形成可独立关闭的目标、范围与成功标准，并需要持续保存当前计划、稳定推进快照、结果判断和责任处置的单一工作责任"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
    - "action-template-foundation"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `workcase` 事实类型的唯一定义来源；它不使实例、Schema、Code、Helper、tests、行动模板或 Web 能力自动成立。本文只定义一份当前契约，不建立 profile、历史形状、兼容读取或迁移语义；不符合本文与统一字段登记的对象不是当前有效 WorkCase。

## 1. 价值判断

### 1.1 根职责

WorkCase 保存一项已经由 Human 选择交给项目承担、能够独立判断关闭的工作责任。未关闭时，它使 Human 与 AI 能够稳定回答：要达成什么、边界在哪里、以什么标准判断、当前计划是什么、哪些工作项已经形成什么事实、现在从哪里继续、什么阻止继续、当前处于哪个质量或 Human 关口。关闭后，它继续回答：原责任与验收基线是什么、实际结果和验证边界是什么、为什么停止，以及剩余责任转交到哪里或为何接受停止。

WorkCase 是当前事实对象，不是实时监控、聊天计划副本、命令清单、AI 推理记录、运行日志或正确性证明包。正常推进路径中，创建前独立方案复核、Human 计划决定、执行、主控自检、独立结果复核、主控收敛和 Human 关闭决定都必须实际发生。受控前置执行终止链不补造执行事实；它以 Human 明确停止决定和据实的 `cancelled` item 终值取代执行，后续主控自检、独立结果复核、主控收敛和 Human 关闭决定仍必须实际发生。某个关口必须发生，不表示其过程记录必须在关闭后永久保留。

### 1.2 活动期与终态价值

活动期信息只在仍约束推进、恢复、授权、复核或关闭判断时保留。被替代计划、旧结果复核、阶段往返、轮次、命令、工具调用和角色流水不进入 WorkCase。实际提交过的差异可能由 Git 保留，但 WorkCase 与 Git 都不承诺完整过程复原。

closed WorkCase 是终态责任与结果记录，不是质量链合规档案。关闭事务必须从完整活动期对象验证当前仍须成立的关口并原子形成精简终态；关闭后只保留仍有查重、结果理解、影响判断、责任去向或后续决策价值的内容。

### 1.3 排除边界

以下内容不进入 WorkCase：

- 单个工作项内部的命令、工具顺序、临时 todo、执行百分比、Agent 运行状态和推理过程；
- phase 进入历史、阶段轮次、复核次数、旧计划、旧结果包和旧批准；
- 仅为 Web Card、计数、分组或视觉完整性制造的字段；
- 能够由其它当前字段无损回答的重复摘要；
- 为证明 review、approval、命令或验证曾发生而复制的证据包。

## 2. 规范依据

### 2.1 直接依据

本文直接依据：

1. `fact-model-foundation`：事实对象共同身份、统一字段登记、来源选择、CAS、原子写入、回读、更正、删除、Human Gate 与失败交还；
2. `source-of-truth-traceability`：管辖项目、当前 Working Tree、稳定来源与可回指边界；
3. `action-template-foundation`：可复用行动方法与单次运行记录不得反向塑造事实对象。

## 3. 职责边界

### 3.1 本文负责

本文唯一负责：

- WorkCase 的类型语义、准入、粒度、载体、类型字段与结构；
- status、phase、work item、计划与结果版本、字段 presence 和 closed 白名单；
- 独立复核、execution approval、关闭提案、专属关闭和关系闭集；
- AI 写回检查点、防幻觉、消费、Human Gate、验证和 Stop Conditions。

### 3.2 本文不负责

本文不复制 05 已定义的通用请求包装、锁、错误档位、CAS、原子文件写入、回读、更正、删除和类型退出机制；只规定这些机制用于 WorkCase 时必须额外满足的条件。本文也不定义具体 CLI、Helper 命令、Web 组件、环境 Hook、Agent API 或模板实现。

角色边界如下：

- Human 决定是否建立项目记录、是否批准当前计划、责任与验收基线变化、风险接受和是否按完整关闭提案停止；
- Controller 形成与收敛当前事实、处置复核反馈、选择合法 phase、发起必要返修并组织写回；
- Reviewer 只提供实际独立第二视角，不替 Human 或 Controller 推进状态；
- 执行 AI 在获准 work item 边界内选择具体实现方法，并据实写回稳定检查点；
- Code 只校验来源已经定义的结构、闭集、版本、指纹、CAS、引用和转换条件，不判断自然语言真实性、相关性、风险接受或责任边界是否充分。

## 4. 适用范围

### 4.1 对象建立前的工作意图

Human 明确选择“由项目承担这项工作并建立 WorkCase”是进入正式计划、独立方案复核和受控创建的前提。该选择发生在对象外，不是 WorkCase phase，也不批准尚未形成的计划。

### 4.2 准入条件

只有同时满足以下条件，才能建立 WorkCase：

1. Human 已明确选择建立项目记录；
2. 存在一个能够独立判断关闭的单一目标；
3. scope 能说明覆盖、重要约束和排除边界；
4. 至少一项成功标准能够被独立检查；
5. 当前工作确有跨行动恢复、稳定推进、质量判断、依赖、阻塞或终态回读价值；
6. 已召回并比较相邻 WorkCase、Spark 与其它稳定事实，没有可无损更新的现有对象；
7. 已知内容可按所需精度回指，未知没有被补造；
8. 对象化带来的净价值高于持续回写与治理成本。

预计持续时间、工作项数量、实现复杂度和是否能在当前会话完成，都不是独立准入或排除条件。

### 4.3 粒度与相邻承载

一个 WorkCase 只承担一个关闭责任。共同服务同一关闭判断、具有明确局部目标和预期结果的内容形成 work item；需要独立准入、授权、长期阻塞、责任转交或关闭判断的目标形成另一个 WorkCase。

尚无可执行目标、scope 或成功标准的内容属于 Spark 候选；当前行动即可完成且没有稳定回读价值的内容留在当前行动；长期规则进入规范；可复用方法进入行动模板。不得把命令、review checklist、纯结果报告或周期运行入口伪装成 WorkCase。

### 4.4 受控创建

受控创建必须一次形成完整目标、scope、成功标准定义、`plan_version=1`、非空 work items、至少一项实际独立方案复核、priority、`status=open`、`phase=human_plan_confirming` 和 Human waiting，并完成 Schema 校验、写入与回读。创建时全部 work item 必须为 `pending`。创建前 Reviewer feedback 必须由 Controller 处置；新对象不得带 execution approval 或结果字段。

## 5. WorkCase 类型定义

### 5.1 类型与身份

`fact_type_key` 固定为 `workcase`。对象使用 UTF-8 YAML，一文件一对象，权威位置固定为：

```text
ldvh-base/workcases/<object_id>.yaml
```

`object_id` 必须匹配 `workcase-[0-9]{4,}`，文件名必须与 `object_id` 完全一致。身份分配后不得因标题、路径、状态或内容变化而改变。`title` 只简短识别工作责任，不复制 `goal`、当前摘要或关闭结论。

未知或不适用的条件字段必须省略，不写 `null`、空字符串、空数组、占位时间、默认状态或默认关系。本文不定义 `closed_at`；`created_at` 表示对象创建，`updated_at` 表示当前内容最近一次实质变化并成功回读的时间，终态更正同样更新 `updated_at`。

### 5.2 单一当前形状

WorkCase 只有本文与 05.Att.01 共同定义的当前字段和结构。任何未登记字段、登记已退出字段、额外 object 成员或实现私有扩展都使对象失效；不得根据文件年代、缺失字段或实现版本猜测另一套形状。

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `workcase` | 经 Human 选择建立项目记录，保存单一工作责任的当前计划、稳定推进事实、质量关口、结果判断和终态处置 | `workcase-fact-type::5. WorkCase 类型定义` |

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `workcase-fact-type::5. WorkCase 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `workcase-fact-type::5. WorkCase 类型定义` |
| `created-at` | required | `inherit` |
| `updated-at` | required | `workcase-fact-type::7. AI 写回与受控操作` |
| `status` | required | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `urls` | conditional | `workcase-fact-type::8. 来源、外部资料与关系` |
| `relations` | conditional | `workcase-fact-type::8. 来源、外部资料与关系` |
| `current-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-resume-from` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-waiting-on` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `priority` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `disposition-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-goal` | required | `inherit` |
| `workcase-scope` | required | `inherit` |
| `workcase-success-criterion-definitions` | required | `inherit` |
| `workcase-success-criterion-results` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-residual-responsibilities` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-phase` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-plan-version` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-items` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-creation-reviews` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-execution-approval` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-result-version` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-overall-result-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-controller-check-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-result-reviews` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-validation-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-blocking-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-closure-proposal` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-closure-outcome` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |

### workcase 结构准入记录

| information_need | compared_structure_keys | decision | resulting_structure_key | rationale |
|---|---|---|---|---|
| 在 Human 关闭决定前稳定保存一份完整、可退回修改且不冒充终态的关闭方案 | `workcase-human-approval,workcase-residual-responsibility,workcase-success-result` | `new` | `workcase-closure-proposal` | approval 只记录执行批准，success result 只回答单项标准结果，terminal residual 只保存已经接受停止的责任；三者都不能承载拟定 outcome、整体停止边界和逐项责任建议，也不能提供 proposal 与 terminal 的生命周期隔离 |
| 在关闭方案中逐项表达一项剩余责任、Controller 建议的处置方向和条件 route target | `relation-target,workcase-residual-responsibility,workcase-success-result` | `differentiate` | `workcase-residual-decision` | relation target 只有稳定目标，terminal residual 已表示 Human 接受停止，success result 只回答标准结果；提案项必须同时支持 `route` 与 `accept_stop`，并在 Human 决定前保持建议态 |
| 绑定拟路由目标的稳定身份和当次完整内容快照，发现 Human 等待期间的目标漂移 | `relation-target,workcase-residual-decision` | `differentiate` | `workcase-proposed-route-target` | terminal relation target 不保存内容指纹，residual decision 还包含责任与建议；proposal target 只在关闭等待期服务 CAS 与防陈旧，关闭后必须消失 |
| 在 closed 中保存没有符合转交条件目标、且 Human 已接受停止的一项具体责任 | `workcase-residual-decision,workcase-success-result` | `differentiate` | `workcase-residual-responsibility` | proposal decision 尚未成立且可以 route，success result 只说明验收结果；terminal residual 只含稳定身份与具体责任正文，不再重复 disposition 或目标引用 |
| 保留独立 Reviewer 对当前计划或结果版本的第二视角，并由 Controller 记录当前处置 | `workcase-review` | `reuse` | `workcase-review` | 当前需求仍是同一 review 结构；删除 `review_basis` 后，review 内容只来自当次实际 Reviewer 输出，并通过 `subject_version` 绑定当前被审对象，不再把证明材料或历史依据纳入成员闭集；字段所有权、失效与出现条件由本章当前契约唯一定义 |
| 保留 Human 对准确计划版本的执行批准，而不持久化关闭决定收据 | `workcase-human-approval` | `reuse` | `workcase-human-approval` | 结构仍只需承载 Human 批准范围、时间与绑定 plan version；关闭决定由专属事务消费，不与 execution approval 共用持久化结构，也不保留为关闭批准服务的旧成员、字段或使用方式 |

### 类型专属结构定义

| structure_key | meaning | not_meaning | constraints |
|---|---|---|---|
| `workcase-item` | 共同服务同一 WorkCase 关闭判断、具有稳定局部身份、目标、预期结果与当前状态的工作单元 | 不表示命令步骤、临时 todo、执行百分比、工具调用、AI 推理或独立 WorkCase | 直接成员闭集由本节字段定义；状态条件字段按 §6.4；依赖只指向同一对象内 item |
| `workcase-review` | 独立 Reviewer 对当前计划版本或结果版本提供的实际第二视角，以及 Controller 对反馈的当前处置 | 不表示 Reviewer 拥有流程决定权，也不保存旧版本、审核次数、主体指纹或证明材料 | container 决定审核对象；creation review 绑定 `plan_version`，result review 绑定当前 `result_version`；Reviewer 字段与 Controller resolution 分属不同所有者 |
| `workcase-human-approval` | Human 对一个准确 `plan_version` 作出的当前执行批准 | 不表示关闭批准、技术验证、后续版本获批、风险自动消失或字段存在即可继续执行 | 只供 `execution_approval` 使用；批准范围、时间和实际来源按成员字段记录；关闭决定不持久化 approval 收据 |
| `workcase-success-criterion` | 一项具有稳定局部身份、可独立检查的成功标准定义 | 不表示执行步骤、结果、验证方法或数组序号 | `criterion_id` 在对象内唯一稳定；statement 与 goal、scope 共同构成验收基线 |
| `workcase-success-result` | 对一项当前成功标准的实际结果判断与范围说明 | 不表示 Code 已证明正文、Human 已验收或命令成功 | 必须按 `criterion_id` 精确覆盖全部当前定义；unknown 通过 `not_verified` 表达，不补猜 |
| `workcase-closure-proposal` | Controller 提交 Human 判断的一份完整关闭方案 | 不表示 Human 已同意、终态已成立、结果主体或证明收据 | 只在关闭准备与关闭待确认期间出现；始终整体形成，不持久化半成品 |
| `workcase-residual-decision` | 关闭提案中一项剩余责任及其 `route` 或 `accept_stop` 建议 | 不表示终态责任已经转交或 Human 已接受停止 | route 必须有 proposal target；accept_stop 禁止 target；所有当前剩余责任必须精确覆盖 |
| `workcase-proposed-route-target` | 拟路由目标的稳定三元身份与当次完整内容 fingerprint | 不表示 terminal relation、Human 阅读对象、目标接受责任或目标完成 | 只服务关闭事务的目标重读与精确比较；四个成员全部必填，关闭后删除 |
| `workcase-residual-responsibility` | closed 中没有符合转交条件目标、且 Human 已接受停止的一项具体责任 | 不表示建议、已处理、已完成、route target 或其它对象已经承接 | 只含 `residual_id` 与 `summary`；已路由责任不得同时保留为 residual |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `workcase-resume-from` | `resume_from` | string | 跨 work item 的当前首个有界恢复入口 | 不表示命令、完整步骤、普通下一项或 phase 标签 | 非空且无需猜测；它只记录责任可继续时的恢复入口，不单独授予行动权；入口完成或变化时更新或移除 |
| `workcase-waiting-on` | `waiting_on` | string | 当前实际等待的 Human、Reviewer、外部输入或能力 | 不表示普通待办、优先级或阻塞原因全文 | 非空且精确指向当前实际等待对象；等待解除时移除 |
| `workcase-goal` | `goal` | string | WorkCase 期望达成并可独立判断关闭的单一目标 | 不表示标题、步骤、当前进展或结果 | 必填非空；实质变成另一关闭责任时新建对象 |
| `workcase-scope` | `scope` | string | WorkCase 承诺覆盖的内容、重要约束与明确排除边界 | 不表示当前进展、实现细节或来源全文 | 必填非空；责任边界变化必须经过 §11 的 Human 决定 |
| `workcase-success-criterion-definitions` | `success_criterion_definitions` | array | 共同构成目标验收边界的成功标准定义闭集 | 不表示工作步骤、结果、测试命令或完成状态 | 至少一项；按 `criterion_id` 唯一；数组位置不表示优先级或顺序 |
| `workcase-success-criterion-results` | `success_criterion_results` | array | 当前结果版本对全部成功标准的逐项判断 | 不表示总体结果、验证全文或 Human 关闭决定 | 数组一旦存在就必须按 ID 精确覆盖全部定义，禁止持久化半数组；判断闭集见成员定义 |
| `workcase-residual-responsibilities` | `residual_responsibilities` | array | Human 已接受不再由当前 WorkCase 推进的具体剩余责任 | 不表示已路由责任、建议、风险列表或待办 | 按 `residual_id` 唯一；已路由项禁止重复；每项必须是 Human 实际接受停止的具体责任 |
| `workcase-phase` | `phase` | string | 未关闭 WorkCase 当前精确推进位置 | 不表示责任能否继续、Web 进展分组或历史阶段 | 闭集 `human_plan_confirming`、`plan_revising`、`executing`、`controller_checking`、`independent_reviewing`、`closure_preparing`、`human_closure_confirming` |
| `workcase-plan-version` | `plan_version` | integer | 当前规范化计划投影的版本身份 | 不表示历史次数、Git revision、phase 轮次或结果版本 | 正整数；初值为 1；只有规范化计划投影发生结构差异时精确 +1，禁止跳号和空升版 |
| `workcase-items` | `work_items` | array | 当前计划及执行、恢复和结果判断所需的工作项闭集 | 不表示内部命令、完整过程历史或独立责任集合 | 非空且 `item_id` 唯一；数组位置不表示顺序；成员组合见 §6.4 |
| `workcase-creation-reviews` | `creation_reviews` | array | 当前计划提交 Human 决定前的实际独立方案复核 | 不表示执行批准、历史审核或 Reviewer 拥有否决权 | 非空；全部绑定当前 `plan_version`；不保存旧计划 review |
| `workcase-execution-approval` | `execution_approval` | object | Human 对当前 `plan_version` 的执行批准及其边界 | 不表示当前一定仍可执行、关闭批准、结果真实或新版本获批 | 精确绑定当前 `plan_version`；授权撤回后若依 §6 暂存，只表示此前行动边界，不授权未来行动 |
| `workcase-result-version` | `result_version` | integer | 当前 `plan_version` 下 canonical result projection 的版本身份 | 不表示自检轮次、review 数量或跨计划全局版本 | 正整数；当前计划首次结果为 1；首条 result review 后 projection 变化精确 +1；计划实际升版时失效 |
| `workcase-overall-result-summary` | `result_summary` | string | 当前结果版本的总体实际产物、重要变化和已观察影响 | 不表示计划、验证方法、逐标准判断、过程流水或责任处置 | 非空；属于 canonical result projection；只保留从 item 终值与实际观察可支持的总体结果 |
| `workcase-controller-check-summary` | `controller_check_summary` | string | Controller 自检的覆盖、发现和当前处置 | 不表示独立复核、总体结果、验证全文或 Human 验收 | 非空；属于 canonical result projection；移除前必须将仍有消费价值的内容吸收到终态结果与验证 |
| `workcase-result-reviews` | `result_reviews` | array | 对当前结果版本的实际独立复核与 Controller 当前处置 | 不表示结果正文、Human 关闭决定或审核历史 | 非空；全部绑定当前 `result_version`；结果版本变化时全部失效，不保存旧版 review |
| `workcase-blocking-summary` | `blocking_summary` | string | 整体责任当前为何无法继续、受影响范围与解除条件 | 不表示 waiting 对象、普通困难、风险列表或终态停止边界 | 非空；必须同时说明无法继续的实际原因、受影响范围与可判断的解除条件 |
| `workcase-closure-proposal` | `closure_proposal` | object | 当前提交 Human 判断的完整关闭分类与责任处置方案 | 不表示终态已经成立、结果包或关闭 approval | 必须按 `workcase-closure-proposal` 成员闭集整体形成，禁止持久化半成品；结果与剩余责任一致性见 §6.7 |
| `workcase-closure-outcome` | `closure_outcome` | string | WorkCase 停止时基于实际结果形成的互斥分类 | 不表示 status、停止理由全文、批准或下游完成 | 闭集 `completed`、`partial`、`not-achieved`、`cancelled`；必须满足 §6.7 的结果一致性，不得由 Human 直接改写技术事实 |
| `workcase-item-id` | `item_id` | string | work item 在本对象内稳定唯一的局部身份 | 不表示数组位置、执行顺序或对象身份 | 匹配 `item-[a-z0-9][a-z0-9-]*`；创建后稳定 |
| `workcase-item-goal` | `goal` | string | 该 item 要形成的局部目标状态 | 不表示命令步骤、当前进展或总体目标 | 必填非空；必须共同服务 WorkCase 关闭判断 |
| `workcase-item-expected-result` | `expected_result` | string | 判断该 item 局部交付是否形成的预期结果 | 不表示成功标准全集、验证命令或实际结果 | 必填非空且可据实判断 |
| `workcase-item-status` | `status` | string | item 当前状态 | 不表示完成百分比、phase 或历史状态 | 闭集 `pending`、`in_progress`、`blocked`、`completed`、`cancelled`；字段组合见 §6.4 |
| `workcase-item-depends-on` | `depends_on` | array | 同一 WorkCase 内该 item 的直接前置 item 身份 | 不表示跨 WorkCase 关系、数组顺序或全部传递依赖 | 出现时非空、成员唯一；禁止缺失目标、自指和有向环 |
| `workcase-item-approach-summary` | `approach_summary` | string | 对 Human 批准或接续执行具有独立价值的方法边界 | 不表示步骤、命令、推理或通用模板全文 | 只有方法选择会改变风险、范围、验证或恢复判断时出现；非空 |
| `workcase-item-template-keys` | `template_keys` | array | 当前 item 实际选择使用的行动模板稳定 key | 不表示模板已适用、已执行或成为事实来源 | 出现时至少一项非空唯一字符串；Code 校验成员类型与唯一性 |
| `workcase-item-template-deviation-summary` | `template_deviation_summary` | string | 相对已选模板、会影响批准或接续判断的实际偏离 | 不表示模板运行日志或普通实现选择 | 仅在 `template_keys` 存在且发生有判断价值的偏离时出现；非空 |
| `workcase-item-current-summary` | `current_summary` | string | item 当前已形成事实、当前位置和剩余不确定性 | 不表示预期目标、步骤流水、命令日志或完成声明 | `in_progress`、`blocked` 必填非空；变化时覆盖，不追加历史 |
| `workcase-item-resume-from` | `resume_from` | string | item 在责任可继续时的首个无需猜测的有界恢复动作 | 不表示命令清单、普通下一步、未来计划全文或当前行动授权 | 非空且无需猜测；具体 item 状态中的出现条件唯一见 §6.4 |
| `workcase-item-blocking-summary` | `blocking_summary` | string | item 的具体阻塞事实、影响与解除条件 | 不表示普通困难、waiting 标签或整体责任必然 blocked | 仅 `blocked` 必填非空 |
| `workcase-item-result-summary` | `result_summary` | string | item 的实际终值、影响和未确认边界 | 不表示 expected result、总体结果、验证全文或证明材料 | `completed`、`cancelled` 必填非空；其它状态禁止 |
| `workcase-review-reviewer` | `reviewer` | string | 实际执行该次独立复核的稳定可识别执行者 | 不表示 Controller、Human 或自动独立性证明 | 必填非空；独立性由实际职责判断，Code 只检查形状 |
| `workcase-review-reviewed-at` | `reviewed_at` | string | Reviewer 完成当前复核内容的时间 | 不表示对象更新时间、批准时间或排序身份 | 带时区 RFC 3339 date-time；同一 review 内容变化按获授权更正边界处理 |
| `workcase-review-subject-version` | `subject_version` | integer | 当前 review 所绑定计划或结果的版本 | 不表示 review 次数、phase 轮次或 Git revision | 正整数；由 container 精确绑定 `plan_version` 或 `result_version` |
| `workcase-review-scope` | `scope` | string | Reviewer 实际检查的范围、重点与未覆盖边界 | 不表示 WorkCase scope、结论或反馈 | 必填非空；不得声称未检查内容已覆盖 |
| `workcase-review-conclusion` | `conclusion` | string | Reviewer 对当前对象的咨询性判断 | 不表示自动推进、自动否决或 Human 决定 | 闭集 `pass`、`pass_with_followups`、`changes_required`、`blocked` |
| `workcase-review-feedback` | `feedback` | array | Reviewer 实际发现的可行动问题或限制 | 不表示 Controller 处置、结果正文或历史发现 | `pass_with_followups`、`changes_required`、`blocked` 时必填非空；`pass` 时可省略；成员为非空唯一字符串 |
| `workcase-review-controller-resolution` | `controller_resolution` | string | Controller 对该 review 全部 feedback 的当前处置 | 不表示 Reviewer 修改结论、结果正文或 Human 批准 | 只有实际 feedback 时出现；creation review 在创建前必须完成处置，result review 在进入关闭准备前必须完成处置 |
| `workcase-criterion-id` | `criterion_id` | string | 成功标准在本对象内稳定唯一的身份 | 不表示数组位置、优先级或 work item | 匹配 `criterion-[a-z0-9][a-z0-9-]*`；创建后稳定 |
| `workcase-criterion-statement` | `statement` | string | 可独立检查的一项成功条件 | 不表示步骤、证据、测试命令或结果 | 必填非空；应能区分满足、未满足和未验证 |
| `workcase-result-criterion-id` | `criterion_id` | string | 当前结果所对应成功标准的稳定身份 | 不表示新标准或数组位置 | 必须精确引用当前定义且覆盖一次 |
| `workcase-result-outcome` | `outcome` | string | 该成功标准的当前结果分类 | 不表示 WorkCase closure outcome 或 Human 风险接受 | 闭集 `satisfied`、`not_satisfied`、`not_verified` |
| `workcase-result-summary` | `summary` | string | 该标准为何得到当前 outcome、实际范围和限制 | 不表示总体结果、验证全文或处置决定 | 必填非空；只写实际已知，不把未验证写成未满足或满足 |
| `workcase-proposal-outcome` | `proposed_outcome` | string | Controller 依据当前结果与验证形成、随关闭方案提交 Human 判断是否在该分类下停止的技术分类 | 不表示终态已成立，也不表示 Human 选择或改写技术分类 | 使用与 `closure_outcome` 相同闭集，并按当前 criterion results 与 validation 形成；Human 认为依据不成立时退回修改 |
| `workcase-proposal-disposition-summary` | `proposed_disposition_summary` | string | 拟定的整体停止边界、逐目标转交范围和 accepted-stop 存在提示 | 不表示结果正文、逐项 residual 依据或既成终态 | 必填非空；正文可在 Human 同意后直接成为 terminal disposition，不写“拟”“建议”占位语 |
| `workcase-proposal-residual-decisions` | `residual_decisions` | array | 当前关闭提案识别出的全部剩余责任与处置建议 | 不表示历史 feedback、普通风险或已经成立的终态 | 有剩余责任时必填且按 `residual_id` 唯一；确实没有时省略并由 disposition summary 直接说明 |
| `workcase-residual-decision-id` | `residual_id` | string | 提案内剩余责任的稳定局部身份 | 不表示数组位置或 terminal relation 身份 | 匹配 `residual-[a-z0-9][a-z0-9-]*`；在当前 proposal 内唯一 |
| `workcase-residual-decision-summary` | `summary` | string | 剩余责任的具体事项、停止依据、未知或风险边界 | 不表示目标已经接受、已经完成或 overall disposition | 必填非空；不得把计划中的未来动作写成既成事实 |
| `workcase-residual-decision-disposition` | `proposed_disposition` | string | Controller 对该剩余责任提出的处置方向 | 不表示 Human 决定或 terminal 值 | 闭集 `route`、`accept_stop` |
| `workcase-residual-decision-route-target` | `route_target` | object | `route` 建议对应的当前目标快照绑定 | 不表示 terminal relation 或目标接受 | `route` 时必填，`accept_stop` 时禁止 |
| `workcase-proposed-route-target-governed-project-id` | `governed_project_id` | string | 拟路由目标所属当前管辖项目身份 | 不表示跨项目授权或项目路径 | 必须等于 source 当前选定的同一 `governed_project_id` |
| `workcase-proposed-route-target-fact-type-key` | `fact_type_key` | string | 拟路由目标事实类型 | 不表示关系 key 或类型兼容 | 固定为 `workcase` |
| `workcase-proposed-route-target-object-id` | `object_id` | string | 拟路由目标 WorkCase 稳定身份 | 不表示标题或责任已经覆盖 | 必须引用实际可读且形成时为 open/blocked 的同项目 WorkCase |
| `workcase-proposed-route-target-content-fingerprint` | `content_fingerprint` | string | 目标当次完整 UTF-8 载体 bytes 的 SHA-256 fingerprint | 不表示 Human 阅读、语义充分或证明材料 | 精确匹配 `[0-9a-f]{64}`，不带算法前缀；必须原样复用实际 `read-fact-objects` 返回的 `content_fingerprint`，禁止重新序列化或另算 canonical-object hash；受控事务时重新比较 |
| `workcase-residual-id` | `residual_id` | string | terminal accepted-stop 责任的稳定局部身份 | 不表示 proposal 顺序或 relation identity | 匹配 `residual-[a-z0-9][a-z0-9-]*`；对象内唯一 |
| `workcase-residual-summary` | `summary` | string | Human 已接受不再由当前 WorkCase 推进的具体责任、事实边界和风险 | 不表示已处理、已完成、route target 或建议 | 必填非空；只保留 proposal 中经 Human 决定的 `accept_stop` 项 |
| `workcase-approval-subject-version` | `subject_version` | integer | Human 执行批准所绑定的准确 plan version | 不表示结果版本、review 次数或后续计划 | 正整数且等于当前 `plan_version` |
| `workcase-approval-approved-at` | `approved_at` | string | Human 实际作出该次执行批准的时间 | 不表示对象更新时间、执行开始或关闭时间 | 带时区 RFC 3339 date-time；不得补造 |
| `workcase-approval-summary` | `summary` | string | Human 实际批准的执行范围、限制或条件 | 不表示技术真实性、无限授权或关闭同意 | 必填非空；不得把 Controller 建议改写成 Human 原因 |
| `workcase-approval-source-refs` | `source_refs` | array | 能够稳定回指 Human 实际批准输入的引用 | 不表示证据包、Human 身份证明或批准正文替代物 | 实际存在稳定引用时出现；成员非空唯一；没有可靠引用时省略，不补造 |

同一 `creation_reviews` 或 `result_reviews` 数组内，`reviewer + reviewed_at + subject_version` 三元组必须唯一，并只作为 Code 识别同一 review 事件、执行字段所有权与获授权事实更正的机械复合身份；它不表示数组顺序、审核先后、review 次数或 Reviewer 独立性。Reviewer 自有内容被获授权更正时该三元组保持不变；新的实际复核必须形成新的 `reviewed_at`，不得覆盖既有事件冒充同一次 review。

### 5.8 自然语言字段不可重复边界

| 字段 | 唯一回答的问题 |
|---|---|
| 顶层 `summary` | 活动期有哪些跨 item 的当前焦点、边界或不确定性无法由 phase、waiting、blocking 和 item 无损回答 |
| item `current_summary` | 该 item 当前已经形成什么事实、停在哪里 |
| item `result_summary` | 该 item 最终实际形成或没有形成什么，以及局部影响和未知 |
| success result `summary` | 某一成功标准为何满足、未满足或未验证 |
| `controller_check_summary` | Controller 自检覆盖了什么、发现并处置了什么 |
| 顶层 `result_summary` | 当前结果版本整体实际形成、改变了什么以及观察到什么影响 |
| `validation_summary` | 实际采用了什么验证、覆盖到哪里、观察到什么、失败和未验证范围是什么 |
| `disposition_summary` | 为什么可以停止、哪些责任转交到哪个目标，以及是否存在 accepted-stop 责任 |

同一事实能够由其中一个字段完整回答时，不得换一种措辞复制到其它字段。

## 6. 状态、阶段与生命周期

### 6.1 status 与活动期共同形状

`status` 闭集为 `open`、`blocked`、`closed`：

- `open`：责任可按当前 phase 继续，顶层 `blocking_summary` 禁止；
- `blocked`：当前 phase 没有任何可继续活动，必须有顶层 `blocking_summary`；block 不自动改变 phase；
- `closed`：Human 已依据完整关闭提案决定当前 WorkCase 不再推进，是终态，不正常重开。

全部活动期对象必须具有身份与时间、`status=open|blocked`、`goal`、`scope`、非空成功标准定义、priority、phase、正整数 plan version 和非空 work items。顶层 `summary` 只在具有独立当前快照价值时出现。终态字段 `closure_outcome`、`disposition_summary`、`residual_responsibilities` 和 `routed-to` 在活动期禁止。

closed 对象的必填集是：`object_id`、`fact_type_key`、`title`、`created_at`、`updated_at`、`status=closed`、`goal`、`scope`、`success_criterion_definitions`、`success_criterion_results`、顶层 `result_summary`、`validation_summary`、`closure_outcome` 和 `disposition_summary`。

closed 的条件集只有：实际存在的 `residual_responsibilities`、实际成立的 `routed-to` relations，以及关闭后仍有独立消费价值的 `urls`。必填集不得缺失，条件集不适用时必须省略，两者之外的字段全部禁止。

closed 禁止 `phase`、顶层 `summary`、priority、resume、waiting、blocking、plan version、work items、creation/result reviews、execution approval、result version、controller check 和 closure proposal。closed 没有 `phase=closed`，也没有 `closed_at`。

### 6.2 phase 闭集与含义

| phase | 当前唯一含义 |
|---|---|
| `human_plan_confirming` | 完整计划已经独立复核，正在等待 Human 对当前计划作执行决定 |
| `plan_revising` | WorkCase 建立后的计划正在返修；旧计划、work items 和既有结果事实冻结，不写半成品新计划 |
| `executing` | 按当前批准边界推进 work items，或在撤回后等待 Human 明确下一方向 |
| `controller_checking` | 全部 work items 已 terminal，Controller 正在形成或修正当前完整结果投影 |
| `independent_reviewing` | 当前完整结果投影正在接受实际独立第二视角，或 Controller 正在处置该版本反馈 |
| `closure_preparing` | 当前结果已完成独立复核，全部 feedback 已由 Controller 处置；Controller 正基于已处置内容形成完整关闭提案 |
| `human_closure_confirming` | 完整关闭提案已经形成，正在等待 Human 决定是否关闭及如何处置剩余责任 |

phase 是当前精确位置，不记录阶段历史、轮次或完成百分比。Reviewer conclusion 本身不自动改变 phase。

### 6.3 phase presence

表中 R 为 required，C 为条件出现，F 为 forbidden：

`PreExecutionStopShape` 是 approval 在前置终止结果快照中可缺失的唯一当前结构谓词：phase 必须为 `plan_revising`、`controller_checking`、`independent_reviewing`、`closure_preparing` 或 `human_closure_confirming`；全部 item 必须为带非空 `result_summary` 的 `cancelled`；不得有 `completed`、`in_progress`、`blocked` 或 `pending` item；`result_version` 必须存在，其它结果字段按当前 phase 成立。只有对象满足该当前形状时，Code 才允许结果快照缺失 approval；AI/Human 仍必须核对确无执行事实、Human 曾明确要求不执行并按当前事实收敛。其它结果链形状的 approval 一律必填并绑定当前 `plan_version`。

| phase | creation reviews | execution approval | 当前结果投影 | result reviews | closure proposal | waiting |
|---|---:|---:|---:|---:|---:|---|
| `human_plan_confirming` | R | F | F | F | F | R：Human 判断当前完整计划 |
| `plan_revising` | F | C：既有 approval 通常暂存；只有 `NoExec` 撤回分支或 `PreExecutionStopShape` 可缺失 | 四种冻结形状：全部 F；只有 `result_version` R；`result_version` 与在 `controller_checking` 已合法形成的部分成员原样保留；或 `result_version` 与完整 projection 全部 R | C：进入前存在则原样冻结，不存在则 F；部分 projection 不得存在 review | F | C：实际等待输入、复核或能力 |
| `executing` | F | R | 首次执行 F；同计划从结果阶段返回时只保留 R 的 `result_version`，projection 其余成员 F | F | F | C：实际外部等待；普通 pending item 不算 waiting |
| `controller_checking` | F | R；仅 `PreExecutionStopShape` F | `result_version` R；projection 成员可在当前检查点分别 C，但每个数组一旦存在必须完整覆盖；离开到独立复核前全部 R | C：返回自检且仍绑定当前版本时可保留 | F | C |
| `independent_reviewing` | F | R；仅 `PreExecutionStopShape` F | R | C：形成中；离开到 closure 前至少一项 | F | 实际等待 Reviewer 时 R |
| `closure_preparing` | F | R；仅 `PreExecutionStopShape` F | R | R | C：只在完整时整体出现 | C |
| `human_closure_confirming` | F | R；仅 `PreExecutionStopShape` F | R | R | R | R：Human 判断完整关闭提案 |

前置执行终止链只指：链开始时 execution approval 已缺失、全部 item 仍为 `pending` 且没有执行事实，Human 明确要求不进入执行并按当前事实收敛，由专属转换把全部 item 据实写为 `cancelled` 后进入结果链。它可以从 `human_plan_confirming` 发起，也可以从无执行事实且 approval 已被 Human 撤回的 `plan_revising` 发起。普通 approval 缺失不是该例外。

`result_reviews` 只能与完整 canonical result projection 同时存在。`plan_revising` 或 `controller_checking` 中的 version-only / 部分 projection 形状必须缺失 reviews；不得用孤立 review 冒充完整被审主体。

`plan_revising` 的四种结果形状还必须满足以下交叉约束：全部结果字段缺失时 approval 为 C；只有 `result_version` 时，正常返工快照必须保留当前 approval 且至少一项 item 非 terminal，只有 `PreExecutionStopShape` 可以 approval 缺失且全部 item cancelled；部分或完整 projection 必须 `AllTerminal`，只有 `PreExecutionStopShape` 可缺失 approval；只有完整 projection 可同时冻结 reviews。

### 6.3.1 status 转换闭集

| from | to | 成立条件 | 同事务必须发生 |
|---|---|---|---|
| 对象不存在 | `open` | §4.4 受控创建成立 | 建立 `phase=human_plan_confirming` 的完整初态 |
| `open` | `blocked` | 当前 phase 确实没有任何可继续活动 | phase 不变；写非空 `blocking_summary`，实际正在等待对象时写 `waiting_on`；可以同事务只把实际造成整体阻塞的 item 由 `pending` / `in_progress` 改为合法 `blocked` 快照，不得推进其它 item |
| `blocked` | `open` | 已经取得足以解除当前整体阻塞的实际输入或能力 | phase 不变；移除 `blocking_summary`，只按当前 phase 的实际等待情况保留或移除 `waiting_on`；若解除整体阻塞同时使具体 item 可继续，可以同事务只把对应 `blocked` item 改为合法 `in_progress` 快照并重新检查其依赖，其它 item 不得推进 |
| `open` | `closed` | `phase=human_closure_confirming` 且 §6.7、§7 `close-workcase` 全部成立 | 原子形成 closed 必填集与条件集，移除全部活动期字段 |

phase 变化只允许以 before/after 均为 `status=open` 执行；`blocked` 必须先在原 phase 按上表解阻，不得把解阻、方向判断和 phase 跳转隐式合并。before/after 均为 `status=blocked` 时不得推进 item、形成或改写 result projection、新增 review/resolution 或形成 proposal；除 Code 托管的 `updated_at` 外，只允许更新 `blocking_summary`、按实际等待更新/移除 `waiting_on`，以及更正不改变 lifecycle 判断对象的 `title`、priority 或 `urls`，其它顶层字段及嵌套内容全部冻结。`open → blocked` 与 `blocked → open` 仅可附带上表列明、直接建立或解除同一阻塞事实的 item 边，不得夹带其它 item、结果、review、proposal 或 phase 推进。`closed` 不得转回 `open` 或 `blocked`。未在上表出现的 status 变化全部禁止。

### 6.3.2 phase 转换闭集

本表使用以下确定性谓词：

- `PlanΔ`：before/after 的规范化 plan projection 存在结构差异；
- `ResultΔ`：before/after 的完整 canonical result projection 存在结构差异；
- `Reviewed`：存在非空且全部绑定当前 `result_version` 的 result reviews；
- `NoExec`：全部 item 为 `pending`，没有 item current/block/result 字段，也没有 result version、result projection、result reviews 或 proposal；
- `AllTerminal`：全部 item 为 `completed` 或 `cancelled`。

| from phase | to phase | 成立条件 | 同事务必须发生 |
|---|---|---|---|
| `human_plan_confirming` | `executing` | Human 批准当前 plan，且至少一项 item 非 terminal | 写入绑定当前 `plan_version` 的新 approval；移除 creation reviews 与 Human waiting；计划/items 不变，结果字段禁止 |
| `human_plan_confirming` | `plan_revising` | Human 要求改方案，或 Controller 依当前来源判断计划覆盖必须变化 | 移除 creation reviews；原 plan/items 冻结；可行动 feedback 先收敛为明确返修要求，并只按 §6.5 写入语义实际匹配的顶层 `summary`、`resume_from`、`waiting_on` 或 `blocking_summary`；不得补造“返修说明”字段 |
| `human_plan_confirming` | `controller_checking` | 两种且仅两种：`NoExec` 且 Human 明确要求不执行、按当前事实收敛；或 `AllTerminal` 且 Human 批准当前 plan | 前置终止时移除 creation reviews/Human waiting、全部 item 写 `cancelled` 与实际 result summary、approval 缺失；正常批准时写当前版本 approval 并保留 terminal items；两者都写当前计划首个 `result_version=1` |
| `plan_revising` | `human_plan_confirming` | 完整候选计划与 fresh review 成立；发生 `PlanΔ`，或尚无 `result_version` 且同计划需重新请求批准 | `PlanΔ` 时精确 `plan_version+1`、原子替换 plan/items/reviews 并清 approval、result 及 proposal；无 `PlanΔ` 时版本不变、result 必须全部缺失，写 fresh reviews 与 Human waiting |
| `plan_revising` | `executing` | 无 `PlanΔ`，结果形状为全部缺失或只有已分配 `result_version`，至少一项非 terminal，且当前计划执行授权已重新成立 | plan/items/version 不变；保留有效 approval 或写新的同版 approval；清返修 waiting/blocking；已分配 `result_version` 不得删除或重置 |
| `plan_revising` | `controller_checking` | 无 `PlanΔ` 且二选一：`AllTerminal` 且当前 plan approval 已成立；或符合前置执行终止链 | 已有结果时原样保留 result version/projection/reviews；首次结果写 `result_version=1`；前置终止时 approval 缺失且全部 item 写为 `cancelled`；其它 approval 缺失的 terminal 计划必须回 `human_plan_confirming` 取得决定 |
| `executing` | `plan_revising` | Human 或 Controller 判断计划必须改变 | 立即停止未来执行；冻结 plan/items 及已分配结果形状；既有 approval 只表示此前行动边界 |
| `executing` | `controller_checking` | `AllTerminal` | 首次结果写 `result_version=1`；同计划返工后保留已分配版本；projection 成员按当前实际检查点形成 |
| `controller_checking` | `executing` | Controller 决定实际返工，且当前计划执行授权仍成立；或 `PreExecutionStopShape` 后 Human 明确决定执行同一未变 plan | 重开受影响 item；移除 projection/proposal；`Reviewed` 时精确 `result_version+1` 并清 reviews，否则保持版本；前置终止反悔分支必须同事务写入绑定同一 `plan_version` 的新 approval，不补造旧执行事实 |
| `controller_checking` | `plan_revising` | 发现 plan 覆盖必须变化 | 冻结 plan/items/result version/projection/reviews；移除 proposal；approval 仅按 §6.5 暂存 |
| `controller_checking` | `independent_reviewing` | 完整 projection 已形成、校验并回读 | projection/version 不变；实际等待 Reviewer 时写 waiting；可保留当前版本既有 reviews |
| `controller_checking` | `closure_preparing` | `Reviewed`，全部 feedback 已有 Controller resolution，projection 未变 | 保留 result/version/reviews；移除 Reviewer waiting；proposal 可缺失或整体形成 |
| `independent_reviewing` | `controller_checking` | Controller 需修正结果或判断返工 | 首先原样保留 projection/version/reviews；后续实际改 projection 时按 §6.6 升版失效；feedback resolution 在离开 `independent_reviewing` 前完成 |
| `independent_reviewing` | `plan_revising` | feedback 或新事实要求改变 plan | 冻结 plan/items/result version/projection/reviews；proposal 缺失 |
| `independent_reviewing` | `closure_preparing` | 至少一项 review，全部 feedback 已处置，projection 未变 | 保留 result/version/reviews；开始形成 proposal |
| `closure_preparing` | `controller_checking` | 需修改结果、补验证、追加复核或重新执行，但 plan 不变 | 移除 proposal；先原样保留 result/version/reviews，再由 `controller_checking` 的唯一转换处理实际影响 |
| `closure_preparing` | `plan_revising` | 需改变 plan | 移除 proposal；冻结 plan/items/result version/projection/reviews |
| `closure_preparing` | `human_closure_confirming` | 完整 proposal、全部 route target 及 fingerprint 成立，source 已无 `depends-on`，终态保留审查已按 §6.7 完成 | 保留完整质量链与 proposal；写 Human waiting；任何即将移除字段和旧依赖中仍有终态消费价值的事实已吸收到保留字段 |
| `human_closure_confirming` | `closure_preparing` | Human 要求修改分类、停止边界或责任处置；或 Controller / Code 依目标重读、指纹比较或关系检查确认当前 proposal 已陈旧，但 plan 与 result 仍成立 | 移除旧 proposal 后重建；plan/result/reviews 不变；原 Human 决定不得沿用到改变后的判断对象 |
| `human_closure_confirming` | `controller_checking` | Human 要求修改结果、补验证、追加复核或重新执行，但 plan 不变；或 Controller 依新事实或失败校验确认当前 result / validation / review 已不可用 | 移除 proposal；先原样保留 result/version/reviews，再由结果链唯一转换处理；原 Human 决定不得沿用 |
| `human_closure_confirming` | `plan_revising` | Human 要求改变 plan projection；或 Controller 依新事实确认当前计划边界已失效 | 移除 proposal；冻结 plan/items/result version/projection/reviews；原 Human 决定不得沿用 |

`human_closure_confirming → closed` 不是普通 phase 边，只由 §6.7 的专属关闭事务完成。Human 从关闭待确认要求重新执行或复核时，必须先回 `controller_checking`，不直跳 `executing` 或 `independent_reviewing`。未在上表出现的 phase 边全部禁止。

### 6.3.3 同 phase 更新闭集

| phase | 允许的实质变化 |
|---|---|
| `human_plan_confirming` | 当前 plan version 的实际 creation review、Controller resolution 与 waiting；plan 变化必须转 `plan_revising` |
| `plan_revising` | Human 撤回且 `NoExec` 时可移除 approval；plan/items/result version/projection/reviews 冻结 |
| `executing` | 合法 item 推进、当前快照与实际外部 waiting；同计划重新授权必须实际替换 approval，不改 plan/result version |
| `controller_checking` | 按稳定检查点形成 projection 成员；尚无 review 时可在同版本修改；`Reviewed` 后发生 `ResultΔ` 必须同事务 `result_version+1`、清 reviews/proposal |
| `independent_reviewing` | projection/version 冻结；新增实际 review 或更新 Controller resolution |
| `closure_preparing` | projection/version/reviews 冻结；proposal 只能整体移除或整体写入 |
| `human_closure_confirming` | plan/result/reviews/proposal 全部冻结；改变 Human 判断对象的任何事实必须返回相应 phase |

下列活动期快照更新是上表的公共 overlay，不改变 phase 专属字段所有权：

- 顶层 `summary`、`resume_from` 和 `waiting_on` 可按其当前实际语义在稳定检查点写入、更新或移除；§6.3 要求 waiting 必填时不得省略；
- `title`、priority 和仍有消费价值的 `urls` 可按当前事实更正；不得借这类更正改写 goal、scope、criteria、计划或结果；
- 除 `human_closure_confirming` 始终禁止 outgoing `depends-on` 外，其它活动 phase 只可按 §8 形成、更正或解除 `depends-on`；变更前必须吸收仍有当前价值的依赖边界并完成引用/图检查，`routed-to` 仍禁止；Human 等待期发现新依赖时必须先退回 `closure_preparing` 或更早 phase；
- status 变换、`blocked` 内阻塞原因更新以及对应 `blocking_summary` / 实际 `waiting_on` 的写入和移除只按 §6.3.1，是不受上表限制的 status overlay；`open` 始终禁止顶层 `blocking_summary`。

除上表与公共 overlay 明示授权的更新外，同 phase 其它字段改写必须拒绝。

### 6.4 work item 状态形状

| item status | 必填条件字段 | 禁止条件字段 | 语义边界 |
|---|---|---|---|
| `pending` | none | `current_summary`、`resume_from`、`blocking_summary`、`result_summary` | 计划内尚未开始；不表示被阻塞 |
| `in_progress` | `current_summary`、`resume_from` | `blocking_summary`、`result_summary` | 已有实际推进事实且存在有界继续入口；能否当下继续仍由 status、phase、approval 与当次 Human 指令共同约束，字段存在不构成授权 |
| `blocked` | `current_summary`、`blocking_summary` | `result_summary`；`resume_from` 仅在解阻后的首个动作已清楚时 C | 当前 item 无法继续，不等于整个 WorkCase 必然 blocked |
| `completed` | `result_summary` | `current_summary`、`resume_from`、`blocking_summary` | 实际局部结果已经形成；不自动表示成功标准满足 |
| `cancelled` | `result_summary` | `current_summary`、`resume_from`、`blocking_summary` | 该 item 不再继续；不计为 completed，也不自动决定 closure outcome |

除下文专属边界外，item 状态只在 `phase=executing` 变化：

| from item status | to item status | 成立条件 | 同事务字段变化 |
|---|---|---|---|
| `pending` | `in_progress` | 该 item 实际开始，且全部 `depends_on` 目标为 `completed` | 写非空 current summary 与有界 resume point |
| `pending` | `blocked` | 已据实确认无法开始，且全部 `depends_on` 目标为 `completed` | 写非空 current summary 与 blocking summary；解阻动作已清楚时可写 resume point |
| `pending` | `completed` | 局部结果在不需要持久化中间状态的同一稳定检查点已经形成，且全部 `depends_on` 目标为 `completed` | 写非空 actual result summary；不补造 in-progress 历史 |
| `in_progress` | `blocked` | 当前 item 实际无法继续 | 更新 current summary，写 blocking summary；resume point 只在解阻后入口已清楚时保留 |
| `blocked` | `in_progress` | 实际阻塞已解除，且全部 `depends_on` 目标为 `completed` | 移除 blocking summary，更新 current summary 和可继续 resume point |
| `in_progress` 或 `blocked` | `completed` | 实际局部结果已稳定形成 | 移除 current/resume/blocking，写非空 actual result summary |
| `pending`、`in_progress` 或 `blocked` | `cancelled` | 取消是原批准承诺下的实际终值，或 Human 明确要求按现状停止并进入结果收敛 | 移除 current/resume/blocking，写据实说明未继续范围与已有结果的 result summary；若取消代表改变计划承诺，不走本边，必须先 `executing → plan_revising` 冻结现状，再由 `PlanΔ` 原子替换处理 |

`depends_on` 目标为 `cancelled` 不等于前置已满足；依赖改变时必须进入计划返修，或把受影响 item 据实取消，不得直接开始下游 item。

下列是普通 executing 之外的唯一 item 状态边界：

- 前置执行终止链可在 `human_plan_confirming → controller_checking` 或 `plan_revising → controller_checking` 的同一事务把全部 `pending` 精确写为 `cancelled`；
- `controller_checking → executing` 只可把本次实际返工范围内的 `completed` / `cancelled` 重开为 `in_progress` 或 `blocked`，移除旧 result summary 并写新 current/resume/blocking 合法组合；不得重置为 `pending`，未返工的 terminal item 保持不变；
- `controller_checking` 内可在新事实表明原 terminal 分类记错时把 `completed` 与 `cancelled` 互相更正，必须同时更新 actual result summary；已 `Reviewed` 时仍按 §6.6 升版与重审；
- `PlanΔ` 的原子替换不是旧 item 逐项跳转：新 `item_id` 只能以 `pending` 出现；保留 ID 的已有执行事实原样保留，或在 Human 明确的边界变化下据实收敛为 `blocked` / `cancelled`；不得把已有事实重置为 `pending` 或无声删除。移除已有 ID 前，其独有执行事实必须无损吸收到保留 item 或顶层当前摘要。

同一 item status 内只可按上表形状更新当前快照。`executing` 中已 terminal item 的 actual result summary 发现笔误或事实错误时可及时据实更正而不改 status；terminal `completed` / `cancelled` 分类互换仍只在 `controller_checking` 按结果版本规则执行。未列出的 item status 边全部禁止。`phase=executing` 始终必须至少有一项非 terminal item；最后一项转为 terminal 时必须同事务执行 `executing → controller_checking`，不得留下 `executing + AllTerminal`。

全部 item terminal 是进入 `controller_checking` 的必要条件。item 数组位置、ID 数字尾缀和依赖拓扑都不自动表示“第几项”；只有来源明确存在固定顺序时，派生视图才能表达顺序。

### 6.5 计划投影、批准与返修

canonical plan projection 由以下解析后结构组成：

- `goal`、`scope`；
- 按 `criterion_id` 排序的成功标准定义；
- 按 `item_id` 排序的每项 `item_id`、`goal`、`expected_result`、排序去重后的 `depends_on` / `template_keys`，以及实际存在的 `approach_summary` / `template_deviation_summary`。

原 YAML 数组位置不进入比较；字符串按解析后的精确值比较，Code 不判断自然语言等义或“实质相同”。

规则如下：

1. 创建时 `plan_version=1`；creation reviews 全部绑定该版本；
2. `human_plan_confirming → executing` 必须在同一事务写入绑定当前版本的新 execution approval，移除 creation reviews 与 Human waiting，不建立结果字段；
3. Human 拒绝执行并要求改方案，或 Controller 根据当前来源、新事实或已处置 feedback 判断计划覆盖必须改变时，未来执行立即停止并进入 `plan_revising`；
4. Controller 发起返修时，既有 approval 只作为旧计划此前获批的事实暂存到原子计划替换，不表示仍可执行；只有 Human 明确撤回且没有执行事实时才可提前移除；
5. `plan_revising` 冻结原 plan projection、work items、当前结果形状和已存在的 result reviews；只允许更新顶层 summary、resume、waiting 和 blocking 来表达返修位置，进入时移除 closure proposal。Controller 必须在进入前把仍可行动的 feedback 收敛为明确返修要求；review 的内容和顺序不得在本 phase 改写或删除；
6. 只有完整候选计划、work items 和 fresh 独立方案复核都已形成，才可原子离开 `plan_revising`。projection 有任一结构差异时只能精确 `plan_version + 1`，同一事务写完整新计划与 creation reviews，并移除旧 approval、旧 `result_version`、旧结果投影、result reviews 和 proposal；
7. projection 完全相同时禁止升版和结果版本重置。尚未分配 `result_version` 时，可在 fresh review 后按同一计划版本回到 `human_plan_confirming`，或在当前批准重新成立后返回 `executing`；只有已分配 `result_version` 而没有 projection 时，只能按同计划返工规则返回 `executing`；已有部分或完整 projection 时，必须返回 `controller_checking` 并原样保留当前成员，完整 projection 已有 reviews 时还必须保留同版本冻结语义；
8. 计划替换前，仍有当前价值的实际执行事实必须进入替换后继续存在的 item current/result summary；不能归入单项但仍影响返修判断的跨 item 事实进入顶层 summary，不得为整洁而丢失；

对 PlanΔ 删除一个已有执行事实的旧 `item_id`（包括 `in_progress`、`blocked`、`completed`、`cancelled` 或实际存在的 current/resume/blocking/result 字段），Code 除了检查结构合法性，还必须机械要求一个当次更新的、来源已定义的承接载体：替换后的顶层 `summary` 必须为非空 string，且与替换前的解析值不同。新 item、未改变的旧顶层 summary 以及保留 item 的字段改写都不是这一机械条件的承接载体；保留 `item_id` 的已有执行事实仍按本节要求原样保留，不得为满足这一条而改写。这个条件只确保发生了可回读的承接载体更新，不证明自然语言已无损吸收旧事实；后者仍由 Controller 按本条首段的责任判断，Code 不得以机械通过代替该判断。

9. 涉及 `goal`、`scope` 或成功标准等责任与验收基线的变化，必须先取得 Human 对边界调整的明确决定；Controller 不能自行改写；
10. 局部取消后继续其它工作，且取消代表改变原承诺时，必须形成实际计划结构差异、升版、重审与再批准；取消只是原承诺下的实际结果，或 Human 明确停止整项责任时，走结果与关闭链，不制造假升版。

Human 撤回未来执行授权时，未来行动立即停止，但不抹除既有事实：

- 要求改方案时进入 `plan_revising`；
- 要求按现状停止并提交关闭判断时，把不再继续的 item 据实置为 `cancelled`，全部 terminal 后进入结果链；该指令不替代最终关闭决定；
- 方向不清时保持当前 phase，写 `status=blocked`、`waiting_on` 与 `blocking_summary`，不得替 Human 选择；
- Human 后续明确恢复同一未变化计划时，不升 plan version：以绑定同一版本的新 execution approval 替换或重建旧记录，清除撤回造成的 waiting / blocking。若回到 executing，仍须遵守 §6.6 的同计划结果返回规则。当前来源或未处置 feedback 已要求改计划时，不得用重新授权绕过返修。

### 6.6 canonical result projection 与结果版本

canonical result projection 由以下完整结构组成：

1. 全部 terminal item 的 `item_id + status + result_summary`，按 `item_id` 排序；
2. 精确覆盖全部成功标准的 results，按 `criterion_id` 排序；
3. 顶层 `result_summary`；
4. `controller_check_summary`；
5. `validation_summary`。

集合顺序按稳定 ID 规范化；字符串按解析后的精确值比较。在 `controller_checking` 内，AI 可在稳定检查点逐个写入已经据实形成的 projection 成员；其中任一数组一旦存在就必须完整覆盖，不得持久化半数组。成员尚未全部存在时只是当前检查候选，不得称为完整 canonical result projection，也不得进入独立复核。review、命令或日志不能代替任一成员。

结果规则如下：

1. 全部 item terminal 后才可进入 `controller_checking`；
2. 当前 `plan_version` 首次形成结果时，`result_version` 只能为 1；
3. 当前版本尚无 result review 时，可在 `controller_checking` 内修改 projection 而不升版；
4. 进入 `independent_reviewing` 前 projection 必须完整、校验并回读；形成首条 result review 的 CAS 必须绑定未变化的完整 before projection，并从该时点冻结；
5. 首条 review 后，projection 任一规范化结构差异都必须在同一事务精确 `result_version + 1`、删除全部旧 result reviews 与 closure proposal，再形成新 projection 并重新复核；projection 完全相同禁止升版、跳号或只删 review 绕过冻结；
6. result version 的作用域是当前 plan version。只有 plan projection 实际变化并使 plan version 递增时，才删除旧 result version；新计划首次结果重新从 1 开始。同一 `plan_version` 下不得删除后复用既有结果版本号；
7. 从结果阶段返回 `executing` 时，移除完整 projection 与 proposal，并重开实际返工 item。已有 result review 时必须先 result version +1 并删除全部 reviews；尚无 review 时必须保持原 result version，不得删除、递增或重置。executing 只保留该已分配版本身份，不保留旧 projection 或 reviews；
8. `independent_reviewing → controller_checking` 可以保留仍绑定当前版本的 review 供 Controller 处置；一旦要改 projection，先按第 5 条升版清理；
9. Reviewer conclusion 不自动推进或否决。进入 `closure_preparing` 前至少一项实际独立结果复核已经形成，全部 feedback 已有 Controller resolution，projection 仍完整；
10. Reviewer 自有字段的获授权事实更正与 Controller resolution 更新不属于 result projection 变化，但必须遵守字段所有权、CAS 和同事件边界，不得借更正修改被审主体。

### 6.7 关闭提案、结果分类与原子关闭

`closure_proposal` 只保存当前拟提交 Human 的关闭方案，不复制结果 projection。它必须满足：

- `proposed_outcome` 按下表从当前结果与验证形成；
- `proposed_disposition_summary` 只写整体停止边界、逐目标转交范围、没有剩余责任的结论或 accepted-stop 项存在提示；
- `residual_decisions` 精确覆盖全部当前剩余责任；每项仍适用的 `not_satisfied` / `not_verified` 标准和其它未完成 scope 责任都必须由至少一项 decision 无损覆盖；`route` 必须有 target，`accept_stop` 禁止 target；
- proposal 只整体写入；编辑期间先移除旧 proposal，完整后整体写回；
- 进入 `human_closure_confirming` 前，每个 route target 都已实际回读，责任边界经 AI 判断覆盖待转交事项，并保存完整内容 fingerprint；
- Human 决定前禁止写 terminal outcome、disposition、residual 或 `routed-to`。

剩余责任与 decision 不必机械一一对应；一项 decision 可以完整覆盖多个相关标准，一项标准也可以拆成多个不同去向。Reviewer 在结果复核中检查 result / validation 是否如实暴露失败、未知、影响和潜在剩余责任，但不审核尚未形成的 proposal。Controller 在 `closure_preparing` 负责依已复核结果形成完整处置覆盖，Human 在 `human_closure_confirming` 判断是否接受该最终处置。Code 不判断自然语言覆盖是否充分，但任一结果为 `not_satisfied` 或 `not_verified` 时必须机械要求非空 `residual_decisions`；Controller 尚未能确认全覆盖时不得进入关闭待确认，Human 不接受时必须退回修改。

进入 `human_closure_confirming` 前，Controller 必须对关闭时将移除的顶层 summary、item current/result、controller check、reviews、plan、approval、waiting/blocking 和依赖边做一次终态保留审查：仍用于理解实际结果、标准判断、验证边界、停止原因、责任去向或长期复核资料的内容，必须无损吸收到 `success_criterion_results`、顶层 `result_summary`、`validation_summary`、proposal 的 disposition / residual decisions 或仍有价值的 `urls`；无独立消费价值的过程内容不复制。独立 result review 只需审查它形成时已存在的 result / validation 是否完整暴露了这些事实；后续 proposal 的吸收与责任覆盖由 Controller 收敛、Human 判断，不伪造 Reviewer 对尚未存在内容的审核。WorkCase 不为此新增保留收据；Code 不判断自然语言是否已无损吸收，Controller 或 Human 尚不能确认时必须停止关闭。

| outcome | 与实际结果的一致性 |
|---|---|
| `completed` | 全部成功标准为 `satisfied`，原 scope 内没有未满足或未验证责任 |
| `partial` | 至少一项 `satisfied`，且至少一项 `not_satisfied` 或 `not_verified`，已形成部分稳定价值 |
| `not-achieved` | 没有任何 `satisfied`，且当前结果与验证足以判断没有形成任一成功标准的稳定结果 |
| `cancelled` | 当前结果与验证仍不足以评价前三类，Human 已决定改变方向或不再继续投入 |

停止执行、全部 item cancelled 或 Human 撤回授权，都不自动决定 outcome；仍须按实际成功标准结果和验证边界分类。

`completed` 表示当前责任在原 scope 内没有剩余责任，因此完整 proposal 中必须省略 `residual_decisions`，closed 中必须同时省略 `residual_responsibilities` 和 `routed-to`。其它三种 outcome 按实际未满足、未验证或未完成 scope 责任形成非空处置；不得用空集合或“无剩余”文案消除实际责任。

`human_closure_confirming → closed` 只能由专属原子关闭操作形成：

1. before 仍完整保留当前计划、work item 终值、与当前 plan version 匹配的 execution approval、完整结果 projection、当前 result reviews、proposal 和版本绑定，且已无 `depends-on`；
2. 前置执行终止链是 approval 唯一例外：链开始时 approval 已缺失、没有执行事实、全部 item 为 cancelled；关闭操作必须继续要求 approval 缺失，但 outcome 仍按统一分类；
3. Human 作出决定前，已实际取得并可以阅读目标、scope、成功标准与逐项结果、总体结果、验证边界、独立复核处置和完整 proposal；Human 决定是否关闭、停止边界和责任处置，不为技术结果真实性背书；
4. 操作绑定完整 source before fingerprint、Human 当次决定和 proposal 中全部 route target fingerprint；
5. 操作重新读取每个 target；任何变化、缺失、机械无效、不可读、状态不适合形成关系或 fingerprint 不匹配，都拒绝关闭，source 保持不变，Controller 重建 proposal 后重新取得 Human 决定；
6. after 的 `closure_outcome` 必须精确等于 `proposed_outcome`，`disposition_summary` 必须精确等于 `proposed_disposition_summary`，`residual_responsibilities` 必须精确等于全部 `accept_stop` decision 的 `residual_id + summary`，`routed-to` targets 必须精确等于全部 `route` decision 的稳定三元组按目标去重集合；不得改写 proposal 自然语言、漏项或增加第二目标清单；
7. after 中 `title`、`goal`、`scope`、`success_criterion_definitions`、`success_criterion_results`、`result_summary`、`validation_summary` 与 `urls` 必须与 before 解析后精确相同；身份与 `created_at` 按 05 原样保留，`updated_at` 由 Code 托管；需要修正任一保留事实时必须先退回相应活动 phase，不在 close 事务中夹带更正；
8. routed 项不再复制为 terminal residual；accepted-stop 项不形成 routed-to；
9. 任一校验、CAS、写入或回读失败都不得声称关闭成功；
10. Human 拒绝关闭或要求修改时不压缩对象，按实际影响返回合法 phase；
11. `close-workcase` 对已 closed before 一律拒绝；closed 不正常重开，也不通过重复 close 冒充幂等更正。

closed 的任何更正都必须使用 §7 `correct-closed-workcase`。只要改动 goal、scope、成功标准定义/结果、result summary、validation、outcome、disposition、residual 或责任去向，一律视为实质更正：必须取得与影响范围匹配的新 Human Gate，并绑定当前 closed fingerprint、完整目标 after 与全部 after route target fingerprints。仅更正 `title`，或只更正不改变已记支持范围、限制和关闭判断基础的 `urls`，才可不经新 Human Gate；无法确定时按实质更正处理。两类更正都不得绕过专属事务。

## 7. AI 写回与受控操作

### 7.1 字段所有权

- Reviewer 只形成 `reviewer`、`reviewed_at`、`subject_version`、`scope`、`conclusion` 和 `feedback`；
- Controller 形成 review `controller_resolution`、phase、当前计划、work item 快照、结果、验证与关闭提案；
- Human 决定 execution approval、责任与验收边界变化和最终关闭；
- Code 不生成自然语言事实，也不从 Web、环境、日志或字段缺口推断语义。

普通更新不得改写 Reviewer 自有字段、补造 Human approval、形成 closed 或绕过版本失效规则。事实更正必须使用 05 已授权的更正边界，不能与不相干的生命周期推进合并。

### 7.2 强制写回检查点

| 检查点 | 必须写入的稳定事实 |
|---|---|
| 受控创建 | 完整责任、计划、work items、creation reviews、初始 phase/status 与 Human waiting |
| Human 批准计划 | 新 execution approval、executing phase；同事务移除 creation reviews 与 Human waiting |
| item 开始 | `in_progress`、current summary、resume point |
| item 阻塞或解阻 | item status、blocking/current/resume 的合法组合；整体确实无法继续时同步 WorkCase status/blocking |
| item 完成或取消 | terminal status 与实际 result summary |
| 委派、交接、上下文压缩前或关键中间结果 | 最近稳定 item current/resume；确有跨 item 独立价值时更新顶层 summary |
| 进入计划返修 | 冻结原计划与结果事实，收敛 feedback，停止未来执行 |
| 原子替换计划 | 完整新 plan projection、fresh creation reviews、版本与旧结果/批准失效 |
| 形成结果 | 当前 result version 与完整 canonical result projection |
| 发起和取得独立结果复核 | 完整 projection 已回读；review 绑定准确版本；Controller 处置 feedback |
| 形成关闭提案 | 完整 proposal、实际 target fingerprints 与 Human waiting |
| Human 关闭决定 | 专属原子关闭 after 与成功回读 |

写回发生在稳定语义检查点，不要求记录每条命令或实时事件。意外中断只能恢复到最近一次已写入并成功回读的检查点；不得把聊天记忆或工具输出冒充已写事实。

### 7.3 共用机制与专属操作

WorkCase 的创建、读取、更新和更正都复用 05 的当前事实源选择、Schema 校验和精确回读。创建只复用 05 的受控身份分配与原子创建，没有 before、expected fingerprint 或替换 CAS；只有更新和更正才复用完整 before、expected fingerprint、CAS 与原子替换。WorkCase 额外要求 Code 检查：

- status/phase/presence 与允许转换；
- plan/result 版本、review 和 approval 绑定；
- plan/result projection 的规范化结构差异；
- item 状态组合与依赖图；
- proposal/terminal 分离；
- route target fingerprints、closed 白名单和关系图约束。

WorkCase 的全部活动期写入必须使用 `update-workcase`；关闭必须使用 `close-workcase`；closed 更正必须使用 `correct-closed-workcase`。通用 `update-fact-object` 不接受 WorkCase，不得借完整 after 绕过字段所有权、版本失效、关闭映射或终态更正边界。Human 决定作为受控操作输入被消费，不持久化 `closure_approval` 或证明收据。

### Helper 公开操作

| operation_key | summary | effect | arguments_contract | result_contract |
|---|---|---|---|---|
| `update-workcase` | 对一个已精确读取的活动期 WorkCase 提交完整目标 after，并按本文机械执行字段所有权、版本、失效、phase 与 CAS 检查 | `may_change_state` | `workcase-fact-type::update-workcase 输入与结果` | `workcase-fact-type::update-workcase 输入与结果` |
| `close-workcase` | 消费完整活动期 before、Human 当次关闭决定和目标指纹，原子形成 closed 白名单并回读 | `may_change_state` | `workcase-fact-type::close-workcase 输入与结果` | `workcase-fact-type::close-workcase 输入与结果` |
| `correct-closed-workcase` | 对一个 closed WorkCase 提交完整更正 after，并在需要时消费新 Human 决定与全部 after route target 指纹 | `may_change_state` | `workcase-fact-type::correct-closed-workcase 输入与结果` | `workcase-fact-type::correct-closed-workcase 输入与结果` |

### update-workcase 输入与结果

本操作完整复用 05 §11.7 的 `workspace_root`、`fact_ref`、`expected_content_fingerprint`、`fact_object`、共同请求包装、结果字段和 §11.8 事务；不复制第二套公共字段。额外收紧如下：

- `fact_ref.fact_type_key` 固定为 `workcase`，before 必须是当前 mechanically valid 的活动期 WorkCase。invalid、unavailable、not-found 或只能解析部分字段的 before 一律拒绝且零写入；本操作不提供旧形状转换或 invalid 记录修复入口；
- `fact_object` 是排除 Code 托管身份与时间字段后的完整目标 after，必须仍为活动期；未提交字段表示 after 中不存在，不做部分 merge；
- before 与全部 after 必须满足 §6 的字段所有权、projection、版本、review、approval、proposal 与转换规则；操作不替 Controller 选择 phase、版本或 Human Gate；
- 当次变化消费 Human 的实际决定或授权时，共同 `authorization_reference` 只能回指该 Human 输入；没有可靠引用时不得补造，Code 也不把引用存在解释为语义授权充分。Reviewer 输入只由当次实际 `creation_reviews` / `result_reviews` 及其字段所有权承载，不写入 `authorization_reference`；
- `update-workcase` 的 before 与 after 都不得为 `status=closed`；活动期 before 要形成 closed 必须改用 `close-workcase`，已经 closed 的 before 要更正必须改用 `correct-closed-workcase`；
- 成功与 `no_change` 的结果完整复用 05 §11.7，不新增审核、批准、过程历史或证明 receipt。调用方需要当前对象时使用返回的回读对象或再次精确读取。

### close-workcase 输入与结果

本操作复用 05 §11.7 的共同参数与结果形状、§11.8 的共享事务，并把 `fact_object` 收紧为完整 closed 目标 after：

- before 必须为 `phase=human_closure_confirming` 的 mechanically valid WorkCase，`expected_content_fingerprint` 精确绑定 Human 实际判断的完整 source before；
- 共同 `authorization_reference` 必须回指 Human 当次实际关闭决定；它只用于授权回指，不持久化到 WorkCase，也不证明技术结果真实；
- after 必须完全满足 §6.1 closed 白名单，并由 before 当前 proposal 确定性形成 outcome、disposition、accepted-stop residuals 与去重 `routed-to`；调用方不得提交 proposal target fingerprints 之外的第二目标清单；
- after 中的终态映射和 before 事实保留必须逐值满足 §6.7 第 6–7 项；关闭事务不得同时修正标题、责任、标准、结果、验证或 URL；
- 操作在同一事务内重新读取全部 proposal route targets，逐个精确比较 fingerprint，并检查项目、类型、状态、引用、去重与目标所在项目关系图约束；另对 source 完整检查入向 `depends-on`。任一项不成立时 source 零写入；
- 除且仅除 before 满足 §6.3 `PreExecutionStopShape` 时 approval 必须缺失外，其它 before 必须存在与当前 result 所依据 `plan_version` 匹配的 execution approval；
- `close-workcase` 不提供 `no_change`；before 已 closed 或 after 未形成新的合法 closed 目标时都拒绝。成功结果的共同形状复用 05 §11.7；不返回或保存 closure approval、Human 身份证明、review 正文或质量链 receipt。

### correct-closed-workcase 输入与结果

本操作复用 05 §11.7 的共同参数与结果形状、§11.8 的共享事务，并在领域 `arguments` 中追加必填 `route_target_fingerprints` array 与必填 `independent_review_reference` object-or-null：

- before 必须是 mechanically valid 的 closed WorkCase，after 必须仍完全满足 §6.1 closed 必填集、条件集与禁止集；status 不变，不重开 phase 或补造活动期记录。invalid、unavailable、not-found 或只能解析部分字段的 before 一律拒绝且零写入；本操作不提供旧形状转换或 invalid 记录修复入口；
- 更正只能修复原关闭时已经成立但被记错或遗漏的事实；不得把关闭后才出现的新目标、新责任、新验收边界、target 后续进展或事后方向变化写成原关闭时的事实。新责任必须建立新 WorkCase，必要时由当前 disposition、`routed-to` 链或新对象承接；
- `route_target_fingerprints[]` 成员字段闭集为 `target` 和 `content_fingerprint`；`target` 使用 05 稳定三元组，`content_fingerprint` 原样复用该 target 当次 `read-fact-objects` 的完整载体 bytes 指纹；数组必须按目标去重，并与 after 全部 `routed-to` targets 精确相等，没有 target 时为空数组；
- `independent_review_reference` 非空时精确复用 04.Att.01 的单个“来源回指字段” object，不新建裸 string 引用形状；它只定位当次实际独立复核输入，不因存在就证明 Reviewer 独立或结论正确；
- 操作在同一事务重新读取全部 after targets 并比较指纹。before 已有且 after 未变的 target 可以已 closed；after 新增的 target 在形成时必须为同项目 mechanically valid `open` / `blocked` WorkCase，并完成引用、去重、自指、有向环、入向责任与关系图检查；任一 target 缺失、不可读、指纹变化或检查未完成时 source 零写入；
- 改变 goal、scope、criteria definitions/results、result summary、validation、outcome、disposition、residual 或 `routed-to` 时，必须先完成一次实际独立复核及 Controller 处置，`independent_review_reference` 必须为指向该当次输入的非空稳定引用；共同 `authorization_reference` 必须回指与完整 before/after、复核结果和全部 target fingerprints 匹配的 Human 新决定。两个引用只是当次输入定位，不持久化为证明包；Code 不判断复核独立性或决定自然语言充分性，AI 不得用笔误名义绕过 Gate；
- after 必须继续满足 §6.7 outcome 一致性与剩余责任完整处置；任一 criterion result 为 `not_satisfied` 或 `not_verified` 时，Code 必须要求 after 至少存在一项 `residual_responsibilities` 或 `routed-to`；Controller、Reviewer 与 Human 必须确认 disposition + residual/routes 无损覆盖全部仍适用的未完成 scope，Code 不猜测自然语言对应；
- 只更正 `title`，或只更正不改变已记支持范围、限制和关闭判断基础的 `urls` 时，array 型 `authorization_reference` 可以省略或使用空列表、不得为 `null`，且 `independent_review_reference` 必须为 `null`；无法确定影响时必须走上一条实质更正路径。活动期的 review/approval 过程字段在形成 closed 时已移除，Human 最终决定由 closed 终态内容表达而不另存收据；不得以笔误更正重建 review、approval 或过程历史；
- 成功与 `no_change` 的结果复用 05 §11.7；必须回读实际 closed after，不返回或保存 Human 决定收据、target 指纹或更正历史。

### 7.4 防止 AI 幻觉

WorkCase 的防幻觉机制是相互约束、独立第二视角和明确未知，不是为每句话建立证明结构：

1. item terminal result、逐标准结果、总体结果、controller check 和 validation 必须构成同一完整 result projection；
2. `not_verified` 与 `not_satisfied` 分离；未执行、无法取得或无法确认的内容不能写成满足或未满足；
3. Reviewer 必须检查总体结果是否超出局部结果和实际观察、是否隐藏失败、未知或副作用；Reviewer 存在不证明正文正确；
4. 首条 result review 后 projection 冻结；结构值变化必须确定性升版并重新复核；
5. route target 必须实际回读并在关闭时再次精确比较 fingerprint；fingerprint 只防陈旧，不判断语义责任是否充分；
6. 路径、命令成功、日志、测试进程退出码、review、approval 或 Human Gate 都不能单独代替自然语言结果与验证边界；
7. 写入或回读失败时只报告实际结果，不能声称状态已经推进；
8. 环境 Hook、adapter、Helper、Web 与 Code 只传递、读取或机械校验来源定义的内容，不生成 WorkCase 自然语言事实。

## 8. 来源、外部资料与关系

### 8.1 来源与验证边界

WorkCase 不要求通用证据结构，也不建立证明包。AI 必须根据当次实际来源和观察据实形成目标、当前快照、结果与验证边界；无法确认的内容保持 unknown 或 `not_verified`。

`validation_summary` 说明实际验证了什么、覆盖到哪里、观察到什么、失败和未验证范围；不保存命令日志。`urls` 只用于关闭后或后续判断仍有长期复核价值的外部 HTTP(S) 资料，并说明支持范围与限制；本机路径、代码、会话、日志和 Git revision 不写入 urls。

### 8.2 关系闭集

WorkCase 只允许两种正向关系；反向导航由 Code 派生，不写第二份权威：

| relation_key | source | target | 唯一语义 |
|---|---|---|---|
| `depends-on` | 同项目 `open` / `blocked` WorkCase | 形成和保留期间均为同项目 `open` / `blocked` WorkCase | source 当前某项行动或关闭判断确实依赖 target 仍在承担的责任 |
| `routed-to` | `closed` WorkCase，只由 `close-workcase` 形成，或由 `correct-closed-workcase` 在相应 Human Gate 下更正原关闭记录错误/遗漏 | 首次形成或更正新增时，target 为同项目 mechanically valid 的 `open` / `blocked` WorkCase；形成后可以继续活动或成为 closed | source 经 Human 关闭决定，将不再由自身承担的剩余责任转交至 target；target 后续进展不构成回溯换路理由 |

共同约束：

- target 暂只允许当前选定的同一 `governed_project_id`；跨项目不进入当前契约；
- 同一 `relation_key + target` 最多一项；数组顺序无语义；没有关系时省略；
- 禁止自指、缺失、无效、不可读目标和同 key 有向环；无法完成项目全集或环检查时交还 unavailable，不得假定无环；
- `depends-on` 与 item `depends_on` 不同，不能相互替代；
- `routed-to` 不能指向 Spark，也不表示某个人或系统另行接受、开始执行或完成责任；
- proposal `route_target` 不是 relation；Human 决定前不写 `routed-to`，terminal relation 不保存 fingerprint 或 residual ID；
- 多项责任可去往同一 target，终态只保留一条去重关系；`disposition_summary` 按目标说明转交范围。

### 8.3 关系失效与入向约束

`depends-on` 解除或 target 准备改变责任边界时，source 必须先把仍影响结果或停止边界的事实吸收到正确自然语言字段并移除关系。target 仍有任何入向 `depends-on` 时不得关闭；closed source 禁止保留 `depends-on`。

`routed-to` 形成时，target 当前 goal/scope 必须按 WorkCase 语义覆盖被转交事项，AI 负责判断，Code 只检查引用、状态、指纹和图约束。形成后即使 target 后来 closed，upstream relation 仍保留；消费者沿 target 的终态处置继续理解责任去向。target 关闭或改变 scope 前必须检查入向 `routed-to`，不得静默丢失已转入责任，必要时由自身终态 disposition、下一跳 routed-to 或 accepted-stop residual 继续说明。

当前契约不定义 WorkCase 的 archive、merge、replace 或 delete 操作，AI、Helper、Code 和 Web 均不得自行实施或用隐藏代替。责任拆分、后续承接或方向变化使用新 WorkCase、当前对象的结果/处置收敛与必要 `routed-to`，不改写或删除已经成立的稳定身份。若 WorkCase 类型本身准备退出，必须先按 05 §12 形成专门处置与事实承接，不得直接删除对象或实现支持。

## 9. 召回、消费与派生视图

### 9.1 渐进式召回

进入新上下文、恢复、压缩或委派时，不无条件恢复全部 WorkCase。只有当前 Human 目标需要项目事实时，AI 才依据 00 与 05 进入事实消费分支。下列语义情形产生 WorkCase 召回机会：

- Human 要求建立、继续、恢复、委派、交接、解阻、复核或关闭一项需跨多步持续承担的责任；
- Human、环境或上层入口提供已知稳定 WorkCase 引用，或当前对象的直接 `depends-on` / `routed-to` 边对当次理解必不可少；
- 创建前需查重、判断更新现有 WorkCase 还是从 Spark 承接，或关闭/终态更正前需核对依赖、转交与入向责任。

`current_workcase_ref` 只能来自 Human 明确引用、当前环境实际提供的稳定引用或已按规则建立的精确绑定。标题相似、唯一候选、优先级、Web 选择状态或关系边都不能自动绑定。

WorkCase F1 恢复基线固定包含当前项目全部 mechanically valid `open` / `blocked` WorkCase；必须沿 `next_cursor` 持续分页，直至读完全部页，才可声称该类型 F1 完整。其最小 `fields` 投影闭集为 `object_id`、`title`、`status`、`phase`、`goal`、`scope`、`summary`、`priority`、`blocking_summary`、`updated_at` 及派生 `work_item_counts`；条件字段在对象中不存在时省略。`work_item_counts` 不写回事实源，字段闭集和顺序为 `pending`、`in_progress`、`blocked`、`completed`、`cancelled`，每项是从当前 `work_items` 机械计数的非负整数。F1 不含摘录，不表示对象全文已读或行动获准。

F2 候选使用 05 已定义的类型、状态、精确引用、直接关系、locator 和字段文本确定性条件，不做语义相似度。省略显式状态时，WorkCase F2 默认也只取 `open` / `blocked`；`closed` 只在显式状态、精确引用或已知直接关系目标下进入候选，不因终态历史无差别恢复。F2 `fields` 投影为：

- active：与 F1 相同，包含派生 `work_item_counts`；
- closed：`object_id`、`title`、`status`、`goal`、`scope`、`result_summary`、`closure_outcome`、`disposition_summary`、`updated_at`；
- 两者都不生成摘录。WorkCase F2 允许精确文本匹配的完整直接字段只有 `title`、`goal`、`scope`、`summary`、`blocking_summary`、`result_summary`、`validation_summary` 和 `disposition_summary`；匹配不会把未入投影的完整字段附带返回。

AI 选中候选后使用稳定引用进入 F3，并按当次语义展开：

- 创建查重展开能够承接同一责任的 WorkCase/Spark 全文，不以卡片标题直接新建；
- 继续执行或交接展开精确当前 WorkCase 的 goal、scope、criteria、plan approval、items、current/resume/waiting/blocking 和当前 phase，并只在当次行动受其约束时继续展开直接 `open` / `blocked` dependencies；
- 方案决定展开完整责任、成功标准、work items 与 creation reviews；结果复核展开完整 result projection、当前 reviews 及未验证边界；
- 关闭待确认展开 Human 需要看到的完整 before、proposal、每个 route target 当前 F3 与引用/入向关系；closed 或其更正则展开全部终态结果、处置、residual、`routed-to` 与仍有效 urls；
- 解阻只展开阻塞/等待、受影响 items、直接依赖和能够判断解除条件的当前事实，不恢复无关历史正文。

每次召回与交付必须说明来源、已读范围、未读、无效、不可读与继续入口。卡片、索引、计数和关系候选不成为第二事实源，也不自动表示相关、适用、当前结论、获准行动或已完成。

### 9.2 活动期与 closed 消费

活动期按当前目标渐进展开目标、scope、criteria、计划、approval、work items、恢复点、结果与关系；不是每个消费者都必须读取全对象。

closed 消费只依赖：

- 原责任、scope 与成功标准；
- 逐项及总体结果；
- validation；
- closure outcome 与 disposition；
- accepted-stop residual；
- routed-to 与仍有效 urls。

不得要求 closed 重新提供 plan、items、reviews、approvals、controller check、phase 或版本。

### 9.3 Web 派生投影

WorkCase 的 Web 列表与详情按 08 §5.3 的页面字段级解析读取来源文件，与其它事实类型一致，不以完整机械校验通过为呈现前提；字段缺失或类型不符时按 08 §5.3 呈现为空或进入未解析结构，未解析结构不得静默丢弃或阻断其它内容呈现。

Web 只显示四个“进展分组”，不是生命周期或 YAML 字段：

| Web 进展分组 | 确定性来源 |
|---|---|
| 方案待确认 | `phase=human_plan_confirming` |
| 推进中 | `plan_revising`、`executing`、`controller_checking`、`independent_reviewing`、`closure_preparing` |
| 关闭待确认 | `phase=human_closure_confirming` |
| 已关闭 | `status=closed` |

status=blocked 仍保留其 phase 所属分组，且在具体 Card 正文契约允许时额外如实表达阻塞。当前 `closure_confirmation` Card 正文尚未定义，它即使处于 `status=blocked` 也不在 Card 中增加阻塞信息；详情页、精确读取诊断和其它已定义的支持范围仍须如实保留 `blocking_summary`。Card 可以派生 item 五状态计数、当前活动 item 和精确环节，但不得把派生结果写回 YAML，不得猜测“第几轮”“第几项”或完成百分比。详情页使用同一信息结构，不按 status 建立不同事实模型；具体 Card 内容与视觉设计由 Web 规范承接，不能反向要求新增事实字段。

## 10. 验证要求

### 10.1 验证对象

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| 类型定义与登记 | 新建或实质修改本文、05.Att.01 或派生 Schema 时 | 结构、字段、绑定、H2 引用与统一登记唯一一致，无悬空、遗漏或第二定义 | 00、01、05、05.Att.01 与本文当前 Working Tree | 规范仓库检查、字段登记检查和当前来源回读 | 当前来源的机械结构一致性；不证明自然语言设计正确 | 本文或附件不得进入当前规则源；先修正唯一来源 |
| 准入与创建 | 建议建立、形成正式计划和受控创建前 | Human 工作意图、单一责任、scope、criteria、查重、净价值、完整计划与实际独立方案复核成立 | Human 当前指令、当前来源、相邻事实回读、候选计划与 Reviewer 实际反馈 | AI 语义审核、事实召回、受控创建校验与创建后回读 | 当次候选的已读范围和创建结果；不证明未来执行成功 | 不创建；更新现有对象、留在当前行动、拆分或转 Spark |
| 活动形状与转换 | 每次读取、写回、phase/status 改变、计划返修或授权变化时 | status/phase/presence、item 组合、plan version、review/approval 绑定和允许转换成立 | 当前对象 before/after、Human 决定、Reviewer feedback 与本文 | Schema、CAS、projection 比较、转换校验和 after 回读 | 可机械检查的形状、版本与转换；不证明当前摘要真实 | 不消费为有效 WorkCase或拒绝转换；修正最小相关范围 |
| 结果与复核 | 形成结果、发起独立复核、处置反馈或改变 projection 时 | projection 完整、criterion 全覆盖、版本冻结、实际独立 review 与 Controller resolution 成立 | item 终值、当前结果与 validation、Reviewer 实际输出 | AI 结果审核、规范化 projection 比较、CAS、review/版本检查 | 当次结果包结构、已读观察和 review 绑定；不证明技术结论天然正确 | 不进入关闭准备；补事实、升版、清旧 review 或重新复核 |
| 关闭提案与终态 | 形成 proposal、进入 Human 关闭 Gate、执行关闭或终态更正时 | proposal 完整、outcome 一致、target 重读、Human 决定、原子 close 与 closed 白名单成立 | 完整 source before、Human 当次决定、目标当前快照与 fingerprints | AI 责任处置审核、target 回读、CAS、专属关闭和 closed after 回读 | 当次停止边界、机械原子性和实际写入结果；不证明 target 已接受或技术事实无误 | source 保持活动期，不声明关闭；重建提案或重新取得 Human 决定 |
| 关系 | 新增、移除、读取依赖、target 变更或任一对象关闭前 | source/target 状态、同项目、唯一性、无自指/环、入向约束与责任边界成立 | source/target 当前对象、项目对象全集和本文关系语义 | 引用回读、图检查、AI 责任边界审核 | 稳定引用、状态与已检查图范围；不证明语义责任充分或目标接受 | 移除或修正关系；无法完成检查时交还 unavailable，暂停受影响关闭 |
| 写回与消费 | 每个稳定检查点、上下文接续和信息交付时 | 当前事实源、CAS、原子写入、回读、coverage 与未读边界明确 | Working Tree、实际写入结果、读取结果与稳定引用 | 05 共用写回/读取入口和对象回读 | 已写入、已回读和已交付范围；不证明未读信息不存在 | 只报告实际结果，不声称推进或上下文完整；保留最近有效检查点 |

### 10.2 Code 的机械边界

Code 可以检查：

- Schema、字段闭集、presence、枚举、时间、ID 和 closed 白名单；
- criterion 覆盖、item 条件组合、依赖和关系图；
- plan/result version、review、approval 和 phase 绑定；
- 规范化 projection 的结构差异、确定性升版和失效字段；
- proposal shape、fingerprint、source/target CAS、target 状态与引用；
- 专属关闭操作是否原子写入一个满足终态契约的 after。

Code 不能判断：

- 目标是否值得建立或仍是同一责任；
- Reviewer 是否真正独立；
- 自然语言是否真实、充分、相关或等义；
- criterion outcome、overall outcome 或验证判断是否正确；
- Human 意图、风险接受、方法合理性或 target 责任边界是否语义充分。

### 10.3 最低测试

当前契约的最低测试必须覆盖：

1. open/blocked 与七个 active phase 的全部合法/非法 presence 组合、status 转换闭集、`open → blocked` / `blocked → open` 可附带的唯一 item 边及夹带其它推进的拒绝、before/after 均 blocked 时不得推进的边界、全部列明及未列明 phase 边，以及 closed 必填/条件/禁止集；
2. 受控创建、Human 计划批准、前置执行终止、`PreExecutionStopShape` 的唯一例外、approval 撤回四分流、Controller 发起返修和同计划重新授权；
3. 五种 item 状态的列明边与未列明边、条件字段、依赖只能由 `completed` 满足、缺失/自指/成环、Controller 返工重开、terminal 分类更正、`executing + AllTerminal` 拒绝、无序 item 与模板 key 成员类型/唯一性；
4. `PlanΔ` 的规范化比较、精确 +1、相同计划不升版、新 item 只以 pending 建立、既有执行事实不得重置/静默删除，以及全部四种结果冻结形状的返修退出；
5. criterion results 数组全覆盖或整体缺失、`controller_checking` 稳定逐成员形成、数组禁止半覆盖、进入独立复核前 projection 完整、首条 review 冻结、`ResultΔ` 确定性升版、同版本不重置和返回 executing；
6. Reviewer/Controller 字段所有权、同一数组 review 复合身份重复拒绝、新实际复核使用新 `reviewed_at`、同事件事实更正保持复合身份且与生命周期转换不可混用、返修期 review 冻结不可通过删除绕过版本失效；
7. proposal/terminal 分离、四种 outcome、`completed` 时 proposal residual / terminal residual / `routed-to` 三者全部省略、其它 outcome 对未满足/未验证/未完成 scope 的责任处置、accepted-stop residual、proposal 自然语言与 terminal 的精确映射、before 保留事实精确相等、route target 漂移后合法退回，以及专属原子关闭；
8. `depends-on` / `routed-to` 的 source、target、入向约束、去重、自指、环、跨项目拒绝、首次形成条件和 routed target 后续成为 closed 后的持续读取；
9. `correct-closed-workcase` 的 closed before/after、after 全部 route target 指纹精确集合与重读、新增与未变 target 的不同状态条件、实质更正的 Human Gate 与独立复核引用、非实质更正的引用空值、终态责任覆盖，以及因后来事实回溯改写原关闭历史被拒绝；
10. 未登记字段、半成品结构、空占位、日志/命令/推理字段，以及通用 update 读写 WorkCase、活动期 update 形成 closed、close 更正 closed 均被拒绝；三个 WorkCase 专属操作对 invalid、unavailable、not-found 或只能解析部分字段的 before 必须正向覆盖零写入拒绝，不建立旧形状转换或 invalid 修复正例；
11. 渐进式召回的触发语义、F1/F2 字段闭集与 coverage、active/closed 默认范围、F3 按场景展开、四个 Web 分组的确定性派生，以及派生信息不写回事实源。

测试只针对这份当前契约，不建立历史形状、profile、兼容读取或迁移测试。


## 11. Human Gate

### 11.1 对象外工作意图

Human 对“是否由项目承担并建立 WorkCase”的决定发生在对象外，只授权形成正式计划、独立方案复核和受控创建。Human 已作出范围清楚的决定时，不重复请求同一决定；该决定不授权执行具体计划。

### 11.2 当前计划执行批准

WorkCase 创建后，必须向 Human 展示当前目标、scope、成功标准、work items、重要依赖、具有判断价值的方法边界、验证安排、重要风险和 creation review 的实质反馈处置。Human 明确批准后，才能写 execution approval 并进入 executing。

批准只绑定当前 `plan_version`，不自动授权其它规则保留给 Human 的高影响行动，也不使技术验证或来源适用自动成立。计划 projection 改变必须升版、fresh 独立复核并重新进入本 Gate；同一未变化计划在授权撤回后恢复，按 §6.5 写新的同版本 approval，不制造计划版本。

### 11.3 最终关闭决定

Human 在 `human_closure_confirming` 判断：

- 是否停止当前 WorkCase；
- 是否在当前结果与验证所支持的分类下停止，并接受相应风险；
- 哪些剩余责任转交到哪些稳定 WorkCase；
- 对哪些没有符合转交条件目标的责任作出接受停止决定。

Human 不为技术结果真实性背书。若 Human 认为当前分类或依据不成立，应退回结果、验证或提案修改，不直接把另一分类写成终态事实。决定必须绑定完整 source before 与 route targets，由专属关闭操作消费；不持久化 closure approval。Human 要求修改时，Controller 按修改对象返回 `closure_preparing`、`controller_checking` 或 `plan_revising`；需要重新执行时，必须先返回 `controller_checking`，再按 §6.3.2 的合法边进入 `executing`，不得从关闭待确认直跳执行或先关闭再补写。

### 11.4 其它保留给 Human 的变化

以下变化仍须 Human 决定：

- 改变同一责任的 goal、scope 或成功标准；
- 在当前结果与验证所支持的 `partial`、`not-achieved` 或 `cancelled` 分类下停止，并接受 accepted stop 或残余风险；
- 扩大范围、高影响或不可逆行动；
- 拆分、合并、删除或重组可能丢失身份、当前事实或责任去向；
- closed 实质更正改变原关闭判断基础。

Human 决定、review 和 Code 校验彼此不能替代。


## 12. Stop Conditions

### 12.1 准入与身份

出现以下任一情况，暂停创建或身份变化：

- Human 未明确选择建立项目记录；
- goal、scope 或成功标准不清楚；
- 多个独立关闭责任被捆绑；
- 未查重，或现有对象可以无损更新；
- 来源、管辖项目或当前 Working Tree 无法成立；
- 无法说明对象化净价值。

### 12.2 计划、执行与恢复

出现以下任一情况，暂停受影响推进：

- 计划未实际独立复核或未获 Human 批准即执行；
- plan projection 改变却未升版、fresh review 和再批准；
- Controller 发起返修后仍继续使用旧 approval 行动；
- 通过删除 approval、手改 phase 或假升版掩盖撤回或计划变化；
- 同一计划重新授权时重置 plan/result version；
- item 写成命令、日志、推理、百分比或过期快照；
- in-progress 缺 current/resume，blocked 缺具体事实和解除条件；
- 写回或回读失败却声称检查点成立。

### 12.3 结果与复核

出现以下任一情况，暂停进入下一质量关口：

- item 未全部 terminal 就进入 controller checking；
- result projection 不完整或 criterion results 只覆盖部分标准；
- 把未验证写成满足或未满足；
- Reviewer 不独立、scope 不清，或非 pass conclusion 没有可行动 feedback；
- projection 改变却沿用旧 result version、reviews 或 proposal；
- 把命令成功、日志、review、approval 或 Human 决定当成结果真实性证明；
- Controller 尚未处置 feedback 就进入 closure preparing。

### 12.4 关闭与关系

出现以下任一情况，暂停关闭或关系写入：

- Human 决定前写 terminal outcome、disposition、residual 或 routed-to；
- closure proposal 不完整或保存半成品；
- 关闭时将移除的字段仍含有终态消费价值，却未吸收到结果、验证、proposal 处置或仍有价值的 urls；
- outcome 与 criterion results / validation 不一致；
- outcome 为 `completed` 却仍有 residual decision、terminal residual 或 `routed-to`；
- route target 未实际回读、fingerprint 失配、不可读、状态不合法或责任边界不覆盖；
- 通过普通 update 形成 closed；
- closed 不满足白名单；
- accepted-stop 写成已处理/已完成，或 routed 项仍复制为 residual；
- 关系跨项目、重复、自指、缺失、不可读、成环或违反入向约束；
- 把 routed-to 表达成 target 已接受、已开始或已完成。

### 12.5 能力与失败交还

CAS、原子写入、回读、项目全集、环检查或专属关闭能力不可用时，只暂停最小相关范围并如实交还 unavailable；不得猜测成功、扩大失败范围或用旧行为替代缺失能力。本文不能被用来推导实例、Helper、Code、tests、Web 或行动模板已经实现。
