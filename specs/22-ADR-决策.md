# ADR-决策

```yaml
ldvh_spec:
  spec_id: "22"
  spec_kind: "fact_model_member_spec"
  title: "ADR-决策"
  status: "candidate"
  authority: "candidate"
  canonical_path: "specs/22-ADR-决策.md"
  parent_spec: "specs/05-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 ADR 的对象定位、准入条件、事实源边界、最小状态边界、规范吸收边界、Human Gate 和首批 Code 可消费检查"
  scope: "需要把长期决策、方案取舍、事实源归属或执行约束记录为可追踪事实对象的项目工作"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
    - "specs/05-事实模型基础规范.md"
  related_specs:
    - "specs/20-Spark-火花.md"
    - "specs/21-WorkCase-工作项.md"
    - "specs/23-Pitfall-踩坑经验.md"
    - "specs/24-Study-研究报告.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
  migration_sources:
    - "v2:specs/22-ADR-决策.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "fact_model_member_identity"
    - "adr_admission_rules"
    - "adr_source_boundaries"
    - "adr_state_boundaries"
    - "adr_decision_boundaries"
    - "adr_human_gate_boundaries"
    - "adr_instance_checks"
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

> 文件状态：candidate；本文吸收 V2 ADR 成员规范的最小父层规则。本文不迁入 V2 完整字段表、真实实例、决策创建行动模板或 Web 编辑能力。

## 1. 价值判断

ADR 的价值，是把长期决策、方案取舍、事实源归属、协作方式或执行约束记录为可追踪事实对象，减少 AI 在后续执行时反复重建决策背景和取舍依据的负担。

ADR 是决策事实对象，不是规范正文。决策需要成为长期规则时，应被吸收到对应 specs 或运行入口；吸收完成后，ADR 只保留决策原因、归档原因和追溯关系。

## 2. 权威依据

本文承接 `specs/05-事实模型基础规范.md` 的事实对象准入、实例边界、字段状态证据边界和成员规范迁移要求。

若 ADR 与正式 specs 冲突，不能让 ADR 覆盖 specs；应回到上位规范、事实源边界和 Human Gate 处理。

## 3. 归口边界

本文归口定义 ADR 的成员规范最小规则：对象定位、准入条件、事实源边界、最小状态闭集、规范吸收边界、Human Gate 和首批实例检查。

本文不归口定义完整字段表、完整影响闭环模板、行动模板步骤、Rules/Hook/Skill 同步机制或 Web 编辑能力。

## 4. 适用范围

本文适用于：

1. 判断某个判断或取舍是否应形成 ADR；
2. 创建、迁移、审计、归档或废弃 ADR 实例前的最小规则读取；
3. Code、Web、行动模板和测试消费 ADR 状态、决策边界和规范吸收关系；
4. V2 `22-ADR-决策.md` 的后续字段迁移判断。

## 5. 对象定位与准入

ADR / 决策是长期有效的决策补丁事实对象。它回答为什么选择某个方向、放弃哪些方向、影响哪些对象、什么时候被规范或实现吸收。

一个判断满足以下条件之一时，可以考虑形成 ADR：

1. 改变长期执行方式、协作方式、事实源归属或 Human Gate 边界；
2. 对多个 WorkCase、事实对象、Web、Code、测试或行动模板产生持续影响；
3. 需要在后续执行中优先参考，且不能只停留在聊天或当前 WorkCase；
4. 需要保留决策背景、取舍依据、影响范围、风险和吸收位置；
5. 从 Spark、WorkCase 或 Study 中沉淀出长期决策。

不应形成 ADR 的内容包括：临时偏好、普通实现步骤、尚未形成取舍的问题、已经直接进入 specs 的规则正文、已解决经验和完整研究报告。

创建 ADR 前，AI 必须说明准入理由、决策问题、建议结论、影响范围和预期回写位置；无法说明对象化价值和减少的 AI 负担时，应留在 WorkCase、Spark、Study 或待补齐事项。

## 6. 事实源与实例边界

ADR 实例未来的权威事实源位置为：

```text
ldvh-base/adrs/adr-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；短标题使用小写短横线。每个受管项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| ADR 成员规范 | `specs/22-ADR-决策.md` |
| ADR 实例 | `ldvh-base/adrs/` |
| ADR 展示、聚合或诊断输出 | Code、Web 或测试派生输出，不作为事实源 |

