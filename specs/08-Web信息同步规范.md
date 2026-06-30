# Web信息同步规范

```yaml
ldvh_spec:
  spec_id: "08"
  spec_kind: "spec"
  title: "Web信息同步规范"
  status: "candidate"
  authority: "candidate"
  canonical_path: "specs/08-Web信息同步规范.md"
  parent_spec: "specs/00-理念与构成.md"
  relation: "refines"
  positioning: "定义 Web 的 Human-facing 展示、同源读取、派生状态、受控交互和不得成为事实源的 V3 基础规则"
  scope: "Web 展示、Human-facing 状态、风险、证据、待确认事项、Confirm UI、Web 缓存、受控轻写入、DTO/API 边界和 Web 回归线"
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
      - "6. 同源读取与派生状态"
      - "7. 受控交互与 Confirm UI"
    assurance_measures: "8. 保障措施"
    verification_method: "9. 验证方法"
    human_gate: "10. Human Gate"
    stop_conditions: "11. Stop Conditions"
    next_queries: "12. 待补齐事项"
```

> 文件状态：candidate；本文吸收 V2 Web 父层规则。本文不迁移具体页面、API、缓存实现、DTO 长表或视觉回归矩阵。

## 1. 价值判断

本文存在的价值，是让 Human 能看见 AI 行动所依据的状态、风险、证据、验证结果和待确认事项，从而提高 Human 确认质量。

Web 的直接服务对象是 Human，但它仍服务 00 的 AI 第一目标：Web 通过让 Human 更好地确认、纠偏和验收，反过来给 AI 提供更清晰、可消费、可溯源的确认结果。

## 2. 权威依据

本文承接 `specs/00-理念与构成.md` 的 Web 构成要素定位、`specs/01-保障与衔接.md` 的证据和 Human Gate 呈现边界、`specs/02-AI行为规范.md` 的面向 Human 输出责任、`specs/03-事实源与Git溯源规范.md` 的非事实源边界，以及 `specs/04-Specs基础规范.md` 的结构规则。

Web 展示若与 Git 文件事实源、Code 诊断或 specs 正文冲突，应回到事实源和正文判断。

## 3. 归口边界

本文归口定义 Web 的 Human-facing 展示、同源读取、派生状态、受控交互、缓存边界和 Confirm UI 基础规则。

本文不归口定义事实对象字段、Code DTO schema、行动模板 Gate、测试治理、Git commit 契约或具体页面实现。这些内容分别由 05、07、06、09、03 和 Web 实现域承接。

## 4. 适用范围

本文适用于：

1. Web 页面、API、DTO、缓存和展示状态的规则边界；
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

## 6. 同源读取与派生状态

Web 必须与 AI 和 Code 读取同一事实源。Web 可以使用 Code 输出、Git 查询、API 聚合或直接读取实现展示，但不得维护第二套字段契约、状态机、规则判断或事实源。

Web 派生状态必须满足：

1. 能回指事实源路径、对象 ID、章节、Code 输出、commit hash 或测试入口；
2. 明确区分事实源状态、派生态势、诊断状态和 UI 交互状态；
3. 冲突时回到事实源、Code 诊断和 specs 正文，不以页面显示覆盖；
4. 缓存只服务性能和交互，不形成长期事实；
5. 刷新、重新查询或事实源变化后，应重新获取可溯源来源。

Web 暂不实施时，Web 契约仍可作为迁移回归线保留，但不得声称 Web 保障已经落地。

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

Web 受控轻写入只有在对应事实模型、事实源、Code/API、测试和 Human Gate 边界明确后才能开启。V2 Spark quick create 等具体白名单暂留迁移材料，未迁入前不得作为 V3 已生效能力。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源呈现要求 | Web 展示的状态、风险和证据必须可回指来源 | source_refs、Code DTO、事实源路径 | 展示治理 | 新增页面、API 或诊断展示时 |
| 非事实源要求 | Web 状态、缓存和筛选不得成为事实源 | 本文、03、09 | 事实源治理 | 使用缓存、派生态势或页面状态时 |
| Confirm UI 要求 | Human 交互必须呈现对象、影响、证据、风险和回写位置 | 本文、01、06、09 | Human Gate 治理 | 展示确认、验收或风险接受时 |
| 受控写入要求 | Web 写入必须有规范授权、验证和 Git 溯源 | 05、07、09、03 | 写入治理 | 新增或扩大 Web 写入能力时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 来源检查 | 展示内容是否能回指事实源或 Code/test 证据 | 标为不可验证或隐藏派生结论 |
| 边界检查 | Web 状态是否没有替代事实源、Human Gate 或完成结论 | 停止展示为稳定事实 |
| 交互检查 | Confirm UI 是否呈现影响、证据、风险和回写位置 | 不得启用确认或写入 |
| 回归检查 | Web 契约变化是否有 API、页面或等价验证 | 写入 09 或 Web 待补齐事项 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 新增、扩大或删除 Web 写入能力；
2. 改变 Confirm UI 的确认对象、影响范围、证据或回写边界；
3. 接受 Web 无法展示关键风险、证据或未验证范围；
4. 将 Web 状态、缓存、筛选或按钮点击升级为事实源或 Human Gate 完成；
5. 删除高价值 Web 回归线且无替代验证。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. Web 展示无法回指来源；
2. Web 状态正在覆盖事实源、Code 诊断或 specs 正文；
3. Confirm UI 被当作 Human Gate 自动完成；
4. Web 写入缺少事实源、验证或 Git 溯源；
5. Web 暂未实现却被描述为保障已生效。

## 12. 待补齐事项

1. 后续从 V2 `05.Att.*` 中筛选 DTO/API、Confirm UI 和 Web 回归线；
2. 后续定义 Web 只读差距审计模板是否迁入 V3 附件；
3. 后续 Web 实现启动时，应先按本文和 09 建立 API contract 与来源回指测试；
4. 后续 Code 应提供 Web 可消费的 source_refs、diagnostics 和 verification summary。
