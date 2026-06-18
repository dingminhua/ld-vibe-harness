# WorkPlan-工作计划

> 创建日期：2026-06-12
> 更新日期：2026-06-18
> 定位：定义 WorkPlan / 工作计划工作模型，包括对象定位、准入条件、事实源边界、状态机、执行编排、Human Gate、字段契约、事实源回写和适配规则
> 适用范围：所有接入 LDVH 且需要把一次目标组织为可执行、可验证、可关闭工作计划的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/05.01-工作字段内容格式规范.md`

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

WorkPlan / 工作计划是 Human 与 AI 围绕一次目标达成的工作事实契约。工作计划承载目标、范围、成功标准、所属工作域、执行编排、验证证据、关闭审查和经验分流。

Human 主要确认工作计划是否对齐目标和关闭判断；AI 负责在工作计划内部安排执行项、调度角色或专业视角、完成验证和整理证据。执行项只属于 WorkPlan 内部编排，不作为独立工作模型，不进入 20-39 集合，也不在 `ldvh-base/` 下形成独立事实实例。

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
| 工作计划字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| 工作计划展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

执行过程不作为长期事实源。工作计划只保留最小恢复信息、验证证据、关闭证据和经验分流结果；AI 的临时步骤、局部选择、工具缓存、子 Agent 中间过程和未采纳草稿不得写成独立工作对象。

---
## 3. 状态机

### 3.1 标准状态

| 状态 | 含义 |
|---|---|
| `draft` | 已记录，目标、范围、成功标准或执行编排尚未确认 |
| `active` | 已确认，可执行或正在执行 |
| `review_needed` | 验证证据和关闭证据已整理，待关闭审查 |
| `closed` | 关闭判断已确认，工作计划终态稳定 |

`closed` 是稳定终态，只表示该工作计划不再作为 active 计划推进，不等同于目标成功。关闭可以表示目标完成、被新工作计划承接、范围失效、终止、降级接受或其他经证据说明的关闭结果；关闭原因、完成程度、残留风险、未完成项分流和 Human Gate 结果必须写入 `closure_evidence` 或关联工作对象。

目标重新启动、扩大范围或改变成功标准时，应创建新的工作计划，并引用原工作计划。

`active` 状态的工作计划不得退回 `draft`。如果确认后发现目标、范围或成功标准需要大幅修改，应关闭当前工作计划并记录原因，或创建新工作计划承接。

### 3.2 合法状态流转

```text
draft -> active
active -> review_needed
review_needed -> closed
review_needed -> active
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `draft` -> `active` | 工作域、目标、成功标准和初始执行编排已确认 | Human 直接确认的主要入口 |
| `active` -> `review_needed` | 计划内应完成的执行项已完成，成功标准已检查，验证证据和关闭证据已整理 | 应填写 `review_requested_at`、`verification_evidence` 和 `closure_evidence` |
| `review_needed` -> `closed` | Human 完成关闭审查 | 应填写 `closed_at`，并确认 `closure_evidence` 足以解释关闭结果 |
| `review_needed` -> `active` | 审查不通过或需要继续执行 | 应在 `closure_evidence` 或执行编排中记录退回原因和继续执行方向 |

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
| `pending` | 尚未开始 | 可存在于 `draft` 或 `active`；进入 `review_needed` 前不得仍为该状态 |
| `in_progress` | 正在执行 | 仅用于 `active`；进入 `review_needed` 前不得仍为该状态 |
| `blocked` | 当前执行项受阻 | 必须填写 `blocking_reason`；进入 `review_needed` 前应分流、解决或在 `closure_evidence` 中说明接受原因 |
| `done` | 执行项已完成 | 应填写 `result_summary`，并在有稳定证据时填写 `evidence_refs` |
| `skipped` | 明确决定不执行 | 必须填写 `result_summary`；`closure_evidence` 可补充整体接受原因 |

