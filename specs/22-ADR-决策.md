# ADR / 决策

```yaml
ldvh_spec:
  spec_key: "adr-fact-type"
  spec_id: "22"
  spec_kind: "spec"
  title: "ADR / 决策"
  status: "active"
  canonical_path: "specs/22-ADR-决策.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 ADR 事实类型的对象边界、Schema、生命周期、形成边界、取舍说明、替代关系与复用规则"
  scope: "管辖项目中已经实际作出、具有跨行动持续影响并需要稳定保存选择、适用边界、理由和后果的单一决定"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `adr` 事实类型的唯一定义来源；它不使 ADR 读取、创建、校验、Helper、Code、tests、行动模板或 Web 能力自动成立。字段与状态的必要性只由当前准入审计、本文和独立复核证明，不能以任何外部实例替代。

## 1. 价值判断

ADR 保存一个已经实际成立、会跨行动持续影响项目的决定，使后续 AI 能定位当时解决了什么选择问题、选择了什么、适用哪里、为何这样选择以及接受了哪些后果，而不必从聊天、提交或实现结果反向猜测决定。

新建 ADR 使用 `fact-object-controlled-creation`（31）；既有 ADR 的事实更正、内容更新、状态变化或承接处置使用 `fact-object-lifecycle-change`（32）。这只是行动入口，不替代本文的准入、决定成立或 Human Gate。

ADR 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 与行动模板承担；ADR 不承载实施计划、任务进度或执行授权。新增成本包括查重、持续维护、Schema、迁移和消费；通过只记录已成立决定、一个决定问题、两个状态、五个专属字段且不保存提案或过程历史，维护成本被限制在低于反复重建重要取舍、重复争论和错误泛化的范围。不能证明这种净收益的判断不准入 ADR。

当前版本从最小可解释决定记录开始，不按传统 ADR 模板或旧 Code 快照补齐未经证明的结构。

面向 Human，当已经成立的决定确需跨行动保留时，ADR 直接承接 HV3 的决定入档、当前 `active` 状态和 `retired` 处置节点，并直接承接 HV5 中关键决定、当前有效内容、形成理由、已接受影响和退出或替代历史的可循性。ADR 不承载仍待选择的选项、决策提请、实施进展或工作结果，不能单独满足 HV1，也不能单独串联完整项目演进。ADR 的存在、数量或被下位来源吸收，只提供 HV4 的积累内容输入；本文不记录实际使用或复用及可观察效用，不声明 HV4 成立。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、形成边界、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定管辖项目当前事实源、Working Tree、来源回指和稳定事实边界。

ADR 是决定事实，也是其声明适用范围内必须遵从的当前决策来源；它不是“决策补丁”，也不以字段或实现细节重复正式规范。`active` ADR 所决定的方向必须约束后续 AI 的理解、判断、写入与行动；具体 Specs、Code、Web 和行动模板负责将该决定落实为可操作、可校验的细节，不得与之相悖。ADR 不单独证明技术状态、实现完成或验证通过，也不绕开 Human 明确保留的高风险、不可逆或外部行动授权。

## 3. 职责边界

本文负责定义：

1. `adr` 的类型语义、对象粒度、准入和排除边界；
2. ADR 的唯一当前承载位置、完整 Schema、状态和终态处置；
3. 决策问题、已作决定、适用边界、理由和后果；
4. ADR 的形成边界、取舍说明、替代关系、变更、更正、删除和类型退出边界；
5. ADR 的验证要求、Human Gate、Stop Conditions 和最小失败范围。

本文不负责定义：

1. 正式规范、项目规则、字段契约、Human Gate 规则或其它可执行纪律；
2. 提案、选项收集、研究正文、实施计划、执行步骤、任务状态或技术完成情况；
3. WorkCase、Spark 或其它事实类型的语义与生命周期；
4. Helper API、CLI、Web 表单、Git Hook 或迁移兼容或文件分配算法；
5. 仅因 ADR 存在而产生的执行、写入、提交、发布或风险接受授权。

AI 负责判断决定是否已实际成立、是否值得对象化、是否重复、Human 授权与适用边界是否准确、理由与后果是否据实；Code 只可按当前来源检查固定结构、值闭集、引用和状态条件。

## 4. 适用范围

一个判断只有同时满足以下条件，才可以形成 ADR：

1. 决策问题清楚，并且一个方向已经实际被选择；仍在比较选项的内容不准入；
2. 选择存在真实、可说明的长期取舍，跨行动影响架构、接口、事实归属、兼容性、风险或协作边界；
3. 适用对象、条件、范围、明确排除项、理由和预期后果能够稳定表达；
4. 作出决定的 Human 授权范围能够由对象自有字段据实说明；ADR 必须在决定实际形成时创建，`created_at` 即该决定记录的成立时间，不能事后补造“当时已决定”；
5. 已召回当前 ADR、适用规范、Spark、WorkCase 和相邻稳定来源，没有可无损更新或已经自然承载的现有位置；
6. 该决定有独立替代与追溯价值，对象化减少的理解与重复争论负担高于维护成本。

一个 ADR 只回答一个可以独立替代或退出的决策问题。多项选择只有在必须整体成立、整体替代且不能独立变化时才可合并；否则拆分。

以下内容不得形成 ADR：尚未选择的方案或开放问题；明确执行目标与实现任务；正式规则、Human Gate、操作纪律或字段契约；当前行动内可逆且低影响的技术选择；偏好、会议纪要、聊天摘要、执行日志、测试结果或研究正文；已经被当前规范无损表达且没有独立决策生命周期的理由；无法如实说明实际选择、授权范围或适用边界的事后合理化。

未决问题保持 Spark；实施或吸收决定使用 WorkCase。ADR 回答“决定什么、为何、适用哪里”，WorkCase 回答“完成什么、如何验收、当前是否阻塞或关闭”。具体 Specs 负责可操作规则与字段合同，`active` ADR 负责其适用范围内的方向约束；二者冲突时必须暂停受影响范围并完成对齐，不得自行以任一方静默覆盖另一方。

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
| `object-uid` | conditional | `adr-fact-type::5. ADR 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `adr-fact-type::5. ADR 类型定义` |
| `created-at` | required | `adr-fact-type::8. 变更、删除与类型退出` |
| `updated-at` | required | `adr-fact-type::8. 变更、删除与类型退出` |
| `change-log` | conditional | `adr-fact-type::8. 变更、删除与类型退出` |
| `status` | required | `adr-fact-type::6. 对象语义与生命周期` |
| `urls` | conditional | `adr-fact-type::7. 形成边界、取舍说明与替代关系` |
| `relations` | conditional | `adr-fact-type::7. 形成边界、取舍说明与替代关系` |
| `disposition-summary` | conditional | `adr-fact-type::6. 对象语义与生命周期` |
| `adr-decision-question` | required | `inherit` |
| `adr-decision` | required | `inherit` |
| `adr-applicability` | required | `adr-fact-type::7. 形成边界、取舍说明与替代关系` |
| `adr-rationale` | required | `inherit` |
| `adr-consequences` | required | `inherit` |
| `adr-trigger-signal` | required | `inherit` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `adr-decision-question` | `decision_question` | string | 这个 ADR 已经回答的单一长期选择问题，即“当时需要在什么方向之间作出取舍” | 不表示故障现象、当前工作目标、研究问题列表或标题 | 必填非空；必须能独立替代或退出；多个独立问题必须拆分 |
| `adr-decision` | `decision` | string | 在已说明的 Human 授权范围内已经实际选择的方向 | 不表示提案、规则正文、实施计划、完成状态或对未来行为的自行授权 | 必填非空；实质改变时建立新 ADR，原记录只做事实更正；必须区分已作选择与尚未实施的效果 |
| `adr-rationale` | `rationale` | string | 作出选择时的理由、关键取舍以及未选择主要方向的原因 | 不表示来源全文、证据列表、传统 alternatives 结构、实施结果或事后合理化 | 必填非空；只保留理解决定所需取舍；未能确认的事实前提或效果必须如实保留为未知 |
| `adr-consequences` | `consequences` | string | 作出决定时接受的正负后果、限制、风险和后续义务 | 不表示规范条款、实施 todo、验证结果、完成声明或终态处置 | 必填非空；未知后果必须如实标明，不为满足模板补造固定段落 |
| `adr-trigger-signal` | `trigger_signal` | string | 当 AI 正在执行以下类型的动作时，该决策可能已被触达；即哪些动作会触达这个决策边界 | 不表示该决策的适用范围（那是 applicability）、该决策的内容（那是 decision） | 必填非空；必须是动作/行为描述而非范围描述；一个 ADR 可以有多个 trigger_signal，用换行或分隔符表达 |

