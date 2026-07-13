# WorkCase / 工作项

```yaml
ldvh_spec:
  spec_key: "workcase-fact-type"
  spec_id: "21"
  spec_kind: "spec"
  title: "WorkCase / 工作项"
  status: "active"
  canonical_path: "specs/21-WorkCase-工作项.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 WorkCase 事实类型的对象边界、Schema、生命周期、来源、关系、验证与关闭规则"
  scope: "管辖项目中已经形成明确可验证目标，并需要跨行动或会话持续保存当前推进与终态判断的单一工作责任"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
    - "action-template-foundation"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `workcase` 事实类型的唯一定义来源；它不使 WorkCase 读取、创建、校验、迁移、Helper、Code、tests、行动模板或 Web 能力自动成立。V3 WorkCase 规范、附件、实例和实现只作为设计与反例输入，不取得 V4 当前效力。

## 1. 价值判断

WorkCase 把一个已经形成明确目标、范围和成功标准的工作责任，保留为可跨行动恢复、可验证、可阻塞、可关闭的当前事实。它使后续 AI 不必依赖聊天记忆重建“要完成什么、边界在哪里、当前进展如何、什么阻止继续、依据什么关闭”。

一个 WorkCase 只承担一个能够独立判断关闭的工作责任。步骤、命令、子 Agent 分工、方案审核顺序和当次计划不是 WorkCase；共同服务同一关闭判断的步骤留在当前行动计划或适用行动模板中，可独立验收、阻塞、取消或转交的目标则分别形成 WorkCase。

V3 的 24 个实例平均约 479 行、最大约 1099 行；全部保存固定 `orchestration.mode`，122 个执行项中 106 个仍标为 `single`，120 个阻塞原因为空，且对象状态与执行项状态已出现互相矛盾。这证明跨会话目标与关闭事实有价值，也证明把编排、复核和空占位长期写入对象会制造同步负担与漂移。V4 因而保留工作责任事实，移除运行脚手架，只登记恢复与关闭所需的最小字段。

WorkCase 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累；它通过阻塞、关闭与 Human Gate 交还当前状态、依据、影响、风险和待决定事项来服务 V7。V4 稳定推进由行动模板和当次计划承担，WorkCase 只提供目标与当前事实，不复制行动编排。新增成本包括发现、查重、持续回写、Schema、迁移和消费维护；在字段统一复用、三状态、六个专属字段以及不保存执行日志的边界下，这些成本低于跨会话反复重建目标、范围、验证和关闭判断的持续损耗。不能证明该净收益的工作不准入 WorkCase。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定 Git 可追踪事实源、当前 Working Tree、来源回指和稳定事实边界；
3. `action-template-foundation`：规定可复用行动结构与单次执行计划不应反向成为事实对象 Schema。

历史 V3 21、21.Att.01、24 个实例和 V2 候选行动编排只用于识别真实需求与失败模式。它们不能证明 V4 路径、字段、状态、实例、固定审核流程或写入能力成立。

## 3. 职责边界

本文负责定义：

1. `workcase` 的类型语义、对象粒度、准入和排除边界；
2. WorkCase 的唯一当前承载位置、完整 Schema、状态与关闭口径；
3. 目标、范围、成功标准、当前摘要、验证、阻塞、来源、证据和关系的领域语义；
4. WorkCase 创建、更新、更正、拆分、合并、关闭、删除和停止使用的边界；
5. WorkCase 的验证要求、Human Gate、Stop Conditions 和最小失败范围。

本文不负责定义：

1. 当次实施计划、执行步骤、执行项状态、子 Agent 角色、并行或顺序安排；
2. 方案审核、结果复核、Human 交互顺序、controller receipt 或工具运行状态；
3. Helper API、CLI、Web 表单、Hook、文件分配算法或迁移兼容；
4. 其它事实类型、普通文档、规范、Git 提交或行动模板的内容；
5. 仅因 WorkCase 存在而产生的执行、写入、提交、发布或风险接受授权。

AI 负责判断是否值得对象化、是否与现有事实重复、目标和范围是否清楚、证据是否充分以及关闭是否真实；Code 只可按当前来源检查固定结构、值闭集、引用和状态条件。WorkCase 不是任务执行引擎，也不是聊天计划副本。

## 4. 适用范围

一个目标只有同时满足以下条件，才可以形成 WorkCase：

1. 已经存在清楚、可执行且能够独立判断关闭的单一目标；
2. 范围、排除边界和至少一项可检查成功标准能够明确表达；
3. 需要跨行动或会话恢复，或具有显著验证、授权、依赖、阻塞或独立关闭事实；
4. 已召回并比较当前 WorkCase、Spark 与相邻稳定事实，没有可无损更新的现有对象；
5. 来源能够按目标、范围和成功标准所需精度回指，未知内容没有被补造；
6. 对象化减少的恢复、验证和关闭漂移高于持续回写与 Schema 维护成本。

以下内容不得形成 WorkCase：当前行动即可完成且无需稳定回读的小任务；只有模糊问题或信息缺口、尚无可验收目标的输入；临时 todo、Agent plan、命令清单、review checklist 或执行日志；长期规则或普通文档正文；纯结果报告；没有独立身份与关闭需要的提醒；无终点的周期运行入口。

Spark 与 WorkCase 的分界不取决于“以后是否可能做”。Spark 尚无确定承接位置或清楚验收边界；WorkCase 已经有可执行目标、范围与成功标准。把 Spark 分流到 WorkCase 必须分别满足 Spark 完整承接和本文准入，不得自动升级。

## 5. WorkCase 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `workcase` | 已形成明确可验证目标并需要跨行动或会话保存当前推进与终态判断的单一工作责任 | `workcase-fact-type::5. WorkCase 类型定义` |

### 结构准入记录

本类型没有结构准入事项

### 类型专属结构定义

本类型没有类型专属结构

### 字段准入记录

| information_need | compared_field_keys | decision | resulting_field_key | rationale | review_ref |
|---|---|---|---|---|---|
| 稳定识别同一 WorkCase | `object-id` | reuse | `object-id` | 公共对象身份无损适用，只收紧 WorkCase 格式 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 声明对象属于 WorkCase 类型 | `fact-type-key` | reuse | `fact-type-key` | 公共类型身份无损适用，固定为 `workcase` | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 提供 Human 与 AI 可读短标签 | `title` | reuse | `title` | 公共标题只用于识别，不承担目标或当前进展 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 记录首次形成时间 | `created-at` | reuse | `created-at` | 公共形成时间语义无损适用 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 记录当前内容最近实质变化时间 | `updated-at` | reuse | `updated-at` | 公共更新时间无损适用，不建立请求与确认时间镜像 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 表达工作责任是否仍可继续、被阻塞或已经结束 | `status` | reuse | `status` | 公共条件状态入口适用，由本文定义 WorkCase 三状态闭集 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 回指目标、范围和成功标准的形成依据 | `source-refs` | reuse | `source-refs` | 公共来源统一替代 V3 `source` 与 `input_refs` | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 支持验证、阻塞和关闭判断 | `evidence-refs` | reuse | `evidence-refs` | 公共证据引用负责定位依据，不用自由文本复制命令日志 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 表达依赖、剩余责任承接或替代关系 | `relations` | reuse | `relations` | 公共关系统一替代 `related_*` 和 `followup_refs` | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 直接恢复当前进展、边界和剩余工作 | `current-summary,title` | promote | `current-summary` | Spark 与 WorkCase 都需要非历史的当前语义快照；共同基线一致，由类型绑定收紧 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 排序同类型未终态 WorkCase 的相对处理优先级 | `priority` | promote | `priority` | 与 Spark 优先级同样只排序本类型未终态入口，不构成授权或执行顺序 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 说明关闭为何成立以及剩余责任如何收口 | `disposition-summary` | promote | `disposition-summary` | 与 Spark 终态处置具有相同共同基线；验证结论与结果枚举仍分别表达 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 记录 WorkCase 终态首次有效成立时间 | `closed-at` | promote | `closed-at` | 与 Spark 终态时间完全同义，不能另建关闭时间字段 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 表达该工作责任期望达成什么状态 | `current-summary,title` | differentiate | `workcase-goal` | 当前摘要描述现在，标题只识别对象；目标描述期望达成状态 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 表达该责任包含与明确不包含什么 | `current-summary,workcase-goal` | differentiate | `workcase-scope` | 目标和当前摘要都不能稳定替代承诺边界与排除项 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 表达哪些可观察条件共同构成目标达成 | `evidence-refs,workcase-goal` | differentiate | `workcase-success-criteria` | 目标说明期望，证据只定位依据；成功标准定义可检查的验收边界 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 说明实际验证覆盖、结果与未验证范围 | `disposition-summary,evidence-refs,workcase-validation-summary` | reuse | `workcase-validation-summary` | 该字段已因 Pitfall 的同义验证需求提升为共享定义；WorkCase 继续收紧为成功标准的实际验证覆盖 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0002` |
| 说明当前为什么不能继续以及解除条件 | `current-summary,disposition-summary` | differentiate | `workcase-blocking-summary` | 当前快照不应隐藏明确阻塞条件，终态说明只在关闭时出现 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |
| 结构化区分关闭是完成、部分完成、取消、替代或未达成 | `disposition-summary,status` | differentiate | `workcase-closure-outcome` | `closed` 不等于成功，终态说明又不能替代稳定结果分类 | `workcase-fact-type::5. WorkCase 类型定义::field-review-0001` |

