---
title: LDVH 五类事实对象生命周期并行摩擦测试报告
status: active
report_kind: internal_audit
research_intent: 6 路并行摩擦测试完成后，需要将分散的摩擦记录合并为一份可跨行动复读的汇总报告。记录 LDVH 行为清单落地过程中发现的全部摩擦点，为后续规范改进、模板完善和执行者避坑提供系统化参考。
research_question: LDVH 五类事实对象在完整生命周期执行中，实际遇到了哪些摩擦？这些摩擦的根因、影响和恢复路径是什么？有哪些共性摩擦贯穿所有类型？
abstract: 本报告汇总了 6 路并行摩擦测试的全部发现。测试覆盖 5 类事实对象的完整生命周期以及 6 项读取类操作。共记录了 14 类摩擦点，涵盖 draft→create schema 不对齐、change_log 隐式要求、托管字段污染、promote 与 change_log 矛盾、全库审计 partial 等核心问题。每类摩擦标注了根因、影响和恢复步骤，归纳了 4 项共性摩擦和 5 项改进建议。
recommendation_summary: 建议优先处理 4 项高影响共性摩擦：draft→create schema 不对齐、托管字段扩散、全库审计 partial 的既有 invalid 对象清理、以及 promote 的 status-only 约束与 write-entry 矛盾。建议通过修模板、清遗留对象、加专属操作来消除这些摩擦的重复发生。
input_refs:
- kind: specification
  locator: specs/20-Spark-火花.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/21-WorkCase-工作项.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/22-ADR-决策.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/23-Pitfall-踩坑经验.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/24-Study-研究报告.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/31-事实对象判定与受控创建行动模板.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/32-事实对象生命周期变更与承接处置行动模板.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/34-WorkCase获批计划执行行动模板.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: specification
  locator: specs/00-理念与构成.md
  version: b1d1489d
  observed_at: '2026-08-18T16:00:00Z'
- kind: working-tree-statistics
  locator: docs/ldvh-behaviors/frictions/friction-read-operations.md
  observed_at: '2026-08-18T16:30:00Z'
- kind: working-tree-statistics
  locator: docs/ldvh-behaviors/frictions/friction-study-lifecycle.md
  observed_at: '2026-08-18T16:30:00Z'
- kind: working-tree-statistics
  locator: docs/ldvh-behaviors/frictions/friction-spark-lifecycle.md
  observed_at: '2026-08-18T16:30:00Z'
- kind: working-tree-statistics
  locator: docs/ldvh-behaviors/frictions/friction-pitfall-lifecycle.md
  observed_at: '2026-08-18T16:30:00Z'
- kind: working-tree-statistics
  locator: docs/ldvh-behaviors/frictions/friction-adr-lifecycle.md
  observed_at: '2026-08-18T16:30:00Z'
- kind: working-tree-statistics
  locator: docs/ldvh-behaviors/frictions/friction-wc-lifecycle.md
  observed_at: '2026-08-18T16:30:00Z'
change_log:
- summary: 受控创建 Study：LDVH 五类事实对象生命周期并行摩擦测试报告，汇总 6 路 Worker 摩擦测试结果。
  signature:
    product_name: Cindy
    model_name: gpt-5
  at: '2026-08-18T12:33:42.634139Z'
- summary: 受控更新 Study：补充每项摩擦的精确复现命令、CLI 输入、JSON 错误响应和修复方向，使各项摩擦可直接用于 fix bug 或完善 specs。
  signature:
    product_name: Cindy
    model_name: gpt-5
  at: '2026-08-18T12:45:57.277364Z'
- summary: 受控更新 Study：新增 F15（签名未继承）摩擦，新增 发现六分析 Worker 签名错误根因，新增建议 6 及后续分流 6。
  signature:
    product_name: Cindy
    model_name: gpt-5
  at: '2026-08-18T12:57:46.013452Z'
- summary: 受控更新 Study：修正插入位置，在「建议」前新增 发现六：签名未继承（Worker 写入署名全部错误，处理办法为 Subagent 写入需继承主控信息）。
  signature:
    product_name: Cindy
    model_name: gpt-5
  at: '2026-08-18T12:58:42.240617Z'
object_uid: 01a014dd-0337-747e-a7d4-27618acb720b
object_id: study-01M0ADT0SQEHZAFN17C65CPWGB
fact_type_key: study
created_at: '2026-08-18T12:33:42.634139Z'
updated_at: '2026-08-18T12:58:42.240617Z'
---

