# Study / 研究报告

```yaml
ldvh_spec:
  spec_key: "study-fact-type"
  spec_id: "24"
  spec_kind: "spec"
  title: "Study / 研究报告"
  status: "active"
  canonical_path: "specs/24-Study-研究报告.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 Study 事实类型的对象边界、Schema、报告正文、生命周期、来源、时效与验证规则"
  scope: "管辖项目中已经完成、可独立引用且具有跨行动复读价值的外部研究、内部审计、技术评估或方案比较报告"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `study` 事实类型的唯一定义来源；它不使 Study 读取、创建、校验、Helper、Code、tests、行动模板或 Web 能力自动成立。外部研究、内部审计和技术评估都必须按本文重新满足输入来源、观察时点、适用边界与验证闭包，不能批量直接成为当前 active 对象。

## 1. 价值判断

Study 保存一轮已经完成、可独立引用且具有跨行动稳定阅读价值的**外部研究、内部审计、技术评估或方案比较报告**。报告必须明确其对象、问题、输入边界、观察时点、关键发现、限制和建议；它使后续 AI 能快速恢复当次判断的形成范围，并把研究或审计启发转化为项目下一步。

报告通过 `report_kind` 区分 `external_research`、`internal_audit`、`technical_assessment` 和 `comparison`。新建或实质更新的 Study 必须记录合法的报告类型和对应输入来源；这不表示内容正确、审批、验收或外部资料作者。

新建 Study 使用 `fact-object-controlled-creation`（31）；既有 Study 的事实更正、内容更新、状态变化或承接处置使用 `fact-object-lifecycle-change`（32）。模板不替代本文的报告类型准入、来源验证闭包或 Human Gate。

Study 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V7 清晰沟通和 V8 持续积累。审计、评估和外部调研的执行与进度由 WorkCase 和当次计划承担；Study 不承载搜索过程、任务编排、内部设计探索或行动授权。普通文档已经能够自然承载且不需要稳定身份、状态和后续复读价值时，不创建 Study。
稳定研究报告具有真实需求，但 archived、空关系数组、独立 URL 池、user_intent、conclusion 或旧实例当前性不能仅凭旧 shape 获得稳定价值。当前版本只吸收经全局查重的信息需要，不继承旧 shape 或内容效力。

面向 Human，当 Human 提出的已完成外部研究经判断需要跨行动保留时，Study 直接承接 HV3 的受控入档、当前 `active` 状态和 `retired` 处置节点。其来源、输入边界、发现和建议可以为 HV1 提供决定依据，`inspired-by` 与 `informs` 可以为 HV5 提供候选导航；但 Study 不形成当前决策提请，关系也不证明建议已采纳，更不单独串联长期意图、决定、工作与结果。研究报告只是 HV4 的积累内容输入；对象存在、被引用或被其它来源吸收均不证明实际复用和可观察效用，本文不声明 HV4 成立。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定管辖项目当前事实源、Working Tree、来源回指和稳定事实边界。

Study 是研究、审计、评估或比较报告事实，不是正式规则、长期决定、执行计划或当前事实证明。报告发现、结论和建议需要成为规则、决定、任务或经验时，必须由相应正式来源另行准入、授权和验证；被吸收不会自动使 Study 终态。

## 3. 职责边界

本文负责定义：

1. `study` 的类型语义、报告类型、对象粒度、准入和排除边界；
2. Study 的唯一当前承载位置、完整 Schema、Markdown 正文骨架、状态和终态处置；
3. 报告问题、摘要、来源、输入边界、关键发现、建议与后续分流要求；
4. Study 的变更、更正、删除、验证、Human Gate 与 Stop Conditions。

本文不负责定义：

1. 正式规则、长期决定、执行目标、研究计划、实际失败经验、行动授权或把报告结论直接写成规则；
2. 外部资料抓取、搜索、缓存、全文镜像、引用格式美化或研究方法教程；
3. 其它事实类型的语义、状态和 Schema；
4. Helper API、CLI、Web 页面、迁移工具、自动时效判断或真伪评分；
5. 仅因 Study 存在而产生的事实当前性、建议采纳、规则吸收或风险接受结论。

AI 负责判断研究是否完成、来源是否充分、推断是否越界、限制与适用范围是否诚实、结论是否仍可安全引用以及是否值得对象化；Code 只可按当前来源检查固定结构、值闭集、引用 shape、时间、标题骨架和状态条件。

## 4. 适用范围

一份研究、审计、评估或比较报告只有同时满足以下条件，才可以形成 Study：

1. 一轮报告已经完成，不是进行中的搜索、调查、执行或链接收集；
2. 存在一个可独立引用的对象与核心报告问题；外部研究的问题面向外部对象，内部审计或评估的问题面向明确的项目、代码、环境、事实源或方案；
3. 实际输入、方法、观察时点、适用边界、排除项和未覆盖范围清楚；内部输入使用 `input_refs` 表达，外部资料使用 `urls` 表达；
4. `report_kind=external_research` 时 `urls` 至少包含一条实际读取的外部 HTTP(S) 资料；内部报告至少包含一条可重新定位的 `input_refs`；每项来源的用途或限制在正文中如实表达；
5. 报告能够以可阅读的“观察—项目影响—适用边界—后续选择”单元形成关键发现、建议和后续分流，不以验证或关系充当报告结论的证明；
6. 报告具有跨行动复读或被其它稳定来源参考的现实价值；
7. 已召回相邻 Study、Spark、WorkCase、ADR、Pitfall、当前规则和普通文档，没有可无损更新或自然承载的位置；
8. 对象化减少的重复研究、审计或误用风险高于维护、重验证与消费成本；
9. 新建或报告内容实质更新必须带合法 `report_kind` 与对应输入来源；历史对象缺失这些字段时仍可按兼容读取边界消费，不得凭空补写。

一个 Study 只承载一个能被独立引用或退出的研究问题与发现单元。不同外部对象、不同输入边界或能够独立重开的主要研究问题必须拆分。同一问题和边界下补充资料或刷新观察可以更新原对象；研究问题、方法或主要发现实质变化时通常新建 Study，并把旧对象废弃而不是建立替代链。

以下内容不得形成 Study：临时搜索结果、裸链接清单、聊天摘要、未完成调查、运行日志或一次性笔记；研究任务、执行计划、todo、验收或进度；已经成立的长期决定；实际发生并解决的失败经验；正式规则；纯内部 WorkCase、编排或行动授权；单纯迁移索引、吸收台账、派生搜索视图或没有独立发现的资料汇编。

未完成或仍需澄清的问题保持 Spark 或进入 WorkCase；已经作出的选择进入 ADR；已经发生、查明、解决并验证的失败机制进入 Pitfall。Study 可以回答“对哪个外部或内部对象，在什么输入、方法、版本和观察时点下发现了什么、限制是什么”，但不回答“当前必须遵守什么”“LDVH 已经决定做什么”或“行动应如何获批执行”。

## 5. Study 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `study` | 已经完成、以明确外部或内部对象为主体、可独立引用且具有跨行动稳定阅读价值的一轮研究、审计、评估或比较报告 | `study-fact-type::5. Study 类型定义` |

### 类型专属结构定义

| structure_key | meaning | not_meaning | constraints |
|---|---|---|---|
| `study-input-ref` | 一项能够重新定位本报告实际输入的外部或内部来源回指 | 不表示来源真实、内容正确或结论已经被采纳 | 成员闭集为 `kind`、`locator`、`version`、`observed_at`；`kind` 与 `locator` 必填，其余按来源稳定性条件出现 |

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `study-fact-type::5. Study 类型定义` |
| `object-uid` | conditional | `study-fact-type::5. Study 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `study-fact-type::5. Study 类型定义` |
| `created-at` | required | `inherit` |
| `updated-at` | required | `study-fact-type::8. 变更、更正、删除与类型退出` |
| `change-log` | conditional | `study-fact-type::8. 变更、更正、删除与类型退出` |
| `status` | required | `study-fact-type::6. 对象语义与生命周期` |
| `study-report-kind` | conditional | `study-fact-type::5. Study 类型定义` |
| `urls` | conditional | `study-fact-type::7. 外部网址、研究边界、关系与时效` |
| `study-input-refs` | conditional | `study-fact-type::7. 外部网址、研究边界、关系与时效` |
| `relations` | conditional | `study-fact-type::7. 外部网址、研究边界、关系与时效` |
| `disposition-summary` | conditional | `study-fact-type::6. 对象语义与生命周期` |
| `study-research-question` | required | `inherit` |
| `study-abstract` | required | `inherit` |
| `study-research-intent` | conditional | `study-fact-type::5. Study 类型定义` |
| `study-recommendation-summary` | conditional | `study-fact-type::5. Study 类型定义` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `study-report-kind` | `report_kind` | string | 本报告的稳定语义类别 | 不表示报告质量、状态或建议已采纳 | 新建或报告实质更新时必填；闭集为 `external_research`、`internal_audit`、`technical_assessment`、`comparison` |
| `study-input-refs` | `input_refs` | array | 内部审计、技术评估或比较报告实际使用的可重新定位输入来源 | 不表示来源真实、内容正确或结论已经被采纳 | 内部报告至少一项；成员使用 `study-input-ref`；历史对象可缺失 |
| `study-input-ref-kind` | `kind` | string | 输入来源的实际种类 | 不建立跨来源权威顺序 | 必填非空；复用 04.Att.01 来源种类语义 |
| `study-input-ref-locator` | `locator` | string | 按当前判断所需精度重新定位输入来源的位置或引用 | 不表示来源已经正确或被采纳 | 必填非空；不得只写无法复核的模糊名称 |
| `study-input-ref-version` | `version` | string | 输入依赖的版本、commit 或 ref | 不表示该版本内容正确 | 条件出现；来源依赖版本时必填。对 specification、specification-attachment、fact-objects、git-history 等有 Git 锚点的来源，应写实际 commit SHA（如 `d4677530`），不写 `当前 working tree` 等无追溯价值的占位文本。对 helper-call-results、working-tree-statistics 等会话级来源，省略 version。|
| `study-input-ref-observed-at` | `observed_at` | string | 输入来源实际观察时点 | 不表示报告创建时点或来源当前仍有效 | 条件出现；来源会变化且结论依赖时点时必填 |
| `study-research-question` | `research_question` | string | 本报告实际回答的一个以外部或内部对象为主体、可独立引用的研究、审计、评估或比较问题 | 不表示 Human 原话、纯内部 WorkCase 执行目标、ADR 决定问题、搜索关键词或待办 | 必填非空；正文“研究问题”只可展开，不得改变本字段；问题实质变化通常形成新 Study |
| `study-abstract` | `abstract` | string | 不读完整正文即可理解研究问题、证据边界、主要发现和关键限制的报告摘要 | 不表示标题、进行中进展、完整结论、正式决定、规则或外部事实仍当前 | 必填非空；正文实质变化时同步更新；只作快速入口，不复制整段正文 |
| `study-research-intent` | `research_intent` | string | 当前项目为什么需要这轮外部研究、希望借此澄清或推动什么判断 | 不表示 Human 原话、创建对象指令、执行计划、既有结论、决定或授权 | active 时必填非空；从原始项目语境提炼为可独立阅读的动机与待判断方向；与 `research_question` 分工，前者说明项目为何研究，后者说明外部对象上的具体问题 |
| `study-recommendation-summary` | `recommendation_summary` | string | 本轮研究最值得项目继续判断、试行或交给 Human 取舍的建议摘要 | 不表示已决定规则、已创建行动、验证通过、事实当前性或完整后续分流 | active 时必填非空；与正文“建议”分工，前者提供首级阅读入口，后者展开建议、条件、边界与分流；建议实质变化时同步更新 |

