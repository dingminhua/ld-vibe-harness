# V4 WorkCase 设计独立审计报告

**审计者：** glm-5.2（智谱AI）
**审计日期：** 2026-07-14
**审计范围：** V4 WorkCase 类型定义（specs/21）、统一字段登记（05.Att.01）、事实模型基础规范（05）、行动模板基础规范（06）、00 理念与构成、V3 对照资料、相关 Code 与 tests

---

## 1. 总结结论：**有条件通过**

**最高严重度：P2**

V4 WorkCase 设计在大多数关键维度上优于 V3——对象粒度稳定、status/phase 正交清晰、双 Human Gate 版本绑定机制完善、阶段性工作项与内部步骤的边界明确、中断恢复骨架完整、字段治理严格。但审计发现 3 个 P2 问题，集中在**两个具体场景**下设计存在缺口：

1. **Human 退回后 plan_version 递增的级联失效规则有歧义**（P2-1）：spec 要求"递增 plan_version，移除旧 creation_reviews、execution_approval…"，但 Human 在 `human_closure_confirming` 退回后可能只要求修改结果而非计划，此时 spec 的级联规则过于激进，会不必要地清除还在 worktree 中的工作项结果。
2. **`waiting_on` 字段在 `human_closure_confirming` 阶段的可选性不明确**（P2-2）：spec 对 `human_closure_confirming` 的 `waiting_on` 条件没有明确说明，导致 Human Gate 等待状态无法被可靠恢复。
3. **Code 对 `creation_reviews` 的阻断检查覆盖不完整**（P2-3）：validation.py 只检查 `creation_reviews` 中无 `changes_required`/`blocked`，但未检查 `pass_with_followups` 中的 followups 是否已被 controller_resolution 覆盖。

---

## 2. 00 与 V1–V8 覆盖矩阵

| 价值标准 | 覆盖情况 | 证据 |
|---|---|---|
| **V1 快速定位** | ✅ 覆盖 | F1 责任卡固定投影 open/blocked WorkCase；F2 支持类型、状态、精确引用、关系、locator、字段文本过滤 |
| **V2 充分理解** | ✅ 覆盖 | goal/scope/success_criteria + work_items 阶段目标 + summary/resume_from/waiting_on 恢复快照组成完整上下文 |
| **V3 边界识别** | ✅ 覆盖 | 明确区分 WorkCase 责任阶段、独立审核、两种 Human Gate 的不同作用；Stop Conditions 第 7 条阻止内部步骤混入 work items |
| **V4 稳定推进** | ✅ 覆盖 | 7 阶段闭集 + 完整转换边 + plan/result 版本绑定 + 工作项状态条件，链路闭合 |
| **V5 据实判断** | ✅ 覆盖 | 审核必须绑定具体版本；controller_resolution 逐项处理 feedback；evidence_refs 定位依据；Code 不解释自然语言 |
| **V6 工作接续** | ✅ 覆盖 | 顶层 resume_from + 工作项级 resume_from 双层恢复点；非终态阶段必填 resume_from；F1 恢复基线 |
| **V7 清晰沟通** | ✅ 覆盖 | 两次 Human Gate 的交还范围明确（plan/approval 版本、execution_approval、closure_approval） |
| **V8 持续积累** | ⚠️ 部分覆盖 | WorkCase 本身不积累经验（经验进 Pitfall）；阶段转换和审核结果保留在对象中可回读，但跨 WorkCase 的模式识别尚未对象化 |

**说明：** 未覆盖的部分属于 V8 的长期积累维度，由 Pitfall 和 Study 类型承担，不属于 WorkCase 的设计责任范围。

---

## 3. 当前需求、V3 意图与 V4 设计的三向映射

