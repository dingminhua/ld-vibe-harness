---
title: LDVH 常用行为清单——五类事实对象生命周期流程
status: active
report_kind: internal_audit
research_intent: LDVH 项目缺乏系统化的常用行为清单，AI 执行者每次从零探索操作模式，效率低且容易遗漏步骤。本 Study 旨在系统化提炼五类事实对象的完整生命周期常用行为清单，使 AI 执行者不再重复探索，减少步骤遗漏和摩擦重复。
research_question: LDVH 五类事实对象（Spark, WorkCase, ADR, Pitfall, Study）各自的完整生命周期是怎样的？在创建、更新、状态转换、终态处置四个环节中，每个环节需要执行哪些 Helper CLI 操作？各类型之间如何在生命周期中交互流转？
abstract: 本 Study 基于 LDVH 规范 20~24、行动模板 31/32/34 和 Helper CLI 实际 capabilities，系统化提炼了五类事实对象的完整生命周期常用行为清单。每类覆盖创建、更新、状态转换、终态处置四个环节，每个行为步骤标注对应的 Helper CLI 操作名和参数提示，包含跨类型交叉引用说明。
recommendation_summary: 建议 AI 执行者按本行为清单逐项执行 LDVH 受控操作，避免遗漏步骤。WorkCase 专属操作不可绕过，每次写入前必须重新观察 signature，写后必须精确回读。本清单应与具体规范（20~24）和行动模板（31/32/34）配合使用，后者是权威来源。
input_refs:
- kind: specification
  locator: specs/20-Spark-火花.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/21-WorkCase-工作项.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/22-ADR-决策.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/23-Pitfall-踩坑经验.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/24-Study-研究报告.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/31-事实对象判定与受控创建行动模板.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/32-事实对象生命周期变更与承接处置行动模板.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: specification
  locator: specs/34-WorkCase获批计划执行行动模板.md
  version: b1d1489d
  observed_at: '2026-08-18T08:30:00Z'
- kind: helper-call-results
  locator: ldvh capabilities
  observed_at: '2026-08-18T08:30:00Z'
change_log:
- summary: 受控创建 Study：LDVH 常用行为清单——五类事实对象生命周期流程。
  signature:
    product_name: Cindy
    model_name: gpt-5
  at: '2026-08-18T08:26:48.966320Z'
- summary: 受控更新 Study：按独立结果复核反馈修正——关键发现改为影响导向、建议具体到承接对象、input_refs version 改为实际 commit、后续分流补判断标准。
  signature:
    product_name: Cindy
    model_name: gpt-5
  at: '2026-08-18T08:40:08.319002Z'
- summary: 受控更新 Study：增加「完成后同事务更新item状态」行为清单条目，更新与并行Study关系（承接workcase-01M0B272H5EZAAR1E32X8KZ1JH改进4）。
  signature:
    product_name: Cindy
    model_name: glm-5.2
  at: '2026-08-18T08:40:09.319003Z'
object_uid: 01a013fa-f948-78e6-87f0-3b5b7daf758b
object_id: study-01M09ZNYA8F3K8FW1VBDYTYXCB
fact_type_key: study
created_at: '2026-08-18T08:26:48.966320Z'
updated_at: '2026-08-18T08:40:09.319003Z'
---

## 研究问题

**本项目为何需要这轮报告**：LDVH 项目经过多次迭代，已形成完整的规范体系与事实模型，但 AI 执行者每次实际操作仍需从零探索操作模式，缺少一份系统化的常用行为清单，导致步骤遗漏与摩擦重复。本轮内部审计的目标是为 AI 执行者提供一份可复用的操作参考，减少重复探索成本。

**本报告实际回答的问题**：LDVH 五类事实对象（Spark, WorkCase, ADR, Pitfall, Study）各自的完整生命周期是怎样的？在创建、更新、状态转换、终态处置四个环节中，每个环节需要执行哪些 Helper CLI 操作？各类型之间如何在生命周期中交互流转？

## 输入与边界

本报告基于以下输入：

| 输入 | 种类 | 用途与限制 |
|---|---|---|
| specs/20-Spark-火花.md | specification | 确认 Spark 的 intent/summary/evolution 审核、三状态闭集、related-to 关系 |
| specs/21-WorkCase-工作项.md | specification | 确认 WorkCase 状态机、phase 闭集、5 个专属操作、Gate 1/2 |
| specs/22-ADR-决策.md | specification | 确认 ADR active→retired 状态、五个专属字段不可实质改变 |
| specs/23-Pitfall-踩坑经验.md | specification | 确认 Pitfall draft→active→discarded 三态、WC 现场保留 |
| specs/24-Study-研究报告.md | specification | 确认 Study 五段 H2 正文结构、report_kind、input_refs 要求 |
| specs/31-事实对象判定与受控创建行动模板.md | specification | 确认所有类型受控创建的通用流程 |
| specs/32-事实对象生命周期变更与承接处置行动模板.md | specification | 确认生命周期变更分类（correction/update/lifecycle/multi-object） |
| specs/34-WorkCase获批计划执行行动模板.md | specification | 确认获批 WorkCase 的执行、检查点、结果复核组织 |
| ldvh capabilities 输出 | helper-call-results | 确认当前 26 个公开 Helper 操作清单 |