### Schema 与对象载体

ADR 对象使用 UTF-8 YAML，一文件一对象；新 UID-native 对象使用 `ldvh-base/adrs/adr-<uid26>.yaml`，legacy 对象继续从 `ldvh-base/adrs/<object_id>.yaml` 双读。legacy `object_id` 必须匹配 `adr-[0-9]{4,}`且与旧文件名一致；新建只写 UID 路径，不要求 candidate_object_id 或 counter。具有 `object_uid` 时其权威身份、legacy 缺失兼容和不可变边界统一按 05 §7.3–§7.4，新建 ADR 必须由 Code 生成 UID。

`title` 是对已作决策的简短名称，必须直接表达 `decision` 所确定的方向，使只读标题的人能区分“决定了什么”与“在讨论什么”。它不复制完整 `decision_question` 或 `decision`，也不写成正式规则条文或实现步骤。不得只写领域名、对象名、问题名、章节名、文档标题或“讨论/说明/解释”等未表达决定的名词短语；例如可写“规则缺口时先修规则源”“交付中解释关键术语与代码标识”，不可只写“规则缺口来源先行”“技术术语与代码标识解释”。标题与 `decision` 不一致、无法单独识别决定方向或把决定伪装成字段合同、实现完成时，不得创建或消费该 ADR。

