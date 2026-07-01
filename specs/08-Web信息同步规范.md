# Web信息同步规范

```yaml
ldvh_spec:
  spec_id: "08"
  spec_kind: "spec"
  title: "Web信息同步规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/08-Web信息同步规范.md"
  parent_spec: "specs/00-理念与构成.md"
  relation: "refines"
  positioning: "定义 Web 的 Human-facing 展示、同源独立读取、派生状态、受控交互和不得成为事实源的 V3 基础规则"
  scope: "Web 展示、Human-facing 状态、风险、证据、待确认事项、Confirm UI、Web 缓存、受控轻写入、Web API 边界和 Web 回归线"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
  related_specs:
    - "specs/05-事实模型基础规范.md"
    - "specs/06-行动模板基础规范.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/09-测试与验证规范.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "web_sync_boundaries"
    - "web_code_separation_boundaries"
    - "human_facing_display_rules"
    - "source_ref_display_requirements"
    - "controlled_interaction_boundaries"
    - "web_cache_boundaries"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. Human-facing 展示边界"
      - "6. 同源独立读取与派生状态"
      - "7. 受控交互与 Confirm UI"
    assurance_measures: "8. 保障措施"
    verification_method: "9. 验证方法"
    human_gate: "10. Human Gate"
    stop_conditions: "11. Stop Conditions"
    next_queries: "12. 待补齐事项"
```

> 文件状态：active；本文吸收 V2 Web 父层规则。阶段 9D 已迁入 Web API 数据契约、同源独立读取、来源回指、缓存边界和基础回归测试；本文不把具体页面设计、缓存实现细节、DTO 长表或视觉回归矩阵写成规则正文。

## 1. 价值判断

本文存在的价值，是让 Human 能看见 AI 行动所依据的状态、风险、证据、验证结果和待确认事项，从而提高 Human 确认质量。

Web 的直接服务对象是 Human，但它仍服务 00 的 AI 第一目标：Web 通过让 Human 更好地确认、纠偏和验收，反过来给 AI 提供更清晰、可消费、可溯源的确认结果。

## 2. 权威依据

本文承接 `specs/00-理念与构成.md` 的 Web 构成要素定位、`specs/01-保障与衔接.md` 的证据和 Human Gate 呈现边界、`specs/02-AI行为规范.md` 的面向 Human 输出责任、`specs/03-事实源与Git溯源规范.md` 的非事实源边界，以及 `specs/04-Specs基础规范.md` 的结构规则。

Web 展示若与 Git 文件事实源、Code 诊断或 specs 正文冲突，应回到事实源和正文判断；Code 诊断只能作为发现冲突的证据，不覆盖事实源或正文。

## 3. 归口边界

本文归口定义 Web 的 Human-facing 展示、同源独立读取、派生状态、受控交互、缓存边界和 Confirm UI 基础规则。

本文不归口定义事实对象字段、Code DTO schema、行动模板 Gate、测试治理、Git commit 契约、Code 到 Web 的页面数据通道或具体页面实现。这些内容分别由 05、07、06、09、03、07/08 边界和 Web 实现域承接。

本文只定义 Web 的展示契约、来源回指、同源独立读取、受控交互、缓存和写入边界，不定义具体页面、组件、API 路由、状态管理、样式系统、构建工具或性能实践。Web 实践由 `web/` 和 `web/docs/` 承接；这些实现域材料可以说明页面结构、API 聚合、设计系统、缓存策略和测试映射，但不得反向改写 specs、事实源、Human Gate、Code 契约或测试治理。

## 4. 适用范围

本文适用于：

1. Web 页面、API、缓存和展示状态的规则边界；
2. Human-facing 风险、证据、诊断、待确认事项和验证状态展示；
3. Confirm UI、受控轻写入和确认结果回写；
4. V2 `05-Web信息同步规范.md` 与 `05.Att.*` 的迁移判断。

## 5. Human-facing 展示边界

Web 可以展示：

1. 事实对象状态、风险、证据和关系；
2. specs、事实源、Code 诊断和测试结果的来源回指；
3. 待确认事项、Human Gate 触发原因、影响范围和选项；
4. Git 提交记录、变更影响和验证状态；
5. Action Guide、preflight 或 runtime facade 暴露的缺口和不可验证范围。

Web 不得展示成：

1. 页面状态就是事实源状态；
2. 按钮点击就是 Human Gate 完成；
3. Code 或测试通过就是 Human 授权；
4. 缓存、筛选、颜色、标签或排序就是稳定事实；
5. Web 路由就是新的对象类型或规则入口。

## 6. 同源独立读取与派生状态

Web 和 Code 是同源的并列实现，不是上下游数据依赖。Web 页面/API 的数据路径必须由 Web 自行从 Git 文件事实源、正式 specs、正式事实对象或 Web 自有 API 聚合读取；不得把 Code 输出、Code DTO、validator 内部对象、preflight/action-guide/runtime receipt 作为页面数据源或长期缓存基础。

Web 可以在测试、审计、调试或不可验证提示中引用 Code 诊断、验证摘要或 source_refs，只能用于对照显示和缺口定位；该引用不得驱动页面字段契约、状态机、排序筛选语义或事实判断。

