# LDVH 生产对象与 Trae Spec/Plan 对接评估

> 创建日期：2026-06-04
> 定位：评估 LDVH 生产对象体系与 Trae SOLO Spec/Plan 工作流的对接可能性，分析映射关系、差距和增强方案
> 上位依据：`specs/20-事实模型集合索引.md`、`specs/13-LDVH事实模型基础规范.md`、`specs/27-Task-任务.md`、`specs/24-Intent-意图.md`
> 相关评估：`specs/evals/02-LDVH对gstack的借鉴评估.md`、`specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`

---

## 1. 本文解决的问题

LDVH 已建立 Intent → Task 的生产对象体系，Trae SOLO 内置了 Spec → Plan 的结构化工作流。两者在"先规划后执行"的理念上高度一致，但在对象粒度、文档结构、确认流程和状态追踪上存在差距。本文评估：

1. LDVH 生产对象与 Trae Spec 三文档的映射关系；
2. LDVH Task 对象与 Trae Spec 规范化能力的差距；
3. 如何让 LDVH Task 像 Trae Spec 一样具备结构化规划、分阶段确认和自动状态追踪；
4. 对接方案和实施路径。

---

## 2. Trae Spec/Plan 工作流核心机制

### 2.1 Spec 三文档结构

| 文档 | 定位 | 核心内容 | 类比 |
|------|------|---------|------|
| `spec.md` | 需求大纲（北极星文档） | Why / What Changes / Impact / Requirements（ADDED / MODIFIED / REMOVED） | 概设 |
| `tasks.md` | 任务拆解（开发排期表） | Task / SubTask checkbox 列表 + Task Dependencies | 详设 |
| `checklist.md` | 验收清单（完整性核查表） | 验收项 checkbox 列表 | 验收 |

存储位置：`.trae/specs/<任务名称>/`，可纳入版本控制。

### 2.2 Plan 单文档结构

Plan 是 Spec 的轻量版，生成单份 `plan.md`，存储在 `.trae/documents/`，适用于中小型任务。

### 2.3 Spec 核心能力（LDVH 需要对标的能力）

| 能力 | 描述 | LDVH 当前状态 |
|------|------|--------------|
| 结构化规划 | 三文档分离：需求大纲 → 任务拆解 → 验收清单 | Intent 有 description + success_criteria，但无结构化大纲 |
| 分阶段确认 | spec → tasks → checklist 逐份确认后才执行 | Task 有 Human Gate，但无分阶段确认 |
| 自动状态追踪 | tasks.md 中 `[ ]` → `[x]` 自动更新 | Task 有状态机，但 acceptance 是静态 YAML 字段 |
| 需求变更追踪 | ADDED / MODIFIED / REMOVED Requirements | 无结构化变更追踪 |
| 影响范围声明 | Impact 章节：受影响的 specs / code / docs / facts | 无显式影响范围声明 |
| 任务依赖声明 | Task Dependencies 章节 | 无依赖声明（Dependency 已降级为字段候选） |

---

## 3. LDVH 生产对象与 Spec 三文档映射

### 3.1 核心映射

| Trae Spec 文档 | LDVH 对象 | 映射关系 | 差距 |
|----------------|----------|---------|------|
| `spec.md` Why | Intent `description` | Intent 记录人的原始目标和约束 | Intent 缺少结构化的 Why / What Changes / Impact 章节 |
| `spec.md` What Changes | 无直接对应 | Intent 的 `description` 可包含变更描述 | 无结构化变更清单 |
| `spec.md` Impact | 无直接对应 | — | 缺少显式影响范围声明 |
| `spec.md` Requirements | Intent `success_criteria` + Task `acceptance` | 分散在两个对象中 | Intent 只有 success_criteria，无 ADDED/MODIFIED/REMOVED 分类 |
| `tasks.md` | Task + sub_tasks | Task 是最小执行单元，子任务是纵向分解 | Task 缺少依赖声明和 checkbox 自动追踪 |
| `checklist.md` | Task `acceptance` | acceptance 是验收标准字段 | acceptance 是 YAML 字段而非 Markdown checkbox，无自动状态追踪 |

### 3.2 对象级映射