### Schema、Markdown 正文与对象载体

Study 对象使用 UTF-8 Markdown，一文件一对象；新 UID-native 对象使用 `ldvh-base/studies/study-<uid26>.md`，legacy 对象继续从 `ldvh-base/studies/<object_id>.md` 双读。legacy `object_id` 必须匹配 `study-[0-9]{4,}`且与旧文件名一致；新建只写 UID 路径，不要求 candidate_object_id 或 counter。具有 `object_uid` 时其权威身份、legacy 缺失兼容和不可变边界统一按 05 §7.3–§7.4，新建 Study 必须由 Code 生成 UID。`title` 应以“报告对象 + 当前项目判断主题”简短识别报告，不复制 `research_question`、`abstract`、建议摘要或结论；它是当前文件名之外的可读命名入口。YAML frontmatter 只承载本节绑定字段，之后的 Markdown 正文承载详细报告。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

正文必须按顺序各出现且只出现一次以下非空 H2：`研究问题`、`输入与边界`、`关键发现`、`建议`、`后续分流`。这五段不是最小填空骨架；active Study 必须使用下表的可见阅读单元，使读者能区分外部资料的观察、对当前项目的启发、尚未成立的结论和下一步选择。frontmatter 的 research_question 和 abstract 是稳定机器入口，正文不得改变或弱化这些边界。

