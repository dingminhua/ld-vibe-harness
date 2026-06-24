# Study-研究报告

```yaml
v2_spec:
  spec_id: "24"
  spec_kind: "member_spec"
  title: "Study-研究报告"
  status: "active"
  authority: "active"
  canonical_path: "specs/24-Study-研究报告.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: "specs/02-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Study / 研究报告事实模型的对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、Markdown 正文契约、实例写入与消费边界"
  scope: "所有接入 LDVH 且需要把 AI 调研、资料分析、方案比较或事实核验结果沉淀为稳定可阅读报告的项目"
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
    - "specs/22-ADR-决策.md"
    - "specs/23-Pitfall-踩坑经验.md"
  migration_sources:
    - "history/specs-v1/24-Study-研究报告.md"
  active_fact_source:
    - "specs/24-Study-研究报告.md"
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
  spec_id: "24"
  kind: "fact_model"
  name_en: "Study"
  name_zh: "研究报告"
  collection_status: "active"
  canonical_path: "specs/24-Study-研究报告.md"
  instance_root: "ldvh-base/studies/"
  instance_carrier: "markdown"
  fact_source_anchor: "§5"
  schema_anchor: "§9"
  state_machine_anchor: "§6"
  human_gate_anchor: "§8"
  code_consumption:
    - "fields"
    - "state_machine"
    - "markdown_frontmatter"
    - "instance_checks"
```

> 文件状态：本文是 active 正式规范；正式规则以本文及其授权附件为准。

## 1. 本文解决的问题

本文定义 Study / 研究报告如何承载已经形成稳定阅读价值的调研、分析、核验或方案比较结果，并把报告正文、摘要、输入边界、结论边界和关联对象纳入 Git 可追踪事实源。

本文解决：

1. 什么内容应进入 Study，什么内容应留在 docs/studies、docs/sources、Spark、ADR、WorkCase 或 Pitfall；
2. Study Markdown 工作对象的事实源位置、frontmatter 字段、正文骨架和状态机；
3. Study 与 Spark、WorkCase、ADR、Pitfall、项目文档、外部网址和 Git commit records 的关系；
4. Study 创建、归档、大幅改写和作为关键依据时的 Human Gate；
5. Study 字段契约、正文契约、网址结构、实例检查和 Web 阅读边界。

本文不定义外部资料原文管理、正式规范吸收流程、行动编排流程、Code 输出 Schema、Web 页面布局或 Git commit message 契约。

## 2. 上位依据

本文承接 `00-LDVH理念与价值标准.md`：Study 通过稳定报告正文、摘要、结论边界和来源边界，减少 AI 反复调研、重复引用临时材料和把报告全文塞入 Spark 的负担。

本文承接 `01-规范体系基础规范.md`：本文作为事实模型成员规范，必须声明成员身份、迁移来源、active 事实源、保障要求、Human Gate 和待补齐事项。

本文承接 `02-事实模型基础规范.md`：Study 必须在成员主文件中定义字段契约、状态机、Markdown frontmatter、正文契约、事实源边界和实例检查。

若本文与 active `specs/24-Study-研究报告.md`、v2 00、v2 01 或 v2 02 冲突，应按上位依据、事实源边界和 Human Gate 处理，不得由局部段落自行覆盖。

## 3. 构成要素归属与价值判断

### 3.1 构成要素归属

本文属于六类构成要素中的 `事实模型`。

| 项目 | 判断 |
|---|---|
| 主归属 | 事实模型 |
| 辅助服务对象 | Code、Web、行动编排和运行时扩展可消费 Study frontmatter、正文骨架、关联对象和 URL 结构 |
| 不归属边界 | 不定义 docs/studies 资料区规则、外部资料抓取、行动流程、Code 输出 Schema、Web 布局或 Git 提交格式 |

### 3.2 正向价值判断