未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义和类型专属字段定义组合。ADR 不得出现 current summary、priority、evolution、WorkCase 字段、`alternatives` 结构、`affects`、`archive_reason`、`deprecated_reason`、implementation/absorption status、revision history、按目标类型拆分的关系或其它未登记内容。

### 面向 Human 的详情阅读投影

当 Web 或其它 Human 阅读面按 08 §5.3 呈现 ADR 详情时，必须按对象实际存在字段依次使用下列中文区段标题：`问题`（`decision_question`）、`决策`（`decision`）、`范围`（`applicability`）、`理由`（`rationale`）、`影响`（`consequences`）；`retired` 对象的 `disposition_summary` 另以 `处置` 呈现。六个标题均为两个汉字。条件或可选字段不存在时如实省略对应区段，不生成空态、默认结论或替代内容；类型来源定义为必填的字段缺失或类型不符时，按 08 §5.3 如实显示空态与字段问题。

这里的“问题”仅指这个 ADR 已经回答的选择问题，不表示缺陷、故障或待办；“决策”只陈述已经作出的决定，不表示规范、行动授权或实现完成；“范围”说明该决定何时适用或排除；“理由”和“影响”分别保留作出决定时的取舍与当时接受的后果，不将后来的技术结果倒灌其中；“处置”只说明终态如何退出当前决定。标题是面向阅读的固定词，不新增字段、不改写 YAML 字段名，也不允许 Web 用“决策问题”“适用范围”“处置说明”等通用或旧词替代，或把多个字段合并为一段。

## 6. 对象语义与生命周期