### 字段独立复核

| review_key | reviewer | reviewed_scope | findings | disposition |
|---|---|---|---|---|
| `field-review-0001` | independent-workcase-spec-review-agent | WorkCase 对象粒度、准入、状态、关闭、关系、全部字段与结构准入提案 | V3 七状态、整个 orchestration、执行项、review receipt、revision_history 和请求时间属于行动运行态；24 个实例已出现双层状态漂移；当前事实只需目标、范围、成功标准、当前摘要、阻塞、验证与终态 | 状态收敛为 open/blocked/closed；排除执行项和历史日志；提升四个同义字段；新增六个 WorkCase 字段 |
| `field-review-0002` | independent-workcase-field-audit-agent | 24 个 V3 WorkCase、122 个执行项、当前统一登记及全部候选字段，并回读 Pitfall 准入后的字段提升 | 来源、证据和关系可统一；验证结论不能由 evidence refs 替代；Pitfall 具有同义验证摘要需求；执行项存在恢复诉求但与行动模板边界冲突；evolution 与 revision history 容易恢复日志负担 | 将 validation summary 提升为 WorkCase/Pitfall 共享字段；执行步骤留在行动计划或模板；WorkCase 不复用 Spark evolution，不新建 revision history、residual risks 或 followup 字段 |

