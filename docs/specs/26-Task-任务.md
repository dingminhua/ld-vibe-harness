# Task-任务

> 创建日期：2026-06-09
> 更新日期：2026-06-09
> 定位：定义 Task / 任务工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要管理 AI 可执行工作单元、验收标准、状态追踪和关闭证据的项目
> 上位依据：`docs/specs/05-工作模型基础规范.md`
> 相关规范：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/02-术语规范.md`、`docs/specs/03.04-工作模型文档规范.md`、`docs/specs/05.01-工作字段内容格式规范.md`、`docs/specs/06-工作流程基础规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/08-Web信息同步规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/10-运行闭环测试规范.md`、`docs/specs/20-工作模型集合索引.md`

---
## 1. 对象定位与准入条件

Task / 任务是 AI 可执行的工作单元，有明确目标、验收标准、状态流转和回写目标。Task 用于承载从 Intent 拆解或由用户直接授权的具体工作，使 AI、Human、Code 和 Web 可以围绕同一事实追踪执行进度、验证结果和关闭证据。

Task 不是所有工作的默认归宿。AI 可以在当前上下文中直接处理简单操作；只有需要跨会话追踪、需要验收确认、需要状态流转、需要回写证据或需要与其他对象建立关系的工作，才应进入 Task 事实源。

### 1.1 Task 准入条件

一个工作单元满足以下条件之一时，应考虑形成 Task：

1. 有明确目标和可验证验收标准；
2. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
3. 需要关闭证据、验证结果或产物引用；
4. 需要关联 Intent、ADR、Change、Memo、Pitfall 或其他 Task；
5. 存在前置依赖、子任务分解、风险判断或文档同步检查；
6. 不结构化会导致进度、责任、验收标准或验证结果不可追踪。

创建 Task 前，AI 必须说明创建原因、来源、建议验收标准和预期回写位置，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 Task 的内容

以下内容通常不应单独形成 Task：

1. 当前上下文中可以直接完成的简单操作；
2. 没有明确验收标准的开放式探索；
3. 已由现有 Task 完全覆盖的重复工作；
4. 只属于现有 Task 的一个执行步骤，且不需要独立状态和关闭证据；
5. 只是一条备忘、观察、参考资料或待讨论想法。

不形成 Task 的内容，应按性质留在当前执行上下文，或进入 Memo、docs、refs、evals、现有 Task 字段或其他权威位置。

---
## 2. 事实源边界

本文是 Task 工作模型的权威规范，定义 Task 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

Task 实例的权威事实源位置为：

```text
ldvh-base/tasks/task-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Task 工作模型规范 | `docs/specs/26-Task-任务.md` |
| Task 实例 | `ldvh-base/tasks/` |
| Task 字段内容格式 | `docs/specs/05.01-工作字段内容格式规范.md` |
| Task 展示、聚合或查询结果 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

Task 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Task 标准状态如下：

| 状态 | 含义 |
|---|---|
| `planned` | 已创建，待执行 |
| `executing` | 正在执行 |
| `verifying` | 执行完成，正在进行独立、专项或并行验证 |
| `review_needed` | 验证通过，待最终关闭检查或人工审查 |
| `closed` | 关闭条件满足，已关闭 |

`closed` 是稳定终态。终态 Task 不得直接重开；如需重新处理，应新建 Task，并在新 Task 中引用原 Task。

### 3.2 合法状态流转

