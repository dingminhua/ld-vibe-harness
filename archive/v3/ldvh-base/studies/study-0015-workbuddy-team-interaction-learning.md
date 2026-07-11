---
id: study-0015
type: study
title: WorkBuddy 专家团团队交互模式与 LDVH 学习方向调研
status: active
created: '2026-07-02T18:34:24+08:00'
updated: '2026-07-02T18:34:24+08:00'
summary: |
  本 Study 调研 WorkBuddy / CodeBuddy 团队交互模式对 LDVH 的学习价值。核心结论是：WorkBuddy 值得学习的不是“多开几个 Agent”，而是把专家角色、方法论、工具链、团队席位、共享任务列表、成员状态、直接沟通、计划审批、后台任务和结果整合显性化。LDVH 应吸收为“团队编排层”的设计方向：角色契约、任务卡、计划门禁、成员消息、状态投影、质量复核和成本/权限边界都应成为可追踪结构；但 WorkBuddy 的专家团运行状态、截图 UI 或外部工具输出不能替代 LDVH 的 Spark、Study、WorkCase、ADR、Pitfall、specs 和 Git 文件事实源。
user_intent: |
  Human 提供 WorkBuddy 团队交互界面截图，要求创建 Spark 并安排 Study 调研这种团队交互模式，分析 LDVH 后续应学习和吸收的方向。
conclusion: |
  LDVH 应把 WorkBuddy 式团队交互作为下一阶段行动编排和 Web 表达的重要参考：主控 AI 不只是执行者，还应能显式组织角色团队、分配任务、读取成员状态、要求计划审批、整合交付并把质量复核留痕。优先学习方向包括 Role Contract、Team Session / Task List、Result Review、TaskOutput 状态投影、专家/Skill/MCP 组合边界、Human Gate 与权限分层，以及团队协作视图。但正式落地前应先形成 WorkCase 或 ADR，避免把外部产品的专家团、Agent Teams 或后台任务状态直接写成 LDVH 事实模型规则。
urls:
  - ref: https://www.codebuddy.cn/work/
    title: WorkBuddy - AI Agent 办公新范式
    summary: |
      官方产品页，用于确认 WorkBuddy 将自身定位为 AI Agent 办公工具，强调自主规划、复杂任务交付和多 Agents 并行工作。
  - ref: https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Expert-Center
    title: WorkBuddy 专家功能说明
    summary: |
      官方 WorkBuddy 文档，用于确认专家是“人设 + 方法论 + 工具链”的角色切换机制，专家团是由多位专家分工协作、由团长拆解并整合交付的协作执行机制。
  - ref: https://www.codebuddy.ai/docs/cli/agent-teams
    title: CodeBuddy Agent Teams
    summary: |
      官方 CodeBuddy CLI 文档，用于确认 Agent Teams 的团队负责人、独立成员、共享任务列表、成员直接消息、状态栏、计划审批、Delegate Mode 和任务依赖等机制。
  - ref: https://www.codebuddy.ai/docs/cli/sub-agents
    title: CodeBuddy Sub-Agents
    summary: |
      官方 CodeBuddy CLI 文档，用于确认 Sub-Agent、background agents、TaskOutput、可恢复执行、工具权限和后台任务状态等机制。
  - ref: https://www.tencent.com/zh-cn/articles/2202350.html
    title: 腾讯云首发效率智能体工具集
    summary: |
      腾讯官方动态，用于确认 WorkBuddy 企业版、员工与 AI 协作、腾讯文档和乐享能力接入、企业知识沉淀和能力复用等方向。
input_refs:
  - spark-0042
  - /var/folders/gh/szvhx1md1mn9qy9n6p2b2w5h0000gn/T/codex-clipboard-453a907e-11b4-4154-af72-45dea8e5d4c0.png
  - specs/00-理念与构成.md
  - specs/01-保障与衔接.md
  - specs/02-AI行为规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
  - ldvh-base/studies/study-0011-codex-worktree-subagent-thread-practices.md