## 研究问题

**本项目为何需要这轮报告**：前期 Study（study-01M09ZNYA8F3K8FW1VBDYTYXCB）已完成 LDVH 五类事实对象生命周期行为清单的建立，但清单中的行为是否在实际执行中遇到摩擦、哪些摩擦具有共性、哪些需要规范/模板/执行者层面改进——这些信息尚未系统化收集。6 路并行摩擦测试产出 6 份分散的摩擦记录文件，需要合并为一份可跨行动复读的汇总报告，使后续 AI 执行者无需重读 6 份原始文件即可理解摩擦全景。

**本报告实际回答的问题**：6 路并行摩擦测试中，每类事实对象暴露了哪些具体摩擦？这些摩擦的根因（工具限制、契约模糊、规范冲突、信息不足）和影响范围是什么？有哪些摩擦贯穿所有 5 类事实对象？哪些摩擦可以通过改进规范/模板/CLI 消除，哪些必须依赖 AI 自律？全库审计 partial 的真实原因是什么？6 个测试对象的创建与更新是否成功？

## 输入与边界

本报告基于以下输入：

**规范来源**（commit `b1d1489d`，2026-08-18 基线）：
- `specs/20-Spark-火花.md`、`specs/21-WorkCase-工作项.md`、`specs/22-ADR-决策.md`、`specs/23-Pitfall-踩坑经验.md`、`specs/24-Study-研究报告.md`、`specs/31-事实对象判定与受控创建行动模板.md`、`specs/32-事实对象生命周期变更与承接处置行动模板.md`、`specs/34-WorkCase获批计划执行行动模板.md`、`specs/00-理念与构成.md`

**摩擦记录来源**（6 路 Worker 产出，文件位于 `docs/ldvh-behaviors/frictions/`，gitignored）：
- `friction-read-operations.md`：读取类 6 项操作摩擦
- `friction-study-lifecycle.md`：Study 创建→更新→retired 摩擦
- `friction-spark-lifecycle.md`：Spark 创建→更新→discarded 摩擦
- `friction-pitfall-lifecycle.md`：Pitfall 2 条线摩擦
- `friction-adr-lifecycle.md`：ADR 创建→更新→retired 摩擦
- `friction-wc-lifecycle.md`：WorkCase 全流程摩擦

**测试产生的对象**（未提交）：
- Spark: `spark-01M0A68XW3EYBR6DY3XQ1QSWXD`（最终 discarded）
- ADR: `adr-01M0A6AXBFFYCVHTZWF3FB70RZ`（最终 retired）
- Pitfall 主: `pitfall-01M0A65MQ1FYV8DMQN3DP38XQF`（最终 active）
- Pitfall 副: `pitfall-01M0A6E07DFAS80N5ATBHVY3FB`（最终 discarded）
- Study: `study-01M0A6524BE939372CZ9Z5DFGM`（最终 retired）
- WorkCase: `workcase-01M0A6YSD0E93SV9GDM9HEPNPH`（最终 closed）

**边界**：本报告只汇总摩擦测试结果，不代替规范作为权威来源。摩擦的严重度评估基于单次测试经验，不表示在所有场景下同等严重。全库审计 partial 的既有 3 个 invalid 对象未在本报告范围内修复。

**版本与日期**：LDVH v4.1.0-124-gb1d1489d，2026-08-18。

## 关键发现

### 发现一：14 类摩擦点全景

按摩擦类型分组，6 路测试共发现 14 类摩擦点：

