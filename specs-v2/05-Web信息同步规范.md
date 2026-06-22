# Web信息同步规范

```yaml
v2_spec:
  spec_id: "05"
  spec_kind: "spec"
  title: "Web信息同步规范"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/05-Web信息同步规范.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: ""
  relation: ""
  positioning: "定义 v2 Web 的 Human-facing 派生展示、状态可见、风险可见、证据可见、受控轻写入和信息同步边界"
  scope: "LDVH Web、Human-facing 派生视图、事实对象 DTO、提交记录展示、知识地图展示、受控轻写入白名单、Confirm UI 和 Web 与 Code/事实源/测试的消费边界"
  basis:
    - "specs-v2/00-LDVH理念与价值标准.md"
    - "specs-v2/01-规范体系基础规范.md"
    - "specs-v2/07-事实源边界与Git追溯规范.md"
  related_specs:
    - "specs-v2/02-事实模型基础规范.md"
    - "specs-v2/03-行动编排规范.md"
    - "specs-v2/04-Code确定性执行规范.md"
    - "specs-v2/06-运行时扩展规范.md"
    - "specs-v2/08-测试基础规范.md"
  migration_sources:
    - "specs/08-Web信息同步实现规范.md"
  active_fact_source:
    - "specs/08-Web信息同步实现规范.md"
  code_consumption:
    - "v2_spec_metadata"
    - "v2_relations"
    - "web_contracts"
    - "dto_boundaries"
    - "human_visible_states"
    - "knowledge_map_display"
    - "controlled_light_write_boundaries"
    - "assurance_requirements"
  migration_status: "not_migrated"
```

> 文件状态：本文当前位于 `specs-v2/`，尚未切换为 active；正式 Web 规则仍以 active `specs/08-Web信息同步实现规范.md` 和当前 Web 实现为准。
>
> Web v2 当前暂不实施。本文只建立框架、边界和回归线；未经 Human 单篇确认前，不得作为 active 规范、Code 默认消费依据、Rules 入口依据或迁移完成结论。

## 1. 本文解决的问题

本文定义 LDVH Web 如何帮助 Human 看见状态、风险、证据和待确认事项，同时不成为第二事实源。

本文解决：

1. Web 如何消费 Code DTO、事实模型、Git 提交记录和知识地图投影；
2. Web 如何展示 Human-facing 状态、风险、证据、关联提交和待确认事项；
3. Web 何时可以提供受控轻写入，何时必须只读展示；
4. Web 页面状态、缓存、筛选和派生视图为什么不能替代 Git 文件事实源；
5. Web 暂不实施时，哪些 v1 契约仍必须作为迁移回归线保留。

本文不定义事实模型字段、Code 输出 Schema、Git 提交契约、测试治理或运行时扩展入口。

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
2. 关系边类型来自 `01.Att.01-知识地图关系类型表.md`；
3. `diagnostics`、`excluded_inputs` 和 `degraded` 状态必须对 Human 可见；
4. 图布局、筛选、折叠、颜色和交互状态不成为稳定事实；
5. Web 不得补写 Code 未输出的节点、关系边或来源回指；
6. Web 必须呈现本次查询的 `input_scope`、`project_scope`、生成时间、降级原因和项目命名空间；
7. 跨项目关系必须显示来源项目和目标项目，不得把不同项目中的同名对象 ID 合并展示为同一节点。

Web 展示知识地图必须使用无缓存语义。API 响应应使用 `Cache-Control: no-store` 或等价措施；前端不得使用 localStorage、sessionStorage、IndexedDB、Service Worker cache 或等价浏览器持久化机制保存图谱节点、关系边、诊断结果、项目范围或展开状态。页面可以在内存中保留当前交互态，但刷新、重新查询或事实源变化后必须重新向 Code/API 获取只读投影。

## 6. 受控轻写入白名单

Web 默认只读。Web 只有在规范明确授权、事实模型字段边界清晰、API contract 可测试、失败可回滚且 Git 追溯路径明确时，才能提供受控轻写入。

v1 迁移期间必须保留的轻写入白名单只有 Spark quick create：

| 写入入口 | 允许字段 | 固定写入 | 禁止写入 |
|---|---|---|---|
| `POST /api/sparks` | `title`、`description`、`priority` | `status: pending`、`source: web` | `status_history`、关闭状态、验收字段、长期证据字段、非 Spark 对象字段 |

Spark quick create 必须写后读取并验证事实源结果。写入失败、字段不合法、路径冲突、Human Gate 缺失或事实源不可追溯时，Web 必须返回错误，不得静默缓存为“已创建”。

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

## 8. 提交记录与关联提交展示

Web 可以展示 Git commit records、Changelog、关联提交和对象详情中的提交追溯信息。提交记录展示必须来自 Git history、Code commit DTO 或 07 授权的派生规则。

Web 不得：

1. 创建 `ldvh-base/changes/` 或等价手写 change 对象；
2. 让用户手写 `related_changes` 或 `related_commits` 作为对象事实；
3. 用页面上的关联提交覆盖 Git history 和 Code 派生结果；
4. 把提交记录描述为工作对象生命周期状态。

