# LD Vibe Harness 项目规则

> 最后更新：2026-06-03
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness
> 生效方式：始终生效
> 规范来源：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/11.01-Rules机制规范.md`、`specs/03.01-Specs文档索引规范.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`
> 维护边界：本文件只作 LDVH 项目入口、项目硬约束和 L2 引导，不替代 specs 正式规范

## 入口

LDVH 定位和总纲级价值原则见 00，目录见 01，术语见 02，specs 骨架和引用纪律见 03，specs 文档质量检查见 03.01。定位 specs 文档和章节时，通过搜索 Markdown 标题定位候选文档和章节行号，再按行范围读取原文片段；evals/refs 仅在用户明确指定或任务明确要求时读取。

## 硬约束

不自动 commit、push、tag、release。所有决策、设计、规范和机制都应服务 LDVH 价值实现标准中的一项或多项；不能服务快速定位、完整理解、正确判断、稳定执行、门禁识别、强制验证、证据沉淀、可靠回写、人类确认质量或持续完善的新增内容，不应进入核心体系。

索引、标题搜索、工具输出、网页视图和聊天记忆只作定位、辅助理解或过程信息，不替代规范原文和 Git 文件事实源。稳定事实、执行证据、检查结果、决策和变更必须回到 Git 文件事实源。

涉及 LDVH 理念、价值标准、五类构成要素、基础规范权威领域、事实模型或行动模型的高影响变更，先识别 Human Gate；需要确认时暂停拟执行动作并说明事实源、影响范围和建议确认事项。

新增或修改项目文档、Rules、规范或事实实例后，应按 `specs/22-Change-变更记录.md` 定义的 commit message 格式记录变更。

## ADR 入口

修改 specs、Rules、Tools、事实模型边界或长期协作机制前，应检查是否存在相关 ADR；判断是否满足 ADR 准入条件见 `specs/21-ADR-决策记录.md` §3.3。创建 ADR、状态流转、推翻、废弃或升级必须触发 Human Gate；ADR 读取、创建和写入流程见 21.02-Skill.md；ADR Tools 命令和能力边界见 21.04-Tools.md。proposed 状态 ADR 不得作为执行依据。

## L2 引导

编辑 specs Markdown 时进入 `.trae/rules/ldvh-l2-specs-rules.md`。编辑 `ldvh-base/` YAML 时进入工作区 L0 事实模型规则。新增、修改或审计 L0/L1/L2 Rules 时，先读 11.01 §7，并从 `specs/*.md` 反向发现 Rules 需求。

## 压缩保护

LDVH | 00总纲 | 不自动push | 价值标准服务 | 搜索标题定位 | 按行范围读原文 | 稳定事实回Git | HumanGate先暂停 | 变更记录见22 | ADR准入见21§3.3 | ADR写入须HumanGate | proposed不作为依据 | specs进L2 | ldvh-base进事实模型L0 | Rules审计读11.01§7
