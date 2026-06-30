# Code确定性执行规范

```yaml
ldvh_spec:
  spec_id: "07"
  spec_kind: "spec"
  title: "Code确定性执行规范"
  status: "candidate"
  authority: "candidate"
  canonical_path: "specs/07-Code确定性执行规范.md"
  parent_spec: "specs/00-理念与构成.md"
  relation: "refines"
  positioning: "定义 Code 的读取、解析、校验、诊断、Action Guide、preflight、runtime facade 和环境适配实现边界"
  scope: "Code 解析、结构校验、诊断、source_refs、Action Guide、preflight、runtime facade、payload/adapter/dispatcher/validator 边界和 Code 变更纪律"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
  related_specs:
    - "specs/05-事实模型基础规范.md"
    - "specs/06-行动模板基础规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "code_determinism_rules"
    - "diagnostic_boundaries"
    - "action_guide_contracts"
    - "preflight_contracts"
    - "runtime_facade_contracts"
    - "adapter_dispatcher_boundaries"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. Code 能力边界"
      - "6. 结构化输出与诊断"
      - "7. Runtime facade 与环境适配实现边界"
      - "8. Code 变更纪律"
    assurance_measures: "9. 保障措施"
    verification_method: "10. 验证方法"
    human_gate: "11. Human Gate"
    stop_conditions: "12. Stop Conditions"
    next_queries: "13. 待补齐事项"
```

> 文件状态：candidate；本文吸收 V2 Code 父层规则和 V2 runtime 中具体实现边界。本文不授权 Hook 安装、环境接入、Web API 或 Human Gate 放行。

## 1. 价值判断

本文存在的价值，是让 Code 承担确定性读取、解析、校验、聚合、诊断和行动前检查，减少 AI 盲读、误判、漏验证和凭记忆执行的负担。

Code 服务 00 的 Code 构成要素定位和 V6 强制验证。Code 可以提供证据和诊断，但不替代 AI 判断、Human Gate、事实源或完成结论。

## 2. 权威依据

本文承接 `specs/00-理念与构成.md` 的 Code 定位、`specs/01-保障与衔接.md` 的保障消费语义、`specs/02-AI行为规范.md` 的主控责任、`specs/03-事实源与Git溯源规范.md` 的事实源边界，以及 `specs/04-Specs基础规范.md` 的 Markdown 结构规则。

若 Code 输出与 specs 正文冲突，以 specs 正文和 Human Gate 为准。Code 发现规则缺口时只能输出 diagnostic 并回到对应规范，不得自行补写规则。

## 3. 归口边界

本文归口定义 Code 的确定性执行边界：读取、解析、校验、诊断、source_refs、Action Guide、preflight、runtime facade、payload/adapter/dispatcher/validator 规则和 Code 变更纪律。

本文不归口定义事实对象字段、行动模板步骤、Web 页面、测试治理、Git commit 契约本体、环境安装方式或 Hook registry。相邻内容分别由 05、06、08、09、03 和 01/06 承接。

## 4. 适用范围

本文适用于：

1. `code/` 下的正式解析、校验、CLI 和 runtime facade；
2. Code 生成的 Action Guide、preflight、receipt、diagnostic、source_refs 和 read_plan；
3. 由 V2 `04` 和 V2 `06` 迁入的 dispatcher、adapter、payload 和 validator 设计；
4. 测试中对 Code 行为的正反例和验证命令。

## 5. Code 能力边界

Code 可以提供以下能力：

| 能力 | 作用 | 边界 |
|---|---|---|
| 读取 | 读取 Git 文件事实源、specs、附件、配置和测试输入 | 不修改事实源 |
| 解析 | 提取 identity block、章节、表格、引用和路径 | 不推断未声明规则 |
| 校验 | 检查结构、闭集、引用、路径、必读项和证据 | 不替代 Human Gate |
| 聚合 | 生成对象集合、read_plan、source_refs 和影响摘要 | 不成为集合事实源 |
| 诊断 | 输出 blocking、warning、follow_up、unverifiable 或 error | 不直接授权、放行或关闭 |
| preflight | 写入或提交前暴露目标、读取、Gate 和验证风险 | 不回答“是否应该写入” |
| runtime facade | 按 canonical event 消费保障需求并输出 stdout-only receipt | 不证明环境已接入 |

Code 输出必须声明 authority、authorization 和来源边界。当前未接入环境时，必须保持 `environment_integrated=false` 或等价缺口说明。

## 6. 结构化输出与诊断

Code 输出应能被 AI 和 tests 稳定消费，至少包含状态、来源、诊断和边界。

诊断必须区分：

