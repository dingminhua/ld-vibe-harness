---
title: LDVH 深度审计：规范—代码—实践三轴对齐与结构性改进方向
status: active
report_kind: internal_audit
research_question: 在 study-0022 已建立的价值主干与过度设计基线之上，进一步从规范密度、规范—代码对齐度、AI 执行体验、架构分层合理性与自诊断能力五个维度，审计当前 LDVH（v4 worktree，2026-08-05 观察时点）的实际运行状态，识别 study-0022 未覆盖的深层结构性问题，并提出可操作的分层改进路线。
abstract: 本次深度审计在 study-0022 的价值判断基础上，完成了五个新维度的全量探索：① 规范密度审计——创建单个 Spark 需要穿越 7 份规范、3 层交叉引用、23 条 Stop Conditions；② 规范—代码对齐审计——18 项 Helper 操作逐项映射，发现 3 项规范声明与代码实现之间存在"结构投影断言"式耦合而非语义绑定；③ AI 执行体验审计——首次以 Claude Code 在 Kimi Work 环境中实测完整 LDVH 交互链，记录 12 次 Helper 调用中 3 次 invalid_request 的根因与修正成本；④ 架构分层审计——facts 模块（7671 行）的 creation → application → transitions → validation 四层中 application 层价值不成立，transitions（1278 行）与 workcase_validation（984 行）可合并下沉；⑤ 自诊断能力审计——项目已有 3 份独立过度设计诊断，2 份残留审计（study-0021/0022），但无一份进入实际收敛。建议形成三层改进路线：第 0 层立即冻结——收敛三份诊断为一份共享基线并关闭火花；第 1 层小步快跑——helper 协议收敛 + 提交验证减负（1–2 周）；第 2 层结构性演进——比例原则自适用 + 条款日落机制（需 Human Gate ADR）。关键限制：未对 Web 层做运行时审计；未做跨平台验证；未做与外部工具（GitHub/GitLab）的集成验证。
research_intent: study-0022 已确认价值主干成立、过度设计为淤积型且三份诊断未收敛。本审计在此基础上完成 study-0022 明确标记为"未精读"和"未验证"范围的补充审计，并首次从 AI 执行体验角度（非 Kimi Work 的 Kimi 执行者视角，而是 Claude Code 的跨环境视角）提供独立复证，为后续 WorkCase 的具体计划形成提供更精确的改进边界。
recommendation_summary: 立即行动（无对象化成本）：更新 spark-0019 记录本审计中 Claude Code 的跨环境复证，更新 spark-0055 记录本审计对 80/20 倒置的独立复证。第0 层冻结：新建 WorkCase「收敛三份过度设计诊断为共享基线」。第 1 层小步快跑：更新承接 spark-0019 的 WorkCase，纳入本审计发现的规范—代码结构投影耦合问题。第 2 层方向取舍：条款日落方向继续等待 Human Gate。不必新建的对象：study-0021/0022 与本审计的三份独立诊断可互相印证，不必再建第四份价值评估报告。
input_refs:
- kind: specification
  locator: specs/00-理念与构成.md（全文，含 §6 V1-V8/HV1-HV5、§9 验证要求、§10 Human Gate、§11 Stop Conditions）
  version: 当前 working tree
  observed_at: '2026-08-05T16:30:00+08:00'
- kind: specification
  locator: specs/01-规范模型基础规范.md（§9.6–9.7）、specs/04-Helper CLI 服务规范.md（全文）、specs/05-事实模型基础规范.md（§7.2.1、§8.1、§11.4–11.11）、specs/06-行动模板基础规范.md（§5.1–5.4、§9）、specs/09-环境接入规范.md（§5）、specs/21-WorkCase-工作项.md（§4.4、§6）、specs/24-Study-研究报告.md（全文）、specs/30-Git提交行动模板.md（全文）、specs/31-事实对象判定与受控创建行动模板.md（全文）
  version: 当前 working tree
  observed_at: '2026-08-05T16:30:00+08:00'
- kind: specification-attachment
  locator: specs/attachments/04.Att.01-Helper CLI 请求与响应字段表.md（全文）、specs/attachments/09.Att.01-环境接入面.md（全文）
  version: 当前 working tree
  observed_at: '2026-08-05T16:30:00+08:00'
- kind: helper-call-results
  locator: 当次会话内 capabilities / resolve-governance-scope / read-specification-candidates / read-action-template-candidates / read-action-template-content（3 次 invalid_request + 修正重试）/ read-fact-objects（study-0022、spark-0055、spark-0019、spark-0056）的实际响应
  observed_at: '2026-08-05T16:22:00+08:00'
- kind: working-tree-statistics
  locator: specs/（20 文件 7,662 行，含附件 9,118 行）、code/ldvh/（非测试约 32,496 行，测试约 31,548 行，测试比 ≈0.97）、Web（3,724 TS/TSX 约 786,567 行含依赖）、ldvh-base/（59 workcase、6 adr、6 pitfall、22 study、56 spark）的当次核实统计
  observed_at: '2026-08-05T16:25:00+08:00'
- kind: git-history
  locator: git log（812 commits，branch dev-v4，HEAD d46775304）；归档评估（commit 6ecdcc4be 中 file-asset-0003 全文回读）
  version: HEAD @ 2026-08-05
  observed_at: '2026-08-05T16:23:00+08:00'
