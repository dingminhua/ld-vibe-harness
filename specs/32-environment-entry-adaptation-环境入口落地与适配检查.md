# environment-entry-adaptation-环境入口落地与适配检查

```yaml
v2_spec:
  spec_id: "32"
  spec_kind: "member_spec"
  title: "environment-entry-adaptation-环境入口落地与适配检查"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs/32-environment-entry-adaptation-环境入口落地与适配检查.md"
  created: "2026-06-24"
  updated: "2026-06-25"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "候选定义 AI 如何从 active specs 的规范保障要求动态生成环境落地投影，并帮助 Human 将所需运行时入口、薄引用、Skill、Hook、Code 命令或等价配置适配到具体 AI 协作环境"
  scope: "保障要求聚合、行动接管状态识别、运行时承载方向映射、能力缺口分流、环境入口候选渲染、受控写入授权、部署后适配检查、问题原因说明、禁止声明和证据留存"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/03-行动编排规范.md"
    - "specs/06-运行时扩展规范.md"
    - "specs/07-事实源边界与Git追溯规范.md"
  related_specs:
    - "specs/04-Code确定性执行规范.md"
    - "specs/08-测试基础规范.md"
    - "specs/30-rules-entry-sync-review-Rules入口同步审查.md"
    - "specs/31-git-commit-action-Git提交行动编排.md"
    - "specs/attachments/03.Att.02-成员主文件骨架模板.md"
    - "specs/attachments/06.Att.02-固定运行时扩展登记表.md"
    - "specs/attachments/06.Att.05-保障要求承载矩阵.md"
    - "specs/attachments/06.Att.06-能力缺口分流核对表.md"
    - "specs/attachments/06.Att.07-环境适配字段表.md"
    - "specs/attachments/06.Att.08-适配状态表.md"
    - "specs/attachments/06.Att.09-薄引用模板.md"
    - "specs/attachments/06.Att.10-部署检查核对表.md"
    - "specs/attachments/06.Att.11-Codex环境入口候选矩阵.md"
    - "specs/attachments/06.Att.12-CodexHook事件候选矩阵.md"
    - "specs/attachments/06.Att.13-非Codex自助适配核对表.md"
    - "specs/attachments/06.Att.14-权威资产副本分层核对表.md"
  migration_sources:
    - "history/specs-v1/04.03-环境入口适配与部署规范.md"
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "environment_adaptation"
    - "deployment_entries"
    - "capability_assets"
    - "assurance_requirements"
    - "assurance_to_capability_mapping"
    - "runtime_capability_gap_routing"
  migration_status: "not_migrated"
```

```yaml
v2_action_member:
  spec_id: "32"
  kind: "action_process"
  name_en: "environment-entry-adaptation"
  name_zh: "环境入口落地与适配检查"
  collection_status: "candidate"
  canonical_path: "specs/32-environment-entry-adaptation-环境入口落地与适配检查.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover:
    - "source_spec=specs/01-规范体系基础规范.md; requirement=规范保障要求; scope=以 active specs 的规范保障要求五字段表作为环境落地投影的动态输入，不维护手写静态清单"
    - "source_spec=specs/06-运行时扩展规范.md; requirement=环境入口、薄引用与适配检查; scope=环境入口候选、薄引用生成、受控写入、部署后检查和声明边界"
    - "source_spec=specs/06-运行时扩展规范.md; requirement=能力保障要求; scope=按 06.Att.05/06.Att.06 将保障要求映射到运行时承载方向、外部归口和缺口分流"
    - "source_spec=specs/03-行动编排规范.md; requirement=保障需求生成要求; scope=把环境落地这类跨步骤、高 Gate、高证据需求收束为候选行动闭环"
    - "source_spec=specs/04-Code确定性执行规范.md; requirement=确定性执行要求; scope=消费 assurance-report、assurance-plan、ldvh-assurance-check、deployment-entries 和 capability-environment 的只读诊断，不用 Code 输出替代事实源或授权写入"
    - "source_spec=specs/07-事实源边界与Git追溯规范.md; requirement=回写边界要求; scope=环境观察、部署证据、问题原因说明何时能成为稳定事实"
    - "source_spec=specs/08-测试基础规范.md; requirement=失败阻断要求; scope=未完成适配检查、关键验证缺失或证据不可追溯时不得声明接入完成"
  capability_assets:
    - "type=rule; path=rules/LDVH-ENTRY.md; purpose=工作区入口薄引用目标; status=required"
    - "type=rule; path=rules/LDVH-ENTRY.md; purpose=LDVH 产品资产维护入口薄引用目标; status=required"
    - "type=skill; path=skills/ldvh-git-commit/SKILL.md; purpose=需要在环境中验证 Skill 可发现或可手动等价执行时的固定 Skill 资产; status=optional_by_environment"
    - "type=hook; path=hooks/ldvh-hooks.yaml; purpose=需要在环境中验证 Hook registry 可被调用或接入时的固定 Hook 资产; status=optional_by_environment"
    - "type=code; path=code/specs_validate.py assurance-report; purpose=聚合 active specs 的规范保障要求，作为环境落地投影的动态需求输入; status=required"
    - "type=code; path=code/specs_validate.py assurance-plan; purpose=聚合保障缺口、写入需求、Human Gate 和回写目标，作为落地优先级与分流输入; status=required"
    - "type=code; path=code/specs_validate.py ldvh-assurance-check; purpose=生成 LDVH 部署与适配检查派生报告，辅助识别部署基线和剩余缺口; status=required"
    - "type=code; path=code/specs_validate.py deployment-entries; purpose=固定运行时扩展登记一致性检查; status=required"
    - "type=code; path=code/specs_validate.py capability-environment; purpose=固定能力资产与环境落地边界只读矩阵; status=required"
    - "type=code; path=code/specs_validate.py v2-check --input-scope runtime_extensions; purpose=固定运行时扩展自描述入口层只读诊断; status=required"
  code_consumption:
    - "action_member_identity"
    - "action_member_anchors"
    - "environment_adaptation"
    - "deployment_entries"
    - "capability_assets"
```

