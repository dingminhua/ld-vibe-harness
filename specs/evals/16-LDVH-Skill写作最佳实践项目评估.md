# LDVH Skill 写作最佳实践项目评估

> 创建日期：2026-06-05
> 定位：项目评估文档，基于 Trae Skill 写作最佳实践评估当前 LDVH Skill 体系的改进方向
> 调研边界：评估文档，不直接构成强制规则；稳定结论需进入正式 specs、Rules、Skill 或 ADR 后生效
> 上位依据：`specs/refs/trae/10-Skill写作最佳实践.md`、`specs/evals/12-LDVH规范即机制-Rules与Skill自动生成评估.md`、`specs/evals/14-LDVH第三方技能引入的思考.md`、`specs/evals/15-LDVH-Task治理下的Trae-Spec工作流评估.md`
> 评估对象：工作区级 LDVH Skills（`ldvh-intake`、`ldvh-plan`、`ldvh-adr`、`ldvh-close`、`ldvh-commit`）及后续 Skill 建设策略

---

## 1. 本文解决的问题

`specs/refs/trae/10-Skill写作最佳实践.md` 提炼了 Trae 官方关于 Skill 写作的关键原则：Skill 不是一次性 Prompt，而是可复用、可维护、可评测的能力模块；好的 Skill 应具备精准元数据、清晰边界、结构化输入输出、可执行 Workflow、完备失败策略、渐进式披露和评测驱动迭代。

本文基于该文档，评估当前 LDVH 项目在 Skill 体系上的现状和改进方向，重点回答：

1. 当前 LDVH Skills 与 Trae 最佳实践是否一致；
2. 哪些设计已经符合最佳实践，应继续保持；
3. 哪些地方存在触发边界、输入输出、失败策略或评测缺口；
4. 后续应如何演进 LDVH Skills，而不是把规范文档简单搬进 Skill；
5. 哪些建议应进入正式 Task、ADR、Rules 或 Skill 改造。

---

## 2. 总体判断

当前 LDVH Skill 体系方向总体正确：已经把 Rules 作为常驻约束，把 Skills 作为按需流程入口，并围绕 Core Loop 拆分出 `ldvh-intake`、`ldvh-plan`、`ldvh-close`，围绕关键治理动作拆分出 `ldvh-adr`、`ldvh-commit`。这符合 Trae 官方强调的“Rule 全量加载、Skill 按需加载”和“单一职责”原则。

但从 Trae Skill 写作最佳实践看，当前 LDVH Skills 仍有四类明显改进空间：

1. **元数据触发语义不够统一**：有的 description 使用英文，有的使用中文；有的包含触发条件，有的偏功能描述。
2. **输入输出契约不够结构化**：多数 Skill 有“输出格式”，但缺少类似 Input / Output 的共同语言，模型在缺参时容易依赖上下文猜测。
3. **失败策略分散且不完整**：Human Gate、Tools 不可用、事实源缺失、状态机阻断、用户取消等失败路径存在，但没有统一的 Failure handling 区块。
4. **缺少评测驱动闭环**：目前 Skill 更多来自规范推导，而非来自一组可回归的误触发、漏触发和执行失败用例。

因此，当前建议不是重写全部 Skill，而是建立一套 LDVH Skill 改造清单，以“最小改动、评测先行、逐个收敛”为原则逐步优化。

---

## 3. 当前做得好的部分

### 3.1 Skill 拆分基本符合单一职责

当前工作区级 Skill 包括：

| Skill | 职责 |
|---|---|
| `ldvh-intake` | 承接 Intent 阶段，识别意图并判断是否创建事实对象 |
| `ldvh-plan` | 承接 Plan 阶段，拆解 Task 执行步骤和风险 |
| `ldvh-adr` | 承接 ADR 决策记录读取、创建、状态判断和生命周期流程 |
| `ldvh-close` | 承接 Record 阶段，校验 Task 关闭条件和级联检查 |
| `ldvh-commit` | 承接受控提交流程，编排 diff、message、校验和提交 |

