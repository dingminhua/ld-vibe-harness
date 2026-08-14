# 最小执行证据协议规范草案

## 1. 目标与范围

本草案定义 LDVH 最小执行证据协议（Minimum Execution Evidence Protocol），为第 3–5 项优化（读写契约统一、read→update 契约闭合、签名拼装减负、只读去重）提供「是否真有效」的评估前置机制。

协议以会话事件日志（harness-delivered 层级）为证据来源，不提升为 host-received。

**不在本协议范围内**：
- 修改正式 `specs/` 文件
- 因果结论（causal-effect）或总体服务改善证据
- 消息正文、工具结果内容、assistant 输出的读取

## 2. 四类身份定义

每个 trial 在评分前记录以下四类身份指纹：

| 身份 | 来源 | 指纹计算 |
|---|---|---|
| **task** | `task_id` + `task_package_hash` | `SHA-256({"task_id": …, "task_package_hash": …})` |
| **contract** | `contract_sha256` | `SHA-256({"contract_sha256": …})` |
| **payload** | payload 结构键集合 + payload 自身 canonical SHA-256 | `SHA-256({"payload_keys": […], "payload_sha256": …})` |
| **runner** | `carrier_fingerprint` | `SHA-256({"carrier_fingerprint": …})` |

`IdentityFingerprintSet` 聚合四类指纹，提供：

- `fingerprint()`：四类身份整体的 canonical SHA-256
- `identity_mismatch(other)`：逐类型比较，返回每类是否匹配
- `fully_matches(other)`：仅当全部四类匹配时返回 `True`

## 3. 五级事件来源分级

每个可分类的会话事件类型归属于以下五个级别之一：

| 级别 | 标签 | 包含事件类型 | 可观察性 |
|---|---|---|---|
| **LDVH 预备** | `ldvh-prepared` | `approval/asked`, `approval/decided`, `approval/policy`, `permission/preset`, `sandbox/mode`, `compaction/*`, `llm/retry`, `hook/*`, `session/end-seed`, `plan/mode`, `feedback/record`, `subagent/descriptor`, `todo/write`, `tool-workflow/*` | 从会话日志可观察 |
| **Harness 递达** | `harness-delivered` | `request/header`, `tool/call`, `tool/result`, `turn/start`, `turn/end`, `step/start`, `step/end` | 从会话日志可观察 |
| **Host 接收** | `host-received` | 无（host 侧事件不可从会话日志获取） | **不可观察** |
| **行为一致** | `behavior-consistent` | 聚合级观察（跨 trial 比较） | 从聚合结果可推断 |
| **因果效应** | `causal-effect` | 无（需要实验设计，超出结构化日志范围） | **不可观察** |

**证据边界**：协议只使用 `ldvh-prepared` 和 `harness-delivered` 级别作为证据来源。`host-received` 和 `causal-effect` 明确不在范围内。

**不透明事件类型**：`user/message`, `assistant/message`, `assistant/chunk`, `text-chunks`, `reasoning-chunks`, `tool-call-chunks`, `agent/inbox/spliced`, `session/title`, `session/title-llm-request`, `request/context`, `session`, `agent-preset/selected` 等事件类型的内容不被读取，跳过分类。

## 4. 评分前可比性门槛

协议在 `session_comparability` 的 session 级可比性判定的基础上，增加以下协议级检查：

### 4.1 Session 级可比性（复用）

复用 `session_comparability.judge_comparability()` 的结果：

| 条件 | 判定 |
|---|---|
| 无 `request/header` 条目 | `inconclusive` |
| 多于一个 distinct provider/model entry | `not_comparable` |
| turn/step/tool 配对不完整 | `not_comparable` |
| 以上均不满足 | `comparable` |

### 4.2 协议级身份匹配

当提供 `reference_identity` 时，每个 trial 的身份指纹与参考身份比较：

- 四类身份全部匹配 → `comparable`
- 任意一类不匹配 → `not_comparable`（原因：`out_of_protocol: identity mismatch on <type>`）

### 4.3 事件图配对完整性

检查 session fingerprint 的 `pairing_ok` 属性：

- `pairing_ok = True` → 通过
- `pairing_ok = False` → `not_comparable`（原因：`event_graph_pairing_incomplete`）

### 4.4 组合判定

`ProtocolComparability` 的 `effective_verdict` 按以下规则得出：

1. 如果 `protocol_verdict` 为 `not_comparable` → `not_comparable`
2. 否则使用 `session_verdict.verdict`

## 5. 消费规则

### 5.1 评分前过滤

`check_pre_scoring_threshold()` 返回 `(passed, reason)`：

- `(True, "comparable")` → 允许进入评分
- `(False, reason)` → 阻止评分，原因如 `out_of_protocol`、`session_not_comparable`、`session_inconclusive`、`protocol_not_comparable`

### 5.2 Scoring 集成

在 `equivalence_retrial.py` 中：

- `run_trial()` 接受可选 `reference_identity` 参数
- 每个 trial 记录 `protocol_identity`（四类指纹）和 `protocol_verdict`
- `out_of_protocol = True` 的 trial 在评分前被标记
- `BatchSummary` 报告 `out_of_protocol_count`

### 5.3 持久化

`persist_batch_artifacts()` 在 `trials.json` 中记录每个 trial 的 `out_of_protocol` 状态。

## 6. 实现参考

协议在以下模块中实现：

- `code/ldvh/testing/evidence_protocol.py`：身份定义、来源分级、可比性门槛规则
- `code/ldvh/testing/equivalence_retrial.py`：评分管线集成（`TrialRecord.protocol_identity`, `run_trial(..., reference_identity=...)`, `BatchSummary.out_of_protocol_count`）
- `code/tests/testing/test_evidence_protocol.py`：协议聚焦测试（23 项）
- `code/tests/testing/test_equivalence_retrial.py`：协议集成测试（5 项）

## 7. 边界与限制

- 协议不证明因果效应、host receipt 或总体服务改善
- 协议不读取消息正文、工具结果内容或 assistant 输出
- 协议以 harness-delivered 事件日志为证据来源上限，不提升为 host-received
- 协议身份不匹配的 trial 不进入评分，但不影响其他 trial 的评分结果
- 本草案不修改正式 `specs/` 文件