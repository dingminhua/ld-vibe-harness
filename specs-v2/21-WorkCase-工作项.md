# WorkCase-工作项

```yaml
v2_spec:
  spec_id: "21"
  spec_kind: "member_spec"
  title: "WorkCase-工作项"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/21-WorkCase-工作项.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: "specs-v2/02-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 WorkCase / 工作项事实模型的对象定位、准入条件、事实源边界、方案审核、执行、结果自检、结果复核、关闭确认、字段契约、实例写入与消费边界"
  scope: "所有接入 LDVH 且需要把一次目标组织为可执行、可验证、可关闭工作项的项目"
  basis:
    - "specs-v2/00-LDVH理念与价值标准.md"
    - "specs-v2/01-规范体系基础规范.md"
    - "specs-v2/02-事实模型基础规范.md"
  related_specs:
    - "specs-v2/attachments/02.Att.01-字段注册表.md"
    - "specs-v2/attachments/02.Att.02-成员身份字段表.md"
    - "specs-v2/attachments/02.Att.03-成员主文件骨架模板.md"
    - "specs-v2/attachments/02.Att.04-成员一致性辅助核对表.md"
    - "specs-v2/attachments/02.Att.05-成员双读映射矩阵.md"
    - "specs-v2/attachments/02.Att.06-字段矩阵诊断表.md"
    - "specs-v2/07-事实源边界与Git追溯规范.md"
    - "specs-v2/attachments/21.Att.01-orchestration字段契约表.md"
    - "specs/20-Spark-火花.md"
    - "specs/22-ADR-决策.md"
    - "specs/23-Pitfall-踩坑经验.md"
  migration_sources:
    - "specs/21-WorkCase-工作项.md"
  active_fact_source:
    - "specs/21-WorkCase-工作项.md"
  code_consumption:
    - "v2_spec_metadata"
    - "fact_model_member_identity"
    - "fact_model_fields"
    - "fact_model_state_machine"
    - "fact_model_instance_checks"
  migration_status: "migrated"
```

```yaml
v2_fact_model_member:
  spec_id: "21"
  kind: "fact_model"
  name_en: "WorkCase"
  name_zh: "工作项"
  collection_status: "active"
  canonical_path: "specs-v2/21-WorkCase-工作项.md"
  instance_root: "ldvh-base/workcases/"
  instance_carrier: "yaml"
  fact_source_anchor: "§5"
  schema_anchor: "§9"
  state_machine_anchor: "§6"
  human_gate_anchor: "§8"
  code_consumption:
    - "fields"
    - "state_machine"
    - "execution_items"
    - "instance_checks"
```

> 文件状态：本文当前位于 `specs-v2/`，尚未切换为 active；正式 WorkCase 事实模型仍以 `specs/21-WorkCase-工作项.md` 为准。
>
> 本文只作为 21-WorkCase 的 v2 成员草案和单篇核对输入。未经 Human 单篇确认前，本文不得作为 active 规范、Code 默认消费依据、Rules 入口依据或迁移完成结论。

## 1. 本文解决的问题

本文定义 WorkCase / 工作项如何把一次目标组织为可执行、可验证、可复核、可关闭的工作事实契约。

本文解决：

1. 什么目标应进入 WorkCase，什么目标应留在当前对话、Spark、Study 或其它事实源；
2. WorkCase 实例事实源、文件命名和 active 事实源边界；
3. WorkCase 从方案审核到 Human 方案确认、执行、结果自检、结果复核、Human 关闭确认和关闭的状态机；
4. `orchestration.execution_items`、`plan_review`、`result_review` 和 `revision_history` 如何作为 WorkCase 内部字段承载执行恢复和审核事实；
5. WorkCase 与 Spark、ADR、Pitfall 和 Git commit records 的关系；
6. WorkCase 字段契约、状态条件、证据留存、实例检查和 Web / Code 消费边界。

本文不定义子 Agent、角色系统、行动编排流程、Code 输出 Schema、Web 页面布局或 Git commit message 契约。执行项不是独立事实模型，不进入 20-29 成员集合，也不在 `ldvh-base/` 下形成独立事实实例。

## 2. 上位依据

本文承接 `00-LDVH理念与价值标准.md`：WorkCase 用于把 AI 与 Human 的目标、范围、成功标准、执行路径、验证证据和关闭判断结构化，减少目标漂移、上下文丢失和无证据完成。

本文承接 `01-规范体系基础规范.md`：本文作为事实模型成员规范，必须声明 `v2_spec`、`v2_fact_model_member`、上位依据、价值判断、规范保障要求、Human Gate 和待补齐事项；v2 未切换 active 前，本文不得替代 active v1 规则。

