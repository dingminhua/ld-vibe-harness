# workcase-action-carrying-工作项行动承接编排

```yaml
v2_spec:
  spec_id: "35"
  spec_kind: "member_spec"
  title: "workcase-action-carrying-工作项行动承接编排"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs/35-workcase-action-carrying-工作项行动承接编排.md"
  created: "2026-06-25"
  updated: "2026-06-25"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "候选定义 AI 如何把明确目标承接为 WorkCase，并围绕方案审核、Human 方案确认、执行、结果自检、结果复核和关闭确认组织行动"
  scope: "WorkCase 创建前对齐、记录对象召回、执行项组织、方案审核、执行推进、验证证据、结果复核、关闭确认、残留风险和后续分流"
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
    - "specs/31-git-commit-action-Git提交行动编排.md"
    - "specs/33-record-object-routing-recall-记录对象归口与召回.md"
    - "specs/34-study-research-output-研究行动产物编排.md"
    - "ldvh-base/workcases/workcase-0010-record-object-routing-recall-orchestration.yaml"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "workcase_action_carrying_candidate"
    - "assurance_takeover"
    - "capability_assets"
  migration_status: "not_migrated"
```

```yaml
v2_action_member:
  spec_id: "35"
  kind: "action_process"
  name_en: "workcase-action-carrying"
  name_zh: "工作项行动承接编排"
  collection_status: "candidate"
  canonical_path: "specs/35-workcase-action-carrying-工作项行动承接编排.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover:
    - "source_spec=specs/21-WorkCase-工作项.md; requirement=工作流程接管要求; scope=WorkCase 创建、方案审核、执行、结果自检、结果复核和关闭确认的行动承接"
    - "source_spec=specs/20-Spark-火花.md; requirement=Spark 分流为 WorkCase 边界; scope=Spark 中明确目标、成功标准或执行需求时转 WorkCase"
    - "source_spec=specs/22-ADR-决策.md; requirement=ADR 与 WorkCase 关系; scope=WorkCase 执行中产生长期决策时转 ADR，并召回 active ADR"
    - "source_spec=specs/23-Pitfall-踩坑经验.md; requirement=Pitfall 与 WorkCase 关系; scope=WorkCase 执行、验证或关闭中发现可复用经验时转 Pitfall"
    - "source_spec=specs/24-Study-研究报告.md; requirement=Study 作为 WorkCase 输入; scope=Study 作为资料输入时不替代 WorkCase 成功标准或验证证据"
    - "source_spec=specs/31-git-commit-action-Git提交行动编排.md; requirement=Git 提交行动衔接; scope=WorkCase 涉及事实源修改并需要提交追溯时转 active 31"
  capability_assets:
    - "type=code; path=code/fact_cli.py show; purpose=读取 WorkCase、来源 Spark、ADR、Pitfall 和 Study; status=required"
    - "type=code; path=code/fact_cli.py search; purpose=创建或执行 WorkCase 前召回相关记录对象; status=required"
    - "type=code; path=code/fact_validate.py ldvh-base; purpose=WorkCase 写入、状态流转、执行项和引用校验; status=required"
    - "type=action_member; path=specs/31-git-commit-action-Git提交行动编排.md; purpose=事实源修改完成后的 Git 提交行动; status=required_when_commit_needed"
    - "type=human_gate; path=current_conversation; purpose=创建 WorkCase、确认方案、改写目标/成功标准和关闭确认; status=required"
  code_consumption:
    - "action_member_identity"
    - "action_member_anchors"
    - "workcase_action_carrying_candidate"
    - "assurance_takeover"
    - "capability_assets"
```

> 文件状态：本文是 draft 候选行动编排成员主文件，当前 `collection_status=candidate`。它不是 active 行动编排，不得被 Rules、Skill、Agent、Hook、Code、Web 或 AI 默认当作已生效流程执行。
> 当前用途：为 WorkCase 行动承接形成可审阅草案；`workcase-0009` 暂缓，仅作为后续 WorkCase/行动承接编排讨论中的并行执行能力参考。

## 1. 本文解决的问题

本文候选定义 AI 如何把一个已经具备目标、范围、成功标准、验证或关闭判断需求的事项承接为 WorkCase，并在 WorkCase 生命周期内组织方案审核、Human 方案确认、执行、结果自检、独立结果复核和 Human 关闭确认。

