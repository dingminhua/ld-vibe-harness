# Pitfall-踩坑

> 创建日期：2026-06-09
> 定位：定义 Pitfall / 踩坑工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要沉淀已解决、已验证且具有复用价值的踩坑经验的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/02-术语规范.md`、`specs/03.03-工作模型文档规范.md`、`specs/05.01-工作字段内容格式规范.md`、`specs/07-Code确定性执行实现规范.md`、`specs/08-Web信息同步实现规范.md`、`specs/09-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`、`specs/21-ADR-决策.md`、`specs/22-Change-变更.md`、`specs/24-WorkArea-工作域.md`、`specs/27-TaskPlan-任务计划.md`、`specs/25-Memo-备忘.md`、`specs/26-Task-任务.md`

---
## 1. 对象定位与准入条件

Pitfall / 踩坑是已解决、已验证且具有复用价值的经验事实，用于沉淀反直觉问题、误判原因、触发条件、根因、解决方式、验证结果和后续规避策略。

Pitfall 的目标是让 AI 和 Human 在后续执行中提前识别同类陷阱。它不是所有 bug、失败命令、临时阻塞、未验证猜测或复盘感想的默认归宿。只有问题已经被解决，且后续执行可能复现同类误判或重复踩坑时，才应进入 Pitfall 事实源。

### 1.1 Pitfall 准入条件

一个经验满足以下条件之一时，应考虑形成 Pitfall：

1. 问题已经解决，且解决方式已验证；
2. 问题具有反直觉性，AI 或 Human 后续容易重复误判；
3. 问题跨 WorkArea、TaskPlan、Task、项目阶段或管辖项目具有复用价值；
4. 问题暴露了事实源读取、字段契约、Code 使用、Web 派生视图、环境适配、适配措施或工作流程中的稳定陷阱；
5. 同类问题已经出现多次，需要形成规避策略；
6. 问题可作为后续规范、Rules / Instructions、Skill、Agent、Code、Web、ADR 或工作流程改进的输入。

创建 Pitfall 前，AI 必须说明准入理由、问题是否已解决、验证证据、适用范围、规避策略和预期回写位置，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 Pitfall 的内容

以下内容通常不应单独形成 Pitfall：

1. 尚未解决的问题；
2. 未验证的猜测、假设或临时判断；
3. 只影响当前一次执行且没有复用价值的错误；
4. 单纯的命令输出、日志片段或失败记录；
5. 已由 specs、Rules / Instructions、ADR、Task 或 Code 明确约束，且没有新增经验的信息；
6. 没有规避策略的抱怨、复盘感想或笼统提醒。

不形成 Pitfall 的内容，应按性质留在当前执行上下文，或进入 Memo、Task、ADR、Change、docs、sources、studies、Code 测试或其他权威位置。

### 1.3 Pitfall 与规范、运行入口和实现的边界

Pitfall 记录为什么会踩坑、如何解决、如何验证和以后如何规避。正式规范、Rules / Instructions、Skill、Agent、Code、Web 或工作流程记录以后必须怎么做、如何执行、如何校验或如何呈现。

当 Pitfall 中的规避策略需要成为长期强制行为时，应将规则正文吸收到对应正式规范、运行入口、Code、Web 或工作流程。Pitfall 保留问题背景、根因、验证证据和被吸收位置的引用，不替代被吸收后的权威规则。

---
## 2. 事实源边界

本文是 Pitfall 工作模型的权威规范，定义 Pitfall 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

Pitfall 实例的权威事实源位置为：

```text
ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Pitfall 工作模型规范 | `specs/23-Pitfall-踩坑.md` |
| Pitfall 实例 | `ldvh-base/pitfalls/` |
| Pitfall 字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| Pitfall 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

Pitfall 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Pitfall 标准状态如下：

| 状态 | 含义 |
|---|---|
| `draft` | 已记录草稿，尚未确认符合准入条件或字段完整性不足 |
| `active` | 已确认，问题已解决且可作为后续执行参考 |
| `superseded` | 已被新的 Pitfall、ADR、规范、运行入口、Code、Web 或工作流程替代 |
| `archived` | 已归档，不再作为常规参考，但保留记录 |

`superseded` 和 `archived` 是稳定终态。终态 Pitfall 不得直接重开；如需重新沉淀，应新建 Pitfall，并在新 Pitfall 中引用原 Pitfall。

### 3.2 合法状态流转

