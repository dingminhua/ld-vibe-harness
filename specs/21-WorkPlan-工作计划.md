# WorkPlan-工作计划

```yaml
ldvh_doc:
  doc_id: "21"
  doc_kind: "work_model_spec"
  title: "WorkPlan-工作计划"
  status: "active"
  canonical_path: "specs/21-WorkPlan-工作计划.md"
  created: "2026-06-12"
  updated: "2026-06-20"
  parent_doc: ""
  relation: ""
  positioning: "定义 WorkPlan / 工作计划工作模型，包括对象定位、准入条件、事实源边界、方案审核、执行、结果自检、结果复核、关闭确认、变更记录、字段契约、事实源回写和适配规则"
  scope: "所有接入 LDVH 且需要把一次目标组织为可执行、可验证、可关闭工作计划的项目"
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
  name_en: WorkPlan
  name_zh: 工作计划
  collection_status: active
  canonical_path: specs/21-WorkPlan-工作计划.md
  instance_root: ldvh-base/workplans/
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

WorkPlan / 工作计划是 Human 与 AI 围绕一次目标达成的工作事实契约。工作计划承载已经由主控 AI 起草到可审核程度的目标、范围、成功标准、所属工作域、执行编排、方案审核、执行过程、结果自检、结果复核、关闭确认和经验分流。

主控 AI 在 WorkPlan 创建前可以起草方案草稿；该起草动作不是 WorkPlan 状态。只有当草稿已经足以被第三方子 Agent 审核时，才创建 WorkPlan 并进入方案审核。Human 主要确认方案是否允许执行和结果是否允许关闭；AI 负责在工作计划内部安排执行项、调度角色或专业视角、完成验证、整理证据并接受独立复核。执行项只属于 WorkPlan 内部编排，不作为独立工作模型，不进入 20-39 集合，也不在 `ldvh-base/` 下形成独立事实实例。

### 1.1 工作计划准入条件

一个目标满足以下条件之一时，应形成工作计划：

1. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
2. 需要表达目标、范围、成功标准、验证证据或关闭判断；
3. 需要多个执行项、并行安排、顺序安排或角色分工；
4. 需要 Human 明确确认目标、范围、成功标准或关闭判断；
5. 需要留下最小恢复信息、验证证据、关闭证据或结果物引用；
6. 不结构化会导致目标、范围、执行编排或完成判断漂移。

当前对话即可完成、无需留存记录、无需流程治理的小工作，不创建工作计划。

---
## 2. 事实源边界

工作计划实例的权威事实源位置为：

```text
ldvh-base/workplans/workplan-{NNNN}-short-title.yaml
```

| 内容 | 权威位置 |
|---|---|
| 工作计划工作模型规范 | `specs/21-WorkPlan-工作计划.md` |
| 工作计划实例 | `ldvh-base/workplans/` |
| 工作计划字段内容格式 | `specs/05.02-工作模型字段内容与格式规范.md` |
| 工作计划展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

执行过程不作为长期事实源。工作计划只保留最小恢复信息、验证证据、关闭证据和经验分流结果；AI 的临时步骤、局部选择、工具缓存、子 Agent 中间过程和未采纳草稿不得写成独立工作对象。

---
## 3. 状态机

### 3.1 标准状态

| 状态 | 含义 |
|---|---|
| `plan_reviewing` | 方案审核中：主控 AI 已起草出可审核方案，等待或正在由多视角子 Agent / 第三方审核 Agent 审核方案 |
| `plan_confirming` | 方案确认中：方案审核已形成结论，等待 Human 确认是否允许执行 |
| `executing` | 执行中：Human 已确认方案，主控 AI / 执行子 Agent 正在按方案执行 |
| `result_self_checking` | 结果自检中：主控 AI 已认为执行结果可以进入收口，正在自检成功标准、验证证据、关闭证据和残留风险 |
| `result_reviewing` | 结果审核中：主控自检已形成材料，等待或正在由多专业子 Agent / 第三方审核 Agent 复查结果与关闭材料 |
| `closure_confirming` | 关闭确认中：结果审核已形成结论，等待 Human 确认是否关闭、退回补审、继续执行或修改方案 |
| `closed` | 关闭判断已确认，工作计划终态稳定 |

`closed` 是稳定终态，只表示该工作计划不再继续推进，不等同于目标成功。关闭可以表示目标完成、被新工作计划承接、范围失效、终止、降级接受或其他经证据说明的关闭结果；关闭原因、完成程度、残留风险、未完成项分流和 Human Gate 结果必须写入 `closure_evidence` 或关联工作对象。

目标重新启动、扩大范围或改变成功标准时，应创建新的工作计划，并引用原工作计划。

主控起草方案不是 WorkPlan 状态。WorkPlan 的第一个权威状态是 `plan_reviewing`，表示方案已经可以被第三方审核。若方案尚不足以审核，应继续留在当前对话、Memo、Study 或其他前置事实源中，不得为了记录草稿而创建 WorkPlan。

### 3.2 合法状态流转

```text
plan_reviewing -> plan_confirming
plan_confirming -> executing
executing -> result_self_checking
result_self_checking -> result_reviewing
result_reviewing -> closure_confirming
closure_confirming -> closed

