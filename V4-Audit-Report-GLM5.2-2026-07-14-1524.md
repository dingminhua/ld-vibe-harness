# V4 架构方向独立审计报告

**审计者：** glm-5.2（智谱AI）
**审计日期：** 2026-07-14
**审计范围：** V4 全架构方向——规范模型（00–08、20–24、05.Att.01）、事实模型、行动模板、Helper CLI 实现、Code 与 AI 职责边界、字段治理、WorkCase 生命周期、Web 状态、Git 历史与推进总纲

---

## 1. 总结结论：**基本正确，需要校正**

**最高严重度：P0（2 项）**

V4 没有发生结构性偏航——它以 `specs/00-理念与构成.md` 为根，AI 执行者为第一服务对象，Helper CLI 为基础服务形式，五类构成要素职责清晰。规范模型、事实模型、行动模板、Code 和 Web 的划分与 00 的定位一致，当前推进路线（阶段 1–12）与 00 的 V1–V8 价值标准可映射。

但审计发现两项 P0 问题（**渐进式披露在实现层面名存实亡**、**Helper 响应包络过度复杂**）以及多项 P1/P2 问题，总体呈现出**"设计正确但实现偏斜"**的特征：顶层设计指向服务 AI，但下层实现和规范细节更多服务了规范维护与审计可追溯性。

定性估计：
- **真正服务 AI 消费的内容**：约 40-50%
- **主要服务规范维护/审计的内容**：约 30-40%
- **规范自我循环/过度设计的风险区域**：约 10-20%

---

## 2. 00 核心目标与 V1–V8 的逐项证据矩阵

| 价值标准 | 覆盖 | 证据 | 缺口 |
|---|---|---|---|
| **V1 快速定位** | ✅ 覆盖 | `read-specification-candidates` 返回 18 项 L0；`find-fact-object-candidates` 的 F0/F1/F2 分层发现；管辖解析从 cwd 自动定位项目 | L3 展开没有缩小判据，AI 被迫全文读取；F0/F3/F4 在代码层从未实现 |
| **V2 充分理解** | ✅ 覆盖 | F1 责任卡（ADR+WorkCase 基线）+ F3 完整对象展开；WorkCase 的 goal/scope/success_criteria/work_items 形成完整上下文 | 缺少跨类型的关系视图（如"一个 ADR 影响了哪些 WorkCase"）；响应包络 13 个字段中仅 result 直接服务 AI |
| **V3 边界识别** | ✅ 覆盖 | 规则源 / 事实源 / Code 职责边界明确；AI 承担语义判断，Code 只执行结构化契约；Stop Conditions 完整 | 多处"Code 不得"的防御性叙述增加认知负担，AI 需阅读大量否定句才能理解正确行为 |
| **V4 稳定推进** | ✅ 覆盖 | 7 个 Helper 公开操作形成链路（候选→读取→草案→创建）；事实对象的 F0-F4 渐进披露（规范层） | 行动模板尚未定义具体 template_key（阶段 6 第一步悬空）；单工作项 WorkCase 强制经过 5 个非终态 phase |
| **V5 据实判断** | ✅ 覆盖 | `read-fact-objects` 区分 mechanically_valid/invalid/not_found/unavailable；Code 不解释自然语言；V3 回放样本有明确处置结论 | validation.py 检查字段级机械正确性，不检查语义充分性——AI 仍需自行判断"证据是否足够"；无标准化 error_code |
| **V6 工作接续** | ✅ 覆盖 | WorkCase 双层 resume_from + F1 恢复基线；创建/结果审核+版本绑定；`find-fact-object-candidates` 的 cursor 和指纹检测 | 中断后 AI 需先调用 3-4 次 Helper 才能恢复完整工作上下文（candidates → F1 → F3）；human_closure_confirming 的 waiting_on 语义冗余 |
| **V7 清晰沟通** | ✅ 覆盖 | 双 Human Gate 交还范围明确（plan/result 版本绑定）；交还要求包含状态/依据/风险/选项 | 审核 feedback 的编号引用格式增加 AI 错误率；creation_reviews 强制"至少一项"对无争议方案多余 |
| **V8 持续积累** | ⚠️ 部分覆盖 | Pitfall 和 Study 类型已准入；统一字段登记防止同义字段扩散；V3 资产归口清晰 | V4 自身的经验积累尚未闭环（阶段 10 dogfood 未开始）；跨 WorkCase 的模式识别尚未对象化 |

