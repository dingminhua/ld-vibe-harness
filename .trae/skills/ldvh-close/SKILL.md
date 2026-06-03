---
name: "ldvh-close"
description: "Orchestrates LDVH Task closing workflow: closure condition validation, Human Gate confirmation, status update, and Intent cascade check. Invoke when a Task is in review_needed state and ready to close, or when user requests Task closure or completion review."
---

# LDVH Close Skill

## 定位

ldvh-close 承接 LDVH Core Loop 的 Record 阶段，用于在 Task 满足关闭条件时，由 AI 主控应用，完成从审查到关闭的流程。

本 Skill 是部署在项目 `.trae/skills/ldvh-close/SKILL.md` 的 LDVH 通用 Skill。Skill 实体不是事实源，不重新定义 Task 准入条件、字段契约或 Human Gate。发生冲突时，以 `ld-vibe-harness/specs/31-Task-任务.md`、`ld-vibe-harness/specs/31.06-Contract.md`、`ld-vibe-harness/specs/28-Evidence-验证证据.md` 和 `ld-vibe-harness/specs/28.06-Contract.md` 为准。

## 触发条件

在以下场景由 AI 主控应用本 Skill：

1. Task 处于 `review_needed` 状态，用户或 AI 判断可以关闭；
2. 用户要求关闭某个 Task；
3. 用户要求审查 Task 的完成情况。

## 不适用场景

1. Task 尚未进入 `review_needed` 状态；
2. 用户只是查看 Task 状态，不执行关闭；
3. Task 已处于 `closed` 状态。

## 必读文件

执行本 Skill 前，AI 必须读取以下事实源和规范文档：

- `ld-vibe-harness/specs/31-Task-任务.md` — Task 关闭条件和状态机
- `ld-vibe-harness/specs/28-Evidence-验证证据.md` — Evidence 验证结果判断
- `ld-vibe-harness/specs/31.06-Contract.md` — Task YAML schema 和状态流转契约
- `ld-vibe-harness/specs/28.06-Contract.md` — Evidence YAML schema

## 编排流程

### 1. 读取 Task 实例

从 `ldvh-base/tasks/` 读取当前 Task 的 YAML 实例。

### 2. 校验关闭条件

依次检查：

- **closure_evidence** — 是否已填写关闭证据；
- **关联 Evidence** — 关联 Evidence 的 `verification_result` 是否为 `fail`（如有 fail 则不可关闭）。

条件不满足时：
- 缺少 `closure_evidence` → 提示用户补充；
- Evidence 存在 `fail` → 提示用户退回 Task 修复。

### 3. Human Gate 确认

通过 AskUserQuestion 展示关闭摘要，请求用户确认：

- **确认** → 继续关闭流程；
- **退回** → 将 Task 状态更新为 `executing`，记录退回原因；
- **取消** → 停止流程。

### 4. 更新 Task 状态

确认后更新 Task 实例：

- `status` → `closed`
- `closed_at` → 当前时间
- `closure_evidence` → 保留已填写的关闭证据

### 5. 检查关联 Intent

读取 Task 关联的 Intent 实例，检查该 Intent 下所有 Task 是否均已 `closed`：

- 全部 `closed` → 提示用户是否将 Intent 状态更新为 `completed`；
- 存在非 `closed` Task → 不触发 Intent 状态变更。

### 6. 记录 Change

按 `specs/22-Change-变更记录.md` 格式记录本次变更。

## 输出格式

执行完成后，AI 输出结构化结果：

- 读取的 Task 实例路径和当前状态
- 校验结果（closure_evidence、Evidence 验证结果）
- 是否触发 Human Gate 及用户决策
- 待更新文件列表和影响范围
- Intent 级联检查结果

## Human Gate

关闭 Task 时**必须**通过 AskUserQuestion 确认：

- 展示 Task 摘要（标题、状态、closure_evidence、关联 Evidence 结果）
- 用户选择：
  - **确认关闭** → 执行状态更新
  - **退回** → Task 状态更新为 `executing`，记录退回原因
  - **取消** → 停止流程，不修改任何事实源

## 事实源回写

- Task 实例更新 → `ldvh-base/tasks/task-{NNNN}-short-title.yaml`
- Intent 状态变更（如触发）→ `ldvh-base/intents/intent-{NNNN}-short-title.yaml`
- 所有变更记录 Change（按 `specs/22-Change-变更记录.md` 格式）

## Agent 边界

Skill 不调度 Agent。如需多角色独立审查，建议用户或主控评估是否使用 Agent。