### 类型字段使用绑定

| field_key | field_path | presence | type_constraints |
|---|---|---|---|
| `object-id` | `object_id` | required | 必须匹配 `workcase-[0-9]{4,}`；分配后不得因标题、路径、状态或内容改变而变化 |
| `fact-type-key` | `fact_type_key` | required | 唯一允许值为 `workcase` |
| `title` | `title` | required | 简短识别工作责任，不复制 goal 或 summary |
| `created-at` | `created_at` | required | 只使用有依据的首次形成时间 |
| `updated-at` | `updated_at` | required | 目标、范围、成功标准、当前摘要、优先级、状态、验证、来源、证据、关系或关闭事实实质变化并回读后更新 |
| `status` | `status` | required | 只使用 `open`、`blocked`、`closed` |
| `source-refs` | `source_refs` | required | 至少一项；必须能重新定位目标、范围和成功标准的形成依据及必要授权来源 |
| `evidence-refs` | `evidence_refs` | conditional | `blocked` 或 `closed` 时必填；open 状态声明已验证进展时必填；只定位实际依据 |
| `relations` | `relations` | conditional | 只有存在本文闭集中的有向关系时出现；无关系时省略 |
| `current-summary` | `summary` | required | 说明当前进展、范围内剩余工作、当前不确定性和下一判断，不复制验证结论、完整计划或历史 |
| `priority` | `priority` | conditional | `open` 或 `blocked` 时必填并只使用 `P0`、`P1`、`P2`、`P3`；`closed` 时省略；只排序当前 WorkCase 队列 |
| `disposition-summary` | `disposition_summary` | conditional | `closed` 时必填，未终态时禁止；必须说明完成与未完成边界、残余内容以及每项承接结论 |
| `closed-at` | `closed_at` | conditional | `closed` 时必填，未终态时禁止；使用带时区 RFC 3339 date-time且不得晚于 updated_at |
| `workcase-goal` | `goal` | required | none |
| `workcase-scope` | `scope` | required | none |
| `workcase-success-criteria` | `success_criteria` | required | none |
| `workcase-validation-summary` | `validation_summary` | conditional | 声称任何成功标准已验证时出现；`closed` 时必填；逐项说明通过、失败、豁免与未验证范围，依据进入 evidence_refs |
| `workcase-blocking-summary` | `blocking_summary` | conditional | 出现条件：status 为 `blocked` 时必填，其他状态禁止 |
| `workcase-closure-outcome` | `closure_outcome` | conditional | 出现条件：status 为 `closed` 时必填，其他状态禁止 |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `workcase-goal` | `goal` | string | WorkCase 期望达成并可独立判断关闭的单一目标状态 | 不表示标题、当前进展、步骤、成功标准或结果 | 必填非空；必须能够与范围和成功标准共同产生独立关闭判断；实质改成另一目标时新建对象 |
| `workcase-scope` | `scope` | string | WorkCase 承诺覆盖的内容、重要约束和明确排除边界 | 不表示当前进展、完整计划、实现细节或来源全文 | 必填非空；边界变化时同步复核目标、成功标准、授权和对象身份 |
| `workcase-success-criteria` | `success_criteria` | array | 共同构成目标达成判断的可观察条件闭集 | 不表示执行步骤、todo 状态、证据、测试命令或关闭结果 | 至少一项非空唯一字符串；每项可独立检查；不嵌入 checklist 标记或可变完成状态 |
| `workcase-blocking-summary` | `blocking_summary` | string | WorkCase 当前不能继续的具体事实、影响范围和解除条件 | 不表示低优先级、普通剩余工作、失败历史或终态理由 | 非空；解除条件必须可观察且有依据；不保留已经解除的历史阻塞占位 |
| `workcase-closure-outcome` | `closure_outcome` | string | WorkCase 在当前身份下停止推进时的结果分类 | 不表示状态、成功标准验证详情、终态理由或 Git 已提交 | 闭集 completed、partial、cancelled、superseded、not-achieved；completed 要求全部成功标准有充分满足依据 |

