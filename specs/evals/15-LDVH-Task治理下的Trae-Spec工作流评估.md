# LDVH Task 治理下的 Trae Spec 工作流评估

> 创建日期：2026-06-05
> 定位：评估 LDVH 如何在 Task 治理下吸收 Trae Spec 工作流，形成从需求记录、Spec 生成、事实源吸收、序列执行到独立审计的闭环
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/07-工作模型基础规范.md`、`specs/08-工作流程基础规范.md`、`specs/20-工作模型集合索引.md`、`specs/24-Intent-意图.md`、`specs/27-Task-任务.md`
> 相关评估：`specs/evals/25-LDVH全盘确认与核心吸收建议.md`、`specs/refs/trae/06-Spec与Plan工作流.md`
> 调研边界：评估文档，不直接构成强制规则；稳定规则需进入正式 specs、Rules、Skill 或 ADR 后生效

---

## 1. 本文解决的问题

旧的 20 号评估文档将重点放在“让 LDVH Intent / Task 具备 Trae Spec 级规范化能力”上，倾向于通过字段增强、Skill 封装和双向桥接，让 LDVH 自身复制一部分 Spec 能力。

当前判断需要调整：LDVH 不应优先复制 Trae Spec，而应把 Trae Spec 作为 LDVH Plan 阶段的原生规划承载层，并在 Task 治理下吸收其产物。

本文重新评估以下问题：

1. 需求沟通完成后，Task 是否应先于 Spec 被记录；
2. Trae Spec 生成后，如何被 LDVH 吸收到事实源；
3. Spec 完成是否等于立即执行；
4. 执行阶段如何按 Spec 序列行动和检查；
5. 执行完成后如何由主控调用独立子 Agent 审计；
6. 该工作流应沉淀为哪些 Skill、Rules 或正式规范。

---

## 2. 核心结论

新的主线应是：

```text
需求沟通 → Task 记录 → Trae Spec → Spec 吸收 → 等待执行 → 序列执行 → 独立审计 → Record / Learn
```

其核心判断是：

1. **Task 是治理锚点**：需求沟通完成后应先创建或更新 Task，避免 Spec 文档成为无主规划产物。
2. **Trae Spec 是规划产物**：`spec.md`、`tasks.md`、`checklist.md` 承担复杂任务的结构化规划，但不直接替代 LDVH Task、Intent、ADR 或 Change。
3. **Spec 需要被吸收后才成为执行依据**：主控应调用专门 Skill 读取 Spec 三件套，并将目标、执行序列、验收映射、验证策略、风险点吸收到 LDVH 事实源或受控执行上下文。
4. **Spec 确认不等于执行授权**：Spec 完成后 Task 可以保持待执行状态，直到用户或主控明确进入执行。
5. **执行应按序列进行**：执行阶段应读取已吸收的步骤序列，逐步行动、逐项检查、收集 evidence，而不是重新自由规划。
6. **审计应由独立子 Agent 完成**：执行者完成后，主控应切换 Task 到 verifying，并调用独立子 Agent 审计 acceptance、checklist、diff、验证命令和 evidence。
7. **Record / Learn 才是闭环出口**：审计通过后再进入 Change 记录、Task 关闭、Pitfall / Memo / ADR / Rule 改进。

---

## 3. 与旧思路的差异

| 维度 | 旧 20 号文档思路 | 新判断 |
|---|---|---|
| 核心目标 | 让 LDVH Intent / Task 具备 Spec 级能力 | 让 Trae Spec 在 Task 治理下成为 Plan 阶段承载层 |
| 实现方向 | 增强 Intent 字段、增强 Task 字段、创建 ldvh-spec Skill | 保持最小事实内核，新增 Spec 吸收和序列执行流程 |
| 对 Trae Spec 的态度 | 与 LDVH 事实源双向桥接，部分复制能力 | 使用 Trae 原生 Spec，LDVH 负责治理和吸收 |
| 对 Task 的定位 | Task 承接 tasks.md，acceptance 承接 checklist.md | Task 是治理锚点，Spec 文档是规划产物，吸收后才成为执行依据 |
| 对字段扩展的态度 | 倾向新增 why / impact / dependencies 等字段 | 短期避免字段膨胀，优先通过 Skill 和现有字段 Dogfood |
| 对执行的态度 | 规划确认后可进入执行 | Spec 确认不等于执行授权，执行是独立阶段 |
| 对审计的态度 | AI 检查验收项 | 主控调用独立子 Agent 审计 |

新判断并不否定旧文档中“LDVH 与 Trae Spec 是互补关系”的结论，但修正了实现优先级：**不要先复制 Spec 能力，应先利用 Trae 原生 Spec，再用 LDVH 吸收、治理和审计。**

---

## 4. 推荐工作流

### 4.1 Intake：需求沟通与 Task 记录

当用户需求已经沟通清楚，主控应先判断是否需要创建 Intent + Task 或仅 Task。

```text
用户需求沟通完成
  ↓
