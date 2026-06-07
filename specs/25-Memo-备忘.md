# Memo 备忘

> 创建日期：2026-06-04
> 定位：定义 Memo 备忘工作模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理尚未任务化但有保留价值的输入、发现和提醒的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档基础规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`

---

## 1. 对象定位与准入条件

本文定义 Memo 备忘工作模型。Memo 承载尚未任务化但有保留价值的输入、发现和提醒，避免误创建 Task 或 ADR。

### 1.1 Memo 定义

Memo 承载尚未任务化但有保留价值的输入、发现和提醒，避免误创建 Task 或 ADR。Memo 应记录内容描述、来源、分类和关联对象。

Memo 不是所有信息的默认归宿。AI 可以在当前上下文中直接处理简单信息，但只有满足准入条件、需要跨会话保留或需要分流追踪的信息，才应进入 Memo 事实源。

### 1.2 Memo 与临时信息

临时信息是对话过程中的简单问答、一次性确认或即时处理的内容，不默认成为 Memo。临时信息可以保留在当前执行上下文中。

一个 Memo 至少应具备：

1. 明确的内容描述；
2. 明确的来源；
3. 明确的分类；
4. 可追溯的状态。

### 1.3 Memo 准入条件

当一个信息单元满足以下条件之一时，应考虑形成 Memo：

1. 有保留价值但尚未任务化的发现、输入或提醒；
2. 不满足 Task 准入条件（无明确验收标准或执行目标）但有记录价值；
3. 不满足 ADR 准入条件（非长期决策）但需要保留的临时判断或偏好；
4. 执行过程中发现的问题、缺口或待讨论事项，尚未决定如何处理。

不满足 Memo 准入条件的临时信息，可以直接在当前上下文中处理。

以下内容通常不应单独形成 Memo：

1. 可以在当前对话中直接处理的信息；
2. 已有明确目标和验收标准的工作（应创建 Task）；
3. 需要长期追踪的决策（应创建 ADR）；
4. 纯粹的聊天或闲聊。

AI 不得因为用户提出了任何信息就自动创建 Memo。只有满足准入条件的信息单元，才应写入 Memo 事实源。

---

## 2. 事实源边界

本文是 Memo 备忘工作模型的权威事实源。本文定义 Memo 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Memo 对象实例的权威事实源位置为：

```text
ldvh-base/memos/memo-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Memo 对象模型 | `specs/25-Memo-备忘.md` |
| Memo 对象实例 | `ldvh-base/memos/` |
| Memo 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 3. 状态机

### 3.1 标准状态

Memo 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `draft` | 已记录，待确认 |
| `active` | 已确认，可作为参考 |
| `resolved` | 已分流到 Task/ADR/其他对象或已失效 |
| `archived` | 已归档，不再活跃但保留历史 |

### 3.2 合法状态流转

```text
draft → active
draft → archived（直接归档：记录后判断不需要保留）
active → resolved（分流到具体对象）
active → archived（不再需要但保留）
resolved → archived
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`archived` 是稳定终态。终态 Memo 不得重开；如需重新激活，必须新建 Memo 承接，并在新 Memo 中引用原 Memo。

`resolved` 状态的 Memo 必须填写 `resolved_to` 字段，记录分流目标对象 ID。

### 3.3 关闭条件

Memo 没有"关闭"概念，只有"已分流"或"已归档"。

Memo 从 `active` → `resolved` 必须满足：

1. `resolved_to` 字段已填写，指向有效的 Task、ADR 或其他对象 ID；
2. 已获得 Human Gate 确认。

---

## 4. 与其他对象的关系

### 4.1 Memo → Task

Memo 可分流为 Task，作为尚未任务化信息转化为可执行工作单元的路径。

Memo 分流为 Task 后，Memo 的 `resolved_to` 字段应记录 Task ID。Task 的 `source` 字段可记录 Memo ID。Task 的字段和状态由 Task 对象模型（`specs/27-Task-任务.md`）定义。

### 4.2 Memo → ADR

Memo 可分流为 ADR，作为临时判断或偏好转化为长期决策的路径。

Memo 分流为 ADR 后，Memo 的 `resolved_to` 字段应记录 ADR ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策.md`）定义。