**观察时点**：全部规范以 commit `b1d1489d` 为基线读取；capabilities 于 2026-08-18T08:30:00Z 现场获取。

**边界**：本报告只分析 LDVH 规范已定义的生命周期行为，不涉及 Git 提交、环境接入、Web 交互等外围操作。行为清单是经验总结，不替代正式规范作为权威来源；未覆盖各类型完整 Schema 校验细则（统一登记 05.Att.01 承载）。

## 关键发现

### 发现一：五类事实对象共享统一生命周期框架但操作入口分化

五类事实对象共享 create/update/read 的通用骨架（05 规范），但 **WorkCase 是唯一拥有专属操作集合的类型**（update-workcase / close-workcase / begin-workcase-termination / complete-workcase-termination / correct-closed-workcase / recover-invalid-workcase），其余四类（Spark/ADR/Pitfall/Study）均走通用 `update-fact-object`。

**对后续项目工作的直接影响**：AI 执行者必须记住本操作路由差异，否则会在 WorkCase 上误用通用 `update-fact-object` 被机械拒绝。建议把该路由规则作为后续 WorkCase 的行为要点，并在新执行者上手时以本清单为参考入口。

### 发现二：状态闭集的共性与差异决定生命周期动作

| 类型 | 状态闭集 | 初态 | 终态 |
|---|---|---|---|
| Spark | open → implemented / discarded | open | implemented / discarded |
| WorkCase | open / blocked → closed | open + human_plan_confirming | closed（含 termination 时） |
| ADR | active → retired | active | retired |
| Pitfall | draft → active → discarded | draft | active / discarded |
| Study | active → retired | active | retired |

**对后续项目工作的直接影响**：Pitfall 是唯一以 draft 为初态的类型，且 draft 必须与 active 具有相同完整度；门槛最高的类型是 WorkCase（Gate 1/Gate 2 双重 Human 决定）。识别当前对象类型的初态与状态机，是选择正确生命周期动作的第一步。建议行为清单使用者先查状态闭集再决定动作。

### 发现三：写后精确回读是贯穿所有写入的不可省略步骤

每次受控创建或更新后，都必须以 `read-fact-objects` 公开精确回读当前对象，并检查 `check-fact-integrity`；创建/更新操作内部的 readback 不替代公开回读。`create-fact-object` 返回的 `result.actual_ref` 应原样作为下一次 `read-fact-objects` 的定位输入。

**对后续项目工作的直接影响**：这是 31/32 模板共同的强制步骤，遗漏会造成"未验证的成功声明"。建议把"写后精确回读"固化为每次受控写入的行为检查点（可由后续 Pitfall 沉淀为踩坑经验）。

### 发现四：三字段 signature 必须每次写入前重新观察

每次 `change_log` 写入和每次 Git 提交前，都必须重新取得并判断 product_name / model_name 两字段快照，不得复用先前动作的快照；不可观察项如实标为 null 并向 Human 披露。历史对象的旧签名形状（agent_runtime_name 等）只读兼容，不得改名归一。

**对后续项目工作的直接影响**：跨会话、跨 Agent 写入时若复用旧签名会造成署名污染。建议执行者在每次受控写入前单独观察当前环境署名，而非从历史对象复制。

### 发现五：WorkCase 的 item_event 路径不能代替完整 after 更新

`update-workcase` 的 `fact_object` 与 `item_event` 是严格 XOR 二选一。item_event（start/update-checkpoint/complete）只能在 `phase=executing` 用于单 item 状态推进；phase 转换、status 变化、结果形成、授权更新都必须用完整 fact_object 路径。

**对后续项目工作的直接影响**：在 executing 外的 phase 尝试 item_event 会被机械拒绝；phase 转换时若误用 item_event 会造成状态卡死。建议执行者区分两种路径的使用边界。

**行为清单新增条目（承接 spark-01M09PNH9CEAVBMQS4JXNC74W6 缺口一改进4）**：完成 item 实际工作后，必须同事务用 `item_event`（`start-work-item` / `complete-work-item` / `cancel-work-item`）或 `fact_object` 路径推进 item 状态，不得留下 `pending` item 与已执行工作并存。`complete-work-item` 在最后一项 terminal 时会同事务投影 `executing → controller_checking`，无需另发完整 after。该条目压缩"忘记更新 item 状态"的发生率，不替代机械保障——`pending_item_observation` 投影字段让该缺口可见但不阻断。

