# LDVH 工作域与任务计划对象模型重构参考

> 创建日期：2026-06-12
> 定位：记录 LDVH 从 Intent 主导模型转向 WorkArea / TaskPlan / Task / SubTask 模型的设计决策、边界约束和迁移原则
> 关联对象：当前对话决策；后续应落入 `docs/specs/20-工作模型集合索引.md`、`docs/specs/24-WorkArea-工作域.md`、`docs/specs/27-TaskPlan-任务计划.md`、`docs/specs/26-Task-任务.md`、`docs/specs/28-SubTask-子任务.md`

---
## 1. 决策背景

LDVH 旧模型以 Intent / 意图承载人的目标、成功标准、任务集合和完成判断。实践中出现两个边界问题：

1. 长期工作范围不适合用 Intent 表达。类似 Web 展示管理、工作流程管理、规则规范梳理等对象不是一次性目标，不能用 `completed`、`closed` 或待关闭语义自然表达。
2. 具体目标执行需要表达前置关系、并行关系、Human 确认点和关闭证据。旧 Intent 与 Task 的二层结构不足以稳定承载“一个目标拆成一组任务序列”的计划语义。

因此 LDVH 正式退出 Intent 作为 active 工作模型，改为任务优先、计划治理、AI 执行的对象模型。

---
## 2. 最终对象链路

LDVH 工作主链路固定为：

```text
WorkArea -> TaskPlan -> Task -> SubTask
工作域 -> 任务计划 -> 任务 -> 子任务
```

对象边界如下：

| 对象 | 中文名 | 定位 | 生命周期边界 |
|---|---|---|---|
| `WorkArea` | 工作域 | 长期工作范围、系统领域或治理范围 | 只有活跃和归档，不表达完成 |
| `TaskPlan` | 任务计划 | 人与 AI 围绕一次目标达成的执行契约 | 由人确认，具备关闭审查 |
| `Task` | 任务 | AI 可执行的工作单元 | 必须归属一个任务计划 |
| `SubTask` | 子任务 | Task 下最小可并行执行单元 | 必须归属一个任务，不得再拆分 |

`TaskGroup` 不进入模型，也不作为字段引入。并行关系和前置关系直接由 `TaskPlan.tasks` 中的 `depends_on` 或类似结构表达，避免增加新的理解负担。

---
## 3. 命名约束

为避免同一对象出现多个日常叫法，命名规则如下：

1. `WorkArea` 的中文正式名和 UI 名均为“工作域”，不使用“模块”“工作集合”“工作区”等别名。
2. `TaskPlan` 使用“任务计划”，UI 可直接显示“任务计划”。
3. `Task` 使用“任务”。
4. `SubTask` 使用“子任务”。
5. 新事实 ID 使用短对象前缀：`workarea-0001`、`taskplan-0001`、`task-0001`、`subtask-0001`。

---
## 4. 人机职责边界

Human 直接沟通和确认的对象是 `TaskPlan`。

Human 应在任务计划层确认：

1. 目标、范围和成功标准；
2. 所属工作域；
3. 任务拆解、前置关系和可并行关系；
4. 需要人工确认的 Gate；
5. 最终关闭判断和证据是否足够。

AI 主导 `Task` 和 `SubTask` 的执行、验证、证据整理和事实源回写。Task 和 SubTask 可以有状态，但它们不作为 Human 直接管理入口。

很小、无需留存纪录、无需流程治理、当前对话即可完成的工作，不创建任务计划、任务或子任务。

---
## 5. 无例外归属规则

为保持模型可管理性，主链路不允许例外：

1. 每个 `TaskPlan` 必须归属一个 `WorkArea`。
2. 每个 `Task` 必须归属一个 `TaskPlan`。
3. 每个 `SubTask` 必须归属一个 `Task`。
4. `SubTask` 不得再拥有子任务。
5. 即使只有一个 Task，也必须有一个 TaskPlan；重复上下文必须通过引用处理，不制造多个权威事实。

---
## 6. 事实引用和重复控制

跨层重复只允许重复摘要，不允许重复权威事实。

推荐规则：

1. `TaskPlan` 记录目标、成功标准、任务关系和关闭判断。
2. `Task` 记录执行目标、验收标准、验证方式和关闭证据。
3. `SubTask` 记录叶子执行步骤、结果和局部证据。
4. 如果下层需要使用上层事实，应通过 ID 引用，而不是复制完整目标或成功标准。
5. 如果上层需要呈现下层结果，应摘要引用 Task / SubTask 的证据，不替代下层事实源。

---
## 7. 状态边界

推荐状态边界如下：

| 对象 | 状态 |
|---|---|
| `WorkArea` | `active`、`archived` |
| `TaskPlan` | `draft`、`active`、`review_needed`、`closed` |
| `Task` | `planned`、`executing`、`verifying`、`review_needed`、`closed` |
| `SubTask` | `planned`、`executing`、`verifying`、`review_needed`、`closed` |

`WorkArea` 不使用 `completed`、`review_needed` 或 `closed`。长期工作恢复时应从 `archived` 回到 `active`，不是重开完成态。

---
## 8. 迁移原则

本次迁移采用保守策略：

1. 现有 Intent 实例 1:1 迁移为 WorkArea。
2. 现有 Task 每个生成一个对应 TaskPlan，避免推断历史任务之间不存在的依赖关系。
3. 原 `source_intent` 不迁移为 Task 字段；Task 只通过 `taskplan` 归属任务计划，工作域从 `TaskPlan.workarea` 追溯。
4. 新增 `taskplan` 字段，使每个 Task 明确归属任务计划。
5. 旧 `parent_task` / `sub_tasks` 从 Task 主模型移出；未来需要叶子拆解时使用独立 SubTask。
6. 旧文档或历史记录中的 Intent 表述不强行重写为新事实；当前规范、事实源、校验、CLI 和 Web 应完成同步。

---
## 9. 落地顺序

本参考文档建立后，实施顺序为：

1. 更新工作模型集合索引；
2. 将 Intent 规范改为 WorkArea 规范；
3. 新增 TaskPlan 规范；
4. 更新 Task 规范；
5. 新增 SubTask 规范；
6. 更新字段格式、基础规范、Web 规范等关联规范；
7. 迁移 `ldvh-base` 实例；
8. 更新 fact validator、fact CLI、测试和 Web；
9. 运行事实校验、单元测试和 Web 检查。