```text
draft → active
draft → archived
active → superseded
active → archived
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `draft` → `active` | 问题已解决、解决方式已验证、规避策略已可复用 | 只有 active Pitfall 可作为稳定执行参考 |
| `draft` → `archived` | 记录后判断不满足准入条件或不需要继续保留 | 应记录归档原因 |
| `active` → `superseded` | 已被新 Pitfall、ADR、规范、运行入口或实现替代 | `superseded_by` 条件必填 |
| `active` → `archived` | 经验不再常规适用，但保留记录 | 应记录归档原因 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 Pitfall 与 Task

Task 执行、验证或关闭过程中发现的已解决且可复用经验，可以整理为 Pitfall。Pitfall 可通过 `source_tasks` 记录来源 Task。

Task 的准入、状态和字段契约由 `specs/26-Task-任务.md` 定义。Pitfall 不替代 Task 的验收标准、验证证据、关闭证据、风险判断或缺陷修复动作。

### 4.2 Pitfall 与 Memo

Memo 中保留的发现、提醒、复盘线索或问题线索满足 Pitfall 准入条件后，可以分流为 Pitfall。分流后，Pitfall 的 `source_memos` 应记录来源 Memo，Memo 的 `resolved_to` 可记录 Pitfall ID。

Memo 的准入、状态和字段契约由 `specs/25-Memo-备忘.md` 定义。

### 4.3 Pitfall 与 WorkArea / TaskPlan

工作域和任务计划可以通过 `related_pitfalls` 引用执行过程中形成或需要参考的踩坑经验。Pitfall 可通过 `related_workareas` 记录关联工作域，通过 `related_taskplans` 记录关联任务计划。

WorkArea 的准入、状态和字段契约由 `specs/24-WorkArea-工作域.md` 定义；TaskPlan 的准入、状态和字段契约由 `specs/27-TaskPlan-任务计划.md` 定义。Pitfall 不替代 WorkArea 的长期范围，也不替代 TaskPlan 的目标、成功标准、任务序列或关闭判断。

### 4.4 Pitfall 与 ADR

Pitfall 和 ADR 是独立工作模型。经验是经验，决策是决策，两者可以关联但不可互相替代。

当 Pitfall 暴露的问题需要形成长期决策、改变事实源归属、改变规范边界或影响多个工作模型时，应创建或关联 ADR。Pitfall 可通过 `related_adrs` 引用相关 ADR。

ADR 的准入、状态和字段契约由 `specs/21-ADR-决策.md` 定义。

### 4.5 Pitfall 与 Change

Pitfall 的创建、状态变化、核心经验改写、归档、替代和被吸收到规范、运行入口、Code、Web 或工作流程时，都应留下 Change。Change 的 commit message 契约由 `specs/22-Change-变更.md` 定义。

### 4.6 Pitfall 与规范、Code、Web 和运行入口

当 Pitfall 中的规避策略需要长期生效时，应按内容性质分流：

| 需要沉淀的内容 | 承接位置 |
|---|---|
| 强制规则、字段契约、事实源边界或 Human Gate | specs 正式规范 |
| 高频入口提示或硬约束摘要 | Rules / Instructions 适配措施 |
| 可复用多步骤流程 | Skill 或工作流程规范 |
| 独立、专项或并行审查视角 | Agent 适配措施或工作流程规范 |
| 可机械化校验、解析、聚合或受控写入 | Code 实现 |
| Human-facing 展示、确认或受控轻写入 | Web 信息同步实现 |

分流后，Pitfall 应保留经验事实和被吸收位置引用，不得复制并维护第二份规则正文。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Pitfall 实例；
2. 将 Task 过程发现、Memo、docs/studies 结论或对话输入升级为 Pitfall；
3. 将 `draft` Pitfall 确认为 `active`；
4. 将 `active` Pitfall 标记为 `superseded` 或 `archived`；
5. 修改 `root_cause`、`resolution`、`verification` 或 `avoidance` 等核心经验字段；
6. 将 Pitfall 的规避策略吸收到 specs、Rules / Instructions、Skill、Agent、Code、Web 或工作流程；
7. 将未解决或未验证问题写成 `active` Pitfall；
8. 删除原 Pitfall 而不是通过状态表达归档或替代。

Human Gate 的具体环境实体由 04 系列环境适配项和适配措施记录承接。本文只规定 Pitfall 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 字段表

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | Pitfall ID，格式为 `pitfall-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `pitfall` | Reference | AI、Code、Web |
| `title` | 踩坑标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建时间 | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | 最近更新时间 | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `symptoms` | 问题现象、错误表现或误判结果 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `trigger_conditions` | 触发条件、上下文或复现场景 | string | 是 | 应说明何时可能复现 | Narrative / Checklist | AI、Code、Web |
| `root_cause` | 根因或误判原因 | string | 是 | active 时必须明确 | Narrative | AI、Human、Web |
| `resolution` | 解决方式 | string | 是 | active 时必须可执行 | Narrative / Evidence | AI、Code、Web |
| `verification` | 验证方式、验证命令或验证结论 | string | 是 | active 时必须填写 | Evidence | AI、Code、Web |
| `avoidance` | 后续规避策略 | string | 是 | active 时必须可复用 | Narrative / Checklist | AI、Human、Web |
| `applicability` | 适用范围和不适用范围 | string | 是 | 应避免泛化过度 | Narrative | AI、Web |
| `repeatability` | 复现或重复概率 | string | 否 | `unknown`、`once`、`recurring`，默认 `unknown` | Reference | AI、Code、Web |
| `tags` | 标签列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `source_tasks` | 来源 Task ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `source_memos` | 来源 Memo ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workareas` | 关联 WorkArea ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_taskplans` | 关联 TaskPlan ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联 ADR ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_changes` | 关联 Change commit 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_rules` | 已吸收或承接该经验的规范、Rules、Skill、Agent、Code 或 Web 路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `superseded_by` | 替代本经验的新对象、规范或实现引用 | string | 条件必填 | `status: superseded` 时必须填写 | Reference | AI、Code、Web |
| `archive_reason` | 归档原因 | string | 条件必填 | `status: archived` 时应填写 | Narrative | AI、Human |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |
| `notes` | 补充说明 | string | 否 | 不得承载规则正文第二事实源 | Narrative / Reference | AI、Web |

