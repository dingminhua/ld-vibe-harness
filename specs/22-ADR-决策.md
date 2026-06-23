# ADR-决策

```yaml
v2_spec:
  spec_id: "22"
  spec_kind: "member_spec"
  title: "ADR-决策"
  status: "active"
  authority: "active"
  canonical_path: "specs/22-ADR-决策.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: "specs/02-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 ADR / 决策事实模型的对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、实例写入与消费边界"
  scope: "所有接入 LDVH 且需要管理长期决策、事实源边界、规范判断和后续执行约束的项目"
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
    - "specs/07-事实源边界与Git追溯规范.md"
    - "specs/20-Spark-火花.md"
    - "specs/21-WorkCase-工作项.md"
  migration_sources:
    - "history/specs-v1/22-ADR-决策.md"
  active_fact_source:
    - "specs/22-ADR-决策.md"
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
  spec_id: "22"
  kind: "fact_model"
  name_en: "ADR"
  name_zh: "决策"
  collection_status: "active"
  canonical_path: "specs/22-ADR-决策.md"
  instance_root: "ldvh-base/adrs/"
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

本文定义 ADR / 决策如何承载已经确认但尚未完全吸收到 specs、Rules、Skills、Agents、行动编排或适配措施中的决策补丁，并在吸收完成前约束后续 AI 和 Human 行动。

本文解决：

1. 什么判断应进入 ADR，什么判断应留在 WorkCase、Spark、Study、docs 或当前上下文；
2. ADR 的事实源位置、状态机、终态和规范吸收边界；
3. ADR 与 WorkCase、Spark、规范、Rules、Git commit records 的关系；
4. ADR 创建、归档、废弃、核心决策改写和升级为规范时的 Human Gate；
5. ADR 字段契约、影响闭环五段式、Human Gate 记录回写和实例检查要求。

本文不定义正式规范正文、Rules 执行入口、行动编排流程、Code 输出 Schema、Web 页面契约或 Git commit message 契约。

## 2. 上位依据

本文承接 `00-LDVH理念与价值标准.md`：ADR 通过保存长期决策、取舍依据、影响范围和注意事项，减少 AI 重复争论、规则漂移和长期执行失据。

本文承接 `01-规范体系基础规范.md`：本文是事实模型成员规范，必须声明成员身份、迁移来源、active 事实源、价值判断、保障要求、Human Gate 和待补齐事项。

本文承接 `02-事实模型基础规范.md`：ADR 必须在自身主文件定义状态机、字段契约、事实源边界和实例检查；字段注册表不得反向改变 ADR schema。

若本文与 active `specs/22-ADR-决策.md`、v2 00、v2 01 或 v2 02 冲突，应按上位依据、事实源边界和 Human Gate 处理，不得由局部段落自行覆盖。

## 3. 构成要素归属与价值判断

### 3.1 构成要素归属

本文属于六类构成要素中的 `事实模型`。

| 项目 | 判断 |
|---|---|
| 主归属 | 事实模型 |
| 辅助服务对象 | 规范体系、行动编排、Code、Web 和运行时扩展可消费 ADR 的状态、决策内容、关联规则、影响闭环和 Human Gate 证据 |
| 不归属边界 | 不定义正式规范规则、行动流程、Code 输出 Schema、Web 页面契约或 Git 提交格式 |

### 3.2 正向价值判断

| 价值标准 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过 `ldvh-base/adrs/`、状态和关联规则定位当前决策补丁 |
| V2 可行动理解 | 通过 `context`、`decision` 和 `consequences` 让 AI 理解决策背景、选择和影响 |
| V3 正确判断 | 通过准入条件和规范边界避免把一次性执行策略或未确认讨论误升级为 ADR |
| V4 稳定执行 | 通过 active ADR 约束后续执行，直到稳定承载吸收 |
| V5 门禁识别 | 创建、归档、废弃、核心决策改写和升级为规范时触发 Human Gate |
| V6 强制验证 | 通过状态、条件必填、影响闭环、Human Gate 记录和引用关系提供检查入口 |
| V7 证据沉淀 | 保留决策背景、取舍依据、影响、Human Gate 和 Git 追溯 |
| V8 可靠回写 | 决策补丁写入 ADR，稳定规则吸收到对应规范或入口 |
| V10 持续完善 | 决策被吸收、归档或废弃时触发相关规范、Code、Web 和行动编排同步 |

### 3.3 逆向价值判断

| 反向风险 | 本文如何避免 |
|---|---|
| 用 ADR 替代正式规范 | ADR 只记录决策补丁；长期规则应吸收到对应正式规范或入口 |
| 把未确认讨论写成决策 | 准入条件要求已确认、需持续约束、存在明确取舍 |
| 删除历史决策导致失去追溯 | 推翻或替代原决策时使用 `archived` 或 `deprecated`，不得删除原 ADR 文件 |
| 用旧生命周期字段制造漂移 | 不使用 `proposed`、`accepted`、`rejected`、`superseded` 等旧状态 |
| 用 Web 状态替代事实源 | Web 只展示或受控编辑，不能维护独立 ADR 权威状态 |

## 4. 对象定位与准入条件

ADR / 决策是已确认但尚未完全吸收到 specs、Rules、Skills、Agents、行动编排或适配措施中的决策补丁，用于在稳定吸收完成前约束 AI 和 Human 的后续行动，并保留为什么这样决定的追溯依据。

ADR 不是所有判断或提案的默认归宿。AI 可以在当前任务中做临时判断、记录分析结论或选择局部执行策略；未确认、未采纳或尚在讨论的内容应留在 Spark、WorkCase 或 Study 中。

### 4.1 ADR 准入条件

一个判断满足以下条件之一时，应考虑形成 ADR：

1. 影响多个 WorkCase、事实模型、行动编排或项目阶段；
2. 改变长期执行方式、协作方式、事实源归属或 Human Gate 边界；
3. 改变 specs、Rules、Skills、Agents 或适配措施的长期规则；
4. 对后续 AI 或 Human 执行具有持续约束；
5. 多次重复出现，需要稳定记录选择理由；
6. 存在明确取舍且已形成确认结论；
7. 不记录会导致后续重复争论、误读或规则漂移。

创建 ADR 前，AI 必须说明准入理由、决策问题、建议结论、影响范围和预期回写位置，并按本文 §8 评估 Human Gate。

### 4.2 不应形成 ADR 的内容

以下内容通常不应单独形成 ADR：

1. 当前 WorkCase 内的一次性执行策略；
2. 不影响后续协作的局部技术选择；
3. 尚未稳定或尚未确认的讨论、想法、提案或资料；
4. 已由 specs、Rules 或其他正式规范明确约束的重复判断；
5. 仅属于风险判断、依赖关系、产物引用或检查结果的字段内容。

未采纳的候选方案不得写入 ADR 字段作为并行决策；可留在 Spark、Study、WorkCase 上下文或当前讨论记录中。ADR 只记录已形成长期执行约束的决策补丁及其取舍后果。

### 4.3 ADR 与规范的边界

ADR 记录决策补丁的背景、原因、选择和后果；正式规范记录稳定规则。ADR 不替代 specs 正文、Rules 执行入口、事实模型字段契约或行动编排规则。

当 ADR 中的决策需要成为长期规则时，应把规则正文吸收到对应正式规范或运行入口。吸收完成后，ADR 应转为 `archived`，只保留决策原因、归档原因和追溯关系；未吸收完成前保持 `active`。

## 5. 事实源边界

ADR 实例的权威事实源位置为：

```text
ldvh-base/adrs/adr-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| ADR active 事实模型规范 | `specs/22-ADR-决策.md` |
| ADR v2 成员规范 | `specs/22-ADR-决策.md` |
| ADR 实例 | `ldvh-base/adrs/` |
| ADR 字段内容格式和公共字段语义 | 以 `specs/02-事实模型基础规范.md`、字段注册表和本文为准 |
| ADR 展示、聚合或查询结果 | Web、Code 或知识地图派生输出，不作为最终事实源 |