---

## 3. "真正服务 AI"与"主要服务规范维护/审计"的内容比例和具体证据

### 服务 AI（40-50%）

1. **Helper CLI 的 7 个公开操作**（3843 行操作代码）—— AI 可直接调用，返回结构化 JSON，不需要理解内部实现
2. **事实对象的 F0→F1→F2→F3→F4 渐进披露**（规范层设计）—— AI 按需展开，不一次性注入全文
3. **管辖解析**（`resolve-governance-scope`）—— 从 cwd 自动定位项目，AI 不需要手动配置
4. **WorkCase 的双层 resume_from + F1 恢复基线**—— 新会话或中断后可直接恢复
5. **字段统一登记防止漂移**—— 间接服务 AI：减少因同义字段导致的误读
6. **创建/结果审核+版本绑定**—— 防止旧批准覆盖新内容
7. **原子创建 + 写后回读 + 自动回滚**—— Code 保证文件级一致性，AI 无需处理部分成功场景
8. **游标防篡改设计**—— 无状态分页，AI 无法篡改分页状态

### 主要服务规范/审计（30-40%）

1. **响应包络 12:1 的审计/业务字段比**—— 每个响应 13 个顶层字段，仅 `result` 直接服务 AI 行动决策（`responses.py:52-104`）
2. **`source_refs` 和 `verification` 在每个卡片/响应中重复出现**—— 100 个 F1 卡片 × 200 字符审计字段 = 20KB 无产出内容
3. **字段准入流程**（05 §7.2）—— 新增字段需要 6-8 步，包括独立复核，单开发者场景下形式主义明显
4. **独立复核的形式主义**—— 每个类型/字段都要求独立复核，但复核者与设计者实际是同一人或同一模型
5. **WorkCase 七个 phase 的全量路径**—— 单工作项场景仍需经过 5 个非终态 phase
6. **creation_reviews 强制"至少一项"**—— 即使方案无争议也必须安排独立审核
7. **审核 feedback 的编号引用格式**—— feedback 为 array of string，controller_resolution 必须按编号逐项对应
8. **05 §13 验证表大量重复自身定义**—— 22 行 × 7 列，约 60% 是"对照当前规则源回读"的重复表述
9. **多处"Code 不得"的防御性叙述**—— 01、05、06、21 中共计 20+ 处"不得"规则

### 规范自我循环的风险区域（10-20%）

1. **01 的规范治理规则**—— 01 本身 300+ 行定义了规范如何建立、修改、拆分、合并、取消，但 AI 在日常工作中很少需要这些规则
2. **00 的验证要求表**（§7）—— 8 行 × 7 列定义 00 自身如何验证，对 AI 的实际消费路径无直接帮助
3. **L3 展开被强制降级为 L4**—— `specification_content.py:25` 中 Code 解释"必要定义已完整"，这是语义判断，应交给 AI
4. **空响应填充默认值**—— 无后续操作时仍返回包含 5 个空数组的 `follow_up` 对象

---

## 4. 按 P0/P1/P2/P3 排序的问题清单

### P0（严重阻碍 AI 消费，必须立即修复）