> 文件状态：本文是 draft 候选行动编排成员主文件，当前 `collection_status=candidate`。它不是 active 行动编排，不得被 Rules、Skill、Agent、Hook、Code、Web 或 AI 默认当作已生效流程执行。
> 当前用途：为“环境入口落地与适配检查”形成可审阅草案，供 Human 后续决定是否升级为 active 成员。

## 1. 本文解决的问题

本文候选定义 AI 在 LDVH 场景中如何从 active specs 的 `规范保障要求` 动态生成环境落地投影，再帮助 Human 将投影所需的运行时入口、薄引用、Skill、Hook、Code 命令或等价配置适配到具体 AI 协作环境，并完成现场适配检查和证据交还。

本文拟解决：

1. 环境落地项应如何从 specs `规范保障要求`、行动编排接管状态和能力缺口动态生成，而不是手写静态清单；
2. 如何把每条来源要求投影为承接状态、运行时承载方向、已有能力资产、环境入口候选、验证方式和缺口分流；
3. 如何区分官方维护入口模板、用户现场配置、本次检查结果、长期适配措施和环境类型能力判断；
4. AI 何时只能生成候选薄引用或适配说明，何时可以在 Human 授权后受控写入；
5. 如何检查薄引用、AGENTS、config、hooks、Skill、Code 命令或等价入口是否服务于对应保障要求；
6. 如何输出接入证据、失败项、未承接项和禁止声明，避免把本地观察写成长期支持状态。

本文不定义新的规范保障要求类型，不维护静态环境落地清单，不定义 Rules、Skill、Agent、Hook 的资产本体，不定义各 AI 环境的产品能力（Codex/WorkBuddy/Claude Code 支持 AI Hook；Trae 不支持 AI Hook；CI/IDE/Shell 非 AI 协作环境），不定义 Code 输出 Schema，不定义测试实现，也不声明任何环境已经完整支持 LDVH。

## 2. 上位依据

本文承接 `specs/03-行动编排规范.md` 的候选成员、Context、Scenario、Gate、主控调度、证据、回写和能力边界规则。

本文承接 `specs/06-运行时扩展规范.md` 的能力保障链路、环境入口、薄引用、部署适配、适配检查、固定承载物自描述、Human Gate 和环境状态声明边界。

本文承接 `specs/attachments/06.Att.05-保障要求承载矩阵.md` 和 `specs/attachments/06.Att.06-能力缺口分流核对表.md`，用于把来源保障要求映射为运行时承载方向、外部归口和缺口分流。

本文承接 `specs/07-事实源边界与Git追溯规范.md` 的过程输出、环境观察、工具报告和稳定事实源回写边界。