ADR 实例不得定义、重写或授权 specs 规则、字段闭集、状态机、事实源边界或 Human Gate。ADR 可以记录决策补丁，但稳定规则必须进入对应正式规范或运行入口。

Web、Code、测试输出、迁移材料、聊天和工具缓存不得替代 `ldvh-base/adrs/` 中的实例事实。Git commit records 只溯源文件修改，不替代 ADR 的决策内容和影响说明。

## 7. 状态、证据与关闭边界

ADR 首批状态闭集如下：

| 状态 | 含义 |
|---|---|
| `active` | 决策补丁仍有效，AI 和 Human 应优先参考 |
| `archived` | 决策补丁已被 specs、Rules、Code、Web、行动模板或其它稳定承载吸收，ADR 只保留追溯 |
| `deprecated` | 决策补丁不再适用、方向被放弃或不应继续作为执行依据 |

`archived` 和 `deprecated` 是稳定终态。终态 ADR 不得直接重开；如需重新判断，应新建 ADR 或修改对应稳定承载，并在新事实源中引用原 ADR。

新增或重写 ADR 不得使用 V2 legacy 状态 `proposed`、`accepted`、`rejected`、`superseded`，也不得使用旧字段 `superseded_by`、`alternatives` 或 `affects` 作为新写入字段。

ADR 的关闭口径必须满足：

1. `active` ADR 可以作为当前优先决策补丁，但不得覆盖正式 specs；
2. `archived` 必须填写 `archive_reason`，说明吸收位置和归档依据；
3. `deprecated` 必须填写 `deprecated_reason`，说明废弃原因和不得继续作为依据的边界；
4. 决策需要成为长期规则时，应先吸收到对应 specs 或运行入口，再归档 ADR；
5. 核心决策变化、归档、废弃和升级为规范应通过 Git commit records 溯源。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 准入说明要求 | 创建 ADR 前必须说明决策问题、影响范围和预期回写位置 | 本文、05、02 | 对象治理 | 判断被提升为 ADR 时 |
| 事实源边界要求 | ADR 实例不得替代 specs 规则或由 Web/Code/测试输出替代 | 本文、03、05 | 事实源治理 | 创建、迁移或审计实例时 |
| 状态闭集要求 | ADR 状态必须属于本文闭集，legacy 状态只能作为迁移诊断 | 本文、Code/tests | 状态治理 | 写入、迁移或展示状态时 |
| 吸收证据要求 | 归档或废弃前必须记录原因、影响范围和后续依据边界 | 本文、09、Human Gate | 验证治理 | 进入 `archived` 或 `deprecated` 时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 准入检查 | 是否说明决策问题、影响范围和减少的 AI 负担 | 保留为 WorkCase、Spark、Study 或待补齐事项 |
| 状态检查 | 状态是否属于闭集，且未使用 legacy 状态 | 阻断写入或记录迁移诊断 |
| 吸收检查 | `archived` 是否说明吸收位置，`deprecated` 是否说明废弃边界 | 不得声明 ADR 收口完整 |
| 事实源检查 | ADR 是否没有覆盖正式 specs 或替代 Human Gate | 回到 03/05 边界修正 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 创建 ADR、删除或重命名 ADR 实例；
2. 从 Spark、WorkCase 或 Study 中升级长期决策为 ADR；
3. 创建 `active` ADR；
4. 将 `active` ADR 标记为 `archived` 或 `deprecated`；
5. 修改 `active` ADR 的 `decision`、影响范围、事实源归属或 Human Gate 边界；
6. 将 ADR 中的决策升级为 specs、Rules、Code、Web 或行动模板规则；
7. 删除原 ADR 而不是通过状态表达废弃、归档或替代。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法判断当前判断是否应对象化为 ADR；
2. ADR 正在替代 specs 正文、事实源边界或 Human Gate；
3. `archived` 缺少吸收位置，或 `deprecated` 缺少废弃原因；
4. legacy 状态或旧字段被当作 V3 ADR 契约；
5. Web、Code、测试输出或迁移材料正在替代 ADR 实例事实。

## 12. 待补齐事项

1. 后续再判断是否迁入 ADR 完整字段表、五段式影响闭环和实例样例；
2. 后续受管项目事实源稳定后，再决定是否迁移真实 ADR 实例目录；
3. 后续行动模板实例启动时，再定义 ADR 创建、归档、废弃和规范吸收流程；
4. 后续 Code 可继续扩展 ADR 字段级 validator，但不得让字段级检查反向定义本文未授权规则。