```text
planned → executing
executing → verifying
verifying → review_needed
verifying → executing
review_needed → closed
review_needed → executing
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `planned` → `executing` | AI 准备执行任务，且 `blocked_by` 中所有前置 Task 已关闭 | 如前置依赖未关闭，不得进入执行态 |
| `executing` → `verifying` | AI 完成执行并准备启动验证 | 验证方式由本文字段和后续工作流程共同约束 |
| `verifying` → `review_needed` | 独立、专项或并行验证通过 | 环境不支持子 Agent 时，应记录降级方式 |
| `verifying` → `executing` | 验证发现未满足验收项、bug 或事实源缺口 | 应记录问题和修复计划 |
| `review_needed` → `closed` | 关闭条件全部满足 | 高风险或用户要求人工验收时，应先触发 Human Gate |
| `review_needed` → `executing` | 最终检查或人工审查不通过 | 应记录退回原因 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

### 3.3 关闭条件

Task 进入 `closed` 前必须同时满足：

1. `acceptance` 字段中所有检查项已标记为 `- [x]`；
2. `sub_tasks` 中所有子任务均为 `closed`；
3. `verification` 已说明验证方式、验证命令、人工审查方式或无法自动验证的降级方式；
4. `closure_evidence` 已填写，并能追溯到 Git 文件事实源、验证命令、结果物、人工确认或审计结论；
5. `closure_evidence` 已说明验证结果、关键证据、残留风险和无法验证事项；不得只写“done”“已完成”“看起来没问题”等无证据结论；
6. 验证失败、证据不足、结果不可复现或需要长期降级时，已按 `docs/specs/06-工作流程基础规范.md` §6.10.1 暂停并完成分流，不得关闭为 `closed`；
7. `affected_docs` 非空时，已完成文档同步检查或在 `closure_evidence` 中说明豁免理由；
8. `closed_at` 已填写；
9. 需要 Human Gate 的场景已完成确认，并按 `docs/specs/06-工作流程基础规范.md` §6.3.1 留下最小证据记录。

### 3.4 关闭证据最低要求

`closure_evidence` 是 Task 关闭判断的证据摘要，不是过程日志全文。关闭证据至少应覆盖：

1. 完成了哪些 acceptance 项；
2. 执行了哪些验证、审查或人工确认；
3. 关键验证结果、输出摘要或结果物路径；
4. 受影响事实源、文档或产物是否已回写或同步；
5. 发现的问题如何修复、分流或降级；
6. 是否仍有残留风险、无法验证事项或需要后续 Task。

涉及 Human Gate 的 Task，`closure_evidence` 应摘要嵌入或引用符合 `docs/specs/06-工作流程基础规范.md` §6.3.1 的 Human Gate 记录。该记录可以写入 `closure_evidence`、`status_history`、相关 Memo / ADR / Task 或 Change / commit 证据中，但关闭证据必须能定位到确认事项、影响范围、确认结果、验证方式和回写位置。

无法提供上述证据时，Task 应停留在 `executing`、`verifying` 或 `review_needed`，并按问题性质进入 blocking、follow-up、Memo、Pitfall、ADR、Human Gate 或具体工作流程。

---
## 4. 对象关系

### 4.1 Task 与 Intent

Task 可以关联一个 Intent，作为该 Intent 的执行单元。关联字段为 `source_intent`。Intent 的目标、约束、成功标准、任务集合职责和完成判断由 `docs/specs/24-Intent-意图.md` 定义。

### 4.2 Task 与 ADR

Task 可以通过 `related_adrs` 引用多个 ADR，表示执行时需要遵守或参考的长期决策。ADR 的准入、状态和字段契约由 `docs/specs/21-ADR-决策.md` 定义。

### 4.3 Task 与 Change

Task 的创建、状态变化、关闭和关键事实源修改都应留下 Git 可追溯记录。Task 可通过 Git commit、`status_history`、`closure_evidence` 和 `related_changes` 保持追溯；Change 的 commit message 契约和 Git 记录事实源边界由 `docs/specs/22-Change-变更.md` 定义。

### 4.4 Task 与 Task 子任务

Task 可以通过 `parent_task` 和 `sub_tasks` 建立父子关系。

子任务规则：

1. 子任务与父任务使用同一工作模型和状态机；
2. 子任务默认继承父任务的 `source_intent`；
3. 父任务关闭前，所有子任务必须为 `closed`；
4. 子任务不得再有子任务；如子任务执行中发现新问题，应创建同级子任务挂到同一个父任务；
5. AI 发现当前 Task 范围内的 bug、缺口或遗漏时，应提出创建子任务建议，经 Human Gate 或已授权工作流程确认后写入事实源；
6. 子任务创建后，AI 应继续完成当前 Task 的剩余工作，除非人明确切换执行目标。

### 4.5 Task 与前置依赖

Task 可以通过 `blocked_by` 声明前置依赖。`blocked_by` 表示当前 Task 进入 `executing` 前必须等待的硬前置 Task 列表。

前置依赖规则：

1. `blocked_by` 为 Task ID 列表，可为空；
2. 每个 Task ID 必须引用已存在 Task；
3. 当前 Task 不得引用自身；
4. 当前 Task 从 `planned` 进入 `executing` 前，`blocked_by` 中所有 Task 必须为 `closed`；
5. 前置依赖是执行顺序约束，不等同于父子任务分解。

### 4.6 暂缓对象化概念的承接

20 已将 Evidence、Dependency、Risk、Artifact 和 Checklist 等概念取消或暂缓为独立工作模型。Task 对这些概念的承接方式如下：

| 概念 | 当前承接方式 | 字段 |
|---|---|---|
| Evidence / 验证证据 | 作为验证方式和关闭证据摘要，不创建独立 Evidence 对象 | `verification`、`closure_evidence` |
| Dependency / 依赖 | 作为前置 Task 关系字段，不创建独立 Dependency 对象 | `blocked_by` |
| Risk / 风险 | 作为任务风险判断字段，不创建独立 Risk 对象 | `risk_assessment` |
| Artifact / 产物 | 作为结果物路径或引用，不创建独立 Artifact 对象 | `deliverables` |
| Checklist / 检查清单 | 作为验收标准和关闭检查项，不创建独立 Checklist 对象 | `acceptance` |

上述字段承接不表示这些概念没有价值，只表示当前不具备独立工作模型的默认准入。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Task 实例；
2. AI 自动识别到应创建子任务、同 Intent 新 Task 或 Memo；
3. Task 涉及修改 docs/specs、docs 正文、ldvh-base、Rules / Instructions、Skill、Agent、Code、Web 或其他高影响事实源；
4. 跳过、删除或改写 `acceptance` 检查项；
5. 在 `affected_docs` 无实际变更时，通过豁免理由关闭 Task；
6. 关闭高风险 Task，或用户明确要求人工验收；
7. 绕过合法状态流转、修改 `closed` 终态或补写关闭证据；
8. 将 20 中 removed、deferred-field 或 deferred-doc 项升级为 Task 之外的新工作模型。

Human Gate 的具体环境实体由 04 系列环境适配映射和运行投影记录承接。本文只规定 Task 语境下需要确认的事实、影响范围和证据承接要求。

Task 语境下的 Human Gate 记录应遵守 `docs/specs/06-工作流程基础规范.md` §6.3.1。创建、删除、验收改写、关闭豁免、终态修改或高风险事实源写入等场景中，确认记录至少应说明目标 Task、拟变更字段或状态、影响的事实源和后续验证方式。

---
## 6. 字段契约

### 6.1 字段表

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | Task ID，格式为 `task-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `task` | Reference | AI、Code、Web |
| `title` | 任务标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建日期 | date | 是 | `YYYY-MM-DD` | Reference | AI、Code、Web |
| `updated` | 最近更新日期 | date | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `description` | 任务背景、目标和范围 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `source` | 任务来源 | string | 是 | Intent ID、用户直接指示或其他可追溯来源 | Reference / Narrative | AI、Web |
| `source_intent` | 关联 Intent ID | string | 否 | 为空表示非 Intent 拆解任务 | Reference | AI、Code、Web |
| `parent_task` | 父任务 ID | string | 否 | 非空时表示本 Task 是子任务 | Reference | AI、Code、Web |
| `sub_tasks` | 子任务 ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `blocked_by` | 前置 Task ID 列表 | list[string] | 否 | 默认为空列表；全部关闭后才可执行 | Reference | AI、Code、Web |
| `acceptance` | 验收标准和检查项 | string | 是 | 关闭前全部为 `- [x]` | Checklist | AI、Code、Web |
| `verification` | 验证方式、验证命令或验证计划 | string | 否 | 执行进入验证前应补齐 | Evidence / Checklist | AI、Code、Web |
| `risk_assessment` | 风险判断、已知不确定性和降级方式 | string | 否 | 高风险任务应填写 | Narrative / Checklist | AI、Human |
| `assignee` | 执行者 | string | 否 | 可为 AI、Human 或角色名 | Reference | AI、Web |
| `related_adrs` | 关联 ADR ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_changes` | 关联 Change commit 列表 | list[string] | 否 | 可记录 commit hash 或 Change 引用 | Reference | AI、Code、Web |
| `related_docs` | 参考输入文档路径列表 | list[string] | 否 | 路径应可追溯 | Reference | AI、Code、Web |
| `affected_docs` | 任务完成后应同步检查的文档路径列表 | list[string] | 否 | 关闭前检查是否变更或说明豁免 | Reference | AI、Code |
| `deliverables` | 产物、报告、截图、构建产物或导出文件路径列表 | list[string] | 否 | 结果物应可追溯 | Reference | AI、Code、Web |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |
| `closed_at` | 关闭日期 | date | 条件必填 | `status: closed` 时必须填写 | Reference | AI、Code、Web |
| `closure_evidence` | 关闭证据摘要 | string | 条件必填 | `status: closed` 时必须填写，并符合 §3.4 最低要求 | Evidence | AI、Code、Web |

字段内容格式按 `docs/specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、关闭条件不满足或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: task-0001
type: task
title: 更新 Task 工作模型
status: planned
created: 2026-06-09
updated: 2026-06-09
description: |
  将 Task 工作模型纳入 docs/specs，并按当前工作模型文档规范校准字段、状态和 Human Gate。