### 4.3 Memo → Intent

Memo 可升级为 Intent，作为待讨论事项转化为明确意图的路径。

Memo 升级为 Intent 后，Memo 的 `resolved_to` 字段应记录 Intent ID。Intent 的字段和状态由 Intent 对象模型（`specs/24-Intent-意图.md`）定义。

### 4.4 Memo → Change

Memo 的创建、状态变更和分流都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更.md`）。

---

## 5. Human Gate

以下场景必须触发 Human Gate：

1. 状态从 `draft` → `active` 时确认；
2. 状态从 `active` → `resolved` 时确认分流目标；
3. 高风险操作前确认（修改 specs、Rules、ADR、ldvh-base/ 等事实源）。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo环境规范.md` §9）。

---

## 6. 字段契约

### 6.1 基础字段

Memo 基础字段遵循 `specs/07-工作模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Memo 对象 ID，格式为 `memo-{NNNN}` |
| `type` | string | 是 | 固定为 `memo` |
| `title` | string | 是 | 备忘标题 |
| `status` | string | 是 | Memo 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 6.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `description` | string | 是 | 备忘详细描述 |
| `source` | string | 是 | 来源 |
| `category` | string | 是 | 分类：`discovery`/`reminder`/`question`/`gap`/`preference` |
| `priority` | string | 否 | 优先级：`low`/`medium`/`high`，默认 `low` |
| `resolved_to` | string | 条件必填 | 仅当 `status` 为 `resolved` 时必须填写，分流目标对象 ID |
| `resolved_at` | date | 条件必填 | 仅当 `status` 为 `resolved` 时必须填写 |
| `related_tasks` | list of string | 否 | 关联 Task ID 列表 |
| `related_adrs` | list of string | 否 | 关联 ADR ID 列表 |
| `related_docs` | list of string | 否 | 关联文档路径列表，存放与备忘相关的文档路径（相对项目根或绝对路径） |

字段约束和完整 YAML 示例已回并到本文。

### 6.3 完整 YAML 示例

```yaml
id: memo-0001
type: memo
title: 规范文档中缺少错误处理章节
status: resolved
created: 2026-06-04
updated: 2026-06-04
description: 在审查 specs/07 时发现缺少错误处理和异常场景的统一规范，需要后续补充
source: 执行 task-0003 过程中的发现
category: gap
priority: medium
resolved_to: task-0012
resolved_at: 2026-06-04
related_tasks:
  - task-0003