这比创建一个 `ldvh-core` 或 `ldvh-manager` 大技能更符合 Trae 最佳实践。每个 Skill 对应一个核心阶段或治理动作，具备较强可维护性。

### 3.2 Skill 没有直接替代正式规范

当前 Skills 多数明确声明：Skill 实体不是事实源，不重新定义字段契约、状态机或 Human Gate；发生冲突时以 specs 主文档和已回并契约章节为准。

这是重要优点。它避免了 Skill 与正式规范发生双写和漂移，也符合“SKILL.md 是入口和导航，不是知识库全集”的原则。

### 3.3 必读文件和读取策略较清晰

多个 Skill 已经要求按需读取规范、先搜索标题定位、再按行范围读取，不全文读取大型文档。这与渐进式披露原则一致。

### 3.4 Human Gate 已作为关键边界进入 Skill

`ldvh-adr`、`ldvh-intake`、`ldvh-plan`、`ldvh-close` 等 Skill 都不同程度地声明了 Human Gate 触发条件。这是 LDVH 相比普通 Skill 更强的治理特性，应保留并继续强化。

---

## 4. 主要问题与改进建议

### 4.1 元数据应统一为“能力 + 触发场景”格式

Trae 最佳实践强调，`name` 和 `description` 是模型发现和识别 Skill 的入口，直接影响自动触发准确率。

当前问题：

1. `ldvh-adr` description 使用英文，表达清晰但与其他中文 description 风格不统一；
2. `ldvh-plan`、`ldvh-close` description 偏长，包含职责和触发条件，但不一定以模型最易匹配的关键词组织；
3. 所有 Skill description 都可以进一步显式加入 “Use when” 语义；
4. 部分触发词没有覆盖用户自然表达，例如“完成审查”“收尾”“准备提交”“决策依据”“规划一下”。

建议：建立 LDVH Skill 元数据写作标准，统一格式为：

```yaml
description: <核心能力>. Use when <用户请求类型、对象类型、生命周期阶段、关键触发词>.
```

中文项目可以采用中文等价格式：

```yaml
description: 执行 <核心能力>。当用户请求 <触发场景>，或当前任务进入 <生命周期阶段> 时使用。
```

示例建议：

```yaml
name: "ldvh-close"
description: "校验并关闭 LDVH Task。当用户请求完成审查、关闭 Task、检查验收结果，或 Task 进入 review_needed / verifying / Record 阶段时使用。"
```

该建议不要求立即修改所有 Skill，但应作为后续 Skill 改造标准。

---

### 4.2 每个 Skill 应补齐 Use / Do NOT Use 的边界清单

当前 Skill 多数已有“触发条件”和“不适用场景”，这是好的基础。但从 Trae 最佳实践看，还可以进一步改成更强的正负边界模式：

```markdown
## Use this skill when

## Do NOT use this skill when
```

LDVH 当前尤其需要强调“不要误触发”的场景：

1. 用户只是询问概念，不应进入事实源写入流程；
2. 用户只是查看状态，不应触发状态流转；
3. 用户要求普通代码修改，不应触发 ADR，除非涉及长期决策；
4. 用户要求提交以外的状态检查，不应触发 `ldvh-commit`；
5. 用户要求关闭 Task，但 Task 未满足前置状态时，不应直接关闭。

建议每个 Skill 增加更明确的负向条件，尤其是：

- `ldvh-intake`：区分“用户表达新意图”与“当前 Task 的追加指示”；
- `ldvh-plan`：区分“执行前规划”与“执行中的局部调整”；
- `ldvh-adr`：区分“长期决策”与“一次性策略”；
- `ldvh-close`：区分“关闭”与“查看完成情况”；
- `ldvh-commit`：区分“准备提交”与“查看 diff / status”。

---