本文承接 `specs/08-测试基础规范.md` 的验证声明边界：未完成关键适配检查或证据不可追溯时，不得声明接入完成。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的行动编排。

正向价值判断：

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 给出保障要求聚合、承载矩阵、缺口分流、环境入口和检查入口 |
| V2 可行动理解 | 把“落地到环境”拆成来源要求、承接状态、承载方向、环境渲染、检查和证据 |
| V4 稳定执行 | 固化候选文本、授权、写入、检查、交还和问题分流顺序 |
| V5 门禁识别 | 在覆盖用户入口、启用 Hook、扩大权限或声明支持前触发 Human Gate |
| V6 强制验证 | 要求 assurance-report、assurance-plan、deployment-entries、capability-environment、入口可读性和现场检查 |
| V7 证据沉淀 | 输出来源要求、投影行、环境类型、入口、承载物、检查方式、结论、失败项和未承接项 |
| V8 可靠回写 | 按 07 判断长期缺口、风险、经验或决策是否回写事实源 |

逆向价值判断：

| 反模式 | 本文必须阻止 |
|---|---|
| 把候选入口当已部署 | 候选文本、配置片段和 Hook registry 不等于环境已接入 |
| 把本机检查写成长期状态 | 本次检查只能说明当前环境、路径、版本和配置 |
| 用行动编排替代 06 | 本文只编排落地检查，不改变运行时扩展规则 |
| 静态清单替代保障要求 | 所有落地项必须回指来源保障要求、接管状态和承载矩阵 |
| 用薄引用复制正文 | 薄引用只能包含入口路径、恢复后重读提示和管理段标记 |
| 覆盖用户配置 | 未经 Human 授权不得写入、覆盖或删除用户入口 |
| 声明完整支持 | 未完成适配检查不得声明完整支持、原生支持、Hook 生效或资产已部署 |

## 4. 行动定位与适用场景

本文候选定位为保障要求驱动的环境入口落地和适配检查行动。它先从 LDVH 权威 specs、行动编排接管状态、运行时承载矩阵和能力缺口分流生成环境落地投影，再处理投影到具体 AI 协作环境入口之间的部署层事务。

环境入口候选、AGENTS、config、hooks、Skill、Code 命令和手动步骤都只是投影结果中的承载方式，不是落地需求的来源。

适用场景包括：

1. 用户要求把 LDVH 接入某个 AI 协作环境；
2. 用户指出入口之外还缺少保障能力，需要识别哪些保障要求尚未被环境承载；
3. 用户要求生成、检查或修复 AGENTS、instructions、config、hooks、软链、安装脚本或等价入口；
4. 需要确认环境入口是否只包含薄引用，并能定位工作区入口或维护入口；
5. 需要检查 Skill、Hook、Code 命令或等价能力在当前环境中是否可发现、可调用或只能使用临时核对动作；
6. 需要输出“本次接入是否有效”的证据摘要，并说明禁止声明。

不适用场景包括：

1. 只修改 Rules 入口表达，应按 `specs/30-rules-entry-sync-review-Rules入口同步审查.md`；
2. 只准备 Git commit，应按 `specs/31-git-commit-action-Git提交行动编排.md`；
3. 修改固定运行时扩展承载物本体，应回到 06 和对应资产自描述；
4. 只需要查看全部规范保障缺口但不涉及环境承载时，应优先使用 `assurance-report` 或 `assurance-plan`；
5. 判断管辖项目工作对象，应回到工作区入口和事实模型成员规范；
6. 非 active 环境能力研究或产品调研，应分流为 Study、Spark 或 ADR。

## 5. 准入条件

进入本文候选流程必须同时满足：

1. 用户目标涉及环境入口、配置、Hook、Skill、Agent、指令入口、安装副本或等价运行时接入；
2. 能识别目标环境类型，或明确标记为“待确认环境类型”；
3. 能读取 active specs 的规范保障要求聚合结果；若工具不可用或输出不足，必须记录原因并回读原文；
4. 能识别保障要求到行动接管、运行时承载、外部归口和缺口分流的当前依据；
5. 能识别至少一个对应 LDVH 承载物、Code 命令或临时核对动作，例如工作区 Rules、维护 Rules、Skill、Hook registry 或 `specs_validate.py` 命令；
6. 能区分候选文本、用户现场配置、本次检查结果和长期状态；
7. 不把本文候选状态解释为 active 流程。

