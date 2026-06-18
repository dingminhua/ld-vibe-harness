# Study-研究报告

> 创建日期：2026-06-18
> 定位：定义 Study / 研究报告工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要把 AI 调研、资料分析、方案比较或事实核验结果沉淀为稳定可阅读报告的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/03.01-规范文档规范.md`、`specs/05.01-工作字段内容格式规范.md`、`specs/07-Code确定性执行实现规范.md`、`specs/08-Web信息同步实现规范.md`、`specs/09-事实源边界与承载规范.md`、`specs/24-Memo-备忘.md`、`specs/25-Change-变更.md`

```yaml
ldvh_member:
  spec_id: "26"
  kind: work_model
  name_en: Study
  name_zh: 研究报告
  collection_status: active
  canonical_path: specs/26-Study-研究报告.md
  instance_root: ldvh-base/studies/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
    - state_machine
    - markdown_frontmatter
    - instance_checks
```

---
## 1. 对象定位与准入条件

Study / 研究报告承载已经形成稳定阅读价值的调研、分析、核验或方案比较结果。它解决的问题是：docs/studies 可以作为可变资料区，随时整理或删除；但某些报告已经成为后续讨论、决策、计划或 Memo 演变的关键依据，需要作为工作对象进入 Git 可追踪事实源。

Study 是报告产物对象，不是讨论过程对象。讨论的关键转折由 Memo 的 `evolution` 承载；决策进入 ADR；可执行事项进入 WorkPlan；复用经验进入 Pitfall。Study 只保留报告正文、摘要、输入边界、结论边界和关联对象。

### 1.1 Study 准入条件

一个内容满足以下条件之一时，应考虑形成 Study：

1. AI 或 Human 已完成一轮调研，结果需要长期保留为可阅读报告；
2. 报告会被多个 Memo、WorkPlan、ADR 或 Pitfall 引用；
3. docs/studies 中的临时资料已经被整理为稳定结论，不宜继续只放在可变资料区；
4. 某个 Memo 的讨论依赖一份报告，但 Memo 不应复制报告全文；
5. 方案比较、资料核验或事实调查需要保留结论边界、来源边界和残留不确定性。

### 1.2 不应形成 Study 的内容

以下内容通常不应单独形成 Study：

1. 尚未整理的临时摘录、对话片段或原始资料；
2. 已经可直接吸收到 specs、ADR、WorkPlan、Pitfall 或 Memo 的短结论；
3. 外部资料原文副本，应进入 docs/sources 或项目约定的外部资料区；
4. 只服务当前一次执行、无需长期复读的命令输出；
5. 讨论过程中的每一次观点变化。

---
## 2. 事实源边界

本文是 Study 工作模型的权威规范，定义 Study 的准入条件、状态机、对象关系、Human Gate、字段契约、事实源回写和证据留存要求。Study 作为 Markdown 工作对象时，文档治理承接 `specs/03.01-规范文档规范.md`；权威事实源、派生展示和外部资料边界承接 `specs/09-事实源边界与承载规范.md`。

Study 实例的权威事实源位置为：

```text
ldvh-base/studies/study-{NNNN}-short-title.md
```

Study 是 Markdown 工作对象。每个实例使用 YAML frontmatter 承载结构化字段，frontmatter 之后的 Markdown 正文承载报告内容。编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个管辖项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Study 工作模型规范 | `specs/26-Study-研究报告.md` |
| Study 实例 | `ldvh-base/studies/` |
| Study 字段内容格式 | `specs/05.01-工作字段内容格式规范.md` |
| Study 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

Study 不替代 `docs/studies/`。`docs/studies/` 仍是可变内部研究资料区；Study 是被提升为工作对象后的稳定报告事实源。

---
## 3. 状态机

### 3.1 标准状态

Study 标准状态如下：

| 状态 | 含义 |
|---|---|
| `active` | 活跃：报告是当前可引用的稳定研究产物 |
| `archived` | 已归档：报告保留历史价值，但不再作为当前入口 |

### 3.2 合法状态流转

```text
active → archived
```

合法流转规则如下：

| 流转 | 触发条件 | 说明 |
|---|---|---|
| `active` → `archived` | 报告不再作为当前入口，但仍有历史参考价值 | `archive_reason` 条件必填 |

未列出的状态流转为非法流转。Code 和 Web 不得绕过本文状态机直接修改状态。

---
## 4. 对象关系

### 4.1 Study 与 Memo

Memo 可以引用一个或多个 Study。Memo 负责保留议题当前摘要和关键语义转折，Study 负责承载完整报告正文。Memo 不应复制 Study 全文；Study 不应记录 Memo 的讨论流水。

Memo 的准入、状态和字段契约由 `specs/24-Memo-备忘.md` 定义。

### 4.2 Study 与 WorkPlan、ADR 和 Pitfall

Study 可以作为 WorkPlan 的资料输入、ADR 的决策依据或 Pitfall 的证据来源。目标对象应只引用 Study ID 或路径，不复制报告正文。

WorkPlan、ADR 和 Pitfall 的准入、状态和字段契约分别由 `specs/21-WorkPlan-工作计划.md`、`specs/22-ADR-决策.md` 和 `specs/23-Pitfall-踩坑经验.md` 定义。

### 4.3 Study 与关联文档和网址

docs/studies 和 docs/sources 可以作为 Study 的输入资料区，但不应成为 Study 的稳定事实源前提。Study 一旦形成，应把报告正文中需要复读的外部网页资料提炼到 `urls`。`urls` 回答“这份报告依据了哪些外部网址，以及每个网址支撑了当前报告中的什么判断”。

`urls` 不得只是裸 URL 列表。每个外部网址必须使用结构化条目：`ref` 记录完整 `http(s)` URL，`summary` 用中文记录该网址在当前报告中的用途摘要，`title` 可记录可读标题。摘要属于“关联”下的“网址”分组，用于帮助复读报告依据；报告正文只保留研究叙述本身，不应在正文中间堆叠网址摘要清单。历史字符串 URL 条目应在维护时迁移为结构化条目，不得继续新增。

`related_docs` 只记录与 Study 相关的项目内文档路径，例如后续承接文档、被报告消费的本地 Markdown、或需要从 Study 页面直达的项目文档。它回答“这个 Study 与哪些项目文档有关”。如果某项是报告正文中的外部网页资料，应放入 `urls`；如果某项是项目内文档、规范路径或代码位置，应放入 `related_docs` 或对象规范定义的专属关联字段。

### 4.4 Study 与 Change

Study 的创建、状态变化、核心报告改写和归档都应留下 Change。Change 的 commit message 契约由 `specs/25-Change-变更.md` 定义。

---
## 5. Human Gate

以下情况应评估 Human Gate：

1. 创建、删除或重命名 Study 实例；
2. 将 docs/studies、docs/sources、外部资料或对话调研结果提升为 Study；
3. 将 Study 标记为 `archived`；
4. 大幅改写 `summary`、`conclusion` 或报告正文；
5. 将 Study 作为 ADR、WorkPlan 或 Memo 的关键依据；
6. 接受报告中的不确定性、降级结论或高影响判断。

Human Gate 的具体环境实体由 04 系列环境适配和适配措施记录承接。本文只规定 Study 语境下需要确认的事实和影响范围。

---
## 6. 字段契约

### 6.1 Frontmatter 字段表

公共字段语义定义见 `specs/05.01-工作字段内容格式规范.md` §4。本表只列出对象特有字段语义补充。

| 字段名 | 含义 | 类型 | 必填 | 默认值或状态约束 | 内容格式 | 消费方 |
|---|---|---|---|---|---|---|
| `id` | 格式为 `study-{NNNN}` | string | 是 | 与文件编号一致 | Reference | AI、Code、Web |
| `type` | 固定为 `study` | string | 是 | 固定为 `study` | Reference | AI、Code、Web |
| `title` | 研究报告一句话概括 | string | 是 | 应简短可读 | Narrative | AI、Web |
| `status` | 见 §3.1 状态枚举 | string | 是 | 必须属于 §3.1 状态枚举；创建 Study 时即应为 `active` | Reference | AI、Code、Web |
| `created` | — | datetime | 是 | ISO 8601 时间戳 | Reference | AI、Code、Web |
| `updated` | — | datetime | 是 | 每次事实源更新时同步 | Reference | AI、Code、Web |
| `user_intent` | 用户意图、调研出发点或最初想解决的问题 | string | 否 | 可为空 | Narrative / Reference | AI、Web |
| `summary` | 报告摘要和当前可引用结论 | string | 是 | 使用 YAML 块标量 | Narrative | AI、Web |
| `conclusion` | 报告结论、边界和残留不确定性 | string | 否 | 推荐填写 | Narrative / Decision | AI、Web |
| `urls` | 报告正文中的外部网址及中文用途摘要；每项必须使用 `{ref, summary}` 或 `{ref, title, summary}` 结构，`ref` 必须是完整 `http(s)` URL，`summary` 必须是中文简介 | list[object] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_memos` | 关联备忘 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workareas` | 关联工作域 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_workplans` | 关联工作计划 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_adrs` | 关联决策记录 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_pitfalls` | 关联踩坑经验 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `related_docs` | 后续引用或承接文档路径 | list[string] | 否 | 默认为空列表 | Reference | AI、Code、Web |
| `archive_reason` | 归档原因 | string | 条件必填 | `status: archived` 时必须填写 | Narrative | AI、Human |

