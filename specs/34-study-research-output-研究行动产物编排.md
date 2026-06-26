# study-research-output-研究行动产物编排

```yaml
v2_spec:
  spec_id: "34"
  spec_kind: "member_spec"
  title: "study-research-output-研究行动产物编排"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs/34-study-research-output-研究行动产物编排.md"
  created: "2026-06-25"
  updated: "2026-06-25"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "候选定义 AI 如何把调研、分析、核验或方案比较行动的稳定结果沉淀为 Study，并在创建 Study 前强制确认 Spark、ADR 或 Pitfall 承接链"
  scope: "研究行动准入、承接对象检查、缺失承接对象时的 Spark 优先入口、Study 写作边界、关联回写、后续分流和 Human Gate"
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
    - "specs/36-record-object-routing-recall-记录对象归口与召回.md"
    - "ldvh-base/workcases/workcase-0010-record-object-routing-recall-orchestration.yaml"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "study_research_output_candidate"
    - "assurance_takeover"
    - "capability_assets"
  migration_status: "not_migrated"
```

```yaml
v2_action_member:
  spec_id: "34"
  kind: "action_process"
  name_en: "study-research-output"
  name_zh: "研究行动产物编排"
  collection_status: "candidate"
  canonical_path: "specs/34-study-research-output-研究行动产物编排.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover:
    - "source_spec=specs/24-Study-研究报告.md; requirement=工作流程接管要求; scope=Study 创建、报告整理、吸收、引用和归档前的行动步骤、验证和 Gate"
    - "source_spec=specs/20-Spark-火花.md; requirement=Study 关联边界; scope=Study 不能单独完成 Spark 分流；创建 Study 前若无承接对象优先创建 Spark"
    - "source_spec=specs/22-ADR-决策.md; requirement=Study 作为决策依据边界; scope=Study 作为 ADR 关键依据时触发 Human Gate 和关联回写"
    - "source_spec=specs/23-Pitfall-踩坑经验.md; requirement=Study 作为经验证据边界; scope=Study 作为 Pitfall 来源或证据时不替代已解决、已验证的经验字段"
    - "source_spec=specs/21-WorkCase-工作项.md; requirement=Study 作为行动输入边界; scope=Study 输出产生明确行动目标时转 WorkCase 行动承接"
  capability_assets:
    - "type=code; path=code/fact_cli.py search; purpose=创建 Study 前召回 Spark/ADR/Pitfall 承接对象; status=required"
    - "type=code; path=code/fact_cli.py show; purpose=读取承接对象、既有 Study 或关联 WorkCase 摘要; status=required"
    - "type=code; path=code/fact_validate.py ldvh-base; purpose=Study 写入后校验 frontmatter、正文骨架和引用有效性; status=required"
    - "type=human_gate; path=current_conversation; purpose=创建 Study、作为关键依据、接受高影响不确定性或缺失承接对象时确认; status=required"
  code_consumption:
    - "action_member_identity"
    - "action_member_anchors"
    - "study_research_output_candidate"
    - "assurance_takeover"
    - "capability_assets"
```

> 文件状态：本文是 draft 候选行动编排成员主文件，当前 `collection_status=candidate`。它不是 active 行动编排，不得被 Rules、Skill、Agent、Hook、Code、Web 或 AI 默认当作已生效流程执行。
> 当前用途：为 Study 研究行动产物形成可审阅草案；核心边界是 Study 必须有 Spark、ADR 或 Pitfall 承接链，缺失时优先 Spark。

## 1. 本文解决的问题

本文候选定义 AI 在完成研究、资料分析、事实核验或方案比较后，如何判断是否应形成 Study，并如何在创建 Study 前确认承接对象，避免 Study 成为无来源、无议题承接、无后续分流的孤立报告。

本文拟解决：

1. Study 作为研究行动产物的准入判断；
2. 创建 Study 前必须检查关联 Spark、ADR 或 Pitfall；
3. 没有关联承接对象时，优先创建或转入 Spark 承接研究议题；
4. Study 写入后如何建立与 Spark、ADR、Pitfall、WorkCase 的引用和分流；
5. Study 作为关键依据、不确定性或高影响判断时如何进入 Human Gate。

