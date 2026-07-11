---
id: study-0016
type: study
title: OpenAI Codex Harness Engineering 与 Symphony 对 LDVH 的学习方向调研
status: active
created: '2026-07-03T02:40:43+08:00'
updated: '2026-07-03T02:40:43+08:00'
summary: |
  本 Study 吸收 OpenAI 两篇工程文章：Harness Engineering 强调让仓库、文档、工具、验证、观测和品味约束对 Codex 可读、可执行、可校验；Symphony 强调把 issue tracker 变成 coding agent 的控制面，让每个开放任务都有隔离 workspace 和持续运行的 agent。对 LDVH 的核心启发是：应把 harness 和 orchestration 当作一套可进化工程系统，而不是单次提示技巧；Spark/Study/WorkCase、行动指南、运行时 Hook、Web 状态投影和 Git 追溯应共同服务“agent 能读懂、能执行、能验证、能回收结果”的闭环。
user_intent: |
  Human 阅读 OpenAI Harness Engineering 与 Symphony 文章后，要求新增一个 Spark，并关联一个 Study 来学习和吸收这两篇文章对 LDVH 的启发。
conclusion: |
  LDVH 应学习 OpenAI 的两个分层：第一层是 Harness Engineering，把知识、工具、验证、观测、约束和清理机制放进 agent 可消费的仓库与运行环境；第二层是 Symphony，把工作对象变成持续编排控制面，而不是让 Human 手动管理多个 Codex 会话。后续优先分流方向包括：LDVH Harness 成熟度模型、工作对象驱动编排、WorkCase / issue 状态机映射、过程输出与事实源吸收边界、agent legibility 质量检查、周期性事实源清理和 Codex App Server / SDK 集成边界。
urls:
  - ref: https://openai.com/index/harness-engineering/
    title: "Harness engineering: leveraging Codex in an agent-first world"
    summary: |
      OpenAI Engineering 文章，用于吸收 agent-first 仓库、短 AGENTS.md、结构化 docs、执行计划、可观测性、自定义 lint、反馈回路、merge 哲学和持续清理机制。
  - ref: https://openai.com/index/open-source-codex-orchestration-symphony/
    title: "An open-source spec for Codex orchestration: Symphony"
    summary: |
      OpenAI Engineering 文章，用于吸收 issue tracker 作为 agent 控制面、每个任务对应 workspace、任务 DAG、CI/PR shepherding、WORKFLOW.md 和 Codex App Server 编排思路。
  - ref: https://github.com/openai/symphony
    title: openai/symphony
    summary: |
      OpenAI Symphony 开源仓库，用于确认 Symphony 是工程预览和参考实现，定位为把项目工作变成隔离自治实现运行。
  - ref: https://github.com/openai/symphony/blob/main/SPEC.md
    title: Symphony Service Specification
    summary: |
      Symphony 语言无关服务规范，用于确认它把 issue tracker、per-issue workspace、WORKFLOW.md、重试、可观测性和安全姿态文档化为可实现契约。
  - ref: https://developers.openai.com/codex/app-server
    title: Codex App Server
    summary: |
      OpenAI Codex 开发者文档，用于确认 app-server 是可嵌入 Codex 线程、审批、历史和流式事件的 JSON-RPC 接口；LDVH 后续若做自动编排，应先明确 SDK / app-server 的职责边界。
input_refs:
  - spark-0043
  - study-0011
  - study-0015
  - specs/00-理念与构成.md
  - specs/01-保障与衔接.md
  - specs/02-AI行为规范.md
  - specs/03-事实源与Git溯源规范.md
  - specs/07-Code确定性执行规范.md
  - specs/08-Web信息同步规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
related_sparks:
  - spark-0043
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/00-理念与构成.md
  - specs/01-保障与衔接.md
  - specs/02-AI行为规范.md
  - specs/03-事实源与Git溯源规范.md
  - specs/07-Code确定性执行规范.md
  - specs/08-Web信息同步规范.md
  - specs/20-Spark-火花.md
  - specs/21-WorkCase-工作项.md
  - specs/24-Study-研究报告.md
  - ldvh-base/studies/study-0011-codex-worktree-subagent-thread-practices.md
  - ldvh-base/studies/study-0015-workbuddy-team-interaction-learning.md
archive_reason: null
---

# OpenAI Codex Harness Engineering 与 Symphony 对 LDVH 的学习方向调研

## 研究问题

