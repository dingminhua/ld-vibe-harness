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

新建 Pitfall 使用 `fact-object-controlled-creation`（31）；既有 Pitfall 的更正、draft/promote/discard 等生命周期变化或承接处置使用 `fact-object-lifecycle-change`（32）。模板不替代本文的完整性、逐对象 Human 决定或实际验证条件。

Pitfall 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累。V4 稳定推进由 WorkCase 和行动模板承担；Pitfall 不承载 bug backlog、实施计划或行动授权。新增成本包括发现、查重、维护、Schema、迁移、时效复核和消费；通过只准入已发生且验证的单一失败机制、四个状态、五个专属字段、两个共享语义字段并排除日志与自由标签，维护成本低于重复犯错和错误复用的损耗。普通文档、测试、代码说明或当前规则能够无损承载且不需要独立身份、状态、可复用经验边界和替代历史时，不创建 Pitfall。Pitfall 不设置按对象数量或正文长度形成的硬上限，也不按时间自动过期；对象增长由完整准入、全量查重、单一机制粒度、Human 逐对象确认和本文 Stop Conditions 约束。

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
4. 标签词表、搜索算法、Helper API、CLI、Web 表单、Git Hook 或迁移兼容；
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

当 Web 或其它 Human 阅读面按 08 §5.3 呈现 Pitfall 详情时，必须按对象实际存在字段依次使用下列中文区段标题：`现象`（`symptoms`）、`触发`（`trigger_conditions`）、`范围`（`applicability`）、`验证`（`validation_summary`）、`根因`（`root_cause`）、`方案`（`resolution`）、`规避`（`avoidance`）；`discarded` 对象的 `disposition_summary` 另以 `处置` 呈现。八个标题均为两个汉字。条件或可选字段不存在时如实省略对应区段，不生成空态、默认结论或替代内容；类型来源定义为必填的字段缺失或类型不符时，按 08 §5.3 如实显示空态与字段问题。

这些标题只帮助 Human 按字段身份阅读：`现象`是实际可观察表现，`触发`是失败前置条件，`范围`是经验复用边界，`验证`是已观察结果与未知覆盖，`根因`是当前机制判断，`方案`是实际采用的处理，`规避`是可复用的预防经验，`处置`只说明为何废弃。对象状态必须按当前值分别显示为 `draft`“待确认”、`active`“活跃”、`discarded`“已废弃”；这些中文词是 Human 投影，不改写事实状态。它们不新增字段、不改写 YAML 字段名，也不允许 Web 用通用或旧字段词替代，或合并字段后要求读者自行分辨。

## 6. 对象语义与生命周期

Pitfall 只记录已解决、已验证且可复用的失败机制。问题尚未解决、无法形成与已观察症状和触发条件相容的根因判断、无法如实说明处理结果与未覆盖范围，或适用边界不清时不得创建 Pitfall，包括不得以 `draft` 保存半成品。`draft` 只表示完整经验尚未取得 Human 的最终确认，不降低任何正文、验证、查重或单一机制粒度要求。经验的存在不证明外部环境、协议或实现仍与验证时相同；消费前必须按 applicability 以及对象自有语义字段中实际记录的环境、版本或观察时点，重新判断现时适用性。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `draft` | 全部现场信息、根因判断、解决、规避、验证和适用边界已经按正式 Pitfall 的完整形状保存，但 Human 尚未确认其成为活跃经验 | 只能作为新建初态；全部 active 核心字段和验证条件逐项成立；`disposition_summary` 禁止；可以在确认前据实更正，但每个成功回读快照都必须完整合法 |
| `active` | Human 已针对最终 draft 快照确认该 Pitfall；根因判断、解决和验证说明仍可信，经验在 applicability 内仍可安全参考 | 只能由同一对象 `draft → active` 形成；除 Code 托管的 `updated_at` 与 `status` 外，promote 前后解析值必须逐值相同；终态字段禁止；不表示规则权威或技术观察由 Human 代替 |
| `discarded` | 完整 draft 未被 Human 接受，或曾活跃经验因适用条件消失、方向撤回、不再需要或已被新 Pitfall 覆盖而废弃 | 对当前合法对象只能由 `draft → discarded` 或 `active → discarded` 形成；全部核心正文、验证、边界和关系继续保留；`disposition_summary` 必填并据实区分“draft 未被接受”与“曾活跃但已不再适用”的处置依据；终态不重开，不表示对象未曾完整或可以删除 |