若用户要求 AI 直接写入环境入口，必须先进入 Human Gate，并确认目标入口、写入范围、已有内容保护和退出方式。

## 6. 事实源边界

| 内容 | 权威位置 |
|---|---|
| 规范保障要求五字段和接管状态口径 | `specs/01-规范体系基础规范.md` §12 |
| 行动编排来源承接和能力实践闭环 | `specs/03-行动编排规范.md` §12 |
| 保障要求到运行时承载方向 | `specs/attachments/06.Att.05-保障要求承载矩阵.md` |
| 能力缺口分流 | `specs/attachments/06.Att.06-能力缺口分流核对表.md` |
| 环境入口、薄引用和部署适配规则 | `specs/06-运行时扩展规范.md` §7 |
| 环境适配字段 | `specs/attachments/06.Att.07-环境适配字段表.md` |
| 适配状态闭集 | `specs/attachments/06.Att.08-适配状态表.md` |
| 薄引用模板 | `specs/attachments/06.Att.09-薄引用模板.md` |
| 部署检查阶段 | `specs/attachments/06.Att.10-部署检查核对表.md` |
| Codex 入口候选 | `specs/attachments/06.Att.11-Codex环境入口候选矩阵.md` |
| Codex Hook 候选 | `specs/attachments/06.Att.12-CodexHook事件候选矩阵.md` |
| 非 Codex 自助适配 | `specs/attachments/06.Att.13-非Codex自助适配核对表.md` |
| 权威资产与部署副本分层 | `specs/attachments/06.Att.14-权威资产副本分层核对表.md` |
| 固定承载物基线 | `specs/attachments/06.Att.02-固定运行时扩展登记表.md` 和资产自身 `ldvh_asset` |
| 保障要求聚合与计划视图 | `code/specs_validate.py assurance-report`、`code/specs_validate.py assurance-plan`、`code/specs_validate.py ldvh-assurance-check` 的只读输出 |
| 过程输出回写边界 | `specs/07-事实源边界与Git追溯规范.md` |

环境入口文件、配置片段、Hook 配置、软链、安装副本和用户本地 instructions 属于部署或适配层，不是 LDVH 权威 Rules、Skill、Agent 或 Hook 本体。

本文产生的环境落地投影、候选文本、检查摘要、失败报告和建议默认是过程输出。只有写入对应权威事实源并可 Git 追溯后，才成为稳定事实。

## 7. Context 要求

主控 AI 进入本文候选流程前，应收集：

1. 用户目标、目标环境类型、目标工作区和目标项目边界；
2. active specs 的规范保障要求聚合视图，以及未能聚合时的问题原因和原文回读动作；
3. 行动编排接管状态，包括 active 成员、candidate 成员、待接管缺口、建议接管和临时核对动作；
4. `06.Att.05` 的保障要求承载方向和 `06.Att.06` 的能力缺口分流；
5. 目标环境入口候选，例如 AGENTS、instructions、config、hooks、软链、安装脚本或会话入口；
6. 对应 LDVH 承载物、Code 命令、临时核对动作和真实绝对路径；
7. `specs/06-运行时扩展规范.md` §5、§7、§11、§12；
8. `06.Att.07` 至 `06.Att.14` 中与目标环境相关的附件；
9. 固定资产登记和目标资产自描述；
10. 必要 Code 输出：

```bash
python3 code/specs_validate.py assurance-report --format text
python3 code/specs_validate.py assurance-plan --format text
python3 code/specs_validate.py ldvh-assurance-check --format text
python3 code/specs_validate.py deployment-entries
python3 code/specs_validate.py capability-environment
python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text
```

环境落地投影至少应包含以下字段：

| 字段 | 含义 |
|---|---|
| 来源要求 | `source_spec`、保障要求名称、同步类型和触发条件 |
| 接管状态 | active 接管、candidate 接管、建议接管、待接管缺口或临时核对动作 |
| 承载方向 | Rules、Skill、Agent、Hook、Code、Web、测试、Human Gate、临时核对动作或外部归口 |
| 当前资产 | 可回指的固定承载物、自描述、Code 命令或无可用资产 |
| 环境渲染 | 在目标环境中的入口候选、配置方式、手动步骤或不适用原因 |
| 验证方式 | 可执行命令、现场检查、测试入口、Human Gate 或 Human 复核 |
| 缺口分流 | 06.Att.06 缺口类型、建议回写位置和禁止声明 |

