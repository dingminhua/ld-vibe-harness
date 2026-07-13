# V4 Pitfall 类型封闭记录

> 记录日期：2026-07-13。本文只记录 Pitfall 类型 Gate 的审核和验证结果，不取得类型定义权。Pitfall 当前规则以 `specs/23-Pitfall-踩坑经验.md`、`specs/05-事实模型基础规范.md` 和统一登记附件为准。

## 1. 结论

Pitfall 的对象语义、粒度、准入、Schema、状态、来源、证据、替代关系、变更、验证、Human Gate 与 Stop Conditions 已完成定义、机械检查和两路独立复核。复核发现的重复字段准入 P2 已修正，两路终审均确认没有剩余 P1/P2；Pitfall Gate 关闭，可以按严格串行顺序开始 Study。

本结论只证明类型来源与当前机械范围成立。commit `3d028ec2` 历史快照包含两个 V3 Pitfall 实例；两者都表达 symptoms、trigger conditions、root cause、resolution、verification、avoidance 和 applicability，只能证明这些核心信息需求存在，不能证明 tags、archived、旧引用数组、内容、外部协议、字段或状态仍然当前；任何 Pitfall 对象迁移、事实读取或写入、Helper、行动模板、Web 或环境接入能力也尚未因此实现。

## 2. 主要收敛

1. Pitfall 是已经实际发生、查明、解决、验证且仍有迁移复用价值的单一失败机制与规避经验，不是规则、任务、决定、研究正文、调试日志或操作手册。
2. 状态使用 `active / superseded / retired`；吸收到规范、Code 或行动模板不会自动使 Pitfall 终态，经验也不取得规则权威或行动授权。
3. 复用公共身份、来源、证据、关系和终态字段；把 `applicability` 从 ADR 专属字段提升为 ADR/Pitfall 有限共享，把 `validation_summary` 从 WorkCase 专属字段提升为 WorkCase/Pitfall 有限共享。
4. 新增 symptoms、trigger_conditions、root_cause、resolution、avoidance 五个 Pitfall 专属字段；分别限定触发后表现、触发前提、因果机制、已执行修复和未来经验复用，避免相互替代或退化为自由叙述。
5. 第一版关系只允许新 Pitfall 单向 supersedes 旧 Pitfall。建边时新对象 active、旧对象同时转 superseded；每个旧对象全生命周期最多一个直接替代源，全部边构成 DAG。
6. V3 两个实例依赖旧 shape 或可变化外部协议，且缺少 V4 来源、证据和重新验证闭包；它们只作为需求和反例输入，不能直接迁为 V4 active 对象。

## 3. 独立复核与修正

规范治理复核覆盖经验事实与规则、WorkCase、Spark、ADR 的边界，字段查重与提升，状态、关系、时间约束，以及两个 V3 实例的证据。字段与 Code 复核覆盖 18 条准入、18 条绑定、5 条专属定义、44 项统一登记和有限共享字段单一提升来源。

终审拦截了一个 P2：同一类型原可为同一个 `resulting_field_key` 保留多份形式合法的准入记录。修正后，同一类型内 `information_need` 与 `resulting_field_key` 分别唯一，每个绑定字段恰好只有一项准入结论；Code 已增加确定性拒绝和两条失败测试。两路终审最终均确认没有剩余 P1/P2。

## 4. 验证

tests 数字记录 Pitfall Gate 关闭当时结果；仓库文档、事实类型与字段数量是五类型全局归并前的当前回查结果。

- 全量 tests：335 passed；
- Ruff lint：passed；
- Ruff format check：passed；
- `git diff --check`：passed；
- 当前仓库检查：18 个当前文档、0 issues、repository complete；
- 字段治理检查：`fact_types = [spark, workcase, adr, pitfall, study]`、5 个结构、46 个字段、0 issues；
- 当前验证只覆盖规范与字段机械闭包，不包含 Pitfall 实例消费测试。
