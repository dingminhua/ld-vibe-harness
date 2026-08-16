---
title: DeepSeek Harness 会话事件日志执行可比性观察面盘点
status: active
report_kind: technical_assessment
research_question: DeepSeek Harness 持久化会话事件日志能否在评分前以机器证据判定各试次执行载体是否可比较（comparable / not_comparable / inconclusive），从而支撑 LDVH 最小执行证据协议与执行可比性门槛？
abstract: 对当前环境 6 个真实 DeepSeek Harness 会话日志（~/.dsh/sessions 下 Zstandard 压缩 JSONL）执行只读盘点，确认模型/工具入口、事件图配对完整性与 approval/permission/compact/retry/hook 等执行载体事件均可直接机器观察，并给出每会话的可比性三值初判。盘点确认轨迹日志可作为 harness-delivered 层级的执行载体证据来源，但不提升为 host-received；同会话跨模型切换（reason=change）是执行载体不等价的直接机器证据。
research_intent: 保存本次只读盘点的观察面、提取规则与三值初判结论，供后续最小执行证据协议定义与等价复验 WorkCase 直接消费，避免后续 AI 重新摸索 DSH 日志结构或误把轨迹渲染视图当作可读数据源。
recommendation_summary: 轨迹日志可直接支撑评分前执行可比性判定；下一步以 session_comparability 模块把盘点逻辑固化为可复用只读工具并配聚焦测试（纳入 WorkCase），先过执行可比性门槛再判断上下文效果差异。
input_refs:
- kind: working_tree
  locator: ~/.dsh/sessions/--Users-dmh2002-poker_hud_projects-ld-vibe-harness-v4--/*/session.jsonl.zstd（6 个会话，只读聚合）
  observed_at: '2026-08-13T21:47:25Z'
- kind: code
  locator: node_modules/@deepseek-ai/dsh-session/lib/types/known-event-types.js（DSH 事件词汇表）
  version: 0.1.0-rc.6
  observed_at: '2026-08-13T21:47:25Z'
relations:
- relation_key: inspired-by
  target:
    object_uid: 019ffb52-ebb5-74ea-a2f9-9f309e85d013
action_relevance: 分析或比较不同会话日志的可比性时，标注各环境的事件观察面差异，不假设字段对称
change_log:
- signature:
    product_name: DeepSeek Harness
    model_name: deepseek-v4-flash
    agent_runtime_name:
  at: '2026-08-13T21:48:03.167269Z'
  summary: 受控创建 technical_assessment：保存 6 个 DSH 会话日志的执行可比性观察面盘点聚合结论；只保存聚合与结构指纹，不保存原始会话内容。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
object_uid: 019ffd18-bafe-714f-be81-257c1502b922
object_id: study-01KZYHHEQYE57VX095FGAG5E92
fact_type_key: study
created_at: '2026-08-13T21:48:03.167269Z'
updated_at: '2026-08-16T21:42:45.620720Z'
---

## 研究问题

DeepSeek Harness 持久化会话事件日志能否在评分前以机器证据判定各试次执行载体是否可比较（`comparable` / `not_comparable` / `inconclusive`），从而支撑 LDVH 最小执行证据协议与执行可比性门槛？

## 输入与边界

输入为当前环境 `~/.dsh/sessions/` 下 6 个真实会话的持久化事件日志（Zstandard 压缩 JSONL，每个会话一条文件），以及 DSH 会话事件词汇表（`@deepseek-ai/dsh-session` 的 `known-event-types.js`，43 种已知事件类型）。盘点只读取结构化字段（事件类型、时间戳、provider/model、工具名、事件配对计数），不读取 user/message 文本、tool/result 内容或 assistant 输出，符合 Spark 隐私停止边界；长期事实只保存聚合结论，不保存原始交互。

## 关键发现

- 模型/工具入口可直接机器观察：`request/header` 事件携带 `data.header.config.provider/model` 与 `data.reason`（`initial`/`change`/`resume`）；`tool/call` 携带工具名与参数（参数内容未读取）。
- 事件图配对完整性可机械校验：turn/step/tool 的 start/end 配对计数可逐会话统计；未配对即事件图不完整。
- `reason=change` 是执行载体不等价的直接机器证据：实测 2 个会话发生会话中途模型切换（`23c4d407`：glm-5.2→deepseek-v4-flash；`fa022f70`：1 个 initial + 4 个 change，跨 4 个不同模型）。
- 三值初判可机械落地：单模型入口且事件图配对完整 → `comparable`；多模型入口或配对缺失 → `not_comparable`；无 `request/header`（会话未运行）→ `inconclusive`。
- 6 会话盘点结果：2 个 `comparable`（1ebd4598、f3e87f83、89176a87 共 3 个单模型完整会话）、1 个 `inconclusive`（201a6d46 无请求头）、2 个 `not_comparable`（23c4d407 多模型+配对缺失、fa022f70 跨 4 模型）。
- approval/permission/sandbox 事件可观察：`fa022f70` 记录完整 `approval/asked`+`approval/decided` 链。
- compact/retry/hook/resume 均有原生事件类型（`compaction/*`、`llm/retry`、`hook/invoked|result`、`session/end-seed`、`plan/mode`），当前 6 个会话尚未触发，词汇表已确认存在。
- 解析注意点（盘点工具自身的可靠性要求）：`reason` 位于 `data.reason` 而非 `data.header` 内；`tool/call` 配对计数必须与工具名校验共用同一分支，否则计数恒为 0。

### 边界与限制

- 本盘点只证明 DSH 日志可作为 `harness-delivered` 层级的执行载体证据来源；不提供 `host-received`（无 provider 回执时仍为 `unavailable`），不证明 `behavior-consistent` 或 `causal-effect`。
- 三值初判是机械可比的必要条件判断，不是因果结论；`comparable` 只表示执行载体与事件图满足可比前置，不表示上下文条件等价或结果可解释。
- 当前样本为同一项目 worktree 的 6 个会话，不代表全部宿主或模型群体的代表样本。

## 建议

- 将盘点逻辑固化为 `code/ldvh/testing/session_comparability.py` 只读模块并配聚焦测试（纳入 WorkCase），输出结构化指纹与三值初判，供评分管线直接消费。
- 在等价复验（WFPQDZ 延续）中，先以本盘点规则判断各试次 `comparable`，再进入上下文效果比较。
- 保留本 Study 为方法证据；不据此建立健康分、遥测、Dashboard 或告警。

## 后续分流

- 本 Study 不替代 WorkCase Gate 2；盘点结论作为新建 WorkCase 提案依据。
- 不创建统一健康分、长期遥测、Dashboard 或告警。
