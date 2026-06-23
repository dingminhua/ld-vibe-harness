# rules-entry-sync-review-Rules入口同步审查

```yaml
v2_spec:
  spec_id: "30"
  spec_kind: "member_spec"
  title: "rules-entry-sync-review-Rules入口同步审查"
  status: "ready_for_review"
  authority: "not_active_until_human_approved"
  canonical_path: "specs/30-rules-entry-sync-review-Rules入口同步审查.md"
  created: "2026-06-24"
  updated: "2026-06-24"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "定义 specs 入口可见相关变化后，如何审查固定 Rules 入口表达是否需要同步"
  scope: "active specs、附件或行动成员主文件变化影响 Rules 入口路由、最小读取、STOP、工具入口、交接、验证或降级提示时的同步审查"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/03-行动编排规范.md"
    - "specs/06-运行时扩展规范.md"
  related_specs:
    - "specs/attachments/01.Att.07-行动编排接管建议矩阵.md"
    - "specs/attachments/03.Att.01-成员身份字段表.md"
    - "specs/attachments/03.Att.02-成员主文件骨架模板.md"
    - "specs/attachments/03.Att.03-成员一致性辅助核对表.md"
    - "specs/04-Code确定性执行规范.md"
    - "specs/attachments/04.Att.02-Code命令入口表.md"
    - "specs/attachments/04.Att.04-Code诊断码表.md"
    - "specs/attachments/06.Att.02-固定运行时扩展登记表.md"
    - "specs/07-事实源边界与Git追溯规范.md"
    - "specs/08-测试基础规范.md"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "rules_entry_sync_review"
    - "capability_assets"
  migration_status: "not_applicable"
```

```yaml
v2_action_member:
  spec_id: "30"
  kind: "action_process"
  name_en: "rules-entry-sync-review"
  name_zh: "Rules入口同步审查"
  collection_status: "planned"
  canonical_path: "specs/30-rules-entry-sync-review-Rules入口同步审查.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover: []
  capability_assets:
    - "type=rule; path=rules/LDVH-WORKSPACE-ENTRY.md; purpose=工作区入口表达同步审查对象; status=required"
    - "type=rule; path=rules/LDVH-MAINTAINER-ENTRY.md; purpose=维护入口表达同步审查对象; status=required"
    - "type=code; path=code/specs_validate.py preflight; purpose=写入前提示 Rules 影响和 Human Gate; status=required"
    - "type=code; path=code/specs_validate.py capability-environment; purpose=固定能力资产与环境保障矩阵只读投影; status=required"
    - "type=code; path=code/specs_validate.py deployment-entries; purpose=固定运行时扩展登记一致性检查; status=required"
  code_consumption:
    - "action_member_identity"
    - "action_member_anchors"
    - "rules_entry_sync_review"
    - "capability_assets"
```

```yaml
ldvh_member:
  spec_id: "30"
  kind: work_process
  name_en: rules-entry-sync-review
  name_zh: Rules入口同步审查
  collection_status: planned
  canonical_path: specs/30-rules-entry-sync-review-Rules入口同步审查.md
  code_consumption:
    - workflow_index
    - rules_entry_sync_review
```

> 文件状态：本文是 30-59 行动编排成员主文件草案，当前 `collection_status=planned`，不是 active 行动编排，不得被 Rules、Skill、Agent、Hook、Code 或 Web 当作已生效流程默认调用。
> 当前用途：在 30 进入 active 前，本文只作为 Rules 入口同步审查的候选清单和人工降级参考；正式执行仍以 `specs/06-运行时扩展规范.md` 的 4.2 节、固定 Rules 入口和 Human Gate 为准。

## 1. 本文解决的问题

本文定义当 active specs、附件或行动成员主文件发生变化，并可能影响固定 Rules 资产的入口表达时，AI 如何判断是否需要同步 `rules/LDVH-WORKSPACE-ENTRY.md` 或 `rules/LDVH-MAINTAINER-ENTRY.md`。

本文解决：

1. 什么变化应进入 Rules 入口同步审查；
2. 审查前应读取哪些最小 Context；
3. 如何区分无需同步、建议同步和必须进入 Human Gate；
4. 编排只负责检查和提出同步意见，不把来源 specs 的入口可见要求改写为新规则；
5. Human 确认后由谁实际修改 Rules；
6. 修改后如何验证、留证和回写。

本文不定义 Rules 资产本体规则、不定义 specs 入口可见要求、不定义 Skill/Hook/Agent/Code 的落地需求，也不写入任何外部环境入口。Rules 资产自描述、同步触发和 Human Gate 边界归 06；Code 输出 Schema 归 04；事实源回写和 Git 追溯归 07。