related_adrs: []
related_docs: []
```

### 6.4 字段约束

1. `status` 必须属于 Memo 标准状态枚举：`draft`、`active`、`resolved`、`archived`；
2. `type` 必须固定为 `memo`；
3. `category` 必须属于分类枚举：`discovery`、`reminder`、`question`、`gap`、`preference`；
4. `priority` 必须属于优先级枚举：`low`、`medium`、`high`；未填写时默认为 `low`；
5. `resolved_to` 仅在 `status: resolved` 时必填，其他状态下不得填写；
6. `resolved_at` 仅在 `status: resolved` 时必填，其他状态下不得填写；
7. `resolved_to` 应引用已存在的工作模型 ID，引用无效时应标记为校验警告；
8. `related_tasks` 和 `related_adrs` 应引用已存在的工作模型 ID，引用无效时应标记为校验警告；
9. `id` 格式必须为 `memo-{NNNN}`，编号固定 4 位，从 `0001` 起递增；
10. `created`、`updated` 和 `resolved_at` 使用 ISO 8601 日期格式（`YYYY-MM-DD`）；
11. `related_tasks`、`related_adrs`、`related_docs` 为列表类型，可为空列表，不得省略字段后以 null 替代空列表；
12. `related_docs` 存放文档路径，推荐使用相对项目根路径，路径不存在时应标记为校验警告；

### 6.5 文件命名契约

Memo 实例文件命名规则为 `memo-{NNNN}-short-title.yaml`。编号从 `0001` 起递增，固定 4 位；英文短标题使用小写短横线命名；每个项目独立编号，不使用跨项目全局编号；文件存放位置为 `ldvh-base/memos/`；文件名变化必须同步检查所有引用该 Memo 的 `related_tasks`、`related_adrs` 和其他关联字段。

### 6.6 状态流转契约

| 当前状态 | 可流转至 |
|---|---|
| `draft` | `active`, `archived` |
| `active` | `resolved`, `archived` |
| `resolved` | `archived` |
| `archived` | 无 |

`draft` → `archived` 为直接归档流转，表示记录后判断不需要保留。`active` → `resolved` 为分流流转，必须填写 `resolved_to` 字段。

### 6.7 契约消费与检查项

1. Tools 辅助程序解析 Memo 时应依据本文定义的 YAML schema 和字段约束，不得自行扩张格式契约；
2. Tools 辅助程序校验 Memo 时应覆盖字段完整性、状态合法性、条件必填和引用有效性；
3. Tools 辅助程序读取 Memo 时可依据本文状态枚举和字段契约执行状态筛选、详情解析和关联字段解析，但 Memo 读取结果是否可作为当前执行依据由本文和 Skill 流程判断；
4. 实践子文档和工具可以消费本文契约，但不得复制维护契约字段第二事实源；
5. 修改本文契约属于规范变更，应评估 Human Gate 并记录 Change（依据 `specs/22-Change-变更.md`）；
6. Memo YAML 实例字段完整性、`status`、`type`、分类、优先级、分流字段、关联引用、文件命名、状态流转和终态重开情况均属于契约检查项。

---

## 7. 事实源回写与证据留存

### 7.1 事实源回写

1. 创建 Memo 时应记录 Change（依据 `specs/22-Change-变更.md`）；
2. Memo 状态变更时应记录 Change；
3. Memo 分流为 Task、ADR 或 Intent 时应更新 `resolved_to` 字段并记录 Change；
4. Memo 关联 Task、ADR、Evidence 时应更新对应字段并记录 Change；
5. Memo 实例写入 `ldvh-base/memos/` 目录后，应确保文件命名符合 `memo-{NNNN}-short-title.yaml` 格式。

### 7.2 证据留存

证据留存通用规则引用 `specs/07-工作模型基础规范.md` §7.4。Memo 对象特有差异：

1. Memo 分流（`resolved`）时，应留存分流依据（如分流目标对象的 ID 和分流原因）；
2. Memo 归档（`archived`）时，应留存归档原因和确认记录。

---

## 8. 适配规则

### 8.1 AI 协作

AI 协作通用规则引用 `specs/07-工作模型基础规范.md` §7.5。Memo 对象特有差异：

1. AI 发现有保留价值但未任务化信息时，应判断是否满足 Memo 准入条件（§1.3）；
2. 创建 Memo 前必须通过 Human Gate 确认（§5）。

### 8.2 Tools 辅助

Tools 辅助通用规则引用 `specs/07-工作模型基础规范.md` §7.6。当前由通用 Fact Validator 消费本文结构化契约完成校验，对象级 Tools 实践待按需创建。

### 8.3 Web 信息同步

Web 信息同步通用规则引用 `specs/07-工作模型基础规范.md` §7.7。当前未实现对象级 Web 实践，待后续统一适配。

---

## 9. 待补齐事项

1. Memo YAML schema 的 JSON Schema 表达待 Tools 实现稳定后补齐；
2. `resolved_to`、`related_tasks`、`related_adrs` 的引用校验规则待对应对象模型稳定后补充；
3. `category` 枚举是否需要扩展待 Memo 实践积累后确定。