| 价值标准 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过 `ldvh-base/studies/` 和 Markdown frontmatter 定位稳定报告 |
| V2 可行动理解 | 通过摘要、结论和固定正文骨架支持 AI 快速复读报告 |
| V3 正确判断 | 通过准入和对象边界避免把讨论过程、短结论或外部原文误写为 Study |
| V4 稳定执行 | 通过报告正文和后续分流为 WorkCase、ADR、Spark、Pitfall 或 docs 提供依据 |
| V5 门禁识别 | 创建、归档、大幅改写和作为关键依据时触发 Human Gate |
| V6 强制验证 | 通过 frontmatter、正文骨架、URL 结构和引用字段提供检查入口 |
| V7 证据沉淀 | 保留研究问题、输入边界、关键发现、建议、后续分流和 Git 追溯 |
| V8 可靠回写 | 稳定报告写入 Markdown 工作对象，外部资料只以结构化 URL 摘要引用 |
| V10 持续完善 | 报告结论可分流到 Spark、WorkCase、ADR、Pitfall、docs 或规范 |

### 3.3 逆向价值判断

| 反向风险 | 本文如何避免 |
|---|---|
| 用 Study 替代 Spark 演变 | Spark 保留议题当前摘要和关键语义转折，Study 承载完整报告正文 |
| 用 Study 替代 ADR 或 WorkCase | 决策进入 ADR，可执行事项进入 WorkCase |
| 复制外部资料原文 | 外部资料原文进入 docs/sources 或项目约定位置，Study 只提炼 URL 和用途摘要 |
| 用 docs/studies 替代工作对象 | docs/studies 是可变资料区，Study 是被提升后的稳定报告事实源 |
| 用 Web 扩展阅读区形成第二正文 | Web 复用同一份 Study 文件，不维护第二套摘要或正文 |

## 4. 对象定位与准入条件

Study / 研究报告承载已经形成稳定阅读价值的调研、分析、核验或方案比较结果。它解决的问题是：docs/studies 可以作为可变资料区，随时整理或删除；但某些报告已经成为后续讨论、决策、计划或 Spark 演变的关键依据，需要作为工作对象进入 Git 可追踪事实源。

Study 是报告产物对象，不是讨论过程对象。讨论的关键转折由 Spark 的 `evolution` 承载；决策进入 ADR；可执行事项进入 WorkCase；复用经验进入 Pitfall。

### 4.1 Study 准入条件

一个内容满足以下条件之一时，应考虑形成 Study：

1. AI 或 Human 已完成一轮调研，结果需要长期保留为可阅读报告；
2. 报告会被多个 Spark、WorkCase、ADR 或 Pitfall 引用；
3. docs/studies 中的临时资料已经被整理为稳定结论，不宜继续只放在可变资料区；
4. 某个 Spark 的讨论依赖一份报告，但 Spark 不应复制报告全文；
5. 方案比较、资料核验或事实调查需要保留结论边界、来源边界和残留不确定性。

### 4.2 不应形成 Study 的内容

以下内容通常不应单独形成 Study：

1. 尚未整理的临时摘录、对话片段或原始资料；
2. 已经可直接吸收到 specs、ADR、WorkCase、Pitfall 或 Spark 的短结论；
3. 外部资料原文副本，应进入 docs/sources 或项目约定的外部资料区；
4. 只服务当前一次执行、无需长期复读的命令输出；
5. 讨论过程中的每一次观点变化。

## 5. 事实源边界

Study 实例的权威事实源位置为：

```text
ldvh-base/studies/study-{NNNN}-short-title.md
```

Study 是 Markdown 工作对象。每个实例使用 YAML frontmatter 承载结构化字段，frontmatter 之后的 Markdown 正文承载报告内容。编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Study active 事实模型规范 | `specs/24-Study-研究报告.md` |
| Study v2 成员规范 | `specs/24-Study-研究报告.md` |
| Study 实例 | `ldvh-base/studies/` |
| Study 字段内容格式和公共字段语义 | 以 `specs/02-事实模型基础规范.md`、字段注册表和本文为准 |
| Study 展示、聚合或查询结果 | Web、Code 或知识地图派生输出，不作为最终事实源 |

Study 不替代 `docs/studies/`。`docs/studies/` 仍是可变内部研究资料区；Study 是被提升为工作对象后的稳定报告事实源。

## 6. 状态机

### 6.1 标准状态

| 状态 | 含义 |
|---|---|
| `active` | 活跃：报告是当前可引用的稳定研究产物 |
| `archived` | 已归档：报告保留历史价值，但不再作为当前入口 |

### 6.2 合法状态流转