本报告回答 `spark-0043` 提出的学习问题：OpenAI 的 Harness Engineering 文章和 Symphony 开源编排文章，哪些内容对 LDVH 的后续建设有稳定吸收价值，哪些只能作为外部工程参考，不能直接写成 LDVH 已具备能力或正式规则。

具体问题包括：

1. Harness Engineering 的核心不是哪一条工具技巧，而是什么样的工程系统；
2. Symphony 如何把 issue tracker、workspace、agent session、工作流文件和 proof-of-work 串成持续编排；
3. LDVH 当前已有 Spark、Study、WorkCase、ADR、Pitfall、specs、Code、Hook、Web 和管辖项目配置，和 OpenAI 文章中的实践相比还缺什么；
4. 哪些学习方向应进入 WorkCase、ADR、Pitfall、docs、specs、Code、Web、运行时扩展或行动指南；
5. 哪些边界必须保留，避免把 OpenAI 内部实践、Symphony 参考实现或 Codex App Server 能力误写成 LDVH 当前事实。

## 输入与边界

本次输入包括 OpenAI 官网 Engineering 栏目的 Harness Engineering 文章、OpenAI 官网 Symphony 文章、`openai/symphony` 开源仓库、Symphony `SPEC.md`、Codex App Server 开发者文档，以及 LDVH 内部的事实模型与既有研究资料。

OpenAI 两篇文章提供的可吸收事实包括：

- Harness Engineering 文章描述了一个从空仓库开始、全部代码由 Codex 生成的内部产品实验；重点不是“零人工写代码”本身，而是 Human 把工作上移到环境、脚手架、规范、反馈回路、工具和验证系统设计；
- 该文章强调短 `AGENTS.md` 应作为地图，结构化仓库文档和执行计划才是系统事实源；agent 看不见的聊天、隐性知识或外部文档，在运行时等同于不存在；
- 该文章还强调 UI、日志、指标、trace、Chrome DevTools、E2E 测试、自定义 lint、CI、文档清理和质量原则都应成为 Codex 可直接使用的反馈回路；
- Symphony 文章描述了从“人监督多个 Codex 会话”转向“工作对象驱动 agent 编排”的模式：issue tracker 成为控制面，开放任务对应隔离 workspace 和持续运行 agent；
- Symphony 进一步把复杂特性和迁移拆成依赖 DAG，让 agent 只处理未阻塞任务，并通过 CI、rebase、冲突处理、视频 walkthrough、review packet 等 proof-of-work 减少 Human babysitting；
- Symphony `SPEC.md` 明确它是 scheduler / runner / tracker reader，不把 ticket 写入逻辑内置在 orchestrator 内，workflow policy 应放在仓库拥有的 `WORKFLOW.md` 中，安全姿态由实现文档化。

边界如下：

- 本报告不声称 LDVH 已具备 OpenAI 内部 harness 或 Symphony 的完整能力；
- 本报告不修改 specs、Code、Web、Hook、运行时入口或事实模型字段；
- 本报告不把 Symphony 参考实现当作 LDVH 必须采用的技术栈；
- 本报告不把 Linear 作为唯一 issue tracker 假设，LDVH 的工作对象可以是 Spark、WorkCase 或外部 tracker；
- 本报告不把 Codex App Server / SDK 集成作为默认落地路线，只把它作为后续编排技术边界候选；
- 文章和文档会继续变化，后续正式实现前应重新核对官方资料和当前 Codex 能力。

## 关键发现

### 一句话判断

OpenAI 两篇文章对 LDVH 的共同启发是：agent-first 工程不是让 AI 多写代码，而是把“环境、知识、约束、工作状态、验证和回收”设计成 agent 能直接操作的系统。

LDVH 已经有事实源、行动对象、规范、Code、Hook 和 Web 的雏形，但还需要更明确地区分三层：

| 层级 | OpenAI 文章中的表达 | LDVH 应学习的表达 |
|---|---|---|
| Harness | agent 可读的仓库知识、工具、测试、观测、lint、反馈回路 | 事实源、行动指南、Hook、Code、验证、Web 状态和质量检查共同构成的执行环境 |
| Orchestration | Symphony 持续读取 issue tracker，为每个开放任务运行 agent | WorkCase / Spark / 外部 issue 驱动的任务编排、workspace 隔离、状态机和 proof-of-work |
| Governance | Human 判断、文档化流程、约束编码、周期性清理 | Human Gate、ADR、Pitfall、事实源吸收边界、周期性整理和 Git 追溯 |

这说明 LDVH 后续不应只继续堆规范，也不应只优化 Web UI。真正有价值的是把规范、Code、运行时和 Web 合起来，形成 agent 可执行的工作系统。