## 2. 上位依据

本文承接 `specs/03-行动编排规范.md`：

1. 行动编排承接的是执行责任，不是来源规范的规则权威；
2. 当前 `collection_status=planned`，不得被解释为 active 可执行流程；
3. Skill、Agent、Code、Hook 和 Rules 输出必须交还主控判断；
4. 过程输出、检查结果和同步建议默认不是最终事实源。

本文承接 `specs/06-运行时扩展规范.md`：

1. Rules 资产可以把 active specs 派生为入口路由、最小读取、STOP、工具导航、交接和降级提示；
2. active specs、附件或成员主文件变化后，应评估固定 Rules 资产是否受影响；
3. 评估结论只能是无需同步、需要同步 Rules 入口表达，或进入 Human Gate；
4. 来源规范负责触发影响评估，Rules 文件自身只承载实例自描述和运行时入口表达。

本文承接 `specs/01-规范体系基础规范.md` 的保障要求和成员机制，承接 `specs/04-Code确定性执行规范.md` 的只读诊断边界，承接 `specs/07-事实源边界与Git追溯规范.md` 的事实源和 Git 追溯边界，承接 `specs/08-测试基础规范.md` 的验证声明边界。

## 3. 构成要素归属与价值判断

### 3.1 构成要素归属

本文属于六类构成要素中的行动编排。

| 项目 | 判断 |
|---|---|
| 主归属 | 行动编排 |
| 承接对象 | specs 入口可见相关变化后的 Rules 入口表达同步审查 |
| 调度能力 | Rules、Code 命令、知识地图只读投影、人工降级检查和 Human Gate |
| 不归属边界 | 不定义 specs 规则、不定义 Rules 资产身份、不定义 Skill/Hook/Agent/Code 落地流程、不写入环境入口 |

### 3.2 正向价值判断

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 明确 Rules 入口同步审查的进入信号、Context 和候选命令 |
| V2 可行动理解 | 把“入口可见要求变化后谁检查 Rules”收束为单一 planned 成员 |
| V4 稳定执行 | 固化无需同步、建议同步、Human Gate 三类结论 |
| V5 门禁识别 | 修改 Rules 边界、STOP、source_specs 或 sync_triggers 前识别 Human Gate |
| V6 强制验证 | 要求同步前后运行 preflight、deployment-entries、capability-environment 和相关 specs 检查 |
| V8 可靠回写 | 把稳定同步结论和修改通过 Git commit records 追溯 |

### 3.3 逆向价值判断

| 反模式 | 本文必须阻止 |
|---|---|
| 把所有能力变化都拉进 Rules 同步 | 只有影响 Rules 入口表达的 specs、附件或成员变化才进入本文范围 |
| 用编排替代来源 specs | 本文只承接检查和同步执行责任，不改变来源规范权威 |
| 用 planned 成员冒充 active 流程 | 当前只能作为候选清单和人工降级参考 |
| 自动修改 Rules | 编排给出建议；涉及高影响边界时先进入 Human Gate，由主控 AI 在授权范围内修改 |
| 用 Rules 复制 specs 正文 | Rules 只保留入口表达、回指和降级提示，不复制规范本体 |

## 4. 行动定位与适用场景

本文定位为 Rules 入口表达同步审查的 planned 行动编排成员。

适用场景是：某次 specs、附件或行动成员主文件变化，可能影响 AI 通过固定 Rules 入口定位规范、判断场景、执行最小读取、识别 STOP、选择工具、交还入口或说明降级风险。

本文不适用于以下场景：

1. 普通 `rules/` 文案调整但未改变入口表达；
2. Skill、Hook、Agent、Code 或 Web 自身实现变化；
3. 环境入口安装、Hook 接入或用户配置写入；
4. 管辖项目 WorkCase、Spark、ADR、Pitfall 或 Study 处理；
5. 单次聊天建议、未进入 specs 的临时口径。

## 5. 准入条件

进入本文审查必须同时满足：

1. 变化来源是 active specs、授权附件或行动成员主文件；
2. 变化可能影响固定 Rules 资产的入口表达；
3. 影响对象至少包括 `rules/LDVH-WORKSPACE-ENTRY.md` 或 `rules/LDVH-MAINTAINER-ENTRY.md` 之一；
4. 需要给出无需同步、建议同步或 Human Gate 结论；
5. 能回指变化来源、影响字段或影响章节。

典型准入信号包括：