| LDVH 对象 | Trae Spec 对应 | 说明 |
|-----------|---------------|------|
| Intent | `spec.md` 的角色 | Intent 承载目标、约束和成功标准，与 spec.md 的 Why + Requirements 对应 |
| Task | `tasks.md` 中单个 Task/SubTask | Task 承载执行单元，与 tasks.md 中的条目对应 |
| Task `acceptance` | `checklist.md` | Task 的验收标准与 checklist.md 的验收项对应 |
| Task `sub_tasks` | `tasks.md` 中的 SubTask | 子任务与 SubTask 对应 |
| Intent `related_tasks` | `tasks.md` 的 Task 列表 | Intent 关联的任务列表与 tasks.md 的任务列表对应 |
| ADR | `spec.md` 中的决策记录 | ADR 记录长期决策，与 spec.md 中隐含的架构决策对应 |
| Memo | 无直接对应 | Memo 是 LDVH 独有的信息暂存对象 |
| Profile | 无直接对应 | Profile 是 LDVH 独有的项目身份对象 |
| Pitfall | 无直接对应 | Pitfall 是 LDVH 独有的经验沉淀对象 |
| Change | Git commit | Change 与 Trae 的 Git 事实源一致 |

### 3.3 映射结论

**LDVH 的 Intent + Task 组合可以覆盖 Trae Spec 三文档的核心语义，但缺少 Spec 的结构化表达力和流程控制力。**

- Intent ≈ spec.md（但缺少结构化章节）
- Task + acceptance ≈ tasks.md + checklist.md（但缺少 checkbox 追踪和依赖声明）
- LDVH 独有的 ADR / Memo / Profile / Pitfall / Change 是 Trae Spec 不具备的治理层

---

## 4. 差距分析：为什么 Task 不如 Spec 规范

### 4.1 结构化差距

| 维度 | Trae Spec | LDVH Task | 差距本质 |
|------|-----------|-----------|---------|
| 需求大纲 | spec.md 有 Why / What Changes / Impact / Requirements 结构 | Intent 只有 description + success_criteria | Intent 缺少结构化章节模板 |
| 任务拆解 | tasks.md 有 Task / SubTask 层级 + Dependencies | Task 有 sub_tasks 但无依赖声明 | 缺少横向依赖关系 |
| 验收清单 | checklist.md 独立文档，checkbox 自动追踪 | acceptance 是 YAML 字段，手动填写 | 验收项无自动状态追踪 |
| 变更追踪 | ADDED / MODIFIED / REMOVED Requirements | 无 | 缺少需求变更分类 |
| 影响范围 | Impact 章节显式声明 | 无 | 缺少影响范围声明 |

### 4.2 流程控制差距

| 维度 | Trae Spec | LDVH Task | 差距本质 |
|------|-----------|-----------|---------|
| 确认流程 | 三阶段逐份确认 | 单次 Human Gate | Spec 有更细粒度的确认控制 |
| 确认选项 | 确认执行 / 取消（平台 UI） | AskUserQuestion（自由形式） | Spec 有平台级 UI，LDVH 靠 Skill 模拟 |
| 执行追踪 | tasks.md checkbox 自动更新 | Task 状态机手动流转 | Spec 有自动进度追踪 |
| 纠偏机制 | 用户可随时修改 spec 文档 | Task 字段修改需 Human Gate | Spec 更灵活，LDVH 更严谨 |

### 4.3 根因分析

差距的根因不是 LDVH 对象模型设计不足，而是**LDVH 和 Trae Spec 服务于不同层级**：

- **Trae Spec**：面向开发任务的结构化规划工具，目标是"先定规范再写代码"
- **LDVH Task**：面向 AI 协作治理的事实对象，目标是"跨会话可追溯、可验收、可审计"

Trae Spec 是**过程工具**（帮助人理清思路），LDVH Task 是**治理对象**（确保 AI 行为可追溯）。两者不是替代关系，而是互补关系。

---

## 5. 增强方案：让 Task 具备 Spec 级规范化能力

### 5.1 方案概述

不改变 Task 对象模型的核心结构，通过**字段增强 + Skill 流程封装**让 Task 具备 Spec 级规范化能力。

核心思路：**Intent 承接 spec.md 角色，Task 承接 tasks.md 角色，Task.acceptance 承接 checklist.md 角色。**

### 5.2 Intent 增强：结构化大纲

为 Intent 增加结构化大纲字段，使其具备 spec.md 的表达力：

