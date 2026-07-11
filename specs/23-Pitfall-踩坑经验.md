# Pitfall-踩坑经验

```yaml
ldvh_spec:
  spec_id: "23"
  spec_kind: "fact_model_member_spec"
  title: "Pitfall-踩坑经验"
  status: "active"
  authority: "active"
  canonical_path: "specs/23-Pitfall-踩坑经验.md"
  parent_spec: "specs/05-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Pitfall 的对象定位、准入条件、事实源边界、最小状态边界、经验吸收边界、Human Gate 和首批 Code 可消费检查"
  scope: "需要把已解决且验证的反复问题、误判、规避策略或可复用经验记录为事实对象的项目工作"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-规范体系基础规范.md"
    - "specs/05-事实模型基础规范.md"
  related_specs:
    - "specs/20-Spark-火花.md"
    - "specs/21-WorkCase-工作项.md"
    - "specs/22-ADR-决策.md"
    - "specs/24-Study-研究报告.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
  migration_sources:
    - "v2:specs/23-Pitfall-踩坑经验.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "fact_model_member_identity"
    - "pitfall_admission_rules"
    - "pitfall_source_boundaries"
    - "pitfall_state_boundaries"
    - "pitfall_evidence_boundaries"
    - "pitfall_human_gate_boundaries"
    - "pitfall_instance_checks"
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

> 文件状态：active；本文吸收 V2 Pitfall 成员规范的父层规则。真实 Pitfall 实例已由阶段 9C 迁入 `ldvh-base/pitfalls/` 并由 Code/tests 校验；本文不迁入 V2 完整字段表、标签闭集或 Web 编辑能力。

## 1. 价值判断

Pitfall 的价值，是把已解决且验证的反复问题、误判、规避策略或可复用经验沉淀为事实对象，减少 AI 在后续执行中重复犯错和重新推理的负担。

Pitfall 主要服务 V3、V4、V6、V7 和 V9，并支撑 V1、V2：它帮助 AI 快速定位已知风险，理解触发条件和规避策略，正确判断相似问题，按已验证经验稳定执行，保留验证证据和吸收关系，并推动反复问题回到规范、行动模板、Code、Web 或保障与衔接层。Pitfall 不是 bug backlog、未验证问题列表、TODO、长期决策或规范正文。

## 2. 权威依据

本文承接 `specs/05-事实模型基础规范.md` 的事实对象准入、实例边界、字段状态证据边界和成员规范迁移要求。

若 Pitfall 与正式 specs、ADR、WorkCase 或 Human Gate 冲突，应按上位规范、事实源边界和 Human Gate 处理，不得由 Pitfall 局部规则自行覆盖。

## 3. 归口边界

本文归口定义 Pitfall 的成员规范最小规则：对象定位、准入条件、事实源边界、最小状态闭集、经验吸收边界、Human Gate 和首批实例检查。

本文不归口定义完整字段表、标签闭集、经验检索算法、Web 编辑能力、行动模板步骤或规则正文。

## 4. 适用范围

本文适用于：

1. 判断一个问题或经验是否应形成 Pitfall；
2. 创建、迁移、审计、归档或吸收 Pitfall 实例前的最小规则读取；
3. Code、Web、行动模板和测试消费 Pitfall 状态、经验证据和吸收关系；
4. 当前 V3 Pitfall 字段契约、标签闭集和实例样例的后续补充判断；该判断不得以本地 V2 成员文件作为默认来源。

## 5. 对象定位与准入

Pitfall / 踩坑经验是已解决、已验证且可复用的经验事实对象。它回答问题现象是什么、触发条件是什么、根因是什么、如何解决、如何验证、后续如何规避。

一个问题满足以下条件时，可以考虑形成 Pitfall：

1. 问题已经解决，且有验证证据；
2. 后续执行容易再次遇到同类问题；
3. 经验具有可复用规避策略、适用范围和不适用范围；
4. 需要被 WorkCase、ADR、Spark、Study、Code、Web 或行动模板引用；
5. 不对象化会增加 AI 重复误判、重复调试或错误复用的负担。

不应形成 Pitfall 的内容包括：未解决问题、未验证猜测、一次性日志、普通任务、长期决策、完整研究报告、规范规则正文和单纯情绪化复盘。

创建 Pitfall 前，AI 必须说明准入理由、问题是否已解决、验证证据、适用范围、规避策略和预期回写位置。

## 6. 事实源与实例边界

Pitfall 实例未来的权威事实源位置为：

```text
ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；短标题使用小写短横线。每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Pitfall 成员规范 | `specs/23-Pitfall-踩坑经验.md` |
| Pitfall 实例 | `ldvh-base/pitfalls/` |
| Pitfall 展示、聚合或诊断输出 | Code、Web 或测试派生输出，不作为事实源 |