| 固定 H2 | 必须可见的阅读单元 | 不得退化为 |
|---|---|---|
| `研究问题` | 清楚区分当前项目为何需要这轮报告，与本对象实际回答的外部或内部问题；可用 H3、段落或表格组织 | 只重述标题、搜索关键词或 Human 原话 |
| `输入与边界` | 说明实际读取的外部资料或内部输入如何分工，以及观察时点、未覆盖、冲突或不适用范围；可用 H3、段落或表格组织 | 只复制 URL 列表，或用无法重新定位的模糊说明代替输入来源 |
| `关键发现` | 一个或多个可独立讨论的发现单元；每个单元据实区分外部观察和对项目可能带来的启发。只有存在实质误解、风险、冲突或不适用边界时，才说明其限制；active Study 至少有一个发现或建议明确提出由研究带来的具体项目方向、取舍或下一研究问题。每个发现单元必须说明“对后续项目工作的直接影响”：它应创建/更新某 WorkCase/ADR/Spark，还是应影响某个正在进行的判断。如果当前确实不需要创建任何对象，必须明确说明判断依据和后续监测条件，不得省略或用“待决定”占位 | 一段压缩结论、资料摘抄、把产品能力直接写成项目规则，或把每条发现机械写成“这不等于什么”的免责声明 |
| `建议` | 一个或多个具体建议或取舍，说明适用条件、风险或不成立边界。每个建议必须具体到可被 WorkCase 或 ADR 直接承接：至少说明目标对象类型、预期目标、验收条件和创建/更新判断。如果研究认为当前确实不需要创建任何对象，建议可以直接写“无需对象化”，但必须说明判断依据和后续监测条件，不得省略或用“后续再看”占位 | 为填满模板虚构每一类建议，或把建议伪装成已决定行动 |
| `后续分流` | 清楚说明每项建议/未决问题的后续承载方向，或为何无需对象化。每个分流项必须包含判断标准：什么信号出现时应该创建/更新哪个对象类型，以及什么条件下可以继续无需对象化。可用表格、列表或短段组织 | 只写“后续再看”、无条件地创建 Spark，或暗示下游对象已经建立 |

