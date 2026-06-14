# TaskPlan-任务计划

> 创建日期：2026-06-12
> 定位：定义 TaskPlan / 任务计划工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写和适配规则
> 适用范围：所有接入 LDVH 且需要把一次目标拆解为可追踪任务序列、前置关系或并行执行单元的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/02-术语规范.md`、`specs/03.03-工作模型文档规范.md`、`specs/05.01-工作字段内容格式规范.md`、`specs/06-工作流程基础规范.md`、`specs/07-Code确定性执行实现规范.md`、`specs/08-Web信息同步实现规范.md`、`specs/09-事实源边界与承载规范.md`、`specs/20-WorkArea-工作域.md`、`specs/22-Task-任务.md`

```yaml
ldvh_member:
  spec_id: "21"
  kind: work_model
  name_en: TaskPlan
  name_zh: 任务计划
  collection_status: active
  canonical_path: specs/21-TaskPlan-任务计划.md
  instance_root: ldvh-base/taskplans/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
    - status_machine
    - instance_checks
```

---
## 1. 对象定位与准入条件

TaskPlan / 任务计划是 Human 与 AI 围绕一次目标达成的执行契约。任务计划承载目标、范围、成功标准、所属工作域、任务列表、人工确认点和最终关闭判断。

Human 直接沟通和确认任务计划；AI 主导计划下 Task 和 SubTask 的执行。即使一次目标只拆出一个 Task，也必须创建任务计划，避免出现 Task 直接游离于工作域或对话之外的例外。

### 1.1 任务计划准入条件

一个目标满足以下条件之一时，应形成任务计划：

1. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
2. 需要一个或多个 Task 承载执行；
3. 需要表达前置关系、并行执行或阶段性执行；
4. 需要 Human 明确确认目标、范围、成功标准或关闭判断；
5. 需要留下验证、关闭证据或结果物引用；
6. 不结构化会导致目标、范围、任务关系或完成判断漂移。

当前对话即可完成、无需留存纪录、无需流程治理的小工作，不创建任务计划。

---
## 2. 事实源边界

任务计划实例的权威事实源位置为：

```text
ldvh-base/taskplans/taskplan-{NNNN}-short-title.yaml
```

| 内容 | 权威位置 |
|---|---|
| 任务计划工作模型规范 | `specs/21-TaskPlan-任务计划.md` |
| 任务计划实例 | `ldvh-base/taskplans/` |
| 任务计划字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| 任务计划展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

---
## 3. 状态机

### 3.1 标准状态

| 状态 | 含义 |
|---|---|
| `draft` | 已记录，目标、范围、成功标准或任务拆解尚未确认 |
| `active` | 已确认，可执行或正在执行 |
| `review_needed` | 任务计划的关闭证据已整理，待关闭审查 |
| `closed` | 关闭判断已确认，计划终态稳定 |

`closed` 是稳定终态。目标重新启动、扩大范围或改变成功标准时，应创建新的任务计划，并引用原任务计划。

`active` 状态的任务计划不得退回 `draft`。如果确认后发现目标、范围或成功标准需要大幅修改，应关闭当前任务计划（在 `completion_evidence` 中记录撤回原因），并创建新任务计划引用原任务计划。

### 3.2 合法状态流转

```text
draft -> active
active -> review_needed
review_needed -> closed
review_needed -> active
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `draft` -> `active` | 工作域、目标、成功标准和初始任务列表已确认；`tasks` 不得为空 | Human 直接确认的主要入口 |
| `active` -> `review_needed` | 计划内应关闭的 Task 均已关闭，证据已整理 | 应填写 `review_requested_at` 和 `completion_evidence` |
| `review_needed` -> `closed` | Human 完成关闭审查 | 应填写 `closed_at` |
| `review_needed` -> `active` | 审查不通过或需要继续执行 | 应记录退回原因 |

---
## 4. 对象关系

### 4.1 任务计划与工作域

每个任务计划必须通过 `workarea` 引用一个工作域。任务计划不得脱离工作域存在。

### 4.2 任务计划与任务

任务计划通过 `tasks` 字段记录计划内 Task ID 列表。每个 Task 必须通过 `taskplan` 指回唯一任务计划。

任务间前置关系由 Task 的 `blocked_by` 字段表达，属于计划内部执行关系。任务计划展示任务序列或并行可能性时，应从计划内 Task 的 `blocked_by` 派生，不引入额外分组对象。

规则如下：

1. `tasks` 中的每个 Task 必须存在；
2. Task 的 `taskplan` 必须指回当前任务计划；
3. 计划进入 `review_needed` 前，计划内应完成的 Task 必须为 `closed`；
4. Task 的验收标准、验证方式和关闭证据由 Task 自身承载；
5. 任务计划只摘要引用 Task 结果，不复制 Task 的完整证据。

### 4.3 任务计划与 SubTask

任务计划不直接引用 SubTask。SubTask 只归属于 Task，并通过 Task 间接进入任务计划。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名任务计划；
2. 将用户输入、Memo 或临时讨论升级为任务计划；
3. 确认 `draft` -> `active`；
4. 将任务计划从 `active` 推进到 `review_needed`；
5. 将任务计划从 `review_needed` 关闭为 `closed`；
6. 改写目标、成功标准、任务列表或工作域归属；
7. 跳过未关闭 Task 或通过豁免关闭任务计划；
8. 合并或拆分任务计划。