| 新增/增强字段 | 类型 | 对应 Spec 章节 | 说明 |
|--------------|------|---------------|------|
| `why` | string | spec.md Why | 项目背景和动机 |
| `what_changes` | list of string | spec.md What Changes | 变更清单 |
| `impact` | list of string | spec.md Impact | 影响范围 |
| `requirements_added` | list of string | spec.md ADDED Requirements | 新增需求 |
| `requirements_modified` | list of string | spec.md MODIFIED Requirements | 修改需求 |
| `requirements_removed` | list of string | spec.md REMOVED Requirements | 删除需求 |

增强后的 Intent YAML 示例：

```yaml
id: intent-0001
type: intent
title: LDVH Task 对象规范化
status: active
created: 2026-06-04
updated: 2026-06-04
description: 让 LDVH Task 具备 Trae Spec 级规范化能力
why: 当前 Task 对象缺少结构化规划、分阶段确认和自动状态追踪
what_changes:
  - Intent 增加结构化大纲字段
  - Task 增加依赖声明和验收追踪
  - 创建 ldvh-spec Skill 封装规划流程
impact:
  - specs/24-Intent-意图.md
  - specs/27-Task-任务.md
  - specs/27.06-Contract.md
success_criteria: Task 对象具备结构化规划、分阶段确认和验收追踪能力
requirements_added:
  - Intent SHALL 支持 why/what_changes/impact 结构化字段
  - Task SHALL 支持 dependencies 字段声明任务依赖
  - Task acceptance SHALL 支持 checkbox 状态追踪
requirements_modified: []
requirements_removed: []
source: 用户在 2026-06-04 会话中提出
related_tasks:
  - task-0001
  - task-0002
related_adrs: []
```

### 5.3 Task 增强：依赖声明和验收追踪

| 新增/增强字段 | 类型 | 对应 Spec 能力 | 说明 |
|--------------|------|---------------|------|
| `dependencies` | list of object | tasks.md Task Dependencies | `{depends_on: task-XXXX, reason: string}` |
| `acceptance` 格式增强 | string（Markdown checkbox） | checklist.md 自动追踪 | 验收项使用 `- [ ]` / `- [x]` 格式，AI 执行时自动更新 |

增强后的 Task YAML 示例：

```yaml
id: task-0001
type: task
title: Intent 增加结构化大纲字段
status: planned
created: 2026-06-04
updated: 2026-06-04
description: 为 Intent 对象增加 why/what_changes/impact/requirements_* 结构化字段
source_intent: intent-0001
source: intent-0001
acceptance: |
  - [ ] specs/24-Intent-意图.md 已更新结构化大纲字段
  - [ ] specs/24.06-Contract.md 已更新 YAML schema
  - [ ] 至少一个 Intent 实例已使用新字段格式
verification: 读取更新后的规范和实例，确认字段存在且格式正确
dependencies:
  - depends_on: null  # 无前置依赖
    reason: 本任务是首个任务
related_adrs: []
related_changes: []
```

### 5.4 Skill 封装：ldvh-spec Skill

创建 `ldvh-spec` Skill，封装类似 Trae Spec 的结构化规划流程：

**Skill 触发条件**：用户表达复杂意图，需要结构化规划时触发。

**Skill 流程**：

```
1. 规划阶段
   ├─ AI 分析用户意图，生成 Intent 草案（含 why/what_changes/impact/requirements_*）
   ├─ AskUserQuestion：确认 / 仅保存 / 修改后确认 / 部分执行
   └─ 用户确认后 Intent 进入 active

2. 拆解阶段
   ├─ AI 基于 Intent 拆解 Task 列表（含 dependencies 和 acceptance）
   ├─ AskUserQuestion：确认 / 仅保存 / 修改后确认 / 部分执行
   └─ 用户确认后 Task 进入 planned

3. 执行阶段
   ├─ AI 按 Task 依赖顺序执行
   ├─ 每完成一个验收项，更新 acceptance 中的 [ ] → [x]
   ├─ Task 完成后进入 verifying → review_needed → closed
   └─ Intent 的 related_tasks 自动更新

4. 验收阶段
   ├─ AI 检查所有 Task 的 acceptance 是否全部 [x]
   ├─ AI 检查 Intent 的 success_criteria 是否满足
   └─ AskUserQuestion：确认完成 / 需要返工
```

