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
  positioning: "定义 Pitfall 事实类型的对象边界、Schema、生命周期、形成边界、验证说明、替代关系与复用规则"
  scope: "管辖项目中已经发生、查明、解决、验证且仍有迁移复用价值的单一失败机制与规避经验"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `pitfall` 事实类型的唯一定义来源；它不使 Pitfall 读取、创建、校验、Helper、Code、tests、行动模板或 Web 能力自动成立。任何外部材料都必须按本文重新满足字段、来源、验证与适用边界，不能直接作为当前 active 对象。

## 1. 价值判断

Pitfall 保存一个已经实际发生、查明、解决、验证且仍能迁移复用的失败机制，使后续 AI 能识别相似症状与触发条件，理解当前范围内的根因判断，在适用边界内复用实际解决与规避经验，避免重复误判和调试。

Pitfall 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 和行动模板承担；Pitfall 不承载 bug backlog、实施计划或行动授权。新增成本包括发现、查重、维护、Schema、迁移、时效复核和消费；通过只准入已发生且验证的单一失败机制、两个状态、五个专属字段、两个共享语义字段并排除日志与自由标签，维护成本低于重复犯错和错误复用的损耗。普通文档、测试、代码说明或当前规则能够无损承载且不需要独立身份、状态、可复用经验边界和替代历史时，不创建 Pitfall。

当前版本只吸收经重新查重且具有稳定消费价值的语义字段，不继承旧 shape、旧引用数组或实例当前性。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定管辖项目当前事实源、Working Tree、来源回指和稳定事实边界。

Pitfall 是经验事实，不是规则来源。`avoidance` 说明在适用边界内如何识别、预防或安全复用经验，不取得 MUST 级规则权威。需要形成强制规则、Code 行为或行动结构时，必须由相应正式来源另行定义、授权和验证；吸收不会自动使 Pitfall 终态。

AI 消费 `avoidance` 时只能把它作为由对象自有语义字段和 applicability 限定的经验候选：先核对目标症状、触发条件、环境、版本、根因判断与验证覆盖是否仍相容，再决定是否用于当前判断或提出行动建议。它不能覆盖当前规范、授权或实际验证，也不能仅因 Pitfall 为 active 就自动执行；需要形成强制做法时必须进入相应正式来源。

## 3. 职责边界

本文负责定义：

1. `pitfall` 的类型语义、对象粒度、准入和排除边界；
2. Pitfall 的唯一当前承载位置、完整 Schema、状态和终态处置；
3. 症状、触发条件、根因、已验证解决方式、规避方法、适用边界和验证摘要；
4. Pitfall 的形成边界、验证说明、替代关系、变更、更正、删除和类型退出边界；
5. Pitfall 的验证要求、Human Gate、Stop Conditions 和最小失败范围。

本文不负责定义：

1. 正式规范、项目规则、强制纪律、Code 行为或行动模板步骤；
2. 未解决故障、开放问题、任务进度、实施计划、调试日志、研究正文或长期决定；
3. 其它事实类型的语义、状态和 Schema；
4. 标签词表、搜索算法、Helper API、CLI、Web 表单、Hook 或迁移兼容；
5. 仅因经验存在而产生的行动、风险接受或技术正确性授权。

AI 负责判断失败是否实际发生、根因判断与解决说明是否同症状、触发条件和验证覆盖相容、经验是否值得对象化、适用边界是否仍当前、是否重复以及复用是否安全；Code 只可按当前来源检查固定结构、值闭集、引用和状态条件。

## 4. 适用范围

一个经验只有同时满足以下条件，才可以形成 Pitfall：

1. 存在实际发生的失败或误判，不是设想、提醒或一般风险；
2. 问题已经实际解决，根因判断能够与症状和触发条件相容地说明，且没有把相关性冒充因果；
3. 解决方式已经实际采用并观察到结果，验证覆盖、结果、失败与未验证范围能够由 `validation_summary` 据实说明；
4. 后续存在现实复发概率或跨行动迁移价值；
5. 症状、触发条件、适用对象、环境、条件、范围和排除项清楚；
6. 存在可复用的解决与规避经验，但没有把经验写成规则或行动授权；
7. 已召回相邻 Pitfall、当前规则、ADR、WorkCase 和 Spark，没有可无损更新或重复对象；
8. 对象化减少的重复误判与调试负担高于发现、维护、复核和消费成本。