ADR 只记录已经成立的决定。选项仍在收集、方向仍在比较或授权尚未成立时不得创建 proposed ADR；保留在 Spark、Study、WorkCase 或当前行动中。一个决定写入 `active` ADR 后，必须在 applicability 内被遵从；这不表示实现已经完成、技术结果已经验证，或 Human 保留的高风险、不可逆或外部行动授权已经自动取得。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 决定在其声明适用范围内仍是当前、必须遵从的方向 | 只能作为新建初态；终态字段禁止；实际决定、授权范围、以 `created_at` 如实记录的成立时间、适用边界与取舍说明成立；约束后续理解、判断、写入与行动，但不单独证明实现状态或技术结果 |
| `retired` | 原决定因适用条件消失、方向撤回、不再需要或已被新 ADR 的决定范围覆盖而退出当前选择 | disposition_summary 必填；必须有具体退出依据；终态更新以 `updated_at` 记录；disposition_summary 直接写处置结论，不重复 `retired` 状态或添加“退出理由：”等字段标签；被新 ADR 覆盖时在其中说明替代关系，不建立独立关系边 |

初始状态只能是 `active`。正常转换只有 `active → retired`；终态不直接重开。任何 ADR 转为 `retired` 都必须在写入前取得 Human 对该对象退出的明确授权；仅授权创建、普通更新、事实更正、阅读、验证或记录决定，不覆盖退出。五个 ADR 专属字段发生实质改变时建立新 ADR；`title` 只能在不改变原选择的前提下更正为准确的选择名称，不能借标题修正改写决定。只有依据充分且不改变原决定语义的事实更正可以原地修正，不把语义改写伪装成生命周期变化。

规范、Code 或其它正式来源吸收决定不会使 ADR 自动终态。ADR 即使已被下位来源具体落实，仍在其 applicability 内约束后续判断，直至获得获准的退出；下位来源不得借实现方便改写或规避当前决定。吸收位置和实现结果不是 ADR 的必填结构，也不能据此自动改变状态。不得用单一 `archived` 状态混合“已经被吸收”和“不再是当前决定”两种含义。

## 7. 形成边界、取舍说明与替代关系

ADR 通过对象自有语义字段据实说明实际选择、Human 授权范围、适用范围、作出选择时的理由、已接受后果和仍未知的效果。`created_at` 是该决定记录的成立时间；`decision` 记录已经作出的选择；`rationale` 记录作出该选择时采用的取舍；`consequences` 记录当时接受的限制、风险和后续义务。它们不要求附带证据引用、聊天 locator、命令、日志、commit 或来源对象；Human 当前指令、Spark、WorkCase、规范、Code、测试或外部材料可以作为形成决定时的当次输入，但不因此成为 ADR 的字段、关系或证明材料。无法稳定定位的对话不得被伪造为 locator。

决定已经成立即在其 applicability 内形成必须遵从的方向，但不表示理由中的所有事实前提已经永久正确，也不表示后果已经发生、实现已经完成、规范已经生效或 Human 保留的行动授权已经取得。对象必须在相关字段中区分已作决定、作出决定时的判断和仍未知或未验证的效果；不得以提交、测试成功、实现存在或后来结果倒推当时决定或扩大其适用范围。外部资料确有长期消费价值时才可按 05 使用 `urls`，其 `summary` 说明支持范围、限制以及必要的版本或观察时点。

ADR 不建立 `source_ref`、`evidence_ref` 或来源关系。ADR 不定义 relation_key。新旧 ADR 之间的替代或覆盖关系通过 `disposition_summary` 表达，不建立独立关系边。如果新决定只替代旧决定的一部分，应拆分新决定或让旧决定保持 active，并修正适用边界所需的正式来源。

### 主动召回与消费时机

当 Human 目标已经明确需要项目事实，且当前工作可能受长期选择、架构边界、数据模型、稳定接口或运行约束影响时，AI 才取得该项目全部 `active` ADR 的 F1 决策卡。新会话开始、会话恢复或上下文压缩本身不构成恢复 ADR 事实的理由；它们只取得 00 §8.1 定义的规则引导。每张卡只直接投影条件出现的 `object_uid`、以及 `object_id`、`title`、`decision_question`、`decision`、`applicability`、`trigger_signal` 和 `updated_at`；不用 AI 临时摘要、索引标签或缓存改写权威字段。这一完整最小投影帮助 AI 判断当前行动可能受哪些长期决定制约；不得先要求 AI 已知 applicability 命中，再决定是否让其看到该 ADR。

