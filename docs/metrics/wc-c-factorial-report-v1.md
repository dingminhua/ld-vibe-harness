# WC-C Phase 1 / Phase 2 因子对照与残差判定

## 结论摘要

本报告按 `docs/metrics/wc-c-factorial-protocol-v1.json` 的冻结设计，完成了一个固定模型、固定任务、2×2 因子 replay 对照：

- Phase 1 因子：legacy stdin/full-response CLI vs `--request` + `--example` + `--fields`；
- Phase 2 因子：完整 `fact_object` request 构造 vs strict `item_event` request 构造；
- 四个 cell 各 10 个 valid session，共 40 个 valid records；
- Phase 1 与 Phase 2 各形成 20 对 treatment/control replay pairs；
- 40 个 primary attempts 中 3 个没有形成 structured output，按预注册的 `technical_launch_failure` 原因保留 exclusion ledger，并以 attempts 41–43 替换；总 attempts=43，未超过 48 上限；
- 40 个纳入会话全部是 `gpt-5.6-sol`、structurally `comparable`，实际 state-changing Helper call 为 0。

**Phase 1：** 三个机械验收组件在各自声明的观察边界内成立，但不能解释为“所有交互成本下降”。`--example`/`--fields` treatment 的 invalid-request 与 field-guess 结果更好；`--request` treatment 的 Python heredoc 为 0，但 legacy control 同样为 0，因此该组件只有受任务约束的零值，没有实验主效应。与此同时，treatment 每会话 Helper command characters 平均增加 **151.1**（95% bootstrap CI **127.7–172.05**，exact sign-flip `p=1.9073e-6`），Helper direct round trips 不变。因此冻结 v1 残差判定为 **`significant`**。

**Phase 2：** `item_event` 将原始 request 平均从 **2555.35 bytes** 降至 **619.6 bytes**；paired difference 为 **-1935.75 bytes**（95% CI **-1945.6–-1926.25**，`p=1.9073e-6`），约减少 **75.8%**。但是 raw validity 是两组各 19/20，projected-after validity 为 full-object 18/20、item-event 19/20；当前 20-pair 样本没有形成有效率提升证据。它证明的是本 WorkCase strict event 的 request-construction friction 大幅下降，不证明 generic patch，也不证明 Helper round trips 已下降。

本实验最多支持本固定任务包的 **behavior-consistent** paired estimate。它不提供 host-received 观察，也不把结果提升为广义产品 causal-effect。`significant` 仅能成为后续独立 09 治理议题的输入；本 WorkCase 没有授权、创建或实现 MCP / Phase 3。

## 1. 冻结身份与方法

| 项 | 值 |
|---|---|
| Protocol SHA-256 | `f651d1ad1053fcf162efbe68fd3cbf52db8f2d7c47bbe1d017dc71d2710455cd` |
| Task package SHA-256 | `ef338f11e5f32b42320020967c805a03cbdd8ab9fdf708238634f75a8232b7b6` |
| Result artifact SHA-256 | `a2228442abd3f7cece65413d21548d0e6a5824937a5c788f492bab8b136930d2` |
| Retained records SHA-256 | `3193838af32f52015f191de01b7713d9ee3192a0d114bf73a59cc5d19ad1c526` |
| Fixed model | `gpt-5.6-sol` |
| Pairing | `replay`，同 replicate、同另一因子 stratum |
| Uncertainty | deterministic bootstrap percentile 95% CI；exact complete sign-flip enumeration |
| Historical 65-session baseline | 只作 contextual frozen reference，不作本实验 control |

Contemporaneous legacy condition 是本实验的“before/control”操作形态；它不是代码回滚。Phase 1 主效应在两个 Phase 2 strata 内配对后等权聚合；Phase 2 主效应同理。报告同时检查 difference-in-differences interaction，避免把另一因子作用混入主效应。

## 2. 样本、替换与无写入边界

- primary attempts：40；
- technical replacements：3；
- total attempts：43；
- valid retained records：40；
- cell balance：`legacy-full=10`、`legacy-event=10`、`new-full=10`、`new-event=10`；
- Phase 1：20 control + 20 treatment；
- Phase 2：20 control + 20 treatment；
- session comparability：40/40 `comparable`；
- model identity：40/40 `gpt-5.6-sol`；
- state-changing Helper calls：0。