| 编号 | 摩擦点 | 影响类型 | 出现类型 | 严重度 | 可机械修复？ |
|---|---|---|---|---|---|
| F1 | draft→create schema 不对齐（carrier/field_contracts/managed_fields 超限） | 工具限制 | ADR, Pitfall, Study, Spark, WorkCase | 高 | 是 |
| F2 | change_log 首条流水隐式要求（draft 阶段无提示） | 信息不足 | ADR, Pitfall, Study, Spark, WorkCase | 中 | 是 |
| F3 | observed_context.signature 缺失 | 信息不足 | Study, WorkCase | 中 | 是 |
| F4 | evolution.at 时间约束（不能早于 Code 绑定 created_at） | 契约模糊 | Spark | 中 | 是 |
| F5 | 托管字段污染（after 携带托管字段被拒） | 工具限制 | ADR, Pitfall, Study, Spark, WorkCase | 高 | 是 |
| F6 | promote 的 status-only 约束与 update-fact-object 的 change_log 追加矛盾 | 规范冲突 | Pitfall | 高 | 否 |
| F7 | urls.ref 必须是绝对 HTTP(S) URL | 设计约束 | ADR | 低 | 否 |
| F8 | retirement Human Gate 不可见（Code 不检查授权） | 设计选择 | ADR, Study | 中 | 否 |
| F9 | read-specification-content 信封坑（requested_disclosure 放错位置，退出码 0） | 信息不足 | 读取类 | 中 | 是 |
| F10 | capabilities 超大单行 JSON 输出 | 工具限制 | 读取类 | 低 | 是 |
| F11 | 全库审计始终 partial（既有 3 个 invalid 对象污染） | 信息不足 | 所有 5 类 + 读取类 | 高 | 是 |
| F12 | WorkCase item_event 不能自动推进 phase | 设计约束 | WorkCase | 信息 | 否 |
| F13 | WorkCase complete-work-item 拒绝最后一项 | 设计约束 | WorkCase | 低 | 否 |
| F14 | .gitignore 的 docs/ 规则忽略摩擦记录文件 | 工具限制 | 所有 6 路 | 中 | 是 |
| F15 | Worker 签名未继承主控上下文（product_name/model_name 全部错误） | 信息不足 | 所有 6 路 Worker 测试对象 | 高 | 是 |



### 摩擦精确复现链（含 CLI 输入与错误响应）

以下为每项可机械复现摩擦的精确 CLI 命令、输入 JSON 和收到错误响应，可直接用于 fix bug 或完善 specs：

#### F1：draft_basis 包含 carrier/field_contracts/managed_fields

**复现命令**：
```bash
printf '%s' '{"arguments":{"draft_basis":{"governed_project_id":"ldvh","fact_type_key":"study","schema_fingerprint":"<当前schema_fp>","worktree_fingerprint":"<当前worktree_fp>","carrier":"markdown","managed_fields":["created_at"],"field_contracts":[{"field_path":"title"}]},"fact_object":{...<合法对象>...},"observed_context":{"signature":{"product_name":"Cindy","model_name":"gpt-5"}}}' | ./ldvh call create-fact-object
```

**错误响应**：
```
outcome=invalid_request
gaps=["arguments.draft_basis 包含未知字段: carrier, field_contracts, managed_fields"]
diagnostics=[["arguments.draft_basis 包含未知字段: carrier, field_contracts, managed_fields"]]
```

**修复方向**：`prepare-fact-object-draft` 返回的 result 中，carrier/field_contracts/managed_fields 的语义是"供 AI 填表参考"，不应出现在 draft_basis 的 schema 路径中。可在 prepare 结果中标注 `draft_basis_allowed: [governed_project_id, fact_type_key, schema_fingerprint, worktree_fingerprint]`，或直接在 CLI 提供预裁剪的 draft_basis_candidate。

#### F2：change_log 首条流水隐式要求

**复现命令**：
```bash
printf '%s' '{"arguments":{"draft_basis":{"governed_project_id":"ldvh","fact_type_key":"study","schema_fingerprint":"<fp>","worktree_fingerprint":"<fp>"},"fact_object":{"frontmatter":{...<含 change_log: [] 空数组>...},"body":"..."},"observed_context":{"signature":{"product_name":"Cindy","model_name":"gpt-5"}}}' | ./ldvh call create-fact-object
```

**错误响应**：
```
outcome=rejected
gaps=["change_log: array 字段出现时不得为空",
      "change_log: 新建事实对象必须包含首条 change_log 流水",
      ...其他字段的汉字约束...]
```

**修复方向**：`prepare-fact-object-draft` 的 field_contracts 中 change_log 的 presence 标注为 conditional，但创建时实际是 required。把 change_log 的 presence 改为 required（或增加 conditional_reason 说明"创建时必填，后续更新 conditional"），或 draft 阶段直接提供首条流水模板。

#### F3：observed_context.signature 缺失

**复现命令**：
```bash
printf '%s' '{"arguments":{...<合法 draft_basis + fact_object>...},"observed_context":{}}' | ./ldvh call create-fact-object
```

**错误响应**：
```
outcome=invalid_request
gaps=["LDVH 署名必须是 object",
      "observed_context 解析失败：LDVH 署名必须是 object"]
diagnostics=[["LDVH 署名必须是 object",
              "observed_context 解析失败：LDVH 署名必须是 object"]]
```

