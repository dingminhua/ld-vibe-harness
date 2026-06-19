# Memo-备忘

```yaml
ldvh_doc:
  doc_id: "24"
  doc_kind: "work_model_spec"
  title: "Memo-备忘"
  status: "active"
  canonical_path: "specs/24-Memo-备忘.md"
  created: "2026-06-09"
  updated: "2026-06-09"
  parent_doc: ""
  relation: ""
  positioning: "定义 Memo / 备忘工作模型，包括对象定位、演变承载、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则"
  scope: "所有接入 LDVH 且需要管理尚未计划化但有保留价值的输入、发现、提醒、问题、缺口和偏好的项目"
  basis:
    - "specs/05-工作模型基础规范.md"
  related_specs:
    - "specs/05.01-工作字段内容格式规范.md"
    - "specs/07-Code确定性执行实现规范.md"
    - "specs/08-Web信息同步实现规范.md"
    - "specs/20-WorkArea-工作域.md"
    - "specs/21-WorkPlan-工作计划.md"
    - "specs/22-ADR-决策.md"
    - "specs/10-Git提交规范.md"
    - "specs/25-Study-研究报告.md"
  code_consumption:
    - "doc_metadata"
    - "relations"
    - "structure"
    - "member_consistency"
    - "work_model_collection"
```

```yaml
ldvh_member:
  spec_id: "24"
  kind: work_model
  name_en: Memo
  name_zh: 备忘
  collection_status: active
  canonical_path: specs/24-Memo-备忘.md
  instance_root: ldvh-base/memos/
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

Memo / 备忘承载尚未计划化但有保留价值的输入、发现、提醒、问题、缺口、偏好和待消化议题。Memo 的目标是降低误创建 WorkArea、WorkPlan 或 ADR 的冲动，同时避免有价值的信息只留在聊天记忆中。

Memo 是分流前的工作对象。它可以后续转化或关联到 WorkArea、WorkPlan、ADR、Pitfall、docs、管辖项目配置或其他事实源，但在转化前不替代这些对象的字段契约、状态机、验收规则或配置边界。

Memo 可以从一句话开始，随后逐步扩展和收敛。`description` 承载当前可读摘要，`evolution` 只记录关键语义转折、方向变化、阶段性收敛和重要分流，不记录逐条对话、完整报告正文或状态流转历史。完整研究报告由 Study 承载，状态流转历史由 Git 提交记录派生。

### 1.1 Memo 准入条件

一个信息单元满足以下条件之一时，应考虑形成 Memo：

1. 有保留价值，但尚未形成明确执行目标或验收标准；
2. 不满足 WorkPlan 准入条件，但可能后续转为 WorkPlan；
3. 不满足 ADR 准入条件，但属于可能影响后续判断的偏好、观察或临时判断；
4. 不满足 WorkArea 或 WorkPlan 准入条件，但可能后续发展为长期范围、目标或约束；
5. 执行过程中发现问题、缺口、风险线索、资料线索或待讨论事项，尚未决定如何处理；
6. 不记录会导致后续遗忘、重复讨论或信息断裂；
7. 一个想法需要先暂存，后续可能通过讨论、AI 调研、Study 报告或 WorkPlan 逐步收敛。

创建 Memo 前，AI 应说明保留原因、来源、优先级和后续可能分流方向，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 Memo 的内容

以下内容通常不应单独形成 Memo：

1. 当前对话中可以直接处理的信息；
2. 已有明确目标和验收标准的工作，应创建 WorkPlan 或写入现有对象；
3. 已经满足长期决策准入的判断，应创建 ADR；
4. 已经满足长期范围或工作计划准入的输入，应创建 WorkArea 或 WorkPlan；
5. 纯闲聊、寒暄或无后续价值的信息；
6. 已由 Study、docs、sources 或现有对象完整承载的信息；
7. 完整调研报告正文，应形成 Study 或进入项目约定文档位置，而不是复制到 Memo。

---
## 2. 事实源边界

本文是 Memo 工作模型的权威规范，定义 Memo 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

Memo 实例的权威事实源位置为：

```text
ldvh-base/memos/memo-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Memo 工作模型规范 | `specs/24-Memo-备忘.md` |
| Memo 实例 | `ldvh-base/memos/` |
| Memo 字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| Memo 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