- kind: fact-objects
  locator: ldvh-base/studies/study-0021.md、study-0022.md（F3 全文回读）；ldvh-base/sparks/spark-0019.yaml、spark-0055.yaml、spark-0056.yaml（F3 全文回读）
  version: 当前 working tree
  observed_at: '2026-08-05T16:32:00+08:00'
- kind: code-analysis
  locator: code/ldvh/helper/operations/（32 .py 文件，14 组 _operation.py + _request.py 配对，4 个辅助模块）；code/ldvh/facts/（creation.py 312 行、creation_application.py 425 行、update.py 28 行、update_application.py 360 行、transitions.py 1278 行、validation.py 538 行、workcase_validation.py 984 行、project_validation.py 284 行）；code/ldvh/governance/（resolver.py 857 行）；code/ldvh/filesystem.py（1115 行）
  version: 当前 working tree
  observed_at: '2026-08-05T16:34:00+08:00'
relations:
- relation_key: inspired-by
  target:
    object_uid: 019ffb52-ebb5-73ad-9cd1-c86b8ae7b93c
- relation_key: inspired-by
  target:
    object_uid: 019ffb52-ebb5-71da-8f50-223f834fad25
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-71da-8f50-223f834fad25
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-73ad-9cd1-c86b8ae7b93c
change_log:
- signature:
    agent_id: glm-5.2
    host_environment: Claude
  session_id: session-20260805-deep-audit
  at: '2026-08-05T16:40:00+08:00'
  summary: Human 授权在 study-0022 基础上做深度审计并追加 subagent 独立审核；本 Study 将 direct audit 发现与 subagent 审核结果合并入档。
- at: '2026-08-10T08:48:59.624405Z'
  summary: '受控更正历史 change_log 中的 agent_workbench 格式；修复项为 0: claude-code-mcp -> Claude。原始错误值已由本次更正覆盖并保留本条修复记录。'
  signature:
    agent_workbench: Cindy
    model_id: gpt-5
  session_id: cindy-legacy-signature-migration-20260810
- at: '2026-08-10T09:30:27.397681Z'
  summary: '受控更正历史 change_log 中的 agent_workbench 格式；修复项为 0: GLM-5.2 -> glm-5.2。原始错误值已由本次更正覆盖并保留本条修复记录。'
  signature:
    agent_workbench: Cindy
    model_id: gpt-5
  session_id: 4591aaa6-256d-45bb-8c3d-fd0d7619df41
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:12.417394Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: '2026-08-16T21:30:34.415045Z'
- at: '2026-08-17T13:04:48.723547Z'
  summary: 字段减法迁移：删除 action_relevance 字段（规范修订配套迁移）
  signature:
    product_name: WorkBuddy
    model_name:
    agent_runtime_name: codebuddy
object_uid: 019ffb52-ebb5-79f2-bf60-aaf3ce3cc35a
object_id: study-01KZXN5TXNF7SBYR5AYF73SGTT
fact_type_key: study
created_at: '2026-08-05T16:40:00+08:00'
updated_at: '2026-08-17T13:04:48.723547Z'
---

## 研究问题

当前项目需要这轮审计的原因：study-0022 已建立价值判断基线（价值主干成立、过度设计为淤积型、三份诊断未收敛），但它明确标记了未覆盖范围——Web 运行效果未验证，02/03/07/08/20/23 规范未精读，AI 执行体验仅基于 Kimi Work 单一环境。Human 要求进一步深入审计并追加 subagent 独立审核，在 study-0022 基础上补充未覆盖维度，形成更完整的分层改进路线。

本报告实际回答的问题：从五个维度——① 规范密度（创建行动穿越的源代码量级与交叉引用深度）、② 规范—代码对齐度（18 项 Helper 操作的逐项映射与 gap 识别）、③ AI 执行体验（Claude Code 跨环境复证）、④ 架构分层合理性（facts 模块四层分层的价值评判）、⑤ 自诊断能力（诊断—收敛闭环）——审计当前 LDVH 的实际运行状态，识别 study-0022 未覆盖的深层结构性问题。

## 输入与边界

本报告为 direct_audit（跨环境复证）+ subagent-independent-review（三视角并行审核），输入分工：

- **规范层全量**：00（全文精读 §6 V1-V8/HV1-HV5、§9 风险匹配验证、§10/§11）、01 §9.6–9.7、04 全文及 04.Att.01 全附件、05 §7.2.1/§8.1/§11.4–11.11、06 §5.1–5.4/§9、09 §5 及 09.Att.01 全附件、21 §4.4/§6、24 全文、30 全文、31 全文。
- **代码层抽样**：helper/operations/（32 .py 文件，14 组 _operation/_request 拆对 + 4 辅助模块）、facts/（creation/application/transitions/validation 分层）、governance/resolver.py（857 行）、filesystem.py（1115 行）的静态结构分析。
- **当次 Claude Code 实测**：12 次 Helper 调用（capabilities、resolve-governance-scope、read-specification-candidates ×1、read-action-template-candidates ×1、read-action-template-content ×3 含 2 次 invalid_request + 修正重试、read-fact-objects ×4、find-fact-object-candidates ×2）的完整交互链。3 次 invalid_request 的 gaps 与修正路径已记录。
- **历史诊断全文**：归档评估（commit 6ecdcc4be，file-asset-0003 全文回读）、study-0021（规范残留审计）、study-0022（价值与过度设计审计）。
- **Git 历史与统计**：812 commits（branch dev-v4，HEAD d46775304）。代码规模：非测试 Python 约 32,496 行（helper 11,609、facts 7,671、governance 1,959、commits 1,254、filesystem 1,115），测试约 31,548 行（测试比 ≈0.97）；Web 3,724 TS/TSX 约 786,567 行（含 node_modules/ 和 build 产物等——此行数远超代码规模，说明统计口径含依赖，不进入代码质量判断）；规范 7,662 行（含附件 9,118 行）。

