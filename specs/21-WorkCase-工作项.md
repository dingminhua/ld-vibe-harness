# WorkCase-工作项

```yaml
ldvh_doc:
  doc_id: "21"
  doc_kind: "work_model_spec"
  title: "WorkCase-工作项"
  status: "active"
  canonical_path: "specs/21-WorkCase-工作项.md"
  created: "2026-06-12"
  updated: "2026-06-21"
  parent_doc: ""
  relation: ""
  positioning: "定义 WorkCase / 工作项工作模型，包括对象定位、准入条件、事实源边界、方案审核、执行、结果自检、结果复核、关闭确认、变更记录、字段契约、事实源回写和适配规则"
  scope: "所有接入 LDVH 且需要把一次目标组织为可执行、可验证、可关闭工作项的项目"
  basis:
    - "specs/05-工作模型基础规范.md"
  related_specs:
    - "specs/05.01-工作模型字段定义与语义规范.md"
    - "specs/05.02-工作模型字段内容与格式规范.md"
    - "specs/05.03-工作模型字段注册与消费规范.md"
  code_consumption:
    - "doc_metadata"
    - "relations"
    - "structure"
    - "member_consistency"
    - "work_model_collection"
```

```yaml
ldvh_member:
  spec_id: "21"
  kind: work_model
  name_en: WorkCase
  name_zh: 工作项
  collection_status: active
  canonical_path: specs/21-WorkCase-工作项.md
  instance_root: ldvh-base/workcases/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
    - state_machine
    - execution_items
    - instance_checks
```

---
## 1. 对象定位与准入条件

WorkCase / 工作项是 Human 与 AI 围绕一次目标达成的工作事实契约。工作项承载已经由主控 AI 起草到可审核程度的目标、范围、成功标准、所属工作域、执行编排、方案审核、执行过程、结果自检、结果复核、关闭确认和经验分流。

主控 AI 在 WorkCase 创建前可以起草方案草稿；该起草动作不是 WorkCase 状态。只有当草稿已经足以被第三方子 Agent 审核时，才创建 WorkCase 并进入方案审核。Human 主要确认方案是否允许执行和结果是否允许关闭；AI 负责在工作项内部安排执行项、调度角色或专业视角、完成验证、整理证据并接受独立复核。执行项只属于 WorkCase 内部编排，不作为独立工作模型，不进入 20-39 集合，也不在 `ldvh-base/` 下形成独立事实实例。

### 1.1 工作项准入条件

一个目标满足以下条件之一时，应形成工作项：

1. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
2. 需要表达目标、范围、成功标准、验证证据或关闭判断；
3. 需要多个执行项、并行安排、顺序安排或角色分工；
4. 需要 Human 明确确认目标、范围、成功标准或关闭判断；
5. 需要留下最小恢复信息、验证证据、关闭证据或结果物引用；
6. 不结构化会导致目标、范围、执行编排或完成判断漂移。

当前对话即可完成、无需留存记录、无需流程治理的小工作，不创建工作项。

---
## 2. 事实源边界

工作项实例的权威事实源位置为：

```text
ldvh-base/workcases/workcase-{NNNN}-short-title.yaml
```

| 内容 | 权威位置 |
|---|---|
| 工作项工作模型规范 | `specs/21-WorkCase-工作项.md` |
| 工作项实例 | `ldvh-base/workcases/` |
| 工作项字段内容格式 | `specs/05.02-工作模型字段内容与格式规范.md` |
| 工作项展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

执行过程不作为长期事实源。工作项只保留最小恢复信息、验证证据、关闭证据和经验分流结果；AI 的临时步骤、局部选择、工具缓存、子 Agent 中间过程和未采纳草稿不得写成独立工作对象。

---
## 3. 状态机

### 3.1 标准状态

| 状态 | 含义 |
|---|---|
| `subagents_plan_reviewing` | 子 Agent 方案审核中：主控 AI 已起草出可审核方案，等待或正在由多个子 Agent / 第三方审核 Agent 按审核策略审核方案 |
| `human_plan_confirming` | Human 方案确认中：方案审核和主控处理记录已形成，等待 Human 确认是否允许执行 |
| `executing` | 执行中：Human 已确认方案，主控 AI / 执行子 Agent 正在按方案执行 |
| `result_self_checking` | 结果自检中：主控 AI 已认为执行结果可以进入收口，正在自检成功标准、验证证据、关闭证据和残留风险 |
| `subagents_result_reviewing` | 子 Agent 结果复核中：主控自检已形成材料，等待或正在由多个子 Agent / 第三方审核 Agent 复查结果与关闭材料 |
| `human_closure_confirming` | Human 关闭确认中：结果复核和主控处理记录已形成，等待 Human 确认是否关闭、退回补审、继续执行或修改方案 |
| `closed` | 关闭判断已确认，工作项终态稳定 |

`closed` 是稳定终态，只表示该工作项不再继续推进，不等同于目标成功。关闭可以表示目标完成、被新工作项承接、范围失效、终止、降级接受或其他经证据说明的关闭结果；关闭原因、完成程度、残留风险、未完成项分流和 Human Gate 结果必须写入 `closure_evidence` 或关联工作对象。

目标重新启动、扩大范围或改变成功标准时，应创建新的工作项，并引用原工作项。

主控起草方案不是 WorkCase 状态。WorkCase 的第一个权威状态是 `subagents_plan_reviewing`，表示方案已经可以被第三方审核。若方案尚不足以审核，应继续留在当前对话、Spark、Study 或其他前置事实源中，不得为了记录草稿而创建 WorkCase。

### 3.2 合法状态流转

