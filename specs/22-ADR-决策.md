# ADR-决策

```yaml
ldvh_doc:
  doc_id: "22"
  doc_kind: "work_model_spec"
  title: "ADR-决策"
  status: "active"
  canonical_path: "specs/22-ADR-决策.md"
  created: "2026-06-09"
  updated: "2026-06-09"
  parent_doc: ""
  relation: ""
  positioning: "定义 ADR / 决策工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则"
  scope: "所有接入 LDVH 且需要管理长期决策、事实源边界、规范判断和后续执行约束的项目"
  basis:
    - "specs/05-工作模型基础规范.md"
  related_specs:
    - "specs/05.01-工作模型字段定义与语义规范.md"
    - "specs/05.02-工作模型字段内容与格式规范.md"
    - "specs/05.03-工作模型字段注册与消费规范.md"
    - "specs/07-Code确定性执行实现规范.md"
    - "specs/10-Git提交规范.md"
  code_consumption:
    - "doc_metadata"
    - "relations"
    - "structure"
    - "member_consistency"
    - "work_model_collection"
```

```yaml
ldvh_member:
  spec_id: "22"
  kind: work_model
  name_en: ADR
  name_zh: 决策
  collection_status: active
  canonical_path: specs/22-ADR-决策.md
  instance_root: ldvh-base/adrs/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
    - state_machine
    - instance_checks
```

---
## 1. 对象定位与准入条件

ADR / 决策是已确认但尚未完全吸收到 specs、Rules / Instructions、Skill、Agent 或工作流程中的决策补丁，用于在稳定吸收完成前约束 AI 和 Human 的后续行动，并保留为什么这样决定的追溯依据。ADR 记录决策补丁的背景、内容、影响和关联关系；specs、Rules / Instructions 或其他稳定入口记录以后必须怎么做。

ADR 不是所有判断或提案的默认归宿。AI 可以在当前任务中做临时判断、记录分析结论或选择局部执行策略；未确认、未采纳或尚在讨论的内容应留在 Spark、WorkCase 或 Study 中。只有已经确认、需要作为过渡约束被后续 AI/Human 读取，且尚未完全吸收到稳定承载中的判断，才应进入 ADR 事实源。

### 1.1 ADR 准入条件

一个判断满足以下条件之一时，应考虑形成 ADR：

1. 影响多个 WorkArea、WorkCase、工作模型、工作流程或项目阶段；
2. 改变长期执行方式、协作方式、事实源归属或 Human Gate 边界；
3. 改变 specs、Rules / Instructions、Skill、Agent 或适配措施的长期规则；
4. 对后续 AI 或 Human 执行具有持续约束；
5. 多次重复出现，需要稳定记录选择理由；
6. 存在明确取舍且已形成确认结论；
7. 不记录会导致后续重复争论、误读或规则漂移。

创建 ADR 前，AI 必须说明准入理由、决策问题、建议结论、影响范围和预期回写位置，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 ADR 的内容

以下内容通常不应单独形成 ADR：

1. 当前工作项内的一次性执行策略；
2. 不影响后续协作的局部技术选择；
3. 尚未稳定或尚未确认的讨论、想法、提案或资料；
4. 已由 specs、Rules / Instructions 或其他正式规范明确约束的重复判断；
5. 仅属于风险判断、依赖关系、产物引用或检查结果的字段内容。

不形成 ADR 的内容，应按性质进入 WorkCase 字段、Spark、Study、docs/sources、当前执行上下文或对应事实源。未采纳的候选方案不应单独创建 ADR，也不应写入 ADR 字段；如需保留，应进入对应 Spark / Study 的演变记录或当前对话上下文。

### 1.3 ADR 与规范的边界

ADR 记录决策补丁的背景、原因、选择和后果；正式规范记录稳定规则。ADR 不替代 specs 正文、Rules / Instructions 执行入口、工作模型字段契约或工作流程行动规则。

当 ADR 中的决策需要成为长期规则时，应把规则正文吸收到对应正式规范或运行入口。吸收完成后，ADR 应转为 `archived`，只保留决策原因、归档原因和追溯关系；未吸收完成前保持 `active`。

