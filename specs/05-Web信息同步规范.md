# Web信息同步规范

```yaml
v2_spec:
  spec_id: "05"
  spec_kind: "spec"
  title: "Web信息同步规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/05-Web信息同步规范.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: ""
  relation: ""
  positioning: "定义 v2 Web 的 Human-facing 派生展示、状态可见、风险可见、证据可见、受控轻写入和信息同步边界"
  scope: "LDVH Web、Human-facing 派生视图、事实对象 DTO、提交记录展示、知识地图展示、受控轻写入白名单、Confirm UI 和 Web 与 Code/事实源/测试的消费边界"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/07-事实源边界与Git追溯规范.md"
  related_specs:
    - "specs/02-事实模型基础规范.md"
    - "specs/03-行动编排规范.md"
    - "specs/04-Code确定性执行规范.md"
    - "specs/06-运行时扩展规范.md"
    - "specs/08-测试基础规范.md"
    - "specs/attachments/05.Att.01-DTO与API契约表.md"
    - "specs/attachments/05.Att.02-页面与API映射矩阵.md"
    - "specs/attachments/05.Att.03-轻写入白名单表.md"
    - "specs/attachments/05.Att.04-Confirm-UI字段表.md"
    - "specs/attachments/05.Att.05-Gate与Validate阶段边界矩阵.md"
    - "specs/attachments/05.Att.06-Human-facing态势语义表.md"
    - "specs/attachments/05.Att.07-提交记录展示矩阵.md"
    - "specs/attachments/05.Att.08-缓存与同步状态矩阵.md"
    - "specs/attachments/05.Att.09-Web回归矩阵.md"
    - "specs/attachments/05.Att.10-Web差距审计模板.md"
    - "specs/attachments/05.Att.11-Web能力删除核对表.md"
  migration_sources:
    - "history/specs-v1/08-Web信息同步实现规范.md"
    - "history/specs-v1/05.03-字段注册与消费规范.md"
    - "history/specs-v1/10-Git提交规范.md"
    - "history/specs-v1/11-测试基础规范.md"
    - "history/specs-v1/04.02-LDVH能力资产与保障机制规范.md"
    - "history/specs-v1/04.03-环境入口适配与部署规范.md"
    - "history/specs-v1/20-Spark-火花.md"
    - "history/specs-v1/21-WorkCase-工作项.md"
  active_fact_source:
    - "specs/05-Web信息同步规范.md"
  code_consumption:
    - "v2_spec_metadata"
    - "v2_relations"
    - "web_contracts"
    - "dto_boundaries"
    - "human_visible_states"
    - "knowledge_map_display"
    - "controlled_light_write_boundaries"
    - "assurance_requirements"
  migration_status: "migrated"
```

> 文件状态：本文是 active 正式规范；正式规则以本文及其授权附件为准。

## 1. 本文解决的问题

本文定义 LDVH Web 如何帮助 Human 看见状态、风险、证据和待确认事项，同时不成为第二事实源。

LDVH 整体以 AI 执行者为第一服务对象；Web 的直接服务对象是 Human。Web 设计必须服务 Human 的理解、判断、确认、验收和方向校正，使 Human 能看见 AI 正在依据什么执行、哪些事项需要介入、哪些证据支持关闭或继续推进。Web 不得按传统项目管理看板优先设计后再要求 AI 适配。

本文解决：

1. Web 如何消费 Code DTO、事实模型、Git 提交记录和知识地图投影；
2. Web 如何展示 Human-facing 状态、风险、证据、关联提交和待确认事项；
3. Web 何时可以提供受控轻写入，何时必须只读展示；
4. Web 页面状态、缓存、筛选和派生视图为什么不能替代 Git 文件事实源；
5. Web 暂不实施时，哪些 v1 契约仍必须作为迁移回归线保留。

本文不定义事实模型字段、Code 输出 Schema、Git 提交契约、测试治理或运行时扩展入口。

本文定义 Web 的能力契约、消费边界、展示要求、交互白名单、验收条件和不得越界事项；不限定 Web 的实现语言、框架、依赖、后端/前端拆分、内部模块结构或具体技术栈。当前实现若使用特定框架、路由、组件、目录组织或缓存机制，只能作为 Web 实现域事实或参考实现状态，不构成 v2 规范义务。