决策卡可以分页，但必须披露全部 `active` 数量、已读数量、未读范围、指纹和后续 cursor。coverage 未完整时，不得声称已恢复全部当前决策约束，也不得在可能受未读 ADR 影响的高影响行动前宣称 ADR 检查完成。AI 审阅全部决策卡后，对当前对象、环境或选择问题可能适用的 ADR 展开 F3；准备作出、重议或改变长期选择，以及影响架构边界、数据模型、稳定接口或运行约束前，必须重新完成这一筛选与全文核对。

`retired` ADR 不作为当前决定默认约束；只在精确引用、决定或授权追溯、检查替代链，或判断新选择是事实更正、整体替代还是独立决定时展开。AI 消费 `active` ADR 时必须同时核对 decision question、decision、applicability、rationale、consequences、created_at 与当前环境，并在适用范围内遵从该决定；ADR 不替代正式规范的具体字段和实现合同，也不授权超出当前 Human 授权范围的行动或改变决定本身。

## 8. 变更、删除与类型退出

创建前必须召回相邻 ADR、适用规范、Spark 和 WorkCase，先判断不对象化、更新事实更正、拆分或建立新身份。ADR 创建后，decision_question、decision、applicability、rationale 和 consequences 五个专属字段除不改变原决定语义的事实更正外均不得原地实质改变；任何语义变化都必须建立新 ADR。`title` 可以原地更正，但更正后仍必须与未改变的 `decision` 表达同一选择。文字澄清只有不改变原决定语义、没有把后来的结果倒灌为当时理由时才作为事实更正。

active 和 retired 文件均默认保留在当前载体中供来源、理由和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失决定历史时才成立，不能用删除代替终态。

ADR 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用决定；全部 active 决定还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| ADR 类型定义 | 新建或实质修改本文时 | 唯一声明、绑定、状态、形成边界、取舍说明与关系边界完整且无第二权威 | 05、统一登记与本文 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 `adr` 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| ADR 准入与查重 | 创建对象前 | 单一选择已实际成立、影响长期、Human 授权范围、边界与取舍清楚，title 直接表达该选择而非话题，且没有现有无损承载 | 当前输入、对象自有语义字段、召回结果与 AI 语义比较 | AI 对 title、decision_question、decision 和当前环境的据实核对与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、Spark、WorkCase、Study 或已有来源 |
| ADR 召回与消费 | Human 目标明确需要项目事实且当前工作可能受长期决定约束，或作出、重议、改变长期决定与高影响行动前 | 全部 `active` ADR 权威 F1 决策卡 coverage 完整；可能适用者已展开回读并在 applicability 内作为当前约束遵从；终态只作追溯或替代链候选；不把 ADR 冒充为技术完成、具体字段合同或超出 Human 授权的行动许可 | 管辖与 worktree 结果、全部 `active` 卡片、coverage/cursor、当前问题与已展开 ADR | 完整卡片分页回读、范围走查、完整对象回读与 AI applicability 核对 | 当次已读卡片范围、当前问题与已展开决定 | 不声称 ADR 基础上下文完整或自行偏离受影响 ADR；继续分页、缩小范围或交还冲突 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 ADR 消费；报告字段和未验证范围 |
| 决定与适用边界 | 创建或消费 active ADR 时 | 决定确已成立；title 与 decision 表达同一选择而非话题；已作选择、作出选择时的判断、未知或未验证效果没有混写；授权、适用和排除范围与当前规范和其它 active ADR 不冲突 |对象自有语义字段、当前规范、相邻 ADR、Human 决定与当前环境 | AI 语义审核与当前环境回读 | 当次决定及声明范围 | 不创建或暂停当前决定消费；缩小范围、继续调查或进入 Human Gate |
| 退出 | 准备 retired 时 | 已取得针对该 ADR 退出的明确 Human 授权，且退出依据、适用边界和时间一致 | 当前 ADR 与 Human 明确授权 | AI 语义审核和结构校验 | 当次终态声明 | 保持 active；补充处置说明并取得 Human 授权 |
| 变更与回读 | 创建、更正、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核决定是否实际成立、是否值得对象化、对象粒度、title 是否准确表达选择、Human 授权范围、适用边界、理由、后果、与当前规范及 active ADR 的冲突、替代完整性和退出依据。当前字段定义只能在已实现范围内验证结构与语义边界，不能把读取、来源存在、技术结果或后续消费冒充为决定正确、规则生效或实现完成。

