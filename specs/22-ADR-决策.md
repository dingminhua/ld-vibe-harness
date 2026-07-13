# ADR / 决策记录

```yaml
ldvh_spec:
  spec_key: "adr-fact-type"
  spec_id: "22"
  spec_kind: "spec"
  title: "ADR / 决策记录"
  status: "active"
  canonical_path: "specs/22-ADR-决策.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 ADR 事实类型的对象边界、Schema、生命周期、来源、关系、取舍与验证规则"
  scope: "管辖项目中已经实际作出、具有跨行动持续影响并需要稳定保存选择、适用边界、理由和后果的单一决定"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `adr` 事实类型的唯一定义来源；它不使 ADR 读取、创建、校验、迁移、Helper、Code、tests、行动模板或 Web 能力自动成立。V3 ADR 规范和实现只作为设计与反例输入；V3 没有可供审计的 ADR 实例，因此任何字段和状态都不能以历史实例消费证明必要性。

## 1. 价值判断

ADR 保存一个已经实际成立、会跨行动持续影响项目的决定，使后续 AI 能定位当时解决了什么选择问题、选择了什么、适用哪里、为何这样选择以及接受了哪些后果，而不必从聊天、提交或实现结果反向猜测决定。

ADR 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 与行动模板承担；ADR 不承载实施计划、任务进度或执行授权。新增成本包括查重、持续维护、Schema、迁移和消费；通过只记录已成立决定、一个决定问题、三状态、六个专属字段且不保存提案或过程历史，维护成本被限制在低于反复重建重要取舍、重复争论和错误泛化的范围。不能证明这种净收益的判断不准入 ADR。

历史 V3 没有 ADR 实例，只有规范和 validator 草案。这能证明“长期取舍与理由需要稳定位置”的设计意图，不能证明 `archived`、固定影响模板、传统 alternatives 数组或任何旧字段已经被实际消费。V4 因而从最小可解释决定记录开始，不按传统 ADR 模板或 V3 Code 快照补齐未经证明的结构。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定 Git 可追踪事实源、当前 Working Tree、来源回指和稳定事实边界。

ADR 是决定事实，不是“决策补丁”或规则来源。规范、项目规则、Code、Web 和行动模板各自的当前来源决定实际规则与行为；ADR 只能记录决定和理由。Human 决定只证明决定及其作用范围，不证明技术状态、实现完成、规则生效或后续行动已经获准。

## 3. 职责边界

本文负责定义：

1. `adr` 的类型语义、对象粒度、准入和排除边界；
2. ADR 的唯一当前承载位置、完整 Schema、状态和终态处置；
3. 决策问题、已作决定、适用边界、理由、后果和决定时间；
4. ADR 来源、证据、替代关系、变更、更正、删除和类型退出边界；
5. ADR 的验证要求、Human Gate、Stop Conditions 和最小失败范围。

本文不负责定义：

1. 正式规范、项目规则、字段契约、Human Gate 规则或其它可执行纪律；
2. 提案、选项收集、研究正文、实施计划、执行步骤、任务状态或技术完成情况；
3. WorkCase、Spark 或其它事实类型的语义与生命周期；
4. Helper API、CLI、Web 表单、Hook、迁移兼容或文件分配算法；
5. 仅因 ADR 存在而产生的执行、写入、提交、发布或风险接受授权。

AI 负责判断决定是否已实际成立、是否值得对象化、是否重复、来源授权与适用边界是否准确、理由与后果是否据实；Code 只可按当前来源检查固定结构、值闭集、引用和状态条件。

## 4. 适用范围

一个判断只有同时满足以下条件，才可以形成 ADR：

1. 决策问题清楚，并且一个方向已经实际被选择；仍在比较选项的内容不准入；
2. 选择存在真实、可说明的长期取舍，跨行动影响架构、接口、事实归属、兼容性、风险或协作边界；
3. 适用对象、条件、范围、明确排除项、理由和预期后果能够稳定表达；
4. 决定来源、作出决定的授权范围和实际决定时间可以回指，不能事后补造“当时已决定”；
5. 已召回当前 ADR、适用规范、Spark、WorkCase 和相邻稳定来源，没有可无损更新或已经自然承载的现有位置；
6. 该决定有独立替代与追溯价值，对象化减少的理解与重复争论负担高于维护成本。

一个 ADR 只回答一个可以独立替代或退出的决策问题。多项选择只有在必须整体成立、整体替代且不能独立变化时才可合并；否则拆分。

以下内容不得形成 ADR：尚未选择的方案或开放问题；明确执行目标与实现任务；正式规则、Human Gate、操作纪律或字段契约；当前行动内可逆且低影响的技术选择；偏好、会议纪要、聊天摘要、执行日志、测试结果或研究正文；已经被当前规范无损表达且没有独立决策生命周期的理由；无来源的事后合理化。

未决问题保持 Spark；实施或吸收决定使用 WorkCase。ADR 回答“选择什么、为何、适用哪里”，WorkCase 回答“完成什么、如何验收、当前是否阻塞或关闭”。规范始终是规则权威；ADR 与当前规范冲突时先遵守规范，并暂停把冲突 ADR 作为当前决定消费，直至冲突得到获准处置。

## 5. ADR 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `adr` | 已经实际作出、具有跨行动持续影响并需要保存选择、适用边界、理由和后果的单一决定事实 | `adr-fact-type::5. ADR 类型定义` |

### 结构准入记录

本类型没有结构准入事项

### 类型专属结构定义

本类型没有类型专属结构

### 字段准入记录

| information_need | compared_field_keys | decision | resulting_field_key | rationale | review_ref |
|---|---|---|---|---|---|
| 稳定识别同一 ADR | `object-id` | reuse | `object-id` | 公共对象身份无损适用，只收紧 ADR 格式 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 声明对象属于 ADR 类型 | `fact-type-key` | reuse | `fact-type-key` | 公共类型身份无损适用，固定为 `adr` | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 提供 Human 与 AI 可读短标签 | `title` | reuse | `title` | 公共标题只用于识别，不承担决定内容 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 记录对象首次形成时间 | `created-at` | reuse | `created-at` | 公共形成时间无损适用，与实际决定时间分开 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 记录当前对象内容最近实质变化时间 | `updated-at` | reuse | `updated-at` | 公共更新时间无损适用，不建立状态历史 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 表达决定是否仍是当前选择、已被替代或无替代退出 | `status` | reuse | `status` | 公共条件状态入口适用，由本文定义 ADR 三状态闭集 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 回指决策问题、输入和实际决定来源 | `source-refs` | reuse | `source-refs` | 公共来源负责重新定位问题、输入与决定来源 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 支持决定确已成立、授权范围与终态判断 | `evidence-refs` | reuse | `evidence-refs` | 公共证据引用定位实际依据，不由决定文本自证 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 表达一个 ADR 对旧 ADR 的单向整体替代 | `relations` | reuse | `relations` | 公共关系统一承载 supersedes，不恢复 related_* 或 superseded_by | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 说明 superseded 或 retired 为什么成立以及剩余适用边界 | `disposition-summary,status` | reuse | `disposition-summary` | 与 Spark、WorkCase 的终态处置共同基线一致；ADR 只收紧终态内容 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 记录 ADR 首次有效进入终态的时间 | `closed-at,updated-at` | reuse | `closed-at` | 与其它类型的终态首次成立时间完全同义 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 表达该 ADR 必须解决的单一选择问题 | `current-summary,workcase-goal` | differentiate | `adr-decision-question` | 当前摘要是可变快照，WorkCase goal 是期望工作结果；二者都不表示决定所回答的选择问题 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 表达已经实际选择的方向 | `current-summary,workcase-goal` | differentiate | `adr-decision` | 决定是稳定选择事实，不是进展快照、目标或可执行规则正文 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 表达决定适用的对象、条件、范围和排除项 | `adr-applicability,workcase-scope` | reuse | `adr-applicability` | 该字段已因 Pitfall 的同义适用边界需求提升为共享定义；ADR 继续收紧为决定成立与适用的边界，仍不同于 WorkCase 承诺范围 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 表达选择理由、关键取舍与未选主要方向 | `evidence-refs,source-refs` | differentiate | `adr-rationale` | 引用只定位依据，不能替代可读取舍判断；第一版不建立 alternatives 结构 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |
| 表达决定接受的正负后果、限制和风险 | `disposition-summary,workcase-validation-summary` | differentiate | `adr-consequences` | 验证摘要说明工作验证，终态处置说明退出；均不能承载决定成立时接受的后果 | `adr-fact-type::5. ADR 类型定义::field-review-0001` |
| 记录决定在来源与授权范围内实际成立的时间 | `closed-at,created-at,evolution-at,updated-at` | differentiate | `adr-decided-at` | closed-at 是终态时间，evolution-at 是 Spark 内部语义转折时间，created-at 与 updated-at 是对象形成和最近更新时间；均不能替代决定实际成立时间 | `adr-fact-type::5. ADR 类型定义::field-review-0002` |

### 字段独立复核

| review_key | reviewer | reviewed_scope | findings | disposition |
|---|---|---|---|---|
| `field-review-0001` | independent-adr-spec-review-agent | ADR 对象价值、准入、规范/WorkCase/Spark 边界、状态、关系、Human Gate 及全部字段提案 | V3 把 ADR 当决策补丁并用 absorbed/archived 表示规范吸收，会与正式来源争权；未决内容、行动纪律和实现计划不应对象化为 ADR | 改为决定事实；使用 active/superseded/retired；第一版只保留 supersedes；不建立 absorption 状态 |
| `field-review-0002` | independent-adr-field-audit-agent | V3 22、历史 validator、相关 Spark、当前统一登记及全部字段准入提案，并回读 Pitfall 准入后的字段提升 | V3 没有 ADR 实例，不能证明传统模板消费；公共身份、来源、证据、终态与 applicability 可复用，summary/priority/evolution/WorkCase 字段不适用 | 新增五个 ADR type 字段并把 applicability 提升为 ADR/Pitfall 共享字段；扩展两个共享终态字段到 ADR；不建 alternatives、affects、archive reason 或实现状态 |

### 类型字段使用绑定

| field_key | field_path | presence | type_constraints |
|---|---|---|---|
| `object-id` | `object_id` | required | 必须匹配 `adr-[0-9]{4,}`；分配后不得因标题、状态或内容改变而变化 |
| `fact-type-key` | `fact_type_key` | required | 唯一允许值为 `adr` |
| `title` | `title` | required | 简短识别决定主题，不复制 decision_question 或 decision |
| `created-at` | `created_at` | required | 只使用对象首次按 ADR 形成的有依据时间；可以晚于 decided_at |
| `updated-at` | `updated_at` | required | 六个专属字段有来源的事实更正，或来源、证据、状态、关系、终态事实实质变化并回读后更新；不授权原地改写决定语义 |
| `status` | `status` | required | 只使用 `active`、`superseded`、`retired` |
| `source-refs` | `source_refs` | required | 至少一项；必须能重新定位决策问题、关键输入和实际决定来源 |
| `evidence-refs` | `evidence_refs` | required | 至少一项；必须支持决定确已成立及其授权范围；终态时还要支持替代或退出判断 |
| `relations` | `relations` | conditional | 只有 supersedes 关系存在时出现；无关系时省略 |
| `disposition-summary` | `disposition_summary` | conditional | `superseded` 或 `retired` 时必填，active 时禁止；说明替代或退出依据、剩余适用边界和承接结论 |
| `closed-at` | `closed_at` | conditional | `superseded` 或 `retired` 时必填，active 时禁止；继承 `created_at <= closed_at <= updated_at` |
| `adr-decision-question` | `decision_question` | required | none |
| `adr-decision` | `decision` | required | none |
| `adr-applicability` | `applicability` | required | 明确适用对象、环境、条件、范围和排除项；不得无依据泛化 |
| `adr-rationale` | `rationale` | required | none |
| `adr-consequences` | `consequences` | required | none |
| `adr-decided-at` | `decided_at` | required | none |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `adr-decision-question` | `decision_question` | string | ADR 所回答的单一长期选择问题 | 不表示当前摘要、工作目标、研究问题列表或标题 | 必填非空；必须能独立替代或退出；多个独立问题必须拆分 |
| `adr-decision` | `decision` | string | 在可回指来源与授权范围内已经实际选择的方向 | 不表示提案、规则正文、实施计划、完成状态或对未来行为的自行授权 | 必填非空；实质改变时建立新 ADR 并按 supersedes 处置，原记录只做事实更正 |
| `adr-rationale` | `rationale` | string | 选择理由、关键取舍以及未选择主要方向的原因 | 不表示来源全文、证据列表、传统 alternatives 结构或事后合理化 | 必填非空；只保留理解决定所需取舍；事实依据进入 refs |
| `adr-consequences` | `consequences` | string | 作出决定时接受的正负后果、限制、风险和后续义务 | 不表示规范条款、实施 todo、验证结果、完成声明或终态处置 | 必填非空；未知后果必须如实标明，不为满足模板补造固定段落 |
| `adr-decided-at` | `decided_at` | string | 决定在所述来源与授权范围内实际成立的时间 | 不表示 ADR 对象创建、最近更新、实现或规则生效时间 | 必填；带时区 RFC 3339 date-time；`decided_at <= created_at <= updated_at`，补录历史决定不得用创建时间冒充 |

### Schema 与对象载体

ADR 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `facts/adrs/<object_id>.yaml`。文件名必须与 `object_id` 完全一致；标题、状态和目录移动不得参与身份计算。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义和类型专属字段定义组合。ADR 不得出现 current summary、priority、evolution、WorkCase 字段、`alternatives` 结构、`affects`、`superseded_by`、`archive_reason`、`deprecated_reason`、implementation/absorption status、revision history、按目标类型拆分的关系或其它未登记内容。

## 6. 对象语义与生命周期

ADR 只记录已经成立的决定。选项仍在收集、方向仍在比较或授权尚未成立时不得创建 proposed ADR；保留在 Spark、Study、WorkCase 或当前行动中。一个决定被写入 ADR 不表示已经实现、已进入规范、具有规则权威或后续行动已获准。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 决定在其声明适用范围内仍是当前选择 | 只能作为新建初态；终态字段禁止；决定来源与授权证据持续可回指；不表示规则权威或实现状态 |
| `superseded` | 原决定已经被一个后来成立的 ADR 整体替代 | disposition_summary、closed_at、evidence_refs 必填；旧对象必须成为一个在关系建立时为 active 的新 ADR 的有效 supersedes 目标；替代源后来进入终态不使既有边失效 |
| `retired` | 原决定因适用条件消失、方向撤回或不再需要而退出当前选择，且没有被新 ADR 整体替代 | disposition_summary、closed_at、evidence_refs 必填；必须有具体退出依据，不得用低优先级或已实现冒充退出 |

初始状态只能是 `active`。正常转换只有 `active → superseded` 和 `active → retired`；终态不直接重开。六个 ADR 专属字段发生实质改变时建立新 ADR；只有来源充分且不改变原决定语义的事实更正可以原地修正，不把语义改写伪装成生命周期变化。

规范、Code 或其它正式来源吸收决定不会使 ADR 自动终态。ADR 即使 active 也只是当前决定记录，实际规则与行为始终来自相应正式来源；吸收位置和实现结果按实际作用进入 evidence_refs。V3 `archived` 把“已经被吸收”和“不再是当前决定”错误绑定，V4 不恢复。

## 7. 来源、证据与替代关系

`source_refs` 回指决策问题、关键输入和实际决定来源。`evidence_refs` 必须支持选择确已成立及其授权范围；Human 当前指令可以成为证据，但必须能够稳定定位，不能伪造对话 locator。事实来源、Human 确认、提交、测试和实现结果各自只证明实际覆盖范围，不能互相替代。

ADR 来自 Spark 或 WorkCase 时可以把源对象作为 source_ref；Spark 的 routed-to 已表达分流，ADR 不复制反向关系。实施决定的 WorkCase 可以把 ADR 作为 source_ref；ADR 不维护双写 related_workcases。规范、Code、commit、文档或外部页面不是事实对象，分别进入 source_refs 或 evidence_refs。

ADR `relation_key` 第一版只允许 `supersedes`：

| source condition | target condition | cardinality | reverse authority | missing and cycle boundary |
|---|---|---|---|---|
| 关系建立时新 ADR 必须为 active；关系与旧 ADR 状态转换在同一获准变更中成立，建立后可以随 source 后续进入终态而永久保留 | 目标是可恢复的 superseded ADR，且关系建立前为 active；只允许同一管辖项目的 `adr` | 每个旧 ADR 全生命周期最多一个直接 supersedes source，既有关系不因 source 状态变化而释放基数；一个新 ADR 只有在多个旧决定不可分割合并时才可指向多个不同目标 | `superseded-by` 只由 Code 派生，不写回；旧 ADR 不复制新对象引用 | 目标缺失、非 superseded、类型或项目不符、自指时无效；必须满足 `target.decided_at <= source.decided_at <= target.closed_at`；全部保留的 supersedes 边必须组成 DAG |

如果新决定只替代旧决定的一部分，不能把旧对象整体标为 superseded；应拆分新决定或让旧决定保持 active，并修正适用边界所需的正式来源。关系存在不单独证明替代成立，必须与两个对象、来源、证据、适用范围和同一变更一致。

## 8. 变更、删除与类型退出

创建前必须召回相邻 ADR、适用规范、Spark、WorkCase 和稳定来源，先判断不对象化、更新事实更正、拆分或建立新身份。ADR 创建后，decision_question、decision、applicability、rationale、consequences 和 decided_at 六个专属字段除有来源的事实更正外均不得原地实质改变；任何语义变化都必须建立新 ADR，并在整体替代成立时走 supersedes。文字澄清只有不改变原决定语义且有来源时才作为事实更正。

active、superseded 和 retired 文件均默认保留在当前载体中供来源、理由和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失决定历史时才成立，不能用删除代替终态。

ADR 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用决定；全部 active 决定还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| ADR 类型定义 | 新建或实质修改本文时 | 唯一声明、字段准入、绑定、状态、来源、证据、关系和独立复核完整且无第二权威 | 05、统一登记、本文、V3 反例与独立复核 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 `adr` 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| ADR 准入与查重 | 创建对象前 | 单一选择已实际成立、影响长期、边界与理由清楚、来源授权可回指且没有现有无损承载 | 当前输入、决定来源、授权依据、召回结果与 AI 语义比较 | AI 来源回读与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、Spark、WorkCase、Study 或已有来源 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 ADR 消费；报告字段和未验证范围 |
| 决定与适用边界 | 创建或消费 active ADR 时 | 决定确已成立，授权、适用和排除范围有来源支持，未与当前规范或其它 active ADR 冲突 | source_refs、evidence_refs、当前规范、相邻 ADR 与 Human 决定 | AI 语义审核、来源与规范回读 | 当次决定及声明范围 | 不创建或暂停当前决定消费；缩小范围、补依据或进入 Human Gate |
| 替代或退出 | 准备 superseded 或 retired 时 | 新决定或退出依据成立，两个对象、关系、证据、适用边界和时间一致 | 新旧 ADR、来源、证据、当前规范与 Human 决定 | AI 语义审核、目标回读和结构校验 | 当次终态与替代声明 | 保持 active；修正替代范围、补证据或进入 Human Gate |
| 变更与回读 | 创建、更正、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核决定是否实际成立、是否值得对象化、对象粒度、来源授权、适用边界、理由、后果、与当前规范及 active ADR 的冲突、替代完整性和退出依据。V3 无实例意味着当前只能验证结构与语义边界，不能宣称真实 ADR 样本消费已经成立。

Code 可以确定性检查：载体、身份、Schema 闭集、字段类型与非空、状态值、状态条件、时间格式与顺序、引用 shape、目标身份与状态、自指、全部保留关系上的全生命周期单一直接替代源、跨对象时间顺序和 supersedes DAG。Code 不得判断决定是否真的值得记录、Human 是否拥有相应决定权、理由是否充分、适用范围是否被错误泛化、后果是否真实或自然语言决定是否互相冲突。

最低验证样例必须覆盖：active、superseded、retired；每个状态缺少条件字段或带禁止字段；decided_at 的对象内与 `target.decided_at <= source.decided_at <= target.closed_at` 跨对象边界；决定来源与授权缺失；未决提案冒充决定；多个独立问题捆绑；ADR 与当前规范或 active ADR 冲突；supersedes 的建立时与持久 source/target 状态、项目、全生命周期单一直接替代源、自指、缺失目标和全部保留关系 DAG；旧 patch/archived/deprecated/related_* 与空占位被拒绝；V3 没有实例可直接作为有效 fixture。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 决定本身属于产品方向、长期规则、重大架构、事实权威归属、Human Gate 变化或风险接受，且未由 Human 当前指令明确决定或授权 AI 在该范围自主选择；
2. 决定来源、授权主体或作用范围不清，AI 无法从当前来源无损确定；
3. 准备 supersede、retire、合并或拆分决定，实际取舍或剩余适用范围需要 Human 判断；
4. 修改 active ADR 的六个专属字段会实质改写原决定，而不是有来源的事实更正；
5. 删除或重组可能丢失决定身份、来源、证据、理由或替代历史。

Human 已明确作出决定，或明确授权 AI 在该技术范围自主选择时，记录 ADR 不因对象类型本身重复进入 Gate。Human 决定不能替代 Schema、来源回读、技术验证或正式规则写入；技术结果也不能替代保留给 Human 的取舍和风险接受。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入或宣称 ADR 成立：

1. 仍在比较选项、收集资料或等待决定，却准备创建 ADR；
2. 没有可回指的决定来源、授权范围或实际决定时间；
3. 正在把 ADR 写成规范补丁、项目纪律、执行计划、实现状态或行动授权；
4. 与当前规范或 active ADR 冲突，但没有完成获准的冲突处置；
5. 多个可以独立替代或退出的决定被捆绑；
6. decision、applicability、rationale 或 consequences 为空、过度泛化或事后补造；
7. 用关系、commit、测试成功或实现存在冒充决定已实施、规则已生效或行动已授权；
8. superseded 没有有效新 ADR 与单向关系，retired 没有具体退出依据；
9. 准备写入 proposed、archived、deprecated、alternatives、affects、superseded_by、related_*、空占位或其它未登记内容；
10. 高影响决定没有实际授权，或获准写入后没有回读与范围匹配验证。

暂停期间可以继续只读召回、来源与授权核对、决定拆分、适用边界澄清、证据补充、正式承载位置比较和 Human Gate 准备。只有选择实际成立、来源授权可回指、冲突与对象粒度得到处置、Schema 和关系一致并完成写后回读后，才能恢复相应范围。