字段内容格式按 `specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: pitfall-0001
type: pitfall
title: 把参考与研究材料直接当成当前权威规范
status: active
created: '2026-06-09T00:00:00'
updated: '2026-06-09T00:00:00'
symptoms: |
  AI 在吸收参考与研究材料或临时参考中的规则时，未先判断该内容是否已经吸收到 specs。
trigger_conditions: |
  - [x] 参考与研究材料内容比当前正式规范更详细
  - [x] 当前主题存在候选事项或待补齐事项
root_cause: |
  参考与研究材料不是当前权威事实源；直接引用会绕过正式规范的吸收和重写边界。
resolution: |
  先读取 specs 的对应正文和集合索引，再把参考与研究材料只作为比较和吸收来源。
verification: |
  已通过 01、03、09 和 20 的参考与研究材料边界检查。
avoidance: |
  - [x] 修改正式规范前先确认对应规范是否已经存在或登记为候选事项
  - [x] 参考与研究材料只在参考与研究材料语境下引用
applicability: |
  适用于 specs 维护、参考与研究材料吸收和规范边界检查任务。
repeatability: recurring
tags:
  - input-material
  - fact-source
source_tasks: []
source_memos: []
related_workareas: []
related_taskplans: []
related_adrs: []
related_changes: []
related_docs:
  - specs/01-目录说明.md
  - specs/09-事实源边界与承载规范.md
related_rules:
  - specs/20-工作模型集合索引.md
superseded_by:
archive_reason:
status_history:
  - at: 2026-06-09
    from:
    to: active
    actor: AI
    reason: 更新 Pitfall 工作模型
notes:
```

### 6.3 字段约束

1. `status` 必须属于 Pitfall 标准状态枚举：`draft`、`active`、`superseded`、`archived`；
2. `type` 必须固定为 `pitfall`；
3. `id` 格式必须为 `pitfall-{NNNN}`，编号固定 4 位；
4. `active` Pitfall 必须具备 `symptoms`、`trigger_conditions`、`root_cause`、`resolution`、`verification`、`avoidance` 和 `applicability`；
5. `status: superseded` 时必须填写 `superseded_by`；
6. `status: archived` 且未被替代时，应填写 `archive_reason`；
7. `repeatability` 如填写，必须属于 `unknown`、`once`、`recurring`；
8. 不得使用 `severity` 字段；影响和后果应写入 `symptoms`、`applicability`、`avoidance` 或 `notes`；
9. `related_*` 和 `source_*` 列表应引用已存在对象、commit 或路径；引用无效时应报告校验警告；
10. `created` 和 `updated` 使用 ISO 8601 时间戳格式；
11. 列表字段可为空列表，不得省略字段后以 null 替代空列表。

### 6.4 文件命名契约

Pitfall 实例文件命名规则为 `pitfall-{NNNN}-short-title.yaml`。编号从 `0001` 起递增，固定 4 位；英文短标题使用小写短横线命名；文件存放位置为 `ldvh-base/pitfalls/`。

文件名变化必须同步检查引用该 Pitfall 的 WorkArea、TaskPlan、Task、Memo、ADR、Change、Web 派生视图和 Code 聚合结果。

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Pitfall 回写遵循以下规则：

