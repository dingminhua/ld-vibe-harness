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

> 文件状态：`active`。本文是 `pitfall` 事实类型的唯一定义来源；它不使 Pitfall 读取、创建、校验、Helper、Code、tests、行动模板或 Web 能力自动成立。任何外部材料都必须按本文重新满足字段、来源、验证与适用边界，不能直接作为 V4 active 对象。

## 1. 价值判断

Pitfall 保存一个已经实际发生、查明、解决、验证且仍能迁移复用的失败机制，使后续 AI 能识别相似症状与触发条件，理解有证据的根因，在适用边界内复用实际解决与规避经验，避免重复误判和调试。

Pitfall 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 和行动模板承担；Pitfall 不承载 bug backlog、实施计划或行动授权。新增成本包括发现、查重、维护、Schema、迁移、时效复核和消费；通过只准入已发生且验证的单一失败机制、三状态、五个专属字段、两个共享语义字段并排除日志与自由标签，维护成本低于重复犯错和错误复用的损耗。普通文档、测试、代码说明或当前规则能够无损承载且不需要独立身份、状态、证据和替代历史时，不创建 Pitfall。

V4 只吸收经重新查重且具有稳定消费价值的语义字段，不继承旧 shape、旧引用数组或实例当前性。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定管辖项目当前事实源、Working Tree、来源回指和稳定事实边界。

Pitfall 是经验事实，不是规则来源。`avoidance` 说明在适用边界内如何识别、预防或安全复用经验，不取得 MUST 级规则权威。需要形成强制规则、Code 行为或行动结构时，必须由相应正式来源另行定义、授权和验证；吸收不会自动使 Pitfall 终态。

AI 消费 `avoidance` 时只能把它作为由当前证据和 applicability 限定的经验候选：先核对目标症状、触发条件、环境、版本、根因与验证覆盖是否仍相容，再决定是否用于当前判断或提出行动建议。它不能覆盖当前规范、授权或实际验证，也不能仅因 Pitfall 为 active 就自动执行；需要形成强制做法时必须进入相应正式来源。

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

### 类型专属结构定义

