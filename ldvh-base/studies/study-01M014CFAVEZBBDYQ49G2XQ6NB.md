---
title: 从 DeepSeek Harness 会话日志观察 LDVH Helper 调用模式与优化方向（65 会话结构化统计）
status: active
report_kind: internal_audit
research_question: 对 DeepSeek Harness 真实会话日志（docs/logs 下 65 个会话、103911 条事件）做结构化统计，能观察到哪些 LDVH Helper 调用模式、性能特征与易错点，以及它们指向哪些有证据支撑的优化方向？
abstract: 对 DeepSeek Harness 65 个真实会话日志（docs/logs，Zstandard 解压 JSONL，103911 条事件、250 轮、3265 次工具调用）做结构化统计：总输入 20.30M tok vs 输出 1.80M tok（约 11.3:1），覆盖 10 种模型；bash 工具共 1964 次，其中直接调用 LDVH Helper 757 次（38.5%），python heredoc 拼接 155 次（含 PYEOF 定界 18）；Helper 操作集中在 read-fact-objects(224)、read-specification-content(99)、update-workcase(83)、find-fact-object-candidates(63)、read-action-template-content(60)；6 个会话出现 KeyError，64 个会话出现重复/两份信号；52 会话 cacheReadTokens 合计 474.8M（此前误报缓存字段缺失已更正）。结论：Helper 调用封装、规范契约回查、create 结果提示三类优化方向在 65 会话样本中得到量化佐证；统计口径来自宿主（DSH）而非 LDVH 自身，优化立项仍需 LDVH 自身可测量口径。
research_intent: 保存 65 个真实会话日志的结构化统计结果与 Helper 调用模式证据，为 LDVH 的 Helper 交互、规范检索与上下文占用优化提供跨会话、跨模型的量化证据起点，避免优化仅凭单点观察。
recommendation_summary: 基于 65 会话统计收敛为分层优化方案：Phase 1 CLI 机械扩展——P1-1 请求文件化（--request，针对 155 次 python heredoc 拼接，验收新会话降为 0）、P1-2 请求骨架现取（--example/input_examples，针对 capabilities 48 次契约发现与盲试重试）、P1-3 结果投影（--fields，针对 KeyError 6 会话）；Phase 2 领域契约扩展——P2-1 CAS prepare-update 一体化（read-fact-objects 224 与 update-workcase 83 配对，往返 3-4 次降为 2）、P2-2 写入成功信号显式化（KeyError 6 会话/重复信号 64 会话）；Phase 3 MCP 化列为治理议题（须先经 09 规范修订 Human Gate 判定是否构成新接入层）。可测量口径（per-op 往返、命令 token、invalid_request 率）为 Phase 1/2 验证前置，经 session_comparability/replay 对照后立项。
input_refs:
- kind: working_tree
  locator: DeepSeek Harness 会话日志解压目录 docs/logs/（65 个 session.jsonl，来自 ~/.dsh/sessions/--Users-dmh2002-poker_hud_projects-ld-vibe-harness-v4--/），经 Python 脚本做结构化统计
  observed_at: '2026-08-15T00:00:00Z'
- kind: working_tree
  locator: docs/logs/analyze_sessions.py 与 docs/logs/analyze_calls.py（统计脚本，含正确解析 tool/call arguments JSON 字符串的口径）
  observed_at: '2026-08-15T00:00:00Z'
- kind: rule
  locator: specs/21-WorkCase-工作项.md
  version: 7b235c7f2fd6f3aca038f7e08d0eaa8f775e4b4f
  observed_at: '2026-08-15T00:00:00Z'
relations:
- relation_key: inspired-by
  target:
    object_uid: 01a0004d-dc0c-71cd-806f-b5acb36d7057
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-75f4-888d-2d7c6df0e8e2
action_relevance: 分析或优化 Helper 调用模式时，基于会话日志的结构化统计识别高频调用、异常路径和优化方向
change_log:
- signature:
    product_name: TraeCode
    model_name: deepseek-v4-flash
    agent_runtime_name:
  at: '2026-08-14T21:55:51.666073Z'
  summary: 受控创建 internal_audit：从 DeepSeek Harness 轨迹视图观察 LDVH Helper 调用模式、性能特征与易错点，形成优化方向证据起点。
