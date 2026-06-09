# ADR-决策

> 创建日期：2026-06-09
> 定位：定义 ADR / 决策工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要管理长期决策、事实源边界、规范判断和后续执行约束的项目
> 上位依据：`docs/specs/05-工作模型基础规范.md`
> 相关规范：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/02-术语规范.md`、`docs/specs/03.04-工作模型文档规范.md`、`docs/specs/05.01-工作字段内容格式规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/08-Web信息同步规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/20-工作模型集合索引.md`、`docs/specs/22-Change-变更.md`、`docs/specs/24-Intent-意图.md`、`docs/specs/26-Task-任务.md`

---
## 1. 对象定位与准入条件

ADR / 决策是已确认或正在确认的长期决策记录，用于沉淀需要跨会话、跨任务、跨执行轮次或跨角色追溯的判断。ADR 记录为什么这样决定，docs/specs、Rules / Instructions 或其他规范入口记录以后必须怎么做。

ADR 不是所有判断的默认归宿。AI 可以在当前任务中做临时判断、记录分析结论或选择局部执行策略；只有影响长期行为边界、事实源归属、协作方式或规范体系的判断，才应进入 ADR 事实源。

### 1.1 ADR 准入条件

一个判断满足以下条件之一时，应考虑形成 ADR：

1. 影响多个 Task、Intent、工作模型、工作流程或项目阶段；
2. 改变长期执行方式、协作方式、事实源归属或 Human Gate 边界；
3. 改变 docs/specs、Rules / Instructions、Skill、Agent、Code、Web 或运行投影的长期规则；
4. 对后续 AI 或 Human 执行具有持续约束；
5. 多次重复出现，需要稳定记录选择理由；
6. 存在多个可行方案，需要保留选择与取舍；
7. 不记录会导致后续重复争论、误读或规则漂移。

创建 ADR 前，AI 必须说明准入理由、决策问题、备选方案、建议结论、影响范围和预期回写位置，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 ADR 的内容

以下内容通常不应单独形成 ADR：

1. 当前 Task 内的一次性执行策略；
2. 不影响后续协作的局部技术选择；
3. 尚未稳定的讨论、想法或资料；
4. 已由 docs/specs、Rules / Instructions 或其他正式规范明确约束的重复判断；
5. 仅属于风险判断、依赖关系、产物引用或检查结果的字段内容。

不形成 ADR 的内容，应按性质进入 Task 字段、Memo、docs/evals、docs/refs、当前执行上下文或对应事实源。

### 1.3 ADR 与规范的边界

ADR 记录决策背景、原因、选择和后果；正式规范记录稳定规则。ADR 不替代 docs/specs 正文、Rules / Instructions 执行入口、工作模型字段契约或工作流程行动规则。

当 ADR 中的决策需要成为长期规则时，应把规则正文吸收到对应正式规范或运行入口，ADR 保留决策原因和追溯关系。

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
| ADR 工作模型规范 | `docs/specs/21-ADR-决策.md` |
| ADR 实例 | `ldvh-base/adrs/` |
| ADR 字段内容格式 | `docs/specs/05.01-工作字段内容格式规范.md` |
| ADR 展示、聚合或查询结果 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

ADR 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

ADR 标准状态如下：

| 状态 | 含义 |
|---|---|
| `proposed` | 已提出，尚未确认，不得作为稳定执行依据 |
| `accepted` | 已确认，后续应遵守 |
| `deprecated` | 已废弃，不再建议遵守，但保留记录 |
| `superseded` | 已被新 ADR 替代 |
| `rejected` | 已否决，不采纳 |

`deprecated`、`superseded` 和 `rejected` 是稳定终态。终态 ADR 不得直接重开；如需重新判断，应新建 ADR，并在新 ADR 中引用原 ADR。

### 3.2 合法状态流转

```text
proposed → accepted
proposed → rejected
accepted → deprecated
accepted → superseded
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `proposed` → `accepted` | Human 已确认决策内容和影响范围 | 只有 accepted ADR 可作为稳定执行依据 |
| `proposed` → `rejected` | Human 否决该决策 | 应保留否决原因 |
| `accepted` → `deprecated` | 决策不再建议遵守，但没有明确替代 ADR | 应记录废弃原因 |
| `accepted` → `superseded` | 决策被新 ADR 替代 | `superseded_by` 条件必填 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 ADR 与 Intent

Intent 的实现涉及长期决策、方案选择或事实源边界时，应创建或关联 ADR。ADR 可通过 `related_intents` 引用来源 Intent。

ADR 不替代 Intent 的目标、成功标准、约束或完成判断。

### 4.2 ADR 与 Task

Task 执行过程中产生的判断满足 ADR 准入条件时，可升级为 ADR。ADR 可通过 `related_tasks` 引用来源 Task 或执行 Task。

ADR 不替代 Task 的验收标准、验证证据、风险判断或关闭证据。

### 4.3 ADR 与 Change

