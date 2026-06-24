# Code确定性执行规范

```yaml
v2_spec:
  spec_id: "04"
  spec_kind: "spec"
  title: "Code确定性执行规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/04-Code确定性执行规范.md"
  created: "2026-06-23"
  updated: "2026-06-24"
  parent_spec: ""
  relation: ""
  positioning: "定义 v2 Code 的确定性解析、校验、聚合、知识地图投影、诊断反馈、受控写入边界和实现可验证性"
  scope: "LDVH Code、CLI、校验器、派生索引、知识地图只读投影、机器诊断输出、受控写入前检查和 Code 实现测试入口"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/07-事实源边界与Git追溯规范.md"
  related_specs:
    - "specs/02-事实模型基础规范.md"
    - "specs/03-行动编排规范.md"
    - "specs/05-Web信息同步规范.md"
    - "specs/08-测试基础规范.md"
    - "specs/attachments/04.Att.01-Code需求记录字段表.md"
    - "specs/attachments/04.Att.02-Code命令入口表.md"
    - "specs/attachments/04.Att.03-Code结构化输出Schema表.md"
    - "specs/attachments/04.Att.04-Code诊断码表.md"
    - "specs/attachments/04.Att.05-知识地图输入范围表.md"
    - "specs/attachments/04.Att.06-知识地图投影Schema表.md"
    - "specs/attachments/04.Att.07-受控写入前检查矩阵.md"
    - "specs/attachments/04.Att.08-v1-v2-Code消费双读映射矩阵.md"
    - "specs/attachments/04.Att.09-Code回归入口表.md"
    - "specs/attachments/04.Att.10-Code参考实现文档边界清单.md"
  migration_sources:
    - "history/specs-v1/07-Code确定性执行实现规范.md"
  active_fact_source:
    - "specs/04-Code确定性执行规范.md"
  code_consumption:
    - "v2_spec_metadata"
    - "v2_relations"
    - "code_contracts"
    - "diagnostics"
    - "knowledge_map_projection"
    - "knowledge_map_input_scope"
    - "source_refs"
    - "controlled_write_boundaries"
    - "assurance_requirements"
  migration_status: "migrated"
```

> 文件状态：本文是 active 正式规范；正式规则以本文及其授权附件为准。

## 1. 本文解决的问题

本文定义 LDVH Code 如何为 AI 和 Human 提供确定性解析、校验、聚合、诊断、知识地图投影和受控写入前检查。

本文解决：

1. Code 如何消费规范身份、事实模型字段、行动编排成员、事实源和运行时扩展自描述；
2. Code 输出如何作为导航、诊断、聚合或展示输入，而不替代事实源；
3. 知识地图 nodes、edges、diagnostics 和 source refs 如何保持只读投影；
4. Code 如何区分读取、校验、聚合、诊断、受控写入前检查和写入执行；
5. Code 与 Web、行动编排、运行时扩展、事实源和测试治理之间如何分工。

本文不定义事实模型字段契约、行动流程、Web 页面契约、运行时扩展资产登记、Git commit message 契约或测试治理本体。

本文定义 Code 的能力契约、输入输出、来源回指、诊断边界、校验要求和不得越界事项；不限定 Code 的实现语言、框架、依赖、内部模块结构或具体技术栈。当前实现若使用特定语言、命令、目录组织或库，只能作为 Code 实现域事实或参考实现状态，不构成 v2 规范义务。

## 2. 上位依据

本文承接 00 中“用 Code 提供确定性解析、校验、聚合和反馈”的构成要素定位。

本文承接 01 的规范结构、Code 消费、知识地图输入和保障要求规则。若本文与 00、01 或 07 的事实源边界冲突，以 00、01 和 07 为准。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的 Code。

