# V4 ADR 类型封闭记录

> 记录日期：2026-07-13。本文只记录 ADR 类型 Gate 的审核和验证结果，不取得类型定义权。ADR 当前规则以 `specs/22-ADR-决策.md`、`specs/05-事实模型基础规范.md` 和统一登记附件为准。

## 1. 结论

ADR 的对象语义、粒度、准入、Schema、状态、来源、证据、替代关系、变更、验证、Human Gate 与 Stop Conditions 已完成定义、机械检查和两路独立复核。复核提出的 P1/P2 已全部修正，ADR Gate 关闭，可以按严格串行顺序开始 Pitfall。

本结论只证明类型来源与当前机械范围成立。commit `3d028ec2` 历史快照中 V3 没有 ADR 实例，只有规范和 validator 草案；因此不能宣称真实 ADR 样本消费已经验证，也不能以历史快照补齐 `archived`、固定影响模板、传统 alternatives 数组或任何旧字段。任何 ADR 对象、迁移、事实读取或写入、Helper、Code、tests、行动模板、Web 或环境接入能力也尚未因此实现。

## 2. 主要收敛

1. ADR 是已经实际作出、具有跨行动持续影响的单一决定事实，不是规范补丁、规则来源、提案、研究正文或实施计划。
2. 状态使用 `active / superseded / retired`；active 不表示规则权威或实现状态，规范吸收不会自动使 ADR 终态，V3 archived 与宽泛 deprecated 不继承。
3. 新增 decision_question、decision、applicability、rationale、consequences、decided_at 六个专属字段；六字段除有来源且不改变原决定语义的事实更正外，不得原地实质改写。
4. ADR 不使用 current-summary、priority、evolution 或 WorkCase 字段；只复用公共身份、来源、证据、关系和已经共享的 disposition-summary、closed-at。
5. 第一版关系只允许新 ADR 单向 supersedes 旧 ADR。建边时新对象 active、旧对象同时转 superseded；边永久保留，每个目标全生命周期最多一个直接替代源，全部边构成 DAG。
6. 替代链时间必须满足 `target.decided_at <= source.decided_at <= target.closed_at`；普通文件、规范、Code 和 commit 只通过 source/evidence refs 定位，不扩张事实对象关系目标。

## 3. 独立复核与修正

规范复核覆盖决定事实与规则权威、准入、Spec/WorkCase/Spark 边界、V1–V8、状态、关系、变更和 Gate。字段与 Code 复核检查 V3 22、历史 validator、相关 Spark、当前统一登记、三类型绑定和 promotion 机械闭包。

终审实际拦截并修正了：共享 disposition-summary 偏向工作完成语义、supersedes source 后续终态的关系存续歧义、直接替代源基数可能被重置、跨对象决定与关闭时间倒置、六个专属字段不可改写闭集不一致，以及 decided_at 未比较全部近邻时间字段。两路终审最终均确认没有剩余 P1/P2。

## 4. 验证

tests 数字记录 ADR Gate 关闭当时结果；仓库文档、事实类型与字段数量是五类型全局归并前的当前回查结果。

- 全量 tests：333 passed；
- Ruff lint：passed；
- Ruff format check：passed；
- `git diff --check`：passed；
- 当前仓库检查：18 个当前文档、0 issues、repository complete；
- 字段治理检查：`fact_types = [spark, workcase, adr, pitfall, study]`、5 个结构、46 个字段、0 issues；
- 当前验证只覆盖规范与字段机械闭包，不包含真实 ADR 实例消费测试。
