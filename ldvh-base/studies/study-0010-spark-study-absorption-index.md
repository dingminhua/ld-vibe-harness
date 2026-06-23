---
id: study-0010
type: study
title: Spark 与 Study 迁移后吸收索引
status: active
created: '2026-06-24T01:40:00+08:00'
updated: '2026-06-24T01:40:00+08:00'
summary: |
  本 Study 记录 LDVH v2 迁移后对现有 Spark 和 Study 的吸收判断。结论是：Spark 和 Study 不属于本轮事实源清理对象；Spark 的 `pending` 与 Study 的 `active` 均可作为合法保留状态。迁移后的主要工作不是关闭它们，而是建立读取索引，说明哪些内容已经被 specs、Code、Web、运行时扩展或 Git 事实源吸收，哪些内容仍作为后续工作入口保留。
user_intent: 用户确认 Spark 和 Study 应保留，要求继续推进迁移后的吸收标注和误读风险清理。
conclusion: |
  当前应把 Spark/Study 视为 v2 后续建设的入口层和研究证据层。已被迁移吸收的内容可以在本索引中标注为“已吸收但保留证据”，不能据此自动关闭 Spark；仍有未承接议题的 Spark 继续保持 `pending`。Study 继续保持 `active`，除非 Human 明确确认其不再作为当前引用入口。后续若要推进具体实现，应从本索引中选择候选议题创建新的 WorkCase 或行动编排，而不是把旧 WorkCase 或旧流程机械迁回。
urls: []
related_sparks:
- spark-0001
- spark-0002
- spark-0003
- spark-0004
- spark-0005
- spark-0006
- spark-0007
- spark-0008
- spark-0009
- spark-0010
- spark-0011
- spark-0012
- spark-0013
- spark-0014
- spark-0015
- spark-0016
- spark-0017
- spark-0018
- spark-0019
- spark-0020
- spark-0021
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
- specs/20-Spark-火花.md
- specs/24-Study-研究报告.md
- specs/04-Code确定性执行规范.md
- specs/05-Web信息同步规范.md
- specs/06-运行时扩展规范.md
- specs/07-事实源边界与Git追溯规范.md
- code/docs/02-知识地图与Preflight实现计划.md
archive_reason: null
---

# Spark 与 Study 迁移后吸收索引

## 研究问题

本报告回答一个迁移后的事实源治理问题：在 v2 规范体系、事实模型、Code、Web、运行时扩展和 Git 追溯已经基本迁入后，现有 21 个 pending Spark 和 9 个 active Study 应如何被读取、保留和分流。

具体问题包括：

1. Spark 和 Study 是否应作为清理对象被关闭、归档或删除；
2. 哪些 Spark 内容已经被 v2 规范、Code、Web、运行时扩展或 Git 事实源吸收；
3. 哪些 Spark 仍应作为后续 WorkCase、行动编排、知识地图或 Web 建设入口；
4. Study 在迁移后应如何继续作为研究证据被引用；
5. 后续 AI 读取这些对象时应避免哪些误读。

## 输入与边界

本报告的输入来自当前 `ldvh-base/sparks/` 与 `ldvh-base/studies/` 实例、`specs/20-Spark-火花.md`、`specs/24-Study-研究报告.md`，以及 v2 迁移后已经 active 的 00-08、20-24、60-69 规范和 Code 实现计划。

本报告不改变任何 Spark 或 Study 的状态，不创建新的执行计划，不替代后续 WorkCase，也不把旧 WorkCase 的执行步骤机械迁回 v2。它只形成一个稳定读取索引，帮助后续 AI 在进入事实源时理解“已吸收”“仍待分流”“保留为研究证据”三类关系。

边界如下：

- `pending` Spark 可以长期保留，尤其当它被部分吸收但仍存在未承接议题时；
- `active` Study 是当前可引用研究报告，不因迁移完成而自动归档；
- Study 关联 Spark 只说明报告可作为输入或证据，不说明 Spark 已解决；
- 已吸收到 specs、Code 或 Web 的内容仍可保留为历史语境和设计证据；
- 若后续需要执行，应新建或更新 WorkCase，并按 v2 当前需求重新定义目标、验收和验证。

## 关键发现

### 总体判断

Spark 和 Study 的保留价值不在于“还有多少未完成任务”，而在于它们保存了 v2 迁移过程中形成的议题入口、研究证据、概念演化和误读风险。若为了表面清爽而关闭或归档，会削弱 AI 后续追溯为什么这么设计的能力。

因此，当前正确动作是建立吸收索引，而不是清空、关闭或统一分流。

### Spark 吸收判断

