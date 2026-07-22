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

> 文件状态：`active`。本文是 `adr` 事实类型的唯一定义来源；它不使 ADR 读取、创建、校验、Helper、Code、tests、行动模板或 Web 能力自动成立。字段与状态的必要性只由当前准入审计、本文和独立复核证明，不能以任何外部实例替代。

## 1. 价值判断

ADR 保存一个已经实际成立、会跨行动持续影响项目的决定，使后续 AI 能定位当时解决了什么选择问题、选择了什么、适用哪里、为何这样选择以及接受了哪些后果，而不必从聊天、提交或实现结果反向猜测决定。

ADR 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 与行动模板承担；ADR 不承载实施计划、任务进度或执行授权。新增成本包括查重、持续维护、Schema、迁移和消费；通过只记录已成立决定、一个决定问题、三状态、六个专属字段且不保存提案或过程历史，维护成本被限制在低于反复重建重要取舍、重复争论和错误泛化的范围。不能证明这种净收益的判断不准入 ADR。

V4 从最小可解释决定记录开始，不按传统 ADR 模板或旧 Code 快照补齐未经证明的结构。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定管辖项目当前事实源、Working Tree、来源回指和稳定事实边界。

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

### 类型专属结构定义

本类型没有类型专属结构

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `adr-fact-type::5. ADR 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `adr-fact-type::5. ADR 类型定义` |
| `created-at` | required | `adr-fact-type::8. 变更、删除与类型退出` |
| `updated-at` | required | `adr-fact-type::8. 变更、删除与类型退出` |
| `status` | required | `adr-fact-type::6. 对象语义与生命周期` |
| `source-refs` | required | `adr-fact-type::7. 来源、证据与替代关系` |
| `evidence-refs` | required | `adr-fact-type::7. 来源、证据与替代关系` |
| `relations` | conditional | `adr-fact-type::7. 来源、证据与替代关系` |
| `disposition-summary` | conditional | `adr-fact-type::6. 对象语义与生命周期` |
| `closed-at` | conditional | `adr-fact-type::6. 对象语义与生命周期` |
| `adr-decision-question` | required | `inherit` |
| `adr-decision` | required | `inherit` |
| `adr-applicability` | required | `adr-fact-type::7. 来源、证据与替代关系` |
| `adr-rationale` | required | `inherit` |
| `adr-consequences` | required | `inherit` |
| `adr-decided-at` | required | `inherit` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `adr-decision-question` | `decision_question` | string | ADR 所回答的单一长期选择问题 | 不表示当前摘要、工作目标、研究问题列表或标题 | 必填非空；必须能独立替代或退出；多个独立问题必须拆分 |
| `adr-decision` | `decision` | string | 在可回指来源与授权范围内已经实际选择的方向 | 不表示提案、规则正文、实施计划、完成状态或对未来行为的自行授权 | 必填非空；实质改变时建立新 ADR 并按 supersedes 处置，原记录只做事实更正 |
| `adr-rationale` | `rationale` | string | 选择理由、关键取舍以及未选择主要方向的原因 | 不表示来源全文、证据列表、传统 alternatives 结构或事后合理化 | 必填非空；只保留理解决定所需取舍；事实依据进入 refs |
| `adr-consequences` | `consequences` | string | 作出决定时接受的正负后果、限制、风险和后续义务 | 不表示规范条款、实施 todo、验证结果、完成声明或终态处置 | 必填非空；未知后果必须如实标明，不为满足模板补造固定段落 |
| `adr-decided-at` | `decided_at` | string | 决定在所述来源与授权范围内实际成立的时间 | 不表示 ADR 对象创建、最近更新、实现或规则生效时间 | 必填；带时区 RFC 3339 date-time；`decided_at <= created_at <= updated_at`，补录历史决定不得用创建时间冒充 |

### Schema 与对象载体

ADR 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `ldvh-base/adrs/<object_id>.yaml`。`object_id` 必须匹配 `adr-[0-9]{4,}`；文件名必须与 `object_id` 完全一致，分配后的身份不得因标题、路径、状态或内容改变。`title` 只简短识别决定主题，不复制 `decision_question` 或 `decision`。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

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

规范、Code 或其它正式来源吸收决定不会使 ADR 自动终态。ADR 即使 active 也只是当前决定记录，实际规则与行为始终来自相应正式来源；吸收位置和实现结果按实际作用进入 evidence_refs。不得用单一 `archived` 状态混合“已经被吸收”和“不再是当前决定”两种含义。

## 7. 来源、证据与替代关系

`source_refs` 回指决策问题、关键输入和实际决定来源。`evidence_refs` 必须支持选择确已成立及其授权范围；Human 当前指令可以成为证据，但必须能够稳定定位，不能伪造对话 locator。事实来源、Human 确认、提交、测试和实现结果各自只证明实际覆盖范围，不能互相替代。

ADR 来自 Spark 或 WorkCase 时可以把源对象作为 source_ref；Spark 的 routed-to 已表达分流，ADR 不复制反向关系。实施决定的 WorkCase 可以把 ADR 作为 source_ref；ADR 不维护双写 related_workcases。规范、Code、commit、文档或外部页面不是事实对象，分别进入 source_refs 或 evidence_refs。

ADR `relation_key` 第一版只允许 `supersedes`：

| source condition | target condition | cardinality | reverse authority | missing and cycle boundary |
|---|---|---|---|---|
| 关系建立时新 ADR 必须为 active；关系与旧 ADR 状态转换在同一获准变更中成立，建立后可以随 source 后续进入终态而永久保留 | 目标是可恢复的 superseded ADR，且关系建立前为 active；只允许同一管辖项目的 `adr` | 每个旧 ADR 全生命周期最多一个直接 supersedes source，既有关系不因 source 状态变化而释放基数；一个新 ADR 只有在多个旧决定不可分割合并时才可指向多个不同目标 | `superseded-by` 只由 Code 派生，不写回；旧 ADR 不复制新对象引用 | 目标缺失、非 superseded、类型或项目不符、自指时无效；必须满足 `target.decided_at <= source.decided_at <= target.closed_at`；全部保留的 supersedes 边必须组成 DAG |

如果新决定只替代旧决定的一部分，不能把旧对象整体标为 superseded；应拆分新决定或让旧决定保持 active，并修正适用边界所需的正式来源。关系存在不单独证明替代成立，必须与两个对象、来源、证据、适用范围和同一变更一致。

### 主动召回与消费时机

在管辖项目和实际 Working Tree 成立后，新会话开始、会话恢复和上下文压缩后恢复都必须向 AI 提供该项目全部 `active` ADR 的 F1 决策卡。每张卡只直接投影 `object_id`、`title`、`decision_question`、`decision`、`applicability` 和 `updated_at`；不用 AI 临时摘要、索引标签或缓存改写权威字段。这一完整最小投影是 AI 判断当前行动可能受哪些长期决定制约的前置；不得先要求 AI 已知 applicability 命中，再决定是否让其看到该 ADR。

决策卡可以分页，但必须披露全部 `active` 数量、已读数量、未读范围、指纹和后续 cursor。coverage 未完整时，不得声称已恢复全部当前决策约束，也不得在可能受未读 ADR 影响的高影响行动前宣称 ADR 检查完成。AI 审阅全部决策卡后，对当前对象、环境或选择问题可能适用的 ADR 展开 F3；准备作出、重议或改变长期选择，以及影响架构边界、数据模型、稳定接口或运行约束前，必须重新完成这一筛选与全文核对。

`superseded` 与 `retired` ADR 不作为当前决定默认约束；只在精确引用、决定或授权追溯、检查替代链，或判断新选择是事实更正、整体替代还是独立决定时展开。AI 消费 `active` ADR 时必须同时核对 decision question、decision、applicability、rationale、consequences、来源与证据；召回 ADR 不代表它取代正式规范，也不授权当次实施或改变决定。

## 8. 变更、删除与类型退出

创建前必须召回相邻 ADR、适用规范、Spark、WorkCase 和稳定来源，先判断不对象化、更新事实更正、拆分或建立新身份。ADR 创建后，decision_question、decision、applicability、rationale、consequences 和 decided_at 六个专属字段除有来源的事实更正外均不得原地实质改变；任何语义变化都必须建立新 ADR，并在整体替代成立时走 supersedes。文字澄清只有不改变原决定语义且有来源时才作为事实更正。

active、superseded 和 retired 文件均默认保留在当前载体中供来源、理由和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失决定历史时才成立，不能用删除代替终态。

ADR 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用决定；全部 active 决定还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| ADR 类型定义 | 新建或实质修改本文时 | 唯一声明、绑定、状态、来源、证据与关系完整且无第二权威 | 05、统一登记与本文 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 `adr` 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| ADR 准入与查重 | 创建对象前 | 单一选择已实际成立、影响长期、边界与理由清楚、来源授权可回指且没有现有无损承载 | 当前输入、决定来源、授权依据、召回结果与 AI 语义比较 | AI 来源回读与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、Spark、WorkCase、Study 或已有来源 |
| ADR 召回与消费 | 会话开始/恢复/压缩恢复，或作出、重议、改变长期选择与高影响行动前 | 全部 `active` ADR 权威 F1 决策卡 coverage 完整；可能适用者已展开回读；终态只作追溯或替代链候选；卡片/全文未被冒充为规范权威或实施授权 | 管辖与 worktree 结果、全部 `active` 卡片、coverage/cursor、当前选择问题、已展开 ADR、来源、证据与替代关系 | 完整卡片分页回读、范围走查、完整对象回读与 AI applicability 核对 | 当次已读卡片范围、选择问题与已展开决定 | 不声称 ADR 基础上下文完整或将受影响 ADR 作为当次约束；继续分页、补读来源、缩小范围或交还冲突 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 ADR 消费；报告字段和未验证范围 |
| 决定与适用边界 | 创建或消费 active ADR 时 | 决定确已成立，授权、适用和排除范围有来源支持，未与当前规范或其它 active ADR 冲突 | source_refs、evidence_refs、当前规范、相邻 ADR 与 Human 决定 | AI 语义审核、来源与规范回读 | 当次决定及声明范围 | 不创建或暂停当前决定消费；缩小范围、补依据或进入 Human Gate |
| 替代或退出 | 准备 superseded 或 retired 时 | 新决定或退出依据成立，两个对象、关系、证据、适用边界和时间一致 | 新旧 ADR、来源、证据、当前规范与 Human 决定 | AI 语义审核、目标回读和结构校验 | 当次终态与替代声明 | 保持 active；修正替代范围、补证据或进入 Human Gate |
| 变更与回读 | 创建、更正、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核决定是否实际成立、是否值得对象化、对象粒度、来源授权、适用边界、理由、后果、与当前规范及 active ADR 的冲突、替代完整性和退出依据。当前字段定义只能在已实现范围内验证结构与语义边界，不能把缺少实际消费证据宣称为已验证的样本消费。

Code 的共同机械边界按 05 §§10–11 执行；对 ADR，只可额外检查本文明确给出的状态条件、跨对象时间顺序、全生命周期单一直接替代源和 supersedes DAG。决定是否值得记录、Human 决定权、理由、适用范围、后果及自然语言冲突仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：active、superseded、retired；每个状态缺少条件字段或带禁止字段；decided_at 的对象内与 `target.decided_at <= source.decided_at <= target.closed_at` 跨对象边界；决定来源与授权缺失；未决提案冒充决定；多个独立问题捆绑；ADR 与当前规范或 active ADR 冲突；supersedes 的建立时与持久 source/target 状态、项目、全生命周期单一直接替代源、自指、缺失目标和全部保留关系 DAG；patch/archived/deprecated/related_* 与空占位被拒绝；任何外部实例不得直接作为有效 fixture。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 决定本身属于产品方向、长期规则、重大架构、事实权威归属、Human Gate 变化或风险接受，且未由 Human 当前指令明确决定或授权 AI 在该范围自主选择；
2. 决定来源、授权主体或作用范围不清，AI 无法从当前来源无损确定；
3. 准备 supersede、retire、合并或拆分决定，实际取舍或剩余适用范围需要 Human 判断；
4. 修改 active ADR 的六个专属字段会实质改写原决定，而不是有来源的事实更正；
5. 删除或重组可能丢失决定身份、来源、证据、理由或替代历史。

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权作出或记录相应决定，且适用于该行动的全部来源规则许可条件已经成立时，记录 ADR 不因对象类型本身重复进入 Human Gate。Human 决定不能替代 Schema、来源回读、技术验证或正式规则写入；技术结果也不能替代保留给 Human 的取舍和风险接受。

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

暂停范围与允许继续的行动按 00 §11 执行；对 ADR，只有选择实际成立、来源授权可回指、冲突与对象粒度得到处置、Schema 和关系一致并完成写后回读后，才能恢复相应范围。
