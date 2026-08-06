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

WorkCase 保存一项已经由 Human 选择交给项目承担、能够独立判断关闭的工作责任。未关闭时，它使 Human 与 AI 能够稳定回答：要达成什么、边界在哪里、以什么标准判断、当前计划是什么、哪些动作与风险已经在执行授权基线中由 Human 决定、哪些工作项已经形成什么事实、现在从哪里继续、什么阻止继续、当前处于哪个质量或 Human 关口。关闭后，它继续回答：原责任与验收基线是什么、实际结果和验证边界是什么、为什么停止，以及剩余责任转交到哪里或为何接受停止。

WorkCase 是当前事实对象，不是实时监控、聊天计划副本、命令清单、AI 推理记录、运行日志或正确性证明包。单次运行只有两个主动 Human 确认：Gate1 对当前计划与完整执行授权基线作出一次执行决定，Gate2 对已复核的结果与完整关闭提案作出一次关闭决定。正常推进路径中，创建前方案复核、Gate1、执行、主控自检、结果复核、主控收敛和 Gate2 都必须实际发生；review 默认由独立 subagent 完成，当前环境明确不支持时只能按 §4.5 的低保证边界降级。Gate1 与 Gate2 之间不得再新增 Human Gate。受控前置执行终止链不补造执行事实；它以 Gate1 未批准时 Human 明确停止决定和据实的 `cancelled` item 终值取代执行，后续主控自检、结果复核、主控收敛和 Gate2 仍必须实际发生。某个质量关口必须发生，不表示其过程记录必须在关闭后永久保留。

### 1.2 活动期与终态价值

活动期信息只在仍约束推进、恢复、授权、复核或关闭判断时保留。被替代计划、旧结果复核、阶段往返、轮次、命令、工具调用和角色流水不进入 WorkCase。实际提交过的差异可能由 Git 保留，但 WorkCase 与 Git 都不承诺完整过程复原。

closed WorkCase 是终态责任与结果记录，不是质量链合规档案。关闭事务必须从完整活动期对象验证当前仍须成立的关口并原子形成精简终态；关闭后只保留仍有查重、结果理解、影响判断、责任去向或后续决策价值的内容。

面向 Human，WorkCase 直接承接 HV1、HV2 和 HV3：Gate1 与 Gate2 分别保存当前完整计划及执行授权基线、经复核结果及关闭提案；批准后把已授权对象、范围和边界与实际计划、进展、结果、恢复和阻塞入口稳定绑定；受控创建、当前 phase、两次 Human Gate 与原子关闭节点均可回读并按来源条件核对。该承接不表示 WorkCase 或 Code 自动保证自然语言提请质量、技术结果正确或 Human 必须批准。

closed WorkCase 保留的重要工作、结果、验证与处置，是 HV4、HV5 的来源输入；本文不记录这些积累后来是否被实际使用或复用、产生了什么可观察效用，也不单独串联长期意图、关键决定与跨 WorkCase 演进，因此不声明 HV4 或完整 HV5 已由 WorkCase 单独满足。

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

本文不复制 05 已定义的通用请求包装、锁、错误档位、CAS、原子文件写入、回读、更正、删除和类型退出机制；只规定这些机制用于 WorkCase 时必须额外满足的条件。本文也不定义具体 CLI、Helper 命令、Web 组件、Agent API 或模板实现。

角色边界如下：

- Human 决定是否建立项目记录、是否批准当前计划、责任与验收基线变化、风险接受和是否按完整关闭提案停止；
- Controller 形成与收敛当前事实、处置复核反馈、选择合法 phase、发起必要返修并组织写回；
- Reviewer 只提供实际只读第二视角并据实披露方法与保证边界，不替 Human 或 Controller 推进状态；
- 执行 AI 在获准 work item 边界内选择具体实现方法，并据实写回稳定检查点；
- Code 只校验来源已经定义的结构、闭集、版本、指纹、CAS、引用和转换条件，不判断自然语言真实性、相关性、风险接受或责任边界是否充分。

## 4. 适用范围

### 4.1 对象建立前的工作意图

Human 明确选择“由项目承担这项工作并建立 WorkCase”是进入正式计划、独立方案复核和受控创建的前提。该选择发生在对象外，不是 WorkCase phase，也不批准尚未形成的计划。Human 初始要求已明确命名 WorkCase、批准为项目责任推进，或以其它作用范围清楚的表达要求建立该记录时，直接消费该工作意图，不为“是否建立 WorkCase”新增一次主动 Human 确认。

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

work item 只承载获批计划内能够实施并形成局部结果的工作，不承载 WorkCase 自身的生命周期关口。`controller_checking`、`independent_reviewing`、`closure_preparing`、`human_closure_confirming` 及其对应的 Controller 自检、独立结果复核、受控提交、关闭提案和 Human Gate，均由 §6 的 phase 链在全部 item terminal 后承接，不得被写成 item 的 goal、expected result、依赖或“最后一步”。执行中形成测试、扫描或其它验证材料可以是 item 局部交付；使用这些材料形成 canonical result projection、完成独立结果复核或取得 Human 关闭决定不是 item。典型非法反例是新增 goal 为“全部实现完成后安排独立结果复核”的 item：该 item 会等待结果复核，而结果复核又要求全部 item terminal，形成循环；把 goal 为“受控提交”或“执行本地提交”的收敛动作写成 item 同样违规——应在全部 item terminal 后由受控提交承接。

Code 不判断自然语言是否属于生命周期关口；Controller 与 Reviewer 必须按本节语义逐项审核，机械测试只固定来源持续交付该边界和明确反例。

尚无可执行目标、scope 或成功标准的内容属于 Spark 候选；当前行动即可完成且没有稳定回读价值的内容留在当前行动；长期规则进入规范；可复用方法进入行动模板。不得把命令、review checklist、纯结果报告或周期运行入口伪装成 WorkCase。

### 4.4 受控创建

受控创建必须一次形成完整目标、scope、成功标准定义、`plan_version=1`、非空 work items、完整 `execution_authorization`、至少一项实际方案复核、priority、`status=open`、`phase=human_plan_confirming` 和 Human waiting，并完成 Schema 校验、写入与回读。创建时全部 work item 必须为 `pending`。`execution_authorization` 必须把全部已知 Human Gate、目标与影响范围、风险、动作上限、禁止项、允许的调整与重试、验证/回滚和超界安全收敛一次呈现给 Human；只能由 Human 完成的前置动作必须在 Gate1 决定前完成或从本次运行范围明确排除。创建前的 Controller 与 Reviewer 必须逐项检查 work item 是否错误吸收 §4.3 的生命周期关口或 Human Gate（含将受控提交、完整结果投影等收敛动作写成 item 的违例），并检查已知授权需求是否已进入基线；命中时当前候选计划不得提交 Human 批准或受控创建，必须先返修。创建前 Reviewer feedback 必须由 Controller 处置；新对象不得带 execution approval 或结果字段。

默认情况下，创建复核使用只读 subagent。若当前环境明确不提供该能力，候选必须在创建时把限制、当前证据、受影响审核类别、低保证差距和停止条件登记到 `execution_authorization.capability_limitations`，并可由同一 AI 以只读 Reviewer 视角完成一次 `same-ai-switched-role-read-only` 创建复核。这个创建 bootstrap 发生在 Gate1 前，不依赖尚未存在的 Gate1 approval；它只形成供 Human 判断的低保证事实，不使 fallback 已获批准，也不得被描述为 subagent、环境独立或等价独立审核。Gate1 必须同时呈现实际创建复核方法、保证差距和拟用于 Gate1 后的 fallback policy；只有 Human 明确接受这份完整基线，WorkCase 才能进入执行。

### 4.5 审核方法与保证边界

WorkCase review 是 Reviewer 对计划版本或结果版本提供的只读第二视角。标准方法是独立 subagent；只有当前环境明确缺少该能力、并满足本节低保证 fallback 约束时，才允许同一 AI 切换 Reviewer 视角。后者仍是实际 review，但不是 subagent 审核、不是执行环境独立审核，也不与标准方法等价。

#### 4.5.1 核心语义

1. **方法必须据实**：subagent review 的 Reviewer 与 Controller 处于不同执行环境；同一 AI 切换视角只能记录为 `same-ai-switched-role-read-only`，不得自称独立 subagent 或隐去保证差距。
2. **判断视角分离**：Reviewer 从第二视角审视计划或结果，不参与形成被审内容，不替 Controller 或 Human 推进状态或作决定。Code 只检查有限结构与引用，不能证明真实职责分离或证据正文。
3. **只读原则**：所有 review 均为只读，Reviewer 不修改任何文件、不创建或更新事实对象、不改变任何状态。Reviewer 的输出仅限于 review 结构中的 Reviewer 自有字段，不写入被审内容。
4. **能力限制先记录**：只有 `availability=unavailable` 且有当前证据时才能启用同一 AI fallback；能力未知、证据缺失、限制未覆盖当前审核类别或任一停止条件不清晰时必须停止，不得降级。
5. **Gate1 分界**：创建 bootstrap 仅为形成 Gate1 可审材料；Gate1 不追认其为独立审核。Gate1 后的 PlanΔ 和 result review 只能使用 Human 已批准且已进入冻结 fingerprint 的 capability limitation/fallback policy，并必须记录当次当前证据与停止条件评估。

#### 4.5.2 可接受的执行方式（闭集）

| 优先级 | 执行方式 | 适用场景 | 限制 |
|--------|----------|----------|------|
| 1 | **委派一个或多个只读 subagent 并行复核** | 环境提供 subagent 能力 | 标准且保证更高；subagent 数量由 Controller 按范围、复杂度和风险判断，所有 subagent 均为只读 |
| 2 | **同一 AI 切换只读 Reviewer 视角** | 环境明确不提供 subagent；创建 bootstrap，或 Gate1 已批准的 PlanΔ/result fallback | 低保证方法；必须绑定 capability limitation、记录当前证据与 assurance gap，且停止条件评估为 `clear`；不得声称独立或等价 |

checklist 与 Helper 只读检查只提供机械或标准化验证，不能单独形成 review conclusion，也不能替代上述实际 Reviewer 输出。

#### 4.5.3 不可接受行为

- 同一 AI 切换视角却自称 subagent、执行环境独立或等价审核
- 冒充独立视角（如 Controller 以 Reviewer 身份自我批准而无实际 subagent 委派）
- 虚假审核声明（如声称已委托 subagent 审核但未实际执行）
- 没有可用的 subagent 能力时不登记限制、当前证据、保证差距和停止条件而直接降级
- Gate1 后使用未被 Gate1 批准、未进入冻结 fingerprint 或未覆盖当前审核类别的 fallback
- 没有可用的 subagent 能力时硬等不推进，或以 subagent 不可用为由跳过必要审核
- 审核中修改被审内容或状态
- 以命令成功、工具输出、测试通过代替审核结论

#### 4.5.4 适用范围

本定义适用于所有 WorkCase 生命周期中的 review 场景，包括：
- 受控创建前的方案复核（creation review）
- 执行完成后的结果复核（result review）
- 授权基线内 PlanΔ 的 fresh 方案复核

