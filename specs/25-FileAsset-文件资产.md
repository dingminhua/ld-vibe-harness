# FileAsset / 文件资产

```yaml
ldvh_spec:
  spec_key: "file-asset-fact-type"
  spec_id: "25"
  spec_kind: "spec"
  title: "FileAsset / 文件资产"
  status: "active"
  canonical_path: "specs/25-FileAsset-文件资产.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 FileAsset 事实类型的原生文件载体、稳定身份、内容完整性、纳入签名、引用、生命周期与验证规则"
  scope: "管辖项目中需要跨行动、会话、执行者或阶段持续保留，并需要集中发现、稳定引用或受控生命周期的单一原生文件资产"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `file-asset` 事实类型的唯一定义来源；它与 03、05、05.Att.01、05.Att.02、20、21、31、32 和术语表的同批变更共同使类型语义、派生 Schema、正式读取、候选发现、完整性检查及 WorkCase `has-file-asset` 消费边界进入当前规则源。本文不自动创建任何 FileAsset 实例，也不使目录创建、manifest 更新、归档写入、物理删除、Git Index 多成员 after-image 校验、Web 下载或安全预览能力成立；这些未实现能力必须如实保持不可用。现有 Git Gate 对 staged FileAsset 路径只能失败关闭并报告不可验证，不能把阻断误写为已完成多成员完整性保护。

> 准入结论：Human 于 2026-07-31 明确 FileAsset 记录的是“一份确定内容以稳定身份客观存在”，不是证据或内容正确性声明。05 §7.2.1 也明确事实对象不是用来证明自身正确的材料包。A/B 隔离读取产生相同领域结论是同一 payload 被正确消费的预期结果，不能作为拒绝 FileAsset 的依据；相反，A 为满足同一需求已经复制身份、状态、签名、引用、发现和生命周期，说明另建平行资产对象体系会混淆责任。经两轮独立复核，本类型以第一阶段只读 activation 边界完成准入；未实现写入和呈现能力不由类型声明推定成立。

## 1. 价值判断

FileAsset 保存一个已经选定、需要长期留在管辖项目事实源中的原生文件。它使后续 Human 与 AI 能用稳定对象身份重新发现和引用同一份 canonical bytes，并能核对文件是否仍存在、字节是否与登记内容一致，以及本次把最终 bytes 直接交给受控摄取边界的是 Human 还是哪个 AI agent。

FileAsset 的稳定事实语义只覆盖：一组确定的 canonical bytes 以该对象身份存在，具有登记的完整性元数据、本次纳入签名和生命周期状态。它不把 payload 中的陈述变成事实结论，也不声明内容真实、正确、当前适用或具有证明力；这些判断始终由消费对象依据自身来源和语境承担。`active` 只表示对象在完整性检查通过后进入默认 FileAsset 候选，不表示内容当前有效。

当前根级 `docs/` 可以承载临时说明、调查、外部提供材料和草稿，但普通路径与文件名不提供事实对象身份、内容完整性、默认发现边界、纳入签名或受控生命周期。所谓“受保护普通资产目录”若同时提供稳定 asset ID、sidecar manifest、hash、纳入签名、状态、引用、反向导航、发现和删除检查，就已经形成第二套结构化资产对象模型，需要平行的规则、ID 域、Helper、Git Gate、资源和安全合同。它并未消除对象化成本，只把同一责任移出事实模型并增加 AI 在两套身份、引用、发现和生命周期之间选择的负担。对于 Human 已明确需要独立身份、跨行动发现和后续引用的文件，统一纳入事实对象体系比建立平行资产体系更不混淆责任。

对 AI 执行者，FileAsset 主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V5 据实判断、V6 工作接续、V7 清晰沟通和 V8 持续积累；只有实际 Helper、受控写入和 Git Gate 使 AI 能复用稳定行动结构并取得确定性反馈后，才可以在相应范围声明 V4 稳定推进。对象、Schema 或候选操作存在本身不证明这些价值已经实现。

对 Human，FileAsset 最直接服务 HV3 入档闭环节点可验：Human 明确要求跨行动保留的文件能够离开临时 `docs/`，进入来源允许、可回读完整性和状态的稳定承载。文件作为决策材料并明确用途、边界和未验证范围时，可以支持 HV1 决策提请清晰可决，但对象存在不自动使决策问题或选项清楚。FileAsset 不保存执行授权基线，因而不单独证明 HV2；只有实际复用、可观察效用和依据能够对应时才可声明 HV4；只有文件与长期意图、决定、重要工作和结果的真实关系已由其它正确来源明确记录并可读时才可支持 HV5，不能用文件数量或自然语言相似性拼出演进脉络。

新增成本包括独立类型发现、目录 carrier、字段和结构登记、多文件原子写入、payload 资源控制、跨类型关系、迁移、Git Gate、Web 安全消费及长期 Schema 维护。当前 Human 目标、两个真实文件样本、跨 fresh reader 回读和 A/B 结构对照支持准入时的 V1、V2、V3、V5、V6、V7 与 HV3 净价值判断：统一对象身份使文件可定位和关联，内容与证明力边界可识别，bytes 与签名可据实核对，不同会话和执行者能够接续，Human 要求保留的内容不再只停留在临时材料。V4、V8、HV1、HV4 与 HV5 只能在相应实现或真实复用范围成立后声明，不能由本类型声明提前扩大。两组价值必须按各自实际服务对象分别成立，不能互相替代。

FileAsset 的 payload、签名、多文件事务、失败场景、生命周期与消费时机形成不同于 05 共同事实边界和 20–24 语义对象的独立规范责任；把全部类型专属规则塞入 05、授权附件或某一个消费类型都会混淆职责。A/B 对照还表明，把这些规则移到独立资产库不会消除责任，只会形成第二套对象治理。本文据此通过 01 §13 的独立责任判断，并经独立复核作为普通规范进入当前规则源。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定事实类型的准入、字段与结构全局查重、统一登记、对象身份、canonical 载体、来源、证据、关系、状态、变更、验证和类型退出共同边界；
2. `source-of-truth-traceability`：规定管辖项目 Working Tree、当前事实源、来源回指、证据范围和稳定事实形成边界。

本文不改变 `specification-model-foundation` 对“授权附件（Authorized Attachment）”的定义。规范授权附件继续只表示由父规范授权的结构化规则文件；FileAsset 只表示项目事实源中的原生文件资产。两者不得共用类型名称、机器键、对象身份或 canonical 位置。

FileAsset 只稳定记录“这些 canonical bytes 以这个对象身份被保存，并由 manifest 声明了本次纳入签名与完整性元数据”。该事实边界不包含文件内容真实、正确、安全、具有证明力、已经批准、已经验收、构成规则、构成决定或足以支持消费方结论，也不把签名者解释为文件的历史作者或原始生成者。消费方必须依据自身来源规则、文件实际内容、当前目标和必要验证另行判断。

## 3. 职责边界

本文负责定义：

1. `file-asset` 的类型语义、准入、对象粒度、稳定身份和排除边界；
2. FileAsset manifest 与 payload 组成的唯一目录 carrier、成员闭集、内容完整性和不可变边界；
3. 摄取文件名、媒体类型、字节数、内容 SHA-256 与 Human / AI agent 二分纳入签名；
4. FileAsset 的状态、发现、读取、引用、归档、物理删除和类型退出边界；
5. FileAsset 的验证、Human Gate、Stop Conditions 及当前 activation 能力边界。

本文不负责定义：

1. 文件内容所属领域的真实性、证明力、审计方法、研究结论、决定、任务、经验或规则；
2. 任意 `docs/` 文件、构建产物、缓存、下载文件或工具输出自动成为 FileAsset；
3. 其它事实类型的字段、状态或关系；消费类型是否允许 `has-file-asset` 及其基数和缺失目标规则，必须由相应消费类型的唯一定义来源显式定义；
4. 文件编辑器、外部对象存储、全文索引、病毒扫描、内容净化、媒体解码或安全渲染；
5. Helper API、CLI 参数、Git Gate 事件、Web 下载或预览协议及其实现细节；
6. 密码学签名、Human 身份认证、审批 receipt、作者身份或触发者身份。

AI 负责判断文件是否具有独立持续消费价值、本次纳入签名应属于 Human 还是当前可观察 AI agent、是否应复用现有对象、内容和来源边界能否安全消费，以及归档是否符合 Human 意图。Code 只可检查来源已经定义的路径、普通文件、成员闭集、字段 shape、字节数、哈希、状态、关系、CAS、原子写入和已实现资源边界，不得裁决内容价值、签名陈述真实性、证明力或授权。

## 4. 适用范围

一份原生文件只有同时满足以下条件，才可以形成 FileAsset：

1. 最终文件 bytes 已经确定，不是尚在编辑、下载、生成或拼接中的中间结果；
2. 需要在管辖项目中跨行动、会话、执行者或阶段持续保留，而不是只服务当次展示、推理、缓存或命令运行；
3. 文件自身具有独立消费价值，后续需要重新读取、核对、引用、下载或保留其原始格式，且不能由现有事实对象的自然语言字段或普通稳定文档无损替代；
4. 稳定 ID、集中发现、内容完整性、纳入签名、跨对象引用或生命周期管理中至少一项是现实需要，并且不能通过建立第二套平行资产身份、引用、发现和生命周期体系来假装由“普通目录”自然承接；
5. 一个对象只需要承载一个原生 payload；多个独立文件分别判断和创建，不为绕过这一粒度由系统主动打包；
6. 本次把最终 bytes 直接交给受控摄取边界的责任主体，能无歧义归入“Human 直接提供”或“一个当前可观察 AI agent 代表自身提交”之一；
7. 文件进入 Git Working Tree 及后续消费不违反敏感信息、许可、安全、体积或管辖边界；
8. 已检查现有 FileAsset 候选、普通稳定文件和相邻事实对象，没有可无损复用或更小承载位置。

正例包括：Human 提供并要求后续 WorkCase 或 ADR 稳定引用的 PDF 审计报告；Human 要求 AI agent 生成并需要保留实际文件的 Markdown 审计报告；需要跨会话复核的截图、导出 JSON、日志、诊断输出或设计 mockup；Human 或 AI 原本提供且自身就是单一压缩包的文件。

如果 Markdown 报告、Study、ADR 或其它普通稳定内容本身承担项目当前语义权威，继续由其正确来源承载；只有某一时点的精确不可变 bytes 或原始格式具有独立消费价值时，才额外形成 FileAsset。可编辑语义来源与 FileAsset 快照同时存在时，前者仍是当前语义权威，后者只是明确时点和用途的来源材料；消费对象必须说明实际使用的是快照 bytes 还是当前语义来源，不得让两份载体同时声称当前结论权威。

反例包括：临时搜索结果、缓存、可无损再生成且无保留必要的构建产物、仍在变化的工作文件、只含可由现有字段无损表达的短观察、单纯 HTTP(S) 地址、为满足模板保存的命令流水、没有独立消费价值的普通文档，以及只因文件重要、体积大或已有扩展名而提出的对象化请求。

现有 `docs/` 文件不得批量自动迁移。每个候选必须逐项确认消费价值、最终 bytes、签名分支、敏感与许可边界、现有引用和 canonical 迁移结果；FileAsset 形成并完成引用核对前，原文件不得由迁移流程自动删除。

## 5. FileAsset 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `file-asset` | 被纳入项目事实源集中管理、具有稳定身份、canonical bytes、完整性元数据、纳入签名和受控生命周期的单一原生文件资产 | `file-asset-fact-type::5. FileAsset 类型定义` |

### 类型准入审计

| `fact-model-foundation` §6.1 条件 | 准入结论 | 当前边界 |
|---|---|---|
| 跨行动持续保留 | 通过 | Human 明确指出散落在 `docs/` 的关键文件可能被随手删除；两个审计文件提供了不同来源分支的实际样本 |
| 对象化、状态化或证据化需要 | 通过 | 需求明确包含稳定身份、独立发现、完整性、签名、引用和生命周期；对象化成立，不依赖 payload 内容具有证明力 |
| 稳定语义和对象边界 | 通过 | 一对象一原生 payload；manifest 与 payload 共同成立；payload bytes 不可原地改变 |
| 其它承载位置不能自然承担 | 通过 | `docs/` 只适合临时材料；现有事实类型不能承载任意独立文件内容；A 为满足同一需求已经复制对象身份、状态、签名、引用、发现和生命周期，形成平行资产事实体系而混淆责任 |
| 唯一当前定义来源 | 通过 | 本文为 `active`，正式声明精确回指本 H2，且同批共同来源、登记、实现与测试一致 |
| V1–V8 与 HV1–HV5 净价值 | 通过 | Human 目标和试点支持 V1、V2、V3、V5、V6、V7 与 HV3；统一事实模型避免第二套身份/引用/发现负担。V4、V8、HV1、HV4、HV5 只在后续实际机制与复用范围声明 |
| 术语和机器治理 | 通过 | `FileAsset / 文件资产` 已与“授权附件”消歧；字段登记、机械目录和首个消费类型关系已同批生效 |

因此，本文声明 `file-asset` **完成准入**并进入当前事实类型集合。该结论只使当前来源明确列出的规则与已实现只读能力成立，不扩大未实现的创建、更新、Git Gate 或 Web 能力。

### 术语准入审计

不使用候选名称时，本概念表达的是：一个被复制进管辖项目事实源、以稳定对象身份管理的单一原生文件，其 canonical bytes、完整性元数据、本次纳入签名和生命周期可以被后续工作重新发现和引用。

| 候选名称 | 判断 |
|---|---|
| `Attachment / 附件` | 拒绝；与当前“授权附件（Authorized Attachment）”重名并可能混淆规范文件与事实对象 |
| `ProjectAttachment / 项目附件` | 拒绝；仍以“附件”暗示从属 UI 动作，不能清楚表达独立事实身份 |
| `ManagedFile / 受管文件` | 拒绝；容易与所有受 Git 或项目规则管理的普通文件混淆 |
| `Artifact / 制品` | 拒绝；常被理解为构建或交付产物，不能覆盖 Human 提供的原生材料 |
| `FileAsset / 文件资产` | 当前采用；直接表达独立文件及其持续复用价值，并避开规范附件的正式术语 |

`FileAsset` 的正例与反例由 §4 给出；相邻概念包括授权附件、普通项目文件、外部 URL、Study 报告语义和各类事实对象正文。面向 Human 的界面可以使用“添加附件”描述动作，但实际对象类型、稳定引用、机器键和规范名称只能使用 FileAsset，不得让界面文案反向建立第二类型名称。

### file-asset 结构准入记录

| information_need | compared_structure_keys | decision | resulting_structure_key | rationale |
|---|---|---|---|---|
| 记录本次把最终 payload bytes 交给摄取边界的是 Human 还是一个可观察 AI agent，并在 AI 分支保留 agent 与宿主环境 | `fact-object,relation,relation-target,spark-evolution-entry,url-ref,workcase-authorized-action,workcase-closure-proposal,workcase-execution-authorization,workcase-human-approval,workcase-item,workcase-proposed-route-target,workcase-residual-decision,workcase-residual-responsibility,workcase-review,workcase-spark-suggestion,workcase-success-criterion,workcase-success-result` | new | `file-asset-signature` | 现有结构没有回答纳入责任主体；该结构只承载 Human/AI 二分与 AI 自报身份，不承担审批、来源证据、作者或密码学签名，成员闭集、出现条件和不可变边界均不同 |

### 类型专属结构定义

| structure_key | meaning | not_meaning | constraints |
|---|---|---|---|
| `file-asset-signature` | 记录本次把最终 canonical payload bytes 直接交给受控摄取边界的是 Human，还是哪个 AI agent 代表自身提交 | 不表示密码学签名、历史作者、原始生成者、最初触发者、审批者、授权、验收、证明力或签名陈述真实性已经由 Code 证明 | 成员闭集为 `signer_type`、`agent_id`、`host_environment`；Human 分支只含 `signer_type=human`；AI 分支必须同时含三个成员且 `signer_type=ai-agent` |

### 字段与结构准入审计

已检索 `fact-object-field-registry` 的全部当前结构和字段，并对当前登记中最接近的语义作如下判断：

| 信息需求 | 最近现有位置 | 结论 |
|---|---|---|
| 摄取文件名 | 公共 `title`、`url-ref.title` | 区分并新增；`title` 标识对象，URL title 标识外部资料，二者都不能保存 Human 提供或 AI agent 提交 payload 时使用的实际文件名 |
| 媒体类型 | 无当前或 retired 事实字段 | 新增；它声明 payload 的预期解释类型，不证明真实格式或安全性 |
| payload 字节数 | Working Tree 测试证据的 `size_bytes` 不是事实对象登记字段 | 新增；用于当前 payload 完整性和资源消费，不把测试证据 DTO 提升为事实字段 |
| payload SHA-256 | WorkCase `content_fingerprint`、`baseline_fingerprint` 和测试证据 `sha256` | 区分并新增；这些值分别指向事实载体、授权基线或测试输入，不表示 FileAsset payload bytes |
| 纳入签名 | 无当前或 retired 事实字段或结构 | 新增结构；只记录本次把最终 bytes 直接提交给受控摄取边界的 Human / AI agent 二分责任主体 |
| 终态处置 | 公共 `disposition-summary` | 复用；激活变更包应把 `file-asset` 加入其适用类型，并在 archived 时绑定为必填 |
| 外部网址 | 公共 `urls` | 禁止；URL 是重新访问外部资料的入口，不是已捕获的 canonical payload |
| 事实关系 | 公共 `relations` | FileAsset 自身初版禁止；消费方按各自类型来源定义 `has-file-asset`，反向引用只由 Code 派生 |

上述字段和结构已经在 `fact-object-field-registry` 中完成唯一登记，并由 `fact-object-mechanical-validation-catalog` 登记当前机械规则与未实现边界。Schema 只能由这些当前来源单向派生；任何实现不得另设 provisional 字段或结构再反向追认。

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `file-asset-fact-type::5. FileAsset 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `file-asset-fact-type::5. FileAsset 类型定义` |
| `created-at` | required | `file-asset-fact-type::5. FileAsset 类型定义` |
| `updated-at` | required | `file-asset-fact-type::8. 变更、更正、归档、删除与类型退出` |
| `status` | required | `file-asset-fact-type::6. 对象语义与生命周期` |
| `urls` | forbidden | `file-asset-fact-type::7. 来源、完整性、引用与消费` |
| `relations` | forbidden | `file-asset-fact-type::7. 来源、完整性、引用与消费` |
| `disposition-summary` | conditional | `file-asset-fact-type::6. 对象语义与生命周期` |
| `file-asset-filename` | required | `inherit` |
| `file-asset-media-type` | required | `inherit` |
| `file-asset-size-bytes` | required | `inherit` |
| `file-asset-content-sha256` | required | `inherit` |
| `file-asset-signature` | required | `inherit` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `file-asset-filename` | `filename` | string | Human 直接提供或 AI agent 代表自身提交 payload 时实际使用的可读文件名 | 不表示 canonical 路径、对象身份、当前标题、文件系统来源位置、历史原名或原作者命名 | 必填非空；Human 分支保留其提供文件的 basename；AI 分支使用实际生成、捕获、导出或提交文件的 basename，内存 bytes 必须先以明确文件名物化后再摄取；不含 `/`、反斜杠或 NUL，且完整值不得为 `.` 或 `..`；创建后不可原地改变 |
| `file-asset-media-type` | `media_type` | string | payload 被声明和预期解释为何种 IANA media type | 不表示 Code 已证明真实格式、内容无恶意、可执行或可安全渲染 | 必填非空；使用规范化 `type/subtype` 小写 token，不带参数；创建后不可原地改变；无法安全确定更具体类型时据实使用 `application/octet-stream`，不得根据扩展名冒充已证明格式 |
| `file-asset-size-bytes` | `size_bytes` | integer | canonical payload 的精确原始字节长度 | 不表示已满足某个未经来源定义的体积上限、字符数或解压后大小 | 必填且不小于 0；必须等于安全读取的完整 payload bytes 长度；创建后不可原地改变 |
| `file-asset-content-sha256` | `content_sha256` | string | canonical payload 完整原始 bytes 的稳定内容指纹 | 不表示来源真实、内容正确、密码学签名、无碰撞绝对保证或 manifest 自身指纹 | 必填；匹配 `[0-9a-f]{64}`；对完整 payload 原始 bytes 计算 SHA-256；创建后不可原地改变 |
| `file-asset-signature` | `signature` | object | 本次把最终 canonical payload bytes 直接交给受控摄取边界的 Human / AI agent 二分责任签名 | 不表示密码学签名、个人身份、历史作者、原始生成者、最初触发者、授权者、审批者、验收者或内容证明力 | 必填；值使用 `file-asset-signature`；创建后不可原地改变 |
| `file-asset-signature-signer-type` | `signer_type` | string | 本次纳入由 Human 直接提供 bytes，还是由 AI agent 代表自身提交 bytes | 不表示个人身份、历史形成方式、agent 能力、审批或签名陈述真实性已被机械证明 | 必填；闭集 `human`、`ai-agent` |
| `file-asset-signature-agent-id` | `agent_id` | string | AI 分支中对本次提交承担签名责任的可观察 AI agent 自报标签 | 不表示全局稳定 agent 身份、Human 指令者、历史作者、原始生成工具、模型能力或账号身份 | `signer_type=ai-agent` 时必填非空；Human 分支禁止；必须由该 agent 据实写自身当次可观察标签，不能代签不可观察 agent |
| `file-asset-signature-host-environment` | `host_environment` | string | AI 分支中该 agent 提交最终 bytes 时所在的可观察宿主环境 | 不表示环境已安装 LDVH、自动触发、受信任或已经通过集成验证 | `signer_type=ai-agent` 时必填非空；Human 分支禁止；使用当次实际环境名称，不从目标文件或历史猜测 |