### 发现六：跨类型流转主要经由关系与处置字段

| 流转场景 | 源→目标 | 机制 |
|---|---|---|
| 研究启发决定 | Study informs → ADR/WorkCase | relation `informs` |
| 研究受议题驱动 | Study inspired-by → Spark | relation `inspired-by` |
| 执行中保存失败经验 | WorkCase contributed-to → Pitfall draft | relation `contributed-to`（仅 human_closure_confirming 外） |
| 新旧决定替代 | ADR → ADR | disposition_summary 说明，无关系边 |
| 新旧经验替代 | Pitfall → Pitfall | disposition_summary 说明，无关系边 |
| 未决事项保留 | 任意类型 → Spark | WorkCase 关闭时 spark_suggestions → 未来 Spark |

**对后续项目工作的直接影响**：关系并非跨类型流转的唯一载体；ADR/Pitfall 的"替代历史"通过 disposition_summary 表达而不建立关系边，这与 Spark/Study 的关系语义不同。执行者需按目标类型的来源规则选择承载方式。

## 建议

1. **将本行为清单作为 WorkCase 获批计划执行（34）的参考入口**：
   - 目标对象类型：WorkCase（新建或既有执行中）
   - 预期目标：执行者按五类行为清单组织 item 执行与检查点
   - 验收条件：WorkCase 的 item 执行不再因"从零探索操作模式"而遗漏步骤
   - 创建/更新判断：下一次创建分析类 WorkCase 时，在 scope 或 approach_summary 中引用本 Study 的 object_uid

2. **将"写后精确回读"固化为受控写入的强制检查点（Pitfall 候选）**：
   - 目标对象类型：Pitfall（新建 draft）
   - 预期目标：记录"未公开回读就把创建/更新响应写成成功"的失败机制与规避方法
   - 验收条件：失败症状、触发条件、根因、解决、规避、验证齐全且可迁移复用
   - 创建/更新判断：当再次观察到同类"未回读即声明成功"的失败时创建

3. **用 ADR 固定"WorkCase 专属操作不可绕过通用 update-fact-object"的决策**：
   - 目标对象类型：ADR（新建）
   - 预期目标：把 21 规范的专属操作路由固化为项目级遵循决定
   - 验收条件：decision/applicability/rationale/consequences 四要素完整，Human 已授权
   - 创建/更新判断：当项目出现多次误用 update-fact-object 于 WorkCase 的摩擦时创建

4. **本清单随规范更新而维护**：
   - 目标对象类型：Study（既有的本对象）
   - 预期目标：当 20~24 或 31/32/34 发生实质变化时同步修订本清单
   - 验收条件：新规范状态闭集或专属操作变化后，本清单相应章节同步更新
   - 创建/更新判断：检测到规范正文实质变化且本清单相关内容过时时更新

## 后续分流

1. **WorkCase 对接**：当后续创建需要执行获批计划的分析/编排类 WorkCase 时，把本 Study 的 object_uid（01a013fa-f948-78e6-87f0-3b5b7daf758b）作为行为清单引用来源；若执行者已熟悉五类生命周期，可不重复引用。判断标准：item 涉及五类事实对象任一类的生命周期操作时引用。

2. **Pitfall 沉淀**：当再次观察到"写后未公开回读即声明成功"或"在 WorkCase 上误用 update-fact-object"的失败时，创建 Pitfall 记录该机制；若此类失败已多轮未再出现，可暂不创建，由本清单推荐 2 的上限持续观测。

3. **Spark 建议展开**：本清单中"摩擦点"（如 intent 审核难、item_event 与 fact_object 路径混淆）若出现新的具体实例，可以新建 Spark 展开分析；若无新实例，保持本清单作为唯一承载即可。

4. **定时复核**：当 specs/20~24 或 specs/31/32/34 发生实质修订（commit 变化 + 状态闭集/专属操作变化）时，复核本清单并同步修订；若规范无实质变化，无需对象化，本清单继续有效。

5. **与并行 Study 的关系**：spark-01M09PNH9CEAVBMQS4JXNC74W6（WorkCase 执行阶段两个设计缺口）已由 workcase-01M0AVJD0XFK6APB33SMGQR6CZ 完成分析并关闭（closure_outcome=completed），其结论已由本清单吸收：item_event 闭集扩展（cancel-work-item + complete-work-item 同事务投影）已落实，阶段 Goal 行为约束（34 §5.2 升级为应尝试并记录缺口）已落实。