source: 用户直接指示
source_intent:
parent_task:
sub_tasks: []
blocked_by: []
acceptance: |
  - [ ] 创建 docs/specs/26-Task-任务.md
  - [ ] 明确 Task 对证据、依赖、风险、产物和检查项的字段承接
  - [ ] 更新 20 工作模型集合索引
verification: |
  运行 specs 文档校验和 git diff --check。
risk_assessment: |
  - 避免恢复 Evidence、Risk、Dependency、Artifact、Checklist 的独立对象化。
assignee: AI
related_adrs: []
related_changes: []
related_docs:
  - docs/specs/26-Task-任务.md
  - docs/specs/20-工作模型集合索引.md
affected_docs:
  - docs/specs/20-工作模型集合索引.md
deliverables:
  - docs/specs/26-Task-任务.md
status_history:
  - at: 2026-06-09
    from:
    to: planned
    actor: AI
    reason: 用户要求继续完善工作模型
closed_at:
closure_evidence:
```

### 6.3 Human Gate 记录回写样例

Task 创建、删除、验收改写、关闭豁免、终态修改、高风险事实源写入或人工验收时，Human Gate 记录可以摘要写入 `closure_evidence`、`status_history`、相关 Memo / ADR / Task 或 Change / commit 证据中。Task 关闭时若依赖 Human Gate，`closure_evidence` 应能直接嵌入或定位以下信息：

```yaml
closure_evidence: |
  ## 验证结果

  已完成 acceptance 检查，相关命令通过。

  ## Human Gate 记录

  Human Gate 记录：
  - 触发原因：关闭高风险 Task，且涉及 affected_docs 无实际变更豁免
  - 确认事项：是否允许以豁免理由关闭该 Task
  - 影响范围：目标 Task、affected_docs、相关规范和后续审计
  - 确认依据：验收清单、验证命令结果、diff 摘要和豁免理由
  - Human 决策：确认关闭
  - 确认人/时间：Human，2026-06-10
  - 后续动作：填写 closed_at 与 closure_evidence，并提交 Change
  - 验证方式：运行 Task / specs 校验并检查 Git diff
  - 回写位置：本 Task 的 closure_evidence、相关 Change / commit
  - 残留风险：后续若发现 affected_docs 漏同步，应创建 follow-up Task

  ## 结论

  Task 满足关闭条件；残留风险已记录。
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Task 回写遵循以下规则：

