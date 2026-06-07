# LD Vibe Harness 项目规则

> 最后更新：2026-06-08
> 层级：项目规则
> 适用项目：ld-vibe-harness
> 生效方式：始终生效
> 规范来源：`specs/00-08`、`specs/20-39`、`specs/05-Trae-Solo环境规范.md`、`specs/07-工作模型基础规范.md`、`specs/20-工作模型集合索引.md`
> 维护边界：仅作 LDVH 项目入口、硬约束、对象规范入口、specs 编辑入口和事实实例编辑硬约束，不替代 specs 正式规范；LDVH 不使用场景规则层

## 入口

先识别任务类型，再按 00-08 和相关应用剖面读原文片段：00 定位/价值；01 目录/编号/文档工作区映射；02 术语；03 文档基础；03.01 规范文档；03.02 管辖项目文档；04 事实源边界；05 Trae Solo 环境规范；07 工作模型；08 工作流程；14 Code / PyTools；15 Web。定位章节先搜标题行号，再按行范围读；工具输出、网页、聊天记忆不替代 Git 事实源；与任务主题相关的 evals/refs 应按文档工作区边界读取。

## 硬约束

新增机制、规则或规范内容必须服务 LDVH 价值标准（见 00 §4-5）。Human Gate 场景见工作区 L0 "场景入口"。Skill 语言约束见 05 §7.3。防递归建设原则见 00 §6。涉及规范、Rules、Skill、Agent、Tools、工作模型、状态机、部署边界或目录边界的判断，必须先定位并读取对应规范原文（见 05 §11.2）。

**规范变更后执行约束**：规范变更后同一会话内执行受影响的任务时，AI 必须重新读取变更后的规范，并明确声明"已按新规范调整执行计划"。执行 Task 前必须遵守 `blocked_by` 前置任务强制阻塞规则；任务关闭前必须检查 acceptance 列表是否已全部勾选为 `- [x]`；未勾选则必须启动独立 agent 重新审计，不得直接关闭。

**规格变更与工具联动约束**：变更涉及事实源边界、字段契约、状态机、对象类型、目录结构或术语的 specs 修改，AI 必须在提交前同步检查 tools/ 下的代码实现，确认是否存在需要更新的硬编码行为、目标对象映射、校验规则或测试用例。未完成 tools/ 同步的规格变更不得声称已完成。

**事实实例编辑硬约束**：编辑 `ldvh-base/` YAML 前，必须识别对象类型，读取 `specs/07-工作模型基础规范.md` 和 `specs/20-工作模型集合索引.md` 指向的对应主规范及已回并结构化契约章节；不得把 `ldvh-base/` YAML 当普通配置文件随意修改；不得绕过对象状态机；不得自行添加对象规范未定义字段；未读取对应对象规范和结构化契约章节时，不得编辑事实实例。

## Core Loop 阶段路由

| 阶段 | AI 应做什么 | 推荐 Skill |
|---|---|---|
| Intent | 识别用户意图，创建 Intent/Task | ldvh-intake |
| Plan | 拆解步骤，评估风险 | ldvh-plan |
| Execute | 按计划实施，遵守约束 | 待建设 |
| Verify | 独立 agent 审计 acceptance 检查列表（Task 状态: verifying）+ lint/test/build | ldvh-close §2.1 |
| Record | Change 记录，状态更新 | ldvh-close |
| Learn | Pitfall 沉淀，Rule 改进 | 待建设 |

AI 应在每次用户交互时判断当前 Core Loop 阶段，并推荐对应 Skill。未建设的阶段按现有 Rules 和规范执行。

## ADR 入口

修改 specs、Rules、Tools、工作模型边界或长期协作机制前检查 ADR；准入见 21 §3.3。ADR 写入、状态流转、推翻、废弃或升级必须 Human Gate；流程和工具见 21 主规范。proposed ADR 不作执行依据。

## Specs 与 Rules 入口

编辑 specs Markdown 时，文档工作区、章节编号、标题层级、引用纪律和 refs/evals 通用边界以 `specs/03-文档基础规范.md` 为准；规范文档骨架、机制落地关系和历史机制文件边界以 `specs/03.01-规范文档规范.md` 为准；管辖项目 docs/、docs/evals、docs/refs 和 README 边界以 `specs/03.02-管辖项目文档规范.md` 为准；编号分区以 `specs/01-目录说明.md` 为准；术语以 `specs/02-术语规范.md` 为准。新增、修改或审计 Rules 时读 05 §6，并从 `specs/*.md` 反向发现需求。规格变更涉及事实源边界、字段契约、状态机、对象类型、目录结构或术语时，同步检查 `tools/` 代码实现并在提交前完成同步。

## 压缩保护

LDVH | 00-08按任务读原文 | 相关evals/refs按文档工作区读取 | 规范/Skill/Tools/部署判断必须回原文(05§11.2) | 防递归见00§6 | Skill语言见05§7.3 | 00价值 01目录 02术语 03文档基础 03.01规范文档 03.02项目文档 04事实源边界 05环境 07工作模型 08工作流程 14Code 15Web | 搜标题行号 | Git为准 | ADR见21 | specs编辑读03/03.01/01/02 | docs编辑读03/03.02/01/04 | ldvh-base读07/20及对象主规范 | 不使用场景规则 | 项目规则不引用evals | CoreLoop路由=Intent→ldvh-intake|Plan→ldvh-plan|Record→ldvh-close | 改specs检查tools/代码