```text
active -> archived
```

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` -> `archived` | 报告不再作为当前入口，但仍有历史参考价值 | `archive_reason` 条件必填 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

## 7. 对象关系

### 7.1 Study 与 Spark

Spark 可以引用一个或多个 Study。Spark 负责保留议题当前摘要和关键语义转折，Study 负责承载完整报告正文。Spark 不应复制 Study 全文；Study 不应记录 Spark 的讨论流水。

### 7.2 Study 与 WorkCase、ADR 和 Pitfall

Study 可以作为 WorkCase 的资料输入、ADR 的决策依据或 Pitfall 的证据来源。目标对象应只引用 Study ID 或路径，不复制报告正文。

### 7.3 Study 与关联文档和网址

docs/studies 和 docs/sources 可以作为 Study 的输入资料区，但不应成为 Study 的稳定事实源前提。Study 一旦形成，应把报告正文中需要复读的外部网页资料提炼到 `urls`。

`urls` 不得只是裸 URL 列表。每个外部网址必须使用结构化条目：`ref` 记录完整 `http(s)` URL，`summary` 用中文记录该网址在当前报告中的用途摘要，`title` 可记录可读标题。

维护历史 Study 时，若发现 `urls` 中仍有字符串 URL 条目，应迁移为 `{ref, summary}` 结构；不得继续新增裸 URL。

`related_docs` 只记录与 Study 相关的项目内文档路径。如果某项是报告正文中的外部网页资料，应放入 `urls`；如果某项是项目内文档、规范路径或代码位置，应放入 `related_docs` 或对象规范定义的专属关联字段。

引用不等于吸收。Study 被 WorkCase、ADR、Pitfall、Spark、docs 或规范引用时，只说明该报告被作为输入或依据；稳定规则、决策、任务、经验或事实源修改必须进入对应权威事实源，并通过 Git commit records 追溯。

### 7.4 Study 与 Git 提交记录

Study 的创建、状态变化、核心报告改写和归档都应留下 Git commit records。

## 8. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Study 实例；
2. 将 docs/studies、docs/sources、外部资料或对话调研结果提升为 Study；
3. 将 Study 标记为 `archived`；
4. 大幅改写 `summary`、`conclusion` 或报告正文；
5. 将 Study 作为 ADR、WorkCase 或 Spark 的关键依据；
6. 接受报告中的不确定性、残留风险或高影响判断。

## 9. 字段契约

### 9.1 Frontmatter 字段契约

| 字段名或路径 | 字段来源 | 字段含义 | 值形态 | 是否必填 | 状态条件 | 内容格式 | schema 归口 | 消费方 |
|---|---|---|---|---|---|---|---|---|
| `id` | 模型身份基线字段 | Study 实例唯一标识，格式为 `study-{NNNN}` | string | 必填 | 与文件编号一致 | reference | 24 | AI、Code、Web |
| `type` | 模型身份基线字段 | 固定为 `study` | string | 必填 | 所有状态必须为 `study` | reference | 24 | AI、Code、Web |
| `title` | 模型身份基线字段 | 研究报告一句话概括 | string | 必填 | 应简短可读 | narrative | 24 | AI、Web |
| `status` | 模型身份基线字段 | 当前 Study 状态 | string | 必填 | 必须属于 `active` 或 `archived`；创建 Study 时即应为 `active` | reference | 24 | AI、Code、Web |
| `created` | 模型身份基线字段 | 创建时间 | datetime | 必填 | ISO 8601 时间戳 | reference | 02、24 | AI、Code、Web |
| `updated` | 模型身份基线字段 | 最近更新时间 | datetime | 必填 | 每次事实源更新时同步 | reference | 02、24 | AI、Code、Web |
| `user_intent` | Study 模型特有字段 | 用户意图、调研出发点或最初想解决的问题 | markdown | 可选 | 可为空 | narrative / reference | 24 | AI、Web |
| `summary` | 公共字段，Study 采用 | 报告摘要和当前可引用结论 | markdown | 必填 | 使用 YAML 块标量 | narrative | 24 | AI、Web |
| `conclusion` | Study 模型特有字段 | 报告结论、边界和残留不确定性 | markdown | 可选 | 推荐填写 | narrative / decision | 24 | AI、Web |
| `urls` | 公共字段，Study 采用 | 报告正文中的外部网址及中文用途摘要 | list_object | 可选 | 默认为空列表；每项至少包含 `ref` 和 `summary` | reference | 24 | AI、Code、Web |
| `urls[].ref` | Study 嵌套字段 | 完整外部 URL | string | 条件必填 | `urls` 条目存在时必须是完整 `http(s)` URL | reference | 24 | AI、Code、Web |
| `urls[].title` | Study 嵌套字段 | 可读标题 | string | 可选 | 可为空 | narrative | 24 | AI、Web |
| `urls[].summary` | Study 嵌套字段 | URL 支撑当前报告中什么判断 | markdown | 条件必填 | `urls` 条目存在时必须填写中文用途摘要 | narrative / reference | 24 | AI、Web |
| `input_refs` | 公共字段，Study 采用 | 当前报告实际消费的稳定输入对象或项目内文档 | list_string | 可选 | 默认为空列表；可记录 Spark、WorkCase、ADR、Pitfall、Study ID 或项目内文档路径；外部网页资料仍写入 `urls` | reference | 24 | AI、Code、Web、知识地图 |
| `related_sparks` | 公共字段，Study 采用 | 关联 Spark | list_string | 可选 | 默认为空列表 | reference | 24 | AI、Code、Web |
| `related_workcases` | 公共字段，Study 采用 | 关联 WorkCase | list_string | 可选 | 默认为空列表 | reference | 24 | AI、Code、Web |
| `related_adrs` | 公共字段，Study 采用 | 关联 ADR | list_string | 可选 | 默认为空列表 | reference | 24 | AI、Code、Web |
| `related_pitfalls` | 公共字段，Study 采用 | 关联 Pitfall | list_string | 可选 | 默认为空列表 | reference | 24 | AI、Code、Web |
| `related_docs` | 公共字段，Study 采用 | 后续引用或承接文档路径 | list_string | 可选 | 默认为空列表；不承载外部网页资料 | reference | 24 | AI、Code、Web |
| `archive_reason` | 公共字段，Study 采用 | 归档原因 | markdown | 条件必填 | `status: archived` 时必须填写 | narrative | 24 | AI、Human |

Study 不得维护 `source`、`source_detail` 或 `source_docs`；用户侧调研出发点统一写入 `user_intent`，外部网页资料统一写入 `urls`。`input_refs` 只表达报告消费了哪些稳定输入，不替代 `related_*` 导航关系，不表示目标对象已吸收报告结论。

### 9.2 Markdown 正文契约

Frontmatter 后的 Markdown 正文是报告正文。正文必须使用稳定 Markdown 骨架，保证所有 Study 在 Web 扩展阅读区有一致阅读节奏。

正文结构要求如下：

1. 正文第一行必须是一级标题 `# {Study title}`，并与 frontmatter `title` 保持一致或语义等价；
2. 正文必须按顺序包含二级标题：`## 研究问题`、`## 输入与边界`、`## 关键发现`、`## 建议`、`## 后续分流`；
3. 二级标题只承担报告主阅读节点，不应为每个小点新增大量二级标题；
4. 细节分组应放在对应二级标题下，用三级标题、列表、表格或段落表达；
5. `## 输入与边界` 统一承载资料边界、方法、来源范围和不纳入范围；
6. `## 建议` 统一承载结论性建议、路线建议、候选补充方向和残留不确定性；
7. `## 后续分流` 统一承载应进入 Spark、WorkCase、ADR、Pitfall、docs 或规范的后续动作；
8. 报告正文应避免连续超长段落；超过三个并列判断时应使用列表或表格。