1. 创建 Task 时，应写入 `ldvh-base/tasks/`，并填写基础字段、来源、目标和验收标准；
2. 状态变化前应检查合法流转、前置依赖、子任务和 Human Gate；
3. 状态变化后应更新 `updated`，并向 `status_history` 追加记录；
4. 创建子任务、补充依赖、修改验收标准、添加产物或关闭证据时，应保留 Git 可追溯变更；
5. Task 关闭时必须填写 `closed_at` 和 `closure_evidence`；
6. Task 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 文档同步检查

Task 关闭时，如 `affected_docs` 非空，必须检查：

1. `affected_docs` 中列出的文档在 Task 执行期间是否有 Git 变更；
2. 有变更时，视为完成同步检查；
3. 无变更时，必须在 `closure_evidence` 中说明豁免理由；
4. 无变更且无豁免理由时，不得关闭 Task。

三类文档字段语义如下：

| 字段 | 语义 |
|---|---|
| `related_docs` | 任务参考的输入文档 |
| `affected_docs` | 任务完成后需要同步检查的文档 |
| `deliverables` | 任务产出的结果物路径 |

同一文档可以同时出现在 `related_docs` 和 `affected_docs` 中。

### 7.3 证据留存

Task 证据至少包括：

1. 创建原因和来源；
2. 验收标准；
3. 状态变化记录；
4. 验证方式或验证命令；
5. 产物路径或引用；
6. 关闭证据；
7. 符合 06 §6.3.1 的 Human Gate 确认记录或降级说明。