| Human 需求 | V3 实现 | V4 当前设计 | 审计判断 |
|---|---|---|---|
| 长时工作责任可恢复 | 7 状态混合 + orchestration 容器 | status/phase 正交 + 阶段性 work_items + 双层恢复快照 | ✅ V4 更清晰，V3 的 orchestration 过重 |
| 阶段性工作项有独立结果 | execution_items 含 role/mode/input_refs 等运行脚手架 | work_items 精简为 item_id/goal/expected_result/status/approach_summary/result_summary | ✅ V4 移除运行脚手架，保留阶段目标 |
| 创建前独立审核 | orchestration.plan_review (含 review_items/controller_resolution/human_confirmation) | creation_reviews (workcase-review 结构，含 reviewer/feedback/controller_resolution) | ✅ V4 更结构化，要求联合覆盖 |
| 第一次 Human Gate | human_confirmation 占位 | execution_approval 绑定 plan_version，Human 批准后才出现 | ✅ V4 版本绑定更严格 |
| 主控自检 | controller_self_check 占位 | controller_check_summary 必填 + 退回 executing 路径 | ✅ V4 更明确 |
| 结果独立审核 | result_review 含 review_items 和 controller_resolution | result_reviews (workcase-review 结构，绑定 result_version) | ✅ V4 版本绑定更严格 |
| 第二次 Human Gate | human_closure_confirmation 占位 | closure_approval 绑定 result_version，与 closed 同一受控变更 | ✅ V4 更严格 |
| 关闭结果分类 | closure_outcome 字符串 | 五种 closure_outcome 互斥条件 + routed-to 关系 | ✅ V4 语义更精确 |
| 中断恢复 | 无专门机制 | 顶层 resume_from + 工作项 resume_from 双层 + F1 恢复基线 | ✅ V4 新增 |
| 阻塞管理 | blocking_reason 字符串 | blocking_summary 必填含解除条件；WorkCase blocked 与 item blocked 分离 | ✅ V4 更精确 |
| 后续分流 | followup_refs 列表 | routed-to 关系 + disposition_summary 说明 | ✅ V4 用关系替代自由文本 |
| 对象内历史 | revision_history 列表 | 由 Git 承载，当前对象只保留当前版本 | ✅ V4 消除第二事实源 |
| 按类型拆分关系 | related_*/followup_refs 多个字段 | 统一 relations 数组 | ✅ V4 统一 |
| 执行角色 | role 字段（枚举 owner_model） | 不保留，由 WorkCase 外层行动模板和能力判断 | ✅ V4 避免角色脚手架固化 |
| 空占位字段 | 大量必填字段允许空字符串 | 条件字段省略，不使用 null/空字符串占位 | ✅ V4 更严格 |

---

## 4. 按 P0/P1/P2/P3 排序的问题清单

### P2-1 | Human 退回后 plan_version 递增的级联失效范围不明确

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §6，第 256 行 |
| **违反的上位要求** | 00 §7 验证要求：声明必须与实际范围一致；05 §9.2 更新规则：失败和部分结果应如实保留 |
| **具体失败场景** | WorkCase 处于 `human_closure_confirming`，Human 退回要求修改工作项结果（如 item-01 的 result_summary 被指出不完整）。当前 spec 要求"Human 退回时……递增 plan_version，按本节清除旧审核、批准与结果包"（§6 第 256 行）。但实际修改只影响结果包，不涉及计划。递增 plan_version 会清除全部 work_items 状态、creation_reviews 和 execution_approval，导致已正确完成的工作项被迫重新审核和批准，增加不必要的 Human Gate 往返 |
| **影响** | 只修改结果时，本应递增 result_version 并回到 controller_checking 或 independent_reviewing，但 spec 的级联失效规则未区分退回原因，可能迫使计划版本膨胀 |
| **最小修正建议** | 在 `human_closure_confirming → 任一非终态 phase` 的转换描述中，明确区分退回影响范围：若只影响结果包，递增 result_version 并回到对应阶段，不清除 plan_version 相关字段；若影响计划、范围或成功标准，才递增 plan_version 并执行完整级联失效。当前 spec 第 256 行的"Human 退回时按受影响范围回到 executing/controller_checking/independent_reviewing/closure_preparing"已经部分正确，但第 277 行的"若改计划按 plan_version 级联失效；若改结果按 result_version 失效"之间存在歧义——它没有明确"改结果但不改计划"时是否也需要递增 plan_version |