本文不定义 Study frontmatter 字段、Markdown 正文骨架或状态机；这些以 active 24 为准。本文不直接执行 WorkCase，也不把 Study 结论升级为 ADR 或 Pitfall。

## 2. 上位依据

本文承接 `specs/03-行动编排规范.md` 的候选成员机制和过程输出边界。

本文承接 `specs/24-Study-研究报告.md`：Study 是稳定报告事实源，不是讨论过程、执行承接或决策承接。

本文承接 `specs/20-Spark-火花.md`：Study 可以关联 Spark，但不得作为 `resolved_to`；形成 Study 不等于 Spark 已完成分流。

本文承接 `specs/22-ADR-决策.md`、`specs/23-Pitfall-踩坑经验.md` 和 `specs/21-WorkCase-工作项.md`：决策、经验和行动目标分别进入对应事实源。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的行动编排。

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 通过承接对象和 Study 引用让后续 AI 定位研究报告 |
| V2 可行动理解 | 把研究问题、输入边界、报告产物和后续分流分开 |
| V3 正确判断 | 防止 Study 替代 Spark 演变、ADR 决策、WorkCase 执行或 Pitfall 经验 |
| V5 门禁识别 | 创建 Study、关键依据和高影响不确定性进入 Human Gate |
| V7 证据沉淀 | 把稳定报告写入 Study，并回写承接对象引用 |
| V8 可靠回写 | Study、承接对象和 Git 提交记录共同保留可追溯证据 |

反模式：

| 反模式 | 本文必须阻止 |
|---|---|
| 无承接对象创建 Study | 先召回 Spark/ADR/Pitfall；缺失时优先 Spark |
| Study 替代 Spark resolved | Study 只关联 Spark，不作为 Spark 的 `resolved_to` |
| Study 替代 ADR | 长期决策仍需 ADR 和 Human Gate |
| Study 替代 WorkCase | 明确目标、成功标准和验证应转 WorkCase |
| 复制外部资料原文 | 外部资料按 24 的 URL 和资料边界处理 |

## 4. 行动定位与适用场景

本文候选定位为研究行动产物编排，不是通用资料抓取流程。

适用场景：

1. AI 已完成一轮调研、核验、分析或方案比较，结果需要长期保留；
2. 报告会被 Spark、ADR、Pitfall 或 WorkCase 引用；
3. docs/studies 或临时资料已整理为稳定结论；
4. 当前议题需要报告正文承载，但不能把报告全文塞入 Spark；
5. 研究结果产生后续 WorkCase、ADR、Pitfall 或 Spark 分流。

不适用场景：

1. 尚未整理的资料摘录或命令输出；
2. 可直接进入 ADR、WorkCase、Pitfall 或 Spark 的短结论；
3. 外部资料原文副本；
4. 单次执行中无需长期复读的临时分析。

## 5. 准入条件

进入本文候选流程必须同时满足：

1. 存在一项研究行动或稳定报告候选；
2. 能识别研究问题、输入边界、关键发现、建议和后续分流；
3. 已召回或准备召回相关 Spark、ADR、Pitfall；
4. 缺少 Spark、ADR、Pitfall 承接对象时，优先转入 Spark 创建判断；
5. 不把本文 candidate 状态解释为 active 默认流程。

## 6. 事实源边界

| 内容 | 权威位置 |
|---|---|
| Study 模型、frontmatter、正文骨架、状态和 Human Gate | `specs/24-Study-研究报告.md` |
| Spark 承接议题和 Study 关联边界 | `specs/20-Spark-火花.md` |
| ADR 决策依据和升级边界 | `specs/22-ADR-决策.md` |
| Pitfall 经验证据和升级边界 | `specs/23-Pitfall-踩坑经验.md` |
| WorkCase 行动承接边界 | `specs/21-WorkCase-工作项.md` |

