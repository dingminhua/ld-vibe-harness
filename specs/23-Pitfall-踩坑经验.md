# Pitfall-踩坑经验

```yaml
ldvh_doc:
  doc_id: "23"
  doc_kind: "work_model_spec"
  title: "Pitfall-踩坑经验"
  status: "active"
  canonical_path: "specs/23-Pitfall-踩坑经验.md"
  created: "2026-06-09"
  updated: "2026-06-09"
  parent_doc: ""
  relation: ""
  positioning: "定义 Pitfall / 踩坑经验事实模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则"
  scope: "所有接入 LDVH 且需要沉淀已解决、已验证且具有复用价值的踩坑经验的项目"
  basis:
    - "specs/05-工作模型基础规范.md"
  related_specs:
    - "specs/05.01-工作模型字段定义与语义规范.md"
    - "specs/05.02-工作模型字段内容与格式规范.md"
    - "specs/05.03-工作模型字段注册与消费规范.md"
    - "specs/07-Code确定性执行实现规范.md"
    - "specs/21-WorkCase-工作项.md"
    - "specs/22-ADR-决策.md"
    - "specs/20-Spark-火花.md"
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
  spec_id: "23"
  kind: work_model
  name_en: Pitfall
  name_zh: 踩坑经验
  collection_status: active
  canonical_path: specs/23-Pitfall-踩坑经验.md
  instance_root: ldvh-base/pitfalls/
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

Pitfall / 踩坑经验是已解决、已验证且具有复用价值的经验事实，用于沉淀反直觉问题、误判原因、触发条件、根因、解决方式、验证结果和后续规避策略。

Pitfall 的目标是让 AI 和 Human 在后续执行中提前识别同类陷阱。它不是所有 bug、失败命令、临时阻塞、未验证猜测或复盘感想的默认归宿。只有问题已经被解决，且后续执行可能复现同类误判或重复踩坑时，才应进入 Pitfall 事实源。

### 1.1 Pitfall 准入条件

一个经验满足以下条件之一时，应考虑形成 Pitfall：

1. 问题已经解决，且解决方式已验证；
2. 问题具有反直觉性，AI 或 Human 后续容易重复误判；
3. 问题跨 WorkCase、项目阶段或管辖项目具有复用价值；
4. 问题暴露了事实源读取、字段契约、Code 使用、Web 派生视图、环境适配、适配措施或行动编排中的稳定陷阱；
5. 同类问题已经出现多次，需要形成规避策略；
6. 问题可作为后续规范、Rules / Instructions、Skill、Agent、Code、Web、ADR 或行动编排改进的输入。

创建 Pitfall 前，AI 必须说明准入理由、问题是否已解决、验证证据、适用范围、规避策略和预期回写位置，并按本文 §5 评估 Human Gate。

### 1.2 不应形成 Pitfall 的内容

以下内容通常不应单独形成 Pitfall：

1. 尚未解决的问题；
2. 未验证的猜测、假设或临时判断；
3. 只影响当前一次执行且没有复用价值的错误；
4. 单纯的命令输出、日志片段或失败记录；
5. 已由 specs、Rules / Instructions、ADR、WorkCase 或 Code 明确约束，且没有新增经验的信息；
6. 没有规避策略的抱怨、复盘感想或笼统提醒。

不形成 Pitfall 的内容，应按性质留在当前执行上下文，或进入 Spark、WorkCase、ADR、docs、sources、studies、Code 测试、Git 提交记录或其他权威位置。

### 1.3 Pitfall 与规范、运行入口和实现的边界

Pitfall 记录为什么会踩坑、如何解决、如何验证和以后如何规避。正式规范、Rules / Instructions、Skill、Agent、Code、Web 或行动编排记录以后必须怎么做、如何执行、如何校验或如何呈现。

当 Pitfall 中的规避策略需要成为长期强制行为时，应将规则正文吸收到对应正式规范、运行入口、Code、Web 或行动编排。Pitfall 保留问题背景、根因、验证证据和被吸收位置的引用，不替代被吸收后的权威规则。

---
## 2. 事实源边界

本文是 Pitfall 事实模型的权威规范，定义 Pitfall 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。

Pitfall 实例的权威事实源位置为：

```text
ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Pitfall 事实模型规范 | `specs/23-Pitfall-踩坑经验.md` |
| Pitfall 实例 | `ldvh-base/pitfalls/` |
| Pitfall 字段内容格式 | `specs/05.02-工作模型字段内容与格式规范.md` |
| Pitfall 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