正向价值判断：

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过索引、查询和读取建议降低 AI 盲读成本 |
| V3 正确判断 | 通过确定性诊断暴露字段、锚点、引用、状态和关系缺口 |
| V4 稳定执行 | 通过 CLI、校验器和受控写入前检查减少手工漂移 |
| V6 强制验证 | 通过可复现命令、exit code、结构化输出和测试入口支持验证 |
| V9 人类确认质量 | 为 Web 和报告提供可回指来源的派生数据 |

逆向价值判断：

| 反模式 | 本文必须阻止 |
|---|---|
| Code 输出替代事实源 | Code 输出只作导航、诊断和派生展示，不替代 Git 文件事实源 |
| Code 替代 AI 和 Human 判断 | Code 不判断价值取舍、授权、方向校正或验收确认 |
| Code 反向定义规范 | 实现逻辑不得反向改变字段契约、状态机、Gate 或事实源边界 |
| 知识地图落盘成事实 | 知识地图必须可从事实源实时生成，不成为新事实源 |
| 测试治理混入 Code 本体 | 测试治理归 08；04 只说明 Code 自身实现的可验证入口 |

## 4. Code 能力分层

Code 能力至少分为：

| 能力 | 作用 | 边界 |
|---|---|---|
| 读取 | 读取 Git 文件事实源、规范、对象和配置 | 不改变事实源 |
| 解析 | 提取身份块、字段、章节、锚点、关系和状态 | 不推断未声明规则 |
| 校验 | 检查结构、枚举、引用、锚点、格式和契约 | 不替代 Human Gate |
| 聚合 | 生成索引、集合、矩阵、统计和读取建议 | 不成为集合事实源 |
| 诊断 | 报告缺口、冲突、漂移和降级建议 | 不直接关闭问题 |
| 投影 | 生成知识地图或 Web 消费 DTO | 不落盘为权威事实 |
| 受控写入前检查 | 在写入前检查字段、状态、Gate 和路径 | 不绕过规范、Human Gate 或 Git 追溯 |

受控写入若后续进入 v2，应由对应事实模型、行动编排、Human Gate 和 07 事实源规则共同授权。

## 5. Code 需求准入

Code 只能承接需要确定性解析、校验、聚合、诊断、投影或受控写入前检查的需求。下列条件至少命中一项时，才能提出 Code 需求：

1. 同一规则需要反复机械检查；
2. AI 容易因为上下文过长、字段分散或引用复杂而误读；
3. Web、知识地图、Rules、Hook 或行动编排需要稳定机器输出；
4. 事实模型、规范、行动编排、Git 追溯或运行时扩展需要结构化诊断；
5. 写入前需要用确定性检查暴露路径、字段、状态、Gate 或事实源风险。

下列内容不得作为 Code 需求准入理由：

1. 用 Code 替代规范正文；
2. 用 Code 判断价值取舍、方向校正、授权或验收；
3. 用 Code 固化尚未被规范确认的候选规则；
4. 用 Code 绕过 Human Gate；
5. 为一次性讨论、临时展示或无法复现的环境观察新增长期实现。

提出 Code 需求时，应能回指来源规范、事实源、行动编排成员或 Human Gate 记录；无法回指时，只能记录为待澄清需求，不得直接实现为规则。

Code 需求记录字段表由 `attachments/04.Att.01-Code需求记录字段表.md` 承载。需求记录只能说明来源、输入范围、输出形式、写入行为、验证方式和降级方式，不得替代正式规范或 Human Gate。

## 6. Code 实现纪律

Code 实现必须以规范和事实源为输入，不得反向定义规范。实现纪律包括：