初始状态只能是 `draft`。正常转换只有 `draft → active`、`draft → discarded` 和 `active → discarded`；`discarded` 是终态，不直接重开。draft 的普通更正保持 `status=draft`，可以修改任一对象自有语义字段以形成更准确的最终快照，但不得在任一中间写入中缺字段、写占位或降低验证充分性。Human 只审核最终回读快照；此前更正不构成 promote，也不要求把一组 draft 批量原子处理。

`retired` 不是 Pitfall 的当前合法状态、初态或普通转换节点。迁移三态模型前已经存在且因此机械无效的 `status=retired` 载体，只能复用 05 的 invalid-before exact-CAS 修复边界，在显式迁移中改为 `discarded`：after 必须完整合法，除 `status` 与 Code 托管的 `updated_at` 外，全部解析后正文、关系、身份、`created_at` 和既有非空 `disposition_summary` 必须逐值保持；不得借修复新增、删除或改写内容，不提供 retired 到其它状态、当前合法对象到 retired、无指纹写入或迁移专用旁路。该边界只使旧无效载体能够收敛到当前三态，不使 retired 重新成为可创建、可召回或可消费的合法状态。

`draft → active` 的 promote 只改变 `status`：同一次完整 after 中，除 Code 托管的 `updated_at` 外，`title`、`urls`、`relations`、`applicability`、`validation_summary`、五个 Pitfall 专属字段、身份和 `created_at` 都必须与 before 解析值精确相同，且不得新增 `disposition_summary`。需要完善内容时必须先保持 draft 更正并回读，再由 Human 针对最终指纹确认；不得在 promote 中夹带“顺便完善”。`draft → discarded` 和 `active → discarded` 都必须保持全部正文与关系不变，只允许 `status` 变化并新增非空 `disposition_summary`；前者说明 Human 不接受的决定和边界，后者说明曾活跃经验不再适用的具体依据。三个转换都必须在写入前取得 Human 对准确对象、当前完整快照和目标动作的明确授权。Human 确认或废弃决定只决定经验对象状态，不替代实际症状、处理、技术验证和 applicability。

WorkCase Gate 1 可以在当前 `execution_authorization` 中逐项列明执行期 Pitfall 行动，并由准确 `execution_approval` 授权消费。只有失败确在该 WC 推进中实际发生、已经解决和验证、完整 draft 满足本文全部准入与查重条件时，授权包中相应的现场保留边界才允许执行者创建 `status=draft` Pitfall，并在 draft 创建回读后由 source WC 写 `contributed-to`；不因进入保存步骤或切换执行者重复请求 Human。active 初态仍不合法。promote、discard 或其它变化只有在 Gate 1 已针对当时可精确绑定的目标对象、动作、允许影响与风险逐项列明时才获授权；执行中才形成、Gate 1 无法绑定最终快照的 draft 不得反向推定 promote/discard 授权，也不得在执行期询问扩权。独立 subagent 只作为可由授权包覆盖的推荐复核机制，不是 draft 成立条件；模板和本文不证明环境具有 spawn 能力。

每个 draft 独立审核。WC 可以在 draft 尚未 promote 或 discard 时关闭；WC 关闭不批量处理 draft，不要求“全部已审核”收据，也不改变 draft 状态。审核时只沿 WC 实际 `contributed-to` 关系定位并筛选当前 draft：准确则 Human 确认后 promote；需完善则保持 draft 更正、回读并重新提交最终快照；不接受则 discarded；延期则保持 draft。没有数量上限、时间阈值或自动过期转换。

规范、Code 或行动模板吸收经验不会自动使 Pitfall 终态。Pitfall 即使 active 也只是经验参考，实际规则和行为来自相应正式来源。不得用单一 `archived` 状态混合存储、吸收和不再有效。

## 7. 形成边界、验证说明与替代关系