related_sparks:
  - spark-0042
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/00-理念与构成.md
  - specs/01-保障与衔接.md
  - specs/02-AI行为规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
  - ldvh-base/studies/study-0011-codex-worktree-subagent-thread-practices.md
archive_reason: null
---

# WorkBuddy 专家团团队交互模式与 LDVH 学习方向调研

## 研究问题

本报告回答一个面向 LDVH 后续建设的问题：WorkBuddy 截图和官方资料中呈现的“专家 / 专家团 / 团队成员 / TaskOutput / 任务状态”交互模式，哪些值得 LDVH 学习，哪些只能作为外部产品参考，不能直接吸收为 LDVH 事实源规则。

具体问题包括：

1. WorkBuddy 式专家团交互的核心结构是什么；
2. 它与 CodeBuddy Sub-Agents、Agent Teams 和 background TaskOutput 的关系对 LDVH 有什么启发；
3. LDVH 当前已有 Spark、Study、WorkCase、ADR、Pitfall、Human Gate 和 Web 对象展示，团队协作层还缺什么；
4. 哪些学习方向应进入 WorkCase、ADR、Pitfall、docs、specs、Code、Web 或运行时扩展；
5. 哪些边界必须保留，防止把外部产品运行态误写成 LDVH 权威事实。

## 输入与边界

本次输入包括 Human 提供的 WorkBuddy 任务界面截图、WorkBuddy 官方产品页、WorkBuddy 专家功能说明、CodeBuddy CLI 的 Sub-Agents 和 Agent Teams 文档、腾讯官方产品动态，以及 LDVH 既有 `study-0011` 对 Codex 工作树、子 Agent 与新建对话并行实践的调研。

截图提供的现场观察包括：

- 顶部出现多个角色席位，例如总编辑和质量审核员；
- TaskOutput 区域显示等待模型响应，说明成员或后台任务的输出可被单独观察；
- 输入区支持 Craft、Ask、Plan 等意图模式；
- 召唤菜单中出现专业文档生成团队、UI 设计师、内容创作专家等专家或专家团；
- 底部同时出现模型、技能、连接应用、默认权限等运行时选择。

官方资料提供的可确认事实包括：

- WorkBuddy 产品页强调 AI Agent 办公、复杂任务交付和多 Agents 并行；
- WorkBuddy 专家文档把专家定义为角色切换机制，专家团定义为协作执行机制；
- CodeBuddy Agent Teams 文档描述团队负责人、独立成员、共享任务列表、消息系统、状态栏、计划审批、Delegate Mode 和任务依赖；
- CodeBuddy Sub-Agents 文档描述子 Agent、后台任务、TaskOutput、可恢复 Agent 和工具权限；
- 腾讯官方动态强调 WorkBuddy 企业版、人和 AI 协作、知识沉淀和能力复用。

边界如下：

- 本报告不把 WorkBuddy 截图中的任何 UI 状态写成 LDVH 已支持能力；
- 本报告不修改 specs、Code、Web、Hook 或运行时入口；
- 本报告不声称 LDVH 应复制 WorkBuddy 的产品形态；
- 本报告只沉淀学习方向和后续分流建议，正式落地必须进入对应事实源；
- WorkBuddy / CodeBuddy 文档和产品能力变化较快，后续实现前应再次核对官方资料。

## 关键发现

### 一句话判断

WorkBuddy 值得 LDVH 学习的核心，是把“一个 AI 在聊天里隐式调度多个角色”变成“用户可见、状态可查、职责可分、结果可整合、权限可控”的团队协作界面。

这对 LDVH 很关键。LDVH 的目标不是让 AI 更会聊天，而是让 AI 工作可执行、可验证、可交还。团队协作一旦只停留在自然语言提示里，就会出现角色责任不清、复核缺席、后台任务状态丢失、多个结论无法整合、Human 不知道该信谁的问题。WorkBuddy 的专家团和 Agent Teams 模式恰好把这些隐性结构显性化。