- signature:
    product_name: TraeCode
    model_name: deepseek-v4-flash
    agent_runtime_name:
  summary: content_update：将证据基础从两个会话轨迹视图扩展为 docs/logs 下 65 个会话 JSONL 的结构化统计（103911 事件/250 轮/3265 工具调用/753 次 Helper 直调/111 次 PYEOF/6 会话 KeyError），量化三类优化方向；保留 status、report_kind 与关系。
  at: '2026-08-14T22:04:08.796882Z'
- signature:
    product_name: TraeCode
    model_name:
    agent_runtime_name:
  at: '2026-08-14T22:15:55.859781Z'
  summary: fact_correction：统计脚本固化为 docs/logs/analyze_sessions.py 与 analyze_calls.py 并复现全部数字，据此更正记错事实——Helper 直调 753→757（38.5%，其中 ldvh call 682/capabilities 48/check 27）、heredoc 拼接 111→155（含 PYEOF 定界 18，单会话 session-23c4d407 81 次）、输入 token 20.46M→20.30M、缓存结论由“字段缺失统计为 0”更正为 cacheReadTokens 合计 474.8M（52 会话）、重复信号 top 会话更正为 session-2402ebe8/f86b63cf/c46e04f4；status、report_kind 与关系保持不变。
- signature:
    product_name: TraeCode
    model_name: glm-5.3
    agent_runtime_name:
  at: '2026-08-14T22:22:24.300028Z'
  summary: content_update（Human 当次授权）：把“更薄 Helper 调用封装”细化为分层优化方案写入建议章节——Phase 1 CLI 机械扩展（P1-1 请求文件化 --request / P1-2 请求骨架 --example / P1-3 结果投影 --fields）、Phase 2 领域契约扩展（P2-1 prepare-update CAS 一体化 / P2-2 成功信号显式化）、Phase 3 MCP 化治理议题（09 修订 Human Gate 先行）；建议 4 升级为验证前置并绑定 session_comparability/replay 对照；recommendation_summary 同步更新，后续分流表逐项保持判断标准；status、report_kind、关系与其余章节不变。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
object_uid: 01a00246-3d5b-77d6-b6fa-e44c05db9aab
object_id: study-01M014CFAVEZBBDYQ49G2XQ6NB
fact_type_key: study
created_at: '2026-08-14T21:55:51.666073Z'
updated_at: '2026-08-16T21:42:45.620720Z'
---

## 研究问题

当前项目对 Helper 交互、规范检索与上下文占用的优化（如 spark Helper 只读交互优化、受控写入优化）需要跨会话证据。本报告回答：对 DeepSeek Harness 65 个真实会话日志做结构化统计，能观察到哪些 LDVH Helper 调用模式、性能特征与易错点，以及它们分别指向哪些有证据支撑的优化方向？

## 输入与边界

输入为 DeepSeek Harness 会话日志解压目录 [docs/logs/](docs/logs/)（65 个 session.jsonl，来自 ~/.dsh/sessions/--Users-dmh2002-poker_hud_projects-ld-vibe-harness-v4--/，Zstandard 解压）。分析脚本为 docs/logs/analyze_sessions.py（会话级统计）与 docs/logs/analyze_calls.py（工具调用模式，正确解析 tool/call 的 arguments JSON 字符串）；两份脚本已固化于该目录，本报告全部关键数字可由脚本复现（2026-08-15 更正即基于复现结果）。

样本规模：65 会话、103911 条事件、250 轮、3265 次工具调用，覆盖 10 种模型（gpt-5.6-terra/luna/sol、deepseek-v4-flash/pro、glm-5.2、kimi-k3、claude-fable-5、gpt-5.3-codex-spark、deepseek-flash 等）。

边界与限制：

