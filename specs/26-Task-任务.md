# Task-任务

> 创建日期：2026-06-09
> 更新日期：2026-06-12
> 定位：定义 Task / 任务工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要管理 AI 可执行工作单元、验收标准、状态追踪和关闭证据的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/02-术语规范.md`、`specs/03.03-工作模型文档规范.md`、`specs/05.01-工作字段内容格式规范.md`、`specs/06-工作流程基础规范.md`、`specs/07-Code确定性执行实现规范.md`、`specs/08-Web信息同步实现规范.md`、`specs/09-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`、`specs/27-TaskPlan-任务计划.md`、`specs/28-SubTask-子任务.md`

---
## 1. 对象定位与准入条件

Task / 任务是 AI 可执行的工作单元，有明确目标、验收标准、状态流转和回写目标。Task 只在 TaskPlan / 任务计划下存在；Human 直接确认任务计划，AI 主导 Task 执行。

Task 不再承担父子任务层级。需要在 Task 内拆分最小并行执行单元时，应创建 SubTask / 子任务。SubTask 不得再拆分。

### 1.1 Task 准入条件

一个工作单元满足以下条件之一时，应考虑形成 Task：

1. 已属于某个任务计划；
2. 有明确目标和可验证验收标准；
3. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
4. 需要关闭证据、验证结果或产物引用；
5. 存在前置依赖、风险判断、文档同步检查或需要拆分子任务；
6. 不结构化会导致进度、验收标准或验证结果不可追踪。

当前上下文中可以直接完成、无需留存事实源的小工作，不创建 Task。

---
## 2. 事实源边界

Task 实例的权威事实源位置为：

```text
ldvh-base/tasks/task-{NNNN}-short-title.yaml
```

| 内容 | 权威位置 |
|---|---|
| Task 工作模型规范 | `specs/26-Task-任务.md` |
| Task 实例 | `ldvh-base/tasks/` |
| Task 字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| Task 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

---
## 3. 状态机

### 3.1 标准状态

| 状态 | 含义 |
|---|---|
| `planned` | 已创建，待执行 |
| `executing` | 正在执行 |
| `verifying` | 执行完成，正在进行验证 |
| `review_needed` | 已验证，待完成关闭检查 |
| `closed` | 关闭条件满足，已关闭 |

`closed` 是稳定终态。终态 Task 不得直接重开；如需重新处理，应在同一任务计划或新任务计划下创建新 Task。

### 3.2 合法状态流转

```text
planned -> executing
executing -> verifying
verifying -> review_needed
verifying -> executing
review_needed -> closed
review_needed -> executing
```

未列出的状态流转为非法流转。

### 3.3 关闭条件

Task 进入 `closed` 前必须同时满足：

1. `acceptance` 字段中所有检查项已标记为 `- [x]`；
2. 所属 SubTask 均为 `closed`；
3. `verification` 已说明验证方式、验证命令、人工审查方式或无法自动验证的降级方式；
4. `closure_evidence` 已填写，并能追溯到 Git 文件事实源、验证命令、结果物、人工确认或审计结论；
5. `affected_docs` 非空时，已完成文档同步检查或在 `closure_evidence` 中说明豁免理由；
6. `closed_at` 已填写；
7. 需要 Human Gate 的场景已回到 TaskPlan 层确认。

---
## 4. 对象关系

### 4.1 Task 与任务计划

每个 Task 必须通过 `taskplan` 引用一个 TaskPlan。Task 不得脱离任务计划存在。

规则如下：

1. `taskplan` 必须引用存在的任务计划；
2. 被引用任务计划的 `tasks` 必须包含当前 Task ID；
3. Task 不直接引用 WorkArea，所属工作域从 TaskPlan 的 `workarea` 字段追溯；
4. Task 的关闭证据可被 TaskPlan 摘要引用，但不被 TaskPlan 复制为第二权威事实。

### 4.2 Task 与 SubTask

SubTask 通过 `task` 字段引用 Task。Task 不保存 `parent_task` 或 `sub_tasks` 字段。

规则如下：

1. Task 可以拥有零个或多个 SubTask；
2. Task 关闭前，其所属 SubTask 必须均已关闭；
3. SubTask 结果应被 Task 摘要吸收；
4. SubTask 不得再拥有子任务。

### 4.3 Task 与前置依赖

Task 可以通过 `blocked_by` 声明同一任务计划内的前置 Task。`blocked_by` 表示当前 Task 进入执行态前必须等待的硬前置 Task 列表。

前置依赖规则如下：

1. `blocked_by` 为 Task ID 列表，可为空；
2. 每个 Task ID 必须引用已存在 Task；
3. 当前 Task 不得引用自身；
4. 前置 Task 应属于同一 TaskPlan；
5. 当前 Task 从 `planned` 进入 `executing` 前，`blocked_by` 中所有 Task 必须为 `closed`。

### 4.4 Task 与 ADR、Change、Memo、Pitfall

Task 可以引用 ADR、Memo、Pitfall、文档和 Git commit。Change 的 commit message 契约和 Git 记录事实源边界由 `specs/22-Change-变更.md` 定义。

---
## 5. Human Gate

Task 不作为 Human 直接管理入口。以下情况应回到 TaskPlan 层评估 Human Gate：

1. 创建、删除或重命名 Task；
2. 修改 TaskPlan 的任务列表、目标或成功标准；
3. 跳过、删除或改写 Task 的 `acceptance`；
4. 在 `affected_docs` 无实际变更时，通过豁免理由关闭 Task；
5. 关闭高风险 Task，或用户明确要求人工验收；
6. 绕过合法状态流转、修改 `closed` 终态或补写关闭证据；
7. Task 执行发现计划范围、任务依赖或成功标准需要变化。

---
## 6. 字段契约

下表“消费方”表示读取、Web 展示、校验或执行时会消费该字段，不表示 Web 写入授权。

公共字段语义定义见 `specs/05.01-工作字段内容格式规范.md` §3.5。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `task-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `task` | string | 是 | 固定为 `task` | Reference | AI、Code、Web |
| `title` | 任务一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `taskplan` | 所属任务计划 ID | string | 是 | 必须引用已存在 TaskPlan | Reference | AI、Code、Web |
| `description` | 任务背景、目标和范围 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `source` | 任务来源 | string | 是 | 任务计划、用户指示或其他可追溯来源 | Reference / Narrative | AI、Web |
| `blocked_by` | 同一任务计划内的前置 Task | list[string] | 否 | 默认为空列表；必须同属一个任务计划 | Reference | AI、Code、Web |
| `acceptance` | 关闭前全部为 `- [x]` | string | 是 | 关闭前全部为 `- [x]` | Checklist | AI、Code、Web |
| `verification` | 执行进入验证前应补齐 | string | 否 | 执行进入验证前应补齐 | Evidence / Checklist | AI、Code、Web |
| `assignee` | 执行者 | string | 否 | 可为 AI、Human 或角色名 | Reference | AI、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_changes` | 关联变更 | list[string] | 否 | 可记录 commit hash 或 Change 引用 | Reference | AI、Code、Web |
| `related_docs` | 参考输入文档路径 | list[string] | 否 | 路径应可追溯 | Reference | AI、Code、Web |
| `affected_docs` | 任务完成后应同步检查的文档路径 | list[string] | 否 | 关闭前检查是否变更或说明豁免 | Reference | AI、Code |
| `deliverables` | 产物、报告、截图、构建产物或导出文件路径 | list[string] | 否 | 结果物应可追溯 | Reference | AI、Code、Web |
| `status_history` | — | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |
| `closed_at` | — | date | 条件必填 | `status: closed` 时必须填写 | Reference | AI、Code、Web |
| `closure_evidence` | — | string | 条件必填 | `status: closed` 时必须填写 | Evidence | AI、Code、Web |

### 6.1 YAML 示例

```yaml
id: task-0001
type: task
title: 更新 Task 工作模型
status: planned
created: '2026-06-12T00:00:00'
updated: '2026-06-12T00:00:00'
taskplan: taskplan-0001
description: |
  将 Task 工作模型调整为任务计划下的 AI 执行单元。