聊天内容、临时命令输出、Web 页面状态和工具缓存不得单独作为关闭证据。需要长期保留时，应摘要写入 `closure_evidence`、产物文件或对应事实源。

### 7.4 关闭证据与失败暂停

Task 关闭证据必须支持“结果有证可验”。AI 不得把以下内容单独作为关闭证据：

1. “已完成”“done”“应该通过”“看起来没问题”等结论性自述；
2. 未说明命令、输入、输出或结果物位置的验证描述；
3. 只存在于聊天、临时终端输出、Web 页面状态或工具缓存中的过程信息；
4. 未经回写的 Agent、Skill 或工具输出；
5. 未按 06 §6.3.1 说明触发原因、确认事项、影响范围、确认依据、确认结果、后续动作、验证方式和回写位置的 Human Gate 对话。

若验证失败、结果不可复现、证据不足或需要跳过部分验证，Task 不得进入 `closed`。AI 应先记录失败原因、已尝试修复、剩余风险和后续分流；修复后必须重新执行相关验证，或在 `closure_evidence` 中明确说明无法验证的原因、Human Gate 确认和后续 Task。

---
## 8. 适配规则

### 8.1 AI 协作

AI 处理 Task 时应遵守：

1. 先判断是否满足 Task 准入条件，再提出创建建议；
2. 创建、更新、关闭或删除 Task 前评估 Human Gate；
3. 执行前检查 `blocked_by`、`status`、`acceptance`、`related_docs` 和 `affected_docs`；
4. 执行完成后进入验证阶段，按 `verification` 和 `acceptance` 检查；
5. 关闭前确认 §3.3 关闭条件和 §3.4 关闭证据最低要求全部满足；
6. 发现范围内 bug、缺口或规范遗漏时，按 §4.4 判断是否创建子任务；
7. 验证失败、证据不足、结果不可复现或需要长期降级时，按 06 §6.10.1 暂停并分流，不得用推测性表述替代证据；
8. 不得把 20 中 removed 或 deferred 的概念自动升级为独立工作模型。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Task YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `blocked_by`、`parent_task`、`sub_tasks` 和相关对象引用；
5. 校验 `acceptance` checklist 是否全部完成；
6. 校验 `verification` 和 `closure_evidence` 在 closed 状态下不为空，并逐步检查是否包含验证结果、证据归属和豁免说明；
7. 校验 `affected_docs` 的变更或豁免说明；
8. 聚合 Task 状态、依赖、风险判断、产物和关闭证据。

