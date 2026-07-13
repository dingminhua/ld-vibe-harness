# V4 WorkCase 类型封闭记录

> 记录日期：2026-07-13。本文只记录 WorkCase 类型 Gate 的审核和验证结果，不取得类型定义权。WorkCase 当前规则以 `specs/21-WorkCase-工作项.md`、`specs/05-事实模型基础规范.md` 和统一登记附件为准。

## 1. 结论

WorkCase 的对象语义、粒度、准入、Schema、状态、目标、范围、成功标准、来源、证据、关系、验证、关闭、Human Gate 与 Stop Conditions 已完成定义、机械检查和两路独立复核。复核提出的 P1/P2 已全部修正，WorkCase Gate 关闭，可以按严格串行顺序开始 ADR。

本结论只证明类型来源与当前机械范围成立，不证明任何 WorkCase 对象、V3 迁移、事实读取或写入、Helper、Code、tests、行动模板、Web 或环境接入能力已经实现。

## 2. 主要收敛

1. WorkCase 只承载一个已经形成明确目标、范围与成功标准，并需要跨行动或会话保持当前推进与终态判断的独立工作责任；当前即可完成的小任务、Spark 式模糊问题和运行计划不准入。
2. 状态收敛为 `open / blocked / closed`；新建初态只能是 open 或有具体可证阻塞的 blocked，closed 不等于成功、已提交或下游完成。
3. V3 整个 `orchestration`、执行项、七段 Agent/Human 流程状态、review receipt、请求时间、revision history 和空占位退出事实 Schema；行动步骤归当次计划或行动模板。
4. 新增 `goal`、`scope`、`success_criteria`、`validation_summary`、`blocking_summary`、`closure_outcome` 六个 WorkCase 专属字段；来源、证据和关系复用公共入口。
5. `current-summary`、`priority`、`disposition-summary`、`closed-at` 从 Spark 类型定义提升为 Spark 与 WorkCase 的共享 foundation 字段，唯一共同定义移入 05.Att.01；Spark evolution 保持 Spark 专属。
6. WorkCase 关系限定为 `depends-on`、`routed-to`、`supersedes`，分别定义 source/target 状态、基数、反向派生、缺失和循环边界；superseded 关闭只由旧对象 outbound routed-to 承担承接权威。

## 3. 独立复核与修正

规范复核覆盖对象价值、准入、Spark 分界、行动模板边界、状态、初态、关闭、关系、类型退出和 V1–V8。字段与 Code 复核扫描 24 个 V3 WorkCase、122 个执行项及当前统一登记，检查字段复用、提升、定义闭包和失败隔离。

终审实际拦截并修正了：summary 与 validation_summary 职责冲突、初态缺失、关系目标承接能力与基数/环边界不足、superseded 方向含混、closed_at 下界丢失、P0–P3 含义丢失、类型退出遗漏 closed 对象、V7 名称漂移，以及有限共享字段 promotion 缺少唯一机械来源。两路复核最终均确认没有剩余 P1/P2。

执行项是否进入 Schema 出现过审议分歧。最终依据 06 的行动边界、V3 双层状态漂移和最小事实原则，选择不进入 WorkCase；未来只有出现稳定独立消费证据并重新完成统一字段准入时才能重审。

## 4. 验证

tests 数字记录 WorkCase Gate 关闭当时结果；仓库文档、事实类型与字段数量是五类型全局归并前的当前回查结果。

- 全量 tests：333 passed；
- Ruff lint：passed；
- Ruff format check：passed；
- `git diff --check`：passed；
- 当前仓库检查：18 个当前文档、0 issues、repository complete；
- 字段治理检查：`fact_types = [spark, workcase, adr, pitfall, study]`、5 个结构、46 个字段、0 issues；
- promotion 负向检查：有限共享字段缺失提升来源或存在多个提升来源均被阻断。