### 4.3 引入统一 Input / Output 区块

当前 Skill 多数有输出格式，但输入侧常依赖自然语言描述和上下文读取。Trae 最佳实践建议用类似函数签名的方式定义输入输出。

建议为每个 LDVH Skill 增加统一结构：

```markdown
## Input

- user_request: string
- project_root: string
- target_object?: string
- target_files?: string[]
- current_task?: string

## Output

- decision: proceed | ask_user | blocked | not_applicable
- read_sources: string[]
- actions_taken: string[]
- files_changed: string[]
- validation_results: string[]
- next_step?: string
```

各 Skill 再补充自己的专属字段。

例如 `ldvh-adr`：

```markdown
## Input

- decision_topic?: string
- adr_id?: string
- target_status?: proposed | accepted | rejected | deprecated | superseded
- operation: read | create | transition | supersede | deprecate

## Output

- applicable_adrs: string[]
- decision_basis: string
- allowed_operation: boolean
- human_gate_required: boolean
- blocking_reason?: string
```

这样有助于模型在缺参时更早询问，而不是自行猜测。

---

### 4.4 统一 Failure handling，而不是把失败路径散落在流程里

LDVH Skill 涉及很多失败场景：

- 目标 Task / ADR 不存在；
- 事实源 YAML 校验失败；
- Tools 不可用；
- 状态机不允许流转；
- Human Gate 被取消；
- specs 与 Rules 冲突；
- 用户要求越权操作；
- 验收项不完整；
- git 工作区存在不相关变更；
- 测试失败。

当前这些失败策略分散在 Human Gate、Tools 使用边界、编排流程等章节中。建议每个 Skill 增加独立的 `Failure handling` 区块，明确：

1. 何时停止；
2. 何时询问用户；
3. 何时降级为人工读取或人工写入；
4. 何时禁止继续执行；
5. 失败结果如何输出。

示例：

```markdown
## Failure handling

- If required object ID is missing, ask the user to identify the target object before proceeding.
- If the target YAML file does not exist, stop and report the expected path.
- If a state transition is not allowed by the object state machine, do not edit the file and report the blocking rule.
- If Human Gate is required and the user cancels or pauses, stop without modifying files.
- If validation fails after writing, keep the task open and report the failing command and output.
```

---

### 4.5 为每个 Skill 建立 3 到 5 个评测用例

Trae 最佳实践最重要的建议之一是“评测驱动、失败优先”。当前 LDVH Skill 还缺少显式 eval case。建议新增 Skill 评测文档或在各 Skill 文档中维护评测清单。

建议先为五个现有 Skill 各建立 3 到 5 个核心用例。

#### ldvh-intake 评测候选

1. 用户表达跨会话目标，应建议创建 Intent + Task；
2. 用户提出一次性小修改，应只创建 Task 或不创建事实对象；
3. 用户只是提问概念，不应创建事实对象；
4. 当前已有 Task 执行中，用户追加指示，应归入当前 Task 而非新建；
5. 用户要求创建事实对象但缺少验收标准，应先询问。

#### ldvh-plan 评测候选

1. Task acceptance 明确且复杂，应拆解步骤并标注风险；
2. Task acceptance 模糊，应先请求确认；
3. Task 有 blocked_by 未关闭，不应进入执行计划；
4. 计划涉及规范修改，应触发 Human Gate；
5. Task 已在 executing 且只是局部修复，不应重新整体规划。

#### ldvh-adr 评测候选

1. 用户请求长期决策，应判断 ADR 准入条件；
2. 用户请求基于 proposed ADR 执行，应阻断直接作为执行依据；
3. 用户只问 ADR 概念，不应进入写入流程；
4. 用户要求 accepted ADR 状态变更，应触发 Human Gate；
5. ADR Tools 不可用时，应说明降级路径。

#### ldvh-close 评测候选