Web 原生实现可以读取、解析、筛选、排序、聚合、缓存和提供 API；这些实现必须使用正式 specs、正式附件和事实对象中的字段与状态契约，保留 source_refs，不得新增第二套字段契约、状态机、规则判断或事实源归口。

Web 派生状态必须满足：

1. 事实展示能回指事实源路径、对象 ID、章节或 commit hash；诊断和验证展示能回指对应 Code/test 入口；
2. 明确区分事实源状态、派生态势、诊断状态和 UI 交互状态；
3. 冲突时回到事实源和 specs 正文，不以页面显示、Code 诊断或测试输出覆盖；
4. 缓存只服务性能和交互，不形成长期事实；
5. 刷新、重新查询或事实源变化后，应重新获取可溯源来源。

Web 尚未实施的具体能力只能作为迁移回归线保留；已经实施的 Web API、页面或轻写入能力必须按本文保留来源回指、独立读取边界和对应测试，不得因页面可见而声称 Human Gate 已完成。

## 7. 受控交互与 Confirm UI

Web 默认只读。任何写入、确认、取消、暂缓、状态改变或验收操作，都必须满足来源规则、事实源回写、验证和 Human Gate 边界。

Confirm UI 应至少让 Human 看见：

1. 确认对象；
2. 影响范围；
3. 事实源和证据；
4. 验证状态和未验证范围；
5. 风险和替代选项；
6. 确认后写入位置；
7. 失败、取消、暂缓和残留风险。

Web 受控轻写入只有在对应事实模型、事实源、Web API、测试和 Human Gate 边界明确后才能开启。V3 当前只迁入 Spark quick create 这一最小轻写入：它只能创建 `pending` Spark 事实实例，必须写回 Git 可追踪文件并通过回读验证，响应必须包含 `source_refs`，不得写入 legacy 字段，不得替代 Git 提交、Human Gate 或完成声明。新增或扩大任何 Web 写入能力仍需按本文进入 Human Gate。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源呈现要求 | Web 展示的状态、风险和证据必须可回指来源 | source_refs、事实源路径、Web API contract | 展示治理 | 新增页面、API 或诊断展示时 |
| Web/Code 分离要求 | Web 页面/API 数据路径不得依赖 Code 输出、Code DTO 或 validator 内部对象 | 本文、07、tests | 架构治理 | 新增页面数据源、API 聚合或缓存策略时 |
| 非事实源要求 | Web 状态、缓存和筛选不得成为事实源 | 本文、03、09 | 事实源治理 | 使用缓存、派生态势或页面状态时 |
| Confirm UI 要求 | Human 交互必须呈现对象、影响、证据、风险和回写位置 | 本文、01、06、09 | Human Gate 治理 | 展示确认、验收或风险接受时 |
| 受控写入要求 | Web 写入必须有规范授权、验证和 Git 溯源 | 05、07、09、03 | 写入治理 | 新增或扩大 Web 写入能力时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 来源检查 | 展示内容是否能回指事实源或 Code/test 证据 | 标为不可验证或隐藏派生结论 |
| 分离检查 | Web 页面/API 是否没有把 Code 输出、Code DTO 或 validator 内部对象作为主数据源 | 停止作为 Web 数据契约，改回 Web 同源独立读取或只作为诊断对照 |
| 边界检查 | Web 状态是否没有替代事实源、Human Gate 或完成结论 | 停止展示为稳定事实 |
| 交互检查 | Confirm UI 是否呈现影响、证据、风险和回写位置 | 不得启用确认或写入 |
| 回归检查 | Web 契约变化是否有 API、页面或等价验证 | 写入 09、Web tests 或 Web 待补齐事项 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 新增、扩大或删除 Web 写入能力；
2. 改变 Confirm UI 的确认对象、影响范围、证据或回写边界；
3. 接受 Web 无法展示关键风险、证据或未验证范围；
4. 将 Web 状态、缓存、筛选或按钮点击升级为事实源或 Human Gate 完成；
5. 让 Web 页面/API 改为依赖 Code 输出、Code DTO 或 validator 内部对象作为主数据源；
6. 删除高价值 Web 回归线且无替代验证。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. Web 展示无法回指来源；
2. Web 状态正在覆盖事实源、Code 诊断或 specs 正文；
3. Confirm UI 被当作 Human Gate 自动完成；
4. Web 写入缺少事实源、验证或 Git 溯源；
5. Web 页面/API 依赖 Code 输出、Code DTO 或 validator 内部对象作为主数据源；
6. Web 暂未实现、未测试或未接入的能力被描述为保障已生效。

## 12. 待补齐事项

1. 后续继续判断 V2 `05.Att.*` 中 DTO 长表、Confirm UI 细则和视觉回归矩阵是否进入 Web 实现域或 tests；
2. 后续定义 Web 只读差距审计模板是否迁入 V3 附件；
3. 后续补齐 Confirm UI 端到端验证、页面视觉回归和真实 Human Gate 展示验证；
4. 后续 Code 可继续提供 diagnostics、source_refs 和 verification summary 供测试、审计或诊断对照，不作为 Web 页面/API 数据源。
