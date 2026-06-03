# LD Vibe Harness 项目规则

> 最后更新：2026-06-03
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness
> 生效方式：始终生效
> 规范来源：`specs/00-05`、`specs/10-14`、`specs/20-22`
> 维护边界：仅作 LDVH 项目入口、硬约束和 L2 引导，不替代 specs 正式规范

## 入口

先识别任务类型，再按 00-20 读原文片段：00 定位/价值；01 目录/编号；02 术语；03/03.01 specs/索引；04 模型子文档；05 Human Gate；10 事实源/证据/回写；11 协作；11.01 Rules；11.02 Skill；11.03 Agent；12/12.01 Tools；12.02 Web；13 事实模型；14 行动模型；20 事实模型索引。定位章节先搜标题行号，再按行范围读；工具输出、网页、聊天记忆不替代 Git 事实源；evals/refs 仅明确要求时读。

产品化、Gstack 借鉴、Trae Solo 利用、Core Loop、PyTools、事实模型、Skill、Rules、Agent、Web 或安装配置体验相关任务，先读 `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md` 作为产品方向入口；13 号文档是底层架构前置，优先级高于 14 号评估，必要时回读 `specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md`；发现重要共识、关键决策、方向修正或长期约束时，应更新 evals/17。

## 硬约束

新增机制、规则或规范内容必须服务 LDVH 价值标准。Human Gate 场景见工作区 L0 "场景入口"。Skill 提示词、Skill 文档和面向 AI 的 Skill 编排说明使用中文，除非外部平台字段或技术标识必须使用英文。框架建设必须服务最近一次可运行闭环；连续新增抽象而未 Dogfood 时，应暂停扩张并转入实例验证。涉及规范、Rules、Skill、Agent、Tools、事实模型、状态机、部署边界或目录边界的判断，必须先定位并读取对应规范原文，不得只凭记忆、目录现状或经验推断。

## Core Loop 阶段路由

| 阶段 | AI 应做什么 | 推荐 Skill |
|---|---|---|
| Intent | 识别用户意图，创建 Intent/Task | ldvh-intake |
| Plan | 拆解步骤，评估风险 | 待建设 |
| Execute | 按计划实施，遵守约束 | 待建设 |
| Verify | 独立 agent 验证 acceptance 检查列表 + lint/test/build | ldvh-close §2.1 |
| Record | Evidence 回写，Change 记录，状态更新 | ldvh-close |
| Learn | Pitfall 沉淀，Rule 改进 | 待建设 |

AI 应在每次用户交互时判断当前 Core Loop 阶段，并推荐对应 Skill。未建设的阶段按现有 Rules 和规范执行。

## ADR 入口

修改 specs、Rules、Tools、事实模型边界或长期协作机制前检查 ADR；准入见 21 §3.3。ADR 写入、状态流转、推翻、废弃或升级必须 Human Gate；流程见 21.02，工具见 21.04。proposed ADR 不作执行依据。

## L2 引导

编辑 specs 进 `.trae/rules/ldvh-l2-specs-rules.md`；编辑 `ldvh-base/` YAML 进工作区 L0 事实模型规则；新增、修改或审计 Rules 时读 11.01 §7-10，并从 `specs/*.md` 反向发现需求。

## 压缩保护

LDVH | 00-20按任务读原文 | 产品化/Gstack/Trae/CoreLoop/PyTools先读evals17 | evals13=底层架构前置>evals14 | 重要共识更新evals17 | 规范/Skill/Tools/部署判断必须回原文 | 错误模式转检查项 | 防递归=服务最近可运行闭环+抽象后Dogfood | WebMVP=PyTools聚合后只读态势入口不写事实源 | Skill提示词中文 | Plan/Spec分级使用并映射Intent/Task/Evidence | Memo/Profile/初始化/审计/开发交付实践为待吸收高价值 | 00价值 01目录 02术语 03specs 04子文档 05HG 10事实源 11协作 12Tools 13事实 14行动 20索引 | 搜标题行号 | Git为准 | ADR见21 | specs进L2 | ldvh-base进事实L0 | CoreLoop路由=Intent→ldvh-intake|Record→ldvh-close
