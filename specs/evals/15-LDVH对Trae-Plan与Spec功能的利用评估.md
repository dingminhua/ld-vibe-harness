# Trae Plan 与 Spec 功能深度分析：LDVH 优化利用方案

> 创建日期：2026-06-03
> 定位：分析 Trae IDE 原生 Plan/Spec 功能机制，提出 LDVH 更好利用这两个功能的具体方案
> 状态：draft

---

## 1. Trae Plan 功能深度解析

### 1.1 核心机制

Trae Plan 模式是 SOLO Coder 内置的任务规划机制，核心理念是**"先计划，再动手"**。启用后，AI 不会直接写代码，而是先生成一份结构化开发计划，经用户审阅确认后才执行。

**三阶段闭环流程：**

| 阶段 | AI 行为 | 人的角色 |
|------|---------|---------|
| 规划 | 分析需求，拆解任务，生成开发计划文档 | 审阅者 |
| 确认 | 等待用户审阅、修改、批准 | 决策者（握否决权） |
| 执行 | 按确认后的计划逐步执行，DiffView 可视化 | 监督者（可回滚） |

**计划文档核心内容：**
- 待完成任务清单（拆分具体步骤）
- 技术选型建议
- 待修改文件列表及依赖关系
- 潜在风险预警

### 1.2 关键特性

1. **可编辑性**：计划文档可直接手动编辑，也可用自然语言让 AI 修改
2. **只读安全**：规划阶段 AI 只读取代码，不修改任何文件
3. **可视化追踪**：执行阶段通过 DiffView 逐文件展示变更
4. **一键回滚**：不符合预期可回退到对话前状态
5. **执行总结报告**：完成后生成报告，说明完成的任务、修改的文件、测试结果

### 1.3 适用场景

- Bug 修复
- 接口改造
- 跨模块变更
- 代码重构
- 中小型功能开发

### 1.4 限制

- 仅在 SOLO 模式下生效
- 计划质量依赖需求描述的精确度
- 复杂项目（30+ 文件跨模块）建议拆分为多个子任务
- 不生成持久化文档资产（计划随对话结束而消失）

---

## 2. Trae Spec 功能深度解析

### 2.1 核心机制

Trae Spec 模式面向更复杂的系统级任务，理念类似软件工程中的**"概设→详设→验收"**流程。开启后自动生成三份标准化文档：

| 文档 | 定位 | 内容 |
|------|------|------|
| `spec.md` | 大纲文档 | 项目背景、整体架构、技术选型、系统边界等高层设计 |
| `tasks.md` | 任务列表 | 宏观需求拆分为细粒度可执行任务，类似"开发排期表" |
| `checklist.md` | 验收清单 | 关键功能点验收对照表，含前后端逻辑、UI 细节、异常处理 |

**存储位置**：`.trae/specs/<spec-name>/` 目录，可作为项目知识资产进行版本控制。

**状态自动更新**：任务列表和验收清单的状态随 AI 执行进度自动更新。

### 2.2 关键特性

1. **三文档分离**：大纲、任务、验收各司其职，层次清晰
2. **持久化资产**：文档存储在项目目录中，不随对话消失
3. **版本可控**：可纳入 Git 管理，作为项目知识资产
4. **进度追踪**：任务和验收状态自动更新
5. **可复用**：后续维护可直接引用 Spec 文档

### 2.3 适用场景

- 从零搭建新系统/模块
- 大规模重构
- 多人协作项目（Spec 文档作为"单一事实来源"）
- 高质量/高稳定性项目（支付、安全模块）
- 需长期维护的项目

### 2.4 限制

- 仅在 SOLO 模式下生效
- 三文档结构与 LDVH 现有规范体系不完全对齐
- 文档格式由 Trae 内置模板决定，自定义空间有限
- 不直接与 LDVH 的事实模型（Intent、Task、Evidence 等）关联

---

## 3. Plan 与 Spec 的对比

| 维度 | Plan 模式 | Spec 模式 |
|------|-----------|-----------|
| 复杂度定位 | 中小型任务 | 系统级复杂任务 |
| 产出物 | 临时性计划文档（对话内） | 持久化三文档（spec/tasks/checklist） |
| 文档生命周期 | 随对话结束消失 | 持久化在 `.trae/specs/` |
| 可编辑性 | 对话内编辑 | 文件级编辑 |
| 验收机制 | 执行总结报告 | checklist.md 验收清单 |
| 与 LDVH 对象对应 | 无直接对应 | spec≈Intent, tasks≈Task, checklist≈Evidence |
| 人工干预点 | 确认阶段 | 三阶段均可干预 |

---

## 4. LDVH 当前对 Plan/Spec 的使用现状