DTO 与 API 契约由 `attachments/05.Att.01-DTO与API契约表.md` 承载；页面与 API 映射由 `attachments/05.Att.02-页面与API映射矩阵.md` 承载。

## 2. 上位依据

本文承接 00 中“用 Web 帮助 Human 看见状态、风险、证据和待确认事项”的构成要素定位。

本文承接 01 的规范结构和 07 的事实源边界。Web 所有展示和交互都必须能回指 Git 文件事实源、Code 派生输出或明确 Human Gate 记录。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的 Web。

正向价值判断：

| 价值 | 本文如何服务 |
|---|---|
| V2 可行动理解 | 用页面组织让 Human 和 AI 看见对象状态、风险和证据 |
| V5 门禁识别 | 通过 Confirm UI 和待确认事项呈现高影响选择 |
| V7 证据沉淀 | 展示证据来源和回指路径，帮助判断是否可追溯 |
| V9 人类确认质量 | 提供 Human-facing 状态、风险、提交记录和诊断视图 |
| V10 持续完善 | 展示反复问题、缺口和待分流线索 |

逆向价值判断：

| 反模式 | 本文必须阻止 |
|---|---|
| Web 状态替代事实源 | 页面状态、缓存和筛选结果不得成为权威事实 |
| Web 反向定义对象规则 | Web 表单和 DTO 不得反向改变字段契约或状态机 |
| Web 绕过 Human Gate | Confirm UI 不等于 Human 已授权，必须记录确认范围 |
| Web 暂停实施导致契约丢失 | Web v2 暂不实施，但 DTO、白名单和展示边界仍是回归线 |

## 4. Web 信息同步边界

Web 是派生展示和受控交互层。Web 可以读取 Code 输出、事实对象、规范索引、Git 提交记录和知识地图投影，但不得独立维护稳定事实。

Web 可以提供：

1. 事实对象列表、详情、状态和风险展示；
2. 规范、字段、行动、运行时扩展和事实源关系展示；
3. Git 提交记录、关联提交和变更影响面展示；
4. Code 诊断、测试状态和待确认事项展示；
5. 受控轻写入白名单内的交互入口；
6. Human Gate 提醒、确认范围呈现和确认结果回写入口。

Web 不得提供：

1. 未经事实模型授权的字段写入；
2. 未经行动编排或 Human Gate 授权的状态流转；
3. 用页面缓存替代 Git 文件事实源；
4. 用 UI 标签替代规范字段或对象状态；
5. 用前端路由创造新的工作对象类别。

## 5. 同源读取与派生展示

Web 必须与 Code 和 AI 读取同一事实源。Web 可以独立聚合和展示 Git 文件事实源、Code DTO、Git commit records、知识地图只读投影和测试状态，但不得维护第二套字段契约、状态机、对象目录或事实源归口。

Web 派生展示必须满足：

1. 展示数据能回指事实源路径、对象 ID、章节锚点、Code 输出或 commit hash；
2. 页面状态、筛选状态、缓存、排序、颜色、标签和布局不成为稳定事实；
3. 页面上的缺口、风险和待确认事项必须能回指来源，不得凭 UI 自造结论；
4. Web 与 Code 对同一对象出现差异时，必须退回事实源和 Code 诊断，不得以页面显示覆盖事实源。

Web 可以展示知识地图，但只能消费 04 定义的知识地图只读投影。知识地图展示必须满足：

1. 每个节点和关系边都能查看或追溯 `source_refs`；
2. 关系边类型来自 `attachments/01.Att.01-知识地图关系类型表.md`；
3. `diagnostics`、`excluded_inputs` 和 `degraded` 状态必须对 Human 可见；
4. 图布局、筛选、折叠、颜色和交互状态不成为稳定事实；
5. Web 不得补写 Code 未输出的节点、关系边或来源回指；
6. Web 必须呈现本次查询的 `input_scope`、`project_scope`、生成时间、降级原因和项目命名空间；
7. 跨项目关系必须显示来源项目和目标项目，不得把不同项目中的同名对象 ID 合并展示为同一节点。

