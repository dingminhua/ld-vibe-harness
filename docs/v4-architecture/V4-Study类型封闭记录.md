# V4 Study 类型封闭记录

> 记录日期：2026-07-13。本文只记录 Study 类型 Gate 的审核和验证结果，不取得类型定义权。Study 当前规则以 `specs/24-Study-研究报告.md`、`specs/05-事实模型基础规范.md` 和统一登记附件为准。

## 1. 结论

Study 的对象语义、粒度、准入、Schema、Markdown 正文、状态、来源、证据、时效、替代关系、变更、验证、Human Gate 与 Stop Conditions 已完成定义、机械检查和两路独立复核。终审发现的重复 limitations 权威和来源 kind/时效机械契约两个 P2 已全部修正，两路终审均确认没有剩余 P1/P2；Study Gate 关闭，Spark、WorkCase、ADR、Pitfall、Study 五类型定义阶段完成，可以进入全局归并审核。

本结论只证明类型来源与当前机械范围成立。V3 17 个 Study 实例只证明报告信息需求存在，不证明其内容、产品能力、网页资料或状态仍然当前；任何 Study 对象迁移、事实读取或写入、正文 validator、Helper、行动模板、Web 或环境接入能力也尚未因此实现。

## 2. 主要收敛

1. Study 是一轮已经完成、可独立引用且具有跨行动稳定阅读价值的研究结果，不是搜索过程、研究任务、决定、规则、失败经验或当前外部事实证明。
2. 状态使用 `active / superseded / retired`；active 只在明示 applicability、来源版本、观察时点、validation_summary 和正文限制内表示当前研究入口，不证明外部事实最新。
3. 复用公共身份、来源、证据、关系和终态字段，以及已有共享 applicability 与 validation_summary；不复用 Spark/WorkCase 的 current-summary，也不产生第二个 promote 来源。
4. 只新增 research_question 和 abstract 两个 Study 专属字段。独立 limitations 字段因与 applicability、validation_summary、来源版本、摘要和正文重复而删除；详细限制唯一留在正文相应章节。
5. Markdown 正文固定六个唯一、顺序明确且非空的 H2；frontmatter 是稳定机器入口，正文只展开而不得改变或弱化其边界。
6. Study 引用限定七种 kind，固定 locator profile 与 version/observed_at 最低条件；全部引用必须带 observed_at 且不晚于 updated_at，临时绝对路径、缓存和不可恢复来源被拒绝。
7. 第一版关系只允许新 Study 单向 supersedes 旧 Study；只作整体替代，每个旧对象全生命周期最多一个直接替代源，全部边构成 DAG。
8. V3 17 个实例缺少结构化 version/observed_at，含无时区时间、临时绝对路径及大量空数组/null；全部只能逐个重新查重、重验证和准入，不能批量直接迁为 V4 active。

## 3. 独立复核与修正

规范治理复核覆盖研究报告与相邻类型及规则的边界、对象粒度、字段最小化、正文权威、状态、替代关系和 V3 证据。字段与 Code 复核统计 17 个实例、135 个网页引用、旧 validator、15 条准入、15 条绑定、2 条专属定义、46 项统一登记和有限共享字段单一提升来源。该历史统计以 commit `3d028ec2` 快照为准；17 个实例全部具备研究问题、输入边界、关键发现、建议和后续分流正文，但缺少 V4 来源版本、观察时点、适用边界与验证闭包，只能作为设计与反例证据，不取得 V4 实例当前性。

终审拦截并修正了两个 P2：第一，删除与多个已有入口及正文重复的 limitations 字段，避免同一限制需要多处同步；第二，把来源 version、observed_at 和临时 locator 的自然语言要求收敛为七种 kind 的固定矩阵、路径 profile、时间顺序和未来正反测试契约。两路终审最终均确认没有剩余 P1/P2。

## 4. 验证

tests 数字记录 Study Gate 关闭当时结果；仓库文档、事实类型与字段数量是五类型全局归并前的当前回查结果。

- 全量 tests：335 passed；
- Ruff lint：passed；
- Ruff format check：passed；
- `git diff --check`：passed；
- 当前仓库检查：18 个当前文档、0 issues、repository complete；
- 字段治理检查：`fact_types = [spark, workcase, adr, pitfall, study]`、5 个结构、46 个字段、0 issues；
- 当前验证只覆盖规范与字段机械闭包，不包含 Study 实例、Markdown 正文或来源引用对象消费测试。