plan_confirming -> plan_reviewing
executing -> plan_reviewing
result_self_checking -> executing
result_reviewing -> result_self_checking
result_reviewing -> executing
closure_confirming -> result_reviewing
closure_confirming -> result_self_checking
closure_confirming -> executing
closure_confirming -> plan_reviewing
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `plan_reviewing` -> `plan_confirming` | 方案审核完成，审核结论允许提交 Human 确认 | `plan_review.review_items` 应记录审核 Agent、提示上下文、输入引用、结论和签署声明 |
| `plan_confirming` -> `executing` | Human 确认方案允许执行 | 应填写 `plan_confirmed_at`，并保留 Human 确认摘要 |
| `executing` -> `result_self_checking` | 主控认为执行结果已足以进入收口自检 | 执行项结果、阻塞、跳过或分流情况应已更新 |
| `result_self_checking` -> `result_reviewing` | 主控完成结果自检 | `result_review.controller_self_check` 应记录自检上下文、结论、证据和签署声明 |
| `result_reviewing` -> `closure_confirming` | 结果复核完成，复核结论允许提交 Human 关闭确认 | `result_review.review_items` 应记录复核 Agent、提示上下文、输入引用、结论和签署声明 |
| `closure_confirming` -> `closed` | Human 确认关闭 | 应填写 `closed_at`，并确认 `closure_evidence` 足以解释关闭结果 |
| `plan_confirming` -> `plan_reviewing` | Human 要求修改方案或补充审核 | 必须在 `revision_history` 记录原因、修改内容和需要重新审核的字段 |
| `executing` -> `plan_reviewing` | 执行中发现目标、范围、成功标准或执行编排需要修改 | 必须暂停执行，在 `revision_history` 记录原因和修改内容，修改后重新进入方案审核 |
| `result_self_checking` -> `executing` | 主控自检发现执行不足、证据不足或仍需补做 | 必须记录自检不通过原因和继续执行方向 |
| `result_reviewing` -> `result_self_checking` | 第三方复核要求主控补充自检材料或修正证据整理 | 必须记录复核意见和需补充的自检内容 |
| `result_reviewing` -> `executing` | 第三方复核认为结果不足，需要继续执行 | 必须记录复核意见和继续执行方向 |
| `closure_confirming` -> `result_reviewing` | Human 要求补充第三方复核 | 必须记录 Human 退回原因和需要复核的内容 |
| `closure_confirming` -> `result_self_checking` | Human 要求主控补充自检或整理证据 | 必须记录 Human 退回原因和需要补充的自检内容 |
| `closure_confirming` -> `executing` | Human 判断仍需继续执行既有方案 | 必须记录继续执行原因、范围和目标 |
| `closure_confirming` -> `plan_reviewing` | Human 要求修改目标、范围、成功标准或执行编排后重新执行 | 必须在 `revision_history` 记录修改原因、修改字段、修改摘要和重新审核要求；若改变已经大到形成新目标，应关闭当前 WorkPlan 并创建新 WorkPlan 承接 |

---
## 4. 对象关系

### 4.1 工作计划与工作域