Code 的共同机械边界按 05 §§10–11 执行；对 ADR，只可额外检查本文明确给出的状态条件。决定是否值得记录、Human 决定权、理由、适用范围、后果及自然语言冲突仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：active、retired；每个状态缺少条件字段或带禁止字段；不带 `urls`、`relations`、`source_ref` 或 `evidence_ref` 的完整 ADR；`source_ref`、`evidence_ref` 与其它未登记字段被拒绝；title 只写话题、问题或章节名，title 与 decision 不一致，及 title 把选择写成规则；未决提案冒充决定；已作选择、理由或未验证效果混写；多个独立问题捆绑；ADR 与当前规范或 active ADR 冲突；与 retired 终态条件；patch/archived/deprecated/related_* 与空占位被拒绝。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 决定本身属于产品方向、长期规则、重大架构、事实权威归属、Human Gate 变化或风险接受，且未由 Human 当前指令明确决定或授权 AI 在该范围自主选择；
2. Human 授权主体或作用范围不清，AI 无法从当前输入和对象自有字段无损确定；
3. 准备将任何 ADR 转为 `retired`；此项始终需要 Human 对目标 ADR 及退出动作的明确授权，不因 AI 已判断退出依据充分而豁免。准备合并或拆分决定且实际取舍或剩余适用范围需要 Human 判断时，也进入 Human Gate；
4. 修改 active ADR 的五个专属字段会实质改写原决定，而不是不改变原决定语义的事实更正；
5. 删除或重组可能丢失决定身份、取舍说明或替代历史。

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权作出或记录相应决定，且适用于该行动的全部来源规则许可条件已经成立时，记录 ADR 不因对象类型本身重复进入 Human Gate。Human 决定不能替代 Schema、当前对象回读、技术验证或正式规则写入；技术结果也不能替代保留给 Human 的取舍和风险接受。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入或宣称 ADR 成立：

1. 仍在比较选项、收集资料或等待决定，却准备创建 ADR；
2. 无法如实说明实际选择、Human 授权范围、适用边界、取舍或未知效果，或准备在决定实际形成之后事后补建 ADR；
3. 正在把 ADR 写成字段合同、实现步骤、技术完成声明，或用它绕开 Human 明确保留的行动授权；
4. 与当前规范或 active ADR 冲突，但没有完成获准的冲突处置；
5. 多个可以独立替代或退出的决定被捆绑；
6. title 只写话题、问题、章节名或未表达选择的名词短语，title 与 decision 不一致，或 title、decision、applicability、rationale 或 consequences 为空、过度泛化、把选择写成规则，或将后来的结果事后倒灌为当时理由；
7. 用关系、commit、测试成功或实现存在冒充决定已实施、规则已生效或行动已授权；
8. 准备转为 retired 却没有针对目标 ADR 退出的明确 Human 授权，或 retired 没有具体退出依据；
9. 准备写入 proposed、archived、deprecated、alternatives、affects、related_*、空占位或其它未登记内容；
10. 高影响决定没有实际授权，或获准写入后没有回读与范围匹配验证。

暂停范围与允许继续的行动按 00 §11 执行；对 ADR，只有选择实际成立、Human 授权范围与取舍说明清楚、冲突与对象粒度得到处置、Schema 和关系一致并完成写后回读后，才能恢复相应范围。