### Schema 与对象载体

一个 FileAsset 对象对应一个目录，canonical 位置为：

```text
ldvh-base/file-assets/<object_id>/
├── file-asset.yaml
└── payload
```

`object_id` 必须匹配 `file-asset-[0-9]{4,}`，对象目录名必须与 `object_id` 完全一致。目录直接成员闭集只有 UTF-8 YAML manifest `file-asset.yaml` 和保存完整原始 bytes 的 `payload`；二者都必须是当前 Working Tree 中不经过 symlink 的普通文件。payload 固定不使用摄取文件名作为路径，摄取时的实际文件名只由 manifest `filename` 保存。对象当前权威位置是这一个两成员目录；manifest、payload、副本、索引、下载文件或 Web 投影均不得单独成为第二事实权威。

manifest 只包含本节绑定允许的字段。`title` 是面向 Human 与 AI 的简短资产名称，不替代 `filename`；`created_at` 是对象首次成功形成的时间，不冒充源文件创建时间、mtime、Git 时间或文件内容时间；`updated_at` 只在允许的 manifest 变更完成并回读时更新。未知或不适用字段必须省略，不使用 `null`、空字符串、空数组、占位 hash、占位媒体类型或默认签名。

完整 Schema 必须从 `fact-object-field-registry` 的 `fact-object`、本节绑定、当前结构及类型专属字段定义单向派生。目录成员、payload 完整性、manifest 与目录身份一致性以及资源边界必须进入机械规则目录；Code 不得根据目录长相、扩展名或已有实现反向发明 carrier 语义。