### Harness Engineering 的核心：让仓库成为 agent 可读环境

Harness Engineering 文章中最重要的判断，是 Human 的职责从手写代码转向设计环境、指定意图和构建反馈回路。对 LDVH 来说，这非常贴近现有理念：AI 行为不能只靠上下文提醒，必须靠事实源、运行时入口、Code 检查和验证证据共同约束。

具体可吸收点如下：

| OpenAI 实践 | LDVH 吸收方向 |
|---|---|
| 短 `AGENTS.md` 作为地图，结构化 docs 承载知识 | LDVH 的行动指南应继续做“入口地图”，不要把所有规则塞进单一长提示 |
| 执行计划、设计历史、质量文档进仓库 | WorkCase、Study、ADR、Pitfall 和 docs 应继续作为 Git 可追溯事实层 |
| UI、日志、指标、trace 对 Codex 可读 | Web / runtime / hook 输出应变成可查询、可回指、可验证的过程投影 |
| 自定义 lint 和结构测试注入修复指引 | Code 检查不只报错，还应告诉 AI 回到哪个事实源、哪个字段或哪个 Gate |
| Human taste 被写回文档或工具 | Review 反馈、失败模式和质量偏好应分流到 ADR、Pitfall、specs 或 Code |
| 周期性 doc gardening / cleanup | LDVH 需要周期性事实源清理和 stale 规则扫描，不靠人工一次性大清理 |

一个关键学习点是“agent legibility”。人能理解但 agent 读不到、查不到、验证不了的信息，不应被当作稳定工程资产。LDVH 当前已有这个方向，但还可以进一步把可读性拆成可检查维度：路径可发现、关系可回指、状态可枚举、验证可复跑、输出可分流、门禁可解释。

### Symphony 的核心：把工作对象变成控制面

Symphony 文章真正重要的地方，不是“用 Linear”或“开很多 Codex session”，而是把工作从会话抽象成 deliverable。OpenAI 的表述里，PR 和 session 只是手段，issue / task / milestone 才是团队组织工作的对象。

这对 LDVH 很直接。LDVH 已有 Spark、Study、WorkCase、ADR 和 Pitfall，但当前大多数编排仍由主线程即时判断。Symphony 提醒我们：后续应让工作对象自己携带足够的调度信息，让 agent 可以从对象状态进入执行，而不是依赖聊天里临时记忆。

可吸收结构包括：

| Symphony 结构 | LDVH 对应候选 |
|---|---|
| Issue tracker 控制面 | WorkCase 列表、Spark 待分流队列、外部 issue 适配层 |
| 每个开放任务一个 workspace | Codex worktree / Git worktree / cloud task / 本地隔离目录 |
| 状态机驱动 agent 生命周期 | WorkCase status、execution item、review / verification / Human Gate |
| DAG 依赖 | WorkCase dependency / blocked_by / followup_refs 候选字段或派生关系 |
| `WORKFLOW.md` 仓库工作流契约 | LDVH 行动模板、运行时协议、目标项目本地工作流文档 |
| Proof-of-work packet | 验证命令、CI 状态、diff、视频、截图、review 结论、残留风险 |
| Orchestrator 不内置业务写入 | LDVH Code / Runtime 只做调度和候选，不代替 AI / Human 判断事实源写入 |

这说明 LDVH 后续可以研究“WorkCase as orchestration control plane”：WorkCase 不只是静态计划文件，而是可被运行时或行动指南读取的任务控制对象。

### Harness 和 Symphony 是先后关系，不是替代关系

Symphony 能工作，是因为底层仓库已经做了 harness engineering。OpenAI 文章里也明确提到：第一版只是 tmux 轮询加 subagents，不够可靠；后来放进 agent-friendly 仓库和 App Server 模式后，才有更稳定的编排基础。

对 LDVH 的结论是：不要直接跳到“自动给每个 Spark / WorkCase 派 agent”。如果底层事实源、验证、运行时、写入边界、工具权限、状态投影和失败恢复还不够清楚，自动编排只会放大混乱。

合理顺序应是：

1. 先定义 LDVH harness 成熟度：事实源可读、入口可路由、工具可调用、验证可复跑、失败可回收；
2. 再定义 WorkCase / Spark 的最小可编排状态机；
3. 再实验单一对象到单一 workspace 的 agent run；
4. 再加入依赖、并发、重试、CI / review / proof-of-work；
5. 最后再考虑外部 issue tracker、Codex App Server / SDK 或长期 daemon。