上述单元是研究报告的阅读和讨论契约，不是可审计论证包：`urls` 继续只保留资料线索与用途/限制，验证继续只提供方法，Code 不证明自然语言研究正确。研究方法、来源质量、冲突证据、未覆盖与时效限制在“输入与边界”或“关键发现”中据实表达；建议和后续分流可以明确没有可行动内容，但不得写占位语、虚构任务或暗示已经创建下游对象。发现是否真正产生了具体项目方向、取舍或下一研究问题，及限制是否实质相关，属于 AI/Human 的研究质量审核，不属于 Markdown validator 的判断。

### 阅读语义与逐层展开

下列读序定义的是同一份 Study 源内容的消费语义，不新增阅读投影字段、DTO、副本或第二报告，也不把旧版本的 `user_intent` 原话重新引入当前版本：

1. 摘要层依次使用实际的 `research_intent`（意图）、`abstract`（摘要）和 `recommendation_summary`（建议）。显示标签可以为“意图”“摘要”“建议”，但不得因此改名、拼接、推断或补写字段语义；
2. `research_question` 是完整报告中“研究问题”的稳定入口，同时可用于 F2 候选发现；它不属于与上述三个字段并列的摘要层，也不得代替正文的问题展开；
3. 完整阅读层只展开同一对象的唯一 Markdown 正文，保留原有 H2、H3、表格、链接和段落结构；摘要层不得复制、重组或部分改写为另一份完整报告；
4. Study 的正文载体为 Markdown。精确读取已经取得可消费正文时，消费者按该载体解释；正文未取得、无效或不可用时，消费者只能如实呈现读取状态、问题和未读取范围，不能根据对象 ID、路由 target、文件名或预期路径猜测、拼装或伪造正文。

