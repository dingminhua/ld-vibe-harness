# LDVH工作流程推进顺序修正记录

> 创建日期：2026-06-15
> 定位：LDVH 工作流程重建推进顺序的修正记录
> 调研边界：不直接构成强制规则
> 执行效力：无；规范规则需进入 specs 正文区，工作流程需进入 `specs/40-59` 成员主文件后才生效
> 来源：Human 指出当前 specs 已由 Code 提供工作流程集合派生索引，不应再设计 40 手写集合索引或 40 bootstrap
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`rules/LDVH-AI-ENTRY.md`、`specs/01-目录说明.md`、`specs/03.03-工作流程文档规范.md`、`specs/06-工作流程基础规范.md`、`specs/07-Code确定性执行实现规范.md`、`specs/09-事实源边界与承载规范.md`、`specs/10-测试基础规范.md`

---
## 1. 本文解决的问题

本文记录一次工作流程推进顺序判断修正，避免后续 AI 因旧上下文或聊天记忆再次提出“先创建 40 工作流程集合索引”或“先创建 40 workflow bootstrap”。

本文解决：

1. 当前工作流程集合发现和索引由哪里承接；
2. 为什么不应恢复手写 40 集合索引；
3. 为什么不需要创建 40 bootstrap；
4. 当前更合理的工作流程推进顺序；
5. 后续 AI 继续工作时应如何避免重复误判。

---
## 2. 修正结论

当前 LDVH 已明确由 Code 提供工作流程集合的派生索引、状态清单、冲突诊断和 AI Context Pack。工作流程集合成员事实源来自 `specs/40-59` 中实际存在的成员主文件及其机器可读自描述字段，而不是独立手写集合索引。

因此：

1. 不应恢复 `specs/40-工作流程集合索引.md` 作为权威集合索引；
2. 不应创建 `40 workflow bootstrap / 工作流程集合引导` 来重复说明集合如何被发现；
3. 第一个工作流程成员主文件应直接承接实际治理价值；
4. 当前最适合作为 40 的流程是 `workflow design audit / 工作流程设计审核`，用于审核后续 40-59 工作流程主文件是否符合 06 和 03.03；
5. Code 派生集合索引只作为派生视图、导航结果和诊断结果，不替代成员主文件或正式规范。

---
## 3. 依据

### 3.1 入口资产依据

`rules/LDVH-AI-ENTRY.md` 已说明：AI 进入 LDVH 时，能由 Code 定位、聚合或检查的内容，应优先使用 Code 工具查询；工具输出只作为导航、聚合和诊断结果，不替代权威文件原文。

入口资产的常用查询命令已包括：

1. `python3 code/specs_validate.py index`，用于生成规范派生索引，辅助定位文件、章节、引用和诊断；
2. `python3 code/specs_validate.py landing-report`，用于聚合正式规范的落地要求、状态和建议回写方向；
3. `python3 code/specs_validate.py doc specs`，用于检查正式规范文档结构；
4. `python3 code/specs_validate.py refs specs`，用于检查正式规范中的章节引用；
5. `python3 code/specs_validate.py landing specs`，用于检查规范落地要求表结构；
6. `python3 code/specs_validate.py all`，用于执行 specs 综合校验。

入口资产对处理工作流程的路由是：先用 `index` 和 `landing-report`，再读取 `specs/06-工作流程基础规范.md`、`specs/03.03-工作流程文档规范.md` 和对应 `specs/40-59` 工作流程规范。

入口资产还明确：遇到对应 `specs/40-59` 工作流程规范时，应按 `specs/03.03-工作流程文档规范.md` 的成员自描述契约和实际存在的成员主文件定位具体文件，不得凭编号区段、标题记忆或聊天上下文猜测文件。

### 3.2 目录规范依据

`specs/01-目录说明.md` 已说明：工作模型集合和工作流程集合不再通过独立手写集合索引文档维护成员清单。具体成员主文件必须按 `specs/03.02-工作模型文档规范.md` 或 `specs/03.03-工作流程文档规范.md` 声明机器可读自描述字段，成员编号、标题、状态、路径、可执行性和规则锚点以成员主文件为权威来源。