| 信号 | 说明 |
|---|---|
| 入口可见要求变化 | 来源 specs 改变 AI 应如何定位某规范、对象、命令或入口 |
| 最小读取顺序变化 | Rules 现有启动顺序、场景路由或必读入口可能不再准确 |
| STOP 或 Human Gate 变化 | Rules 需要提醒 AI 暂停或交还 Human 的条件变化 |
| 交接路径变化 | 工作区入口、维护入口或其它入口的 handoff 规则变化 |
| 验证入口变化 | Rules 中应列出的 Code 命令、验证入口或降级检查变化 |
| 知识地图或 Code 入口含义变化 | Rules 对知识地图、preflight、runtime_extensions 或 capability-environment 的导航口径变化 |
| 事实源边界变化 | Rules 中对工作对象、产品资产、Git 追溯或环境状态的边界提示可能需要同步 |

## 6. 事实源边界

本文是 planned 行动编排成员主文件，不是 active 执行事实源。

| 内容 | 权威位置 |
|---|---|
| Rules 同步责任通用规则 | `specs/06-运行时扩展规范.md` §4.2 |
| 行动编排成员机制 | `specs/03-行动编排规范.md` |
| 工作区 Rules 入口资产 | `rules/LDVH-WORKSPACE-ENTRY.md` |
| 维护 Rules 入口资产 | `rules/LDVH-MAINTAINER-ENTRY.md` |
| 固定运行时扩展登记 | `specs/attachments/06.Att.02-固定运行时扩展登记表.md` |
| 受控写入前诊断 | `python3 code/specs_validate.py preflight --target-path <path>` |
| 能力环境矩阵 | `python3 code/specs_validate.py capability-environment` |

本文产生的审查结论、同步建议、命令输出和草案补丁默认是过程输出。只有写入 specs、Rules、事实对象或 Git commit records 后，才形成可追溯事实。

## 7. Context 要求

进入审查前，主控 AI 应读取或查询：

1. 本文状态；若 `collection_status` 不是 `active`，必须说明当前只是人工降级参考；
2. 变化来源文件和相关章节；
3. `specs/06-运行时扩展规范.md` 的 4.1、4.2、5、7、11、12 节；
4. 受影响的固定 Rules 文件；
5. `specs/attachments/06.Att.02-固定运行时扩展登记表.md`；
6. 必要 Code 输出：

```bash
python3 code/specs_validate.py preflight --target-path <changed-path>
python3 code/specs_validate.py deployment-entries
python3 code/specs_validate.py capability-environment
python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text
```

若工具不可用，应退回文件事实源和人工降级检查，不得因为工具缺口跳过 Rules 影响评估。

## 8. Scenario 识别

当满足以下任一 Scenario 时，应进入 Rules 入口同步审查：

1. 用户明确要求检查 specs 变化后 Rules 是否需要同步；
2. 修改或计划修改 active specs、附件或行动成员主文件，且内容涉及入口可见、最小读取、场景路由、STOP、Human Gate、工具入口、交接、验证、降级提示、知识地图入口或 Code 检查入口含义；
3. `preflight` 输出固定 Rules 资产影响提示；
4. `capability-environment`、`deployment-entries` 或 `runtime_extensions` 投影显示固定 Rules 资产来源、验证链或同步触发与当前变化存在冲突；
5. 主控 AI 准备声明某个 specs 入口已可被 Rules 稳定导航。

以下情况不进入本文：

1. `rules/`、`skills/`、`hooks/` 或 `code/` 文件普通实现变化，但没有上游 specs 入口表达变化；
2. Skill、Hook、Agent 或 Code 的能力落地需求，需要进入后续能力承载分流，而不是 Rules 入口同步；
3. 环境入口写入、安装或支持声明，需要进入环境入口落地与适配检查，而不是 Rules 同步审查。

## 9. 执行流程

当前 `collection_status=planned` 时，以下流程只作为人工降级检查清单。未来本文 active 后，才能作为正式行动编排流程。

1. 确认触发源是否为 specs、附件或行动成员主文件变化；
2. 摘要变化内容，标注是否影响入口可见、读取顺序、STOP、工具入口、交接、验证或降级提示；
3. 读取受影响 Rules 的 `ldvh_asset.source_specs`、`sync_triggers`、`verification` 和正文场景路由；
4. 运行必要 Code 检查；
5. 判断影响类型：