**修复方向**：observed_context.signature 是顶层请求字段，不是 arguments 内字段。prepare-fact-object-draft 的 preparation 结果应在 observed_context 或 signature 相关字段中提示"创建请求必须包含顶层 observed_context.signature"。当前 capabilities 的 --example 路径未直接展示此字段，可考虑在模板中显式标注。

#### F4：evolution.at 不得早于 created_at

**复现命令**：
```bash
printf '%s' '{"arguments":{"draft_basis":{"governed_project_id":"ldvh","fact_type_key":"spark","schema_fingerprint":"<Spark fp>","worktree_fingerprint":"<fp>"},"fact_object":{"title":"F4","status":"open","priority":"P2","intent":"i","summary":"s","evolution":[{"summary":"准备","at":"2026-08-17T00:00:00Z"}],"change_log":[{"summary":"创建","signature":{"product_name":"Cindy","model_name":"gpt-5"},"at":"2026-08-18T17:40:00Z"}]},"observed_context":{"signature":{"product_name":"Cindy","model_name":"gpt-5"}}}' | ./ldvh call create-fact-object
```

**错误响应**：
```
outcome=rejected
gaps=["evolution[0].at: evolution.at 不得早于 created_at"]
```

**修复方向**：创建时 Code 时间未知，调用方无法预填 evolution.at 为"不早于 created_at"的值。建议在 prepare-fact-object-draft 的 field_contracts 中标注 evolution[].at 约束: 创建时不可预填，创建成功后通过 update-fact-object 追加，或创建时自动忽略 evolution 字段由 Code 绑定时间。

#### F5：托管字段污染（after 携带托管字段被拒）

**复现命令**：
```bash
# 先用 read-fact-objects 读取对象，直接把读取结果作为 update-fact-object 的 after
# 读取结果包含 object_uid/object_id/fact_type_key/created_at/updated_at
# 将这些字段带入 fact_object 提交 update-fact-object → rejected
```

**错误响应**（来自 Worker 原始记录）：
```
invalid_request: AI 不得填写 Code 托管字段 — object_uid, object_id, fact_type_key, created_at, updated_at
```

**复现对象**：当前工作树中任意已创建对象均可复现，托管字段列表可通过 prepare-fact-object-update 的 managed_fields_removed 确认。

**修复方向**：`update-fact-object` 的契约中应明确标注托管字段列表，`read-fact-objects` 的响应中可标注 managed_fields 标记提醒调用方在构造 after 时移除。当前 prepare-fact-object-update 已自动移除托管字段（managed_fields_removed），但 read-fact-objects 的响应中没有自动移除提醒。

#### F7：urls.ref 必须是绝对 HTTP(S) URL

**复现命令**：
```bash
printf '%s' '{"arguments":{"draft_basis":{"governed_project_id":"ldvh","fact_type_key":"adr","schema_fingerprint":"<ADR fp>","worktree_fingerprint":"<fp>"},"fact_object":{"title":"F7","status":"active","decision_question":"d","decision":"d","applicability":"a","rationale":"r","consequences":"c","urls":[{"ref":"specs/22-ADR-决策.md","title":"本地","summary":"测试"}],"change_log":[{"summary":"创建","signature":{"product_name":"Cindy","model_name":"gpt-5"},"at":"2026-08-18T17:40:00Z"}]},"observed_context":{"signature":{"product_name":"Cindy","model_name":"gpt-5"}}}' | ./ldvh call create-fact-object
```

**错误响应**：
```
outcome=rejected
gaps=["urls[0].ref: urls.ref 必须是绝对 HTTP(S) URL"]
```

**对比**：将 ref 改为 https://example.com/spec 后创建成功。

**修复方向**：此为设计约束（urls 只接受外部 HTTP(S) 资源），非 bug。但可在 prepare-fact-object-draft 的 field_contracts 中更明确地标注 urls[].ref 约束: 必须是绝对 HTTP(S) URL，当前只有 urls 的 definition_ref 没有直接展示 ref 约束。

#### F9：read-specification-content 信封字段错位

**复现命令**（错误位置）：
```bash
printf '%s' '{"arguments":{"selections":[{"responsibility_key":"ldvh-root","heading_path":["8. 系统级运行架构"]}],"requested_disclosure":"L3"}}' | ./ldvh call read-specification-content
```