### P2-2 | `human_closure_confirming` 阶段 `waiting_on` 不明确

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §6，第 319 行 |
| **违反的上位要求** | 00 §8.2 交还要求：Human Gate 交还必须清楚说明待决定事项；V6 工作接续：后续执行者必须能恢复当前状态 |
| **具体失败场景** | WorkCase 进入 `human_closure_confirming` 后，AI 压缩上下文或切换模型。新 AI 需要知道当前是等待 Human 关闭确认。但 spec 第 319 行只要求 `human_plan_confirming` 和 `human_closure_confirming` 阶段必填 `waiting_on`，而 `human_closure_confirming` 的进入条件（第 311 行）只要求"更新 summary/resume_from/waiting_on；closure_approval 禁止"，没有明确 `waiting_on` 在该阶段必须填写什么内容。如果 AI 省略了 `waiting_on`，新执行者无法区分"正在等待 Human 决定"和"阶段已停滞但未标记" |
| **影响** | Web 恢复时无法确定是否在等待 Human 决定，可能误判 WorkCase 为停滞而非等待 |
| **最小修正建议** | 在 `human_closure_confirming` 的进入条件中明确 `waiting_on` 必须为非空 string，内容为"等待 Human 关闭确认"或类似表述，与 `human_plan_confirming` 阶段保持一致 |

### P2-3 | Code 对 `creation_reviews` 的阻断检查不完整

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/facts/validation.py` 第 399-404 行 |
| **违反的上位要求** | 05 §9.1 状态边界：每次转换所需的来源、证据、验证和必要授权必须完整；21 §6：creation_reviews 联合覆盖必须无未解决阻断项 |
| **具体失败场景** | creation_reviews 中有一项 `pass_with_followups`，其 feedback 包含"建议补充验证方法"，但 controller_resolution 没有逐项回应（例如缺少第 2 条 feedback 的处理）。当前 Code 检查（第 400-404 行）只检查 `conclusion` 值不在 `{pass, pass_with_followups}` 中，即只检查了 `changes_required` 和 `blocked`。`pass_with_followups` 通过了，但 controller_resolution 可能没有覆盖所有 feedback 条目 |
| **影响** | 虽然 spec 要求 controller_resolution 必须"按 feedback 原顺序使用编号清单逐项对应"，但 Code 没有检查这一条件。接受不完整的 controller_resolution 可能使未处理的反馈被忽略，Human 看到的计划可能包含未解决的缺陷 |
| **最小修正建议** | 在 `_validate_workcase` 函数中增加：对 `pass_with_followups` 的审核，检查其 `feedback` 数组长度是否与 `controller_resolution` 中实际处理的项数匹配（简单检查分辨项数，如编号数量或换行数；不要求自然语言语义判断）。或者，在 spec 中把 `pass_with_followups` 的 controller_resolution 完整性检查列为"后续 Code 能力"（当前 Code 不语义判断） |

### P3-1 | `workcase-item-current-summary` 字段在 item `completed` 后应移除但未明确

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §6，第 252 行（工作项状态条件表） |
| **违反的上位要求** | 05 §9.2 更新规则：内容变化应如实反映 |
| **具体失败场景** | 工作项从 `in_progress` 变为 `completed` 后，current_summary 和 resume_from 被禁止（第 252 行），但 spec 没有说明谁负责移除它们。如果 AI 忘记删除，validator 会报错，但实际的创建/更新操作尚未实现，暂时无影响 |
| **影响** | 当前无影响（因为受控更新尚未实现），但未来受控更新实现时必须包含自动移除条件字段的能力 |
| **最小修正建议** | 在 §6 工作项状态条件表后增加一句：状态转换时，Code 的受控更新操作必须自动移除禁止字段并写入必填字段。该需求可列为后置能力 |

### P3-2 | F1 卡片中 `work_item_counts` 派生字段的命名未在 spec 中授权

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/helper/operations/fact_candidate_operation.py` 第 242-250 行 |
| **违反的上位要求** | 05 §7.1：派生 Schema 必须从登记的唯一字段定义和类型绑定单向组合；派生字段不得成为新字段权威 |
| **具体失败场景** | `fact_candidate_operation.py` 在 F1 卡片中为 WorkCase 添加了 `work_item_counts` 派生字段（第 248-250 行），但 21 §6 第 313 行只授权"Web 和 Helper 可以从当前对象派生……工作项计数"，F1 的显式字段投影（§6 第 312 行）没有列出 `work_item_counts`。虽然这是派生字段而非登记字段，但 F1 的字段闭集在 spec 中固定为 `object_id/title/status/goal/scope/summary/priority/blocking_summary/updated_at`，没有 `work_item_counts` 的授权 |
| **影响** | 低——派生字段确实是 Web 和 Helper 需要的，且不写回对象。但严格来说，F1 投影在 spec 中的闭集与 Code 实际输出不一致，可能在未来 Schema 变更时造成派生字段的维护遗漏 |
| **最小修正建议** | 在 21 §6 第 312 行的 F1 卡片字段投影中增加 `work_item_counts` 说明，或在 21 §6 的派生展示边界中明确"F1 卡片可包含从工作项状态派生的计数" |

