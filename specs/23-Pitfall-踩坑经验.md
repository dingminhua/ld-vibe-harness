# Pitfall / 踩坑经验

```yaml
ldvh_spec:
  spec_key: "pitfall-fact-type"
  spec_id: "23"
  spec_kind: "spec"
  title: "Pitfall / 踩坑经验"
  status: "active"
  canonical_path: "specs/23-Pitfall-踩坑经验.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 Pitfall 事实类型的对象边界、Schema、生命周期、来源、关系、验证与复用规则"
  scope: "管辖项目中已经发生、查明、解决、验证且仍有迁移复用价值的单一失败机制与规避经验"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `pitfall` 事实类型的唯一定义来源；它不使 Pitfall 读取、创建、校验、迁移、Helper、Code、tests、行动模板或 Web 能力自动成立。V3 规范、Code 和两个实例只作为需求与反例输入；两个实例都依赖 V3 字段或可变化的外部协议，不能直接作为 V4 active 对象。

## 1. 价值判断

Pitfall 保存一个已经实际发生、查明、解决、验证且仍能迁移复用的失败机制，使后续 AI 能识别相似症状与触发条件，理解有证据的根因，在适用边界内复用实际解决与规避经验，避免重复误判和调试。

Pitfall 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 和行动模板承担；Pitfall 不承载 bug backlog、实施计划或行动授权。新增成本包括发现、查重、维护、Schema、迁移、时效复核和消费；通过只准入已发生且验证的单一失败机制、三状态、五个专属字段、两个共享语义字段并排除日志与自由标签，维护成本低于重复犯错和错误复用的损耗。普通文档、测试、代码说明或当前规则能够无损承载且不需要独立身份、状态、证据和替代历史时，不创建 Pitfall。

V3 两个实例都实际表达 symptoms、trigger conditions、root cause、resolution、verification、avoidance 和 applicability，能够证明这些信息问题有表达需求；它们不能证明 tags、archived 或旧引用数组有稳定消费价值，也不能证明旧经验在 V4 或当前外部环境仍有效。V4 只吸收经重新查重的语义字段，不继承实例当前性。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定 Git 可追踪事实源、当前 Working Tree、来源回指和稳定事实边界。

Pitfall 是经验事实，不是规则来源。`avoidance` 说明在适用边界内如何识别、预防或安全复用经验，不取得 MUST 级规则权威。需要形成强制规则、Code 行为或行动结构时，必须由相应正式来源另行定义、授权和验证；吸收不会自动使 Pitfall 终态。

## 3. 职责边界

本文负责定义：

1. `pitfall` 的类型语义、对象粒度、准入和排除边界；
2. Pitfall 的唯一当前承载位置、完整 Schema、状态和终态处置；
3. 症状、触发条件、根因、已验证解决方式、规避方法、适用边界和验证摘要；
4. Pitfall 来源、证据、替代关系、变更、更正、删除和类型退出边界；
5. Pitfall 的验证要求、Human Gate、Stop Conditions 和最小失败范围。

本文不负责定义：

1. 正式规范、项目规则、强制纪律、Code 行为或行动模板步骤；
2. 未解决故障、开放问题、任务进度、实施计划、调试日志、研究正文或长期决定；
3. 其它事实类型的语义、状态和 Schema；
4. 标签词表、搜索算法、Helper API、CLI、Web 表单、Hook 或迁移兼容；
5. 仅因经验存在而产生的行动、风险接受或技术正确性授权。

AI 负责判断失败是否实际发生、根因和解决是否有证据、经验是否值得对象化、适用边界是否仍当前、是否重复以及复用是否安全；Code 只可按当前来源检查固定结构、值闭集、引用和状态条件。

## 4. 适用范围

一个经验只有同时满足以下条件，才可以形成 Pitfall：

1. 存在实际发生的失败或误判，不是设想、提醒或一般风险；
2. 问题已经实际解决，根因有来源支持，没有把相关性冒充因果；
3. 解决方式已经实际验证，验证覆盖、结果、失败与未验证范围能够说明且有稳定证据；
4. 后续存在现实复发概率或跨行动迁移价值；
5. 症状、触发条件、适用对象、环境、条件、范围和排除项清楚；
6. 存在可复用的解决与规避经验，但没有把经验写成规则或行动授权；
7. 已召回相邻 Pitfall、当前规则、ADR、WorkCase、Spark 和稳定来源，没有可无损更新或重复对象；
8. 对象化减少的重复误判与调试负担高于发现、维护、复核和消费成本。

一个 Pitfall 只承载一个可独立识别、验证、替代或退出的失败机制，其身份由核心根因和相容的规避方式共同限定。增加同一机制的症状、触发样例或更强证据可以更新原对象；出现不同根因、互不相容处置，或新经验使旧经验不安全时必须拆分或新建并替代。

以下内容不得形成 Pitfall：未解决、未验证或根因未知的故障；一次性日志、当前测试失败、调试记录、bug backlog、todo 或实施责任；开放问题；长期决定；规范条款、强制纪律或纯 how-to；情绪复盘；没有适用与排除边界的“最佳实践”；已有 Pitfall 能无损承载的同义经验。

未解决但目标明确的修复进入 WorkCase；承接位置或验收边界仍模糊的观察保持 Spark；长期选择进入 ADR。Pitfall 回答“曾怎样失败、为何、什么修复被怎样验证、何时可复用”，规则回答“当前必须遵守什么”。

## 5. Pitfall 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `pitfall` | 已经发生、查明、解决、验证且仍有迁移复用价值的单一失败机制与规避经验 | `pitfall-fact-type::5. Pitfall 类型定义` |

### 结构准入记录

本类型没有结构准入事项

### 类型专属结构定义

本类型没有类型专属结构

### 字段准入记录

| information_need | compared_field_keys | decision | resulting_field_key | rationale | review_ref |
|---|---|---|---|---|---|
| 稳定识别同一 Pitfall | `object-id` | reuse | `object-id` | 公共对象身份无损适用，只收紧 Pitfall 格式 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 声明对象属于 Pitfall 类型 | `fact-type-key` | reuse | `fact-type-key` | 公共类型身份无损适用，固定为 `pitfall` | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 提供 Human 与 AI 可读短标签 | `title` | reuse | `title` | 公共标题只用于识别，不承担失败机制正文 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 记录对象首次形成时间 | `created-at` | reuse | `created-at` | 公共形成时间无损适用，不冒充事故发生或验证时间 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 记录当前经验内容最近实质变化时间 | `updated-at` | reuse | `updated-at` | 公共更新时间无损适用，不建立经验演变日志 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 表达经验是否仍可参考、已被整体替代或无替代退出 | `status` | reuse | `status` | 公共条件状态入口适用，由本文定义 Pitfall 三状态闭集 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 回指原始事故、问题调查和经验形成输入 | `source-refs` | reuse | `source-refs` | 公共来源统一替代 source_objects、source_sparks 和拆分来源字段 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 支持根因、解决、验证、适用和终态判断 | `evidence-refs` | reuse | `evidence-refs` | 公共证据引用定位依据，不由验证摘要或命令文本自证 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 表达一个 Pitfall 对旧 Pitfall 的单向整体替代 | `relations` | reuse | `relations` | 公共关系统一承载 supersedes，不恢复 related_* 或 superseded_by | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 说明 superseded 或 retired 为什么成立以及剩余适用边界 | `disposition-summary,status` | reuse | `disposition-summary` | 共享终态处置无损承接经验整体替代或退出边界 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 记录 Pitfall 首次有效进入终态的时间 | `closed-at,updated-at` | reuse | `closed-at` | 与其它类型的终态首次成立时间完全同义 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 表达经验成立与适用的对象、环境、条件、范围和排除项 | `adr-applicability,workcase-scope` | promote | `adr-applicability` | 与 ADR applicability 具有相同共同基线，均限定对象核心内容的适用边界；WorkCase scope 仍是执行责任承诺 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 说明实际验证覆盖、结果、失败与未验证范围 | `evidence-refs,workcase-validation-summary` | promote | `workcase-validation-summary` | 与 WorkCase validation summary 共同回答实际验证覆盖与边界；Pitfall 收紧为根因、解决和安全复用验证 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 表达失败发生后的可观察表现与识别信号 | `current-summary,title` | differentiate | `pitfall-symptoms` | 标题只识别对象，当前摘要是进展快照；症状是失败发生后的稳定可观察表现 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 表达会触发失败的前置条件或组合 | `adr-applicability,pitfall-symptoms` | differentiate | `pitfall-trigger-conditions` | applicability 限定经验可复用范围，symptoms 是触发后的表现；均不能替代触发前置条件 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 表达经证据支持的失败因果机制 | `adr-rationale,evidence-refs,source-refs` | differentiate | `pitfall-root-cause` | ADR rationale 解释选择，引用只定位依据；都不表示失败因果机制 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0001` |
| 表达已经实际解决该问题的修复方式 | `adr-decision,disposition-summary,workcase-goal` | differentiate | `pitfall-resolution` | 决定、终态处置和工作目标都不表示已发生问题的实际修复方式 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |
| 表达后续识别、预防或安全复用方式 | `adr-consequences,pitfall-resolution` | differentiate | `pitfall-avoidance` | resolution 回答已发生问题如何修复，consequences 回答决定后果；均不能替代未来规避经验 | `pitfall-fact-type::5. Pitfall 类型定义::field-review-0002` |