### WorkBuddy 专家团的结构启发

WorkBuddy 专家文档把专家视为“人设 + 方法论 + 工具链”，把专家团视为多位专家加协作流程。这个拆分比单纯的 prompt role 更具体：角色不是一句“你是质量审核员”，还包括它使用什么方法、可调用什么工具、在什么任务中被召唤、对最终交付承担什么职责。

对 LDVH 的学习方向是：后续 Role Contract 不应只定义角色名称和语气，而应至少表达：

| 维度 | LDVH 应学习的表达 |
|---|---|
| 角色身份 | 角色 ID、名称、职责边界、适用场景 |
| 方法论 | 该角色检查什么、如何形成结论、必须指出哪些不确定性 |
| 工具链 | 可用 Skill、MCP、Code、Web、文件读取或写入权限 |
| 输入契约 | 必读事实源、任务卡、截图、外部资料或验证命令 |
| 输出契约 | 交付摘要、证据路径、风险、建议分流和是否可直接采用 |
| 复核责任 | 哪些角色只做建议，哪些角色负责质量审核，谁汇总最终结论 |
| Human Gate | 哪些结论必须等待 Human 或主控 AI 确认后才能写入事实源 |

LDVH 已有事实源边界和 Human Gate，但角色契约仍主要靠对话即时说明。WorkBuddy 的专家团模式说明，角色应成为可复用、可审计的调度资产，而不是临时称谓。

### Agent Teams 的结构启发

CodeBuddy Agent Teams 文档给出了更工程化的团队协作结构：一个 lead 负责协调、分配任务和聚合结果，成员有独立上下文窗口，成员之间可以直接消息沟通，并共享任务列表。任务列表支持 pending、in progress、completed，任务还能表达依赖；复杂或高风险任务可以要求成员先提交 plan，lead 再批准。

这对 LDVH 有四个直接启发：

1. **主控责任要显性化**：主控 AI 应维护任务卡、事实源边界、验证要求、Human Gate 和最终交付，不应把成员输出直接当最终答案。
2. **任务列表要结构化**：团队任务不应只在聊天里散落，应有可被 Web / Code 派生展示的 task list、owner、status、dependency、evidence。
3. **成员通信要可回收**：成员之间可以直接沟通，但最终应回收到主控摘要和事实源变更建议，避免证据链丢失。
4. **计划审批要进入门禁**：高风险写入、跨文件改造、规则修改和外部动作，应先由成员给 plan，再由 lead 或 Human Gate 确认。

LDVH 当前的 WorkCase 已有执行、验证和关闭边界，但多成员协作的中间状态尚未成为一等结构。后续可以先不修改 WorkCase 状态机，而是增加团队编排的派生对象或行动模板。

### TaskOutput 与后台任务的结构启发

CodeBuddy Sub-Agents 文档中的 background agents 和 TaskOutput 说明了另一类重要能力：长期运行或并行任务可以在后台执行，主线程继续交互，随后通过 TaskOutput 查询状态和结果。截图中 “TaskOutput / 等待模型响应” 与这种模式在交互语义上接近：用户看到的是一个可查询、可等待、可失败、可返回结果的任务输出槽，而不是混进主聊天的一大段中间日志。

对 LDVH 的学习方向是：运行时任务结果应进入“过程输出投影”，而不是直接污染事实源。一个合理边界是：

- 后台任务状态可以展示为 pending、running、completed、failed、cancelled；
- TaskOutput 可以作为过程证据输入 Study、WorkCase 或 Spark；
- 只有经主控 AI 整理、验证和 Human Gate 后，结果才可写入 `ldvh-base/`、specs、Code 或 Web；
- Web 可以学习这种输出槽，把多成员结果、验证命令、审查结论和残留风险放进可读面板；
- Code 可增加确定性检查，识别“后台任务完成”与“事实源已吸收”之间的差异。

