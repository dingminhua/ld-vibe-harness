# Task 任务

> 创建日期：2026-06-03
> 定位：定义 Task 任务工作模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理 AI 可执行工作单元的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档基础规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`

---

## 1. 对象定位与准入条件

本文定义 Task 任务工作模型。Task 是 AI 可执行的工作单元，有明确验收标准和回写目标，用于承载从 Intent 拆解或用户直接指示的具体工作。

### 1.1 Task 定义

Task 是 AI 可执行的工作单元，有明确验收标准和回写目标。Task 应记录目标、验收标准、验证方式、来源和关联对象。

Task 不是所有工作的默认归宿。AI 可以在当前上下文中直接处理简单操作，但只有满足准入条件、需要跨会话追踪或需要验收确认的工作，才应进入 Task 事实源。

### 1.2 Task 与临时工作

临时工作是执行过程中的简单操作、一次性调整或局部修改，不默认成为 Task。临时工作可以保留在当前执行上下文中。

一个 Task 至少应具备：

1. 明确的目标描述；
2. 可验证的验收标准；
3. 明确的来源（Intent 或用户直接指示）；
4. 可追溯的状态。

### 1.3 Task 准入条件

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

## 2. 事实源边界

本文是 Task 任务工作模型的权威事实源。本文定义 Task 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Task 对象实例的权威事实源位置为：

```text
ldvh-base/tasks/task-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Task 对象模型 | `specs/27-Task-任务.md` |
| Task 对象实例 | `ldvh-base/tasks/` |
| Task 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 3. 状态机

### 3.1 标准状态

Task 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `planned` | 已拆解，待执行 |
| `executing` | 正在执行 |
| `verifying` | 独立 agent 审计中 |
| `review_needed` | 执行完成，待审查 |
| `closed` | 审查通过，已关闭 |

### 3.2 合法状态流转

```text
planned → executing（要求 blocked_by 全部 closed，如有）
executing → verifying
verifying → review_needed
verifying → executing（退回：审计发现 bug）
review_needed → closed
review_needed → executing（退回：审查不通过）
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

#### 3.2.1 状态触发规则

状态触发规则、关闭条件和 Human Gate 场景由本文直接承接。

| 流转 | 触发时机 | 触发者 |
|---|---|---|
| planned → executing | AI 准备执行任务，且 `blocked_by` 中所有前置 Task 已关闭时 | AI |
| executing → verifying | AI 完成执行，启动独立 agent 审计时 | AI |
| verifying → review_needed | 独立 agent 审计 acceptance 全部通过后 | AI |
| verifying → executing | 审计发现 bug，需要修复时 | AI |
| review_needed → closed | 关闭条件全部满足时 | AI |
| review_needed → executing | 审查不通过，需要修复时 | AI |

`closed` 是稳定终态。终态 Task 不得重开；如需重新执行，必须新建 Task 承接，并在新 Task 中引用原 Task。

### 3.3 关闭条件

关闭条件由本文直接承接：

1. `acceptance` 字段中所有检查项已标记为 `- [x]`；
2. 所有子任务（`sub_tasks`）已关闭（`status: closed`）；
3. `closure_evidence` 字段已填写。

以上条件全部满足时，AI 直接将 Task 状态变更为 `closed`，不需要 Human Gate 确认。

---

## 4. 与其他对象的关系

### 4.1 Task → Intent

Task 可关联一个 Intent，作为该 Intent 的执行单元。

创建 Task 后，关联 Intent 的 `related_tasks` 字段应记录 Task ID。Intent 的字段和状态由 Intent 对象模型（`specs/24-Intent-意图.md`）定义。

### 4.2 Task → ADR

Task 可关联多个 ADR，作为执行过程中涉及的决策参考。

创建 Task 后，关联 ADR 的 `related_objects` 字段应记录 Task ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策.md`）定义。

### 4.3 Task → Evidence（已取消）

Evidence 独立工作模型已取消。Task 直接通过 `closure_evidence` 字段记录关闭证据，通过引用结果物（如文件路径、构建产物、测试报告等）承接验证和关闭证据功能。不再使用 `related_evidence` 字段和独立的 Evidence 对象。

### 4.4 Task → Change