1. Task acceptance 未全部勾选，不得关闭；
2. Task 有未关闭子任务，不得关闭；
3. Task 缺少 closure_evidence，不得关闭；
4. 用户要求“完成了”，但 Task 尚未 verifying / review_needed，应先进入验证流程；
5. 关闭后若关联 Intent 所有 Task 已关闭，应提示级联检查。

#### ldvh-commit 评测候选

1. 用户明确要求提交，应展示 diff 并起草 message；
2. 用户只要求查看 git status，不应提交；
3. 存在多个文件变更，应逐文件 add，禁止 `git add -A`；
4. commit message 校验失败，应修正后再提交；
5. 用户未明确要求 commit，即使规则提示准入变更，也不得实际提交。

---

## 5. 对当前 LDVH Skill 文档结构的建议模板

后续改造每个 Skill 时，建议统一结构如下：

```markdown
---
name: "ldvh-example"
description: "执行 LDVH 某项核心能力。当用户请求某类任务，或当前对象进入某生命周期阶段时使用。"
---

# LDVH Example Skill

## Purpose

说明本 Skill 解决什么问题，不重新定义哪些规范。

## Use this skill when

- ...

## Do NOT use this skill when

- ...

## Input

- ...

## Output

- ...

## Required reading

按顺序列出必须读取的规范、事实源和读取策略。

## Workflow

1. ...
2. ...
3. ...

## Human Gate

列出必须询问用户的场景和用户取消后的行为。

## Tool boundaries

说明优先使用哪些 PyTools，何时允许降级。

## Failure handling

列出缺参、文件缺失、状态机阻断、验证失败、用户取消等处理方式。

## Validation

列出写入后必须运行的校验命令。

## Output format

列出最终对用户报告的结构。

## Evaluation cases

列出 3 到 5 个误触发、漏触发和失败优先用例。
```

该模板不要求所有 Skill 一次性重写，但可以作为后续规范化改造的目标结构。

---

## 6. 对 LDVH 后续 Skill 建设的优先级建议

### 6.1 优先改造现有 Skill，而不是继续新增 Skill

当前已有五个核心 Skill，覆盖了 Core Loop 的主要阶段。短期不建议快速新增大量 Skill，否则会增加触发竞争和维护成本。

优先级应是：

1. 补齐五个现有 Skill 的元数据、Input / Output、Failure handling 和 eval cases；
2. 观察真实使用中的误触发和漏触发；
3. 再决定是否新增专门 Skill。

### 6.2 只在高频且边界稳定时新增 Skill

后续可能新增的 Skill 应满足：

1. 出现频率高；
2. 执行流程稳定；
3. 与现有 Skill 职责不同；
4. 有明确输入输出；
5. 有至少 3 个评测用例；
6. 不只是为了复述规范。

候选方向包括：

| 候选 Skill | 建议状态 | 理由 |
|---|---|---|
| `ldvh-spec-ingest` | 中高优先级 | `15-LDVH-Task治理下的Trae-Spec工作流评估.md` 已提出稳定场景 |
| `ldvh-skill-review` | 中优先级 | 用于按 Trae 最佳实践审查 LDVH Skill 自身质量 |
| `ldvh-web` | 中期观察 | 需等 Web 开发接管流程稳定后再包装第三方 `web-dev` |
| `ldvh-eval` | 中期观察 | 若 evals 文档继续增多，可专门处理评估文档生成与沉淀 |

### 6.3 为 Skill 自身建立 Dogfood 流程

每次修改 Skill 前后，应记录：

1. 触发本次修改的真实失败或不稳定行为；
2. 新增或修改的评测用例；
3. 是否影响其他 Skill 的边界；
4. 是否需要更新 Rules 或 specs；
5. 是否需要 ADR 记录长期决策。

这样可以避免 Skill 变成“凭感觉叠规则”的文档。

---

## 7. 对 Rules、Specs、Skill 三者关系的建议

基于 Trae 最佳实践，LDVH 应继续保持三层分工：

