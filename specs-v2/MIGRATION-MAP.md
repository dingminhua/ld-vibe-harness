# v1 to v2 migration map

```yaml
migration_map:
  status: coverage_control_draft
  active_fact_source: specs/
  canonical_path: specs-v2/MIGRATION-MAP.md
  purpose: "记录 v1 active 规范到 v2 写作区的覆盖去向、迁移状态、阻断条件和 Human 核对入口"
  rule: "本文只控制迁移覆盖，不替代 active specs/，不证明任何 v2 文档已经 active。"
  required_before:
    - "判断 v2 是否已经承接 v1 核心职责"
    - "宣称 00-08 已完整承接 v1 核心职责"
    - "规划 Rules/Skills/Agents/Hooks/Code/Web 默认入口切换"
```

> 文件状态：本文是 `specs-v2/` 的迁移覆盖控制文件，不是正式规范正文，不替代 active `specs/`。
>
> 本文中的去向只表示迁移覆盖目标和当前草案状态；每一项是否完成迁移，必须经对应 v2 规范或成员主文件的 Human 单篇核对后才能更新。

## 1. 用途

本文用于回答四个问题：

1. v1 每个 active 规范、子规范或成员规范由 v2 哪个文件承接；
2. 承接方式是迁入、合并、拆分、废弃还是后置；
3. 当前只是已映射、已起草、待 Human 核对，还是被前置缺口阻断；
4. v2 在未 active 前，哪些内容不能被 Rules、Skills、Hooks、Code、Web 或事实源写入流程默认消费。

本文不得用于：

1. 宣称 v2 已经完整迁移；
2. 绕过 `V1-UNDERSTANDING-GATE.md`；
3. 把 `specs-v2/` 文件作为 active 正式规范引用；
4. 把知识地图、Code 输出或本文表格当作新的事实源。

## 2. 填写口径

### 2.1 迁移动作闭集

| 动作 | 含义 |
|---|---|
| `migrate` | v1 规则主体迁入单个 v2 主规范或成员主文件 |
| `merge` | v1 规则并入某个 v2 主规范或其授权附件，不再保留独立主干编号 |
| `split` | v1 规则被拆到多个 v2 规范、成员主文件或附件 |
| `drop` | v1 内容经 Human 核对后废弃，不进入 v2 active 体系 |
| `defer` | v1 内容暂不迁入，保留明确后置条件 |
| `history_extract` | v1 退出 active 后作为历史记录，只提取仍有价值内容进入新事实源 |

### 2.2 覆盖状态闭集

| 状态 | 含义 |
|---|---|
| `mapped_pending_review` | 已有 v2 去向，但尚未形成可审正文或覆盖证据 |
| `drafted_pending_review` | v2 草案已存在，但仍需逐项覆盖核对 |
| `deferred_until_v2_requirement_plan` | 暂不按 v1 迁移，待 v2 各规范保障需求稳定后再制定行动编排候选计划 |
| `ready_for_human_review` | 已完成覆盖证据，等待 Human 单篇核对 |
| `human_confirmed` | Human 已明确确认该项迁移完成 |
| `deferred` | 经记录后置，尚不进入当前迁移主线 |
| `dropped_pending_review` | 计划废弃，但尚未经过 Human 确认 |

任何行在未取得 Human 明确确认前，不得填为 `human_confirmed`。

### 2.3 覆盖判断字段

| 字段 | 要求 |
|---|---|
| `v1 来源` | 必须指向 active `specs/` 文件 |
| `v1 职责` | 记录该文件在 v1 中承担的机制性职责 |
| `v2 目标` | 指向 v2 主规范、成员主文件、附件或后置处理对象 |
| `动作` | 必须使用 §2.1 闭集 |
| `状态` | 必须使用 §2.2 闭集 |
| `阻断/核对条件` | 写明继续迁移前必须检查的边界 |

## 3. v1 到 v2 覆盖矩阵