---
## 2. 事实源边界

本文是 ADR 工作模型的权威规范，定义 ADR 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

ADR 实例的权威事实源位置为：

```text
ldvh-base/adrs/adr-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| ADR 工作模型规范 | `specs/22-ADR-决策.md` |
| ADR 实例 | `ldvh-base/adrs/` |
| ADR 字段内容格式 | `specs/05.02-工作模型字段内容与格式规范.md` |
| ADR 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

ADR 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

ADR 标准状态如下：

| 状态 | 含义 |
|---|---|
| `active` | 决策补丁仍有效，AI 和 Human 应优先参考 |
| `archived` | 决策补丁已被 specs、Rules / Instructions、Skill、Agent 或工作流程等稳定承载吸收，ADR 只保留追溯 |
| `deprecated` | 决策补丁已废弃，不得继续作为执行依据 |

`archived` 和 `deprecated` 是稳定终态。终态 ADR 不得直接重开；如需重新判断，应新建 ADR 或修改对应稳定承载，并在新事实源中引用原 ADR。

### 3.2 合法状态流转

```text
active → archived
active → deprecated
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` → `archived` | 决策补丁已被稳定承载吸收 | `archive_reason` 条件必填，应说明吸收位置和归档依据 |
| `active` → `deprecated` | 决策补丁不再适用或方向被放弃 | `deprecated_reason` 条件必填，应说明废弃原因和不得继续作为依据的边界 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 ADR 与 WorkArea / WorkCase

工作域或工作项涉及长期决策、方案选择或事实源边界时，应创建或关联 ADR。ADR 可通过 `related_workareas` 引用来源工作域，通过 `related_workcases` 引用来源工作项。

ADR 不替代 WorkArea 的长期范围，也不替代 WorkCase 的目标、成功标准、执行编排或关闭判断。

### 4.2 ADR 与 WorkCase

工作项执行过程中产生的判断满足 ADR 准入条件时，可升级为 ADR。ADR 可通过 `related_workcases` 引用来源工作项。

ADR 不替代 WorkCase 的成功标准、验证证据、风险判断或关闭证据。

### 4.3 ADR 与 Git 提交记录

ADR 的创建、状态变化、核心决策改写、归档、废弃和升级为规范时，都应留下 Git 提交记录。commit message 格式规则由 `specs/10-Git提交规范.md` 定义。

### 4.4 ADR 与 Spark

Spark 中的输入满足 ADR 准入条件后，可以转化为 ADR。转化时应：

1. 保留 Spark 与 ADR 的引用关系；
2. 说明为什么从未计划化输入升级为长期决策；
3. 评估 Human Gate；
4. 不在 ADR 中复制 Spark 全文，只保留摘要和引用。

Spark 的准入、状态和字段契约由 `specs/24-Spark-火花.md` 定义。

### 4.5 ADR 与 specs / Rules

ADR 中的决策补丁升级为稳定规则时，应：

1. 将规则正文写入对应 specs 正式规范、Rules / Instructions 或其他权威入口；
2. 在 ADR 的 `related_rules` 或其他 `related_*` 字段中记录追溯关系；
3. 保留 ADR 的背景、取舍和后果；
4. 通过 Git 提交记录留下变更追溯；
5. 经 Human Gate 确认。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 ADR 实例；
2. 将 Spark、WorkCase 过程判断、临时讨论或 docs/studies 结论升级为 ADR；
3. 创建 `active` ADR；
4. 将 `active` ADR 标记为 `archived` 或 `deprecated`；
5. 修改 `active` ADR 的 `decision` 字段；
6. 将 ADR 决策升级为 specs、Rules / Instructions、Skill、Agent 或适配措施规则；
7. 改变 ADR 的事实源载体、状态机、升级路径或终态语义；
8. 删除原 ADR 而不是通过状态表达废弃或替代。

推翻或替代原决策补丁时，不得删除原 ADR 文件。若原补丁已被稳定承载吸收，应将原 ADR 标记为 `archived` 并写入 `archive_reason`；若原补丁不再适用或方向被放弃，应将原 ADR 标记为 `deprecated` 并写入 `deprecated_reason`。如存在新的 ADR 或稳定关联位置，应在 `related_adrs`、`related_rules` 或其他 `related_*` 字段中记录追溯关系，不再使用独立 `superseded` 状态表达替代。

Human Gate 的具体环境实体由 04 系列环境适配项和适配措施记录。本文只规定 ADR 语境下需要确认的事实、影响范围和证据要求。

ADR 语境下的 Human Gate 记录应遵守 `specs/06-工作流程基础规范.md` §6.3.1。创建、归档、废弃、核心决策改写或升级为规范等场景中，确认记录至少应说明目标 ADR、决策变化、影响范围、确认依据、Human 决策、后续回写位置和残留风险。确认记录可以摘要写入 ADR 的 `context`、`consequences`、`archive_reason`、`deprecated_reason`、相关 WorkCase / Spark 或 Git commit 证据中，但不得只停留在对话结论里，不得维护手写 `status_history`。

---
## 6. 字段契约

### 6.1 字段表

公共字段语义定义见 `specs/05.01-工作模型字段定义与语义规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `adr-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `adr` | string | 是 | 固定为 `adr` | Reference | AI、Code、Web |
| `title` | 决策一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 `active` / `archived` / `deprecated` | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `date` | 决策确认日期 | date | 是 | `YYYY-MM-DD`，表示该补丁被确认进入 ADR 的日期 | Reference | AI、Web |
| `context` | 决策背景、问题和来源 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `decision` | 决策补丁内容 | string | 是 | `active` 后核心内容变更需 Human Gate | Decision | AI、Human、Web |
| `consequences` | 决策影响闭环 | string | 是 | active ADR 必须按 `## 正向价值`、`## 逆向价值`、`## 实施成本`、`## 风险评估`、`## 注意事项` 五段式书写；有逆向价值时必须引用 V1-V10；无逆向价值时 `## 逆向价值` 填写 `当前决策无逆向价值` | Decision / Narrative | AI、Code、Web |
| `related_workareas` | 关联工作域 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workcases` | 关联工作项 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_sparks` | 来源或关联火花 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_rules` | 关联规范或 Rules 路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `archive_reason` | 归档原因和吸收位置 | string | 条件必填 | `status: archived` 时必须填写 | Narrative | AI、Code、Web |
| `deprecated_reason` | 废弃原因和不再适用边界 | string | 条件必填 | `status: deprecated` 时必须填写 | Narrative | AI、Code、Web |

字段内容格式按 `specs/05.02-工作模型字段内容与格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: adr-0001
type: adr
title: Git 提交记录承载事实源修改追溯
status: active
created: '2026-06-09T00:00:00'
updated: '2026-06-09T00:00:00'
date: 2026-06-09
context: |
  LDVH 需要记录事实源变更，但不希望为每次变更额外创建 YAML 实例。
