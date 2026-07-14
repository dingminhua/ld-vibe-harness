# V4 WorkCase 设计外部审计交接包

> 准备日期：2026-07-14。本文是外部审计入口，不取得 WorkCase、事实字段、行动模板或实现定义权。审计必须回到所列当前规则源核对，不能把本文摘要当成规则。

## 1. 审计目标

独立评估 V4 WorkCase 当前设计是否：

1. 忠实满足 `specs/00-理念与构成.md` 的上位要求和 V1–V8；
2. 正确保留 V3 WorkCase 中仍有价值的长时责任、阶段结果、委派、审核、Human 控制和中断恢复意图；
3. 没有恢复 V3 通用 orchestration、环境内部步骤、工具日志、角色脚手架和对象内历史流水；
4. 清楚区分 WorkCase 事实、阶段性 work item、行动模板、环境执行、Code、AI、Subagent 与 Human 的责任；
5. 具有足够稳定且可操作的 work item 颗粒度、阶段状态、版本失效、双 Human Gate、进度披露和关闭机制；
6. 没有通过字段重复、跨文档第二权威、不可机械验证的 Code 声明或尚未实现能力制造新的漂移。

这次审计不是措辞润色，也不是要求审计者默认赞成当前方案。允许结论为通过、有条件通过或需要重开；所有问题必须给出来源证据和最小修正方向。

## 2. 当前状态与变更范围

当前内部状态是“WorkCase 修正版已经正式定义、实现当前可机械部分并通过内部验证；等待外部审计后再进入受控更新与生命周期执行能力”。相关提交：

- `753eb1f6 docs: reopen WorkCase lifecycle design`
- `ca037e1d feat: restore governed WorkCase lifecycle`
- 建议比较范围：`c46c8da4..ca037e1d`

当前已成立：WorkCase Schema、阶段和工作项规则、统一字段/结构登记、准入记录、当前对象机械校验、创建 fixtures、F1 phase 与工作项状态计数投影。当前未成立：事实对象受控更新/CAS、阶段转换写入、多对象事务、生命周期行动模板、Web 进度界面和环境 Hook。审计必须区分“当前设计错误”和“已明确留给后续阶段实现”，但若后置能力因现有设计无法可靠实现，仍应指出架构阻断。

当前验证基线：18 个当前规范文档、5 个事实类型、8 个登记结构、81 个登记字段、0 repository/field-governance issues；`code/tests/` 为 440 passed；Ruff lint、format check 与 `git diff --check` 通过。

## 3. 必读资料及顺序

### A. 上位要求

1. `specs/00-理念与构成.md`
2. `specs/05-事实模型基础规范.md`
3. `specs/attachments/05.Att.01-事实对象统一字段登记.md`
4. `specs/06-行动模板基础规范.md`

### B. 当前 WorkCase 设计与证据

5. `specs/21-WorkCase-工作项.md`
6. `docs/v4-architecture/closures/V4-WorkCase类型封闭记录.md`
7. `docs/v4-architecture/active/V4-五类型全局归并封闭记录.md` 中 workcase 结构、字段准入和 `field-review-0003/0004`
8. `docs/v4-architecture/active/V4-工作推进总纲.md` 中阶段 5、阶段 6 和当前下一步
9. `docs/v4-architecture/investigations/V3-行动资产盘点与V4内部行动能力设计.md` 中 WorkCase 生命周期与行动平面边界

### C. V3 对照资料

10. `archive/v3/specs/21-WorkCase-工作项.md`
11. `archive/v3/specs/attachments/21.Att.01-orchestration字段契约表.md`
12. `archive/v3/ldvh-base/workcases/` 中至少抽查：简单对象、长对象、含多 execution items 对象、审核/关闭状态有代表性的对象
13. 可选参考：仓库根目录 `V3-WorkCase-架构分析-独立只读.md`。它只是一份未纳入当前规则源的外部分析，不得作为事实或规范权威。

### D. 实现与测试

14. `code/ldvh/facts/validation.py`
15. `code/ldvh/helper/operations/fact_candidate_operation.py`
16. `code/ldvh/helper/operations/fact_candidate_request.py`
17. `code/tests/facts/test_validation.py`
18. `code/tests/helper/test_fact_candidate_operation.py`
19. `code/tests/helper/test_fact_creation_operation.py`
20. `code/tests/helper/test_fact_object_operation.py`
21. `code/tests/specs/test_field_registry.py`

## 4. 已确认的 Human 需求

审计不得忽略以下已经明确的产品需求，但可以指出它们与 00 冲突或实现方式不合理：

1. WorkCase 用于长时工作责任，工作项记录有独立阶段目标的结果，不记录工作项内部具体步骤。
2. WorkCase 创建前，高性能主控 AI 形成计划并由独立 Subagent 审核；主控处理意见后才创建对象。
3. 对象创建后不能直接执行，必须由 Human 查看目标、工作项、模板选择和偏离，并批准当前计划版本。
4. 执行者可在 work item 边界内自由实现；中断、压缩、模型切换和高性能 AI 规划/低性能 AI 执行/高性能 AI 检查必须可恢复。
5. 全部工作项结束后，主控先检查修复，再由独立 Subagent 审核结果，主控处理反馈并形成最终报告和分流建议。
6. Human 最终确认当前结果版本后才能关闭 WorkCase。
7. Web 至少应显示当前推进阶段、工作项状态计数和活动项恢复信息；无权重时不得伪造完成百分比。