本文产生的报告草稿、资料摘要、研究建议和分流建议默认是过程输出。只有写入 Study、承接对象、WorkCase、规范或 Git commit records 后，才成为稳定事实。

## 7. Context 要求

进入本文候选流程时，主控 AI 应最小读取或查询：

1. 研究行动触发来源、用户意图或上游对象；
2. `specs/24-Study-研究报告.md` 的准入、对象关系、Human Gate、frontmatter 和正文骨架；
3. `specs/20-Spark-火花.md` 的 Study 关联和 `resolved_to` 禁止边界；
4. 如涉及决策、经验或行动，读取 22、23、21 的对应准入和 Gate；
5. 通过 `fact_cli.py search` 或对象原文召回 Spark、ADR、Pitfall；
6. 若无承接对象，回到候选 33 的 Spark 优先入口判断。

## 8. Scenario 识别

| 信号 | 处理 |
|---|---|
| 用户要求把调研结果沉淀为报告 | 进入 Study 准入和承接对象检查 |
| AI 完成研究并产生稳定结论 | 检查是否需要 Study，且先确认 Spark/ADR/Pitfall 承接 |
| Study 将作为 ADR、WorkCase 或 Pitfall 的关键依据 | 进入 Human Gate 和关联回写 |
| 当前议题只有报告，没有承接对象 | 优先创建 Spark 承接研究议题 |
| Study 结论产生明确执行目标 | 转 WorkCase 行动承接 |

## 9. 执行流程

1. 判断研究产物是否满足 Study 准入；不满足时留在当前上下文、docs 资料区或对应对象中。
2. 召回承接对象：搜索相关 Spark、ADR、Pitfall，必要时查看 WorkCase 或既有 Study。
3. 判断承接链：已有 Spark/ADR/Pitfall 时记录关联；没有时，先按候选 33 判断是否创建 Spark，通常优先 Spark 承接研究议题。
4. 整理报告边界：明确研究问题、输入与边界、关键发现、建议和后续分流。
5. 按 active 24 写入 Study frontmatter 和 Markdown 正文；不得在本文重定义字段。
6. 回写关联：在 Study 写入 `related_sparks`、`related_adrs`、`related_pitfalls`、`related_workcases`；必要时回写承接对象引用和 evolution。
7. 分流结论：决策进 ADR，行动进 WorkCase，已解决可复用经验进 Pitfall，待讨论议题进 Spark。
8. 验证并交还：运行事实源校验，记录证据、残留不确定性和 Human Gate 结论。

## 10. 执行中问题分流与失败暂停

| 问题 | 分流 |
|---|---|
| 找不到承接 Spark/ADR/Pitfall | 优先 Spark；需要 Human Gate 时暂停 |
| 研究结果未成稳定报告 | 不创建 Study，留在资料区或当前对象 |
| 报告含长期决策 | 转 ADR 判断，不在 Study 中伪装决策 |
| 报告含明确行动目标 | 转 WorkCase 判断 |
| 报告含未解决问题 | 转 Spark 或 WorkCase，不写 Pitfall |
| 外部资料边界不清 | 暂停补充来源边界或记录不确定性 |

## 11. Human Gate

以下情况必须评估 Human Gate：

1. 创建、删除、重命名或归档 Study；
2. 将 docs/studies、docs/sources、外部资料或对话调研结果提升为 Study；
3. 没有 Spark、ADR 或 Pitfall 承接对象，却准备创建 Study；
4. 将 Study 作为 ADR、WorkCase、Spark 或 Pitfall 的关键依据；
5. 接受报告中的高影响不确定性、残留风险或事实判断；
6. 大幅改写 Study `summary`、`conclusion` 或正文；
7. 将本文从 candidate 升级为 active。

## 12. Skill 和 Agent 调度

本文候选不要求固定 Skill。可选 Agent 可用于：

| 视角 | 用途 |
|---|---|
| 研究质量审查 | 检查输入边界、关键发现和结论是否足以形成 Study |
| 分流审查 | 检查结论是否应转 ADR、WorkCase、Pitfall 或 Spark |

Agent 输出必须交还主控，不得替代 Study 事实源或 Human Gate。