Study 采用“意图—摘要—建议—正文”的阅读节奏，不额外定义字段、关系或审计式资料结构；外部资料仍按 `urls` 和正文“输入与边界”按需进入阅读。具体页面布局、入口控件、复制行为和 Web 传输投影由 08 与实现说明负责，不由本文定义。

Study 必须由已完成的外部研究、内部审计、技术评估或方案比较形成。外部来源在 `urls[].summary` 中说明用途或限制，内部来源在 `input_refs` 中提供可重新定位的 kind/locator，正文说明输入、边界和由此得到的发现；只复制 URL、标题、路径或旧结论而丢弃用途、边界和发现不成立。若一项稳定信息无法在现有来源成员和正文中无歧义承接，必须停止创建并按 05 重新进行字段准入。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义、类型专属字段定义和本节正文骨架组合。Study 不得出现 current summary、priority、evolution、WorkCase/ADR/Pitfall 专属字段、user_intent、conclusion、related_*、archive_reason、正文外第二报告、自由 metadata 或其它未登记 frontmatter；`input_refs` 仅按本节类型绑定使用。

## 6. 对象语义与生命周期

Study 只记录完成的一轮外部内容调研。搜索、阅读、实验或比较仍在进行时不得创建 active Study；调研工作保持在 WorkCase 或当次上下文，报告完成后再形成 Study。active 只表示报告在所述资料、输入边界和正文限制内仍可作为当前研究入口，不表示所有外部事实仍最新、建议已采纳、发现成为规则或决定已经成立。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 报告在明示版本、观察时点、适用与限制内仍可作为当前研究入口 | 只能作为新建初态；终态字段禁止；全部核心字段、正文和证据成立；不证明外部事实仍当前 |
| `retired` | 报告不再作为当前研究入口，包括已被重新研究、资料失效、范围不再相关或不再值得复读 | disposition_summary 必填；必须说明退出依据；终态更新以 `updated_at` 记录；不要求或建立替代关系 |

初始状态只能是 active。正常转换只有 `active → retired`；终态不直接重开。错字、来源定位修正、同问题同边界的资料补充或不改变主要发现的时效复核可以原地更正；研究问题、核心方法或主要发现实质变化时建立新的 Study。新研究可以在正文或后续分流中参考旧研究，但不以 `supersedes` 建立对象关系。被规范、ADR、WorkCase、Pitfall、Spark 或普通文档吸收不会自动使 Study 终态。

## 7. 外部网址、研究边界、关系与时效

`urls` 是全体事实对象共用的外部资料字段：每项使用 `{ ref, title, summary }`，`ref` 是绝对 HTTP(S) URL，`title` 是资料标题，`summary` 说明该资料对当前报告支持什么、未支持什么或具有什么限制。`report_kind=external_research` 时 Study 至少有一条 `urls`；内部报告可以省略 `urls`，但必须使用 `input_refs`。

`input_refs` 使用 `study-input-ref` 成员，回指代码、事实源、测试、环境、Git 或其它实际输入；其 `locator` 必须足以按当前判断所需精度重新定位，依赖版本或观察时点时提供 `version` 与 `observed_at`。项目内路径、代码、日志、会话与 Git revision 不得伪装成 `urls`，但可以在 `input_refs` 中按来源回指语义表达。