**错误响应**：
```
outcome=invalid_request
gaps=["arguments 包含未知字段: requested_disclosure",
      "requested_disclosure 必填且只允许 L3 或 L4"]
diagnostics=[["arguments 包含未知字段: requested_disclosure",
              "requested_disclosure 必填且只允许 L3 或 L4"]]
```

**正确命令**：
```bash
printf '%s' '{"arguments":{"selections":[{"responsibility_key":"ldvh-root","heading_path":["8. 系统级运行架构"]}]},"requested_disclosure":"L3"}' | ./ldvh call read-specification-content
```

**响应**：`outcome=ok`

**修复方向**：requested_disclosure 是顶层合作字段（与 arguments 并列），不是 arguments 内的字段。此约束在 04 规范和 04.Att.01 中有定义，但 capabilities 的 --example 输出中可能不易直观发现。可在 read-specification-content 的 capability 描述中增加"请求信封示例"或提供更清晰的参数说明。退出码为 0 加剧了误判风险——调用方只检查 exit code 会误认为成功。

#### F10：capabilities 超大单行 JSON

**复现命令**：
```bash
./ldvh capabilities </dev/null
```

**现象**：返回完整 JSON 为单行，约 50KB+，包含大量 sources/qualification gaps 和 evidence 链路。在输出上限受限的环境中会被截断，尾部能力项不可见。

**修复方向**：为 capabilities 输出增加 --format=pretty 或 --compact 选项，或按 operation_key 分组输出。当前输出完整性不受影响，但人工浏览成本高。

### 发现二：4 项共性摩擦贯穿所有 5 类事实对象

以下摩擦在至少 4 类事实对象中出现，应视为系统级问题：

1. **draft→create schema 不对齐（F1）**：`prepare-fact-object-draft` 返回的 result 包含 carrier/field_contracts/managed_fields 等上下文字段，但 `create-fact-object` 的 `draft_basis` 只接受 governed_project_id/fact_type_key/schema_fingerprint/worktree_fingerprint 四项。

2. **托管字段扩散（F5）**：所有类型的 `update-fact-object` 要求 after 中不得包含 object_uid/object_id/fact_type_key/created_at/updated_at，但 `read-fact-objects` 返回的精确对象包含这些字段。

3. **全库审计 partial（F11）**：当前工作树有 3 个既有 invalid 对象，导致所有写后独立完整性检查均为 partial。

4. **首条 change_log 隐式要求（F2）**：所有类型在创建时强制要求 change_log 首条流水，但 `prepare-fact-object-draft` 的 field_contracts 中 change_log 标注为 conditional，无创建提示。

### 发现三：WorkCase 是全生命周期操作最复杂的类型

WorkCase 的测试覆盖了 6 个步骤，暴露了独有的操作摩擦：
- item_event 与 fact_object 的 XOR 约束
- complete-work-item 的最后一项拒绝
- Gate 2 关闭的专属入口

### 发现四：全库审计 partial 的真实原因

扫描 290 个对象，3 个既有无效对象：
- Spark `01KZXN5TXNEKMANG1WTFBKT5FW`：未登记签名字段
- Study（2 个）：缺失关系目标

### 发现五：promote 的 status-only 约束与 write-entry 的 change_log 追加存在规范冲突

Pitfall 规范要求 promote 前后解析值逐值相同，但通用 `update-fact-object` 写入口会追加 change_log 条目，导致对象正文客观上发生变化。

### 发现六：签名未继承——Worker 写入的署名全部错误

6 路 Worker 产生的测试对象，其 `change_log[].signature` 中的 `product_name` 和 `model_name` 全部偏离了当前会话的正确值：

| 对象 | 实际写入 | 应为 |
|---|---|---|
| Spark | product_name=Cindy, model_name=glm-5.2 | product_name=Cindy, model_name=gpt-5 |
| ADR | product_name=ldvh, model_name=glm-5.2 | product_name=Cindy, model_name=gpt-5 |
| Pitfall 主/副 | product_name=LDVH CLI, model_name=glm-5.2 | product_name=Cindy, model_name=gpt-5 |
| Study | product_name=Cindy, model_name=glm-5.2 | product_name=Cindy, model_name=gpt-5 |
| WorkCase | product_name=LDVH, model_name=test | product_name=Cindy, model_name=gpt-5 |

