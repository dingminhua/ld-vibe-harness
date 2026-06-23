# Spark-火花

```yaml
v2_spec:
  spec_id: "20"
  spec_kind: "member_spec"
  title: "Spark-火花"
  status: "active"
  authority: "active"
  canonical_path: "specs/20-Spark-火花.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: "specs/02-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Spark / 火花事实模型的对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、实例写入与消费边界"
  scope: "所有接入 LDVH 且需要管理尚未计划化但有保留价值的输入、发现、提醒、问题、缺口、偏好和待消化议题的项目"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/02-事实模型基础规范.md"
  related_specs:
    - "specs/attachments/02.Att.01-字段注册表.md"
    - "specs/attachments/02.Att.02-成员身份字段表.md"
    - "specs/attachments/02.Att.03-成员主文件骨架模板.md"
    - "specs/attachments/02.Att.04-成员一致性辅助核对表.md"
    - "specs/attachments/02.Att.05-成员双读映射矩阵.md"
    - "specs/attachments/02.Att.06-字段矩阵诊断表.md"
    - "specs/07-事实源边界与Git追溯规范.md"
    - "specs/21-WorkCase-工作项.md"
    - "specs/22-ADR-决策.md"
    - "specs/23-Pitfall-踩坑经验.md"
    - "specs/24-Study-研究报告.md"
  migration_sources:
    - "history/specs-v1/20-Spark-火花.md"
  active_fact_source:
    - "specs/20-Spark-火花.md"
  code_consumption:
    - "v2_spec_metadata"
    - "fact_model_member_identity"
    - "fact_model_fields"
    - "fact_model_state_machine"
    - "fact_model_instance_checks"
  migration_status: "migrated"
```

```yaml
v2_fact_model_member:
  spec_id: "20"
  kind: "fact_model"
  name_en: "Spark"
  name_zh: "火花"
  collection_status: "active"
  canonical_path: "specs/20-Spark-火花.md"
  instance_root: "ldvh-base/sparks/"
  instance_carrier: "yaml"
  fact_source_anchor: "§5"
  schema_anchor: "§9"
  state_machine_anchor: "§6"
  human_gate_anchor: "§8"
  code_consumption:
    - "fields"
    - "state_machine"
    - "instance_checks"
```

> 文件状态：本文是 active 正式规范；正式规则以本文及其授权附件为准。

## 1. 本文解决的问题

本文定义 Spark / 火花作为事实模型成员时如何承载尚未计划化但有保留价值的信息，并说明这些信息如何在后续被分流、关联、废弃或保留为待处理入口。

本文解决：

1. 什么内容应进入 Spark，什么内容应直接处理、进入 WorkCase、ADR、Pitfall、Study、docs 或其它事实源；
2. Spark 实例的事实源位置、文件命名、编号和 active 事实源边界；
3. Spark 的对象状态、合法状态流转、终态规则和多线并行分流规则；
4. Spark 与 WorkCase、ADR、Pitfall、Study、docs、管辖项目配置和 Git commit records 的关系；
5. Spark 创建、分流、废弃、核心摘要修改和关键关联变化时的 Human Gate；
6. Spark 字段契约、条件必填、内容格式、证据留存和实例检查要求；
7. AI、Code、Web、知识地图和运行时扩展消费 Spark 时不得越过的事实源边界。

本文不定义 WorkCase、ADR、Pitfall 或 Study 的准入条件、字段契约和状态机；这些对象即使已有 v2 成员规范，在 Human 单篇确认和 active 切换前的历史默认入口为对应 v1 历史 成员主文件为准。本文也不扩展 Web 写入白名单、不定义 Code 输出 Schema、不定义行动编排执行步骤或 Git commit message 契约。

## 2. 上位依据

本文承接 `00-LDVH理念与价值标准.md`：

1. Spark 属于事实模型实践，用于让 AI 把有价值但尚未可执行、尚未可决策或尚未可沉淀为报告的输入对象化承载，减少聊天记忆和隐含上下文依赖；
2. Spark 必须服务 AI 第一服务对象，使 AI 能快速定位待分流议题、理解当前收敛状态、判断下一步事实源归口，并留下可追溯证据；
3. Spark 实例必须遵守事实源底层原则，稳定事实应进入 Git 可追踪文件，聊天、Web 页面状态、工具输出或派生索引不得替代实例事实源。

本文承接 `01-规范体系基础规范.md`：