一个 Pitfall 只承载一个可独立识别、验证、替代或退出的失败机制，其身份由核心根因判断和相容的规避方式共同限定。增加同一机制的症状、触发样例或新的观察可以更新原对象；出现不同根因、互不相容处置，或新经验使旧经验不安全时必须拆分或新建并替代。

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
| `urls` | conditional | `pitfall-fact-type::7. 形成边界、验证说明与替代关系` |
| `relations` | conditional | `pitfall-fact-type::7. 形成边界、验证说明与替代关系` |
| `disposition-summary` | conditional | `pitfall-fact-type::6. 对象语义与生命周期` |
| `adr-applicability` | required | `pitfall-fact-type::7. 形成边界、验证说明与替代关系` |
| `workcase-validation-summary` | required | `pitfall-fact-type::7. 形成边界、验证说明与替代关系` |
| `pitfall-symptoms` | required | `inherit` |
| `pitfall-trigger-conditions` | required | `inherit` |
| `pitfall-root-cause` | required | `inherit` |
| `pitfall-resolution` | required | `inherit` |
| `pitfall-avoidance` | required | `inherit` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `pitfall-symptoms` | `symptoms` | string | 失败或误判实际发生后的可观察表现与识别信号 | 不表示标题、根因、触发前置条件、当前任务进展或日志全文 | 必填非空；只描述实际观察到的表现；同一机制的新表现可以补充 |
| `pitfall-trigger-conditions` | `trigger_conditions` | string | 会触发该失败机制的前置条件、组合与必要上下文 | 不表示失败后的症状、经验适用范围、根因或一般风险 | 必填非空；区分已观察条件与未知条件；同一机制的新触发样例可以补充 |
| `pitfall-root-cause` | `root_cause` | string | 在当前经验范围内能够解释症状与触发的根因判断 | 不表示相关现象、未经说明的普遍因果、ADR 选择理由、来源或验证摘要 | 必填非空；必须与 symptoms、trigger_conditions 和 validation_summary 相容；必要时区分已观察事实、当前根因判断和仍未知的机制环节；不能只凭单次相关性成立；根因判断实质变化通常形成新 Pitfall |
| `pitfall-resolution` | `resolution` | string | 已经实际采用以解决该失败机制的处理方式及其必要边界 | 不表示提案、WorkCase 目标、实施 todo、规避建议或规则正文 | 必填非空；必须已实际采用；说明适用前提、处理对象或动作及可观察成功信号，且在适用前提不成立或成功信号未出现时不把处理宣称为通用修复；validation_summary 据实说明观察到的结果、覆盖与未知范围；不相容修复形成新对象 |
| `pitfall-avoidance` | `avoidance` | string | 后续识别、预防或安全复用该经验的方式 | 不表示强制规则、行动授权、已执行修复或通用最佳实践 | 必填非空；说明复用前应核对的关键条件、处理后的确认信号，以及不相容时应继续调查、重新验证或转入正确对象的边界；只在 applicability 内成立；需要强制时转正确规则来源，不在本字段使用 MUST 冒充权威 |

### Schema 与对象载体

Pitfall 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `ldvh-base/pitfalls/<object_id>.yaml`。`object_id` 必须匹配 `pitfall-[0-9]{4,}`；文件名必须与 `object_id` 完全一致，分配后的身份不得因标题、路径、状态或内容改变。`title` 只简短识别失败机制，不复制 `symptoms` 或 `root_cause`。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义和类型专属字段定义组合。Pitfall 不得出现 current summary、priority、evolution、tags、`archive_reason`、repeatability、severity、source_objects/source_sparks、related_*、长命令日志字段、实现状态、revision history 或其它未登记内容。

### 面向 Human 的详情阅读投影

