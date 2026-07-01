# Spark-火花

```yaml
ldvh_spec:
  spec_id: "20"
  spec_kind: "fact_model_member_spec"
  title: "Spark-火花"
  status: "active"
  authority: "active"
  canonical_path: "specs/20-Spark-火花.md"
  parent_spec: "specs/05-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Spark 的对象定位、准入条件、事实源边界、最小状态边界、分流口径、Human Gate 和首批 Code 可消费检查"
  scope: "需要把未成型输入、线索、问题、想法或待分流议题暂存为可追踪事实对象的项目工作"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
    - "specs/05-事实模型基础规范.md"
  related_specs:
    - "specs/21-WorkCase-工作项.md"
    - "specs/22-ADR-决策.md"
    - "specs/23-Pitfall-踩坑经验.md"
    - "specs/24-Study-研究报告.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
  migration_sources:
    - "v2:specs/20-Spark-火花.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "fact_model_member_identity"
    - "spark_admission_rules"
    - "spark_source_boundaries"
    - "spark_state_boundaries"
    - "spark_resolution_boundaries"
    - "spark_human_gate_boundaries"
    - "spark_instance_checks"
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

> 文件状态：active；本文吸收 V2 Spark 成员规范的父层规则。真实 Spark 实例已由阶段 9C 迁入 `ldvh-base/sparks/` 并由 Code/tests 校验；本文不迁入 V2 完整字段表、Web quick create、完整标签或分流 UI。

## 1. 价值判断

Spark 的价值，是把尚未成型但值得保留的输入、线索、问题、想法或待分流议题放到可追踪事实对象中，减少 AI 对聊天记忆、临时笔记和隐含上下文的依赖。

Spark 服务 05 的事实对象准入和分流规则。它不是完成对象，也不是任务计划、长期决策、经验库或研究报告；它只承接“现在还不能确定归口，但丢掉会增加后续定位和分流负担”的内容。

## 2. 权威依据

本文承接 `specs/05-事实模型基础规范.md` 的事实对象准入、实例边界、字段状态证据边界和成员规范迁移要求。

若 Spark 规则与 03 事实源边界、05 父层规则、WorkCase/ADR/Pitfall/Study 成员规则或 Human Gate 冲突，应回到上位规范和 Human Gate，不得由 Spark 局部规则自行覆盖。

## 3. 归口边界

本文归口定义 Spark 的成员规范最小规则：对象定位、准入条件、事实源边界、最小状态闭集、分流/废弃口径、Human Gate 和首批实例检查。

本文不归口定义 WorkCase、ADR、Pitfall 或 Study 的字段契约、状态机、验收规则、报告正文、Web 写入白名单或行动模板步骤。

## 4. 适用范围

本文适用于：

1. 判断一段输入是否应形成 Spark；
2. 创建、迁移、审计或关闭 Spark 实例前的最小规则读取；
3. Code、Web、行动模板和测试消费 Spark 状态、分流目标和事实源边界；
4. V2 `20-Spark-火花.md` 的后续字段迁移判断。

## 5. 对象定位与准入

Spark / 火花是分流前的事实对象。它可以后续转化或关联到 WorkCase、ADR、Pitfall、Study、docs、受管项目配置或其它事实源，但在转化前不替代这些对象的字段契约、状态机、验收规则或配置边界。

一个输入满足以下条件之一时，可以考虑形成 Spark：

1. 当前有保留价值，但尚无法判断应进入 WorkCase、ADR、Pitfall、Study 或 docs；
2. 丢失该输入会增加后续定位、分流或复盘负担；
3. 需要记录来源、优先级、当前摘要、关键演变或潜在分流方向；
4. 需要保留多线并行分流前的共同线索；
5. 需要 Human 后续决定是否升级、废弃或拆分。

不应形成 Spark 的内容包括：当前对话即可处理的小事项、已经满足 WorkCase 准入的目标、已经需要 ADR 承载的长期决策、已解决且可复用的 Pitfall、完整研究报告正文和普通执行步骤。

创建 Spark 前，AI 应说明保留原因、来源、优先级和后续可能分流方向；无法说明对象化价值和减少的 AI 负担时，应留在当前上下文或待补齐事项。

## 6. 事实源与实例边界

Spark 实例未来的权威事实源位置为：

```text
ldvh-base/sparks/spark-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；短标题使用小写短横线。每个受管项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Spark 成员规范 | `specs/20-Spark-火花.md` |
| Spark 实例 | `ldvh-base/sparks/` |
| Spark 展示、聚合或诊断输出 | Code、Web 或测试派生输出，不作为事实源 |

