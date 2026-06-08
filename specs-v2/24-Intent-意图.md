# Intent-意图

> 创建日期：2026-06-09
> 定位：定义 Intent / 意图工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要管理人的目标、范围、成功标准、约束、任务集合和完成判断的项目
> 上位依据：`specs-v2/05-工作模型基础规范.md`
> 相关规范：`specs-v2/00-LD-Vibe-Harness理念与纲要.md`、`specs-v2/02-术语规范.md`、`specs-v2/03.04-工作模型文档规范.md`、`specs-v2/05.01-工作字段内容格式规范.md`、`specs-v2/07-Code实现规范.md`、`specs-v2/08-Web信息同步规范.md`、`specs-v2/09-事实源边界与承载规范.md`、`specs-v2/20-工作模型集合索引.md`、`specs-v2/27-Task-任务.md`

---
## 1. 对象定位与准入条件

Intent / 意图是人的目标、范围、成功标准和约束的结构化事实。Intent 用于沉淀需要跨任务追踪的目标入口，为 Task 拆解、ADR 决策、Memo 转化和最终完成判断提供上游依据。

Intent 同时承接旧 TaskSet / 任务集取消后的任务集合职责。LDVH v2 不再创建独立 TaskSet 工作模型；围绕同一目标、主题、阶段或治理域组织的一组 Task，应通过 Intent 的 `related_tasks`、`success_criteria` 和完成证据承载。

### 1.1 Intent 准入条件

一个输入满足以下条件之一时，应考虑形成 Intent：

1. 人表达了明确目标，且该目标需要跨任务、跨会话或跨执行轮次追踪；
2. 目标影响范围超出单次操作，需要多个 Task 协同完成；
3. 目标包含成功标准、约束、边界或阶段性完成判断；
4. 目标需要长期保留为后续 Task、ADR、Memo 或审计的上游依据；
5. 不结构化会导致目标、范围、约束或完成判断漂移。

创建 Intent 前，AI 必须说明创建原因、目标摘要、建议成功标准、约束、预期关联任务和回写位置，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 Intent 的内容

以下内容通常不应单独形成 Intent：

1. 当前 Task 内的简单指示；
2. 一次性操作或局部调整；
3. 没有明确目标或成功标准的开放式讨论；
4. 已由现有 Intent 或 Task 完全覆盖的重复输入；
5. 只是资料、观察、提醒或未决想法。

不形成 Intent 的内容，应按性质留在当前执行上下文，或进入 Task、Memo、docs、refs、evals、ADR 或其他权威位置。

---
## 2. 事实源边界

本文是 Intent 工作模型的权威规范，定义 Intent 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

Intent 实例的权威事实源位置为：

```text
ldvh-base/intents/intent-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Intent 工作模型规范 | `specs-v2/24-Intent-意图.md` |
| Intent 实例 | `ldvh-base/intents/` |
| Intent 字段内容格式 | `specs-v2/05.01-工作字段内容格式规范.md` |
| Intent 展示、聚合或查询结果 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

旧 `specs/24-Intent-意图.md` 只作为迁移素材。v2 生效后，Intent 的稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Intent 标准状态如下：

| 状态 | 含义 |
|---|---|
| `draft` | 已记录，尚未完成分析、边界确认或任务拆解 |
| `active` | 已分析并可作为 Task 拆解、执行或决策上游依据 |
| `completed` | 关联 Task 已完成，成功标准已满足或已说明豁免 |
| `closed` | 完成结论已确认并沉淀，Intent 不再继续追踪 |

`closed` 是稳定终态。终态 Intent 不得直接重开；如目标重新启动、扩大范围或改变成功标准，应新建 Intent，并在新 Intent 中引用原 Intent。

### 3.2 合法状态流转

```text
draft → active
active → completed
completed → closed
completed → active
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `draft` → `active` | 目标、范围、成功标准和约束已足够明确，可拆解或关联 Task | `draft` 不应作为稳定 Task 拆解依据 |
| `active` → `completed` | `related_tasks` 中应完成的 Task 已关闭，成功标准已满足或有豁免说明 | 应填写 `completion_evidence` |
| `completed` → `closed` | Human 已确认完成结论，或工作流程明确允许关闭 | 应填写 `closed_at` |
| `completed` → `active` | 完成检查或人工审查不通过，需要继续拆解或执行 | 应记录退回原因 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

### 3.3 完成条件

Intent 进入 `completed` 前必须同时满足：

1. `success_criteria` 已逐项检查；
2. `related_tasks` 中应完成的 Task 均已 `closed`，或在 `completion_evidence` 中说明无需关闭的原因；
3. 约束条件没有被未授权突破，或已记录 Human Gate 确认；
4. `completion_evidence` 已填写，并能追溯到 Task 关闭证据、产物、文档或人工确认；
5. `completed_at` 已填写。

Intent 进入 `closed` 前必须满足：

1. 已处于 `completed`；
2. 完成结论已确认；
3. `closed_at` 已填写；
4. 需要 Human Gate 的场景已完成确认。