1. 本文作为事实模型成员规范，必须具备 `v2_spec` 和 `v2_fact_model_member` 身份块；
2. 本文必须声明上位依据、构成要素归属与价值判断、规范保障要求、Human Gate 和待补齐事项；
3. 本文的成员身份、章节锚点、迁移来源和 active 事实源只作为 active 成员诊断输入，不改变实例事实源；
4. 迁移来源、Code 输出、Web 展示和过程讨论不得升级为 active 权威。

本文承接 `02-事实模型基础规范.md`：

1. Spark 必须在成员主文件中定义完整对象规则，包括对象定位、事实源边界、状态机、对象关系、Human Gate、字段契约、实例写入、消费边界和对象特有检查；
2. Spark 字段契约必须说明字段来源、含义、值形态、必填性、状态条件、内容格式、schema 归口和消费方；
3. 字段注册表只能辅助诊断公共字段和消费元数据，不能反向证明 Spark 采用某字段或改变 Spark 对象内 schema；
4. Spark 的正式事实模型以当前 active `specs/20-Spark-火花.md` 为准。

若本文与 00、01、02 或事实源边界规范冲突，不得自行选择覆盖；应记录为待核对事项并回到 Human Gate。

## 3. 构成要素归属与价值判断

### 3.1 构成要素归属

本文属于六类构成要素中的 `事实模型`。

| 项目 | 判断 |
|---|---|
| 主归属 | 事实模型 |
| 辅助服务对象 | 规范体系、行动编排、Code、Web 和运行时扩展都可消费 Spark 的成员身份、字段契约、状态机、对象关系、实例检查和待确认边界 |
| 不归属边界 | 本文不定义 WorkCase、ADR、Pitfall、Study 的完整规则；不定义行动编排流程、Code 输出 Schema、Web 页面契约、运行时扩展适配规则或 Git 提交格式 |

### 3.2 正向价值判断

本文至少服务以下价值标准：

| 价值标准 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过 `ldvh-base/sparks/`、成员身份块、状态枚举和关联字段，让 AI 快速定位待处理、已分流或已废弃的火花 |
| V2 可行动理解 | 通过 `description` 与 `evolution` 区分当前摘要和关键语义转折，让 AI 不依赖聊天记忆理解 Spark 的剩余议题 |
| V3 正确判断 | 通过准入条件、非准入内容和分流规则，降低 AI 误建 WorkCase、误建 ADR、误把 Study 当作完成分流的风险 |
| V4 稳定执行 | 通过状态机、条件必填和多线分流规则，使 Spark 创建、分流、废弃和关闭判断有稳定路径 |
| V5 门禁识别 | 通过 Human Gate 明确创建、分流、废弃、高影响字段修改和用 Spark 替代其它对象时的暂停边界 |
| V6 强制验证 | 通过字段契约、实例检查和 Code 可消费入口，为字段完整性、状态合法性、引用和 Web 写入白名单提供检查依据 |
| V7 证据沉淀 | 通过来源、优先级、关键演变、分流目标、废弃原因、Human Gate 记录和 Git 提交记录追溯保留证据 |
| V8 可靠回写 | 通过事实源边界和写入规则，约束稳定火花事实进入 Git 文件事实源 |
| V10 持续完善 | 通过 Spark 暂存待分流问题、缺口、经验线索和候选议题，把重复讨论和体系缺口保留为后续改进入口 |

### 3.3 逆向价值判断

本文必须避免以下反向风险：

| 反向风险 | 本文如何避免 |
|---|---|
| 用 Spark 长期替代 WorkCase 或 ADR | 准入条件要求 Spark 只承载未计划化、未决策化的信息；已有目标、验收标准或长期决策时应分流到对应对象 |
| 用 Spark 替代 Study 或复制报告正文 | Study 只通过 `related_studies` 关联；Spark 只记录报告对议题理解的关键影响，不复制报告全文 |
| 用关联字段伪装完成分流 | 多线并行或部分承接时必须保持 `pending`，只有剩余议题完整承接、明确废弃或无需继续跟踪后才可进入终态 |
| 用 Web 页面状态替代事实源 | Web 只能按白名单快速创建 pending Spark；创建后字段编辑、状态流转、分流、废弃和删除不得由 Web 直接执行 |
| 用派生索引或 Code 输出替代成员主文件 | Code、Web 和知识地图只作为诊断、展示或最小读取建议，不替代本文和实例文件 |
| 用 Spark 规避 Human Gate | 创建、分流、废弃、核心摘要和关键关联变化时必须评估 Human Gate |

## 4. 对象定位与准入条件