Spark 实例不得定义、重写或授权 Spark 事实模型规则、字段闭集、状态机、分流口径或 Human Gate。Web、Code、测试输出、迁移材料、聊天和工具缓存不得替代 `ldvh-base/sparks/` 中的实例事实。

Study 只作为 Spark 的关联输入或资料来源，不作为 `resolved_to` 的完整分流目标。完整报告应由 Study 承载，Spark 只记录报告如何改变议题理解。

## 7. 状态、证据与关闭边界

Spark 首批状态闭集如下：

| 状态 | 含义 |
|---|---|
| `pending` | 待处理：已捕获，尚未决定是否分流、处理或废弃；或已被部分分流但仍存在未承接议题 |
| `resolved` | 已完整分流到 WorkCase、ADR、Pitfall、docs、受管项目配置更新或其它非 Study 事实源，或已明确处理 |
| `discarded` | 已废弃：确认不再需要继续跟踪或作为分流入口 |

`resolved` 和 `discarded` 是稳定终态。终态 Spark 不得直接重开；如需重新处理，应新建 Spark，并在新 Spark 中引用原 Spark。

Spark 的关闭口径必须满足：

1. `pending` 仍有未承接议题时不得写成 `resolved`；
2. `resolved` 必须说明 `resolved_to` 和 `resolved_at`，且分流目标不得为 Study；
3. 多线并行或分阶段承接时，应保持 `pending`，直到剩余议题已被完整承接、明确废弃或无需继续跟踪；
4. `discarded` 必须说明 `discard_reason`；
5. 创建、分流、废弃、核心摘要或关键关联变化应通过 Git commit records 溯源。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 准入说明要求 | 创建 Spark 前必须说明保留原因、来源、优先级和后续可能分流方向 | 本文、05、02 | 对象治理 | 输入被提升为 Spark 时 |
| 事实源边界要求 | Spark 实例不得反向定义规则，也不得由 Web/Code/测试输出替代 | 本文、03、05 | 事实源治理 | 创建、迁移或审计实例时 |
| 状态闭集要求 | Spark 状态必须属于本文闭集，终态不得直接重开 | 本文、Code/tests | 状态治理 | 写入、迁移或展示状态时 |
| 分流证据要求 | 分流、废弃或多线并行承接必须记录目标、范围和残留议题 | 本文、09、Human Gate | 验证治理 | 进入 `resolved` 或 `discarded` 时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 准入检查 | 是否说明保留价值、事实源位置和减少的 AI 负担 | 保留为当前上下文或待补齐事项 |
| 状态检查 | 状态是否属于闭集，终态是否被直接重开 | 阻断写入或记录迁移诊断 |
| 分流检查 | `resolved` 是否有非 Study 分流目标，`discarded` 是否有废弃原因 | 不得声明分流完整 |
| 事实源检查 | Web/Code/测试输出是否没有替代 Spark 实例事实 | 回到 03/05 边界修正 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 创建 Spark、删除或重命名 Spark 实例；
2. 将对话输入、Study 结论或执行发现写入 Spark；
3. 将 `pending` Spark 分流为 WorkCase、ADR、Pitfall、docs、受管项目配置更新或其它事实源；
4. 将 Spark 标记为 `discarded`，且废弃会丢失后续跟踪入口；
5. 将 Spark 从单线分流改为多线并行分流，或将多个并行承接对象判断为已经共同完整承接；
6. 修改 `resolved_to`、`priority`、`description`、`evolution` 或关键关联；
7. 将 Spark 作为规避 WorkCase 或 ADR 准入判断的长期替代物。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法判断输入是否应对象化为 Spark；
2. Spark 正在替代 WorkCase、ADR、Pitfall、Study 或 docs 的正式承载职责；
3. `resolved` 缺少分流目标，或 Study 被写成 `resolved_to`；
4. Spark 仍有未承接议题却被标记为 `resolved`；
5. Web、Code、测试输出或迁移材料正在替代 Spark 实例事实。

## 12. 待补齐事项

1. 后续再判断是否迁入 Spark 完整字段表、字段条件必填和实例样例；
2. 后续 Web 实现启动时，Spark quick create 必须绑定事实源回写和 Human Gate 边界；
3. 真实 Spark 实例目录已迁入 `ldvh-base/sparks/`，后续新增或改写实例必须继续通过字段 schema、状态闭集和关系校验；
4. 后续 Code 可继续扩展 Spark source_refs、状态条件必填和 Web/API 回归 validator，但不得让字段级检查反向定义本文未授权规则。