**Skill 确认选项**（解决"只有执行和取消"的问题）：

| 选项 | 行为 | 对应场景 |
|------|------|---------|
| 确认执行 | 按计划全部执行 | 规划符合预期 |
| 仅保存 | 保存文档但不执行，后续手动触发 | 规划 OK 但现在不想执行 |
| 修改后确认 | 用户指定修改点，AI 修改后再确认 | 规划基本 OK 但需要调整 |
| 部分执行 | 用户选择要执行的任务子集 | 只想先做一部分 |

### 5.5 与 Trae 原生 Spec/Plan 的关系

| 维度 | Trae 原生 Spec/Plan | ldvh-spec Skill |
|------|---------------------|-----------------|
| 触发方式 | `/spec` `/plan` 命令 | Skill 自动匹配或用户指示 |
| 产物格式 | `.trae/specs/` Markdown 文件 | `ldvh-base/` YAML 事实源 |
| 确认 UI | 平台级确认界面 | AskUserQuestion |
| 状态追踪 | tasks.md checkbox 自动更新 | Task YAML acceptance 字段自动更新 |
| 治理能力 | 无 ADR / Change / Pitfall 关联 | 完整 LDVH 治理链 |
| 跨会话追踪 | 依赖 `.trae/specs/` 文件 | 依赖 Git 事实源 |
| 确认选项 | 确认 / 取消 | 确认执行 / 仅保存 / 修改后确认 / 部分执行 |

**ldvh-spec Skill 不替代 Trae 原生 Spec/Plan，而是补充治理层能力。** 对于不需要 LDVH 治理的简单项目，继续使用原生 Spec/Plan；对于需要 LDVH 治理的项目，使用 ldvh-spec Skill。

---

## 6. 对接路径

### 6.1 Phase 1：字段增强（最小可用）

1. 为 Intent 增加 `why`、`what_changes`、`impact`、`requirements_added`、`requirements_modified`、`requirements_removed` 字段
2. 为 Task 增加 `dependencies` 字段
3. 更新 `specs/24.06-Contract.md` 和 `specs/27.06-Contract.md`
4. 不改变现有状态机和 Human Gate

### 6.2 Phase 2：Skill 封装

1. 创建 `ldvh-spec` Skill，封装规划 → 拆解 → 执行 → 验收四阶段流程
2. Skill 内实现自定义确认选项（确认执行 / 仅保存 / 修改后确认 / 部分执行）
3. Skill 内实现 acceptance checkbox 自动更新

### 6.3 Phase 3：与 Trae Spec 互操作

1. ldvh-spec Skill 可读取 `.trae/specs/` 下已有的 Spec 文档作为输入
2. ldvh-spec Skill 可将 Intent + Task 结构导出为 Trae Spec 三文档格式
3. 实现双向桥接：Trae Spec 文档 ↔ LDVH 事实源

---

## 7. 风险与约束

| 风险 | 缓解措施 |
|------|---------|
| Intent 字段膨胀导致精简版规范变重 | 新字段均为可选，不影响现有实例 |
| Skill 确认选项增加交互复杂度 | 默认推荐"确认执行"，其他选项为高级操作 |
| acceptance checkbox 格式与 YAML 兼容性 | acceptance 字段使用多行字符串，内部用 Markdown checkbox |
| 与 Trae 原生 Spec 功能重叠 | 明确边界：原生 Spec 面向开发任务，ldvh-spec 面向治理任务 |
| Task dependencies 字段与 deferred Dependency 对象冲突 | dependencies 是 Task 内嵌字段，不等同于独立 Dependency 对象 |

---

## 8. 结论

1. **LDVH 的 Intent + Task 组合可以覆盖 Trae Spec 三文档的核心语义**，但缺少结构化表达力和流程控制力
2. **差距的根因是层级不同**：Trae Spec 是过程工具，LDVH Task 是治理对象，两者互补而非替代
3. **通过字段增强 + Skill 封装**，可以让 Task 具备 Spec 级规范化能力，同时保持 LDVH 治理链完整性
4. **ldvh-spec Skill 的自定义确认选项**解决了 Trae Spec"只有执行和取消"的问题
5. **对接路径分三阶段**：字段增强 → Skill 封装 → 与 Trae Spec 互操作