被替换的 primary ordinals 是 9、20、25。三者的 session carrier 本身 structurally comparable，但 workflow 没有取得 structured output；它们以 hashed session identity 和闭集原因保留在 results ledger 中。替换与任何行为结果无关。

两个 legacy trials 的 read-only task 返回 `invalid_request`，以及三个 replacement raw synthetic requests 的构造错误，都作为**行为结果**保留，没有被 exclusion 或再次替换。没有根据好坏结果停止、重跑或调 cell。

## 3. Phase 1 CLI 对照

### 3.1 Manipulation check

- treatment 中 `--request`、`--example`、`--fields` 各出现 20 次；
- control 中三项各出现 0 次；
- treatment 没有 legacy stdin call；control 使用 legacy stdin；
- treatment/control 的 Python heredoc 均为 0。

因此 condition manipulation 成立，但 P1-1 heredoc 指标被固定任务结构约束为两组均 0；不能把历史基线中的 155 次 heredoc 当成本次 contemporaneous causal control。

### 3.2 机械验收组件

| 组件 | Control | Treatment | Paired estimate（treatment-control） | 判断 |
|---|---:|---:|---|---|
| Python heredoc | 0 | 0 | mean 0；CI 0–0；p=1 | `satisfied_with_zero_contrast`；structurally constrained |
| `invalid_request` hits | 22 | 0 | mean -1.1/session；CI -1.25–-1.0；p=1.9073e-6 | satisfied；behavior-consistent |
| field-guess errors | 2 | 0 | mean -0.1/session；CI -0.25–0；p=0.5 | treatment 达到 0；样本未证明显著率差 |

Control 的 22 个 invalid hits 中，20 个来自 legacy `capabilities <operation>` 形态在当前 CLI 上不能形成合法请求，另 2 个来自 read-only call 构造错误。这个结果量化了当前骨架现取入口的机械价值，但只适用于该固定 task prompt。

### 3.3 成本与结构残差

| 指标 | Paired mean difference | 95% CI | exact p | 解释 |
|---|---:|---:|---:|---|
| Helper direct calls | 0.0 | 0.0–0.0 | 1.0 | round trips 未下降 |
| Helper command chars | +151.1 | +127.7–+172.05 | 1.9073e-6 | treatment 明显增加 |
| All bash command chars | +168.0 | +147.9–+182.9 | 1.9073e-6 | treatment 明显增加 |
| Bash calls | +0.5 | +0.25–+0.75 | 0.00635 | temp request-file handling 增加 shell action |
| Share of bash | -0.1667 | -0.25–-0.0833 | 0.00635 | 分母被额外 bash actions 改变，不能单独解释为总摩擦下降 |
| Output tokens | +69.45 | +54.1–+83.9 | 3.8147e-6 | treatment 增加 |
| Cache-read tokens | +3865.6 | +460.8–+7193.6 | 0.0471 | raw token count 增加；受 session usage 影响 |
| Cache amplification proxy | +2.559 | -1.919–+7.229 | 0.3037 | inconclusive |

Helper command-character interaction没有显著证据：

- full-object stratum：+160.1（CI +131.1–+190.3）；
- item-event stratum：+142.1（CI +107.8–+166.6）；
- difference-in-differences：-18.0（CI -77.2–+31.0，p=0.602）。

因此 command-character 残差没有被 Phase 2 condition 解释掉。该 proxy 不是 tokenizer 直接测量；它只表示 shell command surface 变长。

### 3.4 Phase 1 residual judgment

冻结 `phase1-comparison/v1` 的 residual candidate 为：

```text
significant
```

理由：三个机械 acceptance components 在其观察边界内成立，同时至少一个结构性指标显著劣于预期——Helper command chars 增加 151.1/session，CI 完全高于 0，exact p 远小于 0.05；direct calls 又完全没有下降。这个判断是“固定任务的结构性残差仍显著”，不是“Phase 1 无效”，也不是 MCP 已获批准。

## 4. Phase 2 WorkCase request-construction 对照

### 4.1 Request size

| 条件 | n | Mean raw bytes | Raw valid | Projected-after valid |
|---|---:|---:|---:|---:|
| Full `fact_object` | 20 | 2555.35 | 19/20 | 18/20 |
| Strict `item_event` | 20 | 619.6 | 19/20 | 19/20 |

