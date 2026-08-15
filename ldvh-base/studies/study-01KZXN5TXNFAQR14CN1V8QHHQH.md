---
title: v2 局部编辑运行证据的可回放性与诊断边界评估
status: retired
report_kind: technical_assessment
input_refs:
- kind: fact-objects
  locator: ldvh-base/workcases/workcase-0103.yaml、ldvh-base/workcases/workcase-0104.yaml、ldvh-base/sparks/spark-0045.yaml
  version: 928bd160aadb737a5400f53950f9a4f85b782a9d
  observed_at: '2026-08-13T08:21:10Z'
- kind: code
  locator: code/ldvh/testing/trial_measurement.py、code/ldvh/testing/local_edit_evidence.py、code/ldvh/testing/local_edit_evidence_runner.py；以 HEAD 加当前 dirty diff 定位未提交实现
  version: 928bd160aadb737a5400f53950f9a4f85b782a9d
  observed_at: '2026-08-13T08:21:10Z'
- kind: test
  locator: code/tests/testing/test_local_edit_evidence.py 及相关 testing/helper 回归范围；以 HEAD 加当前 dirty diff 定位未提交测试
  version: 928bd160aadb737a5400f53950f9a4f85b782a9d
  observed_at: '2026-08-13T08:21:10Z'
- kind: helper-call-results
  locator: workcase-0104 唯一 v2 六轨迹试跑的聚合结果与独立结果复核；原始 records 已按关闭交接安全删除
  observed_at: '2026-08-13T08:21:10Z'
- kind: working-tree-statistics
  locator: 修复后定向 32 tests、相关回归 213 tests、Ruff 与 git diff --check 的当次结果
  observed_at: '2026-08-13T08:21:10Z'
relations:
- relation_key: inspired-by
  target:
    object_uid: 019ffb52-ebb5-748a-b247-38b1cc5795f9
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-74ea-a2f9-9f309e85d013
research_question: 在 workcase-0103 形成 v2 证据信封实现、workcase-0104 完成一次受限六轨迹试跑后，这套记录与四态投影实际能够证明哪些可回放、隐私和诊断边界，哪些执行健康、真实中断耐久或产品价值结论仍不能成立？
abstract: 本技术评估汇总一次受限 v2 六轨迹试跑及其独立复核：T1/T2 投影 observed、T3a failed、T3b timeout、T4a/T4b inconclusive，真实 Helper 调用 4 次、唯一 stale repair 1 次、响应 45977 bytes、观测耗时 4541 ms。结果支持 v2 record layer 在闭集元数据、隐私边界、原子落盘/回读和损坏 fail-closed 上形成可复读证据，但不证明 Helper 正确、事实写入、执行健康、真实跨进程中断耐久、tamper 注入原子性或产品效益。试跑暴露的旧 WorkCase 前缀硬编码和摘要根路径误用已在关闭后修复并通过 32 项定向与 213 项相关回归；未追加真实 trial。
research_intent: spark-0045 需要判断输入、事件、外部状态和验证证据能否共同形成不冒充事实源的可回放观察。本报告把两次 WorkCase 的实现、一次受限试跑、独立复核与关闭后修复收束成可独立阅读的技术评估，避免后续把事件存在、测试通过或临时记录持久化误写为执行健康、正确性或产品价值已经成立。
recommendation_summary: 保留 v2 信封与四态投影作为受限诊断基础，并使用通用可参数化 run_suite 与不含原始 record 的 summary_payload。当前不创建新 WorkCase、不追加真实 trial，也不产品化为长期遥测；只有出现真实跨进程恢复需求、操作者定位收益样本或统一事件消费方时，才据相应单一问题创建或更新 WorkCase/ADR，并继续由 spark-0045 承接尚未成立的健康判断。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T08:25:56.260249Z'
  summary: 汇总 workcase-0103/0104 的 v2 局部编辑证据实现、受限试跑、独立复核、关闭后 runner 修复及其可证明与未验证边界。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:35.664002Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- signature:
    product_name: Cindy
    model_name: chatgpt/gpt-5.6-luna
    agent_runtime_name: claude-code
  at: '2026-08-15T19:08:19.740703Z'
  summary: v2 局部编辑运行证据边界评估已完成；当前不追加 trial、不产品化长期遥测，未来仅在明确触发条件出现时重开专项.