## 6. 状态机

### 6.1 标准状态

| 状态 | 含义 |
|---|---|
| `active` | 决策补丁仍有效，AI 和 Human 应优先参考 |
| `archived` | 决策补丁已被 specs、Rules、Skills、Agents 或行动编排等稳定承载吸收，ADR 只保留追溯 |
| `deprecated` | 决策补丁已废弃，不得继续作为执行依据 |

`archived` 和 `deprecated` 是稳定终态。终态 ADR 不得直接重开；如需重新判断，应新建 ADR 或修改对应稳定承载，并在新事实源中引用原 ADR。

### 6.2 合法状态流转

```text
active -> archived
active -> deprecated
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` -> `archived` | 决策补丁已被稳定承载吸收 | `archive_reason` 条件必填，应说明吸收位置和归档依据 |
| `active` -> `deprecated` | 决策补丁不再适用或方向被放弃 | `deprecated_reason` 条件必填，应说明废弃原因和不得继续作为依据的边界 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

## 7. 对象关系

### 7.1 ADR 与 WorkCase

WorkCase 执行过程中产生的判断满足 ADR 准入条件时，可升级为 ADR。ADR 可通过 `related_workcases` 引用来源 WorkCase。ADR 不替代 WorkCase 的成功标准、验证证据、风险判断或关闭证据。

