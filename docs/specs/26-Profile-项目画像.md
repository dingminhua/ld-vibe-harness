# Profile-项目画像

> 创建日期：2026-06-09
> 定位：定义 Profile / 项目画像工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要管理项目身份、路径映射、项目名册和接入配置的项目
> 上位依据：`docs/specs/05-工作模型基础规范.md`
> 相关规范：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/01-目录说明.md`、`docs/specs/02-术语规范.md`、`docs/specs/03.04-工作模型文档规范.md`、`docs/specs/04.02-环境适配与运行投影规范.md`、`docs/specs/04.03-环境适配映射与运行投影记录模板.md`、`docs/specs/05.01-工作字段内容格式规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/08-Web信息同步规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/20-工作模型集合索引.md`、`docs/specs/22-Change-变更.md`、`docs/specs/23-Pitfall-踩坑.md`、`docs/specs/24-Intent-意图.md`、`docs/specs/25-Memo-备忘.md`、`docs/specs/27-Task-任务.md`

---
## 1. 对象定位与准入条件

Profile / 项目画像是项目身份、路径映射、项目名册和 LDVH 接入配置的结构化事实。Profile 用于让 AI、Human、Code 和 Web 稳定识别当前管辖项目是谁、项目根目录在哪里、`ldvh-base/` 在哪里、项目文档入口在哪里，以及当前项目是否已经进入 LDVH 治理。

Profile 不是所有项目配置、环境能力、运行投影或平台设置的默认归宿。当前开发环境能力核验、环境适配映射、运行投影和降级方式，应由根目录 `LDVH-ENVIRONMENT-INITIALIZATION.md` 按 `docs/specs/04.03-环境适配映射与运行投影记录模板.md` 承载。Profile 可以引用该记录的位置和接入状态，但不得复制环境适配正文或替代该记录。

### 1.1 Profile 准入条件

一个项目满足以下条件之一时，应考虑形成 Profile：

1. 项目需要接入 LDVH 治理；
2. 项目需要被 AI 跨会话识别和定位；
3. 多项目场景需要统一名册、路径映射或项目入口；
4. 产品初始化、产品审计或后续工作对象需要稳定引用项目身份；
5. 不结构化会导致项目根路径、`ldvh-base/` 路径、文档入口或接入状态反复漂移。

创建 Profile 前，AI 必须说明准入理由、项目身份、路径来源、预期事实源位置、是否已有环境初始化记录，以及是否需要 Human Gate。

### 1.2 不应形成 Profile 的内容

以下内容通常不应单独形成 Profile：

1. 一次性路径设置、临时命令参数或当前对话中的局部路径选择；
2. 不需要 LDVH 治理或跨会话识别的临时项目；
3. 已由现有 Profile 完整覆盖的重复项目；
4. 当前环境能力、平台能力、Hook、Skill、Agent、Code 或 Web 的具体运行投影；
5. 只属于项目正文、需求、调研、报告或分析的文档内容。

不形成 Profile 的内容，应按性质留在当前执行上下文，或进入 `LDVH-ENVIRONMENT-INITIALIZATION.md`、docs、Memo、Task、ADR、Change 或其他权威位置。

### 1.3 Profile 与环境初始化记录

Profile 和当前环境初始化记录的边界如下：

| 内容 | 权威位置 | Profile 是否承载 |
|---|---|---|
| 项目名称、项目根路径、`ldvh-base/` 路径、docs 路径 | Profile | 是 |
| 当前环境初始化记录路径 | Profile 字段引用 | 是，仅记录路径 |
| 当前开发平台能力核验 | `LDVH-ENVIRONMENT-INITIALIZATION.md` | 否 |
| 环境适配映射和运行投影正文 | `LDVH-ENVIRONMENT-INITIALIZATION.md` 与 04 系列规范 | 否 |
| 环境能力缺口和降级方式 | `LDVH-ENVIRONMENT-INITIALIZATION.md`、Task、Memo 或 ADR | 否 |

当 Profile 指向的环境初始化记录不存在、未适配当前项目或未覆盖当前开发平台时，AI 不得把 Profile 的 `active` 状态解释为运行投影已经落地。应先按 04.03 处理环境初始化记录。

---
## 2. 事实源边界

本文是 Profile 工作模型的权威规范，定义 Profile 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

Profile 实例的权威事实源位置为：

```text
ldvh-base/profiles/profile-{NNNN}-project-name.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Profile 工作模型规范 | `docs/specs/26-Profile-项目画像.md` |
| Profile 实例 | `ldvh-base/profiles/` |
| Profile 字段内容格式 | `docs/specs/05.01-工作字段内容格式规范.md` |
| 当前环境初始化记录 | 项目根目录 `LDVH-ENVIRONMENT-INITIALIZATION.md` |
| Profile 展示、聚合或查询结果 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