这能防止一个常见误读：成员完成任务或 TaskOutput 返回成功，不等于 LDVH 工作项已完成，更不等于规则、代码或研究结论已经稳定吸收。

### 角色团队与 LDVH 当前结构的差距

LDVH 已经具备事实模型和基础治理能力：

| LDVH 已有能力 | 现状 | 相对 WorkBuddy 的缺口 |
|---|---|---|
| Spark | 可保留未成型议题 | 尚不能直接表达一个议题需要哪些专家参与 |
| Study | 可沉淀研究报告 | 尚未固定研究团队、审稿角色和证据回收格式 |
| WorkCase | 可承接执行闭环 | 多成员任务、依赖、成员状态和计划审批仍偏隐性 |
| ADR | 可承接长期决策 | 还缺团队编排是否成为正式机制的决策 |
| Pitfall | 可沉淀错误经验 | 可补充“成员输出被误当事实源”的风险 |
| Human Gate | 可控制关键写入 | 还需明确团队 lead、成员和 Human 的审批关系 |
| Web | 可展示对象和阅读面板 | 还缺团队席位、任务状态、成员输出和结果整合视图 |
| Runtime/Hook | 可做目标项目治理 | 还缺团队运行态事件、成员输出和工具权限的统一 payload |

因此，LDVH 的学习方向不应是“马上做一个专家团 UI”，而是先把团队协作拆成可治理的概念：角色契约、团队会话、任务列表、成员输出、结果整合、复核结论、权限边界和事实源吸收。

### 对 LDVH Web 的启发

WorkBuddy 截图中的强信号是：用户在输入前就能看到当前协作结构。谁是总编辑、谁是质量审核员、谁还在等待响应、可召唤哪些专家、当前是 Craft / Ask / Plan 哪种意图，都是交互面的一部分。

LDVH Web 后续可学习的不是视觉风格，而是信息架构：

- 在 WorkCase 或 Study 详情中展示参与角色；
- 展示主控、研究、执行、审核、总结等角色状态；
- 把角色输出折叠到可展开的证据面板，而不是塞进正文；
- 对 AI 建议、已验证事实、Human 决策使用不同视觉语义；
- 对等待中、失败、需审批和已吸收的结果使用不同状态；
- 让用户能从对象进入相关 Spark、Study、WorkCase、ADR、Pitfall；
- 明确“可召唤专家”只是动作入口，不是事实源状态。

这与现有 Study 阅读面板、ObjectDetail 和 Dashboard 方向相容，但需要避免把页面变成装饰型团队卡片。LDVH 的 Web 价值应是快速判断“谁做了什么、依据是什么、是否可写入、还缺哪个门禁”。

### 对 LDVH 运行时扩展的启发

WorkBuddy / CodeBuddy 模式还提示 LDVH：团队协作不是纯 UI。底层需要 runtime payload 和事件结构支持，否则 Web 只会展示静态文字。

后续可研究的运行时字段包括：

| 字段方向 | 作用 |
|---|---|
| team_id / session_id | 绑定一次团队协作过程 |
| lead_id | 表示主控角色或主线程 |
| member_id / role_id | 标识成员和角色契约 |
| task_id | 绑定成员承担的任务 |
| task_status | 表达 pending、running、completed、failed 等过程状态 |
| dependency_refs | 表达任务依赖 |
| output_ref | 指向成员输出或 TaskOutput 过程材料 |
| approval_required | 标记是否需要 plan approval 或 Human Gate |
| fact_absorption_status | 区分过程完成、主控采纳、验证通过和事实源已吸收 |

这些字段如果落地，应先进入运行时扩展或行动编排 WorkCase，不应直接塞进 Spark / Study / WorkCase 现有字段闭集。

### 边界风险

WorkBuddy 式团队交互如果被 LDVH 误吸收，会带来几个风险：

