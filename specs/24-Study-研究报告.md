# Study-研究报告

```yaml
ldvh_spec:
  spec_id: "24"
  spec_kind: "fact_model_member_spec"
  title: "Study-研究报告"
  status: "candidate"
  authority: "candidate"
  canonical_path: "specs/24-Study-研究报告.md"
  parent_spec: "specs/05-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Study 的对象定位、准入条件、事实源边界、最小状态边界、Markdown 正文骨架、Human Gate 和首批 Code 可消费检查"
  scope: "需要把已形成稳定阅读价值的调研、分析、核验或方案比较结果记录为 Markdown 事实对象的项目工作"
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
    - "specs/22-ADR-决策.md"
    - "specs/23-Pitfall-踩坑经验.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
  migration_sources:
    - "v2:specs/24-Study-研究报告.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "fact_model_member_identity"
    - "study_admission_rules"
    - "study_source_boundaries"
    - "study_state_boundaries"
    - "study_markdown_body_boundaries"
    - "study_human_gate_boundaries"
    - "study_instance_checks"
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

> 文件状态：candidate；本文吸收 V2 Study 成员规范的最小父层规则。本文不迁入 V2 完整 frontmatter schema、真实实例、Web 阅读实现或研究行动模板。

## 1. 价值判断

Study 的价值，是把已形成稳定阅读价值的调研、分析、核验或方案比较结果记录为 Markdown 事实对象，减少 AI 在后续讨论、决策和执行中重新整理资料、引用结论或判断来源边界的负担。

Study 是报告承载，不是讨论入口、执行承接、长期决策或经验库。报告结论被吸收后，应分流到 WorkCase、ADR、Pitfall、Spark、docs、specs 或其它事实源。

## 2. 权威依据

本文承接 `specs/05-事实模型基础规范.md` 的事实对象准入、实例边界、字段状态证据边界和成员规范迁移要求。

若 Study 与正式 specs、ADR、WorkCase、Pitfall 或 Human Gate 冲突，应按上位规范、事实源边界和 Human Gate 处理，不得由 Study 局部规则自行覆盖。

## 3. 归口边界

本文归口定义 Study 的成员规范最小规则：对象定位、准入条件、事实源边界、最小状态闭集、Markdown frontmatter 与正文骨架边界、Human Gate 和首批实例检查。

本文不归口定义完整 frontmatter schema、Web 阅读页面、研究行动模板、外部资料抓取、缓存实现或事实吸收流程。

## 4. 适用范围

本文适用于：

1. 判断一份调研、分析、核验或方案比较结果是否应形成 Study；
2. 创建、迁移、审计、引用或归档 Study 实例前的最小规则读取；
3. Code、Web、行动模板和测试消费 Study 状态、正文骨架、URL 结构和事实源边界；
4. V2 `24-Study-研究报告.md` 的后续字段迁移判断。

## 5. 对象定位与准入

Study / 研究报告承载已经形成稳定阅读价值的调研、分析、核验或方案比较结果。它解决的问题是：普通资料区可以继续变化，但某些报告已经成为后续讨论、决策、计划或 Spark 演变的关键依据，需要进入 Git 可追踪事实源。

一个报告满足以下条件之一时，可以考虑形成 Study：

1. AI 或 Human 已完成一轮调研，结果需要长期保留为可阅读报告；
2. 报告会被 WorkCase、ADR、Pitfall、Spark、docs 或 specs 作为关键依据；
3. 报告包含输入边界、关键发现、建议、残留不确定性和后续分流；
4. 不对象化会增加 AI 重新查找资料、重建结论或误用来源的负担。

不应形成 Study 的内容包括：临时搜索结果、未整理的链接列表、普通聊天摘要、执行计划、长期决策、已解决经验和纯规则正文。

创建 Study 前，AI 必须说明研究问题、输入边界、关键发现、建议、后续分流和预期引用对象。

## 6. 事实源与实例边界

Study 实例未来的权威事实源位置为：

```text
ldvh-base/studies/study-{NNNN}-short-title.md
```

编号从 `0001` 开始递增，固定 4 位；短标题使用小写短横线。每个受管项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Study 成员规范 | `specs/24-Study-研究报告.md` |
| Study 实例 | `ldvh-base/studies/` |
| Study 展示、聚合或诊断输出 | Code、Web 或测试派生输出，不作为事实源 |

Study 是 Markdown 事实对象。每个实例使用 YAML frontmatter 承载结构化字段，frontmatter 之后的 Markdown 正文承载报告内容。

Study 实例不得定义、重写或授权 specs 规则、字段闭集、状态机、事实源边界或 Human Gate。Study 被 WorkCase、ADR、Pitfall、Spark、docs 或规范引用时，只说明报告作为输入或依据；稳定规则、决策、任务、经验或事实源修改必须进入对应权威事实源。

外部网址不得只是裸 URL 列表。`urls` 必须使用结构化条目，至少包含 `ref` 和 `summary`；项目内文档路径进入 `related_docs`，不得混入外部网页资料。

## 7. 状态、证据与关闭边界

Study 首批状态闭集如下：

| 状态 | 含义 |
|---|---|
| `active` | 报告是当前可引用的稳定研究产物 |
| `archived` | 报告保留历史价值，但不再作为当前入口 |

`archived` 是稳定终态。终态 Study 不得直接重开；如需重新研究，应新建 Study 或更新对应承接对象，并在新事实源中引用原 Study。

Study 的正文骨架必须包含以下二级标题：

| 正文标题 |
|---|
| `## 研究问题` |
| `## 输入与边界` |
| `## 关键发现` |
| `## 建议` |
| `## 后续分流` |

