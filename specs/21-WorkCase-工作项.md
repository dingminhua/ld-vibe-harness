# WorkCase-工作项

```yaml
ldvh_spec:
  spec_id: "21"
  spec_kind: "fact_model_member_spec"
  title: "WorkCase-工作项"
  status: "candidate"
  authority: "candidate"
  canonical_path: "specs/21-WorkCase-工作项.md"
  parent_spec: "specs/05-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 WorkCase 的对象定位、准入条件、事实源边界、最小状态边界、完成口径、Human Gate 和首批 Code 可消费检查"
  scope: "需要把一次 Human-AI 目标组织为可执行、可验证、可复核、可关闭事实对象的项目工作"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
    - "specs/05-事实模型基础规范.md"
  related_specs:
    - "specs/06-行动模板基础规范.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
  migration_sources:
    - "v2:specs/21-WorkCase-工作项.md"
    - "v2:specs/attachments/21.Att.01-orchestration字段契约表.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "fact_model_member_identity"
    - "workcase_admission_rules"
    - "workcase_source_boundaries"
    - "workcase_state_boundaries"
    - "workcase_closure_boundaries"
    - "workcase_human_gate_boundaries"
    - "workcase_instance_checks"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. 对象定位与准入"
      - "6. 事实源与实例边界"
      - "7. 状态、证据与关闭边界"
    assurance_measures: "8. 保障措施"
    verification_method: "9. 验证方法"
    human_gate: "10. Human Gate"
    stop_conditions: "11. Stop Conditions"
    next_queries: "12. 待补齐事项"
```

> 文件状态：candidate；本文吸收 V2 WorkCase 成员规范的父层规则。真实 WorkCase 实例已由阶段 9C 迁入 `ldvh-base/workcases/` 并由 Code/tests 校验；本文不迁入 V2 完整字段表、`21.Att.01` 长字段表、正式行动模板、Hook、commit gate、Web 写入或 runtime adapter。

## 1. 价值判断

本文存在的价值，是把一次 Human-AI 目标组织为可恢复、可验证、可复核、可关闭的事实对象，减少 AI 在跨会话、跨执行轮次或上下文压缩后对聊天记忆的依赖。

WorkCase 服务 00 的事实模型构成要素定位。它承接目标、范围、成功标准、执行状态、验证证据、关闭判断和后续分流；不对象化会增加 AI 的恢复、验证和关闭判断负担。

## 2. 权威依据

本文承接 `specs/05-事实模型基础规范.md` 的事实对象准入、实例边界、字段状态证据边界和成员规范迁移要求。

若本文与 03 事实源边界、05 父层规则、09 验证规则或 Human Gate 冲突，应回到上位规范和 Human Gate，不得由 WorkCase 局部规则自行覆盖。

## 3. 归口边界

本文归口定义 WorkCase 的成员规范最小规则：对象定位、准入条件、事实源边界、最小状态闭集、执行项内部化、完成口径、Human Gate 和首批实例检查。

本文不归口定义行动模板实例、正式 Hook 接入、commit gate、Web 写入、Code 输出 schema 或完整 `orchestration` 嵌套字段表。具体 WorkCase 实例位于 `ldvh-base/workcases/`，由 03 的事实源边界、本文成员规则和 Code/tests 字段 schema 共同约束。

## 4. 适用范围

本文适用于：

1. 判断一次目标是否应形成 WorkCase；
2. 创建、迁移、审计或关闭 WorkCase 实例前的最小规则读取；
3. Code、Web、行动模板和测试消费 WorkCase 状态、证据和关闭边界；
4. V2 `21-WorkCase-工作项.md` 和 `21.Att.01` 的后续迁移判断。

## 5. 对象定位与准入

WorkCase / 工作项是 Human 与 AI 围绕一次目标达成的工作事实契约。它承载目标、范围、成功标准、执行编排摘要、验证证据、关闭证据和后续分流。

一个目标满足以下条件之一时，应考虑形成 WorkCase：

1. 需要跨会话、跨执行轮次或跨 AI 角色追踪；
2. 需要表达目标、范围、成功标准、验证证据或关闭判断；
3. 需要多个执行项、并行安排、顺序安排或角色分工；
4. 需要 Human 明确确认目标、范围、成功标准或关闭判断；
5. 需要留下最小恢复信息、验证证据、关闭证据或结果物引用；
6. 不结构化会导致目标、范围、执行编排、验证或完成判断漂移。

当前对话即可完成、无需留存记录、无需流程治理的小工作，不创建 WorkCase。WorkCase 准入判断必须说明对象化价值和减少的 AI 恢复、验证或关闭判断负担；无法说明时，应留在当前上下文、Spark 候选、迁移材料或待补齐事项。

WorkCase 不替代 ADR、Spark、Pitfall 或 Study。长期决策进入 ADR，暂存输入进入 Spark，已解决且可复用经验进入 Pitfall，稳定报告进入 Study。

## 6. 事实源与实例边界

WorkCase 实例未来的权威事实源位置为：