Memo 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Memo 标准状态如下：

| 状态 | 含义 |
|---|---|
| `pending` | 待处理：已捕获，尚未决定是否分流、处理或废弃 |
| `resolved` | 已分流到 WorkArea、WorkPlan、ADR、docs 或其他事实源，或已明确处理 |
| `discarded` | 已废弃：确认不再需要继续跟踪或作为分流入口 |

`resolved` 和 `discarded` 是稳定终态。终态 Memo 不得直接重开；如需重新处理，应新建 Memo，并在新 Memo 中引用原 Memo。

### 3.2 合法状态流转

```text
pending → resolved
pending → discarded
resolved → discarded
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `pending` → `resolved` | 已分流到目标事实源或已明确处理 | `resolved_to` 和 `resolved_at` 条件必填 |
| `pending` → `discarded` | 判断不需要继续处理 | 应记录 `discard_reason` |
| `resolved` → `discarded` | 分流记录不再需要作为活跃入口展示 | 保留分流关系，并记录 `discard_reason` |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 Memo 与 WorkPlan

Memo 可以分流为 WorkPlan，作为尚未计划化信息转化为可执行工作计划的路径。分流后，Memo 的 `resolved_to` 应记录 `{type: workplan, ref: <WorkPlan ID>}`，WorkPlan 的 `source` 或 `related_memos` 可记录 Memo ID 或路径。

WorkPlan 的准入、状态和字段契约由 `specs/21-WorkPlan-工作计划.md` 定义。

### 4.2 Memo 与 ADR

Memo 可以分流为 ADR，作为临时判断、偏好或方案取舍转化为长期决策的路径。分流后，Memo 的 `resolved_to` 应记录 `{type: adr, ref: <ADR ID>}`，ADR 的 `related_memos` 可记录来源 Memo。

ADR 的准入、状态和字段契约由 `specs/22-ADR-决策.md` 定义。

### 4.3 Memo 与 WorkArea 和 WorkPlan

Memo 可以分流为 WorkArea，作为长期范围、治理域或持续维护面的来源线索。Memo 也可以分流为 WorkPlan，作为一次目标、执行计划或关闭审查的来源线索。分流后，Memo 的 `resolved_to` 应记录 `{type: workarea, ref: <WorkArea ID>}` 或 `{type: workplan, ref: <WorkPlan ID>}`，目标对象的 `related_memos` 可记录来源 Memo。

WorkArea 的准入、状态和字段契约由 `specs/20-WorkArea-工作域.md` 定义；WorkPlan 的准入、状态和字段契约由 `specs/21-WorkPlan-工作计划.md` 定义。

### 4.4 Memo 与 Study

Memo 可以关联一个或多个 Study，用于承接 AI 调研、资料分析、事实核验或方案比较后的稳定报告。Memo 的 `related_studies` 记录 Study ID；Study 的 `related_memos` 可反向记录来源或关联 Memo。

Memo 只保留报告对议题演变产生的关键影响，不复制报告全文。Study 的准入、状态和字段契约由 `specs/25-Study-研究报告.md` 定义。

### 4.5 Memo 与 Pitfall、管辖项目配置、docs

Memo 可以分流或关联到 Pitfall、管辖项目配置或 docs：

1. 已解决且有复用价值的踩坑经验线索，可转为 Pitfall；
2. 项目路径或管辖项目清单线索，可转为工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 更新建议或项目文档更新建议；
3. 项目正文、说明或短结论，可吸收到 docs；
4. 稳定调研、分析或报告内容，应优先形成 Study；
5. 外部引用或调研资料，应进入 docs/sources。

Pitfall 的准入、状态和字段契约由 `specs/23-Pitfall-踩坑经验.md` 定义。管辖项目配置的字段和边界由 `specs/03.04-管辖项目配置规范.md` 定义。环境能力核验、环境适配和适配措施正文不得写入管辖项目配置；需要长期保留的稳定事实应进入环境适配待补齐事项、WorkPlan、Memo、Study、ADR、正式规范或按 04 系列规范处理。当前具体检查结果只保留当前过程结论，不作为持久状态事实源。

### 4.6 Memo 与 Git 提交记录

Memo 的创建、状态变化、分流和废弃都应留下 Git 提交记录。commit message 格式规则由 `specs/10-Git提交规范.md` 定义。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Memo 实例；
2. 将对话输入、docs/studies 结论或执行发现写入 Memo；
3. 将 `pending` Memo 分流为 WorkArea、WorkPlan、ADR、Pitfall、docs、管辖项目配置更新或其他事实源；
4. 将 Memo 标记为 `discarded`，且废弃会丢失后续跟踪入口；
6. 修改 `resolved_to`、`priority`、`description`、`evolution` 或关键关联；
7. 将 Memo 作为规避 WorkArea、WorkPlan 或 ADR 准入判断的长期替代物。

Human Gate 的具体环境实体由 04 系列环境适配和适配措施记录承接。本文只规定 Memo 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 字段表

公共字段语义定义见 `specs/05.01-工作字段内容格式规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `memo-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `memo` | string | 是 | 固定为 `memo` | Reference | AI、Code、Web |
| `title` | 备忘一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `description` | 当前可读摘要、问题焦点和阶段性收敛方向 | string | 是 | 使用 YAML 块标量；不写完整报告正文或流水账 | Narrative | AI、Web |
| `evolution` | 关键语义转折 | list[object] | 否 | 默认为空列表；元素至少包含 `at` 和 `summary` | Log / Narrative | AI、Code、Web |
| `source` | 备忘进入事实源的入口来源 | enum | 是 | `web` 或 `conversation`；Web 快速创建固定为 `web`，对话中由 Human 或 AI 确认记录固定为 `conversation` | Reference | AI、Code、Web |
| `source_detail` | 来源说明、触发场景或原始输入摘要 | string | 否 | 可为空 | Narrative / Reference | AI、Web |
| `priority` | 优先级 | string | 是 | `P0`、`P1`、`P2`、`P3`；判断标准见 `specs/05-工作模型基础规范.md` §7.3.1 | Reference | AI、Code、Web |
| `resolved_to` | 分流目标对象引用 | object | 条件必填 | `status: resolved` 时必须填写；结构为 `{type, ref}` | Reference | AI、Code、Web |
| `resolved_at` | 分流日期 | date | 条件必填 | `status: resolved` 时必须填写 | Reference | AI、Code、Web |
| `discard_reason` | 废弃原因 | string | 条件必填 | `status: discarded` 时必须填写 | Narrative | AI、Human |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_studies` | 关联研究报告 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workareas` | 关联工作域 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workplans` | 关联工作计划 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |

字段内容格式按 `specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: memo-0001
type: memo
title: 规范文档中缺少错误处理章节
status: resolved
created: '2026-06-09T09:30:00+08:00'
updated: '2026-06-09T10:00:00+08:00'
description: |
  审查工作流程规范时发现错误处理和异常场景尚未形成统一规则。当前方向是先保留缺口，再决定是否分流为 WorkPlan 或 Study。
evolution:
  - at: '2026-06-09T09:45:00+08:00'
    summary: 发现错误处理章节缺失，先作为备忘保留。
source: conversation
source_detail: 执行 workplan-0003 过程中的发现
priority: P2
resolved_to:
  type: workplan
  ref: workplan-0012
resolved_at: 2026-06-09
discard_reason:
related_adrs: []
related_studies: []
related_workareas: []
related_workplans: []
related_docs: []
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Memo 回写遵循以下规则：

1. 创建 Memo 时，应写入 `ldvh-base/memos/`，并填写标题、当前摘要、来源类型、优先级和状态；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit 派生，不在 Memo YAML 中手写维护；
4. Memo 出现关键语义转折、方向变化或阶段性收敛时，应更新 `description` 并向 `evolution` 追加摘要；不得记录完整聊天流水；
5. Memo 分流为 WorkArea、WorkPlan、ADR、Study、Pitfall、docs、管辖项目配置更新或其他事实源时，应更新 `resolved_to` 和 `resolved_at`；
6. Memo 创建、分流、废弃、关键关联变化、核心摘要或演变记录修改应通过 Git 提交记录留痕；
7. Memo 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

Memo 证据至少包括：

1. 创建原因和来源；
2. 优先级；
3. 当前摘要和关键语义转折；
4. 分流目标或废弃原因；
5. Human Gate 确认记录；
6. 相关 WorkArea、WorkPlan、ADR、Study、Git 提交记录或文档引用。

Memo 的分流证据应保留摘要和目标引用，不复制目标对象全文。

---
## 8. 适配边界

### 8.1 AI 协作

AI 处理 Memo 时应遵守：

1. 先判断信息是否满足 Memo 准入条件；
2. 创建、分流、废弃或删除 Memo 前评估 Human Gate；
3. 不得用 Memo 长期替代已经满足准入条件的 WorkArea、WorkPlan 或 ADR；
4. 分流时应说明为什么目标类型合适；
5. 分流后不再在 Memo 中维护目标对象的状态、验收或决策正文；
6. 有完整报告时应形成或关联 Study，Memo 只记录报告如何改变议题理解。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Memo YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `source`、`priority`、`evolution`、`resolved_to`（`type` 枚举和 `ref` 引用有效性）和引用字段；
5. 聚合待处理 Memo、已分流 Memo、已废弃 Memo 和分流目标。

Code 不得自行创建、分流、废弃或删除 Memo，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/memos/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Memo 状态、优先级、来源类型、来源说明、关键演变、分流目标、废弃原因和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

当前唯一允许的 Memo Web 写入是快速创建：Web 可通过 `POST /api/memos` 创建 `status: pending` 的新 Memo，并写入 `title`、`description` 和 `priority`。Web 创建时 `source` 固定写入 `web`，不得要求用户在页面上填写来源类型。对话中创建或由 AI 根据对话整理的 Memo 固定写入 `conversation`。该能力是 `specs/08-Web信息同步实现规范.md` §8.2 的当前唯一 Web 事实源写入白名单。

Web 不得在页面状态、缓存或数据库中维护独立 Memo 权威状态。Memo 创建后的字段编辑、状态流转、分流、废弃和删除不得通过 Web 直接执行；如未来需要开放，必须先更新 08 白名单、本文字段/状态约束、Code 校验、测试和 Human Gate 影响评估。

### 8.4 工作流程与环境适配

Memo 创建、分流和废弃的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Memo 实例的事实规则和状态约束。

环境不支持完整引用校验、分流辅助或创建后字段编辑时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Memo 实例和后续工作流程应遵守本文定义的准入、演变承载、状态机、字段契约、分流规则和事实源边界 | 05、03.02、本文、22 ADR、20 WorkArea、21 WorkPlan、25 Study、Human Gate | 工作模型治理 | 创建、修改、搬移、审计、分流或废弃 Memo 时 |
| 入口可见要求 | AI 处理未计划化但有保留价值的信息、发现、提醒、问题或缺口时，应能定位本文 | 成员自描述、运行入口摘要、Memo 分流流程入口 | AI 执行入口提示 | 信息保留、分流、废弃或字段契约变化时 |
| 确定性执行要求 | Memo 字段、状态、来源枚举、演变记录、优先级、引用、文件命名和条件必填应由 Code 校验或记录缺口 | `specs/07-Code确定性执行实现规范.md`、Memo 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、分流规则或引用关系变化时 |
| Human 交互要求 | Memo 创建、分流、废弃、核心摘要修改、演变记录修改和用 Memo 规避对象准入时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Memo 规范变化后，应检查成员自描述、05.01、ADR、Study、WorkArea、WorkPlan、Code、Web、适配措施和相关工作流程是否需要同步 | 成员自描述检查、字段格式映射、对象关系检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Memo 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

Memo 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Memo |
| 事实源位置 | 实例路径符合 `ldvh-base/memos/memo-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 演变承载 | `description` 是当前摘要，`evolution` 只记录关键语义转折，不记录流水账 |
| 分流规则 | resolved Memo 已填写 `resolved_to` 和 `resolved_at` |
| 废弃规则 | discarded Memo 已说明废弃原因 |
| 对象边界 | Memo 未长期替代 WorkArea、WorkPlan、ADR 或 Study |
| Human Gate | §5 场景已完成确认或记录降级 |
| Git 追溯 | Memo 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Memo 校验 Code 待字段契约稳定后继续补齐更多正反样例；
2. Memo 快速创建已作为当前唯一 Web 写入能力落地；Memo 分流、废弃、删除和创建后字段编辑仍待工作流程、受控写入规范和 Human Gate 样例补齐；
3. Memo 创建、分流和废弃的具体工作流程待 40-59 承接；