涉及规范、入口或同步影响判断时，应使用带起点的知识地图查询。若知识地图工具不可用、输出不足或无法回指来源，必须说明问题原因，并退回 active specs、附件、资产原文和临时核对动作。

## 8. Scenario 识别

命中以下任一信号时，可进入本文候选流程：

1. 用户说“安装 LDVH 入口”“接入 Codex/Claude/Trae”“让环境读取 LDVH Rules”；
2. 用户指出入口规则之外还缺少运行保障能力，要求说明环境中还需要落地什么；
3. 用户要求生成、检查或修复薄引用文本；
4. 用户要求把候选文本写入 AGENTS、instructions、config、hooks 或等价入口；
5. 用户要求确认某环境是否已经能读取 LDVH 入口、触发 Hook、调用 Skill 或执行必要 Code 检查；
6. `assurance-report`、`assurance-plan` 或 `ldvh-assurance-check` 暴露运行投影、环境承接、Workflow/Skill、Code/Test 或 Human Gate 缺口，而用户要求推进环境落地；
7. `capability-environment` 显示固定资产为 `not_claimed`，而用户要求推进环境落地；
8. 30 或其它流程把问题分流为环境入口安装、Hook 接入、能力保障或支持声明。

以下情况不得进入本文作为 active 流程执行：

1. 只因为本文文件存在就执行环境写入；
2. 只因为用户说“应该装好了”就声明环境已支持；
3. 未生成来源要求投影就直接套用 AGENTS、Hook 或 Skill 静态清单；
4. 未定位目标入口、未保护已有内容或无退出方式时执行写入；
5. 将本文 `candidate` 状态解释为已生效行动编排。

## 9. 执行流程

1. 确认本文状态；若仍为 `candidate`，只能作为候选草案参考，不能宣称 active 执行。
2. 明确目标环境类型、目标工作区、目标项目边界和用户要求的接入深度。
3. 聚合来源保障要求：
   - 优先运行 `assurance-report`、`assurance-plan` 和 `ldvh-assurance-check`；
   - 若 Code 不可用或输出不足，回读 active specs 的 `规范保障要求` 表，并记录问题原因；
   - 不得用 AGENTS、Hook、Skill 或固定资产清单替代来源要求。
4. 判断每条来源要求的接管状态：
   - active 行动编排接管；
   - candidate 成员或建议接管；
   - 待接管缺口；
   - 临时核对动作；
   - 不适用当前环境落地。
5. 按 06.Att.05 和 06.Att.06 生成运行时承载与缺口分流：
   - 能由 Rules、Skill、Agent、Hook 或环境入口承载的，继续映射到固定资产或候选资产；
   - 属于 Code、Web、测试、CI、事实源或 Human Gate 的，记录外部归口和环境中的可见入口；
   - 无承载物、不可发现、权限不足或未验证的，记录缺口和问题分流位置。
6. 运行或读取固定资产检查，确认目标资产自描述和登记一致，但不得把固定资产存在解释为环境已安装。
7. 生成目标环境落地投影。每个投影行必须回指来源要求、接管状态、承载方向、当前资产、环境渲染、验证方式、缺口分流和禁止声明。
8. 仅对投影中需要环境承载的项判断接入方式：
   - 薄引用优先；
   - 软链、安装脚本或可复查配置次之；
   - 受控复制全文必须进入 Human Gate，并记录复制原因、来源版本、更新方式、退出方式和漂移检查方法；
   - 无稳定入口时标记为会话提示、临时核对动作或显式待确认。
9. 生成候选薄引用、配置说明、手动命令或临时核对步骤。候选薄引用必须使用真实绝对路径，不得保留模板变量。
10. 若用户只要求候选文本，交还投影摘要、文本、放置位置、检查步骤和禁止声明。
11. 若用户要求 AI 代写，先确认 Human Gate 记录、目标入口、已有内容保护和退出方式。
12. 受控写入后执行部署后检查：入口是否存在、目标资产是否可读、薄引用是否未复制正文、Hook/Skill/Code 命令是否按投影方式可检查。
13. 输出声明完成前证据摘要，列出已承载项、失败项、未承接项、未验证项、外部归口项和禁止声明。
14. 判断是否需要事实源回写、Spark/ADR/Pitfall/WorkCase 分流或 Git commit records 追溯。

## 10. 执行中问题分流与失败暂停