ldvh-intake
  ↓
创建或更新 Task
  ↓
Task.status = planned
```

Task 至少承载：

1. 用户目标；
2. 关键范围和约束；
3. 初始 acceptance；
4. 是否需要 Trae Spec；
5. 后续 Spec 文档路径或吸收结果。

Task 的 acceptance 在 Intake 阶段不必展开为最终细粒度清单，但必须有足够明确的关闭边界。

### 4.2 Spec：主控触发 Trae Spec

对于复杂系统任务、跨模块改造、大规模重构、长期维护任务或高质量交付任务，主控应触发 Trae Spec。

```text
Task 已记录
  ↓
主控触发 Trae Spec
  ↓
生成 .trae/specs/<任务名称>/
  - spec.md
  - tasks.md
  - checklist.md
  ↓
用户确认 Spec
```

这里的确认语义应定义为：

```text
Spec 文档可作为规划产物被 LDVH 吸收。
```

而不是：

```text
立即执行全部任务。
```

### 4.3 Ingest：吸收 Spec 到事实源

Spec 完成后，主控应调用专门 Skill，例如：

```text
ldvh-spec-ingest
```

该 Skill 的职责不是简单复制 Markdown，而是完成结构化吸收：

1. 读取 `spec.md`，提取目标、范围、变更点、影响范围；
2. 读取 `tasks.md`，提取有序执行步骤、依赖关系和可能的子任务候选；
3. 读取 `checklist.md`，提取验收项并映射到 Task acceptance；
4. 识别风险、Human Gate、ADR / Memo / Pitfall 候选；
5. 补充 Task 的 description、acceptance、verification 或 closure_evidence 模板；
6. 记录 Spec 文档路径；
7. 给出是否建议创建子 Task 的判断。

短期应优先使用现有 Task 字段承载吸收结果，避免立即扩展 Contract。若字段不足，可先写入 `description`、`verification` 或 `closure_evidence` 的块标量中，并在 Dogfood 后再评估是否新增字段。

### 4.4 Ready：Spec 完成但不立即执行

Spec 吸收完成后，Task 可以保持 `planned`，但语义上已经进入：

```text
ready for execution
```

此阶段表达：

1. 需求已记录；
2. Spec 已生成；
3. Spec 已吸收；
4. 执行序列和验收映射已准备；
5. 尚未获得执行授权或尚未进入执行窗口。

短期不建议为了这个语义立刻修改 Task 状态机。可以先通过 Task 内容、Change 记录或 Skill 输出表达 `spec ingested / ready for execution`。若后续多次 Dogfood 证明必要，再评估新增 `specifying`、`spec_ready` 等状态。

### 4.5 Execute：按序列行动和检查

执行阶段不应重新自由规划，而应读取已吸收的执行序列。

理想流程：

```text
Task.status = executing
  ↓
读取 Task 与 Spec 吸收结果
  ↓
找到下一个未完成步骤
  ↓
执行该步骤
  ↓
运行对应验证
  ↓
收集 evidence
  ↓
更新 checklist / acceptance 映射
  ↓
