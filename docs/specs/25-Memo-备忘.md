# Memo-备忘

> 创建日期：2026-06-09
> 定位：定义 Memo / 备忘工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要管理尚未任务化但有保留价值的输入、发现、提醒、问题、缺口和偏好的项目
> 上位依据：`docs/specs/05-工作模型基础规范.md`
> 相关规范：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/02-术语规范.md`、`docs/specs/03.04-工作模型文档规范.md`、`docs/specs/05.01-工作字段内容格式规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/08-Web信息同步规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/20-工作模型集合索引.md`、`docs/specs/21-ADR-决策.md`、`docs/specs/22-Change-变更.md`、`docs/specs/24-Intent-意图.md`、`docs/specs/26-Task-任务.md`

---
## 1. 对象定位与准入条件

Memo / 备忘承载尚未任务化但有保留价值的输入、发现、提醒、问题、缺口和偏好。Memo 的目标是降低误创建 Task、ADR 或 Intent 的冲动，同时避免有价值的信息只留在聊天记忆中。

Memo 是分流前的事实对象。它可以后续转化或关联到 Task、ADR、Intent、Pitfall、docs、管辖项目配置或其他事实源，但在转化前不替代这些对象的字段契约、状态机、验收规则或配置边界。

### 1.1 Memo 准入条件

一个信息单元满足以下条件之一时，应考虑形成 Memo：

1. 有保留价值，但尚未形成明确执行目标或验收标准；
2. 不满足 Task 准入条件，但可能后续转为 Task；
3. 不满足 ADR 准入条件，但属于可能影响后续判断的偏好、观察或临时判断；
4. 不满足 Intent 准入条件，但可能后续发展为目标或约束；
5. 执行过程中发现问题、缺口、风险线索、资料线索或待讨论事项，尚未决定如何处理；
6. 不记录会导致后续遗忘、重复讨论或信息断裂。

创建 Memo 前，AI 应说明保留原因、来源、分类和后续可能分流方向，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 Memo 的内容

以下内容通常不应单独形成 Memo：

1. 当前对话中可以直接处理的信息；
2. 已有明确目标和验收标准的工作，应创建 Task 或写入现有 Task；
3. 已经满足长期决策准入的判断，应创建 ADR；
4. 已经满足目标入口准入的输入，应创建 Intent；
5. 纯闲聊、寒暄或无后续价值的信息；
6. 已由 docs、refs、research 或现有对象完整承载的信息。

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
| Memo 工作模型规范 | `docs/specs/25-Memo-备忘.md` |
| Memo 实例 | `ldvh-base/memos/` |
| Memo 字段内容格式 | `docs/specs/05.01-工作字段内容格式规范.md` |
| Memo 展示、聚合或查询结果 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

Memo 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Memo 标准状态如下：

| 状态 | 含义 |
|---|---|
| `draft` | 已记录，待确认是否保留或分类 |
| `active` | 已确认保留，可作为后续参考或分流输入 |
| `resolved` | 已分流到 Task、ADR、Intent、docs 或其他事实源，或已明确处理 |
| `archived` | 已归档，不再活跃但保留记录 |

`archived` 是稳定终态。终态 Memo 不得直接重开；如需重新处理，应新建 Memo，并在新 Memo 中引用原 Memo。

### 3.2 合法状态流转

```text
draft → active
draft → archived
active → resolved
active → archived
resolved → archived
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `draft` → `active` | 确认该信息有保留价值 | 可作为后续参考或分流输入 |
| `draft` → `archived` | 记录后判断不需要继续保留 | 应记录归档原因 |
| `active` → `resolved` | 已分流到目标事实源或已明确处理 | `resolved_to` 和 `resolved_at` 条件必填 |
| `active` → `archived` | 不再需要继续跟踪但保留记录 | 应记录归档原因 |
| `resolved` → `archived` | 分流后不再活跃 | 保留关系记录 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 Memo 与 Task

Memo 可以分流为 Task，作为尚未任务化信息转化为可执行工作单元的路径。分流后，Memo 的 `resolved_to` 应记录 Task ID，Task 的 `source` 或 `related_docs` 可记录 Memo ID 或路径。

Task 的准入、状态和字段契约由 `docs/specs/26-Task-任务.md` 定义。

### 4.2 Memo 与 ADR

Memo 可以分流为 ADR，作为临时判断、偏好或方案取舍转化为长期决策的路径。分流后，Memo 的 `resolved_to` 应记录 ADR ID，ADR 的 `related_memos` 可记录来源 Memo。