`specs/01-目录说明.md` 还说明：Code 依据编号分区、03.02 / 03.03 的成员自描述契约、05 / 06 的基础规则和 09 的事实源边界生成派生集合索引、状态清单、冲突诊断和 AI Context Pack。Code 输出只作为派生视图、导航结果和诊断结果，不替代成员主文件或正式规范。

目录规范还明确：Code 检查和派生索引能力已由 `code/spec_checks/index.py` 承接。若对应文件尚未创建或尚未生效，只能记录为候选事项、计划或待补齐事项，不能引用不存在的成员文件或派生索引作为事实源入口。

### 3.3 Code 规范依据

`specs/07-Code确定性执行实现规范.md` 已定义成员集合派生索引边界。Code 可以依据编号分区、成员自描述契约、基础规则和事实源边界生成工作模型和工作流程派生集合索引。

成员集合派生索引必须满足：

1. 输入来自 20-39 / 40-59 成员主文件、明确命令输出和测试结果，不从聊天记忆推断成员状态；
2. 输出必须回指成员主文件路径、成员自描述字段、章节锚点和诊断依据；
3. 输出可以列出成员清单、collection_status 分布、active 清单、编号冲突、缺失锚点、非法状态、重复路径和建议读取位置；
4. 输出只作为派生视图、导航结果和诊断结果，不替代成员主文件或正式规范；
5. 删除、重命名、重排编号或改变成员状态仍属于规范结构变更，必须按对应规范和 Human Gate 执行，Code 不生成授权。

---
## 4. 被修正的误判

本次被修正的误判是：由于当前 `specs/40-59` 还没有 active 工作流程主文件，AI 曾推断应先创建 `40 workflow bootstrap / 工作流程集合引导`，用于说明如何新增、重排、升级、降级、删除工作流程成员主文件。

该推断不成立，原因是：

1. 工作流程集合发现、状态聚合和冲突诊断已经由 Code 派生索引承接；
2. 成员如何声明身份已经由 `specs/03.03-工作流程文档规范.md` 承接；
3. 工作流程基础规则已经由 `specs/06-工作流程基础规范.md` 承接；
4. 目录、编号和文件归属已经由 `specs/01-目录说明.md` 承接；
5. 再创建 bootstrap 流程会重复上位规范和 Code 的职责，增加入口层级和误读风险。

---
## 5. 修正后的推进顺序

工作流程重建不应从集合索引或 bootstrap 开始，而应从第一个具有实际治理价值、且能帮助后续流程主文件写正确的工作流程开始。

推荐顺序如下：

