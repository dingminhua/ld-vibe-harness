# LDVH 全盘确认与核心吸收建议

> 创建日期：2026-06-07
> 更新日期：2026-06-07
> 定位：LD Vibe Harness 当前 specs 与 evals 多轮迭代后的项目级全盘确认和吸收研判参考
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-目录说明.md`、`specs/03-文档基础规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/08-工作流程基础规范.md`、`specs/20-工作模型集合索引.md`

---

## 1. 本文解决的问题

本文承接 LD Vibe Harness 项目在多轮 specs 编写、evals 调研、外部项目借鉴和内部机制讨论后的全盘确认需求，系统整理当前最值得吸收进入正式规范体系的核心内容、应暂缓吸收的方向和不建议吸收的外部机制。

本文不是正式规范正文，不直接定义强制规则。本文用于辅助后续重写或确认 00 总纲、08 工作流程基础规范、20-27 工作模型规范、41 多角色思考流程以及 Rules、Skill、Tools、Web 相关机制边界。

当前项目已经积累了足够多的素材、调研和机制判断。后续重点不应继续无边界扩张，而应将已经反复出现、方向一致、能服务 AI 工作闭环的内容正式吸收进主规范；仍然只是参考、实验或局部灵感的内容，应继续留在 evals 或进入待确认状态。

---

## 2. 本文使用方式

当后续讨论 LDVH 重构、00 总纲、Core Loop、Task 治理、Skill 生命周期、Web MVP、规范即机制或项目改进路线时，应优先读取本文作为 evals 层唯一重构入口。

本文不替代正式 specs。本文结论只有在以下路径之一完成后，才成为稳定规则或执行依据：

1. 写入 00-79 正式 specs；
2. 通过 accepted ADR 确认；
3. 写入项目 Rules 或 Skill，并能追溯到正式 specs；
4. 进入 Task 并完成对应 Change commit。

关于 LDVH 重构、总纲收敛、系统结构调整、项目改进路线的 evals 层入口，仅保留本文。后续如出现新的 LDVH 重构判断，优先补充或修订本文；除非是独立外部项目调研、正式 ADR 或正式 specs，否则不再新增同类重构 evals 文档。

下一轮项目改进建议按以下顺序推进：

> 进度同步：00 总纲首轮吸收已经完成，已吸收项和下游承接清单以 `specs/evals/22-00总纲吸收差异清单.md` 的当前状态为准。本文保留为全盘研判入口，不重复维护 00 吸收进度明细。

1. 先重写或确认 00 总纲；
2. 再将 Core Loop、Human Gate、验证铁律、Task 治理锚点回流到 08；
3. 再对齐 27 Task 的 Verify / Record / closure_evidence；
4. 再审查 41 多角色思考、Agent 审计边界和核心 Skill；
5. 再规划 Web MVP 的只读态势入口；
6. MCP、Automation、Web 写入、ProjectGroup 和大规模生成链路暂不作为第一轮重构入口。

近期不要优先推进：ProjectGroup、Automation / Cron 对象、大量新增 Skill、大量新增 Agent、Web 写入后台、自建 MCP Controlled Writer、Risk / Dependency / Artifact / Checklist / Roadmap 对象化，以及恢复 Evidence / TaskSet 独立模型。

---

## 3. 研判范围与阅读分组

本轮研判覆盖 `specs/evals/` 中 01-24 的全部输入文档。25 本文是吸收结果文档，不作为本轮输入依据。当前目录中未发现 17 号 evals 文档；11、13、23 三篇 LDVH 重构类文档的核心内容已吸收进入本文，并按“25 作为唯一重构入口”的原则删除。

| 分组 | 文档 | 研判重点 |
|---|---|---|
| 外部产品与任务治理 | 01 Linear、02 gstack、03 Agent Harness、04 七层管理模型、05 Git、06 MCP、07 自建 MCP、08 Shrimp | 任务治理、AI 行动闭环、事实源边界、工具与 MCP 边界 |
| 内部提示与多项目治理 | 09 常用提示词模板、18 多项目治理 | 模板结构化、审查协议、项目边界、Profile tags |
| 平台、产品方向与 Skill | 10 Codex、11 Gstack-Trae 共识（已吸收删除）、12 规范即机制、13 系统结构（已吸收删除）、14 第三方 Skill、15 Trae Spec、16 Skill 写作 | 平台边界、Core Loop、Task 治理锚点、Skill 生命周期化 |
| 深度调研与 Web / 理念 | 19 Gstack 深调、20 Superpowers、21 BMAD、22 Web 页面、23 00 理念重梳（已吸收删除）、24 Hermes | 验证铁律、反合理化、微文件、Web 三层、AI 第一体验、工具权限面 |

---

## 4. 总体结论

LDVH 当前最值得正式吸收的，不是某个外部项目的具体功能，而是多轮迭代中反复被证明有效的 AI 工作闭环纪律：AI 第一体验、Git 文件事实源、四类构成要素、Core Loop、Human Gate、未验证不完成、Change / Record / Learn 回流，以及 specs 向 Rules、Skill、Tools、Web、Tests 派生的长期路线。

建议全盘确认以下核心判断：

1. LDVH 是面向 Vibe Coding 的规范驱动 AI 工作 Harness；
2. LDVH 以 AI 执行者为第一服务对象，同时保留 Human 的关键判断权；
3. Git 可追踪文件是最终事实源，聊天、工具输出、Web 状态、MCP memory、Skill 输出和 Agent 输出都不是最终事实源；
4. 开发环境、辅助工具、工作模型、工作流程是 LDVH 的四类构成要素，事实源不是第五类要素，而是贯穿四类要素的权威原则；
5. LDVH 的标准运行闭环是 Intent → Plan → Execute → Verify → Record → Learn；
6. 未验证不完成，没有 evidence 的 done 不是真正的 done；
7. Human Gate 是判断权和授权权边界，不是普通偏好选择，也不是 AI 懒得判断时的随意提问；
8. specs 定义产品 DNA，Rules、Skill、Tools、Web、Tests 是派生能力，实践结果通过 Change、Pitfall、ADR、Memo 和 specs 回流。

---

## 5. 应正式吸收的核心内容

### 5.1 产品定义

建议正式确认：LD Vibe Harness 是面向 Vibe Coding 的规范驱动 AI 工作 Harness。

LDVH 不应被描述为单纯的文档体系、工具集合、Web 后台、任务管理器或 Agent 框架。它的核心价值在于通过规范、事实源、工作模型、工作流程、Code 确定性执行和 Web 桥接能力，把随性的 AI 编程转化为可读取、可判断、可执行、可验证、可回写、可演进的工程闭环。

可吸收表达：

```text
LD Vibe Harness 是面向 Vibe Coding 的规范驱动 AI 工作 Harness。它以 specs 定义产品 DNA，以事实源承载稳定状态，以工作模型组织工程对象，以工作流程约束 AI 行动，以 Code 提供确定性执行，以 Web 桥接 Human 判断，最终形成可读取、可判断、可执行、可验证、可回写、可演进的 AI 工程闭环。
```

### 5.2 AI 第一体验

建议将 AI 第一体验正式确认为 LDVH 的设计原则。

LDVH 的第一体验不是 Human 管理界面，而是 AI 能否快速进入项目、理解事实、判断边界、执行任务、验证结果并回写事实源。Human 是判断者，AI 是主要执行者，Code 是确定性执行者，Web 是桥接界面。

该原则会影响后续机制设计：

1. Web MVP 不应先做复杂后台，而应先做 AI 和 Human 都能理解的态势入口；
2. Tools 不应只服务人手动操作，而应服务 AI 读取、校验和聚合；
3. specs 不应只是人类文档，应逐渐增强机器可消费性；
4. Task 不应只是项目管理卡片，而应是 AI 可执行工作单元；
5. Human Gate 不应退化为偏好选择，而应体现判断权边界。

### 5.3 Core Loop 六阶段

建议正式吸收以下 Core Loop：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

该链路已经在多轮调研和内部讨论中反复出现，适合作为 LDVH 主运行闭环。当前项目已有局部雏形：ldvh-intake 对应 Intent，ldvh-plan 对应 Plan，ldvh-close 对应 Verify / Record，ldvh-commit 对应 Change；Execute 和 Learn 仍需要进一步补齐。

建议吸收路径：

1. 在 00 中作为运行闭环总原则；
2. 在 08 中作为工作流程基础框架；
3. 在 27 中映射 Task 生命周期；
4. 在 40-59 区间逐步补齐 Plan、Execute、Verify、Record、Learn 相关工作流程。

### 5.4 Task 作为治理锚点

建议正式确认 Task 是 LDVH 中承接执行、验证、关闭和回写的治理锚点。

外部项目和内部评估反复指向同一结论：Trae Spec、第三方 Skill、Plan、执行序列、Web 操作、Agent 审查、工具验证都不应成为新的权威治理入口，而应被 Task 接管和约束。

建议吸收原则：

1. Task 控制治理粒度；
2. Sequence 控制执行粒度；
3. Output Contract 或 acceptance 控制验证粒度；
4. 临时 Todo 只作为会话 scratchpad，不成为事实源；
5. Spec / Plan / 第三方 Skill 产物必须经 LDVH 吸收后才可作为执行依据。

### 5.5 未验证不完成

建议将“未验证不完成”上升为 LDVH 的工程纪律。

可吸收表达：

```text
完成必须以可验证结果和可追溯证据为依据。AI 的口头总结、主观判断或未执行的检查，不构成完成依据。
```

该原则适合进入 00 运行闭环标准、08 工作流程基础规范、27 Task 关闭条件、ldvh-close Skill 和 10 工作流测试。它与当前 Task acceptance、closure_evidence、verifying / review_needed 状态和独立审计机制方向一致。

### 5.6 反合理化与失败暂停

建议吸收 Superpowers 类工程纪律中的反合理化机制，但转译为 LDVH 风格。

可吸收内容：

1. 对每条硬约束增加常见违规借口和红旗表达；
2. 不允许用“应该通过”“看起来没问题”“已经做了”替代验证证据；
3. 同一问题连续修复失败多次时暂停猜测式修改，回到根因调查；
4. 必要时触发 Human Gate、Memo、Pitfall、ADR 或子 Task；
5. Task Verify 不只看测试通过，还要看 acceptance 是否真正满足。

### 5.7 Human Gate 是判断权边界

建议将 Human Gate 明确为 Human 判断权、授权权和责任边界的显式化机制。

Human Gate 不应是普通偏好选择，也不应是 AI 无法决定时的随意提问。它应覆盖关键事实源创建、关键状态流转、高风险变更、ADR 接受或废弃、删除或覆盖、任务关闭、自动化授权、发布或外部影响、多方案存在实质差异等场景。

可吸收表达：

```text
Human Gate 是 LDVH 中 Human 判断权、授权权和责任边界的显式化机制，不是普通交互确认，也不是 AI 无法判断时的随意提问。
```

Human Gate 的呈现可以吸收 Gstack 的 decision brief 思路：背景摘要、影响范围、推荐选项、风险说明、取消 / 暂缓 / 修改路径。

### 5.8 事实源不可替代

建议继续强化 Git 文件事实源作为底层权威原则。

需要明确排除以下机制成为最终事实源：聊天上下文、工具输出、Skill 输出、Agent 输出、Web UI 状态、数据库派生视图、MCP memory、隐藏本地状态目录、临时 task json、Trae Spec 中间产物、Kanban DB、外部 memory snapshot。

可吸收表达：

```text
任何机制只要不能回到 Git 可追踪事实源，就只能是过程辅助，不能成为 LDVH 的稳定事实。
```

该原则是防止 Web、MCP、Skill、Agent 或外部工作流形成第二事实源的关键边界。

### 5.9 Web 三层与只读态势入口

建议吸收 Web 方向，但只吸收原则，不在 00 中写死页面布局、组件名或技术栈。

推荐 Web 三层：

```text
LDVH Web
├── Workbench：事实对象管理和态势入口
├── Docs：规范文档站
└── Runtime Panel：运行态辅助侧栏
```

推荐 MVP 原则：

```text
Web MVP 优先作为事实源的只读态势入口和 Human Gate 辅助界面，不先作为复杂写入后台。
```

可优先考虑的 Web 信息同步范围包括 Task 列表、Task 详情、Intent 详情、Fact Validation 面板、Change / Record 视图、Docs 入口、Human Gate 页面和 Runtime Panel。

Web 写入能力应晚于事实源解析、校验、状态聚合和 Human Gate 规则成熟之后。

### 5.10 Skill 生命周期化与质量升级

建议正式确认 LDVH Skill 不应按角色无限扩张，而应优先按 Core Loop 生命周期补位。

当前核心 Skill 可映射为：

| Core Loop 阶段 | 当前 Skill / 状态 |
|---|---|
| Intent | ldvh-intake |
| Plan | ldvh-plan |
| Execute | 待建设 |
| Verify / Record | ldvh-close |
| Decision | ldvh-adr |
| Change | ldvh-commit |
| Learn | 待建设 |

Skill 写作和维护应吸收以下要求：Use / Do NOT Use、输入输出契约、失败处理、Human Gate 条件、事实源读取要求、评估用例、不调度 Agent、不链式调度 Skill、输出不是事实源且回写后才成立。

短期重点不应是大量新增 Skill，而应是升级现有核心 Skill 质量。

### 5.11 独立审计 Agent 与工具权限面

建议将独立审计 Agent 吸收为 Verify 阶段的重要机制，但不应对所有任务无差别强制。

可吸收分级：

1. 普通任务：工具验证和 acceptance 检查；
2. 中等任务：建议独立审计；
3. 高风险任务：必须独立审计；
4. 规范、状态、事实源变更：Human Gate 与验证必需。

建议吸收 Hermes 的工具权限面思想：不同阶段、不同 Agent、不同任务类型，不应暴露同一套写入和执行能力。

可吸收边界：

| 阶段 / 角色 | 权限边界 |
|---|---|
| Intake | 可读规范，可创建草案，不直接执行目标变更 |
| Plan | 可读事实源，可生成计划，不直接修改目标文件 |
| Execute | 可修改目标文件，但不得绕过状态机和 Human Gate |
| Verify Agent | 只读 Task、diff、产物和相关规范，可运行验证命令 |
| Review Agent | 只读事实源、diff 和证据，输出审查结论 |
| Close | 可写 closure_evidence 和状态流转，必须满足关闭条件 |

### 5.12 工具执行证据层与 closure_evidence 结构化

建议将 closure_evidence 从单纯文本摘要逐步增强为结构化证据层。

可吸收内容：

1. 执行命令；
2. 输出摘要；
3. 产物路径；
4. 验证结果；
5. 审查 Agent 输出；
6. Human Gate 选择；
7. 关联 Change；
8. 本次新增错误与历史遗留错误区分。

该方向不要求恢复独立 Evidence 工作模型，可先由 Task `closure_evidence` 和关联结果物承接。

### 5.13 渐进式上下文加载

建议吸收 Hermes Skills、BMAD 微文件和 LDVH 现有读取策略的共同方向：先索引定位，再按需读取，不全文灌入。

可吸收原则：

1. AI 先识别场景，再读取最小可行动上下文；
2. specs 先通过标题、索引或派生索引定位；
3. Skill 只加载当前流程所需章节；
4. Agent 委派只接收任务封包、相关规范和必要证据；
5. Web / Tools 可提供 Context Pack，但 Context Pack 不成为事实源。

### 5.14 第三方 Skill 治理接管

建议吸收第三方 Skill 引入原则：第三方 Skill 是能力供给方，LDVH 是治理约束方。

可吸收表达：

```text
第三方 Skill 只做脚手架，持续开发必须回到 LDVH Core Loop。
```

第三方 Skill 产物应视为待审计外部贡献，完成后必须进入 LDVH 管辖，接受对象规范、状态机、Human Gate、Change 和验证约束。

### 5.15 Trae Spec 纳入 Task 治理

建议吸收以下原则：

1. Task 是治理锚点，Spec 是规划产物；
2. Spec 确认不等于执行授权；
3. Spec 必须被 LDVH 吸收后才可作为执行依据；
4. `.trae/specs/` 不得成为第二权威事实源；
5. `tasks.md` 中的每一项不自动成为 LDVH 子 Task，只有满足独立状态、独立验收、跨会话追踪等条件时才升级。

### 5.16 多项目治理的轻量吸收

建议吸收项目边界定义与 Profile tags 方向，但暂缓 ProjectGroup。

一个项目是否适合接入 LDVH，可参考以下判断：

1. 有独立 Git 仓库或仓库内独立管理的顶层目录；
2. 有独立构建 / 部署单元或发布节奏；
3. 需要独立需求、任务或变更治理；
4. 接入 LDVH 后有独立 `ldvh-base/` 目录和项目规则。

Profile tags 可作为轻量分组能力候选，但需先评估字段契约和 validator 影响。

### 5.17 规范即机制长期路线

建议将“规范即机制”吸收为长期方向，而不是立即全面落地。

长期目标是：

```text
specs → Rules
specs → Skill
specs → Validators
specs → Web schema
specs → Tests
```

但当前 specs 结构还未完全机器可消费，字段契约、状态机、流转矩阵、Human Gate 条件和历史 Contract 文档仍需进一步整理。因此建议先吸收方向，后续再通过结构化契约、validator 覆盖矩阵和 drift 检测逐步落地。

---

## 6. 逐篇吸收研判矩阵

### 6.1 Linear

| 类型 | 内容 |
|---|---|
| 可吸收 | 高速、清晰、低打扰的任务治理体验；Task 详情作为 AI 协作上下文入口；今日行动、阻塞、待验收、决策等待等多视图；轻量输入后分流为 Memo / Intent / Task；空状态引导 |
| 暂缓 | Cycle / Sprint / Roadmap 重模型；第三方工具自动同步；复杂团队协作 SaaS 能力 |
| 不吸收 | 云端账号体系、大型 SaaS 数据库模型、重评论系统 |

### 6.2 gstack 与 Gstack 深调

| 类型 | 内容 |
|---|---|
| 可吸收 | 流程即入口；阶段产物连续交接；Human Gate decision brief；真实验证意识；质量门禁前置；retro / learn 思路 |
| 暂缓 | 浏览器 daemon；完整 Skill 矩阵；安全护栏命令体系；多宿主安装和自动更新 |
| 不吸收 | `~/.gstack/` 隐藏状态事实源；自动提交、push、发布；大量人格化角色 Skill；速度优先替代治理纪律 |

### 6.3 Agent Harness

| 类型 | 内容 |
|---|---|
| 可吸收 | Harness 不是 Prompt；可控行动循环；Guardrails 可见化；Memory 转译为 ADR / Task / Memo / Pitfall / Change；Test Harness 证据完成 |
| 暂缓 | Memory 命中机制；事实源健康检查；反馈沉淀提示自动化 |
| 不吸收 | 通用 Agent Runtime；向量库或运行时数据库替代 Git 文件事实源；完全自动关闭任务 |

### 6.4 七层管理模型

| 类型 | 内容 |
|---|---|
| 可吸收 | 按内容性质分层治理；规范、决策、需求、实践、对象、记录、审查的归属判断；分层上下文包 |
| 暂缓 | Web / Tools 展示内容所属层级；审查闭环分流工具化 |
| 不吸收 | 复制七层编号体系；引入独立审计编号体系；把七层变成教条 |

### 6.5 Git 版本管理参考

| 类型 | 内容 |
|---|---|
| 可吸收 | commit / diff / log 作为证据来源；人管 push / tag / release；Conventional Commits 参考；Release Notes 结构参考 |
| 暂缓 | main + dev 双分支正式化；tag / release 规范化；git log 与 Change 的完整关系重构 |
| 不吸收 | AI 自动 push / tag / release；只以 git log 替代 Change 记录 |

### 6.6 MCP 与自建 MCP

| 类型 | 内容 |
|---|---|
| 可吸收 | MCP 是 Agent 可选工具能力来源；Sequential Thinking、Context7、Playwright 可按需使用；自建 MCP 只作为 Tools 薄协议入口；Fact Reader、Status Aggregator、Context Pack、Validator 可作为长期候选 |
| 暂缓 | 自建写入型 MCP；Controlled Writer；MCP 工具总清单；Codex / GitHub Action 自动审计 |
| 不吸收 | Memory MCP 作为事实源；文件系统 MCP 绕过 LDVH 读写规范；云服务、数据库、支付类 MCP 进入核心配置 |

### 6.7 Shrimp Task Manager

| 类型 | 内容 |
|---|---|
| 可吸收 | 任务治理直接服务 AI 执行过程；Task 可执行对象；依赖、验收、验证、证据；研究模式骨架；Web 可观察性 |
| 暂缓 | Task 字段全面扩展；TaskSet；MCP Server 工具链；Agent 自动分配辅助 |
| 不吸收 | `{DATA_DIR}/tasks.json` 作为权威任务源；memory 备份作为长期事实源；score 自动关闭；完整思维链作为事实 |

### 6.8 常用提示词模板

| 类型 | 内容 |
|---|---|
| 可吸收 | 模板骨架：适用场景、目标、必读入口、角色选择、Human Gate、输出契约、风险分级、建议写回对象；多角色提示词作为审查协议 |
| 暂缓 | 直接升格为正式 workflow spec；每次审查默认多 Agent |
| 不吸收 | 模板即事实源；模板输出直接成为稳定规则 |

### 6.9 Codex

| 类型 | 内容 |
|---|---|
| 可吸收 | 平台能力替换底座，LDVH 内核不变；Codex 可作辅助轨道；大上下文、沙箱、自动审计可作为候选能力 |
| 暂缓 | Rules → AGENTS.md 迁移；删除 Trae 读取策略；Agent 规范大幅删减 |
| 不吸收 | 立即从 Trae Solo 迁移到 Codex；Codex 平台能力导致事实模型变化；Memory / Linear 替代 LDVH 事实源 |

### 6.10 Gstack-Trae 融合共识

| 类型 | 内容 |
|---|---|
| 可吸收 | Gstack 体验范式 + LDVH 治理骨架 + Trae Solo 原生机制；最小事实内核；执行中问题分流；Web 只读态势优先 |
| 暂缓 | 一次性创建 Execute / Review / Retro / Learn 全套 Skill；Context Primer、Gate Detector、Evidence Collector 工具能力 |
| 不吸收 | Gstack 具体技术结构；Roadmap / Risk / Checklist / Artifact 立即对象化 |

### 6.11 规范即机制

| 类型 | 内容 |
|---|---|
| 可吸收 | specs 是唯一权威源；Rules / Skill 是派生产物；生成验证闭环；AUTO-GENERATED 标记和 override 机制 |
| 暂缓 | 立即实现 `ldvh-gen-rules` / `ldvh-gen-skills`；specs 变更后自动触发重新生成；生成 Skill 自举 |
| 不吸收 | 把 AI 生成当确定性编译；生成物直接覆盖人工定制；specs 未结构化前大规模自动生成 |

### 6.12 系统性结构调整

| 类型 | 内容 |
|---|---|
| 可吸收 | 五类构成要素分层；evals / refs / docs / specs / ldvh-base 效力边界；先分层、先收敛、先 Dogfood；主控唯一调度 |
| 暂缓 | 一次性结构制图；单独创建 `ldvh-verify`；Contract 消费路线全面落地 |
| 不吸收 | 一次性重排 specs 全部编号；恢复 TaskSet / Evidence；Risk / Dependency / Artifact / Checklist / Roadmap 立即对象化 |

### 6.13 第三方 Skill

| 类型 | 内容 |
|---|---|
| 可吸收 | 第三方 Skill 是能力供给方，LDVH 是治理约束方；脚手架先行，治理接管后续；第三方产物视为待审计外部贡献 |
| 暂缓 | 创建 `ldvh-web` 包装 Skill；通用第三方 Skill 引入框架正式规范化 |
| 不吸收 | 第三方 Skill 做持续开发；第三方产物不经审计直接进入主干；完全自建替代所有第三方 Skill |

### 6.14 Trae Spec 工作流

| 类型 | 内容 |
|---|---|
| 可吸收 | Task governance over Trae Spec execution；Task 是治理锚点，Spec 是规划产物；Spec 确认不等于执行授权；Spec 必须被 LDVH 吸收后才可作为执行依据；Task / Sequence / Output Contract 三层颗粒度 |
| 暂缓 | 正式新增 `ldvh-spec-ingest`；正式新增 `ldvh-execute-sequence`；新增 Plan / Spec / Checklist / Artifact 事实模型 |
| 不吸收 | 让 Spec 替代 Task；Spec 确认后自动执行；`tasks.md` 每项自动变成 LDVH 子 Task |

### 6.15 Skill 写作最佳实践

| 类型 | 内容 |
|---|---|
| 可吸收 | Rules 常驻，Skill 按需；现有五个 Skill 优先打磨；统一 Skill 元数据；Use / Do NOT Use；Input / Output；Failure handling；eval cases |
| 暂缓 | `ldvh-skill-review`；`ldvh-eval`；eval cases 的长期承载形式 |
| 不吸收 | 一次性重写全部 Skill；继续快速新增大量 Skill；把 Skill 写成 specs 副本 |

### 6.16 多项目治理

| 类型 | 内容 |
|---|---|
| 可吸收 | 明确项目定义；工作区规则继续承担项目名册入口；Profile tags 作为轻量分组候选 |
| 暂缓 | ProjectGroup 工作模型；多项目写入型 Web 后台 |
| 不吸收 | 多项目集合优先建模；隐藏状态目录或外部数据库作为项目集合事实源 |

### 6.17 Superpowers

| 类型 | 内容 |
|---|---|
| 可吸收 | 验证铁律；反合理化体系；两阶段审查；多次修复失败暂停；子代理隔离审查；Skill 描述不泄漏流程摘要 |
| 暂缓 | TDD 铁律绝对化；Worktree 强制隔离；每任务子代理执行 |
| 不吸收 | 删除代码重来的极端惩罚；会话级状态替代事实源；连续执行覆盖 Human Gate |

### 6.18 BMAD-METHOD

| 类型 | 内容 |
|---|---|
| 可吸收 | 微文件步骤架构；步骤完成状态可见；Stakes 校准；维度化评审；Definition of Done；规则优先级显式化 |
| 暂缓 | Headless 模式；external handoffs；Web Bundles；大规模多 Agent 并行评审 |
| 不吸收 | 具名人格 Agent；微文件绝对线性流程；Party Mode；文件系统事实源替代 Git 事实源 |

### 6.19 Web 页面调研

| 类型 | 内容 |
|---|---|
| 可吸收 | Workbench / Docs / Runtime 三层；Task / Intent MVP；Fact Validation 面板；Human Gate / ADR 可视化卡片；区分历史错误和本次错误 |
| 暂缓 | 完整 Docs 站点；Runtime Panel；编辑能力 |
| 不吸收 | 把 Web 做成单一形态；复杂可视化优先；Web 绕过 CLI / PyTools 写事实源 |

### 6.20 00 理念重梳

| 类型 | 内容 |
|---|---|
| 可吸收 | 最适合 AI 工作的 Vibe Coding Harness；规范定义产品，AI 推理实现，事实源验证闭环，实践经验回流规范；能力不可缺席，载体可以替换；Human / AI / Code 分工 |
| 暂缓 | 00 文档完整重写；多宿主 specs 消费模型 |
| 不吸收 | AI 自主推动体系演进的误读；只要 specs 就够的误读 |

### 6.21 Hermes Agent

| 类型 | 内容 |
|---|---|
| 可吸收 | 工具注册表 + Toolset 分组；Todo 与正式 Task 边界；工具执行管线；隔离 Subagent 审查；Memory 注入前安全过滤；Skills 渐进披露；自动化任务执行封包概念 |
| 暂缓 | Automation / Cron 对象；Gateway / ACP / Messaging / Honcho；并发工具执行 |
| 不吸收 | 即时模型工具调用替代事实源状态机；普通 chat 默认可见所有工具；子代理自主复杂写入 |

---

## 7. 应暂缓吸收的内容

### 7.1 自建 MCP

自建 MCP 可以保留为远期方向，但当前不宜进入核心体系。

原因包括：PyTools 尚未完全稳定，Web 只读态势入口尚未落地，Fact Validator、Context Pack 和 Status Aggregator 仍可用本地 Tools 推进，写入型 MCP 风险较高，过早 MCP 化会分散主线。

建议路线：先做 PyTools，只读聚合和校验成熟后，再考虑 MCP 协议入口。

### 7.2 ProjectGroup 工作模型

多项目治理方向有价值，但当前不建议新增 ProjectGroup 工作模型。

可先吸收 Profile tags、项目身份、project_path、ldvh_base_path 和多项目只读聚合。当管辖项目数量和跨项目聚合需求达到稳定阈值后，再评估是否引入 ProjectGroup。

### 7.3 Trae Spec Ingest 完整机制

Trae Spec 可以作为规划辅助，但不应成为第二权威事实源。

可吸收原则：Task 是治理锚点，Trae Spec 是规划产物，Spec 确认不等于执行授权，Spec 必须被吸收后才能成为执行依据。

不建议当前立即将完整 ldvh-spec-ingest 机制写入主规范，除非后续确定进入实现阶段。

### 7.4 多角色思考扩张

41 多角色思考规范已有基础，不建议继续扩张为角色体系或人格化 Agent 系统。

应保留主上下文轻量模式、多 Agent 模式、同轮最多 4 个并行 Agent、输出不是事实源、回写建议由主控判断等原则。多角色思考应是复杂判断方法，不是组织架构。

### 7.5 Web 写入后台

Web 可以后续做受控写入，但当前不应直接发展成复杂写入后台。

过早写入会带来绕过 Human Gate、产生第二事实源、UI 状态与 Git 事实源不一致、为了前端体验牺牲对象规范等风险。

### 7.6 自动化 / Cron 对象

Hermes 和平台自动化评估说明周期性任务有价值，但当前不建议立即新增 Automation / Cron 工作模型。

更稳妥的路线是先把 Task / Change / Verify / Web / Validator 闭环跑稳。未来若周期性治理任务成为稳定需求，再考虑独立执行封包或对象模型，而不是在 Task 中简单增加 `cron` 字段。

### 7.7 大规模生成与自举

规范即机制方向应保留，但不宜立即大规模生成 Rules、Skill、Validators 或 Web schema。

原因是 specs 结构化程度尚未完全统一，字段契约、状态机、Human Gate 条件、Contract 消费路线和 validator 覆盖矩阵仍需逐步整理。

---

## 8. 不建议吸收的内容

### 8.1 隐藏本地状态目录

不建议吸收隐藏本地状态目录、memory store、local database、agent state、本地 task json、Kanban DB 或 Web 数据库作为 LDVH 核心事实源。

这些机制可以作为缓存或派生视图，但必须明确不是事实源。

### 8.2 自动 push、release、merge

LDVH 可以辅助 commit 草案、commit 校验和变更记录，但不应自动 push、release 或 merge。

这些行为属于 Human 权限边界。

### 8.3 分数式完成标准

不建议吸收 score >= 80 等分数式完成标准。

LDVH 的完成标准应依据 acceptance 是否满足、验证是否执行、evidence 是否存在、Human Gate 是否通过、Change 是否记录和对象状态是否正确，而不是模糊评分。

### 8.4 人格化 Agent 系统

不建议吸收人格化 Agent 系统。

LDVH 中的 Agent 应作为独立上下文、专业审计或隔离评估能力，而不是人格角色扮演系统。

### 8.5 AI 自审即完成

不建议接受 AI 主控仅凭自身总结完成审查和关闭。

LDVH 的 Verify 应具备外部性，包括工具验证、测试结果、独立上下文审计、Human Gate、Git diff、validator 输出或其他可追溯 evidence。

### 8.6 平台能力替代 LDVH 内核

不建议让 Codex、Trae Spec、MCP、Hermes 类 Agent OS、Gstack 类体验工具、第三方 Skill 或 Web 后台替代 LDVH 的事实模型、Git 文件事实源、Task 治理、Human Gate、状态机、Change / Record / Learn 闭环。

平台能力可以增强底座，但不能改变 LDVH 内核。

---

## 9. 全盘确认命题

### 9.1 产品定义

LDVH 是面向 Vibe Coding 的规范驱动 AI 工作 Harness。

### 9.2 第一服务对象

LDVH 以 AI 执行者为第一服务对象，但 Human 保留关键判断权。

### 9.3 事实源原则

Git 可追踪文件是最终事实源；聊天、工具输出、Web 状态、MCP memory、Skill 输出和 Agent 输出都不是最终事实源。

### 9.4 四类构成要素

开发环境、辅助工具、工作模型、工作流程是 LDVH 的四类构成要素；事实源不是第五类要素，而是贯穿四类要素的权威原则。

### 9.5 运行闭环

LDVH 的标准运行闭环是 Intent → Plan → Execute → Verify → Record → Learn。

### 9.6 完成标准

未验证不完成；没有 evidence 的 done，不是真正的 done。

### 9.7 Human Gate 原则

Human Gate 是判断权和授权权边界，不是普通偏好选择，也不是 AI 懒得判断时的随意提问。

### 9.8 Task 治理原则

Task 是治理锚点，Spec、Plan、第三方 Skill、执行序列、Agent 审查和工具验证都必须被 Task、状态机、acceptance、closure_evidence 和 Change / Record 约束。

### 9.9 平台适配原则

平台能力可以替换承载底座，但不改变 LDVH 内核。Trae、Codex、MCP、Web、Agent OS 都只能作为机制承载或辅助能力，不得成为第二事实源或第二治理中心。

### 9.10 演进方式

specs 定义产品 DNA，Rules、Skill、Tools、Web、Tests 是派生能力；实践结果通过 Change、Pitfall、ADR、Memo 和 specs 回流。

---

## 10. 对 00 总纲的建议影响

如果围绕 00 总纲进行全盘确认，建议形成以下结构逻辑：

1. 为什么存在：解释 Vibe Coding 的问题和 LDVH 的使命；
2. 以 AI 执行者为第一服务对象：解释 AI 依赖、AI 能力、AI 本质，以及 Human / AI / Code / Web 分工；
3. 四类构成要素与事实源原则：解释开发环境、辅助工具、工作模型、工作流程和事实源原则；
4. 价值实现标准：解释什么样的机制值得进入 LDVH；
5. 运行闭环标准：正式吸收 Intent → Plan → Execute → Verify → Record → Learn；
6. 机制落地关系：解释 00 如何约束后续 specs、Rules、Skill、Tools、Web；
7. Human Gate 与检查要求：明确 Human Gate 是判断权边界；
8. 待补齐事项：放置仍未定稿、不宜立即固化的内容。

当前 00 的第 1、2 章已经基本稳定。第 3 章适合确认四类构成要素、事实源原则和协作关系。第 4 章之后适合重点吸收 Core Loop、验证铁律、Human Gate、Task 治理锚点、工具权限面和规范即机制长期路线。

---

## 11. 项目改进推动优先级

### 11.1 P0：应尽快进入正式规范或 Rules / Skill 改造

1. LDVH 产品定义：面向 Vibe Coding 的规范驱动 AI 工作 Harness；
2. AI 第一体验与 Human / AI / Code / Web 分工；
3. Core Loop：Intent → Plan → Execute → Verify → Record → Learn；
4. Task 是 Trae Spec、Plan、第三方 Skill、执行序列和 Agent 审查的治理锚点；
5. Spec 确认不等于执行授权，Spec 必须被 LDVH 吸收后才可作为执行依据；
6. 未验证不完成，closure_evidence 必须包含新鲜验证证据；
7. Human Gate 是判断权和授权权边界；
8. 独立审计 Agent 默认只读限权，不直接修改事实源或关闭任务；
9. 现有核心 Skill 增加 Use / Do NOT Use、Input / Output、Failure handling、eval cases；
10. 第三方 Skill 只做脚手架，后续由 LDVH 治理接管。

### 11.2 P1：近期 Dogfood 后正式化

1. closure_evidence 结构化；
2. 工具权限面；
3. Task closure 两阶段审查：规格合规 + 质量合规；
4. 反合理化红旗清单；
5. Profile tags；
6. Web 只读态势入口；
7. Fact Validation 面板；
8. Context Pack；
9. `ldvh-spec-ingest` 候选 Skill；
10. `ldvh-skill-review` 候选 Skill；
11. 规范即机制的半自动审查和漂移检测。

### 11.3 P2：长期方向

1. 自建 MCP；
2. Automation / Cron 对象或执行封包；
3. Codex 双轨辅助；
4. 浏览器真实验证增强；
5. Docs 独立站点；
6. 多宿主适配；
7. Headless 只读审计；
8. Web 受控写入后台；
9. Contract 消费全面落地；
10. specs → Rules / Skill / Validators / Web schema / Tests 生成链路。

### 11.4 暂不推进

1. ProjectGroup 工作模型；
2. 大量新增 Skill；
3. 大量角色 Agent；
4. Risk / Dependency / Artifact / Checklist / Roadmap 立即对象化；
5. 恢复 TaskSet 或 Evidence 独立事实模型；
6. Trae Spec 替代 Task；
7. Web 直接编辑 YAML；
8. MCP 写入型 Controlled Writer。

---

## 12. 优先清理事项

1. Evidence / Risk 等已取消或 deferred 概念的残留引用；
2. Human Gate 删除豁免与高风险事实源删除之间的边界；
3. 项目规则中产品方向入口编号与实际 evals 文档编号不一致的问题；
4. 11 最佳实践与当前 Task verifying / review_needed 机制之间的措辞对齐；
5. Profile 与工作区管辖项目配置之间的名册权威边界；
6. Task closure 与 Change commit / Record 阶段之间的交接关系；
7. Skill description 过长导致 AI 不读正文的风险；
8. `.trae/specs/`、Web 状态、MCP memory、Agent 输出成为第二事实源的风险说明。

---

## 13. 待补齐事项

1. 将本文核心命题逐条与 00 总纲修订方案对齐；
2. 判断 Core Loop 是否需要 ADR 确认，尤其是其对 08、27 和 Skill 生命周期的长期影响；
3. 梳理 Evidence / Risk / ProjectGroup / Trae Spec Ingest / Automation 等候选概念的正式状态；
4. 为 Verify 阶段建立分级审计和 evidence 类型说明；
5. 为 specs → Rules / Skill / Tools / Web / Tests 派生路线建立结构化契约和 validator 覆盖矩阵；
6. 为现有核心 Skill 建立误触发、漏触发、越权执行、缺参、失败恢复、Human Gate 取消和状态机阻断 eval cases；
7. 为 Web MVP 定义只读范围、事实源读取方式、Validation Panel 和 Human Gate 卡片边界；
8. 为第三方 Skill 治理接管制定最小检查清单；
9. 为 Trae Spec Ingest 做一次真实 Dogfood，再判断是否正式 Skill 化；
10. 为工具权限面建立最小分级，先覆盖 Intake、Plan、Execute、Verify、Review、Close。