Pitfall 实例不得定义、重写或授权 specs 规则、字段闭集、状态机、事实源边界或 Human Gate。经验若需要成为强制规则、字段契约、事实源边界或 Human Gate，应转写到对应 specs 正文或运行入口；Pitfall 只保留经验原因、验证证据和吸收关系。

Web、Code、测试输出、迁移材料、聊天和工具缓存不得替代 `ldvh-base/pitfalls/` 中的实例事实。

## 7. 状态、证据与关闭边界

Pitfall 首批状态闭集如下：

| 状态 | 含义 |
|---|---|
| `active` | 已确认，问题已解决、解决方式已验证，且可作为后续执行参考 |
| `archived` | 已归档，不再作为常规参考，但保留历史经验、归档原因和必要关联 |

`archived` 是稳定终态。终态 Pitfall 不得直接重开；如需重新沉淀，应新建 Pitfall，并在新 Pitfall 中引用原 Pitfall。

新增或重写 Pitfall 不得使用 V2 legacy 字段 `repeatability`、`severity` 或 `superseded_by` 作为新写入字段。

Pitfall 的经验口径必须满足：

1. `active` Pitfall 必须具备问题现象、触发条件、根因、解决方式、验证证据、规避策略、适用范围和不适用范围；
2. `archived` 必须填写 `archive_reason`，说明归档原因或吸收位置；
3. 未解决或未验证问题不得写成 `active` Pitfall；
4. 经验被规范、运行入口、Code、Web 或行动模板吸收时，应记录吸收关系；
5. 创建、状态变化、核心经验改写、归档或被吸收应通过 Git commit records 溯源。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 准入说明要求 | 创建 Pitfall 前必须说明已解决、已验证、可复用和适用范围 | 本文、05、02 | 对象治理 | 问题被提升为 Pitfall 时 |
| 事实源边界要求 | Pitfall 实例不得替代 specs 规则或由 Web/Code/测试输出替代 | 本文、03、05 | 事实源治理 | 创建、迁移或审计实例时 |
| 状态闭集要求 | Pitfall 状态必须属于本文闭集，终态不得直接重开 | 本文、Code/tests | 状态治理 | 写入、迁移或展示状态时 |
| 经验吸收要求 | 经验被规则或实现吸收时必须记录吸收位置和归档原因 | 本文、09、Human Gate | 验证治理 | 归档或吸收 Pitfall 时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 准入检查 | 是否说明问题已解决、已验证、可复用和减少的 AI 负担 | 保留为 WorkCase、Spark 或待补齐事项 |
| 状态检查 | 状态是否属于闭集，终态是否被直接重开 | 阻断写入或记录迁移诊断 |
| 经验检查 | active Pitfall 是否具备现象、根因、解决方式、验证和规避策略 | 不得声明经验可复用 |
| 事实源检查 | Pitfall 是否没有替代 specs、ADR 或 Human Gate | 回到 03/05 边界修正 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 创建 Pitfall、删除或重命名 Pitfall 实例；
2. 从 Spark、WorkCase、ADR 或 Study 中提炼经验为 Pitfall；
3. 将 `active` Pitfall 标记为 `archived`；
4. 修改问题现象、触发条件、根因、解决方式、验证证据、规避策略或适用范围；
5. 将 Pitfall 吸收到 specs、Rules、Code、Web、行动模板或运行入口；
6. 将未解决或未验证问题写成 `active` Pitfall；
7. 删除原 Pitfall 而不是通过 `archived` 表达归档或吸收。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法判断问题是否已解决、已验证且可复用；
2. Pitfall 正在替代 WorkCase、ADR、Study、specs 正文或 Human Gate；
3. active Pitfall 缺少验证证据、规避策略或适用范围；
4. archived Pitfall 缺少归档原因或吸收位置；
5. Web、Code、测试输出或迁移材料正在替代 Pitfall 实例事实。

## 12. 待补齐事项

1. 后续如需补充 Pitfall 完整字段表、标签闭集和实例样例，必须作为 V3-owned 字段契约、实例校验或明确 WorkCase 推进；
2. 真实 Pitfall 实例目录已迁入 `ldvh-base/pitfalls/`，后续新增或改写实例必须通过字段 schema、状态闭集和 legacy 字段检查；
3. 后续行动模板实例启动时，再定义 Pitfall 识别、创建、归档和吸收流程；
4. 后续 Code 可继续扩展 Pitfall 字段级 validator，但不得让字段级检查反向定义本文未授权规则。