字段内容格式按 `specs/05.01-工作字段内容格式规范.md` 执行。字段缺失、类型错误、状态非法、引用不存在、条件必填缺失或文件命名不匹配时，Code 应报告诊断，不得静默通过。Study 不得维护 `source`、`source_detail` 或 `source_docs`；用户侧调研出发点统一写入 `user_intent`，外部网页资料统一写入 `urls`。

### 6.2 正文契约

Frontmatter 后的 Markdown 正文是报告正文。正文必须使用稳定 Markdown 骨架，保证所有 Study 在 Web 扩展阅读区有一致的阅读节奏。

正文结构要求如下：

1. 正文第一行必须是一级标题 `# {Study title}`，并与 frontmatter `title` 保持一致或语义等价；
2. 正文必须按顺序包含以下二级标题：`## 研究问题`、`## 输入与边界`、`## 关键发现`、`## 建议`、`## 后续分流`；
3. 二级标题只承担报告主阅读节点，不应为每个小点新增大量二级标题；
4. 细节分组应放在对应二级标题下，用三级标题 `###`、列表、表格或段落表达；
5. `## 输入与边界` 统一承载资料边界、方法、来源范围和不纳入范围，不再使用 `## 资料边界` 等同义二级标题；
6. `## 建议` 统一承载结论性建议、路线建议、候选补充方向和残留不确定性，不再另设 `## 结论` 或 `## 建议下一步` 作为同层级标题；
7. `## 后续分流` 统一承载应进入 Memo、WorkPlan、ADR、Pitfall、docs 或规范的后续动作，不再使用 `## 后续分流建议` 等同义二级标题；
8. 报告正文应避免连续超长段落；超过三个并列判断时应使用列表或表格；超过两个层次时应优先拆成三级标题和列表。