1. 最小确定性实现：只实现已被规范、事实模型或行动编排授权的可机械判断；
2. 明确输入输出：命令、函数或 DTO 应声明输入范围、输出字段、错误条件和来源回指；
3. 明确失败条件：无法解析、来源缺失、冲突、越权或降级时，应输出诊断，不得静默猜测；
4. 不隐式写入：读取、解析、校验、聚合、诊断和投影默认不得修改事实源；
5. 不硬编码候选规则：未进入 active 或待迁移草案的规则不得被实现为默认判断；
6. 不把测试、Web 或运行时扩展的便利字段反向写成规范字段。
7. 不直接调用 AI、Skill 或 Agent 生成确定性结论；AI、Skill 和 Agent 可以作为过程输入或行动编排能力，但 Code 的确定性输出必须来自可复查文件、参数、命令、Git 记录或其它可解析输入。

Code 变更必须遵守“文档约束先行、测试或等价验证先行、实现后行”的前置纪律。新增或改变 Code 行为前，应先确认：

1. 规则来源能回指规范、事实模型成员、行动编排成员、事实源或 Human Gate；
2. 正例、反例、失败条件和降级路径可描述；
3. 自动化测试、命令校验或等价验证入口已确定；
4. 输出字段、诊断等级、exit code 和来源回指不会反向改变规范；
5. 无法先建立测试或等价验证时，必须记录原因、残留风险和后续补齐位置。

当 Code 暴露出规范缺口、字段缺口、流程缺口或事实源冲突时，应输出诊断并交还对应规范或行动编排处理；Code 不得自行补全规则。

## 7. 结构化输出、诊断与派生产物边界

Code 输出分为结构化结果、诊断、派生索引、过程输出和写入前检查结果。

| 输出类型 | 可用于 | 不得用于 |
|---|---|---|
| 结构化结果 | Web DTO、知识地图输入、行动编排判断辅助 | 替代事实源字段 |
| 诊断 | 暴露缺口、冲突、漂移、降级和建议回写方向 | 直接关闭问题 |
| 派生索引 | 导航、读取建议、成员集合、章节定位 | 成为手写目录或集合事实源 |
| 过程输出 | 临时分析、命令报告、一次性迁移辅助 | 长期事实源 |
| 写入前检查结果 | 暴露写入风险、Gate 条件和事实源边界 | 直接授权写入 |

派生索引和知识地图可以由命令输出到临时文件或 stdout 供 AI、Web 或 Human 阅读，但默认不落盘为权威文件。若后续需要保留某类派生产物，应由 07 判断事实源边界，并由对应构成要素规范声明权威位置。

Code 命令入口表由 `attachments/04.Att.02-Code命令入口表.md` 承载。结构化输出通用 Schema 由 `attachments/04.Att.03-Code结构化输出Schema表.md` 承载。Code 诊断码与诊断字段由 `attachments/04.Att.04-Code诊断码表.md` 承载。

过程输出必须区分候选输出、诊断输出、权威写入前检查和已写入事实源。Code 输出无法回指来源、无法区分候选与权威写入、或无法说明降级风险时，不得被行动编排、Web 或 Human 当作稳定事实使用。

## 8. v1-v2 兼容底线

Code v2 不能一次性替换 v1 Code。它应先提供兼容、诊断和投影层，并至少保留或映射：

1. v1 `ldvh_doc` 元信息；
2. v1 `ldvh_member` 成员自描述；
3. v1 保障要求、Human Gate、待补齐事项等章节锚点；
4. v1 字段注册表列名和枚举；
5. v1 事实对象类型、目录、状态、字段和 DTO；
6. v1 workflow member、`assurance_takeover`、`capability_assets`；
7. v1 Web Spark 创建白名单和 WorkCase orchestration 展示字段；
8. v1 测试命令和回归入口的可发现关系；测试治理归 08。

v2 active 后，Code 可以保留对 v1 历史身份块的只读解析能力，用于历史追溯、迁移审计和价值提取。历史双读只用于诊断和追溯，不得把 `history/specs-v1/` 解释为 active 规范，不得让旧身份块覆盖当前 active `specs/`。

v1-v2 Code 消费双读映射矩阵由 `attachments/04.Att.08-v1-v2-Code消费双读映射矩阵.md` 承载。v2 active 后，`v2-check` 和 `specs_validate.py all` 均默认读取当前 active `specs/`；历史双读、旧身份块兼容和迁移覆盖检查不得替代 active specs 诊断。