`version` 的取值应真实提供再定位锚点。对 specification、specification-attachment、fact-objects、git-history 等承载于受管辖项目 Git 历史或工作树中的来源，`version` 写实际 commit SHA（最简为当前 `HEAD` 的完整或短哈希）；对有 Git 锚点的来源不得写 `当前 working tree` 等无法重建当时内容的占位文本。对 helper-call-results、working-tree-statistics 等无稳定版本含义的会话级或快照级来源，省略 `version`，只保留 `observed_at`。`version` 与 `observed_at` 的组合使后续读者能以「基线 commit + dirty diff」恢复研究输入的主要范围；未提交变更的内容本身不因 version 记录而可重建，属正常可接受边界。

研究问题由 `research_question` 表达；外部资料和内部输入的用途、输入边界、关键发现、推断和限制由 `urls`、`input_refs`、正文与 `abstract` 据实说明。不得以 URL、来源回指、关系或验证动作本身代替报告结论。

### 7.1 关系类型与约束

Study 使用公共 `relations` 字段声明与项目内其他事实对象的语义关联。关系不是研究的必备组成部分；只有当研究确实由某个项目对象驱动、或研究建议应影响某个项目对象时，才应建立关系。允许的关系类型及其语义如下：

| `relation_key` | 方向 | 语义 | 允许的目标类型 | 约束 |
|---|---|---|---|---|
| `inspired-by` | Study → 目标 | 本研究受该 Spark、WorkCase 或 ADR 驱动，或以其提出的问题为研究起点 | `spark`、`workcase`、`adr` | 每个对象至多一条 `inspired-by` 指向同一来源类型；允许指向多个不同的来源对象 |
| `informs` | Study → 目标 | 本研究的关键发现或建议应影响目标 WorkCase、ADR 或 Spark 的判断或执行 | `workcase`、`adr`、`spark` | 不表示建议已被采纳或承接对象已创建；每条关系独立声明，不合并 |

禁止的类型：
- `supersedes`：Study 不替代其他事实对象
- `depends-on`：Study 不依赖其他对象的当前状态

关系只保留目标对象身份。目标名称只能由该稳定目标当前对象的 `title` 派生读取，不得复制、人工维护或把名称写入关系。建立关系不自动改变目标对象的状态，也不暗示建议已被采纳或承接对象已创建。

Study 没有统一 TTL；当前消费依赖易变资料时，AI 必须重新检查必要外部资料并更新自然语言结论或收紧适用范围。

### 主动召回与消费时机

Study 在当前问题需要外部研究、内部审计、技术评估或比较报告启发，或当前输入精确引用报告时产生召回机会。F2 Study 候选卡直接投影条件出现的 `object_uid`、以及 `object_id`、`title`、`status`、`report_kind`、`research_intent`、`research_question`、`abstract`、`recommendation_summary`、`relations` 和 `updated_at`，不在候选层解释报告结论当前性，也不内联输入来源。只在关键发现、限制或建议会影响当前判断时展开完整正文，不得因主题相似就向 AI 无差别注入整份报告。

`active` Study 可进入当前报告候选，但仍必须按本节时效规则核对版本、观察时点、已知变化和冲突；`retired` Study 只在精确引用、报告历史、来源追溯或比较报告变化时展开。上下文压缩后，已在当次被引用且仍影响判断的 Study 必须重新回读 F3 中的研究问题、关键发现、建议与限制，并恢复需要复核的版本、观察时点和来源范围；Study 被召回不证明外部事实仍当前、建议已采纳或发现取得规则与决定权威。

Study 的 `relations` 支持两种方向明确的候选导航：已知目标对象并需反查哪些 Study 指向它时，F2 使用 `fact_type_keys=[study]` 与 `relation_targets=[目标]`；已知一个 Study 并需沿其已声明的 `inspired-by` 或 `informs` 边取得直接目标时，使用 `relation_source_refs=[Study]`。两者都只形成候选及关系边结果，不自动改变 Study 状态、时效或结论当前性。Study 不另定义反向 relation key；两种导航均依赖 05 §11.5–11.6 的通用关系导航机制。