- 统计口径来自宿主 DeepSeek Harness 事件日志，不是 LDVH 自身的测量；token/时间/缓存数据不能直接当作 LDVH 优化依据。
- 日志来自本项目 worktree 的真实会话，不代表全部宿主、模型或工作负载的总体。
- helper 调用识别以 bash 命令中出现 `ldvh call/capabilities/check` 为口径，未覆盖 skill 路由与其它包装方式。

## 关键发现

### 发现 1：Helper 调用在 bash 中占高比例，且存在大量手工拼接

- 65 会话共 1964 次 bash 工具调用，其中 **757 次（38.5%）直接调用 LDVH Helper**（命令含 `ldvh call/capabilities/check`；其中 `ldvh call` 682、`ldvh capabilities` 48、`ldvh check` 27）。
- **155 次 bash 使用 python heredoc**（`python3 << ...`）构造请求（内含 `import json, subprocess`、UTC 时间戳等），其中 18 次以 PYEOF 为定界符；单会话 session-23c4d407 达 81 次。
- Helper 操作分布（bash 直调口径）：read-fact-objects 224、read-specification-content 99、update-workcase 83、find-fact-object-candidates 63、read-action-template-content 60、create-fact-object 31（capabilities 48 与 check 27 为直调子项，见发现 1）。

对后续项目工作的直接影响：这量化佐证“Helper 没有更薄调用封装、AI 每轮重复构造样板”的优化方向，可作为 Helper 交互优化（spark Helper 只读交互优化）的证据。

### 发现 2：规范契约回查与只读展开是高频操作

read-specification-content（99 次）与 read-action-template-content（60 次）、read-action-template-candidates（18 次）合计 177 次，说明 AI 频繁按需读取规范与行动模板；加之 read-fact-objects 224 次为最高频 Helper 操作，反映只读检索与对象读取是主要消耗面。

对后续项目工作的直接影响：这指向“规范字段契约检索成本高、只读输出可窄化”，支持 spark Helper 只读交互优化方向的窄输出/按需展开判断。

### 发现 3：重复创建与脚本解析错误在样本中可量化

- **6 个会话出现 KeyError**（如脚本字段名错误解析 Helper 结果）。
- **64 个会话出现重复/两份信号**（文本含“重复创建”“两份”“duplicate”等）。

需注意：重复/两份信号多为泛文本匹配，不全是真正重复创建；信号最集中的会话为 session-2402ebe8（89 个事件）、session-f86b63cf（72）、session-c46e04f4（67），需人工甄别。但它至少说明 create/update 结果解析易错是跨会话现象，而非孤立个例。

对后续项目工作的直接影响：这是 create 类操作结果提示可优化的量化证据，支持在 Helper 交互优化中评估更明确的“已创建/未创建”机器可判定信号。

### 发现 4：token 与上下文占用特征（口径来自宿主）

- 65 会话总计输入 20.30M tok（20,301,139）vs 输出 1.80M tok（1,800,706），约 11.3:1。
- 52 个会话有 usage 事件；usage 字段为 inputTokens/outputTokens/cacheReadTokens，cacheReadTokens 合计 474.8M（474,806,784），约为非缓存输入的 23 倍。此前版本误用字段名 cacheReadInputTokens 得出“缓存字段缺失（统计为 0）”，本次以固化脚本复现后更正；该失误本身是发现 3 所述“临时脚本解析字段名易错”的一个实例。

对后续项目工作的直接影响：若后续要在 LDVH 内部做上下文占用分析，必须先建立 LDVH 自身的可测量口径（含缓存/耗时/成本），而不是直接消费宿主统计。

## 建议