---
## 4. 对象关系

### 4.1 Intent 与 Task

Intent 通过 `related_tasks` 组织承接该目标的一组 Task。Task 通过 `source_intent` 指回 Intent。

规则如下：

1. 只有 `active` Intent 才应作为新 Task 的稳定上游依据；
2. Task 创建后，应在 Intent 的 `related_tasks` 中记录 Task ID；
3. Intent 完成前，应检查 `related_tasks` 中应完成的 Task 是否已关闭；
4. 如果某个 Task 不再属于该 Intent，应在 Intent 或 Task 中记录调整原因；
5. Intent 承接任务集合职责，但不替代 Task 的状态机、验收标准或关闭证据。

### 4.2 Intent 与 ADR

Intent 可以通过 `related_adrs` 引用多个 ADR，表示目标实现过程中产生或需要遵守的长期决策。ADR 的准入、状态和字段契约由 `specs-v2/21-ADR-决策.md` 定义。

### 4.3 Intent 与 Memo

Memo 中的输入满足 Intent 准入条件后，可以转化为 Intent。转化时应：

1. 保留 Memo 与 Intent 的引用关系；
2. 说明为什么从未任务化输入升级为目标入口；
3. 评估 Human Gate；
4. 不在 Intent 中复制 Memo 全文，只保留摘要和引用。

Memo 的准入、状态和字段契约由 `specs-v2/25-Memo-备忘.md` 定义。

### 4.4 Intent 与 Pitfall

Intent 可以通过 `related_pitfalls` 记录执行该目标过程中形成的可复用踩坑经验。Pitfall 迁入 v2 前，相关引用可先保留为待补齐关系。

### 4.5 Intent 与 TaskSet

TaskSet 已取消独立工作模型。Intent 承接 TaskSet 的目标分组和完成判断职责：

| 原 TaskSet 职责 | v2 承接方式 |
|---|---|
| 组织同一目标下的一组任务 | Intent `related_tasks` |
| 描述任务集合目标 | Intent `description` |
| 描述完成标准 | Intent `success_criteria` |
| 描述约束和范围 | Intent `constraints` |
| 判断集合完成 | Intent `completed` 状态和 `completion_evidence` |

Intent 不承接 Task 的执行状态细节。每个 Task 的执行、验证、关闭和证据仍由 `specs-v2/27-Task-任务.md` 定义。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Intent 实例；
2. 将用户输入、Memo 或临时讨论升级为 Intent；
3. 将 Intent 从 `active` 流转为 `completed`；
4. 将 Intent 从 `completed` 流转为 `closed`；
5. 改写 `success_criteria`、`constraints` 或完成证据；
6. 在关联 Task 未全部关闭时通过豁免方式完成 Intent；
7. 关闭高风险 Intent，或用户明确要求人工验收；
8. 将 TaskSet 恢复为独立工作模型，或把 Intent 的任务集合职责拆出为新对象。

Human Gate 的具体环境实体由 04 系列环境适配映射和运行投影记录承接。本文只规定 Intent 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 字段表

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | Intent ID，格式为 `intent-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `intent` | Reference | AI、Code、Web |
| `title` | 意图标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建日期 | date | 是 | `YYYY-MM-DD` | Reference | AI、Code、Web |
| `updated` | 最近更新日期 | date | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `description` | 目标背景、范围和问题说明 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `success_criteria` | 成功标准 | string | 是 | 应能支持完成判断 | Narrative / Checklist | AI、Code、Web |
| `constraints` | 约束、边界、禁止事项和偏好 | string | 否 | 高影响目标应填写 | Narrative / Checklist | AI、Human |
| `source` | 来源 | string | 是 | 谁在什么场景下表达 | Reference / Narrative | AI、Web |
| `related_tasks` | 关联 Task ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联 ADR ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 来源或关联 Memo ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联 Pitfall ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |
| `completed_at` | 完成日期 | date | 条件必填 | `status: completed` 或 `closed` 时必须填写 | Reference | AI、Code、Web |
| `completion_evidence` | 完成证据摘要 | string | 条件必填 | `status: completed` 或 `closed` 时必须填写 | Evidence | AI、Code、Web |
| `closed_at` | 关闭日期 | date | 条件必填 | `status: closed` 时必须填写 | Reference | AI、Code、Web |

字段内容格式按 `specs-v2/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、完成条件不满足或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: intent-0001
type: intent
title: 建立 LDVH v2 工作模型最小闭环
status: active
created: 2026-06-09
updated: 2026-06-09
description: |
  将工作模型集合索引、Intent 和 Task 迁入 v2，使 AI 可以围绕目标、任务、验收和关闭证据形成最小可追踪闭环。
success_criteria: |
  - [ ] 20 工作模型集合索引已迁入
  - [ ] 24 Intent 已迁入
  - [ ] 27 Task 已迁入
  - [ ] TaskSet 不再作为独立工作模型恢复
constraints: |
  - 不恢复固定 NN.01-NN.06 子文档结构
  - 不把 Evidence、Risk、Dependency、Artifact、Checklist 误对象化