Pitfall 通过对象自有语义字段据实说明实际症状、已观察到的触发条件、当前根因判断、已采用的处理、观察到的结果、验证覆盖、未覆盖范围和 applicability。为使后来者能安全复用，跨这些字段必须能读出一个最小处理闭环：什么条件已命中、对什么对象采取了什么处理、观察到什么成功信号；条件不命中或成功信号未出现时，经验应在何处停止并继续调查、重新验证或转入正确对象。该闭环以与经验粒度相称的自然语言表达，不要求固定步骤模板、命令日志、路径清单或外部引用。

`validation_summary` 是当前说明，不要求附带证据引用、日志、路径、命令或来源对象；命令文本、“测试通过”叙述、文件存在或一次成功也不能单独把经验扩大为超出其说明范围的结论。外部资料确有长期消费价值时才可按 05 使用 `urls`，其 `summary` 说明支持范围、限制以及必要的版本或观察时点。

Pitfall 不建立 `source_ref`、`evidence_ref` 或来源关系。Spark、WorkCase、ADR、规范、Code、commit、文档、日志或外部页面可以作为形成该经验时的当次输入，但不因此成为 Pitfall 的字段、关系或证明材料；只有确实影响后续理解的形成范围、观察、处理、限制或未知范围，才在相应自有语义字段中据实说明。

Pitfall 不定义 relation_key。新旧 Pitfall 之间的替代或覆盖关系通过 `disposition_summary` 表达，不建立独立关系边。新经验只替代旧经验的一部分时，应拆分新经验或让旧经验保持 active，并收紧其适用边界。

### 主动召回与消费时机

Pitfall 在当前出现可能相似的失败症状、进入已知触发条件、准备采用曾有失败风险的方案，或正在调查、修复、验证一项故障时产生召回机会。F2 Pitfall 候选卡直接投影 `object_id`、`title`、`status`、`symptoms`、`trigger_conditions`、`applicability`、`validation_summary` 和 `updated_at`；可以在允许字段中进行可回指到 field path 与实际文本的精确字面检索，但不生成或写回标签、关键词权重或语义分数。该类型化投影提供当前所需的快速检索；`tags` 不进入事实字段或第二分类权威。

默认候选只包含症状、触发条件、环境、版本或 applicability 与当前情形可能相容的 `active` Pitfall；`draft` 和 `discarded` 不进入普通经验召回，也不得被当作已确认规避经验。draft 审核只能由精确引用或来源定义的关系导航定位，不能因标题或文本命中形成批量审核队列。不得因标题、错误文本或某个工具名相同就自动采用规避结论。上下文压缩后必须对当次已经语义选中且仍影响行动的 Pitfall 重新回读 F3，并重新核对当前环境、版本和 applicability；不在会话开始时全量展开全部 Pitfall。

`draft` 和 `discarded` Pitfall 只在精确引用、来源关系导航、审核最终 draft、追溯历史失败或验证、检查替代说明，或判断当前经验是新机制还是旧机制的变体时展开。AI 消费任何 active Pitfall 前必须重新核对 symptoms、trigger conditions、root cause、resolution、avoidance、applicability、validation summary、对象实际记录的环境或版本与当前环境；对象被召回不表示根因已在当次重现，也不表示规避方法已获授权执行。

## 8. 变更、删除与类型退出

创建前必须召回相邻 Pitfall、当前规则、ADR、WorkCase 和 Spark，先判断不对象化、更新同一机制、拆分或建立新身份。创建只能形成完整 draft。更新 draft 或 active Pitfall 时必须重新核对 root cause、resolution、avoidance、applicability 和 validation summary 的一致性；不能让新增样例把经验无依据泛化。draft 的完善、更正和最终审核不改变对象身份。

draft、active 和 discarded 文件均默认保留在当前载体中供来源、经验和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍适用事实已处置且不会丢失经验历史时才成立，不能用删除代替 discarded。draft 不按时间自动删除、discard 或 promote。