| v1 来源 | v1 职责 | v2 目标 | 动作 | 状态 | 阻断/核对条件 |
|---|---|---|---|---|---|
| `specs/00-LD-Vibe-Harness理念与纲要.md` | LDVH 为什么存在、AI 第一服务对象、V1-V10、运行闭环总体叙述 | `specs-v2/00-LDVH理念与价值标准.md`；运行闭环分别落入 02/03/07/08 | `split` | `human_confirmed` | 已确认原文关键表述保留；运行闭环、Markdown/YAML 承载倾向、保障要求和总纲一致性检查已明确下沉承接 |
| `specs/01-目录说明.md` | 目录规划、根文件定位、编号区间、入口定位 | `specs-v2/01-规范体系基础规范.md`、`specs-v2/README.md`、知识地图派生读取 | `split` | `human_confirmed` | 已确认由 01 的规范结构、当前目录登记、附件规则和 README 写作区入口共同承接；不恢复独立目录说明规范 |
| `specs/02-术语规范.md` | 术语推荐表达、不推荐表达和命名边界 | `specs-v2/01-规范体系基础规范.md`、`specs-v2/attachments/01.Att.02-术语表.md`、`specs-v2/attachments/01.Att.08-规范表达清单.md` | `merge` | `human_confirmed` | 已确认术语归入规范体系，附件只承载术语表和表达清单，不反向定义主规范原则 |
| `specs/03-文档基础规范.md` | 文档工作区、吸收规则、引用纪律、文档结构底线 | `specs-v2/01-规范体系基础规范.md`、`specs-v2/07-事实源边界与Git追溯规范.md` | `split` | `drafted_pending_review` | 核对吸收规则与过程输出回写边界的归口，不得被 01 或 07 静默吞并 |
| `specs/03.01-规范文档规范.md` | `ldvh_doc`、正式规范骨架、保障要求、Human Gate、Code 消费要求 | `specs-v2/01-规范体系基础规范.md`、`specs-v2/attachments/01.Att.03-规范保障要求类型表.md`、`specs-v2/attachments/01.Att.04-规范身份字段表.md` | `merge` | `human_confirmed` | 已确认 v2 必要章节、身份块、附件规则、保障要求、Human Gate 和 Code 消费边界由 01 承接 |
| `specs/03.02-事实模型文档规范.md` | 20-29 成员自描述、成员骨架、字段和状态锚点 | `specs-v2/02-事实模型基础规范.md`、`specs-v2/20-Spark-火花.md` 到 `24-Study-研究报告.md`、`specs-v2/attachments/02.Att.*` | `split` | `drafted_pending_review` | 核对 `ldvh_member` 到 `v2_fact_model_member` 的双读映射、锚点和 Code 派生集合 |
| `specs/03.03-行动编排文档规范.md` | 30-59 成员自描述、Context/Scenario/Gate/执行/证据锚点 | `specs-v2/03-行动编排规范.md` 定义生成规则；未来 `specs-v2/30-59` 成员由 v2 保障需求生成 | `defer` | `deferred_until_v2_requirement_plan` | v1 成员机制只作为参考；不得把 30-59 视为必须逐篇迁移 |
| `specs/03.04-管辖项目配置规范.md` | `LDVH-GOVERNED-PROJECTS.yaml` schema、项目命名空间、管辖边界 | `specs-v2/01-规范体系基础规范.md`、`specs-v2/04-Code确定性执行规范.md`、`specs-v2/06-运行时扩展规范.md` | `split` | `mapped_pending_review` | 核对管辖项目配置仍不得记录部署状态，不得默认接管用户 docs |
| `specs/04-规范保障与环境适配基础规范.md` | 保障机制、能力保障和环境适配基础框架 | `specs-v2/06-运行时扩展规范.md`，并与 `specs-v2/01-规范体系基础规范.md` 的保障要求章节配合 | `split` | `human_confirmed` | 已确认保障要求提出归 01，固定运行时扩展承载、环境入口、薄引用、适配检查和人工降级归 06，不吞并 Code/Web/行动编排实现责任 |
| `specs/04.01-规范保障声明规范.md` | 保障声明字段、保障要求类型、声明契约 | `specs-v2/01-规范体系基础规范.md`、`specs-v2/attachments/01.Att.03-规范保障要求类型表.md`、`specs-v2/attachments/01.Att.07-行动编排接管建议矩阵.md` | `merge` | `human_confirmed` | 已确认普通保障要求与建议行动编排实例的关系，不保留 AI 检查要求作为松口自由项 |
| `specs/04.02-LDVH能力资产与保障机制规范.md` | 能力资产登记、Rules/Skills/Agents/Hooks/Code/Web 边界 | `specs-v2/06-运行时扩展规范.md`、`specs-v2/04-Code确定性执行规范.md`、`specs-v2/05-Web信息同步规范.md` | `split` | `human_confirmed` | 已确认运行时扩展只登记固定 Rules/Skills/Agents/Hooks 承载物；Code/Web 是独立构成要素，不作为运行时扩展资产等同处理 |
| `specs/04.03-环境入口适配与部署规范.md` | 环境入口、薄引用、部署适配、适配检查 | `specs-v2/06-运行时扩展规范.md`、`specs-v2/attachments/06.Att.*` | `merge` | `human_confirmed` | 已确认开发环境不是 LDVH 构成要素；Codex 等外部环境只是接入与适配对象，适配检查结果不成为长期状态事实 |
| `specs/05-事实模型基础规范.md` | 事实模型通用规则、事实实例、回写与证据适配 | `specs-v2/02-事实模型基础规范.md`、`specs-v2/07-事实源边界与Git追溯规范.md` | `split` | `human_confirmed` | 已确认事实模型基础规则由 02 承接，02 不覆盖 v1 09 全局事实源原则；全局事实源仍由 07 单篇核对 |
| `specs/05.01-字段定义与语义规范.md` | 字段语义、公共字段和模型字段 owner 分层 | `specs-v2/02-事实模型基础规范.md`、`specs-v2/attachments/02.Att.01-字段注册表.md` | `merge` | `human_confirmed` | 已确认字段契约属于事实模型，公共字段语义和字段治理收口到 02 |
| `specs/05.02-字段内容与格式规范.md` | 字段内容格式、结构化表达和格式约束 | `specs-v2/02-事实模型基础规范.md`、`specs-v2/attachments/02.Att.01-字段注册表.md` | `merge` | `human_confirmed` | 已确认字段内容格式并入 02，作为字段内容表达规则而非独立权威域 |
| `specs/05.03-字段注册与消费规范.md` | 字段注册、消费元数据、Code/Web 字段消费 | `specs-v2/02-事实模型基础规范.md`、`specs-v2/attachments/02.Att.01-字段注册表.md`、`specs-v2/attachments/02.Att.06-字段矩阵诊断表.md` | `merge` | `human_confirmed` | 已确认字段注册表作为 02 附件存在，不反向定义具体模型字段存在性、必填性、状态条件或完整 schema |
| `specs/06-行动编排基础规范.md` | 行动编排通用规则、执行生命周期、过程输出、证据与保障接管 | `specs-v2/03-行动编排规范.md` 定义行动编排如何由规范保障需求生成、登记、执行和回写 | `defer` | `deferred_until_v2_requirement_plan` | 不按 v1 流程直接迁移；v1 06 只作为 v2 03 写作参考 |
| `specs/07-Code确定性执行实现规范.md` | Code 确定性解析、校验、聚合和实现边界 | `specs-v2/04-Code确定性执行规范.md` | `migrate` | `human_confirmed` | 已确认 v2-check 只读边界、双读策略、知识地图投影、受控写入前检查和测试回归入口由 04 承接 |
| `specs/08-Web信息同步实现规范.md` | Web 派生展示、DTO、轻写入白名单、Human-facing 状态 | `specs-v2/05-Web信息同步规范.md` | `migrate` | `human_confirmed` | 已确认 Web v2 暂不实施不等于契约丢失；DTO/API、Spark 轻写入白名单、Confirm UI、提交展示、知识地图展示和 Web 回归线由 05 承接，技术选型不进入 v2 义务 |
| `specs/09-事实源边界与承载规范.md` | 最终事实源、单一事实源、过程输出回写、承载介质 | `specs-v2/07-事实源边界与Git追溯规范.md` | `migrate` | `human_confirmed` | 已确认最终事实源、单一事实源、过程输出回写、历史记录提取、非事实源排除和事实承载介质由 07 承接，未被 02/03/04/05/06 局部规则替代 |
| `specs/10-Git提交规范.md` | Git commit records、commit message 契约、提交追溯 | `specs-v2/07-事实源边界与Git追溯规范.md`；AI 提交流程归未来 44 行动编排成员 | `split` | `human_confirmed` | 已确认 Git commit records 只做事实源修改追溯；commit message 契约、type/scope、body 条件和关联提交派生归 07，AI 提交流程归行动编排 |
| `specs/11-测试基础规范.md` | 测试治理、验证声明、测试证据和回归同步 | `specs-v2/08-测试基础规范.md` | `migrate` | `human_confirmed` | 已确认测试治理、验证声明、测试证据边界、失败阻断、等价验证、同步触发和 Code/Web/运行时扩展测试归属由 08 承接，当前验证入口不固化为长期技术选型义务 |
| `specs/20-Spark-火花.md` | Spark 事实模型成员 | `specs-v2/20-Spark-火花.md` | `migrate` | `human_confirmed` | 已确认 Spark 准入、事实源、状态机、Study 不作为 resolved_to、多线分流、字段契约、Human Gate 和 Web 快速创建白名单由 20 承接 |
| `specs/21-WorkCase-工作项.md` | WorkCase 事实模型成员 | `specs-v2/21-WorkCase-工作项.md` | `migrate` | `drafted_pending_review` | 核对工作项准入、orchestration 字段、证据、关闭和状态流转 |
| `specs/22-ADR-决策.md` | ADR 事实模型成员 | `specs-v2/22-ADR-决策.md` | `migrate` | `drafted_pending_review` | 核对决策准入、后果、吸收、替代和关闭规则 |
| `specs/23-Pitfall-踩坑经验.md` | Pitfall 事实模型成员 | `specs-v2/23-Pitfall-踩坑经验.md` | `migrate` | `drafted_pending_review` | 核对经验准入、复发风险、吸收和长期回流 |
| `specs/24-Study-研究报告.md` | Study 事实模型成员 | `specs-v2/24-Study-研究报告.md` | `migrate` | `drafted_pending_review` | 核对来源、frontmatter、吸收路径和归档边界 |
| `specs/30-action-orchestration-governance-行动编排创建审核与治理.md` | 行动编排创建、审核和治理流程 | 未来行动编排候选计划参考材料 | `defer` | `deferred_until_v2_requirement_plan` | 待 v2 各规范提出行动编排需求后，判断是否需要新的创建/审核/治理编排 |
| `specs/41-fact-model-audit-事实模型审核.md` | 事实模型审核行动编排 | 未来行动编排候选计划参考材料 | `defer` | `deferred_until_v2_requirement_plan` | 待 v2 02 与 20-29 提出保障需求后，判断是否需要事实模型审核编排 |
| `specs/42-specs-audit-规范审核.md` | 规范审核行动编排 | 未来行动编排候选计划参考材料 | `defer` | `deferred_until_v2_requirement_plan` | 待 v2 01 和各主规范提出保障需求后，判断是否需要规范审核编排 |
| `specs/43-assurance-readiness-audit-保障准备度审核.md` | 保障准备度审核行动编排 | 未来行动编排候选计划参考材料 | `defer` | `deferred_until_v2_requirement_plan` | 待 v2 06 和各规范保障要求稳定后，判断是否需要保障准备度审核编排 |
| `specs/44-git-commit-orchestration-Git提交编排.md` | AI Git 提交流程、提交前检查、证据和交还 | 未来行动编排候选计划参考材料；commit message 契约由 v2 07 承接 | `defer` | `deferred_until_v2_requirement_plan` | 待 v2 07 和运行时入口稳定后，判断是否需要新的 Git 提交编排 |