source: 用户讨论中确认工作模型迁移优先级
related_tasks:
  - task-0001
related_adrs: []
related_memos: []
related_pitfalls: []
related_docs:
  - specs-v2/20-工作模型集合索引.md
  - specs-v2/27-Task-任务.md
status_history:
  - at: 2026-06-09
    from:
    to: active
    actor: AI
    reason: 用户确认继续迁移工作模型
completed_at:
completion_evidence:
closed_at:
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Intent 回写遵循以下规则：

1. 创建 Intent 时，应写入 `ldvh-base/intents/`，并填写目标、成功标准、约束和来源；
2. 状态变化前应检查合法流转、关联 Task、完成条件和 Human Gate；
3. 状态变化后应更新 `updated`，并向 `status_history` 追加记录；
4. 创建或关联 Task、ADR、Memo、Pitfall 时，应同步检查 Intent 关系字段；
5. Intent 进入 `completed` 时必须填写 `completed_at` 和 `completion_evidence`；
6. Intent 进入 `closed` 时必须填写 `closed_at`；
7. 关键事实源修改应按 `specs-v2/22-Change-变更.md` 形成 Git 可追溯记录。
7. Intent 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

Intent 证据至少包括：

1. 创建原因和来源；
2. 成功标准和约束；
3. 关联 Task 列表及其关闭状态；
4. 关键 ADR、Memo 或 Pitfall 引用；
5. 完成证据；
6. Human Gate 确认记录或降级说明。

Intent 的完成证据应摘要引用 Task 的关闭证据、产物、文档或人工确认，不得复制所有 Task 详情。

---
## 8. 适配规则

### 8.1 AI 协作

AI 处理 Intent 时应遵守：

1. 先判断是否满足 Intent 准入条件，再提出创建建议；
2. 创建、更新、完成、关闭或删除 Intent 前评估 Human Gate；
3. 将 Intent 拆解为 Task 前，确认 Intent 已进入 `active`；
4. 拆解或关联 Task 后，同步检查 `related_tasks` 与 Task `source_intent`；
5. 完成 Intent 前，检查 `success_criteria`、`constraints`、`related_tasks` 和 `completion_evidence`；
6. 不得恢复 TaskSet 作为独立工作模型。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Intent YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `related_tasks` 与 Task `source_intent` 的引用一致性；
5. 校验完成条件、完成证据和关闭日期；
6. 聚合 Intent 目标、关联 Task、成功标准和完成状态。

Code 不得自行创建、完成、关闭或删除 Intent，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/intents/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Intent 状态、成功标准、约束、关联 Task、完成证据和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Web 不得在页面状态、缓存或数据库中维护独立 Intent 权威状态。受控编辑 Intent 字段时，应调用 Code 校验和受控写入链路，并遵守 Human Gate。

### 8.4 工作流程与环境适配

Intent 创建、拆解、完成和关闭的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Intent 实例的事实规则和状态约束。

环境不支持完整关系校验、Web 展示或受控编辑时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Intent 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、完成条件和事实源边界 | 05、03.04、本文、20 集合索引、27 Task、Human Gate | 工作模型治理 | 创建、修改、迁移、审计、完成或关闭 Intent 时 |
| 入口可见要求 | AI 处理目标、范围、成功标准、约束、任务集合或完成判断时，应能定位本文 | 20 集合索引、运行入口摘要、Intent 拆解流程入口 | AI 执行入口提示 | 目标入口、任务拆解、事实实例目录、状态流转或字段契约变化时 |
| 确定性执行要求 | Intent 字段、状态、引用、文件命名、完成条件和 Task 关系一致性应由 Code 校验或记录缺口 | `specs-v2/07-Code实现规范.md`、Intent 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、引用关系、完成条件或 Task 关系规则变化时 |
| Human 交互要求 | Intent 创建、删除、完成、关闭、成功标准改写、约束突破和 TaskSet 恢复应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Intent 规范变化后，应检查 20、05.01、Task、Code、Web、运行投影和相关工作流程是否需要同步 | 集合索引维护、字段格式映射、Task 关系检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Intent 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

Intent 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Intent |
| 事实源位置 | 实例路径符合 `ldvh-base/intents/intent-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 完成条件 | 完成前满足 §3.3 |
| Task 关系 | `related_tasks` 与 Task `source_intent` 引用一致 |
| TaskSet 边界 | Intent 承接任务集合职责，未恢复 TaskSet 独立对象 |
| Human Gate | §5 场景已完成确认或记录降级 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Intent 校验 Code 待字段契约稳定后补齐正反样例；
2. Intent Web 展示和受控编辑入口待 Web 实现规划时补齐；
3. Intent 创建、拆解、完成和关闭的具体工作流程待 40-59 迁入后承接；
4. ADR、Memo、Pitfall 迁入后，应回查本文中的对象关系字段是否需要同步；
5. `success_criteria` 是否强制使用 Checklist，待更多实例实践后评估。
