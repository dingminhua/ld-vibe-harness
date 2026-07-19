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
  scope: "管辖项目中已经完成、可独立引用且具有跨行动稳定阅读价值的一轮研究结果"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `study` 事实类型的唯一定义来源；它不使 Study 读取、创建、校验、Helper、Code、tests、行动模板或 Web 能力自动成立。任何外部材料都必须按本文重新满足来源版本、观察时点、适用边界与验证闭包，不能批量直接成为 V4 active 对象。

## 1. 价值判断

Study 保存一轮已经完成、可独立引用且具有跨行动稳定阅读价值的研究结果，使后续 AI 能快速恢复研究问题、输入与方法边界、主要发现、结论限制、建议和后续分流，并据来源版本与观察时点判断能否继续引用，避免重复调研或把过时结论冒充当前事实。

Study 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V7 清晰沟通和 V8 持续积累。研究执行与进度由 WorkCase 和当次计划承担；Study 不承载搜索过程、任务编排或行动授权。新增成本包括查重、来源精确化、时效复核、Schema、迁移和消费；通过只准入已经完成的一轮研究、Markdown 单一正文、三状态、两个专属元数据字段、统一来源证据和禁止多套 related 字段，维护成本低于重复重建资料、误用旧结论和无法定位依据的损耗。普通文档已经能够自然承载且不需要稳定身份、状态、证据、时效边界和整体替代历史时，不创建 Study。

稳定研究报告具有真实需求，但 archived、空关系数组、独立 URL 池、user_intent、conclusion 或旧实例当前性不能仅凭旧 shape 获得稳定价值。V4 只吸收经全局查重的信息需要，不继承旧 shape 或内容效力。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型、统一字段、来源、证据、关系、状态、变更和验证的共同边界；
2. `source-of-truth-traceability`：规定 Git 可追踪事实源、当前 Working Tree、来源回指和稳定事实边界。

Study 是研究事实，不是正式规则、长期决定或当前外部事实证明。研究发现、结论和建议需要成为规则、决定、任务或经验时，必须由相应正式来源另行准入、授权和验证；被吸收不会自动使 Study 终态。

## 3. 职责边界

本文负责定义：

1. `study` 的类型语义、对象粒度、准入和排除边界；
2. Study 的唯一当前承载位置、完整 Schema、Markdown 正文骨架、状态和终态处置；
3. 研究问题、快速摘要、适用范围、限制、来源、证据、验证与时效复核要求；
4. Study 的替代关系、变更、更正、删除、验证、Human Gate 与 Stop Conditions。

本文不负责定义：

1. 正式规则、长期决定、执行目标、研究计划、实际失败经验或行动授权；
2. 外部资料抓取、搜索、缓存、全文镜像、引用格式美化或研究方法教程；
3. 其它事实类型的语义、状态和 Schema；
4. Helper API、CLI、Web 页面、迁移工具、自动时效判断或真伪评分；
5. 仅因 Study 存在而产生的事实当前性、建议采纳、规则吸收或风险接受结论。

AI 负责判断研究是否完成、来源是否充分、推断是否越界、限制与适用范围是否诚实、结论是否仍可安全引用以及是否值得对象化；Code 只可按当前来源检查固定结构、值闭集、引用 shape、时间、标题骨架和状态条件。

## 4. 适用范围

一个研究结果只有同时满足以下条件，才可以形成 Study：

1. 一轮研究已经完成，不是进行中的搜索、调查任务或链接收集；
2. 存在一个可独立引用的核心研究问题；子问题共享同一输入、方法、适用边界和结论单元；
3. 实际输入、研究方法、观察时点、适用范围、排除项和未覆盖范围清楚；
4. 关键发现与结论能够精确回到 evidence_refs，来源直接陈述、当次观察和 AI 推断可以区分；
5. 限制、冲突证据、失败访问、未验证范围和时效风险如实表达；
6. 报告具有跨行动复读或被其它稳定来源引用的现实价值；
7. 已召回相邻 Study、Spark、WorkCase、ADR、Pitfall、当前规则和普通文档，没有可无损更新或自然承载的位置；
8. 对象化减少的重复调研和误用风险高于维护、重验证与消费成本。

