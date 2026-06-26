# record-object-routing-recall-记录对象归口与召回

```yaml
v2_spec:
  spec_id: "36"
  spec_kind: "member_spec"
  title: "record-object-routing-recall-记录对象归口与召回"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs/36-record-object-routing-recall-记录对象归口与召回.md"
  created: "2026-06-25"
  updated: "2026-06-25"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "候选定义 AI 如何在创建或消费 Spark、ADR、Pitfall 三类记录对象前执行归口、查重、召回、冲突识别、Human Gate 和分流出口判断"
  scope: "Spark、ADR、Pitfall 的入库分流、创建前召回、出库召回、状态使用边界、更新/合并/并列/新建/归档/废弃建议，以及转 Study 研究行动或 WorkCase 行动承接的出口协调"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/03-行动编排规范.md"
  related_specs:
    - "specs/07-事实源边界与Git追溯规范.md"
    - "specs/20-Spark-火花.md"
    - "specs/21-WorkCase-工作项.md"
    - "specs/22-ADR-决策.md"
    - "specs/23-Pitfall-踩坑经验.md"
    - "specs/24-Study-研究报告.md"
    - "ldvh-base/sparks/spark-0028-record-object-routing-recall-orchestration.yaml"
    - "ldvh-base/workcases/workcase-0010-record-object-routing-recall-orchestration.yaml"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "record_object_routing_recall_candidate"
    - "assurance_takeover"
    - "capability_assets"
  migration_status: "not_migrated"
```

```yaml
v2_action_member:
  spec_id: "36"
  kind: "action_process"
  name_en: "record-object-routing-recall"
  name_zh: "记录对象归口与召回"
  collection_status: "candidate"
  canonical_path: "specs/36-record-object-routing-recall-记录对象归口与召回.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover:
    - "source_spec=specs/03-行动编排规范.md; requirement=保障需求生成要求; scope=把记录对象归口、召回、冲突和分流这类反复发生的多步骤判断收束为候选行动闭环"
    - "source_spec=specs/20-Spark-火花.md; requirement=工作流程接管要求; scope=Spark 创建、分流、废弃、多线并行和 Study 关联前的归口与 Human Gate 判断"
    - "source_spec=specs/22-ADR-决策.md; requirement=工作流程接管要求; scope=长期决策候选升级、active ADR 冲突、归档/废弃和规范吸收前的召回判断"
    - "source_spec=specs/23-Pitfall-踩坑经验.md; requirement=工作流程接管要求; scope=已解决可复用经验沉淀、active Pitfall 召回和核心经验改写前的 Gate 判断"
    - "source_spec=specs/24-Study-研究报告.md; requirement=对象边界要求; scope=研究行动出口必须交给 Study 编排，但创建 Study 前先确认 Spark/ADR/Pitfall 承接对象"
    - "source_spec=specs/21-WorkCase-工作项.md; requirement=行动承接要求; scope=明确目标、成功标准、验证和关闭判断时转 WorkCase 编排"
  capability_assets:
    - "type=code; path=code/fact_cli.py search; purpose=按关键词、对象 ID、来源、规范路径和关联对象召回已有 Spark/ADR/Pitfall; status=required"
    - "type=code; path=code/fact_cli.py show; purpose=读取候选承接对象和召回对象原文摘要; status=required"
    - "type=code; path=code/specs_validate.py knowledge-map; purpose=在可用时辅助定位关联规范、对象和影响范围; status=optional"
    - "type=human_gate; path=current_conversation; purpose=冲突、升级、废弃、关键字段改写或改变长期边界时由 Human 确认; status=required"
  code_consumption:
    - "action_member_identity"
    - "action_member_anchors"
    - "record_object_routing_recall_candidate"
    - "assurance_takeover"
    - "capability_assets"
```

> 文件状态：本文是 draft 候选行动编排成员主文件，当前 `collection_status=candidate`。它不是 active 行动编排，不得被 Rules、Skill、Agent、Hook、Code、Web 或 AI 默认当作已生效流程执行。
> 当前用途：为 `workcase-0010` 的记录对象归口、沉淀与召回形成可审阅草案，供 Human 后续决定是否升级、拆分、合并或废弃。

## 1. 本文解决的问题

本文候选定义 AI 遇到输入、发现、判断、失败、经验线索或长期规则线索时，如何先判断是否需要长期记录，再归口到 Spark、ADR 或 Pitfall，避免重复创建、错误升级、遗漏 active 决策、忽略踩坑经验或把临时讨论误写成稳定事实。

本文拟解决：