本文承接 `02-事实模型基础规范.md`：WorkCase 必须在成员主文件中定义完整对象规则，字段注册表不得反向定义 WorkCase 采用字段、必填性、状态条件或对象内完整 schema。

若本文草案与 active `specs/21-WorkCase-工作项.md`、v2 00、v2 01 或 v2 02 冲突，在 Human 单篇确认前不得自行覆盖，应记录为待核对事项。

## 3. 构成要素归属与价值判断

### 3.1 构成要素归属

本文属于六类构成要素中的 `事实模型`。

| 项目 | 判断 |
|---|---|
| 主归属 | 事实模型 |
| 辅助服务对象 | 行动编排、Code、Web 和运行时扩展可消费 WorkCase 状态机、执行项、审核记录、证据字段和关闭判断 |
| 不归属边界 | 不定义行动编排 Context / Scenario / Gate 流程；不定义子 Agent 实现、Code 输出 Schema、Web 页面契约或 Git 提交格式 |

### 3.2 正向价值判断

| 价值标准 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过 `ldvh-base/workcases/`、成员身份和状态机定位目标当前阶段 |
| V2 可行动理解 | 通过 `goal`、`description`、`success_criteria`、执行项和审核记录让 AI 恢复目标、范围和下一步 |
| V3 正确判断 | 通过准入条件、状态条件、Human Gate 和完成口径分层，降低误判完成或误跳阶段风险 |
| V4 稳定执行 | 通过执行项、方案审核、执行、自检、复核和关闭确认形成稳定推进路径 |
| V5 门禁识别 | 通过方案确认、关闭确认和关键改写场景触发 Human Gate |
| V6 强制验证 | 通过 `verification_evidence`、`closure_evidence`、主控自检和结果复核提供验证入口 |
| V7 证据沉淀 | 通过审核条目、签署声明、修订记录、证据引用和 Git 追溯保留证据 |
| V8 可靠回写 | 通过 YAML 实例回写目标、执行状态、验证证据和关闭判断 |
| V10 持续完善 | 通过 Spark、ADR、Pitfall、后续 WorkCase 和残留风险分流沉淀缺口 |

### 3.3 逆向价值判断

| 反向风险 | 本文如何避免 |
|---|---|
| 把执行项升级为事实模型 | 执行项只作为 WorkCase 内部字段，不形成独立事实源、编号段或一级 Web 入口 |
| 把主控自检冒充独立复核 | 结果复核必须记录独立复核主体、输入引用、结论、证据和主控处理记录 |
| 把等待关闭确认写成已关闭 | `human_closure_confirming` 必须明确是等待 Human 关闭确认，不得表述为 `closed` 或已提交 |
| 只在对话中推进而不回写事实源 | 状态、执行项、成功标准、证据和复核材料必须随阶段推进及时回写 |
| 用 WorkCase 替代 ADR、Spark 或 Pitfall | 长期决策进入 ADR，暂存线索进入 Spark，复用经验进入 Pitfall |

## 4. 对象定位与准入条件

WorkCase / 工作项是 Human 与 AI 围绕一次目标达成的工作事实契约。工作项承载已经由主控 AI 起草到可审核程度的目标、范围、成功标准、执行编排、方案审核、执行过程、结果自检、结果复核、关闭确认和经验分流。

主控 AI 在 WorkCase 创建前可以起草方案草稿；该起草动作不是 WorkCase 状态。只有当草稿已经足以被第三方子 Agent 审核时，才创建 WorkCase 并进入方案审核。Human 主要确认方案是否允许执行和结果是否允许关闭；AI 负责安排执行项、调度角色或专业视角、完成验证、整理证据并接受独立复核。

WorkCase 创建前必须先在对话中完成人和 AI 的需求对齐。Human 决定需要创建 WorkCase 后，主控 AI 应立即创建 WorkCase，并连续完成方案审核编排、子 Agent / 第三方审核 Agent 方案审核和主控处理记录；该创建后审核链路是固定动作，不再插入额外 Human 确认。方案审核完成后才进入 `human_plan_confirming`，由 Human 在执行前确认目标、范围、成功标准、执行颗粒度和约束。

### 4.1 WorkCase 准入条件

一个目标满足以下条件之一时，应形成 WorkCase：

1. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
2. 需要表达目标、范围、成功标准、验证证据或关闭判断；
3. 需要多个执行项、并行安排、顺序安排或角色分工；
4. 需要 Human 明确确认目标、范围、成功标准或关闭判断；
5. 需要留下最小恢复信息、验证证据、关闭证据或结果物引用；
6. 不结构化会导致目标、范围、执行编排或完成判断漂移。

当前对话即可完成、无需留存记录、无需流程治理的小工作，不创建 WorkCase。

## 5. 事实源边界

WorkCase 实例的权威事实源位置为：