正文必须回答以下问题：

1. 研究问题是什么；
2. 输入资料、方法、来源边界和不确定性边界是什么；
3. 关键发现是什么；
4. 建议、取舍、边界和残留不确定性是什么；
5. 后续应分流到哪些 Memo、WorkPlan、ADR、Pitfall、docs 或规范。

### 6.3 Markdown 示例

```markdown
---
id: study-0001
type: study
title: Memo 工作模型演变承载方式研究
status: active
created: '2026-06-18T14:30:00+08:00'
updated: '2026-06-18T15:00:00+08:00'
user_intent: 用户要求评估 Memo 是否足以承载想法、调研、报告和讨论演变。
summary: |
  Memo 应承载议题的当前摘要和关键语义转折，完整调研报告应由 Study 承载。
conclusion: |
  Study 适合承载稳定报告；Memo 保留演变摘要和分流关系。
urls:
  - ref: specs/24-Memo-备忘.md §6
    title: Memo 字段契约
    summary: 用于说明 Memo 的演变记录和分流关系边界，支撑本报告对 Memo/Study 分工的判断。
related_memos:
  - memo-0001
related_workareas: []
related_workplans: []
related_adrs: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Memo 工作模型演变承载方式研究

## 研究问题

Memo 是否应同时承载想法、调研报告和讨论演变。

## 输入与边界

本报告基于 Memo 与 Study 工作模型规范讨论，不复制原始对话流水。

## 关键发现

Memo 适合保留议题演变，Study 适合承载稳定报告正文。

## 建议

Memo 不应复制完整报告；Study 承载稳定报告正文。

## 后续分流

需要修改 Memo 或 Study 规则时，应分别进入对应工作模型规范或 WorkPlan。
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Study 回写遵循以下规则：

1. 创建 Study 时，应写入 `ldvh-base/studies/`，并填写 frontmatter 与 Markdown 正文；
2. 状态变化前应检查合法流转、条件必填和 Human Gate；
3. 状态变化后应更新 `updated`；状态变化历史由 Git commit / Change 派生，不在 Study 中手写维护；
4. Study 被 Memo、WorkPlan、ADR 或 Pitfall 消费时，应通过对应对象的引用字段建立关系；
5. Study 创建、归档或核心报告改写应通过 Change 留痕；
6. Study 事实源写入后，应重新校验文件命名、frontmatter 字段完整性、状态合法性和引用有效性。

### 7.2 证据留存

Study 证据至少包括：

1. 研究问题和触发来源；
2. 报告摘要和正文；
3. 关键网址；
4. 结论、边界和残留不确定性；
5. 相关 Memo、WorkPlan、ADR、Pitfall、Change 或文档引用。

Study 的报告正文应保留足以复读的结论和依据，但不复制外部资料全文，不记录讨论流水。

---
## 8. 适配边界

### 8.1 AI 协作

AI 处理 Study 时应遵守：

1. 先判断内容是否已经从临时资料整理为稳定报告；
2. 创建、归档或大幅改写 Study 前评估 Human Gate；
3. 不得用 Study 替代 Memo 的议题演变、ADR 的长期决策或 WorkPlan 的执行计划；
4. 引用 Study 时只引用 ID、路径或摘要，不复制报告全文；
5. 报告结论被吸收到 specs、ADR 或 WorkPlan 后，应在 Study 或目标对象中保留引用关系。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 解析 Study Markdown frontmatter 和正文；
2. 校验文件命名、ID、字段类型、必填字段和条件必填字段；
3. 校验状态枚举和合法流转；
4. 校验 `urls`、`related_*` 引用字段；
5. 聚合活跃 Study、已归档 Study 和关联 Memo。

Code 不得自行创建、替代、归档或删除 Study，不得绕过 Human Gate，不得把派生输出替代 `ldvh-base/studies/` 权威事实源。

### 8.3 Web 信息同步

Web 可展示 Study 列表、状态、摘要、结论、正文和关联对象。Web 展示必须可追溯到 Git 文件事实源或 Code 派生结果。

Study 详情页是报告阅读界面，不按普通字段卡片表达主内容。中文主节点标题固定为“意图、摘要、建议、正文、关联”，分别对应 `user_intent`、`summary`、`conclusion`、frontmatter 后的 Markdown 报告正文和关联区。主节点标题应使用同一视觉层级，标题前使用小圆点，内容弱于标题；默认全部打开，点击标题栏在打开和收拢之间切换，收拢状态使用向下箭头表示可展开，打开状态使用向上箭头表示可收起。

Study 正文不应在主页面直接铺开全文。“正文”节点下只展示当前 Study 文件入口，点击整行或扩展阅读入口后在右侧扩展阅读区渲染 Markdown 正文。右侧扩展阅读区应复用同一份 Study 事实源，不得维护第二套摘要或正文。

Study 的所有关联内容必须进入上层“关联”区块。`urls` 显示在“关联”下的“网址”分组，每个条目必须显示可读标题或 URL，并显示中文 `summary`；该摘要是引用用途提示，应弱于 Study 主内容，不得替代报告正文结论。`related_docs`、`related_memos`、`related_workareas`、`related_workplans`、`related_adrs` 和 `related_pitfalls` 等关联字段不得散落在正文、证据或其他字段之间。

当前 Web 不得直接创建、编辑、替代、归档或删除 Study。未来如需开放 Study 写入，必须先更新 `specs/08-Web信息同步实现规范.md` 白名单、本文字段/状态约束、Code 校验、测试和 Human Gate 影响评估。

### 8.4 工作流程与环境适配

Study 创建、报告整理、吸收和归档的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Study 实例的事实规则和状态约束。

环境不支持 Markdown frontmatter 解析、引用校验或正文预览时，应记录降级方式，例如改用人工检查、Code 校验或直接读取 Git 文件事实源；不得把未完成的环境能力表述为完整落地。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Study 实例和后续工作流程应遵守本文定义的准入、状态机、字段契约、Markdown frontmatter 和事实源边界 | 05、03.02、本文、24 Memo、25 Change、Human Gate | 工作模型治理 | 创建、修改、审计、引用或归档 Study 时 |
| 入口可见要求 | AI 处理需要长期保留的调研报告时，应能定位本文 | 成员自描述、运行入口摘要、Memo 分流规则 | AI 执行入口提示 | 报告创建、引用、吸收或归档时 |
| 确定性执行要求 | Study frontmatter、状态、引用、文件命名和正文存在性应由 Code 校验或记录缺口 | `specs/07-Code确定性执行实现规范.md`、Study 校验 Code、正反样例 | 校验实现 | 字段契约、状态机、Markdown 承载或引用关系变化时 |
| Human 交互要求 | Study 创建、核心报告改写、归档和作为关键依据时应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Study 规范变化后，应检查成员自描述、01、03.01、05、05.01、08、Memo、Code、Web、适配措施和相关工作流程是否需要同步 | 成员自描述检查、字段格式映射、对象关系检查、Code/Web 联动检查、人工降级检查 | 触发保障 | Study 字段、状态、事实源边界、Markdown frontmatter 或检查要求变化时 |

---
## 10. 检查要求

Study 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明为什么需要或不需要形成 Study |
| 事实源位置 | 实例位于 `ldvh-base/studies/`，文件名采用 Study 四位编号加英文短标题的 Markdown 文件模式 |
| Frontmatter 完整性 | 必填字段、条件必填字段和字段类型符合 §6 |
| 正文骨架 | Frontmatter 后存在非空 Markdown 报告正文；正文第一行是一级标题；二级标题按 §6.2 固定顺序出现 |
| 状态合法性 | 状态属于枚举，流转符合 §3.2 |
| 归档规则 | archived Study 已说明归档原因 |
| 对象边界 | Study 未替代 Memo、ADR、WorkPlan、Pitfall 或 docs/sources |
| Human Gate | §5 场景已完成确认或记录降级 |
| Change 追溯 | Study 关键变化有 Git 可追溯记录 |
| Code / Web 边界 | 派生输出未替代 Git 文件事实源 |

---
## 11. 待补齐事项

1. Study 校验 Code、Web 读取和测试应在本文生效后同步补齐；
2. Study 创建、吸收和归档的具体工作流程待 40-59 承接；
3. Study 与 docs/studies 的迁移样例、正反样例和 Human Gate 样例待真实报告落地后补齐。