1. 创建新 Spark、ADR、Pitfall 前如何召回已有对象；
2. 如何判断不入库、更新旧对象、合并、并列、新建、归档、废弃或进入 Human Gate；
3. 当前任务开始、计划、关闭或修改规范/Rules/行动编排前如何出库召回相关记录对象；
4. 如何区分召回对象可追溯、可参考和可作为当前执行依据的状态边界；
5. 如何把研究产物出口交给 Study 编排，把明确行动出口交给 WorkCase 编排。

本文不定义 Spark、ADR、Pitfall、WorkCase 或 Study 的字段契约、状态机、实例写入格式或验收规则；这些以 active 20-24 为准。本文不执行 Study 正文产出，也不推进 WorkCase 执行。

## 2. 上位依据

本文承接 `specs/03-行动编排规范.md` 的候选成员机制、Context、Scenario、Gate、执行分流、证据和能力边界。

本文承接 `specs/20-Spark-火花.md`、`specs/22-ADR-决策.md` 和 `specs/23-Pitfall-踩坑经验.md` 的对象准入、状态使用、Human Gate 和事实源边界。

本文承接 `specs/21-WorkCase-工作项.md` 和 `specs/24-Study-研究报告.md` 的出口边界：WorkCase 是行动承接，Study 是研究行动产物。Study 不能作为无承接对象的独立入口。

本文承接 `specs/07-事实源边界与Git追溯规范.md` 的过程输出、事实源回写和 Git 追溯边界。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的行动编排。

正向价值判断：

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 用创建前召回和出库召回减少遗漏已有记录 |
| V2 可行动理解 | 把记录需求、对象归口、状态使用和出口分流组织为同一候选闭环 |
| V3 正确判断 | 避免把 Study、WorkCase 混成 Spark/ADR/Pitfall 同级记录分支 |
| V5 门禁识别 | 同主题冲突、active ADR 冲突、核心 Pitfall 推翻和长期边界变化时进入 Human Gate |
| V7 证据沉淀 | 让更新、合并、并列、新建、废弃和分流理由回到对象事实源或 WorkCase |
| V8 可靠回写 | 过程输出按 07 判断后写回对应事实源并由 Git 追溯 |

反模式：

| 反模式 | 本文必须阻止 |
|---|---|
| 不查重直接新建对象 | 新建前必须召回和比较 |
| 用终态对象作为当前执行依据 | archived、deprecated、resolved、discarded 只能追溯或辅助判断 |
| 把 Study 当成无承接记录的独立入口 | Study 创建前必须有 Spark、ADR 或 Pitfall 承接对象；缺失时优先 Spark |
| 用行动编排重定义事实模型 | 本文只编排判断，不复制 20-24 字段和状态规则 |
| 用知识地图替代事实源 | 知识地图只辅助导航、召回和诊断 |

## 4. 行动定位与适用场景

本文候选定位为 Spark、ADR、Pitfall 三类记录对象的归口与召回行动。记录对象在本文中是本候选编排的局部术语，不否认 WorkCase 和 Study 也是事实模型对象。

适用场景：

1. AI 准备创建 Spark、ADR 或 Pitfall；
2. AI 在执行中发现可能需要长期记录的输入、风险、缺口、决策或经验；
3. 当前任务涉及长期规则、事实源边界、重复失败、规范/Rules/Skill/行动编排修改；
4. WorkCase 计划、执行、结果自检、结果复核或关闭前需要召回相关记录；
5. 研究行动可能产出 Study，且需要先确认 Spark、ADR 或 Pitfall 承接链。

不适用场景：

1. 已明确要执行 WorkCase 生命周期时，应转候选 35 或 active 21 的临时核对动作；
2. 已完成研究报告写作时，应转候选 34 或 active 24 的临时核对动作；
3. 只准备 Git commit 时，应按 active 31；
4. 只判断环境入口落地时，应按 candidate 32 或 06 临时核对动作。

## 5. 准入条件

进入本文候选流程必须同时满足：

1. 当前问题可能需要创建、更新、召回或消费 Spark、ADR、Pitfall；
2. 能识别来源输入、主题、影响范围或相关对象；
3. 能读取 20、22、23 的准入、状态和 Human Gate 规则，必要时读取 21、24 出口规则；
4. 能通过对象原文、`fact_cli.py`、关键词搜索或知识地图辅助召回已有对象；
5. 不把本文 candidate 状态解释为 active 默认流程。

## 6. 事实源边界

| 内容 | 权威位置 |
|---|---|
| Spark 对象规则 | `specs/20-Spark-火花.md` 和 `ldvh-base/sparks/` |
| ADR 对象规则 | `specs/22-ADR-决策.md` 和 `ldvh-base/adrs/` |
| Pitfall 对象规则 | `specs/23-Pitfall-踩坑经验.md` 和 `ldvh-base/pitfalls/` |
| WorkCase 出口规则 | `specs/21-WorkCase-工作项.md` |
| Study 出口规则 | `specs/24-Study-研究报告.md` |
| 行动候选来源 | `ldvh-base/sparks/spark-0028-record-object-routing-recall-orchestration.yaml` 和 `ldvh-base/workcases/workcase-0010-record-object-routing-recall-orchestration.yaml` |

