# TaskSet 任务集

> 创建日期：2026-06-04
> 定位：定义 TaskSet 任务集事实模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理 AI 可执行工作单元归类的项目
> 上位依据：`specs/13-LDVH事实模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-Specs文档规范.md`、`specs/04-LDVH模型子文档规范.md`、`specs/10-事实源边界与承载规范.md`、`specs/20-事实模型集合索引.md`

---

---

## 1. 本文解决的问题

本文定义 TaskSet 任务集事实模型。TaskSet 承载同一目标、主题、阶段或治理域下的一组 Task，帮助 AI 自动归类任务并展示主线。所有 Task 应归属一个 TaskSet；找不到合适 TaskSet 时，AI 应提示创建。

本文只定义 TaskSet 对象模型。TaskSet 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践可按需由 §12 附件型实践子文档承接。

本文是精简版规范，只包含核心章节。13 §4.2 中未展开的章节标注于 §10 待补齐事项。

---

## 2. 与 13 的关系

`specs/13-LDVH事实模型基础规范.md` 定义事实模型通用规则、文件命名、附件型实践子文档命名和事实模型标准组成。本文依据 13 §4.2 定义 TaskSet 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 TaskSet 定义

TaskSet 承载同一目标、主题、阶段或治理域下的一组 Task，帮助 AI 自动归类任务并展示主线。TaskSet 应记录范围、背景、关联对象和包含的 Task 列表。

TaskSet 不是所有 Task 的默认归宿。AI 可以在当前上下文中直接处理不需要归类的 Task，但只有满足准入条件、需要组织一组相关 Task 时，才应进入 TaskSet 事实源。

### 3.2 TaskSet 与临时工作集合

临时工作集合是执行过程中的临时分组、一次性聚合或无明确主题的集合，不默认成为 TaskSet。临时工作集合可以保留在当前执行上下文中。

一个 TaskSet 至少应具备：

1. 明确的目标或主题；
2. 可界定的范围描述；
3. 包含一个或多个 Task（创建时可为空，但应预期会包含 Task）；
4. 可追溯的状态。

### 3.3 TaskSet 准入条件

当满足以下条件之一时，应考虑形成 TaskSet：

1. 有同一目标或主题的一组 Task 需要组织；
2. AI 创建 Task 时无法归入现有 TaskSet；
3. 用户要求创建任务集来管理一组相关任务；
4. 项目治理需要一个任务集来承载治理域下的所有 Task。

以下内容通常不应单独形成 TaskSet：

1. 单个独立 Task（不需要归入任务集时，AI 应提示创建默认任务集）；
2. 临时工作集合（无明确目标或主题）。

AI 不得因为用户提出了任何请求就自动创建 TaskSet。只有满足准入条件的任务集合，才应写入 TaskSet 事实源。

### 3.4 自动归类规则

AI 创建 Task 时应优先自动归入现有活跃 TaskSet；无法归入时，应提示用户是否创建新 TaskSet 或归入默认 TaskSet。

---

## 4. 事实源边界

本文是 TaskSet 任务集事实模型的权威事实源。本文定义 TaskSet 的准入条件、状态机、对象关系、Human Gate 和字段契约。

TaskSet 对象实例的权威事实源位置为：

```text
ldvh-base/tasksets/taskset-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| TaskSet 对象模型 | `specs/28-TaskSet-任务集.md` |
| TaskSet 对象实例 | `ldvh-base/tasksets/` |
| TaskSet 契约子文档 | `specs/28.06-Contract.md` |
| TaskSet 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

TaskSet 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `planned` | 已规划，待启动 |
| `active` | 进行中 |
| `review_needed` | 待审查是否可以关闭 |
| `closed` | 已关闭 |

### 5.2 合法状态流转

```text
planned → active
active → review_needed
review_needed → closed
review_needed → active（退回：仍有未完成 Task）
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`closed` 是稳定终态。终态 TaskSet 不得重开；如需重新执行，必须新建 TaskSet 承接，并在新 TaskSet 中引用原 TaskSet。

`review_needed` 状态的 TaskSet 退回到 `active` 时，应记录退回原因，并更新 `updated` 字段。