Pitfall 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部现有对象、引用消费者和仍适用经验；全部 active 经验还必须获得明确稳定承接，不得只删除类型规范或隐藏对象目录。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Pitfall 类型定义 | 新建或实质修改本文时 | 唯一声明、绑定、状态、形成边界、验证说明与关系边界完整且无第二权威 | 05、统一登记与本文 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 pitfall 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| Pitfall 准入与查重 | 创建对象前 | 失败已实际发生、处理已经采用并观察到结果、根因判断与验证说明相容、经验可复用、边界清楚且没有无损现有承载 | 候选对象的自有语义字段、召回结果及 AI 语义比较 | AI 对当前输入、对象与环境的据实审核和全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；留在当前行动、WorkCase、Spark、ADR、文档或已有对象 |
| Pitfall 召回与消费 | 出现相似症状、进入触发条件、采用高风险方案、调查修复故障或压缩恢复已选经验时 | F2 卡片只投影现有权威字段并保留字面命中依据，不恢复 `tags`；`active` 候选的症状、触发、实际记录的环境或版本与 applicability 可能相容；终态只作追溯或替代链候选；召回未被冒充为根因证明或行动授权 | 当前症状与环境、候选卡与命中字段、对象全文和验证说明 | 候选范围走查、对象与当前环境回读、AI 因果与适用审核 | 当次症状、环境与已展开经验 | 不复用规避结论；继续调查、重新验证、缩小边界或建立 WorkCase |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、身份、字段闭集、类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Pitfall 消费；报告字段和未验证范围 |
| 根因、解决与复用 | 创建或消费 active Pitfall 时 | 根因判断与症状、触发条件和验证说明相容；已观察事实、当前判断和未知机制未被混写；处理已实际采用并观察到结果，且能说明适用前提、处理、成功信号及不命中时的边界；applicability 匹配当前环境，验证边界未被扩大 |对象自有语义字段、自然语言验证说明、当前环境和相邻规则 | AI 语义审核与实际环境回读 | 当次经验及声明范围 | 不创建或暂停复用；缩小边界、继续调查、重新验证或建立 WorkCase |
| draft 审核与处置 | 准备 promote、discard 或延后审核时 | 已精确读取最终 draft；Human 直接决定或 WorkCase Gate 1 授权包绑定该准确对象与动作；promote 只改变状态，discard 保留正文并增加处置，延期保持 draft；不依赖 WC 是否已关闭 | 当前 draft、Human 明确决定或 Gate 1 `execution_authorization` / `execution_approval` 与对象指纹 | AI 语义审核、CAS、转换校验和写后回读 | 当次一个 draft 的状态处置 | 保持 draft；普通行动先更正完善、重新回读或取得准确决定，获批 WorkCase 未授权处置按 21、34 收敛；不批量原子处理 |
| active 废弃 | 准备 `active → discarded` 时 | 已取得针对该 active Pitfall 废弃的直接 Human 授权，或 WorkCase Gate 1 已逐项绑定准确 active 对象、目标动作和风险；不再适用的依据、适用边界、验证说明和时间一致 | 当前 Pitfall 与 Human 明确授权，或 Gate 1 授权包与批准 | AI 语义审核、CAS、转换校验和写后回读 | 当次终态声明 | 保持 active；普通行动补充具体处置说明并取得 Human 授权，获批 WorkCase 未授权处置按 21、34 收敛 |
| 变更与回读 | 创建、更正、补强、替代、退出、拆分、合并或删除后 | 获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残余风险 |

AI 必须审核实际发生、对象粒度、根因判断与观察的相容性、解决与验证说明、现时适用、复用安全、规则边界、替代完整性和退出依据。外部样本不能证明经验当前有效、tags 必需或终态已被真实消费。