Spark / 火花承载尚未计划化但有保留价值的输入、发现、提醒、问题、缺口、偏好和待消化议题。Spark 的目标是降低误创建 WorkCase 或 ADR 的冲动，同时避免有价值的信息只留在聊天记忆中。

Spark 是分流前的工作对象。它可以后续转化或关联到 WorkCase、ADR、Pitfall、docs、管辖项目配置或其它事实源，但在转化前不替代这些对象的字段契约、状态机、验收规则或配置边界。

Spark 可以从一句话开始，随后逐步扩展和收敛。`description` 承载当前可读摘要，`evolution` 只记录关键语义转折、方向变化、阶段性收敛和重要分流，不记录逐条对话、完整报告正文或状态流转历史。完整研究报告由 Study 承载，状态流转历史由 Git 提交记录派生。

### 4.1 Spark 准入条件

一个信息单元满足以下条件之一时，应考虑形成 Spark：

1. 有保留价值，但尚未形成明确执行目标或验收标准；
2. 不满足 WorkCase 准入条件，但可能后续转为 WorkCase；
3. 不满足 ADR 准入条件，但属于可能影响后续判断的偏好、观察或临时判断；
4. 执行过程中发现问题、缺口、风险线索、资料线索或待讨论事项，尚未决定如何处理；
5. 不记录会导致后续遗忘、重复讨论或信息断裂；
6. 一个想法需要先暂存，后续可能通过讨论、AI 调研、Study 报告或 WorkCase 逐步收敛。

创建 Spark 前，AI 应说明保留原因、来源、优先级和后续可能分流方向，并按本文 §8 评估 Human Gate。

### 4.2 不应形成 Spark 的内容

以下内容通常不应单独形成 Spark：

1. 当前对话中可以直接处理的信息；
2. 已有明确目标和验收标准的工作，应创建 WorkCase 或写入现有对象；
3. 已经满足长期决策准入的判断，应创建 ADR；
4. 已经满足工作项准入的输入，应创建 WorkCase；
5. 纯闲聊、寒暄或无后续价值的信息；
6. 已由 Study、docs、sources 或现有对象完整承载的信息；
7. 完整调研报告正文，应形成 Study 或进入项目约定文档位置，而不是复制到 Spark。

## 5. 事实源边界

本文是 Spark 的 active 成员主文件。Spark 的正式事实模型以当前 active `specs/20-Spark-火花.md` 为准。

Spark 实例的权威事实源位置为：

```text
ldvh-base/sparks/spark-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Spark active 事实模型规范 | `specs/20-Spark-火花.md` |
| Spark v2 成员规范 | `specs/20-Spark-火花.md` |
| Spark 实例 | `ldvh-base/sparks/` |
| Spark 字段内容格式和公共字段语义 | 以 `specs/02-事实模型基础规范.md`、字段注册表和本文为准 |
| Spark 展示、聚合或查询结果 | Web、Code 或知识地图派生输出，不作为最终事实源 |

Spark 实例是项目事实源，不承载 Spark 事实模型规则。本文和 v1 历史 Spark 规范定义模型规则；实例只承载单个项目中的具体火花事实。

## 6. 状态机

### 6.1 标准状态

Spark 标准状态如下：

| 状态 | 含义 |
|---|---|
| `pending` | 待处理：已捕获，尚未决定是否分流、处理或废弃；或已被部分分流但仍存在未承接议题 |
| `resolved` | 已完整分流到 WorkCase、ADR、Pitfall、docs、管辖项目配置更新或其它非 Study 事实源，或已明确处理 |
| `discarded` | 已废弃：确认不再需要继续跟踪或作为分流入口 |

`resolved` 和 `discarded` 是稳定终态。终态 Spark 不得直接重开；如需重新处理，应新建 Spark，并在新 Spark 中引用原 Spark。

### 6.2 合法状态流转

```text
pending -> resolved
pending -> discarded
resolved -> discarded
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `pending` -> `resolved` | Spark 中仍有保留价值的内容已完整分流到目标事实源或已明确处理 | `resolved_to` 和 `resolved_at` 条件必填；Study 只作为 `related_studies` 关联，不作为 `resolved_to`；部分分流不得转为 `resolved` |
| `pending` -> `discarded` | 判断不需要继续处理 | 应记录 `discard_reason` |
| `resolved` -> `discarded` | 分流记录不再需要作为活跃入口展示 | 保留分流关系，并记录 `discard_reason` |

未列出的状态流转为非法流转。Code、Web、知识地图和运行时扩展不得绕过本文状态机直接修改状态。

## 7. 对象关系

### 7.1 Spark 与 WorkCase