### Schema 与对象载体

WorkCase 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `facts/workcases/<object_id>.yaml`。文件名必须与 `object_id` 完全一致；标题、状态和目录移动不得参与身份计算。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义和类型专属字段定义组合。WorkCase 不得出现 `orchestration`、`execution_items`、`revision_history`、`plan_confirmed_at`、review receipt、Human confirmation 对象、`residual_risks`、`followup_refs`、按目标类型拆分的关系字段或其它未登记内容。

## 6. 对象语义与生命周期

一个 WorkCase 只表达一个能够独立判断关闭的工作责任。`goal` 和 `scope` 定义承诺，`success_criteria` 定义可检查验收边界，`summary` 维护当前快照。步骤多少、是否使用子 Agent、是否并行、是否正在自检或等待某次 review 都不改变 WorkCase 领域状态。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `open` | 目标已经准入，仍有未完成内容，且在当前授权和已知条件下可以继续推进 | `priority` 必填；阻塞与终态字段禁止；summary 明确剩余工作 |
| `blocked` | 仍有未完成内容，但明确的外部依赖、Human 决定、授权、证据或能力缺口使当前不能继续 | `priority`、`blocking_summary`、`evidence_refs` 必填；终态字段禁止 |
| `closed` | 该 WorkCase 身份下不再继续推进，不等于成功、已提交或下游责任完成 | priority 与 blocking_summary 省略；validation_summary、closure_outcome、disposition_summary、closed_at、evidence_refs 必填 |

新建对象的初始状态只能是 `open` 或 `blocked`：当前授权与已知条件允许继续时使用 `open`；准入已经成立但创建时已有具体、可证且当前阻止继续的条件时可以直接使用 `blocked`，不得先写虚假 open 转换。`closed` 不能作为普通新建初态；历史迁移必须重建实际生命周期依据，事实更正按 05 处理。

正常转换只有 `open → blocked`、`blocked → open`、`open → closed` 和 `blocked → closed`。`closed` 不直接重开；后来出现的新工作建立新 WorkCase，确属替代时由新对象使用 `supersedes` 指向旧对象。原终态记录本身错误时按 05 的事实更正规则修正，不把更正伪装成重新推进。

`closed` 必须逐项核对成功标准。`completed` 要求每项均有充分满足依据；`partial` 和 `not-achieved` 必须明确未满足或未验证项；`cancelled` 必须说明停止依据；`superseded` 必须由本对象使用 `routed-to` 指向接替责任的当前 open 或 blocked WorkCase。新对象需要表达身份沿革时可以单向 `supersedes` 本对象，但该入向关系由 Code 派生读取，不是旧对象关闭成立的第二权威，也不能替代旧对象的 `routed-to` 承接声明。所有仍适用责任都必须由 `routed-to` 指向能够按目标类型与当前状态稳定承接该具体责任的事实对象，或在 `disposition_summary` 明确证明没有残余内容。

## 7. 来源、证据与关系

