---
name: "ldvh-intake"
description: "承接 LDVH Core Loop Intent 阶段，从意图识别到 Intent/Task 草案创建。当用户表达明确目标或意图、AI 需判断是否创建 Intent/Task 时触发。"
---

# LDVH Intake Skill

## 定位

本 Skill 承接 LDVH Core Loop 的 Intent 阶段，用于在用户表达意图时，由 AI 主控应用，完成从意图识别到 Intent/Task 草案创建的流程。

本 Skill 是部署在项目 `.trae/skills/ldvh-intake/SKILL.md` 的 LDVH Skill。Skill 实体不是事实源，不重新定义 Intent/Task 准入条件、字段契约或 Human Gate。发生冲突时，以 `ld-vibe-harness/specs/24-Intent-意图.md`、`ld-vibe-harness/specs/31-Task-任务.md`、`ld-vibe-harness/specs/24.06-Contract.md` 和 `ld-vibe-harness/specs/31.06-Contract.md` 为准。

## 触发条件

在以下场景由 AI 主控应用本 Skill：

1. 用户表达了明确目标或意图；
2. AI 需要判断是否应创建 Intent 或 Task；
3. 用户要求创建 Intent 或 Task。

## 不适用场景

1. 用户只是闲聊或提问，没有可执行目标；
2. 用户要求修改现有 Intent/Task（不是创建新的）；
3. 当前已有 Task 在执行中，用户只是追加指示。

## 必读文件

执行本 Skill 前，AI 必须读取以下事实源：

- `ld-vibe-harness/specs/24-Intent-意图.md` — Intent 准入条件和字段契约
- `ld-vibe-harness/specs/31-Task-任务.md` — Task 准入条件和字段契约
- `ld-vibe-harness/specs/24.06-Contract.md` — Intent YAML schema
- `ld-vibe-harness/specs/31.06-Contract.md` — Task YAML schema

读取方式：先搜索章节标题定位目标段落，再按行范围读取；不得全文读取超过 200 行。

## 编排流程

### 1. 识别场景

AI 判断用户意图是否满足 Intent 准入条件：

- 跨任务追踪：意图涉及多个 Task 的协调
- 影响范围超出单次操作：意图的完成需要多次操作或跨会话
- 需要跨会话连续性：意图的推进需要在不同会话中持续

满足任一条件 → 进入 Intent + Task 草案创建分支
均不满足 → 进入仅 Task 草案创建分支

### 2. 创建草案

**分支 A：满足 Intent 准入条件**

1. 按 `24.06-Contract.md` 创建 Intent 草案，填写必填字段
2. 按 `31.06-Contract.md` 创建关联 Task 草案，填写必填字段
3. Task 的 `parent` 引用 Intent

**分支 B：不满足 Intent 准入条件**

1. 按 `31.06-Contract.md` 创建 Task 草案，填写必填字段
2. Task 无 `parent` 引用

### 3. Human Gate 确认

AI 调用 AskUserQuestion，展示：

- 草案内容（Intent 和/或 Task）
- 准入条件判断依据
- 待写入文件路径

用户确认后继续。用户修改则调整草案后重新确认。用户取消则停止流程。

### 4. 写入事实源

确认后写入：

- Intent 实例 → `ldvh-base/intents/intent-{NNNN}-short-title.yaml`
- Task 实例 → `ldvh-base/tasks/task-{NNNN}-short-title.yaml`

### 5. 记录 Change

按 `specs/22-Change-变更记录.md` 格式记录变更。

## 输出格式

每次执行本 Skill 后，AI 应明确输出：

- **输入来源**：用户意图的原始表述
- **读取的事实源**：实际读取的规范文件
- **分析结论**：是否满足 Intent 准入条件及判断依据
- **建议动作**：创建 Intent + Task 或仅创建 Task
- **Human Gate**：是否触发、用户响应
- **待写入文件**：文件路径和影响范围

## Human Gate

创建 Intent 或 Task 时必须通过 AskUserQuestion 确认：

- 展示草案完整内容
- 展示准入条件判断依据
- 用户确认 → 继续写入
- 用户修改 → 调整草案后重新确认
- 用户取消 → 停止流程

## 事实源回写

- Intent 实例写入 `ldvh-base/intents/intent-{NNNN}-short-title.yaml`
- Task 实例写入 `ldvh-base/tasks/task-{NNNN}-short-title.yaml`
- 状态变更记录 Change（按 `specs/22-Change-变更记录.md` 格式）

## Agent 边界

本 Skill 不调度 Agent。如需多角色独立判断，建议用户或主控评估是否使用 Agent。