disposition_summary: v2 局部编辑运行证据边界评估已完成；当前不追加 trial、不产品化长期遥测，未来仅在明确触发条件出现时重开专项.
object_uid: 019ffb52-ebb5-7aaf-8091-950ed178c6f1
object_id: study-01KZXN5TXNFAQR14CN1V8QHHQH
fact_type_key: study
created_at: '2026-08-13T08:25:56.260249Z'
updated_at: '2026-08-15T19:08:19.740703Z'
---

## 研究问题

### 项目为什么需要这份评估

spark-0045 关注输入上下文、行为事件、外部状态和验证证据能否形成可回放判断，同时要求事件流不成为第二事实源。workcase-0103 建立 v2 信封、runner 与四态投影；workcase-0104 只执行一次冻结的六轨迹套件。本报告判断这组实现与一次运行实际证明了什么，以及哪些更强结论仍没有证据。

### 本报告回答的问题

在闭集、隐私受限的 v2 record layer 中，正常、stale 修复、真实拒绝、synthetic timeout、synthetic interruption 和 synthetic integrity tamper 六条轨迹能否被稳定落盘、回读和投影；这些结果对 spark-0045 的诊断方向有什么直接影响，又不能被解释为什么。

## 输入与边界

### 实际输入与方法

本评估回读 workcase-0103、workcase-0104 与 spark-0045，检查当前 `trial_measurement.py`、`local_edit_evidence.py`、`local_edit_evidence_runner.py` 和对应测试。workcase-0104 的唯一实际套件包含六条 v2 轨迹：T1/T2/T3a 来自 real_helper，T3b/T4a/T4b 来自 synthetic_harness；真实 Helper 调用上限为 4，T2 只允许一次 repair。原始 records 在关闭交接时经身份、realpath、lstat 和权限核验后安全删除，本报告只使用 WorkCase 中的聚合结果与独立复核。

关闭后仅修复两个执行入口问题：`run_suite()` 的旧 `wc0103` 临时根前缀改为通用且可参数化；新增 `summary_payload()`，通过 `SafeTrialTempRoot.root` 输出根路径、恢复投影和聚合摘要，不携带原始 records。修复验证使用测试替身，没有重跑 Helper 或 synthetic trial。

### 观察时点与未覆盖

观察绑定 2026-08-13、HEAD `928bd160aadb737a5400f53950f9a4f85b782a9d` 加当前 dirty diff；未提交内容不能仅靠该 commit 重建。未验证真实宿主硬崩溃或 worker 中断后的跨进程 durability、tamper 注入动作自身的原子性、完整 Prompt 捕获、长期存储、生产遥测、告警、A/B 效益、操作者实际定位收益或产品健康。T3b/T4a/T4b 的 synthetic 结果只验证 recorder/projector 负向边界，不构成 Helper 行为证据。

## 关键发现

### 发现一：四态投影能保留边界差异，但不是健康结论

项目观察：唯一套件的投影为 T1/T2 observed、T3a failed、T3b timeout、T4a/T4b inconclusive；真实调用计数为 1/2/1/0/0/0，T2 repair=1，总响应 45977 bytes，观测耗时 4541 ms。v2 对缺失、损坏、顺序、身份、版本、input unavailable 和 verification 异常优先投影 inconclusive。

项目影响：这证明四态投影可以区分“记录到正常协议终态”“真实拒绝”“合成 deadline”和“证据不足/损坏”，并避免把 partial 或 unavailable 当成功。它不证明 Helper 输出正确、事实已写入、任务完成、Human 验收或执行健康。对 spark-0045 的直接影响是保留小投影和证据优先级，不把 observed 改名为 healthy。

### 发现二：隐私受限信封足以支持协议复读，不需要保留正文

项目观察：六份 v2 envelope 使用闭集协议字段、稳定标识/fingerprint、长度、枚举、调用/repair 计数、fault provenance、deadline、external state 与 verification；根目录和 records 权限曾分别核对为 0700 与 0600。禁止 request/response/fact/candidate/prompt 正文、diff 与正文 hash，T4b 损坏回读不返回 record。

项目影响：后续可通过聚合指标和恢复投影复读协议发生了什么，而无需把事实正文或完整 Prompt 复制为第二事实源。该结论只覆盖当前 schema 与实际扫描范围；fingerprint 不证明被指纹内容正确或宿主完整交付。对当前项目无需新建对象；Study 本身保存方法、计数和限制即可。