Pitfall 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 标准状态

Pitfall 标准状态如下：

| 状态 | 含义 |
|---|---|
| `active` | 已确认，问题已解决、解决方式已验证，且可作为后续执行参考 |
| `archived` | 已归档，不再作为常规参考，但保留历史经验、归档原因和必要关联 |

Pitfall 不设 `draft` 状态。未解决、未验证或字段不完整的问题不得写成 Pitfall；应留在 Spark、WorkCase、对话上下文或其他更合适的事实源中继续消化。

`archived` 是稳定终态。终态 Pitfall 不得直接重开；如需重新沉淀，应新建 Pitfall，并在新 Pitfall 中引用原 Pitfall。

### 3.2 合法状态流转

```text
active → archived
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` → `archived` | 经验不再常规适用、已被规范或实现吸收，或不再需要作为常规参考 | 必须记录归档原因；如已被吸收，应在 `archive_reason` 和关联字段中说明承接位置 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 Pitfall 与 WorkCase

工作项执行、验证或关闭过程中发现的已解决且可复用经验，可以整理为 Pitfall。Pitfall 可通过 `source_objects` 或 `related_workcases` 记录来源工作项。

Pitfall 不替代 WorkCase 的成功标准、验证证据、关闭证据、风险判断或缺陷修复动作。

### 4.2 Pitfall 与 Spark

Spark 中保留的发现、提醒、复盘线索或问题线索满足 Pitfall 准入条件后，可以分流为 Pitfall。分流后，Pitfall 的 `source_sparks` 应记录来源 Spark，Spark 的 `resolved_to` 可记录 Pitfall ID。

Spark 的准入、状态和字段契约由 `specs/20-Spark-火花.md` 定义。

### 4.3 Pitfall 与 WorkCase

工作项可以通过 `related_pitfalls` 引用执行过程中形成或需要参考的踩坑经验。Pitfall 可通过 `related_workcases` 记录关联工作项。

WorkCase 的准入、状态和字段契约由 `specs/21-WorkCase-工作项.md` 定义。Pitfall 不替代 WorkCase 的目标、成功标准、执行编排或关闭判断。

### 4.4 Pitfall 与 ADR

Pitfall 和 ADR 是独立事实模型。经验是经验，决策是决策，两者可以关联但不可互相替代。

当 Pitfall 暴露的问题需要形成长期决策、改变事实源归属、改变规范边界或影响多个事实模型时，应创建或关联 ADR。Pitfall 可通过 `related_adrs` 引用相关 ADR。

ADR 的准入、状态和字段契约由 `specs/22-ADR-决策.md` 定义。

### 4.5 Pitfall 与 Git 提交记录

Pitfall 的创建、状态变化、核心经验改写、归档和被吸收到规范、运行入口、Code、Web 或行动编排时，都应留下 Git 提交记录。commit message 格式规则由 `specs/10-Git提交规范.md` 定义。

### 4.6 Pitfall 与规范、Code、Web 和运行入口

当 Pitfall 中的规避策略需要长期生效时，应按内容性质分流：

| 需要沉淀的内容 | 承接位置 |
|---|---|
| 强制规则、字段契约、事实源边界或 Human Gate | specs 正式规范 |
| 高频入口提示或硬约束摘要 | Rules / Instructions 适配措施 |
| 可复用多步骤流程 | Skill 或行动编排规范 |
| 独立、专项或并行审查视角 | Agent 适配措施或行动编排规范 |
| 可机械化校验、解析、聚合或受控写入 | Code 实现 |
| Human-facing 展示、确认或受控轻写入 | Web 信息同步实现 |

分流后，Pitfall 应保留经验事实和被吸收位置引用，不得复制并维护第二份规则正文。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Pitfall 实例；
2. 将 WorkCase 过程发现、Spark、docs/studies 结论或对话输入升级为 Pitfall；
3. 将 `active` Pitfall 标记为 `archived`；
5. 修改 `root_cause`、`resolution`、`verification` 或 `avoidance` 等核心经验字段；
6. 将 Pitfall 的规避策略吸收到 specs、Rules / Instructions、Skill、Agent、Code、Web 或行动编排；
7. 将未解决或未验证问题写成 `active` Pitfall；
8. 删除原 Pitfall 而不是通过 `archived` 表达归档或吸收。