### P3-3 | `blocked → closed` 路径的 spec 描述与流程图有细微不一致

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §6，第 280 行 vs 第 217-240 行流程图 |
| **违反的上位要求** | 00 §7 验证要求：声明必须与实际范围一致 |
| **具体失败场景** | spec 第 280 行明确允许 `blocked → closed` 路径，但流程图（第 217-240 行）没有显示该路径，直接从 `human_closure_confirming → closed` |
| **影响** | 低——流程图是辅助理解，文字是规范依据。但流程图缺少该路径可能导致 AI 误以为 blocked 状态不能直接关闭 |
| **最小修正建议** | 在流程图中增加从 `human_closure_confirming` 到 `closed` 的路径标注，或增加注释说明 "blocked 状态的 WorkCase 也必须经过完整关闭流程才能 closed" |

---

## 5. 对 §5 各组问题的明确回答

### 5.1 对象与颗粒度

- ✅ "一个可独立判断关闭的责任"足以稳定界定 WorkCase。V4 的准入条件（§4 六项条件）比 V3 更严格，且有明确的 Spark 与 WorkCase 分界。
- ✅ "直接服务同一关闭责任、具有阶段目标和可观察结果"足以稳定界定 work item。spec 明确禁止命令步骤、临时 todo、工具日志进入 work item。
- ⚠️ 反例：如果 AI 把"修复三个 bug"拆分为三个独立 work item，但三个 bug 共用同一组成功标准，则它们应合并在一个 WorkCase 中而非拆分为三个。Spec 的 `success_criteria` 整体验收边界设计已经容纳这一场景，但颗粒度判断的最终操作判据仍依赖 AI 和独立审核。
- ⚠️ 颗粒度判断由 AI、独立审核和第一次 Human Gate 共同承担是足够的，但缺少"当 work item 超过 10 个时是否应拆分为多个 WorkCase"的启发式规则。建议在 V4 后续版本中补充为经验性建议而非强制规则。

### 5.2 生命周期与双 Gate