1. **固化更薄的 Helper 调用封装（Phase 1：CLI 机械扩展，不动领域语义）**：目标为 Helper 交互体验，三个候选按证据强度排序：
   - P1-1 请求文件化：`ldvh call <op> --request <path>` 接受请求 JSON 文件，AI 以文件工具生成请求（可 diff、无 shell 引号转义），bash 退化为单行调用；证据为 155 次 python heredoc（top-4 会话占 153 次，属会话级习惯模式）；验收标准为“新会话 heredoc 拼接降为 0”。
   - P1-2 请求骨架现取：补全高频操作 input_examples 并提供 `--example` 直接输出可填骨架；证据为 capabilities 48 次契约发现调用与 invalid_request 盲试重试；验收标准为“首次合法请求率上升、契约试调重试下降”。
   - P1-3 结果投影：`--fields` 按需选取响应字段（与 compact/diagnostic 档位正交）；证据为 KeyError 6 会话源于临时脚本猜字段名；验收标准为“响应字段猜测错误消除”。
2. **降低规范契约回查成本、窄化只读输出**：证据为 read-specification-content/read-action-template-content 合计 177 次；机械部分由 P1-2/P1-3 承接，窄输出语义判断仍归 spark Helper 只读交互优化；验收标准为“完成同类操作所需 read/grep 回查次数下降、成功路径输出收敛为最窄定义”。
3. **领域契约扩展（Phase 2：独立立项，涉及 05/21 修订）**：P2-1 CAS 一体化——`prepare-update` 类操作一次返回当前对象、content_fingerprint 与排除托管字段的 after 骨架，证据为 read-fact-objects 224 与 update-workcase 83 的配对模式及 64 位指纹手工转写风险，验收标准为“单次 CAS 流程 bash 往返 3-4 次降为 2 次”；P2-2 写入成功信号显式化——create/update 固定返回 object_uid/object_id/content_fingerprint/created 与回读 locator，证据为 6 会话 KeyError、64 会话重复/两份信号，验收标准为“重复创建率与结果解析失败率下降”。
4. **建立 LDVH 自身的可测量口径（Phase 1/2 的验证前置）**：指标至少含 per-op 往返数、命令 token 占用与 invalid_request 率；证据为 token 统计依赖宿主口径、cacheReadTokens 474.8M 约为非缓存输入 20.3M 的 23 倍（每次 bash 往返都伴随上下文重载，往返次数直接放大复读量）；验收标准为“token/时间/缓存/成本可归因于 LDVH 自身调用链，并可用 session_comparability/replay 对照验证 Phase 1 因果”。
5. **结构性方向（Phase 3：MCP 化，治理议题先行）**：将 top-N Helper 操作暴露为原生 MCP tools 可同时消除三类根因（757 次直调全部转为结构化工具调用），但 09 规范明文“不存在环境 adapter 层”——是否构成新接入层必须先经 09 规范修订 Human Gate 判定；在此之前不实现、不补规。

以上建议均为评估方向，不构成已决定行动。

## 后续分流

| 建议 | 承接方向 | 判断标准 |
|---|---|---|
| Phase 1（P1-1 请求文件化/P1-2 骨架/P1-3 投影） | 与 spark Helper 只读交互优化对照后并入或衍生 WorkCase；涉及 04/04.Att.01 契约修订 | 多会话重复样板样本已具备（757 直调/155 heredoc），与现有 spark 范围不冲突时立项；立项前先落建议 4 口径 |
| 降低规范契约回查成本、窄化只读输出 | 并入 spark Helper 只读交互优化（source_content 去重/窄输出待承接部分） | read/grep 回查次数可量化下降，且与 spark 现有待承接范围不冲突时立项 |
| Phase 2（P2-1 prepare-update/P2-2 成功信号） | 涉及 05/21 领域契约修订，独立 WorkCase | read/update 配对证据固化后立项（P2-1）；有第二个独立重复创建样本或失败诊断需求时立项（P2-2） |
| Phase 3（MCP 化） | 独立 Spark/ADR 议题 | 经 09 规范修订 Human Gate 判定是否构成新接入层后再决定是否展开 |
| 可测量口径（建议 4） | 作为 Phase 1/2 验证前置 | 需验证 Phase 1 因果或在 LDVH 内部做上下文占用分析时立项 |

### 后续监测

- 继续采集不同模型/宿主/工作负载的日志样本，并补充 LDVH 自身调用链的测量口径后再评估可迁移性。
- 本报告不建立健康分、遥测、Dashboard 或告警。