ADR 的创建、状态变化、核心决策改写、废弃、替代和升级为规范时，都应留下 Change。Change 的 commit message 契约由 `docs/specs/22-Change-变更.md` 定义。

### 4.4 ADR 与 Memo

Memo 中的输入满足 ADR 准入条件后，可以转化为 ADR。转化时应：

1. 保留 Memo 与 ADR 的引用关系；
2. 说明为什么从未任务化输入升级为长期决策；
3. 评估 Human Gate；
4. 不在 ADR 中复制 Memo 全文，只保留摘要和引用。

Memo 的准入、状态和字段契约由 `docs/specs/25-Memo-备忘.md` 定义。

### 4.5 ADR 与 docs/specs / Rules

ADR 中的决策升级为稳定规则时，应：

1. 将规则正文写入对应 docs/specs 正式规范、Rules / Instructions 或其他权威入口；
2. 在 ADR 的 `related_rules` 或 `affects` 中记录承接位置；
3. 保留 ADR 的背景、取舍和后果；
4. 通过 Change 留下变更追溯；
5. 经 Human Gate 确认。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 ADR 实例；
2. 将 Memo、Task 过程判断、临时讨论或 docs/evals 结论升级为 ADR；
3. 将 `proposed` ADR 确认为 `accepted`；
4. 将 `accepted` ADR 标记为 `deprecated` 或 `superseded`；
5. 修改 `accepted` ADR 的 `decision` 字段；
6. 将 ADR 决策升级为 docs/specs、Rules / Instructions、Skill、Agent、Code、Web 或运行投影规则；
7. 改变 ADR 的事实源载体、状态机、升级路径或终态语义；
8. 删除原 ADR 而不是通过状态表达废弃或替代。

推翻原决策时，不得删除原 ADR 文件。应将原 ADR 标记为 `superseded`，在 `superseded_by` 中引用新 ADR，并在新 ADR 的 `context` 中说明替代原因。废弃决策时，应将原 ADR 标记为 `deprecated`，并记录废弃原因。

Human Gate 的具体环境实体由 04 系列环境适配映射和运行投影记录承接。本文只规定 ADR 语境下需要确认的事实、影响范围和证据承接要求。

ADR 语境下的 Human Gate 记录应遵守 `docs/specs/06-工作流程基础规范.md` §6.3.1。创建、接受、废弃、替代、核心决策改写或升级为规范等场景中，确认记录至少应说明目标 ADR、决策变化、影响范围、确认依据、Human 决策、后续回写位置和残留风险。确认记录可以写入 ADR 的 `context`、`consequences`、`status_history`、相关 Task / Memo 或 Change / commit 证据中，但不得只停留在对话结论里。

---
## 6. 字段契约

### 6.1 字段表

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | ADR ID，格式为 `adr-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 对象类型 | string | 是 | 固定为 `adr` | Reference | AI、Code、Web |
| `title` | 决策标题 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 当前状态 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | 创建日期 | date | 是 | `YYYY-MM-DD` | Reference | AI、Code、Web |
| `updated` | 最近更新日期 | date | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `date` | 决策日期 | date | 是 | 通常与 accepted 日期一致，proposed 时可为提出日期 | Reference | AI、Web |
| `context` | 决策背景、问题和来源 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `decision` | 决策内容 | string | 是 | accepted 后核心内容变更需 Human Gate | Decision | AI、Human、Web |
| `consequences` | 决策后果、影响和约束 | string | 是 | 应说明正负影响 | Decision / Narrative | AI、Web |
| `alternatives` | 考虑过但未采纳的替代方案 | string | 否 | 可为空 | Narrative / Decision | AI、Web |
| `affects` | 受影响范围、文件、规范或机制 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_intents` | 关联 Intent ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_tasks` | 关联 Task ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_changes` | 关联 Change commit 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 来源或关联 Memo ID 列表 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_rules` | 决策已升级或承接的规范、Rules 路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `superseded_by` | 替代本决策的新 ADR ID | string | 条件必填 | `status: superseded` 时必须填写 | Reference | AI、Code、Web |
| `status_history` | 状态变化记录 | list[object] | 否 | 状态变化时追加时间、前后状态、原因和执行者 | Log | AI、Code |

字段内容格式按 `docs/specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