进入下一步骤
```

可以建设专门 Skill：

```text
ldvh-execute-sequence
```

职责包括：

1. 按顺序执行步骤；
2. 每一步检查前置条件；
3. 每一步记录产出和验证方式；
4. 遇到 scope drift、规范冲突、高风险操作或验收不明确时暂停；
5. 发现超出当前任务范围的问题时分流为子 Task、Memo、Pitfall 或 ADR 候选；
6. 全部步骤完成后将 Task 交给主控进入 verifying。

### 4.6 Verify：主控调用独立子 Agent 审计

执行者不应自行完成最终审计。执行完成后主控应：

```text
Task.status = verifying
  ↓
调用独立子 Agent
  ↓
审计 acceptance / checklist / diff / evidence / verification
  ↓
返回通过或不通过结论
```

审计 Agent 应只读检查，不应直接修改事实源。审计输入应包括：

1. Task YAML；
2. 关联 Intent，如有；
3. Spec 文档路径；
4. Spec 吸收结果；
5. git diff；
6. 验证命令输出；
7. closure_evidence 草案；
8. acceptance 与 checklist 映射。

审计输出应包括：

1. 是否通过；
2. 未满足的 acceptance；
3. 未完成的 checklist；
4. 未运行或失败的验证命令；
5. evidence 缺口；
6. scope drift；
7. 建议修复项。

审计不通过时，回到 executing 或创建分流任务。审计通过后，进入 Record。

### 4.7 Record / Learn：关闭和沉淀

审计通过后，主控进入 Record：

1. 勾选 Task acceptance；
2. 填写 closure_evidence；
3. 记录 Change；
4. 将 Task 推进到 review_needed 或 closed；
5. 必要时沉淀 Pitfall、Memo、ADR 或 Rule 改进。

Learn 阶段关注：

1. 执行序列是否可复用；
2. Spec 吸收是否有误差；
3. 审计 Agent 是否发现高频缺口；
4. 是否需要调整 Skill、Rules、Tools 或正式规范。

---

## 5. 对事实模型的建议

### 5.1 短期不新增 Plan / Spec 事实模型

不建议立即新增 `Plan`、`Spec`、`Checklist` 或 `Artifact` 事实模型。

原因：

1. Trae 已有 `.trae/specs/` 和 `.trae/documents/` 作为规划产物目录；
2. LDVH 当前应坚持最小事实内核优先；
3. Task / Intent / ADR / Change 已能覆盖治理主线；
4. 过早对象化会增加 Contract、Validator、Rules、Skill 和状态机维护成本；
5. 当前更需要 Dogfood Spec 吸收和序列执行，而不是扩张对象集合。

### 5.2 Task 仍是执行治理中心

Task 应负责回答：

1. 当前要做什么；
2. 为什么可以做；
3. 验收标准是什么；
4. 是否已经规划；
5. 是否已经获得执行授权；
6. 执行结果如何验证；
7. 关闭证据在哪里。

Spec 文档可以提供详细结构，但 Task 仍是关闭和审计的主入口。

### 5.3 子 Task 应按治理需要创建

`tasks.md` 中的每个条目不应自动成为 LDVH 子 Task。

只有满足以下条件时，才建议创建子 Task：

1. 需要独立状态机；
2. 需要跨会话追踪；
3. 有独立验收；
4. 涉及不同执行窗口或不同执行者；
5. 超出当前 Task 的单次执行序列；
6. 需要单独 Change 或独立关闭证据。

普通步骤应留在执行序列中。

---

## 6. 任务粒度与结果物稳定性

Task 粒度是该工作流能否长期可用的关键。若每个执行动作都创建 Task，LDVH 会出现流程爆炸和事实源噪音；若 Task 过粗，又会导致结果物不稳定、测试目标不固定、审计无法判断完成。

因此应建立三层颗粒度：

```text
治理对象：Task
执行对象：Step / Sequence
测试对象：Output Contract / Artifact Matrix
```

核心原则是：**Task 控制治理粒度，Sequence 控制执行粒度，Output Contract 控制测试粒度。**

### 6.1 Task 是治理交付单元

Task 不应等同于每一个执行动作。Task 应定义为具有独立验收标准、可审计结果物和可关闭证据的最小治理交付单元。

只有满足以下条件之一时，才应创建 Task：

1. 需要跨会话追踪；
2. 有独立验收标准；
3. 有明确可审计结果物；
4. 需要独立关闭和 closure_evidence；
5. 失败后需要独立恢复或分流；
6. 会产生 Change、ADR、Pitfall 或 Memo；
7. 需要不同执行窗口、不同执行者或独立审计。

读取文件、搜索代码、总结上下文、运行一次命令、修复当前 Task 内的局部小问题，默认都不应创建 Task，而应作为当前 Task 的 Step。

### 6.2 Sequence 是执行颗粒度

Task 内部允许包含较细的执行序列。Trae Spec 的 `tasks.md` 或 Spec Ingest 生成的执行序列，应主要承载 Step，而不是自动生成 LDVH 子 Task。

例如一个 Task 可以是：

```text
重写 Trae Spec 对接评估文档
```

其执行序列可以是：

```text
1. 读取旧 20 号文档
2. 提炼旧观点
3. 根据当前讨论生成新判断
4. 写入新评估文档
5. 删除旧文档
6. 检查文件列表和 git status
```

这些 Step 不应自动成为 `ldvh-base/tasks/` 下的新 Task。只有 Step 满足升级条件时，才创建子 Task。

### 6.3 Step 升级与降级规则

Step 升级为 Task 的条件：

1. 需要跨会话继续处理；
2. 需要独立验收和关闭；
3. 阻塞当前 Task，但可被单独解决；
4. 范围明显超出当前 Task；
5. 涉及新的长期决策或治理边界；
6. 需要另一个 Agent、人或时间窗口处理；
7. 失败后不能简单回滚或重试；
8. 产物独立到可以被单独测试。

候选 Task 降级为 Step 的条件：

1. 只能在当前 Task 中被理解；
2. 没有独立验收；
3. 没有独立结果物；
4. 不需要跨会话追踪；
5. 完成后只服务当前 Task；
6. 失败后可以立即在当前上下文内修复。

这组规则用于防止子任务蔓延，同时避免真正需要治理的问题被埋在执行步骤中。

### 6.4 Output Contract 固定测试对象

结果物稳定性不应通过增加 Task 数量解决，而应通过 Output Contract 解决。每个可执行 Task 在进入执行前，应明确本 Task 完成后必须产生或保持什么结果。

Output Contract 可先作为 Task `acceptance`、`verification` 或 Spec Ingest 输出的一部分，不必立即新增字段。

建议结构：

```text
Output Contract:
- Primary artifact: <主要结果物路径或对象>
- Required changes: <必须发生的变化>
- Forbidden changes: <不应发生的变化>
- Verification: <验证方式>
- Evidence: <关闭时要引用的证据>
```

示例：

```text
Output Contract:
- Primary artifact: specs/evals/15-LDVH-Task治理下的Trae-Spec工作流评估.md
- Required changes:
  - 新文档存在
  - 旧 20 号文档不存在
  - 新文档包含 Task 记录、Spec 吸收、等待执行、序列执行、独立审计、Record / Learn