## 8. 变更、更正、删除与类型退出

任何创建或更新都必须先召回相邻对象和当前字段登记，确认 Human 当前指令已经授权，且适用于该行动的全部来源规则许可条件已经成立，随后写入当前 UID 文件名或读取兼容的 legacy 文件，回读 Working Tree，并验证 frontmatter、正文、状态和来源。created_at 与已有 `object_id` 不因内容修正改变；正文、report_kind、research_intent、abstract、recommendation_summary、来源用途、版本或观察时点实质变化时 updated_at 必须同步更新。

active 和 retired 文件均默认保留在当前载体中供研究历史和来源回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍有价值的研究内容已处置且不会丢失研究历史时才成立，不能用删除代替终态。

Study 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部对象、引用消费者、字段登记及仍适用内容；不能只删除本文、目录、Schema 或 Web 入口。

### Study 治理保障矩阵

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 报告对象、完成与单一问题准入 | 只把以明确外部或内部对象为主体、完成且可独立引用的一轮研究、审计、评估或比较报告形成 Study | 本文准入、来源回读、AI 审核 | 对象治理 | 创建或拆分 Study 时 |
| 字段唯一与全局查重 | 每项 frontmatter 信息先查统一登记，只使用登记字段和唯一准入结论 | 05、05.Att.01、Code checks、独立复核 | 字段治理 | 新增、提升或改变字段时 |
| 报告输入与边界 | 外部资料以可复核 URL、标题和支持范围/限制摘要保留；内部输入以 `input_refs` 回指；输入、观察和时效限制由正文表达 | `urls`、`input_refs`、正文与重读来源 | 资料治理 | 创建、更新或消费报告时 |
| 报告与规则分离 | 发现、结论和建议不自动成为规则、决定、任务或事实当前性 | 本文、相邻类型来源、Human Gate | 权威治理 | 引用、吸收或提出行动时 |
| 状态与退出边界 | 终态字段、退出理由和时间同时成立；重新研究不改写旧对象 | 本文、对象集、Code checks、AI 审核 | 生命周期治理 | 状态变化时 |

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Study 类型定义 | 新建或实质修改本文时 | 唯一声明、字段绑定、状态、外部资料、正文结构、来源、证据与关系完整且无第二权威 | 05、统一登记与本文 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 `study` 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| Study 召回与消费 | 需要外部研究启发、展开相邻研究、比较方案或压缩恢复已引用研究时 | F2 卡片只投影权威字段与引用边界提示；正文按需展开；`active` 与终态的默认作用分离；压缩后已引用研究的限制与时效边界已恢复；当前性未被状态冒充 | 当前研究问题、对象卡片与正文、版本、观察时点、来源和已知变化 | 分层候选走查、按需正文回读、AI 适用与时效审核 | 当次研究问题、已展开对象和已复核发现 | 不引用受影响发现；补读来源、重新观察或报告未检查范围 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、frontmatter 闭集、身份、字段类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Study 消费；报告字段和未验证范围 |
| Markdown 正文 | 创建或正文变化时 | 五个 H2 精确唯一、顺序固定、内容非空，且不改变 frontmatter 核心边界；研究问题、输入与边界、关键发现、建议和后续分流的阅读责任均有实际内容承接 | 本文与对象正文 | 实际 Markdown validator；AI 回读阅读单元；未实现时结构回读 | 当次对象正文与其可读结构 | 不声明报告结构成立；修正重复、缺失、压缩摘要式写法或漂移 |
| Study 阅读语义 | 新增或修改 Study 的详情、预览或正文入口时 | 摘要层只按 `research_intent`、`abstract`、`recommendation_summary` 的顺序使用实际字段；研究问题留在完整报告；完整正文来自精确读取的同一 Markdown 载体，并以其原有结构呈现，不与摘要层重复改写 | 本文、05 的读取结果、08 与页面/预览 DOM | 来源字段与页面/预览的 contract tests、代表性实际页面回读 | 当次 Study 消费面、字段、正文结构和视口 | 停止把不明、无效或未读取载体作为正文呈现；修正投影或渲染，保留未验证范围 |
| 报告输入、类型与时效 | 创建、更新或消费可变化报告时 | `report_kind` 属于闭集；外部研究至少一条 HTTP(S) URL，内部报告至少一条合法 `input_refs`；正文表达输入、观察、发现和未覆盖范围；`relations` 只使用 `inspired-by` 和 `informs` 且目标身份可解析 | 本文、03、04.Att.01、05、对象正文、外部 URL 与内部输入 | report kind、input_refs、URL shape、关系 key 与目标身份检查、正文与来源回读、AI 观察审查 | 被核对的报告类型、输入、发现、关系和时效边界 | 暂停受影响报告消费；补充来源或说明、更新或退出 |
| 状态 | 状态变化时 | 状态条件、终态字段、退出理由和时间成立 | 本文、当前对象 | Schema 检查与 AI 语义审核 | 当次对象 | 不写入状态；修正退出理由或时间 |
| 规则与相邻对象边界 | 创建、引用、建议或吸收时 | Study 未冒充规则、决定、任务、经验或当前事实；下游另行准入 | 00、05、本文与相邻类型来源 | AI 来源对照；需要时 Human Gate | 当次结论、建议与吸收范围 | 停止越权声明；分流到正确来源并保留未吸收边界 |

