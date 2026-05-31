# LDVH 对 MCP Shrimp Task Manager 的借鉴评估

> 创建日期：2026-05-30
> 更新日期：2026-05-30
> 定位：LD Vibe Harness 对 MCP Shrimp Task Manager 的源码级借鉴评估
> 编号归属：`specs/evals/` 项目评估文档，编号仅用于排序和引用便利，不属于 specs 正式规范编号体系
> 调研边界：基于 `/Users/dmh2002/trae_projects/mcp-shrimp-task-manager` 本地仓库的 README、docs、src、tools/task-viewer 与配置文件进行分析，重点评估其对 LD Vibe Harness 的可借鉴方向
> 执行效力：本文为内部调研和方案比较，不直接构成 LD Vibe Harness 强制规则；结论进入 `specs/00-79` 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/02-LDVH术语规范.md`、`specs/01-LDVH目录说明.md`、`specs/10-事实源边界与承载规范.md`
> 相关规范：`specs/11-LDVH-AI协作规范.md`、`specs/12-LDVH工具基础规范.md`、`specs/13-LDVH生产对象基础规范.md`、`specs/14-LDVH行动模型基础规范.md`、`specs/20-生产对象集合索引.md`、`specs/50-行动模型集合索引.md`
> 参考项目：`/Users/dmh2002/trae_projects/mcp-shrimp-task-manager`

---

## 一、评估结论摘要

MCP Shrimp Task Manager 是一个面向 AI Agent 的 MCP 任务治理工具。它不是传统项目管理系统的简单 MCP 化，而是把 AI 编程过程拆解为可调用工具：任务规划、技术分析、反思、任务拆分、任务列表、执行指导、验证、更新、删除、查询、详情读取、研究模式、思维处理和项目规则初始化。其核心价值在于让 AI 在长上下文、多步骤开发中拥有结构化任务记忆、依赖顺序、执行指引、验证标准和跨会话恢复能力。

从源码看，Shrimp 的架构具有明显的“Prompt-first + JSON 持久化 + MCP 工具编排”特征。多数工具并不直接替 AI 写代码，而是通过工具调用读取或改变任务状态，并返回高结构化 Prompt，引导 AI 进入下一阶段。真正写入数据的环节主要集中在任务拆分、任务状态切换、验证完成、任务更新、任务删除和清空任务。数据层使用 `{DATA_DIR}/tasks.json` 与 `{DATA_DIR}/memory/`，并尝试对数据目录做本地 Git 版本化。Web 能力分为内嵌轻量 WebGUI 和独立 React Task Viewer，后者支持多项目 profile、任务表格、详情、编辑、历史、模板管理、Agent 管理、AI 批量分配 Agent 和 Chat Agent。

对 LD Vibe Harness 而言，Shrimp 最值得借鉴的不是某个具体 MCP 工具名称，也不是它的 JSON 数据格式或 Web 页面，而是它证明了一个重要方向：任务治理可以直接服务 AI 执行过程，而不是只服务人类看板。LDVH 的目标同样是让 AI 进入项目后知道该读什么、做什么、不能做什么、何时停下等待人确认，以及完成后如何把事实写回项目。因此，Shrimp 对 LDVH 的主要启发集中在四个方面：

1. 将 AI 行动拆成显式阶段，并让每个阶段都有可调用入口；
2. 将 Task 从简单 todo 升级为带依赖、执行指引、验证标准、关联文件和完成摘要的可执行对象；
3. 通过持久化任务事实维持跨会话连续性；
4. 用 Web Viewer 提升人对任务状态、历史、Agent 分配和模板的可观察性。

但 Shrimp 与 LDVH 的边界差异同样关键。Shrimp 的 `{DATA_DIR}/tasks.json`、memory 备份、Web Viewer 设置、模板目录、Agent 扫描结果和 OpenAI 交互结果属于工具运行数据或派生数据。LDVH 的最终事实源必须是 Git 可追踪文件，稳定事实应回到 `specs/`、`ldvh-base/`（工作区级目录）、`docs/` 或其他权威位置。LDVH 可以借鉴 Shrimp 的工具化流程、任务字段、验证动作、研究模式、Prompt 模板和可视化思路，但不能把 Shrimp 的 MCP Server 状态、工具私有数据目录、Web UI 状态或模型输出提升为 LDVH 的最终事实源。

本文建议：LDVH 后续建设不应照搬 Shrimp，而应将其能力拆解后重新映射到 LDVH 五类构成要素中：以 Git 文件作为最终事实源，以 LDVH 生产对象承载任务、证据、变更、风险和决策，以 LDVH 行动模型约束计划、拆解、执行、验证和回写，以 Rules / Skill / Agent 规范治理协作机制，以 Tools / Web 降低读取、校验、展示和受控写入成本。

---

## 二、Shrimp 项目结构与核心实现

### 2.1 技术定位与运行方式

Shrimp 的根包是 TypeScript ESM 项目，核心依赖包括 `@modelcontextprotocol/sdk`、`zod`、`zod-to-json-schema`、`uuid`、`dotenv`、`express` 和 `get-port`。根入口为 `src/index.ts`，构建产物为 `dist/index.js`，并通过 `bin.mcp-shrimp-task-manager` 暴露为可执行命令。

其基本运行方式是：

1. MCP 客户端通过配置启动 `dist/index.js`；
2. 服务读取环境变量，如 `DATA_DIR`、`TEMPLATES_USE`、`ENABLE_GUI`；
3. `src/index.ts` 创建 MCP Server，注册工具列表和工具调用分发；
4. AI 客户端调用工具，工具返回 Prompt 或修改任务数据；
5. 任务数据写入 `{DATA_DIR}/tasks.json`；
6. 可选启动内嵌 WebGUI，或使用独立 `tools/task-viewer` 查看和编辑任务。

这说明 Shrimp 的第一服务对象是 AI Agent。它并非先设计一套人类项目管理系统，再让 AI 填写表单，而是围绕 AI 的执行阶段设计 MCP 工具接口。

### 2.2 源码目录分工

Shrimp 的主要源码分工如下：

| 路径 | 作用 |
|---|---|
| `src/index.ts` | MCP Server 入口，负责工具注册、参数校验、调用分发和 stdio 连接 |
| `src/tools/task/` | 任务规划、分析、反思、拆分、执行、验证、查询、更新、删除等工具 |
| `src/tools/research/` | 研究模式工具 |
| `src/tools/thought/` | 思维处理工具 |
| `src/tools/project/` | 项目规则初始化工具 |
| `src/models/taskModel.ts` | 任务读写、创建、更新、依赖检查、复杂度评估、搜索和清空备份 |
| `src/types/index.ts` | Task、TaskStatus、RelatedFile、复杂度等核心类型 |
| `src/prompts/` | Prompt 生成器、模板加载器、中英文模板和工具描述模板 |
| `src/utils/paths.ts` | `DATA_DIR`、`tasks.json`、`memory/`、`WebGUI.md` 路径解析 |
| `src/utils/agentLoader.ts` | Agent 文件扫描与加载 |
| `src/utils/agentMatcher.ts` | 根据任务内容自动匹配 Agent |
| `src/web/webServer.ts` | 内嵌 Express WebGUI，提供任务 API 和 SSE 更新 |
| `tools/task-viewer/` | 独立 React + Node 任务查看器和管理界面 |

对 LDVH 有启发的是：Shrimp 把“工具能力、任务模型、Prompt 模板、Agent 匹配、Web 展示”分层实现，降低了单一工具入口的复杂度。LDVH 后续如构建自有工具，也应避免把 AI 流程、对象字段、Web 展示和文件写入混在一个不可治理模块中。

### 2.3 MCP 工具注册与调用分发

`src/index.ts` 注册的工具包括：

1. `plan_task`
2. `analyze_task`
3. `reflect_task`
4. `split_tasks`
5. `list_tasks`
6. `execute_task`
7. `verify_task`
8. `delete_task`
9. `clear_all_tasks`
10. `update_task`
11. `query_task`
12. `get_task_detail`
13. `process_thought`
14. `init_project_rules`
15. `research_mode`

这些工具通过 `zod` schema 校验输入，再由 MCP Server 分发到对应实现。工具描述也来自 Prompt 模板系统，而不是全部硬编码在入口文件中。

这对 LDVH 的借鉴意义是：AI 行动能力可以通过小而明确的工具接口暴露，而不是依赖一个笼统的“执行任务”入口。LDVH 若未来提供 MCP Server 或其他工具层，也应考虑把任务生命周期、对象查询、证据写入、Human Gate 检查、规则命中和上下文包生成拆成独立工具。

### 2.4 Task 数据模型

Shrimp 的 Task 类型位于 `src/types/index.ts`，核心字段包括：

| 字段 | 含义 |
|---|---|
| `id` | 任务唯一标识 |
| `name` | 任务名称 |
| `description` | 任务描述 |
| `notes` | 补充说明 |
| `status` | `pending`、`in_progress`、`completed`、`blocked` |
| `dependencies` | 依赖任务关系 |
| `createdAt` / `updatedAt` / `completedAt` | 时间字段 |
| `summary` | 完成摘要 |
| `relatedFiles` | 关联文件、类型、描述和行号范围 |
| `analysisResult` | 分析结果 |
| `implementationGuide` | 实现指南 |
| `verificationCriteria` | 验证标准 |
| `agent` | 分配的 Agent |

这个模型比普通 todo 更接近 LDVH 规划中的 Task 对象：它不仅描述“要做什么”，还描述“为什么做、依赖什么、看哪些文件、怎么做、如何验、由谁做、完成后留下什么摘要”。

LDVH 后续定义 `specs/12-Task-任务对象` 时，Shrimp 的字段具有重要参考价值，但需要按 LDVH 的事实源、状态机、Human Gate 和 Evidence 关系重新建模。例如，Shrimp 的 `summary` 可对应 LDVH 的关闭摘要或 Evidence 引用；`verificationCriteria` 可对应验收标准；`relatedFiles` 可对应影响文件或证据关联；`agent` 可对应执行者建议或调度记录，但不能替代 LDVH Agent 机制的事实源治理。

### 2.5 持久化与跨会话记忆

Shrimp 使用 `{DATA_DIR}/tasks.json` 保存当前任务，使用 `{DATA_DIR}/memory/` 保存清空任务时的历史备份，并尝试对数据目录执行 `git init`、`git add tasks.json` 和 `git commit`。路径由 `src/utils/paths.ts` 根据 MCP roots、`DATA_DIR` 和 fallback 规则计算。

需要注意的实现细节包括：

1. 默认任务文件结构为 `{ "tasks": [] }`；
2. 读取任务时会把日期字符串转回 `Date`；
3. `writeTasks(tasks, commitMessage)` 在有提交信息时尝试提交 `tasks.json`；
4. Git 提交失败不会中断主流程；
5. `clearAllTasks()` 只备份 completed tasks 到 memory，并清空当前任务；
6. `query_task` 可搜索当前任务和 memory 备份。

这说明 Shrimp 已意识到 AI 编程中的跨会话记忆问题，并用本地 JSON + 本地 Git 历史缓解上下文丢失。对 LDVH 而言，这个目标高度正确，但实现边界必须不同：LDVH 不应把工具私有 `tasks.json` 作为权威任务事实源。LDVH 的稳定任务、证据、变更和决策应进入 `ldvh-base/`（工作区级目录）下对应对象实例，工具缓存、索引或 Viewer 配置只能作为派生层或受控写入入口。

### 2.6 Prompt-first 工具设计

Shrimp 的很多工具本质上是“状态读取或状态更新 + Prompt 生成器”。例如：

1. `plan_task` 接收自然语言描述，返回规划 Prompt，不直接创建任务；
2. `analyze_task` 接收任务摘要和初步方案，返回分析 Prompt；
3. `reflect_task` 接收分析结果，返回反思 Prompt；
4. `execute_task` 检查依赖、将任务改为 `in_progress`，读取相关文件摘要，再返回执行 Prompt；
5. `verify_task` 根据评分决定是否完成任务，再返回验证 Prompt。

Prompt 模板由 `src/prompts/loader.ts` 管理，支持：

1. `TEMPLATES_USE` 切换内置模板集；
2. `{DATA_DIR}/{TEMPLATES_USE}` 自定义模板覆盖；
3. `templates_en` fallback；
4. `MCP_PROMPT_*` 完全覆盖；
5. `MCP_PROMPT_*_APPEND` 追加；
6. `{paramName}` 变量替换。

这对 LDVH 的启发是：规则、行动模型和工具提示可以分层维护。稳定约束进入 specs 或 Rules；可复用流程进入 Skill 或行动模型；具体工具返回给 AI 的 Prompt 可以从模板生成。LDVH 不应把所有流程都写进一个超长系统提示，而应通过事实源和工具按场景动态组装最小可行动上下文。

### 2.7 任务生命周期

Shrimp 的典型任务生命周期如下：

```text
plan_task
  -> analyze_task
  -> reflect_task
  -> split_tasks
  -> list_tasks
  -> execute_task
  -> verify_task