- ✅ 创建前审核 → 创建后第一次 Human Gate 的先后关系完全自洽。
- ✅ status 与 phase 双轴正交且无歧义。
- ✅ phase 闭集完整，允许边全部列出，退回路径覆盖所有非终态阶段。
- ⚠️ **P2-1**：退回时 plan_version 级联失效的范围有歧义，已列问题。
- ✅ plan_version 和 result_version 的失效规则足够防止旧授权覆盖新内容——旧审核和批准在版本变化后全部移除。
- ✅ 不存在可以绕过 Human Gate 的路径。`blocked → closed` 也要求完整关闭流程。
- ⚠️ **P2-2**：`human_closure_confirming` 的 `waiting_on` 可恢复性不足。

### 5.3 字段、结构与事实边界

- ✅ 三个新增结构（workcase-item、workcase-review、workcase-human-approval）都有稳定独立消费价值。
- ✅ 没有发现同义字段。V3 的 `related_*`、`followup_refs`、`revision_history`、`blocking_reason` 全部被合理替代或删除。
- ✅ 当前只保留当前版本审核，旧版本由 Git 追溯，完全满足追溯与消费需求。
- ✅ `summary`/`resume_from`/`waiting_on` 分工清楚：`summary` 是阶段快照，`resume_from` 是恢复入口，`waiting_on` 是等待条件。三层不重复。
- ✅ review feedback 和 controller_resolution 的结构足够证明反馈得到处理——要求逐项编号对应的机制防止了"已读不回"。

### 5.4 AI、Code、行动模板与环境边界

- ✅ Code 的确定性检查范围（Schema、枚举、时间、引用 shape、DAG、版本绑定）与 spec 授权一致，没有越权解释自然语言。
- ⚠️ **P2-3**：Code 对 `pass_with_followups` 的 controller_resolution 完整性检查不足。
- ✅ WorkCase 没有承担行动模板或环境执行器责任。spec 第 1 条明确声明"不负责定义单个工作项内部的实施步骤"。
- ✅ 未来"事实对象状态转换与承接处置"模板可以无歧义消费当前 Schema——plan_version、result_version、status、phase、creation_reviews、result_reviews、execution_approval、closure_approval 都是确定性字段。
- ✅ 当前设计支持高性能 AI 规划、低性能 AI 执行、高性能 AI 检查的分工。WorkCase 不记录"执行者是谁"，只记录审核者的可区分身份（reviewer 字段）。

### 5.5 渐进式披露、进度和 Web

- ✅ F1 的 `phase + work_item_counts + status` 足够恢复责任上下文。何时展开 F3 由 spec 第 316 行明确：精确绑定 WorkCase 时必须展开 F3。
- ✅ 没有百分比的阶段条、计数和活动项摘要提供了足够的进度感，且避免了伪造精度。
- ✅ Web 派生视图（阶段条、工作项计数、active item 信息）在 spec 中被明确限制为"不得写回对象或取得状态权威"。不会形成第二事实源。

### 5.6 V3 意图与 V4 改进

- ✅ V3 的中断恢复意图 → V4 双层 resume_from 实现。
- ✅ V3 的独立审核意图 → V4 的 creation_reviews/result_reviews 结构化记录。
- ✅ V3 的双 Human Gate 意图 → V4 的版本绑定 approval 机制。
- ✅ V3 的对象内历史 → V4 的 Git 历史 + 当前版本快照。
- ✅ V3 的 execution_items 过重结构 → V4 精简的 work_items。
- ✅ V3 的 orchestration 容器 → V4 移除，由行动模板和当次计划承担。
- ⚠️ V3 的 `pass_with_followups` 审核结论（在 V3 的 review_items 中出现 51 次）→ V4 保留该枚举值，但 Code 未检查 controller_resolution 的完整性。这是一个测试缺口。
- ❌ 没有发现被 V4 忽略但值得吸收的 V3 意图。V3 的 `residual_risks` 和 `followup_refs` 被更精确的 `disposition_summary` + `routed-to` 关系替代，是合理改进。

---