本文拟解决：

1. 什么时候应从当前对话、Spark、Study、ADR 或 Pitfall 转 WorkCase；
2. 创建 WorkCase 前如何召回相关记录对象和研究产物；
3. WorkCase 创建后如何连续完成方案审核并进入 Human 方案确认；
4. 执行中如何更新执行项、验证证据、残留风险和后续分流；
5. 关闭前如何避免用执行完成替代结果自检、结果复核或 Human 关闭确认；
6. 涉及 Git 追溯时如何转 active 31。

本文不定义 WorkCase 字段契约、状态机或 `orchestration` 字段 schema；这些以 active 21 和授权附件为准。本文不激活并行执行编排，也不吸收 workcase-0009。

## 2. 上位依据

本文承接 `specs/03-行动编排规范.md` 的行动成员机制、主控调度、Gate 和过程输出边界。

本文承接 `specs/21-WorkCase-工作项.md` 的准入、状态机、方案审核、执行项、结果自检、结果复核和关闭确认规则。

本文承接 `specs/20-Spark-火花.md`、`specs/22-ADR-决策.md`、`specs/23-Pitfall-踩坑经验.md` 和 `specs/24-Study-研究报告.md` 的对象关系和分流边界。

本文承接 active 31：当 WorkCase 产生事实源修改并需要 Git 追溯时，提交行动由 31 承接。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的行动编排。

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 让 AI 识别明确行动目标应进入 WorkCase |
| V2 可行动理解 | 把目标、成功标准、执行项、验证和关闭分层 |
| V3 正确判断 | 防止用 Spark、Study 或聊天进度替代 WorkCase 生命周期 |
| V4 稳定执行 | 固化方案审核、执行、自检、复核和关闭确认节奏 |
| V5 门禁识别 | 创建、方案确认、目标变更和关闭确认进入 Human Gate |
| V7 证据沉淀 | 执行项、验证、复核和残留风险写回 WorkCase |
| V8 可靠回写 | 事实源修改通过 WorkCase 与 Git commit records 追溯 |

反模式：

| 反模式 | 本文必须阻止 |
|---|---|
| 当前对话中执行大量目标但不建 WorkCase | 满足准入时必须承接为 WorkCase |
| 执行项 done 就宣称关闭 | 仍需结果自检、结果复核和 Human 关闭确认 |
| 用 Study 当行动承接 | Study 是资料或报告输入，不承载执行状态 |
| 用 WorkCase 替代 ADR/Pitfall | 长期决策和可复用经验分流到对应对象 |
| 混入 workcase-0009 | 0009 只作为后续讨论参考，本轮不激活 |

## 4. 行动定位与适用场景

本文候选定位为 WorkCase 行动承接编排。

适用场景：

1. 用户目标需要跨会话、多个执行项、验证证据或关闭判断；
2. Spark 已经收敛出明确行动目标或成功标准；
3. Study、ADR 或 Pitfall 产生后续执行事项；
4. 当前任务需要子 Agent 审核、结果复核或 Human 方案确认；
5. 执行完成后需要进入关闭确认或提交追溯。

不适用场景：

1. 当前对话即可完成的小任务；
2. 尚未形成目标和成功标准的议题，应先 Spark；
3. 纯研究报告，应先 Study；
4. 纯长期决策，应 ADR；
5. 纯可复用经验，应 Pitfall。

## 5. 准入条件

进入本文候选流程必须同时满足：

1. 存在明确目标、范围、成功标准、验证证据或关闭判断需求；
2. Human 已决定或用户目标明确要求创建/推进 WorkCase；
3. 能读取 active 21 的准入、状态和 Human Gate；
4. 能召回相关 Spark、ADR、Pitfall、Study；
5. 不把本文 candidate 状态解释为 active 默认流程。

## 6. 事实源边界

| 内容 | 权威位置 |
|---|---|
| WorkCase 模型、状态机、字段和 Human Gate | `specs/21-WorkCase-工作项.md` |
| WorkCase 实例 | `ldvh-base/workcases/` |
| 来源 Spark、ADR、Pitfall、Study | active 20、22、23、24 和各自实例目录 |
| Git 提交行动 | `specs/31-git-commit-action-Git提交行动编排.md` |
| workcase-0009 | 暂缓；后续 WorkCase/行动承接编排讨论参考 |