decision: |
  Git 提交记录直接承载事实源修改追溯，不创建 ldvh-base/changes/。
consequences: |
  ## 正向价值

  - 服务 V8 可靠回写：事实源修改追溯回到 Git commit，不额外制造 YAML 第二事实源。
  - 服务 V6 强制验证：派生展示必须读取 Git 记录，避免用页面状态替代证据。

  ## 逆向价值

  - 逆向削弱 V2 完整理解和 V9 人类确认质量：Git 提交记录不是独立 YAML 实例，无法像工作对象一样通过对象文件承载补充字段。

  ## 实施成本

  - Code 和 Web 需要从 Git commit 派生提交记录展示，而不是读取 `ldvh-base/changes/`。

  ## 风险评估

  - 若派生逻辑缺失，Human 可能在 Web 中看不到完整提交记录。

  ## 注意事项

  - 对象不手写维护提交列表；Code/Web 派生输出不得替代 Git 事实源。
related_workareas: []
related_workcases: []
related_sparks: []
related_adrs: []
related_rules:
  - specs/10-Git提交规范.md
archive_reason:
deprecated_reason:
```

### 6.3 Human Gate 记录回写样例

ADR 创建、归档、废弃、核心决策改写或升级为规范时，Human Gate 记录可以摘要写入 `context`、`consequences`、`archive_reason`、`deprecated_reason`、相关 WorkCase / Spark 或 Git commit 证据中。若直接写入 ADR 字段，推荐使用以下文本块：

```yaml
context: |
  本 ADR 将改变 active 决策补丁的事实源承载方式，需 Human Gate。

  Human Gate 记录：
  - 触发原因：active ADR 的核心决策将被修改
  - 确认事项：是否接受新的决策内容并保留原 ADR 追溯
  - 影响范围：目标 ADR、相关规范、后续 WorkCase 和 Git 提交记录
  - 确认依据：原 ADR、影响范围说明和验证结果
  - Human 决策：确认修改
  - 确认人/时间：Human，2026-06-10
  - 后续动作：更新 ADR 字段并提交 Git commit
  - 验证方式：运行 ADR / specs 相关校验并检查 Git diff
  - 回写位置：本 ADR、相关 Git commit
  - 残留风险：后续 Web 展示需同步消费变更
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