Changelog、Dashboard、ProjectFiles 和对象详情若展示同一提交信息，应共享同一 Code DTO 或同一派生规则，不得维护多套解析逻辑。

## 9. Confirm UI、Gate 与验证展示

Confirm UI 是 Human-facing 交互入口，不等于 Human Gate 已完成。Web 展示确认、授权、验收或关闭动作时，必须呈现：

1. 确认对象；
2. 影响范围；
3. 关联事实源；
4. 证据或验证状态；
5. 确认后的回写位置；
6. 取消、失败或降级后的状态。

Web 可以展示 Gate、Validate、待确认事项和验证结果，但不得用按钮点击替代行动编排 Gate、测试验证声明、事实源回写或 Human 的高影响判断。

## 10. Web 文档、缓存和变更触发

Web docs、组件说明、API 文档和页面文案只能解释当前实现，不得替代 specs、事实模型、行动编排或事实源规则。发现 Web docs 与 specs 冲突时，以 specs 和事实源为准，并触发 Web 文档同步。

Web 缓存只能用于性能和交互体验。缓存失效、重建或页面刷新不得改变事实源。需要长期保留的展示结论、缺口、确认或验证证据，必须回到对应事实源、Git commit records 或行动编排。

以下变化必须触发 Web 同步检查：

1. 事实模型字段、状态、对象目录或写入边界变化；
2. Code DTO、诊断 Schema、知识地图投影或 Git 解析变化；
3. 03 行动编排的 Gate、验证、回写或 WorkCase 展示相关锚点变化；
4. 07 事实源、commit message、关联提交派生或追溯规则变化；
5. 08 Web 测试、API contract 或验证声明要求变化；
6. Web 页面、API、路由、缓存、文案、i18n 或权限边界变化。

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

## 13. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Web 应承接 00、01、active 08 和 07 的事实源边界，不反向定义事实模型、Code 或测试规则 | 本文、00、01、07、active 08、Human Gate | Web 治理 | Web 展示、DTO、写入边界或事实源回指变化时 |
| 入口可见要求 | Human 或 AI 需要查看状态、风险、证据、提交记录或待确认事项时应能定位 Web 入口或降级视图 | Web 导航、Code 输出、Rules 入口、人工降级检查 | Human-facing 入口 | Web 路由、导航、页面职责或展示入口变化时 |
| 轻写入白名单要求 | Web 写入必须限定在规范授权白名单内，并具备写后验证、错误反馈和事实源追溯 | Web API、Code DTO、事实模型、07、测试 | 受控轻写入 | Web 写入入口、字段、API 或权限变化时 |
| 确定性执行要求 | Web 消费 DTO、API contract、页面状态和写入白名单应有 Code 或测试校验 | Code DTO、Web 测试、API contract、人工降级检查 | 校验实现 | DTO、API、页面、白名单或 Confirm UI 变化时 |
| 知识地图展示要求 | Web 展示知识地图时必须显示来源回指、诊断、排除输入和降级状态，不得补写关系 | 04 知识地图投影、01.Att.01、Web 回归、人工降级检查 | 派生展示 | 知识地图视图、过滤、布局、DTO 或诊断展示变化时 |
| Human 交互要求 | 改变受控写入、Confirm UI、Human Gate 展示或高影响操作入口前应评估 Human Gate | Human Gate、影响范围说明、确认记录 | Human Gate | Web 写入、确认、验收或权限边界变化时 |
| 生命周期触发要求 | 事实模型、行动编排、Code、事实源、测试或运行时入口变化后，应检查 Web 展示和交互是否同步 | Web 回归、Code DTO 检查、测试、人工降级检查 | 生命周期同步 | 上游契约变化影响 Human-facing 展示或交互时 |

## 14. Human Gate

以下情况必须暂停并等待 Human 确认：

1. 新增、删除或扩大 Web 受控写入能力；
2. 改变 Confirm UI、Human Gate 展示、确认范围或确认记录回写；
3. 把 Web 页面状态、缓存、筛选或 DTO 当作稳定事实源；
4. 改变 Spark 创建白名单、对象状态流转入口或高影响操作入口；
5. 删除关键 Web 回归线且没有替代验证；
6. 声明 Web v2 已实施或完整支持某能力。

## 15. Web 检查要求

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

## 16. 待补齐事项

1. 逐条核对 v1 `08`，确认 Web 信息同步、受控轻写入、DTO 和 Human-facing 展示如何迁入本文；
2. 盘点当前 `web/` 与 `web/docs` 的事实对象 DTO、Spark 创建白名单、WorkCase 展示和提交记录页面；
3. 确认 Web v2 暂不实施期间的替代展示和人工降级检查方式；
4. 与 04 对齐 DTO、知识地图投影和提交记录派生输入；
5. 与 08 对齐 Web API contract、页面测试和构建验证入口；
6. 与 07 对齐 Web 展示事实源、证据和 Git 追溯的回指边界；
7. 后续拆出 `05.Att.01-Web DTO与API契约`、`05.Att.02-Web轻写入白名单`、`05.Att.03-Web页面与API映射` 和 `05.Att.04-Web回归矩阵`。