正文不仅要出现固定标题，还必须实际回答五组问题：研究问题是什么、输入资料/方法/来源边界是什么、关键发现是什么、建议/取舍/不确定性是什么、后续应分流到哪里。

## 10. 事实实例写入、回写、验证和证据留存

Study 回写遵循以下规则：

1. 创建 Study 时，应写入 `ldvh-base/studies/`，并填写 frontmatter 与 Markdown 正文；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit records 派生，不在 Study 中手写维护；
4. Study 被 Spark、WorkCase、ADR 或 Pitfall 消费时，应通过对应对象的引用字段建立关系；
5. Study 创建、归档或核心报告改写应通过 Git 提交记录留痕；
6. Study 写入后，应重新校验文件命名、frontmatter 字段完整性、状态合法性、正文骨架和引用有效性。

Study 证据至少包括研究问题和触发来源、报告摘要和正文、关键网址、结论边界和残留不确定性、相关 Spark、WorkCase、ADR、Pitfall、Git 提交记录或文档引用。

## 11. Code、Web、知识地图和运行时扩展消费边界

AI 处理 Study 时应先判断内容是否已经从临时资料整理为稳定报告；不得用 Study 替代 Spark 的议题演变、ADR 的长期决策或 WorkCase 的执行计划。

Code 可解析 Study Markdown frontmatter 和正文，校验文件命名、ID、字段类型、必填字段、条件必填字段、状态枚举、合法流转、`urls`、`related_*` 引用字段和正文骨架。Code 不得自行创建、替代、归档或删除 Study。