`source_refs` 至少回指目标、范围和成功标准的形成依据。来源可以是 Human 输入、Spark、规范、issue、代码、文档或其它可定位内容；Human 当前指令只有在能够稳定定位时才进入长期对象，不能伪造对话 locator。WorkCase 来自 Spark 时可以把 Spark 作为来源；Spark 的 `routed-to` 已是分流关系，WorkCase 不复制反向来源关系。

`evidence_refs` 支持已验证进展、阻塞事实、成功标准判断和关闭结果。`validation_summary` 说明结论，引用负责定位依据；二者不能互相替代。命令返回成功、文件存在、关系存在、Agent 声明或 Human 回应都只能在其实际覆盖范围内作为依据。

WorkCase `relation_key` 闭集为：

| relation_key | source condition | target condition | cardinality | reverse authority | missing and cycle boundary |
|---|---|---|---|---|---|
| `depends-on` | source 为 open 或 blocked；依赖必须实际影响当前目标继续 | target 是可恢复的 open 或 blocked `workcase`，且其明确结果是当前对象的真实前置条件 | 每个不同目标最多一条；可以有多个不同依赖 | 反向 `depended-on-by` 只由 Code 派生，不写回 | 目标缺失、终态、类型不符或自指时无效；全部 depends-on 边组成的有向图不得成环 |
| `routed-to` | 只由 closed source 声明，且存在仍适用的具体剩余责任；没有残余时不得写占位关系 | 目标必须按自身类型与当前状态能够稳定承接该具体责任；WorkCase 目标只允许 open/blocked，Spark 目标只允许 open，其它类型必须由当前类型来源证明相应承接能力 | 每项不同剩余责任至少一个目标；同一责任与目标不得重复 | 反向 `routed-from` 只由 Code 派生，不写回；目标不复制来源关系 | 目标缺失、终态、类型或承接能力不符、自指时无效；routed-to 责任承接边不得形成直接或间接循环，也不得互相证明关闭 |
| `supersedes` | 只在新对象创建为 open/blocked 时建立；之后可以随 source 保留 | target 是同一管辖项目内可恢复的 closed `workcase`，且新对象确实替代其身份或责任 | 每个不同旧对象最多一条；合并多个旧责任时允许多个目标 | 反向 `superseded-by` 只由 Code 派生，不写回；不作为旧对象关闭证明 | 目标缺失、非终态、类型不符或自指时无效；全部 supersedes 边组成的有向图必须是 DAG |

关系目标必须在当前管辖配置中可恢复；跨项目 `depends-on` 或 `routed-to` 必须按 05 提供治理来源并证明实际承接，`supersedes` 限定同一管辖项目。普通文件、规范、commit 或外部页面不是事实对象，分别进入来源或证据引用。关系自身不是充分证据；基数、目标能力、缺失与循环规则不满足时，相应关系和依赖它的状态或关闭判断都不成立。

## 8. 对象变化与授权边界

创建前必须召回相邻 WorkCase、Spark 和其它稳定来源，先判断更新、拆分、分流或保持当前上下文，再分配新身份。仅有多个步骤不构成拆分理由；多个目标能够独立验收、阻塞、取消或关闭时不得捆绑。

目标、范围或成功标准实质变化时，必须重新检查来源、当前授权、对象身份和已有验证。仍是同一工作责任时更新当前字段与 `updated_at`；变成不同关闭责任时新建对象并明确旧对象处置。过程历史由 Git 保留，不写 revision history。

closed 文件默认保留在当前类型载体中供历史、来源和关系回读；本文不建立 `archived` 状态或归档位置。删除只有在适用来源规则允许、全部引用和剩余责任已经处置且不会丢失仍适用事实时才成立，不能用删除替代 closed。WorkCase 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象（包括 closed）、引用消费者和仍适用责任；全部未终态责任还必须获得明确承接，不得只删除类型规范或隐藏对象目录。