### 5.3 关闭条件

TaskSet 从 `review_needed` → `closed` 必须满足：

1. 所有关联 Task 已关闭或已分流到其他 TaskSet；
2. 已获得 Human Gate 确认。

---

## 6. 与其他对象的关系

### 6.1 TaskSet → Task

TaskSet 包含多个 Task，通过 `tasks` 字段记录关联 Task ID 列表。

创建 TaskSet 后，关联 Task 的 `taskset` 字段应记录 TaskSet ID。Task 的字段和状态由 Task 对象模型（`specs/27-Task-任务.md`）定义。

### 6.2 TaskSet → Intent

TaskSet 可关联一个 Intent，作为该 Intent 的任务集合。

创建 TaskSet 后，关联 Intent 的相关字段应记录 TaskSet ID。Intent 的字段和状态由 Intent 对象模型（`specs/24-Intent-意图.md`）定义。

### 6.3 TaskSet → ADR

TaskSet 可关联多个 ADR，作为执行过程中涉及的决策参考。

创建 TaskSet 后，关联 ADR 的 `related_objects` 字段应记录 TaskSet ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策记录.md`）定义。

### 6.4 TaskSet → Evidence

TaskSet 可关联 Evidence，作为整体验证。

创建 Evidence 后，关联 TaskSet 的 `related_evidence` 字段应记录 Evidence ID。Evidence 的字段和状态由 Evidence 对象模型（`specs/29-Evidence-验证证据.md`）定义。

### 6.5 TaskSet → Profile

TaskSet 可关联项目 Profile，标识任务集所属项目治理域。

Profile 的字段和状态由 Profile 对象模型定义。

### 6.6 TaskSet → Change

TaskSet 的创建、状态变更和关闭都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更记录.md`）。

---

## 7. Human Gate

以下场景必须触发 Human Gate：

1. 创建 TaskSet 时确认；
2. 状态从 `active` → `review_needed` 时确认；
3. 状态从 `review_needed` → `closed` 时确认；
4. 将 Task 移入/移出 TaskSet 时确认（如果影响关闭条件）。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo AskUserQuestion使用规范.md`）。

---

## 8. 字段契约

### 8.1 基础字段

TaskSet 基础字段遵循 `specs/13-LDVH事实模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | TaskSet 对象 ID，格式为 `taskset-{NNNN}` |
| `type` | string | 是 | 固定为 `taskset` |
| `title` | string | 是 | 任务集标题 |
| `status` | string | 是 | TaskSet 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 8.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `description` | string | 是 | 任务集详细描述 |
| `scope` | string | 是 | 任务集范围描述 |
| `background_doc` | string | 否 | 背景文档路径，指向描述任务集背景、目标和约束的 Markdown 文件 |
| `source_intent` | string | 否 | 关联 Intent ID |
| `related_profile` | string | 否 | 关联 Profile ID |
| `tasks` | list of string | 是 | 关联 Task ID 列表，默认空列表 |
| `related_adrs` | list of string | 否 | 关联 ADR ID 列表 |
| `related_evidence` | list of string | 否 | 关联 Evidence ID 列表 |
| `closed_at` | date | 条件必填 | 仅当 `status` 为 `closed` 时必须填写 |
| `closure_evidence` | string | 条件必填 | 仅当 `status` 为 `closed` 时必须填写，关闭证据摘要 |

字段约束和完整 YAML 示例详见 `specs/28.06-Contract.md`。

---

## 9. 事实源回写要求

1. 创建 TaskSet 时应记录 Change（依据 `specs/22-Change-变更记录.md`）；
2. TaskSet 状态变更时应记录 Change；
3. TaskSet 关联 Intent、ADR、Evidence、Profile 时应更新对应字段并记录 Change；
4. 将 Task 移入/移出 TaskSet 时应更新 Task 的 `taskset` 字段和 TaskSet 的 `tasks` 字段，并记录 Change；
5. TaskSet 关闭时必须填写 `closure_evidence` 字段；
6. TaskSet 实例写入 `ldvh-base/tasksets/` 目录后，应确保文件命名符合 `taskset-{NNNN}-short-title.yaml` 格式。

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