`fact-model-foundation` §7.4 已把上述目录登记为第六类 canonical 拓扑。当前 Helper 只对该目录提供安全精确读取、候选发现和全库完整性检查；`prepare-fact-object-draft`、`create-fact-object` 与 `update-fact-object` 仍只支持既有单文件载体，收到 `file-asset` 必须以 `invalid_request` 零写入拒绝，不得因正式读取已成立而推断目录写入也成立。

## 6. 对象语义与生命周期

FileAsset 只表达一份已经确定并被复制进 canonical 位置的原生 payload。manifest 和 payload 必须同时存在且互相一致；只存在 manifest、只存在 payload、未知目录成员、身份不一致、大小或哈希不符时，对象不能作为 mechanically valid FileAsset 消费。

重复 bytes 不自动表示同一对象。相同 `content_sha256`、相同纳入签名和相同独立用途时，AI 应优先建议复用既有 FileAsset；不同纳入责任或不同独立保留边界可以形成不同对象。Code 可以返回精确 hash 命中，但不得仅凭 hash 自动合并、复用、拒绝或归档。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `active` | 对象在每次消费时通过实际完整性检查后，可以进入默认 FileAsset 候选 | 只能作为新建初态；`disposition_summary` 禁止；状态不代替 payload 存在、哈希、安全或内容适用检查 |
| `archived` | 对象不进入默认候选，但继续保留 canonical payload，供精确引用、历史回读和入向引用处置 | 只能由 `active → archived` 形成；`disposition_summary` 必填并说明归档原因、仍有效引用、未处置范围和后续边界；payload 与不可变 manifest 字段继续完整 |