```text
ldvh-base/workcases/workcase-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| WorkCase active 事实模型规范 | `specs/21-WorkCase-工作项.md` |
| WorkCase v2 成员草案 | `specs-v2/21-WorkCase-工作项.md` |
| WorkCase 实例 | `ldvh-base/workcases/` |
| WorkCase 字段内容格式和公共字段语义 | v2 未 active 前以 active 05 系列和 WorkCase active 成员主文件为准；v2 草案对照 `specs-v2/02-事实模型基础规范.md` 和 `02.Att.01` |
| WorkCase 展示、聚合或查询结果 | Web、Code 或知识地图派生输出，不作为最终事实源 |

执行过程不作为长期事实源。WorkCase 只保留最小恢复信息、验证证据、关闭证据和经验分流结果；AI 的临时步骤、局部选择、工具缓存、子 Agent 中间过程和未采纳草稿不得写成独立工作对象。

提交追溯、过程输出回写和非事实源排除以 `07-事实源边界与Git追溯规范.md` 为准。审核原文、子 Agent 输出、工具输出、对话播报和 Web 派生态势只有写入 WorkCase 字段、稳定外部引用或对应事实源后才形成可追溯事实；Git 提交记录用于追溯事实源修改，不得手写维护为 WorkCase 字段清单。

## 6. 状态机

### 6.1 标准状态

| 状态 | 含义 |
|---|---|
| `subagents_plan_reviewing` | 子 Agent 方案审核中：主控 AI 已起草出可审核方案，等待或正在由多个子 Agent / 第三方审核 Agent 按审核策略审核方案 |
| `human_plan_confirming` | Human 方案确认中：方案审核和主控处理记录已形成，等待 Human 确认是否允许执行 |
| `executing` | 执行中：Human 已确认方案，主控 AI / 执行子 Agent 正在按方案执行 |
| `result_self_checking` | 结果自检中：主控 AI 已认为执行结果可以进入收口，正在自检成功标准、验证证据、关闭证据和残留风险 |
| `subagents_result_reviewing` | 子 Agent 结果复核中：主控自检已形成材料，等待或正在由多个子 Agent / 第三方审核 Agent 复查结果与关闭材料 |
| `human_closure_confirming` | Human 关闭确认中：结果复核和主控处理记录已形成，等待 Human 确认是否关闭、退回补审、继续执行或修改方案 |
| `closed` | 关闭判断已确认，工作项终态稳定 |

`closed` 是稳定终态，只表示该工作项不再继续推进，不等同于目标成功。关闭可以表示目标完成、被新工作项承接、范围失效、终止、降级接受或其他经证据说明的关闭结果。

主控起草方案不是 WorkCase 状态。WorkCase 的第一个权威状态是 `subagents_plan_reviewing`；若方案尚不足以审核，应继续留在当前对话、Spark、Study 或其他前置事实源中。

### 6.2 合法状态流转

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

关键流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `subagents_plan_reviewing` -> `human_plan_confirming` | 方案审核完成，主控已处理审核意见，允许提交 Human 确认 | `plan_review.review_items` 和 `plan_review.controller_resolution` 必须完整 |
| `human_plan_confirming` -> `executing` | Human 确认方案允许执行 | 应填写 `plan_confirmed_at` 和 `plan_review.human_confirmation`；行动前未确认事项不得带入执行 |
| `executing` -> `result_self_checking` | 主控认为执行结果已足以进入收口自检 | 执行项结果、阻塞、跳过或分流情况应已更新 |
| `result_self_checking` -> `subagents_result_reviewing` | 主控完成结果自检 | `result_review.controller_self_check` 必须记录自检上下文、结论、证据和签署声明 |
| `subagents_result_reviewing` -> `human_closure_confirming` | 结果复核完成，主控已处理复核意见，允许提交 Human 关闭确认 | `result_review.review_items` 和 `result_review.controller_resolution` 必须完整 |
| `human_closure_confirming` -> `closed` | Human 确认关闭 | 应填写 `closed_at`、`closure_outcome` 和 `result_review.human_closure_confirmation` |
| 退回到 `subagents_plan_reviewing` | Human 要求修改方案，或执行中发现目标、范围、成功标准或执行编排需要修改且超出已确认范围 | 必须追加 `revision_history` 并重新审核 |
| 退回到 `executing` / `result_self_checking` / `subagents_result_reviewing` | 自检、复核或 Human 关闭确认发现执行、证据、复核不足 | 必须记录退回原因、继续范围和需补齐内容 |

未列出的状态流转为非法流转。Code、Web 和行动编排不得把 `human_closure_confirming` 派生为 `closed`。

## 7. 对象关系

### 7.1 WorkCase 与执行项

WorkCase 通过 `orchestration.execution_items` 字段承载内部执行编排。执行项不是更小的工作对象，不得被其他工作对象直接引用为长期事实。需要长期追踪的结论，应按性质分流到 WorkCase、ADR、Spark、Pitfall、docs、正式规范或 Git commit records。

执行项至少应说明 `id`、`title`、`role`、`mode`、`input_refs`、`expected_output`、`status`、`result_summary`、`evidence_refs` 和 `blocking_reason`。执行项内部状态允许值为 `pending`、`in_progress`、`blocked`、`done`、`skipped`；`blocked` 必须填写 `blocking_reason`，`done` 或 `skipped` 必须填写 `result_summary`。

执行开始后，主控不得因普通执行问题再次要求行动前确认。新发现的问题应先按已确认范围处理，并记录到执行项、自检、残留风险、关闭证据或后续分流。只有越出已确认目标/范围、改变成功标准、引入破坏性副作用或触发安全/事实源边界时，才允许退回方案审核或请求新的 Human Gate。

### 7.2 Human 感知与状态同步

主控推进 WorkCase 时必须让 Human 能稳定回答：当前处于哪个状态、已经完成哪些执行项、下一 Gate 是什么、还需要 Human 确认什么，以及 Web 能否看到同一状态。

对话口径必须满足：

1. 跨状态推进、完成一组关键执行项、进入验证/复核/关闭前，主控必须简短说明当前状态、已完成执行项、剩余阻塞、下一 Gate 和需要 Human 确认的事项；
2. 审核建议、主控推断和 Human 已确认事实必须分开表达；
3. 如果主控已经完成实质执行但尚未回写 WorkCase，必须明示执行已发生但事实源尚未回写；
4. 对话中的进度播报不得替代 WorkCase 字段回写；
5. `human_closure_confirming` 只能表述为等待 Human 关闭确认或可提交关闭确认，不得表述为已关闭或已提交。

Web 感知必须满足：

1. Web 只能展示 WorkCase 事实源和确定性派生摘要；
2. 进入 `executing` 后，如果已经开始或完成任何实质执行，必须在同一工作轮次内回写对应执行项；
3. 进入 `result_self_checking` 前，执行项状态必须足以让 Web 展示真实分布；
4. 成功标准、验证证据、关闭证据和结果复核材料应随阶段推进及时回写。

### 7.3 主控自检、结果复核与完成口径

主控结果自检不是形式签名。进入 `subagents_result_reviewing` 前，`result_review.controller_self_check` 必须记录实际检查范围、发现、修复、证据和为什么可以提交独立结果复核。

结果复核是关闭前的独立判断流程。每个必需视角都应有可追溯复核主体、提示上下文、输入引用、结论、证据引用和签署声明。复核 Agent 提出的范围内硬问题必须在进入 `human_closure_confirming` 前修复、退回执行、退回自检，或记录为需要 Human 裁决的争议。

WorkCase 的完成口径必须区分四层：

1. 执行完成：执行项、成功标准和验证证据已回写，但仍需主控自检或结果复核；
2. 可提交关闭确认：状态为 `human_closure_confirming`，结果复核和主控处理完成，但 Human 尚未确认关闭；
3. 已关闭：状态为 `closed`，且 `human_closure_confirmation`、`closed_at` 和 `closure_outcome` 已填写；
4. 已提交：相关事实源修改已经进入符合 Git 提交规范的 Git commit records。

### 7.4 WorkCase 与 ADR、Spark、Pitfall 和 Git 提交记录

WorkCase 可以关联 ADR、Spark、Pitfall，并通过 Git commit records 追溯事实源修改：

1. 长期决策进入 ADR；
2. 暂存信息、待观察输入或分流线索进入 Spark；
3. 已解决且可复用经验进入 Pitfall；
4. Git 文件事实源修改由 Git commit records 承载。

## 8. Human Gate

以下情况应评估 Human Gate：

1. 将用户输入、Spark 或临时讨论升级为 WorkCase 前，Human 必须明确决定创建 WorkCase；
2. 删除或重命名 WorkCase；
3. 确认 `human_plan_confirming` -> `executing`，即在执行前确认目标、范围、成功标准、执行颗粒度和约束；
4. 将 WorkCase 从 `human_closure_confirming` 关闭为 `closed`；
5. 改写目标、成功标准、执行编排或关闭判断；
6. 跳过未验证执行项或通过豁免关闭 WorkCase；
7. 合并、拆分或重新组织 WorkCase。

Human 决定创建 WorkCase 后，创建事实源、进入 `subagents_plan_reviewing`、协调方案审核子 Agent、记录审核结果和形成 `controller_resolution` 是连续的 AI 内部动作，不应再次请求 Human 介入。只有方案审核完成且需要进入执行前确认时，才进入 `human_plan_confirming` 等待 Human 对齐颗粒度。

Human Gate 发生在 WorkCase 层。执行项、角色说明、子 Agent 输出和工具结果不作为 Human 直接管理入口；它们必须回到 WorkCase 证据或对应事实对象后才成为稳定事实。

## 9. 字段契约

### 9.1 顶层字段契约

| 字段名或路径 | 字段来源 | 字段含义 | 值形态 | 是否必填 | 状态条件 | 内容格式 | schema 归口 | 消费方 |
|---|---|---|---|---|---|---|---|---|
| `id` | 模型身份基线字段 | WorkCase 实例唯一标识，格式为 `workcase-{NNNN}` | string | 必填 | 与文件编号一致 | reference | 21 | AI、Code、Web、知识地图 |
| `type` | 模型身份基线字段 | 固定为 `workcase` | string | 必填 | 所有状态必须为 `workcase` | reference | 21 | AI、Code、Web |
| `title` | 模型身份基线字段 | 工作项一句话概括 | string | 必填 | 应简短可读 | narrative | 21 | AI、Web |
| `goal` | WorkCase 模型特有字段 | 本工作项要达成的目标 | markdown | 必填 | 应独立表达目标，不依赖 `description` 推断 | narrative | 21 | AI、Code、Web |
| `status` | 模型身份基线字段 | 当前 WorkCase 状态 | string | 必填 | 必须属于 §6.1 状态枚举 | reference | 21 | AI、Code、Web、知识地图 |
| `created` | 模型身份基线字段 | 创建时间 | datetime | 必填 | ISO 8601 时间戳 | reference | 02、21 | AI、Code、Web |
| `updated` | 模型身份基线字段 | 最近更新时间 | datetime | 必填 | 每次事实源更新时同步 | reference | 02、21 | AI、Code、Web |
| `priority` | 公共字段，WorkCase 采用 | 执行优先级 | string | 必填 | `P0`、`P1`、`P2`、`P3`；不得使用 `importance` | reference | 02、21 | AI、Code、Web |
| `description` | 公共字段，WorkCase 采用 | 目标背景、范围和问题说明 | markdown | 必填 | 使用 YAML 块标量 | narrative | 21 | AI、Web |
| `success_criteria` | 公共字段，WorkCase 采用 | 工作项成功标准 | checklist_markdown | 必填 | 应使用 checklist 或等价可验证条目支持关闭审查 | checklist | 21 | AI、Code、Web |
| `source` | 公共字段，WorkCase 采用 | 工作项来源 | markdown | 必填 | 说明谁在什么场景下表达 | reference / narrative | 21 | AI、Web |
| `orchestration` | WorkCase 模型特有字段 | 执行编排、方案审核和结果复核对象 | object | 必填 | 至少包含 `mode`、`execution_items`、`plan_review` 和 `result_review` | structured | 21 | AI、Code、Web |
| `plan_confirmed_at` | WorkCase 模型特有字段 | Human 确认方案可执行的时间 | datetime | 条件必填 | `executing` 及后续状态必须填写 | reference | 21 | AI、Code、Web |
| `verification_evidence` | 公共字段，WorkCase 采用 | 成功标准如何被检查 | evidence_markdown | 条件必填 | `subagents_result_reviewing`、`human_closure_confirming` 或 `closed` 时必须填写 | evidence | 21 | AI、Code、Web |
| `closure_evidence` | 公共字段，WorkCase 采用 | 为什么可以关闭、关闭结果、残留风险和 Human Gate 结果 | evidence_markdown | 条件必填 | `subagents_result_reviewing`、`human_closure_confirming` 或 `closed` 时必须填写 | evidence | 21 | AI、Code、Web |
| `closure_requested_at` | WorkCase 模型特有字段 | 请求 Human 关闭确认时间 | datetime | 条件必填 | `human_closure_confirming` 或 `closed` 时必须填写 | reference | 21 | AI、Code、Web |
| `closed_at` | 公共字段，WorkCase 采用 | 关闭时间 | datetime | 条件必填 | `closed` 时必须填写 | reference | 02、21 | AI、Code、Web |
| `closure_outcome` | WorkCase 模型特有字段 | 关闭结果分类 | string | 条件必填 | `closed` 时必须为 `completed`、`partial_completed`、`cancelled`、`superseded`、`invalid` 或 `degraded_accepted` | reference | 21 | AI、Code、Web |
| `residual_risks` | WorkCase 模型特有字段 | 残留风险摘要列表 | list_string | 可选 | 默认为空列表；关闭时如接受风险或未完成项必须填写 | evidence / log | 21 | AI、Web |
| `followup_refs` | WorkCase 模型特有字段 | 后续承接引用 | list_string | 可选 | 默认为空列表；可引用后续 WorkCase、Spark、ADR、Pitfall 或文档路径 | reference | 21 | AI、Code、Web |
| `revision_history` | WorkCase 模型特有字段 | 方案、执行或关闭确认退回后的修订记录 | list_object | 可选 | 发生退回、方案修改、成功标准修改或执行编排修改时必须追加 | structured / log | 21 | AI、Code、Web |
| `related_docs` | 公共字段，WorkCase 采用 | 关联文档路径 | list_string | 可选 | 默认为空列表 | reference | 21 | AI、Code、Web |
| `related_adrs` | 公共字段，WorkCase 采用 | 关联 ADR | list_string | 可选 | 默认为空列表 | reference | 21 | AI、Code、Web |
| `related_sparks` | 公共字段，WorkCase 采用 | 来源或关联 Spark | list_string | 可选 | 默认为空列表 | reference | 21 | AI、Code、Web |
| `related_pitfalls` | 公共字段，WorkCase 采用 | 关联 Pitfall | list_string | 可选 | 默认为空列表 | reference | 21 | AI、Code、Web |
| `related_workcases` | 公共字段，WorkCase 采用 | 关联 WorkCase | list_string | 可选 | 默认为空列表；不表示父子或阻塞关系 | reference | 21 | AI、Code、Web |

### 9.2 `orchestration` 字段契约

`orchestration` 至少包含以下字段：

| 字段名或路径 | 字段含义 | 值形态 | 是否必填 | 状态条件 |
|---|---|---|---|---|
| `orchestration.mode` | 总体编排方式 | string | 必填 | 允许 `single`、`sequential`、`parallel`、`mixed` |
| `orchestration.execution_items` | 执行项列表 | list_object | 必填 | 不得为空；执行项不形成独立对象 |
| `orchestration.plan_review` | 方案审核记录 | object | 必填 | `subagents_plan_reviewing` 及后续状态必须存在 |
| `orchestration.result_review` | 结果自检和结果复核记录 | object | 必填 | `result_self_checking` 及后续状态逐步补齐 |

`orchestration` 的详细字段契约由 `attachments/21.Att.01-orchestration字段契约表.md` 承载。该附件只展开 `plan_review`、`result_review`、`controller_resolution`、`review_items`、`human_confirmation`、`human_closure_confirmation`、`controller_self_check` 和 `revision_history` 的字段表、枚举和条件，不得改变本文定义的状态机、Human Gate 或关闭口径。

每个 `execution_items[]` 至少包含：`id`、`title`、`role`、`mode`、`input_refs`、`expected_output`、`status`、`result_summary`、`evidence_refs`、`blocking_reason`。`mode` 允许 `single`、`sequential`、`parallel`，不得为 `mixed`。`status` 允许 `pending`、`in_progress`、`blocked`、`done`、`skipped`。

`plan_review` 必须承载方案审核编排责任方、审核策略、审核条目、主控处理记录和 Human 方案确认。进入 `human_plan_confirming` 前，`review_items`、`controller_resolution` 必须完成；进入 `executing` 及后续状态前，`human_confirmation` 和 `plan_confirmed_at` 必须填写。

`result_review` 必须承载主控结果自检、结果复核策略、结果复核条目、主控处理记录和 Human 关闭确认。进入 `subagents_result_reviewing` 前，`controller_self_check` 必须完成且 `required_changes` 不得保留未处理必须修改项；进入 `human_closure_confirming` 前，结果复核条目和主控处理记录必须完成；进入 `closed` 前，`human_closure_confirmation` 必须填写。

`revision_history[]` 至少包含 `at`、`from_status`、`to_status`、`actor`、`reason`、`changed_fields` 和 `summary`。发生退回、目标修改、成功标准修改、执行编排修改，或主控根据审核意见修改 WorkCase 字段时，必须追加修订记录。

### 9.3 状态条件字段

| 状态 | 必须满足的对象条件 |
|---|---|
| `subagents_plan_reviewing` | 基础字段、`priority`、`description`、`success_criteria`、`source`、`orchestration.mode`、`orchestration.execution_items`、`orchestration.plan_review` 和 `orchestration.result_review` 已存在；`plan_review.review_policy` 已存在 |
| `human_plan_confirming` | `plan_review.review_items` 已完成，`plan_review.controller_resolution` 已记录主控处理意见、必要修改和未决事项，等待 Human 确认 |
| `executing` | `plan_confirmed_at` 和 `plan_review.human_confirmation` 已填写；执行项可以处于 `pending`、`in_progress`、`blocked`、`done` 或 `skipped` |
| `result_self_checking` | 执行项不得仍为 `pending` 或 `in_progress`；`blocked` 执行项必须填写阻塞原因；主控正在整理或填写自检、验证证据和关闭证据 |
| `subagents_result_reviewing` | 主控自检已填写并签署；`verification_evidence` 和 `closure_evidence` 已填写；结果复核策略已存在 |
| `human_closure_confirming` | 结果复核条目和主控处理记录已完成；`closure_requested_at` 已填写；等待 Human 关闭确认 |
| `closed` | 满足 `human_closure_confirming` 条件；`closed_at`、`closure_outcome` 和 `result_review.human_closure_confirmation` 已填写 |

## 10. 事实实例写入、回写、验证和证据留存

WorkCase 的目标、成功标准、执行编排、验证证据和关闭证据回写到 WorkCase YAML。执行项结果只保留摘要、证据和稳定输出路径，不复制完整对话、工具日志或子 Agent 中间过程。

关闭 WorkCase 前，至少应具备：

1. 成功标准检查结果；
2. 主控自检结论；
3. 必要时的专业角色复检结论；
4. 验证命令、文件路径、产物引用或人工确认记录；
5. 经验、决策、火花或提交追溯的分流结果。

事实源回写必须跟上对话进度。主控不得只在对话中宣布已完成、已通过或进入下一阶段，却让 WorkCase 仍呈现全部执行项 `pending`、成功标准未检查、结果自检为空或 Web 无法派生真实态势。

## 11. Code、Web、知识地图和运行时扩展消费边界

Code 应检查：

1. `priority` 必须属于 `P0`、`P1`、`P2`、`P3`，不得维护 `importance`；
2. `orchestration.execution_items[].id` 在当前 WorkCase 内唯一；
3. `orchestration.mode`、执行项 `mode`、执行项 `status` 和顶层 `status` 必须属于本文枚举；
4. `human_plan_confirming` 及后续状态必须具备方案审核和主控处理记录；
5. `executing` 及后续状态必须填写 `plan_confirmed_at` 和方案确认；
6. `result_self_checking` 及后续状态不得存在 `pending` 或 `in_progress` 执行项；
7. `subagents_result_reviewing` 及后续状态必须填写主控自检、验证证据和关闭证据；
8. `human_closure_confirming` 和 `closed` 必须填写 `closure_requested_at`；
9. `closed` 必须填写 `closed_at`、`closure_outcome` 和 Human 关闭确认；
10. 退回、关键字段修改或主控根据审核意见修改字段时必须追加 `revision_history`；
11. 执行项不得被其他工作对象作为独立对象引用；
12. 工作项相关提交由 Git history 和提交正文自然文本派生，不得手写维护 `related_changes`。
13. `plan_review.review_items[].result.status`、`result_review.review_items[].result.status` 和 `controller_self_check.result.status` 必须属于 `pass`、`pass_with_followups`、`fail`、`needs_human_gate`；
14. `plan_review.human_confirmation.decision` 必须属于 `execute`、`revise_plan`、`close`；
15. `result_review.human_closure_confirmation.decision` 必须属于 `close`、`continue_execution`、`revise_plan`、`request_result_review`、`request_self_check`；
16. `orchestration_owner` 必须属于 `main_controller` 或 `workflow`，主控不得在 `review_items` 中自签冒充子 Agent；
17. `controller_self_check.result.key_findings` 必须非空，`required_changes` 非空时不得进入结果复核；
18. `subagents_result_reviewing` 状态下 `result_review.review_items` 为空时，Code 应至少给出 warning；
19. `related_workcases` 只承载 WorkCase ID，不承载执行项 ID、提交 hash 或自由文本关系。

Web 应把 WorkCase 作为 Human 直接查看和确认的主对象。Web 可以展示执行编排、验证证据和关闭证据，但不得把执行项提升为一级导航、独立对象详情页或可独立写入的权威事实。

知识地图可以消费 WorkCase 成员身份、章节锚点、字段契约、状态机、对象关系和实例事实源目录，生成定位、最小读取、影响判断和诊断提示。知识地图输出不得替代本文、active v1 WorkCase 规范或实例文件。

运行时扩展承载物不得复制 WorkCase 完整字段契约、状态机、关闭条件或 Human Gate 细则；需要摘要时必须回指本文、active WorkCase 规范和对应实例事实源。

## 12. 附件规则

本文授权以下附件承载可枚举、可复用或可被 Code/Web 消费的细表；附件不得替代本文、02、07、行动编排或测试治理。

| 附件 | 承载内容 | 不承载 |
|---|---|---|
| `attachments/21.Att.01-orchestration字段契约表.md` | WorkCase `orchestration` 长字段表、枚举和条件 | 状态机本体、Human Gate 本体、行动编排流程 |

新增、删除、重命名或改变以上附件的信息对象时，应回到本文 Human Gate，并同步 01 当前目录登记、README 写作区入口和 Code v2 解析。

## 13. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | WorkCase 实例和后续行动编排应遵守本文定义的准入、状态机、执行项内部化、审核记录、Human Gate、字段契约和关闭判断 | 本文、active `specs/21-WorkCase-工作项.md`、v2 02、Human Gate；未 active 前为人工降级检查 | 事实模型治理 | 创建、迁移、关闭、重排或审计 WorkCase 时 |
| 入口可见要求 | AI 处理需要组织为可执行、可验证、可关闭目标时，应能定位 WorkCase active 规范、本文草案和对应实例事实源 | `specs-v2/README.md`、02 成员身份、知识地图输入、运行时入口；未 active 前为人工降级检查 | AI 执行入口 | WorkCase 入口、成员身份、实例目录或读取顺序变化时 |
| 确定性执行要求 | WorkCase 状态、执行项、方案审核、自检、结果复核、关闭确认、修订记录、条件必填和完成口径应由 Code 校验或记录缺口 | 现有 active Code、`02.Att.04`、`02.Att.05`、`02.Att.06`、`21.Att.01`、人工降级检查；v2 双读实现和测试仍待后续 Code 规范承接 | Code 校验 | 字段契约、状态机、执行编排、Web 派生态势或 Code 消费入口变化时 |
| 子 Agent 思考要求 | 方案审核和结果复核必须记录审核 Agent、角色、提示上下文、输入引用、重点结论、可审计签署声明和主控处理记录 | Agent 能力、主控多视角审查、事实实例校验；后续可由行动编排接管 | 独立审查 | 方案审核、结果复核、Agent 能力、签署字段或主控处理记录变化时 |
| Human 交互要求 | 方案执行和最终关闭必须经 Human 确认；退回、修改方案或接受残留风险必须记录原因和修改内容 | Human Gate、Web 展示、事实实例校验 | Human Gate | 方案确认、关闭确认、退回或修改关键字段时 |
| 生命周期触发要求 | WorkCase 规范变化后应检查 Spark、ADR、Pitfall、Code、Web、运行时扩展、行动编排和待补齐事项是否同步 | 本文、02 授权附件、active 20-23、Code 诊断、人工降级检查；建议由规范生命周期同步行动编排接管 | 生命周期同步 | 字段、状态、执行编排、事实源路径或展示规则变化时 |

## 14. 对象特有实例检查

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 WorkCase |
| 文件命名 | 实例路径符合 `ldvh-base/workcases/workcase-{NNNN}-short-title.yaml` |
| 优先级 | `priority` 已填写且符合 02 统一标准，未维护 `importance` |
| 执行编排 | `orchestration.execution_items` 是内部字段，不存在独立执行项事实源文件 |
| 状态枚举 | `status` 属于本文 §6.1 状态枚举，且不使用旧的 `draft`、`active`、`review_needed` |
| 方案审核 | `human_plan_confirming` 及后续状态具备方案审核 Agent、输入引用、重点结论、签署声明和主控处理记录 |
| 对话感知 | 跨阶段推进时清楚表达当前状态、已完成项、剩余阻塞、下一 Gate 和待 Human 确认事项 |
| Web 感知 | `executing` 及后续状态的执行项、成功标准和证据回写足以支持 Web 派生真实态势 |
| 结果自检 | `subagents_result_reviewing` 及后续状态具备主控自检、验证证据和关闭证据 |
| 结果复核 | `human_closure_confirming` 及后续状态具备真实独立结果复核材料；硬问题已处理或退回 |
| 关闭证据 | `human_closure_confirming` / `closed` 具备验证证据、关闭证据和关闭确认请求时间 |
| 完成口径 | 能清楚区分执行完成、可提交关闭确认、已关闭和已提交 |
| 修订记录 | 退回、方案修改、成功标准修改、执行编排修改或主控根据审核意见修改字段时，`revision_history` 记录原因、字段和修改内容 |

## 15. 待补齐事项

1. WorkCase v2 草案和 `21.Att.01` 已迁入主要状态机、执行编排、方案审核、结果自检、结果复核、关闭确认、修订记录和 orchestration 长字段规则，并已完成 Human 单篇确认；active 切换前仍以 active v1 WorkCase 规范为默认入口；
2. active `ldvh_member` 与 v2 `v2_fact_model_member` 的双读 Code 实现、正反样例和切换策略尚未完成；本文不改变 Code 默认消费入口；
3. WorkCase Web 派生态势、状态标签和关闭/提交口径应在 v2 Web 规范和实现迁移时复核；
4. WorkCase 创建、方案审核、结果复核和关闭确认的具体行动编排不按 v1 直接迁入；应待 v2 保障需求稳定后进入行动编排候选计划；
5. 本文切换 active 前，应再次核对 active `specs/21-WorkCase-工作项.md`、02 授权附件、现有 Code/Web 测试和相关 active 20-24 成员规则，确认没有字段、状态、引用或消费入口漂移。