当 Web 或其它 Human 阅读面呈现可消费 Pitfall 的详情时，必须按对象实际存在字段依次使用下列中文区段标题：`现象`（`symptoms`）、`触发`（`trigger_conditions`）、`范围`（`applicability`）、`验证`（`validation_summary`）、`根因`（`root_cause`）、`方案`（`resolution`）、`规避`（`avoidance`）；`retired` 对象的 `disposition_summary` 另以 `处置` 呈现。八个标题均为两个汉字。条件或可选字段不存在时如实省略对应区段，不生成空态、默认结论或替代内容；类型来源定义为必填的字段缺失或类型不符时，按 08 §5.3 如实显示空态与字段问题。

这些标题只帮助 Human 按字段身份阅读：`现象`是实际可观察表现，`触发`是失败前置条件，`范围`是经验复用边界，`验证`是已观察结果与未知覆盖，`根因`是当前机制判断，`方案`是实际采用的处理，`规避`是可复用的预防经验，`处置`只说明终态如何退出。它们不新增字段、不改写 YAML 字段名，也不允许 Web 用通用或旧字段词替代，或合并字段后要求读者自行分辨。

## 6. 对象语义与生命周期

Pitfall 只记录已解决、已验证且可复用的失败机制。问题尚未解决、无法形成与已观察症状和触发条件相容的根因判断、无法如实说明处理结果与未覆盖范围，或适用边界不清时不得创建 active Pitfall。经验的存在不证明外部环境、协议或实现仍与验证时相同；消费前必须按 applicability 以及对象自有语义字段中实际记录的环境、版本或观察时点，重新判断现时适用性。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 根因判断、解决和验证说明仍可信，经验在 applicability 内仍可安全参考 | 只能作为新建初态；终态字段禁止；全部核心字段、验证说明和适用边界成立；不表示规则权威 |
| `retired` | 原经验因适用条件消失、方向撤回、不再需要或已被新 Pitfall 的经验范围覆盖而退出当前选择 | disposition_summary、自然语言验证说明必填；必须有具体退出依据；终态更新以 `updated_at` 记录；disposition_summary 直接写处置结论，不重复 `retired` 状态或添加“退出理由：”等字段标签；被新 Pitfall 覆盖时在其中说明替代关系，不建立独立关系边 |

初始状态只能是 active。正常转换只有 `active → retired`；终态不直接重开。任何 Pitfall 转为 `retired` 都必须在写入前取得 Human 对该对象退出的明确授权；仅授权创建、普通更新、事实更正、阅读、验证或记录经验，不覆盖退出。根因判断、解决方式、规避方式或 applicability 的实质改变通常建立新 Pitfall；只有仍是同一失败机制的事实更正、症状与触发补强、验证说明更新可以原地修正。

规范、Code 或行动模板吸收经验不会自动使 Pitfall 终态。Pitfall 即使 active 也只是经验参考，实际规则和行为来自相应正式来源。不得用单一 `archived` 状态混合存储、吸收和不再有效。

## 7. 形成边界、验证说明与替代关系

Pitfall 通过对象自有语义字段据实说明实际症状、已观察到的触发条件、当前根因判断、已采用的处理、观察到的结果、验证覆盖、未覆盖范围和 applicability。为使后来者能安全复用，跨这些字段必须能读出一个最小处理闭环：什么条件已命中、对什么对象采取了什么处理、观察到什么成功信号；条件不命中或成功信号未出现时，经验应在何处停止并继续调查、重新验证或转入正确对象。该闭环以与经验粒度相称的自然语言表达，不要求固定步骤模板、命令日志、路径清单或外部引用。

`validation_summary` 是当前说明，不要求附带证据引用、日志、路径、命令或来源对象；命令文本、“测试通过”叙述、文件存在或一次成功也不能单独把经验扩大为超出其说明范围的结论。外部资料确有长期消费价值时才可按 05 使用 `urls`，其 `summary` 说明支持范围、限制以及必要的版本或观察时点。

Pitfall 不建立 `source_ref`、`evidence_ref` 或来源关系。Spark、WorkCase、ADR、规范、Code、commit、文档、日志或外部页面可以作为形成该经验时的当次输入，但不因此成为 Pitfall 的字段、关系或证明材料；只有确实影响后续理解的形成范围、观察、处理、限制或未知范围，才在相应自有语义字段中据实说明。