Study 的报告口径必须满足：

1. `active` Study 必须具备摘要、研究问题、输入边界、关键发现、建议和后续分流；
2. `archived` 必须填写 `archive_reason`；
3. `urls` 条目必须包含 `ref` 和 `summary`，其中 `ref` 是完整 `http(s)` URL，`summary` 是中文用途摘要；
4. Study 不替代 Spark 的议题演变、ADR 的长期决策、Pitfall 的经验沉淀或 WorkCase 的执行计划；
5. 创建、状态变化、核心报告改写和归档应通过 Git commit records 溯源。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 准入说明要求 | 创建 Study 前必须说明研究问题、输入边界、关键发现、建议和后续分流 | 本文、05、02 | 对象治理 | 报告被提升为 Study 时 |
| 事实源边界要求 | Study 实例不得替代 specs 规则或由 Web/Code/测试输出替代 | 本文、03、05 | 事实源治理 | 创建、迁移或审计实例时 |
| 状态闭集要求 | Study 状态必须属于本文闭集，归档必须说明原因 | 本文、Code/tests | 状态治理 | 写入、迁移或展示状态时 |
| 正文骨架要求 | Markdown 正文必须包含固定二级标题和可追溯输入边界 | 本文、09、Code/tests | 验证治理 | 创建或核心改写 Study 时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 准入检查 | 是否说明研究问题、输入边界、关键发现和减少的 AI 负担 | 保留为资料区、Spark 或待补齐事项 |
| 状态检查 | 状态是否属于闭集，归档是否说明原因 | 阻断写入或记录迁移诊断 |
| 正文检查 | Markdown 正文是否包含固定二级标题，URL 是否结构化 | 不得声明 Study 可稳定消费 |
| 事实源检查 | Study 是否没有替代 ADR、Pitfall、WorkCase、Spark、specs 或 Human Gate | 回到 03/05 边界修正 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 创建 Study、删除或重命名 Study 实例；
2. 将调研结果从资料区、聊天或 WorkCase 输出提升为 Study；
3. 将 Study 标记为 `archived`；
4. 大幅改写研究问题、输入边界、关键发现、建议、结论或后续分流；
5. 将 Study 作为 ADR、Pitfall、WorkCase、Spark、docs 或 specs 的关键依据；
6. 删除原 Study 而不是通过 `archived` 表达归档。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法判断报告是否已形成稳定阅读价值；
2. Study 正在替代 Spark、WorkCase、ADR、Pitfall、specs 正文或 Human Gate；
3. Study 缺少输入边界、关键发现、建议或后续分流；
4. URL 只有裸链接，没有 `ref` 和 `summary`；
5. Web、Code、测试输出或迁移材料正在替代 Study 实例事实。

## 12. 待补齐事项

1. 后续再判断是否迁入 Study 完整 frontmatter schema、正文样例和 URL 字段细节；
2. 后续受管项目事实源稳定后，再决定是否迁移真实 Study 实例目录；
3. 后续 Web 实现启动时，应复用同一份 Study 事实源，不维护第二套摘要或正文；
4. 后续 Code 可继续扩展 Study frontmatter 和正文骨架 validator，但不得让字段级检查反向定义本文未授权规则。