Code 不得自行创建、关闭或删除 Task，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/tasks/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Task 状态、验收清单、前置依赖、子任务、风险判断、产物、关闭证据和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Web 不得在页面状态、缓存或数据库中维护独立 Task 权威状态。受控编辑 Task 字段时，应调用 Code 校验和受控写入链路，并遵守 Human Gate。

### 8.4 工作流程与环境适配

Task 执行、验证、关闭和审计的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Task 实例的事实规则和状态约束。

独立、专项或并行验证的环境承接方式由 04 系列环境适配映射和运行投影记录处理。环境不支持子 Agent 时，应记录降级方式，例如改用人工审查、Code 校验或单 Agent 分阶段自检；不得把未完成的独立验证表述为完整通过。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Task 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、关闭条件和事实源边界 | 05、03.04、本文、20 集合索引、Human Gate | 工作模型治理 | 创建、修改、搬移、审计或关闭 Task 时 |
| 入口可见要求 | AI 处理可执行工作单元、验收标准、证据、依赖、风险、产物或检查项时，应能定位本文 | 20 集合索引、运行入口摘要、Task 执行流程入口 | AI 执行入口提示 | 任务入口、事实实例目录、状态流转或字段契约变化时 |
| 确定性执行要求 | Task 字段、状态、引用、文件命名、验收清单、关闭条件、关闭证据和文档同步检查应由 Code 校验或记录缺口 | `docs/specs/07-Code实现规范.md`、`docs/specs/10-运行闭环测试规范.md`、Task 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、引用关系、关闭条件、closure_evidence 或 affected_docs 规则变化时 |
| Human 交互要求 | Task 创建、删除、高风险事实源写入、验收改写、关闭豁免和终态修改应触发 Human Gate，并按 06 §6.3.1 留下最小证据记录 | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Task 规范变化后，应检查 20、05.01、Code、Web、运行投影和相关工作流程是否需要同步 | 集合索引维护、字段格式映射、Code/Web 联动检查、人工降级检查 | 触发保障 | Task 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

Task 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Task |
| 事实源位置 | 实例路径符合 `ldvh-base/tasks/task-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 关闭条件 | 关闭前满足 §3.3 |
| 关闭证据 | `closure_evidence` 符合 §3.4，包含验证结果、关键证据、回写位置、失败处理和残留风险 |
| 子任务关系 | 子任务不超过一层，父任务关闭前子任务已关闭 |
| 前置依赖 | `blocked_by` 引用存在、无自引用，执行前均已关闭 |
| 暂缓对象化 | 证据、依赖、风险、产物和检查项由字段承接，未误建独立对象 |
| 文档同步 | `affected_docs` 已检查变更或填写豁免理由 |
| Human Gate | §5 场景已完成确认并符合 06 §6.3.1，或记录降级 |
| 失败暂停 | 验证失败、证据不足、结果不可复现或长期降级时，Task 未被关闭且已按 06 §6.10.1 分流 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Task 校验 Code 待字段契约稳定后补齐正反样例；
2. Task Web 展示和受控编辑入口待 Web 实现规划时补齐；
3. Task 执行、验证、关闭和审计的具体工作流程待 40-59 承接；
4. `closure_evidence` 的结构化子字段是否需要从 Evidence 文本升级为更细字段，待 Task 验证与关闭流程稳定后评估；
5. `risk_assessment` 的字段内容格式是否需要从 Narrative / Checklist 细化为专用格式，待更多实例实践后评估。