Spark 可以分流为一个或多个 WorkCase，作为尚未计划化信息转化为可执行工作项的路径。

当 Spark 只被单个 WorkCase 完整承接时，Spark 的 `resolved_to` 应记录 `{type: workcase, ref: <WorkCase ID>}`，WorkCase 的 `source` 或 `related_sparks` 可记录 Spark ID 或路径。

当 Spark 被多个 WorkCase 并行或分阶段承接时，应先保持 `status: pending`，在 Spark 的 `related_workcases` 中记录已承接或相关的 WorkCase ID，并在 `evolution` 中说明每个 WorkCase 承接的议题范围、剩余未承接内容和下一步分流方向。只有当 Spark 的剩余议题已被完整承接、明确废弃或无需继续跟踪时，才可以进入 `resolved` 或 `discarded`。

WorkCase 的准入、状态和字段契约当前以 active `specs/21-WorkCase-工作项.md` 为准；`specs/21-WorkCase-工作项.md` 只作为active 成员规范。

### 7.2 Spark 与 ADR

Spark 可以分流为 ADR，作为临时判断、偏好或方案取舍转化为长期决策的路径。分流后，Spark 的 `resolved_to` 应记录 `{type: adr, ref: <ADR ID>}`，ADR 的 `related_sparks` 可记录来源 Spark。

ADR 的准入、状态和字段契约当前以 active `specs/22-ADR-决策.md` 为准；`specs/22-ADR-决策.md` 只作为active 成员规范。

### 7.3 Spark 与 Study

Spark 可以关联一个或多个 Study，用于承接 AI 调研、资料分析、事实核验或方案比较后的稳定报告。Spark 的 `related_studies` 记录 Study ID；Study 的 `related_sparks` 可反向记录来源或关联 Spark。

Spark 只保留报告对议题演变产生的关键影响，不复制报告全文。Study 是报告承载，不是讨论入口、执行承接或决策承接。将完整报告提炼为 Study 时，应更新 `related_studies` 和 `evolution`；除非 Spark 的剩余议题已经被 WorkCase、ADR、Pitfall、docs、管辖项目配置更新或其它非 Study 事实源完整承接，否则不得仅因形成 Study 就把 Spark 标记为 `resolved`。

Study 的准入、状态和字段契约当前以 active `specs/24-Study-研究报告.md` 为准；`specs/24-Study-研究报告.md` 只作为active 成员规范。

### 7.4 Spark 与 Pitfall、管辖项目配置、docs

Spark 可以分流或关联到 Pitfall、管辖项目配置或 docs：

1. 已解决且有复用价值的踩坑经验线索，可转为 Pitfall；
2. 项目路径或管辖项目清单线索，可转为工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 更新建议或项目文档更新建议；
3. 项目正文、说明或短结论，可吸收到 docs；
4. 稳定调研、分析或报告内容，应优先形成或关联 Study；这只表示报告正文已有承载，不等同于 Spark 已完成分流；
5. 外部引用或调研资料，应进入 docs/sources。

Pitfall 的准入、状态和字段契约当前以 active `specs/23-Pitfall-踩坑经验.md` 为准；`specs/23-Pitfall-踩坑经验.md` 只作为active 成员规范。管辖项目配置不是工作对象，不进入 `ldvh-base/`；环境能力核验、环境适配和适配措施正文不得写入管辖项目配置。

### 7.5 多线并行分流

一个 Spark 可以承载同一讨论中产生的多个相关缺口、问题或后续方向。只要这些内容尚未形成各自独立的稳定事实源入口，允许暂时保留在同一个 Spark 中；一旦某个方向具备独立目标、成功标准、决策判断或长期跟踪价值，应分流到 WorkCase、ADR、Pitfall、docs、管辖项目配置更新或其它事实源。

多线并行分流遵守以下规则：

1. `related_workcases`、`related_adrs`、`related_studies` 和 `related_docs` 可以记录多个关联对象，用于表达并行承接、分阶段承接或主题相关；
2. 关联字段不等同于完成分流。Spark 仍存在未承接议题时必须保持 `pending`；
3. `evolution` 应记录每条线的承接范围、当前判断和剩余问题，避免后续 AI 只看到关联对象却不知道 Spark 是否已经收敛；
4. `resolved_to` 是单一最终分流目标或主承接目标，不用于记录多个并列目标；若没有单一主目标，应继续使用 `related_*` 与 `evolution` 表达多线承接状态；
5. 当多个关联对象共同完整承接 Spark 时，应在 `evolution` 中说明完整承接判断，再选择最能代表关闭判断的主目标写入 `resolved_to`，或在经 Human Gate 确认后使用 `{type: other, ref: <说明性引用>}` 表达由多对象共同承接的关闭判断；
6. 如果多线内容已经彼此独立且继续放在同一个 Spark 会削弱恢复和关闭判断，应创建新的 Spark 或 WorkCase，并通过 `description`、`evolution` 或目标对象 `related_sparks` 保留追溯关系。

