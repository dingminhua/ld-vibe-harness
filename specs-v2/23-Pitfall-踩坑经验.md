# Pitfall-踩坑经验

```yaml
v2_spec:
  spec_id: "23"
  spec_kind: "member_spec"
  title: "Pitfall-踩坑经验"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/23-Pitfall-踩坑经验.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: "specs-v2/02-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Pitfall / 踩坑经验事实模型的对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、实例写入与消费边界"
  scope: "所有接入 LDVH 且需要沉淀已解决、已验证且具有复用价值的踩坑经验的项目"
  basis:
    - "specs-v2/00-LDVH理念与价值标准.md"
    - "specs-v2/01-规范体系基础规范.md"
    - "specs-v2/02-事实模型基础规范.md"
  related_specs:
    - "specs-v2/02.Att.01-字段注册表.md"
    - "specs-v2/02.Att.02-成员身份字段表.md"
    - "specs-v2/02.Att.03-成员主文件骨架模板.md"
    - "specs-v2/02.Att.04-成员一致性辅助核对表.md"
    - "specs-v2/02.Att.05-成员双读映射矩阵.md"
    - "specs/20-Spark-火花.md"
    - "specs/21-WorkCase-工作项.md"
    - "specs/22-ADR-决策.md"
  migration_sources:
    - "specs/23-Pitfall-踩坑经验.md"
  active_fact_source:
    - "specs/23-Pitfall-踩坑经验.md"
  code_consumption:
    - "v2_spec_metadata"
    - "fact_model_member_identity"
    - "fact_model_fields"
    - "fact_model_state_machine"
    - "fact_model_instance_checks"
  migration_status: "partially_migrated"
```