### 7.2 ADR 与 Spark

Spark 中的输入满足 ADR 准入条件后，可以转化为 ADR。转化时应保留 Spark 与 ADR 的引用关系，说明为什么从未计划化输入升级为长期决策，评估 Human Gate，并且不在 ADR 中复制 Spark 全文。

### 7.3 ADR 与 specs / Rules

ADR 中的决策补丁升级为稳定规则时，应将规则正文写入对应 specs 正式规范、Rules 或其它权威入口，在 `related_rules` 或其它关联字段中记录追溯关系，并通过 Git commit records 留下变更追溯。

### 7.4 ADR 与 Git 提交记录

ADR 的创建、状态变化、核心决策改写、归档、废弃和升级为规范时，都应留下 Git commit records。Git 提交记录用于追溯事实源修改，不作为 ADR 字段手写维护。

## 8. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 ADR 实例；
2. 将 Spark、WorkCase 过程判断、临时讨论或 docs/studies 结论升级为 ADR；
3. 创建 `active` ADR；
4. 将 `active` ADR 标记为 `archived` 或 `deprecated`；
5. 修改 `active` ADR 的 `decision` 字段；
6. 将 ADR 决策升级为 specs、Rules、Skills、Agents 或适配措施规则；
7. 改变 ADR 的事实源载体、状态机、升级路径或终态语义；
8. 删除原 ADR 而不是通过状态表达废弃或替代。

ADR 语境下的 Human Gate 记录至少应说明目标 ADR、决策变化、影响范围、确认依据、Human 决策、后续回写位置和残留风险。确认记录可以摘要写入 ADR 的 `context`、`consequences`、`archive_reason`、`deprecated_reason`、相关 WorkCase / Spark 或 Git commit 证据中，但不得只停留在对话结论里，不得维护手写 `status_history`。

## 9. 字段契约