### 字段独立复核

| review_key | reviewer | reviewed_scope | findings | disposition |
|---|---|---|---|---|
| `field-review-0001` | independent-pitfall-spec-review-agent | Pitfall 对象价值、准入、规则/ADR/WorkCase/Spark 边界、状态、关系及全部字段提案 | 两个 V3 实例证明核心信息需求但不能直接迁移；经验不能成为规则，外部协议经验必须受版本与观察时点限制；archived 混淆吸收与有效性 | 使用 active/superseded/retired；第一版只保留 supersedes；淘汰 tags、archived、拆分引用与空占位 |
| `field-review-0002` | independent-pitfall-field-audit-agent | V3 23、历史 Code、两个真实实例、当前 39 字段及全部字段准入提案 | 七类核心经验信息在 2/2 样本出现；applicability 与 validation summary 可提升共享；长验证日志、tags 和 related_* 没有稳定消费证明 | 提升两个既有字段；新增五个 type 字段；复用公共及终态入口；旧实例仅作迁移与反例输入 |

### 类型字段使用绑定

| field_key | field_path | presence | type_constraints |
|---|---|---|---|
| `object-id` | `object_id` | required | 必须匹配 `pitfall-[0-9]{4,}`；分配后不得因标题、状态或内容改变而变化 |
| `fact-type-key` | `fact_type_key` | required | 唯一允许值为 `pitfall` |
| `title` | `title` | required | 简短识别失败机制，不复制 symptoms 或 root_cause |
| `created-at` | `created_at` | required | 只使用对象首次按 Pitfall 形成的有依据时间 |
| `updated-at` | `updated_at` | required | 同一机制的症状、触发、证据、验证、来源、状态、关系或终态事实实质变化并回读后更新 |
| `status` | `status` | required | 只使用 `active`、`superseded`、`retired` |
| `source-refs` | `source_refs` | required | 至少一项；必须能重新定位原始事故或误判、调查输入和经验形成来源 |
| `evidence-refs` | `evidence_refs` | required | 至少一项；必须支持根因、解决、验证覆盖和 applicability；终态时还要支持替代或退出 |
| `relations` | `relations` | conditional | 只有 supersedes 关系存在时出现；无关系时省略 |
| `disposition-summary` | `disposition_summary` | conditional | superseded 或 retired 时必填，active 时禁止；说明替代或退出依据、仍有效边界和承接结论 |
| `closed-at` | `closed_at` | conditional | superseded 或 retired 时必填，active 时禁止；继承 `created_at <= closed_at <= updated_at` |
| `adr-applicability` | `applicability` | required | 明确经验可安全复用的对象、环境、条件、范围和排除项；外部事实变化时必须重新验证 |
| `workcase-validation-summary` | `validation_summary` | required | 说明 root cause、resolution 与安全复用的实际验证覆盖、结果、失败和未验证范围；不复制命令日志 |
| `pitfall-symptoms` | `symptoms` | required | none |
| `pitfall-trigger-conditions` | `trigger_conditions` | required | none |
| `pitfall-root-cause` | `root_cause` | required | none |
| `pitfall-resolution` | `resolution` | required | none |
| `pitfall-avoidance` | `avoidance` | required | none |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `pitfall-symptoms` | `symptoms` | string | 失败或误判实际发生后的可观察表现与识别信号 | 不表示标题、根因、触发前置条件、当前任务进展或日志全文 | 必填非空；只描述可观察表现；同一机制的新表现可以据证补充 |
| `pitfall-trigger-conditions` | `trigger_conditions` | string | 会触发该失败机制的前置条件、组合与必要上下文 | 不表示失败后的症状、经验适用范围、根因或一般风险 | 必填非空；区分已证条件与未知条件；同一机制的新触发样例可以据证补充 |
| `pitfall-root-cause` | `root_cause` | string | 经稳定证据支持、能够解释症状与触发的失败因果机制 | 不表示相关现象、推测、ADR 选择理由、来源或验证摘要 | 必填非空；不能只凭单次相关性成立；根因实质变化通常形成新 Pitfall |
| `pitfall-resolution` | `resolution` | string | 已经实际解决该失败机制的修复方式及其必要边界 | 不表示提案、WorkCase 目标、实施 todo、规避建议或规则正文 | 必填非空；必须已执行并由 validation summary 与 evidence refs 支持；不相容修复形成新对象 |
| `pitfall-avoidance` | `avoidance` | string | 后续识别、预防或安全复用该经验的方式 | 不表示强制规则、行动授权、已执行修复或通用最佳实践 | 必填非空；只在 applicability 内成立；需要强制时转正确规则来源，不在本字段使用 MUST 冒充权威 |