| 问题 | 分流 |
|---|---|
| 未能聚合 active specs 保障要求 | `blocking` 或原文回读，不得生成静态落地清单 |
| 投影行无法回指来源要求 | `blocking`，回到来源 specs、03、06.Att.05 和临时核对动作 |
| 接管状态无法判断 | 标记为 `待接管缺口` 或 `临时核对动作`，不得声称 active 接管 |
| 承载方向不属于 06.Att.05 或外部归口不清 | 回到 06.Att.05、06.Att.06 和对应构成要素规范 |
| Code 聚合输出不足或互相冲突 | 记录问题诊断，回读 active specs 和资产原文 |
| 目标环境入口不存在或不可确认 | `blocking` 或 `待确认`，不得写入 |
| 已有用户配置可能被覆盖 | Human Gate，先保护原内容并定义退出方式 |
| 薄引用复制了 Rules 或 specs 正文 | `blocking`，改为薄引用 |
| 目标资产不可读或路径不是真实绝对路径 | `blocking`，修正路径或记录问题原因 |
| Hook 事件、权限、trust 或命令来源不明 | `待确认` 或 `临时核对动作`，不得声明 Hook 生效 |
| 当前环境缺少稳定入口 | `临时核对动作`，可输出会话提示或手动步骤 |
| 本次检查失败但有长期价值 | 分流为 Spark、Pitfall、ADR 或 WorkCase |
| 用户要求声明完整支持但证据不足 | Human Gate；不得用推测替代证据 |

同一适配检查连续失败，或失败原因无法区分为权威资产问题、环境适配问题还是本地配置问题时，应暂停并请求 Human 方向校正。

## 11. Human Gate

以下情况必须暂停并等待 Human 确认：

1. 写入、覆盖、删除或迁移用户环境入口、项目规则、工作区规则或等价配置；
2. 覆盖用户已有 AGENTS、instructions、config、hooks、Skill、Agent、Hook 或等价入口；
3. 启用自动触发、危险权限、跨工作区写入或 Hook 阻断；
4. 受控复制 LDVH 能力资产全文，而不是薄引用、软链、安装脚本或可复查配置；
5. 声明某环境完整支持 LDVH、某能力已部署生效、Hook 已稳定运行或环境原生支持；
6. 将一次本地适配检查结果写成长期环境状态；
7. 接受环境入口、运行时扩展承载物、适配措施或能力资产长期能力缺口；
8. 将本文从 `candidate` 升级为 `active`，或改变 Context、Scenario、Gate、回写触发、能力边界。

本草案创建时的 Human Gate 记录：

| 字段 | 记录 |
|---|---|
| 时间 | 2026-06-24 当前对话 |
| 决策 | Human 在审阅候选方向后要求“推进”，授权形成非 active 成员主文件草案 |
| 范围 | 新增 `specs/32-environment-entry-adaptation-环境入口落地与适配检查.md` draft/candidate，并在 01 目录登记为非 active 成员 |
| 约束 | 不授权 active 化；不授权写入用户环境入口；不声明任何环境完整支持或能力已部署；写入后必须运行登记、能力环境和相关 specs 检查 |

## 12. Skill 和 Agent 调度

本文不要求固定 Skill 或 Agent。

可选调度边界：

| 能力 | 可做 | 不可做 |
|---|---|---|
| Skill | 复用候选文本生成、配置片段检查或提交准备 | 不替代 Human Gate，不新增环境规则 |
| Agent | 对高风险环境配置、Hook 权限或跨环境适配做独立审查 | 不直接写入环境，不独立决定部署完成 |

所有 Skill 或 Agent 输出必须交还主控 AI。主控按 03、06、07、08 和 Human Gate 判断是否继续。

## 13. Code、命令和 Web 协作适配

本文主要消费以下 Code 命令：