```yaml
id: adr-0001
type: adr
title: Change 使用 Git commit 记录承载
status: accepted
created: 2026-06-09
updated: 2026-06-09
date: 2026-06-09
context: |
  LDVH 需要记录事实源变更，但不希望为每次变更额外创建 YAML 实例。
decision: |
  Change 事实实例直接由 Git commit 记录承载，不创建 ldvh-base/changes/。
consequences: |
  - Git commit message 必须符合 Change 规范
  - Web 和 Code 只能派生展示 Change，不得替代 Git 记录
alternatives: |
  曾考虑创建 changes YAML 实例，但会与 Git 记录形成重复事实源。
affects:
  - docs/specs/22-Change-变更.md
related_intents: []
related_tasks: []
related_changes: []
related_memos: []
related_rules:
  - docs/specs/22-Change-变更.md
superseded_by:
status_history:
  - at: 2026-06-09
    from: proposed
    to: accepted
    actor: Human
    reason: 确认 Change 以 Git commit 作为事实实例
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

ADR 回写遵循以下规则：

1. 创建 ADR 时，应写入 `ldvh-base/adrs/`，并填写背景、决策、后果和影响范围；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`，并向 `status_history` 追加记录；
4. accepted ADR 的核心决策变更必须经 Human Gate，并通过 Change 留痕；
5. ADR 升级为规范或 Rules 后，应同步更新 `related_rules` 或 `affects`；
6. ADR 事实源写入后，应重新校验文件命名、字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

ADR 证据至少包括：

1. 决策背景；
2. 决策内容；
3. 替代方案或取舍说明；
4. 决策后果；
5. 影响范围；
6. Human Gate 确认记录；
7. 相关 Change、Task、Intent、Memo 或规范引用。

聊天内容、临时命令输出、Web 页面状态和工具缓存不得单独作为 ADR 证据。需要长期保留时，应摘要写入 ADR 字段或相关事实源。

---
## 8. 适配规则

### 8.1 AI 协作

AI 处理 ADR 时应遵守：

1. 先判断是否满足 ADR 准入条件，再提出创建建议；
2. `proposed` ADR 不得作为稳定执行依据；
3. `accepted` ADR 是后续执行应遵守的决策；
4. 读取 `superseded` ADR 时，应继续追踪 `superseded_by` 指向的新 ADR；
5. 创建、确认、废弃、替代、升级或删除 ADR 前评估 Human Gate；
6. 不得把 Task 字段中的风险判断、依赖关系、产物引用或检查结果误升级为 ADR，除非满足本文准入条件。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 ADR YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `superseded_by`、`related_rules` 和对象引用；
5. 聚合 ADR 状态、影响范围、替代链、关联对象和规范承接位置；
6. 检查 accepted ADR 的决策变更是否有 Change 和 Human Gate 记录。

Code 不得自行创建、接受、废弃、替代或删除 ADR，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/adrs/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 ADR 状态、决策内容、影响范围、关联对象、替代链、规范承接位置和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Web 不得在页面状态、缓存或数据库中维护独立 ADR 权威状态。受控编辑 ADR 字段时，应调用 Code 校验和受控写入链路，并遵守 Human Gate。

### 8.4 工作流程与环境适配

ADR 创建、确认、废弃、替代和升级为规范的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 ADR 实例的事实规则和状态约束。

环境不支持完整引用校验、替代链聚合或受控编辑时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | ADR 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、终态规则和事实源边界 | 05、03.04、本文、20 集合索引、22 Change、Human Gate | 工作模型治理 | 创建、修改、搬移、审计、接受、废弃或替代 ADR 时 |
| 入口可见要求 | AI 处理长期决策、规范判断、事实源边界、方案取舍或执行约束时，应能定位本文 | 20 集合索引、运行入口摘要、ADR 决策流程入口 | AI 执行入口提示 | 决策入口、规范升级、状态流转或字段契约变化时 |
| 确定性执行要求 | ADR 字段、状态、引用、文件命名、替代链和条件必填应由 Code 校验或记录缺口 | `docs/specs/07-Code实现规范.md`、ADR 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、引用关系、替代规则或相关规范路径变化时 |
| Human 交互要求 | ADR 创建、接受、废弃、替代、核心决策改写和升级为规范应触发 Human Gate，并按 06 §6.3.1 留下最小证据记录 | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | ADR 规范变化后，应检查 20、05.01、Change、Code、Web、运行投影和相关工作流程是否需要同步 | 集合索引维护、字段格式映射、Change 追溯、Code/Web 联动检查、人工降级检查 | 触发保障 | ADR 字段、状态、事实源边界、适配规则或检查要求变化时 |

---
## 10. 检查要求

ADR 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 ADR |
| 事实源位置 | 实例路径符合 `ldvh-base/adrs/adr-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 执行依据 | 只有 accepted ADR 可作为稳定执行依据 |
| 终态处理 | deprecated、superseded、rejected 不得重开 |
| 替代链 | superseded ADR 已填写 `superseded_by` |
| 规范边界 | ADR 不替代 docs/specs 或 Rules / Instructions 正文 |
| Human Gate | §5 场景已完成确认并符合 06 §6.3.1，或记录降级 |
| Change 追溯 | ADR 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. ADR 校验 Code 待字段契约稳定后补齐正反样例；
2. ADR Web 展示和受控编辑入口待 Web 实现规划时补齐；
3. ADR 创建、接受、废弃、替代和升级为规范的具体工作流程待 40-59 承接；
4. 是否需要 ADR 定期审查机制，待更多实例实践后评估。