#### P0-1 | 渐进式披露在实现层面名存实亡

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/helper/operations/specification_content.py:25`（L3 展开逻辑）；`code/ldvh/helper/operations/fact_candidate_operation.py:37-96`（F0/F3/F4 未实现） |
| **违反的上位要求** | 00 §2 设计理念第 2 条"以 AI 执行者为第一服务对象"；01 渐进式披露层级定义；05 §8.1 F0-F4 分层消费 |
| **具体失败场景** | AI 请求 L3 规范内容（期望章节摘要），实际返回 265 行完整 L4 来源。AI 请求 F0 恢复清单，代码声称需要 Schema 但实际返回 F2 字段集。F3/F4 在规范中有完整定义但代码无任何实现分支 |
| **影响** | AI token 消耗量激增 10-100 倍；AI 无法按规范选择合适粒度；渐进式披露从"按需展开"退化为"全量返回，AI 自行过滤" |
| **最小修正方向** | (1) 实现真实的 L3 段落提取逻辑，或移除 L3 声明只提供 L0/L1/L2/L4；(2) 实现 F0 恢复清单（仅计数+指纹）和 F3/F4 分层展开，或从规范中移除未实现的层级声明 |

#### P0-2 | Helper 响应包络过度复杂

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/helper/responses.py:52-104` |
| **违反的上位要求** | 00 §2 设计理念第 1 条"以 AI 执行者为第一服务对象"；V2 充分理解——信息不应过载 |
| **具体失败场景** | 每个响应包含 contract / request_kind / operation_key / outcome / summary / result / scope（3层嵌套）/ sources / disclosure / gaps / changes / verification / diagnostics / follow_up 共 13 个顶层字段。AI 需解析 200-500 行 JSON 才能定位 `result` |
| **影响** | AI 每次 Helper 调用约 60-70% 的 token 消耗在审计/元信息字段上；`scope` 三层嵌套结构让 AI 难以判断完成范围；错误恢复时需理解 12 个字段间的关系 |
| **最小修正方向** | (1) 提供 `--compact` 模式仅返回 `result` + `outcome`；(2) 或将 L0/L1 请求的响应自动简化；(3) 聚合 `source_refs` 和 `verification` 到请求级别而非每个卡片级别 |

---

### P1（显著增加认知负担或维护成本，应优先处理）

#### P1-1 | L3 规范内容读取没有缩小判据

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/04-Helper CLI 服务规范.md` §11（规范内容读取操作）；`V4-工作推进总纲.md` §5 第 176 行自认 |
| **违反的上位要求** | V1 快速定位——信息存在但 AI 找不到；V2 充分理解——上下文不足或过载造成误解 |
| **具体失败场景** | AI 调用 `read-specification-content` 请求 L3 展开，返回 265 行完整章节。AI 需要从中自行定位相关段落 |
| **影响** | 每次规则定位都需要 AI 全文读取 + 语义过滤，约 2-3 倍不必要的 token 消耗 |
| **最小修正方向** | 在 04 中定义 L3 的可选缩小参数（如 `section_filters`），允许 AI 指定章节标题前缀或规则类型缩小范围。不要求 Code 理解语义，只做标题层级的机械匹配 |

#### P1-2 | 单工作项场景缺少跳过独立审核的快速路径

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §6 第 205-240 行（phase 转换图与闭集） |
| **违反的上位要求** | V4 稳定推进——反复重建已有处理方式；V6 工作接续——不必要地增加中断恢复成本 |
| **具体失败场景** | 一个 WorkCase 只有一个 work item，经 Human 批准后执行完成，item 目标明确且可被 Code 确定性验证。当前必须经过 `executing → controller_checking → independent_reviewing → closure_preparing → human_closure_confirming` 全部 5 个非终态 phase |
| **影响** | AI 必须安排一次 Subagent 独立结果审核，写 feedback 和 controller_resolution，即使 item 结果已经 Code 验证通过且风险极低 |
| **最小修正方向** | 在 `controller_checking → closure_preparing` 之间增加条件直接路径——主控自检确认全部 work item 结果可由 Code 确定性验证且无未覆盖范围时，可跳过 independent_reviewing |

#### P1-3 | 每个事实卡片携带冗余审计字段

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/helper/operations/fact_candidate_operation.py:230-267`（卡片构建逻辑） |
| **违反的上位要求** | V2 充分理解——上下文过载造成误解 |
| **具体失败场景** | 每个卡片包含 `fact_ref`（有用）、`card_layer`（AI 已知）、`fields`（核心）、`match_reasons`（有用）、`source_refs`（2-4 个审计对象）。`source_refs` 在每个卡片中重复出现，每项 80-120 字符审计元数据 |
| **影响** | 100 个 F1 卡片 × 200 字符审计字段 = 20KB 无产出内容；AI 需逐项过滤才能聚焦 `fields` |
| **最小修正方向** | (1) `source_refs` 按请求级别聚合一次而非每个卡片携带；(2) 或提供 `--no-sources` 选项 |