## 9. 知识地图输出边界

知识地图是 Code 基于规范结构、事实模型、管辖项目配置和运行时扩展自描述生成的只读派生投影。

知识地图服务运行时入口导航是其核心价值之一。Rules 资产可以消费知识地图投影，用于规范定位、最小读取、来源回指、影响判断和同步风险提示；Code 只能提供当次只读投影和诊断，不得把知识地图输出落盘为 Rules 缓存、环境配置、事实对象字段或第二事实源。

Code/知识地图可以发现、定位和提示 Rules 资产同步影响，尤其是 active specs 变化可能影响哪些 Rules `source_specs`、入口读取顺序、STOP 点、验证入口或交接路径；但 Code 不得决定 Rules 正文如何修改，不得自动写入 Rules，不得把影响面投影缓存为 Rules 事实源。

知识地图输入范围必须受控。Code 只能把以下内容纳入知识地图节点和边：

1. active `specs/` 中可由身份块、规范结构或事实源边界识别的正式规范、附件、成员主文件和事实对象；
2. 01 当前目录登记明确授权的 active 规范、附件或成员主文件，且文件自身具有 `v2_spec`、`v2_attachment`、`v2_fact_model_member` 或 `v2_action_member` 身份块；
3. 工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 中已登记的管辖项目配置事实源；
4. 管辖项目 `ldvh-base/` 中由 02 和 20-29 成员主文件授权的事实实例、对象 ID、字段路径和对象关系；
5. 运行时扩展、Code、Web 或测试入口中带有稳定自描述、来源规范和 canonical path 的承载物。

下列内容不得作为知识地图节点或关系边的权威输入：

1. `PLAN.md`、`MIGRATION-MAP.md`、`AUDIT-*.md`、临时审查输出、过程计划、讨论记录和一次性命令报告；
2. 未登记、无身份块、来源不可回指或状态不可判断的草稿文件；
3. Web 缓存、测试缓存、截图、trace、页面筛选状态或聊天过程；
4. 只表达建议、猜测或候选判断且未进入规范身份块、附件授权、成员身份或事实源记录的内容。

被排除的输入可以出现在 `diagnostics` 或 `excluded_inputs` 中，但不得静默生成节点或边。

知识地图输入范围表由 `attachments/04.Att.05-知识地图输入范围表.md` 承载。该附件只说明允许输入、排除输入、后置输入和降级诊断，不得把知识地图运行时能力提前为当前主线。

知识地图查询必须按范围和层级受控展开。Code 至少应支持以下读取层级：

| 层级 | Code 输出 | 约束 |
|---|---|---|
| 入口层 | 节点摘要、状态、路径、归属、上位依据、附件和消费类别 | 默认层级，不读取原文全文或全量事实对象正文 |
| 邻接层 | 指定节点的一跳关系和来源回指 | 只围绕指定节点展开，不隐式返回全图 |
| 展开层 | 二跳、多跳、影响面、阻塞链、证据链、收敛链和跨项目边 | 必须由调用方提供任务目的、起点和深度或关系类型 |
| 原文层 | 规范正文片段、附件表格、事实对象全文或测试输出 | 仅在关系视图不足以判断或需要验证证据时返回 |

Code 不得把“生成知识地图”实现为一次性全量上下文注入。CLI/API/Web 调用应能声明 `input_scope`、`project_scope`、`start_node`、`relation_types`、`depth` 和是否允许原文层展开；未声明时必须使用最小默认范围。