```text
subagents_plan_reviewing -> human_plan_confirming
human_plan_confirming -> executing
executing -> result_self_checking
result_self_checking -> subagents_result_reviewing
subagents_result_reviewing -> human_closure_confirming
human_closure_confirming -> closed

human_plan_confirming -> subagents_plan_reviewing
executing -> subagents_plan_reviewing
result_self_checking -> executing
subagents_result_reviewing -> result_self_checking
subagents_result_reviewing -> executing
human_closure_confirming -> subagents_result_reviewing
human_closure_confirming -> result_self_checking
human_closure_confirming -> executing
human_closure_confirming -> subagents_plan_reviewing
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `subagents_plan_reviewing` -> `human_plan_confirming` | 方案审核完成，主控已处理审核意见，允许提交 Human 确认 | `plan_review.review_items` 应记录审核 Agent、提示上下文、输入引用、重点结论和签署声明；`plan_review.controller_resolution` 应记录主控如何采纳、拒绝、修改或提交争议 |
| `human_plan_confirming` -> `executing` | Human 确认方案允许执行 | 应填写 `plan_confirmed_at`，并保留 Human 方案确认决策；方案审核阶段的 `unresolved_items` 必须已被 Human 确认覆盖、改入执行范围、降级为后续事项或退回重审，不得带着行动前未确认事项进入执行 |
| `executing` -> `result_self_checking` | 主控认为执行结果已足以进入收口自检 | 执行项结果、阻塞、跳过或分流情况应已更新 |
| `result_self_checking` -> `subagents_result_reviewing` | 主控完成结果自检 | `result_review.controller_self_check` 应记录自检上下文、结论、证据和签署声明 |
| `subagents_result_reviewing` -> `human_closure_confirming` | 结果复核完成，主控已处理复核意见，允许提交 Human 关闭确认 | `result_review.review_items` 应记录复核 Agent、提示上下文、输入引用、重点结论和签署声明；`result_review.controller_resolution` 应记录主控如何采纳、拒绝、修改或提交争议 |
| `human_closure_confirming` -> `closed` | Human 确认关闭 | 应填写 `closed_at`，并确认 `closure_evidence` 足以解释关闭结果 |
| `human_plan_confirming` -> `subagents_plan_reviewing` | Human 要求修改方案或补充审核 | 必须在 `revision_history` 记录原因、修改内容和需要重新审核的字段 |
| `executing` -> `subagents_plan_reviewing` | 执行中发现目标、范围、成功标准或执行编排需要修改，且该修改超出 Human 已确认执行范围 | 必须暂停执行，在 `revision_history` 记录原因和修改内容，修改后重新进入方案审核；普通缺陷、文案漂移、验证失败、残留命中或局部实现问题不得作为停下等待的新确认理由，应记录到执行项、自检、残留风险或后续分流并继续完成已确认方案 |
| `result_self_checking` -> `executing` | 主控自检发现执行不足、证据不足或仍需补做 | 必须记录自检不通过原因和继续执行方向 |
| `subagents_result_reviewing` -> `result_self_checking` | 第三方复核要求主控补充自检材料或修正证据整理 | 必须记录复核意见和需补充的自检内容 |
| `subagents_result_reviewing` -> `executing` | 第三方复核认为结果不足，需要继续执行 | 必须记录复核意见和继续执行方向 |
| `human_closure_confirming` -> `subagents_result_reviewing` | Human 要求补充第三方复核 | 必须记录 Human 退回原因和需要复核的内容 |
| `human_closure_confirming` -> `result_self_checking` | Human 要求主控补充自检或整理证据 | 必须记录 Human 退回原因和需要补充的自检内容 |
| `human_closure_confirming` -> `executing` | Human 判断仍需继续执行既有方案 | 必须记录继续执行原因、范围和目标 |
| `human_closure_confirming` -> `subagents_plan_reviewing` | Human 要求修改目标、范围、成功标准或执行编排后重新执行 | 必须在 `revision_history` 记录修改原因、修改字段、修改摘要和重新审核要求；若改变已经大到形成新目标，应关闭当前 WorkCase 并创建新 WorkCase 承接 |

---
## 4. 对象关系

### 4.1 工作项与工作域

每个工作项必须通过 `workarea` 引用一个工作域。工作项不得脱离工作域存在，且 `workarea` 是工作项归属工作域的唯一权威事实源字段。

WorkArea 不反向维护所属 WorkCase ID 列表。Code / Web 需要展示某个 WorkArea 下有哪些 WorkCase 时，应扫描 WorkCase 集合并按 `workarea` 反向聚合；该聚合结果是派生视图，不得回写为 WorkArea YAML 字段。

### 4.2 工作项与执行项

工作项通过 `orchestration.execution_items` 字段承载内部执行编排。执行项用于说明 AI 当前如何安排工作、验证和角色分工；执行项没有独立状态机、编号区段或事实源文件。

执行项不是“更小的工作对象”。它只承载 WorkCase 内部执行委派、恢复和关闭判断所需的最小信息；执行者拿到执行项后可以使用自身的临时 checklist、计划模式、工具调用和局部推理继续拆分，但这些执行期拆分不进入 LDVH 长期事实源。

执行项至少应说明以下最小恢复信息：

1. `id`：工作项内局部唯一标识；
2. `title`：一句话概括；
3. `role`：承担该执行项的角色、子 Agent 类型或专业视角；
4. `mode`：`sequential`、`parallel` 或 `single`；
5. `input_refs`：该执行项读取或依赖的事实源、文件、对象或上下文入口；
6. `expected_output`：该执行项应交还的结果类型、证据类型或判断；
7. `status`：当前内部执行态，由工作项内部使用；
8. `result_summary`：已完成时的结果摘要；
9. `evidence_refs`：稳定产物、验证证据、命令、路径或回写目标；
10. `blocking_reason`：未完成或等待时的阻塞原因，可为空。

执行项内部状态只服务 WorkCase 恢复、证据组织和关闭判断，允许值如下：

| 状态 | 含义 | 条件要求 |
|---|---|---|
| `pending` | 尚未开始 | 可存在于 `subagents_plan_reviewing`、`human_plan_confirming` 或 `executing`；进入 `result_self_checking` 前不得仍为该状态 |
| `in_progress` | 正在执行 | 仅用于 `executing`；进入 `result_self_checking` 前不得仍为该状态 |
| `blocked` | 当前执行项受阻 | 必须填写 `blocking_reason`；进入 `human_closure_confirming` 前应分流、解决或在 `closure_evidence` 中说明接受原因 |
| `done` | 执行项已完成 | 应填写 `result_summary`，并在有稳定证据时填写 `evidence_refs` |
| `skipped` | 明确决定不执行 | 必须填写 `result_summary`；`closure_evidence` 可补充整体接受原因 |

WorkCase 的 Human-facing 阅读必须直接消费本文定义的权威状态，并先表达工作项对象自身生命周期与关闭判断，再表达执行项队列。Code 或 Web 可以从 `status`、`success_criteria` checklist、`plan_review`、`result_review`、`verification_evidence`、`closure_evidence`、`closure_requested_at`、`closed_at` 和 `orchestration.execution_items` 派生只读摘要，用于展示推进阶段、成功标准完成度、执行项状态分布和关闭材料完备性。该摘要不得写回 YAML，也不得成为第二事实源；事实判断仍以本 WorkCase 字段、关联工作对象和 Git 提交记录为准。

#### 4.2.1 Human 感知与状态同步契约

WorkCase 不只约束 YAML 字段，也约束主控在对话和 Web 展示中的行动口径。主控推进 WorkCase 时必须让 Human 能稳定回答：当前处于哪个状态、已经完成哪些执行项、下一 Gate 是什么、还需要 Human 确认什么，以及 Web 能否看到同一状态。

对话口径必须满足：

1. 跨状态推进、完成一组关键执行项、进入验证/复核/关闭前，主控必须用简短状态播报说明当前 WorkCase 状态、已完成执行项、剩余阻塞、下一 Gate 和需要 Human 确认的事项；
2. 审核建议、主控推断和 Human 已确认事实必须分开表达；未被 Human 明确确认的命名、范围、Web 文案、降级接受或关闭判断不得写成已确认事实；
3. 如果主控已经完成了实质执行但尚未回写 WorkCase，必须明示“执行已发生但事实源尚未回写”，不得让 Human 误以为 Web 已能看到真实进展；
4. 对话中的进度播报不得替代 `orchestration.execution_items`、`success_criteria`、`verification_evidence`、`closure_evidence`、`result_review` 或 `revision_history` 的事实源回写。
5. Human 已确认执行后，主控不得再以“行动前还需确认”为由停在中途；新发现的问题应先按已确认范围继续处理，并记录到执行项、自检、残留风险、关闭证据或后续分流。只有发现会越出已确认目标/范围、改变成功标准、引入破坏性副作用或触发安全/事实源边界时，才允许退回方案审核或请求新的 Human Gate。
6. `human_closure_confirming` 只能表述为“等待 Human 关闭确认”或“可提交关闭确认”，不得表述为“整个链条已完成”“已关闭”或“已提交”。主控回答完成度时必须同时说明 WorkCase 是否 `closed`、是否存在 `human_closure_confirmation`、是否还有未提交 Git 变更。

Web 感知必须满足：

1. Web 只能展示 WorkCase 事实源和确定性派生摘要；因此主控不得只修改顶层 `status`，却让执行项、成功标准、验证证据或复核记录长期停留在旧状态；
2. 进入 `executing` 后，如果已经开始或完成任何实质执行，必须在同一工作轮次内回写对应执行项的 `status`、`result_summary` 和必要 `evidence_refs`，让 Web 执行态势反映真实进展；
3. 进入 `result_self_checking` 前，执行项状态必须足以让 Web 展示“完成 / 跳过 / 阻塞 / 待执行”的真实分布；不得出现主控声称已经完成迁移、测试或验证，但 Web 仍显示所有执行项 `pending` 的情况；
4. 成功标准、验证证据、关闭证据和结果复核材料应随阶段推进及时回写；若暂时不能回写，必须停留在当前阶段并说明阻塞原因，不得提前提交下一 Gate。

#### 4.2.2 主控结果自检硬规则

主控结果自检不是进入结果复核前的形式签名。进入 `subagents_result_reviewing` 前，`result_review.controller_self_check` 必须记录本轮实际检查了什么、发现了什么、没发现什么、修复了什么，以及为什么可以交给独立结果复核。

自检记录必须满足：

1. `controller_self_check.result.key_findings` 必须是非空列表；发现问题时逐条记录问题和证据；未发现问题时也必须写入“未发现范围内问题”或等价明确结论；
2. `controller_self_check.result.required_changes` 必须是列表；没有必须修改项时填写空列表；发现范围内必须修改项时不得直接进入 `subagents_result_reviewing`；
3. 自检发现范围内问题后，主控必须先自行修复、补充证据、复跑相关验证，并把修复写入执行项 `result_summary` / `evidence_refs`、`verification_evidence`、`closure_evidence` 或 `revision_history`；修复完成后再提交子 Agent 结果复核；
4. 自检发现超出当前 WorkCase 范围的问题，应写入 `residual_risks`、`followup_refs`、Spark 或后续 WorkCase，并说明为什么不阻塞当前复核；
5. 自检不得把“未检查”写成“未发现”；工具未运行、文件未读、Web 未验或事实源未扫时，必须记录为未完成检查并停留在 `result_self_checking`。

#### 4.2.3 结果复核与完成口径

结果复核是关闭前的独立判断流程，不是主控自检的格式化副本。进入 `subagents_result_reviewing` 后，主控必须按 `result_review.review_policy.required_perspectives` 真实发起并等待独立复核，或明确记录由专门工作流程接管；不得先进入 `human_closure_confirming`，再用主控摘要补填空的 `review_items`。

结果复核必须满足：

1. 每个必需视角都有可追溯的复核主体、提示上下文、输入引用、结论、证据引用和签署声明；
2. 复核 Agent 提出的硬问题必须在进入 `human_closure_confirming` 前修复、退回执行、退回自检，或记录为需要 Human 裁决的争议；不得把范围内硬问题降级为普通 follow-up；
3. 非本 WorkCase 范围的问题可以写入 `residual_risks`、`followup_refs`、Spark 或后续 WorkCase，但主控必须说明为什么不阻塞当前关闭确认；
4. 主控必须在 `result_review.controller_resolution` 中逐项说明采纳、拒绝、已修复、分流或提交争议的处理结果，并保证 `unresolved_items` 不包含行动前未决事项；
5. 若复核流程曾经缺失、失败或被旁路指出不完整，应追加 `revision_history`，说明缺失发生在哪个阶段、如何补齐、补齐后重新验证了什么。

WorkCase 的“完成”口径必须区分四层：

1. 执行完成：执行项、成功标准和验证证据已回写，但仍需主控自检或结果复核；
2. 可提交关闭确认：状态为 `human_closure_confirming`，结果复核和主控处理完成，但 Human 尚未确认关闭；
3. 已关闭：状态为 `closed`，且 `human_closure_confirmation`、`closed_at` 和 `closure_outcome` 已填写；
4. 已提交：相关事实源修改已经进入符合 `specs/10-Git提交规范.md` 的 Git commit records。

主控不得把前一层冒充后一层。用户询问“是否完成整个工作链条”时，应至少核对 WorkCase 状态、关闭确认字段、事实源校验和 Git 工作树状态，再给出结论。

执行项不得被其他工作对象直接引用为长期事实。需要长期追踪的结论，应按性质分流到 WorkCase、ADR、Spark、Pitfall、docs、正式规范或 Git 提交记录。

当某个执行项出现以下任一情况时，应停止把它作为内部执行项继续推进，并按事实性质分流；若它仍是可执行工作，应创建新的 WorkCase：

1. 需要独立目标、独立范围或独立成功标准；
2. 需要独立 Human Gate、独立验收或独立关闭判断；
3. 需要跨会话长期治理或成为后续工作的事实源入口；
4. 产生独立 ADR、Spark、Pitfall 或 Git 提交追溯链路，且该链路已经超出当前 WorkCase 的关闭判断；
5. 范围扩大到当前 WorkCase 无法清晰关闭；
6. 继续作为执行项会迫使 Web、Code 或 Human 把它当成一级对象管理。

### 4.3 工作项与 ADR、Spark、Pitfall 和 Git 提交记录

工作项可以关联 ADR、Spark、Pitfall，并通过 Git 提交记录追溯事实源修改：

1. 长期决策进入 ADR；
2. 暂存信息、待观察输入或分流线索进入 Spark；
3. 已解决且可复用经验进入 Pitfall；
4. Git 文件事实源修改由 Git commit records 承载，并按 `specs/10-Git提交规范.md` 追溯。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名工作项；
2. 将用户输入、Spark 或临时讨论升级为工作项；
3. 将方案审核结果从 `subagents_plan_reviewing` 提交到 `human_plan_confirming`；
4. 确认 `human_plan_confirming` -> `executing`；
5. 将工作项从 `human_closure_confirming` 关闭为 `closed`；
6. 改写目标、成功标准、执行编排、工作域归属或关闭判断；
7. 跳过未验证执行项或通过豁免关闭工作项；
8. 合并、拆分或重新组织工作项。

Human Gate 发生在工作项层。执行项、角色说明、子 Agent 输出和工具结果不作为 Human 直接管理入口；它们必须回到工作项证据或对应工作对象后才成为稳定事实。

---
## 6. 字段契约

公共字段语义定义见 `specs/05.01-工作模型字段定义与语义规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `workcase-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `workcase` | string | 是 | 固定为 `workcase` | Reference | AI、Code、Web |
| `title` | 工作项一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `goal` | 本工作项要达成的目标 | string | 是 | 应独立表达目标，不依赖 `description` 推断 | Narrative | AI、Code、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建时间 | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | 更新时间 | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `workarea` | 所属工作域 ID | string | 是 | 必须引用已存在 WorkArea；这是工作项归属工作域的唯一权威事实源字段 | Reference | AI、Code、Web |
| `priority` | 执行优先级 | string | 是 | `P0`、`P1`、`P2`、`P3`；判断标准见 `specs/05.01-工作模型字段定义与语义规范.md` §3.1 | Reference | AI、Code、Web |
| `description` | 目标背景、范围和问题说明 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `success_criteria` | 工作项成功标准 | string | 是 | 应使用 checklist 或等价可验证条目支持关闭审查 | Checklist | AI、Code、Web |
| `source` | 工作项来源 | string | 是 | 谁在什么场景下表达 | Reference / Narrative | AI、Web |
| `orchestration` | 执行编排对象 | object | 是 | 至少包含 `mode`、`execution_items`、`plan_review` 和 `result_review` | Structured | AI、Code、Web |
| `plan_confirmed_at` | Human 确认方案可执行的时间 | datetime | 条件必填 | `executing`、`result_self_checking`、`subagents_result_reviewing`、`human_closure_confirming` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `verification_evidence` | 验证证据，说明成功标准如何被检查 | string | 条件必填 | `subagents_result_reviewing`、`human_closure_confirming` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closure_evidence` | 关闭证据，说明为何可以关闭、关闭结果、残留风险和 Human Gate 结果 | string | 条件必填 | `subagents_result_reviewing`、`human_closure_confirming` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closure_requested_at` | 请求 Human 关闭确认时间 | datetime | 条件必填 | `human_closure_confirming` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `closed_at` | 关闭时间 | datetime | 条件必填 | `closed` 时必须填写 | Reference | AI、Code、Web |
| `closure_outcome` | 关闭结果分类 | string | 条件必填 | `closed` 时必须填写；允许 `completed`、`partial_completed`、`cancelled`、`superseded`、`invalid`、`degraded_accepted` | Reference | AI、Code、Web |
| `residual_risks` | 残留风险摘要列表 | list[string] | 否 | 默认为空列表；关闭时如接受风险或未完成项必须填写 | Evidence / Log | AI、Web |
| `followup_refs` | 后续承接引用 | list[string] | 否 | 默认为空列表；可引用后续 WorkCase、Spark、ADR、Pitfall 或文档路径 | Reference | AI、Code、Web |
| `revision_history` | 方案、执行或关闭确认退回后的修订记录 | list[object] | 否 | 默认为空列表；发生退回、方案修改、成功标准修改或执行编排修改时必须追加 | Structured / Log | AI、Code、Web |
| `related_docs` | 关联文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_sparks` | 来源或关联火花 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联踩坑经验 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workcases` | 关联工作项 | list[string] | 否 | 默认为空列表；承载 WorkCase ID，不表示父子或阻塞关系 | Reference | AI、Code、Web |

### 6.1 orchestration 最小结构

`orchestration` 至少包含以下字段：

| 字段名 | 含义 | 类型 | 必填 |
|---|---|---|---|
| `mode` | 总体编排方式，允许 `single`、`sequential`、`parallel`、`mixed` | string | 是 |
| `execution_items` | 执行项列表 | list[object] | 是 |
| `plan_review` | 方案审核记录，承载第三方子 Agent 对执行前方案的审核签署 | object | 是 |
| `result_review` | 结果自检和结果复核记录，承载主控自检和第三方子 Agent 对关闭材料的复查签署 | object | 是 |

`orchestration.mode` 的允许值如下：

| 值 | 含义 |
|---|---|
| `single` | 单一执行项或单一执行路径 |
| `sequential` | 多个执行项按顺序推进 |
| `parallel` | 多个执行项可并行推进 |
| `mixed` | 同时存在顺序和并行安排 |

`execution_items` 是工作项内部字段，不得被提升为独立工作模型。并行执行项可以由不同子 Agent 或专业角色执行；子 Agent 不再继续创建子 Agent，所有结果回到主控汇总、自检和后续复检。

每个 `orchestration.execution_items` 对象的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 状态条件 |
|---|---|---|---|---|
| `id` | WorkCase 内局部唯一标识 | string | 是 | 当前 WorkCase 内不得重复；不得作为全局对象 ID |
| `title` | 执行项一句话概括 | string | 是 | 应能支持恢复上下文 |
| `role` | 专业视角、责任边界或子 Agent 类型 | string | 是 | 只保留最小角色标识，不定义完整 Role Contract |
| `mode` | 执行项编排方式，允许 `single`、`sequential`、`parallel` | string | 是 | 不得使用 `mixed`；混合编排只属于 `orchestration.mode` |
| `input_refs` | 执行项输入引用 | list[string] | 是 | 可包含对象 ID、路径、URL、命令或说明性引用 |
| `expected_output` | 执行项预期输出 | string | 是 | 应说明交还结果、证据或判断 |
| `status` | 执行项内部执行态 | string | 是 | 必须属于 §4.2 执行项内部状态枚举 |
| `result_summary` | 执行项结果摘要 | string 或 null | 条件必填 | `done` 或 `skipped` 时必须填写 |
| `evidence_refs` | 执行项证据引用 | list[string] | 否 | 默认为空列表；有稳定产物、命令或变更时应填写 |
| `blocking_reason` | 执行项阻塞原因 | string 或 null | 条件必填 | `blocked` 时必须填写 |

`evidence_refs` 是混合引用字段，可以包含对象 ID、文件/目录路径、URL、命令、Git 变更引用或说明性文本。Code 应只对可判定为文件或目录路径的项做存在性检查；命令、对象 ID、提交号、外部 URL、仓库外临时路径和带附注的说明性文本不得被误判为必须存在的项目内路径。

`role` 只表达本执行项所需的专业视角、责任边界或子 Agent 类型，不在 WorkCase 字段契约中提前定义完整角色规则。完整角色规则如需稳定化，应由工作流程、能力资产规范或后续专门规范承接；WorkCase 只保留执行恢复所需的最小角色标识。

`plan_review` 和 `result_review` 不创建独立 Review 工作对象，但它们是 WorkCase 内部权威审核事实。审核记录必须能回答：哪个 Agent 审核、以什么角色审核、当时获得的提示上下文和输入引用是什么、审核结论是什么、主控如何处理审核意见、何时签署。没有真实密码学能力时，签署为可审计 attestation，不得伪装成密钥签名。

WorkCase 只记录审核事实和可决策摘要，不记录子 Agent 审核原文全文。审核条目应保留关键发现、关键建议、必须修改项和证据引用；完整原文只有在高风险审核、争议审核或 Human Gate 需要时，才通过可选 `raw_output_ref` 指向外部稳定位置。

子 Agent 审核完成后，主控必须形成 `controller_resolution`。主控不得改写 `review_items` 中的原始审核结论；主控只能采纳、拒绝、归并、提交 Human 裁决，或修改 WorkCase 的方案、成功标准、执行编排、验证证据、关闭证据、残留风险等字段。凡主控根据审核意见修改 WorkCase 字段，必须追加 `revision_history`；若修改影响本轮审核对象本身，必须回到对应的子 Agent 审核状态重新审核。

子 Agent 审核的视角选择和工具方法当前由主控安排。WorkCase 只承载审核编排需求和审核事实，不承载子 Agent 系统实现；当存在 active 的专门审核编排工作流程时，主控应调用该流程，并在 `workflow_ref` 中记录承接位置。

`orchestration.plan_review` 的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 条件 |
|---|---|---|---|---|
| `orchestration_owner` | 方案审核编排责任方 | string | 是 | 允许 `main_controller` 或 `workflow` |
| `workflow_ref` | 专门审核编排工作流程引用 | string 或 null | 否 | 没有专门流程时为空；由工作流程接管时必须填写 |
| `review_policy.selection_reason` | 审核视角选择理由 | string | 是 | 说明为什么需要这些视角 |
| `review_policy.required_perspectives` | 必须执行的审核视角 | list[string] | 是 | 例如 scope_reviewer、success_criteria_reviewer、risk_reviewer、verification_reviewer |
| `review_policy.optional_perspectives` | 可选补充审核视角 | list[string] | 否 | 可为空列表 |
| `review_policy.tool_method_requirements` | 工具或方法要求 | list[string] | 否 | 写能力类型，如 `read_authoritative_sources`、`inspect_changed_files`、`run_relevant_validators`、`produce_evidence_refs`，不绑定具体工具名 |
| `review_policy.aggregation_rule` | 多个审核结论聚合规则 | string | 是 | 说明 pass、fail、needs_human_gate 等结论如何聚合 |
| `review_items` | 方案审核条目列表 | list[object] | 是 | `subagents_plan_reviewing` 时可以正在补齐；进入 `human_plan_confirming` 前必须全部完成 |
| `review_items[].id` | WorkCase 内局部审核条目 ID | string | 是 | 当前 WorkCase 内唯一 |
| `review_items[].role` | 审核角色或专业视角 | string | 是 | 例如 specs-reviewer、web-reviewer、governance-reviewer |
| `review_items[].agent_name` | 执行审核的子 Agent 名称或稳定标识 | string | 是 | 必须能让 Human 和后续 AI 识别是谁做的审核 |
| `review_items[].requested_at` | 审核请求时间 | datetime | 是 | ISO 8601 时间戳 |
| `review_items[].prompt_context.objective` | 给审核 Agent 的目标说明 | string | 是 | 应说明本次审核要判断什么 |
| `review_items[].prompt_context.input_refs` | 给审核 Agent 的输入引用 | list[string] | 是 | 应列出方案、规范、事实源、上下文入口或其他输入 |
| `review_items[].prompt_context.constraints` | 给审核 Agent 的约束 | list[string] | 否 | 可为空列表；用于记录只读、禁止修改、重点检查等约束 |
| `review_items[].context_digest` | 审核上下文摘要 | string | 否 | 可使用 hash 或说明性摘要；用于帮助追溯当时上下文，不替代输入引用 |
| `review_items[].result.status` | 审核结论 | string | 是 | 允许 `pass`、`pass_with_followups`、`fail`、`needs_human_gate` |
| `review_items[].prompt_context.prompt_digest` | 审核提示摘要 | string | 否 | 记录关键提示摘要，不要求保存完整提示全文 |
| `review_items[].result.summary` | 审核结论摘要 | string | 是 | 必须说明通过、条件通过或不通过的理由 |
| `review_items[].result.key_findings` | 关键发现 | list[string] | 否 | 只记录对 Human 或主控决策有影响的发现 |
| `review_items[].result.recommendations` | 关键建议 | list[string] | 否 | 只记录需要主控处理或 Human 知道的建议 |
| `review_items[].result.required_changes` | 必须修改项 | list[string] | 否 | 为空表示该审核条目没有强制修改要求 |
| `review_items[].result.evidence_refs` | 审核证据引用 | list[string] | 否 | 可包含路径、命令、对象 ID、报告或说明性引用 |
| `review_items[].raw_output_ref` | 审核原文外部引用 | string 或 null | 否 | 常规审核为空；高风险或争议审核才引用外部稳定位置 |
| `review_items[].attested_at` | 审核签署时间 | datetime | 是 | 审核结论完成时填写 |
| `review_items[].attestation.signer` | 签署者 | string | 是 | 通常等于 `agent_name` |
| `review_items[].attestation.statement` | 签署声明 | string | 是 | 应声明基于上述 prompt context 和 input refs 完成审核并对结论负责 |
| `controller_resolution` | 主控对审核意见的处理记录 | object 或 null | 条件必填 | 进入 `human_plan_confirming` 前必须填写 |
| `controller_resolution.resolved_at` | 主控处理完成时间 | datetime | 是 | ISO 8601 时间戳 |
| `controller_resolution.resolver` | 处理者 | string | 是 | 通常为主控 AI 标识 |
| `controller_resolution.source_review_item_ids` | 被处理的审核条目 ID | list[string] | 是 | 应覆盖本轮已完成审核条目 |
| `controller_resolution.accepted_findings` | 已采纳发现 | list[string] | 否 | 可为空列表 |
| `controller_resolution.rejected_findings` | 未采纳发现 | list[string] | 否 | 不得只写“无”；有拒绝时应说明理由 |
| `controller_resolution.required_changes_applied` | 已落实必须修改项 | list[string] | 否 | 修改 WorkCase 字段时必须与 `revision_history` 对齐 |
| `controller_resolution.unresolved_items` | 未解决或需 Human 裁决事项 | list[string] | 否 | 可为空列表；非空时 Human 确认必须覆盖；`executing` 及后续状态不得仍保留行动前未确认事项 |
| `controller_resolution.changed_fields` | 主控处理导致修改的字段路径 | list[string] | 否 | 改字段时必须填写，并回指 `revision_history` |
| `controller_resolution.revision_history_refs` | 对应修订记录引用 | list[string] | 否 | 可使用 `revision_history` 局部引用或说明性引用 |
| `controller_resolution.summary` | 主控处理摘要 | string | 是 | 说明如何处理审核意见以及是否需要重审或 Human 裁决 |
| `human_confirmation` | Human 方案确认记录 | object 或 null | 条件必填 | `executing` 及后续状态必须填写 |
| `human_confirmation.decision` | Human 方案决策 | string | 条件必填 | 允许 `execute`、`revise_plan`、`close` |
| `human_confirmation.scope` | Human 确认范围 | string | 条件必填 | 说明本次授权覆盖的目标、范围和执行边界 |
| `human_confirmation.constraints` | Human 确认约束 | list[string] | 条件必填 | 可为空列表；有约束时必须写清 |
| `human_confirmation.confirmed_at` | Human 确认方案时间 | datetime | 条件必填 | `executing` 及后续状态必须填写 |
| `human_confirmation.summary` | Human 确认摘要 | string | 条件必填 | 说明确认依据、是否有条件通过和执行边界 |

`orchestration.result_review` 的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 条件 |
|---|---|---|---|---|
| `controller_self_check` | 主控结果自检记录 | object 或 null | 条件必填 | `subagents_result_reviewing`、`human_closure_confirming` 或 `closed` 时必须填写 |
| `controller_self_check.controller` | 主控标识 | string | 是 | 填写主控 AI 或执行控制者标识 |
| `controller_self_check.checked_at` | 自检完成时间 | datetime | 是 | ISO 8601 时间戳 |
| `controller_self_check.prompt_context.objective` | 主控自检目标 | string | 是 | 应说明检查成功标准、验证证据、关闭证据和残留风险 |
| `controller_self_check.prompt_context.input_refs` | 主控自检输入引用 | list[string] | 是 | 应列出 WorkCase、产物、验证命令、相关对象或上下文入口 |
| `controller_self_check.result.status` | 主控自检结论 | string | 是 | 允许 `pass`、`pass_with_followups`、`fail`、`needs_human_gate` |
| `controller_self_check.result.summary` | 主控自检摘要 | string | 是 | 必须说明是否可提交第三方复核及理由 |
| `controller_self_check.result.key_findings` | 主控自检发现清单 | list[string] | 是 | 必须非空；无发现时写明未发现范围内问题 |
| `controller_self_check.result.required_changes` | 主控自检必须先修复项 | list[string] | 是 | 没有必须修改项时为空列表；非空时不得进入结果复核，必须先修复并回写证据 |
| `controller_self_check.result.evidence_refs` | 主控自检证据引用 | list[string] | 否 | 可为空列表 |
| `controller_self_check.attested_at` | 主控自检签署时间 | datetime | 是 | 自检结论完成时填写 |
| `controller_self_check.attestation.signer` | 签署者 | string | 是 | 通常为主控标识 |
| `controller_self_check.attestation.statement` | 签署声明 | string | 是 | 应声明基于上述上下文完成自检并对结论负责 |
| `orchestration_owner` | 结果复核编排责任方 | string | 是 | 允许 `main_controller` 或 `workflow` |
| `workflow_ref` | 专门结果复核编排工作流程引用 | string 或 null | 否 | 没有专门流程时为空；由工作流程接管时必须填写 |
| `review_policy` | 结果复核策略 | object | 是 | 字段与 `plan_review.review_policy` 相同，视角和方法按结果复核选择 |
| `review_items` | 结果复核条目列表 | list[object] | 是 | `subagents_result_reviewing` 时可以正在补齐；进入 `human_closure_confirming` 前必须全部完成 |
| `review_items[]` | 结果复核条目结构 | object | 是 | 字段与 `plan_review.review_items[]` 相同，`phase` 语义为结果复核 |
| `controller_resolution` | 主控对结果复核意见的处理记录 | object 或 null | 条件必填 | 进入 `human_closure_confirming` 前必须填写；字段与 `plan_review.controller_resolution` 相同 |
| `human_closure_confirmation` | Human 关闭确认记录 | object 或 null | 条件必填 | `closed` 时必须填写 |
| `human_closure_confirmation.decision` | Human 关闭决策 | string | 条件必填 | 允许 `close`、`continue_execution`、`revise_plan`、`request_result_review`、`request_self_check` |
| `human_closure_confirmation.scope` | Human 关闭确认范围 | string | 条件必填 | 说明确认关闭或退回覆盖的范围 |
| `human_closure_confirmation.constraints` | Human 关闭约束 | list[string] | 条件必填 | 可为空列表；有约束时必须写清 |
| `human_closure_confirmation.confirmed_at` | Human 确认关闭时间 | datetime | 条件必填 | `closed` 时必须填写 |
| `human_closure_confirmation.summary` | Human 关闭确认摘要 | string | 条件必填 | 说明关闭依据、残留风险接受或退回判断 |

`revision_history` 的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 条件 |
|---|---|---|---|---|
| `revision_history[].at` | 修订发生时间 | datetime | 是 | ISO 8601 时间戳 |
| `revision_history[].from_status` | 修订前状态 | string | 是 | 必须属于 §3.1 状态枚举 |
| `revision_history[].to_status` | 修订后状态 | string | 是 | 必须属于 §3.1 状态枚举 |
| `revision_history[].actor` | 触发修订的主体 | string | 是 | Human、主控 AI、审核 Agent 或其他明确主体 |
| `revision_history[].reason` | 修订原因 | string | 是 | 必须说明为什么退回或修改 |
| `revision_history[].changed_fields` | 修改字段路径 | list[string] | 是 | 例如 `success_criteria`、`orchestration.execution_items` |
| `revision_history[].summary` | 修改内容摘要 | string | 是 | 必须说明改了什么以及后续应如何执行、审核或确认 |

### 6.2 状态条件字段

| 状态 | 必须满足的对象条件 |
|---|---|
| `subagents_plan_reviewing` | 基础字段、`workarea`、`priority`、`description`、`success_criteria`、`source`、`orchestration.mode`、`orchestration.execution_items`、`orchestration.plan_review` 和 `orchestration.result_review` 已存在；`execution_items` 不得为空；`plan_review.review_policy` 已存在；`plan_review.review_items` 可以正在补齐 |
| `human_plan_confirming` | `plan_review.review_items` 已完成并具备 Agent、角色、提示上下文、输入引用、重点结论和签署声明；`plan_review.controller_resolution` 已记录主控处理意见、必要修改和未决事项；不存在必须先改方案并重审的失败结论；等待 Human 确认 |
| `executing` | 满足 `human_plan_confirming` 条件；`plan_confirmed_at` 和 `plan_review.human_confirmation` 已填写；方案审核阶段不得仍存在行动前未确认的 `unresolved_items`；执行项可以处于 `pending`、`in_progress`、`blocked`、`done` 或 `skipped`；一旦发生实质执行，执行项状态、结果摘要和证据引用必须在同一工作轮次内回写 |
| `result_self_checking` | 执行项不得仍为 `pending` 或 `in_progress`；`blocked` 执行项必须填写 `blocking_reason`；主控正在整理或填写 `result_review.controller_self_check`、`verification_evidence` 和 `closure_evidence`；成功标准检查进展和执行项状态必须足以支持 Web 派生态势 |
| `subagents_result_reviewing` | `result_review.controller_self_check` 已填写并签署；`controller_self_check.result.key_findings` 已非空记录发现或明确无发现，`controller_self_check.result.required_changes` 已存在且不得保留未处理必须修改项；`verification_evidence` 和 `closure_evidence` 已填写；`result_review.review_policy` 已存在；`result_review.review_items` 可以正在补齐，但主控不得把该状态表述为可关闭或已完成 |
| `human_closure_confirming` | `result_review.review_items` 已按必需视角完成并具备 Agent、角色、提示上下文、输入引用、重点结论和签署声明；`result_review.controller_resolution` 已记录主控处理意见、必要修改和未决事项；范围内硬问题已修复、退回或提交 Human 裁决；`closure_requested_at` 已填写；等待 Human 关闭确认 |
| `closed` | 满足 `human_closure_confirming` 条件；`closed_at`、`closure_outcome` 和 `result_review.human_closure_confirmation` 已填写；`closure_evidence` 足以说明关闭结果、残留风险、未完成项分流和 Human Gate 结果；若该 WorkCase 对应 Git 事实源修改，仍应区分“已关闭”和“已提交” |

### 6.3 YAML 示例

```yaml
id: workcase-0001
type: workcase
title: 重构工作模型状态边界
status: subagents_result_reviewing
created: '2026-06-18T00:00:00'
updated: '2026-06-18T03:30:00'
workarea: workarea-0001
priority: P1
description: |
  将一次模型重构目标组织为可执行、可验证、可关闭的工作项。