### 7.6 Spark 与 Git 提交记录

Spark 的创建、状态变化、分流和废弃都应留下 Git 提交记录。Git 提交记录用于追溯事实源修改，不作为 Spark 字段手写维护。

## 8. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Spark 实例；
2. 将对话输入、docs/studies 结论或执行发现写入 Spark；
3. 将 `pending` Spark 分流为 WorkCase、ADR、Pitfall、docs、管辖项目配置更新或其它事实源；
4. 将 Spark 标记为 `discarded`，且废弃会丢失后续跟踪入口；
5. 将 Spark 从单线分流改为多线并行分流，或将多个并行承接对象判断为已经共同完整承接；
6. 修改 `resolved_to`、`priority`、`description`、`evolution` 或关键关联；
7. 将 Spark 作为规避 WorkCase 或 ADR 准入判断的长期替代物。

Human Gate 的具体环境实体由后续运行时扩展、Web、行动编排或当前对话确认承接。本文只规定 Spark 语境下需要确认的事实和影响范围。Human Gate 记录进入 Spark 字段时，应至少说明确认时间、确认主体、确认事项、确认结论、确认范围、约束条件和后续责任。

## 9. 字段契约

### 9.1 字段契约表

Spark 字段契约如下。字段注册表只提供公共语义和消费诊断辅助；Spark 是否采用字段、字段是否必填、状态条件和对象内 schema 以本节为准。

| 字段名或路径 | 字段来源 | 字段含义 | 值形态 | 是否必填 | 状态条件 | 内容格式 | schema 归口 | 消费方 |
|---|---|---|---|---|---|---|---|---|
| `id` | 模型身份基线字段 | Spark 实例唯一标识，格式为 `spark-{NNNN}`，必须与文件编号一致 | string | 必填 | 所有状态必须存在 | reference | 20 | AI、Code、Web、知识地图 |
| `type` | 模型身份基线字段 | 固定为 `spark` | string | 必填 | 所有状态必须为 `spark` | reference | 20 | AI、Code、Web、知识地图 |
| `title` | 模型身份基线字段 | 火花一句话概括 | string | 必填 | 所有状态必须存在，应简短可读 | narrative | 20 | AI、Web |
| `status` | 模型身份基线字段 | 当前对象状态 | string | 必填 | 必须属于 §6.1 状态枚举 | reference | 20 | AI、Code、Web、知识地图 |
| `created` | 模型身份基线字段 | 创建时间 | datetime | 必填 | ISO 8601 时间戳，至少包含日期、小时和分钟 | reference | 02、20 | AI、Code、Web |
| `updated` | 模型身份基线字段 | 最近更新时间 | datetime | 必填 | 每次事实源更新时同步，ISO 8601 时间戳 | reference | 02、20 | AI、Code、Web |
| `description` | 公共字段，Spark 采用 | 当前可读摘要、问题焦点和阶段性收敛方向 | markdown | 必填 | 所有状态必须存在；不写完整报告正文或流水账 | narrative | 20 | AI、Web |
| `evolution` | 公共字段，Spark 采用 | 关键语义转折、方向变化、阶段性收敛和重要分流 | list_object | 可选 | 默认空列表；元素至少包含 `at` 和 `summary`；不得作为手写状态历史 | log | 20 | AI、Code、Web |
| `evolution.at` | Spark 嵌套字段 | 语义转折发生或记录时间 | datetime | 条件必填 | `evolution` 条目存在时必须存在，使用 ISO 8601 时间戳 | reference | 20 | AI、Code、Web |
| `evolution.summary` | Spark 嵌套字段 | 语义转折摘要 | markdown | 条件必填 | `evolution` 条目存在时必须存在，只写关键变化 | log / narrative | 20 | AI、Code、Web |
| `source` | 公共字段，Spark 采用 | 火花进入事实源的入口来源 | string | 必填 | 只能是 `web` 或 `conversation`；Web 快速创建固定为 `web`，对话整理固定为 `conversation` | reference | 20 | AI、Code、Web |
| `source_detail` | 公共字段，Spark 采用 | 来源说明、触发场景或原始输入摘要 | markdown | 可选 | 可为空；不承载一般关联清单 | narrative / reference | 20 | AI、Web |
| `priority` | 公共字段，Spark 采用 | 优先级，回答哪个火花应先处理 | string | 必填 | 必须是 `P0`、`P1`、`P2` 或 `P3`；判断标准承接 02 | reference | 02、20 | AI、Code、Web |
| `resolved_to` | Spark 模型特有字段，兼容公共字段语义 | 单一最终分流目标或主承接目标引用 | object | 条件必填 | `status: resolved` 时必须填写；`pending` 时不得用于伪装完整收敛；`discarded` 如来自 resolved 可保留原分流关系 | structured / reference | 20 | AI、Code、Web |
| `resolved_to.type` | Spark 嵌套字段 | 非 Study 分流目标类型 | string | 条件必填 | `resolved_to` 存在时必须存在；只能是 `workcase`、`adr`、`pitfall`、`docs`、`governed-projects` 或 `other`，不得为 `study` | reference | 20 | AI、Code、Web |
| `resolved_to.ref` | Spark 嵌套字段 | 分流目标引用 | string | 条件必填 | `resolved_to` 存在时必须存在；填写对象 ID、文档路径、管辖项目配置引用或说明性引用 | reference | 20 | AI、Code、Web |
| `resolved_at` | Spark 模型特有字段 | 完整分流日期 | date | 条件必填 | `status: resolved` 时必须填写；格式为 `YYYY-MM-DD` | reference | 20 | AI、Code、Web |
| `discard_reason` | 公共字段，Spark 采用 | 废弃原因 | markdown | 条件必填 | `status: discarded` 时必须填写；不得只写已废弃 | narrative | 20 | AI、Human |
| `related_adrs` | 公共字段，Spark 采用 | 关联 ADR | list_string | 可选 | 默认为空列表；用于关联或并行承接，不表示完成分流 | reference | 20 | AI、Code、Web |
| `related_studies` | 公共字段，Spark 采用 | 关联 Study | list_string | 可选 | 默认为空列表；Study 不得写入 `resolved_to` | reference | 20 | AI、Code、Web |
| `related_workcases` | 公共字段，Spark 采用 | 关联 WorkCase | list_string | 可选 | 默认为空列表；可记录多个并行承接、分阶段承接或主题相关的 WorkCase ID，不表示 Spark 已 resolved | reference | 20 | AI、Code、Web |
| `related_docs` | 公共字段，Spark 采用 | 关联文档路径 | list_string | 可选 | 默认为空列表；用于 docs、sources 或其它项目文档路径，不承载对象 ID | reference | 20 | AI、Code、Web |