本文产生的召回列表、比较结论、分流建议和 Human Gate 待确认项默认是过程输出。只有写入对应对象、规范、WorkCase 或 Git commit records 后，才成为稳定事实。

## 7. Context 要求

进入本文候选流程时，主控 AI 应最小读取或查询：

1. 用户目标、当前任务事实源和可能关联对象 ID；
2. `specs/20-Spark-火花.md`、`specs/22-ADR-决策.md`、`specs/23-Pitfall-踩坑经验.md` 的对象定位、状态机、对象关系和 Human Gate；
3. 若可能转行动，读取 `specs/21-WorkCase-工作项.md` 的准入和 Human Gate；
4. 若可能转研究产物，读取 `specs/24-Study-研究报告.md` 的准入和对象关系；
5. 通过 `python3 code/fact_cli.py search <keyword>`、`show <id>` 或等价查询召回相关 Spark、ADR、Pitfall；
6. 必要时用知识地图辅助定位，但以对象原文和 active specs 为准。

## 8. Scenario 识别

以下信号进入本文候选流程：

| 信号 | 处理 |
|---|---|
| 准备创建 Spark、ADR 或 Pitfall | 先召回同主题对象并比较 |
| 用户输入长期偏好、规则、风险、缺口或经验线索 | 判断是否不入库、Spark、ADR、Pitfall、WorkCase 或 Study |
| 当前任务涉及规范、Rules、Skill、行动编排或事实源边界变化 | 召回 active ADR、active Pitfall 和 pending Spark |
| 重复失败、反直觉修复或经验可能复用 | 召回 Pitfall 和 Spark，判断是否已有经验或待消化线索 |
| 研究行动可能产出 Study | 检查是否已有 Spark、ADR 或 Pitfall 承接对象；缺失时优先 Spark |

## 9. 执行流程

1. 识别输入性质：当前信息是临时处理、未计划化线索、长期决策、已验证经验、研究产物还是明确行动目标。
2. 执行创建前召回：按主题、关键词、对象 ID、来源、相关规范、相关 WorkCase、相关 Study 和关联对象搜索已有 Spark、ADR、Pitfall。
3. 比较召回结果：比较主题、适用范围、来源证据、状态、结论或经验、是否已有稳定承接事实源。
4. 判断状态使用：active ADR 可作为当前优先决策补丁；active Pitfall 可作为规避经验；pending Spark 只是待消化入口；终态对象用于追溯、避免重复或判断吸收位置。
5. 选择处置闭集：不入库、更新旧对象、合并补充、并列保留、新建 Spark、新建 ADR、新建 Pitfall、归档/废弃建议、转候选 34、转候选 35 或进入 Human Gate。
6. 形成最小说明：说明为什么这样归口，召回了什么，是否有冲突，是否需要 Human Gate，后续应写回哪里。
7. 回写或交还：在授权范围内写入对应对象；未授权、冲突或高影响变化时暂停交还 Human。

## 10. 执行中问题分流与失败暂停

| 问题 | 分流 |
|---|---|
| 召回工具不可用或输出不可信 | 回到文件事实源和对象原文；记录工具限制 |
| 同主题对象结论冲突 | Human Gate |
| 已满足 WorkCase 准入 | 转候选 35 或 active 21 临时核对动作 |
| 已满足 Study 报告产物准入 | 先检查承接对象，再转候选 34 或 active 24 临时核对动作 |
| 尚未满足 ADR/Pitfall/WorkCase/Study 条件但有保留价值 | 倾向 Spark |
| 未解决、未验证问题想写 Pitfall | 暂停，不写 Pitfall；转 Spark 或 WorkCase |

不得把 blocking 问题弱化为候选对象。不得因召回结果很多而跳过比较。

## 11. Human Gate

以下情况必须评估 Human Gate：

1. 创建、删除、重命名 Spark、ADR 或 Pitfall；
2. 将 Spark、WorkCase 过程判断、Study 结论或对话输入升级为 ADR 或 Pitfall；
3. 同主题结论冲突，或与 active ADR 冲突；
4. 需要推翻、归档或改写 active Pitfall 的核心经验；
5. 改变长期规则、事实源边界、Human Gate 边界或后续 AI 执行取舍；
6. 将 pending Spark 分流、废弃，或修改 `resolved_to`、`description`、`evolution`、`priority`、关键关联；
7. 创建 Study 前没有 Spark、ADR 或 Pitfall 承接对象，需要先创建 Spark；
8. 将本文从 candidate 升级为 active，或改变本文管辖边界。