| 结论 | 使用条件 | 后续动作 |
|---|---|---|
| 无需同步 | 变化不影响 Rules 入口表达，或 Rules 已通过来源规范/工具入口覆盖 | 记录依据，继续原任务 |
| 建议同步 | 变化影响 Rules 可见表达，且不触发高影响 Human Gate | 给出具体修改点，由主控 AI 修改并验证 |
| Human Gate | 涉及职责边界、STOP、`source_specs`、`sync_triggers`、canonical path、固定承载物身份、权限扩大或环境薄引用 | 暂停，向 Human 说明影响范围和建议 |

6. 若 Human Gate 通过，由主控 AI 在授权范围内修改 Rules；
7. 修改后重新运行验证；
8. 将稳定结论写入对应文件、事实对象或 Git commit records。

## 10. 执行中问题分流与失败暂停

执行中发现问题时按以下方式分流：

| 问题 | 分流 |
|---|---|
| 来源 specs 与 Rules 正文冲突 | 回到来源 specs、06 和受影响 Rules；必要时 Human Gate |
| Code 输出与文件事实源冲突 | 以文件事实源为准，修正 Code 或记录 Code 缺口 |
| 变化实际属于 Skill/Hook/Agent/Code 落地 | 分流到能力承载落地分流候选，不在本文内处理 |
| 变化实际属于环境入口安装或支持声明 | 分流到环境入口落地与适配检查候选 |
| 缺少验证命令或验证失败 | 不得声明完成；修复后重新验证或记录人工降级 |
| 需要接受长期降级 | 进入 Human Gate，不得由主控 AI 单独接受 |

若同一 Rules 同步判断连续失败，或无法判断变化是否影响入口表达，应暂停并请求 Human 方向校正。

## 11. Human Gate

以下情况必须触发 Human Gate：

1. 修改固定 Rules 资产职责边界、权限含义、STOP 点或入口交接；
2. 修改固定 Rules 的 `source_specs`、`sync_triggers`、canonical path 或固定承载物身份；
3. 新增、删除、移动或重命名固定 Rules 资产；
4. 改变工作区入口与维护入口的职责分离；
5. 覆盖用户环境入口、项目规则或等价配置；
6. 声明 Rules 入口已在某环境中部署生效；
7. 接受 Rules 同步长期降级；
8. 将 planned 或 candidate 行动编排当作 active 流程执行。

普通文案澄清、路径错字修正、验证命令补充或不改变入口行为的读取建议调整，可在说明依据并完成验证后由主控 AI 处理。

## 12. Skill 和 Agent 调度

本文不要求固定 Skill 或 Agent。

可选调度边界如下：

| 能力 | 可做 | 不可做 |
|---|---|---|
| Skill | 辅助提交准备或固定检查步骤复用 | 不决定 Rules 是否同步，不替代 Human Gate |
| Agent | 对高风险入口边界做独立审查 | 不直接修改 Rules，不独立成为最终结论 |

所有 Skill 或 Agent 输出必须交还主控 AI，由主控按本文、03、06 和 Human Gate 判断。

## 13. Code、命令和 Web 协作适配

本文主要消费以下 Code 命令：

| 命令 | 用途 | 边界 |
|---|---|---|
| `python3 code/specs_validate.py preflight --target-path <path>` | 写入前提示 Human Gate、Rules 影响和归口 | 不授权写入 |
| `python3 code/specs_validate.py deployment-entries` | 检查固定运行时扩展登记与自描述一致性 | 不说明环境已安装 |
| `python3 code/specs_validate.py capability-environment` | 投影固定能力资产来源、同步、验证和环境边界 | 不写环境入口，不替代 Rules 判断 |
| `python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text` | 查看固定运行时扩展自描述知识地图投影 | 不替代 active specs 或资产原文 |
| `python3 code/specs_validate.py all --fail-on-diagnostics` | 修改完成后的综合诊断 | 不替代专项验证声明 |

本文暂不要求 Web 协作。未来 Web 只能展示审查状态、风险和待确认项，不得替代主控判断或 Human Gate。

## 14. 事实源回写与证据留存

以下内容应按 07 判断是否回写：

1. Rules 实际修改；
2. Human Gate 决策；
3. 验证结果；
4. 无需同步的稳定结论；
5. 失败降级和后续分流。

可回写位置包括：

| 内容 | 候选位置 |
|---|---|
| Rules 同步后的稳定入口表达 | 对应 Rules 文件 |
| 候选计划或未完缺口 | Spark |
| 高影响取舍 | ADR |
| 可复用失败经验 | Pitfall |
| 提交追溯 | Git commit records |

不得把聊天过程、临时命令输出或 planned 编排状态直接写成 active 流程事实。

## 15. 环境适配边界

本文不负责环境入口落地。