Web 展示知识地图必须使用无缓存语义。API 响应应使用 `Cache-Control: no-store` 或等价措施；前端不得使用 localStorage、sessionStorage、IndexedDB、Service Worker cache 或等价浏览器持久化机制保存图谱节点、关系边、诊断结果、项目范围或展开状态。页面可以在内存中保留当前交互态，但刷新、重新查询或事实源变化后必须重新向 Code/API 获取只读投影。

Web 与 Code 是同源协作关系，不是强制上下游关系。Web 可以为 Human-facing 热路径独立实现读取、解析、筛选、排序、聚合、缓存和 API；Web 消费 Code DTO 或诊断输出不意味着所有 Web 页面必须经由 Code。Web 原生实现只能处理读取、解析、筛选、排序、聚合和展示，不得新增字段契约、状态机、验收规则、事实源归口或写入能力。

Web AI、并行 AI 或其他执行者承接 Web 工作前，必须先按 `attachments/05.Att.10-Web差距审计模板.md` 做只读差距审计，至少按页面或 API 列出事实源来源、派生状态、Human Gate、写入白名单、测试归属、错误态和需要 Human 决策的事项。

## 6. 受控轻写入白名单

Web 默认只读。Web 只有在规范明确授权、事实模型字段边界清晰、API contract 可测试、失败可回滚且 Git 追溯路径明确时，才能提供受控轻写入。

v1 迁移期间必须保留的轻写入白名单只有 Spark quick create：

| 写入入口 | 允许字段 | 固定写入 | 禁止写入 |
|---|---|---|---|
| `POST /api/sparks` | `title`、`description`、`priority` | `status: pending`、`source: web` | `status_history`、关闭状态、验收字段、长期证据字段、非 Spark 对象字段 |

Spark quick create 必须写后读取并验证事实源结果。写入失败、字段不合法、路径冲突、Human Gate 缺失或事实源不可追溯时，Web 必须返回错误，不得静默缓存为“已创建”。

轻写入白名单由 `attachments/05.Att.03-轻写入白名单表.md` 承载。Web 不得提供通用 `PATCH`、`PUT`、`DELETE`、任意 YAML 编辑器或白名单外对象字段写回接口。Spark quick create API 必须区分成功、字段错误、冲突、写入失败和写后验证失败，并由 08 授权的 Web 回归入口覆盖成功、字段错误、冲突和写后验证路径。

新增、删除或扩大任何 Web 写入入口，必须先修改本文或对应事实模型规范，并通过 Human Gate。

## 7. WorkCase 与行动状态展示

Web 可以展示 WorkCase 的执行姿态、阻塞、验证、Human Gate、关闭材料和关联证据，但不得把行动编排执行项创造为新的事实模型对象。

WorkCase 页面至少应区分：

1. 工作对象自身状态；
2. 行动编排派生出的执行姿态；
3. 阻塞原因；
4. 验证状态；
5. Human Gate 待确认事项；
6. 关闭判断所需材料；
7. 来源事实和关联提交。

Web 呈现派生态势时，不得只使用不能回答原因的泛化状态词。凡是 Web 根据事实源字段、对象关系、状态机、Code 输出或后端聚合生成的 Human-facing 态势，都应同时展示原因语义和可追溯依据。

派生态势原因语义必须满足：

1. 态势标签不得反向定义事实源状态机；
2. 同一事实源状态在不同原因下需要拆分展示时，应拆分为不同 Human-facing 态势；
3. “等待”“阻塞”“风险”“需要确认”“验证失败”“待执行”等态势必须能回指事实源字段、对象关系、Code 输出、Web 后端确定性聚合或明确 Human 输入；
4. 等待类态势必须区分等待前置、等待验证、等待 Human Gate、等待事实源回写或待执行，不得用一个“等待中”覆盖；
5. 态势条、状态图标、列表、详情和扩展阅读区必须消费同一套原因语义，不得维护互相冲突的标签、颜色、图标或排序。

行动编排成员、执行步骤、Gate 和回写触发由 03 及具体成员主文件定义。Web 只做 Human-facing 展示和受控交互入口，不决定流程进入、暂停、完成或关闭。

Human-facing 态势语义由 `attachments/05.Att.06-Human-facing态势语义表.md` 承载。页面、态势条、状态图标、列表卡片、对象详情和扩展阅读区必须消费同一套原因语义，不得维护互相冲突的标签、颜色、图标或排序。

