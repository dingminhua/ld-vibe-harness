# SubTask-子任务

> 创建日期：2026-06-12
> 定位：定义 SubTask / 子任务工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写和适配规则
> 适用范围：所有接入 LDVH 且需要在 Task 内拆分最小并行执行单元的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/05.01-工作字段内容格式规范.md`

```yaml
ldvh_member:
  spec_id: "23"
  kind: work_model
  name_en: SubTask
  name_zh: 子任务
  collection_status: active
  canonical_path: specs/23-SubTask-子任务.md
  instance_root: ldvh-base/subtasks/
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

SubTask / 子任务是 Task 下的最小可执行、可并行、可验证单元。子任务用于把一个 Task 内部可以独立推进的叶子工作拆出来，让 AI 或不同执行角色可以并行处理。

子任务不是新的任务层级。SubTask 不得再拥有 SubTask；如果执行中发现新的叶子工作，应创建同一 Task 下的并列 SubTask，或回到 TaskPlan 重新拆分 Task。

### 1.1 子任务准入条件

一个执行单元满足以下条件之一时，应考虑形成子任务：

1. 属于某个 Task 内部，但可以独立执行和验证；
2. 可以与同一 Task 下其他子任务并行；
3. 需要独立记录局部结果、验证或阻塞原因；
4. 不拆分会导致 Task 过大、验证不清或并行执行困难。

当前 Task 内的一般步骤、临时 TODO 或无需独立状态的操作，不创建子任务。

---
## 2. 事实源边界

子任务实例的权威事实源位置为：

```text
ldvh-base/subtasks/subtask-{NNNN}-short-title.yaml
```

| 内容 | 权威位置 |
|---|---|
| 子任务工作模型规范 | `specs/23-SubTask-子任务.md` |
| 子任务实例 | `ldvh-base/subtasks/` |
| 子任务字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| 子任务展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

---
## 3. 状态机

### 3.1 标准状态

| 状态 | 含义 |
|---|---|
| `planned` | 已创建，待执行 |
| `executing` | 正在执行 |
| `verifying` | 执行完成，正在验证 |
| `review_needed` | 已验证，待并入 Task 关闭检查 |
| `closed` | 关闭条件满足，已关闭 |

`closed` 是稳定终态。需要重新处理时，应创建新的子任务或回到 Task 重新拆分。

### 3.2 合法状态流转

```text
planned -> executing
executing -> verifying
verifying -> review_needed
verifying -> executing
review_needed -> closed
review_needed -> executing
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `planned` -> `executing` | 开始执行；`blocked_by` 中所有 SubTask 必须为 `closed` | 硬前置约束，不满足时不得进入执行 |

---
## 4. 对象关系

### 4.1 子任务与任务

每个子任务必须通过 `task` 字段引用一个 Task。Task 可以通过派生展示看到所属子任务，但 Task 不再使用 `parent_task` 或 `sub_tasks` 字段承载父子任务关系。

规则如下：

1. 子任务必须归属一个存在的 Task；
2. 子任务不得引用 TaskPlan 或 WorkArea 作为直接父级；
3. 子任务不得再拥有子任务；
4. Task 关闭前，其所属子任务必须均已 `closed`；
5. 子任务的结果应被 Task 摘要引用，不替代 Task 的关闭证据。

### 4.2 子任务依赖

子任务可以通过 `blocked_by` 引用同一 Task 下的其他 SubTask，表示硬前置依赖。`blocked_by` 表示当前子任务进入执行态前必须等待的前置子任务列表。不同 Task 下的执行关系应由 Task 的 `blocked_by` 表达。

前置依赖规则如下：

1. `blocked_by` 为 SubTask ID 列表，可为空；
2. 每个 SubTask ID 必须引用已存在且同属一个 Task 的 SubTask；
3. 当前 SubTask 不得引用自身；
4. 当前 SubTask 从 `planned` 进入 `executing` 前，`blocked_by` 中所有 SubTask 必须为 `closed`。

---
## 5. Human Gate

子任务不作为 Human 直接管理入口。以下情况应回到 Task 或 TaskPlan 层评估 Human Gate：

1. 创建、删除或重命名高影响子任务；
2. 子任务发现会改变 Task 验收标准或任务计划范围的问题；
3. 子任务无法验证或需要人工确认局部结果；
4. 子任务关闭会影响 Task 或任务计划的最终判断。

---
## 6. 字段契约

公共字段语义定义见 `specs/05.01-工作字段内容格式规范.md` §3.5。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `subtask-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `subtask` | string | 是 | 固定为 `subtask` | Reference | AI、Code、Web |
| `title` | 子任务一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `task` | 所属 Task ID | string | 是 | 必须引用已存在 Task | Reference | AI、Code、Web |
| `description` | 子任务目标、范围和步骤说明 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `source` | 子任务来源 | string | 是 | Task 内拆解、AI 发现或人工确认 | Reference / Narrative | AI、Web |
| `acceptance` | 关闭前全部为 `- [x]` | string | 是 | 关闭前全部为 `- [x]` | Checklist | AI、Code、Web |
| `blocked_by` | 同一 Task 下的前置 SubTask | list[string] | 否 | 默认为空列表；必须同属一个 Task | Reference | AI、Code、Web |
| `verification` | 关闭前必须填写 | string | 否 | 关闭前必须填写 | 验证证据 / Checklist | AI、Code、Web |
| `closure_evidence` | — | string | 条件必填 | `closed` 时必须填写 | 验证证据 | AI、Code、Web |
| `closed_at` | — | date | 条件必填 | `closed` 时必须填写 | Reference | AI、Code、Web |
| `status_history` | — | list[object] | 否 | 状态变化时追加 | Log | AI、Code |