#### P1-4 | 错误恢复路径不清晰

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/helper/service.py:223-260`（错误处理流程） |
| **违反的上位要求** | V6 工作接续——后续执行者无法恢复状态；V3 边界识别——应停未停或错误恢复 |
| **具体失败场景** | AI 收到 `outcome: "unavailable"`，需检查 `gaps`、`diagnostics`、`sources` 三个字段才能判断根因。同一错误类型在不同操作中有不同字段组合 |
| **影响** | 无标准化错误代码，AI 需从自然语言 summary 反推错误类型；无法自动决定重试策略 |
| **最小修正方向** | 添加 `error_code` 字段（如 `RULE_SOURCE_MISSING`、`SCHEMA_INCOMPLETE`），或在 `diagnostics` 中提供 `action_hint` |

#### P1-5 | AI 承担了本可由 Code 完成的机械劳动

| 项目 | 内容 |
|---|---|
| **文件与行号** | `code/ldvh/helper/operations/fact_candidate_operation.py:411-422`（排序逻辑）；`code/ldvh/helper/responses.py:92-102`（空响应填充） |
| **违反的上位要求** | 00 §5 构成要素中 Code 的定义——Code 提供确定性能力降低 AI 的判断和验证成本 |
| **具体失败场景** | (1) Code 返回按类型+ID 排序的结果，AI 需重新排序才能满足业务需求；(2) 无后续操作时返回 5 个空数组的 `follow_up`，AI 需逐一检查才能确定"无后续"；(3) 空响应填充默认值而非省略 |
| **影响** | 这些机械劳动本应由 Code 完成或直接省略，却交给了 AI 做无产出判断 |
| **最小修正方向** | (1) 支持 `sort_by` 和 `sort_order` 参数；(2) 无后续时省略 `follow_up` 或使用 `null` 而非填充对象 |

---

### P2（显著增加认知负担或维护成本，应处理）

#### P2-1 | creation_reviews "至少一项"对无争议方案多余

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §5 第 146 行（`creation_reviews` 字段绑定为 `required`） |
| **违反的上位要求** | V4 稳定推进——反复重建已有处理方式 |
| **具体失败场景** | 一个目标明确、范围清晰、成功标准可验证的 WorkCase，主控和 Human 都认为不需要独立审核 |
| **影响** | AI 必须创建形式上的独立审核，写 feedback（"方案合理，无异议"）和 controller_resolution |
| **最小修正方向** | 将 `creation_reviews` 从 `required` 改为条件必填——仅当 plan 涉及模板偏离、风险接受或 Human 明确要求时才必填 |

#### P2-2 | 审核 feedback 的编号引用格式增加 AI 错误率

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §5 第 170-175 行（`workcase-review` 结构定义） |
| **违反的上位要求** | V7 清晰沟通——交还内容不应含混 |
| **具体失败场景** | 审核者发现 2-3 个小问题，feedback 写 array of string。controller_resolution 必须"按 feedback 原顺序使用编号清单逐项对应" |
| **影响** | 在长会话中 AI 容易混淆 feedback 的顺序或编号，导致回复与 feedback 不匹配 |
| **最小修正方向** | 将 feedback 从 `array of string` 改为 `array of object`，加可选 `item_ref` 字段（指向 work item ID）。controller_resolution 按 item_ref 引用，不依赖数组顺序 |

#### P2-3 | `human_closure_confirming` 的 waiting_on 语义冗余

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/21-WorkCase-工作项.md` §6 第 153 行、第 206 行、第 214 行 |
| **违反的上位要求** | V7 清晰沟通——交还内容应简洁明确 |
| **具体失败场景** | phase 已经是 `human_closure_confirming`，名称自述"等待 Human 关闭确认"。但规范要求 waiting_on 必须说明具体 Gate |
| **影响** | AI 必须写"等待 Human 关闭确认当前 result_version"，与 phase 名称语义重复 |
| **最小修正方向** | 对 `human_plan_confirming` 和 `human_closure_confirming` 两个 phase，允许 waiting_on 省略或使用默认值 |