Code 的共同机械边界按 05 §§10–11 执行；对 Study，只可额外检查本文明确给出的 frontmatter、`report_kind`、`urls` 与 `input_refs` 的 shape、标题、摘要与去重、正文 H2 和状态约束。报告价值、资料充分性与真实性、观察时效、推断、限制、建议、自然语言同义性、阅读单元的实质内容和外部或内部对象当前性仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：有效外部 URL；内部输入回指；缺 URL、输入、标题或摘要；缺研究意图或建议摘要；本机路径仅作为 input ref、非 HTTP(S) URL 与重复 URL；非法 report kind；正文五个 H2 的缺失、重复、乱序和空内容；两个状态及终态字段。当前 Study parser/validator 已由 `read-fact-objects` 的只读实现从本文与统一登记派生；实现和测试只证明实际覆盖的机械范围，不得把读取通过冒充报告价值、来源真实性、资料充分性或当前可消费性已经成立。

## 10. Human Gate

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权据实记录相应 Study，且适用于该行动的全部来源规则许可条件已经成立时，不因对象类型本身重复进入 Human Gate。Human 确认不能替代来源、Schema、时效复核或资料充分性，也不能把建议变成决定或规则。

以下情况必须进入 Human Gate：把研究建议写入高影响规则或决定；研究来源涉及需要 Human 授权的私密、许可或风险边界；语义查重仍不能判断应复用、提升或新增字段；删除对象或退出类型；需要 Human 接受来源冲突、未覆盖范围或重大时效风险。

## 11. Stop Conditions

出现以下任一情况时，暂停受影响的创建、更新、引用、吸收、状态或关系变更：

1. 研究、审计、评估或比较仍在进行，报告问题未能识别明确对象，或方法、输入边界、主要发现、限制和分流不能形成完成报告；
2. 外部研究缺少可复核的 URL、标题或支持范围/限制摘要，内部报告缺少可重新定位的 `input_refs`，或关键发现、输入边界或限制无法在对象自身说明与来源之间如实表达；
3. Study 正在替代规则、ADR、WorkCase、Pitfall、Spark、Human Gate 或当前外部事实判断；
4. 新字段或报告类型没有完成全局查重、登记、唯一准入结论、独立复核和全部受影响类型同步；
5. frontmatter 与正文冲突、H2 缺失、重复、乱序或空内容、关键发现退化为压缩摘要、存在旧字段、null、空数组、临时路径或第二报告权威；
6. 终态依据不足，或退出理由、时间与当前对象内容不一致；
7. 实际实现、迁移、Helper、Web 或测试声称了本文尚未实现或验证的能力。

暂停范围与允许继续的行动按 00 §11 执行；对 Study，只有完成性、来源、时效、字段、正文、状态和权威边界成立，实际变更完成回读后，才能恢复相应范围。