### 9.2 字段写入约束

Spark 字段写入遵循以下规则：

1. `description` 应使用 YAML 块标量，写当前摘要、问题焦点和收敛方向；
2. `evolution` 只记录关键语义转折、方向变化、阶段性收敛和重要分流，不记录逐条对话、完整报告正文或状态流转历史；
3. `created`、`updated` 和 `evolution.at` 必须使用 datetime；`resolved_at` 是 date；
4. `priority` 只用于执行调度顺序、价值判断和保留意义判断，不得改名为 `importance`；
5. `resolved_to` 保留 active Spark 的 `{type, ref}` 对象结构；公共字段注册摘要中的通用 `resolved_to` 形态不得反向改变 Spark 对象内 schema；
6. `resolved_to.type` 不得为 `study`；Study 只通过 `related_studies` 关联；
7. 关联字段不等同于完成分流，仍存在未承接议题时必须保持 `pending`；
8. Spark 不得手写维护 `status_history`；状态变化历史由 Git 提交记录派生。

## 10. 事实实例写入、回写、验证和证据留存

### 10.1 写入与回写规则

Spark 写入遵循以下规则：

1. 创建 Spark 时，应写入 `ldvh-base/sparks/`，并填写标题、当前摘要、来源类型、优先级和状态；
2. 创建前应说明保留原因、来源、优先级和后续可能分流方向；
3. 状态变化前应检查合法流转、条件必填和 Human Gate；
4. 状态变化后应更新 `updated`；状态变化历史由 Git 提交记录派生，不在 Spark YAML 中手写维护；
5. Spark 出现关键语义转折、方向变化或阶段性收敛时，应更新 `description` 并向 `evolution` 追加摘要；
6. Spark 被单一目标完整分流为 WorkCase、ADR、Pitfall、docs、管辖项目配置更新或其它非 Study 事实源时，应更新 `resolved_to` 和 `resolved_at`；
7. Spark 被多个目标并行或分阶段承接时，应先更新对应 `related_*` 字段和必要的 `evolution`，并保持 `pending`；
8. 形成或引用 Study 时只更新 `related_studies` 和必要的 `evolution`；
9. Spark 创建、分流、废弃、关键关联变化、核心摘要或演变记录修改应通过 Git 提交记录留痕；
10. Spark 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 10.2 证据留存