success_criteria: |
  - [ ] 工作模型规范已更新
  - [ ] 事实实例路径已明确
  - [ ] Code 和 Web 缺口已记录
source: 用户确认创建工作项
plan_confirmed_at: '2026-06-18T01:00:00'
verification_evidence: |
  - `python3 code/specs_validate.py all --fail-on-diagnostics` 已执行并通过。
closure_evidence: |
  成功标准已检查；剩余 Code 和 Web 缺口已记录为后续工作，不阻塞当前计划进入结果复核。
closure_outcome:
residual_risks:
  - Code 和 Web 同步作为后续工作处理。
followup_refs: []
orchestration:
  mode: mixed
  execution_items:
    - id: item-1
      title: 更新模型规范
      role: specs-editor
      mode: sequential
      input_refs:
        - specs/05-工作模型基础规范.md
        - specs/21-WorkCase-工作项.md
      expected_output: 更新后的 WorkCase 规范正文和可复查验证结果
      status: done
      result_summary: WorkCase 规范已更新，执行项边界已收敛为内部恢复节点。
      evidence_refs:
        - specs/21-WorkCase-工作项.md
        - python3 code/specs_validate.py all --fail-on-diagnostics
      blocking_reason:
  plan_review:
    orchestration_owner: main_controller
    workflow_ref:
    review_policy:
      selection_reason: 工作项涉及规范状态机，需要规范一致性视角审核。
      required_perspectives:
        - spec_or_contract_reviewer
        - verification_reviewer
      optional_perspectives: []
      tool_method_requirements:
        - read_authoritative_sources
        - produce_evidence_refs
      aggregation_rule: 任一必须修改项未处理时不得进入 Human 方案确认。
    review_items:
      - id: plan-review-1
        role: specs-reviewer
        agent_name: codex-specs-review-agent
        requested_at: '2026-06-18T00:20:00'
        prompt_context:
          objective: 审核该 WorkCase 的目标、范围、成功标准和执行编排是否可执行。
          input_refs:
            - workcase-0001
            - specs/21-WorkCase-工作项.md
          constraints:
            - 只审核方案，不修改事实源。
          prompt_digest: 审核 WorkCase 方案是否可执行、可验证、可关闭。
        context_digest: workcase-0001-plan-context
        result:
          status: pass
          summary: 方案边界清晰，可以提交 Human 确认。
          key_findings:
            - 方案目标、成功标准和执行项之间可追溯。
          recommendations:
            - Human 确认时应保留 Code 和 Web 后续同步边界。
          required_changes: []
          evidence_refs:
            - workcase-0001
        raw_output_ref:
        attested_at: '2026-06-18T00:40:00'
        attestation:
          signer: codex-specs-review-agent
          statement: 基于上述 prompt context 和 input refs 完成方案审核并对结论负责。
    controller_resolution:
      resolved_at: '2026-06-18T00:50:00'
      resolver: codex-main-controller
      source_review_item_ids:
        - plan-review-1
      accepted_findings:
        - 方案目标、成功标准和执行项之间可追溯。
      rejected_findings: []
      required_changes_applied: []
      unresolved_items: []
      changed_fields: []
      revision_history_refs: []
      summary: 主控接受方案审核结论，未修改方案，可提交 Human 确认。
    human_confirmation:
      decision: execute
      scope: 按当前目标、成功标准和执行编排执行。
      constraints:
        - Code 和 Web 后续同步不阻塞本轮规范收敛。
      confirmed_at: '2026-06-18T01:00:00'
      summary: Human 确认按该方案执行。
  result_review:
    controller_self_check:
      controller: codex-main-controller
      checked_at: '2026-06-18T03:00:00'
      prompt_context:
        objective: 检查成功标准、验证证据、关闭证据和残留风险是否足以提交复核。
        input_refs:
          - workcase-0001
          - specs/21-WorkCase-工作项.md
          - python3 code/specs_validate.py all --fail-on-diagnostics
      result:
        status: pass_with_followups
        summary: 当前结果可以进入第三方复核，Code 和 Web 后续同步已作为残留工作记录。
        key_findings:
          - 未发现范围内阻塞问题；Code 和 Web 后续同步已记录为残留工作。
        required_changes: []
        evidence_refs:
          - specs/21-WorkCase-工作项.md
      attested_at: '2026-06-18T03:05:00'
      attestation:
        signer: codex-main-controller
        statement: 基于上述上下文完成结果自检并对结论负责。
    review_items: []
    orchestration_owner: main_controller
    workflow_ref:
    review_policy:
      selection_reason: 当前状态等待结果复核，需检查证据和残留风险是否足以提交关闭确认。
      required_perspectives:
        - evidence_reviewer
        - residual_risk_reviewer
      optional_perspectives: []
      tool_method_requirements:
        - inspect_tests_or_evidence
        - produce_evidence_refs
      aggregation_rule: 必须修改项未落实时不得进入 Human 关闭确认。
    controller_resolution:
    human_closure_confirmation:
revision_history: []
related_docs: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_workcases: []
```

---
## 7. 事实源回写与证据留存

工作项的目标、成功标准、执行编排、验证证据和关闭证据回写到工作项 YAML。执行项结果只保留摘要、证据和稳定输出路径，不复制完整对话、工具日志或子 Agent 中间过程。

关闭工作项前，至少应具备：

1. 成功标准检查结果；
2. 主控自检结论；
3. 必要时的专业角色复检结论；
4. 验证命令、文件路径、产物引用或人工确认记录；
5. 经验、决策、火花或提交追溯的分流结果。

进入 `result_self_checking` 前，不要求所有执行项都必须成功，但必须让执行项状态足以说明：哪些完成、哪些跳过、哪些阻塞被分流或接受、哪些风险仍需 Human 判断。进入 `subagents_result_reviewing` 前，主控自检、验证证据和关闭证据必须足以支持第三方复核。`closed` 不代表目标必然成功，只代表该 WorkCase 的推进责任已经依据证据和关闭判断稳定终止。

事实源回写必须跟上对话进度。主控不得只在对话中宣布“已完成”“已通过”“进入下一阶段”，却让 WorkCase 仍呈现全部执行项 `pending`、成功标准未检查、结果自检为空或 Web 无法派生真实态势。若回写尚未完成，主控应继续停留在当前阶段并把“待回写事实源”作为当前剩余工作，而不是进入下一 Gate。

---
## 8. 适配边界

Code 应检查：

1. 工作项必须引用存在的 WorkArea；
2. `priority` 必须属于 `P0`、`P1`、`P2`、`P3`；
3. 不得维护 `importance` 字段；
4. `orchestration.execution_items` 中的 `id` 在当前工作项内唯一；
5. `orchestration.mode`、`orchestration.execution_items.mode` 和 `orchestration.execution_items.status` 必须属于本文定义的枚举；
6. `status` 必须属于本文 §3.1 定义的 WorkCase 状态枚举，不得继续使用 `draft`、`active` 或 `review_needed`；
7. `subagents_plan_reviewing` 及后续状态必须存在 `orchestration.plan_review` 和 `orchestration.result_review`；
8. `human_plan_confirming` 及后续状态必须能追溯方案审核 Agent、提示上下文、输入引用、重点结论、签署声明和主控处理记录；
9. `executing` 及后续状态必须填写 `plan_confirmed_at` 和 `plan_review.human_confirmation`；
10. `executing` 及后续状态不得在 `plan_review.controller_resolution.unresolved_items` 中保留行动前未确认事项；
11. `result_self_checking` 及后续状态不得存在 `pending` 或 `in_progress` 执行项；
12. `subagents_result_reviewing` 及后续状态必须填写主控自检、验证证据和关闭证据；
13. `subagents_result_reviewing` 状态下若 `result_review.review_items` 为空，Code 应至少给出 warning，提醒结果复核流程尚未真实启动或尚未记录；
14. `human_closure_confirming` 和 `closed` 必须填写 `closure_requested_at`，并具备结果复核 Agent、提示上下文、输入引用、重点结论、签署声明和主控处理记录；
15. `closed` 工作项必须填写 `closed_at`、`closure_outcome` 和 `result_review.human_closure_confirmation`；
16. `human_closure_confirming` 不得被 Code/Web 派生为 `closed` 或“已完成”；Web 展示应明确这是等待 Human 关闭确认的阶段；
17. `blocked` 执行项必须填写 `blocking_reason`；
18. `done` 或 `skipped` 执行项必须填写 `result_summary`；
19. `executing` 状态下若所有执行项仍为 `pending`，Code 应至少给出 warning，提醒事实源和 Web 派生态势可能没有跟上真实执行；
20. 发生退回、目标修改、成功标准修改、执行编排修改，或主控根据审核意见修改 WorkCase 字段时必须追加 `revision_history`，记录原因、修改字段和修改内容；
21. 执行项不得被其他工作对象作为独立对象引用；
22. `related_workcases` 必须承载 WorkCase ID；
23. 工作项相关提交由 Git 历史、对象 ID、文件路径和提交正文自然文本派生，不得手写维护 `related_changes`。

Web 应把工作项作为 Human 直接查看和确认的主对象。Web 可以展示执行编排、验证证据和关闭证据，但不得把执行项提升为一级导航、独立对象详情页或可独立写入的权威事实。

---
## 9. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 工作项必须遵守 05、05.01 和本文定义的人机职责边界 | 05、05.01、本文、Human Gate | 工作模型治理 | 创建、迁移、关闭或重排工作项时 |
| 确定性执行要求 | 工作项内部执行项不得作为独立工作模型出现 | Validator、CLI、Web 展示 | 事实模型校验 | 创建、更新、展示或关闭工作项时 |
| 确定性执行要求 | 工作项必须依据 `specs/05.01-工作模型字段定义与语义规范.md` §3.1 维护 `priority`，不得维护 `importance` | Validator、CLI、Web 展示 | 字段契约同步 | 创建、更新、排序、筛选或展示工作项时 |
| 确定性执行要求 | 工作项状态必须明确区分方案审核、方案确认、执行、结果自检、结果复核、关闭确认和已关闭，不得把审核阶段折叠为执行态派生含义 | Validator、CLI、Web 展示 | 状态机同步 | 状态枚举、流转、实例校验或 Web 展示变化时 |
| 子 Agent 思考要求 | 方案审核和结果复核必须记录审核 Agent、角色、提示上下文、输入引用、重点结论、可审计签署声明和主控处理记录 | Agent 能力、主控多视角审查、事实实例校验 | 审核事实同步 | 方案审核、结果复核、主控处理记录、Agent 能力或签署字段变化时 |
| 子 Agent 思考要求 | 结果复核必须按必需视角真实启动、等待结论、处理硬问题并记录主控 resolution；不得用空 `review_items`、主控代签或事后补表冒充独立复核 | Validator warning、Agent 编排记录、主控 resolution、revision_history | 复核闭环同步 | 进入结果复核、旁路指出复核缺失、修复复核发现或请求关闭确认时 |
| Human 交互要求 | 方案执行和最终关闭必须经 Human 确认；退回、修改方案或接受残留风险必须记录原因和修改内容 | Human Gate、Web 展示、事实实例校验 | Gate 同步 | 方案确认、关闭确认、退回或修改关键字段时 |
| Human 交互要求 | 主控跨阶段推进时必须说明当前状态、已完成执行项、剩余阻塞、下一 Gate 和待 Human 确认事项；未确认推断不得写成已确认事实 | 对话状态播报、Human Gate、WorkCase 回写、Web 派生态势 | 感知同步 | 状态推进、执行项完成、验证复核、Web 展示或 Human 待确认事项变化时 |
| 入口可见要求 | WorkCase 顶层状态、执行项状态、成功标准、验证证据和结果复核记录必须能支持 Web 展示真实阶段；不得让 Web 长期显示与对话进展矛盾的派生态势 | Validator warning、Web 派生摘要、事实源回写 | 展示同步 | 执行开始、执行完成、进入结果自检、结果复核或关闭确认时 |
| Human 交互要求 | 主控和 Web 必须区分执行完成、可提交关闭确认、已关闭和已提交，不得把 `human_closure_confirming` 或校验干净表述为整个工作链条完成 | 对话状态播报、Web 状态标签、Git 工作树检查、提交规范 | 关闭与提交同步 | 用户询问完成度、进入关闭确认、关闭 WorkCase 或准备 Git 提交时 |
| 生命周期触发要求 | 工作项规范变化后应检查 Code、Web、事实实例和相关工作流程是否需要同步 | Code 测试、事实校验、Web 检查、流程检查 | 触发保障 | 字段、状态、执行编排或事实源路径变化时 |

---
## 10. 检查要求

| 检查项 | 标准 |
|---|---|
| 工作域归属 | 每个工作项必须引用一个存在的工作域 |
| 优先级 | `priority` 已填写且符合 05.01 统一标准，未维护 `importance` |
| 执行编排 | `orchestration.execution_items` 是内部字段，不存在独立执行项事实源文件 |
| 人类入口 | 关闭审查发生在工作项层 |
| 状态枚举 | `status` 属于本文 §3.1 状态枚举，且不使用旧的 `draft`、`active`、`review_needed` |
| 方案审核 | `human_plan_confirming` 及后续状态具备方案审核 Agent、提示上下文、输入引用、重点结论、签署声明和主控处理记录 |
| 对话感知 | 跨阶段推进时清楚表达当前状态、已完成项、剩余阻塞、下一 Gate 和待 Human 确认事项 |
| Web 感知 | `executing` 及后续状态的执行项、成功标准和证据回写足以支持 Web 派生真实态势 |
| 结果自检 | `subagents_result_reviewing` 及后续状态具备主控自检、验证证据和关闭证据 |
| 结果复核 | `human_closure_confirming` 及后续状态具备真实独立结果复核 Agent、提示上下文、输入引用、重点结论、签署声明和主控处理记录；硬问题已处理或退回 |
| 关闭证据 | `human_closure_confirming` / `closed` 具备验证证据、关闭证据和关闭确认请求时间 |
| 完成口径 | 能清楚区分执行完成、可提交关闭确认、已关闭和已提交；`human_closure_confirming` 不被表述为 `closed` |
| 修订记录 | 退回、方案修改、成功标准修改、执行编排修改或主控根据审核意见修改字段时，`revision_history` 记录原因、字段和修改内容 |
| 角色边界 | 执行项仅保留最小 `role` 标识；完整角色规则如需稳定化，由工作流程、能力资产规范或后续专门规范承接 |

---
## 11. 待补齐事项

1. WorkCase 状态机、方案审核签署、结果自检、结果复核、Human 关闭确认和修订记录已经成为本文规则；后续 Code、Web、事实实例和相关工作流程应按本文同步实现；
2. 旧工作对象清退后的历史说明只应保留在 Git 历史、Spark、ADR 或明确标注的研究材料中，不得重新成为当前事实源兼容要求。