## 13. Code、命令和 Web 协作适配

推荐命令：

| 命令 | 用途 |
|---|---|
| `python3 code/fact_cli.py search <keyword>` | 召回承接对象和既有报告 |
| `python3 code/fact_cli.py show <id>` | 查看承接对象原文 |
| `python3 code/fact_validate.py ldvh-base --format text` | 写入后校验 Study 和引用 |

Web 未来可展示 Study 报告和承接对象关系，但不得直接创建、编辑、归档或删除 Study，除非对应规范和白名单先更新。

## 14. 事实源回写与证据留存

应留存：

1. 研究问题和触发来源；
2. Spark、ADR、Pitfall 承接对象检查结果；
3. 无承接对象时创建 Spark 或暂停的理由；
4. Study 文件路径、frontmatter、正文和 URL 边界；
5. 关联对象回写位置；
6. 后续分流建议；
7. Human Gate 记录、验证命令和 Git commit 追溯。

## 15. 环境适配边界

本文不定义资料抓取能力、浏览器能力、Web 编辑能力或环境入口。环境中需要暴露 Study 研究产物流程时，应先由 06、30 或 32 评估入口表达和部署边界。

## 16. 行动特有可测试性锚点

| 锚点 | 应能检查 |
|---|---|
| Study 准入 | 报告已具备稳定阅读价值 |
| 承接对象 | 创建前已检查 Spark/ADR/Pitfall |
| Spark 优先 | 无承接对象时未直接创建孤立 Study |
| 正文骨架 | Study 符合 active 24 正文要求 |
| 后续分流 | 决策、行动、经验和待议题未停留在 Study 中伪装完成 |

## 17. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| Study 工作流程接管要求 | Study 创建、报告整理、引用、吸收和归档应有承接对象检查、验证、证据和 Gate | 本文候选、active 24、对象原文、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | Study 准入、状态、正文骨架、URL 结构或关联字段变化时 |
| Spark Study 关联边界 | Study 只能作为 Spark 的关联报告，不得作为 Spark `resolved_to`，也不得单独完成 Spark 分流 | 本文候选、active 20、active 24、候选 33；未 active 前使用临时核对动作 | 行动编排治理 | Spark 与 Study 关系、`resolved_to` 规则或 Study 承接链边界变化时 |
| ADR 关键依据边界 | Study 可作为 ADR 输入或依据，但长期决策仍需 ADR 准入、Human Gate 和对象回写 | 本文候选、active 22、active 24、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | ADR 准入、Study 作为关键依据或决策升级边界变化时 |
| Pitfall 经验证据边界 | Study 可作为 Pitfall 来源或证据，但不替代已解决、已验证和规避策略字段 | 本文候选、active 23、active 24、Human Gate；未 active 前使用临时核对动作 | 行动编排治理 | Pitfall 准入、证据字段、Study 来源关系或经验升级边界变化时 |
| WorkCase 输入边界 | Study 可作为 WorkCase 资料输入，但明确行动目标仍需 WorkCase 承接 | 本文候选、active 21、active 24、候选 35；未 active 前使用临时核对动作 | 行动编排治理 | WorkCase 准入、Study 输入关系或后续行动分流边界变化时 |

## 18. 行动编排成员检查要求

检查要求：

1. `v2_spec.status=draft` 且 `v2_action_member.collection_status=candidate`；
2. 不得默认执行或被环境入口硬依赖；
3. 明确 Study 承接链和 Spark 优先入口；
4. 不复制 active 24 字段和正文契约；
5. 升级 active 前需 Human 决策、实例样例和 Code/Web 同步评估。

## 19. 待补齐事项

1. 需要 Human 决定本文是否升级 active，以及是否与记录对象编排合并或保持独立；
2. 需要决定 Study 创建前承接对象检查是否应机械化为 Code 诊断；
3. 需要补充正反样例：孤立 Study、Spark 关联 Study、Study 作为 ADR/WorkCase/Pitfall 输入；
4. 管理类编排需要与本文、33、35 一起讨论。