### 6.1 YAML 示例

```yaml
id: subtask-0001
type: subtask
title: 更新对象类型枚举
status: planned
created: '2026-06-12T00:00:00'
updated: '2026-06-12T00:00:00'
task: task-0001
description: |
  在 Validator、CLI 和 Web 中补齐新的对象类型枚举。
source: task-0001
acceptance: |
  - [ ] 新对象类型可以通过校验
blocked_by: []
```

---
## 7. 事实源回写与证据留存

子任务的局部执行结果和证据回写到子任务 YAML。Task 关闭证据应摘要引用相关子任务结果，不复制子任务全文。

---
## 8. 适配边界

Code 应检查：

1. 子任务必须引用存在的 Task；
2. 子任务不得拥有子任务字段；
3. `blocked_by` 只能引用同一 Task 下的 SubTask；
4. 子任务从 `planned` 进入 `executing` 前，`blocked_by` 中所有 SubTask 必须为 `closed`；
5. `closed` 子任务必须具备 `closed_at`、`verification` 和 `closure_evidence`；
6. 关闭 Task 前，其所属子任务必须关闭。

Web 可以展示子任务，但不应把子任务作为 Human 直接管理入口。

---
## 9. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 子任务必须遵守 05、20、26 和本文定义的叶子执行边界 | 05、20、26、本文 | 工作模型治理 | 创建、迁移或关闭子任务时 |
| 确定性执行要求 | 子任务不得再拥有子任务 | Validator、CLI、Web 展示 | 事实模型校验 | 子任务字段变化时 |
| 生命周期触发要求 | 子任务规范变化后应检查 Task、Code、Web 和事实实例 | Code 测试、事实校验、Web 检查 | 触发保障 | 字段、状态或关系变化时 |

---
## 10. 检查要求

| 检查项 | 标准 |
|---|---|
| Task 归属 | 每个子任务必须引用一个存在的 Task |
| 无递归 | 子任务没有 `sub_tasks` 或 `parent_task` 字段 |
| 关闭证据 | closed 子任务具备验证和关闭证据 |
| 同级依赖 | `blocked_by` 只引用同一 Task 下子任务 |
| 前置约束 | `planned` → `executing` 前 `blocked_by` 中所有 SubTask 必须为 `closed` |

---
## 11. 待补齐事项

暂无额外待补齐事项；后续随字段契约、Code 校验或 Web 消费变化更新。
