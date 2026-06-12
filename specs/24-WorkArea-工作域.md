# WorkArea-工作域

> 创建日期：2026-06-12
> 定位：定义 WorkArea / 工作域工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写和适配规则
> 适用范围：所有接入 LDVH 且需要长期管理工作范围、系统领域、治理域或产品域的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/02-术语规范.md`、`specs/03.03-工作模型文档规范.md`、`specs/05.01-工作字段内容格式规范.md`、`specs/07-Code确定性执行实现规范.md`、`specs/08-Web信息同步实现规范.md`、`specs/09-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`、`specs/27-TaskPlan-任务计划.md`

---
## 1. 对象定位与准入条件

WorkArea / 工作域是长期存在的工作范围事实，用于承载一个项目中的系统领域、治理范围、产品方向、能力区或持续维护面。工作域回答“这一类工作属于哪里”，不回答“一次目标是否已经完成”。

工作域是上游长期范围对象。一次性目标、阶段性目标、任务序列和关闭判断应由 TaskPlan / 任务计划承载，不应由工作域承载。

### 1.1 工作域准入条件

一个范围满足以下条件之一时，应考虑形成工作域：

1. 需要长期沉淀上下文、约束、相关任务计划和历史决策；
2. 后续会持续产生多个任务计划；
3. 代表系统、产品、规范、Code 工具、Web、规范规则、流程或治理的稳定范围；
4. 不结构化会导致任务计划缺少上游范围或上下文归属；
5. 需要在 Web、Code 工具或规范中作为长期筛选和聚合维度。

### 1.2 不应形成工作域的内容

以下内容不应形成工作域：

1. 一次性目标；
2. 一组为了完成同一目标而拆出的任务；
3. 当前对话即可完成的小工作；
4. 只有验收标准、关闭证据或执行步骤的事项；
5. 已由现有工作域覆盖的重复范围。

上述内容应进入 TaskPlan、Task、SubTask、Memo、ADR、docs 或当前对话上下文。

---
## 2. 事实源边界

本文是工作域工作模型的权威规范。

工作域实例的权威事实源位置为：

```text
ldvh-base/workareas/workarea-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号。

| 内容 | 权威位置 |
|---|---|
| 工作域工作模型规范 | `specs/24-WorkArea-工作域.md` |
| 工作域实例 | `ldvh-base/workareas/` |
| 工作域字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| 工作域展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

---
## 3. 状态机

### 3.1 标准状态

工作域标准状态如下：

| 状态 | 含义 |
|---|---|
| `active` | 当前有效，可承载新的任务计划 |
| `archived` | 暂不作为当前工作范围使用，但历史事实保留 |

工作域没有 `completed`、`review_needed` 或 `closed`。工作域被重新启用时，应从 `archived` 回到 `active`，不是重开完成态。

### 3.2 合法状态流转

```text
active -> archived
archived -> active
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` -> `archived` | 该范围暂不再承载新的任务计划 | 应填写 `archive_reason` |
| `archived` -> `active` | 该范围重新进入当前工作 | 应记录恢复原因 |

---
## 4. 对象关系

### 4.1 工作域与任务计划

工作域通过 TaskPlan 的 `workarea` 字段被引用。任务计划必须归属一个工作域。

规则如下：

1. 工作域不直接管理 Task 或 SubTask；
2. 工作域不保存任务序列、执行步骤或关闭证据；
3. 工作域可以通过派生展示聚合其下任务计划的状态、产物和风险；
4. 任务计划关闭后不改变工作域状态；
5. 一个工作域可以长期产生多个任务计划。

### 4.2 工作域与 ADR、Memo、Pitfall

ADR、Memo、Pitfall 可以引用工作域，用于表达某条决策、备忘或踩坑经验适用于哪个长期范围。具体字段由对应对象规范定义。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除、重命名工作域；
2. 将临时讨论、未建模意图或范围判断升级为工作域；
3. 将工作域归档或恢复；
4. 改写工作域的范围、约束或长期上下文；
5. 合并或拆分工作域；
6. 将一次性目标误挂为工作域时进行纠偏。

工作域的 Human Gate 关注范围边界和长期上下文，不承接具体执行验收。

---
## 6. 字段契约

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 工作域 ID，格式为 `workarea-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `workarea` | Reference | AI、Code、Web |
| `title` | 工作域标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建时间 | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | 最近更新时间 | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `description` | 工作域背景、范围和长期上下文 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `scope` | 范围边界、包含和不包含的事项 | string | 否 | 高影响工作域应填写 | Narrative / Checklist | AI、Human |
| `constraints` | 长期约束、偏好和禁止事项 | string | 否 | 可为空 | Narrative / Checklist | AI、Human |
| `source` | 来源 | string | 是 | 谁在什么场景下确认 | Reference / Narrative | AI、Web |
| `related_docs` | 关联文档路径列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联 ADR ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 关联 Memo ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联 Pitfall ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加 | Log | AI、Code |
| `archive_reason` | 归档原因 | string | 条件必填 | `status: archived` 时必须填写 | Narrative | AI、Code、Web |

### 6.1 YAML 示例

```yaml
id: workarea-0001
type: workarea
title: Web 展示管理
status: active
created: '2026-06-12T00:00:00'
updated: '2026-06-12T00:00:00'
description: |
  承载 LDVH Web 展示、对象阅读、状态展示和管理后台体验相关的长期工作。
scope: |
  - 包含 Web 信息同步、对象详情、列表视图和阅读体验
  - 不直接承载单次功能实现的验收和关闭证据
constraints: |
  - 工作域不作为完成对象
source: 用户确认工作域模型
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
```

---
## 7. 事实源回写与证据留存

工作域变化应回写 YAML 实例。因某个任务计划完成而产生的执行证据、验证证据或关闭判断，不得回写为工作域完成证据。

---
## 8. 适配规则

Code 应检查：

1. 文件名、ID、type、status 合法；
2. `archived` 状态必须提供 `archive_reason`；
3. 工作域不出现任务计划、任务或子任务的执行状态字段；
4. 引用字段格式和路径存在性。

Web 应显示工作域列表和详情，但不得把工作域展示为“待关闭”对象。

---
## 9. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 工作域必须遵守 05、20 和本文定义的长期范围边界 | 05、20、本文、Human Gate | 工作模型治理 | 创建、迁移、归档或恢复工作域时 |
| 确定性执行要求 | 工作域不得承载一次性目标完成判断 | Validator、Web 展示、任务计划规范 | 事实模型校验 | 工作域字段或状态变化时 |
| 生命周期触发要求 | 工作域规范变化后应检查 TaskPlan、Task、Code、Web 和事实实例 | Code 测试、Web 检查、事实校验 | 触发保障 | 字段、状态或事实源路径变化时 |

---
## 10. 检查要求

工作域检查至少包括：

| 检查项 | 标准 |
|---|---|
| 命名 | 只使用 WorkArea / 工作域 |
| 状态 | 仅允许 `active`、`archived` |
| 关系 | 不直接挂 Task 或 SubTask |
| 归档 | archived 必须说明原因 |
| UI | 不显示 Intent、意图、模块等别名 |

---
## 11. 待补齐事项

暂无额外待补齐事项；后续随字段契约、Code 校验或 Web 消费变化更新。