ADR 回写遵循以下规则：

1. 创建 ADR 时，应写入 `ldvh-base/adrs/`，并填写背景、决策、后果和影响范围；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit 派生，不在 ADR YAML 中手写维护；
4. active ADR 的核心决策变更必须经 Human Gate，并通过 Git 提交记录留痕；
5. ADR 升级为规范或 Rules 后，应同步更新 `related_rules`；
6. ADR 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

ADR 证据至少包括：

1. 决策背景；
2. 决策内容；
3. 决策取舍说明；
4. 决策后果；
5. 影响范围；
6. Human Gate 确认记录；
7. 相关 Git 提交记录、WorkArea、WorkCase、Spark 或规范引用。

active ADR 的 `consequences` 字段必须按以下五段式记录影响闭环：

1. `## 正向价值`：依据 `specs/00-LD-Vibe-Harness理念与纲要.md` §4 的 V1-V10 价值标准说明决策为什么值得进入 ADR；
2. `## 逆向价值`：依据 `specs/00-LD-Vibe-Harness理念与纲要.md` §4 的 V1-V10 价值标准，说明决策成功生效后仍确定接受或长期承受的价值削弱、牺牲或折中；若不存在逆向价值，填写 `当前决策无逆向价值`；
3. `## 实施成本`：说明迁移、实现、维护、学习、Web 呈现、校验或协作成本；
4. `## 风险评估`：说明该决策可能造成的误判、事实源漂移、上下文过载、Human Gate 缺失、实现不一致或其他概率性风险；
5. `## 注意事项`：说明通过规范约束、Code 校验、Web 呈现、Human Gate、后续 WorkCase、降级策略或关联对象需要注意和托底的事项。

`## 逆向价值` 只记录相对 `specs/00-LD-Vibe-Harness理念与纲要.md` §4 的 V1-V10 价值判断中被削弱、牺牲或折中的部分，存在逆向价值时必须点名 `V1`-`V10` 中至少一项；不记录实施投入、迁移摩擦或概率性风险。

聊天内容、临时命令输出、Web 页面状态和工具缓存不得单独作为 ADR 证据。需要长期保留时，应摘要写入 ADR 字段或相关事实源。

---
## 8. 适配边界

### 8.1 AI 协作

AI 处理 ADR 时应遵守：

1. 先判断是否满足 ADR 准入条件，再提出创建建议；
2. `active` ADR 是 AI 和 Human 后续执行应优先参考的决策补丁；
3. `archived` ADR 只作为追溯依据，AI 默认不把它作为当前优先约束；
4. `deprecated` ADR 不得继续作为执行依据；
5. 创建、归档、废弃、核心决策改写、升级或删除 ADR 前评估 Human Gate；
6. 不得把 WorkCase 字段中的风险判断、依赖关系、产物引用或检查结果误升级为 ADR，除非满足本文准入条件。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 ADR YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `archive_reason`、`deprecated_reason`、`related_rules` 和对象引用；
5. 聚合 ADR 状态、关联对象和关联规范位置；
6. 检查 active ADR 的决策变更是否有 Git 提交记录和 Human Gate 记录。