| 字段名或路径 | 字段来源 | 字段含义 | 值形态 | 是否必填 | 状态条件 | 内容格式 | schema 归口 | 消费方 |
|---|---|---|---|---|---|---|---|---|
| `id` | 模型身份基线字段 | ADR 实例唯一标识，格式为 `adr-{NNNN}` | string | 必填 | 与文件编号一致 | reference | 22 | AI、Code、Web |
| `type` | 模型身份基线字段 | 固定为 `adr` | string | 必填 | 所有状态必须为 `adr` | reference | 22 | AI、Code、Web |
| `title` | 模型身份基线字段 | 决策一句话概括 | string | 必填 | 应简短可读 | narrative | 22 | AI、Web |
| `status` | 模型身份基线字段 | 当前 ADR 状态 | string | 必填 | 必须属于 `active`、`archived`、`deprecated` | reference | 22 | AI、Code、Web |
| `created` | 模型身份基线字段 | 创建时间 | datetime | 必填 | ISO 8601 时间戳 | reference | 02、22 | AI、Code、Web |
| `updated` | 模型身份基线字段 | 最近更新时间 | datetime | 必填 | 每次事实源更新时同步 | reference | 02、22 | AI、Code、Web |
| `date` | ADR 模型特有字段 | 决策确认日期 | date | 必填 | `YYYY-MM-DD` | reference | 22 | AI、Web |
| `context` | 公共字段，ADR 采用 | 决策背景、问题和来源 | markdown | 必填 | 使用 YAML 块标量 | narrative | 22 | AI、Web |
| `decision` | 公共字段，ADR 采用 | 决策补丁内容 | markdown | 必填 | `active` 后核心内容变更需 Human Gate | decision | 22 | AI、Human、Web |
| `consequences` | 公共字段，ADR 采用 | 决策影响闭环 | markdown | 必填 | active ADR 必须按五段式书写 | decision / narrative | 22 | AI、Code、Web |
| `related_workcases` | 公共字段，ADR 采用 | 关联 WorkCase | list_string | 可选 | 默认为空列表 | reference | 22 | AI、Code、Web |
| `related_sparks` | 公共字段，ADR 采用 | 来源或关联 Spark | list_string | 可选 | 默认为空列表 | reference | 22 | AI、Code、Web |
| `related_adrs` | 公共字段，ADR 采用 | 关联 ADR | list_string | 可选 | 默认为空列表 | reference | 22 | AI、Code、Web |
| `related_rules` | 公共字段，ADR 采用 | 关联规范、Rules、Skill、Agent、Code 或 Web 路径 | list_string | 可选 | 默认为空列表 | reference | 22 | AI、Code、Web |
| `archive_reason` | 公共字段，ADR 采用 | 归档原因和吸收位置 | markdown | 条件必填 | `status: archived` 时必须填写 | narrative | 22 | AI、Code、Web |
| `deprecated_reason` | 公共字段，ADR 采用 | 废弃原因和不再适用边界 | markdown | 条件必填 | `status: deprecated` 时必须填写 | narrative | 22 | AI、Code、Web |

active ADR 的 `consequences` 字段必须包含 `## 正向价值`、`## 逆向价值`、`## 实施成本`、`## 风险评估`、`## 注意事项`。`## 正向价值` 只记录相对 V1-V10 的价值增强；`## 逆向价值` 只记录相对 V1-V10 的价值削弱，不混入实施成本、概率风险或执行代价。存在逆向价值时必须引用 V1-V10；无逆向价值时 `## 逆向价值` 填写 `当前决策无逆向价值`。

## 10. 事实实例写入、回写、验证和证据留存

ADR 回写遵循以下规则：

1. 创建 ADR 时，应写入 `ldvh-base/adrs/`，并填写背景、决策、后果和影响范围；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit records 派生，不在 ADR YAML 中手写维护；
4. active ADR 的核心决策变更必须经 Human Gate，并通过 Git 提交记录留痕；
5. ADR 升级为规范或 Rules 后，应同步更新 `related_rules`；
6. ADR 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

ADR 证据至少包括决策背景、决策内容、决策取舍说明、决策后果、影响范围、Human Gate 确认记录，以及相关 Git 提交记录、WorkCase、Spark 或规范引用。

## 11. Code、Web、知识地图和运行时扩展消费边界

AI 处理 ADR 时应先判断是否满足准入条件；`active` ADR 是后续执行应优先参考的决策补丁；`archived` ADR 只作为追溯依据；`deprecated` ADR 不得继续作为执行依据。