Pitfall 不定义 relation_key。新旧 Pitfall 之间的替代或覆盖关系通过 `disposition_summary` 表达，不建立独立关系边。新经验只替代旧经验的一部分时，应拆分新经验或让旧经验保持 active，并收紧其适用边界。

### 主动召回与消费时机

Pitfall 在当前出现可能相似的失败症状、进入已知触发条件、准备采用曾有失败风险的方案，或正在调查、修复、验证一项故障时产生召回机会。F2 Pitfall 候选卡直接投影 `object_id`、`title`、`status`、`symptoms`、`trigger_conditions`、`applicability`、`validation_summary` 和 `updated_at`；可以在允许字段中进行可回指到 field path 与实际文本的精确字面检索，但不生成或写回标签、关键词权重或语义分数。该类型化投影提供当前所需的快速检索；`tags` 不进入事实字段或第二分类权威。

默认候选只包含症状、触发条件、环境、版本或 applicability 与当前情形可能相容的 `active` Pitfall；不得因标题、错误文本或某个工具名相同就自动采用规避结论。上下文压缩后必须对当次已经语义选中且仍影响行动的 Pitfall 重新回读 F3，并重新核对当前环境、版本和 applicability；不在会话开始时全量展开全部 Pitfall。

`retired` Pitfall 只在精确引用、追溯历史失败或验证、检查替代链，或判断当前经验是新机制还是旧机制的变体时展开。AI 消费任何 Pitfall 前必须重新核对 symptoms、trigger conditions、root cause、resolution、avoidance、applicability、validation summary、对象实际记录的环境或版本与当前环境；对象被召回不表示根因已在当次重现，也不表示规避方法已获授权执行。

## 8. 变更、删除与类型退出

创建前必须召回相邻 Pitfall、当前规则、ADR、WorkCase 和 Spark，先判断不对象化、更新同一机制、拆分或建立新身份。更新 active Pitfall 时必须重新核对 root cause、resolution、avoidance、applicability 和 validation summary 的一致性；不能让新增样例把经验无依据泛化。

active 和 retired 文件均默认保留在当前载体中供来源、经验和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失经验历史时才成立，不能用删除代替终态。

Pitfall 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用经验；全部 active 经验还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Pitfall 类型定义 | 新建或实质修改本文时 | 唯一声明、绑定、状态、形成边界、验证说明与关系边界完整且无第二权威 | 05、统一登记与本文 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 pitfall 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| Pitfall 准入与查重 | 创建对象前 | 失败已实际发生、处理已经采用并观察到结果、根因判断与验证说明相容、经验可复用、边界清楚且没有无损现有承载 | 候选对象的自有语义字段、召回结果及 AI 语义比较 | AI 对当前输入、对象与环境的据实审核和全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、WorkCase、Spark、ADR、文档或已有对象 |
| Pitfall 召回与消费 | 出现相似症状、进入触发条件、采用高风险方案、调查修复故障或压缩恢复已选经验时 | F2 卡片只投影现有权威字段并保留字面命中依据，不恢复 `tags`；`active` 候选的症状、触发、实际记录的环境或版本与 applicability 可能相容；终态只作追溯或替代链候选；召回未被冒充为根因证明或行动授权 | 当前症状与环境、候选卡与命中字段、对象全文和验证说明 | 候选范围走查、对象与当前环境回读、AI 因果与适用审核 | 当次症状、环境与已展开经验 | 不复用规避结论；继续调查、重新验证、缩小边界或建立 WorkCase |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Pitfall 消费；报告字段和未验证范围 |
| 根因、解决与复用 | 创建或消费 active Pitfall 时 | 根因判断与症状、触发条件和验证说明相容；已观察事实、当前判断和未知机制未被混写；处理已实际采用并观察到结果，且能说明适用前提、处理、成功信号及不命中时的边界；applicability 匹配当前环境，验证边界未被扩大 |对象自有语义字段、自然语言验证说明、当前环境和相邻规则 | AI 语义审核与实际环境回读 | 当次经验及声明范围 | 不创建或暂停复用；缩小边界、继续调查、重新验证或建立 WorkCase |
| 退出 | 准备 retired 时 | 已取得针对该 Pitfall 退出的明确 Human 授权，且退出依据、适用边界、验证说明和时间一致 | 当前 Pitfall 与 Human 明确授权 | AI 语义审核和结构校验 | 当次终态声明 | 保持 active；补充退出说明并取得 Human 授权 |
| 变更与回读 | 创建、更正、补强、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核实际发生、对象粒度、根因判断与观察的相容性、解决与验证说明、现时适用、复用安全、规则边界、替代完整性和退出依据。外部样本不能证明经验当前有效、tags 必需或终态已被真实消费。