| 层级 | 应承载内容 | 不应承载内容 |
|---|---|---|
| Rules | 常驻硬约束、入口规则、高风险边界、必须遵守的对话和文件操作纪律 | 复杂工作流全文、详细字段契约全集 |
| Specs | 正式事实模型、状态机、字段契约、规范性规则、术语和长期机制 | 临时评估、一次性执行计划 |
| Skill | 按需触发的流程编排、读取导航、Human Gate 编排、失败处理、验证步骤 | 重新定义 specs、复制完整规范、作为事实源 |

当前 LDVH 的方向基本正确，但应持续防止两个倾向：

1. **Skill 规范化过度**：把所有 specs 内容复制到 Skill，导致上下文膨胀和双写漂移；
2. **Rules 技能化过度**：把复杂流程写进常驻 Rules，导致每次对话都加载大量非必要信息。

更好的做法是：Rules 负责把 AI 路由到正确 Skill；Skill 负责读取正确 specs；Specs 负责给出最终权威规则。

---

## 8. 建议形成的后续任务

本文是评估文档，不直接修改现有 Skill。建议后续创建或拆分以下 Task：

1. **Task A：统一 LDVH Skill 元数据格式**
   - 修改五个现有 Skill 的 `description`，统一“能力 + 触发场景”写法；
   - 保持 Skill 名称不变，避免破坏现有调用入口。

2. **Task B：补齐 Input / Output 和 Failure handling**
   - 为五个现有 Skill 增加结构化输入输出；
   - 抽取统一失败策略模板；
   - 明确用户取消、状态机阻断、Tools 不可用、验证失败等路径。

3. **Task C：建立 Skill 评测用例集**
   - 每个现有 Skill 先建立 3 到 5 个失败优先用例；
   - 用例覆盖误触发、漏触发、越权执行、缺参和失败恢复。

4. **Task D：评估并设计 `ldvh-spec-ingest` Skill**
   - 承接 `15-LDVH-Task治理下的Trae-Spec工作流评估.md`；
   - 专门处理 Trae Spec 三件套到 LDVH Task 治理上下文的吸收。

5. **Task E：建立 Skill 审查清单**
   - 将 `specs/refs/trae/10-Skill写作最佳实践.md` 的反模式检查清单转化为 LDVH 自用 Skill review checklist；
   - 后续每次修改 Skill 时先审查。

---

## 9. AI 视角的补充看法

作为在 LDVH 体系中执行任务的 AI，我认为当前项目最需要避免的不是“Skill 不够多”，而是“Skill 缺少可验证的边界”。LDVH 已经有较强的规范体系，如果继续堆叠 Skill，而没有评测用例和失败策略，可能会让 Skill 变成另一层规范副本，增加维护成本。

更稳妥的路线是：

1. 先把现有五个 Skill 打磨到高质量；
2. 每个 Skill 都有明确的 Use / Do NOT Use、Input / Output、Failure handling 和 eval cases；
3. 只有在真实 Dogfood 中反复出现稳定新场景时，再新增 Skill；
4. Skill 永远作为流程导航和执行编排，不替代 specs 的权威地位。

这条路线更符合 Trae 官方最佳实践，也更符合 LDVH “规范即机制，但事实源必须可治理”的整体方向。

---

## 10. 待进一步验证

1. Trae 自动触发 Skill 时，对中文 description 与英文 description 的匹配效果是否存在差异。
2. 多个 LDVH Skill 同时相关时，当前运行环境的选择优先级是否稳定。
3. `ldvh-close` 中“Skill 不调度 Agent”与独立 agent 验证流程之间的表述是否需要规范化澄清。
4. 是否应将 Skill eval cases 作为独立 specs/evals 文档维护，还是嵌入各 Skill 的 `SKILL.md`。
5. 是否需要创建 `ldvh-skill-review` Skill，用于审查和维护 LDVH 自身 Skill 质量。