本类型没有类型专属结构

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `pitfall-fact-type::5. Pitfall 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `pitfall-fact-type::5. Pitfall 类型定义` |
| `created-at` | required | `inherit` |
| `updated-at` | required | `pitfall-fact-type::8. 变更、删除与类型退出` |
| `status` | required | `pitfall-fact-type::6. 对象语义与生命周期` |
| `urls` | conditional | `pitfall-fact-type::7. 来源、证据与替代关系` |
| `relations` | conditional | `pitfall-fact-type::7. 来源、证据与替代关系` |
| `disposition-summary` | conditional | `pitfall-fact-type::6. 对象语义与生命周期` |
| `closed-at` | conditional | `pitfall-fact-type::6. 对象语义与生命周期` |
| `adr-applicability` | required | `pitfall-fact-type::7. 来源、证据与替代关系` |
| `workcase-validation-summary` | required | `pitfall-fact-type::7. 来源、证据与替代关系` |
| `pitfall-symptoms` | required | `inherit` |
| `pitfall-trigger-conditions` | required | `inherit` |
| `pitfall-root-cause` | required | `inherit` |
| `pitfall-resolution` | required | `inherit` |
| `pitfall-avoidance` | required | `inherit` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `pitfall-symptoms` | `symptoms` | string | 失败或误判实际发生后的可观察表现与识别信号 | 不表示标题、根因、触发前置条件、当前任务进展或日志全文 | 必填非空；只描述可观察表现；同一机制的新表现可以据证补充 |
| `pitfall-trigger-conditions` | `trigger_conditions` | string | 会触发该失败机制的前置条件、组合与必要上下文 | 不表示失败后的症状、经验适用范围、根因或一般风险 | 必填非空；区分已证条件与未知条件；同一机制的新触发样例可以据证补充 |
| `pitfall-root-cause` | `root_cause` | string | 经稳定证据支持、能够解释症状与触发的失败因果机制 | 不表示相关现象、推测、ADR 选择理由、来源或验证摘要 | 必填非空；不能只凭单次相关性成立；根因实质变化通常形成新 Pitfall |
| `pitfall-resolution` | `resolution` | string | 已经实际解决该失败机制的修复方式及其必要边界 | 不表示提案、WorkCase 目标、实施 todo、规避建议或规则正文 | 必填非空；必须已执行并由 validation summary 与 evidence refs 支持；不相容修复形成新对象 |
| `pitfall-avoidance` | `avoidance` | string | 后续识别、预防或安全复用该经验的方式 | 不表示强制规则、行动授权、已执行修复或通用最佳实践 | 必填非空；只在 applicability 内成立；需要强制时转正确规则来源，不在本字段使用 MUST 冒充权威 |

### Schema 与对象载体

Pitfall 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `ldvh-base/pitfalls/<object_id>.yaml`。`object_id` 必须匹配 `pitfall-[0-9]{4,}`；文件名必须与 `object_id` 完全一致，分配后的身份不得因标题、路径、状态或内容改变。`title` 只简短识别失败机制，不复制 `symptoms` 或 `root_cause`。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义和类型专属字段定义组合。Pitfall 不得出现 current summary、priority、evolution、tags、`archive_reason`、repeatability、severity、source_objects/source_sparks、related_*、长命令日志字段、实现状态、revision history 或其它未登记内容。

## 6. 对象语义与生命周期

Pitfall 只记录已解决、已验证且可复用的失败机制。问题尚未解决、根因仍是推测、验证不足或适用边界不清时不得创建 active Pitfall。经验的存在不证明外部环境、协议或实现仍与验证时相同；消费前必须按 applicability、对象自有语义字段 的版本与 observed_at 重新判断现时适用性。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 根因、解决和验证仍可信，经验在 applicability 内仍可安全参考 | 只能作为新建初态；终态字段禁止；全部核心字段与证据成立；不表示规则权威 |
| `retired` | 原经验因适用条件消失、方向撤回、不再需要或已被新 Pitfall 的经验范围覆盖而退出当前选择 | disposition_summary、closed_at、自然语言验证说明 必填；必须有具体退出依据；被新 Pitfall 覆盖时在 disposition_summary 中说明替代关系，不建立独立关系边 |

初始状态只能是 active。正常转换只有 `active → retired`；终态不直接重开。根因、解决方式、规避方式或 applicability 的实质改变通常建立新 Pitfall；只有来源充分且仍是同一失败机制的事实更正、症状与触发补强、验证更新可以原地修正。

规范、Code 或行动模板吸收经验不会自动使 Pitfall 终态。Pitfall 即使 active 也只是经验参考，实际规则和行为来自相应正式来源。不得用单一 `archived` 状态混合存储、吸收和不再有效。

## 7. 来源、证据与替代关系

对象自有语义字段 至少回指原始事故或误判、调查输入和经验形成来源。自然语言验证说明 必须实际支持根因、解决已经生效、验证覆盖及 applicability；命令文本、“测试通过”叙述、文件存在或一次成功不能自证超出其覆盖的结论。外部来源会变化时必须记录 version 和 observed_at。

Pitfall 来自 Spark、WorkCase 或 ADR 时可以把源对象作为 source_ref；源对象已有分流关系时不复制反向关系。落实规避措施的 WorkCase 可以把 Pitfall 作为 source_ref；Pitfall 不维护双写 related_workcases。规范、Code、commit、文档、日志或外部页面不是事实对象，分别进入 对象自有语义字段 或 自然语言验证说明。

Pitfall 不定义 relation_key。新旧 Pitfall 之间的替代或覆盖关系通过 `disposition_summary` 表达，不建立独立关系边。新经验只替代旧经验的一部分时，应拆分新经验或让旧经验保持 active，并收紧其适用边界。

### 主动召回与消费时机

Pitfall 在当前出现可能相似的失败症状、进入已知触发条件、准备采用曾有失败风险的方案，或正在调查、修复、验证一项故障时产生召回机会。F2 Pitfall 候选卡直接投影 `object_id`、`title`、`status`、`symptoms`、`trigger_conditions`、`applicability`、`validation_summary` 和 `updated_at`；可以在允许字段中进行可回指到 field path 与实际文本的精确字面检索，但不生成或写回标签、关键词权重或语义分数。该类型化投影提供当前所需的快速检索；`tags` 不进入事实字段或第二分类权威。

默认候选只包含症状、触发条件、环境、版本或 applicability 与当前情形可能相容的 `active` Pitfall；不得因标题、错误文本或某个工具名相同就自动采用规避结论。上下文压缩后必须对当次已经语义选中且仍影响行动的 Pitfall 重新回读 F3，并重新核对当前环境、版本和 applicability；不在会话开始时全量展开全部 Pitfall。

`retired` Pitfall 只在精确引用、追溯历史失败或验证、检查替代链，或判断当前经验是新机制还是旧机制的变体时展开。AI 消费任何 Pitfall 前必须重新核对 symptoms、trigger conditions、root cause、resolution、avoidance、applicability、validation summary、来源版本与当前环境；对象被召回不表示根因已在当次重现，也不表示规避方法已获授权执行。

## 8. 变更、删除与类型退出

创建前必须召回相邻 Pitfall、当前规则、ADR、WorkCase、Spark 和稳定来源，先判断不对象化、更新同一机制、拆分或建立新身份。更新 active Pitfall 时必须重新验证 root cause、resolution、avoidance、applicability 和 validation summary 的一致性；不能让新增样例把经验无依据泛化。

active 和 retired 文件均默认保留在当前载体中供来源、经验和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失经验历史时才成立，不能用删除代替终态。

Pitfall 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用经验；全部 active 经验还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Pitfall 类型定义 | 新建或实质修改本文时 | 唯一声明、绑定、状态、来源、证据与关系完整且无第二权威 | 05、统一登记与本文 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 pitfall 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| Pitfall 准入与查重 | 创建对象前 | 失败已发生、解决、根因与验证成立、经验可复用、边界清楚且没有无损现有承载 | 原始事故、调查与验证来源、召回结果及 AI 语义比较 | AI 来源回读与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、WorkCase、Spark、ADR、文档或已有对象 |
| Pitfall 召回与消费 | 出现相似症状、进入触发条件、采用高风险方案、调查修复故障或压缩恢复已选经验时 | F2 卡片只投影现有权威字段并保留字面命中依据，不恢复 `tags`；`active` 候选的症状、触发、环境、版本与 applicability 可能相容；终态只作追溯或替代链候选；召回未被冒充为根因证明或行动授权 | 当前症状与环境、候选卡与命中字段、对象全文、来源版本、证据和验证范围 | 候选范围走查、对象与当前环境回读、AI 因果与适用审核 | 当次症状、环境与已展开经验 | 不复用规避结论；继续调查、重新验证、缩小边界或建立 WorkCase |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Pitfall 消费；报告字段和未验证范围 |
| 根因、解决与复用 | 创建或消费 active Pitfall 时 | 根因有证据、解决已执行验证、applicability 匹配当前环境、验证边界未被扩大 | 对象自有语义字段、自然语言验证说明、当前环境和相邻规则 | AI 语义审核、来源及实际环境回读 | 当次经验及声明范围 | 不创建或暂停复用；补证据、缩小边界、重新验证或建立 WorkCase |
| 退出 | 准备 retired 时 | 退出依据成立，证据、适用边界和时间一致 | 当前 Pitfall、来源、证据与 Human 决定 | AI 语义审核和结构校验 | 当次终态声明 | 保持 active；补证据或进入 Human Gate |
| 变更与回读 | 创建、更正、补强、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核实际发生、对象粒度、因果证据、解决与验证、现时适用、复用安全、规则边界、替代完整性和退出依据。外部样本不能证明经验当前有效、tags 必需或终态已被真实消费。

Code 的共同机械边界按 05 §§10–11 执行；对 Pitfall，只可额外检查本文明确给出的状态条件、跨对象时间顺序。根因真实性、验证充分性、外部协议当前性、迁移安全、规则吸收及自然语言同义性仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：active、retired；每个状态缺条件字段或带禁止字段；外部材料不得直接写入；根因无证据、解决未执行、验证边界扩大、外部版本变化、多个独立机制捆绑；与 retired 终态条件；archived/tags/related_*/空占位被拒绝。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 当前来源之间对根因、验证充分性或 applicability 存在相互冲突的证据、权威或适用边界，且需要 Human 在可保留的解释、方向或风险取舍之间作选择；仅因根因证据不足、验证不足或需要补充当前来源时，不进入 Human Gate；
2. 准备把经验提升为强制规则、接受重大风险，或决定超出 Human 已授权给 AI 的判断范围；
3. 准备 retire、合并或拆分经验，实际因果、复用安全或剩余适用范围需要 Human 判断；
4. 删除或迁移可能丢失对象身份、来源、证据、经验或替代历史；
5. 涉及安全、产品方向、责任归属或其它来源明确保留给 Human 的决定。

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权据实记录相应 Pitfall，且适用于该行动的全部来源规则许可条件已经成立时，不因对象类型本身重复进入 Human Gate。Human 确认不能替代因果证据、实际验证、Schema 和来源回读；技术结果也不能替代保留给 Human 的风险接受。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入、消费或宣称 Pitfall 成立：

1. 问题尚未解决、根因仍是推测、解决未执行或验证不足；这些证据或验证缺口应暂停并补证或复验，不因缺口本身进入 Human Gate；
2. 没有可回指的原始事故、调查、验证来源或适用边界证据；
3. 仅凭一次相关现象声称因果机制，或把对象写成规则、任务、决定、操作手册或行动授权；
4. applicability 过度泛化、没有排除项，或外部协议与实现已变化却沿用旧验证；
5. 多个独立根因或不相容解决方式被捆绑；
6. 与当前规范或 active Pitfall 冲突，但没有完成获准的冲突处置；
7. 用关系、commit、测试成功或实现存在冒充经验普遍有效、规则已生效或行动已授权；
8. retired 没有具体退出依据；
9. 准备写入 archived、archive_reason、tags、repeatability、severity、source_objects、source_sparks、related_*、空占位或其它未登记内容；
10. 高影响取舍没有实际授权，或获准写入后没有回读与范围匹配验证。

暂停范围与允许继续的行动按 00 §11 执行；对 Pitfall，只有失败、根因、解决、验证、复用价值与边界成立，冲突和 Schema 得到处置并完成写后回读后，才能恢复相应范围。