| 分组 | Spark | 当前读取判断 | 后续处理方向 |
|---|---|---|---|
| 已大量吸收但保留证据 | spark-0001、spark-0004、spark-0009、spark-0010、spark-0011、spark-0017、spark-0020 | 相关内容已经在 v2 规范、WorkCase 事实源、Code/Web 边界或 Git 提交治理中被大量吸收，但仍保留迁移语境和局部残留问题 | 不自动关闭；后续若发现剩余问题明确，再单独分流 |
| 当前仍有架构入口价值 | spark-0002、spark-0003、spark-0006、spark-0012、spark-0013、spark-0014、spark-0015、spark-0019、spark-0021 | 这些 Spark 涉及规则建立方式、多项目治理、Spark 分流提醒、模糊用词、影响判断、流程触发、反思分流、派生型审核和子 Agent 复查，仍可能影响 v2 后续建设 | 可按优先级转为新 WorkCase、行动编排候选或规范补丁 |
| 研究证据入口 | spark-0007、spark-0008、spark-0016、spark-0018 | 这些 Spark 已关联或可关联 Study 研究，适合作为后续 Agent、产品级能力、知识地图和 Web 颜色治理的资料入口 | 保持 pending，后续按当前 v2 需求重新计划 |
| 需要谨慎复读的历史线索 | spark-0005 | WorkCase 与行动编排边界在 v2 中已发生明显重排，旧描述具有重要历史价值，但不能直接当作当前行动编排方案 | 后续只吸收问题意识和边界判断，不机械迁移旧流程 |

上述分组只用于读取和分流，不是状态流转依据。任何 Spark 若要进入 `resolved` 或 `discarded`，仍需回到 Spark 规范、确认剩余议题是否完整承接，并经过 Human Gate。

### Study 吸收判断

现有 Study 应继续作为 active 研究报告保留：

| Study | 当前作用 |
|---|---|
| study-0001 | WorkCase 与行动编排关系的历史演变证据，后续讨论 03 或 WorkCase 边界时仍可引用 |
| study-0002、study-0003、study-0004 | 子 Agent / 多角色能力设计资料，后续运行时扩展和 Agent 资产准入可引用 |
| study-0005 | Vibe Coding 产品级能力缺口资料，后续 Code/Web/流程能力规划可引用 |
| study-0006 | 知识地图实践评估资料，后续知识地图、preflight、索引和写入门禁可引用 |
| study-0007 | Web 颜色体系治理资料，后续 Web 视觉规范和实现可引用 |
| study-0008 | AI 能力资产行业实践资料，后续运行时扩展、Skill/Agent/Hook 准入可引用 |
| study-0009 | Superpowers 吸收资料，后续验证铁律、反合理化、两阶段审查和子代理边界可引用 |

这些 Study 的 `active` 不表示所有建议已经落地，只表示报告仍是当前可引用的稳定研究证据。若某个建议要变成规则或实现，应进入 specs、WorkCase、Code、Web、运行时扩展或行动编排。

### 误读风险

后续 AI 读取 Spark/Study 时，最容易发生五类误读：

1. 看到 Spark 已关联 Study，就误以为 Spark 已完成分流；
2. 看到 v2 已迁移完成，就误以为所有历史 Spark 都可以关闭；
3. 看到旧 WorkCase 已关闭，就误以为相关 Spark 的剩余议题也已关闭；
4. 看到 Study 是 active，就误以为报告建议已经成为正式规则；
5. 看到本索引给出吸收判断，就误以为本索引替代了目标 Spark 或 Study 的原文。

这些误读都应被避免。本索引只提供导航和分流判断，不替代对象原文。

## 建议

1. 保留所有当前 Spark 和 Study，不做批量关闭、归档或删除。
2. 后续每次推进具体议题时，优先从本索引选择最相关的 Spark/Study，再读取目标对象原文。
3. 若某个 Spark 的剩余议题已经明确，应创建新的 WorkCase 或行动编排候选，而不是复用旧 WorkCase 的步骤。
4. 若某个 Study 的建议被正式吸收，应在目标规范、Code、Web、运行时扩展或 WorkCase 中写入稳定事实，并通过 Git 提交记录追溯。
5. 知识地图和 preflight 可以消费本索引作为导航资料，但不得把本索引输出当作事实源状态。

## 后续分流

优先候选分流如下：

| 候选 | 原因 | 建议承载 |
|---|---|---|
| spark-0021 子 Agent 复查编排流程缺口 | 用户已经多次要求用子 Agent 审核规范和迁移质量，当前仍缺少固定行动编排 | 后续行动编排或运行时扩展相关 WorkCase |
| spark-0016 知识地图建设方向 | active specs 范围、preflight 和知识地图入口已有初版 Code，但正式知识地图机制尚未完全展开 | Code / 知识地图 / 受控写入 WorkCase |
| spark-0006 Spark 分流与收敛提醒机制 | 当前本索引只解决读取误读，尚未形成自动提醒或分流检查 | Code 诊断或 Web 提醒 WorkCase |
| spark-0019 派生型审核流程与能力资产边界 | 与两阶段审查、子 Agent 复查、能力资产准入相关 | 行动编排候选或运行时扩展规范补丁 |
| spark-0018 Web 颜色体系治理 | Study 已有研究，Web 仍需要后续实现规划 | Web WorkCase |

本报告完成后，后续迁移工作应继续围绕 v2 当前事实源需求推进，而不是把 Spark/Study 当作待清空列表处理。