Human Gate 的具体环境实体由 04 系列环境适配项和适配措施记录承接。本文只规定 Pitfall 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 字段表

公共字段语义定义见 `specs/05.01-工作模型字段定义与语义规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `pitfall-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `pitfall` | string | 是 | 固定为 `pitfall` | Reference | AI、Code、Web |
| `title` | 踩坑经验一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举 | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `symptoms` | 问题现象、错误表现或误判结果 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `trigger_conditions` | 触发条件、上下文或复现场景 | string | 是 | 应说明何时可能复现 | Narrative | AI、Code、Web |
| `root_cause` | 根因或误判原因 | string | 是 | active 时必须明确 | Narrative | AI、Human、Web |
| `resolution` | 解决方式 | string | 是 | active 时必须可执行 | Narrative | AI、Code、Web |
| `verification` | 经验可用性的验证证据 | string | 是 | active 时必须填写；按 05.02 四段式验证证据结构书写 | 验证证据 | AI、Code、Web |
| `avoidance` | 后续规避策略 | string | 是 | active 时必须可复用 | Narrative | AI、Human、Web |
| `applicability` | 适用范围和不适用范围 | string | 是 | 应避免泛化过度 | Narrative | AI、Web |
| `tags` | 英文标签列表 | list[string] | 否 | 默认为空列表；写入前应参考已有标签 | Reference | AI、Code、Web |
| `source_objects` | 来源对象 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `source_sparks` | 来源火花 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workcases` | 关联工作项 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 关联文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_rules` | 已吸收或承接该经验的规范、Rules、Skill、Agent、Code 或 Web 路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `archive_reason` | 归档原因；如已被规范、Rules、Skill、Agent、Code、Web 或行动编排吸收，应说明承接位置 | string | 条件必填 | `status: archived` 时必须填写 | Narrative | AI、Human |
| `notes` | 不得承载规则正文第二事实源 | string | 否 | 不得承载规则正文第二事实源 | Narrative / Reference | AI、Web |