ADR 的准入、状态和字段契约由 `docs/specs/21-ADR-决策.md` 定义。

### 4.3 Memo 与 Intent

Memo 可以分流为 Intent，作为待讨论事项、目标线索或约束线索转化为明确意图的路径。分流后，Memo 的 `resolved_to` 应记录 Intent ID，Intent 的 `related_memos` 可记录来源 Memo。

Intent 的准入、状态和字段契约由 `docs/specs/24-Intent-意图.md` 定义。

### 4.4 Memo 与 Pitfall、管辖项目配置、docs

Memo 可以分流或关联到 Pitfall、管辖项目配置或 docs：

1. 已解决且有复用价值的踩坑线索，可转为 Pitfall；
2. 项目路径或管辖项目清单线索，可转为工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 更新建议或项目文档更新建议；
3. 项目正文、调研、说明或报告内容，可吸收到 docs；
4. 外部引用或调研资料，应进入 refs 或 docs/refs。

Pitfall 的准入、状态和字段契约由 `docs/specs/23-Pitfall-踩坑.md` 定义。管辖项目配置的字段和边界由 `docs/specs/03.06-管辖项目配置规范.md` 定义。环境能力核验、环境投射和运行投影正文不得写入管辖项目配置；需要长期保留的稳定事实应进入环境投射待补齐事项、Task、Memo、ADR、正式规范或按 04 系列规范处理。42 落地与检查报告只保留当前过程结论，不作为持久状态事实源。

### 4.5 Memo 与 Change

Memo 的创建、状态变化、分流和归档都应留下 Change。Change 的 commit message 契约由 `docs/specs/22-Change-变更.md` 定义。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Memo 实例；
2. 将对话输入、docs/research 结论或执行发现写入 Memo；
3. 将 `draft` Memo 确认为 `active`；
4. 将 `active` Memo 分流为 Task、ADR、Intent、Pitfall、docs、管辖项目配置更新或其他事实源；
5. 将 Memo 归档，且归档会丢失后续跟踪入口；
6. 修改 `resolved_to`、`category`、`priority` 或核心描述；
7. 将 Memo 作为规避 Task、ADR 或 Intent 准入判断的长期替代物。

Human Gate 的具体环境实体由 04 系列环境投射和运行投影记录承接。本文只规定 Memo 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 字段表

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | Memo ID，格式为 `memo-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `memo` | Reference | AI、Code、Web |
| `title` | 备忘标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建日期 | date | 是 | `YYYY-MM-DD` | Reference | AI、Code、Web |
| `updated` | 最近更新日期 | date | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `description` | 备忘内容描述 | string | 是 | 使用 YAML 块标量 | Narrative / Decision / Reference / Log | AI、Web |
| `source` | 来源 | string | 是 | 谁在什么场景下表达或发现 | Reference / Narrative | AI、Web |
| `category` | 分类 | string | 是 | `discovery`、`reminder`、`question`、`gap`、`preference` | Reference | AI、Code、Web |
| `priority` | 优先级 | string | 否 | `low`、`medium`、`high`，默认 `low` | Reference | AI、Code、Web |
| `resolved_to` | 分流目标对象 ID、路径或说明 | string | 条件必填 | `status: resolved` 时必须填写 | Reference | AI、Code、Web |
| `resolved_at` | 分流日期 | date | 条件必填 | `status: resolved` 时必须填写 | Reference | AI、Code、Web |
| `archive_reason` | 归档原因 | string | 条件必填 | `status: archived` 且未 resolved 时应填写 | Narrative | AI、Human |
| `related_tasks` | 关联 Task ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联 ADR ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_intents` | 关联 Intent ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_changes` | 关联 Change commit 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |

字段内容格式按 `docs/specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: memo-0001
type: memo
title: 规范文档中缺少错误处理章节
status: resolved
created: 2026-06-09
updated: 2026-06-09
description: |
  在审查工作流程规范时发现错误处理和异常场景尚未形成统一规则，需要后续补充。
source: 执行 task-0003 过程中的发现
category: gap
priority: medium
resolved_to: task-0012
resolved_at: 2026-06-09
archive_reason:
related_tasks:
  - task-0003
related_adrs: []
related_intents: []
related_changes: []
related_docs: []
status_history:
  - at: 2026-06-09
    from: active
    to: resolved
    actor: AI
    reason: 已分流为 task-0012
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Memo 回写遵循以下规则：