Code 的共同机械边界按 05 §§10–11 执行；对 Pitfall，只可额外检查本文明确给出的状态条件、跨对象时间顺序。根因真实性、验证充分性、外部协议当前性、迁移安全、规则吸收及自然语言同义性仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：draft、active、discarded；初态只允许完整 draft；draft 与 active 正文 shape 相同；draft 原地完善后回读；promote 状态-only 的正例和夹带正文修改的拒绝；draft 不接受与 active 不再适用均转为 discarded，两类 discard 都保留完整正文与关系并要求具体处置说明；discarded 终态不重开；legacy retired invalid-before 只能在 exact-CAS 下保持全部解析值与既有处置不变并修复为 discarded，改正文、改关系、改处置、改为其它状态或缺少精确指纹均拒绝；每个状态缺条件字段或带禁止字段；默认召回只含 active；不带 `urls`、`relations`、`source_ref` 或 `evidence_ref` 的完整 Pitfall；`source_ref`、`evidence_ref` 与其它未登记字段被拒绝；根因判断与症状、触发或验证说明不相容、解决未实际采用、验证边界扩大、外部版本变化、多个独立机制捆绑；archived/retired/tags/related_*/空占位被拒绝。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 当前对象、规则或环境之间对根因判断、验证说明或 applicability 存在相互冲突的内容、权威或适用边界，且需要 Human 在可保留的解释、方向或风险取舍之间作选择；仅因当前说明不足、验证不足或需要补充观察时，不进入 Human Gate；
2. 准备把经验提升为强制规则、接受重大风险，或决定超出 Human 已授权给 AI 的判断范围；
3. 准备将 draft promote 为 active，或将 draft/active discard 为 discarded；每项始终需要 Human 对准确对象、目标动作和风险的明确授权。当前 WorkCase Gate 1 已在 `execution_authorization` 中逐项绑定当时准确对象与动作并形成有效 `execution_approval` 时，该授权已经存在，不因进入转换步骤重复确认；执行中才形成、Gate 1 无法绑定最终快照的 draft 不获 promote/discard 授权。准备合并或拆分经验且实际因果、复用安全或剩余适用范围需要 Human 判断时，也进入 Human Gate；
4. 删除或迁移可能丢失对象身份、经验、验证说明或替代历史；
5. 涉及安全、产品方向、责任归属或其它来源明确保留给 Human 的决定。

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权据实记录相应 Pitfall，或当前 WorkCase Gate 1 授权包已逐项覆盖准确对象、动作与风险，且适用于该行动的全部来源规则许可条件已经成立时，不因对象类型、模板步骤或执行者切换重复进入 Human Gate。获批 WorkCase 中出现未列明、范围扩大或新增风险的 Pitfall 行动时，不在执行期询问扩权；保持零写入并按 21、34 收敛受影响 item。Human 确认不能替代实际观察、验证说明、Schema 和来源回读；技术结果也不能替代保留给 Human 的风险接受。

## 11. Stop Conditions

出现以下情况时暂停最小相关范围，不得写入、消费或宣称 Pitfall 成立：

1. 问题尚未解决、无法形成与已观察症状和触发条件相容的根因判断、解决未实际采用或验证说明不足；不得以 draft 保存这些半成品，这些观察或验证缺口应暂停并补充观察或复验，不因缺口本身进入 Human Gate；
2. 无法如实说明实际症状、已采取的处理、观察到的验证结果、未覆盖范围或适用边界；或者无法说明当前根因判断中已观察、推断与未知部分的区别，以及处理不命中时的安全退出边界；
3. 仅凭一次相关现象声称因果机制，或把对象写成规则、任务、决定、操作手册或行动授权；
4. applicability 过度泛化、没有排除项，或外部协议与实现已变化却沿用旧验证；
5. 多个独立根因或不相容解决方式被捆绑；
6. 与当前规范或 active Pitfall 冲突，但没有完成获准的冲突处置；
7. 用关系、commit、测试成功或实现存在冒充经验普遍有效、规则已生效或行动已授权；
8. 准备 promote 或 discard 却没有针对准确对象与最终快照的明确 Human 授权；promote 夹带任何正文/关系修改；discard 删除或改写完整正文/关系、缺少具体处置，或 active 废弃未说明不再适用依据；
9. 准备写入 archived、archive_reason、tags、repeatability、severity、source_objects、source_sparks、related_*、空占位或其它未登记内容；
10. 高影响取舍没有实际授权，或获准写入后没有回读与范围匹配验证；
11. 仅凭 WC `execution_approval` 存在而推定授权包未逐项列明的 active 初态、promote/discard、其它事实对象创建或项目级全局锁，或者把独立 subagent 误写成 draft 成立条件或环境 spawn 能力证明；
12. 按数量、正文长度或时间自动删除、过期、promote 或 discard draft。

暂停范围与允许继续的行动按 00 §11 执行；对 Pitfall，只有失败、根因判断、解决、验证说明、复用价值与边界成立，冲突和 Schema 得到处置并完成写后回读后，才能恢复相应范围。