| 命令 | 用途 | 边界 |
|---|---|---|
| `python3 code/specs_validate.py assurance-report --format text` | 聚合 active specs 的规范保障要求、状态和建议回写方向 | 启发式派生报告，不替代来源 specs |
| `python3 code/specs_validate.py assurance-plan --format text` | 汇总保障缺口、能力状态、写入需求、Human Gate 和回写目标 | 只读计划视图，不自动创建 WorkCase 或授权写入 |
| `python3 code/specs_validate.py ldvh-assurance-check --format text` | 生成 LDVH 部署与适配检查派生报告，暴露部署基线和剩余缺口 | 派生报告，不声明现场环境已接入 |
| `python3 code/specs_validate.py deployment-entries` | 检查固定运行时扩展登记和资产自描述一致性 | 不说明环境已安装 |
| `python3 code/specs_validate.py capability-environment` | 投影固定能力资产来源、同步责任、验证链和环境落地边界 | 只读矩阵，不写环境入口 |
| `python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text` | 查看固定运行时扩展入口层候选和诊断 | 不替代资产原文 |
| `python3 code/specs_validate.py preflight --target-path <path>` | 写入 specs、Rules 或配置候选前提示 Gate 和影响 | 不授权写入 |
| `python3 code/hook_dispatch.py run <event> ...` | 对 Hook registry 进行等价手动检查 | 不证明环境 Hook 已自动接入 |

`capability-environment` 只能说明固定能力资产与环境落地边界；`assurance-report` 和 `assurance-plan` 才能作为来源保障要求和缺口聚合输入。两者都不是事实源，也不授权写入。

Web 可展示环境适配状态、投影行、证据和风险，但不得维护第二事实源，不得替代主控判断或 Human Gate。

## 14. 事实源回写与证据留存

本文候选流程完成后，过程输出至少应交还：

1. 环境类型和目标工作区；
2. 本次使用的保障要求聚合来源和问题状态；
3. 环境落地投影摘要，至少列出来源要求、接管状态、承载方向、当前资产、环境渲染、验证方式和缺口分流；
4. 用户选择或确认的环境入口；
5. 对应 LDVH 承载物、Code 命令或临时核对动作；
6. 接入方式；
7. 检查时间；
8. 检查方式和命令；
9. 检查结论；
10. 失败项、未承接项、未验证项、外部归口项；
11. 禁止声明；
12. 是否发生 Human Gate，以及最小记录；
13. 剩余风险和后续分流。

需要长期追溯时，应按内容性质回写：

| 内容 | 回写位置 |
|---|---|
| 候选计划或未完缺口 | Spark |
| 高影响环境取舍 | ADR |
| 可复用失败经验 | Pitfall |
| 工作闭环、验证证据或关闭判断 | WorkCase |
| 规范、Rules、Skill、Hook、Code 或测试修改 | 对应 Git 文件事实源和 Git commit records |

不得把聊天摘要、临时命令输出、环境观察或未通过 Human Gate 的授权记录直接写成稳定事实。

## 15. 环境适配边界

本文只候选编排保障要求到环境入口的落地投影和适配检查，不负责定义外部环境产品能力。

LDVH 提供插件方式和 Rules 方式两种接入路径，由用户根据环境 AI Hook 能力选择。具体适配需回到 `specs/06-运行时扩展规范.md` §7 判断。

环境入口、薄引用、软链、配置片段、安装副本、Hook 配置和用户本地 instructions 都属于部署或适配层。它们不得反向改变 LDVH 权威资产字段契约、来源规范、保障要求、接管状态、状态闭集或 Human Gate。

同一个来源保障要求可以投影到多个环境承载方式，也可以只形成外部归口或临时核对动作。环境承载方式变化时，必须重新生成投影，不得手工保留旧清单。

## 16. 行动特有可测试性锚点

| 锚点 | 正例 | 反例 |
|---|---|---|
| Scenario | 用户要求把 LDVH 接入 Codex，并要求说明入口之外还缺哪些保障能力 | 普通 Rules 文案修改误进入本文 |
| Context | 读取 assurance-report、assurance-plan、06 §5/§7、06.Att.05/06、目标 Rules 和 capability-environment | 只凭聊天记忆生成入口 |
| 动态投影 | 每个环境落地项均回指来源要求、接管状态和承载方向 | 直接列 AGENTS、Hook、Skill 静态清单 |
| Gate | 覆盖用户 AGENTS 前暂停确认 | 静默覆盖已有入口 |
| 薄引用 | 只包含入口路径、恢复后重读提示和管理段标记 | 复制 specs 或 Rules 正文 |
| 环境声明 | 输出“本次检查通过/失败/待确认” | 声明该环境完整支持 LDVH |
| Hook 检查 | 手动运行 dispatcher 并说明不代表自动 Hook 已安装 | 仅因 registry 存在宣称 Hook 生效 |
| 证据 | 交还投影摘要、环境、入口、承载物、检查方式、结论、失败和未承接项 | 只说“已经落地” |