字段内容格式按 `specs/05.02-工作模型字段内容与格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。

### 6.2 YAML 示例

````yaml
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
  ## 验证计划

  检查规范维护任务是否会先确认参考材料边界，再修改正式 specs。

  ## 验证命令

  ```bash
  python3 code/specs_validate.py refs specs
  ```

  ## 验证结果

  已通过 01、03、09 和 20 的参考与研究材料边界检查。

  ## 结论

  该经验已具备复用价值，可作为 active Pitfall。
avoidance: |
  - [x] 修改正式规范前先确认对应规范是否已经存在或登记为候选事项
  - [x] 参考与研究材料只在参考与研究材料语境下引用
applicability: |
  适用于 specs 维护、参考与研究材料吸收和规范边界检查任务。
tags:
  - input-material
  - fact-source
source_objects: []
source_sparks: []
related_workcases: []
related_adrs: []
related_docs:
  - specs/01-目录说明.md
  - specs/09-事实源边界与承载规范.md
related_rules:
  - specs/03.02-工作模型文档规范.md
archive_reason:
notes:
````

### 6.3 字段约束

1. `status` 必须属于 Pitfall 标准状态枚举：`active`、`archived`；
2. `type` 必须固定为 `pitfall`；
3. `id` 格式必须为 `pitfall-{NNNN}`，编号固定 4 位；
4. `active` Pitfall 必须具备 `symptoms`、`trigger_conditions`、`root_cause`、`resolution`、`verification`、`avoidance` 和 `applicability`；
5. `status: archived` 时必须填写 `archive_reason`；如果归档原因是已被规范或实现吸收，应同步填写 `related_rules`、`related_docs`、`related_adrs` 或其他关联字段；
6. 不得使用 `repeatability` 字段；复现和重复踩坑判断应写入 `trigger_conditions`、`applicability` 和 `avoidance`；
7. 不得使用 `severity` 字段；影响和后果应写入 `symptoms`、`applicability`、`avoidance` 或 `notes`；
8. `related_*` 和 `source_*` 列表应引用已存在对象、commit 或路径；引用无效时应报告校验警告；
9. `created` 和 `updated` 使用 ISO 8601 时间戳格式；
10. 列表字段可为空列表，不得省略字段后以 null 替代空列表；
11. `tags` 必须使用英文 slug，推荐小写短横线格式；不得使用中文标签、空格、展示翻译或一次性临时短语；
12. 写入或修改 Pitfall `tags` 前，Code 应提供当前事实源中已有标签清单，AI 应优先复用已有标签；已有标签无法表达当前经验时可以新增英文标签；
13. `verification` 必须按 `specs/05.02-工作模型字段内容与格式规范.md` §3.3 的四段式验证证据结构书写，不得只写“已验证”“通过”或把验证结果混入 `resolution`。
14. `symptoms`、`trigger_conditions`、`root_cause`、`resolution`、`avoidance` 和 `applicability` 等阅读节点字段可以使用 Markdown 段落或列表，但不得通过手写前导空格模拟缩进排版；需要条目时使用标准 Markdown 列表，需要普通说明时使用顶格段落。
15. `root_cause`、`resolution` 和 `avoidance` 应优先写成可独立阅读的原子条目；每个条目只表达一个原因、一个动作或一个规避规则，不应把多个判断用分号串成一段长句。
16. `trigger_conditions` 可使用短段落描述触发上下文；当触发条件超过一个时，应改用 Markdown 列表，让 Web 能稳定呈现为条目化经验。
17. 无明确顺序、步骤或优先级的经验条目应使用无序列表；只有表达必须按序执行、先后依赖或编号本身有事实含义时，才使用 `1.`、`2.`、`3.` 有序列表。

### 6.4 文件命名契约

Pitfall 实例文件命名规则为 `pitfall-{NNNN}-short-title.yaml`。编号从 `0001` 起递增，固定 4 位；英文短标题使用小写短横线命名；文件存放位置为 `ldvh-base/pitfalls/`。

文件名变化必须同步检查引用该 Pitfall 的 WorkCase、Spark、ADR、Web 派生视图、Git 提交记录和 Code 聚合结果。

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Pitfall 回写遵循以下规则：

1. 创建 Pitfall 时，应写入 `ldvh-base/pitfalls/`，并填写问题现象、触发条件、根因、解决方式、验证方式、规避策略和适用范围；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit 派生，不在 Pitfall YAML 中手写维护；
4. Pitfall 被吸收到规范、运行入口、Code、Web 或行动编排后，应更新 `related_rules` 或相关引用；
5. Pitfall 创建、状态变化、核心经验改写、归档或被吸收应通过 Git 提交记录留痕；
6. Pitfall 事实源写入前，应查询并呈现当前已有 `tags`，供 AI/Human 选择复用或确认新增；
7. Pitfall 事实源写入后，应重新校验文件命名、字段完整性、状态合法性、标签格式和引用有效性。

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
9. 相关 WorkCase、Spark、ADR、docs、规范、Code 或 Git 提交引用。

证据摘要应足以支持经验复用判断，但不得复制大量日志、命令输出、代码片段或外部资料形成第二事实源。

---
## 8. 适配边界

### 8.1 AI 协作

AI 处理 Pitfall 时应遵守：

1. 先判断经验是否满足 Pitfall 准入条件；
2. 不得把未解决、未验证或字段不完整的问题写成 Pitfall；
3. 读取 `archived` Pitfall 时，应查看 `archive_reason` 和关联字段，判断是否已被规范、运行入口或实现吸收；
4. 创建、归档或核心经验改写前评估 Human Gate；
5. 进入代码、文档、规范、环境适配或工具修改前，可按任务类型、文件路径、技术栈、标签和事实源类型筛选 active Pitfall；
6. 不得把未解决问题、未验证猜测或一次性失败直接写成 active Pitfall；
7. 写入或修改 `tags` 时，应先查看 Code 提供的已有标签清单，优先复用，必要时再新增英文 slug；
8. 不得让 Pitfall 替代 WorkCase、Spark、ADR、规范、Code 测试或 Git 提交记录。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Pitfall YAML；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验引用字段、`archive_reason` 条件必填，并对旧字段 `repeatability`、`severity`、`superseded_by` 报告迁移诊断；
5. 按 tags、状态、适用范围、来源对象和相关文档聚合 Pitfall；
6. 在 Pitfall 写入或修改前提供当前已有 tags 清单，辅助 AI/Human 复用已有标签或确认新增英文标签；
7. 在任务执行前生成相关 active Pitfall 摘要。

Code 不得自行创建、归档、删除 Pitfall 或改写核心经验，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/pitfalls/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Pitfall 状态、症状、触发条件、根因、解决方式、验证结论、规避策略、适用范围、标签、归档原因、吸收关系和待确认项。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Pitfall 详情页是可复用经验阅读页，不按普通字段卡片堆叠。主节点固定为“现象、触发、根因、方案、验证、规避、范围、关联”，节点标题栏整行可点击，默认全部打开，折叠图标规则与 Study 一致。`verification` 节点消费 `specs/05.02-工作模型字段内容与格式规范.md` 的四段式验证结构，并按“验证计划、验证命令、验证结果、结论”顺序轻量分段展示，不使用表格左列重复标签。

Pitfall 详情页展示 `tags` 时应保留事实源中的英文原始值，不做中文翻译。列表卡片不展示 `tags`，也不展示 `repeatability`、“已解决/未解决”、复现概率或其他冗余解决态，避免把内部索引标签和已解决前提提升为外部卡片信号。

Pitfall 的 Markdown 列表应保持阅读层级一致：无序列表只使用普通灰色圆点；有序列表保留原文 `1.`、`2.`、`3.` 文本编号，不得额外渲染为徽标、强调色、状态色或对象信号。

当前 Web 不得直接创建、编辑、归档、删除 Pitfall 或改写核心经验。Web 不得在页面状态、缓存或数据库中维护独立 Pitfall 权威状态。未来如需开放 Pitfall 写入，必须先更新 `specs/08-Web信息同步实现规范.md` 白名单、本文字段/状态约束、Code 校验、测试和 Human Gate 影响评估。

### 8.4 行动编排与环境适配

Pitfall 识别、创建、归档和吸收到规范或实现的具体行动流程由后续 40-59 行动编排规范承接。本文只定义 Pitfall 实例的事实规则和状态约束。

环境不支持相关 Pitfall 检索、归档原因聚合或受控编辑时，应记录降级方式，例如改用人工搜索、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整支持。

---
## 9. 规范保障要求

本文通过以下规范保障要求说明相关要求的同步、检查或审计触发条件。

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Pitfall 实例和后续行动编排应遵守本文定义的准入、状态机、字段契约、经验吸收边界和事实源边界 | 05、03.02、本文、22 ADR、24 Spark、21 WorkCase、Human Gate | 事实模型治理 | 创建、修改、搬移、审计、归档或吸收 Pitfall 时 |
| 入口可见要求 | AI 处理已解决可复用经验、反直觉问题、重复误判或规避策略时，应能定位本文 | 成员自描述、运行入口摘要、Pitfall 检索或经验吸收流程入口 | AI 执行入口提示 | 经验沉淀、任务执行前检查、状态流转或字段契约变化时 |
| 确定性执行要求 | Pitfall 字段、状态、引用、文件命名、条件必填、标签格式、已有标签清单和归档吸收关系应由 Code 校验、提供或记录缺口 | `specs/07-Code确定性执行实现规范.md`、Pitfall 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、引用关系、归档规则或标签规则变化时 |
| Human 交互要求 | Pitfall 创建、归档、核心经验改写和吸收到规范或实现时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 事实模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Pitfall 规范变化后，应检查成员自描述、05.01、05.02、05.03、ADR、Spark、WorkCase、Code、Web、适配措施和相关行动编排是否需要同步 | 成员自描述检查、字段格式映射、对象关系检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Pitfall 字段、状态、事实源边界、适配规则或检查要求变化时 |

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
| 终态处理 | archived 不得重开 |
| 吸收关系 | archived Pitfall 已填写 `archive_reason`；如被规范、运行入口、Code、Web 或行动编排吸收，已填写对应关联字段 |
| 对象边界 | Pitfall 未替代 WorkCase、Spark、ADR、规范、Code 测试或 Git 提交记录 |
| 经验吸收边界 | 规避策略被吸收后只保留引用，不复制规则正文第二事实源 |
| Human Gate | §5 场景已完成确认或记录降级 |
| Git 追溯 | Pitfall 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Pitfall Web 基础详情字段已同步，筛选和任务执行前提示入口待 Web 实现规划时补齐；
2. Pitfall 识别、创建、归档和吸收的具体行动编排待 40-59 承接；
3. Pitfall 与行动编排中 Learn 阶段的关系，待 40-59 稳定后进一步校准。