这条顺序可以避免把 Symphony 当作一个可以直接安装的万能工具。

### 对 LDVH 事实源的启发

Harness Engineering 文章对 LDVH 最大的肯定，是“仓库内事实源”方向是正确的。OpenAI 文章把聊天、Google Docs、Slack 和隐性知识视为 agent 不可见上下文；LDVH 的事实源边界也在解决同一问题。

但 LDVH 需要进一步补强两类事实：

| 缺口 | 说明 |
|---|---|
| 过程事实 | agent run、子 Agent 输出、测试、截图、日志、review、CI、重试和失败原因目前还没有统一过程投影 |
| 吸收事实 | 某个过程输出是否已被主控采纳、验证通过、进入事实源、还需 Human Gate，目前仍主要靠正文描述 |

Symphony 的 proof-of-work packet 和 Harness 的 observability stack 都说明：过程输出不等于事实源，但过程输出必须可查询、可回收、可验证。LDVH 后续应把这点写清楚，避免两个极端：一是把过程日志直接当事实源，二是完全不保存过程证据。

### 对 LDVH Web 的启发

OpenAI 两篇文章都隐含一个 Web / UI 学习方向：Human 不应被迫看完整 agent 内部过程，而应看到状态、证据和需要判断的点。

LDVH Web 后续可以学习：

- Dashboard 区分 pending work object、active run、blocked dependency、review needed、verification failed 和 fact absorbed；
- ObjectDetail 展示来源对象、派生任务、相关 Study、proof-of-work、验证命令和残留风险；
- Study / WorkCase 详情中明确“这是研究结论”“这是执行状态”“这是正式事实源吸收”；
- 对 Spark 关联 Study 的情况显示“已研究但未分流完成”，避免误读为 resolved；
- 对自动编排输出显示 workspace、agent run、CI / review / screenshot / video 等证据引用；
- 保持工作界面密集、可扫描、以状态和证据为主，不做装饰性团队卡片。

这与既有 `study-0015` 对 WorkBuddy 团队交互的学习方向可以合并阅读：WorkBuddy 提醒“角色和团队状态要显性”；Symphony 提醒“工作对象和运行状态要显性”；Harness Engineering 提醒“仓库知识和反馈回路要显性”。

### 对运行时和 Code 的启发

Symphony `SPEC.md` 的一个重要边界是：orchestrator 是 scheduler / runner / tracker reader，ticket 写入通常由 coding agent 通过 workflow/runtime 工具完成。这对 LDVH 很有价值，因为它避免把确定性 Code 写成“业务判断者”。

LDVH 后续 Code / Runtime 可学习的边界是：

| 能力 | 可以由 Code / Runtime 做 | 不应由 Code / Runtime 做 |
|---|---|---|
| 对象发现 | 找 pending Spark / WorkCase、读取状态、生成候选 read plan | 判断某议题是否有价值 |
| workspace 管理 | 建议或创建隔离工作区、记录 run id、检查目录边界 | 判定变更内容是否已满足 Human 意图 |
| 调度 | 根据状态和依赖生成候选执行队列 | 擅自越过 Human Gate 派发高风险写入 |
| 验证 | 运行确定性命令、收集退出码、关联 evidence | 把测试通过等同于事实源吸收完成 |
| 回收 | 提示应更新 Spark / Study / WorkCase / ADR / Pitfall | 直接关闭对象或修改长期决策 |

Codex App Server / SDK 可以作为后续技术路线，但必须先决策：LDVH 是做本地辅助 orchestrator、Codex app 内部工作流、还是外部 issue tracker daemon。三者权限、认证、线程历史、审批、成本和失败恢复边界不同。

### 对现有 LDVH 对象的映射

OpenAI 两篇文章可以映射到 LDVH 的已有对象，而不是强迫新增事实模型：

| LDVH 对象 | 吸收方式 |
|---|---|
| Spark | 捕获 harness / orchestration 缺口、自动编排风险、待研究议题 |
| Study | 沉淀外部文章、工具、系统和实践调研 |
| WorkCase | 承接具体实现：成熟度模型、状态机、Web 视图、运行时实验 |
| ADR | 决策是否引入自动编排、Role Contract、App Server / SDK、状态机扩展 |
| Pitfall | 记录误把过程输出当事实源、误把 Study 关联当 Spark resolved、误把 agent 完成当工作完成 |
| specs | 只吸收稳定规则，不吸收文章叙述或产品细节 |
| Code | 做确定性检查、导航、状态投影、引用完整性和验证 evidence |
| Web | 展示对象状态、工作队列、证据、门禁和吸收状态 |