Task 的创建、状态变更和关闭都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更.md`）。

### 4.5 Task → Task（子任务）

Task 可以有子任务。子任务与父任务使用相同的对象模型和状态机，通过 `parent_task` 字段建立纵向分解关系。

子任务规则：

1. **深度限制**：子任务不能再有子任务，即 `parent_task` 不为空的 Task 不得被其他 Task 的 `parent_task` 引用；
2. **默认归属**：子任务默认关联父任务的 `source_intent`；
3. **关闭条件**：父任务关闭前，所有子任务必须已关闭（`status: closed`）；
4. **自动创建**：AI 执行 Task 时发现 bug、缺口或规范遗漏，应自动创建子任务并关联到当前 Task；
5. **验证发现 bug 时创建子任务**：独立 agent 验证 acceptance 列表时发现未通过项，应为每个 bug 创建子任务，`parent_task` 指向当前 Task，`acceptance` 包含修复该 bug 的验收标准；子任务修复完成后重新验证主任务 acceptance 列表；如重新验证仍发现新 bug，停止自动循环并通过 AskUserQuestion 向用户报告；
6. **同级扩展**：如果子任务执行过程中又发现新问题，应创建新的子任务挂在同一个父任务下，而不是嵌套更深层级。

子任务与 Intent 是两个维度：Intent 是横向归类（同目标的一组任务），parent_task 是纵向分解（父任务的子任务）。

### 4.6 Task → Task（前置依赖）

Task 可以通过 `blocked_by` 字段声明前置 Task。`blocked_by` 表示当前 Task 在进入执行态前必须等待的硬前置任务列表。

前置依赖规则：

1. `blocked_by` 为 Task ID 列表，可为空列表；
2. `blocked_by` 中的每个 Task ID 必须引用已存在的 Task；
3. 当前 Task 不得在 `blocked_by` 中引用自身；
4. 当前 Task 从 `planned` 进入 `executing` 前，`blocked_by` 中所有 Task 必须为 `closed`；
5. 前置依赖是执行顺序约束，不等同于父子任务分解；`blocked_by` 不改变 `source_intent`、`parent_task` 或 `sub_tasks` 关系。

### 4.7 关联任务自动创建流程

AI 执行 Task 时发现 bug、缺口或规范遗漏，应按以下流程自动创建关联任务：

1. **识别问题**：AI 在执行过程中发现以下情况时，应进入关联任务创建流程：
   - 代码或配置中存在 bug 或错误
   - 规范中存在缺口或矛盾
   - 流程中存在遗漏或不符合预期的情况
   - 发现需要额外处理但当前 Task 范围外的工作

2. **判断关联类型**：
   - **子任务（parent_task）**：问题属于当前 Task 的执行范围，修复后才能完成当前 Task → 创建子任务
   - **同 Intent 新 Task**：问题不属于当前 Task 范围，但属于同一目标或治理域 → 创建新 Task 关联同一 Intent
   - **Memo**：问题尚未决定如何处理，但有保留价值 → 创建 Memo

3. **创建子任务**：
   - 设置 `parent_task` 为当前 Task ID
   - 设置 `source_intent` 为当前 Task 的 `source_intent`
   - 将子任务 ID 添加到当前 Task 的 `sub_tasks` 列表
   - 通知用户（Human Gate §5 第 3 条）

4. **继续执行**：创建关联任务后，AI 应继续完成当前 Task 的剩余工作，而不是中断当前 Task 去执行子任务。子任务应在当前 Task 完成或暂停后执行。

5. **关闭条件联动**：当前 Task 进入 `review_needed` 前，所有子任务必须已关闭。

---

## 5. Human Gate

Human Gate 场景由本文直接承接：

1. 状态从 `verifying` → `review_needed` 时确认；
2. 高风险操作前确认（修改 specs、Rules、ADR、ldvh-base/ 等事实源）；
3. 创建子任务时确认（AI 自动创建子任务时应通知用户）。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo环境规范.md` §9）。

---

## 6. 字段契约

### 6.1 基础字段