1. `40 workflow design audit / 工作流程设计审核`：审核 40-59 工作流程主文件是否符合 06 和 03.03，尤其是成员自描述、Context、Scenario、Gate、执行流程、证据、回写、环境适配、行动特有可测试性锚点和 Code 消费字段；
2. `41 specs audit / specs 审核`：审核 specs 是否内部逻辑自洽、符合 00 价值标准、符合 AI 第一服务对象、符合文档治理、落地要求和事实源边界；
3. `42 code audit / Code 审核`：审核 Code 是否符合 07 和 10，是否有需求准入、测试或等价验证、输出边界、成员集合派生索引边界；
4. `43 rules entry audit / Rules 入口审核`：审核 `rules/LDVH-AI-ENTRY.md` 是否保持薄入口、场景路由准确、STOP 点清晰、未复制 specs 正文、未保存长期状态且与正式规范和 Code 查询入口同步；
5. `44 capability asset audit / 能力资产审核`：审核 Rules、Skill、Agent、Hook、Code、Web 等能力资产是否边界清楚，未互相替代，未绕过事实源和 Human Gate；
6. `45 fact-source writeback audit / 事实源与回写审核`：审核稳定事实是否回到 Git 文件事实源，过程输出、派生索引、测试结果、Skill 输出、Agent 输出和 Web 状态是否未冒充最终事实；
7. `46 change impact audit / 变更影响审核`：审核 specs、成员自描述、Code、入口资产、测试、能力资产、目录、编号和集合状态变化后的同步影响；
8. `47 dogfood loop / Dogfood 闭环`：用 LDVH 自身执行一次最小闭环，防止继续抽象而不落地；
9. `48 context preparation / 上下文准备`：基于入口、Code 派生索引、成员自描述、工作对象和任务目标生成最小可行动上下文；
10. `49 input intake / 输入接入`：将 Human 输入分流为 WorkArea、TaskPlan、Task、Memo、docs 或配置更新建议；
11. `50 planning / 计划规划`：把输入转为 TaskPlan、Task 序列、验收标准、依赖、验证方式和 Human Gate；
12. `51 task execution and verification / 任务执行与验证闭环`：合并执行、验证、失败分流、证据留存和关闭判断；
13. `52 decision formation / 决策形成`：将争议、取舍、长期规则和架构判断分流为 Human Gate 轻量决策记录、ADR、Memo 或 specs 更新建议；
14. `53 object and project management / 对象与项目管理`：管理 ADR、Change、对象状态流转和管辖项目配置；
15. `54 learning and practice upgrade / 经验回流与实践升级`：将重复问题、踩坑、规范缺口和工具缺口回流到 Pitfall、Memo、ADR、specs、Code、Web 或能力资产；
16. `55 non-LDVH content handover / 非 LDVH 来源内容接管`：接管外部资料、第三方 Skill、环境能力、用户既有内容或自动生成内容；
17. `56 workflow test redesign / 工作流程测试重设`：在首批 active 流程真实跑过后，再判断是否需要统一流程测试机制、测试事实源或 Code 测试矩阵；
18. `57-59 reserved or reevaluation / 保留或待重评扩展`：只接收前面流程执行后确实反复出现、且无法被已有流程承接的新候选。

---
## 6. 后续 AI 检查提示

后续 AI 在讨论或创建工作流程时，应先执行以下检查：

1. 读取 `rules/LDVH-AI-ENTRY.md`，确认工作流程场景路由和 Code 查询入口；
2. 运行或参考 `python3 code/specs_validate.py index` 和 `python3 code/specs_validate.py landing-report`，确认当前 `specs/40-59` 实际存在的成员主文件；
3. 读取 `specs/06-工作流程基础规范.md` 和 `specs/03.03-工作流程文档规范.md`；
4. 不得恢复手写集合索引；
5. 不得创建只用于说明集合发现方式的 bootstrap 流程；
6. 新建 40-59 工作流程主文件时，必须满足 03.03 的成员自描述契约，并能被 Code 派生索引发现；
7. Code 派生索引结果只能作为导航和诊断，最终事实仍以成员主文件和正式规范为准。

---
## 7. 与上一份评估的关系

`docs/studies/22-LDVH工作流程重建设计评估.md` 记录了工作流程重建的早期判断，其中包含“重建后的 40 应优先登记底层治理流程候选”等表述。

本文对该早期判断作出修正：

1. 工作流程集合不应通过手写 40 索引登记候选；
2. 工作流程集合发现和候选状态应依赖成员主文件自描述与 Code 派生索引；
3. 首个工作流程不应是集合索引或 bootstrap，而应是工作流程设计审核；
4. 早期评估中关于 specs 审核、Code 审核、Rules 入口审核的重要性仍然成立，但推进顺序应调整为先建立工作流程设计审核，再创建这些审查流程。

---
## 8. 待补齐事项

1. 尚未创建 `40 workflow design audit / 工作流程设计审核` 主文件；
2. 尚未创建 `41 specs audit / specs 审核` 主文件；
3. 尚未创建 `42 code audit / Code 审核` 主文件；
4. 尚未创建 `43 rules entry audit / Rules 入口审核` 主文件；
5. 尚未验证新增 40-59 成员主文件是否能被 `code/spec_checks/index.py` 派生索引正确发现；
6. 后续如创建工作流程主文件，应同步运行 `python3 code/specs_validate.py index`、`python3 code/specs_validate.py doc specs`、`python3 code/specs_validate.py refs specs` 和 `python3 code/specs_validate.py all`。