Human Gate 发生在任务计划层。Task 和 SubTask 不作为 Human 直接管理入口。

---
## 6. 字段契约

公共字段语义定义见 `specs/05.01-工作字段内容格式规范.md` §3.5。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `taskplan-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `taskplan` | string | 是 | 固定为 `taskplan` | Reference | AI、Code、Web |
| `title` | 任务计划一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `workarea` | 所属工作域 ID | string | 是 | 必须引用已存在 WorkArea | Reference | AI、Code、Web |
| `priority` | 执行优先级 | string | 是 | `P0`、`P1`、`P2`、`P3`；判断标准见 `specs/05-工作模型基础规范.md` §7.3.1 | Reference | AI、Code、Web |
| `importance` | 重要程度 | string | 是 | `high`、`medium`、`low`；判断标准见 `specs/05-工作模型基础规范.md` §7.3.1 | Reference | AI、Code、Web |
| `description` | 目标背景、范围和问题说明 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `success_criteria` | 任务计划成功标准 | string | 是 | 应能支持关闭审查 | Narrative / Checklist | AI、Code、Web |
| `source` | 任务计划来源 | string | 是 | 谁在什么场景下表达 | Reference / Narrative | AI、Web |
| `tasks` | 计划内 Task ID 列表 | list[string] | 是 | `draft` 状态下可为空列表；`active` 及之后状态至少一个 Task；Task 必须指回本计划 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 来源或关联备忘 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联踩坑 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `status_history` | — | list[object] | 否 | 状态变化时追加 | Log | AI、Code |
| `review_requested_at` | 请求关闭审查时间 | date | 条件必填 | `review_needed` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `completion_evidence` | — | string | 条件必填 | `review_needed` 或 `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closed_at` | — | date | 条件必填 | `closed` 时必须填写 | Reference | AI、Code、Web |

### 6.1 YAML 示例

```yaml
id: taskplan-0001
type: taskplan
title: 重构工作模型状态边界
status: active
created: '2026-06-12T00:00:00'
updated: '2026-06-12T00:00:00'
workarea: workarea-0001
priority: P1
importance: high
description: |
  将一次模型重构目标拆解为可执行任务，并在任务完成后进行关闭审查。
success_criteria: |
  - [ ] 工作模型规范已更新
  - [ ] 事实实例已迁移
  - [ ] Validator、CLI 和 Web 已同步
source: 用户确认创建任务计划
tasks:
  - task-0001
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
```

---
## 7. 事实源回写与证据留存

任务计划的目标、成功标准、任务列表和关闭审查证据回写到任务计划 YAML。Task 的执行细节、验收、验证和关闭证据回写到 Task；SubTask 的局部执行证据回写到 SubTask。

---
## 8. 适配边界

Code 应检查：

1. 任务计划必须引用存在的 WorkArea；
2. `priority` 必须属于 `P0`、`P1`、`P2`、`P3`；
3. `importance` 必须属于 `high`、`medium`、`low`；
4. `draft` 状态下 `tasks` 可为空列表，`active` 及之后状态 `tasks` 必须非空；
5. `tasks` 中每个 Task 必须存在并通过 `taskplan` 指回当前任务计划；双向引用不一致时必须报告诊断，不得静默通过；
6. `review_needed` 和 `closed` 必须提供关闭审查字段；
7. `closed` 任务计划内的 Task 必须已关闭。

Web 应把任务计划作为 Human 直接查看和确认的主对象。Task 和 SubTask 的状态可以展示，但不应作为 Human 直接管理入口。

---
## 9. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 任务计划必须遵守 05、20、24 和本文定义的人机职责边界 | 05、20、24、本文、Human Gate | 工作模型治理 | 创建、迁移、关闭或拆分任务计划时 |
| 确定性执行要求 | 每个 Task 必须归属一个任务计划 | Validator、CLI、Web 展示 | 事实模型校验 | 创建或迁移 Task 时 |
| 确定性执行要求 | 任务计划必须依据 05 的统一标准维护 `priority` 和 `importance` | Validator、CLI、Web 展示 | 字段契约同步 | 创建、更新、排序、筛选或展示任务计划时 |
| 生命周期触发要求 | 任务计划规范变化后应检查 Task、SubTask、Code、Web 和事实实例 | Code 测试、事实校验、Web 检查 | 触发保障 | 字段、状态或关系变化时 |

---
## 10. 检查要求

| 检查项 | 标准 |
|---|---|
| 工作域归属 | 每个任务计划必须引用一个存在的工作域 |
| 优先级与重要程度 | `priority` 和 `importance` 已填写，且符合 05 统一标准 |
| 任务归属 | `active` 及之后状态 `tasks` 非空，且每个 Task 指回当前任务计划；`draft` 状态 `tasks` 可为空 |
| 人类入口 | 关闭审查发生在任务计划层 |
| 关闭证据 | review_needed / closed 具备关闭审查字段 |
| 无额外分组对象 | 规范和事实源不引入额外分组对象 |

---
## 11. 待补齐事项

暂无额外待补齐事项；后续随字段契约、Code 校验或 Web 消费变化更新。