## 8. 提交记录与关联提交展示

Web 可以展示 Git commit records、Changelog、关联提交和对象详情中的提交追溯信息。提交记录展示必须来自 Git history、Code commit DTO 或 07 授权的派生规则。

Web 不得：

1. 创建 `ldvh-base/changes/` 或等价手写 change 对象；
2. 让用户手写 `related_changes` 或 `related_commits` 作为对象事实；
3. 用页面上的关联提交覆盖 Git history 和 Code 派生结果；
4. 把提交记录描述为工作对象生命周期状态。

Changelog、Dashboard、ProjectFiles 和对象详情若展示同一提交信息，应共享同一 Code DTO 或同一派生规则，不得维护多套解析逻辑。

提交记录展示矩阵由 `attachments/05.Att.07-提交记录展示矩阵.md` 承载。`/changelog` 是 Web 路由和展示名称，不是新的事实源；commit body 应作为提交说明优先展示，改动文件默认收起，复制给 AI 的上下文应保留原始 commit token、body 和可追溯来源。

## 9. Confirm UI、Gate 与验证展示

Confirm UI 是 Human-facing 交互入口，不等于 Human Gate 已完成。Web 展示确认、授权、验收或关闭动作时，必须呈现：

1. 确认对象；
2. 影响范围；
3. 关联事实源；
4. 证据或验证状态；
5. 确认后的回写位置；
6. 取消、失败或降级后的状态。

Web 可以展示 Gate、Validate、待确认事项和验证结果，但不得用按钮点击替代行动编排 Gate、测试验证声明、事实源回写或 Human 的高影响判断。

Confirm UI 字段由 `attachments/05.Att.04-Confirm-UI字段表.md` 承载。Confirm UI 至少应支持 Gate 触发原因、确认对象、影响范围、确认依据、风险、可替代方案、用户选择、确认人/时间、确认后的执行动作、验证结果、错误状态、降级说明、回写位置和残留风险被 Human 看见或被确认结果记录。

Gate 与 Validate 阶段边界由 `attachments/05.Att.05-Gate与Validate阶段边界矩阵.md` 承载。Gate 只能展示候选待确认事项、确认对象、影响范围、风险和可选操作；在回写合同、对象规范和 Human Gate 证据落点明确前，确认、取消、暂缓和修改反馈只能作为占位或候选过程输出。Validate 只展示验证结果、错误态、降级说明、来源命令和修复线索，不得自动修复、自动关闭任务或自动写入验证结论。

## 10. Web 文档、缓存和变更触发

Web docs、组件说明、API 文档和页面文案只能解释当前实现，不得替代 specs、事实模型、行动编排或事实源规则。发现 Web docs 与 specs 冲突时，以 specs 和事实源为准，并触发 Web 文档同步。

Web 缓存只能用于性能和交互体验。缓存失效、重建或页面刷新不得改变事实源。需要长期保留的展示结论、缺口、确认或验证证据，必须回到对应事实源、Git commit records 或行动编排。

缓存与同步状态矩阵由 `attachments/05.Att.08-缓存与同步状态矩阵.md` 承载。Web 能力删除核对表由 `attachments/05.Att.11-Web能力删除核对表.md` 承载。删除 Web 页面、接口或能力前，必须确认依赖、替代入口、测试、文档和 Human Gate 影响；影响受控写入、Confirm UI、Human Gate、事实源同步或关键回归线时，必须暂停并等待 Human 确认。

以下变化必须触发 Web 同步检查：

1. 事实模型字段、状态、对象目录或写入边界变化；
2. Code DTO、诊断 Schema、知识地图投影或 Git 解析变化；
3. 03 行动编排的 Gate、验证、回写或 WorkCase 展示相关锚点变化；
4. 07 事实源、commit message、关联提交派生或追溯规则变化；
5. 08 Web 测试、API contract 或验证声明要求变化；
6. Web 页面、API、路由、缓存、文案、i18n 或权限边界变化。

Web 回归矩阵由 `attachments/05.Att.09-Web回归矩阵.md` 承载。Web 测试应优先 API contract；高风险 API 优先覆盖 `POST /api/sparks`、ProjectFiles、Validate 和 Objects；页面优先覆盖 Gate、Validate、ProjectFiles 和 ObjectDetail 的空态、错误态、降级态、只读边界和来源呈现。