每个工作计划必须通过 `workarea` 引用一个工作域。工作计划不得脱离工作域存在。

### 4.2 工作计划与执行项

工作计划通过 `orchestration.execution_items` 字段承载内部执行编排。执行项用于说明 AI 当前如何安排工作、验证和角色分工；执行项没有独立状态机、编号区段或事实源文件。

执行项不是“更小的工作对象”。它只承载 WorkPlan 内部执行委派、恢复和关闭判断所需的最小信息；执行者拿到执行项后可以使用自身的临时 checklist、计划模式、工具调用和局部推理继续拆分，但这些执行期拆分不进入 LDVH 长期事实源。

执行项至少应说明以下最小恢复信息：

1. `id`：工作计划内局部唯一标识；
2. `title`：一句话概括；
3. `role`：承担该执行项的角色、子 Agent 类型或专业视角；
4. `mode`：`sequential`、`parallel` 或 `single`；
5. `input_refs`：该执行项读取或依赖的事实源、文件、对象或上下文入口；
6. `expected_output`：该执行项应交还的结果类型、证据类型或判断；
7. `status`：当前内部执行态，由工作计划内部使用；
8. `result_summary`：已完成时的结果摘要；
9. `evidence_refs`：稳定产物、验证证据、命令、路径或回写目标；
10. `blocking_reason`：未完成或等待时的阻塞原因，可为空。

执行项内部状态只服务 WorkPlan 恢复、证据组织和关闭判断，允许值如下：

| 状态 | 含义 | 条件要求 |
|---|---|---|
| `pending` | 尚未开始 | 可存在于 `plan_reviewing`、`plan_confirming` 或 `executing`；进入 `result_self_checking` 前不得仍为该状态 |
| `in_progress` | 正在执行 | 仅用于 `executing`；进入 `result_self_checking` 前不得仍为该状态 |
| `blocked` | 当前执行项受阻 | 必须填写 `blocking_reason`；进入 `closure_confirming` 前应分流、解决或在 `closure_evidence` 中说明接受原因 |
| `done` | 执行项已完成 | 应填写 `result_summary`，并在有稳定证据时填写 `evidence_refs` |
| `skipped` | 明确决定不执行 | 必须填写 `result_summary`；`closure_evidence` 可补充整体接受原因 |

WorkPlan 的 Human-facing 阅读必须直接消费本文定义的权威状态，并先表达计划对象自身生命周期与关闭判断，再表达执行项队列。Code 或 Web 可以从 `status`、`success_criteria` checklist、`plan_review`、`result_review`、`verification_evidence`、`closure_evidence`、`closure_requested_at`、`closed_at` 和 `orchestration.execution_items` 派生只读摘要，用于展示推进阶段、成功标准完成度、执行项状态分布和关闭材料完备性。该摘要不得写回 YAML，也不得成为第二事实源；事实判断仍以本 WorkPlan 字段、关联工作对象和 Git 提交记录为准。

执行项不得被其他工作对象直接引用为长期事实。需要长期追踪的结论，应按性质分流到 WorkPlan、ADR、Memo、Pitfall、docs、正式规范或 Git 提交记录。

当某个执行项出现以下任一情况时，应停止把它作为内部执行项继续推进，并按事实性质分流；若它仍是可执行工作，应创建新的 WorkPlan：

1. 需要独立目标、独立范围或独立成功标准；
2. 需要独立 Human Gate、独立验收或独立关闭判断；
3. 需要跨会话长期治理或成为后续工作的事实源入口；
4. 产生独立 ADR、Memo、Pitfall 或 Git 提交追溯链路，且该链路已经超出当前 WorkPlan 的关闭判断；
5. 范围扩大到当前 WorkPlan 无法清晰关闭；
6. 继续作为执行项会迫使 Web、Code 或 Human 把它当成一级对象管理。

### 4.3 工作计划与 ADR、Memo、Pitfall 和 Git 提交记录

工作计划可以关联 ADR、Memo、Pitfall，并通过 Git 提交记录追溯事实源修改：