### 发现三：耐久性证据只成立于 record layer

项目观察：SafeTrialTempRoot 的受限根、原子新文件写入、fsync、身份/realpath/lstat 检查、v2 readback 和损坏 fail-closed 有实现、测试与一次套件证据。T4a 的 recovered=false 是 projector 对 inconclusive 不返回 record；T4b 通过直接改写完整性值注入，只证明篡改检测与不返回 record。

项目影响：可以声明 record-layer 原子落盘、回读和损坏 fail-closed 已验证，不能声明真实进程中断后的耐久恢复或 tamper 注入自身原子。若未来出现跨进程恢复的真实消费需求，应以真实 kill/restart、所有权恢复和清理边界为单一验收问题；此前无需创建新 WorkCase。

### 发现四：一次端到端试跑同时检验了 runner 的交付可用性

项目观察：v2 public sequence 完成了四次真实调用与六份记录，但源码原始 `run_suite()` 当时仍硬编码旧 `wc0103` 前缀；首次参数化进程在全部记录持久化后又因摘要代码误用不存在的 `SafeTrialTempRoot.path` 抛出 AttributeError。这些缺陷没有改写既有 records，却说明协议实现通过不等于交付入口完整可用。

项目影响：关闭后将前缀改为通用可参数化值，并用正式 `summary_payload()` 固定无正文交还形状；32 项定向测试、213 项相关回归、Ruff 与 `git diff --check` 通过。没有重跑真实 trial，因此修复证明代码路径与回归成立，不把原套件改写为“原入口当时成功”。

## 建议

### 建议一：把 v2 作为受限诊断 primitive 保留

目标承载：继续由当前 Code/tests 和 spark-0045 承载，不创建新 WorkCase。预期目标是保持闭集信封、真实/synthetic provenance、四态投影、隐私禁止项和 fail-closed 优先级。验收条件是任何 schema、事件或 fault 变更仍通过闭集负例与相关回归，且摘要不携带原始 records。若只是维护当前实现且没有新的消费需求，继续无需对象化。

### 建议二：未来只在真实恢复需求出现时验证跨进程 durability

目标对象类型与创建判断：出现需要 worker/host 重启后恢复记录的真实流程、稳定复现样本和明确所有权/清理责任时，再创建单一 WorkCase。预期目标是验证 kill/restart 后的读取、身份绑定、残留处置和安全交还。验收条件必须包含真实跨进程中断，而不能用 T4a/T4b synthetic 投影替代；没有消费方或风险样本时不创建。

### 建议三：诊断价值扩大前先取得操作者使用证据

目标对象类型与创建判断：只有 Human 或执行者实际使用摘要定位失败，并能记录“是否帮助定位、是否触发重读/修复、误报/漏报/重复/乱序”的稳定样本时，更新 spark-0045 或创建边界单一的 WorkCase；需要长期决定统一事件契约、存储或告警时再创建 ADR。验收条件是收益声明绑定实际使用，不以事件存在、测试通过或 Web/告警入口存在代替。当前一次套件不足以证明产品效益。

## 后续分流

| 信号 | 应创建或更新的对象 | 继续无需对象化的条件 |
|---|---|---|
| v2 schema、事件或 fault 闭集发生实质变化 | 在已有实现维护无法无损承载时创建 WorkCase；需要长期兼容决定时创建 ADR | 仅局部修复且现有测试完整覆盖 |
| 出现真实 worker/host 中断恢复消费需求 | 创建只验证跨进程 durability 的 WorkCase | 没有真实消费方、复现样本或所有权边界 |
| 操作者使用摘要定位问题并形成稳定收益/误报样本 | 更新 spark-0045；目标和验收可冻结时创建 WorkCase | 只有合成轨迹、单次演示或主观预期 |
| 拟建设长期记录、统一事件平台、Web 健康页或告警 | 先由 ADR 决定权威、隐私、保留期与成本，再由 WorkCase 实施 | v2 仍只作为受限测试 primitive，暂无产品消费方 |
| 当前试跑与修复结论 | 由本 Study 提供方法、计数、影响与限制入口 | 不更新既有 WorkCase，不追加 trial，不创建新 WorkCase |