**根因**：Worker 作为独立 AI 会话，没有从 Lead（主控）继承签名的能力。每个 Worker 自行猜测 `product_name` 和 `model_name`，结果全部错误：
- `product_name` 错误使用了 `ldvh`/`LDVH`/`LDVH CLI`（违反 `signature_guard.py` 的"署名 product_name 不得使用当前管辖实例名"规则）
- `model_name` 错误使用了 Worker 自己的模型名（`glm-5.2`）或 Code 归一值（`test`），而非 Lead 当前会话的实际模型（`gpt-5`）

**对后续项目工作的直接影响**：这是一个系统级问题。Worker（或更广义的 Subagent）在写入 LDVH 事实对象时，必须继承主控会话的签名上下文，否则产出的事实对象署名污染整个工作树。在 LDVH 的签名契约下，`product_name` 和 `model_name` 是刚性必填字段，Worker 猜错后无法通过后续的提交签名验证。

**处理办法**：Subagent 如果写入，需要继承主控的信息——Lead 在分派 Worker 时应显式传递当前会话签名（`product_name=Cindy, model_name=gpt-5`），或创建机制自动继承主控签名上下文。

## 建议


1. **裁剪 prepare-fact-object-draft 输出或增加 create 映射提示**：
   - 目标对象类型：规范 specs/31 和 specs/05
   - 预期目标：prepare 结果中明确标注哪些字段可通过 draft_basis 透传
   - 验收条件：新执行者首次操作时不会被 invalid_request 拒绝
   - 创建/更新判断：当 F1 摩擦再次出现时执行

2. **清理 3 个既有 invalid 对象以恢复全库审计 complete**：
   - 目标对象类型：Spark `01KZXN5TXNEKMANG1WTFBKT5FW` 和 2 个 Study
   - 预期目标：使 check-fact-integrity 返回 status=complete
   - 验收条件：全库扫描 290 个对象，0 个 invalid
   - 创建/更新判断：当需要全库完整声明时执行

3. **为 Pitfall promote 增加专用操作或澄清规范冲突**：
   - 目标对象类型：specs/23 和 specs/32
   - 预期目标：明确 promote 时 change_log 追加是否视为正文变化
   - 验收条件：AI 执行者能无歧义地执行 promote
   - 创建/更新判断：当 promote 摩擦再次被记录时执行

4. **将本摩擦汇总报告作为行为清单的配套参考**：
   - 目标对象类型：Study（study-01M09ZNYA8F3K8FW1VBDYTYXCB）
   - 预期目标：行为清单引用本报告 object_uid
   - 验收条件：双向引用建立
   - 创建/更新判断：当行为清单被引用时同步更新

6. **Worker/Subagent 必须继承主控签名上下文**：
   - 目标对象类型：Worker 创建机制（Orca Worker 或 Subagent 管理）
   - 预期目标：Worker 在写入 LDVH 事实对象时，`change_log[].signature` 中的 `product_name` 和 `model_name` 与主控会话一致，而非自行猜测
   - 验收条件：Worker 创建的事实对象，其 signature 可通过提交签名验证，不因签名错误被拒
   - 创建/更新判断：当创建新的 Worker 或 Subagent 执行 LDVH 写入任务时，检查签名是否继承
5. **在仓库中解除 docs/ 的 gitignore 以纳入摩擦记录**：
   - 目标对象类型：`.gitignore` 文件
   - 预期目标：friction 文件不被 gitignore 忽略
   - 验收条件：git status 显示摩擦记录可追踪
   - 创建/更新判断：当需要提交时执行

## 后续分流

1. **行为清单更新**：当本报告发现需要反映到行为清单时增加引用。判断标准：使用者因本报告所述摩擦卡住时。

2. **规范修订**：当 F1、F5、F6 被确认需要规范层面修复时，创建 Spark 或 WorkCase 推进。判断标准：摩擦导致重复出错时。

3. **既有 invalid 对象清理**：当清理 3 个对象的时机成熟时创建 WorkCase。判断标准：需要全库完整声明时。

4. **Pitfall 沉淀**：当 F6 的规范冲突无法立即修复时创建 Pitfall。判断标准：规范修订无法在单次迭代中完成时。

6. **签名继承机制改进**：当 Worker/Subagent 签名错误再次出现时，推进 Worker 创建机制的签名自动继承能力。判断标准：新 Worker 创建时未自动携带主控签名。
5. **定时复核**：当 specs/20~24、31、32、34 或 CLI 实现变化时复核本报告。判断标准：规范 commit 变化 + 状态闭集/专属操作变化时。