## 17. 规范保障要求

本节不生成新的规范保障要求，只说明本文候选如何承接来源要求。本文当前为 `candidate`，以下承接关系不得被解释为 active 执行入口。

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 入口可见要求 | 回指 01 §12、06 §7 和 06.Att.09 至 06.Att.14；本文只把 active specs 的 `规范保障要求` 聚合为环境落地投影输入，并编排投影后的入口生成、受控写入、适配检查和声明边界 | 本文 §7-§15、`assurance-report`、`assurance-plan`、06 附件、Human Gate、原文回读 | 环境适配 | 规范保障要求、环境入口、薄引用、Hook 接入、受控复制或声明边界变化时 |
| 工作流程接管要求 | 回指 03 §5、§10、§12 和 06 §5；本文保持 draft/candidate，不作为 active 流程；接管状态、承载矩阵和能力缺口分流只作为投影输入 | 本文身份块、§7-§10、06.Att.05、06.Att.06、Gate 记录、待补齐事项 | 行动编排治理 | 决定是否升级 active、改变编号、改变承接范围，或来源要求需要 Rules、Skill、Agent、Hook、Code、Web、测试、Human Gate 或临时核对动作承载时 |
| 确定性执行要求 | 回指 04 Code 确定性执行边界和 08 失败阻断要求；本文消费 Code 只读聚合和检查输出，不用工具成功替代事实源、Human Gate 或验证声明 | 本文 §13、§16、`assurance-report`、`assurance-plan`、`ldvh-assurance-check`、`deployment-entries`、`capability-environment`、部署检查、临时核对动作 | Code 诊断协作 | Code 命令、诊断字段、投影能力、问题状态或接入完成声明变化时 |
| 上位约束承接要求 | 回指 07 §7、§13；环境观察和工具输出只有写入对应事实源并可追溯后才成为稳定事实 | 本文 §14、Git commit records、事实对象分流 | 事实源回写 | 检查结论、风险或 Human Gate 记录需要长期追溯时 |

## 18. 行动编排成员检查要求

检查本文至少包括：

| 检查项 | 标准 |
|---|---|
| 身份块 | 同时包含 `v2_spec` 和 `v2_action_member` |
| 状态分工 | `v2_spec.status=draft`，`v2_action_member.collection_status=candidate`，不得当作 active 流程 |
| 锚点 | Scenario、Context、Gate、执行、问题分流、回写、证据和可测试性锚点可定位 |
| 动态输入 | Context 和执行流程从 specs 保障要求、接管状态、06.Att.05/06 和 Code 聚合视图生成投影 |
| 来源承接 | `assurance_takeover` 回指 01、03、04、06、07、08 |
| 能力映射 | `capability_assets` 只登记流程能力需求和映射，不声明部署完成；Code 聚合命令不替代事实源 |
| 投影输出 | 每个环境落地项可回指来源要求、接管状态、承载方向、当前资产、环境渲染、验证方式、缺口分流和禁止声明 |
| 薄引用边界 | 候选入口不复制 specs、Rules 或资产正文 |
| Human Gate | 环境写入、覆盖、自动触发、支持声明和 active 化均被阻断 |
| 验证入口 | assurance-report、assurance-plan、ldvh-assurance-check、deployment-entries、capability-environment、runtime_extensions 和临时核对动作可执行 |

## 19. 待补齐事项

1. 需要 Human 决定本文是否从 `candidate` 升级为 `active`，升级前不得执行为默认流程；
2. 需要确认是否由 Code 增加正式的环境落地投影命令，把 `assurance-report`、`assurance-plan`、06.Att.05/06、固定资产和环境候选矩阵合成为机器可读投影；
3. 需要确认是否由 Code 增加环境入口候选文本、薄引用正文、AGENTS 指向、Hook 配置和投影行回指的机械检查；
4. 需要确认 Codex App 当前版本的 AGENTS、config、hooks、trust、matcher 和 Hook 返回语义；
5. 需要评估本文 active 后是否触发 `rules/LDVH-ENTRY.md` 和 `rules/LDVH-ENTRY.md` 的入口表达同步；
6. 需要补充动态投影、静态清单反例、入口写入、Hook 检查和验证声明的正反样例测试，并按 08 确认验证声明边界；
7. 需要根据 `spark-0022` 和 `spark-0024` 判断是否形成后续 WorkCase。