对应旧规范已吸收。Profile 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Profile 标准状态如下：

| 状态 | 含义 |
|---|---|
| `draft` | 已创建，项目身份、路径或接入状态尚待确认 |
| `active` | 已确认，项目已接入 LDVH，可作为项目身份和路径入口 |
| `suspended` | 暂停接入，暂不作为默认执行项目，但保留路径和历史 |
| `archived` | 项目已归档，不再作为活跃管辖项目 |

`archived` 是稳定终态。终态 Profile 不得直接重开；如需重新接入，应新建 Profile，并在新 Profile 中引用原 Profile。

### 3.2 合法状态流转

```text
draft → active
active → suspended
suspended → active
active → archived
suspended → archived
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `draft` → `active` | 项目身份、路径、`ldvh-base/` 和环境初始化记录路径已确认 | `active` 只表示项目身份可用，不表示运行投影已全部落地 |
| `active` → `suspended` | 项目暂停 LDVH 治理或当前路径暂不可用 | 应记录暂停原因 |
| `suspended` → `active` | 项目恢复治理，路径和环境初始化记录已重新确认 | 应记录恢复原因 |
| `active` → `archived` | 项目确认不再需要 LDVH 治理 | 应记录归档原因和 Human Gate |
| `suspended` → `archived` | 暂停项目确认归档 | 应记录归档原因和 Human Gate |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 Profile 与 Intent

Profile 可以通过 `related_intents` 关联项目级目标、初始化目标或治理目标。Intent 的准入、状态和字段契约由 `docs/specs/24-Intent-意图.md` 定义。

Profile 不替代 Intent 的目标、成功标准、约束或完成判断。

### 4.2 Profile 与 Task

Profile 可以通过 `related_tasks` 关联项目接入、路径调整、初始化、审计或迁移 Task。Task 的准入、状态和字段契约由 `docs/specs/27-Task-任务.md` 定义。

Profile 不替代 Task 的验收标准、验证证据、风险判断或关闭证据。

### 4.3 Profile 与 ADR

项目身份、路径归属、事实源归属或多项目治理方式形成长期决策时，应创建或关联 ADR。Profile 可通过 `related_adrs` 引用相关 ADR。

ADR 的准入、状态和字段契约由 `docs/specs/21-ADR-决策.md` 定义。

### 4.4 Profile 与 Memo

Memo 中的项目身份、路径线索、接入配置线索或初始化缺口满足 Profile 准入条件后，可以分流为 Profile。分流时应：

1. 保留 Memo 与 Profile 的引用关系；
2. 说明为什么从未任务化输入升级为项目画像；
3. 评估 Human Gate；
4. 不在 Profile 中复制 Memo 全文，只保留摘要和引用。

Memo 的准入、状态和字段契约由 `docs/specs/25-Memo-备忘.md` 定义。

### 4.5 Profile 与 Pitfall

Profile 可以通过 `related_pitfalls` 关联适用于该项目或来源于该项目的踩坑经验。Pitfall 的准入、状态和字段契约由 `docs/specs/23-Pitfall-踩坑.md` 定义。

Profile 不替代 Pitfall 的症状、根因、解决方式、验证证据或规避策略。

### 4.6 Profile 与当前环境初始化记录

Profile 通过 `environment_record_path` 指向当前环境初始化记录。该字段只表达“当前项目应读取哪个环境初始化记录”，不表达该记录中的能力核验、运行投影、Hook、Skill、Agent、Code、Web 或降级正文。

当 AI 需要执行环境适配、运行投影创建、运行投影漂移检查或环境能力降级判断时，应读取 `environment_record_path` 指向的文件，并按 04 系列规范处理。

### 4.7 Profile 与 Change

Profile 的创建、状态变化、路径字段修改、环境初始化记录路径修改、归档和重命名都应留下 Change。Change 的 commit message 契约由 `docs/specs/22-Change-变更.md` 定义。

### 4.8 Profile 与 docs

Profile 可以通过 `related_docs` 关联 README、项目说明、初始化说明、需求文档或其他项目正文入口。docs 的文档规则由 `docs/specs/03.02-管辖项目文档规范.md` 和 `docs/specs/01-目录说明.md` 定义。

Profile 不替代 docs 正文，不复制 docs/evals 或 docs/refs 的内容。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Profile 实例；
2. 将临时路径、Memo、docs/evals 结论或对话输入升级为 Profile；
3. 将 `draft` Profile 确认为 `active`；
4. 将 Profile 标记为 `suspended` 或 `archived`；
5. 修改 `project_path`、`ldvh_base_path`、`docs_path` 或 `environment_record_path`；
6. 在环境初始化记录缺失、未适配或无法读取时，仍尝试把 Profile 作为运行投影落地依据；
7. 将 Profile 改为承载环境能力核验或运行投影正文；
8. 合并、拆分或替换多个项目的 Profile 归属。

Human Gate 的具体环境实体由 04 系列环境适配映射和运行投影记录承接。本文只规定 Profile 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 字段表

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | Profile ID，格式为 `profile-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `profile` | Reference | AI、Code、Web |
| `title` | 项目画像标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建日期 | date | 是 | `YYYY-MM-DD` | Reference | AI、Code、Web |
| `updated` | 最近更新日期 | date | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `description` | 项目背景、定位和治理范围摘要 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `project_name` | 项目唯一识别名称 | string | 是 | 不得为空 | Reference | AI、Code、Web |
| `project_kind` | 项目类型 | string | 是 | `ldvh_self`、`governed_project` 或 `management_project` | Reference | AI、Code、Web |
| `project_path` | 项目根路径 | string | 是 | `active` 时必须可定位 | Reference | AI、Code |
| `ldvh_base_path` | 结构化事实实例目录路径 | string | 是 | `active` 时必须可定位 | Reference | AI、Code |
| `docs_path` | 管辖项目文档工作区路径 | string | 否 | 管辖项目通常为 `docs/` | Reference | AI、Code、Web |
| `environment_record_path` | 当前环境初始化记录路径 | string | 条件必填 | `status: active` 或 `suspended` 时必须填写 | Reference | AI、Code、Web |
| `language` | 主要编程语言 | string | 否 | 可为空 | Reference | AI、Web |
| `framework` | 主要框架或技术栈 | string | 否 | 可为空 | Reference | AI、Web |
| `governance_scope` | LDVH 管辖范围、边界和排除项 | string | 否 | 高影响项目应填写 | Narrative / Checklist | AI、Human |
| `related_intents` | 关联 Intent ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_tasks` | 关联 Task ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联 ADR ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 来源或关联 Memo ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联 Pitfall ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_changes` | 关联 Change commit 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |
| `notes` | 补充说明 | string | 否 | 不得承载环境适配正文 | Narrative / Reference | AI、Web |