Rules 文件同步完成，只说明 LDVH 固定 Rules 资产的入口表达已经更新，不说明 Codex、Claude Code、Trae、CI、IDE、Shell 或用户本地配置已经加载该资产。

凡涉及写入、覆盖、安装、启用、声明环境支持、声明 Hook 生效或把候选入口文本放入用户环境，必须回到 `specs/06-运行时扩展规范.md` §7、`specs/attachments/06.Att.10-部署检查核对表.md` 和后续环境入口落地与适配检查编排候选。

## 16. 行动特有可测试性锚点

本文未来 active 前至少应具备以下可测试性锚点：

| 锚点 | 正例 | 反例 |
|---|---|---|
| Scenario | specs 修改影响入口可见时进入审查 | code 实现变化但无入口影响时误进入 |
| Context | 读取变化来源、06 §4.2、受影响 Rules 和 Code 输出 | 只凭聊天记忆判断 |
| Gate | 修改 STOP 或 `source_specs` 前触发 Human Gate | 静默改写高影响入口边界 |
| 输出 | 明确无需同步、建议同步或 Human Gate | 只说“应该没问题” |
| 验证 | 修改后运行 deployment-entries、capability-environment 和相关 specs 检查 | 未验证即声明完成 |

当前 planned 状态下，测试只验证本文结构、身份和人工降级检查口径；不得把测试通过解释为 active 流程已生效。

## 17. 规范保障要求

本节不定义新的规范保障要求，只说明本文如何承接来源 specs 的入口表达要求，并把它落到具体实践、能力资产和验证证据。

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源要求承接实践 | 只承接 specs、附件或行动成员主文件对固定 Rules 入口表达的影响，不新增子级规范保障要求 | 本文 §8、`preflight`、受影响 Rules 文件 | 行动实践关联 | 变化可能影响入口可见、读取顺序、STOP、工具入口、交接、验证或降级提示时 |
| Rules 修改实践 | Rules 入口表达需要同步时，由主控 AI 在授权范围内修改；高影响项先进入 Human Gate | `rules/LDVH-WORKSPACE-ENTRY.md`、`rules/LDVH-MAINTAINER-ENTRY.md`、本文 §9、§11 | Rules 入口表达同步 | 审查结论为建议同步或 Human Gate 通过时 |
| Code 辅助实践 | 使用只读 Code 投影辅助判断固定 Rules 来源、验证链和环境边界，不把投影当作事实源 | `deployment-entries`、`capability-environment`、`runtime_extensions` | Code 诊断协作 | 需要判断固定 Rules 资产来源、验证链或环境边界时 |
| 能力协作实践 | Skill/Agent 只给过程输出，必须交还主控 AI | 本文 §12、主控 AI、可选 Agent 输出 | 能力输出交还 | 需要独立审查、并行探索或复用稳定步骤时 |
| 环境边界实践 | 本文不落地环境入口、不声明部署；环境入口问题回到 06 或后续环境适配编排候选 | 06、固定 Rules、Human Gate、后续候选成员 | 环境适配分流 | 涉及环境入口、部署声明、Hook 生效声明或长期降级时 |

## 18. 行动编排成员检查要求

检查本文至少包括：

| 检查项 | 标准 |
|---|---|
| 身份块 | 同时包含 `v2_spec` 和 `v2_action_member` |
| 状态分工 | `v2_spec.status` 不被误读为 active 流程；以 `collection_status=planned` 为准 |
| 锚点 | Scenario、Context、Gate、执行、问题分流、回写、证据和可测试性锚点可定位 |
| 承接边界 | 只审查 Rules 入口表达同步，不处理 Skill/Hook/Agent/Code 落地 |
| 能力映射 | `capability_assets` 只登记审查所需能力，不声明部署完成 |
| Human Gate | 高影响 Rules 修改、环境写入和 planned 冒充 active 均被阻断 |
| 验证入口 | Code 命令和人工降级检查可回指 04、06 和 08 |

## 19. 待补齐事项

1. 需要 Human 明确确认本文是否可从 `planned` 升级为 `active`；
2. 若升级 active，应补齐 Code 对 `v2_action_member` 锚点、`assurance_takeover` 和 `capability_assets` 的专项诊断；
3. 若升级 active，应把来源 specs 的入口可见要求通过 `assurance_takeover` 明确登记为被承接要求；
4. 需要评估是否由 preflight 在 specs 写入前输出更精确的 `Rules 入口同步审查` 提示；
5. 需要确认环境入口落地与适配检查是否形成独立 31 或后续成员；
6. 需要确认能力承载落地分流是否形成独立 32 或后续成员。