```yaml
v2_fact_model_member:
  spec_id: "23"
  kind: "fact_model"
  name_en: "Pitfall"
  name_zh: "踩坑经验"
  collection_status: "active"
  canonical_path: "specs-v2/23-Pitfall-踩坑经验.md"
  instance_root: "ldvh-base/pitfalls/"
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

> 文件状态：本文当前位于 `specs-v2/`，尚未切换为 active；正式 Pitfall 事实模型仍以 `specs/23-Pitfall-踩坑经验.md` 为准。
>
> 本文只作为 23-Pitfall 的 v2 成员草案和单篇核对输入。未经 Human 单篇确认前，本文不得作为 active 规范、Code 默认消费依据、Rules 入口依据或迁移完成结论。

## 1. 本文解决的问题

本文定义 Pitfall / 踩坑经验如何沉淀已解决、已验证且具有复用价值的经验事实，使 AI 和 Human 在后续执行中提前识别同类陷阱。

本文解决：

1. 什么经验应进入 Pitfall，什么问题应留在 Spark、WorkCase、ADR、docs、Code 测试或当前上下文；
2. Pitfall 的事实源位置、状态机、归档规则和经验吸收边界；
3. Pitfall 与 WorkCase、Spark、ADR、规范、Code、Web、运行入口和 Git commit records 的关系；
4. Pitfall 创建、归档、核心经验改写和吸收到规范或实现时的 Human Gate；
5. Pitfall 字段契约、四段式验证证据、标签规则、实例检查和消费边界。

本文不定义正式规范规则、Code 实现、Web 页面契约、行动编排流程或 Git commit message 契约。

## 2. 上位依据

本文承接 `00-LDVH理念与价值标准.md`：Pitfall 通过沉淀反直觉问题、误判原因、触发条件、解决方式、验证证据和规避策略，减少 AI 重复犯错和经验丢失。

本文承接 `01-规范体系基础规范.md`：本文作为事实模型成员规范，必须声明身份块、价值判断、保障要求、Human Gate 和待补齐事项；v2 写作区不得替代 active 事实源。

本文承接 `02-事实模型基础规范.md`：Pitfall 必须在成员主文件中定义字段契约、状态机、事实源边界和实例检查；字段注册表不得反向定义 Pitfall schema。

若本文草案与 active `specs/23-Pitfall-踩坑经验.md`、v2 00、v2 01 或 v2 02 冲突，在 Human 单篇确认前不得自行覆盖，应记录为待核对事项。

## 3. 构成要素归属与价值判断

### 3.1 构成要素归属

本文属于六类构成要素中的 `事实模型`。

| 项目 | 判断 |
|---|---|
| 主归属 | 事实模型 |
| 辅助服务对象 | Code、Web、行动编排和运行时扩展可消费 Pitfall 的状态、标签、适用范围、规避策略和吸收关系 |
| 不归属边界 | 不定义规范强制规则、Code 输出 Schema、Web 页面契约、行动编排流程或运行时适配细则 |

### 3.2 正向价值判断

| 价值标准 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过 `ldvh-base/pitfalls/`、tags、适用范围和关联对象定位相关经验 |
| V2 可行动理解 | 通过现象、触发条件、根因、解决方式、验证和规避策略形成可复读经验 |
| V3 正确判断 | 通过准入条件和非准入内容避免把未解决问题或一次性失败写成经验 |
| V4 稳定执行 | 通过 active Pitfall 为后续执行提供可复用规避策略 |
| V5 门禁识别 | 创建、归档、核心经验改写和吸收为长期规则时触发 Human Gate |
| V6 强制验证 | 通过四段式 `verification` 和条件必填支持检查 |
| V7 证据沉淀 | 保留问题、根因、解决方式、验证、规避策略、适用范围和 Git 追溯 |
| V8 可靠回写 | 经验写入 Pitfall，强制规则吸收到对应规范、Code、Web 或运行入口 |
| V10 持续完善 | Pitfall 暴露规范、Code、Web、运行时扩展或流程缺口后可分流为后续改进 |

### 3.3 逆向价值判断

| 反向风险 | 本文如何避免 |
|---|---|
| 把未解决问题写成经验 | Pitfall 不设 draft；未解决、未验证或字段不完整的问题不得写成 Pitfall |
| 用 Pitfall 替代规范或实现 | Pitfall 记录经验事实，强制行为应吸收到规范、运行入口、Code、Web 或行动编排 |
| 复制规则正文形成第二事实源 | 吸收后只保留经验事实和被吸收位置引用，不维护第二份规则正文 |
| 用标签制造 Human-facing 误导 | tags 保留英文原始值，列表卡片不把 tags 提升为外部状态信号 |
| 用 Web 状态替代事实源 | Web 当前不得直接创建、编辑、归档、删除 Pitfall 或改写核心经验 |

## 4. 对象定位与准入条件

Pitfall / 踩坑经验是已解决、已验证且具有复用价值的经验事实，用于沉淀反直觉问题、误判原因、触发条件、根因、解决方式、验证结果和后续规避策略。

Pitfall 不是所有 bug、失败命令、临时阻塞、未验证猜测或复盘感想的默认归宿。只有问题已经被解决，且后续执行可能复现同类误判或重复踩坑时，才应进入 Pitfall 事实源。

### 4.1 Pitfall 准入条件

一个经验满足以下条件之一时，应考虑形成 Pitfall：

1. 问题已经解决，且解决方式已验证；
2. 问题具有反直觉性，AI 或 Human 后续容易重复误判；
3. 问题跨 WorkCase、项目阶段或管辖项目具有复用价值；
4. 问题暴露了事实源读取、字段契约、Code 使用、Web 派生视图、环境适配、适配措施或行动编排中的稳定陷阱；
5. 同类问题已经出现多次，需要形成规避策略；
6. 问题可作为后续规范、Rules、Skills、Agents、Code、Web、ADR 或行动编排改进的输入。

创建 Pitfall 前，AI 必须说明准入理由、问题是否已解决、验证证据、适用范围、规避策略和预期回写位置，并按本文 §8 评估 Human Gate。

### 4.2 不应形成 Pitfall 的内容

以下内容通常不应单独形成 Pitfall：

1. 尚未解决的问题；
2. 未验证的猜测、假设或临时判断；
3. 只影响当前一次执行且没有复用价值的错误；
4. 单纯的命令输出、日志片段或失败记录；
5. 已由 specs、Rules、ADR、WorkCase 或 Code 明确约束，且没有新增经验的信息；
6. 没有规避策略的抱怨、复盘感想或笼统提醒。

### 4.3 Pitfall 与规范、运行入口和实现的边界

Pitfall 记录为什么会踩坑、如何解决、如何验证和以后如何规避。正式规范、Rules、Skills、Agents、Code、Web 或行动编排记录以后必须怎么做、如何执行、如何校验或如何呈现。

当 Pitfall 中的规避策略需要成为长期强制行为时，应将规则正文吸收到对应正式规范、运行入口、Code、Web 或行动编排。Pitfall 保留问题背景、根因、验证证据和被吸收位置的引用，不替代被吸收后的权威规则。

## 5. 事实源边界

Pitfall 实例的权威事实源位置为：

```text
ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Pitfall active 事实模型规范 | `specs/23-Pitfall-踩坑经验.md` |
| Pitfall v2 成员草案 | `specs-v2/23-Pitfall-踩坑经验.md` |
| Pitfall 实例 | `ldvh-base/pitfalls/` |
| Pitfall 字段内容格式和公共字段语义 | v2 未 active 前以 active 05 系列和 Pitfall active 成员主文件为准 |
| Pitfall 展示、聚合或查询结果 | Web、Code 或知识地图派生输出，不作为最终事实源 |