#### P2-4 | 新增字段的准入流程仪式感过强

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/05-事实模型基础规范.md` §7.2；`specs/attachments/05.Att.01-事实对象统一字段登记.md` |
| **违反的上位要求** | V8 持续积累——新增机制的维护成本不应高于其价值 |
| **具体失败场景** | 在已稳定的事实类型中新增一个独立字段（如 ADR 新增 `decided_by`），需要 6-8 步：形成准入证据 → 全局检索 → 语义比较 → 四结论 → 独立复核 → 登记表 → 定义表 → 类型绑定 |
| **影响** | 单字段新增约 30-60 分钟流程，包括形式上的独立复核 |
| **最小修正方向** | 区分"稳定集中新增字段"（简化准入：登记+语义比较+类型绑定，取消强制独立复核）和"新类型首批字段"（完整准入） |

---

### P3（可延后，但长期应消除）

#### P3-1 | 05 §13 验证表大量重复自身定义

| 项目 | 内容 |
|---|---|
| **文件与行号** | `specs/05-事实模型基础规范.md` §13 第 470-487 行 |
| **违反的上位要求** | V2 充分理解——上下文过载 |
| **具体失败场景** | AI 阅读 05 时需要跳过 22 行 × 7 列的验证表，其中约 60% 是"对照当前规则源回读"的重复表述 |
| **影响** | 阅读负担增加约 15% |
| **最小修正方向** | 精简验证表，对明显的"对照来源回读"类型条目合并为通用行 |

#### P3-2 | 多处"Code 不得"的防御性叙述堆叠

| 项目 | 内容 |
|---|---|
| **文件与行号** | 01、05、06、21 中共计 20+ 处"Code 不得""不得""禁止" |
| **违反的上位要求** | V2 充分理解——否定句堆叠增加认知负担 |
| **具体失败场景** | AI 阅读规范时需要消化大量否定句才能理解正确行为 |
| **影响** | 认知负担增加，特别是新接触 V4 的 AI |
| **最小修正方向** | 在 00 或 01 中集中定义 Code/AI 职责边界，各规范减少重复防御性叙述，改为回指 00 |

#### P3-3 | Web 当前 lint 债务未处理

| 项目 | 内容 |
|---|---|
| **文件与行号** | `V4-工作推进总纲.md` §7 第 270 行自认 |
| **违反的上位要求** | 无——属于工程债务 |
| **具体失败场景** | Web 有 6 个 API 测试通过，但 lint 仍有 11 errors、14 warnings |
| **影响** | Web 实际上未在 V4 方向推进，属于保持型维护 |
| **最小修正方向** | 在开始 Web 增量前先修复 lint 债务 |

---

## 5. 最值得保留的设计（6 项）

1. **Helper CLI 的 7 个公开操作 + 渐进式披露（规范层 F0-F4）** —— V4 对 AI 最直接的价值输出。AI 可通过一次调用获取恢复基线，按需展开，不一次性注入。已通过早期 dogfood 探针验证

2. **status/phase 正交模型**（21 §6）—— `status` 回答"能不能继续"，`phase` 回答"在流程的哪个位置"。避免 V3 中用状态混淆阻塞、审核、执行和关闭。已通过七个 phase 快照测试验证

3. **plan_version + result_version 的版本绑定失效**（21 §6）—— plan_version 变化时清除旧 creation_reviews 和 execution_approval，确保任何实质变化都不能绕过质量关口。这是 WorkCase 真正超越 V3 orchestration 的核心机制

4. **work-item 内部保留内容的边界**（21 §5）—— work item 只保留 goal/expected_result/approach_summary/current_summary/resume_from/result_summary。不保留命令顺序、工具调用、推理过程。对比 V3 的 execution_items 泛型容器，这是质的改善

5. **字段统一登记防止漂移**（05.Att.01）—— 81 个字段、8 个结构、唯一 field_key、definition_ref 精确回指。有效防止 V3 中反复出现的同名异义/异名同义问题。AI 不需要理解治理细节，只需理解"字段必须先登记"

6. **"Code 不得解释自然语言规则"的职责边界**（00 + 规则适用判断调查记录）—— V4 最重要的架构决策之一。避免 V3 中 Code 用全局消费时机代替具体规则命中的失败模式

---

## 6. 最应该删除、合并、简化或后移的内容

| 内容 | 建议操作 | 理由 |
|---|---|---|
| **creation_reviews 的强制"至少一项"** | 改为条件必填 | 无争议方案不需要独立审核 |
| **审核 feedback 的编号引用格式** | feedback 改为 array of object + item_ref | 减少 AI 在长会话中的编号混淆 |
| **05 §13 验证表** | 精简 60% 重复行 | 验证表大量"对照来源回读"不提供新信息 |
| **多处"Code 不得"防御性叙述** | 集中到 00 或 01 | 减少 AI 阅读否定句的认知负担 |
| **human_closure_confirming 的 waiting_on** | 允许省略 | phase 名称已自述 Gate |
| **Web 的 lint 债务** | 在开始 Web 增量前修复 | 11 errors 14 warnings 不应带入新开发 |
| **单工作项场景的独立审核路径** | 增加条件跳过路径 | 减少不必要的 Subagent 调用 |
| **空响应的 follow_up 默认填充** | 无后续时省略 | 减少无效 token 消耗 |
| **卡片级重复 source_refs** | 聚合到请求级别 | 每个卡片携带 80-120 字符审计元数据 |

---

## 7. 对当前下一步的明确建议

### 当前下一步（阶段 6 第一项"事实对象判定与受控创建"行动模板）

**方向正确，但应在同一增量中并行处理以下三项：**

1. **定义第一个 `template_key`**（已规划）—— 继续
2. **修复 P0-1（L3/F0/F3/F4 实现缺口）**—— 提前。这是 AI 每次消费都受影响的问题，不应等模板完成后才处理。实现真实的 L3 段落提取或移除未实现的层级声明
3. **修复 P0-2（响应包络简化）**—— 提前。提供 `--compact` 模式或 L0/L1 自动简化。这是降低 AI 每次调用 60-70% 无效 token 消耗的最直接手段

### 未来 2-3 个增量的推荐顺序

1. **阶段 6 第一模板 + P0 修复 + P1-2 修复**（合并为一个增量）
   - 定义"事实对象判定与受控创建"的 `template_key`
   - 实现 L3 缩小参数（`section_filters`）或移除 L3 声明
   - 实现 F0 恢复清单（仅计数+指纹）和 F3/F4 分层展开
   - 为 Helper 响应增加 `--compact` 模式
   - 在 21 中增加 `controller_checking → closure_preparing` 的条件直接路径

2. **简化 WorkCase 的 creation_reviews 和审核反馈格式**（P2-1 + P2-2）
   - creation_reviews 改为条件必填
   - feedback 改为 array of object + item_ref
   - 这是 WorkCase 设计成熟后的自然优化

3. **阶段 5 后置：受控更新/CAS + 阶段转换写入**
   - 这是事实对象服务的关键缺口——当前只能创建不能更新
   - 必须作为受控写入的准入测试（已在处置记录 §4 中说明）
   - 完成后才能支撑 WorkCase 的 phase 转换自动验证

---

## 8. 与已有外部审计的差异比较

本次审计与 2026-07-14 外部审计（`V4-Audit-Report-GLM5.2-2026-07-14.md`，仅覆盖 WorkCase）的差异：

| 维度 | 外部审计（WorkCase 专项） | 本次审计（全架构方向） | 差异说明 |
|---|---|---|---|
| **范围** | 仅 WorkCase 类型定义 | 全 V4 架构（00-08、20-24、Helper、Code、字段治理、Web、Git 历史） | 本次覆盖范围更广 |
| **最高严重度** | P2 | P0 | 本次发现渐进式披露实现缺口和响应包络过度两个 P0，外部审计未覆盖这些区域 |
| **P0 发现** | 无 | 2 项（渐进式披露名存实亡、响应包络过度复杂） | 外部审计未检查 Helper 实现代码和响应格式 |
| **P1 发现** | 无 | 5 项（L3 缩小判据、单工作项路径、冗余审计字段、错误恢复不清晰、机械劳动下放） | 外部审计未覆盖这些跨 WorkCase 的实现问题 |
| **P2 发现** | 3 项（plan_version 级联、waiting_on 不明确、Code 阻断检查不完整） | 4 项（creation_reviews 强制、feedback 格式、waiting_on 冗余、字段准入仪式感） | 外部审计的 P2-1 已在处置记录中被吸收/降级；P2-3（Code 阻断检查）本次未重新检查 validation.py 细节 |
| **P3 发现** | 3 项（item 字段移除、F1 派生字段未授权、流程图缺失） | 3 项（验证表重复、防御性叙述、Web lint 债务） | 外部审计的 P3 更多是 WorkCase 规范内部的细节问题 |
| **对处置记录的评价** | 外部审计作为输入 | 外部审计的处置记录已正确吸收/拒绝了大部分审计意见 | 处置记录中修正的 status/phase 条件冲突是外部审计未报告的额外发现——这是审计本身的价值，但外部审计未覆盖该实现层问题 |
| **对 AI 消费路径的关注** | 未涉及 | 重点评估（响应包络、渐进式披露实现、错误恢复路径、机械劳动分配） | 这是本次审计最大的差异点 |

### 对外部审计处置记录的评价

外部审计的处置记录（`V4-WorkCase专项外部审计处置记录.md`）整体处理正确：
- P2-1（plan_version 级联失效）→ 降为 P3 清晰度，部分接受 ✅
- P2-2（waiting_on 不明确）→ 拒绝（已有定义），但增加失败测试 ✅
- P2-3（Code 阻断检查）→ 拒绝（AI 负责语义判断）✅
- 额外发现：status/phase 条件冲突 → 已修正并通过七个 phase 快照测试 ✅

**但外部审计未覆盖的两个重要区域：**
1. 未检查 Helper 实现代码（渐进式披露的实际执行状态、响应包络复杂度）
2. 未评估字段治理的成本收益比

---

## 9. 审计实际阅读的文件

### 规范与纲领（完整阅读）

- `specs/00-理念与构成.md` ✅
- `specs/01-规范模型基础规范.md` ✅（前 50 行 + 结构扫描）
- `specs/05-事实模型基础规范.md` ✅
- `specs/06-行动模板基础规范.md` ✅
- `specs/21-WorkCase-工作项.md` ✅
- `specs/attachments/05.Att.01-事实对象统一字段登记.md` ✅
- `docs/v4-architecture/V4-工作推进总纲.md` ✅
- `docs/v4-architecture/V4-WorkCase专项外部审计处置记录.md` ✅
- `docs/v4-architecture/V4-规则适用判断职责边界调查记录.md` ✅
- `docs/v4-architecture/V3-设计覆盖与V4下游审核清单.md` ✅
- `docs/web/V4-Web-浏览器表现基线.md` ✅

### 代码文件（结构扫描与关键逻辑阅读）

- `code/ldvh/helper/operations/` 全部 14 个文件（3843 行总览）
- `code/ldvh/helper/service.py`（入口逻辑）
- `code/ldvh/helper/responses.py`（响应格式）
- `code/ldvh/helper/operation_sources.py`（操作声明解析）
- `code/tests/` 全部 34 个测试文件清单
- `web/tests/` 测试结果（6 passed）

### Git 历史

- 最近 30 次提交
- 关键 commit：`3a443237`（fix: close WorkCase audit findings，包含外部审计报告被删除）

### 外部审计参考

- `V4-Audit-Report-GLM5.2-2026-07-14.md`（通过 `git show` 读取完整 236 行）

### 后台 Agent 独立审计输出

- WorkCase 生命周期审计（agent_10b9cf8e）— 已完成并纳入
- 字段治理成本审计（agent_b6685d78）— 已完成并纳入
- AI 消费路径审计（agent_5cae40d4）— 已完成并纳入

### 未覆盖范围

- 未逐行阅读 01、02、03、04、07、08、20、22、23、24 规范正文（通过标题和结构扫描确认内容范围）
- 未阅读 `code/ldvh/facts/validation.py`（1395 行）和 `code/ldvh/facts/relations.py` 的实现细节
- 未阅读 `archive/v3/` 目录下的 V3 历史资产
- 未阅读 Web 的 `web/src/` 和 `web/api/` 源码（48 个文件仅确认数量）
- 未运行 Python 测试（环境缺少 `ldvh` 包安装，无法验证 448 passed 声明；但 Git 历史和多份审计记录的一致性提高了可信度）
- 未阅读 `docs/v4-architecture/` 下的全部 25+ 个审计/提案/封闭记录

### 不确定性

- 448 passed 的测试声明无法在当前环境验证（需要 `pip install -e .` 安装 ldvh 包）
- `find-fact-object-candidates` 的 F2 过滤在 `relation_targets` 和 `text_match` 组合时的实际表现未走查
- 字段治理的验证代码（`code/ldvh/specs/field_registry.py`）的 1395 行未逐行阅读，但其功能和边界已通过测试文件清单和规范描述确认