执行项不得被其他工作对象直接引用为长期事实。需要长期追踪的结论，应按性质分流到 WorkPlan、ADR、Memo、Pitfall、Change、docs 或正式规范。

当某个执行项出现以下任一情况时，应停止把它作为内部执行项继续推进，并按事实性质分流；若它仍是可执行工作，应创建新的 WorkPlan：

1. 需要独立目标、独立范围或独立成功标准；
2. 需要独立 Human Gate、独立验收或独立关闭判断；
3. 需要跨会话长期治理或成为后续工作的事实源入口；
4. 产生独立 ADR、Memo、Pitfall 或 Change 链路，且该链路已经超出当前 WorkPlan 的关闭判断；
5. 范围扩大到当前 WorkPlan 无法清晰关闭；
6. 继续作为执行项会迫使 Web、Code 或 Human 把它当成一级对象管理。

### 4.3 工作计划与 ADR、Memo、Pitfall、Change

工作计划可以关联 ADR、Memo、Pitfall 和 Change：

1. 长期决策进入 ADR；
2. 暂存信息、待观察输入或分流线索进入 Memo；
3. 已解决且可复用经验进入 Pitfall；
4. Git 文件事实源修改由 Change 承载。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名工作计划；
2. 将用户输入、Memo 或临时讨论升级为工作计划；
3. 确认 `draft` -> `active`；
4. 将工作计划从 `active` 推进到 `review_needed`；
5. 将工作计划从 `review_needed` 关闭为 `closed`；
6. 改写目标、成功标准、执行编排、工作域归属或关闭判断；
7. 跳过未验证执行项或通过豁免关闭工作计划；
8. 合并、拆分或重新组织工作计划。

Human Gate 发生在工作计划层。执行项、角色说明、子 Agent 输出和工具结果不作为 Human 直接管理入口；它们必须回到工作计划证据或对应工作对象后才成为稳定事实。

---
## 6. 字段契约

公共字段语义定义见 `specs/05.01-工作字段内容格式规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `workplan-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `workplan` | string | 是 | 固定为 `workplan` | Reference | AI、Code、Web |
| `title` | 工作计划一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建时间 | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | 更新时间 | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `workarea` | 所属工作域 ID | string | 是 | 必须引用已存在 WorkArea | Reference | AI、Code、Web |
| `priority` | 执行优先级 | string | 是 | `P0`、`P1`、`P2`、`P3`；判断标准见 `specs/05-工作模型基础规范.md` §7.3.1 | Reference | AI、Code、Web |
| `description` | 目标背景、范围和问题说明 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `success_criteria` | 工作计划成功标准 | string | 是 | 应使用 checklist 或等价可验证条目支持关闭审查 | Checklist | AI、Code、Web |
| `source` | 工作计划来源 | string | 是 | 谁在什么场景下表达 | Reference / Narrative | AI、Web |
| `orchestration` | 执行编排对象 | object | 是 | 至少包含 `mode`、`execution_items` 和 `review` | Structured | AI、Code、Web |
| `verification_evidence` | 验证证据，说明成功标准如何被检查 | string | 条件必填 | `review_needed` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closure_evidence` | 关闭证据，说明为何可以关闭、残留风险和 Human Gate 结果 | string | 条件必填 | `review_needed` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `review_requested_at` | 请求关闭审查时间 | datetime | 条件必填 | `review_needed` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `closed_at` | 关闭时间 | datetime | 条件必填 | `closed` 时必须填写 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 来源或关联备忘 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联踩坑经验 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workplans` | 关联工作计划 | list[string] | 否 | 默认为空列表；承载 WorkPlan ID，不表示父子或阻塞关系 | Reference | AI、Code、Web |
| `related_changes` | 关联变更 | list[string] | 否 | 默认为空列表；承载 Git commit hash、短 hash 或可回指 Git commit 的引用 | Reference | AI、Code、Web |

### 6.1 orchestration 最小结构

`orchestration` 至少包含以下字段：