1. 长期决策进入 ADR；
2. 暂存信息、待观察输入或分流线索进入 Memo；
3. 已解决且可复用经验进入 Pitfall；
4. Git 文件事实源修改由 Git commit records 承载，并按 `specs/10-Git提交规范.md` 追溯。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名工作计划；
2. 将用户输入、Memo 或临时讨论升级为工作计划；
3. 将方案审核结果从 `plan_reviewing` 提交到 `plan_confirming`；
4. 确认 `plan_confirming` -> `executing`；
5. 将工作计划从 `closure_confirming` 关闭为 `closed`；
6. 改写目标、成功标准、执行编排、工作域归属或关闭判断；
7. 跳过未验证执行项或通过豁免关闭工作计划；
8. 合并、拆分或重新组织工作计划。

Human Gate 发生在工作计划层。执行项、角色说明、子 Agent 输出和工具结果不作为 Human 直接管理入口；它们必须回到工作计划证据或对应工作对象后才成为稳定事实。

---
## 6. 字段契约

公共字段语义定义见 `specs/05.01-工作模型字段定义与语义规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `workplan-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `workplan` | string | 是 | 固定为 `workplan` | Reference | AI、Code、Web |
| `title` | 工作计划一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建时间 | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | 更新时间 | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `workarea` | 所属工作域 ID | string | 是 | 必须引用已存在 WorkArea | Reference | AI、Code、Web |
| `priority` | 执行优先级 | string | 是 | `P0`、`P1`、`P2`、`P3`；判断标准见 `specs/05.01-工作模型字段定义与语义规范.md` §3.1 | Reference | AI、Code、Web |
| `description` | 目标背景、范围和问题说明 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `success_criteria` | 工作计划成功标准 | string | 是 | 应使用 checklist 或等价可验证条目支持关闭审查 | Checklist | AI、Code、Web |
| `source` | 工作计划来源 | string | 是 | 谁在什么场景下表达 | Reference / Narrative | AI、Web |
| `orchestration` | 执行编排对象 | object | 是 | 至少包含 `mode`、`execution_items`、`plan_review` 和 `result_review` | Structured | AI、Code、Web |
| `plan_confirmed_at` | Human 确认方案可执行的时间 | datetime | 条件必填 | `executing`、`result_self_checking`、`result_reviewing`、`closure_confirming` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `verification_evidence` | 验证证据，说明成功标准如何被检查 | string | 条件必填 | `result_reviewing`、`closure_confirming` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closure_evidence` | 关闭证据，说明为何可以关闭、残留风险和 Human Gate 结果 | string | 条件必填 | `result_reviewing`、`closure_confirming` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closure_requested_at` | 请求 Human 关闭确认时间 | datetime | 条件必填 | `closure_confirming` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `closed_at` | 关闭时间 | datetime | 条件必填 | `closed` 时必须填写 | Reference | AI、Code、Web |
| `revision_history` | 方案、执行或关闭确认退回后的修订记录 | list[object] | 否 | 默认为空列表；发生退回、方案修改、成功标准修改或执行编排修改时必须追加 | Structured / Log | AI、Code、Web |
| `related_docs` | 关联文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 来源或关联备忘 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联踩坑经验 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workplans` | 关联工作计划 | list[string] | 否 | 默认为空列表；承载 WorkPlan ID，不表示父子或阻塞关系 | Reference | AI、Code、Web |

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

`execution_items` 是工作计划内部字段，不得被提升为独立工作模型。并行执行项可以由不同子 Agent 或专业角色执行；子 Agent 不再继续创建子 Agent，所有结果回到主控汇总、自检和后续复检。

每个 `orchestration.execution_items` 对象的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 状态条件 |
|---|---|---|---|---|
| `id` | WorkPlan 内局部唯一标识 | string | 是 | 当前 WorkPlan 内不得重复；不得作为全局对象 ID |
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

`role` 只表达本执行项所需的专业视角、责任边界或子 Agent 类型，不在 WorkPlan 字段契约中提前定义完整角色规则。完整角色规则如需稳定化，应由工作流程、能力资产规范或后续专门规范承接；WorkPlan 只保留执行恢复所需的最小角色标识。

`plan_review` 和 `result_review` 不创建独立 Review 工作对象，但它们是 WorkPlan 内部权威审核事实。审核记录必须能回答：哪个 Agent 审核、以什么角色审核、当时获得的提示上下文和输入引用是什么、审核结论是什么、何时签署。没有真实密码学能力时，签署为可审计 attestation，不得伪装成密钥签名。

`orchestration.plan_review` 的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 条件 |
|---|---|---|---|---|
| `review_items` | 方案审核条目列表 | list[object] | 是 | `plan_reviewing` 时可以正在补齐；进入 `plan_confirming` 前必须全部完成 |
| `review_items[].id` | WorkPlan 内局部审核条目 ID | string | 是 | 当前 WorkPlan 内唯一 |
| `review_items[].role` | 审核角色或专业视角 | string | 是 | 例如 specs-reviewer、web-reviewer、governance-reviewer |
| `review_items[].agent_name` | 执行审核的子 Agent 名称或稳定标识 | string | 是 | 必须能让 Human 和后续 AI 识别是谁做的审核 |
| `review_items[].requested_at` | 审核请求时间 | datetime | 是 | ISO 8601 时间戳 |
| `review_items[].prompt_context.objective` | 给审核 Agent 的目标说明 | string | 是 | 应说明本次审核要判断什么 |
| `review_items[].prompt_context.input_refs` | 给审核 Agent 的输入引用 | list[string] | 是 | 应列出方案、规范、事实源、上下文入口或其他输入 |
| `review_items[].prompt_context.constraints` | 给审核 Agent 的约束 | list[string] | 否 | 可为空列表；用于记录只读、禁止修改、重点检查等约束 |
| `review_items[].context_digest` | 审核上下文摘要 | string | 否 | 可使用 hash 或说明性摘要；用于帮助追溯当时上下文，不替代输入引用 |
| `review_items[].result.status` | 审核结论 | string | 是 | 允许 `pass`、`pass_with_followups`、`fail`、`needs_human_gate` |
| `review_items[].result.summary` | 审核结论摘要 | string | 是 | 必须说明通过、条件通过或不通过的理由 |
| `review_items[].result.evidence_refs` | 审核证据引用 | list[string] | 否 | 可包含路径、命令、对象 ID、报告或说明性引用 |
| `review_items[].attested_at` | 审核签署时间 | datetime | 是 | 审核结论完成时填写 |
| `review_items[].attestation.signer` | 签署者 | string | 是 | 通常等于 `agent_name` |
| `review_items[].attestation.statement` | 签署声明 | string | 是 | 应声明基于上述 prompt context 和 input refs 完成审核并对结论负责 |
| `human_confirmation` | Human 方案确认记录 | object 或 null | 条件必填 | `executing` 及后续状态必须填写 |
| `human_confirmation.confirmed_at` | Human 确认方案时间 | datetime | 条件必填 | `executing` 及后续状态必须填写 |
| `human_confirmation.summary` | Human 确认摘要 | string | 条件必填 | 说明确认依据、是否有条件通过和执行边界 |

`orchestration.result_review` 的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 条件 |
|---|---|---|---|---|
| `controller_self_check` | 主控结果自检记录 | object 或 null | 条件必填 | `result_reviewing`、`closure_confirming` 或 `closed` 时必须填写 |
| `controller_self_check.controller` | 主控标识 | string | 是 | 填写主控 AI 或执行控制者标识 |
| `controller_self_check.checked_at` | 自检完成时间 | datetime | 是 | ISO 8601 时间戳 |
| `controller_self_check.prompt_context.objective` | 主控自检目标 | string | 是 | 应说明检查成功标准、验证证据、关闭证据和残留风险 |
| `controller_self_check.prompt_context.input_refs` | 主控自检输入引用 | list[string] | 是 | 应列出 WorkPlan、产物、验证命令、相关对象或上下文入口 |
| `controller_self_check.result.status` | 主控自检结论 | string | 是 | 允许 `pass`、`pass_with_followups`、`fail`、`needs_human_gate` |
| `controller_self_check.result.summary` | 主控自检摘要 | string | 是 | 必须说明是否可提交第三方复核及理由 |
| `controller_self_check.result.evidence_refs` | 主控自检证据引用 | list[string] | 否 | 可为空列表 |
| `controller_self_check.attested_at` | 主控自检签署时间 | datetime | 是 | 自检结论完成时填写 |
| `controller_self_check.attestation.signer` | 签署者 | string | 是 | 通常为主控标识 |
| `controller_self_check.attestation.statement` | 签署声明 | string | 是 | 应声明基于上述上下文完成自检并对结论负责 |
| `review_items` | 结果复核条目列表 | list[object] | 是 | `result_reviewing` 时可以正在补齐；进入 `closure_confirming` 前必须全部完成 |
| `review_items[]` | 结果复核条目结构 | object | 是 | 字段与 `plan_review.review_items[]` 相同，`phase` 语义为结果复核 |
| `human_closure_confirmation` | Human 关闭确认记录 | object 或 null | 条件必填 | `closed` 时必须填写 |
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
| `plan_reviewing` | 基础字段、`workarea`、`priority`、`description`、`success_criteria`、`source`、`orchestration.mode`、`orchestration.execution_items`、`orchestration.plan_review` 和 `orchestration.result_review` 已存在；`execution_items` 不得为空；`plan_review.review_items` 可以正在补齐 |
| `plan_confirming` | `plan_review.review_items` 已完成并具备 Agent、角色、提示上下文、输入引用、审核结论和签署声明；不存在必须先改方案的审核失败结论；等待 Human 确认 |
| `executing` | 满足 `plan_confirming` 条件；`plan_confirmed_at` 和 `plan_review.human_confirmation` 已填写；执行项可以处于 `pending`、`in_progress`、`blocked`、`done` 或 `skipped` |
| `result_self_checking` | 执行项不得仍为 `pending` 或 `in_progress`；`blocked` 执行项必须填写 `blocking_reason`；主控正在整理或填写 `result_review.controller_self_check`、`verification_evidence` 和 `closure_evidence` |
| `result_reviewing` | `result_review.controller_self_check` 已填写并签署；`verification_evidence` 和 `closure_evidence` 已填写；`result_review.review_items` 可以正在补齐 |
| `closure_confirming` | `result_review.review_items` 已完成并具备 Agent、角色、提示上下文、输入引用、复核结论和签署声明；`closure_requested_at` 已填写；等待 Human 关闭确认 |
| `closed` | 满足 `closure_confirming` 条件；`closed_at` 和 `result_review.human_closure_confirmation` 已填写；`closure_evidence` 足以说明关闭结果、残留风险、未完成项分流和 Human Gate 结果 |

### 6.3 YAML 示例

```yaml
id: workplan-0001
type: workplan
title: 重构工作模型状态边界
status: result_reviewing
created: '2026-06-18T00:00:00'
updated: '2026-06-18T03:30:00'
workarea: workarea-0001
priority: P1
description: |
  将一次模型重构目标组织为可执行、可验证、可关闭的工作计划。