Code 可解析 ADR YAML，校验文件命名、ID、字段类型、必填字段、条件必填字段、状态枚举、合法流转、`archive_reason`、`deprecated_reason`、`related_rules` 和对象引用。Code 不得自行创建、归档、废弃或删除 ADR，不得绕过 Human Gate。

Web 可展示 ADR 状态、决策内容、关联对象、关联规范和待确认项。Web 不得展示或派生 `proposed`、`accepted`、`rejected`、`superseded`、`superseded_by`、`alternatives` 或 `affects` 等旧生命周期和旧字段语义。Web 页面状态、缓存或数据库不得维护独立 ADR 权威状态。

知识地图和运行时扩展可以消费 ADR 成员身份、状态机、字段契约、关联规范和实例事实源目录，但输出只能作为定位、诊断或展示，不能替代本文或实例文件。

## 12. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | ADR 实例和后续行动编排应遵守本文定义的准入、状态机、字段契约、终态规则、规范吸收边界和事实源边界 | 本文、active `specs/22-ADR-决策.md`、v2 02、Human Gate；行动编排未接管前为人工降级检查 | 事实模型治理 | 创建、修改、迁移、归档或废弃 ADR 时 |
| 入口可见要求 | AI 处理长期决策、规范判断、事实源边界、方案取舍或执行约束时，应能定位 ADR active 规范、本文和对应实例事实源 | 02 成员身份、Rules 入口、`v2-check` 只读诊断和知识地图输入；行动编排未接管前为人工降级检查 | AI 执行入口 | 决策入口、规范升级、状态流转、字段契约、Rules 入口、`v2-check` 或知识地图输入变化时 |
| 确定性执行要求 | ADR 字段、状态、引用、文件命名、关联关系、五段式影响闭环和条件必填应由 Code 校验或记录缺口 | 现有 active Code、`02.Att.04`、`02.Att.05`、`02.Att.06`、人工降级检查 | Code 校验 | 字段契约、状态机、引用关系或相关规范路径变化时 |
| Human 交互要求 | ADR 创建、归档、废弃、核心决策改写和升级为规范应触发 Human Gate | Human Gate、影响范围说明、确认记录 | Human Gate | §8 中任一场景发生时 |
| 生命周期触发要求 | ADR 规范变化后，应检查成员自描述、字段注册、Git 追溯、Code、Web、运行时扩展和相关行动编排是否需要同步 | 本文、02 授权附件、Code 诊断、人工降级检查 | 生命周期同步 | ADR 字段、状态、事实源边界、适配规则或检查要求变化时 |

## 13. 对象特有实例检查

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 ADR |
| 文件命名 | 实例路径符合 `ldvh-base/adrs/adr-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §9 |
| 状态合法性 | 状态属于枚举，流转符合 §6.2 |
| 执行依据 | 只有 `active` ADR 可作为当前优先决策补丁 |
| 终态处理 | `archived`、`deprecated` 不得重开 |
| 归档/废弃原因 | `archived` ADR 已填写 `archive_reason`；`deprecated` ADR 已填写 `deprecated_reason` |
| 规范边界 | ADR 不替代 specs 或 Rules 正文 |
| Human Gate | §8 场景已完成确认或记录降级 |
| Git 追溯 | ADR 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

## 14. 待补齐事项

1. 本文已迁入 ADR 主要准入、状态机、规范吸收、Human Gate、字段契约和 Web 旧字段禁用规则，并已作为 active ADR 成员规范生效；
2. 历史 `ldvh_member` 与 active `v2_fact_model_member` 的双读 Code 实现、正反样例和历史追溯策略尚未完成；本文不改变 Code 默认消费入口；
3. ADR 创建、归档、废弃和升级为规范的具体行动编排不按 v1 直接迁入；应按当前 active 规范保障需求进入行动编排候选计划；
4. 后续修改本文时，应再次核对 active `specs/22-ADR-决策.md`、02 授权附件、现有 Code/Web 测试和相关 active 20-24 成员规则，确认没有字段、状态、引用或消费入口漂移。