初始状态只能是 `active`，正常转换只有 `active → archived`；`archived` 为终态，不直接重开。归档不等于删除、无效或内容不可信，也不证明没有对象继续引用它。状态只影响默认发现；每次读取仍须独立检查目录、manifest、payload、size 和 hash。

纳入签名只回答同一个问题：**本次是谁把最终 bytes 直接交给 FileAsset 受控摄取边界，并对这次提交承担签名责任？**它不追溯历史作者、原始生成工具或此前流转。只使用两个分支：

1. Human 直接把最终文件 bytes 提供给 AI 或受控入口，AI 只原样复制进入 canonical 位置：`signature.signer_type=human`；不记录个人 ID，也不把代为存储的 AI 写成 signer。文件此前是否由某种 AI、工具或外部主体生成，不改变本次可观察的 Human 提交分支；
2. 没有 Human 直接提供最终 bytes，而是 AI agent 在获准范围内生成、实质修改、捕获、导出、下载、选择或提交最终文件：`signature.signer_type=ai-agent`，并由该 agent 据实写自己的 `agent_id` 自报标签与 `host_environment`。即使动作来自 Human 要求 AI 编写、截图、运行命令或导出，签名仍属于实际代表自身提交这份 bytes 的 AI agent；工具或系统不另成第三 signer。