知识地图作为 AI 任务导航时，Code 必须支持以具体规范、附件、行动成员、运行时扩展承载物、工作对象或节点 ID 作为 `start_node` 的邻接查询。该查询至少应让 AI 能看见起点节点的状态、权威、路径、上位依据、相关规范、Code 消费类别、来源回指和一跳关系。`v2-check --format text` 只表示 active specs 结构诊断和知识地图汇总健康状态，不能替代带 `start_node` 的任务导航；当 AI 需要判断某个对象“该读什么、影响谁、能否 active、是否触发 Rules 同步”时，应使用 `knowledge-map --layer neighbors --start-node <path-or-node>` 或等价结构化查询。

知识地图承担“在什么情况读什么文件”的入口导航责任时，Code 不应只把节点和边交给 AI 自行推理。结构化输出必须提供面向行动的 `navigation`、`read_plan`、`next_queries`、`stop_conditions` 和 `impact_summary`：`navigation` 说明任务类型、起点、有效输入范围和降级状态；`read_plan` 给出最小原文读取计划，至少包含路径、节点、优先级、读取角色、原因、来源关系、建议章节或字段和来源回指；`next_queries` 给出需要继续渐进展开时的后续查询；`stop_conditions` 提示必须暂停、降级或回到 Human Gate 的条件；`impact_summary` 汇总受影响规范、运行时扩展、工作对象和关系类型。Rules 入口在正常路径下应消费这些字段，不应长期维护与这些字段重复的大段静态 specs 读取路线。

当输入范围、起点节点、关系类型或层级不足以支撑任务判断时，Code 应通过 `diagnostics`、`degraded`、`review_hints` 或等价结构化字段提示调用方补充查询或退回文件事实源。Code 不得用“节点数/边数/诊断数”这类汇总指标暗示具体任务已经完成定位、影响分析或 active 条件判断。

