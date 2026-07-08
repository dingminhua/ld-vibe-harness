# Code确定性执行规范

```yaml
ldvh_spec:
  spec_id: "07"
  spec_kind: "spec"
  title: "Code确定性执行规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/07-Code确定性执行规范.md"
  parent_spec: "specs/00-理念与构成.md"
  relation: "refines"
  positioning: "定义 Code 的读取、解析、校验、诊断、Action Guide（行动指南）、preflight、runtime facade 和环境适配实现边界"
  scope: "Code 解析、结构校验、诊断、source_refs、Action Guide（行动指南）、preflight、runtime facade、payload/adapter/dispatcher/validator 边界和 Code 变更纪律"
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
    - "specs/10-安装与配置规范.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "code_determinism_rules"
    - "diagnostic_boundaries"
    - "action_guide_contracts"
    - "preflight_contracts"
    - "governed_project_resolution"
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

> 文件状态：active；本文吸收 V2 Code 父层规则和 V2 runtime 中具体实现边界。本文不授权 Hook 安装、环境接入、Web API 或 Human Gate 放行。

## 1. 价值判断

本文存在的价值，是让 Code 承担确定性读取、解析、校验、聚合、诊断和行动前检查，减少 AI 盲读、误判、漏验证和凭记忆执行的负担。

Code 主要服务 V1、V3、V4、V6、V7 和 V9：它通过解析、索引、校验、聚合、诊断、测试和受控写入前检查帮助 AI 快速定位入口、识别风险和阻断、稳定执行指定检查、形成可回指证据，并暴露能力缺口或体系缺口。Code 可以提供证据和诊断，但不替代 AI 判断、Human Gate、事实源或完成结论。

## 2. 权威依据

本文承接 `specs/00-理念与构成.md` 的 Code 定位、`specs/01-保障与衔接.md` 的保障消费语义、`specs/02-AI行为规范.md` 的主控责任、`specs/03-事实源与Git溯源规范.md` 的事实源边界，以及 `specs/04-Specs基础规范.md` 的 Markdown 结构规则。

若 Code 输出与 specs 正文冲突，以 specs 正文和 Human Gate 为准。Code 发现规则缺口时只能输出 diagnostic 并回到对应规范，不得自行补写规则。

## 3. 归口边界

本文归口定义 Code 的确定性执行边界：读取、解析、校验、诊断、source_refs、Action Guide（行动指南）、preflight、runtime facade、payload/adapter/dispatcher/validator 规则和 Code 变更纪律。

本文不归口定义事实对象字段、行动模板步骤、Web 页面、Web 页面/API 数据路径、测试治理、Git commit 契约本体、环境安装方式或 Hook registry。相邻内容分别由 05、06、08、09、03 和 01/06 承接。

Code 输出可以供 AI、tests、审计或 Web 诊断展示对照使用，但不得成为 Web 页面/API 的主数据源、字段契约或页面状态机。

本文只定义 Code 的能力契约、输入输出、诊断、source_refs、验证和越界条件，不定义具体实现语言、框架、内部模块结构、目录组织或性能实践。Code 实践由 `code/` 和 `code/docs/` 承接；这些实现域材料可以说明当前模块拆分、CLI、runtime facade、测试映射和维护方法，但不得反向改写 specs、事实源、Human Gate、Web 契约或测试治理。

## 4. 适用范围

本文适用于：

1. `code/` 下的正式解析、校验、CLI 和 runtime facade；
2. Code 生成的 Action Guide（行动指南）、preflight、receipt、diagnostic、source_refs 和 read_plan；
3. 由 V2 `04` 和 V2 `06` 迁入的 dispatcher、adapter、payload 和 validator 设计；
4. 测试中对 Code 行为的正反例和验证命令。

## 5. Code 能力边界

Code 可以提供以下能力：

| 能力 | 作用 | 边界 |
|---|---|---|
| 读取 | 读取 Git 文件事实源、specs、附件、配置和测试输入 | 不修改事实源 |
| 解析 | 提取 identity block、章节、表格、引用和路径 | 不推断未声明规则 |
| 校验 | 检查结构、闭集、引用、路径、必读项和证据 | 不替代 Human Gate |
| 聚合 | 生成对象集合、read_plan、source_refs 和影响摘要 | 不成为集合事实源或 Web 页面数据源 |
| 诊断 | 输出 blocking、warning、follow_up、unverifiable 或 error | 不直接授权、放行或关闭 |
| preflight | 写入或提交前暴露目标、读取、Gate 和验证风险 | 不回答“是否应该写入” |
| 管辖项目解析 | 读取 `LDVH-GOVERNED-PROJECTS.yaml`，解析 target-first 项目归属、Git common-dir 和多目标边界 | 不安装 Hook，不把解析结果写成授权、项目索引或事实对象实例 |
| runtime facade | 按 canonical event 消费保障需求并输出 stdout-only receipt | 不证明环境已接入 |

Code 输出必须声明 authority、authorization 和来源边界。当前未接入环境时，必须保持 `environment_integrated=false` 或等价缺口说明。

## 6. 结构化输出与诊断

Code 输出应能被 AI 和 tests 稳定消费，至少包含状态、来源、诊断和边界。Web 可以引用 Code 诊断、source_refs 或验证摘要做对照展示，但 Code 输出不是 Web 页面/API 数据契约。

诊断必须区分：

| 类型 | 含义 |
|---|---|
| `blocking` 或 `error` | 阻断当前行动、验证、写入或完成声明 |
| `warning` | 不阻断但影响风险、证据或同步 |
| `follow_up` | 后续补齐，不阻断当前行动 |
| `unverifiable` | 当前无法验证或证据不足 |

Code 不得输出 `approved`、`allowed`、`accepted risk`、`human_gate_passed` 等授权语义。无诊断时可以输出 `diagnostic_clear`，但不得把它解释为授权。

涉及管辖项目、preflight 或 runtime facade 的 Code 输出不得只给出 `governed=true/false`。Code 必须按 10 输出可消费的管辖解析结果，至少能区分 `governed_single`、`non_governed`、`scope_unknown`、`governed_target_unknown`、`declared_multi_governed` 和 `mixed_scope`，并保留 `target_resolutions`、`source`、`governed_via`、`git_common_dir`、`unknown_reason` 或等价可复核依据。

Code 诊断必须区分“对象归口问题”和“动作条件问题”。`scope_unknown` 不得自动升级为管辖阻断；只有已有管辖范围证据但本次 target 不明时，才可输出 `governed_target_unknown` 对高影响动作 gated。普通管辖对象的 preflight 不得被无关全局诊断阻断；全局健康检查只适用于提交、完成声明、关闭、发布或后续规范明确要求全局健康的动作。

Code 生成管辖项目 Action Guide 时，必须消费 01 和 10 的管辖分流契约，并在输出中区分 `ldvh_specs`、`ldvh_facts`、`governed_project_facts` 和 `process_output` 或等价来源类型。只有 `governed_single` 可以生成单项目事实源 read_plan；`declared_multi_governed` 必须按每个 `governed_subject` 拆分 read_plan、source_refs、validation_guard 和 residual risk；`non_governed` 必须 no-op；`scope_unknown` 必须 degraded；`mixed_scope` 必须阻断、拆分或进入 Human Gate。Code 无法确认项目 `ldvh-base/` 入口或事实实例时，必须输出 `capability_gap`、`missing_fields` 或 `unverifiable`，不得伪造项目事实源 read_plan。

## 7. Runtime facade 与环境适配实现边界

01 已定义 Runtime Protocol、canonical event 和 trigger source 的上位语义。本文只承接具体实现边界。

V3 当前 runtime facade 的边界：

1. 可以消费 `01.Att.01` 的消费时机闭集；
2. 可以生成 Action Guide（行动指南）、preflight、stdout-only receipt 和 diagnostics；
3. 可以检查 acknowledged read_plan 和 completion evidence；
4. 不写持久 receipt；
5. 不安装 Hook、Rules、插件或环境入口；
6. 不声明当前环境完整支持 LDVH；
7. 不替代 AI 判断、Human Gate 或事实源回写。

payload schema、dispatcher、adapter、payload_present、unknown event 和环境 fallback 的当前 V3 可用边界由本文、01、10、30、33 和 Code/tests 承接；后续实现缺漏必须转为 V3-owned 待办，不以本地 V2 `06` 作为默认实现来源。涉及写入用户环境、安装 Hook、覆盖入口或扩大权限时，必须先进入 Human Gate 和 09 测试设计。

V2 项目管辖 target-based governance 中的静态解析能力由 `specs/10-安装与配置规范.md` 和本文 Code parser 承接。Code 可以输出 `governed_project_resolution`、`target_resolutions` 和管辖/非管辖边界 diagnostic；这些输出不得被解释为 Hook 已接入、环境已拦截或 Human Gate 已完成。

### 7.1 Repair Mode 输出契约

Code 可以在 preflight / runtime facade 中实现 `operation=repair` 或等价 `mode=repair`，但该模式只能承接 01 定义的 repair lane。Repair mode 不新增 runtime event，不跳过 read_plan、target 归口、Human Gate 或验证声明，也不得被用作 bypass。

Repair mode 必须同时满足：

1. target 归口为单一事实对象实例；
2. 待处理 diagnostic 的 scope 是当前 target 的 `target_primary`；
3. diagnostic code 属于本文定义的可修复事实对象结构诊断闭集；
4. 当前动作不推进状态、不关闭对象、不接受风险、不迁移事实源、不跨对象合并写入；
5. 输出必须标明 `mode=repair`、target、diagnostic code、blocking 计算口径、source_refs 和 final validation 要求。

当前可修复事实对象结构诊断闭集为：

| diagnostic code | 含义 |
|---|---|
| `FACT_INSTANCE_PARSE_FAILED` | 事实对象实例无法解析 |
| `FACT_INSTANCE_REQUIRED_FIELD_MISSING` | 必填字段缺失 |
| `FACT_INSTANCE_FIELD_UNKNOWN` | 出现未知字段 |
| `FACT_INSTANCE_REFERENCE_MISSING` | 引用不存在的事实对象 |
| `FACT_INSTANCE_ID_FILENAME_MISMATCH` | ID 与文件名不匹配 |
| `FACT_INSTANCE_TYPE_MISMATCH` | 事实对象类型不匹配 |
| `FACT_INSTANCE_ID_DUPLICATE` | 事实对象 ID 重复 |
| `FACT_INSTANCE_STATUS_INVALID` | 状态值不在闭集内 |
| `FACT_INSTANCE_LEGACY_FIELD_FORBIDDEN` | 出现禁止保留的 legacy 字段 |

不在该闭集内的 diagnostic、非事实对象 target、状态推进、关闭判断、Human Gate 风险接受、业务语义判断或跨对象迁移，必须输出 blocker 或 Human Gate diagnostic，不得被 repair mode 放行。Repair mode 的 Code 实现若发现 specs 没有覆盖的新诊断码，必须回到本文或对应事实模型规范补齐后再允许自动处理。

## 8. Code 变更纪律

新增或改变 Code 行为前，必须先确认：

1. 规则来源能回指正式 specs、事实对象、行动模板、测试要求或 Human 决策；
2. 正例、反例、失败条件和诊断分流可描述；
3. 输出不会反向定义 specs、事实源、Human Gate 或 Web/测试规则；
4. 有自动化测试、命令校验或等价验证；
5. 不把 Code 输出设计成 Web 页面/API 的主数据源、字段契约或页面状态机；
6. 无法验证时必须说明原因、范围和后续补齐位置。

Code 暴露规范缺口时，应输出 diagnostic 并回到对应规范、授权附件或新的事实对象承接，不得在实现中硬编码未确认候选规则。

`code/docs/` 中的实践文档只能说明当前 Code 参考实现、命令入口、模块职责、运行方式和测试映射。若实践文档需要新增稳定规则、字段契约或跨域职责，必须先回到对应 specs 或附件承接。

## 9. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源回指要求 | Code 行为必须回指正式规则或事实源 | source_refs、identity parser、tests | Code 治理 | 新增 parser、validator、CLI 或 facade 行为时 |
| 授权边界要求 | Code 输出不得表达授权、放行或风险接受 | 本文、02、04、tests | 语义治理 | 输出 status、diagnostic 或 receipt 时 |
| 诊断分流要求 | 失败、缺口和不可验证必须结构化输出 | diagnostic、preflight、runtime | 缺口治理 | Code 无法完成确定性判断时 |
| 管辖项目解析要求 | Code 解析管辖项目时必须回指 10 和根配置 | 10、`LDVH-GOVERNED-PROJECTS.yaml`、tests | 项目治理 | 新增 governed project parser、resolver 或 CLI 时 |
| Web 分离边界要求 | Code 输出不得成为 Web 页面/API 主数据源或字段契约 | 本文、08、tests | 架构治理 | 输出 DTO、diagnostic、source_refs 或验证摘要时 |
| 测试前置要求 | Code 行为变化必须有测试或等价验证 | 09、tests/code、CLI | 验证治理 | 修改 `code/` 或 Code 消费 specs 时 |

## 10. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 结构检查 | Code 是否从 Markdown specs 和附件读取稳定结构 | 回到 04 或 parser 缺口 |
| 诊断检查 | 输出是否区分阻断、警告、后续和不可验证 | 修正诊断或 tests |
| 授权边界检查 | 输出是否避免授权、Human Gate 替代和事实源替代语义 | 阻断完成声明 |
| Web 边界检查 | 输出是否没有被设计成 Web 页面/API 主数据源、字段契约或页面状态机 | 回到 08 分离边界或补测试 |
| 管辖项目检查 | target-first、Git common-dir、多目标和 no-op 是否按 10 解析 | 回到 10、配置或 resolver tests |
| runtime 检查 | facade 是否保持只读、stdout-only、environment_integrated=false | 记录环境接入缺口 |
| 回归检查 | `tests/code` 和 specs validator 是否覆盖关键正反例 | 补测试或写明等价验证 |

## 11. Human Gate

以下情况必须进入 Human Gate：

1. Code 输出被设计为授权、放行、验收或风险接受；
2. Code 准备写入事实源、安装 Hook、修改用户环境或覆盖入口；
3. 接受关键 Code 校验长期不可验证；
4. 让 Code 规则覆盖 specs 正文、事实源或 Human Gate；
5. 让 Code 输出成为 Web 页面/API 主数据源、字段契约或页面状态机；
6. 引入新的持久派生索引、缓存或数据库作为事实判断来源。

## 12. Stop Conditions

出现以下情况时，AI 必须暂停：

1. Code 行为没有正式规则来源；
2. Code 输出正在替代事实源、Human Gate 或完成声明；
3. parser、validator 或 facade 失败但被忽略；
4. unknown event、空 read_plan、缺失 evidence 或 target unknown 未被阻断或分流；
5. Code 输出被当作 Web 页面/API 主数据源或页面契约；
6. 代码变更无法验证且没有等价验证说明。

## 13. 待补齐事项

当前已识别以下待补齐事项。Code 不得在这些事项补齐前把实现输出写成规则已完整承接：

1. 六类管辖解析显式 `scope_status` 输出已补本地承接：涉及管辖项目、preflight 或 runtime facade 的 Code 输出必须继续在顶层表达 `governed_single`、`non_governed`、`scope_unknown`、`governed_target_unknown`、`declared_multi_governed` 或 `mixed_scope`，不得退回让消费者从 `governed`、`blocked` 或 message 反推；
2. `declared_multi_governed` 的只读审计路径已补本地承接：Human 明确发起跨管辖对象读取、审计或对比时，Code resolver 应表达该分类；写入、提交、迁移和事实源回写仍必须拆分或进入 Human Gate；
3. `ldvh.completion_claim` 已补当前 diagnostic 消费：runtime facade 不得只检查验证证据非空，必须继续输出未解决 blocker、未验证范围和残留风险的可消费摘要，并保留回归覆盖；
4. read_plan receipt bootstrap 路径已补受控放行边界；后续仍需保持 `ldvh.acknowledge_read_plan` 或等价 runtime receipt 入口不被 read_plan 消费检查自锁，且不得扩展为任意命令 bypass；
5. Action Guide governed project 链路 specs 契约已补齐：Code 生成行动指南时必须消费 10 的管辖解析结果，并区分 LDVH specs、LDVH facts、管辖项目 facts 和过程输出；Code builder 实现和回归仍需补齐；
6. test runner `verification_plan` 输出已补本地承接：测试 runner 必须继续说明选择理由、覆盖层级、排除层级、未验证范围和 residual risk，并回指 09 的验证入口选择矩阵；
7. Codex / WorkBuddy shim 命令分类逻辑需要收敛到共享实现，避免环境插件独立实现继续漂移。