多 agent 流程以实际把最终 bytes 提交给摄取边界的 agent 承担 AI 分支签名；该标签不宣称它独自创作内容。不能确认本次是 Human 直接提供还是哪个可观察 AI agent 代表自身提交时必须停止；Human 可以直接重新提供一份确定的最终 bytes，使新的摄取动作进入 Human 分支，也可以要求一个可观察 AI agent 重新取得并提交 bytes 进入 AI 分支，但不得给已经完成的摄取动作口头改签。

## 7. 来源、完整性、引用与消费

FileAsset 的可接受形成依据是当次实际选择的完整源文件 bytes、Human 当前指令或已准确覆盖的行动授权、签名分支判断、受控复制结果、canonical manifest/payload 回读和实际机械检查。源文件路径、会话位置、下载目录或临时 staging 只服务当次受控操作，不进入事实对象字段，也不在 canonical 对象之外形成长期权威。

`fact-model-foundation` §7.2.1 已建立唯一窄例外：完整原始 bytes 只可作为 FileAsset 专属 canonical `payload` carrier 成员存在；命令、路径、日志文字、会话定位仍不得进入 FileAsset manifest 或其它类型字段，也不得因 payload 例外放宽普通事实对象。截图、日志、诊断、导出或其它 raw payload 只有在本文对象化条件成立并通过未来受控创建边界时才能形成 FileAsset；当前 activation 不开放该写入能力。

受控创建必须安全读取完整源文件，记录当次源身份和初始指纹，在 canonical 候选命名空间之外的同一文件系统 staging 中复制并同时计算 size/hash，复制后重新确认源身份与 bytes 未漂移，生成 manifest，验证成员闭集与签名 shape，再以不覆盖既有目标的原子目录操作形成对象。写后必须从实际 Working Tree 重读 manifest 和 payload。任何步骤无法完成时不得留下可被发现为正式对象的半成品；残留只有在能证明属于该未完成事务时才可安全清理，归属不明时必须报告并停止。

每次精确读取至少检查：对象目录与两个固定成员精确存在；没有未知成员；所有成员为不经过 symlink 的普通文件；目录名、`object_id` 和 `fact_type_key` 一致；manifest 通过派生 Schema；payload 实际长度等于 `size_bytes`；完整原始 bytes SHA-256 等于 `content_sha256`；签名结构与状态条件成立。媒体类型只按字段规则检查 shape，不证明真实格式、无恶意或可安全呈现。

FileAsset 自身初版禁止 `urls` 和 `relations`。事实对象消费 FileAsset 时，复用公共 `relations` 并由消费类型的唯一定义来源显式定义 `has-file-asset`：方向为消费对象 → FileAsset；来源与目标必须属于同一当前管辖项目；目标类型固定为 `file-asset`；同一来源对象不得重复指向同一目标；关系只表示该对象持有一个文件资产资源引用，不自动表示证据、证明、依赖、采纳、授权或完成。文件在消费对象中的具体用途和能支持的范围，写入该消费对象已有的适当自然语言字段或 Study 正文，不向 relation 临时添加成员。

建立或消费 `has-file-asset` 前必须精确读取目标并确认其 mechanically valid。目标为 `archived` 时只允许精确历史引用或消费类型明确允许的现有引用继续读取，不作为新增关系的默认候选；目标缺失或无效时，来源对象的关系检查必须据实报告，不得静默删除关系、回退路径副本或假定 Git 历史足以替代当前 payload。

“哪些对象引用这个 FileAsset”只能由 Code 从目标所在同一管辖项目的实际扫描范围内，各消费对象正向 `has-file-asset` 派生。反向结果必须说明已扫描项目、类型、状态、无效对象、未完成范围和对象集指纹；不写入 `referenced_by`，不成为第二事实源，也不因结果为空自动证明无人使用或允许归档、删除。初版禁止跨项目 `has-file-asset`，避免把入向完整性扩大到无法闭合的 workspace 配置和其它仓库。

普通稳定文档可以在自然语言中同时写出项目 `id`、`fact_type_key=file-asset` 与 `object_id`，帮助 Human 或 AI 精确定位对象，也可以附上当次派生的可点击 canonical 路径。但在当前没有唯一机器可解析语法时，这种文字只属于导航提示，不进入受保护引用闭包，不提供 referential-integrity 或完整入向枚举保证。只有事实对象中同项目、正式定义的 `has-file-asset` 属于初版可机械闭合引用域；未来若需要普通文档引用取得删除保护，必须先在正确共同来源定义唯一语法、示例转义、扫描范围与迁移规则，不能由关键词共现猜测引用。

FileAsset 不进入无条件 F1 基线；它通过 F0 类型统计、F2 `active` 候选、精确引用或 WorkCase `has-file-asset` 关系进入按需读取。F2 卡片投影 `object_id`、`title`、`status`、`filename`、`media_type`、`size_bytes`、`content_sha256`、纳入签名摘要、`updated_at` 与当次完整性 coverage，不内联 payload。F3 精确读取返回 manifest、完整性结果与 canonical payload 路径；Helper JSON 只返回实际 size/hash 和 coverage，不内联二进制 payload。F4 只在消费结论需要时由调用方通过该路径读取内容；机械有效不表示内容语义相关、当前适用或安全。F0 恢复清单中的 FileAsset 范围只报告对象数量、状态、对象集指纹、完整性 coverage 与未完成范围，不把 manifest 声明或历史检查结果当作当前 bytes 完整性。

`active`、manifest 存在、F1 身份或 F2 卡片都不能单独支持“canonical bytes 当前客观存在且完整”的声明；F2 中的 `size_bytes` 与 `content_sha256` 在未完整读取 payload 时只是 manifest 声明值。F1/F2 必须携带当次实际完整性 coverage，区分只检查 manifest/成员存在、已经读取长度和已经完整计算 SHA-256 的范围；只有当次安全完整读取 payload、实际 size/hash 匹配且其它适用检查通过的 F3 结果，或 F1/F2 明确完成同等完整读取时，才能在该次读取范围声明当前 bytes 存在且与登记一致。大文件预算使完整检查未完成时必须返回未完成 coverage，不得用 `active`、历史 hash 或上次检查结果补成当前有效。

可执行文件、压缩包、HTML、SVG 或其它主动内容即使 mechanically valid，也只表示 bytes 被保存。Web、AI 环境或其它消费者必须依据内容类别与安全策略选择下载、文本显示、沙箱预览或拒绝，不能只信任 `media_type` 后直接执行或渲染。

## 8. 变更、更正、归档、删除与类型退出

payload bytes、`filename`、`media_type`、`size_bytes`、`content_sha256`、`signature`、`object_id`、`fact_type_key` 和 `created_at` 在对象创建成功后不可原地改变。内容变化、纳入签名错误、需要改变摄取文件名或媒体类型时，创建新的 FileAsset；旧对象保持原始载体，按实际情况继续 active 或经 Human 明确决定归档。不得覆盖 payload、复用 ID、静默重签或把内容变化伪装成 manifest 更正。