Task 基础字段遵循 `specs/07-工作模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Task 对象 ID，格式为 `task-{NNNN}` |
| `type` | string | 是 | 固定为 `task` |
| `title` | string | 是 | 任务标题 |
| `status` | string | 是 | Task 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 6.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `description` | string | 是 | 任务详细描述 |
| `source_intent` | string | 否 | 关联 Intent ID |
| `source` | string | 是 | 来源（Intent ID 或用户直接指示） |
| `parent_task` | string | 否 | 父任务 ID，非空时表示本 Task 为子任务 |
| `sub_tasks` | list of string | 否 | 子任务 ID 列表 |
| `blocked_by` | list of string | 否 | 前置 Task ID 列表；列表中的 Task 全部关闭后，当前 Task 才允许进入执行态 |
| `acceptance` | string | 是 | 验收标准，必须使用检查列表格式（`- [ ]` / `- [x]`），每项为可独立验证的原子条件 |
| `verification` | string | 否 | 验证方式 |
| `assignee` | string | 否 | 执行者 |
| `related_adrs` | list of string | 否 | 关联 ADR ID 列表 |
| `related_changes` | list of string | 否 | 关联 Change ID 列表 |
| `related_docs` | list of string | 否 | 任务参考的输入文档路径列表 |
| `affected_docs` | list of string | 否 | 任务完成后需要同步更新的文档路径列表；关闭时校验这些文档是否有变更，无变更需在 closure_evidence 中说明豁免理由 |
| `deliverables` | list of string | 否 | 任务产出的结果物路径列表 |
| `closed_at` | date | 条件必填 | 仅当 `status` 为 `closed` 时必须填写 |
| `closure_evidence` | string | 条件必填 | 仅当 `status` 为 `closed` 时必须填写，关闭证据摘要 |

字段约束和完整 YAML 示例已回并到本文。

---

## 7. 事实源回写与证据留存

### 7.1 事实源回写

1. 创建 Task 时应记录 Change（依据 `specs/22-Change-变更.md`）；
2. Task 状态变更时应记录 Change；
3. Task 关联 Intent、ADR 时应更新对应字段并记录 Change；
4. Task 关闭时必须填写 `closure_evidence` 字段；
5. Task 实例写入 `ldvh-base/tasks/` 目录后，应确保文件命名符合 `task-{NNNN}-short-title.yaml` 格式。

### 7.2 文档同步检查

Task 关闭时，如 `affected_docs` 非空，必须校验：

1. `affected_docs` 中列出的文档在 Task 执行期间是否有 git 变更；
2. 有变更 → 视为已同步，通过检查；
3. 无变更 → 需在 `closure_evidence` 中说明豁免理由（如"该文档无需更新，变更不影响文档内容"）；
4. 未说明豁免理由 → 不得关闭 Task。

三类文档关系的语义区分：

| 字段 | 语义 | 示例 |
|---|---|---|
| `related_docs` | 任务参考的输入文档 | `specs/27-Task-任务.md`（参考字段契约） |
| `affected_docs` | 任务完成后需同步更新的文档 | `specs/27-Task-任务.md`（新增字段需更新契约） |
| `deliverables` | 任务产出的结果物 | `specs/refs/07-竞品测试任务安排分析与最佳实践调研.md` |

同一文档可同时出现在 `related_docs` 和 `affected_docs` 中（既参考又需更新）。

### 7.3 证据留存

证据留存通用规则引用 `specs/07-工作模型基础规范.md` §7.4。Task 对象特有差异：

1. Task 关闭（`closed`）时，应留存 `closure_evidence` 字段内容和验收结果（`acceptance` 列表中所有检查项的最终状态）。

---

## 8. 适配规则

### 8.1 AI 协作

AI 协作通用规则引用 `specs/07-工作模型基础规范.md` §7.5。Task 对象特有差异：

1. AI 识别到可执行目标时，应判断是否满足 Task 准入条件（§1.3）；
2. 创建 Task 前必须通过 Human Gate 确认（§5）；
3. `blocked_by` 未全部关闭时，Task 不得从 `planned` 进入 `executing`（§3.2）。

### 8.2 Tools 辅助

Tools 辅助通用规则引用 `specs/07-工作模型基础规范.md` §7.6。当前由通用 Fact Validator 消费本文结构化契约完成校验，对象级 Tools 实践待按需创建。

### 8.3 Web 信息同步

Web 信息同步通用规则引用 `specs/07-工作模型基础规范.md` §7.7。当前未实现对象级 Web 实践，待后续统一适配。

---

## 9. 待补齐事项

以下章节依据 `specs/07-工作模型基础规范.md` §4.2 应定义但本文未展开，待后续阶段补齐：

| 07 §4.2 编号 | 章节名称 | 计划补齐阶段 |
|---|---|---|
| 8 | 证据留存要求 | Phase 3 |
| 9 | AI 协作适配 | Phase 4 |
| 10 | Tools 契约式校验与执行适配 | Phase 3（Contract 机制文件先行） |
| 11 | Web 信息同步适配 | Phase 5 |
| 12 | 机制适配边界 | Phase 4 |