### Schema 与对象载体

Pitfall 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `facts/pitfalls/<object_id>.yaml`。文件名必须与 `object_id` 完全一致；标题、状态和目录移动不得参与身份计算。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义和类型专属字段定义组合。Pitfall 不得出现 current summary、priority、evolution、tags、`archive_reason`、repeatability、severity、superseded_by、source_objects/source_sparks、related_*、长命令日志字段、实现状态、revision history 或其它未登记内容。

## 6. 对象语义与生命周期

Pitfall 只记录已解决、已验证且可复用的失败机制。问题尚未解决、根因仍是推测、验证不足或适用边界不清时不得创建 active Pitfall。经验的存在不证明外部环境、协议或实现仍与验证时相同；消费前必须按 applicability、source_refs 的版本与 observed_at 重新判断现时适用性。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 根因、解决和验证仍可信，经验在 applicability 内仍可安全参考 | 只能作为新建初态；终态字段禁止；全部核心字段与证据成立；不表示规则权威 |
| `superseded` | 原经验已被一个后来成立的新 Pitfall 整体替代 | disposition_summary、closed_at、evidence_refs 必填；旧对象必须成为一个在建边时为 active 的新 Pitfall 的有效 supersedes 目标 |
| `retired` | 适用条件消失、关键证据被推翻或经验不再安全复用，且没有被新 Pitfall 整体替代 | disposition_summary、closed_at、evidence_refs 必填；必须有具体退出依据，不得用已被规则吸收冒充退出 |