Web 可展示 Study 列表、状态、摘要、结论、正文入口和关联对象。Study 详情页是报告阅读界面，不按普通字段卡片表达主内容。右侧扩展阅读区应复用同一份 Study 事实源，不得维护第二套摘要或正文。当前 Web 不得直接创建、编辑、替代、归档或删除 Study。

知识地图和运行时扩展可以消费 Study 成员身份、frontmatter 字段、正文骨架、关联对象和实例事实源目录，但输出只能作为定位、诊断或展示，不能替代本文或实例文件。

## 12. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Study 实例和后续行动编排应遵守本文定义的准入、状态机、字段契约、Markdown frontmatter、正文骨架和事实源边界 | 本文、active `specs/24-Study-研究报告.md`、v2 02、Human Gate；行动编排未接管前使用临时核对动作 | 事实模型治理 | 创建、修改、迁移、引用或归档 Study 时 |
| 入口可见要求 | AI 处理需要长期保留的调研报告时，应能定位 Study active 规范、本文和对应实例事实源 | 02 成员身份、Rules 入口、`v2-check` 只读诊断和知识地图输入；行动编排未接管前使用临时核对动作 | AI 执行入口 | 报告创建、引用、吸收、归档、Rules 入口、`v2-check` 或知识地图输入变化时 |
| 确定性执行要求 | Study frontmatter、状态、引用、文件命名、URL 结构和正文骨架应由 Code 校验或记录缺口 | 现有 active Code、`02.Att.04`、`02.Att.05`、`02.Att.06`、临时核对动作 | Code 校验 | 字段契约、状态机、Markdown 承载或引用关系变化时 |
| Human 交互要求 | Study 创建、核心报告改写、归档和作为关键依据时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | Human Gate | §8 中任一场景发生时 |
| 生命周期触发要求 | Study 规范变化后，应检查 Spark、WorkCase、ADR、Pitfall、Code、Web、运行时扩展、行动编排和待补齐事项是否需要同步 | 本文、02 授权附件、Code 诊断、临时核对动作 | 生命周期同步 | Study 字段、状态、事实源边界、Markdown frontmatter 或检查要求变化时 |

## 13. 对象特有实例检查

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Study |
| 文件命名 | 实例位于 `ldvh-base/studies/`，文件名采用 `study-{NNNN}-short-title.md` |
| Frontmatter 完整性 | 必填字段、条件必填字段和字段类型符合 §9 |
| 正文骨架 | Frontmatter 后存在非空 Markdown 报告正文；正文第一行是一级标题；二级标题按 §9.2 固定顺序出现 |
| 状态合法性 | 状态属于枚举，流转符合 §6.2 |
| 归档规则 | archived Study 已说明归档原因 |
| URL 结构 | `urls` 条目使用结构化对象，至少包含完整 `http(s)` URL 和中文用途摘要 |
| 对象边界 | Study 未替代 Spark、ADR、WorkCase、Pitfall 或 docs/sources |
| Human Gate | §8 场景已完成确认或记录残留风险 |
| Git 追溯 | Study 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

## 14. 待补齐事项

1. 本文已迁入 Study 主要准入、状态机、frontmatter 字段、正文骨架、URL 结构和 Web 阅读边界，并已作为 active Study 成员规范生效；
2. 历史 `ldvh_member` 与 active `v2_fact_model_member` 的双读 Code 实现、正反样例和历史追溯策略尚未完成；本文不改变 Code 默认消费入口；
3. Study 创建、报告整理、吸收和归档的具体行动编排不按 v1 直接迁入；应按当前 active 规范保障需求进入行动编排候选计划；
4. 后续修改本文时，应再次核对 active `specs/24-Study-研究报告.md`、02 授权附件、现有 Code/Web 测试和相关 active 20-24 成员规则，确认没有字段、状态、引用或消费入口漂移。