Paired `item_event - full_object`：

- raw request bytes：mean **-1935.75**；median -1935；95% CI -1945.6–-1926.25；p=1.9073e-6；
- raw validity：mean 0.0；95% CI -0.15–+0.15；p=1.0；
- projected-after validity：mean +0.05；95% CI -0.10–+0.20；p=1.0。

### 4.2 Raw-before-projection 边界

Scorer 对 worker 返回的原始 request 先做 common/update parser 检查，再投影并与冻结 gold after 比较；不 repair、不 rename、不补 event key、不替换 signature。

三个 replacement 的构造失败说明这个区分有实际意义：

- 一个 full-object request 使用未授权的 `alternative` key 并夹带 managed fields；
- 一个 event request 把 `event_key` 写成 `event_at`；
- 一个 full-object request 的追加 `change_log.signature` 是 `null` 而不是三键 object，因此 raw parser 可接受 alternative，但完整 after 不等于 gold/不满足完整边界。

这些失败均进入统计，没有被 scorer 修复。结果说明 strict event 的主要确定性优势是 payload 大幅缩小；当前样本没有证明 raw-validity 或 final-after-validity 的显著提升。

### 4.3 不支持的外推

本实验不支持以下说法：

- strict event 已减少 Helper read/update round trips；
- WorkCase event 可以泛化为任意事实对象 generic patch；
- `prepare-update`、MCP 或新接入层已经必要或已获授权；
- synthetic request 结果等同于真实并发写入、CAS replacement boundary 或 host receive。

WC-B 的真实 self-hosting evidence 已覆盖实际写路径；本 WC 只比较 request construction friction，保持两项责任分离。

## 5. 证据等级与因果措辞

| 等级 | 本次状态 |
|---|---|
| `ldvh-prepared` | 已验证：task/protocol/condition/scorer identities 已冻结并指纹绑定 |
| `harness-delivered` | 已验证：DSH structural events、tool pairing、model 与 usage aggregates 可观察 |
| `host-received` | unavailable |
| `behavior-consistent` | 40-session balanced fixed-model replay 支持 |
| `causal-effect` | 不建立广义产品 causal-effect；只报告预注册 task-package paired estimate |

Historical 65-session baseline 仍是背景证据：它提供真实工作分布与原始问题规模，但不是本次实验 control。把 historical heterogeneous sessions 与 contemporaneous fixed-task sessions 混算，会破坏 identity/comparability，因此没有这样做。

## 6. Privacy 与保留范围

`wc-c-factorial-results-v1.json` 只保留 protocol 列出的 closed schema：hashed session identity、identity hashes、event type counts、Helper/bash aggregates、token aggregates、raw-request hash/bytes、score codes、comparability 与 exclusion code。

仓库产物不保留：

- raw prompt；
- assistant prose；
- tool-result body；
- full command；
- raw request body；
- session path 或明文 session ID；
- unrelated session metadata。

Results artifact 的 privacy/schema test 逐 record 检查字段闭集，并递归检查 denylist key；40 条 record 均通过。

## 7. 验证

形成报告前已取得：

- protocol validator：0 problems；40 assignments；10 per cell；
- task package/current/gold snapshot/transition：mechanically valid；
- direct scorer/results tests：12 passed；
- adjacent WorkCase item-event/request/session/evidence tests：98 passed（结果 artifact 形成前版本）；
- full `code/tests`：2013 passed，15 skipped；
- focused Ruff：passed；
- final focused `git diff --check`：passed；
- results byte-for-byte regeneration：identical；
- baseline session/call SHA-256：与 frozen v1 完全一致；
- `ldvh check`：外层 outcome `ok`、result `passed`；保留 2 类既有 qualification/直接必要性 gap，不把它们表述为已证明；
- fact integrity：`complete`，256 objects，0 problems；
- records：40；`records_sha256=3193838af32f52015f191de01b7713d9ee3192a0d114bf73a59cc5d19ad1c526`；
- all retained identities：match；
- all retained session comparability：comparable；
- state-changing Helper calls：0。

独立 WorkCase result review 由全部 items terminal 后的 lifecycle phase 承接；它不属于实验 work item 本身。