## 6. 状态机

### 6.1 标准状态

| 状态 | 含义 |
|---|---|
| `active` | 已确认，问题已解决、解决方式已验证，且可作为后续执行参考 |
| `archived` | 已归档，不再作为常规参考，但保留历史经验、归档原因和必要关联 |

Pitfall 不设 `draft` 状态。未解决、未验证或字段不完整的问题不得写成 Pitfall；应留在 Spark、WorkCase、对话上下文或其它更合适的事实源中继续消化。

`archived` 是稳定终态。终态 Pitfall 不得直接重开；如需重新沉淀，应新建 Pitfall，并在新 Pitfall 中引用原 Pitfall。

### 6.2 合法状态流转

```text
active -> archived
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` -> `archived` | 经验不再常规适用、已被规范或实现吸收，或不再需要作为常规参考 | 必须记录 `archive_reason`；如已被吸收，应说明承接位置 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

## 7. 对象关系

### 7.1 Pitfall 与 WorkCase

WorkCase 执行、验证或关闭过程中发现的已解决且可复用经验，可以整理为 Pitfall。Pitfall 可通过 `source_objects` 或 `related_workcases` 记录来源 WorkCase。Pitfall 不替代 WorkCase 的成功标准、验证证据、关闭证据、风险判断或缺陷修复动作。

### 7.2 Pitfall 与 Spark

Spark 中保留的发现、提醒、复盘线索或问题线索满足 Pitfall 准入条件后，可以分流为 Pitfall。分流后，Pitfall 的 `source_sparks` 应记录来源 Spark，Spark 的 `resolved_to` 可记录 Pitfall ID。

### 7.3 Pitfall 与 ADR

Pitfall 和 ADR 是独立事实模型。经验是经验，决策是决策，两者可以关联但不可互相替代。当 Pitfall 暴露的问题需要形成长期决策、改变事实源归属、改变规范边界或影响多个事实模型时，应创建或关联 ADR。

### 7.4 Pitfall 与规范、Code、Web 和运行入口

当 Pitfall 中的规避策略需要长期生效时，应按内容性质分流：