```

其中：

1. `split_tasks` 将分析结果转化为结构化任务并写入 `tasks.json`；
2. 新任务状态为 `pending`；
3. `execute_task` 检查依赖可执行性，状态切换为 `in_progress`；
4. `verify_task` 要求任务处于 `in_progress`；
5. `score >= 80` 时写入 summary 并切换为 `completed`；
6. completed 任务默认不能删除，也不能随意更新；
7. 删除任务时若存在其他任务依赖该任务，则拒绝删除。

这条生命周期对 LDVH 的行动模型区段很有参考价值。LDVH 当前 `specs/50-行动模型集合索引.md` 已规划“需求转任务”“Task 执行”“Task 阻塞处理”“Review 执行”“对象状态更新”等行动。Shrimp 提供了一个可对照样板：行动模型不应只定义原则，还应定义状态变更前置、依赖检查、执行上下文、验证标准、证据回写和关闭条件。

### 2.8 Agent 机制

Shrimp 的 Agent 能力分为 MCP 端和 Viewer 端两条线。

MCP 端包括：

1. `src/utils/agentLoader.ts` 扫描 global agents 和项目 `.claude/agents`；
2. `src/utils/agentMatcher.ts` 按任务名称、描述、notes、implementationGuide 中的关键词匹配 frontend、backend、database、fullstack、mobile、testing、security、data 等类型；
3. `splitTasks` 创建任务时可自动填入 `task.agent`。

Viewer 端包括：

1. 全局 Agent 管理；
2. 项目 Agent 管理；
3. global + project agents 合并展示；
4. Agent 下拉选择；
5. OpenAI 批量分配 Agent；
6. Chat Agent 基于当前任务和页面上下文提供建议。

对 LDVH 的启发是：Agent 分配应服务任务执行，而不是单独作为炫技功能。但 LDVH 也必须坚持 `specs/11.03-Agent机制规范.md` 的边界：Agent 创建、修改、权限调整和事实源回写需要治理；Agent 输出不是最终事实源；Agent 不得自行宣称任务完成；推荐 Agent 清单不应直接进入正式规范。Shrimp 的自动匹配逻辑可以作为工具辅助建议，但不应自动替代 LDVH 的 Agent 调度判断和 Human Gate。

### 2.9 Web 能力

Shrimp 有两套 Web 能力。

第一套是 MCP 内嵌 WebGUI，由 `src/web/webServer.ts` 实现。它在 `ENABLE_GUI=true` 时启动 Express 服务，提供：

1. `GET /api/tasks` 读取当前 `tasks.json`；
2. `GET /api/tasks/stream` 通过 SSE 推送任务文件变化；
3. 静态页面展示任务；
4. 启动后写入 `{DATA_DIR}/WebGUI.md`，记录访问地址。

第二套是独立 `tools/task-viewer`，功能更完整。它包含 Node server、React 前端、TanStack Table、i18n、模板管理、Agent 管理、历史查看、任务详情、任务编辑、Chat Agent 等能力。其配置使用用户 home 下的设置文件和模板目录，并按 project profile 读取不同 `tasks.json`。

对 LDVH 的启发是：Web 展示层应成为“事实源观察与人类确认工作台”，而不是另一个事实源。Shrimp 的 Task Viewer 在可观察性上值得借鉴，包括任务筛选、详情、历史、Agent 分配和模板管理。但 LDVH 的 `specs/12.02-Web展示规范.md` 已明确：Web 页面状态、缓存和数据库派生视图不得替代 Git 文件事实源；Web 可以展示、提示 Gate 和提供受控编辑入口，但不得直接调用 AI、Skill 或 Agent，也不得绕过 Tools 辅助层校验。

---

## 三、Shrimp 能力与 LDVH 五类构成要素映射

| Shrimp 能力 | LDVH 映射位置 | 可借鉴方式 | 边界要求 |
|---|---|---|---|
| MCP Server 工具接口 | LDVH 工具 | 将任务查询、任务拆分、状态切换、验证、上下文包生成等能力工具化 | MCP Server 只能是工具实现形态，不能定义新的事实源权威位置 |
| `plan_task` / `analyze_task` / `reflect_task` | LDVH 行动模型、Skill | 将计划、分析、反思拆成可识别阶段 | 分析结论只有写入 evals、ADR、Task 或 Evidence 后才成为稳定事实 |
| `split_tasks` | Task / TaskSet 对象、需求转任务行动 | 借鉴任务拆分、依赖解析、实现指南和验证标准 | 自动拆分不得绕过 Human Gate，不得擅自扩大范围 |
| Task 模型 | Task 生产对象 | 借鉴依赖、关联文件、实现指南、验证标准、完成摘要、Agent 建议字段 | 字段契约需由 LDVH 12 Task 规范定义，实例应在 `ldvh-base/`（工作区级目录） |
| `execute_task` | Task 执行动作 | 借鉴执行前依赖检查、状态切换、相关文件读取和执行 Prompt | 执行状态变更应先写入权威 Task 实例，不能只在工具缓存中变更 |
| `verify_task` | Review、Evidence、Checklist | 借鉴验证前置、评分阈值和完成摘要 | 工具验证不等于人类验收，不得替代 Human Gate |
| `query_task` / `get_task_detail` | Tools 辅助层、Web 展示层 | 借鉴跨当前任务和历史任务的检索 | 检索结果是派生视图，权威仍是 Git 文件事实源 |
| `{DATA_DIR}/memory` | Evidence、Change、Pitfall、历史索引 | 借鉴跨会话记忆与历史恢复目标 | memory 不能成为唯一事实源，稳定经验应回写对应对象 |
| Prompt 模板系统 | Rules、Skill、行动模型、工具模板 | 借鉴多语言模板、覆盖、追加和变量替换机制 | 模板不能与正式规范形成冲突事实源 |
| Agent 自动匹配 | Agent 调度辅助、Web 建议 | 借鉴基于任务内容的 Agent 建议 | Agent 调度须服从 11.03，不能自动创建或授权 Agent |
| 内嵌 WebGUI | Web 展示层 | 借鉴轻量任务展示和 SSE 刷新 | WebGUI 状态不能替代文件事实源 |
| 独立 Task Viewer | Web 展示层 + Tools 辅助层 | 借鉴任务表格、详情、历史、模板、Agent 管理和人类工作台 | Web 写入必须受控，写入后回读 Git 文件事实源并记录 Change |
| research_mode | specs/evals、ADR、Memo、行动模型 | 借鉴研究状态整合和后续步骤约束 | 研究过程不等于结论，稳定结论需进入 evals、ADR 或正式规范 |
| init_project_rules | 项目初始化行动、Rules 机制 | 借鉴项目入口规则初始化思路 | 规则变更触发 Human Gate，不能自动泛滥生成规则 |

---

## 四、LDVH 应重点吸收的设计原则

### 4.1 面向 AI 行动阶段设计工具

Shrimp 的工具不是按人类页面表单划分，而是按 AI 执行阶段划分：规划、分析、反思、拆分、执行、验证、查询、研究。这与 LDVH “AI 执行者为第一服务对象”的定位高度一致。

LDVH 后续设计工具时，应优先问：

1. AI 当前处于哪个行动阶段；
2. 该阶段需要读取哪些最小事实源；
3. 该阶段允许写入哪些对象；
4. 该阶段是否需要 Human Gate；
5. 该阶段完成后应留下什么证据；
6. 下一个阶段如何被明确触发。

这比直接设计一个“大而全”的任务管理 UI 更符合 LDVH 的架构方向。

### 4.2 把 Task 定义为可执行对象，而不是待办文本

Shrimp 的 Task 已具备可执行对象雏形：它有目标、描述、依赖、关联文件、实现指南、验证标准、执行状态、完成摘要和 Agent 建议。LDVH 的 Task 对象应沿这个方向继续强化。

LDVH 后续 Task 规范可重点评估以下字段或关系：

1. `depends_on`：前置任务或前置对象；
2. `blocks`：被本任务阻塞的对象；
3. `acceptance_criteria`：验收标准；
4. `verification`：验证方法和结果；
5. `evidence_refs`：证据引用；
6. `related_files`：关联文件和影响范围；
7. `implementation_guide`：执行指引；
8. `review`：Review 状态和意见；
9. `human_gate`：是否涉及门禁；
10. `change_refs`：关联变更记录。

但字段是否进入正式规范，应在 `specs/12-Task-任务对象` 建设时确定，本文不直接建立字段契约。

### 4.3 将验证设为完成前置动作

Shrimp 的 `verify_task` 要求任务处于 `in_progress`，并通过评分决定是否完成。这个设计提示 LDVH：任务完成不应只由“实现完成”触发，还应经过验证动作。

LDVH 应进一步把验证拆为四层：

1. 工具验证：lint、typecheck、test、结构校验、引用检查；
2. AI 自检：对照任务目标、规范、事实源边界和 Human Gate 检查；
3. Evidence 留存：将验证结果写入 Evidence 或 Task 的证据字段；
4. 人类验收：人基于事实源、证据和展示结果确认是否接受。

验证可以支持验收，但不能替代验收；AI 自检可以降低风险，但不能绕过 Human Gate。

### 4.4 强化跨会话连续性，但坚持 Git 文件事实源

Shrimp 的 `tasks.json`、memory 备份和本地 git history 都服务于跨会话连续性。LDVH 同样需要解决 AI 无记忆问题，但应采用更严格的事实源纪律。

在 LDVH 中，长期有价值的记忆应按性质进入不同承载：

| 记忆类型 | 建议承载 |
|---|---|
| 稳定规范 | `specs/00-79` |
| 外部资料摘录 | `specs/refs/` |
| 项目级评估 | `specs/evals/` |
| 任务状态与执行字段 | `ldvh-base/tasks/`（工作区级目录）或未来 Task 实例目录 |
| 决策结论 | `ldvh-base/adrs/`（工作区级目录）或对应 ADR 实例目录 |
| 执行证据 | `ldvh-base/evidence/`（工作区级目录）或未来 Evidence 实例目录 |
| 变更记录 | `ldvh-base/changes/`（工作区级目录） |
| 经验教训 | `ldvh-base/pitfalls.md`（工作区级目录）或未来 Pitfall 实例目录 |

工具可以帮助收集、展示和写入这些记忆，但工具自己的数据库、缓存、JSON 文件或 UI 状态不能成为权威事实源。

### 4.5 将 Prompt 模板化纳入工具设计

Shrimp 的 Prompt 模板系统说明，AI 工具不只是 API 返回 JSON，也可以返回高度结构化的执行指令。LDVH 未来的 Tools / Skill / Agent 设计可借鉴模板化思路：

1. 稳定硬约束写入 specs 或 Rules；
2. 可复用多步骤流程写入 Skill 或行动模型；
3. 工具 Prompt 用模板生成，按场景注入最小上下文；
4. 模板变量应来自事实源或工具确定性结果；
5. 模板覆盖机制不得与正式规范形成冲突；
6. 模板变更若影响 AI 行动入口，应评估 Human Gate。

这有助于避免把所有行为约束堆入一个超长规则文件，也有助于让工具输出更适合 AI 执行。

### 4.6 将研究模式规范化

Shrimp 的 `research_mode` 要求输入 topic、previousState、currentState 和 nextSteps，用于整合阶段性研究状态。这对 LDVH 的 `specs/evals/` 有直接借鉴价值。

LDVH 可形成“研究模式行动模型”或 evals 写作骨架：

1. 识别调研问题；
2. 声明调研边界和执行效力；
3. 收集外部资料和本地源码证据；
4. 区分事实观察、分析判断和建议；
5. 映射到 LDVH 五类构成要素；
6. 区分可直接采用、需改造采用和不适合采用；
7. 列出候选正式规范或 ADR；
8. 对升级正式规则触发 Human Gate。

这会让调研从“聊天中问一问”变成可审查、可复用、可追溯的工程活动。

### 4.7 Web Tools 应服务人类确认质量

Shrimp Task Viewer 的价值不只是“好看”，而是让人能看到任务、状态、历史、关联、Agent、模板和操作入口。LDVH 的 Web 展示层也应服务 V6“人类确认质量”。

LDVH Web Tools 可借鉴的视图包括：

1. 当前 Task / TaskSet 状态、阻塞和依赖；
2. 待 Human Gate 确认事项；
3. Task 的证据、验证结果和缺口；
4. Change 记录和影响文件；
5. ADR / Risk / Dependency 与 Task 的关系；
6. Pitfall 命中与重复风险提示；
7. 规则、Skill、Agent 和行动模型命中情况。

但 LDVH Web 展示层必须遵守：页面状态不替代 Git 文件事实源；受控编辑写入必须明确目标文件；写入后必须回读事实源；必要时记录 Change。

---

## 五、不应照搬的部分

### 5.1 不应照搬 Shrimp 的 `{DATA_DIR}/tasks.json` 为权威任务源

Shrimp 使用单一 JSON 文件保存任务，适合工具自身简洁实现。但 LDVH 的任务对象应属于项目事实源，进入 `ldvh-base/`（工作区级目录）下未来定义的 Task 实例目录或文件结构。否则会出现工具数据与 LDVH 生产对象并行维护同一事实的问题。

### 5.2 不应把 memory 备份当作长期事实源

Shrimp 的 memory 目录主要用于清空任务后的 completed tasks 备份和查询。LDVH 中，长期有价值的完成摘要、证据、经验和变更应进入 Evidence、Change、Pitfall 或 Task 关闭字段。备份文件可以辅助恢复，但不能成为唯一事实源。

### 5.3 不应让自动任务拆分绕过 Human Gate

Shrimp 的 `split_tasks` 支持自动拆分、依赖解析和更新模式。LDVH 可以借鉴拆分能力，但自动拆分可能改变范围、优先级、风险和事实源位置。涉及高影响变更、正式规范升级、目录事实源边界调整、Rules / Skill / Agent 改动、远程 Git 操作等事项，仍必须触发 Human Gate。

### 5.4 不应把 `score >= 80` 等同于交付质量

Shrimp 的 `verify_task` 以 80 分作为自动完成阈值，这适合工具流程闭环，但 LDVH 的交付质量还包括事实源回写、证据留存、Human Gate 识别、规范一致性、人类验收和可追溯性。分数只能作为辅助判断，不应成为 LDVH 关闭任务的唯一条件。

### 5.5 不应复制完整思维链作为事实

Shrimp 提供 `process_thought` 和反思工具，强调思维处理。LDVH 可以借鉴“显式反思”动作，但不应把完整思维链保存为事实源。应保存的是可审查的结论、依据、风险、决策、证据和后续行动，而不是不可验证的内部推理文本。

### 5.6 不应让 Web Viewer 直接调用 AI 并写回权威事实

Shrimp 独立 viewer 中存在 OpenAI 批量分配 Agent 和 Chat Agent 能力。LDVH 的 `specs/12.02-Web展示规范.md` 已明确 Web 展示层不得直接调用 AI、Skill 或 Agent。LDVH Web 可以生成上下文、展示建议、提供人工操作入口，但 AI 判断和事实源回写应受行动模型、Tools 辅助层和 Human Gate 约束。

### 5.7 不应把 Agent 自动匹配等同于 Agent 治理

Shrimp 的关键词匹配可以为任务填充 `agent` 字段，但 LDVH 的 Agent 创建、调用、权限、定义摘要和生命周期需要受 `specs/11.03-Agent机制规范.md` 治理。自动匹配最多是建议，不应自动创建 Agent、授权 Agent、修改 Agent Prompt 或绕过主控判断。

### 5.8 不应让项目规则初始化变成规则泛滥

Shrimp 的 `init_project_rules` 提供项目规则初始化指导，这对新 Agent 进入项目有帮助。但 LDVH 需要坚持规则分层、最小入口和权威引用。规则新增、删除、修改属于高影响 AI 行动入口变更，应触发 Human Gate，并记录 Change。

---

## 六、对 LDVH 后续建设的建议

### 6.1 优先建设 Task 对象规范

Shrimp 最直接的借鉴对象是 Task 模型。LDVH 当前 `specs/10-生产对象集合索引.md` 已将 `12` 规划为 Task。建议在建设 `specs/12-Task-任务对象` 时重点吸收 Shrimp 的以下设计：

1. Task 是最小可执行、可追踪、可验证、可关闭对象；
2. Task 应有依赖关系和阻塞关系；
3. Task 应有明确执行指引和验收标准；
4. Task 应记录关联文件和影响范围；
5. Task 应支持 Evidence、Change、Review、Human Gate 引用；
6. Task 终态应受保护，不能随意重开或删除；
7. Task 关闭应留下摘要和验证证据。

### 6.2 补齐任务生命周期行动模型

LDVH 当前 `specs/50-行动模型集合索引.md` 已规划 `44 需求转任务`、`45 Task 执行`、`46 Task 阻塞处理`、`47 Review 执行`、`50 对象状态更新`。建议参考 Shrimp 的任务生命周期，把这些行动模型串成闭环：

1. 读取 Context；
2. 识别 Scenario；
3. 判断事实源边界；
4. 判断 Human Gate；
5. 将需求拆为 Task / TaskSet；
6. 检查依赖和阻塞；
7. 执行前更新状态；
8. 读取关联文件和执行指引；
9. 执行并记录证据；
10. 验证并形成 Evidence；
11. 进入 Review 或请求验收；
12. 关闭 Task 并写入 Change / Pitfall / ADR 等后续事实。

### 6.3 评估 LDVH MCP Server 的工具清单

Shrimp 证明 MCP 适合把任务治理能力暴露给 AI 客户端。LDVH 后续若评估自建 MCP Server，可优先考虑以下工具方向：

| 工具能力 | 说明 |
|---|---|
| 事实源查询 | 查询 specs、ldvh-base、docs 中的权威对象和规则 |
| Context 包生成 | 按 Scenario 生成最小可行动上下文 |
| Task 创建准备 | 根据 Intent 或需求生成 Task 草案，但不绕过确认 |
| Task 状态更新 | 受控更新 Task 状态并记录原因 |
| 依赖检查 | 检查 Task depends_on / blocks 是否满足 |
| Evidence 写入准备 | 将验证结果整理为 Evidence 草案 |
| Human Gate 检查 | 根据规则提示是否必须暂停确认 |
| Change 记录生成 | 根据实际修改生成 Change YAML 草案或受控写入 |
| 规范引用检查 | 检查文档引用和事实源边界 |
| Web 派生数据生成 | 为 Web 工作台提供可追溯视图数据 |

这些工具必须读取和写入 Git 文件事实源，不得另建权威数据库。

### 6.4 设计 LDVH Prompt 模板治理方式

Shrimp 的模板系统值得 LDVH 借鉴，但 LDVH 需要更严格地区分规范、规则、流程和模板：

1. specs 定义稳定模型和边界；
2. Rules 承载高频硬约束入口；
3. Skill 承载可复用流程；
4. Agent 承载独立上下文或专业角色；
5. 工具 Prompt 模板承载具体工具返回给 AI 的执行格式；
6. 模板变量必须来自事实源或工具确定性输出；
7. 模板变更影响 AI 行动入口时触发 Human Gate。

### 6.5 将 Web Tools 设计为事实源观察和确认工作台

LDVH Web Tools 不应复制一个通用任务管理软件，而应围绕 LDVH 生产对象和行动模型提供工作台：

1. 任务状态、依赖、阻塞和证据视图；
2. 待确认 Human Gate 列表；
3. 规范命中和规则命中提示；
4. 变更影响文件和 Change 记录视图；
5. Evidence / Checklist / Review 聚合；
6. Pitfall 重复风险提示；
7. 受控编辑入口和写入前后验证。

Shrimp Task Viewer 中的多 profile、任务历史、模板管理、Agent 管理和任务详情可作为体验参考，但 LDVH Web 不应直接把 UI 内状态作为任务事实。

### 6.6 建立研究模式实践路径

建议将 `specs/evals/` 作为研究模式主要落点，并形成固定评估骨架：

1. 调研对象；
2. 调研边界；
3. 资料来源；
4. 源码结构；
5. 核心机制；
6. 与 LDVH 五类构成要素映射；
7. 可借鉴点；
8. 不适合照搬点；
9. 候选正式规范或 ADR；
10. 后续行动。

本文即按该方向重写，后续可进一步沉淀为 evals 模板或研究模式行动模型。

---

## 七、可转化为正式规范或 ADR 的候选事项

本文不直接建立正式规则，但以下事项值得后续进入正式规范或 ADR 讨论：

| 候选事项 | 建议落点 | 原因 | Human Gate |
|---|---|---|---|
| Task 对象字段、状态机和依赖规则 | `specs/12-Task-任务对象` | 将任务升级为可执行、可验证、可追溯对象 | 创建 planned 对象正式规范需确认 |
| TaskSet 对象与批量任务拆分关系 | `specs/13-TaskSet-任务集` | 承载同一目标下的任务集合和依赖图 | 创建 planned 对象正式规范需确认 |
| 需求转任务行动模型 | `specs/44-需求转任务` | 约束自动拆分、确认边界和 Task 初始化 | 创建 planned 行动正式规范需确认 |
| Task 执行动作 | `specs/45-Task执行` | 约束状态前置、依赖检查、执行证据和验证 | 创建 planned 行动正式规范需确认 |
| Task 阻塞处理 | `specs/46-Task阻塞处理` | 处理依赖未满足、外部等待和 Human Gate 阻塞 | 创建 planned 行动正式规范需确认 |
| Review 执行动作 | `specs/47-Review执行` | 区分工具验证、AI 自检、人类验收和 Human Gate | 创建 planned 行动正式规范需确认 |
| 研究模式行动模型或 evals 模板 | `specs/50-79` 或 `specs/evals/` 模板 | 将外部调研转为可复用工程活动 | 若进入正式行动规范需确认 |
| MCP 工具接入 ADR | `ldvh-base/adrs/`（工作区级目录） | 判断 LDVH 是否以 MCP Server 形式提供 LDVH 工具 | ADR 创建和工具方向确认需评估 |
| Web Tools 任务工作台设计 | `web/` 实现规划或工具设计文档 | 提升人类确认质量 | 若写入或改变事实源链路需确认 |
| Prompt 模板治理规则 | `specs/12` 子文档、Skill/Tools 实践文档 | 防止模板与规范冲突 | 影响 AI 行动入口时需确认 |

---

## 八、最终判断

MCP Shrimp Task Manager 对 LDVH 的最大价值，是提供了一个“面向 AI Agent 的任务治理工具”样板。它证明任务管理可以不是人类看板的附属品，而是 AI 规划、分析、执行、验证、记忆和恢复上下文的核心工具链。

LDVH 应吸收 Shrimp 的以下思想：

1. AI 行动阶段显式化；
2. Task 对象可执行化；
3. 依赖和阻塞结构化；
4. 执行前状态切换和上下文准备；
5. 验证作为任务关闭前置；
6. 跨会话连续性；
7. Prompt 模板化；
8. 研究模式；
9. Agent 分配辅助；
10. Web 可观察性和人类工作台。

同时，LDVH 必须坚持自己的核心边界：

1. LDVH 不是单一 MCP 工具，而是工程化驾驭框架；
2. LDVH 的最终事实源必须是 Git 可追踪文件；
3. LDVH 生产对象承载稳定工程事实；
4. LDVH 行动模型约束 AI 如何行动；
5. Rules / Skill / Agent 是协作机制，不是事实源；
6. LDVH 工具只辅助读取、校验、聚合、展示和受控写入；
7. Web 状态、工具缓存、模型输出和 MCP Server 内存不得替代事实源；
8. Human Gate 不能被自动规划、自动拆分、自动验证或自动 Agent 分配绕过。

因此，Shrimp Task Manager 应作为 LDVH 任务对象、任务生命周期行动模型、MCP 工具形态、Prompt 模板机制和 Web 工作台设计的重要参考，而不是作为 LDVH 规范体系或事实源体系的替代品。最合理的借鉴路径，是把 Shrimp 的任务规划、分析、反思、拆分、依赖、执行、验证、研究、记忆、Agent 辅助和可视化能力拆解为 LDVH 内部的对象规范、行动模型和工具能力，并始终回到 Git 文件事实源与 Human Gate 的治理边界内。