## 4. 行动编排候选计划后置规则

行动编排成员不按 v1 现有流程直接迁移。v2 行动编排应先由 v2 各规范提出的保障需求生成候选计划；v1 06、03.03、30、41、42、43 和 44 只作为参考材料。

v2 03 的职责是定义：

1. 规范保障需求如何提出行动编排需求；
2. 行动编排候选如何登记、去重、合并和排序；
3. 何时需要 Human Gate；
4. 何时需要 Code、Web 或运行时扩展承载；
5. 具体行动编排成员如何在 v2 active 后形成主文件、锚点、输入、输出、证据、回写和测试要求。

具体 30-59 行动编排成员应在 v2 正式生效或至少 v2 各规范保障需求稳定后规划。候选计划至少应记录：

| 字段 | 要求 |
|---|---|
| 来源规范 | 哪篇 v2 规范提出该需求 |
| 保障需求 | 该规范要求保障什么稳定性 |
| 接管理由 | 为什么普通规则、Code 检查或 Human Gate 不足以覆盖 |
| 候选编排 | 拟建立的行动编排名称或编号 |
| v1 参考 | 可参考的 v1 行动编排，不得直接视为迁移来源 |
| 依赖能力 | 需要 Code、Web、运行时扩展或 Human Gate 的哪类承载 |
| 形成时机 | v2 active 前、v2 active 后、新事实源建立后或后置 |
| 状态 | proposed / merged / deferred / dropped / approved |