| 类型 | 含义 |
|---|---|
| `blocking` 或 `error` | 阻断当前行动、验证、写入或完成声明 |
| `warning` | 不阻断但影响风险、证据或同步 |
| `follow_up` | 后续补齐，不阻断当前行动 |
| `unverifiable` | 当前无法验证或证据不足 |

Code 不得输出 `approved`、`allowed`、`accepted risk`、`human_gate_passed` 等授权语义。无诊断时可以输出 `diagnostic_clear`，但不得把它解释为授权。

## 7. Runtime facade 与环境适配实现边界

01 已定义 Runtime Protocol、canonical event 和 trigger source 的上位语义。本文只承接具体实现边界。

V3 当前 runtime facade 的边界：

1. 可以消费 `01.Att.01` 的消费时机闭集；
2. 可以生成 Action Guide、preflight、stdout-only receipt 和 diagnostics；
3. 可以检查 acknowledged read_plan 和 completion evidence；
4. 不写持久 receipt；
5. 不安装 Hook、Rules、插件或环境入口；
6. 不声明当前环境完整支持 LDVH；
7. 不替代 AI 判断、Human Gate 或事实源回写。

V2 `06` 中的 payload schema、dispatcher、adapter、payload_present、unknown event 和环境 fallback 可作为本文后续实现来源。涉及写入用户环境、安装 Hook、覆盖入口或扩大权限时，必须先进入 Human Gate 和 09 测试设计。

## 8. Code 变更纪律

新增或改变 Code 行为前，必须先确认：

1. 规则来源能回指正式 specs、事实对象、行动模板、测试要求或 Human 决策；
2. 正例、反例、失败条件和诊断分流可描述；
3. 输出不会反向定义 specs、事实源、Human Gate 或 Web/测试规则；
4. 有自动化测试、命令校验或等价验证；
5. 无法验证时必须说明原因、范围和后续补齐位置。

Code 暴露规范缺口时，应输出 diagnostic 并回到对应规范或 `_migration` 承接，不得在实现中硬编码未确认候选规则。

## 9. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源回指要求 | Code 行为必须回指正式规则或事实源 | source_refs、identity parser、tests | Code 治理 | 新增 parser、validator、CLI 或 facade 行为时 |
| 授权边界要求 | Code 输出不得表达授权、放行或风险接受 | 本文、02、04、tests | 语义治理 | 输出 status、diagnostic 或 receipt 时 |
| 诊断分流要求 | 失败、缺口和不可验证必须结构化输出 | diagnostic、preflight、runtime | 缺口治理 | Code 无法完成确定性判断时 |
| 测试前置要求 | Code 行为变化必须有测试或等价验证 | 09、tests/code、CLI | 验证治理 | 修改 `code/` 或 Code 消费 specs 时 |

## 10. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 结构检查 | Code 是否从 Markdown specs 和附件读取稳定结构 | 回到 04 或 parser 缺口 |
| 诊断检查 | 输出是否区分阻断、警告、后续和不可验证 | 修正诊断或 tests |
| 授权边界检查 | 输出是否避免授权、Human Gate 替代和事实源替代语义 | 阻断完成声明 |
| runtime 检查 | facade 是否保持只读、stdout-only、environment_integrated=false | 记录环境接入缺口 |
| 回归检查 | `tests/code` 和 specs validator 是否覆盖关键正反例 | 补测试或写明等价验证 |

## 11. Human Gate

以下情况必须进入 Human Gate：

1. Code 输出被设计为授权、放行、验收或风险接受；
2. Code 准备写入事实源、安装 Hook、修改用户环境或覆盖入口；
3. 接受关键 Code 校验长期不可验证；
4. 让 Code 规则覆盖 specs 正文、事实源或 Human Gate；
5. 引入新的持久派生索引、缓存或数据库作为事实判断来源。

## 12. Stop Conditions

出现以下情况时，AI 必须暂停：

1. Code 行为没有正式规则来源；
2. Code 输出正在替代事实源、Human Gate 或完成声明；
3. parser、validator 或 facade 失败但被忽略；
4. unknown event、空 read_plan、缺失 evidence 或 target unknown 未被阻断或分流；
5. 代码变更无法验证且没有等价验证说明。

## 13. 待补齐事项

1. 后续从 V2 `04.Att.*` 筛选可迁入的 Code 命令入口、诊断码和输出 schema；
2. 后续从 V2 `06` 筛选 payload、adapter、dispatcher 和 hook mapping 的最小实现契约；
3. 后续承接 commit validator 到 V3 `03/07/09` 闭环；
4. 后续扩展 specs validator 对 03/05/06/07/08/09 的专属检查。