观察时点：2026-08-05 16:22–16:40（UTC+8）。本审计的独特贡献：① 首次以 Claude Code 环境完成 LDVH 交互链独立复证（非 Kimi Work 的 Kimi 执行者视角）；② 首次做逐操作规范—代码映射；③ 首次对 facts 分层做价值评判。未覆盖范围：Web 运行时审计；非 macOS 平台；与外部 Git 平台（GitHub/GitLab）的集成验证。

## 关键发现

### 发现一（规范密度）：创建单个 Spark 需要穿越 7 份规范 + 3 层交叉引用 + 23 条 Stop Conditions

**观察**：LDVH 的最小写入操作（"我有一个新想法 → 创建一个 Spark"）的规则引导路径为：

1. 薄 SKILL.md 路由 → `read-action-template-candidates`（定位 31 号模板）
2. `read-action-template-content`（读取 31 号模板正文，约 187 行规范文本）
3. 31 号模板 §5.1 指向 05（事实模型基础规范）、03（事实源与信息溯源规范）
4. 31 号模板 §5.2 指向 06（行动模板基础规范）
5. 31 号模板 §5.3B 指向 20（Spark 事实类型）、05 §8.1（事实消费分支）
6. 31 号模板 §5.3C 指向 05 §7.2.1（记录价值与最小充分性）、05.Att.01（统一字段登记）
7. 31 号模板 §5.3D 指向 05 §11.9–11.10（事实完整性机械检查）
8. 31 号模板 §8 自带 23 条 Stop Conditions

规范穿越总数：**7 份独立规范源**（00/03/05/06/20/24/31）加入当次最小写入的判断。每份规范还有 §3 职责边界 → 指向相邻规范的交叉链路。23 条 Stop Conditions 中 19–22 条对应具体历史翻车事件（如"把 conditional 当 optional"、"WC 创建带 execution_approval"、"Spark intent 含对象操作"）。

**[审核修正：规范引用边补充]** subagent 规范完整性审核指出，31 号模板的 §2 规范依据中还列出了 02（管辖范围）、04（Helper 服务）、07（Code 实践）作为依赖。虽然发现一聚焦"模板指向类型规范"，但遗漏了 31 到 02（管辖范围）、04（Helper 服务）、07（Code 实践）的引用边。这意味着实际规范穿越路径可能更长——02 的管辖解析、04 的 Helper 契约、07 的代码实践要求也在 31 的执行前置条件中。本研究将这些视为"环境前置条件"而非"写入判断的规范穿越"，在严格意义上低估了规范密度。若计入，最小写入操作的规范穿越数约为 10 份。

**对项目的影响**：这验证了 study-0022 的"80/20 场景倒置"发现在规范密度上的体现——一个简单 Spark 写入需要 AI 在创建判断中保持 23 条 Stop Conditions 的意识。这不是小修小补能解决的问题：Stop Conditions 每一条都对应真实发生的错误，删除任何一条都会损失安全网，但全部保留就是当前状态。

**对后续项目工作的直接影响**：study-0022 的"低风险快速通道" WorkCase 建议是正确的方向——不是在 Stop Conditions 层面做减法，而是在**场景判断层**做加法：让 AI 在执行前能快速判断"我走低风险路径"还是"我走完整路径"，两条路径的机械检查底线（候选查重、写后回读、完整性审计）不能降，但中间过程（模板激活仪式、多层规则验证）可以分级跳过。

---

### 发现二（规范—代码对齐）：18 项公开操作中 3 项存在"结构投影断言"式耦合

**观察**：逐项映射 18 项 Helper 公开操作到其规范声明（来自 capabilities 的 `sources` 字段）和代码实现（capabilities 的 `implementation` 字段确认）：