`title` 可以在不改变 payload 身份、用途和来源边界时原地更正；`status`、`disposition_summary` 和 Code 托管的 `updated_at` 只按 §6 的转换变化。任何成功变更必须使用当前完整对象指纹作 CAS，在 FileAsset 类型锁内验证 before/after、原子写 manifest 并回读整个目录；普通通用更新入口不得因只能写单文件而绕过 payload 一致性检查。

初版正常生命周期不提供物理删除、移动或目录重命名能力。Working Tree 中手工删除或修改必须在后续完整性检查中成为缺失或无效。当前单文件 Git Gate 不能构造 FileAsset 目录 after-image，因此任何 staged FileAsset 路径都必须报告不可验证并失败关闭；这只阻止当前提交，不证明单边成员、payload 原地变化或完整删除已经由多成员规则精确分类，也不阻止本地命令先改变 Working Tree。

敏感信息、许可、法律义务或类型退出确实要求物理移除时，必须停止普通生命周期操作，取得 Human 对准确对象、入向引用、Git 历史影响、保留与删除范围的决定，并先形成来源规则允许的一次性移除或迁移方案。不能仅凭 `archived`、无人引用、Human 曾批准创建或“Git 中还能找回”推断允许删除。

FileAsset 类型停止新增、合并、替代或取消时，必须先枚举全部对象、canonical payload、同项目正式 `has-file-asset` 正向和入向引用以及仍适用内容；普通文档文字提示只能作为补充扫描线索，不能被表达为已完整枚举。为每个对象确定继续保留或迁移到另一唯一事实位置，并完成受保护消费者改写和 Working Tree 回读。只要仍可能存在未纳入机器闭包的普通文档使用，初版就不能以“引用已清空”为由物理删除；不得只删除本文、目录、Schema、Helper 或 Web 入口后留下无主 payload 或悬空引用。

## 9. Activation 能力边界与受影响来源

本次 activation 以一个闭合、只读优先的变更包使 FileAsset 成为第六个当前事实类型，并以 WorkCase 作为第一个消费者。变更包必须同时保持以下来源和实现一致：

1. `fact-model-foundation` 登记第六类型、目录 carrier、读取/发现/完整性结果，以及既有单文件创建和更新入口对 FileAsset 的零写入拒绝；
2. `fact-object-field-registry` 登记 `file-asset-signature`、全部 manifest 字段和结构成员，并把 `disposition-summary` 扩展至 `file-asset`；
3. `fact-object-mechanical-validation-catalog` 登记目录成员、manifest/payload 一致性、size/hash、签名条件、资源上限和当前不可用边界；
4. `WorkCase` 唯一定义来源新增同项目 `has-file-asset`，并明确形成、保留、关闭冻结和 archived 目标边界；其它类型不因 FileAsset 准入自动获得该关系；
5. `Spark` 明确从既有宽目标集合排除 FileAsset，避免 `routed-to` 或 `related-to` 意外使其成为消费者；WorkCase 的 `related-to` 同样排除 FileAsset，使引用只有一个 relation key；
6. `source-of-truth-traceability` 规定现有单文件 Git Index 校验遇到 staged FileAsset 路径时只能失败关闭并报告不可验证；多成员 after-image 校验未因此成立；
7. 事实对象行动模板对 FileAsset 创建、更新、归档和删除统一交还 capability gap，不复用既有单文件事务；
8. 术语表登记 `FileAsset / 文件资产`，并保持 `Attachment / 附件` 只指授权附件；
9. 正式 Helper 读取、候选发现、对象集指纹、全库完整性与 WorkCase 关系检查直接消费当前 Schema，不保留 provisional Schema 或第二 validator；
10. 独立复核覆盖类型必要性、更小普通目录方案、字段/结构、目录 carrier、签名、关系、生命周期、安全、迁移、Git Gate 和跨来源同步成本。

本次实际开放的能力只有：安全精确读取 manifest 与完整 payload、完整性 coverage、F0/F2 发现、全库完整性检查，以及 WorkCase 对 mechanically valid FileAsset 的同项目稳定引用。没有 canonical FileAsset 实例随 activation 自动形成，现有 `docs/` 文件不迁移也不删除。受控创建、manifest 更新、归档写入、物理删除、多成员 Git Index after-image 校验、普通文档引用闭包、Web 下载/预览和跨项目引用继续不可用；调用方必须看到明确的 `invalid_request`、`unavailable` 或未完成 coverage，不能由类型 active 推断这些能力成立。

2026-07-31 A/B 试点已经完成“现有事实模型 vs 平行资产对象模型”的承载位置比较：A 能取得相同 payload 和消费结论，但要满足完整需求就必须复制身份、状态、签名、引用、发现、读取和生命周期，因此不能作为不混淆责任的普通文件位置。WorkCase 正式消费者验证用于确认统一关系、F0–F4、状态与内容边界按当前来源工作，不要求 FileAsset 改变消费者对同一 payload 得出的领域结论；相同 bytes 被正确读取后形成相同结论是预期结果。对象数量、关系 shape 或能力存在仍不能单独证明 V4、V8、HV4 或项目演进价值。

当前规则源优先读取 Working Tree，active 来源的未提交变化会立即参与规则判断。整包未闭合时，不得只凭本文 `active` 声称 FileAsset 可用；验证必须同时回读上述共同来源、Schema、Helper 结果、关系检查和 Git Gate 失败关闭结果。正式对象创建仍须另行完成安全源读取、目录原子提交、失败残留、编号分配、受控内容交付及真实并发/故障验证。

### 9.1 2026-07-31 A/B 试点的重新解释

本次使用 `docs/跨环境接入分析汇总报告-2026-07-30.md` 与 `docs/ldvh-environment-hook-claim-audit-2026-07-31.md` 的相同 bytes，对比：

1. A：受保护普通资产库候选，使用稳定 `asset_id`、sidecar manifest、固定 payload 与专用 `asset_refs`；
2. B：FileAsset 候选，使用公共事实身份与 `relations: has-file-asset`；
3. 两个 fresh reader 分别只读取一套模型，回答同一 Hook 残留处置问题。

这是一轮真实文件加 synthetic consumer envelope 的隔离语义读取，不是当前有效 WorkCase、ADR、Study 或其它事实对象的关系集成。两边取得相同 bytes、相同完整性结论、相同残留处置和相同未知范围；B 的公共关系提供统一、类型化定位，而具体用途仍由消费对象正文承担。这正符合 FileAsset 的边界：它稳定保存和标识客观存在的内容，不负责改变 payload 的含义、当前适用性或证明力。

