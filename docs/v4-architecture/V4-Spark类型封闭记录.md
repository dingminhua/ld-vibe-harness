# V4 Spark 类型封闭记录

> 记录日期：2026-07-13。本文只记录 Spark 类型 Gate 的审核和验证结果，不取得类型定义权。Spark 当前规则以 `specs/20-Spark-火花.md`、`specs/05-事实模型基础规范.md` 和统一登记附件为准。

## 1. 结论

Spark 的对象语义、粒度、准入、Schema、状态、来源、证据、关系、处置、验证、Human Gate 与 Stop Conditions 已经完成定义、机械检查和两路独立复核。没有剩余 P1/P2；Spark Gate 关闭，可以按严格串行顺序开始 WorkCase。

本结论只证明类型来源与当前机械范围成立，不证明任何 Spark 对象、V3 迁移、事实读取或写入、Helper、Code、tests、Web 或环境接入能力已经实现。

## 2. 主要收敛

1. Spark 只承载跨行动或会话仍有保留价值、但尚未形成确定承接位置的单一信息需求、发现、问题或缺口；不是任务池、报告、决策草稿或兜底垃圾箱。
2. 状态使用 `open / routed / discarded`；`routed` 只表示入口已被稳定位置完整承接，不表示下游工作完成。
3. V3 的 `source/source_detail/input_refs` 归一为 `source_refs/evidence_refs`，全部 `related_*` 和对象型 `resolved_to` 归一为公共 `relations`；没有为 Spark 污染共享 `source-ref` 结构。
4. Spark 首次准入一个 `spark-evolution-entry` 结构和七个字段；WorkCase 准入后，`current-summary`、`priority`、`disposition-summary`、`closed-at` 已按同义需求提升为跨类型共享字段，evolution 结构与三个成员仍为 Spark 专属；`priority` 只在 open 出现，evolution 保持 1–8 项并在每次更新时删除已被当前摘要吸收的条目。
5. 非 Spark 事实对象承接使用 `routed-to`；Spark 接替只由新 open Spark 单向 `supersedes` 旧终态；普通文件由 `evidence_refs` 定位，避免双边权威和关系二环。
6. `facts/sparks/<object_id>.yaml` 是一文件一对象的当前允许位置；V3 路径、实例状态和空值模板不自动继承。

## 3. 独立复核与修正

规范治理复核主动检查对象边界、状态、Study 与普通文件承接、evolution、来源结构、关系目标与循环、净价值、Human Gate 和 Stop Conditions。Code/字段复核检查 39 个 V3 Spark、12 个代表样本、字段分布、统一登记闭包、非全局结构成员准入和失败隔离。

终审实际拦截并修正了：终态 priority 语义矛盾、source-context 对共享结构的污染、关系目标/跨项目/缺失/自指/循环缺口、Spark 接替双向二环、evolution 无持续压缩规则，以及类型结构成员缺少机械准入覆盖。两路复核最终均确认没有剩余 P1/P2。

## 4. 验证

tests 数字记录 Spark Gate 关闭当时结果；仓库文档、事实类型与字段数量是五类型全局归并前的当前回查结果。

- 全量 tests：332 passed；
- Ruff lint：passed；
- Ruff format check：passed；
- `git diff --check`：passed；
- 当前仓库检查：18 个当前文档、0 issues、repository complete；
- 字段治理检查：`fact_types = [spark, workcase, adr, pitfall, study]`、5 个结构、46 个字段、0 issues；有限共享字段另有单一 `promote` 来源检查。