初始状态只能是 active。正常转换只有 `active → superseded` 和 `active → retired`；终态不直接重开。根因、解决方式、规避方式或 applicability 的实质改变通常建立新 Pitfall；只有来源充分且仍是同一失败机制的事实更正、症状与触发补强、验证更新可以原地修正。

规范、Code 或行动模板吸收经验不会自动使 Pitfall 终态。Pitfall 即使 active 也只是经验参考，实际规则和行为来自相应正式来源。V3 archived 混合存储、吸收和不再有效，V4 不恢复。

## 7. 来源、证据与替代关系

source_refs 至少回指原始事故或误判、调查输入和经验形成来源。evidence_refs 必须实际支持根因、解决已经生效、验证覆盖及 applicability；命令文本、“测试通过”叙述、文件存在或一次成功不能自证超出其覆盖的结论。外部来源会变化时必须记录 version 和 observed_at。

Pitfall 来自 Spark、WorkCase 或 ADR 时可以把源对象作为 source_ref；源对象已有分流关系时不复制反向关系。落实规避措施的 WorkCase 可以把 Pitfall 作为 source_ref；Pitfall 不维护双写 related_workcases。规范、Code、commit、文档、日志或外部页面不是事实对象，分别进入 source_refs 或 evidence_refs。

Pitfall relation_key 第一版只允许 supersedes：