这说明本 Study 后续最适合先产生 WorkCase 和 ADR 候选，而不是直接改 `specs/20`、`specs/21` 或运行时代码。

### 边界风险

吸收 OpenAI Harness / Symphony 时需要避免以下误读：

1. 把“0 行人工代码”误读成 LDVH 也应禁止 Human 写任何代码；
2. 把 OpenAI 内部仓库实践误读成所有项目都应使用同样 merge philosophy；
3. 把 Symphony 当作成品平台，而不是参考规范和工程预览；
4. 把 Linear 当作 LDVH 唯一控制面；
5. 把每个 pending Spark 都自动派 agent，跳过分流判断和 Human Gate；
6. 把 agent run 完成、CI 通过或视频生成误当 WorkCase 已关闭；
7. 把 Study 形成误当 Spark resolved；
8. 把 Codex App Server / SDK 能力误写成当前 LDVH 已集成能力；
9. 把更多自动化当作更少治理，忽视权限、成本、失败恢复和数据暴露面；
10. 把文档越写越长当作 agent legibility，忽视索引、结构、检查和渐进披露。

## 建议

1. 新建后续 WorkCase：定义 LDVH Harness 成熟度模型，覆盖事实源可读性、工具可用性、验证可复跑、运行时状态、Web 投影、Git 追溯和清理机制。
2. 新建后续 WorkCase：设计 WorkCase / Spark 驱动的最小编排实验，只做“一个对象 -> 一个隔离 workspace -> 一个 proof-of-work 回收”的窄闭环。
3. 新建 ADR 候选：决策 LDVH 是否引入自动 orchestrator，以及它与行动指南、Hook、Codex App Server / SDK、外部 issue tracker 的边界。
4. 新建 Pitfall 候选：记录“过程输出、agent 完成、Study 关联不能直接等同事实源吸收或对象关闭”的风险。
5. 在 Web 方向设计工作对象编排视图：pending / running / blocked / review / verified / absorbed / needs Human Gate 等状态必须可扫描。
6. 在 Code 方向增加确定性检查候选：Spark 关联 Study 时不得自动 resolved；WorkCase closure evidence 必须和 proof-of-work / verification evidence 分开。
7. 在运行时方向研究 run record / workspace record / proof-of-work packet，但先作为过程投影，不进入现有事实模型字段闭集。
8. 把 `study-0011`、`study-0015` 和本 Study 合并阅读：`study-0011` 解决 Codex worktree / subagent 并行实践，`study-0015` 解决团队交互显性化，本 Study 解决 harness + work-object orchestration。
9. 后续若研究 Symphony 实装，应优先读 `SPEC.md`，而不是只读博客；实现前必须明确信任环境、sandbox、审批、token 暴露、tracker 写入和失败恢复。
10. 先补 harness，再谈持续编排；如果事实源、验证和门禁还不稳，自动派发只会放大错误。

## 后续分流

| 候选 | 建议承载 | 原因 |
|---|---|---|
| LDVH Harness 成熟度模型 | WorkCase | 把事实源、工具、验证、观测、Web、Git 和清理机制统一成可检查梯度 |
| WorkCase / Spark 最小自动编排实验 | WorkCase | 验证对象驱动 workspace 和 proof-of-work 回收，不直接全量自动化 |
| 自动 orchestrator 边界 | ADR | 需要长期决策它与行动指南、Hook、Codex App Server / SDK、issue tracker 和 Human Gate 的关系 |
| 过程输出不等于事实源吸收 | Pitfall | 防止 CI、视频、agent 完成、Study 形成被误当对象关闭证据 |
| Work object status projection | Web WorkCase | 让 Human 可以扫描对象状态、依赖、运行证据和门禁，而不是翻长对话 |
| Run record / proof-of-work packet | 运行时扩展 WorkCase | 为 workspace、agent run、验证、review、截图、视频、残留风险建立过程投影 |
| Agent legibility 检查 | Code / specs WorkCase | 检查路径、引用、状态、关系、验证和文档 stale 风险 |
| 周期性事实源清理 | WorkCase 或行动模板 | 学习 OpenAI doc-gardening / golden principles，避免规则和事实对象漂移 |

本 Study 完成后，`spark-0043` 仍应保持 pending。只有当上述学习方向被 WorkCase、ADR、Pitfall、docs、specs、Code、Web 或运行时扩展完整承接，并且剩余议题被确认处理后，才能考虑关闭对应 Spark。
