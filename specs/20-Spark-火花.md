# Spark / 火花

```yaml
ldvh_spec:
  spec_key: "spark-fact-type"
  spec_id: "20"
  spec_kind: "spec"
  title: "Spark / 火花"
  status: "active"
  canonical_path: "specs/20-Spark-火花.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 Spark 事实类型的对象边界、Schema、生命周期、来源、关系、处置和验证规则"
  scope: "管辖项目中跨行动或会话仍有保留价值、但尚未形成确定承接位置的单一信息需求、发现、问题或缺口"
  basis:
    - "fact-model-foundation"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文是 `spark` 事实类型的唯一定义来源；它不使 Spark 读取、创建、校验、迁移、Helper、Code、tests 或 Web 能力自动成立。V3 Spark 规范、实例、Code 和 Web 只作为设计与反例输入，不取得 V4 当前效力。

## 1. 价值判断

Spark 为跨行动或会话仍有保留价值、但尚未形成确定承接位置的信息提供一个可召回、可继续判断、可明确处置的临时事实入口。没有 Spark 时，这类输入容易只留在聊天记忆中，导致遗忘、重复讨论和上下文断裂；过度使用 Spark 时，它又会成为任务池、报告容器或“不知道放哪里”的垃圾箱。

本文主要服务：

1. V1 快速定位：能够找回仍需处置的议题及其当前状态；
2. V2 充分理解：从当前摘要、关键演变、来源和关系恢复问题焦点与剩余不确定性；
3. V3 边界识别：区分未形成承接位置的信息、已经明确的行动、长期决定、复用经验、研究产物和普通文档；
4. V5 据实判断：把来源、已验证证据、关联对象和完整承接判断分开；
5. V6 工作接续：使议题能够跨会话继续判断，而不依赖逐条对话和过程日志；
6. V8 持续积累：让反复出现的缺口和发现进入正确承接位置，并让已经处置的入口退出待处理集合。

Spark 新增一项事实类型发现入口、一份 Schema 和相应迁移与实现成本，也会增加创建前查重和终态判断负担。相对地，它消除的是跨会话未收敛信息反复丢失、重复讨论、被过早升级为行动或决定以及无法明确退出入口的持续成本；这些问题不能由普通文件或其它四类对象在不混淆责任的情况下自然承担。通过单一对象粒度、九个公共字段复用、一个小型结构、条件字段省略和三状态闭集，新增维护面被限制在实现其独有价值所需的最小范围。因此 V1、V2、V3、V5、V6、V8 的持续净收益高于发现、Schema、迁移和实现成本；V4 稳定推进由后续行动承接，V7 清晰沟通由来源、处置边界和需要时的 Human Gate 交还辅助实现，二者都不作为扩大 Spark 职责的理由。

Human 已确认 V4 保留 Spark 类型，因此本文不重复决定是否建立该类型；本文仍必须证明具体语义、对象边界和 Schema 没有从 V3 实现直接恢复。V3 39 个实际 Spark 中 37 个长期保持 `pending`，多套来源与 `related_*` 字段、空值占位和过长演变记录使分流与退出判断漂移。V4 因而保留跨会话捕获价值，但收紧对象粒度、统一来源与关系，并把终态解释为入口职责结束而不是下游工作完成。

## 2. 规范依据

本文直接依据：

1. `fact-model-foundation`：规定具体事实类型的责任、统一字段登记、状态、来源、证据、关系、对象变更和验证共同边界；
2. `source-of-truth-traceability`：规定 Git 可追踪文件、当前 Working Tree、来源回指和稳定事实边界。

历史 `specs/20-Spark-火花.md`、`ldvh-base/sparks/`、V3 事实模型基础、候选记录对象编排、Code 和 Web 用于识别已验证价值与失败模式。它们不能证明 V4 路径、字段、状态、实例当前性或写入能力成立。V3 候选记录对象编排中的“创建前召回”只作为合理设计输入；本文依据 05 的字段准入与对象查重规则重新定义相应边界。

## 3. 职责边界

本文负责定义：

1. `spark` 的类型语义、对象粒度、准入和非准入边界；
2. Spark 的唯一当前承载位置、稳定身份、完整 Schema 和未知内容处理；
3. Spark 的状态集合、状态转换、终态处置、来源、证据和关系语义；
4. Spark 创建、更新、更正、拆分、合并、处置、删除和停止使用时的领域边界；
5. Spark 的验证要求、Human Gate、Stop Conditions 和最小失败范围。

本文不负责定义：

1. WorkCase、ADR、Pitfall、Study 或普通文档的类型语义、准入、Schema 和生命周期；
2. Helper 请求或响应、Code API、文件分配算法、CLI 命令、Web 表单或页面写入白名单；
3. V3 Spark 的自动迁移、兼容读取或继续生效；
4. 当前行动是否获准、下游工作是否完成、长期决定是否成立或研究结论是否正确；
5. 逐条聊天、执行日志、临时分析、派生索引或 Git 历史的替代副本。

AI 负责判断信息是否需要 Spark、是否与已有事实语义重复、当前摘要和处置结论是否准确；Code 只可依据当前来源检查固定结构、值闭集、引用和状态条件。本文定义 Spark 的领域规则，不授予任何消费方通用写入或删除权限。

## 4. 适用范围

本文适用于管辖项目中准备创建、读取、更新、关联、拆分、合并、处置或消费 Spark 的场景，以及 Spark 与其它稳定事实位置之间的承接判断。

一个信息单元只有同时满足以下条件，才可以形成 Spark：

1. 跨当前行动或会话仍有具体保留价值；
2. 当前尚不能自然写入已有事实对象、规范、文档或其它稳定来源；
3. 尚未形成清楚的执行目标与验收边界、长期决定、已验证复用经验或完整研究产物；
4. 能表达为一个可独立判断“是否仍需处置”的信息需求、发现、问题或缺口；
5. 已召回并比较现有 Spark 和相邻稳定事实，没有可无损更新的现有入口；
6. 至少一个来源可以按所需精度回指，且没有把推测改写成已验证事实。

当前行动中可以直接处理且不需跨会话保留、已经由现有位置完整承载、已经具有明确行动目标、已经形成长期决定或复用经验、完整研究报告、过程日志、逐条聊天、工具输出和单纯执行提醒，不应单独形成 Spark。多个已经可以独立处置的问题不得长期捆成一个 Spark；相关子问题一旦具有独立目标、判断或跟踪价值，必须拆分并建立关系。

## 5. Spark 类型定义

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `spark` | 尚未形成确定承接位置但值得跨行动或会话保留的单一信息需求、发现、问题或缺口 | `spark-fact-type::5. Spark 类型定义` |

### 结构准入记录

| information_need | compared_structure_keys | decision | resulting_structure_key | rationale | review_ref |
|---|---|---|---|---|---|
| 直接读取一项关键语义转折的发生时间和摘要 | `fact-object,relation,relation-target,source-ref` | new | `spark-evolution-entry` | 已检索全部 current 与 retired 结构；现有结构分别承载完整事实对象、关系、关系目标和来源定位，均不能无损表达 Spark 内部关键语义转折条目 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |

### 类型专属结构定义

| structure_key | meaning | not_meaning | constraints |
|---|---|---|---|
| `spark-evolution-entry` | Spark 当前摘要无法单独解释时，需要直接读取的一次关键语义转折 | 不表示逐条对话、执行日志、状态历史、来源或证据对象 | 成员闭集只有 `at` 与 `summary`；只在问题焦点、边界、判断方向或承接方向发生实质变化时增加 |

### 字段准入记录

| information_need | compared_field_keys | decision | resulting_field_key | rationale | review_ref |
|---|---|---|---|---|---|
| 稳定识别同一 Spark 对象 | `object-id` | reuse | `object-id` | 公共对象身份语义无损适用；Spark 只收紧格式，不另建 `id` | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 声明对象属于 Spark 类型 | `fact-type-key` | reuse | `fact-type-key` | 公共类型身份无损适用；固定值为 `spark`，不恢复 `type` | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 提供 Human 与 AI 可读的短标签 | `title` | reuse | `title` | 公共标题语义无损适用，不承担问题全文 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 记录对象首次按 Spark 形成的时间 | `created-at` | reuse | `created-at` | 公共形成时间语义无损适用 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 记录当前 Spark 内容最近一次实质变化时间 | `updated-at` | reuse | `updated-at` | 公共更新时间语义无损适用，不承担关键转折历史 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 表明 Spark 是否仍承担待处置入口 | `status` | reuse | `status` | 公共条件状态入口适用，由本文定义 Spark 值闭集和转换 | `spark-fact-type::5. Spark 类型定义::field-review-0001` |
| 回指形成或理解当前 Spark 的输入 | `source-refs` | reuse | `source-refs` | 公共来源数组替代 V3 `source`、`source_detail` 与 `input_refs` 的重叠入口 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 支持已验证观察或终态处置判断 | `evidence-refs` | reuse | `evidence-refs` | 公共证据数组无损适用；不得用来源存在替代证据充分性 | `spark-fact-type::5. Spark 类型定义::field-review-0001` |
| 表达 Spark 与其它事实对象的有向语义关系 | `relations` | reuse | `relations` | 公共关系统一入口替代全部按目标类型拆分的 `related_*` 与对象型 `resolved_to` | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 直接读取 Spark 当前问题焦点、边界和剩余不确定性 | `current-summary,title` | reuse | `current-summary` | 标题只用于识别；共享当前摘要无损承接 Spark 的当前焦点与剩余问题 | `spark-fact-type::5. Spark 类型定义::field-review-0001` |
| 在多个 open Spark 中表达应优先处理的相对等级 | `priority` | reuse | `priority` | 共享优先级同样只排序本类型未终态入口，不授权或描述下游行动 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 不依赖逐次 Git diff 直接读取少量关键语义转折 | `updated-at` | differentiate | `evolution` | `updated_at` 只回答最近何时变化；关键转折需要时间与摘要的结构化条目，但不得恢复过程日志 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 说明 routed 或 discarded 为什么成立以及剩余议题为何为零 | `disposition-summary,status` | reuse | `disposition-summary` | 共享终态处置说明无损承接完整承接或废弃理由，不由状态值替代 | `spark-fact-type::5. Spark 类型定义::field-review-0001` |
| 记录 Spark 退出待处置入口的时间 | `closed-at,updated-at` | reuse | `closed-at` | 共享终态首次成立时间与 Spark 终态语义一致，不能由最近更新时间替代 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 记录关键语义转折发生或被确认的时间 | `created-at,updated-at` | differentiate | `evolution-at` | 对象创建与最近更新时间不能表达单条语义转折时点 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |
| 记录关键语义转折的最小可读内容 | `current-summary,title` | differentiate | `evolution-summary` | 当前摘要是最新快照，标题是短标签；本字段只保留解释方向变化所需的历史摘要 | `spark-fact-type::5. Spark 类型定义::field-review-0002` |

### 字段独立复核

| review_key | reviewer | reviewed_scope | findings | disposition |
|---|---|---|---|---|
| `field-review-0001` | independent-spec-review-agent | Spark 类型语义、状态、来源、证据、关系及终态字段 | V3 的单一主目标、Study 不能完成分流、普遍 Human Gate 和长期 pending 会制造漂移；当前摘要与最小终态说明需要保留 | 使用 open/routed/discarded；允许任意稳定位置在完整承接时结束入口；统一关系并缩小 Gate |
| `field-review-0002` | independent-field-audit-agent | 39 个 V3 Spark 的字段分布、12 个代表样本、全部字段与结构准入行，以及 WorkCase 准入后的共享提升复核 | 身份与来源关系可复用公共字段；当前摘要、priority 与终态字段有跨类型同义需求；Spark evolution 有直接消费价值但 WorkCase 的历史应由当前快照与 Git 承接；source context 会污染共享结构，空值、related_* 和 resolved_to shape 不应继承 | 复用九个公共入口；提升四个跨类型字段，保留 evolution 结构与三个字段为 Spark 专属；删除 source-context，省略空条件字段并禁止按目标类型拆字段 |

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
| `object-id` | required | `spark-fact-type::5. Spark 类型定义` |
| `fact-type-key` | required | `inherit` |
| `title` | required | `spark-fact-type::5. Spark 类型定义` |
| `created-at` | required | `inherit` |
| `updated-at` | required | `spark-fact-type::8. 创建、更新与停止使用边界` |
| `status` | required | `spark-fact-type::6. 对象语义与生命周期` |
| `source-refs` | required | `spark-fact-type::7. 来源、证据、关系与处置` |
| `evidence-refs` | conditional | `spark-fact-type::7. 来源、证据、关系与处置` |
| `relations` | conditional | `spark-fact-type::7. 来源、证据、关系与处置` |
| `current-summary` | required | `spark-fact-type::6. 对象语义与生命周期` |
| `priority` | conditional | `spark-fact-type::6. 对象语义与生命周期` |
| `evolution` | conditional | `spark-fact-type::6. 对象语义与生命周期` |
| `disposition-summary` | conditional | `spark-fact-type::6. 对象语义与生命周期` |
| `closed-at` | conditional | `spark-fact-type::6. 对象语义与生命周期` |

### 类型专属字段定义

| field_key | field_path | JSON type | meaning | not_meaning | constraints |
|---|---|---|---|---|---|
| `evolution` | `evolution` | array | 为直接理解当前 Spark 保留的少量关键语义转折 | 不表示逐条对话、执行日志、状态历史、Git 变更清单或下游对象正文 | 数组最少 1 项、最多 8 项，每项使用 `spark-evolution-entry`；只有问题焦点、边界、判断方向或承接方向发生实质变化且仅靠当前摘要难以理解时增加条目 |
| `evolution-at` | `at` | string | 一项关键语义转折发生或被当前来源确认的时间 | 不表示 Spark 创建、最近更新、状态转换或提交时间 | 必填；带时区 RFC 3339 date-time；不得早于对象 `created_at` 或晚于当前 `updated_at` |
| `evolution-summary` | `summary` | string | 一项关键语义转折及其对问题焦点、边界或承接方向影响的简短说明 | 不表示完整来源、证据、过程日志或当前摘要副本 | 必填非空；只保留理解转折所需内容，来源与证据分别使用统一引用字段 |

### Schema 与对象载体

Spark 对象使用 UTF-8 YAML，一文件一对象，当前权威位置固定为管辖项目仓库中的 `facts/sparks/<object_id>.yaml`。`object_id` 必须匹配 `spark-[0-9]{4,}`；文件名必须与 `object_id` 完全一致，分配后的身份不得因短标题、路径、状态或内容改变。`title` 只简短标识核心议题，不复制 `summary`。未知或不适用的条件字段必须省略，不使用显式 `null`、空字符串、空数组、占位时间或默认关系。

完整 Schema 由统一登记的 `fact-object` 直接字段、本节绑定、类型专属字段定义及 `value_structure` 递归组合。Spark 不得出现未登记字段，也不得向共享 `source-ref` 添加类型私有扩展；来源触发内容必须由精确 locator 指向原始来源，并由当前 `summary` 在不冒充来源原文的前提下表达。本文没有授权附件，Schema、Code 常量和 test fixture 都只能从当前来源派生。

## 6. 对象语义与生命周期

一个 Spark 只表达一个能够独立判断是否仍需处置的核心信息需求、发现、问题或缺口。`summary` 是当前快照；`evolution` 只在当前快照和 Git 历史无法高效解释关键方向变化时提供最小直接阅读记录。每次更新都必须复核全部 evolution 条目；已经被当前摘要无损吸收、已不能影响当前判断或不再为恢复上下文所必需的条目必须删除，由 Git 保留历史。当前对象最多保留 8 项关键转折；超过时必须先压缩摘要、删除已吸收条目或拆分对象，不得继续追加。Spark 不承载下游对象的正文、计划、状态或验收。

状态闭集为：

| status | 语义 | 必须成立 |
|---|---|---|
| `open` | Spark 仍有未被稳定位置完整承接的内容，需要继续召回、判断、拆分或分流 | `priority` 必填；`disposition_summary` 与 `closed_at` 不得出现；已有关系不等于完整承接 |
| `routed` | 原始信息需求已经由一个或多个稳定当前位置完整承接，Spark 不再承担待处置入口 | `priority` 禁止；`disposition_summary`、`closed_at`、`evidence_refs` 必填；非 Spark 事实对象承接使用 `routed-to`，Spark 接替遵守 §7 的 `supersedes` 单边规则，普通文件承接由证据引用定位 |
| `discarded` | 有依据地确认该信息不再值得继续跟踪或作为分流入口 | `priority` 禁止；`disposition_summary`、`closed_at`、`evidence_refs` 必填；不得仅因暂时无行动或优先级低而废弃 |

正常状态转换只有 `open → routed` 和 `open → discarded`。终态不直接重开；后来出现新的未处置信息时创建新 Spark，并用 `supersedes` 指向旧 Spark。若原终态记录本身错误，应按 05 的事实更正规则修正，而不是把更正伪装成领域状态转换。

`routed` 只表示 Spark 入口职责结束，不表示目标工作完成、决策正确、经验有效或报告结论成立。Study、普通文档或多个位置只要确实完整承接原信息需求，都可以支持 routed；若报告之后仍有行动、决定、规则或其它未承接缺口，Spark 必须保持 open。多个承接位置共同完整覆盖时不强迫选取虚假主目标，分别保留关系或证据，并在 `disposition_summary` 说明覆盖判断。

## 7. 来源、证据、关系与处置

每个 Spark 至少具有一项 `source_refs`。来源可以是 Human 输入、对话、规范、代码、测试观察、事实对象、项目文档或外部资料；`kind` 必须描述实际来源，`locator` 必须达到重新定位当前摘要所需的精度。没有稳定对话标识时不得伪造 locator，也不得用泛化的 `conversation` 字符串冒充可重新定位来源。

`evidence_refs` 只在支持已验证观察或处置判断时出现。`routed` 的证据必须支持全部原始问题已经被稳定位置承接；`discarded` 的证据必须支持不再跟踪的理由。Human 指令可以成为处置依据，但仍需按实际来源回指；关系存在、文件存在或测试命令成功本身不自动充分。

Spark 的 `relation_key` 闭集为：

| relation_key | 目标、基数与方向 | 跨项目、缺失、自指与循环 | 对状态的影响 |
|---|---|---|---|
| `routed-to` | 当前 Spark 指向实际承接其部分或全部信息需求的 current 非 Spark 事实对象；可以有一项或多项 | 可以跨项目，但跨项目目标必须带完整 governance refs；目标缺失或不再 current 时关系及 routed 判断失效；禁止自指；全部 routed-to 边必须无环 | 单独存在不改变状态；只有目标内容实际承接相应范围、全部原始内容被关系与其它稳定位置共同覆盖且证据充分时才能 routed |
| `related-to` | 当前 Spark 指向任意 current 事实对象，表示主题相关但不声明承接；可以有零项或多项 | 可以跨项目并按公共结构保留 governance refs；目标缺失时该关系失效但不自动改变 Spark 状态；禁止自指；允许互相或成环，因为每条边只表达局部相关性，不派生承接或反向权威 | 不构成处置证据，也不因关系数量改变状态 |
| `supersedes` | 一个 `open` 新 Spark 指向被其完整接替的 `routed` 或 `discarded` 旧 Spark；可以指向一项或多项旧对象，反向只作为派生索引 | 只允许同一管辖项目；目标缺失时关系失效；禁止自指；全部 supersedes 边必须无环，不得让两个入口互相替代 | 只说明新入口与旧身份的接替关系；不重开或改写旧对象，也不单独证明旧对象原处置正确 |

`routed-to` 的目标类型必须是已经具有当前唯一定义来源、能够自然承载相应信息的非 Spark 事实类型；不能指向 Spark、缓存、派生索引或只因字段相似而选择的对象。Spark 拆分或替代只由新 `open` Spark 通过 `supersedes` 单向指向旧终态 Spark；旧对象以 `disposition_summary` 和 `evidence_refs` 定位新入口，不再写一条反向 `routed-to` 权威关系。判环时，`routed-to` 按当前 Spark 到承接对象的方向检查，`supersedes` 按新 Spark 到旧 Spark 的替代方向单独检查；不得用任何关系环证明完整承接。反向导航由 Code 派生，不得为了反向展示写入第二条含义不同的权威关系。

普通 Markdown、配置或其它非事实对象不能伪装成 `relation-target`；它们按实际作用进入 `source_refs` 或 `evidence_refs`。V3 `related_workcases`、`related_adrs`、`related_studies`、`related_sparks`、`related_docs`、`input_refs` 和 `resolved_to` 不进入 V4 Schema。

创建前必须按主题、来源、相邻对象和已知引用召回现有 Spark 与稳定事实。完全重复或同一对象的自然更新应更新现有入口；语义范围不同且需要独立处置时才新建并建立必要关系。Code 可以做精确 key、locator 和文本检索，不能裁决自然语言是否同义。

## 8. 创建、更新与停止使用边界

创建 Spark 前必须确认准入条件、召回结果、对象粒度、来源和当前摘要。创建后的任何更新都必须先取得实际行动授权，写入当前权威文件，回读 Working Tree，并验证 Schema 与状态条件；本文不因定义更新规则而授权 AI、Helper、Code 或 Web 修改文件。

修正 `summary` 时必须保持其为当前快照；只有会影响后续恢复的关键语义转折才追加 `evolution`。优先级变化只改变召回排序，不推进状态。新增关系必须说明方向语义，不复制目标正文。拆分必须让每个新 Spark 具有独立问题边界、来源和身份，并由原对象或新对象保留关系；合并、替代或删除不得丢失仍适用来源、证据和承接关系。

Spark 可以保留终态文件作为历史参考。归档只在未来当前来源另行定义明确位置与消费边界后成立；本文不建立独立 archived 状态。删除仅在来源规则允许、稳定身份与引用已经处置且不会丢失仍适用事实时成立，不能用删除代替 discarded。

Spark 类型停止新增、合并、替代或取消时，必须按 05 处理唯一定义来源、全部当前对象、引用消费者和仍适用事实。V3 实例的迁移需要逐对象重新判断来源、当前价值、状态与字段映射；缺少时区、稳定 locator 或终态证据时必须报告不完整，不能生成默认值。

## 9. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Spark 类型定义 | 新建或实质修改本文时 | 唯一声明、对象语义、字段与结构准入、绑定、状态、来源、证据、关系和独立复核完整且无第二权威 | 05、统一登记、本文、历史反例和独立复核记录 | 当前来源回读与规范检查；Code 只验证可机械部分 | 当前 `spark` 类型定义 | 本文不进入或退出当前规则源；修正定义，不消费受影响对象 |
| Spark 准入与查重 | 创建新对象前 | 信息跨行动有保留价值、尚无正确承接位置、粒度单一、已召回相邻事实且没有可无损更新的现有入口 | 当前输入、来源定位、召回结果、相邻对象与 AI 语义比较 | AI 来源回读与全局检索；Code 只辅助精确检索 | 当次候选与直接相邻事实 | 不创建；直接处理、更新现有位置、拆分或转正确承载 |
| 对象 Schema 与身份 | 创建、读取或更新对象时 | 路径、object_id、fact_type_key、字段闭集、类型、出现条件、时间和引用均符合当前来源 | 当前文件、统一登记、本文字段定义与派生 Schema | 实际 parser/validator；未实现时逐项来源回读 | 当次对象当前 Working Tree 内容 | 不作为有效 Spark 消费；报告具体字段与未验证范围 |
| 状态与处置 | 准备 routed 或 discarded 时 | 全部原始内容确已承接或废弃理由成立；终态字段、证据、关系和时间完整一致 | 处置前后对象、承接位置、来源、证据与 Human 决定 | AI 语义审核、目标回读和结构校验 | 当次状态与处置声明 | 保持 open；补齐承接、证据或进入 Human Gate |
| 来源、证据与关系 | 写入摘要、验证观察或建立承接关系时 | 来源可重新定位，证据支持实际声明，关系方向和目标稳定，普通文件未伪装成事实对象 | 原始来源、目标对象或文件、引用成员和当前摘要 | 来源与目标回读；Code 检查结构和稳定身份 | 当次摘要、声明与关系 | 缩小声明、修正引用或移除无依据关系 |
| 变更与回读 | 创建、更新、更正、拆分、合并、替代或删除后 | 实际获准变更已写入、回读并验证；失败和部分结果如实保留 | Human 指令、文件差异、Working Tree 回读和验证结果 | 实际写入入口与当前文件回读 | 当次实际变更 | 不声明成功；修正、回滚或保留部分结果与残留风险 |

当前机械检查可以验证本文及统一登记的身份、表形、唯一性、引用、字段覆盖和适用范围，不证明自然语言准入、来源充分性、终态正确性或任何事实服务已经实现。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 废弃、合并、拆分、替代或删除可能实质丢失仍有价值的入口、来源、证据或关系；
2. 依据不足但准备宣布一个或多个位置已经完整承接全部原始问题；
3. 多个承接位置或权威来源冲突，适用来源规则与证据无法确定保留或放弃哪一处；
4. Spark 的处置实质改变产品方向、长期规则、重大风险接受或其它需要 Human 决定的领域事项；
5. 当次创建、更新或处置超出已有 Human 授权。

Human 已明确要求创建，或在既有授权范围内补充来源、修正摘要和建立普通可逆关系时，不因对象类型是 Spark 而重复进入 Gate。Human 决定不能替代 Schema、来源回读、证据充分性和写后验证，也不能使未完整承接的 Spark 自动 routed。

## 11. Stop Conditions

出现以下任一情况时，必须暂停受影响 Spark 的新建、更新或处置：

1. 未召回已有对象，存在重复或同义 Spark 风险；
2. 信息已经由现有事实源自然、完整承载，或已经满足其它正确承载位置的边界；
3. 没有可回指来源，或 locator 无法达到当前声明所需精度；
4. 正在把推测写成已验证事实，把关系存在写成完整承接，或把终态写成下游完成；
5. 一个对象混入多个独立议题，无法判断何时结束入口职责；
6. 仍有未承接内容，却准备标记 routed；
7. 处置目标缺失、失效或无法稳定定位，或者普通文件被伪装成事实对象关系；
8. 正在用 Spark 长期替代明确行动、长期决定、复用经验、完整报告或普通文档；
9. 使用未登记字段、空值占位、按目标类型拆分关系字段或实现私有扩展；
10. 写入、删除或高影响处置没有实际授权、没有写后回读或没有范围匹配验证；
11. 只因生成报告、建立关联、运行命令或收到 Human 回应就声称 Spark 已完成处置。

暂停只影响相应对象、候选或处置声明。期间可以继续只读召回、来源核对、对象拆分、证据补充、正确承载位置比较和 Human Gate 准备。只有重复风险消除、来源与对象边界成立、Schema 修正、全部内容获得稳定承接或废弃依据充分、实际变更完成回读后，才能恢复相应范围。