1. 创建 Pitfall 时，应写入 `ldvh-base/pitfalls/`，并填写问题现象、触发条件、根因、解决方式、验证方式、规避策略和适用范围；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`，并向 `status_history` 追加记录；
4. Pitfall 被吸收到规范、运行入口、Code、Web 或工作流程后，应更新 `related_rules` 或相关引用；
5. Pitfall 创建、状态变化、核心经验改写、归档或替代应通过 Change 留痕；
6. Pitfall 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

Pitfall 证据至少包括：

1. 问题现象；
2. 触发条件；
3. 根因或误判原因；
4. 解决方式；
5. 验证方式或验证结论；
6. 规避策略；
7. 适用范围和不适用范围；
8. Human Gate 确认记录；
9. 相关 Task、Memo、ADR、Change、docs、规范或 Code 引用。

证据摘要应足以支持经验复用判断，但不得复制大量日志、命令输出、代码片段或外部资料形成第二事实源。

---
## 8. 适配边界

### 8.1 AI 协作

AI 处理 Pitfall 时应遵守：

1. 先判断经验是否满足 Pitfall 准入条件；
2. `draft` Pitfall 不得作为稳定执行依据；
3. 读取 `superseded` Pitfall 时，应继续追踪 `superseded_by` 指向的新对象、规范或实现；
4. 创建、激活、归档、替代或核心经验改写前评估 Human Gate；
5. 进入代码、文档、规范、环境适配或工具修改前，可按任务类型、文件路径、技术栈、标签和事实源类型筛选 active Pitfall；
6. 不得把未解决问题、未验证猜测或一次性失败直接写成 active Pitfall；
7. 不得让 Pitfall 替代 Task、Memo、ADR、规范、Code 测试或 Change。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Pitfall YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `repeatability`、`superseded_by` 和引用字段，并对旧字段 `severity` 报告迁移诊断；
5. 按 tags、状态、适用范围、来源对象和相关文档聚合 Pitfall；
6. 在任务执行前生成相关 active Pitfall 摘要。

Code 不得自行创建、激活、归档、替代或删除 Pitfall，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/pitfalls/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Pitfall 状态、症状、触发条件、根因、解决方式、验证结论、规避策略、适用范围、标签、替代链和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Web 不得在页面状态、缓存或数据库中维护独立 Pitfall 权威状态。受控编辑 Pitfall 字段时，应调用 Code 校验和受控写入链路，并遵守 Human Gate。

### 8.4 工作流程与环境适配

Pitfall 识别、创建、激活、归档、替代和吸收到规范或实现的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Pitfall 实例的事实规则和状态约束。

环境不支持相关 Pitfall 检索、替代链聚合或受控编辑时，应记录降级方式，例如改用人工搜索、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Pitfall 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、经验吸收边界和事实源边界 | 05、03.03、本文、20 集合索引、21 ADR、25 Memo、26 Task、Human Gate | 工作模型治理 | 创建、修改、搬移、审计、激活、归档或替代 Pitfall 时 |
| 入口可见要求 | AI 处理已解决可复用经验、反直觉问题、重复误判或规避策略时，应能定位本文 | 20 集合索引、运行入口摘要、Pitfall 检索或经验吸收流程入口 | AI 执行入口提示 | 经验沉淀、任务执行前检查、状态流转或字段契约变化时 |
| 确定性执行要求 | Pitfall 字段、状态、引用、文件命名、条件必填、标签和替代链应由 Code 校验或记录缺口 | `specs/07-Code确定性执行实现规范.md`、Pitfall 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、引用关系、替代规则或标签规则变化时 |
| Human 交互要求 | Pitfall 创建、激活、归档、替代、核心经验改写和吸收到规范或实现时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Pitfall 规范变化后，应检查 20、05.01、ADR、Memo、Task、Code、Web、适配措施和相关工作流程是否需要同步 | 集合索引维护、字段格式映射、对象关系检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Pitfall 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

Pitfall 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Pitfall |
| 事实源位置 | 实例路径符合 `ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| active 可用性 | active Pitfall 已解决、已验证、具备规避策略和适用范围 |
| 终态处理 | superseded 和 archived 不得重开 |
| 替代链 | superseded Pitfall 已填写 `superseded_by` |
| 对象边界 | Pitfall 未替代 Task、Memo、ADR、规范、Code 测试或 Change |
| 经验吸收边界 | 规避策略被吸收后只保留引用，不复制规则正文第二事实源 |
| Human Gate | §5 场景已完成确认或记录降级 |
| Change 追溯 | Pitfall 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Pitfall Web 基础详情字段已同步，筛选和任务执行前提示入口待 Web 实现规划时补齐；
2. Pitfall 识别、创建、激活、归档、替代和吸收的具体工作流程待 40-59 承接；
3. `repeatability` 和 `tags` 的枚举范围待更多实例实践后评估；
4. Pitfall 与工作流程中 Learn 阶段的关系，待 40-59 稳定后进一步校准。