在候选计划形成前，不得宣称 v1 30-59 行动编排已经迁移完成；但这不阻止 v2 03 先定义行动编排的生成规则和边界。

## 5. v2 工作流程接入边界

### 5.1 当前可以双读的能力

v2 未 active 前，下列能力可以作为只读辅助：

1. `specs-v2/` 草案读取；
2. 本文覆盖矩阵；
3. `V1-UNDERSTANDING-GATE.md`；
4. `python3 code/specs_validate.py v2-check` 的只读诊断；
5. v1/v2 元信息、字段、成员身份、附件路径和引用关系差异检查；
6. 知识地图只读派生预览。

这些输出只能用于定位、诊断和审查，不得作为 active 事实源、不得触发事实源写入、不得替代 Human Gate。

### 5.2 当前绝不能切换的入口

v2 未 active 前，下列入口必须继续以 active `specs/` 为准：

1. `rules/LDVH-WORKSPACE-ENTRY.md` 和 `rules/LDVH-MAINTAINER-ENTRY.md`；
2. Skills 默认执行流程，尤其是 `skills/ldvh-git-commit/SKILL.md`；
3. Hooks 默认检查和阻断规则；
4. Code 默认 `all`、`index`、`assurance-report`、`deployment-entries` 等 active 检查；
5. Web DTO、API、轻写入白名单和 Human-facing 页面；
6. 工作对象事实源写入、状态流转、关闭和长期降级；
7. Git commit message 契约和 Git commit records 追溯；
8. 管辖项目配置和 `ldvh-base/` 运行入口。