## 11. 暂不实施期间的回归线

Web v2 暂不实施不等于 Web 契约可以忽略。以下 v1 线索必须在迁移中保持可见：

1. 事实对象 DTO；
2. Spark 创建白名单；
3. WorkCase orchestration 展示字段；
4. Changelog 或提交记录派生视图；
5. 对象详情关联提交展示；
6. Confirm UI 与 Human Gate 的边界；
7. 受控轻写入白名单和禁止写入边界；
8. 派生态势原因语义；
9. Web 测试、构建和 API contract 的回归入口。

这些内容后续是否迁入、改名或废弃，必须通过 05 单篇核对和 08 测试治理确认。

## 12. 与其它规范的边界

| 对象 | Web 消费方式 | 不得越界 |
|---|---|---|
| 02 事实模型 | 读取字段契约、状态、对象关系和受控写入边界 | 不定义 schema 或状态机 |
| 03 行动编排 | 展示行动姿态、Gate、验证、阻塞和待确认事项 | 不决定流程进入、暂停、关闭或回写 |
| 04 Code | 消费 DTO、诊断、知识地图投影和 Git 解析结果 | 不维护第二套解析规则 |
| 06 运行时扩展 | 展示入口、能力缺口或适配提示 | 不定义 Rules/Skill/Agent/Hook 资产规则 |
| 07 事实源/Git | 展示事实源、证据和提交记录派生视图 | 不把页面状态写成事实源 |
| 08 测试 | 提供 Web 测试入口和验收展示需求 | 不定义测试治理标准 |

## 13. 附件规则

本文授权以下附件承载可枚举、可复用或可被 Code/Web 消费的细表；附件不得替代本文、上位规范、实现域文档或测试实现。

| 附件 | 承载内容 | 不承载 |
|---|---|---|
| `attachments/05.Att.01-DTO与API契约表.md` | Web DTO 与 API 契约 | 事实模型字段本体、Code 输出 Schema |
| `attachments/05.Att.02-页面与API映射矩阵.md` | 页面、API 与来源关系 | 页面实现代码 |
| `attachments/05.Att.03-轻写入白名单表.md` | 受控轻写入白名单和禁止接口 | 新写入能力授权 |
| `attachments/05.Att.04-Confirm-UI字段表.md` | Confirm UI 最小展示和记录字段 | Human Gate 本体 |
| `attachments/05.Att.05-Gate与Validate阶段边界矩阵.md` | Gate/Validate 阶段边界 | 自动修复或回写流程 |
| `attachments/05.Att.06-Human-facing态势语义表.md` | Human-facing 派生态势原因语义 | 事实源状态机 |
| `attachments/05.Att.07-提交记录展示矩阵.md` | Changelog 和对象详情提交展示 | Git commit 规范本体 |
| `attachments/05.Att.08-缓存与同步状态矩阵.md` | 缓存、同步、降级和冲突展示状态 | 稳定事实源 |
| `attachments/05.Att.09-Web回归矩阵.md` | Web API、页面、Confirm UI 和轻写入回归优先级 | 测试治理本体 |
| `attachments/05.Att.10-Web差距审计模板.md` | Web AI 只读差距审计模板 | 执行授权 |
| `attachments/05.Att.11-Web能力删除核对表.md` | Web 页面、API 或能力删除前核对项 | 删除授权本体 |

新增、删除、重命名或改变以上附件的信息对象时，应回到本文 Human Gate，并同步 01 当前目录登记、README 写作区入口和 Code v2 解析。

