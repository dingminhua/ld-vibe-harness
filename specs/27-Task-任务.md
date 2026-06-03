# Task 任务

> 创建日期：2026-06-03
> 定位：定义 Task 任务事实模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理 AI 可执行工作单元的项目
> 上位依据：`specs/13-LDVH事实模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-Specs文档规范.md`、`specs/04-LDVH模型子文档规范.md`、`specs/10-事实源边界与承载规范.md`、`specs/20-事实模型集合索引.md`

---

---

## 1. 本文解决的问题

本文定义 Task 任务事实模型。Task 是 AI 可执行的工作单元，有明确验收标准和回写目标，用于承载从 Intent 拆解或用户直接指示的具体工作。

本文只定义 Task 对象模型。Task 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践可按需由 §12 附件型实践子文档承接。

本文是精简版规范，只包含核心章节。13 §4.2 中未展开的章节标注于 §10 待补齐事项。

---

## 2. 与 13 的关系

`specs/13-LDVH事实模型基础规范.md` 定义事实模型通用规则、文件命名、附件型实践子文档命名和事实模型标准组成。本文依据 13 §4.2 定义 Task 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 Task 定义

Task 是 AI 可执行的工作单元，有明确验收标准和回写目标。Task 应记录目标、验收标准、验证方式、来源和关联对象。

Task 不是所有工作的默认归宿。AI 可以在当前上下文中直接处理简单操作，但只有满足准入条件、需要跨会话追踪或需要验收确认的工作，才应进入 Task 事实源。

### 3.2 Task 与临时工作

临时工作是执行过程中的简单操作、一次性调整或局部修改，不默认成为 Task。临时工作可以保留在当前执行上下文中。

一个 Task 至少应具备：

1. 明确的目标描述；
2. 可验证的验收标准；
3. 明确的来源（Intent 或用户直接指示）；
4. 可追溯的状态。

### 3.3 Task 准入条件

当一个工作单元满足以下条件之一时，应考虑形成 Task：

1. 有明确目标；
2. 有可验证的验收标准；
3. 有来源（Intent 或用户直接指示）；
4. 可在单次或有限次执行轮次内完成。

不满足 Task 准入条件的临时工作，可以直接在当前上下文中执行。

以下内容通常不应单独形成 Task：

1. 当前上下文中的简单操作；
2. 无明确验收标准的探索性工作；
3. 不影响其他对象的局部调整；
4. 已由现有 Task 完全覆盖的重复工作。

AI 不得因为用户提出了任何请求就自动创建 Task。只有满足准入条件的工作单元，才应写入 Task 事实源。

---

## 4. 事实源边界

本文是 Task 任务事实模型的权威事实源。本文定义 Task 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Task 对象实例的权威事实源位置为：

```text
ldvh-base/tasks/task-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Task 对象模型 | `specs/27-Task-任务.md` |
| Task 对象实例 | `ldvh-base/tasks/` |
| Task 契约子文档 | `specs/27.06-Contract.md` |
| Task 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

Task 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `planned` | 已拆解，待执行 |
| `executing` | 正在执行 |
| `review_needed` | 执行完成，待审查 |
| `closed` | 审查通过，已关闭 |

### 5.2 合法状态流转

```text
planned → executing
executing → review_needed
review_needed → closed
review_needed → executing（退回：审查不通过）
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`closed` 是稳定终态。终态 Task 不得重开；如需重新执行，必须新建 Task 承接，并在新 Task 中引用原 Task。

`review_needed` 状态的 Task 退回到 `executing` 时，应记录退回原因，并更新 `updated` 字段。

### 5.3 关闭条件

Task 从 `review_needed` → `closed` 必须满足：

1. `closure_evidence` 字段已填写；
2. 关联 Evidence 的 `verification_result` 不为 `fail`（如有）；
3. 已获得 Human Gate 确认。

---

## 6. 与其他对象的关系

### 6.1 Task → Intent

Task 可关联一个 Intent，作为该 Intent 的执行单元。

创建 Task 后，关联 Intent 的 `related_tasks` 字段应记录 Task ID。Intent 的字段和状态由 Intent 对象模型（`specs/24-Intent-意图.md`）定义。

### 6.2 Task → ADR

Task 可关联多个 ADR，作为执行过程中涉及的决策参考。

创建 Task 后，关联 ADR 的 `related_objects` 字段应记录 Task ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策记录.md`）定义。

### 6.3 Task → Evidence

Task 可关联多个 Evidence，作为验证结果和关闭证据。

创建 Evidence 后，关联 Task 的 `related_evidence` 字段应记录 Evidence ID。Evidence 的字段和状态由 Evidence 对象模型（`specs/29-Evidence-验证证据.md`）定义。

### 6.4 Task → Change

Task 的创建、状态变更和关闭都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更记录.md`）。

### 6.5 Task → TaskSet

Task 应归属一个 TaskSet。Task 的 `taskset` 字段引用所属 TaskSet ID。创建 Task 时，AI 应优先自动归入现有活跃 TaskSet；无法归入时，应提示用户是否创建新 TaskSet。TaskSet 的字段和状态由 TaskSet 对象模型（`specs/28-TaskSet-任务集.md`）定义。

---

## 7. Human Gate

以下场景必须触发 Human Gate：

1. 状态从 `executing` → `review_needed` 时确认；
2. 状态从 `review_needed` → `closed` 时确认；
3. 高风险操作前确认（修改 specs、Rules、ADR、ldvh-base/ 等事实源）。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo AskUserQuestion使用规范.md`）。

---

## 8. 字段契约

### 8.1 基础字段

Task 基础字段遵循 `specs/13-LDVH事实模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Task 对象 ID，格式为 `task-{NNNN}` |
| `type` | string | 是 | 固定为 `task` |
| `title` | string | 是 | 任务标题 |
| `status` | string | 是 | Task 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 8.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `description` | string | 是 | 任务详细描述 |
| `source_intent` | string | 否 | 关联 Intent ID |
| `source` | string | 是 | 来源（Intent ID 或用户直接指示） |
| `taskset` | string | 否 | 所属 TaskSet ID，引用 TaskSet 事实模型 |
| `acceptance` | string | 是 | 验收标准 |
| `verification` | string | 否 | 验证方式 |
| `assignee` | string | 否 | 执行者 |
| `related_adrs` | list of string | 否 | 关联 ADR ID 列表 |
| `related_evidence` | list of string | 否 | 关联 Evidence ID 列表 |
| `related_changes` | list of string | 否 | 关联 Change ID 列表 |
| `closed_at` | date | 条件必填 | 仅当 `status` 为 `closed` 时必须填写 |
| `closure_evidence` | string | 条件必填 | 仅当 `status` 为 `closed` 时必须填写，关闭证据摘要 |

字段约束和完整 YAML 示例详见 `specs/27.06-Contract.md`。

---

## 9. 事实源回写要求

1. 创建 Task 时应记录 Change（依据 `specs/22-Change-变更记录.md`）；
2. Task 状态变更时应记录 Change；
3. Task 关联 Intent、ADR、Evidence 时应更新对应字段并记录 Change；
4. Task 关闭时必须填写 `closure_evidence` 字段；
5. Task 实例写入 `ldvh-base/tasks/` 目录后，应确保文件命名符合 `task-{NNNN}-short-title.yaml` 格式。

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