```text
ldvh-base/workcases/workcase-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；短标题使用小写短横线。每个受管项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| WorkCase 成员规范 | `specs/21-WorkCase-工作项.md` |
| WorkCase 实例 | `ldvh-base/workcases/` |
| WorkCase 字段注册结构 | `specs/attachments/05.Att.01-字段注册表结构.md` 与后续 WorkCase 字段附件 |
| WorkCase 验证声明 | `specs/09-测试与验证规范.md` 与 `specs/attachments/09.Att.01-验证声明字段表.md` |
| WorkCase 展示、聚合或诊断输出 | Code、Web 或测试派生输出，不作为事实源 |

执行过程不作为长期事实源。WorkCase 只保留最小恢复信息、验证证据、关闭证据和后续分流结果；AI 的临时步骤、工具缓存、子 Agent 中间过程、未采纳草稿、Code 输出和 Web 状态不得写成 WorkCase 实例事实。

执行项只能作为 WorkCase 内部字段存在，不得形成独立事实对象、独立编号段、一级 Web 入口或长期被其它对象引用的事实源。需要长期追踪的结论，应按性质分流到 WorkCase、ADR、Spark、Pitfall、Study、docs、正式规范或 Git commit records。

## 7. 状态、证据与关闭边界

WorkCase 首批状态闭集如下：

| 状态 | 含义 |
|---|---|
| `subagents_plan_reviewing` | 子 Agent 或独立视角方案审核中；主控已经形成可审核方案 |
| `human_plan_confirming` | Human 方案确认中；方案审核和主控处理记录已形成，等待 Human 确认是否允许执行 |
| `executing` | 执行中；Human 已确认方案，AI 正在按范围执行 |
| `result_self_checking` | 结果自检中；主控正在检查成功标准、验证证据、关闭证据和残留风险 |
| `subagents_result_reviewing` | 结果复核中；独立视角正在复查结果与关闭材料 |
| `human_closure_confirming` | Human 关闭确认中；结果复核和主控处理完成，等待 Human 判断是否关闭或退回 |
| `closed` | 已关闭；关闭判断已由 Human 确认并形成稳定终态 |

`closed` 是稳定终态，只表示该 WorkCase 不再继续推进，不等同于目标成功。关闭可以表示完成、部分完成、取消、失效、被新 WorkCase 承接或其它经证据说明的结果。

新增或重写 WorkCase 不得使用 V2 legacy 状态 `draft`、`active`、`review_needed`。历史材料出现这些状态时，只能作为迁移诊断输入，不能作为 V3 状态闭集。

WorkCase 的完成口径必须区分四层：

1. 执行完成：执行项、成功标准和验证证据已回写，但仍需主控自检或结果复核；
2. 可提交关闭确认：状态为 `human_closure_confirming`，结果复核和主控处理完成，但 Human 尚未确认关闭；
3. 已关闭：状态为 `closed`，且关闭时间、关闭结果、关闭证据和 Human 关闭确认已填写；
4. 已提交：相关事实源修改已经进入符合 03 契约的 Git commit records。

关闭证据必须包含可读取的 `后续分流 / 收口结果` 段落。收口干净时，应说明无后续分流或无残留尾巴；收口不干净时，应列出承接对象、承接边界和继续处理方式。不得用“后续再看”“待定”“另行处理”等模糊语句替代承接结论。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 准入说明要求 | 创建 WorkCase 前必须说明对象化价值和减少的 AI 负担 | 本文、05、02 | 对象治理 | 目标被提升为 WorkCase 时 |
| 事实源边界要求 | WorkCase 实例不得反向定义规则，也不得由 Code/Web/测试输出替代 | 本文、03、05 | 事实源治理 | 创建、迁移或审计实例时 |
| 状态闭集要求 | WorkCase 状态必须属于本文闭集，legacy 状态只能作为迁移诊断 | 本文、Code/tests | 状态治理 | 写入、迁移或展示状态时 |
| 关闭证据要求 | 关闭前必须区分完成口径并记录后续分流 / 收口结果 | 本文、09、Human Gate | 验证治理 | 进入关闭确认或关闭状态时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 准入检查 | 是否说明对象化价值、事实源位置和减少的 AI 负担 | 保留为当前上下文、Spark 候选或待补齐事项 |
| 状态检查 | 状态是否属于闭集，且未使用 legacy 状态 | 阻断写入或记录迁移诊断 |
| 事实源检查 | 执行项、Code 输出、Web 状态或测试夹具是否没有被写成独立事实源 | 回到 03/05 边界修正 |
| 关闭检查 | 是否区分执行完成、可提交关闭确认、已关闭和已提交，并有后续分流 / 收口结果 | 不得声明关闭完整 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 将用户输入、Spark 或临时讨论升级为 WorkCase，或直接创建 WorkCase；
2. 从 `human_plan_confirming` 进入 `executing`，即确认目标、范围、成功标准、执行颗粒度和约束；
3. 从 `human_closure_confirming` 关闭为 `closed`；
4. 改写目标、成功标准、执行编排、关闭判断或后续分流；
5. 跳过未验证执行项、接受残留风险或通过豁免关闭 WorkCase；
6. 合并、拆分、删除、重命名或重新组织 WorkCase。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法判断当前目标是否应对象化为 WorkCase；
2. WorkCase 实例或测试夹具正在反向定义字段、状态、关闭条件或 Human Gate；
3. 执行项被提升为独立事实对象、独立编号段或一级 Web 入口；
4. `human_closure_confirming` 被表述成 `closed`，或执行完成被写成已提交；
5. 缺少验证证据、关闭证据或后续分流 / 收口结果却声明 WorkCase 已关闭完整。

## 12. 待补齐事项

1. 后续再判断是否迁入 V2 `21.Att.01-orchestration字段契约表.md` 的最小附件或转为 Code/tests；
2. 真实 WorkCase 实例目录已迁入 `ldvh-base/workcases/`；后续仍需判断是否定义 WorkCase 完整字段表、状态条件必填和实例样例；
3. 后续 Hook / commit gate / V3 正式启用前，再判断是否建立 WorkCase 创建、方案审核、结果复核和关闭确认的正式行动模板；
4. 后续 Web 实现启动时，应只展示 WorkCase 事实源和可追溯派生状态，不建立执行项独立页面或第二事实源；
5. 后续继续逐篇判断 Spark、ADR、Pitfall 和 Study 是否进入 V3 成员规范。