### 4.1 已有使用痕迹

LDVH 项目在 `.trae/specs/` 下已有两个 Spec 实例：

1. **investigate-infra-tools-doc-format**：基础设施工具设计文档格式兼容性调查
2. **migrate-temp-to-specs**：temp 目录文档迁入 specs 规范

这说明 LDVH 已经尝试使用 Spec 模式，但使用频率低，且未与 LDVH 自身的事实模型体系深度整合。

### 4.2 当前工作流特点

LDVH 当前工作流以**规范驱动**为核心：

1. **Rules 体系**（L0→L1→L2）控制 AI 行为边界
2. **事实模型**（ADR、Change、Pitfall、Intent、Evidence、Task）管理项目事实
3. **Human Gate** 在关键节点要求人工确认
4. **ldvh-commit Skill** 编排提交流程
5. **ldvh-adr Skill** 编排 ADR 生命周期

### 4.3 当前痛点

1. **Plan 模式与 LDVH 行动模型未打通**：Plan 的"规划-确认-执行"与 LDVH 行动模型的 Context→Scenario→Gate→执行流程高度相似，但各自独立运行
2. **Spec 模式的三文档与 LDVH 事实模型不对齐**：spec.md 对应 Intent、tasks.md 对应 Task、checklist.md 对应 Evidence，但格式和字段不统一
3. **Plan 产出不持久化**：Plan 的计划文档随对话消失，无法作为 LDVH 事实源回写
4. **Spec 产出未纳入 ldvh-base/**：Spec 文档存在 `.trae/specs/` 而非 `ldvh-base/`，不在 LDVH 事实源边界内
5. **缺少从 Plan/Spec 到 LDVH 对象的转化机制**：Plan 的计划无法自动转化为 LDVH Task，Spec 的验收清单无法自动关联 LDVH Evidence

---

## 5. LDVH 更好利用 Plan 功能的方案

### 5.1 方案一：Plan 作为 LDVH 行动模型的"轻量前置"

**核心思路**：将 Plan 模式定位为 LDVH 行动模型执行的"轻量前置检查"，在 AI 进入行动模型定义的执行流程前，先用 Plan 生成执行计划供人确认。

**具体做法：**

1. **在 Rules 中增加 Plan 前置规则**：当任务涉及 `ldvh-base/` YAML 编辑、specs 修改或 ADR 写入时，L0/L1 规则要求 AI 先进入 Plan 模式
2. **Plan 输出映射到行动模型 Context**：Plan 的任务清单对应行动模型的 Context 要求，风险预警对应 Gate 触发条件
3. **Plan 确认替代部分 Human Gate**：对于低风险变更，Plan 确认可替代 AskUserQuestion 的 Human Gate；对于高风险变更，Plan 确认后再触发 AskUserQuestion

**优势**：
- Plan 的"只读安全"特性与 LDVH 行动模型的"Context 最小可行动"原则一致
- Plan 确认阶段天然是 Human Gate 的承载点
- 无需修改 LDVH 现有规范体系

**风险**：
- Plan 产出不持久化，无法作为事实源回写
- Plan 模式仅在 SOLO 模式下生效，Chat 模式无法使用

### 5.2 方案二：Plan 确认后回写 ldvh-base/tasks/

**核心思路**：Plan 确认后，将计划中的任务项回写到 `ldvh-base/tasks/` 作为 LDVH Task 事实实例，实现 Plan 产出的持久化和可追溯。

**具体做法：**

1. Plan 确认后，AI 按 LDVH Task 规范（specs/31）将每个任务项写入 `ldvh-base/tasks/` YAML
2. Task 的 `source` 字段标记为 `plan-mode`
3. Plan 执行过程中，Task 状态随执行进度更新
4. 执行完成后，Evidence 回写到 `ldvh-base/evidence/`

**优势**：
- Plan 产出持久化为 LDVH 事实源
- 与现有 Task 生命周期管理一致
- 可通过 `ldvh-commit` Skill 提交

**风险**：
- 需要修改 L0 规则增加 Plan→Task 回写逻辑
- 小型任务可能不需要如此重的流程

### 5.3 方案三：分级使用 Plan

**核心思路**：根据任务复杂度和风险等级，决定是否启用 Plan 模式以及 Plan 产出是否回写。

| 任务等级 | Plan 使用方式 | 回写策略 |
|----------|--------------|---------|
| 低风险（文档修正、格式调整） | 不启用 Plan | 无需回写 |
| 中风险（功能开发、接口改造） | 启用 Plan，确认后执行 | 不回写，仅对话内追踪 |
| 高风险（specs 修改、ADR 写入、跨模块重构） | 启用 Plan，确认后执行 | 回写 Task 到 ldvh-base/tasks/ |

**优势**：
- 灵活，避免过度流程化
- 高风险任务有完整事实源追踪
- 低风险任务保持高效

---

## 6. LDVH 更好利用 Spec 功能的方案

### 6.1 方案一：Spec 三文档与 LDVH 事实模型对齐

**核心思路**：建立 Spec 三文档与 LDVH 事实模型的映射关系，并在 Rules 中定义转化规则。

**映射关系：**

| Spec 文档 | LDVH 事实模型 | 转化规则 |
|-----------|--------------|---------|
| `spec.md` | Intent（specs/24） | spec.md 的 Why/What Changes/Impact 对应 Intent 的目标、范围、成功标准 |
| `tasks.md` | Task（specs/31） | tasks.md 的每个任务项对应一个 Task 实例 |
| `checklist.md` | Evidence（specs/28） | checklist.md 的验收项对应 Evidence 的验证结果 |

**具体做法：**

1. Spec 完成后，AI 按 LDVH 规范将 spec.md 转化为 `ldvh-base/intents/` YAML
2. tasks.md 的每个任务项转化为 `ldvh-base/tasks/` YAML
3. checklist.md 的验收项在执行完成后转化为 `ldvh-base/evidence/` YAML
4. 转化过程需要 Human Gate 确认

**优势**：
- Spec 产出成为 LDVH 事实源的一部分
- 与现有事实模型体系完全一致
- 可通过 `ldvh-commit` Skill 提交

**风险**：
- 转化过程增加工作量
- Spec 模板格式与 LDVH YAML 格式不完全匹配，需要 AI 做格式转换

### 6.2 方案二：将 `.trae/specs/` 纳入 LDVH 事实源边界

**核心思路**：修改 LDVH 事实源边界规范（specs/10），将 `.trae/specs/` 目录认定为 LDVH 事实源的一部分，无需转化即可作为事实源使用。

**具体做法：**

1. 修改 specs/10，增加 `.trae/specs/` 作为事实源承载位置
2. 定义 `.trae/specs/` 的准入条件：仅限通过 Spec 模式生成的文档
3. 定义 `.trae/specs/` 与 `ldvh-base/` 的关系：Spec 文档是"规划态"事实源，ldvh-base/ 是"执行态"事实源
4. Spec 确认后，相关条目从"规划态"推进到"执行态"（写入 ldvh-base/）

**优势**：
- 无需格式转换，直接利用 Spec 原生产出
- Spec 文档天然是"规划态"，与 LDVH 的 Intent→Task→Evidence 流程一致
- 修改量小，只需调整事实源边界定义

**风险**：
- `.trae/specs/` 的格式由 Trae 控制，LDVH 无法完全约束
- 与 LDVH "Git 文件事实源"原则一致但增加了新的目录层级

### 6.3 方案三：Spec 作为 LDVH 新事实模型创建的前置流程

**核心思路**：将 Spec 模式定位为 LDVH 新事实模型（如 25-Memo、26-Risk、27-Dependency 等 planned 状态对象）创建前的标准前置流程。

**具体做法：**

1. 当需要创建新的 LDVH 事实模型规范时，先启用 Spec 模式
2. Spec 的 spec.md 承载新事实模型的定位、架构和边界设计
3. Spec 的 tasks.md 承载规范创建的具体任务拆分
4. Spec 的 checklist.md 承载规范完成后的验收标准
5. Spec 确认后，按计划执行规范创建，产出写入 specs/

**优势**：
- 为 planned 状态对象（25-32）的创建提供标准化流程
- Spec 产出本身就是规范创建过程的证据
- 与 LDVH "先规划再执行"的理念高度一致

**风险**：
- 不是所有规范创建都需要 Spec 级别的规划
- 可能过度流程化简单规范的创建

---

## 7. 综合推荐方案

### 7.1 核心原则

1. **不替代，只增强**：Plan/Spec 不替代 LDVH 现有的 Rules/事实模型/Skill 体系，而是作为增强层
2. **分级使用**：根据任务复杂度和风险等级选择使用方式
3. **事实源对齐**：Plan/Spec 的关键产出应能回写为 LDVH 事实源
4. **最小修改**：对现有 LDVH 规范体系的修改应最小化

### 7.2 推荐的 Plan 使用策略

| 场景 | 推荐做法 |
|------|---------|
| 编辑 ldvh-base/ YAML | 先 Plan，确认后执行；高风险变更回写 Task |
| 修改 specs/ 规范 | 先 Plan，确认后执行；变更记录按 specs/22 执行 |
| ADR 写入/状态流转 | 先调用 ldvh-adr Skill，Skill 内部可使用 Plan |
| Bug 修复、接口改造 | 启用 Plan，确认后执行 |
| 简单文档修正 | 不启用 Plan，直接执行 |

**Rules 修改建议**：在 L0 规则中增加 Plan 使用指引：

```
## Plan 模式使用指引

编辑 ldvh-base/ YAML 或修改 specs/ 规范前，评估任务风险等级：
- 高风险（跨模块、状态流转、ADR 写入）：启用 Plan 模式，确认后执行
- 中风险（功能开发、接口改造）：建议启用 Plan 模式
- 低风险（文档修正、格式调整）：可选启用 Plan 模式

Plan 确认阶段可替代部分低风险 Human Gate。
高风险 Human Gate 仍须通过 AskUserQuestion 执行。
```

### 7.3 推荐的 Spec 使用策略

| 场景 | 推荐做法 |
|------|---------|
| 创建新事实模型规范（25-32 planned 对象） | 启用 Spec，三文档作为规范设计的前置产出 |
| 大规模重构（30+ 文件） | 启用 Spec，tasks.md 拆分子任务 |
| 新系统/模块搭建 | 启用 Spec，spec.md 承载架构设计 |
| Spec 完成后 | 将 spec.md 关键信息回写为 ldvh-base/intents/ YAML |

**Rules 修改建议**：在 L0 规则中增加 Spec 使用指引：

```
## Spec 模式使用指引

以下场景建议启用 Spec 模式：
- 创建新事实模型规范（planned 对象升级为 active）
- 涉及 30+ 文件的大规模重构
- 从零搭建新系统/模块

Spec 完成后，应将 spec.md 的核心信息（目标、范围、成功标准）回写为
ldvh-base/intents/ YAML，纳入 LDVH 事实源体系。
回写过程需要 Human Gate 确认。
```

### 7.4 Plan/Spec 与 LDVH 体系的整合路径

```
用户需求
    │
    ├─ 低风险 ──→ 直接执行（现有 Rules 体系）
    │
    ├─ 中风险 ──→ Plan 模式 ──→ 确认 ──→ 执行 ──→ Change 记录
    │
    └─ 高风险/系统级 ──→ Spec 模式 ──→ 三文档确认 ──┐
                                                       │
                    ┌──────────────────────────────────┘
                    │
                    ├─ spec.md ──→ 回写 ldvh-base/intents/ (Intent)
                    ├─ tasks.md ──→ 回写 ldvh-base/tasks/ (Task)
                    └─ checklist.md ──→ 执行后回写 ldvh-base/evidence/ (Evidence)
```

---

## 8. 实施建议

### 8.1 短期（立即可做）

1. **在 L0 规则中增加 Plan/Spec 使用指引**：按 7.2 和 7.3 的建议修改 `ldvh-l0-rules.md`
2. **对高风险任务强制 Plan**：编辑 `ldvh-base/` YAML 时，L0 事实模型规则要求先 Plan
3. **Spec 完成后手动回写 Intent**：作为习惯培养，Spec 完成后将核心信息写入 `ldvh-base/intents/`

### 8.2 中期（规范稳定后）

1. **定义 Spec→LDVH 对象的自动转化规则**：在 Rules 中定义 spec.md→Intent、tasks.md→Task 的字段映射
2. **将 `.trae/specs/` 纳入事实源边界**：修改 specs/10，增加 Spec 产出的事实源地位
3. **创建 Plan/Spec 适配的 Skill**：类似 `ldvh-adr` Skill，创建 `ldvh-plan` 和 `ldvh-spec` Skill 编排流程

### 8.3 长期（体系成熟后）

1. **Plan 确认与 Human Gate 合并**：低风险场景 Plan 确认替代 AskUserQuestion，高风险场景两者串联
2. **Spec 作为新事实模型创建的标准前置**：所有 planned 对象升级为 active 前必须走 Spec 流程
3. **Spec 产出自动同步到 ldvh-base/**：AI 在 Spec 确认后自动按映射规则回写

---

## 9. 风险与注意事项

1. **Plan/Spec 仅 SOLO 模式可用**：Chat 模式和 Builder 模式下无法使用，需在 Rules 中明确说明
2. **Spec 模板格式不可控**：Trae 内置的 Spec 模板格式可能随版本变化，LDVH 不应过度依赖其具体格式
3. **避免过度流程化**：不是所有任务都需要 Plan 或 Spec，分级使用是关键
4. **事实源一致性**：如果 Spec 产出和 ldvh-base/ 同时存在相同信息，需明确哪个是权威事实源（建议以 ldvh-base/ 为准）
5. **上下文窗口压力**：Plan/Spec 模式会消耗额外上下文，长任务需注意上下文压缩