| 需要沉淀的内容 | 承接位置 |
|---|---|
| 强制规则、字段契约、事实源边界或 Human Gate | specs 正式规范 |
| 高频入口提示或硬约束摘要 | Rules 适配措施 |
| 可复用多步骤流程 | Skill 或行动编排规范 |
| 独立、专项或并行审查视角 | Agent 适配措施或行动编排规范 |
| 可机械化校验、解析、聚合或受控写入 | Code 实现 |
| Human-facing 展示、确认或受控轻写入 | Web 信息同步实现 |

分流后，Pitfall 应保留经验事实和被吸收位置引用，不得复制并维护第二份规则正文。

### 7.5 Pitfall 与 Git 提交记录

Pitfall 的创建、状态变化、核心经验改写、归档和被吸收到规范、运行入口、Code、Web 或行动编排时，都应留下 Git commit records。

## 8. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Pitfall 实例；
2. 将 WorkCase 过程发现、Spark、docs/studies 结论或对话输入升级为 Pitfall；
3. 将 `active` Pitfall 标记为 `archived`；
4. 修改 `root_cause`、`resolution`、`verification` 或 `avoidance` 等核心经验字段；
5. 将 Pitfall 的规避策略吸收到 specs、Rules、Skills、Agents、Code、Web 或行动编排；
6. 将未解决或未验证问题写成 `active` Pitfall；
7. 删除原 Pitfall 而不是通过 `archived` 表达归档或吸收。

## 9. 字段契约

| 字段名或路径 | 字段来源 | 字段含义 | 值形态 | 是否必填 | 状态条件 | 内容格式 | schema 归口 | 消费方 |
|---|---|---|---|---|---|---|---|---|
| `id` | 模型身份基线字段 | Pitfall 实例唯一标识，格式为 `pitfall-{NNNN}` | string | 必填 | 与文件编号一致 | reference | 23 | AI、Code、Web |
| `type` | 模型身份基线字段 | 固定为 `pitfall` | string | 必填 | 所有状态必须为 `pitfall` | reference | 23 | AI、Code、Web |
| `title` | 模型身份基线字段 | 踩坑经验一句话概括 | string | 必填 | 应简短可读 | narrative | 23 | AI、Web |
| `status` | 模型身份基线字段 | 当前 Pitfall 状态 | string | 必填 | 必须属于 `active` 或 `archived` | reference | 23 | AI、Code、Web |
| `created` | 模型身份基线字段 | 创建时间 | datetime | 必填 | ISO 8601 时间戳 | reference | 02、23 | AI、Code、Web |
| `updated` | 模型身份基线字段 | 最近更新时间 | datetime | 必填 | 每次事实源更新时同步 | reference | 02、23 | AI、Code、Web |
| `symptoms` | Pitfall 模型特有字段 | 问题现象、错误表现或误判结果 | markdown | 必填 | 使用 YAML 块标量 | narrative | 23 | AI、Web |
| `trigger_conditions` | 公共字段，Pitfall 采用 | 触发条件、上下文或复现场景 | markdown | 必填 | 应说明何时可能复现 | narrative | 23 | AI、Code、Web |
| `root_cause` | Pitfall 模型特有字段 | 根因或误判原因 | markdown | 必填 | `active` 时必须明确 | narrative | 23 | AI、Human、Web |
| `resolution` | Pitfall 模型特有字段 | 解决方式 | markdown | 必填 | `active` 时必须可执行 | narrative | 23 | AI、Code、Web |
| `verification` | 公共字段，Pitfall 采用 | 经验可用性的验证证据 | evidence_markdown | 必填 | `active` 时必须按四段式验证证据结构书写 | evidence | 23 | AI、Code、Web |
| `avoidance` | 公共字段，Pitfall 采用 | 后续规避策略 | markdown | 必填 | `active` 时必须可复用 | narrative | 23 | AI、Human、Web |
| `applicability` | Pitfall 模型特有字段 | 适用范围和不适用范围 | markdown | 必填 | 应避免泛化过度 | narrative | 23 | AI、Web |
| `tags` | Pitfall 模型特有字段 | 英文标签列表 | list_string | 可选 | 默认为空列表；写入前应参考已有标签 | reference | 23 | AI、Code、Web |
| `source_objects` | 公共字段，Pitfall 采用 | 来源对象 | list_string | 可选 | 默认为空列表 | reference | 23 | AI、Code、Web |
| `source_sparks` | 公共字段，Pitfall 采用 | 来源 Spark | list_string | 可选 | 默认为空列表 | reference | 23 | AI、Code、Web |
| `related_workcases` | 公共字段，Pitfall 采用 | 关联 WorkCase | list_string | 可选 | 默认为空列表 | reference | 23 | AI、Code、Web |
| `related_adrs` | 公共字段，Pitfall 采用 | 关联 ADR | list_string | 可选 | 默认为空列表 | reference | 23 | AI、Code、Web |
| `related_docs` | 公共字段，Pitfall 采用 | 关联文档路径 | list_string | 可选 | 默认为空列表 | reference | 23 | AI、Code、Web |
| `related_rules` | 公共字段，Pitfall 采用 | 已吸收或承接该经验的规范、Rules、Skill、Agent、Code 或 Web 路径 | list_string | 可选 | 默认为空列表 | reference | 23 | AI、Code、Web |
| `archive_reason` | 公共字段，Pitfall 采用 | 归档原因和吸收位置 | markdown | 条件必填 | `status: archived` 时必须填写 | narrative | 23 | AI、Human |
| `notes` | 公共字段，Pitfall 采用 | 其它字段无法承载的补充说明 | markdown | 可选 | 不得承载规则正文第二事实源 | narrative / reference | 23 | AI、Web |