success_criteria: |
  - [ ] 工作模型规范已更新
  - [ ] 事实实例路径已明确
  - [ ] Code 和 Web 缺口已记录
source: 用户确认创建工作计划
plan_confirmed_at: '2026-06-18T01:00:00'
verification_evidence: |
  - `python3 code/specs_validate.py all --fail-on-diagnostics` 已执行并通过。
closure_evidence: |
  成功标准已检查；剩余 Code 和 Web 缺口已记录为后续工作，不阻塞当前计划进入结果复核。
orchestration:
  mode: mixed
  execution_items:
    - id: item-1
      title: 更新模型规范
      role: specs-editor
      mode: sequential
      input_refs:
        - specs/05-工作模型基础规范.md
        - specs/21-WorkPlan-工作计划.md
      expected_output: 更新后的 WorkPlan 规范正文和可复查验证结果
      status: done
      result_summary: WorkPlan 规范已更新，执行项边界已收敛为内部恢复节点。
      evidence_refs:
        - specs/21-WorkPlan-工作计划.md
        - python3 code/specs_validate.py all --fail-on-diagnostics
      blocking_reason:
  plan_review:
    review_items:
      - id: plan-review-1
        role: specs-reviewer
        agent_name: codex-specs-review-agent
        requested_at: '2026-06-18T00:20:00'
        prompt_context:
          objective: 审核该 WorkPlan 的目标、范围、成功标准和执行编排是否可执行。
          input_refs:
            - workplan-0001
            - specs/21-WorkPlan-工作计划.md
          constraints:
            - 只审核方案，不修改事实源。
        context_digest: workplan-0001-plan-context
        result:
          status: pass
          summary: 方案边界清晰，可以提交 Human 确认。
          evidence_refs:
            - workplan-0001
        attested_at: '2026-06-18T00:40:00'
        attestation:
          signer: codex-specs-review-agent
          statement: 基于上述 prompt context 和 input refs 完成方案审核并对结论负责。
    human_confirmation:
      confirmed_at: '2026-06-18T01:00:00'
      summary: Human 确认按该方案执行。
  result_review:
    controller_self_check:
      controller: codex-main-controller
      checked_at: '2026-06-18T03:00:00'
      prompt_context:
        objective: 检查成功标准、验证证据、关闭证据和残留风险是否足以提交复核。
        input_refs:
          - workplan-0001
          - specs/21-WorkPlan-工作计划.md
          - python3 code/specs_validate.py all --fail-on-diagnostics
      result:
        status: pass_with_followups
        summary: 当前结果可以进入第三方复核，Code 和 Web 后续同步已作为残留工作记录。
        evidence_refs:
          - specs/21-WorkPlan-工作计划.md
      attested_at: '2026-06-18T03:05:00'
      attestation:
        signer: codex-main-controller
        statement: 基于上述上下文完成结果自检并对结论负责。
    review_items: []
    human_closure_confirmation:
revision_history: []
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_workplans: []
```

---
## 7. 事实源回写与证据留存

工作计划的目标、成功标准、执行编排、验证证据和关闭证据回写到工作计划 YAML。执行项结果只保留摘要、证据和稳定输出路径，不复制完整对话、工具日志或子 Agent 中间过程。

关闭工作计划前，至少应具备：

1. 成功标准检查结果；
2. 主控自检结论；
3. 必要时的专业角色复检结论；
4. 验证命令、文件路径、产物引用或人工确认记录；
5. 经验、决策、备忘或提交追溯的分流结果。

进入 `result_self_checking` 前，不要求所有执行项都必须成功，但必须让执行项状态足以说明：哪些完成、哪些跳过、哪些阻塞被分流或接受、哪些风险仍需 Human 判断。进入 `result_reviewing` 前，主控自检、验证证据和关闭证据必须足以支持第三方复核。`closed` 不代表目标必然成功，只代表该 WorkPlan 的推进责任已经依据证据和关闭判断稳定终止。

---
## 8. 适配边界

Code 应检查：

1. 工作计划必须引用存在的 WorkArea；
2. `priority` 必须属于 `P0`、`P1`、`P2`、`P3`；
3. 不得维护 `importance` 字段；
4. `orchestration.execution_items` 中的 `id` 在当前工作计划内唯一；
5. `orchestration.mode`、`orchestration.execution_items.mode` 和 `orchestration.execution_items.status` 必须属于本文定义的枚举；
6. `status` 必须属于本文 §3.1 定义的 WorkPlan 状态枚举，不得继续使用 `draft`、`active` 或 `review_needed`；
7. `plan_reviewing` 及后续状态必须存在 `orchestration.plan_review` 和 `orchestration.result_review`；
8. `plan_confirming` 及后续状态必须能追溯方案审核 Agent、提示上下文、输入引用、结论和签署声明；
9. `executing` 及后续状态必须填写 `plan_confirmed_at` 和 `plan_review.human_confirmation`；
10. `result_self_checking` 及后续状态不得存在 `pending` 或 `in_progress` 执行项；
11. `result_reviewing` 及后续状态必须填写主控自检、验证证据和关闭证据；
12. `closure_confirming` 和 `closed` 必须填写 `closure_requested_at`，并具备结果复核 Agent、提示上下文、输入引用、结论和签署声明；
13. `closed` 工作计划必须填写 `closed_at` 和 `result_review.human_closure_confirmation`；
14. `blocked` 执行项必须填写 `blocking_reason`；
15. `done` 或 `skipped` 执行项必须填写 `result_summary`；
16. 发生退回、目标修改、成功标准修改或执行编排修改时必须追加 `revision_history`，记录原因、修改字段和修改内容；
17. 执行项不得被其他工作对象作为独立对象引用；
18. `related_workplans` 必须承载 WorkPlan ID；
19. 工作计划相关提交由 Git 历史、对象 ID、文件路径和提交正文自然文本派生，不得手写维护 `related_changes`。

Web 应把工作计划作为 Human 直接查看和确认的主对象。Web 可以展示执行编排、验证证据和关闭证据，但不得把执行项提升为一级导航、独立对象详情页或可独立写入的权威事实。

---
## 9. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 工作计划必须遵守 05、05.01 和本文定义的人机职责边界 | 05、05.01、本文、Human Gate | 工作模型治理 | 创建、迁移、关闭或重排工作计划时 |
| 确定性执行要求 | 工作计划内部执行项不得作为独立工作模型出现 | Validator、CLI、Web 展示 | 事实模型校验 | 创建、更新、展示或关闭工作计划时 |
| 确定性执行要求 | 工作计划必须依据 `specs/05.01-工作模型字段定义与语义规范.md` §3.1 维护 `priority`，不得维护 `importance` | Validator、CLI、Web 展示 | 字段契约同步 | 创建、更新、排序、筛选或展示工作计划时 |
| 确定性执行要求 | 工作计划状态必须明确区分方案审核、方案确认、执行、结果自检、结果复核、关闭确认和已关闭，不得把审核阶段折叠为执行态派生含义 | Validator、CLI、Web 展示 | 状态机同步 | 状态枚举、流转、实例校验或 Web 展示变化时 |
| 子 Agent 思考要求 | 方案审核和结果复核必须记录审核 Agent、角色、提示上下文、输入引用、结论和可审计签署声明 | Agent 能力、主控多视角审查、事实实例校验 | 审核事实同步 | 方案审核、结果复核、Agent 能力或签署字段变化时 |
| Human 交互要求 | 方案执行和最终关闭必须经 Human 确认；退回、修改方案或接受残留风险必须记录原因和修改内容 | Human Gate、Web 展示、事实实例校验 | Gate 同步 | 方案确认、关闭确认、退回或修改关键字段时 |
| 生命周期触发要求 | 工作计划规范变化后应检查 Code、Web、事实实例和相关工作流程是否需要同步 | Code 测试、事实校验、Web 检查、流程检查 | 触发保障 | 字段、状态、执行编排或事实源路径变化时 |

---
## 10. 检查要求

| 检查项 | 标准 |
|---|---|
| 工作域归属 | 每个工作计划必须引用一个存在的工作域 |
| 优先级 | `priority` 已填写且符合 05.01 统一标准，未维护 `importance` |
| 执行编排 | `orchestration.execution_items` 是内部字段，不存在独立执行项事实源文件 |
| 人类入口 | 关闭审查发生在工作计划层 |
| 状态枚举 | `status` 属于本文 §3.1 状态枚举，且不使用旧的 `draft`、`active`、`review_needed` |
| 方案审核 | `plan_confirming` 及后续状态具备方案审核 Agent、提示上下文、输入引用、结论和签署声明 |
| 结果自检 | `result_reviewing` 及后续状态具备主控自检、验证证据和关闭证据 |
| 结果复核 | `closure_confirming` 及后续状态具备结果复核 Agent、提示上下文、输入引用、结论和签署声明 |
| 关闭证据 | `closure_confirming` / `closed` 具备验证证据、关闭证据和关闭确认请求时间 |
| 修订记录 | 退回、方案修改、成功标准修改或执行编排修改时，`revision_history` 记录原因、字段和修改内容 |
| 角色边界 | 执行项仅保留最小 `role` 标识；完整角色规则如需稳定化，由工作流程、能力资产规范或后续专门规范承接 |

---
## 11. 待补齐事项

1. WorkPlan 状态机、方案审核签署、结果自检、结果复核、Human 关闭确认和修订记录已经成为本文规则；后续 Code、Web、事实实例和相关工作流程应按本文同步落地；
2. 旧工作对象清退后的历史说明只应保留在 Git 历史、Memo、ADR 或明确标注的研究材料中，不得重新成为当前事实源兼容要求。