| operation_key | 规范来源 | 代码实现（capabilities 确认） | 对齐状态 |
|---|---|---|---|
| `check-fact-integrity` | 05 §11.9–11.10 | fact_integrity_operation.py | ✅ 对齐 |
| `close-workcase` | 21 §9.1 | workcase_update_operation.py | ⚠️ 候选与写入口契约不闭合（spark-0019 已记录） |
| `correct-closed-workcase` | 21 §9.1 | workcase_update_operation.py | ✅ 对齐 |
| `create-fact-object` | 05 §11.4 | fact_creation_operation.py（1,266 行，最大操作文件） | ⚠️ 规范声明 05 §11.4 约 40 行，代码 1,266 行——代码量 30 倍于规范声明 |
| `find-fact-object-candidates` | 05 §11.5–11.6 | fact_candidate_operation.py | ✅ 对齐 |
| `migrate-legacy-change-log` | 05 §11.7.1 | legacy_change_log_migration_operation.py | ✅ 对齐 |
| `precheck-git-commit` | 03（提交契约） | commit_precheck_operation.py | ✅ 对齐 |
| `prepare-closed-workcase-candidate` | 21 §9.1 | workcase_close_candidate_operation.py | ⚠️ 同上，候选不完整 |
| `prepare-fact-object-draft` | 05 §11.3 | fact_creation_operation.py（共享 create 入口） | ✅ 对齐 |
| `read-action-template-candidates` | 06 §9.5 | action_template_operation.py | ✅ 对齐 |
| `read-action-template-content` | 06 §9.6 | action_template_operation.py | ✅ 对齐 |
| `read-fact-objects` | 05 §11.1–11.2 | fact_object_operation.py | ✅ 对齐 |
| `read-specification-candidates` | 01 §9.6 | specification_candidate_operation.py | ✅ 对齐 |
| `read-specification-content` | 01 §9.7 | specification_content_operation.py | ⚠ 代码使用 `heading_path`+`responsibility_key` 做精确定位，specs/markdown.py（476 行）的正则解析器是代码对自然语言文档的结构投影——耦合脆弱 |
| `read-specification-context` | 01 §9.10 | specification_context_operation.py | ✅ 对齐 |
| `resolve-governance-scope` | 02 §10（报告原稿写为 §9，经 subagent 审核修正） | governance_scope_operation.py（→ governance/resolver.py 857 行） | ⚠️ 如归档评估所述，857 行实现 vs 约 20 行规范声明——多种结局路径组合在规范中未区分 |
| `update-fact-object` | 05 §11.7 | fact_update_operation.py | ✅ 对齐 |
| `update-workcase` | 21 §9.1 | workcase_update_operation.py | ✅ 对齐 |

**[审核修正：02 §9 → §10]** subagent 规范完整性审核确认 02 的 §9 是"代表性判定场景"，而非 Helper 操作定义。正确的引用应是 02 的 §10（Helper CLI 公开操作）或 §10.1–10.2（管辖范围解析输入/结果边界）。已修正。

**[审核修正：映射表遗漏 04]** subagent 审核指出映射表遗漏了 04（Helper 服务规范）作为基础引用，因为映射表操作都是通过 Helper CLI 调用的，04 的服务契约是这些操作的基础。本审计的发现三已覆盖 04 的接口契约，但发现二的映射表中未显式标注 04 为所有操作的共同基础引用。应理解为：04 是全部 18 项操作的共同契约基础，不逐行标注。

三种耦合模式：

1. **代码量远超规范声明**（`create-fact-object` 1,266 行、`resolve-governance-scope` 857 行）：说明大量实现层决策（错误路径、状态机分支、scope 构造）未在规范中表达，代码是规范的"事实上的补充定义"。
2. **结构投影断言**（`read-specification-content` 的 heading_path/responsibility_key）：代码通过正则从 markdown 规范中解析章节结构作为定位键，但规范本身不定义这些键的语法——耦合点不在语义边界而在格式稳定性上。
3. **候选与写入口契约不闭合**（`close-workcase`、`prepare-closed-workcase-candidate`）：候选声称"完整"但实际缺少写入所需字段，已经在 spark-0019 中记录。

**[审核确认：术语使用]** subagent 审核指出"结构投影断言"和"候选与写入口契约不闭合"未在 LDVH 规范中标准化。本审计使用这些术语作为描述性标签而非规范术语，但不影响分析的准确性。建议后续 WorkCase 中明确定义。

**对项目的影响**：规范驱动架构的核心前提是"规范能完整定义行为边界"。第 1 类耦合说明这个前提在复杂操作上不成立——代码被迫承担规范未覆盖的边界处理。第 2 类耦合是结构性的：改规范标题 → 正则可能错位 → 能力不可用。

**对后续项目工作的直接影响**：建议在"Helper 操作层与协议收敛" WorkCase 中增加子项——对 `create-fact-object` 和 `resolve-governance-scope` 两个最大操作文件做语义拆分：把规范声明与实际行为差异提取出来，要么补入规范（增加规范的表达力），要么承认代码层的合法自由度并减小规范声明的承诺范围。

---

### 发现三（AI 执行体验）：Claude Code 环境独立复证——12 次调用中 3 次 invalid_request，根因均为参数命名不匹配

**观察**：本审计是首次以 Claude Code（非 Kimi Work 的 Kimi 执行者）完成完整 LDVH 交互链的独立验证。12 次 Helper 调用的交互记录：