字段内容格式按 `docs/specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、路径字段缺失、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: profile-0001
type: profile
title: ld-vibe-harness 项目画像
status: active
created: 2026-06-09
updated: 2026-06-09
description: |
  LDVH 自身项目，承载 docs/specs 规范体系、Code、Web 和 dogfood 事实实例。
project_name: ld-vibe-harness
project_kind: ldvh_self
project_path: /Users/dmh2002/codex_projects/ld-vibe-harness
ldvh_base_path: /Users/dmh2002/codex_projects/ld-vibe-harness/ldvh-base
docs_path: /Users/dmh2002/codex_projects/ld-vibe-harness/docs
environment_record_path: /Users/dmh2002/codex_projects/ld-vibe-harness/LDVH-ENVIRONMENT-INITIALIZATION.md
language: Python
framework: ""
governance_scope: |
  - docs/specs 规范体系
  - tools Code 实现
  - web 信息同步实现
related_intents: []
related_tasks: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_docs:
  - README.md
related_changes: []
status_history:
  - at: 2026-06-09
    from:
    to: active
    actor: AI
    reason: 更新 Profile 工作模型
notes: |
  环境能力核验和运行投影正文以 environment_record_path 指向的根目录记录为准。
```

### 6.3 字段约束

1. `status` 必须属于 Profile 标准状态枚举：`draft`、`active`、`suspended`、`archived`；
2. `type` 必须固定为 `profile`；
3. `id` 格式必须为 `profile-{NNNN}`，编号固定 4 位；
4. `project_kind` 必须属于 `ldvh_self`、`governed_project` 或 `management_project`；
5. `project_name` 不得为空字符串，应使用项目唯一识别名称；
6. `project_path`、`ldvh_base_path` 和 `environment_record_path` 在 `active` 或 `suspended` 状态下必须填写；
7. `ldvh_base_path` 通常应位于 `project_path` 之下；如为集中管理例外，应在 `notes` 中说明；
8. `environment_record_path` 只指向当前环境初始化记录，不得内联运行投影正文；
9. `related_*` 列表应引用已存在对象、commit 或路径；引用无效时应报告校验警告；
10. `created` 和 `updated` 使用 ISO 8601 日期格式（`YYYY-MM-DD`）；
11. 列表字段可为空列表，不得省略字段后以 null 替代空列表。

### 6.4 文件命名契约

Profile 实例文件命名规则为 `profile-{NNNN}-project-name.yaml`。编号从 `0001` 起递增，固定 4 位；英文短标题使用小写短横线命名；文件存放位置为 `ldvh-base/profiles/`。

文件名变化必须同步检查引用该 Profile 的 Memo、Intent、Task、ADR、Pitfall、Change、Web 派生视图和 Code 聚合结果。

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Profile 回写遵循以下规则：