1. 创建 Memo 时，应写入 `ldvh-base/memos/`，并填写标题、描述、来源、分类、优先级和状态；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`，并向 `status_history` 追加记录；
4. Memo 分流为 Task、ADR、Intent、Pitfall、docs、管辖项目配置更新或其他事实源时，应更新 `resolved_to` 和 `resolved_at`；
5. Memo 创建、分流、归档或核心描述修改应通过 Change 留痕；
6. Memo 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

Memo 证据至少包括：

1. 创建原因和来源；
2. 分类和优先级；
3. 分流目标或归档原因；
4. Human Gate 确认记录；
5. 相关 Task、ADR、Intent、Change 或文档引用。

Memo 的分流证据应保留摘要和目标引用，不复制目标对象全文。

---
## 8. 适配规则

### 8.1 AI 协作

AI 处理 Memo 时应遵守：

1. 先判断信息是否满足 Memo 准入条件；
2. 创建、分流、归档或删除 Memo 前评估 Human Gate；
3. 不得用 Memo 长期替代已经满足准入条件的 Task、ADR 或 Intent；
4. 分流时应说明为什么目标类型合适；
5. 分流后不再在 Memo 中维护目标对象的状态、验收或决策正文。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Memo YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `category`、`priority`、`resolved_to` 和引用字段；
5. 聚合 active Memo、待分流 Memo、已归档 Memo 和分流目标。

Code 不得自行创建、分流、归档或删除 Memo，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/memos/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Memo 状态、分类、优先级、来源、分流目标、归档原因和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

当前唯一允许的 Memo Web 写入是快速创建：Web 可通过 `POST /api/memos` 创建 `status: draft` 的新 Memo，并写入 `title`、`description`、`source`、`category`、`priority` 和 `status_history`。该能力是 `docs/specs/08-Web信息同步规范.md` §8.2 的当前唯一 Web 事实源写入白名单。

Web 不得在页面状态、缓存或数据库中维护独立 Memo 权威状态。Memo 创建后的字段编辑、状态流转、分流、归档和删除不得通过 Web 直接执行；如未来需要开放，必须先更新 08 白名单、本文字段/状态约束、Code 校验、测试和 Human Gate 影响评估。

### 8.4 工作流程与环境适配

Memo 创建、分流和归档的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Memo 实例的事实规则和状态约束。

环境不支持完整引用校验、分流辅助或创建后字段编辑时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Memo 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、分流规则和事实源边界 | 05、03.04、本文、20 集合索引、21 ADR、24 Intent、26 Task、Human Gate | 工作模型治理 | 创建、修改、搬移、审计、分流或归档 Memo 时 |
| 入口可见要求 | AI 处理未任务化但有保留价值的信息、发现、提醒、问题或缺口时，应能定位本文 | 20 集合索引、运行入口摘要、Memo 分流流程入口 | AI 执行入口提示 | 信息保留、分流、归档或字段契约变化时 |
| 确定性执行要求 | Memo 字段、状态、分类、优先级、引用、文件命名和条件必填应由 Code 校验或记录缺口 | `docs/specs/07-Code实现规范.md`、Memo 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、分类枚举、分流规则或引用关系变化时 |
| Human 交互要求 | Memo 创建、确认、分流、归档、核心描述修改和用 Memo 规避对象准入时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Memo 规范变化后，应检查 20、05.01、ADR、Intent、Task、Code、Web、运行投影和相关工作流程是否需要同步 | 集合索引维护、字段格式映射、对象关系检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Memo 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

Memo 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Memo |
| 事实源位置 | 实例路径符合 `ldvh-base/memos/memo-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 分流规则 | resolved Memo 已填写 `resolved_to` 和 `resolved_at` |
| 归档规则 | archived 且未 resolved 的 Memo 已说明归档原因 |
| 对象边界 | Memo 未长期替代 Task、ADR 或 Intent |
| Human Gate | §5 场景已完成确认或记录降级 |
| Change 追溯 | Memo 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Memo 校验 Code 待字段契约稳定后补齐正反样例；
2. Memo 快速创建已作为当前唯一 Web 写入能力落地；Memo 分流、归档、删除和创建后字段编辑仍待工作流程、受控写入规范和 Human Gate 样例补齐；
3. Memo 创建、分流和归档的具体工作流程待 40-59 承接；
4. `category` 枚举是否需要扩展，待更多实例实践后评估。