Code 的共同机械边界按 05 §§10–11 执行；对 Pitfall，只可额外检查本文明确给出的状态条件、跨对象时间顺序。根因真实性、验证充分性、外部协议当前性、迁移安全、规则吸收及自然语言同义性仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：active、retired；每个状态缺条件字段或带禁止字段；不带 `urls`、`relations`、`source_ref` 或 `evidence_ref` 的完整 Pitfall；`source_ref`、`evidence_ref` 与其它未登记字段被拒绝；根因判断与症状、触发或验证说明不相容、解决未实际采用、验证边界扩大、外部版本变化、多个独立机制捆绑；与 retired 终态条件；archived/tags/related_*/空占位被拒绝。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 当前对象、规则或环境之间对根因判断、验证说明或 applicability 存在相互冲突的内容、权威或适用边界，且需要 Human 在可保留的解释、方向或风险取舍之间作选择；仅因当前说明不足、验证不足或需要补充观察时，不进入 Human Gate；
2. 准备把经验提升为强制规则、接受重大风险，或决定超出 Human 已授权给 AI 的判断范围；
3. 准备将任何 Pitfall 转为 `retired`；此项始终需要 Human 对目标 Pitfall 及退出动作的明确授权，不因 AI 已判断退出依据充分而豁免。准备合并或拆分经验且实际因果、复用安全或剩余适用范围需要 Human 判断时，也进入 Human Gate；
4. 删除或迁移可能丢失对象身份、经验、验证说明或替代历史；
5. 涉及安全、产品方向、责任归属或其它来源明确保留给 Human 的决定。

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权据实记录相应 Pitfall，且适用于该行动的全部来源规则许可条件已经成立时，不因对象类型本身重复进入 Human Gate。Human 确认不能替代实际观察、验证说明、Schema 和来源回读；技术结果也不能替代保留给 Human 的风险接受。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入、消费或宣称 Pitfall 成立：

1. 问题尚未解决、无法形成与已观察症状和触发条件相容的根因判断、解决未实际采用或验证说明不足；这些观察或验证缺口应暂停并补充观察或复验，不因缺口本身进入 Human Gate；
2. 无法如实说明实际症状、已采取的处理、观察到的验证结果、未覆盖范围或适用边界；或者无法说明当前根因判断中已观察、推断与未知部分的区别，以及处理不命中时的安全退出边界；
3. 仅凭一次相关现象声称因果机制，或把对象写成规则、任务、决定、操作手册或行动授权；
4. applicability 过度泛化、没有排除项，或外部协议与实现已变化却沿用旧验证；
5. 多个独立根因或不相容解决方式被捆绑；
6. 与当前规范或 active Pitfall 冲突，但没有完成获准的冲突处置；
7. 用关系、commit、测试成功或实现存在冒充经验普遍有效、规则已生效或行动已授权；
8. 准备转为 retired 却没有针对目标 Pitfall 退出的明确 Human 授权，或 retired 没有具体退出依据；
9. 准备写入 archived、archive_reason、tags、repeatability、severity、source_objects、source_sparks、related_*、空占位或其它未登记内容；
10. 高影响取舍没有实际授权，或获准写入后没有回读与范围匹配验证。

暂停范围与允许继续的行动按 00 §11 执行；对 Pitfall，只有失败、根因判断、解决、验证说明、复用价值与边界成立，冲突和 Schema 得到处置并完成写后回读后，才能恢复相应范围。