本文产生的计划草案、执行摘要、审核提示和验证摘要默认是过程输出。只有写入 WorkCase、相关对象、规范或 Git commit records 后，才成为稳定事实。

## 7. Context 要求

进入本文候选流程时，主控 AI 应最小读取或查询：

1. 用户目标、范围、成功标准和约束；
2. `specs/21-WorkCase-工作项.md` 的准入、状态机、对象关系和 Human Gate；
3. 相关 Spark、ADR、Pitfall、Study 或规范原文；
4. 通过 `fact_cli.py search` 召回可能影响目标的 active ADR、active Pitfall、pending Spark 和相关 Study；
5. 若涉及事实源修改和提交，读取 active 31 的准入和验证要求；
6. 若需要并行执行能力，仅记录为后续讨论，不引用 0009 为当前流程。

## 8. Scenario 识别

| 信号 | 处理 |
|---|---|
| 用户要求推进一个可执行目标 | 判断 WorkCase 准入 |
| Spark 收敛为明确目标 | 转 WorkCase 创建判断 |
| Study 建议形成后续任务 | 转 WorkCase 创建判断 |
| WorkCase 执行项完成 | 进入自检/复核/关闭确认判断，不直接关闭 |
| 事实源修改完成且需要提交 | 转 active 31 |
| 用户提到并行执行编排 | 记录到后续讨论，0009 本轮不激活 |

## 9. 执行流程

1. 对齐目标：确认目标、范围、成功标准、约束、验证和关闭口径。
2. 召回上下文：召回相关 Spark、ADR、Pitfall、Study 和既有 WorkCase。
3. 判断准入：当前对话可完成则不建 WorkCase；满足 active 21 准入则创建或更新 WorkCase。
4. 组织方案：拆分执行项，定义输入引用、预期输出、状态和审核策略。
5. 方案审核：按 active 21 完成方案审核和主控处理记录。
6. Human 方案确认：进入 `human_plan_confirming`，等待 Human 确认后才能执行。
7. 执行推进：逐项更新执行项、阻塞、证据和分流；遇到范围变化退回方案审核或 Human Gate。
8. 结果自检：执行项完成后先填主控自检，不直接关闭。
9. 独立结果复核：按审核策略获取独立复核和主控处理记录。
10. Human 关闭确认：进入 `human_closure_confirming`，确认后按 active 21 关闭。
11. 提交追溯：需要 Git commit records 时转 active 31。

## 10. 执行中问题分流与失败暂停

| 问题 | 分流 |
|---|---|
| 目标、范围或成功标准变化 | 退回方案审核或 Human Gate |
| 发现长期决策 | 转 ADR 判断 |
| 发现已解决可复用经验 | 转 Pitfall 判断 |
| 发现待研究问题 | 转 Study 前先检查 Spark/ADR/Pitfall 承接 |
| 发现未计划化线索 | 转 Spark 判断 |
| 验证失败或证据不足 | blocking，修复或记录残留风险，不得关闭 |
| 需要提交但提交边界不清 | 转 active 31 的 Gate |

## 11. Human Gate

以下情况必须评估 Human Gate：

1. 创建、删除、重命名 WorkCase；
2. 确认 `human_plan_confirming` -> `executing`；
3. 改写目标、成功标准、执行编排或关闭判断；
4. 跳过未验证执行项或通过豁免关闭 WorkCase；
5. 合并、拆分或重新组织 WorkCase；
6. 将 WorkCase 从 `human_closure_confirming` 关闭为 `closed`；
7. 将本文从 candidate 升级为 active；
8. 将 workcase-0009 的并行执行能力并入本文或作为 active 流程。

## 12. Skill 和 Agent 调度

本文候选允许按 active 21 使用子 Agent 或第三方审核 Agent 执行方案审核和结果复核。Agent 输出必须写入 WorkCase 审核字段或由主控摘要处理后回写；不得替代 Human 方案确认或关闭确认。

本文不固定 Skill。未来可封装 WorkCase 创建、审核材料整理或结果复核格式，但不得定义 WorkCase 字段 schema。

## 13. Code、命令和 Web 协作适配

推荐命令：