字段约束：

1. `active` Pitfall 必须具备现象、触发条件、根因、解决方式、验证、规避策略和适用范围；
2. `status: archived` 时必须填写 `archive_reason`；
3. 不得使用 `repeatability`、`severity` 或 `superseded_by` 作为新写入字段；
4. `tags` 必须使用英文 slug，推荐小写短横线格式；写入或修改前应优先复用已有标签；
5. `verification` 必须按四段式验证证据结构书写，不得只写已验证或通过；
6. 阅读节点字段可以使用 Markdown 段落或列表，但不得通过手写前导空格模拟缩进排版。

## 10. 事实实例写入、回写、验证和证据留存

Pitfall 回写遵循以下规则：

1. 创建 Pitfall 时，应写入 `ldvh-base/pitfalls/`，并填写问题现象、触发条件、根因、解决方式、验证方式、规避策略和适用范围；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit records 派生，不在 Pitfall YAML 中手写维护；
4. Pitfall 被吸收到规范、运行入口、Code、Web 或行动编排后，应更新 `related_rules` 或相关引用；
5. Pitfall 创建、状态变化、核心经验改写、归档或被吸收应通过 Git 提交记录留痕；
6. Pitfall 写入前，应查询并呈现当前已有 `tags`；
7. Pitfall 写入后，应重新校验文件命名、字段完整性、状态合法性、标签格式和引用有效性。

Pitfall 证据至少包括问题现象、触发条件、根因、解决方式、验证方式或验证结论、规避策略、适用范围和不适用范围、Human Gate 确认记录，以及相关 WorkCase、Spark、ADR、docs、规范、Code 或 Git 提交引用。

## 11. Code、Web、知识地图和运行时扩展消费边界

AI 处理 Pitfall 时应先判断经验是否满足准入条件，不得把未解决、未验证或字段不完整的问题写成 Pitfall。读取 `archived` Pitfall 时，应查看 `archive_reason` 和关联字段，判断是否已被规范、运行入口或实现吸收。

Code 可解析 Pitfall YAML，校验文件命名、ID、字段类型、必填字段、条件必填字段、状态枚举、合法流转、引用字段、`archive_reason`、tags 格式和旧字段迁移诊断。Code 不得自行创建、归档、删除 Pitfall 或改写核心经验。