| 字段名 | 含义 | 类型 | 必填 |
|---|---|---|---|
| `mode` | 总体编排方式，允许 `single`、`sequential`、`parallel`、`mixed` | string | 是 |
| `execution_items` | 执行项列表 | list[object] | 是 |
| `review` | 主控自检、专业复检和关闭检查安排 | object | 是 |

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

`role` 只表达本执行项所需的专业视角、责任边界或子 Agent 类型，不在 WorkPlan 字段契约中提前定义完整角色规则。完整角色规则如需稳定化，应由工作流程、能力资产规范或后续专门规范承接；WorkPlan 只保留执行恢复所需的最小角色标识。

`review` 只声明关闭前的检查安排，不承载稳定审查结论，也不形成独立 Review 工作对象。审查结论必须回到 `verification_evidence`、`closure_evidence` 或对应工作对象。`review` 至少应说明以下内容：

1. `controller_self_check`：主控是否必须在申请关闭前自检；
2. `specialist_review`：是否需要专业角色或独立子 Agent 复检；需要时应说明角色或输入输出边界；
3. `human_closure_review`：是否需要 Human 关闭审查；工作计划从 `review_needed` 关闭为 `closed` 时默认需要。

`orchestration.review` 的字段契约如下：

| 字段路径 | 含义 | 类型 | 必填 | 条件 |
|---|---|---|---|---|
| `controller_self_check` | 主控是否必须自检 | boolean | 是 | 申请 `review_needed` 前必须完成自检并把结论写入证据字段 |
| `specialist_review` | 专业复检安排 | object | 是 | 只声明安排，不承载稳定结论 |
| `specialist_review.required` | 是否需要专业复检 | boolean | 是 | 为 `true` 时必须填写 `role` 和 `expected_output` |
| `specialist_review.role` | 复检角色或专业视角 | string 或 null | 条件必填 | `required=true` 时必填 |
| `specialist_review.expected_output` | 复检预期输出 | string 或 null | 条件必填 | `required=true` 时必填 |
| `human_closure_review` | 是否需要 Human 关闭审查 | boolean | 是 | `review_needed` -> `closed` 默认需要；若豁免必须写入 `closure_evidence` |

### 6.2 状态条件字段

| 状态 | 必须满足的对象条件 |
|---|---|
| `draft` | 基础字段存在；目标、成功标准或执行编排可尚未最终确认 |
| `active` | `workarea`、`priority`、`description`、`success_criteria`、`source`、`orchestration.mode`、`orchestration.execution_items`、`orchestration.review` 已确认；`execution_items` 不得为空 |
| `review_needed` | `verification_evidence`、`closure_evidence`、`review_requested_at` 已填写；成功标准已检查；执行项不得仍为 `pending` 或 `in_progress`；`blocked` 执行项必须在 `closure_evidence` 中说明分流、接受或豁免原因 |
| `closed` | 满足 `review_needed` 条件；`closed_at` 已填写；`closure_evidence` 足以说明关闭结果、残留风险、未完成项分流和 Human Gate 结果 |

### 6.3 YAML 示例

```yaml
id: workplan-0001
type: workplan
title: 重构工作模型状态边界
status: active
created: '2026-06-18T00:00:00'
updated: '2026-06-18T00:00:00'
workarea: workarea-0001
priority: P1
description: |
  将一次模型重构目标组织为可执行、可验证、可关闭的工作计划。
success_criteria: |
  - [ ] 工作模型规范已更新
  - [ ] 事实实例路径已明确
  - [ ] Code 和 Web 缺口已记录
source: 用户确认创建工作计划
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
  review:
    controller_self_check: true
    specialist_review:
      required: true
      role: specs-reviewer
      expected_output: 独立复检结论和需要回写的风险提示
    human_closure_review: true
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_workplans: []
related_changes: []
```

---
## 7. 事实源回写与证据留存

工作计划的目标、成功标准、执行编排、验证证据和关闭证据回写到工作计划 YAML。执行项结果只保留摘要、证据和稳定输出路径，不复制完整对话、工具日志或子 Agent 中间过程。