| 命令 | 用途 |
|---|---|
| `python3 code/fact_cli.py show <workcase-id>` | 查看 WorkCase 当前状态 |
| `python3 code/fact_cli.py search <keyword>` | 召回相关记录和研究产物 |
| `python3 code/fact_validate.py ldvh-base --format text` | 写入后校验事实对象 |
| `python3 code/commit_validate.py --check-message ...` | 提交前预检，属于 active 31 |

Web 可展示 WorkCase 状态、执行项、验证、复核和待确认项；不得把 `human_closure_confirming` 展示为已关闭。

## 14. 事实源回写与证据留存

应留存：

1. 创建或不创建 WorkCase 的理由；
2. 召回的 Spark、ADR、Pitfall、Study；
3. 方案审核、Human 方案确认、执行项结果；
4. 验证证据、关闭证据和残留风险；
5. 主控自检、独立结果复核和主控处理记录；
6. Human 关闭确认；
7. 相关 ADR、Pitfall、Spark、Study 分流；
8. Git commit hash 或未提交原因。

## 15. 环境适配边界

本文不声明任何环境已支持 WorkCase 编排。环境入口、Hook、Skill、Agent 可发现性、并行执行能力或 Web 写入能力，均由 06、30、32 或后续管理类编排讨论。

## 16. 行动特有可测试性锚点

| 锚点 | 应能检查 |
|---|---|
| 准入判断 | 创建前能说明为什么需要 WorkCase |
| 召回上下文 | 执行前召回相关 Spark/ADR/Pitfall/Study |
| 状态流转 | 未跳过 active 21 的方案确认、自检、复核和关闭确认 |
| 证据完整 | 执行项、验证和复核材料可追溯 |
| 分流闭环 | ADR/Pitfall/Spark/Study 后续对象不被 WorkCase 吞并 |
| 提交衔接 | 事实源修改需要提交时转 active 31 |

## 17. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| WorkCase 工作流程接管要求 | WorkCase 创建、方案审核、执行、自检、复核和关闭确认应形成可恢复行动闭环 | 本文候选、active 21、对象原文、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | 21 状态机、审核字段、执行项、Human Gate 或关闭口径变化时 |
| Spark 分流为 WorkCase | Spark 中明确目标、成功标准、验证或关闭判断时应转 WorkCase 承接 | 本文候选、active 20、active 21、候选 33；未 active 前使用临时核对动作 | 行动编排治理 | Spark 分流规则、WorkCase 准入或多线承接边界变化时 |
| ADR 关系边界 | WorkCase 执行中产生长期决策时应转 ADR，不得只留在执行项摘要中 | 本文候选、active 21、active 22、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | ADR 准入、active 决策召回或 WorkCase 关联规则变化时 |
| Pitfall 关系边界 | WorkCase 执行、验证或关闭中发现已解决可复用经验时应转 Pitfall | 本文候选、active 21、active 23、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | Pitfall 准入、经验吸收、WorkCase 来源关系或结果复核边界变化时 |
| Study 输入边界 | Study 可作为 WorkCase 资料输入，但不替代 WorkCase 成功标准、执行项或验证证据 | 本文候选、active 21、active 24、候选 34；未 active 前使用临时核对动作 | 行动编排治理 | Study 输入关系、WorkCase 资料边界或后续分流规则变化时 |
| Git 提交行动衔接 | WorkCase 修改事实源并需要 Git 追溯时应转 active 31 | 本文候选、active 31、07、commit validator；未 active 前使用临时核对动作 | Git 追溯 | 31、07、commit message 契约或事实源追溯边界变化时 |

## 18. 行动编排成员检查要求

检查要求：

1. `v2_spec.status=draft` 且 `v2_action_member.collection_status=candidate`；
2. 不得默认执行或激活 workcase-0009；
3. 不复制 active 21 字段和状态机；
4. 明确与 33、34、31 的边界；
5. 升级 active 前需 Human 决策、管理类编排协调和正反样例。

## 19. 待补齐事项

1. 需要 Human 决定本文是否升级 active，以及是否与管理类编排共同讨论；
2. 需要后续讨论 workcase-0009 的并行执行能力是否作为本文能力资产、独立成员或继续暂缓；
3. 需要补充 WorkCase 创建、执行、关闭的正反样例；
4. 需要 Code/Web 评估是否增加 WorkCase 编排行动诊断或展示入口。