知识地图必须支持项目命名空间。Code 读取管辖项目时，应先读取并校验工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml`，再按项目范围生成投影。项目范围至少包括：

1. `current_project`：只读取当前命中的管辖项目；
2. `all_governed_projects`：读取所有已登记管辖项目；
3. `explicit_projects`：只读取调用方明确指定的项目集合。

节点、边和诊断必须携带项目维度。对象节点不得使用 `spark-0016`、`workcase-0001` 等裸对象 ID 作为全局 ID；全局节点 ID 必须组合 `project_id`、对象类型、对象 ID 和必要路径。跨项目关系必须显式声明 `from_project`、`to_project`、来源路径和关系类型，不能因路径相似、编号相同或标题相近而猜测隐含关系。

Code 读取管辖项目时只能读取登记项目根目录内的 `ldvh-base/`、该项目 Git 记录，以及项目自身约定、用户明确指令、当前任务上下文或 Human Gate 授权的文档位置。项目缺少 `ldvh-base/`、Git 不可读、路径越界、引用目标不存在或文档位置未授权时，应输出当次 `diagnostics`，不得写入缓存、不得补写事实字段、不得修改 `LDVH-GOVERNED-PROJECTS.yaml`。

Git 历史查询不进入知识地图默认输入范围，也不要求 LDVH 建立专用 Git 图谱或查询层。需要追溯历史时，应使用 Git 原生命令按需查询 commit hash、commit message、changed files、diff、author/date 和 commit range；LDVH 只要求 commit message 格式满足 07，以便未来可读、可查、可追溯。

知识地图输出至少包含：

1. `nodes`；
2. `edges`；
3. `diagnostics`；
4. `source_refs`；
5. `project_namespace`；
6. `generated_at`；
7. `tool`；
8. `input_scope`；
9. `schema_version`；
10. `degraded`；
11. `navigation`；
12. `read_plan`；
13. `next_queries`；
14. `stop_conditions`；
15. `impact_summary`。

节点至少声明 `id`、`type`、`label`、`canonical_path`、`source_refs`、`project_namespace`、`status` 和 `authority`。跨项目节点 ID 必须包含 `project_namespace`，不得使用裸对象 ID 当全局节点。节点类型至少覆盖规范、附件、事实模型成员、行动编排成员、工作对象、事实实例、对象字段、管辖项目配置、运行时扩展、Code 入口、Web 视图和事实源。

关系边至少声明 `id`、`type`、`from`、`to`、`source_refs`、`direction` 和 `derived_from`。边类型必须来自 `attachments/01.Att.01-知识地图关系类型表.md`，不得由 Code 临时创造。

`source_refs` 至少能回指 `path`、`line_start` 和 `line_end`；需要定位对象、字段、章节或锚点时，应补充 `object_id`、`field_path`、`field` 或 `anchor`。无法提供来源回指的节点、边或诊断不得被输出为可信投影。

`diagnostics` 至少声明 `severity`、`code`、`message`、`source_refs` 和 `suggested_owner`。诊断等级闭集为 `error`、`warning`、`info`；遇到输入范围不明、关系类型不明、来源缺失、v1/v2 权威冲突或 Schema 不完整时，必须输出诊断并将 `degraded` 标记为 true。

知识地图投影目标 Schema 由 `attachments/04.Att.06-知识地图投影Schema表.md` 承载。当前 `v2-check` 可以输出 active specs 诊断和只读知识地图预览子集，但必须通过 `degraded`、`diagnostics` 或 review hints 暴露未实现的输入范围、原文层、多项目层或 raw 层，不得伪装为完整知识地图运行时。

历史价值提取期间，知识地图可以只读消费 v1 历史事实源和当前 active `specs/`，用于发现仍有价值的需求、决策、证据、经验、风险和未完成事项。双读不得把历史事实源解释为 active 权威，也不得让历史图谱边覆盖当前 active 规则。

Code 不得落盘知识地图缓存，不得让知识地图反向维护管辖项目配置、规范正文、事实对象或 Git 提交记录。

知识地图输出只能进入 stdout、HTTP response、当次审核报告正文或等价的一次性调用结果。Code 不得写入长期 JSON、SQLite、外部图数据库、Web 本地缓存或其它派生图状态；若调用方要求持久化图谱结果，Code 必须拒绝或输出诊断。

## 10. 受控写入前检查

Code 可以提供受控写入前检查。该检查只回答“本次写入是否满足已知结构、路径、字段、状态、Gate、事实源和追溯前置条件”，不回答“是否应该写入”。

受控写入前检查必须覆盖：

1. 写入目标是否为规范、事实模型、行动编排、Code、Web、运行时扩展、测试或其它事实源的授权位置；
2. 写入字段、状态、枚举、路径和锚点是否符合对应规范；
3. 是否触发 Human Gate；
4. 是否需要 Git commit records 追溯；
5. 是否存在跨规范、Web、运行时扩展或测试同步影响；当写入目标为 specs 或运行时扩展承载物时，应提示可能受影响的固定 Rules 资产、自描述字段、入口读取顺序、STOP 点、验证入口和降级路径；
6. 检查失败时应回到哪个规范、对象或行动编排。

Code 不得因检查通过而自动写入事实源。真正写入必须由对应事实模型、行动编排、Human Gate、07 事实源规则和 Git 追溯共同授权。

受控写入前检查矩阵由 `attachments/04.Att.07-受控写入前检查矩阵.md` 承载。该矩阵只定义 preflight，不定义实际写入执行。

## 11. Code 生命周期维护

以下变化发生后，必须检查 Code 是否需要同步：

1. 规范编号、身份块、章节骨架、附件规则或知识地图输入规则变化；
2. 事实模型字段、状态、对象目录、受控写入或成员自描述变化；
3. 行动编排成员、`assurance_takeover`、`capability_assets` 或可测试性锚点变化；
4. Web DTO、API contract、页面展示或受控轻写入白名单变化；
5. 运行时扩展资产自描述、Hook 配置、Rules 入口、Rules 同步影响判断或环境适配规则变化；
6. 事实源边界、Git commit message 契约、关联提交派生或回写规则变化；
7. 测试入口、回归命令、夹具或验证声明规则变化。

删除、重命名或替换 Code 命令前，必须检查调用方、Rules/Skill/Hook、Web、测试、项目根 README 和行动编排成员是否仍引用旧入口。

Code 回归入口表由 `attachments/04.Att.09-Code回归入口表.md` 承载。Code 参考实现文档边界清单由 `attachments/04.Att.10-Code参考实现文档边界清单.md` 承载。

## 12. 与其它规范的边界

| 规范 | Code 消费方式 | 不得越界 |
|---|---|---|
| 02 | 消费事实模型、字段契约、字段注册和成员自描述 | 不定义模型 schema 或状态机 |
| 03 | 消费行动成员、锚点、接管关系和能力资产 | 不决定流程价值或 Gate 结论 |
| 05 | 为 Web 提供 DTO、派生视图和诊断输入 | 不维护 Web 页面契约 |
| 06 | 消费 Rules/Skill/Agent/Hook 自描述和环境适配输入 | 不声明环境完整支持 |
| 07 | 消费事实源边界和 commit message 契约 | 不替代 Git 文件事实源或 Git 原生命令 |
| 08 | 暴露 Code 实现测试入口和可验证性 | 不定义测试治理标准 |

## 13. 附件规则

本文授权以下附件。附件只承载主文档已经授权的字段表、命令表、Schema 表、矩阵或清单，不定义新的 Code 原则、行动流程、Web 页面契约、事实模型字段或 Human Gate。

| 附件 | 单一信息对象 | 不得承载 |
|---|---|---|
| `attachments/04.Att.01-Code需求记录字段表.md` | Code 需求记录字段表 | 正式规则、实现代码 |
| `attachments/04.Att.02-Code命令入口表.md` | Code 命令入口表 | 命令实现、测试治理 |
| `attachments/04.Att.03-Code结构化输出Schema表.md` | Code 通用结构化输出字段 | 具体命令完整 Schema |
| `attachments/04.Att.04-Code诊断码表.md` | Code 诊断字段和等级 | 诊断实现、关闭判断 |
| `attachments/04.Att.05-知识地图输入范围表.md` | 知识地图输入范围 | 运行时图谱实现 |
| `attachments/04.Att.06-知识地图投影Schema表.md` | 知识地图目标投影 Schema | 持久图谱缓存 |
| `attachments/04.Att.07-受控写入前检查矩阵.md` | 受控写入 preflight 检查矩阵 | 实际写入授权 |
| `attachments/04.Att.08-v1-v2-Code消费双读映射矩阵.md` | v1-v2 Code 消费双读映射 | active 切换决定 |
| `attachments/04.Att.09-Code回归入口表.md` | Code 回归入口表 | 测试治理本体 |
| `attachments/04.Att.10-Code参考实现文档边界清单.md` | Code 参考实现文档边界 | 正式规范规则 |

新增、删除、重命名或改变以上附件的信息对象时，应回到本文 Human Gate，并同步 01 当前目录登记和 Code v2 解析。

## 14. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Code 能力应承接 00、01、active 07 和对应构成要素规范，不反向定义规范规则 | 本文、00、01、07、相关规范、Human Gate | Code 治理 | Code 输入输出、诊断或写入边界变化时 |
| 入口可见要求 | AI 需要查询、校验、聚合、诊断或生成知识地图时应能定位 Code 入口；涉及具体规范、附件、行动成员、运行时扩展承载物或 Rules 影响判断时，应能定位带 `start_node` 的知识地图任务导航入口 | CLI 帮助、Rules 入口、README、人工降级检查 | AI 执行入口提示 | 命令入口、帮助文本、任务导航入口或读取顺序变化时 |
| 确定性执行要求 | 可机械检查内容应由 Code 输出稳定 exit code、结构化诊断和来源回指 | Code 实现、测试、CI、人工降级检查 | 校验实现 | 解析规则、输出 Schema、诊断等级或输入范围变化时 |
| 知识地图投影要求 | 知识地图必须声明受控输入范围、最小输出 Schema、关系类型闭集、来源回指、降级诊断和以 `start_node` 为核心的任务导航语义；汇总健康检查不得替代具体任务定位 | 本文、01.Att.01、07、Code 检查、测试 | 派生投影 | 知识地图输入、节点、边、诊断、来源回指、任务导航语义或双读规则变化时 |
| 受控写入前检查要求 | 任何 Code 写入前检查都必须暴露路径、字段、状态、Gate、事实源和追溯风险，且不得直接授权写入 | Code 检查、07、Human Gate、行动编排 | 受控写入 | 写入前检查能力新增、扩大或失败时 |
| Human 交互要求 | 接受 Code 长期降级、受控写入、环境能力声明或高影响自动修复前应评估 Human Gate | Human Gate、影响范围说明、确认记录 | Human Gate | Code 越过只读/诊断边界或影响事实源时 |
| 生命周期触发要求 | 规范、事实模型、行动编排、Web、运行时扩展、事实源或测试变化后，应检查 Code 消费是否同步 | Code 回归、知识地图诊断、测试、人工降级检查 | 生命周期同步 | 任一上游结构或消费契约变化时 |

## 15. Human Gate

以下情况必须暂停并等待 Human 确认：

1. 将 Code 输出升级为事实源；
2. 启用或扩大受控写入能力；
3. 改变 Code 对事实模型状态、Human Gate、事实源回写或 Git 追溯的判断边界；
4. 接受关键 Code 校验长期降级；
5. 声明某环境已完整支持某 Code/Hook/CI 能力；
6. 删除关键回归入口或让 Web/运行时扩展依赖未验证 DTO。

## 16. Code 检查要求

Code 检查至少包括：

| 检查项 | 标准 |
|---|---|
| 来源回指 | 输出能回到路径、章节、对象 ID、字段或 commit hash |
| 事实源边界 | 输出没有替代 Git 文件事实源 |
| 结构稳定 | 输出 Schema、诊断等级和 exit code 可复现 |
| 知识地图投影 | 输入范围、关系类型、节点边 Schema、来源回指和 `degraded` 状态可检查 |
| 附件身份一致性 | `attachment_id`、标题、真实路径、`canonical_path`、父规范登记和当前目录登记一致 |
| 跨规范消费 | 02、03、05、06、07、08 的消费边界清晰 |
| 写入前检查 | 写入风险只被报告，不被 Code 直接授权 |
| 测试入口 | 关键 CLI 和诊断有对应测试或等价验证说明 |

## 17. 待补齐事项

1. 本文和 `04.Att.01` 至 `04.Att.10` 已承接 v1 `07` 主体规则，并已作为 active Code 确定性执行规范生效；
2. 盘点 `code/specs_validate.py`、`code/fact_cli.py`、`code/commit_validate.py`、`code/hook_dispatch.py` 和 `code/spec_checks` 的 active specs 兼容策略；
3. 将本文定义的知识地图最小投影契约细化为实现 Schema、正反样例和测试夹具；
4. 明确 v1-v2 双读、降级诊断和迁移覆盖检查；
5. 补齐 v2 附件身份一致性检查，覆盖真实路径、身份块、父规范登记、当前目录登记和旧引用残留；
6. 与 08 对齐 Code 实现测试入口和验证声明；
7. 与 05 对齐 Web DTO 和 Human-facing 派生展示输入；
8. 当前 `v2-check` 已提供 active specs 结构诊断、显式 `runtime_extensions` 只读范围和只读知识地图预览，`preflight` 已提供受控写入前检查第一版并能提示固定 Rules 资产同步影响；仍需补齐完整历史双读、完整诊断 Schema、完整知识地图目标 Schema 和字段级 Schema 检查。
