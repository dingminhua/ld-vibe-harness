# Intent 意图

> 创建日期：2026-06-03
> 定位：定义 Intent 意图工作模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理用户原始目标和约束的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`

---

---

## 1. 本文解决的问题

本文定义 Intent 意图工作模型。Intent 是人的原始目标、范围、成功标准和约束，用于沉淀需要跨任务追踪的用户意图，为 Task 拆解和 ADR 决策提供上游来源。

本文只定义 Intent 对象模型。Intent 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践可按需由 §12 附件型实践子文档承接。

本文是精简版规范，只包含核心章节。07 §4.2 中未展开的章节标注于 §10 待补齐事项。

---

## 2. 与 13 的关系

`specs/07-工作模型基础规范.md` 定义工作模型通用规则、文件命名、附件型实践子文档命名和工作模型标准组成。本文依据 07 §4.2 定义 Intent 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 Intent 定义

Intent 是人的原始目标、范围、成功标准和约束。Intent 应记录用户想要什么、成功标准是什么、约束是什么、来源是什么。

Intent 不是所有用户输入的默认归宿。AI 可以在当前任务中直接处理简单请求，但只有满足准入条件、需要跨任务追踪或影响范围超出单次操作的意图，才应进入 Intent 事实源。

### 3.2 Intent 与临时请求

临时请求是用户在执行过程中的简单指示、一次性操作或局部调整，不默认成为 Intent。临时请求可以保留在当前执行上下文或 Task 中。

一个 Intent 至少应具备：

1. 明确的目标描述；
2. 可判断的成功标准；
3. 明确的来源（谁在什么场景下表达的）；
4. 可追溯的状态。

### 3.3 Intent 准入条件

当一个意图满足以下条件之一时，应考虑形成 Intent：

1. 用户表达了明确目标，且目标尚未任务化或需要跨任务追踪；
2. 影响范围超出单次操作，需要多个 Task 协同完成；
3. 需要跨会话保持意图连续性。

不满足 Intent 准入条件的临时请求，可以直接作为 Task 执行，不需要先创建 Intent。

以下内容通常不应单独形成 Intent：

1. 当前 Task 内的简单指示；
2. 一次性操作或局部调整；
3. 不影响其他对象的临时方案；
4. 已由现有 Task 完全覆盖的重复意图。

AI 不得因为用户表达了任何意图就自动创建 Intent。只有满足准入条件的意图，才应写入 Intent 事实源。

---

## 4. 事实源边界

本文是 Intent 意图工作模型的权威事实源。本文定义 Intent 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Intent 对象实例的权威事实源位置为：

```text
ldvh-base/intents/intent-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Intent 对象模型 | `specs/24-Intent-意图.md` |
| Intent 对象实例 | `ldvh-base/intents/` |
| Intent 契约子文档 | `specs/24.06-Contract.md` |
| Intent 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

Intent 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `draft` | 用户刚表达，AI 尚未分析 |
| `active` | AI 已分析，已关联 Task |
| `completed` | 关联 Task 全部完成 |
| `closed` | 已确认完成并沉淀 |

### 5.2 合法状态流转

```text
draft → active
active → completed
completed → closed
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`closed` 是稳定终态。终态 Intent 不得重开；如需重新追踪，必须新建 Intent 承接，并在新 Intent 中引用原 Intent。

`draft` 状态的 Intent 不应作为 Task 拆解的上游依据。只有 `active` 状态的 Intent 才表示已分析、已关联 Task 的意图。

---

## 6. 与其他对象的关系

### 6.1 Intent → Task

当 Intent 进入 active 状态时，应创建 Task 承接执行工作，Intent 保留意图记录。

创建 Task 后，Intent 的 `related_tasks` 字段应记录相关 Task ID。Task 的字段、状态和关闭规则由 Task 对象模型定义。

### 6.2 Intent → ADR

当 Intent 的实现涉及需要长期追溯的决策时，应创建 ADR 记录决策。

创建 ADR 后，Intent 的 `related_adrs` 字段应记录相关 ADR ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策记录.md`）定义。

### 6.3 Memo → Intent

当 Memo 中的输入涉及明确目标且满足 Intent 准入条件时，Memo 可转化为 Intent。

转化条件：

1. Memo 内容满足 Intent 准入条件；
2. 目标已明确，不再只是未任务化输入；
3. 已获得 Human Gate 确认。

---

## 7. Human Gate

以下场景必须触发 Human Gate：

1. 创建 Intent 时确认；
2. 状态从 `active` → `completed` 时确认（确认关联 Task 是否全部完成）。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo环境规范.md` §9）。

---

## 8. 字段契约

### 8.1 基础字段

Intent 基础字段遵循 `specs/07-工作模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Intent 对象 ID，格式为 `intent-{NNNN}` |
| `type` | string | 是 | 固定为 `intent` |
| `title` | string | 是 | 意图标题 |
| `status` | string | 是 | Intent 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 8.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `description` | string | 是 | 意图详细描述 |
| `success_criteria` | string | 是 | 成功标准 |
| `constraints` | string | 否 | 约束条件 |
| `source` | string | 是 | 来源（谁在什么场景下表达的） |
| `related_tasks` | list of string | 否 | 关联 Task ID 列表 |
| `related_adrs` | list of string | 否 | 关联 ADR ID 列表 |

字段约束和完整 YAML 示例详见 `specs/24.06-Contract.md`。

---

## 9. 事实源回写要求

1. 创建 Intent 时应记录 Change（依据 `specs/22-Change-变更记录.md`）；
2. Intent 状态变更时应记录 Change；
3. Intent 关联 Task 或 ADR 时应更新 `related_tasks` 或 `related_adrs` 字段并记录 Change；
4. Intent 实例写入 `ldvh-base/intents/` 目录后，应确保文件命名符合 `intent-{NNNN}-short-title.yaml` 格式。

---

## 10. 待补齐事项

以下章节依据 `specs/07-工作模型基础规范.md` §4.2 应定义但本文未展开，待后续阶段补齐：

| 07 §4.2 编号 | 章节名称 | 计划补齐阶段 |
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