一个 Study 只承载一个能被独立引用、整体替代或退出的研究问题与结论单元。不同证据域、不同适用边界或能够独立更新和替代的主要结论必须拆分。同一问题、边界和主要结论下补充证据或刷新观察可以更新原对象；研究问题、方法、applicability 或主要结论实质变化时通常新建 Study 并替代旧对象。

以下内容不得形成 Study：临时搜索结果、裸链接清单、聊天摘要、未完成调查、运行日志或一次性笔记；研究任务、执行计划、todo、验收或进度；已经成立的长期决定；实际发生并解决的失败经验；正式规则；单纯迁移索引、吸收台账、派生搜索视图或没有独立研究结论的资料汇编。

未完成或仍需澄清的问题保持 Spark 或进入 WorkCase；已经作出的选择进入 ADR；已经发生、查明、解决并验证的失败机制进入 Pitfall。Study 回答“在什么输入、方法、版本和观察时点下发现了什么、限制是什么”，不回答“当前必须遵守什么”或“已经决定做什么”。

## 5. Study 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `study` | 已经完成、可独立引用且具有跨行动稳定阅读价值的一轮研究结果 | `study-fact-type::5. Study 类型定义` |

### 类型专属结构定义

本类型没有类型专属结构

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `study-fact-type::5. Study 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `study-fact-type::5. Study 类型定义` |
| `created-at` | required | `inherit` |
| `updated-at` | required | `study-fact-type::8. 变更、更正、删除与类型退出` |
| `status` | required | `study-fact-type::6. 对象语义与生命周期` |
| `source-refs` | required | `study-fact-type::7. 来源、证据、时效与替代关系` |
| `evidence-refs` | required | `study-fact-type::7. 来源、证据、时效与替代关系` |
| `relations` | conditional | `study-fact-type::7. 来源、证据、时效与替代关系` |
| `disposition-summary` | conditional | `study-fact-type::6. 对象语义与生命周期` |
| `closed-at` | conditional | `study-fact-type::6. 对象语义与生命周期` |
| `adr-applicability` | required | `study-fact-type::7. 来源、证据、时效与替代关系` |
| `workcase-validation-summary` | required | `study-fact-type::7. 来源、证据、时效与替代关系` |
| `study-research-question` | required | `inherit` |
| `study-abstract` | required | `inherit` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `study-research-question` | `research_question` | string | 本报告实际回答的一个可独立引用研究问题或边界一致的子问题闭集 | 不表示 Human 原话、WorkCase 执行目标、ADR 决定问题、搜索关键词或待办 | 必填非空；正文“研究问题”只可展开，不得改变本字段；问题实质变化通常形成新 Study |
| `study-abstract` | `abstract` | string | 不读完整正文即可理解研究问题、证据边界、主要发现和关键限制的报告摘要 | 不表示标题、进行中进展、完整结论、正式决定、规则或外部事实仍当前 | 必填非空；正文实质变化时同步更新；只作快速入口，不复制整段正文 |

### Schema、Markdown 正文与对象载体

Study 对象使用 UTF-8 Markdown，一文件一对象，当前权威位置固定为管辖项目仓库中的 `ldvh-base/studies/<object_id>.md`。`object_id` 必须匹配 `study-[0-9]{4,}`；文件名必须与 `object_id` 完全一致，分配后的身份不得因标题、路径、状态或内容改变。`title` 只简短识别研究主题，不复制 `research_question`、`abstract` 或结论。YAML frontmatter 只承载本节绑定字段，之后的 Markdown 正文承载详细报告。未知或不适用的条件字段必须省略，不使用 `null`、空字符串、空数组、占位时间、默认状态或默认关系。

正文必须按顺序各出现且只出现一次以下非空 H2：`研究问题`、`输入、方法与观察边界`、`关键发现`、`结论与限制`、`建议`、`后续分流`。正文可以使用 H3、表格和列表展开细节，但 frontmatter 的 research_question、abstract、applicability 和 validation_summary 是稳定机器入口；正文不得改变或弱化这些边界。研究方法、来源质量、冲突证据、未覆盖与时效限制在正文相应章节详细表达，不再建立第二个 limitations 字段。建议和后续分流可以明确没有可行动内容，但不得写占位语、虚构任务或暗示已经创建下游对象。

从外部报告形成 Study 时，来源 locator、正文对来源用途与限制的说明必须按 source_refs、evidence_refs 与正文骨架重新建立准确映射；只复制 URL、标题、摘要或其它旧字段而丢弃用途、观察边界和限制不成立。若一项稳定信息无法在现有引用成员和正文中无歧义承接，必须停止创建并按 05 重新进行字段准入。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、跨类型共享定义、类型专属字段定义和本节正文骨架组合。Study 不得出现 current summary、priority、evolution、WorkCase/ADR/Pitfall 专属字段、user_intent、conclusion、urls、input_refs、related_*、archive_reason、正文外第二报告、自由 metadata 或其它未登记 frontmatter。

## 6. 对象语义与生命周期

Study 只记录完成的一轮研究结果。搜索、阅读、实验或比较仍在进行时不得创建 active Study；研究工作保持在 WorkCase 或当次上下文，报告完成后再形成 Study。active 只表示报告在明示 applicability、来源版本、观察时点、validation_summary 和正文限制内仍可作为当前研究入口，不表示所有外部事实仍最新、建议已采纳、结论成为规则或决定已经成立。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 报告在明示版本、观察时点、适用与限制内仍可作为当前研究入口 | 只能作为新建初态；终态字段禁止；全部核心字段、正文和证据成立；不证明外部事实仍当前 |
| `superseded` | 一个后来成立的新 Study 对同一研究问题与适用范围形成整体替代 | disposition_summary、closed_at、evidence_refs 必填；旧对象必须成为一个在建边时为 active 的新 Study 的有效 supersedes 目标 |
| `retired` | 报告不再安全或没有当前引用价值，且没有新 Study 整体替代 | disposition_summary、closed_at、evidence_refs 必填；必须说明具体失效、冲突或退出依据 |

初始状态只能是 active。正常转换只有 `active → superseded` 和 `active → retired`；终态不直接重开。错字、来源定位修正、同问题同边界的证据补充或不改变主要结论的时效复核可以原地更正；研究问题、核心方法、applicability 或主要结论实质变化通常建立新 Study。被规范、ADR、WorkCase、Pitfall、Spark 或普通文档吸收不会自动使 Study 终态。

## 7. 来源、证据、时效与替代关系

source_refs 至少回指研究委托或问题来源及全部实际输入；evidence_refs 必须精确支持主要发现、结论、applicability、validation_summary 和正文限制。引用成员只承担种类、定位、版本和观察时间；来源为何被使用、支持哪项声明及其限制由正文承担，并通过 locator 与具体引用映射。正文重要事实与推断必须能够映射到具体 evidence_ref，不得只给文末裸链接池。下游事实对象需要引用 Study 时由下游对象把 Study 记入 source_refs；Study 不双写 related_*。

Study 的 source_refs 与 evidence_refs 只允许下列 kind 和最低机械条件：

| kind | locator profile | version | observed_at |
|---|---|---|---|
| `fact-object` | 当前管辖项目内匹配 `ldvh-base/(sparks\|workcases\|adrs\|pitfalls\|studies)/<object_id>.(yaml\|md)` 的 canonical 相对路径 | allowed；结论依赖特定提交时 required | required |
| `repository-path` | 当前管辖项目内的 stable repository-relative path | allowed；结论依赖特定提交、ref 或文件版本时 required | required |
| `git-revision` | 当前管辖项目内的 stable repository-relative path | required，使用可恢复的 commit 或 ref | required |
| `web-page` | 绝对 `http` 或 `https` URL | allowed；页面声明可恢复版本且结论依赖它时 required | required |
| `api-observation` | 绝对 `http` 或 `https` endpoint URL | required，使用被观察 API 或产品版本 | required |
| `runtime-observation` | 当前管辖项目内保存当次输入、环境和结果的 stable repository-relative evidence artifact | required，使用运行时、工具、协议或环境版本 | required |
| `human-provided-artifact` | 当前管辖项目内已经稳定保存的 repository-relative artifact；不能直接指向聊天附件缓存 | allowed；artifact 有版本身份且结论依赖它时 required | required |

`stable repository-relative path` 必须是规范化 POSIX 相对路径：至少一个非空 segment，不以 `/` 开头，不包含 `\`、空 segment、`.`、`..` 或 URI scheme，解析后仍位于当前管辖项目仓库内，并指向能够进入 Git 溯源的实际来源或证据。绝对本地路径、`/tmp`、`/var/folders`、剪贴板、会话附件缓存和其它临时 scheme 一律不成立。`fact-object` 还必须使路径中的类型目录、文件名、对象内 `fact_type_key` 和 `object_id` 一致。

上表的 `required` 和 kind 闭集由 Code 直接检查；`allowed` 表示 Code 不因缺少 version 单独拒绝，但 AI 判断结论依赖具体版本时仍必须把 version 收紧为必填。所有 observed_at 必须是带时区 RFC 3339 date-time，且不得晚于 Study 的 updated_at；同一数组中的 kind、locator、version、observed_at 完全相同的引用不得重复。上表没有授权 Code 根据正文关键词猜测来源种类或版本依赖。

全部 Study 引用都必须记录 observed_at；它表示该来源实际被读取、取得或确认的时间。对于 RFC、已发布论文或其它静态文档，observed_at 仍记录本次实际观察时间，不冒充文档发布时间。结论依赖软件、文档、仓库、package、协议、产品或其它具体版本时还必须按上表记录 version。updated_at 不是观察时间，created_at 不是研究发生时间，version 与 observed_at 也不证明来源正确。

Study 没有统一 TTL。只读取或定位 Study、把它作为历史研究过程的来源，或者严格在已记录版本、观察时点、applicability 与限制内引用其历史结论，不因该动作本身强制重新观察。只有当前消费需要把结论当作观察时点之后仍成立的当前依据，并且目标版本或环境超出或无法确认落在 applicability 内、结论所依赖的可变化事实需要当前性、观察后出现已知变化或冲突，或者高影响决定明确依赖其当前性时，才必须重新观察支持该受影响结论的必要来源；不得无差别重读全部引用。重验证失败只暂停受影响结论的当前消费；同问题同边界且主要结论不变时原地更新，主要结论变化时新建 Study 并替代，无替代且不安全时 retired。

Study relation_key 第一版只允许 supersedes：

| source condition | target condition | cardinality | reverse authority | missing, time and cycle boundary |
|---|---|---|---|---|
| source 与 target 同一管辖项目且均为 Study；source 建边时为 active；target 在同一变更由 active 转为 superseded；source 对 target 的研究问题和 applicability 形成整体替代 | target 必须是当前存在且建边前为 active 的 Study；部分结论替代、范围交叉或仅更新来源时不得建边 | source 可以替代一个或多个能够被整体承接的旧 Study；每个 target 在全部保留历史中最多一个直接 supersedes source，删除 source 或改状态不得重置该基数 | 只保存 source → target；反向索引由 Code 派生，不写回第二权威 | 目标缺失、跨项目、非 Study、自指、状态不符、多个直接 source 或任一保留边形成环时失败；必须满足 `target.created_at <= source.created_at <= target.closed_at` |

supersedes 边一旦有效形成，在 source 后续转为 superseded 或 retired 时仍永久保留并继续占用 target 的唯一直接替代源基数。不能整体承接旧报告时必须先拆分研究问题或保留旧 Study 并收紧 applicability，不得用关系制造虚假关闭。

### 主动召回与消费时机

Study 在当前问题需要已有研究依据、准备展开实质相同或相邻的研究、比较方案或作出依赖研究结论的决定，以及当前输入精确引用研究报告时产生召回机会。F2 Study 候选卡直接投影 `object_id`、`title`、`status`、`research_question`、`abstract`、`applicability`、`validation_summary` 和 `updated_at`，并只提示引用中是否存在 version/observed_at 边界，不在候选层解释结论当前性。只在主要发现、证据映射、限制或建议会影响当前判断时展开完整正文，不得因主题相似就向 AI 无差别注入整份报告。

`active` Study 可进入当前结论候选，但仍必须按本节时效规则核对版本、observed_at、applicability、已知变化和冲突；`superseded` 与 `retired` Study 只在精确引用、研究历史或来源追溯、检查替代链，或比较结论变化时展开。上下文压缩后，已在当次被引用且仍影响判断的 Study 必须重新回读 F3 中的研究问题、主要结论与限制，并恢复需要复核的版本、观察时点和来源范围；Study 被召回不证明外部事实仍当前、建议已采纳或结论取得规则与决定权威。

## 8. 变更、更正、删除与类型退出

任何创建或更新都必须先召回相邻对象和当前字段登记，确认 Human 当前指令已经授权，且适用于该行动的全部来源规则许可条件已经成立，随后写入唯一当前文件，回读 Working Tree，并验证 frontmatter、正文、状态、来源和关系。created_at 与 object_id 不因内容修正改变；正文、abstract、applicability、validation_summary、来源版本或观察时点实质变化时 updated_at 必须同步更新。

active、superseded 和 retired 文件均默认保留在当前载体中供研究历史、来源和关系回读；本文不建立 archived 状态或归档位置。删除只有在适用来源允许、全部引用和仍有价值的研究内容已处置且不会丢失替代历史时才成立，不能用删除代替终态。

Study 类型停止新增、合并、替代或取消时，必须按 05 处置唯一定义来源、全部对象、引用消费者、字段登记 tombstone 和仍适用内容；不能只删除本文、目录、Schema 或 Web 入口。

### Study 治理保障矩阵

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 完成与单一问题准入 | 只把完成且可独立引用的一轮研究形成 Study | 本文准入、来源回读、AI 审核 | 对象治理 | 创建或拆分 Study 时 |
| 字段唯一与全局查重 | 每项 frontmatter 信息先查统一登记，只使用登记字段和唯一准入结论 | 05、05.Att.01、Code checks、独立复核 | 字段治理 | 新增、提升或改变字段时 |
| 来源版本与观察时点 | 可变化来源保留 observed_at，版本相关结论保留 version，locator 可恢复 | source/evidence refs、来源回读、重验证 | 时效治理 | 创建、更新或消费可变化结论时 |
| 报告与规则分离 | 发现、结论和建议不自动成为规则、决定、任务或事实当前性 | 本文、相邻类型来源、Human Gate | 权威治理 | 引用、吸收或提出行动时 |
| 状态与替代闭包 | 终态字段、整体替代、时间、单一直接 source 和 DAG 同时成立 | 本文、对象集、Code checks、AI 审核 | 生命周期治理 | 状态或 supersedes 变化时 |

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Study 召回与消费 | 需要研究依据、展开相邻研究、比较方案、作出依赖研究结论的决定或压缩恢复已引用结论时 | F2 卡片只投影权威字段与引用边界提示；正文按需展开；`active` 与终态的默认作用分离；压缩后已引用结论的限制与时效边界已恢复；当前性未被状态冒充 | 当前研究问题、对象卡片与正文、版本、observed_at、来源、证据和已知变化 | 分层候选走查、按需正文回读、AI 适用与时效审核 | 当次研究问题、已展开对象和已复核结论 | 不引用受影响结论；补读来源、重新观察、收紧 applicability 或报告未检查范围 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、frontmatter 闭集、身份、字段类型、条件、时间和引用符合当前来源 | 当前文件、统一登记、本文与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Study 消费；报告字段和未验证范围 |
| Markdown 正文 | 创建或正文变化时 | 六个 H2 精确唯一、顺序固定、内容非空，且不改变 frontmatter 核心边界 | 本文与对象正文 | 实际 Markdown validator；未实现时结构回读 | 当次对象正文 | 不声明报告结构成立；修正重复、缺失或漂移 |
| 来源、证据与时效 | 创建、更新或消费可变化结论时 | kind 属于闭集；locator 符合 profile；version/observed_at 出现条件和 `observed_at <= updated_at` 成立；重要发现可映射到证据；重验证范围清楚 | 本文、03、对象引用与外部当前来源 | 来源矩阵检查、来源回读、版本核对、实际观察与证据审查 | 被核对的来源、版本、时点和结论 | 暂停受影响结论消费；补证、收紧 applicability、更新、替代或退出 |
| 状态与关系 | 状态或 supersedes 变化时 | 状态条件、终态字段、目标、时间、全生命周期单一直接替代源和 DAG 成立 | 本文、目标对象、完整保留关系集 | Schema/关系检查与 AI 语义审核 | 当次对象、目标和关系闭包 | 不写入状态或关系；修正目标、基数、时间或整体承接 |
| 规则与相邻对象边界 | 创建、引用、建议或吸收时 | Study 未冒充规则、决定、任务、经验或当前事实；下游另行准入 | 00、05、本文与相邻类型来源 | AI 来源对照；需要时 Human Gate | 当次结论、建议与吸收范围 | 停止越权声明；分流到正确来源并保留未吸收边界 |

Code 的共同机械边界按 05 §§10–11 执行；对 Study，只可额外检查本文明确给出的 frontmatter、引用 kind 与 locator/version/observed_at 矩阵、临时路径与重复引用、`observed_at <= updated_at`、正文标题和 supersedes 约束。研究价值、来源充分性与真实性、语义导致的 version 必填、推断、限制、建议、自然语言同义性和外部事实当前性仍由 AI 依据当前来源审核。

最低验证样例必须覆盖：七种 kind 各自的合法引用；未知 kind；每种 locator profile 错误；缺 required version 或 observed_at；带时区时间合法与缺时区；observed_at 晚于 updated_at；绝对本地路径、`/tmp`、`/var/folders`、`.`、`..`、反斜线、临时 scheme、会话附件缓存与重复引用；正文六个 H2 的缺失、重复、乱序和空内容；三个状态及条件字段；supersedes 的项目、类型、状态、全生命周期单一直接 source、时间、自指、缺失目标与 DAG。当前 Study parser/validator 已由 `read-fact-objects` 的只读实现从本文与统一登记派生；实现和测试只证明实际覆盖的机械范围，不得把读取通过冒充研究价值、来源真实性、证据充分性或当前可消费性已经成立。

## 10. Human Gate

Human 决定的复用按 00 §9 执行；Human 当前指令已经授权据实记录相应 Study，且适用于该行动的全部来源规则许可条件已经成立时，不因对象类型本身重复进入 Human Gate。Human 确认不能替代来源、Schema、时效复核或证据充分性，也不能把建议变成决定或规则。

以下情况必须进入 Human Gate：把研究建议写入高影响规则或决定；研究来源涉及需要 Human 授权的私密、许可或风险边界；语义查重仍不能判断应复用、提升或新增字段；报告整体替代会丢失仍适用结论；删除对象或退出类型；需要 Human 接受来源冲突、未验证范围或重大时效风险。

## 11. Stop Conditions

出现以下任一情况时，暂停受影响的创建、更新、引用、吸收、状态或关系变更：

1. 研究仍在进行，或研究问题、方法、输入边界、主要发现、限制和分流不能形成完成报告；
2. 来源或证据不可恢复、重要结论无法映射到证据、可变化来源缺少必要 version/observed_at，或当前性要求尚未重验证；
3. Study 正在替代规则、ADR、WorkCase、Pitfall、Spark、Human Gate 或当前外部事实判断；
4. 新字段没有完成全局查重、登记、唯一准入结论、独立复核和全部受影响类型同步；
5. frontmatter 与正文冲突、H2 缺失或重复、存在旧字段、null、空数组、临时路径或第二报告权威；
6. 终态依据不足、supersedes 不是整体替代，或目标、时间、单一直接 source、DAG 不成立；
7. 实际实现、迁移、Helper、Web 或测试声称了本文尚未实现或验证的能力。

暂停范围与允许继续的行动按 00 §10 执行；对 Study，只有完成性、来源、时效、字段、正文、状态、关系和权威边界成立，实际变更完成回读后，才能恢复相应范围。