source: taskplan-0001
blocked_by: []
acceptance: |
  - [ ] Task 必须归属任务计划
  - [ ] Task 不再使用 parent_task / sub_tasks
related_adrs: []
related_docs: []
affected_docs: []
deliverables: []
```

---
## 7. 事实源回写与证据留存

Task 的执行、验收、验证和关闭证据回写到 Task YAML。任务计划只摘要引用 Task 结果，不复制 Task 的权威事实。

---
## 8. 适配边界

Code 应检查：

1. Task 必须引用存在的 TaskPlan；
2. 被引用 TaskPlan 的 `tasks` 必须包含当前 Task；双向引用不一致时必须报告诊断，不得静默通过；
3. Task 不得包含 `source_intent`、`parent_task`、`sub_tasks`、`priority`、`importance` 或 `risk_assessment` 字段；
4. `blocked_by` 只能引用同一任务计划内的 Task；
5. 关闭 Task 前，其所属 SubTask 均已关闭；
6. `closed` Task 必须具备 `closed_at`、`verification` 和 `closure_evidence`。

Web 可以展示 Task，但应把 TaskPlan 作为 Human 直接确认和关闭审查入口。

---
## 9. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Task 必须遵守 05、20、27 和本文定义的执行单元边界 | 05、20、27、本文 | 工作模型治理 | 创建、迁移或关闭 Task 时 |
| 确定性执行要求 | 每个 Task 必须归属一个 TaskPlan | Validator、CLI、Web 展示 | 事实模型校验 | 创建或迁移 Task 时 |
| 生命周期触发要求 | Task 规范变化后应检查 TaskPlan、SubTask、Code、Web 和事实实例 | Code 测试、事实校验、Web 检查 | 触发保障 | 字段、状态或关系变化时 |

---
## 10. 检查要求

| 检查项 | 标准 |
|---|---|
| 任务计划归属 | 每个 Task 必须引用一个存在的 TaskPlan |
| 无子任务冗余字段 | Task 不包含 `parent_task`、`sub_tasks` |
| 无 Intent 字段 | Task 不包含 `source_intent` |
| 无废弃判断字段 | Task 不包含 `priority`、`importance` 或 `risk_assessment`；风险、约束和降级说明写入 `description`、`acceptance` 或 `verification` |
| 前置依赖 | `blocked_by` 只引用同一任务计划内 Task |
| 关闭证据 | closed Task 具备验证和关闭证据 |

---
## 11. 待补齐事项

暂无额外待补齐事项；后续随字段契约、Code 校验或 Web 消费变化更新。