## 6. 问题分类汇总

| 问题 | 类型 | 严重度 |
|---|---|---|
| P2-1：Human 退回后 plan_version 级联失效范围歧义 | **规范缺陷** | P2 |
| P2-2：`human_closure_confirming` 阶段 `waiting_on` 不明确 | **规范缺陷** | P2 |
| P2-3：Code 对 `pass_with_followups` 的 controller_resolution 检查不完整 | **实现缺陷** | P2 |
| P3-1：item completed 后移除条件字段未显式说明 | **可读性问题** | P3 |
| P3-2：F1 `work_item_counts` 派生字段未在 spec 中授权 | **规范缺陷** | P3 |
| P3-3：流程图未显示 blocked → closed 路径 | **可读性问题** | P3 |

**已声明的后置能力（不列为问题）：**
- 事实对象受控更新/CAS（阶段 5 后置）
- 阶段转换写入（阶段 5 后置）
- 多对象事务（阶段 5 后置）
- 生命周期行动模板（阶段 6 后置）
- Web 进度界面（阶段 9 后置）
- 环境 Hook（阶段 8 后置）

---

## 7. 审计实际阅读的文件

### 必读资料（按交接包顺序）

1. `specs/00-理念与构成.md` ✅
2. `specs/05-事实模型基础规范.md` ✅
3. `specs/attachments/05.Att.01-事实对象统一字段登记.md` ✅
4. `specs/06-行动模板基础规范.md` ✅
5. `specs/21-WorkCase-工作项.md` ✅
6. `docs/v4-architecture/V4-WorkCase类型封闭记录.md` ✅
7. `docs/v4-architecture/V4-五类型全局归并封闭记录.md` ✅
8. `docs/v4-architecture/V4-工作推进总纲.md` ✅
9. `docs/v4-architecture/V3-行动资产盘点与V4内部行动能力设计.md` ✅
10. `archive/v3/specs/21-WorkCase-工作项.md` ✅
11. `archive/v3/specs/attachments/21.Att.01-orchestration字段契约表.md` ✅
12. `archive/v3/ldvh-base/workcases/` 抽查实例 ✅
13. `V3-WorkCase-架构分析-独立只读.md`（可选参考）— 未审计，按交接包要求不作为规范权威
14. `code/ldvh/facts/validation.py` ✅
15. `code/ldvh/helper/operations/fact_candidate_operation.py` ✅
16. `code/ldvh/helper/operations/fact_candidate_request.py` ✅
17. `code/tests/facts/test_validation.py` ✅
18. `code/tests/helper/test_fact_candidate_operation.py` ✅
19. `code/tests/helper/test_fact_creation_operation.py` ✅
20. `code/tests/helper/test_fact_object_operation.py` ✅
21. `code/tests/specs/test_field_registry.py` ✅

### 抽查的 V3 实例

- `workcase-0001-runtime-entry-user-input-contract.yaml`（简单对象，含 execution_items 和可复用的阶段目标模式）
- `workcase-0010-codex-parallel-execution-orchestration.yaml`（含多 execution items，demonstrates V3 的 role/mode/input_refs 运行脚手架）
- `workcase-0014-workcase-tail-routing-confirmation.yaml`（含 plan_review/review_items 和依赖关系，展示 V3 审核结构）

### 未覆盖范围

- 未抽查全部 24 个 V3 实例（审计交接包要求"至少抽查简单对象、长对象、含多 execution items 对象、审核/关闭状态有代表性的对象"，已覆盖前三种）
- 未审计 Web 代码（`web/` 目录）——不属当前审计范围
- 未审计环境 Hook 和 adapter 实现（阶段 8 尚未开始）
- 未审计具体行动模板（阶段 6 尚未定义具体模板）
- 未审计 `code/ldvh/facts/relations.py` 的 P1 问题（已在推进总纲中明确记录，不属于 WorkCase 设计本身的缺陷）