1. 把外部专家团状态当作 LDVH 事实源；
2. 把成员“完成”误当 WorkCase 关闭；
3. 把质量审核员的自然语言意见误当验证证据；
4. 把专家角色 prompt 当作稳定规则；
5. 把 UI 中的角色席位当作真实权限隔离；
6. 把并行执行的速度收益压过事实源边界、测试和 Human Gate；
7. 忽略 token、积分、工具权限、外部服务和数据安全成本。

LDVH 应学习结构，不复制运行态权威。团队交互可以提升工作效率，但只有被验证、整理并写入正确事实源的内容，才成为 LDVH 稳定资产。

## 建议

1. 新建后续 WorkCase，研究 LDVH Team Orchestration 最小行动模板：角色、任务、成员输出、复核、验证和交还格式。
2. 新建 ADR 候选，决策 Role Contract 是否成为 LDVH 正式能力资产，以及它与 Skill、MCP、Agent、WorkCase 的边界。
3. 在 Web 方向上设计团队协作状态视图，优先服务 WorkCase / Study：显示参与角色、任务状态、输出证据、复核结论和事实源吸收状态。
4. 在 Code 方向上增加派生检查：团队任务引用的事实对象是否存在、成员输出是否已被主控采纳、验证证据是否独立于成员完成状态。
5. 在运行时扩展方向上研究 team/session/member/task/output payload，但先作为实验性过程数据，不进入现有事实模型字段闭集。
6. 把 WorkBuddy 专家团模式与既有 `study-0011` 并行实践合并阅读：Codex worktree / subagent 解决隔离和上下文问题，WorkBuddy / CodeBuddy team 模式补足团队状态、成员通信和任务列表。
7. 优先沉淀“总编辑 + 质量审核员 + 专业执行角色”的最小 LDVH 团队样式，用于文档生成、研究报告、规范审查和 Web 设计复核四类场景。
8. 明确成本和权限提示：团队模式需要更多模型调用、工具权限和数据暴露面，必须在 Human Gate 或运行时入口中可见。

残留不确定性：

- WorkBuddy 产品能力与 CodeBuddy CLI 能力不是同一个承载面，不能把 CLI Agent Teams 全量推断到 WorkBuddy UI；
- 截图只能证明某次界面观察，不能证明所有用户或版本都有相同功能；
- 官方文档更新较快，后续实现前应重新核对专家团、Agent Teams、TaskOutput、权限模式和企业版协作能力；
- 本报告没有实际运行 WorkBuddy 专家团任务，也没有验证其产物质量。

## 后续分流

| 候选 | 建议承载 | 原因 |
|---|---|---|
| LDVH Team Orchestration 最小行动模板 | WorkCase | 把主控、成员、任务列表、计划审批、输出回收和验证交还变成可执行流程 |
| Role Contract 是否入正式能力资产 | ADR | 需要决策角色契约与 Skill、MCP、Agent、WorkCase、Human Gate 的长期边界 |
| 团队协作状态 Web 视图 | Web WorkCase | 让 Human 可见成员状态、输出、复核和事实源吸收，而不是只看聊天 |
| 成员输出不可直接成为事实源 | Pitfall | 防止后台任务、质量审核员意见或专家团完成状态被误用为验证证据 |
| Team runtime payload 草案 | 运行时扩展 WorkCase | 为 team_id、member_id、task_status、output_ref、approval_required 等过程字段建立实验边界 |
| Study / 文档生成专家团最小样式 | docs 或 WorkCase | 可先在 Study 研究、规范审查、文档生成场景试验“总编辑 + 审核 + 专业作者”结构 |

本 Study 完成后，`spark-0042` 仍应保持 pending。只有当上述学习方向被 WorkCase、ADR、Pitfall、docs、specs、Code、Web 或运行时扩展完整承接，并且剩余议题被确认处理后，才能考虑关闭对应 Spark。