第一次独立复核曾以“B 是否产生 A 无法取得的领域结论”为标准选择“当前退回普通资产库”，同时指出 A 已经是一套平行结构化资产模型，不能把其规则、Schema、ID、读写、引用、Git Gate、资源和安全成本当作零。Human 随后明确 FileAsset 记录的是内容客观存在，不是证据；结合 05 §7.2.1“事实对象不是用来证明自身正确的材料包”，原拒绝标准不适用。A 的平行对象成本反而支持把同一责任纳入统一事实模型。本轮仍没有验证现有事实对象集成、多项目稳定引用、归档、删除保护、正式 Helper、Web 或长期成本，这些转为 activation 和实现验证缺口，不再被误写成事实语义不成立。

据此，当前处置为：

- FileAsset 已完成类型准入，并以只读 activation 边界进入统一字段、共同来源、Helper 和 WorkCase 关系；
- activation 本身不建立 canonical 对象；当前发现只扫描实际存在的正式目录，不把试点 fixture 或普通 `docs/` 文件提升为 FileAsset；
- 不建立 A 所代表的平行 `asset_id`、`asset_refs`、资产状态或第二套发现/生命周期体系；
- 正式消费者验证关注统一关系、F0/F2/F3/F4、状态、payload 完整性和内容语义边界是否按来源成立，不要求同一 payload 在两种载体中产生不同领域结论；
- 详细输入、机械边界、消费结果、reviewer finding 与未验证范围以 `docs/file-asset-ab-consumer-hook-residual-disposition-2026-07-31.md` 和 `docs/file-asset-fact-object-proposal.md` §22 为试点记录，不把这些普通文档提升为当前规则源。

2026-07-31 的测试域纵切只接受隔离 fixture 命名空间，用于验证 POSIX no-follow descriptor、成员闭集、ABA 检查、二进制 payload、size/hash 和 archived 精确读取。正式实现继承这些安全性质，但改为读取 `ldvh-base/file-assets/<object_id>/`，直接消费 `fact-object-field-registry` 派生的 `FactSchema` 与共同 validator；试点的 provisional Schema 和独立 validator 不再构成可调用实现。不能提供同等目录句柄保证的平台据实返回 `unavailable`，不得按多次路径遍历拼接 manifest/payload 后确认 current bytes。

## 10. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| 规范身份与效力 | 新建、修改或启用本文时 | 身份、结构、直接依据、父规范、职责和 `active` 陈述一致；没有把未实现能力写成当前能力 | 00、01、05 与本文 | 当前来源回读和 Specs 检查 | 本文结构、效力与 activation 边界 | 修正身份或越权声明；闭合前不声明类型可用 |
| 类型准入与独立责任 | 准入或实质修改类型时 | 05 §6.1 七项全部成立；FileAsset 只记录客观存在的内容身份与状态，不冒充证明力；V1–V8 与 HV1–HV5 按实际服务对象分别具有范围匹配净价值；平行资产对象体系不会比统一事实模型更少且不混淆责任；01 §13 记录和独立复核完整 | 方案、A/B 试点、本文、当前来源、独立复核 | AI 语义对照、来源回读、实际使用/复用验证与 Reviewer 反例检查 | `file-asset`、直接相邻承载位置和已验证价值范围 | 撤回受影响能力声明；修正边界、净价值或独立责任 |
| 术语 | 改名、翻译或进入当前术语表时 | FileAsset 与授权附件、普通文件、Artifact、Study 和 UI“添加附件”边界清楚；中英文和机器 key 一致 | 01、术语表、本文和使用扫描 | 术语审计、全库引用扫描和独立复核 | 当次名称、定义和已扫描消费者 | 停止使用歧义名称；消歧、改名或取消术语 |
| 字段、结构与 Schema | 登记、启用或实现时 | 全局 current/retired 查重结论仍成立；结构、字段、成员、适用范围、绑定和定义引用唯一一致；没有第二权威 | 05、05.Att.01、本文和登记 diff | AI 语义复核、登记/Schema 范围 tests | FileAsset manifest 当前 Schema | 不消费受影响对象；复用、区分或补齐同批定义 |
| 目录 carrier 与身份 | 创建、读取、迁移或移动时 | 目录、manifest、payload、普通文件、非 symlink、成员闭集、身份和唯一位置成立 | 本文、实际 Working Tree、Git identity 和安全读取结果 | 真实目录扫描、正反 fixture、并发与故障 tests | 当次项目、对象目录和已扫描成员 | 不作为有效对象；零写入、回滚或报告残留 |
| payload 完整性 | 创建、读取、引用或 Git Gate 检查时 | 完整 bytes 可读，实际 size/hash 与 manifest 精确一致，没有截断或读取期漂移 | 当前 payload、manifest 和实际算法结果 | 完整读取、size/SHA-256 对比、漂移 tests | 当次实际读取 bytes | 不消费或关联；报告缺失、不一致和未读范围 |
| 纳入签名 | 创建或迁移时 | 本次直接提交最终 bytes 的责任明确属于 Human 或一个可观察 AI agent；条件成员闭合；陈述没有扩大为历史作者、原始生成者、授权或证明力 | Human 输入、当次 AI 提交过程、manifest 和本文 | AI 语义判断、结构 validator 与回读 | 当次提交分支和签名 shape；不证明陈述真实性或全局 agent 身份 | 停止创建或迁移；取得明确最终 bytes 与直接提交主体 |
| 引用与反向导航 | 建立、读取或移除引用时 | 消费类型已定义同项目 `has-file-asset`；目标完整可读；三元组、基数、状态和缺失边界成立；反向结果报告 coverage；普通文档文字未冒充受保护引用 | 消费类型来源、来源对象、目标对象和对象集 | 正向关系检查、精确目标读取、范围化同项目反向扫描 | 当次来源、目标和实际扫描范围 | 不建立或消费关系；保留悬空与未完成范围 |
| 生命周期与不可变性 | 更正、归档、修改或删除时 | 转换合法；不可变字段和 payload 未改变；归档有 Human 决定和 disposition；物理删除未通过普通入口发生 | before/after、Human 决定、CAS、回读与本文 | transition tests、payload/hash 对比、真实 Working Tree 回读 | 当次对象和转换 | 拒绝、回滚或停止；不把 archived 当作删除许可 |
| 受控创建 | 声称可以摄取文件时 | 源漂移检查、staging、编号分配、无覆盖原子目录提交、写后回读、故障残留和资源上限全部实现并验证 | Helper 契约、实际实现、两个来源分支样本和故障 tests | 真实 CLI、并发、symlink、超限、partial-write 和 rollback tests | 已验证平台、文件类型、大小和故障范围 | 不开放创建；只保留只读调查与明确缺口 |
| Git Gate 保护 | 声称删除或篡改在提交边界被阻断时 | 新增、单边成员、payload 修改、hash 错误、目录删除/移动和悬空引用具有真实 allow/block 事件证据；未检查范围不静默放行 | 当前规则、Git Gate 核心、真实 staged diff 与事件结果 | 真实 Git 事件测试，不以 unit test 代替接入 | 实际事件、平台和已覆盖 diff 类别 | 不声明受保护；修正 Gate 或报告未覆盖 |
| 安全消费 | 新增下载、预览、渲染或执行入口时 | 不只依赖 `media_type`；主动内容、超限、未知和无效对象按安全策略处理；不无界传输 | 08、实际内容策略、payload 和页面/API | contract tests、代表性文件与实际页面检查 | 当次内容类别、入口和视口 | 禁止执行/渲染；退回下载、文本或不可用状态 |
| 非 canonical 试点 | 使用当前两个审计文件说明可行性时 | 两份源/副本 bytes、size/hash、签名 shape、候选身份和关系 shape 的实际检查范围被准确保留；没有冒充正式对象 | 2026-07-31 试点记录、两个样本 hash 与本文 | 试点记录回读；需要时重新执行隔离试验 | 候选 shape 的有限可行性 | 不扩大为正式 Schema、原子性、Git Gate 或长期净价值结论 |