关闭工作计划前，至少应具备：

1. 成功标准检查结果；
2. 主控自检结论；
3. 必要时的专业角色复检结论；
4. 验证命令、文件路径、产物引用或人工确认记录；
5. 经验、决策、备忘或变更的分流结果。

进入 `review_needed` 前，不要求所有执行项都必须成功，但必须让执行项状态、验证证据和关闭证据共同说明：哪些完成、哪些跳过、哪些阻塞被分流或接受、哪些风险仍需 Human 判断。`closed` 不代表目标必然成功，只代表该 WorkPlan 的推进责任已经依据证据和关闭判断稳定终止。

---
## 8. 适配边界

Code 应检查：

1. 工作计划必须引用存在的 WorkArea；
2. `priority` 必须属于 `P0`、`P1`、`P2`、`P3`；
3. 不得维护 `importance` 字段；
4. `orchestration.execution_items` 中的 `id` 在当前工作计划内唯一；
5. `orchestration.mode`、`orchestration.execution_items.mode` 和 `orchestration.execution_items.status` 必须属于本文定义的枚举；
6. `review_needed` 和 `closed` 必须提供验证证据、关闭证据和 `review_requested_at`；
7. `closed` 工作计划必须填写 `closed_at`；
8. `blocked` 执行项必须填写 `blocking_reason`；
9. `done` 或 `skipped` 执行项必须填写 `result_summary`；
10. 执行项不得被其他工作对象作为独立对象引用；
11. `related_workplans` 必须承载 WorkPlan ID；
12. `related_changes` 必须承载 Git commit hash、短 hash 或可回指 Git commit 的引用。

Web 应把工作计划作为 Human 直接查看和确认的主对象。Web 可以展示执行编排、验证证据和关闭证据，但不得把执行项提升为一级导航、独立对象详情页或可独立写入的权威事实。

---
## 9. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 工作计划必须遵守 05、05.01 和本文定义的人机职责边界 | 05、05.01、本文、Human Gate | 工作模型治理 | 创建、迁移、关闭或重排工作计划时 |
| 确定性执行要求 | 工作计划内部执行项不得作为独立工作模型出现 | Validator、CLI、Web 展示 | 事实模型校验 | 创建、更新、展示或关闭工作计划时 |
| 确定性执行要求 | 工作计划必须依据 05 的统一标准维护 `priority`，不得维护 `importance` | Validator、CLI、Web 展示 | 字段契约同步 | 创建、更新、排序、筛选或展示工作计划时 |
| 生命周期触发要求 | 工作计划规范变化后应检查 Code、Web、事实实例和相关工作流程是否需要同步 | Code 测试、事实校验、Web 检查、流程检查 | 触发保障 | 字段、状态、执行编排或事实源路径变化时 |

---
## 10. 检查要求

| 检查项 | 标准 |
|---|---|
| 工作域归属 | 每个工作计划必须引用一个存在的工作域 |
| 优先级 | `priority` 已填写且符合 05 统一标准，未维护 `importance` |
| 执行编排 | `orchestration.execution_items` 是内部字段，不存在独立执行项事实源文件 |
| 人类入口 | 关闭审查发生在工作计划层 |
| 关闭证据 | review_needed / closed 具备验证证据和关闭证据 |
| 角色边界 | 执行项仅保留最小 `role` 标识；完整角色规则如需稳定化，由工作流程、能力资产规范或后续专门规范承接 |

---
## 11. 待补齐事项

1. Code 和 Web 中仍以 `TaskFlow` 命名的执行项展示辅助组件，应在后续 UI 命名治理中评估是否重命名为 execution item flow；
2. WorkPlan 完成后独立专业复核、Human 关闭审查和经验分流规则，需要在后续工作流程规范中沉淀为标准流程；
3. 旧工作对象清退后的历史说明只应保留在 Git 历史、Memo、ADR 或明确标注的研究材料中，不得重新成为当前事实源兼容要求。