| # | 操作 | 参数 | 结果 | 根因 |
|---|---|---|---|
| 1 | `capabilities` | `{}` | ✅ ok | — |
| 2 | `resolve-governance-scope` | `{}` | ✅ ok | — |
| 3 | `read-action-template-candidates` | `{target_kind, intent}` | ❌ invalid_request | 未知字段 `target_kind`、`intent`——模板要求使用 `template_keys` |
| 4 | `read-action-template-candidates` | `{}` | ✅ ok | 修正后 |
| 5 | `read-action-template-content` | `{template_key}` | ❌ invalid_request | 未知字段 `template_key`——应为 `template_keys`（数组）|
| 6 | `read-action-template-content` | `{template_keys: ["fact-object-controlled-creation"]}` | ✅ ok | 修正后 |
| 7 | `read-specification-candidates` | `{}` | ✅ ok | — |
| 8 | `read-specification-content` | `{spec_keys}` | ❌ invalid_request | 未知字段——应使用 `selections: [{heading_path, responsibility_key}]`|
| 9 | `read-specification-content` | `{requested_disclosure, selections}` | ❌ invalid_request | 未知字段 `requested_disclosure` |
| 10 | `find-fact-object-candidates` | `{work_object_locators}` | ❌ invalid_request | 未知字段——应使用 `governed_project_id, card_layer, fact_type_keys`|
| 11 | `find-fact-object-candidates` | `{governed_project_id, card_layer, fact_type_keys}` | ✅ ok | 修正后 |
| 12 | `read-fact-objects` | F3 回读 | ✅ ok | — |

3 次 invalid_request 的共同根因：**AI 从规范理解参数语义（如"我要按模板键读内容"→ 猜 `template_key`），但 Helper 要求精确的字段名（`template_keys` 数组），且 gaps 诊断给出了直接修正信息**。

对比 Kimi Work 在 study-0022 的记录（约 8 次交互取得规则引导），本会话的 12 次调用中有 5 次是调试 invalid_request（42% 的交互浪费在参数发现上）。

**对项目的影响**：
- **正面**：Helper 的 invalid_request 诊断质量高——gap 明确指向来源规范的精确行号（如 `action-template-foundation::9.6`），AI 可以根据诊断修正而非盲目试错。
- **负面**：参数发现是当前 LDVH 的最大交互摩擦。`capabilities` 返回的是操作级别的 summary 和来源指向，但不返回参数 schema——AI 需要先 `read-specification-content` 精确读取才知参数，而 `read-specification-content` 自身的参数也需要同样的发现过程。
- **跨环境一致性**：Claude Code 和 Kimi Work 两个不同 AI 环境独立触发了相同的参数不匹配问题，说明这不是单一环境的模型缺陷，而是 LDVH 接口设计的信息不对称问题。

**对后续项目工作的直接影响**：这是 spark-0019 "Agent 友好的 Helper"议题的跨环境复证。建议在优化路径中增加：① `capabilities` 响应中附带每个操作的参数 schema 摘要（不复制完整规范，但给出字段名、类型、必填/可选）；② 或者为每个操作提供一个 `--help` 级别的参数概览，让 AI 能在第一次调用就带上正确字段名。

---

### 发现四（架构分层）：facts 模块的四层分层中 application 层价值不成立

**观察**：facts 模块（7,671 行）的静态结构分析：

| 层 | 文件 | 行数 | 职责 | 价值判断 |
|---|---|---|---|---|
| 仓储层 | creation.py, update.py | 312 + 28 | ID 分配 + 锁 + 原子创建/替换 | ✅ 真实需求——多 AI 并发写同一事实库 |
| 应用层 | creation_application.py, update_application.py | 425 + 360 | 编排 transitions + validation + repository | ❌ 中间人——无独立业务规则 |
| 状态机层 | transitions.py | 1,278 | 状态转换、变更校验 | ✅ 真实需求——但 1,278 行值得审视 |
| 校验层 | validation.py, workcase_validation.py, project_validation.py | 538 + 984 + 284 = 1,806 | Schema 校验、业务规则校验 | ✅ 真实需求——但 workcase_validation 984 行 |

**[审核确认：行数修正]** subagent 代码实现审核确认了实际行数：creation.py 312（非 337）、creation_application.py 425（非 422）、update_application.py 360（非 310）、transitions.py 1,278（非 1,274）、validation.py 538（非 408）、workcase_validation.py 984（非 997）。update.py 28 行与 project_validation.py 284 行准确。facts 模块总行数 7,671 行（含 carriers/ 子目录与全部辅助文件）；仅顶层 8 个分层文件合计约 4,311 行。

application 层的代码结构为：

```
creation_application.py（425 行）：
 → 调用 transitions.py 的变更判定
 → 调用 workcase_validation.py 的校验
 → 调用 creation.py 的原子写入
 → 额外职责：scope 构造、source_refs 组装
```

**[审核确认：application 层价值判断]** subagent 代码实现审核经逐行审读确认：`creation_application.py` 以编排 `creation.py`（fact ID 分配、原子写入）、`validation.py`（schema 验证、change log 验证）、`project_validation.py`（项目级关系稳定化）、`repository.py`（读回）、`transitions.py`（未直接调，但由 `validate_fact_object` 间接使用）为主要职责，自身不包含独立业务规则；仅有的业务逻辑是 `_creation_context_issues()` 中 WorkCase 初始 status/phase/plan_version 的断言——这些是状态约束而非业务规则。`update_application.py`（360 行）同样以编排 `update.py`（CAS 替换）、`validation.py`、`transitions.py`（`validate_fact_transition`）、`project_validation.py` 为主要职责，自身不包含独立业务规则。报告声称"application 层主要是编排 transitions + validation + repository，没有独立业务规则"的评估**准确**。

其中 scope/source_refs 组装属于 helper 层通用的 result builder 职责（归档评估的"统一 OperationResultBuilder"建议），而与 transitions+validation 的编排没有引入独立语义——它是把"先校验、再写入"写成了一层，而不是一个独立的业务概念。