当前非 canonical 试点样本为：Human 指定的 `docs/跨环境接入分析汇总报告-2026-07-30.md`，9271 bytes，SHA-256 `58b4a1a5b84ff7470c974b2a16b7beea28b916253762401664ed67b2a1a171b0`，候选签名为 `human`；Human 要求当前 AI 编写的 `docs/ldvh-environment-hook-claim-audit-2026-07-31.md`，11124 bytes，SHA-256 `57ca7ee0c5f006a0736b618fdc526a55e21d0f3ff068de10e7043b6090b6f8ac`，候选签名为 `ai-agent / codex / Codex Desktop`。隔离试验中两份复制的 size/hash 与源一致，候选 manifest、身份、签名结构和两条 `has-file-asset` 关系 shape 通过所执行的确定性检查。首轮 `/tmp/ldvh-file-asset-pilot.tzC5DO` 已删除；A/B 原 `/tmp/ldvh-file-asset-ab.MI32yS` 路径已移除，其废纸篓副本不构成长期依据。该结果不证明正式 carrier、Helper、负例、并发、资源上限、Git Gate、Web 或迁移成立。

## 11. Human Gate

Human 决定的复用按 00 §10 执行。Human 当前指令或准确覆盖的 WorkCase 授权已经允许保存某份明确文件，且本文其它成立条件全部满足时，不因对象类型本身重复请求确认；Human 直接提供最终 bytes 时签名固定为 Human，Human 要求 AI agent 编写、捕获、导出或代表自身提交时签名固定为实际提交的 AI agent，二者不以额外选择 Gate 改写。

以下情况必须进入 Human Gate：

1. 新增类型的 V1–V8 与 HV1–HV5 净价值仍无法在普通目录更小方案与完整事实类型之间收敛，两组价值发生实际冲突，或需要接受显著长期迁移、存储、跨类型同步和安全成本；
2. 文件疑似含密码、token、私钥、个人敏感信息、受限制资料、许可不明内容或不应进入 Git 的数据；
3. 本次直接提交签名无法归入 Human 或一个可观察 AI agent，且需要 Human 重新提供最终 bytes、改变工作方向或接受不能保存的结果；
4. 将 active FileAsset 归档，或改变仍被对象和普通文档引用的发现与消费边界；
5. 物理删除、移动、批量迁移、类型退出或 Git 历史处理可能造成 bytes、来源、入向引用或仍适用内容实质损失；
6. 字段、结构、媒体类型、资源限制或引用模型的语义复核仍有歧义，或拟引入破坏性跨类型迁移。

Human 决定不能替代类型准入、字段登记、文件安全、纳入签名据实记录、payload 完整性、对象回读、技术验证或 Git Gate 真实接入，也不能把文件内容变成有证明力的证据、正式规则、决定或验收结论。

## 12. Stop Conditions

出现以下任一情况时，暂停受影响的创建、迁移、读取、引用、归档、删除或能力声明：

1. 本文、05、05.Att.01、05.Att.02、消费类型或实现彼此不一致，却准备创建、消费或声明正式 FileAsset 能力；
2. 当前需求只能证明“防止随手删除”，不能证明稳定身份、发现、引用、完整性或生命周期的组合价值，却继续扩张事实类型；
3. 最终 bytes 仍在变化、源读取期间漂移、对象需要多个独立 payload，或 manifest/payload 不能以同一受控事务形成；
4. 本次直接提交责任不能无歧义归入 Human 或一个实际可观察 AI agent，或者签名被用来表示历史作者、原始生成者、最初触发者、批准、授权、验收、密码学证明或内容证明力；
5. 目录、成员闭集、普通文件、symlink、身份、size、hash、Schema、状态或唯一当前位置任一检查不成立；
6. 文件包含或疑似包含敏感、许可不明、危险主动内容，或体积、读取、存储、传输和渲染边界无法安全完成；
7. 消费类型没有正式定义同项目 `has-file-asset`，目标缺失、无效、跨项目或 archived 边界不成立，却准备新增或消费关系；
8. 正在通过 `urls`、自定义路径字段、`referenced_by`、目标标题副本、自由 metadata 或专用引用数组绕过当前统一字段与关系模型；
9. payload、签名、摄取文件名、媒体类型、size 或 hash 正在原地改变，或者普通更新入口无法同时验证完整目录；
10. 归档、物理删除、移动、迁移或类型退出没有处理入向引用和仍适用内容，或把 Git 历史当作当前 payload 的替代；
11. Helper、Code、Git Gate、tests、Web 或环境入口正在宣称本文尚未进入当前来源、尚未实现、尚未接入或尚未按真实事件验证的能力；
12. 无法确认失败影响哪些对象、payload、引用、项目或消费者，继续推进可能扩大不一致或数据损失。

暂停范围只覆盖受影响的 FileAsset 类型、对象、引用或能力声明。仍可以继续只读核对当前来源和样本、完成独立复核、比较普通目录方案、补齐字段与结构登记、设计 tests、检查敏感与许可边界，以及开展明确不依赖 FileAsset 已成立的普通工作。恢复必须与触发原因对应：类型和同批来源已生效；最终 bytes 与签名分支明确；carrier、Schema、完整性、资源和引用检查成立；受控写入和真实事件验证完成；入向引用与仍适用内容已处置；或者 Human 已对规则允许其决定的准确范围作出明确取舍。