| source condition | target condition | cardinality | reverse authority | missing, time and cycle boundary |
|---|---|---|---|---|
| 关系建立时新 Pitfall 必须为 active；关系与旧对象状态转换在同一获准变更中成立，建立后随 source 后续终态永久保留 | 目标是可恢复的 superseded Pitfall，且关系建立前为 active；只允许同一管辖项目的 pitfall | 每个旧 Pitfall 全生命周期最多一个直接 supersedes source，既有关系不因 source 状态变化释放基数；多个旧机制只有在不可分割合并时才允许同一 source 指向 | superseded-by 只由 Code 派生，不写回；旧对象不复制新对象引用 | 目标缺失、非 superseded、类型或项目不符、自指时无效；`target.created_at <= source.created_at <= target.closed_at`；全部保留边必须组成 DAG |

新经验只替代旧经验的一部分时，不能把旧对象整体标为 superseded；应拆分新经验或让旧经验保持 active，并收紧其适用边界。关系存在不单独证明替代成立，必须与对象、证据、适用范围和同一变更一致。

## 8. 变更、删除与类型退出

创建前必须召回相邻 Pitfall、当前规则、ADR、WorkCase、Spark 和稳定来源，先判断不对象化、更新同一机制、拆分或建立新身份。更新 active Pitfall 时必须重新验证 root cause、resolution、avoidance、applicability 和 validation summary 的一致性；不能让新增样例把经验无依据泛化。

active、superseded 和 retired 文件均默认保留在当前载体中供来源、经验和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失经验历史时才成立，不能用删除代替终态。