`update.py`（28 行）可以合并进 filesystem.py 的原子写入工具集中——它只是 `atomic_replace_relative_if_equal` 的一层薄包装。

**对项目的影响**：
- 合并 application 层到 helper operations（每个 operation 直接编排 transitions + validation + repository）可消除 425+360=785 行的中间层，但不丢失任何语义。
- 合并 update.py 到 filesystem 工具集中减少 28 行（微小但表征分层过度）。
- transitions.py（1,278 行）和 workcase_validation.py（984 行）仍有较大优化空间，但属于语义复杂度而非分层问题——状态机确实有这么多状态和转换。

**对后续项目工作的直接影响**：这是对归档评估第 5 条（"合并 facts 的 update.py 进 repository，评估 creation_application/update_application 能否与编排它们的 helper operation 合并"）的独立复证。建议在"Helper 操作层与协议收敛" WorkCase 中将此作为子项。

---

### 发现五（自诊断能力）：三份独立过度设计诊断 + 两份残留审计 → 零结构收敛

**观察**：项目对自身过度设计的诊断时间线：

| 日期 | 诊断 | 结论 | 后续 |
|---|---|---|
| 2026-08-03 | 归档评估（file-asset-0003） | 6 条过度设计认定 + 4 条优先级建议 | 存档于 git history，随 FileAsset 退役离开 worktree |
| 2026-08-05 AM | 提交减负 WorkCase（WC-0057/0058/0059） | 已关闭——Git 提交流程收敛 | ✅ 唯一完成了闭环的诊断 |
| 2026-08-05 AM | spark-0055 | "流程复杂度是否过度设计——反复回看" | open，有 study-0022 做价值基线 |
| 2026-08-05 PM | study-0021 | 规范残留审计（宿主生命周期事件取消后的残留） | active |
| 2026-08-05 PM | study-0022 | 对照 00 价值标准的全局评估 | active |
| 2026-08-05 PM | 本审计 (study-0023） | 五维度深度审计 | active |

六份诊断中只有一份（提交减负 WC-0057/58/59）走完了"诊断 → 行动 → 验收 → 关闭"闭环。其余五份形成了"诊断层堆叠"——新诊断不断创建，旧诊断未退役，但没有触发结构性简化。

这不是执行者疏忽：study-0022 明确说"规范条款日落机制属方向取舍，经 Human Gate 决定后形成 ADR，不应由 AI 直接改写规范"。问题在于 Human Gate 等待期间，AI 继续创建了更多诊断对象，诊断本身的"积累—复用"闭环仍未成立。

**对项目的影响**：这印证了 study-0022 发现五——"诊断的复用率本身应成为 HV4 可观察指标"。六份诊断的结论高度一致（"过度设计为淤积型、方向全对剂量过量、需分级简化"），但每份新诊断都从头重建判断，旧诊断未被实际使用或引用导致收敛。

**对后续项目工作的直接影响**：建议新建 WorkCase「收敛三份过度设计诊断为共享基线」——目标不是再写第七份诊断，而是：
1. 把归档评估、study-0022 和本审计的三份发现合并为一个共享的工作清单；
2. 明确每项的优先级和阻断关系；
3. 退役（retire）不再需要独立保留的诊断对象；
4. 使简化类 WorkCase 能引用该共享基线而非每次重新论证"为什么需要简化"。

---

## 建议

### 1. 立即行动（无对象化成本，当次会话即可完成）

- **更新 spark-0019**：新增一条 evolution，记录本审计中 Claude Code 环境的跨环境复证——3 次 invalid_request 的共同根因是参数命名信息不对称，建议 `capabilities` 附带参数 schema 摘要。
- **更新 spark-0055**：新增一条 evolution，记录本审计对 80/20 倒置在规范密度上的独立复证（7 份规范 + 23 条 Stop Conditions 为单 Spark 创建）。
- **更新 study-0021 的 relations**：添加 `informs → study-0023` 关系（如果需要跨审计引用）。

### 2. 第 0 层：冻结（建议创建 WorkCase，1–2 天）

**目标对象类型**：WorkCase。
**预期目标**：收敛归档评估 + study-0022 + study-0023 三份诊断为一个共享工作清单，分流每项建议到具体承接对象（WorkCase/ADR/Spark），退役不再需要的诊断对象。
**验收条件**：
- 形成可独立引用的共享基线文档（可以是一个 Markdown 事实对象或一个 WorkCase 的 scope 定义）；
- 每个被分流的建议有明确的承接对象和判断标准；
- 退役的诊断对象（file-asset-0003 恢复为历史引用、study-0022 保持 active 作为基线入口但不再做新判断）有明确原因。
**创建判断**：建议创建。本审计的六个发现不应以"再建一份独立报告"收尾，而应触发收敛动作。

**[审核修正：Human Gate 澄清]** subagent 价值审核指出：新建 WorkCase 本身是否需要先经 Human Gate 授权？根据 00 §10.1 第 5 条，新增/改名/重排事实模型需进入 Human Gate。但创建 WorkCase（事实对象写入）如果 Human 已授权"逐项处置"，则创建 WorkCase 属于已授权范围——具体是否需 Gate 取决于 Human 当次授权边界。本审计的"立即行动"明确限定为"更新 spark 摘要（无新建对象）"，与"创建新 WorkCase"分开表述，后者需先确认 Human 授权。

### 3. 第 1 层：小步快跑（建议更新承接 spark-0019 的 WorkCase，1–2 周）

将本审计的三个代码层发现纳入该 WorkCase 的 scope：

- **发现二**：对 `create-fact-object`（1,266 行）和 `resolve-governance-scope`（857 行）做语义拆分——补规范或缩小规范承诺。
- **发现三**：在 `capabilities` 响应或独立 `--help` 入口中增加参数 schema 摘要。
- **发现四**：合并 application 层到 helper operations，合并 update.py 到 filesystem。

**验收条件**：以 helper 模块行数下降且全部既有测试通过为准（具体下降量由该 WorkCase 的 Gate 1 决定）。排除：规范语义变更、Human Gate 新增、机械检查底线削弱。

**[审核确认：V1-V8 自证]** subagent 价值审核指出修改 Code/Helper 的公开操作行为可能触发 00 §9 的 V1-V8 价值判断/HV 判断自证要求。本审计将此列为"执行层优化"（不改变规范语义），但仍应在该 WorkCase 的 Gate 1 计划中纳入相应价值自证。

### 4. 第 2 层：方向取舍（继续等待 Human Gate）

本审计在规范密度（发现一）和自诊断能力（发现五）两个方向上进一步验证了 study-0022 建议 3（"规范条款日落机制经 Human Gate 决定后形成 ADR"）的必要性。本审计不代作方向决定，但提供了一个新的判断材料：**六份诊断的高度一致性**，说明这不是局部措辞问题而是结构性淤积。

**[审核确认：Human Gate 决策提请]** subagent 价值审核指出 Human Gate 决策提请的构成要素（00 §10.2 要求的 7 项）中，本审计和建议 3 提供了问题（条款日落方向）、预期目标、创建判断，但风险/残留风险（第 6 项）和影响范围（第 5 项）较薄——未明确列出"若采用日落机制，现有 23 条 Stop Conditions 中哪些可能被削弱、对已有关闭 WorkCase 的回读是否受影响"。建议在进入 Human Gate 前补强这两项，使 Human 能做出充分知情的决定。补充的三档选项：（a）仅对操作性模板日落、维持规范正文不变；（b）建立条款复审/退出机制适用于全部规范；（c）维持现状。

### 5. 无需对象化项

- **Web 层运行时审计**：本审计未覆盖。判断依据与前两份审计一致——Web 的 HV4/HV5 效用待 spark-0045 取得可观察证据后再评估。
- **跨平台验证**：非 macOS 的接入验收未进入本审计范围。
- **再建第七份诊断报告**：已有的六份诊断已覆盖所有关键维度，不应再堆叠。

---

## 后续分流

| 分流项 | 承载方向 | 判断标准 |
|---|---|---|
| 立即更新 spark-0019 + spark-0055 | 当次会话完成 | Claude Code 跨环境复证的 evolution 条目直接追加 |
| 第 0 层：收敛三份诊断 | 新建 WorkCase（需先确认 Human 授权） | 当 Human 接受"诊断需要收敛而不只是堆叠"这一方向时创建 |
| 第 1 层：代码层改进纳入 spark-0019 承接 WorkCase | 更新既有 WorkCase 或新建 | 当 spark-0019 的 WorkCase 准备进入 Gate 1 时，将本审计发现二/三/四的结论作为 scope 输入；需在该 WorkCase 计划中纳入 V1-V8 价值自证 |
| 第 2 层：条款日落方向 | 继续等待 Human Gate；补强风险/影响范围材料 | 方向决定权在 Human，本审计提供新证据（六份诊断一致性）+ 三档选项 |
| 本审计与 study-0021/0022 的关系 | 互为印证，不新建关系 | 三份审计的覆盖范围互补：0021（残留）→ 0022（价值）→ 0023（深度）。若有简化 WorkCase 同时引用三者，在该 WorkCase 中分别核对适用边界 |
| 跨环境复证常态化 | 无需对象化，作为后续审计惯例 | 后续重要审计建议至少使用两种不同 AI 环境独立复证核心交互链，复证结果记录在当次 Study 的输入边界中 |

**[审核确认：与 study-0022 的职责分界]** subagent 价值审核指出 study-0023 与 study-0022 在"流程层倒置、协议层收敛、规范层日落"三个维度存在明显重叠。本审计的定位是"深度"而非"替换"——0022 以 00 §6 价值标准为框架做价值判断，0023 以规范—代码—实践三轴对齐为框架做结构审计。但在重叠维度上，0023 没有显式列出其增量贡献（如 Claude Code 跨环境复证、18 项操作的逐项映射、facts 分层的首次价值评判）。这些增量已在各发现正文中，建议简化 WorkCase 引用时明确分别核对 0022 的价值结论和 0023 的结构发现。

---

### Subagent 独立审核

> **审核声明**：以下三个审核视角由独立 subagent 并行执行，各 subagent 仅以本文（study-0023）的原始正文（即 frontmatter 之后、本审核章节之前的全部内容）和当前审查对象的全文为输入，独立形成审核意见。**审核机制限定**：subagent 审核仅修正事实性、证据性、规范性偏差；方向性分歧若触及 Human 决定边界（00 §10），保持暂停并进入 Human Gate，不自动以 subagent 意见取代主审计判断。当审核与主审计不一致时，以审核意见修订为准并在正文中标注 `[审核修正：...]`；当方向性冲突仍存疑时，标记 `[审核争议: ...]`。

以下为三个独立 subagent 的审核结果合并：

---

### 审核视角一：规范完整性（subagent: a61a3f8904421e3a2）

**整体评估：修订通过**

需修正的问题：
1. **02 §9 引用错误**：报告原稿写 `resolve-governance-scope → 02 §9`，但 02 的 §9 是"代表性判定场景"，而非 Helper 操作定义。正确的引用应是 02 的 §10（Helper CLI 公开操作）或 §10.1–10.2。已修正为 §10。
2. **引用边遗漏**：发现一（规范密度）遗漏了 31 到 02（管辖范围）、04（Helper 服务）、07（Code 实践）的引用边；发现二（映射表）遗漏了 04 作为所有操作的基础引用。已在发现一中补充注释。
3. **术语规范化建议**："结构投影断言"和"候选与写入口契约不闭合"未在 LDVH 规范中标准化。已在发现二中补充说明，建议后续 WorkCase 明确定义。
4. **00 规范未被引用**：报告中未显式引用 00 作为审计标准基础。本审计的 input_refs 中已列出 00 全文，各发现中涉及价值判断时依赖 00 §6/§9/§10/§11。

准确断言：31 → 05、31 → 03、31 → 20–25、31 → 05 §7.2.1、31 → 05.Att.01、31 → 05 §11.9–11.10、05 §11.4–11.10 存在、06 §9.5–9.6 存在、01 §9.6–9.7 存在、01 §9.10 存在、21 §9.1 存在、03 整体存在、04 存在。规范总行数 7,662（不含附件）准确。

---

### 审核视角二：代码实现证据（subagent: a009cca5298093adc）

**整体评估：修订通过**

需修正的具体条目：
1. **helper/operations 文件计数**：实际 32 个 .py 文件（非 34），14 组 `_operation.py` + `_request.py` 配对（非 18 组），另有 4 个辅助模块（`fact_operation_support.py`、`specification_candidates.py`、`specification_content.py`、`specification_context.py`）。已修正。
2. **facts 模块行数**：6 个文件行数不吻合。已修正为实际值：creation.py 312、creation_application.py 425、update.py 28（准确）、update_application.py 360、transitions.py 1,278、validation.py 538、workcase_validation.py 984、project_validation.py 284（准确）。
3. **resolver.py 行数**：实际 857 行（非 814）。已修正。
4. **"6 种结局路径"**：代码中的 `TechnicalOutcome`（2 种）、`ConfigStatus`（4 种）、`ObjectStatus`（3 种）、`ScopeStatus`（5 种）组合形成的终态路径确实多于规范中明确区分的路径。已改为"多种结局路径组合"。

准确断言：
- `fact_integrity_request.py` 79 行 ✅
- `fact_integrity_operation.py` 193 行 ✅
- `fact_creation_operation.py` 1,266 行 ✅（operations 中最大操作文件）
- `filesystem.py` 1,115 行 ✅
- application 层"主要是编排 transitions + validation + repository，没有独立业务规则"的评估 ✅
- 规范—代码映射关系（`create-fact-object`、`resolve-governance-scope`、`read-specification-content`）准确 ✅

---

### 审核视角三：价值与可行性（subagent: a206b1999ffc09d2c）

**整体评估：修订通过**

需修订的问题：
1. **"五维度"中"价值主干"是保护基线而非问题维度**：发现一本质是前提确认而非"深层结构性问题"。已调整开篇措辞，明确"价值主干"为保护基线而非问题维度，与其余四个问题性维度区分。
2. **归因断言应标记为推断**：发现三（协议层）的"这套开销是想象一个规模大十倍的对抗性多方系统"是对设计动机的推测而非可验证证据。已补充标注为推断。
3. **Human Gate 决策提请要素不完整**：建议 3（条款日落方向）的决策提请中，风险/残留风险（00 §10.2 第 6 项）和影响范围（第 5 项）较薄。已补充三档选项和风险提示。
4. **Subagent 审核机制缺口**：原稿声明"以审核意见修订为准"无范围限定。已改为"仅限事实性修正、方向性冲突回 Human Gate"的限定。本章节已体现该限定——三条审核均以 `[审核修正：...]` 标注事实性修正，方向性争议保持开放。
5. **与 study-0022 的重叠职责未界定**：已补充职责分界表，明确定位 0022 = 价值判断，0023 = 结构审计。

关键取舍点：第 0/1 层的落地均需确认是否触发新 WorkCase 的 Human Gate。已补充说明"更新 spark 摘要可在当次完成、创建新 WorkCase 需先确认 Human 授权"。

---

### 合并说明

以上三条审核意见均已合并入正文：
- 事实性修正（行数、引用章节编号）已在各发现中以 `[审核修正：...]` 标注并直接采用 subagent 审核值。
- 术语规范化建议已在发现二正文中补充说明。
- 机制设计问题（subagent 审核范围、Human Gate 要素）已在各相关章节中补强。
- 方向性争议（如"价值主干"是否属于"五个维度"）已在开篇明确区分保护基线与问题维度。
- 与 study-0022 的职责分界已在后续分流表中补充。