## 5. 必答审计问题

### 5.1 对象与颗粒度

- “一个可独立判断关闭的责任”是否足以稳定界定 WorkCase？
- “直接服务同一关闭责任、具有阶段目标和可观察结果”是否足以稳定界定 work item？
- 哪些反例会导致 work item 过细、过粗、伪阶段化或本应拆成其它 WorkCase？
- 颗粒度判断由 AI、独立审核和第一次 Human Gate 共同承担是否足够，是否缺少必须写入规范的操作性判据？

### 5.2 生命周期与双 Gate

- 创建前审核、创建后执行批准的先后关系是否自洽？
- `status` 与 `phase` 的双轴是否必要且无歧义？
- phase 闭集、允许边、退回路径、blocked、取消、计划变化和结果变化是否闭合？
- `plan_version`、`result_version`、creation/result reviews 和两次 approval 的失效规则是否足以防止旧授权覆盖新内容？
- 是否存在无法恢复、无法合法退回或可以绕过 Human Gate 的路径？

### 5.3 字段、结构与事实边界

- 三个新增结构和新增字段是否都具有稳定独立消费价值？
- 是否有同义字段、可删除字段、遗漏字段或把设计/审计过程错误写入事实对象的字段？
- 当前只保留当前版本审核、旧版本交给 Git 的做法是否满足追溯与消费？
- `summary / resume_from / waiting_on`、顶层与 item 级恢复信息是否分工清楚且不会大量重复？
- 审核 feedback 和 controller_resolution 的结构是否足够证明反馈得到处理，又不会伪造过程？

### 5.4 AI、Code、行动模板与环境边界

- 当前哪些检查确实可由 Code 确定性完成，哪些必须留给 AI/Human？实现是否越界或漏检？
- WorkCase 是否错误承担了行动模板或环境执行器责任？反之，是否把必须长期保存的事实错误留给临时行动现场？
- 未来“事实对象状态转换与承接处置”模板和受控更新/CAS 能否无歧义消费当前 Schema？
- 当前设计是否支持高性能 AI 规划、低性能 AI 执行、高性能 AI 检查，而不会让角色脚手架固化进事实？

### 5.5 渐进式披露、进度和 Web

- F1 的 `phase + work_item_counts` 是否足够用于恢复责任上下文？何时必须展开 F3 完整对象？
- 没有百分比的阶段条、计数和活动项摘要是否提供了足够进度感？
- Web 派生视图是否可能形成第二事实源或掩盖 blocked/cancelled？

### 5.6 V3 意图与 V4 改进

- V3 哪些设计意图已被正确保留、改造或删除？
- 当前 V4 是否比 V3 更稳定、清晰、可恢复、可审计并减少 AI 捏造？
- 是否仍有被 V4 忽略但值得吸收的 V3 意图？不得因 V3 有字段就直接主张恢复。

## 6. 输出要求

审计报告必须包含：

1. 总结结论：通过 / 有条件通过 / 需要重开，并说明最高严重度；
2. 00 与 V1–V8 覆盖矩阵；
3. 当前需求、V3 意图和 V4 设计的三向映射；
4. 按 P0/P1/P2/P3 排序的问题清单；
5. 每个问题给出文件与行号、违反的来源要求、具体失败场景、影响和最小修正建议；
6. 对 §5 每组问题给出明确回答；
7. 区分规范缺陷、实现缺陷、测试缺口、可读性问题和明确后置能力；
8. 列出审计实际阅读的文件、抽查的 V3 实例和未覆盖范围。

禁止只给抽象评价、无来源建议、单纯统计篇幅或把“尚未实现”一律判为设计错误。也禁止为了简化而删除中断恢复、独立审核或两次 Human Gate，除非先证明这些需求违反 00 并提出等价保障。

## 7. 可直接使用的提示词

请对当前仓库的 V4 WorkCase 设计做一次独立、严格、以反例为导向的架构与实现一致性审计。先完整阅读 `docs/v4-architecture/V4-WorkCase设计外部审计交接包.md`，严格按其中“必读资料及顺序”“必答审计问题”和“输出要求”执行，不要只审 `specs/21-WorkCase-工作项.md`。以 `specs/00-理念与构成.md` 为最高产品要求，以 05、05.Att.01、06 和当前 21 为正式规则源，以 V3 21、21.Att.01 和代表 WorkCase 实例为历史设计意图对照，并核对相关 Code/tests 是否与来源一致。

不要默认当前方案正确，也不要因 V3 存在某个字段就主张恢复。重点寻找：WorkCase 与 work item 颗粒度不稳定、事实与行动模板/环境步骤混淆、status/phase 双轴歧义、阶段边不闭合、计划或结果变化后旧审核/批准未失效、两次 Human Gate 可被绕过、中断恢复不足、字段重复或第二权威、Code 越权解释自然语言、F1/Web 进度披露不足，以及高性能 AI 规划—低性能 AI 执行—高性能 AI 检查链路无法可靠交接等问题。

报告必须给出通过/有条件通过/需要重开的明确结论，并按 P0/P1/P2/P3 列问题。每个问题必须包含文件和行号、上位要求、可复现失败场景、影响、最小修正建议；同时提供 00/V1–V8 覆盖矩阵、V3 意图—Human 需求—V4 设计映射、已读文件/抽查实例和未覆盖范围。请明确区分设计缺陷、实现缺陷、测试缺口、可读性问题和已经声明的后置能力。