Pitfall 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用经验；全部 active 经验还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Pitfall 类型定义 | 新建或实质修改本文时 | 唯一声明、字段准入与提升、绑定、状态、来源、证据、关系和独立复核完整且无第二权威 | 05、统一登记、本文、两个 V3 样本与独立复核 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 pitfall 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| Pitfall 准入与查重 | 创建对象前 | 失败已发生、解决、根因与验证成立、经验可复用、边界清楚且没有无损现有承载 | 原始事故、调查与验证来源、召回结果及 AI 语义比较 | AI 来源回读与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、WorkCase、Spark、ADR、文档或已有对象 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Pitfall 消费；报告字段和未验证范围 |
| 根因、解决与复用 | 创建或消费 active Pitfall 时 | 根因有证据、解决已执行验证、applicability 匹配当前环境、验证边界未被扩大 | source_refs、evidence_refs、当前环境和相邻规则 | AI 语义审核、来源及实际环境回读 | 当次经验及声明范围 | 不创建或暂停复用；补证据、缩小边界、重新验证或建立 WorkCase |
| 替代或退出 | 准备 superseded 或 retired 时 | 新经验或退出依据成立，对象、关系、证据、适用边界和时间一致 | 新旧 Pitfall、来源、证据、当前规则与 Human 决定 | AI 语义审核、目标回读和结构校验 | 当次终态与替代声明 | 保持 active；修正替代范围、补证据或进入 Human Gate |
| 变更与回读 | 创建、更正、补强、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核实际发生、对象粒度、因果证据、解决与验证、现时适用、复用安全、规则边界、替代完整性和退出依据。两个 V3 样本只能证明核心信息问题存在，不能证明旧经验当前有效、tags 必需或终态已被真实消费。

Code 可以确定性检查：载体、身份、Schema 闭集、字段类型与非空、状态值、状态条件、时间格式与顺序、引用 shape、目标身份与状态、自指、全部保留关系上的全生命周期单一直接替代源、跨对象时间顺序和 supersedes DAG。Code 不得判断根因是否真实、验证是否充分、外部协议是否仍当前、经验能否安全迁移、规则是否已吸收或自然语言经验是否同义。

最低验证样例必须覆盖：active、superseded、retired；每个状态缺条件字段或带禁止字段；两份 V3 样本的字段映射与不直接迁移；根因无证据、解决未执行、验证边界扩大、外部版本变化、多个独立机制捆绑；supersedes 的建立时与持久 source/target 状态、项目、全生命周期单一直接替代源、跨对象时间、自指、缺失目标和全部保留关系 DAG；旧 archived/tags/related_*/空占位被拒绝。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 根因、验证充分性或 applicability 存在无法依据当前来源无损裁决的争议；
2. 准备把经验提升为强制规则、接受重大风险，或决定超出 Human 已授权给 AI 的判断范围；
3. 准备 supersede、retire、合并或拆分经验，实际因果、复用安全或剩余适用范围需要 Human 判断；
4. 删除或迁移可能丢失对象身份、来源、证据、经验或替代历史；
5. 涉及安全、产品方向、责任归属或其它来源明确保留给 Human 的决定。

已有授权范围内据实记录一个证据充分的 Pitfall，不因对象类型本身重复进入 Gate。Human 确认不能替代因果证据、实际验证、Schema 和来源回读；技术结果也不能替代保留给 Human 的风险接受。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入、消费或宣称 Pitfall 成立：

1. 问题尚未解决、根因仍是推测、解决未执行或验证不足；
2. 没有可回指的原始事故、调查、验证来源或适用边界证据；
3. 仅凭一次相关现象声称因果机制，或把对象写成规则、任务、决定、操作手册或行动授权；
4. applicability 过度泛化、没有排除项，或外部协议与实现已变化却沿用旧验证；
5. 多个独立根因或不相容解决方式被捆绑；
6. 与当前规范或 active Pitfall 冲突，但没有完成获准的冲突处置；
7. 用关系、commit、测试成功或实现存在冒充经验普遍有效、规则已生效或行动已授权；
8. superseded 没有有效新 Pitfall 与单向关系，retired 没有具体退出依据；
9. 准备写入 archived、archive_reason、tags、repeatability、severity、superseded_by、source_objects、source_sparks、related_*、空占位或其它未登记内容；
10. 高影响取舍没有实际授权，或获准写入后没有回读与范围匹配验证。

暂停期间可以继续只读召回、来源与证据核对、机制拆分、适用边界收紧、重新验证、正式规则承载比较和 Human Gate 准备。只有失败、根因、解决、验证、复用价值与边界成立，冲突和 Schema 得到处置并完成写后回读后，才能恢复相应范围。