Human Gate 记录至少应说明对象、触发原因、影响范围、Human 决策、确认约束和后续回写位置。

## 12. Skill 和 Agent 调度

本文候选不要求固定 Skill 或 Agent。可选调度：

| 能力 | 用途 | 边界 |
|---|---|---|
| Agent | 对冲突对象、归口争议或升级判断做独立审查 | 输出交还主控，不替代 Human Gate |
| Skill | 未来可封装召回、比较和交还格式 | 不定义新对象规则 |

## 13. Code、命令和 Web 协作适配

Code 可提供对象列表、搜索、字段检查和知识地图导航。推荐命令：

| 命令 | 用途 | 边界 |
|---|---|---|
| `python3 code/fact_cli.py search <keyword>` | 召回相关工作对象 | 不替代对象原文 |
| `python3 code/fact_cli.py show <id>` | 查看对象详情 | 输出是读取辅助 |
| `python3 code/specs_validate.py knowledge-map ...` | 辅助定位相关规范和对象 | 不替代 active specs 或 Human Gate |

Web 未来可展示召回建议、冲突提示和待确认项，但不得维护第二事实源或绕过对象级 Human Gate。

## 14. 事实源回写与证据留存

应留存的证据包括：

1. 输入来源和归口理由；
2. 召回查询条件和召回对象；
3. 主题、范围、状态、证据和结论比较摘要；
4. 处置选择和未选择其它分支的理由；
5. Human Gate 记录或未触发理由；
6. 写回对象、WorkCase、Study、规范或 Git commit 追溯。

过程输出是否写入事实源，由 07 和对应对象规范判断。

## 15. 环境适配边界

本文不定义环境入口、Hook、Skill 安装或 Web 写入能力。需要在环境中默认提示记录对象归口时，应回到 06、30 或 32 的候选/active 边界，并在本文升级 active 前不得声明环境已接管。

## 16. 行动特有可测试性锚点

候选可测试性锚点：

| 锚点 | 应能检查 |
|---|---|
| 创建前召回 | 新建记录对象前存在召回和比较证据 |
| 状态使用 | 终态对象未被当成当前执行依据 |
| 出口分流 | Study 和 WorkCase 未混入 Spark/ADR/Pitfall 记录分支 |
| Study 承接链 | 创建 Study 前有 Spark/ADR/Pitfall 关联；缺失时优先 Spark |
| Human Gate | 冲突、升级、废弃、核心字段变更和长期边界变化未被静默跳过 |

## 17. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| Spark 工作流程接管要求 | 创建、分流、废弃、多线并行和 Study 关联前应召回、比较并识别 Human Gate | 本文候选、active 20、对象原文、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | Spark 对象规则、状态边界、Study 关联或关键字段 Gate 变化时 |
| ADR 工作流程接管要求 | 决策升级、active 冲突、归档/废弃和规范吸收前应召回并判断执行依据边界 | 本文候选、active 22、对象原文、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | ADR 准入、状态、升级路径或 active 执行依据边界变化时 |
| Pitfall 工作流程接管要求 | 已解决经验沉淀和 active Pitfall 使用/改写前应召回并判断经验适用范围 | 本文候选、active 23、对象原文、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | Pitfall 准入、核心字段、归档或吸收路径变化时 |
| Study 对象边界要求 | Study 作为研究产物出口，创建前必须有 Spark/ADR/Pitfall 承接对象，缺失时优先 Spark | 本文候选、active 24、候选 34、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | Study 关联字段、准入、关键依据或报告产物边界变化时 |
| WorkCase 行动承接要求 | 明确目标、成功标准、验证或关闭判断时转 WorkCase 行动承接 | 本文候选、active 21、候选 35、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | WorkCase 生命周期、审核字段、执行项或关闭确认规则变化时 |

## 18. 行动编排成员检查要求

检查要求：

1. `v2_spec.status=draft` 且 `v2_action_member.collection_status=candidate`；
2. 不得被 Rules、Skill、Agent、Hook、Code、Web 或 AI 默认当作 active 流程；
3. Context、Scenario、Gate、执行、问题分流、回写、证据和可测试性锚点可定位；
4. 不复制 20-24 字段契约或状态机；
5. 明确 Study 承接链和 Spark 优先入口；
6. 升级 active 前需 Human 决策和验证补齐。

## 19. 待补齐事项

1. 需要 Human 决定本文是否升级为 active、与 34/35 的边界如何协调、是否需要管理类编排共同讨论；
2. 需要后续 Code 诊断是否识别 `record_object_routing_recall_candidate` 消费入口；
3. 需要决定是否为召回比较建立专门命令、Web 视图或 Agent 审核模板；
4. `workcase-0009` 暂缓；仅在后续 WorkCase/行动承接编排讨论中作为并行执行能力参考。