### 5.3 允许规划切换的最低条件

只有同时满足以下条件后，才允许提出 v2 工作流程接入切换方案：

1. 本文所有 v1 来源均有 `ready_for_human_review` 或 `human_confirmed` 状态，或有明确 `deferred`/`dropped_pending_review` 理由；
2. v2 各规范保障需求已经稳定，且已形成行动编排候选计划或明确后置理由；
3. `specs-v2/` 的 v2-check 能识别主规范、附件、20-29 事实模型成员和 30-59 行动编排成员；
4. active v1 全量检查与 v2 只读检查双跑通过；
5. Rules、Skills、Agents、Hooks、Code、Web 的默认入口切换方案逐项列出回滚路径；
6. Human Gate 明确批准 v2 成为 active 正式规范事实源。

## 6. 非行动编排 ready-for-review 初审

本节记录当前非行动编排 v2 草案的初审状态。该状态不是 Human 单篇确认，不改变 §3 覆盖矩阵中的正式状态，也不把任何 v2 文件升级为 active。

| v2 文件 | 初审判断 | 进入 Human 单篇核对前的主要缺口 |
|---|---|---|
| `00-LDVH理念与价值标准.md` | 已进入 Human 单篇核对 | 已确认 v1 00 存在理由、AI 第一服务对象、V1-V10、运行闭环下沉、Markdown/YAML 承载归口、保障要求收敛和总纲一致性检查承接 |
| `01-规范体系基础规范.md` | Human 单篇确认完成 | 已确认 01 只承接规范体系共同治理；v1 03.02/03.03 只作为成员声明和专属骨架共同治理方法来源，不表示 01 承接事实模型或行动编排成员完整骨架 |
| `02-事实模型基础规范.md` | Human 单篇确认完成 | 已确认 02 承接 v1 05 系列基础职责；20-24 具体事实模型成员仍需逐篇核对，不随 02 自动完成 |
| `04-Code确定性执行规范.md` | Human 单篇确认完成 | 已确认 04 承接 v1 07 Code 主体职责；知识地图和受控写入前检查均保持只读诊断或 preflight 边界 |
| `05-Web信息同步规范.md` | Human 单篇确认完成 | 已确认 05 只承接 Web 契约、Human-facing 展示、受控轻写入白名单、Confirm UI、提交展示、知识地图展示和回归线；不限定 Web 实现语言、框架或技术栈 |
| `06-运行时扩展规范.md` | Human 单篇确认完成 | 已确认 06 承接 v1 04/04.02/04.03 的固定运行时扩展、自描述、薄引用、Codex 候选入口、Hook 候选、适配检查和环境边界；Code/Web/行动编排/测试只作为外部归口或缺口分流方向 |
| `07-事实源边界与Git追溯规范.md` | Human 单篇确认完成 | 已确认 07 承接 v1 09 与 v1 10 的事实源边界、过程输出回写、历史记录提取、Git 追溯和 commit message 契约；v1 44 提交流程仅作为后续行动编排参考 |
| `08-测试基础规范.md` | Human 单篇确认完成 | 已确认 08 承接 v1 11 的测试治理、验证声明、证据边界、失败阻断、等价验证和 Code/Web 回归入口；测试服务六类构成要素验证，不替代构成要素本体规则 |
| `20-Spark-火花.md` | Human 单篇确认完成 | 已确认 active 20、02 字段矩阵、Web 快速创建白名单和 Spark 生命周期保障需求已由 v2 20 承接；21-24 关联成员仍需逐篇核对 |
| `21-WorkCase-工作项.md` | 可进入准备核对 | 需要逐项核对 active 21、`21.Att.01`、orchestration 字段、关闭材料、Web 态势和提交展示 |
| `22-ADR-决策.md` | 可进入准备核对 | 需要逐项核对 active 22、决策吸收、状态机、Human Gate 和 Web 旧字段禁用规则 |
| `23-Pitfall-踩坑经验.md` | 可进入准备核对 | 需要逐项核对 active 23、经验准入、归档、吸收边界、标签和 Web 详情规则 |
| `24-Study-研究报告.md` | 可进入准备核对 | 需要逐项核对 active 24、frontmatter、正文骨架、来源、归档和 Web 阅读边界 |

推荐核对顺序：

1. 先核对 00 和 01，固定最高锚点与规范治理；
2. 再核对 07，固定事实源、回写和 Git 追溯底线；
3. 再核对 02 与 20-24，固定事实模型和成员对象；
4. 再核对 04 与 08，固定 Code 与测试验证；
5. 最后核对 05 与 06，固定 Web 暂不实施回归线和运行时扩展接入边界。

行动编排成员不作为当前 ready-for-review 阻塞项。各规范提出的行动编排需求应先作为候选计划后置，等 v2 保障需求稳定后再决定是否形成 30-59 成员主文件。

## 7. 更新规则

更新本文时必须遵守：

1. 修改任一覆盖状态时，同步检查目标 v2 文件的 `migration_sources`、`active_fact_source` 和 `migration_status`；
2. 新增 v2 主规范、成员主文件或附件时，必须把对应 v1 来源补入 §3；
3. 删除、合并、废弃或后置 v1 机制时，必须写明 Human 核对记录；
4. Code 输出不得自动把状态推进为 `ready_for_human_review` 或 `human_confirmed`；
5. 本文变化后必须运行 v2 只读检查，并继续运行 active v1 回归检查。