Code 不得自行创建、归档、废弃或删除 ADR，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/adrs/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 ADR 状态、决策内容、关联对象、关联规范和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

ADR 详情页应采用固定阅读节点：“背景、决策、影响、关联”，节点交互和视觉层级与 Study、Pitfall 一致。`consequences` 只在“影响”节点内按 Markdown 分段展示，不拆成独立工作对象字段。

ADR 列表卡片只展示身份信息、完整标题、非活跃原因、更新时间、复制和进入入口，不展示摘要、影响范围、关联规范 chip、`context`、`decision` 或未采纳备选提示。列表卡片标题必须允许换行完整显示；非活跃原因必须完整显示但弱于标题，使用“弱圆点 + 原因标签”和弱阅读正文，不得用醒目外框、强竖线、标签 chip 或截断摘要表达。

ADR Web 不得展示或派生 `proposed`、`accepted`、`rejected`、`superseded`、`superseded_by`、`alternatives` 或 `affects` 等旧生命周期和旧字段语义。关联规范、工作域、工作项、火花、Git 提交记录和其他 ADR 应统一进入“关联”节点，不单独形成“承接”或“影响范围”节点。

Web 不得在页面状态、缓存或数据库中维护独立 ADR 权威状态。受控编辑 ADR 字段时，应调用 Code 校验和受控写入链路，并遵守 Human Gate。

### 8.4 工作流程与环境适配

ADR 创建、归档、废弃和升级为规范的具体行动流程由后续 40-59 工作流程规范定义。本文只定义 ADR 实例的事实规则和状态约束。

环境不支持完整引用校验、规范关联聚合或受控编辑时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | ADR 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、终态规则和事实源边界 | 05、03.03、本文、10、Human Gate | 工作模型治理 | 创建、修改、搬移、审计、归档或废弃 ADR 时 |
| 入口可见要求 | AI 处理长期决策、规范判断、事实源边界、方案取舍或执行约束时，应能定位本文 | 成员自描述、运行入口摘要、ADR 决策流程入口 | AI 执行入口提示 | 决策入口、规范升级、状态流转或字段契约变化时 |
| 确定性执行要求 | ADR 字段、状态、引用、文件命名、关联关系和条件必填应由 Code 校验或记录缺口 | `specs/07-Code确定性执行实现规范.md`、ADR 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、引用关系或相关规范路径变化时 |
| Human 交互要求 | ADR 创建、归档、废弃、核心决策改写和升级为规范应触发 Human Gate，并按 06 §6.3.1 留下最小证据记录 | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | ADR 规范变化后，应检查成员自描述、05.01、05.02、05.03、Git 提交记录、Code、Web、适配措施和相关工作流程是否需要同步 | 成员自描述检查、字段格式映射、Git 追溯、Code/Web 联动检查、人工降级检查 | 触发保障 | ADR 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

ADR 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 ADR |
| 事实源位置 | 实例路径符合 `ldvh-base/adrs/adr-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 执行依据 | 只有 active ADR 可作为当前优先决策补丁 |
| 终态处理 | archived、deprecated 不得重开 |
| 归档/废弃原因 | archived ADR 已填写 `archive_reason`；deprecated ADR 已填写 `deprecated_reason` |
| 规范边界 | ADR 不替代 specs 或 Rules / Instructions 正文 |
| Human Gate | §5 场景已完成确认并符合 06 §6.3.1，或记录降级 |
| Git 追溯 | ADR 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. ADR 校验 Code 待字段契约稳定后补齐正反样例；
2. ADR Web 展示和受控编辑入口待 Web 实现规划时补齐；
3. ADR 创建、归档、废弃和升级为规范的具体工作流程待 40-59 定义；
4. 是否需要 ADR 定期审查机制，待更多实例实践后评估。