Spark 证据至少包括：

1. 创建原因和来源；
2. 优先级；
3. 当前摘要和关键语义转折；
4. 分流目标或废弃原因；
5. Human Gate 确认记录；
6. 相关 WorkCase、ADR、Study、Git 提交记录或文档引用。

Spark 的分流证据应保留摘要和目标引用，不复制目标对象全文。聊天、临时分析、命令输出、Web 页面状态和工具报告只有按事实类型写入 Spark 或对应事实源后，才形成可复查证据。

## 11. Code、Web、知识地图和运行时扩展消费边界

### 11.1 AI 协作

AI 处理 Spark 时应遵守：

1. 先判断信息是否满足 Spark 准入条件；
2. 创建、分流、废弃或删除 Spark 前评估 Human Gate；
3. 不得用 Spark 长期替代已经满足准入条件的 WorkCase 或 ADR；
4. 分流时说明为什么目标类型合适；
5. 多线并行分流时，说明每条线为什么可以并行、由哪个对象承接、剩余未承接内容是什么；
6. 分流后不在 Spark 中维护目标对象的状态、验收或决策正文；
7. 有完整报告时应形成或关联 Study，Spark 只记录报告如何改变议题理解；
8. 不得把 Study 写入 `resolved_to`。

### 11.2 Code 消费边界

Code 可依据本文和 active Spark 规范实现或诊断以下能力：

1. 解析 Spark YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `source`、`priority`、`evolution`、`resolved_to` 和引用字段；
5. 聚合待处理 Spark、已分流 Spark、已废弃 Spark、分流目标和已有关联对象但仍 `pending` 的多线分流 Spark；
6. 在 v2 双读期间核对 历史 `ldvh_member` 与 active `v2_fact_model_member` 的编号、路径、实例目录、锚点和 Code 消费入口。