- Forbidden changes:
  - 不修改正式 specs
  - 不修改 Task Contract
- Verification:
  - ls specs/evals
  - git status --short
- Evidence:
  - 新文档路径
  - 删除旧文档的 git diff
```

审计和测试应优先检查 Output Contract，而不是要求每个执行步骤都是 Task。

### 6.5 Artifact Matrix 支撑审计

对于复杂 Task，可以由 Spec Ingest 或执行计划生成轻量 Artifact Matrix：

```text
| artifact | expected state | verification |
|---|---|---|
| specs/evals/15-...md | exists | ls specs/evals |
| specs/evals/20-...md | absent | ls specs/evals |
| specs/27-Task-任务.md | unchanged | git diff -- specs/27-Task-任务.md |
```

独立审计 Agent 不需要复盘每个执行细节，而应检查：

1. Task acceptance 是否满足；
2. Output Contract 是否满足；
3. Artifact Matrix 是否满足；
4. verification 是否执行；
5. git diff 是否越界；
6. closure_evidence 是否充分。

### 6.6 流程等级

为避免所有任务都走重流程，应按复杂度启用不同等级：

| 等级 | 适用场景 | 机制 |
|---|---|---|
| Level 0 即时动作 | 读取、搜索、解释、运行简单命令 | 不建 Task，不建 Spec，不独立审计 |
| Level 1 轻量交付 | 单文件文档修改、小修复、明确的小交付 | Task 可选，不走 Spec，使用 acceptance + verification |
| Level 2 标准 Task | 多步骤、有明确结果物、需要跨会话或审计 | 创建 Task，使用 Plan 或 execution sequence，必要时独立审计 |
| Level 3 Spec Task | 复杂系统任务、跨模块改造、规范/状态机/Skill/Tools 改造、高风险变更 | Task → Trae Spec → Spec Ingest → Ready → Execute Sequence → 独立审计 → Record |

该分级保证：简单动作不会被治理流程拖慢，复杂任务也不会缺少固定结果物和审计边界。

### 6.7 对 Spec Ingest 的影响

Spec Ingest 不应把 `tasks.md` 每一项都映射为 LDVH Task，而应先分类：

| Spec 条目类型 | 吸收结果 |
|---|---|
| 有独立结果物、独立验收、可跨会话 | LDVH 子 Task |
| 当前 Task 内的执行动作 | execution_sequence Step |
| 只用于判断完成与否 | checklist / acceptance 映射 |
| 超范围但有价值 | follow-up Task 候选 |
| 背景说明或经验 | description / Memo / Pitfall 候选 |

这意味着 Ingest Skill 的核心能力不是搬运 Markdown，而是分流和稳定结果物。

---

## 7. 建议建设的 Skill

### 7.1 ldvh-spec-ingest

定位：承接 Trae Spec 完成后的吸收阶段。

触发条件：

1. Task 已创建；
2. `.trae/specs/<任务名称>/` 已存在；
3. 用户或主控要求将 Spec 纳入 LDVH；
4. AI 判断当前 Task 执行前必须吸收 Spec。

核心流程：

```text
读取 Task
读取 spec.md / tasks.md / checklist.md
建立 Task 与 Spec 的关联
提取目标、步骤、验收、验证、风险
映射到 Task acceptance / verification
识别子 Task / ADR / Memo / Pitfall 候选
Human Gate 确认
回写事实源
运行 Fact Validator
```

输出：

1. Spec 摘要；
2. 执行序列；
3. acceptance 映射；
4. verification 策略；
5. 风险与 Gate；
6. 子 Task / ADR / Memo / Pitfall 建议；
7. 待执行入口。

### 7.2 ldvh-execute-sequence

定位：承接 Execute 阶段，按已吸收的 Spec 序列执行。

触发条件：

1. Task 已有 Spec 吸收结果；
2. 用户或主控授权执行；
3. Task 准备从 planned 进入 executing。

核心流程：

```text
读取 Task 和 Spec 吸收结果
确认 Task 状态可执行
状态流转到 executing
按序列执行步骤
逐项验证和收集 evidence
遇到 Gate 或分流点暂停
全部完成后转 verifying
```

### 7.3 ldvh-close 增强

`ldvh-close` 应增强对 Spec 关联任务的关闭检查：

1. 检查 Spec 文档是否存在；
2. 检查 Spec 是否已被吸收；
3. 检查 checklist 与 Task acceptance 是否一致或有解释；
4. 检查独立子 Agent 审计结果；
5. 检查 closure_evidence 是否引用 Spec、验证命令和关键变更；
6. 审计不通过不得关闭。

---

## 8. 建议进入正式规范或规则的内容

以下内容适合后续进入正式 specs、Rules 或 Skill 文档。

### 8.1 规则候选

```text
复杂 Task 在执行前应优先进入 Trae Spec；Spec 完成后必须经 LDVH Skill 吸收，未经吸收不得作为执行依据。
```

```text
Spec 确认不等于执行授权；Task 必须在独立执行授权或主控决策后才能从 planned 进入 executing。
```

```text
关联 Trae Spec 的 Task 关闭前，必须检查 Spec checklist、Task acceptance、验证命令、closure_evidence 和独立审计结果。
```

### 8.2 Skill 候选

1. `ldvh-spec-ingest`：吸收 Trae Spec 到 LDVH 事实源；
2. `ldvh-execute-sequence`：按已吸收序列执行；
3. `ldvh-close` 增强：审计 Spec 关联任务。

### 8.3 ADR 候选

如果后续要修改 Task 状态机、Task Contract 或新增事实模型，应先创建 ADR。

候选 ADR 主题：

```text
LDVH 是否引入 spec_ready 状态或 Spec artifact 字段
```

```text
Trae Spec 文档在 LDVH 中的事实源地位
```

```text
是否将 Checklist / Artifact 对象化
```

---

## 9. 风险与约束

| 风险 | 说明 | 缓解 |
|---|---|---|
| Spec 与 Task 形成双事实源 | checklist 与 acceptance 各自变化，关闭依据不清 | 明确 Task 是治理事实源，Spec 是规划产物，关闭以 Task acceptance 和审计结果为准 |
| Spec 确认后误触发执行 | Trae 原生流程可能把确认与执行绑定 | 在 LDVH 中定义“Spec 确认只表示可吸收，不等于执行授权” |
| 过早扩展 Task Contract | 为承载 Spec 结果新增过多字段 | 先用现有字段和 Skill 输出 Dogfood，再决定是否改 Contract |
| 子 Task 膨胀 | tasks.md 每项都变成 LDVH Task | 只有独立状态、独立验收、跨会话追踪时才创建子 Task |
| 审计流于形式 | 执行者自己判断完成 | 主控必须调用独立子 Agent，只读审计后再关闭 |
| Spec 吸收失真 | Markdown 内容被错误映射到 Task | Ingest Skill 输出映射摘要，并经 Human Gate 确认 |
| 执行序列过度僵化 | 实际执行中发现更优路径或阻塞 | 遇到偏离时暂停，更新 Spec 吸收结果或分流处理 |

---

## 10. 最小 Dogfood 路径

建议下一步不要先大规模修改事实模型，而是用一个真实任务验证：

```text
建设 ldvh-spec-ingest Skill，使 LDVH 能吸收 Trae Spec 三件套
```

Dogfood 流程：

```text
创建 Task
触发 Trae Spec
确认 Spec
调用临时吸收流程
按吸收序列执行一个小范围改动
调用独立子 Agent 审计
记录 Change
沉淀 Pitfall / Memo / Rule 候选
```

Dogfood 后再决定：

1. 是否新增 `ldvh-spec-ingest` 正式 Skill；
2. 是否新增 `ldvh-execute-sequence` Skill；
3. 是否修改 Task Contract；
4. 是否引入 `spec_ready` 状态；
5. 是否需要 ADR。

---

## 11. 结论

LDVH 与 Trae Spec 的最佳结合方式不是让 LDVH 复制 Spec，也不是让 Spec 替代 LDVH Task，而是形成：

```text
Task governance over Trae Spec execution
```

也就是：

```text
Task 先记录需求和治理边界
Trae Spec 负责复杂任务的结构化规划
Spec Ingest 负责将规划吸收到事实源
Execute Sequence 负责按序列执行和检查
独立子 Agent 负责 Verify
Record / Learn 负责关闭和沉淀
```

这一工作流保留了 Trae Spec 的原生产品能力，也保留了 LDVH 的事实源、状态机、Human Gate、Evidence、Change 和审计优势。

后续正式化时，应优先沉淀三条规则：

1. **Spec 确认不等于执行授权**；
2. **Spec 必须经 LDVH Skill 吸收后才能作为执行依据**；
3. **关联 Spec 的 Task 完成后必须由主控调用独立子 Agent 审计，审计通过后才能关闭。**