具体保留给 Human 的决定见 §10。Human 已明确要求推进时，授权范围内更新 summary、验证、证据和客观状态不重复建立 Gate；任何授权都不使技术验证、来源回读和字段约束自动成立。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| WorkCase 类型定义 | 新建或实质修改本文时 | 唯一声明、字段准入、绑定、状态、来源、证据、关系和独立复核完整且无第二权威 | 05、统一登记、本文、V3 反例和独立复核记录 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 `workcase` 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| WorkCase 准入与查重 | 创建新对象前 | 单一目标、范围与成功标准清楚，确需跨行动事实，已召回相邻对象且没有可无损更新入口 | 当前输入、来源定位、召回结果与 AI 语义比较 | AI 来源回读与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、更新已有对象、拆分或转 Spark |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 WorkCase 消费；报告字段和未验证范围 |
| 状态、验证与关闭 | 写入 blocked 或准备 closed 时 | 阻塞有具体解除条件；成功标准逐项核对；结果、终态说明、证据和承接一致 | 当前对象、实际验证、来源、证据、目标对象与 Human 决定 | AI 语义审核、目标回读和结构校验 | 当次状态、验证与关闭声明 | 保持 open 或 blocked；补证据、承接或进入 Human Gate |
| 来源、证据与关系 | 写入当前说明、验证结论、阻塞或关系时 | 来源可定位，证据支持声明，关系方向、目标和状态稳定且无环 | 原始来源、目标对象、引用成员和当前说明 | 来源与目标回读；Code 检查结构、身份及可确定环 | 当次声明与关系 | 缩小声明、修正引用或移除无依据关系 |
| 变更与回读 | 创建、更新、更正、拆分、合并、替代或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 语义审核必须检查：对象是否值得建立；目标、范围和成功标准是否清楚且只有一个关闭责任；是否与现有对象重复；当前摘要是否真实；证据是否覆盖所述结论；阻塞是否具体；关闭结果、残余内容和关系是否成立。

Code 可以确定性检查：载体路径和文件名；对象身份格式；Schema 闭集；字段类型与非空；状态、优先级、关闭结果和关系 key 值闭集；状态条件字段；时间格式与顺序；引用 shape、目标存在性和类型；自指，以及可确定的 depends-on 依赖环、routed-to 责任承接环和 supersedes 替代环。Code 不得自动判断目标是否合理、成功标准是否真正满足、证据是否充分、目标事实上能否承接责任、风险是否可接受或两个自然语言目标是否同义。

最低验证样例必须覆盖：

1. open、blocked、五种 closure outcome 的有效对象；
2. 每个状态缺少条件字段、带禁止字段、空值和未知字段；
3. 成功标准为空、含 checklist 状态或重复项；
4. completed 但验证范围不完整、blocked 无解除条件、closed 有未承接残余内容；
5. 三种关系各自的有效与无效 source/target 状态、基数、跨项目治理引用、自指与缺失目标，以及 depends-on 依赖环、routed-to 责任承接环和 supersedes 替代环；
6. 旧 `orchestration`、execution item、review receipt、related_* 和空占位被拒绝；
7. 历史 V3 实例只能作为迁移输入，不能直接通过 V4 Schema。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 创建、扩大范围或改变目标超出 Human 当前授权；
2. 目标、范围或成功标准存在实质歧义，AI 无法据来源无损确定；
3. 接受 `partial`、`not-achieved`、残余风险、豁免、取消或替代需要 Human 决定；
4. 行动本身包含高影响、不可逆或另有来源保留给 Human 的决定；
5. 合并、拆分、删除或重组可能丢失身份、来源、证据或承接事实。

Human 已明确要求推进时，授权范围内更新 summary、验证、证据和客观状态不重复进入 Gate。Human 确认不能替代技术验证；技术验证也不能替代保留给 Human 的风险接受或范围决定。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入或宣称 WorkCase 成立：

1. 目标、范围或成功标准不清楚，或多个独立关闭责任被捆绑；
2. 未完成现有对象召回与语义查重；
3. 来源无法按所需精度回指，或把推测、计划、Agent 输出、命令成功冒充当前事实；
4. blocked 没有具体阻塞事实、影响和解除条件；
5. 缺少充分验证却声明成功标准满足或 WorkCase 完成；
6. closed 仍有适用责任但没有稳定承接，或把 closed 表述成成功、已提交或下游完成；
7. 关系目标失效、类型或状态不符、自指或成环；
8. 准备写入空占位、V3 orchestration、执行项、review receipt、历史日志或其它未登记字段；
9. 高影响行动、范围扩张或风险接受缺少实际授权；
10. 正在从本文越界推导实例服务、Helper、迁移、Web 或行动模板已经成立；
11. 准备预埋执行项结构，而没有重新比较行动模板、多个 WorkCase 与新结构的净负担并完成统一字段准入。

暂停只影响相应候选、对象、关系或关闭声明。期间可以继续只读召回、来源核对、目标拆分、证据补充、正确承载位置比较和 Human Gate 准备；实例服务、迁移与消费实现必须等待后续阶段明确推进。