Web 可展示 Pitfall 状态、症状、触发条件、根因、解决方式、验证结论、规避策略、适用范围、标签、归档原因、吸收关系和待确认项。当前 Web 不得直接创建、编辑、归档、删除 Pitfall 或改写核心经验，也不得维护独立 Pitfall 权威状态。

知识地图和运行时扩展可以消费 Pitfall 成员身份、字段契约、状态机、标签、关联关系和实例事实源目录，但输出只能作为定位、诊断或展示，不能替代本文或实例文件。

## 12. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Pitfall 实例和后续行动编排应遵守本文定义的准入、状态机、字段契约、经验吸收边界和事实源边界 | 本文、active `specs/23-Pitfall-踩坑经验.md`、v2 02、Human Gate；未 active 前为人工降级检查 | 事实模型治理 | 创建、修改、迁移、归档或吸收 Pitfall 时 |
| 入口可见要求 | AI 处理已解决可复用经验、反直觉问题、重复误判或规避策略时，应能定位 Pitfall active 规范、本文草案和实例事实源 | `specs-v2/README.md`、02 成员身份、知识地图输入、运行时入口；未 active 前为人工降级检查 | AI 执行入口 | 经验沉淀、任务执行前检查、状态流转或字段契约变化时 |
| 确定性执行要求 | Pitfall 字段、状态、引用、文件命名、条件必填、标签格式、已有标签清单和归档吸收关系应由 Code 校验、提供或记录缺口 | 现有 active Code、`02.Att.04`、`02.Att.05`、`02.Att.06`、人工降级检查 | Code 校验 | 字段契约、状态机、引用关系、归档规则或标签规则变化时 |
| Human 交互要求 | Pitfall 创建、归档、核心经验改写和吸收到规范或实现时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | Human Gate | §8 中任一场景发生时 |
| 生命周期触发要求 | Pitfall 规范变化后，应检查 ADR、Spark、WorkCase、Code、Web、运行时扩展、行动编排和待补齐事项是否需要同步 | 本文、02 授权附件、Code 诊断、人工降级检查 | 生命周期同步 | Pitfall 字段、状态、事实源边界、适配规则或检查要求变化时 |

## 13. 对象特有实例检查

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Pitfall |
| 文件命名 | 实例路径符合 `ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml` |
| 字段完整性 | 必填字段、条件必填字段和字段类型符合 §9 |
| 状态合法性 | 状态属于枚举，流转符合 §6.2 |
| active 可用性 | active Pitfall 已解决、已验证、具备规避策略和适用范围 |
| 终态处理 | archived 不得重开 |
| 吸收关系 | archived Pitfall 已填写 `archive_reason`；如被规范、运行入口、Code、Web 或行动编排吸收，已填写对应关联字段 |
| 对象边界 | Pitfall 未替代 WorkCase、Spark、ADR、规范、Code 测试或 Git 提交记录 |
| 经验吸收边界 | 规避策略被吸收后只保留引用，不复制规则正文第二事实源 |
| Human Gate | §8 场景已完成确认或记录降级 |
| Git 追溯 | Pitfall 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

## 14. 待补齐事项

1. 本文已迁入 Pitfall 主要准入、状态机、经验吸收边界、Human Gate、字段契约、标签和 Web 详情规则；仍需在 Human 单篇核对前逐项对照 active `specs/23-Pitfall-踩坑经验.md`；
2. active `ldvh_member` 与 v2 `v2_fact_model_member` 的双读 Code 实现、正反样例和切换策略尚未完成；本文不改变 Code 默认消费入口；
3. Pitfall 识别、创建、归档和吸收的具体行动编排尚未迁入，应由后续 30-59 行动编排单篇处理；
4. 本文切换 active 前，应再次核对 active `specs/23-Pitfall-踩坑经验.md`、02 授权附件、现有 Code/Web 测试和相关 active 20-24 成员规则，确认没有字段、状态、引用或消费入口漂移。