Code 不得自行创建、分流、废弃或删除 Spark，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/sparks/` 权威事实源。Code 默认校验应回到 active `specs/20-Spark-火花.md` 和现有实现。

### 11.3 Web 消费边界

Web 可展示 Spark 状态、优先级、来源类型、来源说明、关键演变、分流目标、废弃原因和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

当前唯一允许的 Spark Web 写入是快速创建：Web 可创建 `status: pending` 的新 Spark，并写入 `title`、`description` 和 `priority`。Web 创建时 `source` 固定写入 `web`；对话中创建或由 AI 根据对话整理的 Spark 固定写入 `conversation`。

Web 不得在页面状态、缓存或数据库中维护独立 Spark 权威状态。Spark 创建后的字段编辑、状态流转、分流、废弃和删除不得通过 Web 直接执行；如未来需要开放，必须先更新对应 Web 写入白名单、本文字段和状态约束、Code 校验、测试和 Human Gate 影响评估。

### 11.4 知识地图和运行时扩展消费边界

知识地图可以消费 Spark 成员身份、章节锚点、字段契约、状态机、对象关系、实例事实源目录和 active 事实源回指，生成定位、最小读取、影响判断和诊断提示。知识地图输出不得替代本文、v1 历史 Spark 规范或 Spark 实例文件。

运行时扩展可以提供入口可见、读取顺序、流程复用、Agent 调度、工具调用和环境适配提示。运行时扩展承载物不得复制 Spark 完整字段契约、状态机、关闭条件或 Human Gate 细则；需要摘要时必须回指本文、active Spark 规范和对应实例事实源。

## 12. 规范保障要求

本文自身保障要求如下：

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Spark 实例和后续行动编排应遵守本文定义的准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、分流规则和证据要求 | 本文、active `specs/20-Spark-火花.md`、v2 02、Human Gate；行动编排未接管前为人工降级检查 | 事实模型治理 | 创建、修改、迁移、审计、分流或废弃 Spark 时 |
| 入口可见要求 | AI 处理未计划化但有保留价值的信息、发现、提醒、问题或缺口时，应能定位 Spark active 规范、本文和对应实例事实源 | `specs/README.md`、02 成员身份、知识地图输入、运行时入口；行动编排未接管前为人工降级检查 | AI 执行入口 | Spark 入口、成员身份、实例目录或读取顺序变化时 |
| 确定性执行要求 | Code 应能检查 Spark 文件命名、字段完整性、状态枚举、合法流转、来源枚举、优先级、`resolved_to` 结构、Study 分流禁用、引用和 Web 快速创建边界 | 现有 active Code、`02.Att.04`、`02.Att.05`、`02.Att.06`、人工降级检查；v2 双读实现和测试仍待后续 Code 规范承接 | Code 校验 | 字段契约、状态机、分流规则、实例目录、Web 写入白名单或 Code 消费入口变化时 |
| Human 交互要求 | Spark 创建、分流、废弃、核心摘要修改、演变记录修改和用 Spark 规避对象准入时应评估 Human Gate | Human Gate、影响范围说明、确认记录；建议由事实模型审核或后续 Spark 行动编排接管 | Human Gate | §8 中任一场景发生时 |
| 生命周期触发要求 | Spark 规范变化后，应检查 02 字段注册、字段矩阵、WorkCase、ADR、Pitfall、Study、Code、Web、运行时扩展、行动编排和待补齐事项是否需要同步 | 本文、02 授权附件、active 20-24、Code 诊断、人工降级检查；建议由规范生命周期同步行动编排接管 | 生命周期同步 | Spark 字段、状态、事实源边界、对象关系、适配规则或检查要求变化时 |
| 工作流程接管要求 | Spark 创建、分流、废弃和多线并行收敛反复发生时，应由后续行动编排接管读取、判断、验证、证据、Human Gate、缺口分流和同步责任 | 行动编排未接管前为人工降级检查；建议建立或复用 Spark 创建、分流和废弃相关行动编排，行动编排未 active 前不得声称已接管 | 行动编排治理 | Spark 生命周期操作高频发生，或 Web / Code 受控写入能力扩展时 |

## 13. 对象特有实例检查

Spark 实例检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Spark |
| 文件命名 | 实例路径符合 `ldvh-base/sparks/spark-{NNNN}-short-title.yaml`，`id` 与编号一致 |
| 字段完整性 | 必填字段、条件必填字段、字段类型和值形态符合 §9 |
| 状态合法性 | `status` 属于 §6.1 状态枚举，状态流转符合 §6.2 |
| 来源枚举 | `source` 为 `web` 或 `conversation`，且与创建入口一致 |
| 优先级 | `priority` 为 `P0`、`P1`、`P2` 或 `P3` |
| 演变承载 | `description` 是当前摘要，`evolution` 只记录关键语义转折，不记录流水账或状态历史 |
| 分流规则 | `resolved` Spark 已填写 `resolved_to` 和 `resolved_at`，且 `resolved_to.type` 不是 `study` |
| 废弃规则 | `discarded` Spark 已说明 `discard_reason` |
| 多线分流 | 有多个关联对象但仍有未承接议题时保持 `pending`，并在 `evolution` 说明剩余问题 |
| 对象边界 | Spark 未长期替代 WorkCase、ADR、Pitfall 或 Study |
| Human Gate | §8 场景已完成确认或记录降级 |
| Git 追溯 | Spark 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源，Web 未越过快速创建白名单 |

## 14. 待补齐事项

1. 本文只处理 20-Spark 草案；21-WorkCase、22-ADR、23-Pitfall 和 24-Study 已另行写入 `specs/` 根目录成员规范，但相关对象规则在 Human 单篇确认和 active 切换前的历史默认入口为 v1 历史 成员主文件为准；
2. v2 字段注册表尚未全量迁入对象特有字段。`resolved_to`、`resolved_to.type`、`resolved_to.ref`、`resolved_at`、`evolution` 和 Spark 关联字段应在后续字段矩阵诊断中与 active 05.03 和本文字段契约逐项核对；
3. 历史 `ldvh_member` 与 active `v2_fact_model_member` 的双读 Code 实现、正反样例和切换策略尚未完成；本文提供 active 成员规范输入；Code 默认消费入口应按 v2 身份块切换；
4. Spark Web 快速创建白名单应在 v2 Web 规范和 Code 实现迁移时复核。本文不扩展 Web 创建后编辑、分流、废弃或删除能力；
5. Spark 创建、分流、废弃、多线并行收敛和 Human Gate 记录的具体行动编排不按 v1 直接迁入；应待 v2 保障需求稳定后进入行动编排候选计划；
6. 后续修改本文时，应再次核对 active `specs/20-Spark-火花.md`、02 授权附件、现有 Code/Web 测试和相关 active 20-24 成员规则，确认没有字段、状态、引用或消费入口漂移。
