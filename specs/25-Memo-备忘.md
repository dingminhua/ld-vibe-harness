# Memo 备忘

> 创建日期：2026-06-04
> 定位：定义 Memo 备忘事实模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理尚未任务化但有保留价值的输入、发现和提醒的项目
> 上位依据：`specs/13-LDVH事实模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`、`specs/20-事实模型集合索引.md`

---

---

## 1. 本文解决的问题

本文定义 Memo 备忘事实模型。Memo 承载尚未任务化但有保留价值的输入、发现和提醒，避免误创建 Task 或 ADR。

本文只定义 Memo 对象模型。Memo 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践可按需由 §12 附件型实践子文档承接。

本文是精简版规范，只包含核心章节。13 §4.2 中未展开的章节标注于 §10 待补齐事项。

---

## 2. 与 13 的关系

`specs/13-LDVH事实模型基础规范.md` 定义事实模型通用规则、文件命名、附件型实践子文档命名和事实模型标准组成。本文依据 13 §4.2 定义 Memo 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 Memo 定义

Memo 承载尚未任务化但有保留价值的输入、发现和提醒，避免误创建 Task 或 ADR。Memo 应记录内容描述、来源、分类和关联对象。

Memo 不是所有信息的默认归宿。AI 可以在当前上下文中直接处理简单信息，但只有满足准入条件、需要跨会话保留或需要分流追踪的信息，才应进入 Memo 事实源。

### 3.2 Memo 与临时信息

临时信息是对话过程中的简单问答、一次性确认或即时处理的内容，不默认成为 Memo。临时信息可以保留在当前执行上下文中。

一个 Memo 至少应具备：

1. 明确的内容描述；
2. 明确的来源；
3. 明确的分类；
4. 可追溯的状态。

### 3.3 Memo 准入条件

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

## 4. 事实源边界

本文是 Memo 备忘事实模型的权威事实源。本文定义 Memo 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Memo 对象实例的权威事实源位置为：

```text
ldvh-base/memos/memo-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Memo 对象模型 | `specs/25-Memo-备忘.md` |
| Memo 对象实例 | `ldvh-base/memos/` |
| Memo 契约子文档 | `specs/25.06-Contract.md` |
| Memo 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

Memo 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `draft` | 已记录，待确认 |
| `active` | 已确认，可作为参考 |
| `resolved` | 已分流到 Task/ADR/其他对象或已失效 |
| `archived` | 已归档，不再活跃但保留历史 |

### 5.2 合法状态流转

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

### 5.3 关闭条件

Memo 没有"关闭"概念，只有"已分流"或"已归档"。

Memo 从 `active` → `resolved` 必须满足：

1. `resolved_to` 字段已填写，指向有效的 Task、ADR 或其他对象 ID；
2. 已获得 Human Gate 确认。

---

## 6. 与其他对象的关系

### 6.1 Memo → Task

Memo 可分流为 Task，作为尚未任务化信息转化为可执行工作单元的路径。

Memo 分流为 Task 后，Memo 的 `resolved_to` 字段应记录 Task ID。Task 的 `source` 字段可记录 Memo ID。Task 的字段和状态由 Task 对象模型（`specs/27-Task-任务.md`）定义。

### 6.2 Memo → ADR

Memo 可分流为 ADR，作为临时判断或偏好转化为长期决策的路径。

Memo 分流为 ADR 后，Memo 的 `resolved_to` 字段应记录 ADR ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策记录.md`）定义。

### 6.3 Memo → Intent

Memo 可升级为 Intent，作为待讨论事项转化为明确意图的路径。

Memo 升级为 Intent 后，Memo 的 `resolved_to` 字段应记录 Intent ID。Intent 的字段和状态由 Intent 对象模型（`specs/24-Intent-意图.md`）定义。

### 6.4 Memo → Change

Memo 的创建、状态变更和分流都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更记录.md`）。

---

## 7. Human Gate

以下场景必须触发 Human Gate：

1. 状态从 `draft` → `active` 时确认；
2. 状态从 `active` → `resolved` 时确认分流目标；
3. 高风险操作前确认（修改 specs、Rules、ADR、ldvh-base/ 等事实源）。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/11-LDVH-Trae-Solo-环境规范.md` §9）。

---

## 8. 字段契约

### 8.1 基础字段

Memo 基础字段遵循 `specs/13-LDVH事实模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Memo 对象 ID，格式为 `memo-{NNNN}` |
| `type` | string | 是 | 固定为 `memo` |
| `title` | string | 是 | 备忘标题 |
| `status` | string | 是 | Memo 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 8.2 扩展字段

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

字段约束和完整 YAML 示例详见 `specs/25.06-Contract.md`。

---

## 9. 事实源回写要求

1. 创建 Memo 时应记录 Change（依据 `specs/22-Change-变更记录.md`）；
2. Memo 状态变更时应记录 Change；
3. Memo 分流为 Task、ADR 或 Intent 时应更新 `resolved_to` 字段并记录 Change；
4. Memo 关联 Task、ADR、Evidence 时应更新对应字段并记录 Change；
5. Memo 实例写入 `ldvh-base/memos/` 目录后，应确保文件命名符合 `memo-{NNNN}-short-title.yaml` 格式。

---

## 10. 待补齐事项

以下章节依据 `specs/13-LDVH事实模型基础规范.md` §4.2 应定义但本文未展开，待后续阶段补齐：

| 13 §4.2 编号 | 章节名称 | 计划补齐阶段 |
|---|---|---|
| 8 | 证据留存要求 | Phase 3 |
| 9 | AI 协作适配 | Phase 4 |
| 10 | Tools 契约式校验与执行适配 | Phase 3（Contract 子文档先行） |
| 11 | Web 信息同步适配 | Phase 5 |
| 12 | 附件型实践子文档按需拆分规则 | Phase 4 |
| 13 | 落地前决策 | Phase 4 |
| 14 | 价值与要素审查 | Phase 4 |
| 15 | 落地初始化 | Phase 4 |
| 16 | 落地审计 | Phase 5 |
| 17 | 合规检查 | Phase 5 |