1. 创建 Profile 时，应写入 `ldvh-base/profiles/`，并填写项目身份、路径和接入状态；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`，并向 `status_history` 追加记录；
4. 修改项目路径、`ldvh_base_path`、docs 路径或环境初始化记录路径时，应保留变更原因；
5. Profile 创建、状态变化、路径变化、归档或重命名应通过 Change 留痕；
6. Profile 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

Profile 证据至少包括：

1. 创建原因和来源；
2. 项目根路径来源；
3. `ldvh-base/` 路径来源；
4. 当前环境初始化记录路径；
5. Human Gate 确认记录或降级说明；
6. 相关 Change、Intent、Task、Memo、ADR 或 docs 引用。

路径检查命令、聊天内容、工具缓存和 Web 页面状态不得单独作为 Profile 证据。需要长期保留时，应摘要写入 Profile、Memo、Task 或对应事实源。

---
## 8. 适配规则

### 8.1 AI 协作

AI 处理 Profile 时应遵守：

1. 先判断是否满足 Profile 准入条件，再提出创建建议；
2. 读取 Profile 后，应继续检查 `environment_record_path` 是否存在且适配当前项目和开发平台；
3. 不得把 Profile 的 `active` 状态解释为环境能力、运行投影或产品初始化已经全部完成；
4. 创建、激活、暂停、归档、路径修改或环境记录路径修改前评估 Human Gate；
5. 不得把 Profile 长期替代 Intent、Task、Memo、ADR、docs 或环境初始化记录；
6. 多项目场景下，应明确当前操作针对哪个 Profile，不得凭聊天记忆切换项目身份。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Profile YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验路径字段存在性或报告路径缺口；
5. 校验 `environment_record_path` 是否指向根目录初始化记录；
6. 聚合 Profile 名册、接入状态、项目路径和相关对象。

Code 不得自行创建、激活、暂停、归档或删除 Profile，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/profiles/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Profile 名册、项目状态、路径摘要、环境初始化记录入口、关联对象和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Web 不得在页面状态、缓存或数据库中维护独立 Profile 权威状态。受控编辑 Profile 字段时，应调用 Code 校验和受控写入链路，并遵守 Human Gate。

### 8.4 工作流程与环境适配

Profile 创建、确认、暂停、归档和项目切换的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Profile 实例的事实规则和状态约束。

环境适配和运行投影落地由 04 系列规范与当前环境初始化记录承接。环境不支持路径校验、环境记录读取或多项目名册聚合时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Profile 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、环境记录边界和事实源边界 | 05、03.04、本文、20 集合索引、04.03、Human Gate | 工作模型治理 | 创建、修改、迁移、审计、暂停或归档 Profile 时 |
| 入口可见要求 | AI 识别项目身份、路径映射、多项目名册或 LDVH 接入状态时，应能定位本文和当前环境初始化记录 | 20 集合索引、01 目录入口、根目录环境初始化记录、运行入口摘要 | AI 执行入口提示 | 项目入口、路径字段、环境记录路径或名册关系变化时 |
| 确定性执行要求 | Profile 字段、状态、路径、文件命名、引用和环境记录路径应由 Code 校验或记录缺口 | `docs/specs/07-Code实现规范.md`、Profile 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、路径规则、引用关系或环境记录边界变化时 |
| Human 交互要求 | Profile 创建、激活、暂停、归档、路径改写和环境记录路径替换应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Profile 规范变化后，应检查 20、05.01、04.03、Code、Web、运行投影和相关工作流程是否需要同步 | 集合索引维护、字段格式映射、环境记录检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Profile 字段、状态、事实源边界、环境记录边界或适配规则变化时 |

---
## 10. 检查要求

Profile 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Profile |
| 事实源位置 | 实例路径符合 `ldvh-base/profiles/profile-{NNNN}-project-name.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 路径边界 | `project_path`、`ldvh_base_path`、`docs_path` 和 `environment_record_path` 语义清晰 |
| 环境记录边界 | Profile 只引用环境初始化记录，不复制运行投影正文 |
| 对象边界 | Profile 未替代 Intent、Task、Memo、ADR、docs 或环境初始化记录 |
| Human Gate | §5 场景已完成确认或记录降级 |
| Change 追溯 | Profile 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Profile Web 基础详情字段已同步，项目名册、项目切换和环境初始化记录专门入口待 Web 实现规划时补齐；
2. Profile 创建、激活、暂停、归档和项目切换的具体工作流程待 40-59 迁入后承接；
3. `project_kind` 是否需要扩展为更细的项目类型，待多项目实践后评估；
4. 多项目集中名册与各管辖项目自有 Profile 的关系，待产品初始化和产品审计流程迁入后进一步校准。