## 14. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Web 应承接 00、01、07、v1 历史 `11` 和 Human 确认后的 v2 08 测试治理，不反向定义事实模型、Code 或测试规则 | 本文、00、01、07、v1 历史 `11`、v2 08、Human Gate | Web 治理 | Web 展示、DTO、写入边界或事实源回指变化时 |
| 入口可见要求 | Human 或 AI 需要查看状态、风险、证据、提交记录或待确认事项时应能定位 Web 入口或降级视图 | Web 导航、Code 输出、Rules 入口、人工降级检查 | Human-facing 入口 | Web 路由、导航、页面职责或展示入口变化时 |
| 轻写入白名单要求 | Web 写入必须限定在规范授权白名单内，并具备写后验证、错误反馈和事实源追溯 | Web API、Code DTO、事实模型、07、测试 | 受控轻写入 | Web 写入入口、字段、API 或权限变化时 |
| 确定性执行要求 | Web 消费 DTO、API contract、页面状态和写入白名单应有 Code 或测试校验 | Code DTO、Web 测试、API contract、人工降级检查 | 校验实现 | DTO、API、页面、白名单或 Confirm UI 变化时 |
| 知识地图展示要求 | Web 展示知识地图时必须显示来源回指、诊断、排除输入和降级状态，不得补写关系 | 04 知识地图投影、01.Att.01、Web 回归、人工降级检查 | 派生展示 | 知识地图视图、过滤、布局、DTO 或诊断展示变化时 |
| Human 交互要求 | 改变受控写入、Confirm UI、Human Gate 展示或高影响操作入口前应评估 Human Gate | Human Gate、影响范围说明、确认记录 | Human Gate | Web 写入、确认、验收或权限边界变化时 |
| 流程复用要求 | Web AI 或并行 AI 承接 Web 工作前，必须先完成只读差距审计，不得直接扩大白名单、写入事实源或声明完整支持 | `05.Att.10`、人工降级检查、后续行动编排 | Web 协作 | Web 实现、页面/API 重写、白名单变更或差距审计结论变化时 |
| 生命周期触发要求 | 事实模型、行动编排、Code、事实源、测试或运行时入口变化后，应检查 Web 展示和交互是否同步 | Web 回归、Code DTO 检查、测试、人工降级检查 | 生命周期同步 | 上游契约变化影响 Human-facing 展示或交互时 |

## 15. Human Gate

以下情况必须暂停并等待 Human 确认：

1. 新增、删除或扩大 Web 受控写入能力；
2. 改变 Confirm UI、Human Gate 展示、确认范围或确认记录回写；
3. 把 Web 页面状态、缓存、筛选或 DTO 当作稳定事实源；
4. 改变 Spark 创建白名单、对象状态流转入口或高影响操作入口；
5. 删除关键 Web 回归线且没有替代验证；
6. 声明 Web v2 已实施或完整支持某能力。
7. 改变 `05.Att.01` 至 `05.Att.11` 的信息对象、授权范围或关键闭集。
8. 删除 Web 页面、API、能力或回归入口，且影响 Human Gate、受控写入、事实源同步、关键页面或行动编排依赖。

## 16. Web 检查要求

Web 检查至少包括：

| 检查项 | 标准 |
|---|---|
| 来源回指 | 展示数据能回指事实源、Code 输出或 Git commit |
| 写入边界 | 只允许白名单内受控轻写入 |
| Human Gate | 高影响交互有确认范围和事实源回写位置 |
| DTO 稳定 | DTO 与 02、04、07 保持一致 |
| 知识地图展示 | 节点、边、诊断、排除输入和降级状态来自 04 投影且可回指 |
| 原因语义 | Human-facing 态势能说明来源事实和归因原因 |
| 提交展示 | 提交记录来自 Git history 或 Code 派生 DTO |
| 测试回归 | 关键页面、API contract 和写入边界有验证或降级说明 |
| Web 差距审计 | Web AI 承接前已按 05.Att.10 列出事实源来源、派生状态、Human Gate、写入白名单、测试归属、错误态和 Human 决策项 |

## 17. 待补齐事项

1. 本文和 `05.Att.01` 至 `05.Att.11` 已承接 v1 `08` 主体规则，仍需 Human 单篇核对后才能视为迁移完成；
2. `05.03` 的 Web 语义化渲染规则、`10` 的提交展示细节、`20/21` 的 Spark/WorkCase Web 线索已进入 05 附件基线，后续需要随 02 字段注册、07 Git 追溯和成员主文件继续核对；
3. Web v2 暂不实施期间，本文只保留契约和回归线，不声明 Web v2 已实施或完整支持；
4. 后续 Code 可增强对 `05.Att.01` 至 `05.Att.11` 的结构检查、关系回指和 Web 回归入口诊断。