方案复核与结果复核各自遵循 §5 中 `workcase-review` 的字段定义和 §6 的版本绑定规则，不因实际方法而改变阶段归属或字段所有权。

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
| `change-log` | conditional | `workcase-fact-type::7. AI 写回与受控操作` |
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
| `workcase-execution-authorization` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-creation-reviews` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-execution-approval` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-result-version` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-overall-result-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-controller-check-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-result-reviews` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-validation-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-blocking-summary` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-closure-proposal` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-spark-suggestions` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |
| `workcase-closure-outcome` | conditional | `workcase-fact-type::6. 状态、阶段与生命周期` |

### workcase 结构准入记录

| information_need | compared_structure_keys | decision | resulting_structure_key | rationale |
|---|---|---|---|---|
| 在 Human 关闭决定前稳定保存一份完整、Gate2 前可修改且不冒充终态的关闭方案 | `workcase-human-approval,workcase-residual-responsibility,workcase-success-result` | `new` | `workcase-closure-proposal` | approval 只记录执行批准，success result 只回答单项标准结果，terminal residual 只保存已经接受停止的责任；三者都不能承载拟定 outcome、整体停止边界和逐项责任建议，也不能提供 proposal 与 terminal 的生命周期隔离 |
| 在关闭方案中逐项表达一项剩余责任、Controller 建议的处置方向和条件 route target 或 Spark suggestion | `relation-target,workcase-residual-responsibility,workcase-success-result,workcase-spark-suggestion` | `differentiate` | `workcase-residual-decision` | relation target 只有稳定目标，terminal residual 已表示 Human 接受停止，success result 只回答标准结果；提案项必须区分 `route_existing`、`suggest_spark` 与 `accept_stop`，并在 Human 决定前保持建议态 |
| 绑定拟路由目标的稳定身份和当次完整内容快照，发现 Human 等待期间的目标漂移 | `relation-target,workcase-residual-decision` | `differentiate` | `workcase-proposed-route-target` | terminal relation target 不保存内容指纹，residual decision 还包含责任与建议；proposal target 只在关闭等待期服务 CAS 与防陈旧，关闭后必须消失 |
| 在 closed 中保存没有符合转交条件目标、且 Human 已接受停止的一项具体责任 | `workcase-residual-decision,workcase-success-result` | `differentiate` | `workcase-residual-responsibility` | proposal decision 尚未成立且可以 route，success result 只说明验收结果；terminal residual 只含稳定身份与具体责任正文，不再重复 disposition 或目标引用 |
| 在关闭方案和 closed 中结构化保留尚未建立 Spark 的后续建议，并区分受限责任与范围外机会 | `workcase-residual-decision,workcase-residual-responsibility` | `new` | `workcase-spark-suggestion` | residual decision 表达当前 scope 责任的处置方向，terminal residual 表达 Human 接受停止；Spark 建议还需在无未来对象 ID 时保留受限原因、影响、恢复条件或范围外机会的准确类型 |
| 保留 Reviewer 对当前计划或结果版本的实际只读第二视角、实际方法和低保证披露，并由 Controller 记录当前处置 | `workcase-review` | `reuse` | `workcase-review` | 当前需求仍是同一 review 结构；`subject_version` 绑定当前被审对象，`actual_method` 与条件字段据实区分 subagent 和同一 AI fallback；字段所有权、失效与出现条件由本章当前契约唯一定义 |
| 保留 Human 对准确计划版本的执行批准，而不持久化关闭决定收据 | `workcase-human-approval` | `reuse` | `workcase-human-approval` | 结构仍只需承载 Human 批准范围、时间与绑定 plan version；关闭决定由专属事务消费，不与 execution approval 共用持久化结构，也不保留为关闭批准服务的旧成员、字段或使用方式 |
| 在 Gate1 前一次呈现本次运行的已知授权动作、上限、禁止项、调整、风险、验证/回滚与超界收敛 | `workcase-human-approval,workcase-item` | `new` | `workcase-execution-authorization` | approval 只记录 Human 已作出的决定，item 只承载局部交付；两者都不能在 Gate1 前作为完整、可审阅且事后冻结的执行授权基线 |
| 在 Gate1 前记录当前环境缺少独立 subagent review 能力、受影响审核类别、可接受的低保证方法与停止边界 | `workcase-execution-authorization,workcase-review` | `new` | `workcase-capability-limitation` | authorization 必须冻结未来 fallback 边界，review 只记录某次实际方法与当前证据；两者不能互相替代，Gate1 也不能把同一 AI review 追认为环境独立 |
| 在授权基线内逐项界定一类动作的目标、影响、风险、回滚与来源规则 | `workcase-execution-authorization` | `new` | `workcase-authorized-action` | 顶层基线需要完整动作集，但不应以连续散文隐藏不同目标与副作用；结构化条目便于 Human 分别批准并便于 Code 检查形状与指纹，不让 Code 判断自然语言授权 |
| 在 Gate1 前声明唯一必经的独立结果复核、其固定 Reviewer 模式和两项已授权 action 引用 | `workcase-execution-authorization,workcase-authorized-action,workcase-review` | `new` | `workcase-quality-gate` | action 条目本身不说明哪项是必经质量关口，review 也不说明计划复核覆盖了完整授权闭环；该有限声明只供 Code 校验枚举、引用、覆盖与冻结，不解释授权散文或证明真实独立性 |

### 类型专属结构定义

| structure_key | meaning | not_meaning | constraints |
|---|---|---|---|
| `workcase-item` | 共同服务同一 WorkCase 关闭判断、具有稳定局部身份、目标、预期结果与当前状态的工作单元 | 不表示命令步骤、临时 todo、执行百分比、工具调用、AI 推理、独立 WorkCase、WorkCase 生命周期关口或 Human Gate | 直接成员闭集由本节字段定义；状态条件字段按 §6.4；依赖只指向同一对象内 item；§4.3 的 phase 关口只能由 WorkCase 生命周期承接 |
| `workcase-review` | Reviewer 对当前计划版本或结果版本提供的实际只读第二视角、实际方法与条件性保证披露，以及 Controller 对反馈的当前处置 | 不表示 Reviewer 拥有流程决定权，也不把同一 AI 切换视角冒充 subagent 或环境独立审核 | container 决定审核对象；creation review 绑定 `plan_version`，result review 绑定当前 `result_version`；Reviewer 字段与 Controller resolution 分属不同所有者 |
| `workcase-human-approval` | Human 对 Gate1 当时计划及完整 execution authorization baseline 作出的执行批准 | 不表示关闭批准、技术验证、基线外动作获批、风险自动消失或字段存在即可继续执行 | 只供 `execution_approval` 使用；subject version、baseline fingerprint、批准范围、时间和真实 Human 来源按成员字段记录；关闭决定不持久化 approval 收据 |
| `workcase-execution-authorization` | Gate1 前形成、Gate1 后冻结的单次 WorkCase 执行授权基线 | 不表示工具白名单、通用授权 token、技术验证已成立、未知风险或范围外动作获准 | 只用于当前 WorkCase 单次运行；必须整体形成；Gate1 后与 goal/scope/criteria 共同经 baseline fingerprint 绑定并保持不变；closed 时移除 |
| `workcase-capability-limitation` | Gate1 前登记的一项已知审核能力缺失、其证据、受影响类别、低保证 fallback 和停止条件 | 不表示能力永远缺失、fallback 已在 Gate1 前获批、同一 AI 已变成独立 subagent 或 Code 已验证证据真实性 | `limitation_id` 在 authorization 内唯一；仅允许当前明确 `unavailable` 的 `independent-subagent-review`；Gate1 后作为冻结 policy 供 PlanΔ/result review 精确引用 |
| `workcase-authorized-action` | Gate1 基线中一项对象、效果、风险与回滚边界可分别审阅的授权动作 | 不表示命令步骤、工具名白名单、动作已执行或来源规则已满足 | 同一基线内 `action_id` 唯一；目标、效果、风险、回滚和规则回指全部非空；Human 对完整基线一次决定不使各条目丢失自身边界 |
| `workcase-quality-gate` | Gate1 前固定声明的标准结果复核质量关口、标准 policy 标识与授权 action 引用 | 不表示 Reviewer 已被实际委派、复核已完成、自然语言授权充分、Reviewer 真实独立或当次实际方法必为 subagent | 当前闭集精确为一个稳定兼容标识 `gate_id=independent-result-review`、`reviewer_mode=independent-read-only`；两者只命名标准关口 policy，不覆盖 review 的 `actual_method`；`delegation_action_id` 与 `result_review_action_id` 必须分别精确引用同一 authorization 内不同的 action_id |
| `workcase-success-criterion` | 一项具有稳定局部身份、可独立检查的成功标准定义 | 不表示执行步骤、结果、验证方法或数组序号 | `criterion_id` 在对象内唯一稳定；statement 与 goal、scope 共同构成验收基线 |
| `workcase-success-result` | 对一项当前成功标准的实际结果判断与范围说明 | 不表示 Code 已证明正文、Human 已验收或命令成功 | 必须按 `criterion_id` 精确覆盖全部当前定义；unknown 通过 `not_verified` 表达，不补猜 |
| `workcase-closure-proposal` | Controller 提交 Human 判断的一份完整关闭方案 | 不表示 Human 已同意、终态已成立、结果主体或证明收据 | 只在关闭准备与关闭待确认期间出现；始终整体形成，不持久化半成品 |
| `workcase-residual-decision` | 关闭提案中一项剩余责任及其 `route_existing`、`suggest_spark` 或 `accept_stop` 建议 | 不表示终态责任已经转交、Spark 已建立或 Human 已接受停止 | route_existing 必须有 proposal target；suggest_spark 必须引用同一 proposal 的 constrained suggestion；accept_stop 二者均禁止；所有当前剩余责任必须精确覆盖 |
| `workcase-proposed-route-target` | 拟路由目标的稳定三元身份与当次完整内容 fingerprint | 不表示 terminal relation、Human 阅读对象、目标接受责任或目标完成 | 只服务关闭事务的目标重读与精确比较；四个成员全部必填，关闭后删除 |
| `workcase-residual-responsibility` | closed 中没有符合转交条件目标、且 Human 已接受停止的一项具体责任 | 不表示建议、已处理、已完成、route target 或其它对象已经承接 | 只含 `residual_id` 与 `summary`；已路由责任不得同时保留为 residual |
| `workcase-spark-suggestion` | 一项尚未建立 Spark、供 Human 日后独立判断的结构化建议 | 不表示 Spark 已建立、已获批、已承接或必须推进 | `constrained_responsibility` 保留当前 scope 内受限事项的原因、影响、恢复条件和后续定位；`follow_up_opportunity` 保留 scope 外机会，不伪造受限原因；不保存未来对象 ID |

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
| `workcase-execution-authorization` | `execution_authorization` | object | Gate1 一次呈现并经批准后冻结的执行授权基线 | 不表示 Human 已批准、每项技术前提已满足、未知风险获准或任意工具可用 | `human_plan_confirming`、`plan_revising`、`executing` 以及正常批准形状的结果链必填；`SafeConvergenceShape` 禁止；Gate1 后与 goal/scope/criteria 共同冻结；完整成员组合见 §6.5；字段存在不替代 `execution_approval` |
| `workcase-creation-reviews` | `creation_reviews` | array | 对当前 `plan_version` 的实际方案复核及其实际方法/保证边界 | 不表示执行批准、历史审核、Reviewer 拥有否决权或 fallback 与 subagent 等价 | 正常活动形状非空；`SafeConvergenceShape` 禁止；全部绑定当前 `plan_version`；计划版本变化时以 fresh review 整体替换，不保存旧计划 review |
| `workcase-execution-approval` | `execution_approval` | object | Human 在 Gate1 对当时计划与冻结执行授权基线作出的一次执行批准 | 不表示关闭批准、结果真实、超出基线的新动作获准或当前计划仍是 Gate1 时版本 | `subject_version` 记录 Gate1 当时计划版本；`baseline_fingerprint` 精确绑定冻结基线；`source_refs` 回指真实 Human 输入；基线内 PlanΔ 不改写 approval |
| `workcase-result-version` | `result_version` | integer | 当前 `plan_version` 下 canonical result projection 的版本身份 | 不表示自检轮次、review 数量或跨计划全局版本 | 正整数；当前计划首次结果为 1；首条 result review 后 projection 变化精确 +1；计划实际升版时失效 |
| `workcase-overall-result-summary` | `result_summary` | string | 当前结果版本的总体实际产物、重要变化和已观察影响 | 不表示计划、验证方法、逐标准判断、过程流水或责任处置 | 非空；属于 canonical result projection；只保留从 item 终值与实际观察可支持的总体结果 |
| `workcase-controller-check-summary` | `controller_check_summary` | string | Controller 自检的覆盖、发现和当前处置 | 不表示独立复核、总体结果、验证全文或 Human 验收 | 非空；属于 canonical result projection；移除前必须将仍有消费价值的内容吸收到终态结果与验证 |
| `workcase-result-reviews` | `result_reviews` | array | 对当前结果版本的实际只读复核、实际方法/保证边界与 Controller 当前处置 | 不表示结果正文、Human 关闭决定、审核历史或同一 AI fallback 已具环境独立性 | 非空；全部绑定当前 `result_version`；结果版本变化时全部失效，不保存旧版 review |
| `workcase-blocking-summary` | `blocking_summary` | string | 整体责任当前为何无法继续、受影响范围与解除条件 | 不表示 waiting 对象、普通困难、风险列表或终态停止边界 | 非空；必须同时说明无法继续的实际原因、受影响范围与可判断的解除条件 |
| `workcase-closure-proposal` | `closure_proposal` | object | 当前提交 Human 判断的完整关闭分类与责任处置方案 | 不表示终态已经成立、结果包或关闭 approval | 必须按 `workcase-closure-proposal` 成员闭集整体形成，禁止持久化半成品；结果与剩余责任一致性见 §6.7 |
| `workcase-spark-suggestions` | `spark_suggestions` | array | 关闭时保留、供 Human 以后判断是否独立建立 Spark 的建议闭集 | 不表示当前 WC 已创建 Spark、未来 ID 或责任已转交 | 只在 closed 出现，必须与关闭前 proposal 的同名数组解析值精确相同；按 `suggestion_id` 唯一；不含任何未来对象引用 |
| `workcase-closure-outcome` | `closure_outcome` | string | WorkCase 停止时基于实际结果形成的互斥分类 | 不表示 status、停止理由全文、批准或下游完成 | 闭集 `completed`、`partial`、`not-achieved`、`cancelled`；必须满足 §6.7 的结果一致性，不得由 Human 直接改写技术事实 |
| `workcase-item-id` | `item_id` | string | work item 在本对象内稳定唯一的局部身份 | 不表示数组位置、执行顺序或对象身份 | 匹配 `item-[a-z0-9][a-z0-9-]*`；创建后稳定 |
| `workcase-item-goal` | `goal` | string | 该 item 要形成的局部目标状态 | 不表示命令步骤、当前进展、总体目标、Controller 自检、独立结果复核、关闭准备或 Human Gate | 必填非空；必须共同服务 WorkCase 关闭判断，且不得吸收 §4.3 的生命周期关口 |
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
| `workcase-authorization-authorized-actions` | `authorized_actions` | array | Gate1 中逐项呈现的已知授权动作闭集 | 不表示工具或命令白名单、动作已执行或未列动作默认允许 | 至少一项；按 `action_id` 唯一；每项使用 `workcase-authorized-action` |
| `workcase-authorization-quality-gates` | `quality_gates` | array | Gate1 前完整授权基线中的必经质量关口声明 | 不表示 Reviewer 身份证明、实际委派记录或结果复核结论 | 新建与 Gate1 批准候选必须精确含当前一个 `workcase-quality-gate`；其进入 canonical execution authorization 与 baseline fingerprint，Gate1 后冻结；存量 Gate1 前对象可缺失但不得借缺失进入 executing |
| `workcase-authorization-action-ceiling` | `action_ceiling` | string | 当前 WorkCase 单次运行不得超过的总体对象、权限、副作用与外部影响上限 | 不表示已列动作的技术前提已成立 | 必填非空；必须能与 scope 及各 action 条目共同判断超界 |
| `workcase-authorization-prohibited-actions` | `prohibited_actions` | array | Gate1 明确不授权的动作、目标或副作用 | 不表示只有列出项才受禁止；未进入 authorized actions 的动作同样未获准 | 非空唯一 string 数组 |
| `workcase-authorization-allowed-adjustments` | `allowed_adjustments` | string | Gate1 后 Controller 可在不改变基线时自动调整计划、重试、重新委派或替换实现方法的范围 | 不表示可改变 goal/scope/criteria、动作上限、风险接受或禁止项 | 必填非空；PlanΔ 仍需 fresh independent review 并按 §6.5 更新 |
| `workcase-authorization-verification-and-rollback` | `verification_and_rollback` | string | 与授权动作相匹配的验证范围、失败恢复和不可回滚边界 | 不表示验证已运行、回滚一定可用或风险已消失 | 必填非空；必须据实包含已知不可回滚部分 |
| `workcase-authorization-out-of-bounds-handling` | `out_of_bounds_handling` | string | 发现未授权动作、新风险或基线改变时的禁止执行、取消受影响 item 与自动结果收敛边界 | 不表示可在执行期索取新授权或把超界风险默认接受 | 必填非空；必须与 §6.5 的安全收敛一致 |
| `workcase-authorization-human-prerequisites` | `human_prerequisites` | array | 只能由 Human 完成、且必须在 Gate1 最终决定前满足或排除的前置条件 | 不表示 Gate1 后可再要求 Human 中断执行 | 存在时为非空唯一 string 数组；Gate1 批准前必须已取得完成依据或从 authorized actions 排除 |
| `workcase-authorization-capability-limitations` | `capability_limitations` | array | Gate1 前登记并提交 Human 判断的当前审核能力限制与 fallback policy 闭集 | 不表示任何限制默认存在、Gate1 前 fallback 已获批准或未来证据无需重检 | 可省略；存在时非空、按 `limitation_id` 唯一，每项使用 `workcase-capability-limitation`；进入 canonical authorization 与 fingerprint，Gate1 后冻结 |
| `workcase-capability-limitation-id` | `limitation_id` | string | authorization 内一项审核能力限制的稳定局部身份 | 不表示对象身份、数组顺序或 review 事件 | 匹配 `limitation-[a-z0-9][a-z0-9-]*`；同一 authorization 内唯一 |
| `workcase-capability-limitation-capability` | `capability` | string | 当前被确认缺失、可能触发低保证 fallback 的能力 | 不表示任意工具不可用或 Reviewer 结论 | 当前闭集精确为 `independent-subagent-review` |
| `workcase-capability-limitation-availability` | `availability` | string | Gate1 材料形成时该能力的实际可用性判断 | 不表示永久状态、未知状态或 Code 已验证环境 | 当前闭集精确为 `unavailable`；未知或无法确认时不得建立 fallback |
| `workcase-capability-limitation-observation-summary` | `observation_summary` | string | 当前环境能力缺失的可审阅事实摘要与观察边界 | 不表示证据本身、永久结论或 Human acceptance | 必填非空；只写当前已知事实 |
| `workcase-capability-limitation-evidence` | `evidence` | array | Gate1 前支持该 availability 判断的当前证据引用或可回读描述 | 不表示 Code 已验证证据语义、未来 review 自动沿用或执行批准 | 非空唯一 string 数组 |
| `workcase-capability-limitation-affected-review-categories` | `affected_review_categories` | array | 该限制与 fallback policy 实际覆盖的审核类别 | 不表示其它类别自动获准降级 | 非空唯一数组；成员闭集 `creation_review`、`plan_delta_review`、`result_review` |
| `workcase-capability-limitation-fallback-policy` | `fallback_policy` | string | Human 在 Gate1 可接受或拒绝的低保证审核方法边界 | 不表示该方法具 subagent 独立性或 Gate1 前已获批准 | 当前闭集精确为 `same-ai-switched-role-read-only` |
| `workcase-capability-limitation-assurance-gap` | `assurance_gap` | string | 相对独立 subagent review 明确存在的保证差距 | 不表示风险已消失、等价性或 Reviewer 结论 | 必填非空；同一 AI review 必须精确重复该值以供呈现和校验 |
| `workcase-capability-limitation-stop-conditions` | `stop_conditions` | array | 不得启用或必须停止 fallback 的可判断边界 | 不表示普通风险列表或可忽略建议 | 非空唯一 string 数组；至少覆盖能力状态未知、当前证据不足、限制未覆盖当前类别或无法保持只读/视角分离 |
| `workcase-authorized-action-id` | `action_id` | string | 授权动作在当前基线内的稳定局部身份 | 不表示执行顺序、工具名或 work item ID | 匹配 `authorization-[a-z0-9][a-z0-9-]*`；基线内唯一；Gate1 后不变 |
| `workcase-authorized-action-summary` | `summary` | string | Human 能直接判断的动作及其目的 | 不表示命令清单、临时步骤或完成声明 | 必填非空 |
| `workcase-authorized-action-target-scope` | `target_scope` | string | 该动作获准影响的对象、路径、环境、事实引用或外部目标范围 | 不表示目标当前存在、可写或来源适用 | 必填非空；不得使用“必要时其它对象”等无界表达 |
| `workcase-authorized-action-effect-scope` | `effect_scope` | string | 该动作允许的写入、删除、委派、提交、发布、安装、外部消息或其它副作用边界 | 不表示未写明的附带影响已获准 | 必填非空；只在本成员明确范围内消费 |
| `workcase-authorized-action-risk-summary` | `risk_summary` | string | Human 在 Gate1 判断的已知风险、未验证范围和残留风险 | 不表示风险已消失、技术验证已通过或未知风险被接受 | 必填非空；没有已识别高影响风险时仍须据实说明当前已检查范围 |
| `workcase-authorized-action-rollback-summary` | `rollback_summary` | string | 该动作的安全退出、可回滚范围和已知不可逆部分 | 不表示回滚已验证或可以覆盖用户既有资产 | 必填非空 |
| `workcase-authorized-action-rule-refs` | `rule_refs` | array | 该动作实际召回的 Human Gate、风险、验证或副作用规则回指 | 不表示规则已自动适用、技术条件已满足或 Human 决定来源 | 非空唯一 string 数组；Human 决定来源只记录在 `execution_approval.source_refs` |
| `workcase-quality-gate-id` | `gate_id` | string | 必经标准质量关口的稳定兼容身份 | 不表示 work item、phase、Review 事件、当次实际方法或自由扩展类型 | 当前闭集精确为 `independent-result-review`；名称不构成实际独立性声明 |
| `workcase-quality-gate-reviewer-mode` | `reviewer_mode` | string | 该关口默认且保证更高的标准 Reviewer policy 标识 | 不表示 Code 能证明实际独立性、任何具体执行者身份或当次 `actual_method` | 当前闭集精确为 `independent-read-only`；冻结 limitation 允许 fallback 时仍保持该标准 policy 标识，实际方法只由 review 据实记录 |
| `workcase-quality-gate-delegation-action-id` | `delegation_action_id` | string | 授权基线中委派标准结果复核或调用已批准 fallback 的 action 引用 | 不表示已发生委派、实际方法为 subagent 或 action 顺序 | 必填，精确引用 `authorized_actions.action_id`，且不得与结果复核引用复用 |
| `workcase-quality-gate-result-review-action-id` | `result_review_action_id` | string | 授权基线中执行实际结果复核的 action 引用 | 不表示复核结论、实际独立性、结果接受或 Human Gate | 必填，精确引用 `authorized_actions.action_id`，且不得与委派引用复用 |
| `workcase-review-reviewer` | `reviewer` | string | 实际执行该次复核的稳定可识别执行者 | 不表示 Controller、Human 或自动独立性证明 | 必填非空；实际方法由 `actual_method` 据实区分，Code 只检查形状 |
| `workcase-review-reviewed-at` | `reviewed_at` | string | Reviewer 完成当前复核内容的时间 | 不表示对象更新时间、批准时间或排序身份 | 带时区 RFC 3339 date-time；同一 review 内容变化按获授权更正边界处理 |
| `workcase-review-subject-version` | `subject_version` | integer | 当前 review 所绑定计划或结果的版本 | 不表示 review 次数、phase 轮次或 Git revision | 正整数；由 container 精确绑定 `plan_version` 或 `result_version` |
| `workcase-review-scope` | `scope` | string | Reviewer 实际检查的范围、重点与未覆盖边界 | 不表示 WorkCase scope、结论或反馈 | 必填非空；不得声称未检查内容已覆盖 |
| `workcase-review-conclusion` | `conclusion` | string | Reviewer 对当前对象的咨询性判断 | 不表示自动推进、自动否决或 Human 决定 | 闭集 `pass`、`pass_with_followups`、`changes_required`、`blocked` |
| `workcase-review-feedback` | `feedback` | array | Reviewer 实际发现的可行动问题或限制 | 不表示 Controller 处置、结果正文或历史发现 | `pass_with_followups`、`changes_required`、`blocked` 时必填非空；`pass` 时可省略；成员为非空唯一字符串 |
| `workcase-review-controller-resolution` | `controller_resolution` | string | Controller 对该 review 全部 feedback 的当前处置 | 不表示 Reviewer 修改结论、结果正文或 Human 批准 | 只有实际 feedback 时出现；creation review 在创建前必须完成处置，result review 在进入关闭准备前必须完成处置 |
| `workcase-creation-review-covered-quality-gate-ids` | `covered_quality_gate_ids` | array | creation review 对当前授权基线必经质量关口的结构化覆盖声明 | 不表示实际结果复核已经发生、Reviewer 独立性证明或 Controller 处置 | 当 authorization 声明 quality_gates 时，当前每项 creation review 必须精确覆盖该固定 gate_id 集合；存量缺失声明的 Gate1 前对象不要求补写，但不能通过新 Gate1 |
| `workcase-review-actual-method` | `actual_method` | string | 当次 review 实际采用的执行方法 | 不表示 policy、保证等价或 Code 已证明真实执行方式 | 可省略以兼容既有合法对象；出现时闭集 `subagent-read-only`、`same-ai-switched-role-read-only`；authorization 含 capability limitations 时当前 reviews 必须出现 |
| `workcase-review-capability-limitation-id` | `capability_limitation_id` | string | 同一 AI fallback 当次引用的冻结 capability limitation | 不表示新授权、自由文本理由或 subagent 身份 | 只随 `actual_method=same-ai-switched-role-read-only` 出现，并精确引用当前 authorization 中覆盖该审核类别的 `limitation_id` |
| `workcase-review-capability-evidence` | `capability_evidence` | array | 当次 review 开始时支持能力仍不可用的当前证据 | 不表示沿用 Gate1 旧证据、Code 已验证语义或永久缺失 | 只随同一 AI fallback 出现；非空唯一 string 数组；必须由 Reviewer/Controller 据实更新 |
| `workcase-review-assurance-gap` | `assurance_gap` | string | 当次同一 AI review 向 Human/Controller 明示的低保证差距 | 不表示可接受风险、独立性或等价保证 | 只随同一 AI fallback 出现；必须与所引用 limitation 的 `assurance_gap` 精确相同 |
| `workcase-review-stop-condition-assessment` | `stop_condition_assessment` | string | 当次 review 对冻结停止条件均未命中的有限声明 | 不表示 Code 已验证证据正文或未来仍可继续 | 只随同一 AI fallback 出现；当前闭集精确为 `clear`；无法确认时不得形成 fallback review |
| `workcase-criterion-id` | `criterion_id` | string | 成功标准在本对象内稳定唯一的身份 | 不表示数组位置、优先级或 work item | 匹配 `criterion-[a-z0-9][a-z0-9-]*`；创建后稳定 |
| `workcase-criterion-statement` | `statement` | string | 可独立检查的一项成功条件 | 不表示步骤、证据、测试命令或结果 | 必填非空；应能区分满足、未满足和未验证 |
| `workcase-result-criterion-id` | `criterion_id` | string | 当前结果所对应成功标准的稳定身份 | 不表示新标准或数组位置 | 必须精确引用当前定义且覆盖一次 |
| `workcase-result-outcome` | `outcome` | string | 该成功标准的当前结果分类 | 不表示 WorkCase closure outcome 或 Human 风险接受 | 闭集 `satisfied`、`not_satisfied`、`not_verified` |
| `workcase-result-summary` | `summary` | string | 该标准为何得到当前 outcome、实际范围和限制 | 不表示总体结果、验证全文或处置决定 | 必填非空；只写实际已知，不把未验证写成未满足或满足 |
| `workcase-proposal-outcome` | `proposed_outcome` | string | Controller 依据当前结果与验证形成、随关闭方案提交 Human 判断是否在该分类下停止的技术分类 | 不表示终态已成立，也不表示 Human 选择或改写技术分类 | 使用与 `closure_outcome` 相同闭集，并按当前 criterion results 与 validation 形成；必须在 Gate2 前修正完整，Gate2 不接受时本次操作零写入且不回退 |
| `workcase-proposal-disposition-summary` | `proposed_disposition_summary` | string | 拟定的整体停止边界、逐目标转交范围和 accepted-stop 存在提示 | 不表示结果正文、逐项 residual 依据或既成终态 | 必填非空；正文可在 Human 同意后直接成为 terminal disposition，不写“拟”“建议”占位语 |
| `workcase-proposal-residual-decisions` | `residual_decisions` | array | 当前关闭提案识别出的全部剩余责任与处置建议 | 不表示历史 feedback、普通风险或已经成立的终态 | 有剩余责任时必填且按 `residual_id` 唯一；确实没有时省略并由 disposition summary 直接说明 |
| `workcase-proposal-spark-suggestions` | `spark_suggestions` | array | 当前关闭方案中的完整 Spark 建议集合 | 不表示已建立对象、route target 或普通无结构待办 | 出现时非空且按 `suggestion_id` 唯一；可同时含受限责任与范围外机会；关闭时整体映射到顶层 `spark_suggestions` |
| `workcase-residual-decision-id` | `residual_id` | string | 提案内剩余责任的稳定局部身份 | 不表示数组位置或 terminal relation 身份 | 匹配 `residual-[a-z0-9][a-z0-9-]*`；在当前 proposal 内唯一 |
| `workcase-residual-decision-summary` | `summary` | string | 剩余责任的具体事项、停止依据、未知或风险边界 | 不表示目标已经接受、已经完成或 overall disposition | 必填非空；不得把计划中的未来动作写成既成事实 |
| `workcase-residual-decision-disposition` | `proposed_disposition` | string | Controller 对该剩余责任提出的处置方向 | 不表示 Human 决定或 terminal 值 | 闭集 `route_existing`、`suggest_spark`、`accept_stop` |
| `workcase-residual-decision-route-target` | `route_target` | object | `route_existing` 建议对应的当前目标快照绑定 | 不表示 terminal relation 或目标接受 | `route_existing` 时必填，其它值时禁止 |
| `workcase-residual-decision-spark-suggestion-id` | `spark_suggestion_id` | string | `suggest_spark` 责任在同一 proposal 中对应的建议身份 | 不表示 Spark object_id、relation target 或未来绑定 | `suggest_spark` 时必填，必须精确引用一项 `suggestion_kind=constrained_responsibility` 的 proposal suggestion；其它处置时禁止 |
| `workcase-proposed-route-target-governed-project-id` | `governed_project_id` | string | 拟路由目标所属当前管辖项目身份 | 不表示跨项目授权或项目路径 | 必须等于 source 当前选定的同一 `governed_project_id` |
| `workcase-proposed-route-target-fact-type-key` | `fact_type_key` | string | 拟路由目标事实类型 | 不表示关系 key 或类型兼容 | 闭集 `workcase`、`spark` |
| `workcase-proposed-route-target-object-id` | `object_id` | string | 拟路由目标稳定身份 | 不表示标题或责任已经覆盖 | 必须引用实际可读且形成时为 open/blocked 的同项目 WorkCase，或 `status=open` 的同项目 Spark |
| `workcase-proposed-route-target-content-fingerprint` | `content_fingerprint` | string | 目标当次完整 UTF-8 载体 bytes 的 SHA-256 fingerprint | 不表示 Human 阅读、语义充分或证明材料 | 精确匹配 `[0-9a-f]{64}`，不带算法前缀；必须原样复用实际 `read-fact-objects` 返回的 `content_fingerprint`，禁止重新序列化或另算 canonical-object hash；受控事务时重新比较 |
| `workcase-residual-id` | `residual_id` | string | terminal accepted-stop 责任的稳定局部身份 | 不表示 proposal 顺序或 relation identity | 匹配 `residual-[a-z0-9][a-z0-9-]*`；对象内唯一 |
| `workcase-residual-summary` | `summary` | string | Human 已接受不再由当前 WorkCase 推进的具体责任、事实边界和风险 | 不表示已处理、已完成、route target 或建议 | 必填非空；只保留 proposal 中经 Human 决定的 `accept_stop` 项 |
| `workcase-spark-suggestion-id` | `suggestion_id` | string | Spark 建议在本 WorkCase 关闭处置中的稳定局部身份 | 不表示未来 Spark object_id 或 residual ID | 匹配 `suggestion-[a-z0-9][a-z0-9-]*`；在数组内唯一 |
| `workcase-spark-suggestion-kind` | `suggestion_kind` | string | 该建议是当前 scope 内的受限责任，还是 scope 外的后续机会 | 不表示优先级、Spark 状态或是否会创建 | 闭集 `constrained_responsibility`、`follow_up_opportunity` |
| `workcase-spark-suggestion-summary` | `summary` | string | 供 Human 快速判断的建议主题与当前边界 | 不表示 Spark 标题、已承接声明或执行计划 | 必填非空 |
| `workcase-spark-suggestion-restriction-reason` | `restriction_reason` | string | 当前 scope 内责任无法继续完成的明确条件限制 | 不表示普通延后理由、计划或范围外机会 | constrained 时必填，follow-up 时禁止；必须是实际受限原因，不得用“建议以后处理”代替 |
| `workcase-spark-suggestion-impact-summary` | `impact_summary` | string | 受限事项对当前结果、验收或风险的实际影响 | 不表示未来 Spark 的成功标准 | constrained 时必填，follow-up 时禁止 |
| `workcase-spark-suggestion-resume-condition` | `resume_condition` | string | 使受限责任将来可以重新判断或推进的可识别条件 | 不表示日期承诺、自动触发或已有承接者 | constrained 时必填，follow-up 时禁止 |
| `workcase-spark-suggestion-follow-up-summary` | `follow_up_summary` | string | 日后独立建立 Spark 时应继续判断的问题、目标或入口 | 不表示新 Spark 正文、强制步骤或未来 ID | 两种 suggestion kind 均必填非空 |
| `workcase-approval-subject-version` | `subject_version` | integer | Human 在 Gate1 实际阅读并批准的当时 plan version | 不表示结果版本、review 次数或基线内自动调整后的当前 plan version | 正整数；形成时等于当时 `plan_version`；Gate1 后不变 |
| `workcase-approval-approved-at` | `approved_at` | string | Human 实际作出该次执行批准的时间 | 不表示对象更新时间、执行开始或关闭时间 | 带时区 RFC 3339 date-time；不得补造 |
| `workcase-approval-summary` | `summary` | string | Human 实际批准的执行范围、限制或条件 | 不表示技术真实性、无限授权或关闭同意 | 必填非空；不得把 Controller 建议改写成 Human 原因 |
| `workcase-approval-baseline-fingerprint` | `baseline_fingerprint` | string | Gate1 实际批准的 canonical execution authorization baseline SHA-256 | 不表示完整 WorkCase 内容指纹、plan version、Human 身份或技术验证摘要 | 必填；精确匹配 `[0-9a-f]{64}` 且等于 §6.5 定义的当前 baseline fingerprint |
| `workcase-approval-source-refs` | `source_refs` | array | 稳定回指 Human 在 Gate1 实际作出批准的输入引用 | 不表示 AI 转述、证据包、Human 身份证明或批准正文替代物 | 必填非空且成员唯一；只能使用当次环境实际提供的 Human 输入稳定引用；无法取得时不得补造 approval，只能进入无有效 approval 安全收敛 |

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

全部活动期对象必须具有身份与时间、`status=open|blocked`、`goal`、`scope`、非空成功标准定义、priority、phase、正整数 plan version 和非空 work items。正常活动形状还必须有全部绑定当前计划版本的非空 `creation_reviews` 与 `execution_authorization`；Gate1 完成后必须同时有与其 baseline fingerprint 匹配的 `execution_approval`。唯一例外是 §6.3 的 `SafeConvergenceShape`：它为了不补造历史 Human 授权或独立方案复核证明，必须同时缺失 `creation_reviews`、`execution_authorization` 与 `execution_approval`，且只能沿结果链向 Gate2 收敛。顶层 `summary` 只在具有独立当前快照价值时出现。终态字段 `closure_outcome`、`disposition_summary`、`residual_responsibilities`、顶层 `spark_suggestions` 和 `routed-to` 在活动期禁止；proposal 内的同名 suggestions 不属于终态字段。

closed 对象的必填集是：`object_id`、`fact_type_key`、`title`、`created_at`、`updated_at`、`status=closed`、`goal`、`scope`、`success_criterion_definitions`、`success_criterion_results`、顶层 `result_summary`、`validation_summary`、`closure_outcome` 和 `disposition_summary`。


closed 禁止 `phase`、顶层 `summary`、priority、resume、waiting、blocking、plan version、work items、execution authorization、creation/result reviews、execution approval、result version、controller check 和 closure proposal。closed 没有 `phase=closed`，也没有 `closed_at`。

### 6.2 phase 闭集与含义

| phase | 当前唯一含义 |
|---|---|
| `human_plan_confirming` | 完整计划、全部已知授权需求与风险基线已经按实际方法复核，正在等待 Gate1 判断计划、授权与保证边界 |
| `plan_revising` | Gate1 前计划正在完善，或 Gate1 后 Controller 在冻结授权基线内自动返修当前计划；旧计划、work items 和既有结果事实冻结，不写半成品新计划 |
| `executing` | 按 Gate1 冻结授权基线与当前已复核计划推进 work items；不等待新 Human 授权 |
| `controller_checking` | 全部 work items 已 terminal，Controller 正在形成或修正当前完整结果投影 |
| `independent_reviewing` | 当前完整结果投影正在接受实际只读第二视角，或 Controller 正在处置该版本反馈；phase 名为稳定兼容标识，不保证实际方法必为 subagent |
| `closure_preparing` | 当前结果已按允许的实际方法完成复核，全部 feedback 已由 Controller 处置；Controller 正基于已处置内容形成完整关闭提案 |
| `human_closure_confirming` | 完整关闭提案已经形成且其它工作全部冻结，正在等待 Gate2 唯一关闭决定 |

phase 是当前精确位置，不记录阶段历史、轮次或完成百分比。Reviewer conclusion 本身不自动改变 phase。

### 6.3 phase presence

表中 R 为 required，C 为条件出现，F 为 forbidden：

`SafeConvergenceShape` 是正常 Gate1 证明无法取得且不得补造时，无当前方案复核、`execution_authorization` / `execution_approval` 对象可以继续保存已发生结果并向 Gate2 安全收敛的唯一当前结构谓词：phase 只能为 `controller_checking`、`independent_reviewing`、`closure_preparing` 或 `human_closure_confirming`；`creation_reviews`、`execution_authorization` 与 `execution_approval` 必须同时缺失；全部 item 必须为带非空 `result_summary` 的 `completed` 或 `cancelled`，不得有 `pending`、`in_progress` 或 `blocked`；`result_version` 必须存在，其它结果字段按当前 phase 成立；对象不得回到 `executing`、`plan_revising` 或 `human_plan_confirming`。该形状同时承接 Gate1 前明确不执行的全 cancelled 前置终止，以及旧对象已有执行事实但无法回指当前 Gate1 完整授权证明或当前 creation review 的结果收敛。它不得被用于恢复执行、添加新动作或伪造历史授权、复核事件。

| phase | execution authorization | creation reviews | execution approval | 当前结果投影 | result reviews | closure proposal | waiting |
|---|---:|---:|---:|---:|---:|---:|---|
| `human_plan_confirming` | R | R | F | F | F | F | R：Gate1 判断当前完整计划与授权基线 |
| `plan_revising` | R | R | C：Gate1 前为 F；Gate1 后必须原样 R | 四种冻结形状：全部 F；只有 `result_version` R；`result_version` 与在 `controller_checking` 已合法形成的部分成员原样保留；或 `result_version` 与完整 projection 全部 R | C：进入前存在则原样冻结，不存在则 F；部分 projection 不得存在 review | F | C：只可等待非 Human 输入、Reviewer 或能力 |
| `executing` | R | R | R | 首次执行 F；同计划从结果阶段返回时只保留 R 的 `result_version`，projection 其余成员 F | F | F | C：只可为实际非 Human 外部等待；普通 pending item 不算 waiting |
| `controller_checking` | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | `result_version` R；projection 成员可在当前检查点分别 C，但每个数组一旦存在必须完整覆盖；离开到独立复核前全部 R | C：返回自检且仍绑定当前版本时可保留 | F | C：不得等待 Human |
| `independent_reviewing` | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R | C：形成中；离开到 closure 前至少一项 | F | 实际等待 Reviewer 时 R |
| `closure_preparing` | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R | R | C：只在完整时整体出现 | C：不得等待 Human |
| `human_closure_confirming` | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R；`SafeConvergenceShape` F | R | R | R | R：Gate2 判断完整关闭提案 |

前置执行终止链只指：Gate1 未批准、全部 item 仍为 `pending` 且没有执行事实，Human 明确要求不进入执行并按当前事实收敛，由专属转换把全部 item 据实写为 `cancelled`、移除未获批的 `creation_reviews` 与 `execution_authorization` 后进入 `SafeConvergenceShape`。旧对象已有 completed/cancelled 执行事实但无可回指的当前 Gate1 证明或当前 creation review 时，也只能以精确事实迁移进入同一 `SafeConvergenceShape`，不补造 review、authorization、approval 或 source refs。

`result_reviews` 只能与完整 canonical result projection 同时存在。`plan_revising` 或 `controller_checking` 中的 version-only / 部分 projection 形状必须缺失 reviews；不得用孤立 review 冒充完整被审主体。

新建候选与 `human_plan_confirming → executing` 的 Gate1 边还必须通过同一最小质量关口检查：`execution_authorization.quality_gates` 精确声明唯一标准 policy `independent-result-review / independent-read-only`，分别引用当前 `authorized_actions` 中不同的委派与结果复核 action；这两个值是稳定兼容的标准 policy 标识，不声明当次实际方法，页面和 Controller 不得据此显示“已经独立复核”。每项当前 `creation_reviews` 精确覆盖该 gate_id。不存在 capability limitation 时，review 可省略兼容字段或明确写 `actual_method=subagent-read-only`；存在 limitation 时，全部当前 review 必须写实际方法，同一 AI review 还必须精确引用覆盖当前类别的 limitation，并写当前 evidence、相同 assurance gap 与 `stop_condition_assessment=clear`。创建前同一 AI review 属于低保证 bootstrap；Gate1 后只有已冻结 policy 可用于 `plan_delta_review` 或 `result_review`。Code 只检查枚举、成员闭集、引用、类别覆盖、字段一致性与后续 fingerprint 冻结，不解释散文、证明证据真实性或把 fallback 追认为独立。缺失、未知模式、未知 action、重复复用、覆盖不足或 fallback 条件不完整时，创建和 Gate1 都零写入拒绝。既有合法对象不因缺少新增可选字段而失效；既有 Gate1 前 active 对象必须形成满足当前关口的 fresh current creation review 和完整当前材料，才可能通过新 Gate1，不得自动迁移或补写历史字段。既有 `SafeConvergenceShape` 与 Gate2/关闭链不要求历史声明或补写。

`plan_revising` 的四种结果形状还必须满足以下交叉约束：Gate1 前 approval 必须缺失，Gate1 后 approval 必须原样保留；只有 `result_version` 时，Gate1 后正常返工快照至少一项 item 非 terminal；部分或完整 projection 必须 `AllTerminal`；只有完整 projection 可同时冻结 result reviews。`SafeConvergenceShape` 不允许 `phase=plan_revising`。

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
| `human_plan_confirming` | `executing` | Gate1 批准当前 plan、完整 execution authorization 和必经质量关口声明，全部 Human prerequisites 已满足或排除，且至少一项 item 非 terminal | 写入 `subject_version=当前 plan_version`、包含质量关口投影的当前 baseline fingerprint 与真实 Human `source_refs` 的新 approval；保留 authorization、plan/items/reviews；移除 Human waiting；结果字段禁止 |
| `human_plan_confirming` | `plan_revising` | Gate1 尚未完成，Human 在同一 Gate1 中要求改方案/授权基线，或 Controller 判断呈现材料必须改变 | approval 仍缺失；原 authorization/plan/items/reviews 冻结；可行动 feedback 收敛为明确返修要求；不补造新授权 |
| `human_plan_confirming` | `controller_checking` | `NoExec` 且 Gate1 明确不批准执行、要求按当前事实收敛；或 `AllTerminal` 且 Gate1 已批准 | 不批准时全部 item 写 `cancelled` 与实际 result summary，移除 creation reviews 与未获批 authorization，approval 缺失，形成 `SafeConvergenceShape`；正常批准时写 approval 并保留 authorization/reviews/terminal items；两者都写 `result_version=1` |
| `plan_revising` | `human_plan_confirming` | Gate1 尚未完成，approval 缺失，完整候选 authorization/plan 与 fresh review 成立 | `PlanΔ` 时精确 `plan_version+1`，原子替换 authorization/plan/items/reviews；无 `PlanΔ` 时版本不变；写 Gate1 waiting；结果字段全部缺失 |
| `plan_revising` | `executing` | Gate1 已完成，authorization 与 approval 原样有效，完整候选 plan 在 baseline 内且 fresh review 成立，至少一项非 terminal | `PlanΔ` 时精确 `plan_version+1`、原子替换 plan/items/reviews；无 `PlanΔ` 时版本不变；authorization/approval 逐值不变；已分配 `result_version` 不删除或重置 |
| `plan_revising` | `controller_checking` | Gate1 已完成且 `AllTerminal`，或 Gate1 前不批准分支正在形成 `SafeConvergenceShape` | 已有结果时原样保留 result version/projection/result reviews；首次结果写 `result_version=1`；无 approval 时必须同时无 creation reviews/authorization 且全部 item terminal |
| `executing` | `plan_revising` | Controller 判断计划可以在当前 baseline 内调整 | 立即停止旧计划的未来行动；冻结 authorization/approval/plan/items 及已分配结果形状；不写 Human waiting |
| `executing` | `controller_checking` | `AllTerminal` | 首次结果写 `result_version=1`；同计划返工后保留已分配版本；projection 成员按当前实际检查点形成 |
| `controller_checking` | `executing` | Controller 决定在当前 baseline 内实际返工，且 authorization/approval 仍成立；`SafeConvergenceShape` 禁止此边 | 重开受影响 item；移除 projection/proposal；`Reviewed` 时精确 `result_version+1` 并清 result reviews，否则保持版本；保留 authorization/approval/creation reviews |
| `controller_checking` | `plan_revising` | 发现 plan 可在 baseline 内调整；`SafeConvergenceShape` 禁止此边 | 冻结 authorization/approval/plan/items/result version/projection/reviews；移除 proposal；不写 Human waiting |
| `controller_checking` | `independent_reviewing` | 完整 projection 已形成、校验并回读 | projection/version 不变；实际等待 Reviewer 时写 waiting；可保留当前版本既有 reviews |
| `controller_checking` | `closure_preparing` | `Reviewed`，全部 feedback 已有 Controller resolution，projection 未变 | 保留 result/version/reviews；移除 Reviewer waiting；proposal 可缺失或整体形成 |
| `independent_reviewing` | `controller_checking` | Controller 需修正结果或判断返工 | 首先原样保留 projection/version/reviews；后续实际改 projection 时按 §6.6 升版失效；feedback resolution 在离开 `independent_reviewing` 前完成 |
| `independent_reviewing` | `plan_revising` | feedback 或新事实要求在 baseline 内改变 plan；`SafeConvergenceShape` 禁止此边 | 冻结 authorization/approval/plan/items/result version/projection/reviews；proposal 缺失 |
| `independent_reviewing` | `closure_preparing` | 至少一项 review，全部 feedback 已处置，projection 未变 | 保留 result/version/reviews；开始形成 proposal |
| `closure_preparing` | `controller_checking` | 需修改结果、补验证、追加复核或重新执行，但 plan 不变 | 移除 proposal；先原样保留 result/version/reviews，再由 `controller_checking` 的唯一转换处理实际影响 |
| `closure_preparing` | `plan_revising` | 需在 baseline 内改变 plan；`SafeConvergenceShape` 禁止此边 | 移除 proposal；冻结 authorization/approval/plan/items/result version/projection/reviews |
| `closure_preparing` | `human_closure_confirming` | 完整 proposal、全部 route_existing target 及 fingerprint 成立，source 已无 `depends-on`，终态保留审查已按 §6.7 完成，现场保留与建议核对已按 §6.8 完成 | 保留完整质量链与 proposal；写 Human waiting；任何即将移除字段和旧依赖中仍有终态消费价值的事实已吸收到保留字段；完整 draft Pitfall 及其 `contributed-to` 已回读，其它后续事项只保留为结果/处置或 Spark suggestions |

`human_closure_confirming → closed` 不是普通 phase 边，只由 §6.7 的专属关闭事务完成。Gate2 开始前所有可修正结果、验证、review、proposal 或 target 的工作必须已完成；进入 `human_closure_confirming` 后不得返回任何早期 phase，也不得以技术失败索取第三次 Human 确认。专属 close 发生 CAS/target drift 时保持原对象与失败诊断，不自动改写 proposal 或重新请求 Human。未在上表出现的 phase 边全部禁止。

### 6.3.3 同 phase 更新闭集

| phase | 允许的实质变化 |
|---|---|
| `human_plan_confirming` | 当前 plan version 的实际 creation review、Controller resolution 与 Gate1 waiting；authorization 或 plan 变化必须转 `plan_revising` |
| `plan_revising` | authorization/approval/plan/items/result version/projection/reviews 冻结；只写非 Human 返修位置、Reviewer/能力 waiting 与实际 blocking；完整候选只在离开该 phase 的原子更新中形成 |
| `executing` | 基线内合法 item 推进、当前快照与实际非 Human 外部 waiting；authorization 与 approval 冻结，不存在重新授权分支 |
| `controller_checking` | 按稳定检查点形成 projection 成员；尚无 review 时可在同版本修改；`Reviewed` 后发生 `ResultΔ` 必须同事务 `result_version+1`、清 reviews/proposal |
| `independent_reviewing` | projection/version 冻结；新增实际 review 或更新 Controller resolution |
| `closure_preparing` | projection/version/reviews 冻结；proposal 只能整体移除或整体写入 |
| `human_closure_confirming` | authorization/approval/plan/result/reviews/proposal 与所有 target 全部冻结；只允许不改变关闭判断对象的当次读取与专属 close |

下列活动期快照更新是上表的公共 overlay，不改变 phase 专属字段所有权：

- 顶层 `summary`、`resume_from` 和 `waiting_on` 可按其当前实际语义在稳定检查点写入、更新或移除；§6.3 要求 waiting 必填时不得省略；`waiting_on` 只在 `human_plan_confirming` 或 `human_closure_confirming` 可以 Human 为等待对象，其它 phase 只能记录 Reviewer、外部输入或能力；
- `title`、priority 和仍有消费价值的 `urls` 可按当前事实更正；不得借这类更正改写 goal、scope、criteria、计划或结果；
- 除 `human_closure_confirming` 始终禁止 outgoing `depends-on` 外，其它活动 phase 只可按 §8 形成、更正或解除 `depends-on`；变更前必须吸收仍有当前价值的依赖边界并完成引用/图检查，`routed-to` 仍禁止；Gate2 发现新依赖时不退回，由当前关闭操作拒绝并交由后续新 WorkCase/Gate1 承接；
- `contributed-to` 只可在 `human_closure_confirming` 以外的活动 phase、且完整 `status=draft` Pitfall target 已由当前 execution authorization 逐项覆盖并创建回读之后按 §8 形成；该边不指向 Spark、ADR 或 Study。关系记错时按事实更正解除或更正，不承载生命周期推进；`blocked` 期间 relations 冻结，不创建 draft 或补边；`human_closure_confirming` 中该边冻结，等待期发现尚未保存的完整 Pitfall 时不得退回；
- `related-to` 只可在活动期对已存在、同项目、mechanically valid 的当前事实形成或依事实更正；不影响 phase、责任或关闭处置，`blocked` 和 `human_closure_confirming` 期间冻结；
- status 变换、`blocked` 内阻塞原因更新以及对应 `blocking_summary` / 实际 `waiting_on` 的写入和移除只按 §6.3.1，是不受上表限制的 status overlay；每个受控写事务按 05 追加的唯一 Code 托管 `change_log` 条目属于该事务的追踪记录，不构成夹带的领域变化；`open` 始终禁止顶层 `blocking_summary`。

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
| `pending`、`in_progress` 或 `blocked` | `cancelled` | 取消是基线内允许的实际终值，或发现继续必须超出 action ceiling、命中 prohibited action、接受新风险或取得 Gate1 后的新 Human 决定 | 移除 current/resume/blocking，写据实说明未继续范围、超界原因与已有结果的 result summary；不改 authorization/approval，不进入 Human waiting；全部 item terminal 后同事务进入 `controller_checking` |

`depends_on` 目标为 `cancelled` 不等于前置已满足；依赖变化可在 baseline 内收敛时进入计划返修，否则把受影响 item 据实取消并进入结果链，不得直接开始下游 item。

下列是普通 executing 之外的唯一 item 状态边界：

- 前置执行终止链可在 `human_plan_confirming → controller_checking` 或 `plan_revising → controller_checking` 的同一事务把全部 `pending` 精确写为 `cancelled`；
- `controller_checking → executing` 只可把本次实际返工范围内的 `completed` / `cancelled` 重开为 `in_progress` 或 `blocked`，移除旧 result summary 并写新 current/resume/blocking 合法组合；不得重置为 `pending`，未返工的 terminal item 保持不变；
- `controller_checking` 内可在新事实表明原 terminal 分类记错时把 `completed` 与 `cancelled` 互相更正，必须同时更新 actual result summary；已 `Reviewed` 时仍按 §6.6 升版与重审；
- 基线内 `PlanΔ` 的原子替换不是旧 item 逐项跳转：新 `item_id` 只能以 `pending` 出现；保留 ID 的已有执行事实原样保留，或在 `allowed_adjustments` 已列范围内据实收敛为 `blocked` / `cancelled`；不得把已有事实重置为 `pending` 或无声删除。移除已有 ID 前，其独有执行事实必须无损吸收到保留 item 或顶层当前摘要。

同一 item status 内只可按上表形状更新当前快照。`executing` 中已 terminal item 的 actual result summary 发现笔误或事实错误时可及时据实更正而不改 status；terminal `completed` / `cancelled` 分类互换仍只在 `controller_checking` 按结果版本规则执行。未列出的 item status 边全部禁止。`phase=executing` 始终必须至少有一项非 terminal item；最后一项转为 terminal 时必须同事务执行 `executing → controller_checking`，不得留下 `executing + AllTerminal`。

全部 item terminal 是进入 `controller_checking` 的必要条件。item 数组位置、ID 数字尾缀和依赖拓扑都不自动表示“第几项”；只有来源明确存在固定顺序时，派生视图才能表达顺序。

### 6.5 计划投影、批准与返修

canonical plan projection 由以下解析后结构组成：

- `goal`、`scope`；
- 按 `criterion_id` 排序的成功标准定义；
- 按 `item_id` 排序的每项 `item_id`、`goal`、`expected_result`、排序去重后的 `depends_on` / `template_keys`，以及实际存在的 `approach_summary` / `template_deviation_summary`。

原 YAML 数组位置不进入比较；字符串按解析后的精确值比较，Code 不判断自然语言等义或“实质相同”。

canonical execution authorization baseline projection 由以下解析后结构组成：

- `goal`、`scope`；
- 按 `criterion_id` 排序的 `criterion_id + statement`；
- 完整 `execution_authorization`：`authorized_actions` 按 `action_id` 排序，每项包含 `action_id`、`summary`、`target_scope`、`effect_scope`、`risk_summary`、`rollback_summary` 与排序去重后的 `rule_refs`；`quality_gates` 按 `gate_id` 排序，每项包含 `gate_id`、`reviewer_mode`、`delegation_action_id` 与 `result_review_action_id`；`capability_limitations` 实际存在时按 `limitation_id` 排序，每项包含 `limitation_id`、`capability`、`availability`、`observation_summary`、`fallback_policy`、`assurance_gap`，以及各自排序去重后的 `evidence`、`affected_review_categories`、`stop_conditions`；并包含 `action_ceiling`、排序去重后的 `prohibited_actions`、`allowed_adjustments`、`verification_and_rollback`、`out_of_bounds_handling`，以及实际存在时排序去重后的 `human_prerequisites`。

Code 必须把该结构编码为 UTF-8 canonical JSON：object keys 按 Unicode code point 升序，array 使用上文规定的稳定排序，string 使用 JSON 标准转义，不写无意义空白；对所得 bytes 计算 SHA-256，保存为 64 位小写十六进制 `baseline_fingerprint`。Code 只判断结构、规范化 bytes、fingerprint 与精确相等；授权条目是否语义覆盖实际动作、风险、目标、影响和回滚，仍由 Controller 与 Reviewer 判断。

规则如下：

1. 创建时 `plan_version=1`；`creation_reviews` 全部绑定该版本，并在正常活动形状的整个生命周期保存当前计划的实际方案复核；`SafeConvergenceShape` 不补造或保留无法成立的历史复核；
2. Gate1 必须一次向 Human 呈现完整 plan projection、work items、creation reviews 与 execution authorization baseline；若存在 capability limitation，还必须明确区分实际 creation review 方法、低保证差距与 Gate1 后拟用 fallback policy。Human 的批准表示接受这份实际保证边界作为当前执行基础，不把既有 same-AI review 追认为独立。`human_plan_confirming → executing` 在同一事务写 `execution_approval`：`subject_version` 是 Gate1 当时呈现的 plan version，`baseline_fingerprint` 精确绑定 Human 所见基线，`source_refs` 必须回指真实 Human 输入；移除 Human waiting，不移除 creation reviews；
3. authorization 字段、fingerprint 或 AI 摘要都不等于 Human approval。没有真实可回指的 Gate1 决定时不得补造 approval/source refs，只能按 `SafeConvergenceShape` 收敛已有事实；
4. Gate1 前可按 feedback 完整修改计划或授权基线、完成 fresh current creation review 并继续在 `human_plan_confirming` 取得一次最终决定；同一 AI bootstrap 只要求候选 limitation 覆盖 `creation_review`，不要求尚未存在的 approval。Gate1 完成后 goal、scope、criteria 与 execution authorization baseline 在本次运行中冻结，不再回到 `human_plan_confirming`；
5. Gate1 后的 `PlanΔ` 只有同时满足以下条件才可自动推进：baseline projection 精确不变；新旧动作都处于 `authorized_actions`、`action_ceiling`、`allowed_adjustments` 范围且不命中 `prohibited_actions`；全部已有执行事实被无损保留；完整候选计划与 fresh creation review 已经形成。若实际方法为同一 AI fallback，冻结 limitation 必须覆盖 `plan_delta_review`，当次 evidence 非空、assurance gap 精确一致且 stop assessment 为 `clear`；否则必须使用 subagent 或停止。AI 负责语义与当前证据判断，Code 负责结构、引用与 fingerprint 检查；
6. 合法 `PlanΔ` 在 `plan_revising → executing` 的单一事务精确 `plan_version + 1`，完整替换 plan/work items，以 fresh `creation_reviews` 替换旧 reviews；`execution_approval` 的全部成员保持精确不变，不因当前 plan version 高于其 `subject_version` 而失效。projection 完全相同时禁止升版；
7. `plan_revising` 不是 Human Gate：只能承载 Gate1 后的基线内自动调整，不能把 Human 写入 waiting；超过基线、命中禁止项、需要接受新风险或需要 Gate1 后新 Human 决定时，不改授权、不执行该动作、不请求第三次确认，而是据实取消受影响 item，全部 item terminal 后进入结果链；
8. Gate1 后不得撤回、扩展或重建本次运行的 execution authorization/approval。Human 主动给出改变基线的新要求时，也先让当前运行按已有事实安全收敛；新要求只能在当前关闭后由新的 WorkCase/Gate1 承接；
9. 计划替换前，仍有当前价值的实际执行事实必须进入替换后继续存在的 item current/result summary；不能归入单项但仍影响返修判断的跨 item 事实进入顶层 summary，不得为整洁而丢失；

对 PlanΔ 删除一个已有执行事实的旧 `item_id`（包括 `in_progress`、`blocked`、`completed`、`cancelled` 或实际存在的 current/resume/blocking/result 字段），Code 除了检查结构合法性，还必须机械要求一个当次更新的、来源已定义的承接载体：替换后的顶层 `summary` 必须为非空 string，且与替换前的解析值不同。新 item、未改变的旧顶层 summary 以及保留 item 的字段改写都不是这一机械条件的承接载体；保留 `item_id` 的已有执行事实仍按本节要求原样保留，不得为满足这一条而改写。这个条件只确保发生了可回读的承接载体更新，不证明自然语言已无损吸收旧事实；后者仍由 Controller 按本条首段的责任判断，Code 不得以机械通过代替该判断。

10. `SafeConvergenceShape` 不得通过计划更新、Human 新决定或重新授权返回执行；它只保存已有事实并沿 `controller_checking → independent_reviewing → closure_preparing → human_closure_confirming` 前进。

### 6.6 canonical result projection 与结果版本

canonical result projection 由以下完整结构组成：

1. 全部 terminal item 的 `item_id + status + result_summary`，按 `item_id` 排序；
2. 精确覆盖全部成功标准的 results，按 `criterion_id` 排序；
3. 顶层 `result_summary`；
4. `controller_check_summary`；
5. `validation_summary`。

集合顺序按稳定 ID 规范化；字符串按解析后的精确值比较。在 `controller_checking` 内，AI 可在稳定检查点逐个写入已经据实形成的 projection 成员；其中任一数组一旦存在就必须完整覆盖，不得持久化半数组。成员尚未全部存在时只是当前检查候选，不得称为完整 canonical result projection，也不得进入结果复核。review、命令或日志不能代替任一成员。

结果规则如下：

1. 全部 item terminal 后才可进入 `controller_checking`；
2. 当前 `plan_version` 首次形成结果时，`result_version` 只能为 1；
3. 当前版本尚无 result review 时，可在 `controller_checking` 内修改 projection 而不升版；
4. 进入 `independent_reviewing` 前 projection 必须完整、校验并回读；形成首条 result review 的 CAS 必须绑定未变化的完整 before projection，并从该时点冻结；
5. 首条 review 后，projection 任一规范化结构差异都必须在同一事务精确 `result_version + 1`、删除全部旧 result reviews 与 closure proposal，再形成新 projection 并重新复核；projection 完全相同禁止升版、跳号或只删 review 绕过冻结；
6. result version 的作用域是当前 plan version。只有 plan projection 实际变化并使 plan version 递增时，才删除旧 result version；新计划首次结果重新从 1 开始。同一 `plan_version` 下不得删除后复用既有结果版本号；
7. 从结果阶段返回 `executing` 时，移除完整 projection 与 proposal，并重开实际返工 item。已有 result review 时必须先 result version +1 并删除全部 reviews；尚无 review 时必须保持原 result version，不得删除、递增或重置。executing 只保留该已分配版本身份，不保留旧 projection 或 reviews；
8. `independent_reviewing → controller_checking` 可以保留仍绑定当前版本的 review 供 Controller 处置；一旦要改 projection，先按第 5 条升版清理；
9. Reviewer conclusion 不自动推进或否决。进入 `closure_preparing` 前至少一项实际结果复核已经形成，全部 feedback 已有 Controller resolution，projection 仍完整；若实际方法为同一 AI fallback，冻结 limitation 必须覆盖 `result_review`，并满足当前 evidence、assurance gap 与 stop assessment 约束；
10. Reviewer 自有字段的获授权事实更正与 Controller resolution 更新不属于 result projection 变化，但必须遵守字段所有权、CAS 和同事件边界，不得借更正修改被审主体。

### 6.7 关闭提案、结果分类与原子关闭

`closure_proposal` 只保存当前拟提交 Human 的关闭方案，不复制结果 projection。它必须满足：

- `proposed_outcome` 按下表从当前结果与验证形成；
- `proposed_disposition_summary` 只写整体停止边界、逐目标转交范围、受限 Spark 建议、没有剩余责任的结论或 accepted-stop 项存在提示；
- `residual_decisions` 精确覆盖全部当前剩余责任；每项仍适用的 `not_satisfied` / `not_verified` 标准和其它未完成 scope 责任都必须由至少一项 decision 无损覆盖；`route_existing` 必须有 target，`suggest_spark` 必须引用一项 constrained suggestion，`accept_stop` 禁止两者；
- `spark_suggestions` 在存在任何 `suggest_spark` decision 或范围外后续机会时出现并保存完整闭集；`constrained_responsibility` 必须如实具备限制原因、影响、恢复条件和后续定位，`follow_up_opportunity` 禁止这三个受限字段；
- proposal 只整体写入；编辑期间先移除旧 proposal，完整后整体写回；
- 进入 `human_closure_confirming` 前，每个 route_existing target 都已实际回读，责任边界经 AI 判断覆盖待转交事项，并保存完整内容 fingerprint；target 可为 open/blocked WorkCase 或 open Spark，Spark 只表示稳定承载了待判断问题，不表示正在执行；
- Human 决定前禁止写 terminal outcome、disposition、residual 或 `routed-to`。

剩余责任与 decision 不必机械一一对应；一项 decision 可以完整覆盖多个相关标准，一项标准也可以拆成多个不同去向。Reviewer 在结果复核中检查 result / validation 是否如实暴露失败、未知、影响和潜在剩余责任，但不审核尚未形成的 proposal。Controller 在 `closure_preparing` 负责依已复核结果形成完整处置覆盖，Human 在 `human_closure_confirming` 判断是否接受该最终处置。Code 不判断自然语言覆盖是否充分，但任一结果为 `not_satisfied` 或 `not_verified` 时必须机械要求非空 `residual_decisions`；Controller 尚未能确认全覆盖时不得进入关闭待确认。进入 Gate2 后对象冻结，Human 不接受时本次关闭操作零写入并保留原对象，不得自动退回、更改提案或发起第三次确认。

进入 `human_closure_confirming` 前，Controller 必须对关闭时将移除的顶层 summary、item current/result、controller check、reviews、plan、approval、waiting/blocking 和依赖边做一次终态保留审查：仍用于理解实际结果、标准判断、验证边界、停止原因、责任去向或长期复核资料的内容，必须无损吸收到 `success_criterion_results`、顶层 `result_summary`、`validation_summary`、proposal 的 disposition / residual decisions 或仍有价值的 `urls`；无独立消费价值的过程内容不复制。独立 result review 只需审查它形成时已存在的 result / validation 是否完整暴露了这些事实；后续 proposal 的吸收与责任覆盖由 Controller 收敛、Human 判断，不伪造 Reviewer 对尚未存在内容的审核。WorkCase 不为此新增保留收据；Code 不判断自然语言是否已无损吸收，Controller 或 Human 尚不能确认时必须停止关闭。

| outcome | 与实际结果的一致性 |
|---|---|
| `completed` | 全部成功标准为 `satisfied`，原 scope 内没有未满足或未验证责任 |
| `partial` | 至少一项 `satisfied`，且至少一项 `not_satisfied` 或 `not_verified`，已形成部分稳定价值 |
| `not-achieved` | 没有任何 `satisfied`，且当前结果与验证足以判断没有形成任一成功标准的稳定结果 |
| `cancelled` | 当前结果与验证仍不足以评价前三类，Human 已决定改变方向或不再继续投入 |

停止执行、全部 item cancelled 或 Human 撤回授权，都不自动决定 outcome；仍须按实际成功标准结果和验证边界分类。

`completed` 表示当前责任在原 scope 内没有剩余责任，因此完整 proposal 中必须省略 `residual_decisions`，closed 中必须同时省略 `residual_responsibilities` 和 `routed-to`；但可以保留只由 `follow_up_opportunity` 组成的 `spark_suggestions`，用于结构化表达结果中值得日后独立判断的正面经验或范围外机会。其它三种 outcome 按实际未满足、未验证或未完成 scope 责任形成非空处置；不得用空集合或“无剩余”文案消除实际责任。

`human_closure_confirming → closed` 只能由专属原子关闭操作形成：

1. 正常批准形状的 before 仍完整保留当前计划、work item 终值、当前 execution authorization、baseline fingerprint 与当前 baseline 精确匹配的 execution approval、完整结果 projection、当前 result reviews、proposal 和版本绑定，且已无 `depends-on`；approval `subject_version` 可以早于当前 plan version，但只能来自同一冻结 baseline 下的合法 `PlanΔ`；
2. `SafeConvergenceShape` 是 authorization/approval 唯一例外：关闭操作必须继续要求两者同时缺失，outcome 仍按统一分类；
3. Human 作出决定前，已实际取得并可以阅读目标、scope、成功标准与逐项结果、总体结果、验证边界、独立复核处置和完整 proposal；Human 决定是否关闭、停止边界和责任处置，不为技术结果真实性背书；
4. 操作绑定完整 source before fingerprint、Human 当次决定和 proposal 中全部 route_existing target fingerprint；
5. 操作重新读取每个 target；任何变化、缺失、机械无效、不可读、状态不适合形成关系或 fingerprint 不匹配，都拒绝关闭，source 保持不变；Gate2 决定已绑定旧 before，不得在同一运行自动重建 proposal 或重新索取 Human 决定；
6. after 的 `closure_outcome` 必须精确等于 `proposed_outcome`，`disposition_summary` 必须精确等于 `proposed_disposition_summary`，`residual_responsibilities` 必须精确等于全部 `accept_stop` decision 的 `residual_id + summary`，`spark_suggestions` 必须精确等于 proposal 的同名数组，`routed-to` targets 必须精确等于全部 `route_existing` decision 的稳定三元组按目标去重集合；不得改写 proposal 自然语言、漏项或增加第二目标/建议清单；`suggest_spark` 不形成任何 relation，`contributed-to` 不属于本映射；
8. routed 项不再复制为 terminal residual；accepted-stop 项不形成 routed-to；suggest-spark 项只保留为 suggestion，Human 可在 Spark 尚未创建时先关闭 WC；
9. 任一校验、CAS、写入或回读失败都不得声称关闭成功；
10. Human 拒绝关闭或要求修改时不压缩对象、不改 phase；当前运行不恢复执行或关闭准备，新工作只能由新的 WorkCase/Gate1 承接；
11. `close-workcase` 对已 closed before 一律拒绝；closed 不正常重开，也不通过重复 close 冒充幂等更正。


### 6.8 现场保留与后续建议责任

WorkCase 的执行批准只授权 execution authorization baseline 中逐项列明、且仍处于 target/effect scope、action ceiling、allowed adjustments 与各事实类型规则内的动作。授权条目可以包含创建或更新其它事实对象、委派 subagent、执行外部动作等，但必须在 Gate1 前把目标范围、影响、风险、回滚与规则引用说清；未列明对象、未知目标、超出 ceiling 或命中 prohibited action 的动作均未获授权。发现范围外机会时先在当前结果/处置或结构化 `spark_suggestions` 中保留准确边界，不以第三次 Human Gate 扩展当前运行。

完整 `status=draft` Pitfall 现场保留只有在 execution authorization 已列出该动作时才获批：失败必须在当前 WC 执行中实际发生，已经解决、验证、查重并满足 23 的全部正文与单一机制准入；它不覆盖 active 初态、半成品、promote 或 discard。独立 subagent 复核 draft 只是推荐机制，不是创建成立的机械前置。

draft 的形成顺序固定为两个各自独立合法的操作：先按 31 创建完整 Pitfall 并回读，再在 source WC 的下一个合法稳定检查点写 `contributed-to`。两步不是跨对象原子事务；第二步失败不删除已成立 draft，而是保留回读结果并在 WC 还处于允许写边的 phase 时重试。`blocked` 期间不借旧 approval 创建 draft；进入 `human_closure_confirming` 后发现尚未保存的现场不退回，由当前结果据实说明，必要的新对象由后续新 WorkCase/Gate1 承接。

当前验收范围内的真正未完成责任不能被“建议以后建 Spark”替代：没有实际条件限制时必须继续完成；确有受限条件时，结果必须如实将标准记为 `not_satisfied` 或 `not_verified`，并在 proposal 中形成 `suggest_spark` residual decision 与对应 `constrained_responsibility` suggestion。Human 可在 Spark 尚未实际创建时先关闭 WC；closed WC 保留建议正文而不保存未来 object ID。

已由存量 active WorkCase 或 open Spark 稳定承载的问题使用 `route_existing`，不再重复建议新 Spark。关闭后若 Human 独立创建新 Spark，新 Spark 从自身写 `related-to → 原 WC`，并由正文语义说明问题；不要求它引用 residual ID 或 suggestion ID，也不回写 closed WC。

正面经验、已形成结果和处置先在 `result_summary`、criterion result、`validation_summary` 或 `disposition_summary` 中如实保留。其中仍值得 Human 日后独立判断的 scope 外机会，可额外形成 `follow_up_opportunity` suggestion；它不伪造 restriction reason，可与 `closure_outcome=completed` 并存。没有这类独立价值时零建议即合规，不设数量配额或自动产出目标。

## 7. AI 写回与受控操作

### 行动入口

新建 WorkCase 使用 `fact-object-controlled-creation`（31）；活动期更新、关闭与 closed 更正使用 `fact-object-lifecycle-change`（32）并路由到本节三个专属操作。当前 `plan_version` 已获 Human 执行批准后的实际计划推进，可使用 `workcase-approved-plan-execution`（34）组织检查点与恢复；该模板不复制本文状态机或成为调度器。

### 7.1 字段所有权

- Reviewer 只形成 `reviewer`、`reviewed_at`、`subject_version`、`scope`、`conclusion` 和 `feedback`；
- Controller 形成 review `controller_resolution`、phase、当前计划、work item 快照、结果、验证与关闭提案；
- Human 在 Gate1 决定 execution approval、责任/验收/风险与授权边界，在 Gate2 决定最终关闭；两者之间不承担运行中追加确认；
- Code 不生成自然语言事实，也不从 Web、环境、日志或字段缺口推断语义。

普通更新不得改写 Reviewer 自有字段、补造 Human approval、形成 closed 或绕过版本失效规则。事实更正必须使用 05 已授权的更正边界，不能与不相干的生命周期推进合并。

### 7.2 强制写回检查点

| 检查点 | 必须写入的稳定事实 |
|---|---|
| 受控创建 | 完整责任、计划、work items、creation reviews、初始 phase/status 与 Human waiting |
| Human 批准计划与授权基线 | 新 execution approval、executing phase；同事务保留当前 creation reviews 并移除 Human waiting |
| item 开始 | `in_progress`、current summary、resume point |
| item 阻塞或解阻 | item status、blocking/current/resume 的合法组合；整体确实无法继续时同步 WorkCase status/blocking |
| item 完成或取消 | terminal status 与实际 result summary |
| 委派、交接、上下文压缩前或关键中间结果 | 最近稳定 item current/resume；确有跨 item 独立价值时更新顶层 summary |
| 现场保留与建议检查点（§6.8） | 完整 draft Pitfall 的创建回读与 WC 侧 `contributed-to`，或结果/关闭方案中的结构化 Spark 建议；无对应内容时零写入 |
| 进入计划返修 | 冻结 authorization baseline 与 approval，收敛基线内 feedback，不建立 Human waiting |
| 原子替换计划 | 完整新 plan projection、fresh creation reviews、精确升版；authorization/approval 保持不变 |
| 形成结果 | 当前 result version 与完整 canonical result projection |
| 发起和取得独立结果复核 | 完整 projection 已回读；review 绑定准确版本；Controller 处置 feedback |
| 形成关闭提案并进入 Gate2 | 完整 proposal、实际 target fingerprints 与 Human waiting |
| Human 关闭决定 | 专属原子关闭 after 与成功回读 |

写回发生在稳定语义检查点，不要求记录每条命令或实时事件。意外中断只能恢复到最近一次已写入并成功回读的检查点；不得把聊天记忆或工具输出冒充已写事实。

### 7.3 共用机制与专属操作

WorkCase 的创建、读取、更新和更正都复用 05 的当前事实源选择、Schema 校验和精确回读。创建只复用 05 的受控身份分配与原子创建，没有 before、expected fingerprint 或替换 CAS；只有更新和更正才复用完整 before、expected fingerprint、CAS 与原子替换。WorkCase 额外要求 Code 检查：

- status/phase/presence 与允许转换；
- plan/result 版本、review 和 approval 绑定；
- 新建与 Gate1 的必经质量关口枚举、Reviewer mode、action 引用/非复用和 creation review 覆盖；
- plan/result projection 的规范化结构差异；
- item 状态组合与依赖图；
- proposal/terminal 分离，suggestion 局部引用与精确映射；
- route_existing target fingerprints、closed 白名单和关系图约束。

WorkCase 的全部活动期写入必须使用 `update-workcase`；关闭必须使用 `close-workcase`；closed 更正必须使用 `correct-closed-workcase`。通用 `update-fact-object` 不接受 WorkCase，不得借完整 after 绕过字段所有权、版本失效、关闭映射或终态更正边界。Human 决定作为受控操作输入被消费，不持久化 `closure_approval` 或证明收据。

### Helper 公开操作

| operation_key | summary | effect | arguments_contract | result_contract |
|---|---|---|---|---|
| `prepare-closed-workcase-candidate` | 从刚读取的 Gate2 source 快照确定性投影完整非托管 closed 候选与 proposal 已保存的目标映射基础，不检查关闭授权或目标当前状态 | `read` | `workcase-fact-type::prepare-closed-workcase-candidate 输入与结果` | `workcase-fact-type::prepare-closed-workcase-candidate 输入与结果` |
| `update-workcase` | 对一个已精确读取的活动期 WorkCase 提交完整目标 after，并按本文机械执行字段所有权、版本、失效、phase 与 CAS 检查 | `may_change_state` | `workcase-fact-type::update-workcase 输入与结果` | `workcase-fact-type::update-workcase 输入与结果` |
| `close-workcase` | 消费完整活动期 before、Human 当次关闭决定和目标指纹，原子形成 closed 白名单并回读 | `may_change_state` | `workcase-fact-type::close-workcase 输入与结果` | `workcase-fact-type::close-workcase 输入与结果` |
| `correct-closed-workcase` | 对一个 closed WorkCase 提交完整更正 after，并在需要时消费新 Human 决定与全部 after route target 指纹 | `may_change_state` | `workcase-fact-type::correct-closed-workcase 输入与结果` | `workcase-fact-type::correct-closed-workcase 输入与结果` |

### prepare-closed-workcase-candidate 输入与结果

本操作是 `read`，只为调用方减少手工重写 §6.7 第 6–8 项的机械错误，不是关闭事务、授权检查、Human Gate 或完成判断：

- 共同请求中 `arguments.fact_ref` 必填，成员闭集为 `governed_project_id`、固定值 `fact_type_key=workcase` 与 `object_id`；`arguments.workspace_root` 和顶层 `work_object_locators` 可选并复用 05 §11.1 的当前 Working Tree 管辖定位语义。其它领域参数禁止，`observed_context`、`authorization_reference` 必须为空，`requested_disclosure` 必须为 `null` 或省略；
- source 必须是当前 Working Tree 中完整、mechanically valid、`status=open` 且 `phase=human_closure_confirming` 的 WorkCase，并有完整当前 `closure_proposal`。invalid、unavailable、not-found、blocked、closed 或其它 phase 不产生候选；
- `mapping_basis` 字段闭集只有 `proposal_route_targets`。其数组按 target 稳定三元组排序去重，每项字段闭集为 `target` 和 `content_fingerprint`，只原样复制当前 proposal 的 `route_existing` 决策已经保存的目标观察；没有 route target 时为空数组。它不表示 target 当前仍存在、有效、处于允许状态或指纹未变；本操作不得读取任何 target、入向依赖或关系图来补强该结论；
- `source_content_fingerprint` 精确绑定形成候选的 source bytes。source 后续变化即使自然语言相似，旧候选也不得作为真实关闭的 `expected_content_fingerprint`；必须重新读取并重新投影。操作不接收 expected fingerprint、Human 决定、route target 第二清单或授权回指；
- 成功只说明对当次完整 source 完成确定性只读投影。响应和 Code 均不得据此声称 Human 已批准、Gate2 已完成、关闭前提齐备、目标可用、“已准备好关闭”或工作完成；真正关闭仍必须调用 `close-workcase`，在事务内重新读取 source 与全部 target、执行 CAS、指纹、状态、入向依赖和关系图检查并成功回读；
- source 资格不成立返回 `rejected`，管辖、Schema 或读取技术边界无法完成返回 `unavailable`，均为零写入；操作不生成或改写任何 WorkCase 自然语言事实。

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
- after 中的终态映射和 before 事实保留必须逐值满足 §6.7 第 6–7 项；关闭事务不得同时修正标题、责任、标准、结果、验证或 URL；
- 操作在同一事务内重新读取全部 proposal route_existing targets，逐个精确比较 fingerprint，并检查同项目、WorkCase open/blocked 或 Spark open 状态、引用、去重与关系图约束；另对 source 完整检查入向 `depends-on`。任一项不成立时 source 零写入；
- before 满足 §6.3 `SafeConvergenceShape` 时 `creation_reviews`、authorization 与 approval 必须同时缺失；其它 before 必须存在当前 creation reviews、authorization，以及 baseline fingerprint 与当前冻结 baseline 精确匹配的 execution approval；其 `subject_version` 可以早于当前 plan version；
- `close-workcase` 不提供 `no_change`；before 已 closed 或 after 未形成新的合法 closed 目标时都拒绝。成功结果的共同形状复用 05 §11.7；不返回或保存 closure approval、Human 身份证明、review 正文或质量链 receipt。

### correct-closed-workcase 输入与结果

本操作复用 05 §11.7 的共同参数与结果形状、§11.8 的共享事务，并在领域 `arguments` 中追加必填 `route_target_fingerprints` array 与必填 `independent_review_reference` object-or-null：

- before 必须是 mechanically valid 的 closed WorkCase，after 必须仍完全满足 §6.1 closed 必填集、条件集与禁止集，并在已有 `change_log` 上严格追加本次终态更正流水；缺失历史的 legacy closed WorkCase 不得由本操作补写。status 不变，不重开 phase 或补造活动期记录。invalid、unavailable、not-found 或只能解析部分字段的 before 一律拒绝且零写入；本操作不提供旧形状转换或 invalid 记录修复入口；
- 更正只能修复原关闭时已经成立但被记错或遗漏的事实；不得把关闭后才出现的新目标、新责任、新验收边界、target 后续进展或事后方向变化写成原关闭时的事实。新责任必须建立新 WorkCase，必要时由当前 disposition、`routed-to` 链或新对象承接；
- `route_target_fingerprints[]` 成员字段闭集为 `target` 和 `content_fingerprint`；`target` 使用 05 稳定三元组，`content_fingerprint` 原样复用该 target 当次 `read-fact-objects` 的完整载体 bytes 指纹；数组必须按目标去重，并与 after 全部 `routed-to` targets 精确相等，没有 target 时为空数组；
- `independent_review_reference` 非空时精确复用 04.Att.01 的单个“来源回指字段” object，不新建裸 string 引用形状；它只定位当次实际独立复核输入，不因存在就证明 Reviewer 独立或结论正确；
- 操作在同一事务重新读取全部 after route targets 并比较指纹。before 已有且 after 未变的 target 可以继续自身生命周期；after 新增的 target 在形成时必须为同项目 mechanically valid `open` / `blocked` WorkCase 或 open Spark，并完成引用、去重、自指、强边环、入向责任与关系图检查；任一 target 缺失、不可读、指纹变化或检查未完成时 source 零写入；
- after 必须继续满足 §6.7 outcome 一致性与剩余责任完整处置；任一 criterion result 为 `not_satisfied` 或 `not_verified` 时，Code 必须要求 after 至少存在一项 `residual_responsibilities`、`routed-to` 或 `suggestion_kind=constrained_responsibility` 的 `spark_suggestions`；Controller、Reviewer 与 Human 必须确认 disposition 与结构化处置无损覆盖全部仍适用的未完成 scope，Code 不猜测自然语言对应；
- 只更正 `title`，或只更正不改变已记支持范围、限制和关闭判断基础的 `urls` 时，array 型 `authorization_reference` 可以省略或使用空列表、不得为 `null`，且 `independent_review_reference` 必须为 `null`。仅更正原关闭时的 `related-to` 记录时，`authorization_reference` 必须非空并回指 Human 决定，`independent_review_reference` 必须为 `null`。无法确定影响时必须走上一条实质更正路径。活动期的 review/approval 过程字段在形成 closed 时已移除，Human 最终决定由 closed 终态内容表达而不另存收据；不得以笔误更正重建 review、approval 或过程历史；
- 成功与 `no_change` 的结果复用 05 §11.7；必须回读实际 closed after，不返回或保存 Human 决定收据、target 指纹或更正历史。

### 7.3.1 当前合同的一次性迁移边界

本次新增 authorization baseline、approval fingerprint/source refs 和持续 current creation review 后，旧活动对象可能不再满足当前形状。迁移只能作为本次受控发布的一次性仓库迁移执行，不属于 `update-workcase`、正常生命周期、兼容 profile 或通用 invalid 修复能力：

1. 每个目标必须显式给出当前管辖项目、精确 `object_id` 与迁移前完整载体 fingerprint；禁止目录扫描后按相似形状批量猜测；
2. 仍在 Gate1 且保存了真实 current creation review 的对象，可以据当前计划形成完整 authorization baseline，但不得写 execution approval；只有可回指真实 Gate1 Human 输入且完整 baseline 可由当时材料无损重建时，才可迁移为正常批准形状；
3. 已有执行/结果事实但没有真实 current creation review、完整 Gate1 授权证明或稳定 Human `source_refs` 的旧对象，不得补造这些字段，只能在全部 item 已据实 terminal 后迁移为 `SafeConvergenceShape`；未 terminal 时先依据现有事实安全终值化，不能以迁移继续新动作；
4. 迁移必须先对完整目标 after 执行当前 Schema、presence、版本、关系和 result projection 校验，再以 old fingerprint CAS 原子替换并回读；任一目标不成立时零写入，或给出可审计的原子回滚失败事实，不得留下半迁移对象；
5. 本次受控交付完成后移除迁移入口与清单，不保留 legacy profile、兼容读取、自动补字段或日常 invalid repair 正例。

### 7.4 防止 AI 幻觉

WorkCase 的防幻觉机制是相互约束、独立第二视角和明确未知，不是为每句话建立证明结构：

1. item terminal result、逐标准结果、总体结果、controller check 和 validation 必须构成同一完整 result projection；
2. `not_verified` 与 `not_satisfied` 分离；未执行、无法取得或无法确认的内容不能写成满足或未满足；
3. Reviewer 必须检查总体结果是否超出局部结果和实际观察、是否隐藏失败、未知或副作用；Reviewer 存在不证明正文正确；
4. 首条 result review 后 projection 冻结；结构值变化必须确定性升版并重新复核；
5. route_existing target 必须实际回读并在关闭时再次精确比较 fingerprint；fingerprint 只防陈旧，不判断语义责任是否充分；
6. 路径、命令成功、日志、测试进程退出码、review、approval 或 Human Gate 都不能单独代替自然语言结果与验证边界；
7. 写入或回读失败时只报告实际结果，不能声称状态已经推进；
8. Helper、Web 与 Code 只传递、读取或机械校验来源定义的内容，不生成 WorkCase 自然语言事实。

## 8. 来源、外部资料与关系

### 8.1 来源与验证边界

WorkCase 不要求通用证据结构，也不建立证明包。AI 必须根据当次实际来源和观察据实形成目标、当前快照、结果与验证边界；无法确认的内容保持 unknown 或 `not_verified`。

`validation_summary` 说明实际验证了什么、覆盖到哪里、观察到什么、失败和未验证范围；不保存命令日志。`urls` 只用于关闭后或后续判断仍有长期复核价值的外部 HTTP(S) 资料，并说明支持范围与限制；本机路径、代码、会话、日志和 Git revision 不写入 urls。

### 8.2 关系闭集

WorkCase 只允许五种正向关系；反向导航由 Code 派生，不写第二份权威：

| relation_key | source | target | 唯一语义 |
|---|---|---|---|
| `depends-on` | 同项目 `open` / `blocked` WorkCase | 形成和保留期间均为同项目 `open` / `blocked` WorkCase | source 当前某项行动或关闭判断确实依赖 target 仍在承担的责任 |
| `routed-to` | `closed` WorkCase，只由 `close-workcase` 形成，或由 `correct-closed-workcase` 在相应 Human Gate 下更正原关闭记录错误/遗漏 | 首次形成或更正新增时，target 为同项目 mechanically valid 的 `open` / `blocked` WorkCase，或 `status=open` Spark；形成后 target 按自身规则继续生命周期 | source 经 Human 关闭决定，将不再由自身承担的剩余责任转交给已稳定承载同一问题的 target；Spark 目标不被表达为执行中，target 后续进展不构成回溯换路理由 |
| `contributed-to` | 活动期或 `closed` WorkCase；活动期按 §6.8 在 target 实际创建回读后形成，closed 上增删只由 `correct-closed-workcase` 按原关闭记录的实质更正执行 | 形成时只能为同项目 mechanically valid 的 `status=draft` Pitfall；形成后 target 可为 draft/active/discarded | source 执行中实际发生、解决并验证的完整现场经验已保存为 target；仅作形成来源追溯，不表示 Human 已确认、经验仍适用或 target 承接责任 |

共同约束：

- target 暂只允许当前选定的同一 `governed_project_id`；跨项目不进入当前契约；
- 同一 `relation_key + target` 最多一项；数组顺序无语义；没有关系时省略；
- `depends-on` 与 item `depends_on` 不同，不能相互替代；
- `routed-to` 指向 Spark 只表示问题已由存量 open Spark 稳定承载，不表示已开始执行或完成责任；
- `contributed-to` 的 target 闭集缩减为 `pitfall`，并且首次形成时必须为 draft；不指向 Spark、ADR、Study 或 WorkCase；
- `contributed-to` 不构成 §6.7 剩余责任处置：验收基线内的未完成责任只能由 `residual_decisions` 覆盖，创建贡献对象与写入本边均不免除该义务（§6.8 划界判据）；
- 入向 `contributed-to` 不构成 22 §7、23 §7 所排除的来源关系、证明材料或准入依据，不影响 ADR / Pitfall 各自的准入条件与对象语义；
- 多项责任可去往同一 target，终态只保留一条去重关系；`disposition_summary` 按目标说明转交范围。

### 8.3 关系失效与入向约束

`depends-on` 解除或 target 准备改变责任边界时，source 必须先把仍影响结果或停止边界的事实吸收到正确自然语言字段并移除关系。target 仍有任何入向 `depends-on` 时不得关闭；closed source 禁止保留 `depends-on`。

`routed-to` 形成时，WorkCase target 的当前 goal/scope 或 Spark target 的当前问题正文必须语义覆盖被转交事项，AI 负责判断，Code 只检查引用、状态、指纹和图约束。形成后 target 按自身生命周期继续，upstream relation 仍保留；消费者沿 target 当前内容理解去向。WorkCase target 关闭/改 scope 或 Spark target 转为 routed/discarded 前必须检查入向 `routed-to`，不得静默丢失已转入责任；必要时由 target 自身当前或终态正文、下一跳关系或 accepted-stop residual 继续说明。

`contributed-to` 形成时，target 必须实际存在、可读、mechanically valid 且为 draft Pitfall；形成后 target 变为 active 或 discarded 不影响边，也不回写 WC。target 后来被删除或不可读时，该边失效但不自动改变 source 的状态与终态；机械读取如实报告。该边不承载未完成责任，不建立 target 状态变化前的入向检查义务；删除方仍必须按 05 §9.3 先处置全部入向引用。


`related-to` 只记录形成时的存量主题联系，不做有向环检查，其它共同引用检查仍成立。close 必须原样保留 before 中已有边。closed WC 不追加未来出现的新关系；后续对象应从自身一侧指向该 WC。一项更正只能修正原关闭时已存在但记错/遗漏的当时事实，不得将后来新建对象冒充“当时遗漏”。

当前契约不定义 WorkCase 的 archive、merge、replace 或 delete 操作，AI、Helper、Code 和 Web 均不得自行实施或用隐藏代替。责任拆分、后续承接或方向变化使用新 WorkCase、当前对象的结果/处置收敛与必要 `routed-to`，不改写或删除已经成立的稳定身份。若 WorkCase 类型本身准备退出，必须先按 05 §12 形成专门处置与事实承接，不得直接删除对象或实现支持。

## 9. 召回、消费与派生视图

### 9.1 渐进式召回

进入新上下文、恢复、压缩或委派时，不无条件恢复全部 WorkCase。只有当前 Human 目标需要项目事实时，AI 才依据 00 与 05 进入事实消费分支。下列语义情形产生 WorkCase 召回机会：

- Human 要求建立、继续、恢复、委派、交接、解阻、复核或关闭一项需跨多步持续承担的责任；
- Human、环境或上层入口提供已知稳定 WorkCase 引用，或当前对象的直接 `depends-on` / `routed-to` 边对当次理解必不可少；
- 需要追溯某贡献对象的形成来源，或反查某 WorkCase 实际产生过哪些贡献对象；
- 创建前需查重、判断更新现有 WorkCase 还是从 Spark 承接，或关闭/终态更正前需核对依赖、转交与入向责任。

`current_workcase_ref` 只能来自 Human 明确引用、当前环境实际提供的稳定引用或已按规则建立的精确绑定。标题相似、唯一候选、优先级、Web 选择状态或关系边都不能自动绑定。

WorkCase F1 恢复基线固定包含当前项目全部 mechanically valid `open` / `blocked` WorkCase；必须沿 `next_cursor` 持续分页，直至读完全部页，才可声称该类型 F1 完整。其最小 `fields` 投影闭集为 `object_id`、`title`、`status`、`phase`、`goal`、`scope`、`summary`、`priority`、`blocking_summary`、`updated_at` 及派生 `work_item_counts`；条件字段在对象中不存在时省略。`work_item_counts` 不写回事实源，字段闭集和顺序为 `pending`、`in_progress`、`blocked`、`completed`、`cancelled`，每项是从当前 `work_items` 机械计数的非负整数。F1 不含摘录，不表示对象全文已读或行动获准。

F2 候选使用 05 已定义的类型、状态、精确引用、直接关系、locator 和字段文本确定性条件，不做语义相似度。省略显式状态时，WorkCase F2 默认也只取 `open` / `blocked`；`closed` 只在显式状态、精确引用或已知直接关系目标下进入候选，不因终态历史无差别恢复。F2 `fields` 投影为：

- active：与 F1 相同，包含派生 `work_item_counts`；
- closed：`object_id`、`title`、`status`、`goal`、`scope`、`result_summary`、`closure_outcome`、`disposition_summary`、`spark_suggestions`、`updated_at`；其中条件字段不存在时省略；
- 两者都不生成摘录。WorkCase F2 允许精确文本匹配的完整直接字段只有 `title`、`goal`、`scope`、`summary`、`blocking_summary`、`result_summary`、`validation_summary` 和 `disposition_summary`；匹配不会把未入投影的完整字段附带返回。

AI 选中候选后使用稳定引用进入 F3，并按当次语义展开：

- 创建查重展开能够承接同一责任的 WorkCase/Spark 全文，不以卡片标题直接新建；
- 继续执行或交接展开精确当前 WorkCase 的 goal、scope、criteria、plan approval、items、current/resume/waiting/blocking 和当前 phase，并只在当次行动受其约束时继续展开直接 `open` / `blocked` dependencies；
- 方案决定展开完整责任、成功标准、work items 与 creation reviews；结果复核展开完整 result projection、当前 reviews 及未验证边界；
- 解阻只展开阻塞/等待、受影响 items、直接依赖和能够判断解除条件的当前事实，不恢复无关历史正文。

每次召回与交付必须说明来源、已读范围、未读、无效、不可读与继续入口。卡片、索引、计数和关系候选不成为第二事实源，也不自动表示相关、适用、当前结论、获准行动或已完成。


### 9.2 活动期与 closed 消费

活动期按当前目标渐进展开目标、scope、criteria、计划、approval、work items、恢复点、结果与关系；不是每个消费者都必须读取全对象。

closed 消费只依赖：

- 原责任、scope 与成功标准；
- 逐项及总体结果；
- validation；
- closure outcome 与 disposition；
- accepted-stop residual 与 Spark suggestions；

不得要求 closed 重新提供 plan、items、reviews、approvals、controller check、phase 或版本。

### 9.3 当前快照确定性呈现投影

WorkCase 的 AI 交还、Helper 读取结果和 Web Human-facing 呈现共用一份非持久、可失效的 `current_snapshot_projection`。本文是 `status`、`phase` 及其呈现语义的唯一权威；Code 只把本文的确定性映射实现为 `workcase-current-snapshot-presentation/1` 合同，Helper、Web、AI、测试、i18n 和文档均不得另建 phase 表、话术成立条件或第二事实源。投影不进入 WorkCase YAML，不替代当前对象，不反向定义生命周期或授权。

投影有两个输入边界：

1. Helper 只对刚完成精确读取、`check_status=mechanically_valid` 且带有当次 `content_fingerprint` 的 WorkCase 形成投影；该指纹原样进入 `source_content_fingerprint`；
2. Web 按 08 §5.3 成功读取当前载体后，以当次原始载体 bytes 的 SHA-256 作为 `source_content_fingerprint`，并只使用字段级可读的 `status` 与 `phase` 形成投影；Web 不以完整机械校验通过为前提，组合缺失、类型不符或不在本节闭集时形成 `unresolved`，同时继续呈现其它可读字段、字段问题和未解析结构。

投影共同字段闭集为：`contract_identity`、`resolution` 和 `source_content_fingerprint`。`contract_identity` 固定为 `workcase-current-snapshot-presentation/1`；`resolution` 只允许 `resolved` 或 `unresolved`；来源指纹通常为 64 位小写十六进制 string，只在 `unresolved_reason=missing_source_content_fingerprint` 时为 `null`。它只绑定当次载体快照，不表示机械有效、语义正确、Git 版本或授权成立。

`resolved` 另有字段 `lifecycle_position`、`handoff_narrative_key`、`next_required_control_step`、`progress_group`、`progress_step` 和 `blocking_overlay`。`progress_step` 无适用值时为 `null`；其余字段必填。非 blocked 的确定性基表如下：

| 当前 `status` / `phase` | `lifecycle_position` | `handoff_narrative_key` | `next_required_control_step` | `progress_group` | `progress_step` |
|---|---|---|---|---|---|
| `open` / `human_plan_confirming` | `human_plan_confirming` | `gate1_waiting` | `human_gate_1` | `plan_confirmation` | `null` |
| `open` / `plan_revising` | `plan_revising` | `plan_revision_in_progress` | `form_current_plan` | `progressing` | `null` |
| `open` / `executing` | `executing` | `item_execution_in_progress` | `advance_current_work_item` | `progressing` | `item_execution` |
| `open` / `controller_checking` | `controller_checking` | `result_projection_preparing` | `form_complete_result_projection` | `progressing` | `controller_self_check` |
| `open` / `independent_reviewing` | `independent_reviewing` | `independent_result_review_in_progress` | `complete_independent_result_review` | `progressing` | `independent_review` |
| `open` / `closure_preparing` | `closure_preparing` | `closure_proposal_preparing` | `form_closure_proposal` | `progressing` | `controller_synthesis` |
| `open` / `human_closure_confirming` | `human_closure_confirming` | `gate2_waiting` | `human_gate_2` | `closure_confirmation` | `null` |
| `closed` / phase 省略 | `closed` | `closed` | `none` | `closed` | `null` |

`status=blocked` 是活动期 phase 之上的阻塞覆盖层，不改变基表中的 `lifecycle_position`、`next_required_control_step`、`progress_group` 或 `progress_step`，但 `blocking_overlay` 必须为 `true`，并必须同时呈现实际 `blocking_summary`。除 `human_closure_confirming` 外，其 `handoff_narrative_key` 固定为 `blocked_at_current_position`；`blocked` / `human_closure_confirming` 固定为 `gate2_position_blocked`，只能说明所处位置及仍有阻塞，不能表达关闭材料已可立即确认、仅剩 Gate 2 或等待 Gate 2。基表中非 blocked 行的 `blocking_overlay` 为 `false`。

只有 `open` / `human_closure_confirming` 的 `gate2_waiting` 可以产生“等待 Gate 2”“仅剩关闭确认”“关闭待确认”或等义的 AI/Web 结论。`independent_reviewing`、`closure_preparing` 以及任何 blocked、unresolved 投影必须负向禁止这些结论；`closed` 只表达已经关闭。AI 交还必须依据刚回读快照所形成的投影 key 描述当前状态，不能凭聊天历史、计划预期、Reviewer pass 或 Web 文案提前生成相邻 phase 的叙述。

`unresolved` 另有 `unresolved_reason`，只允许 `missing_source_content_fingerprint`、`missing_status`、`unsupported_status`、`missing_phase`、`unexpected_phase`、`closed_with_phase` 或 `invalid_status_phase_combination`；不得同时输出生命周期位置、叙述 key、下一控制步骤或进展值，也不得按相似词和相邻 phase 猜测。Web 载体本身不可读或不可解析时沿用 08 `unreadable`，不伪造投影。

`next_required_control_step` 只说明结构上下一必经控制步骤，不断言该步骤已获授权、能力可用、行动允许、优先级更高、工作完成或 phase 应自动推进。Code 可以形成投影、校验转换和检查禁止话术 key，不能替 AI 作上述语义判断或自动选择工作项。任何缓存若将来出现，必须同时绑定 `contract_identity` 与 `source_content_fingerprint`；来源或合同身份变化即失效，当前增量不建立持久缓存。

Card 可以另外派生 item 五状态计数和当前活动 item，但不得把任何派生结果写回 YAML，不得猜测“第几轮”“第几项”或完成百分比。具体 Card 内容与视觉设计由 08 承接，不能反向要求新增事实字段；Card 的“后续贡献”只列实际 `contributed-to` Pitfall 的标题与当前状态，并以待确认/活跃/已废弃呈现；关闭处置另显示三类 decision 与 Spark suggestions。`related-to` 只在详情中作关系导航，不进入关闭 Card 正文。

## 10. 验证要求

### 10.1 验证对象

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| 类型定义与登记 | 新建或实质修改本文、05.Att.01 或派生 Schema 时 | 结构、字段、绑定、H2 引用与统一登记唯一一致，无悬空、遗漏或第二定义 | 00、01、05、05.Att.01 与本文当前 Working Tree | 规范仓库检查、字段登记检查和当前来源回读 | 当前来源的机械结构一致性；不证明自然语言设计正确 | 本文或附件不得进入当前规则源；先修正唯一来源 |
| 准入与创建 | 建议建立、形成正式计划和受控创建前 | Human 工作意图、单一责任、scope、criteria、查重、净价值、完整计划与实际方案复核成立；若缺少 subagent，限制与低保证 bootstrap 已据实披露；Controller 与 Reviewer 已逐项确认没有 work item 吸收生命周期关口或 Human Gate | Human 当前指令、当前来源、相邻事实回读、候选计划与 Reviewer 实际反馈 | AI 语义审核、逐 item 生命周期关口检查、事实召回、受控创建校验与创建后回读 | 当次候选的已读范围、实际方法、保证边界、语义审核和创建结果；Code 不证明证据语义或未来执行成功 | 不创建；先补齐限制/证据或返修误建模 item，或更新现有对象、留在当前行动、拆分或转 Spark |
| 活动形状与转换 | 每次读取、写回、phase/status 改变、计划返修或授权变化时 | status/phase/presence、item 组合、plan version、review/approval 绑定和允许转换成立 | 当前对象 before/after、Human 决定、Reviewer feedback 与本文 | Schema、CAS、projection 比较、转换校验和 after 回读 | 可机械检查的形状、版本与转换；不证明当前摘要真实 | 不消费为有效 WorkCase或拒绝转换；修正最小相关范围 |
| 结果与复核 | 形成结果、发起复核、处置反馈或改变 projection 时 | projection 完整、criterion 全覆盖、版本冻结、实际 review 方法/保证边界与 Controller resolution 成立 | item 终值、当前结果与 validation、Reviewer 实际输出、当前 capability evidence | AI 结果审核、规范化 projection 比较、CAS、review/版本/limitation 检查 | 当次结果包结构、已读观察、实际方法和 review 绑定；不证明证据语义或技术结论天然正确 | 不进入关闭准备；补事实、升版、清旧 review、改用 subagent 或停止 fallback |
| 关闭提案与终态 | 形成 proposal、进入 Gate2、执行关闭或终态更正时 | proposal 完整、outcome 一致、target 重读、Human 决定、原子 close 与 closed 白名单成立 | 完整 source before、Human 当次决定、目标当前快照与 fingerprints | AI 责任处置审核、target 回读、CAS、专属关闭和 closed after 回读 | 当次停止边界、机械原子性和实际写入结果；不证明 target 已接受或技术事实无误 | Gate2 前不进入确认；Gate2 后失败则 source 保持冻结、不声明关闭且不自动重新请求 Human |
| 关系 | 新增、移除、读取依赖、target 变更或任一对象终态前 | source/target 状态、同项目、唯一性、无自指、强边环、related-to 重叠、入向约束与责任边界成立 | source/target 当前对象、项目对象全集和本文关系语义 | 引用回读、强边图检查、AI 责任边界审核 | 稳定引用、状态与已检查图范围；不证明语义责任充分或目标接受 | 移除或修正关系；无法完成检查时交还 unavailable，暂停受影响关闭 |
| 现场保留与后续建议 | WC 执行中出现经验、剩余责任或范围外机会时 | 除完整 draft Pitfall 外不创建新事实；draft 与写边分步回读；受限责任有明确原因、影响和恢复条件；范围外机会不伪造受限 | 当前工作事实、完整 Pitfall 候选、结果/验证与关闭 proposal | AI 语义审核、31 受控创建与回读、关系和 suggestion 机械检查 | 当次保存和结构映射；不证明未来 Spark 会建立 | 继续完成范围内责任，或据实阻塞/形成建议；不创建未获独立授权的其它对象 |
| 写回与消费 | 每个稳定检查点、上下文接续和信息交付时 | 当前事实源、CAS、原子写入、回读、coverage 与未读边界明确 | Working Tree、实际写入结果、读取结果与稳定引用 | 05 共用写回/读取入口和对象回读 | 已写入、已回读和已交付范围；不证明未读信息不存在 | 只报告实际结果，不声称推进或上下文完整；保留最近有效检查点 |

### 10.2 Code 的机械边界

Code 可以检查：

- Schema、字段闭集、presence、枚举、时间、ID 和 closed 白名单；
- criterion 覆盖、item 条件组合、依赖和关系图；
- plan/result version、review、authorization/approval、baseline canonical JSON/fingerprint 和 phase 绑定；
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
2. 受控创建、Gate1 完整授权基线、真实 source refs、fingerprint、`SafeConvergenceShape` 同时禁止 creation review/authorization/approval、Gate1 后不回确认、Gate2 只关闭，以及两 Gate 之间不产生 Human waiting；
3. 五种 item 状态的列明边与未列明边、条件字段、依赖只能由 `completed` 满足、缺失/自指/成环、Controller 返工重开、terminal 分类更正、`executing + AllTerminal` 拒绝、无序 item 与模板 key 成员类型/唯一性；并以“全部实现完成后安排独立结果复核”作为非法 item 反例，检查当前规则和获批计划执行模板持续把该责任留在 phase 链，同时不得把该契约测试表述为 Code 已能理解任意自然语言计划；
4. `PlanΔ` 的规范化比较、baseline 不变检查、精确 +1、fresh review 自动继续、相同计划不升版、新 item 只以 pending 建立、既有执行事实不得重置/静默删除，以及超界动作取消并进入结果链；
5. criterion results 数组全覆盖或整体缺失、`controller_checking` 稳定逐成员形成、数组禁止半覆盖、进入独立复核前 projection 完整、首条 review 冻结、`ResultΔ` 确定性升版、同版本不重置和返回 executing；
6. Reviewer/Controller 字段所有权、同一数组 review 复合身份重复拒绝、新实际复核使用新 `reviewed_at`、同事件事实更正保持复合身份且与生命周期转换不可混用、返修期 review 冻结不可通过删除绕过版本失效；
7. proposal/terminal 分离、四种 outcome、三种 residual disposition、两种 suggestion kind 的字段组合、suggestion 局部引用完整性、`completed` 只允许 follow-up suggestions、其它 outcome 对未满足/未验证/未完成 scope 的责任处置、proposal 与 terminal 精确映射、Gate2 route target 漂移后零写入且不退回，以及专属原子关闭；
9. `correct-closed-workcase` 的 closed before/after、after 全部 route target 指纹精确集合与重读、新增与未变 target 的不同状态条件、实质更正的 Human Gate 与独立复核引用、非实质更正的引用空值、终态责任覆盖，以及因后来事实回溯改写原关闭历史被拒绝；
10. 未登记字段、半成品结构、空占位、日志/命令/推理字段，以及通用 update 读写 WorkCase、活动期 update 形成 closed、close 更正 closed 均被拒绝；三个 WorkCase 专属操作对 invalid、unavailable、not-found 或只能解析部分字段的 before 必须正向覆盖零写入拒绝，不建立旧形状转换或 invalid 修复正例；
11. 渐进式召回的触发语义、F1/F2 字段闭集与 coverage、active/closed 默认范围、F3 按场景展开、四个 Web 分组的确定性派生，以及派生信息不写回事实源。

测试只针对这份当前契约，不建立历史 profile 或兼容读取；§7.3.1 的一次性迁移必须另有精确 ID/fingerprint、正常形状与 SafeConvergenceShape 分流、零写入/回滚和入口移除测试，迁移交付完成后随入口一起删除。


## 11. Human Gate

### 11.1 对象外工作意图

Human 对“是否由项目承担并建立 WorkCase”的意图发生在对象外；Human 已在当前请求中表达范围清楚的工作意图时，Controller 可据此形成正式计划、完整授权基线、独立方案复核和受控创建，不新增一次确认。它不是活动 WorkCase 的第三个 Gate，也不等于 Gate1 执行批准。

### 11.2 当前计划执行批准

WorkCase 创建后，必须向 Human 展示当前目标、scope、成功标准、work items、重要依赖、具有判断价值的方法边界、验证安排、creation review 的实质反馈处置，以及完整 execution authorization baseline。基线必须在这一次沟通中逐项说清全部可预见动作及目标/影响范围、风险、动作上限、禁止项、允许调整与重试、subagent 委派、验证/回滚、超界收敛和只能由 Human 预先完成的前置条件。Human 明确批准后，才能写带真实 `source_refs` 与 `baseline_fingerprint` 的 execution approval 并进入 executing。

批准绑定 Gate1 当时的 plan version 和冻结 authorization baseline；它只授权 baseline 逐项列明且仍满足来源规则的动作，不使技术验证、能力或来源适用自动成立。Gate1 后 baseline 不变的 `PlanΔ` 精确升版并 fresh 独立复核后自动继续，不重新进入本 Gate；超过 baseline 的动作不获准且按 §6.5 安全收敛。

### 11.3 最终关闭决定

Human 在 `human_closure_confirming` 判断：

- 是否停止当前 WorkCase；
- 是否在当前结果与验证所支持的分类下停止，并接受相应风险；
- 哪些剩余责任转交到哪些存量 open/blocked WorkCase 或 open Spark；
- 哪些受限责任在尚无 Spark 对象时作为结构化建议保留，以及哪些责任接受停止；
- 哪些范围外后续机会值得保留为非承诺建议。

Human 不为技术结果真实性背书，也不直接把另一分类写成终态事实。决定必须绑定完整 source before 与 route targets，由专属关闭操作消费；不持久化 closure approval。Gate2 只接受或拒绝当前关闭提案：接受则原子关闭；拒绝、要求修改或目标漂移则本次操作零写入并保持冻结，不返回结果、计划或执行 phase，不自动再向 Human 请求决定。新增或返工责任由新的 WorkCase/Gate1 承接。

### 11.4 其它保留给 Human 的变化

以下变化必须在 Gate1 基线形成时取得 Human 决定并写入授权边界，或在 Gate2 作为关闭处置判断；不得在两 Gate 之间临时插入第三次确认：

- 改变同一责任的 goal、scope 或成功标准；
- 在当前结果与验证所支持的 `partial`、`not-achieved` 或 `cancelled` 分类下停止，并接受 accepted stop 或残余风险；
- 扩大范围、高影响或不可逆行动；
- 拆分、合并、删除或重组可能丢失身份、当前事实或责任去向；
- closed 实质更正改变原关闭判断基础。

Gate1 后出现未覆盖的高影响/不可逆行动、新风险接受、范围扩大或身份重组时，当前 WorkCase 不取得追加授权，只停止受影响动作并按 §6.5 安全收敛。closed 实质更正是关闭后独立的新责任，不属于原 WorkCase 运行。Human 决定、review 和 Code 校验彼此不能替代。


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

- 计划未实际复核、实际方法/保证边界未据实披露，或未获 Human 批准即执行；
- plan projection 改变却未升版、fresh review，或变化已超出冻结 baseline；
- Controller 发起基线内返修后仍按旧计划行动，或把返修转成新的 Human waiting；
- 通过删除/改写 approval、手改 phase、假升版或补造 source refs 掩盖基线变化；
- Gate1 后试图重新授权、扩展 baseline 或重置 plan/result version；
- item 写成命令、日志、推理、百分比或过期快照；
- item 吸收 Controller 自检、独立结果复核、关闭准备、Human Gate 或其它 WorkCase 生命周期关口，造成关口等待 item terminal、item 又等待关口的循环；
- in-progress 缺 current/resume，blocked 缺具体事实和解除条件；
- 借当前 execution approval 执行未进入 authorized actions、超出 target/effect scope 或 action ceiling、命中 prohibited actions 的事实创建/更新或其它副作用；
- 当前 scope 内责任没有实际受限原因却停止继续完成，或以空泛“后续建 Spark”代替结果、影响和恢复条件；
- 写回或回读失败却声称检查点成立。

上述 Gate1 后超界条件只停止受影响动作，不向 Human 请求第三次确认；Controller 据实取消受影响 item，并在全部 item terminal 后继续结果复核与 Gate2。只有 Gate1 与 Gate2 可以把 Human 写为 waiting 对象。

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
- outcome 为 `completed` 却仍有 residual decision、terminal residual、`routed-to` 或 constrained suggestion；
- route_existing target 未实际回读、fingerprint 失配、不可读、状态不合法或责任边界不覆盖；
- suggest_spark 没有引用完整 constrained suggestion，建议包含未来对象 ID，或 follow-up opportunity 伪造限制原因；
- 通过普通 update 形成 closed；
- closed 不满足白名单；
- accepted-stop 写成已处理/已完成，或 routed 项仍复制为 residual；
- 关系跨项目、重复、自指、缺失、不可读、强边成环、related-to 与强边同 target 重叠或违反入向约束；
- 把 routed-to 表达成 target 已接受、已开始或已完成；
- 把验收基线内的未完成责任包装成 Pitfall 贡献，以 `contributed-to` 规避 `residual_decisions` 的完整处置；
- `contributed-to` 指向未实际创建回读的对象、非 draft 初始 target 或非 Pitfall 目标，或在 `blocked` / `human_closure_confirming` 中形成/变更该边；
- 把 `contributed-to` 表达成 Human 已确认、target 已完成或责任已被承接；
- 向 closed WC 追加后来新建对象的 `related-to`，或要求后续 Spark 引用 residual/suggestion ID。

### 12.5 能力与失败交还

CAS、原子写入、回读、项目全集、环检查或专属关闭能力不可用时，只暂停最小相关范围并如实交还 unavailable；不得猜测成功、扩大失败范围或用旧行为替代缺失能力。本文不能被用来推导实例、Helper、Code、tests、Web 或行动模板已经实现。
