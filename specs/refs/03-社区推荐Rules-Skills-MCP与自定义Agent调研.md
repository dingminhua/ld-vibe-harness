# 社区推荐 Rules、Skills、MCP 与自定义 Agent 调研

> 创建日期：2026-05-26
> 来源：Trae 官方论坛、MCP.directory、火山引擎 MCP 市场、Trae 官方文档、Trae 官方最佳实践入口
> 定位：外部资料引用，不直接成为 LDVH 强制规则

---

## 1. 结论摘要

社区材料中对 Rules、Skills、MCP 和自定义 Agent 的分工有一个实用比喻：

```text
MCP 是锤子，Skills 是钉钉子的技能，Rules 是施工规范，Agent 是带着工具箱和施工手册的专业工种。
```

按这个理解：

| 机制 | 本质 | 社区建议 |
|---|---|---|
| Rules | 底线约束 | 精简但必须有，承载强约束、禁止事项、事实源边界和 Skill/Agent 调用入口 |
| Skills | 知识和流程 | 按场景沉淀 SOP、模板、检查清单，负责告诉 AI 如何正确完成任务 |
| MCP | 工具能力 | 够用就好，避免超过工具描述和数量上限；按 Agent 职责分配 |
| 自定义 Agent | 专业角色 + 工具权限 + Prompt 工作流 | 专人专岗，隔离上下文，给不同角色配置最小必要工具 |

社区实践中最常被推荐的通用 MCP 包括：

1. Context7：实时文档 / API 文档上下文。
2. Sequential Thinking：复杂问题拆解和逐步推理。
3. Playwright 或 Puppeteer：浏览器自动化、网页测试、截图、交互验证。
4. Fetch / Web Search 类工具：网络请求和信息获取。
5. Memory 类工具：长期记忆或项目记忆。
6. 文件系统 / 数据库 / 云服务类 MCP：按项目需要启用。

推荐策略：

```text
通用 MCP 少量常开；
场景 MCP 按需启用；
工具使用流程沉淀为 Skill；
底线和调用入口沉淀为 Rule；
专业角色、工具权限和上下文隔离沉淀为自定义 Agent。
```

---

## 2. 社区对 Rules、Skills、MCP、Agent 的分工建议

Trae 社区教程中给出的核心原则是：

> MCP 够用就好，Skills 可以尽情创建，Rules 精简但必须要有。

结合自定义 Agent 后，可扩展为：

> Rules 守底线，Skills 管方法，MCP 给工具，Agent 定角色。

原因：

1. MCP 每启用一个 Server，可能带来多个工具，占用工具配额。
2. Trae 官方 FAQ 提到 MCP 工具数量上限为 40，描述信息也有字符上限。
3. Skills 是知识文本，按需加载，不占 MCP 工具数量。
4. Rules 始终生效，应只放强约束和 Skill/Agent 引用，不宜塞入大量细节。
5. 自定义 Agent 可以把专业角色、工具权限、Prompt 工作流隔离开，减少通用 Agent 过载。

社区常见配置策略：

| 层级 | 放什么 | 不放什么 |
|---|---|---|
| Rules | 必须遵守/禁止事项、启动构建命令、事实源路径、Skill/Agent 调用索引 | 大段教程、完整架构说明、可按需加载的场景知识 |
| Skills | 操作 SOP、项目知识、工具使用约定、质量检查流程 | 高危权限、密钥、所有任务都必须遵守的硬约束 |
| MCP | 浏览器、请求、文档、记忆、数据库、云服务等真实工具 | 项目规范、长篇说明、业务流程 |
| Agent | 专业角色、工具组合、输出格式、失败处理、可被 SOLO 调用的模块化能力 | 所有项目通用底线、无限工具集、敏感凭证 |

---

## 3. 社区推荐的 Rules 内容

### 3.1 Rules 的社区定位

社区实践普遍把 Rules 视为“底线约束”和“入口索引”，不是完整知识库。推荐写法是：

```text
Rules 只写必须遵守和绝对禁止的内容；
详细流程放进 Skills；
外部工具能力放进 MCP；
专业角色和工具组合放进自定义 Agent。
```

这与 Trae 官方文档中的规则最佳实践一致：单条规则应保持清晰、聚焦，避免与其他规则冲突；复杂规则应通过生效方式、目录分层和子目录规则拆开。

### 3.2 社区推荐的 Rule 内容类型

| 类型 | 推荐写入内容 | 示例 | 不建议写入 |
|---|---|---|---|
| 项目身份 | 项目类型、技术栈、关键架构边界 | “本项目是 Wails v2 + Go + Vue3 桌面应用” | 完整架构说明书 |
| 启动/构建铁律 | 正确命令、禁止命令、验证方式 | “必须使用 `wails dev`，禁止只运行 `npm run dev`” | 所有命令教程 |
| 事实源边界 | 哪些文件是权威来源，哪些不是 | “任务状态只维护在 task-base” | 大段对象规范全文 |
| Skill 调用索引 | 什么场景必须调用什么 Skill | “新增文件后调用 codebase-documentation” | Skill 的完整执行步骤 |
| Agent 调用索引 | 什么场景使用什么自定义 Agent | “UI 还原交给 UI Designer，接口验证交给 API Test Pro” | Agent 的完整 Prompt |
| 安全红线 | 禁止泄密、禁止高风险操作、确认门槛 | “Token 不落库；生产写操作需确认” | 详细安全培训材料 |
| 人类确认点 | 哪些动作必须先确认 | “代码修改前先给方案并等待确认” | 所有沟通偏好 |
| 质量检查 | 完成前必须执行的最小检查 | “修改前端后必须刷新页面并看控制台” | 完整测试手册 |
| 目录分层 | 根规则与子目录规则的边界 | “frontend 目录规则只管前端” | 全项目所有模块细节 |

### 3.3 社区示例：AGENTS.md 强约束结构

社区分享中有一种强约束模式：在 `AGENTS.md` 中写明 AI 助手工作规范，并把规则拆成“Skill 调用规范、任务执行流程、代码修改铁律、注释规范、用户提醒机制”。

可抽象为：

```markdown
# AI 助手工作规范

## Skill 调用规范
- 对话开始时必须调用基础协作 Skill。
- 涉及代码/文件操作前必须调用任务规划 Skill。
- 纯问答或解释类任务可以跳过。

## 任务执行流程
1. 复述需求并拆解步骤。
2. 检查已有 hooks、utils、components 或类似可复用资产。
3. 有疑问先向用户确认。
4. 等待用户确认执行后再编码。

## 代码修改铁律
- 发现错误时先告知，再等待确认后修复。
- 用户反馈问题时先问清楚，再处理。
- 提供多个方案时先让用户选择。

## 完成后检查
- 检查功能完整性。
- 检查遗漏逻辑。
- 执行项目规定的验证命令。
```

该模式的价值是把“AI 容易跑偏”的位置提前约束住，尤其适合老项目、多人协作项目和需求不稳定项目。

### 3.4 社区推荐的 Rules 拆分方式

社区建议不要把所有规则写在一个大文件里，而是拆成多个 `.md` 文件，例如：

```text
.trae/rules/
├── project-overview.md
├── development-flow.md
├── code-style.md
├── quality-gate.md
├── security.md
├── frontend/
│   ├── component-rules.md
│   └── ui-rules.md
└── backend/
    ├── api-rules.md
    └── database-rules.md
```

拆分原则：

1. 根目录规则只放全项目通用约束。
2. 模块规则放在对应子目录或按 globs 生效。
3. 场景规则用智能生效或手动触发，避免长期占用上下文。
4. 高频硬约束用始终生效，低频流程放 Skill。
5. 新增或修改规则后建议新开对话验证。

### 3.5 推荐的 Rules 最小模板

适合多数项目的最小模板：

```markdown
# 项目规则

## 项目身份
本项目的技术栈、运行方式和关键事实源以本文件及项目文档为准。

## 必须遵守
1. 修改前先理解现有结构，优先复用已有实现。
2. 涉及代码/文件修改时，先给方案和影响范围。
3. 完成后执行项目规定的验证命令，并汇报结果。

## 禁止事项
1. 禁止硬编码密钥、Token、个人路径和业务无关配置。
2. 禁止绕过项目指定启动/构建方式。
3. 禁止在未确认时执行高风险写操作。

## Skill 调用
- 需求拆解：调用 task-planner。
- 文档维护：调用 codebase-documentation。
- 代码审查：调用 code-review。

## Agent 调用
- UI/UX：使用 UI Designer。
- 前端架构：使用 Frontend Architect。
- 后端架构：使用 Backend Architect。
- API 测试：使用 API Test Pro。
- 运维部署：使用 DevOps Architect。

## MCP 使用
只在任务需要时使用已授权 MCP；高风险 MCP 必须经用户确认。
```

---

## 4. 社区推荐的自定义 Agent 配置

### 4.1 自定义 Agent 的社区定位

社区与官方文档都把自定义 Agent 视为“专业角色 + 工具权限 + 工作流 Prompt”的组合。

与 Rule、Skill、MCP 的分工：

| 机制 | 适合承担 | 不适合承担 |
|---|---|---|
| Rule | 全局底线、禁止事项、事实源边界 | 专业角色完整工作流 |
| Skill | 某类任务的 SOP、模板、检查清单 | 外部工具权限管理 |
| MCP | 外部工具能力 | 判断何时、如何正确使用工具 |
| 自定义 Agent | 专业角色、工具组合、上下文隔离、可被 SOLO 调度 | 所有项目的通用底线 |

因此，自定义 Agent 最适合做“专人专岗”：前端架构师、后端架构师、API 测试工程师、DevOps、性能优化师、合规审查员、文档治理助手等。

### 4.2 官方和社区推荐的 Agent 类型

Trae 官方 SOLO Agent 文档提供了一组可一键导入的自定义 Agent 示例，社区也通常围绕这些角色扩展：

| Agent | 主要职责 | 推荐搭配 MCP | 推荐搭配 Skill |
|---|---|---|---|
| UI Designer | UI/UX、组件、设计系统、视觉优化 | Figma AI Bridge、Playwright | UI/UX Skill、设计系统 Skill |
| Frontend Architect | 前端架构、组件、状态、性能、测试 | Context7、Playwright、Figma | 前端最佳实践、组件规范 |
| Backend Architect | API、业务逻辑、数据库、服务端架构 | Context7、数据库 MCP | API 设计、错误处理、数据库规范 |
| API Test Pro | API 功能、契约、性能、安全测试 | Playwright、HTTP/Fetch、OpenAPI 相关工具 | API 测试 SOP、契约测试 Skill |
| AI Integration Engineer | LLM 接入、推荐系统、智能自动化 | Context7、云服务 MCP | AI 集成规范、模型评估 Skill |
| DevOps Architect | CI/CD、云资源、监控、部署 | Terraform、ECS、TLS、RDS | 发布流程、回滚预案、变更审批 Skill |
| Performance Expert | 性能测试、瓶颈定位、优化建议 | Playwright、日志/监控 MCP | 性能分析报告 Skill |
| Compliance Checker | 法律、隐私、条款、合规风险 | 文档/知识库 MCP | 合规审查清单 Skill |
| Documentation Agent | 文档、知识库、更新日志、需求整理 | Context7、Lark、Confluence | 文档写作、任务验收、备忘写入 Skill |
| Project Manager Agent | 需求拆解、任务同步、验收推进 | Jira、Lark、日历任务 MCP | 需求拆解、会议纪要、验收 Skill |

### 4.3 自定义 Agent Prompt 推荐结构

社区实践中，好的 Agent Prompt 通常包含以下字段：

```markdown
# 角色
你是某领域专家，负责什么，不负责什么。

# 使用场景
当用户提出哪些任务时使用；哪些任务不要使用。

# 输入要求
需要用户或主控 Agent 提供哪些上下文。

# 工作流程
1. 先读取相关文件或资料。
2. 识别风险和不确定点。
3. 给出方案或执行步骤。
4. 必要时调用 MCP 或 Skill。
5. 输出结果和验证方式。

# 工具使用规则
- 只在必要时调用 MCP。
- 高风险工具调用前请求确认。
- 不读取或输出密钥。

# 输出格式
固定输出：结论、依据、变更、风险、验证。

# 失败处理
信息不足时先提问；工具失败时返回错误原因和替代方案。
```

### 4.4 自定义 Agent 工具配置原则

| 原则 | 说明 |
|---|---|
| 最小授权 | 只给 Agent 完成职责必需的 MCP 和内置工具 |
| 避免工具重叠 | Playwright 与 Puppeteer 通常二选一 |
| 专用 Agent 承担高风险工具 | 云命令、数据库写操作、支付退款只给专用 Agent |
| Prompt 写清工具使用时机 | 避免 Agent 为了使用工具而使用工具 |
| 被 SOLO 调用时保持独立上下文 | 子 Agent 只处理明确子任务，返回结构化结果 |
| 分享前脱敏 | Prompt、MCP headers、Token、内部路径必须脱敏 |

### 4.5 社区推荐的 Agent 编排方式

SOLO Agent 适合作为主控 Agent，自定义 Agent 适合作为被调度的专业角色。

推荐编排：

```text
SOLO Agent
├── Search Agent：检索和定位文件
├── Frontend Architect：处理前端实现
├── Backend Architect：处理后端实现
├── API Test Pro：验证接口和契约
├── DevOps Architect：处理部署、CI/CD 和环境
├── Performance Expert：做性能分析
└── Documentation Agent：维护文档和更新日志
```

编排原则：

1. 主控 Agent 负责任务拆解、上下文分配和最终整合。
2. 子 Agent 只处理单一专业领域，避免全能型 Prompt。
3. 每个子 Agent 返回结构化结果，便于主控汇总。
4. 复杂任务先 Plan/Spec，再执行。
5. 对跨模块变更，先由 Search Agent 或代码检索工具识别影响范围。

### 4.6 自定义 Agent 反模式

| 反模式 | 问题 | 改法 |
|---|---|---|
| 一个 Agent 负责所有任务 | Prompt 过长、工具过多、行为不可控 | 按角色拆分 Agent |
| 所有 MCP 都给同一个 Agent | 触发工具上限，误调用风险高 | 按职责分配 MCP |
| Prompt 只有人设，没有流程 | 输出不稳定 | 增加工作流程、输出格式和失败处理 |
| 高风险 Agent 可被随意调用 | 可能误改生产或泄露数据 | 设置明确调用条件和确认规则 |
| 分享 Agent 不脱敏 | 泄露 Token、内部路径或业务信息 | 分享前清理敏感信息 |

---

## 5. 社区高频推荐 MCP

### 5.1 通用开发类

| MCP | 推荐来源 | 作用 | 使用建议 |
|---|---|---|---|
| Context7 | MCP.directory 热门；社区教程推荐 | 为 AI 注入实时 API 文档、库文档上下文 | 适合代码开发和查文档；如果已有稳定内置文档查询工具，可按需启用 |
| Sequential Thinking | MCP.directory 热门；社区教程推荐 | 复杂问题拆解、动态反思、逐步推理 | 适合方案评估、架构决策、复杂 Bug；不必给所有 Agent 默认开启 |
| Fetch / DuckDuckGo / Web Search 类 | 社区教程和 MCP.directory 热门 | 网络请求、网页搜索、资料获取 | 与 Trae 内置联网搜索可能重叠，应按 Agent 需要选择 |
| Memory 类 | 社区教程推荐 | 项目或对话记忆 | 对有严格事实源的项目需谨慎，避免与 docs/task-base 等事实源冲突 |
| 文件系统类 | MCP.directory 分类常见 | 文件读取、写入、目录操作 | Trae 已有内置文件系统工具时通常不需要额外启用 |

### 5.2 浏览器与测试类

| MCP | 推荐来源 | 作用 | 使用建议 |
|---|---|---|---|
| Playwright | Trae 官方教程；MCP.directory 热门 | 网页自动化测试、截图、交互、HTTP 请求、日志 | 官方教程支持度高，适合测试 Agent；与 Puppeteer 二选一 |
| Puppeteer | 社区教程推荐 | 浏览器自动化、导航、截图、点击 | 更轻量的浏览器操作场景可用；与 Playwright 功能重叠 |
| Safari / 多会话浏览器 MCP | MCP.directory 新增/社区生态 | 特定浏览器或多会话自动化 | 仅在明确需要 Safari 或多会话时启用 |

建议：

```text
测试优先选 Playwright；
简单网页操作可选 Puppeteer；
不要在同一 Agent 中同时长期启用多个浏览器自动化 MCP。
```

### 5.3 设计与前端类

| MCP | 推荐来源 | 作用 | 使用建议 |
|---|---|---|---|
| Figma AI Bridge | Trae 官方教程 | 读取 Figma 设计稿，下载图像资源，辅助生成前端页面 | 适合 UI 还原 Agent；需要 Figma Token；需注意设计稿权限和 Token 脱敏 |
| draw.io / diagram 相关 Skill | MCP.directory 热门 Skills | 生成流程图、UML、BPMN、项目管理图 | 更偏 Skill，不一定需要 MCP；适合文档和架构表达 |
| UI/UX 类 Skill | MCP.directory 热门 Skills | UI/UX 设计规范、布局、色彩、组件建议 | 适合与前端 Agent 配合，不建议作为全局 Rule |

### 5.4 项目管理与协作类

| MCP | 推荐来源 | 作用 | 使用建议 |
|---|---|---|---|
| Atlassian Jira & Confluence | MCP.directory 热门/Most Installed | 连接 Jira、Confluence | 适合已有 Atlassian 体系团队；OAuth/权限要严格控制 |
| Lark / 飞书 MCP | 火山引擎市场 | 飞书 OpenAPI，文档、协作、会话管理 | 适合飞书生态团队；需要企业权限和安全审查 |
| DAV / 日历任务类 MCP | MCP.directory 新增 | 日历、联系人、任务协作 | 按组织工具链选择，不建议无需求启用 |

### 5.5 云服务、数据库与运维类

| MCP | 推荐来源 | 作用 | 使用建议 |
|---|---|---|---|
| Terraform MCP | MCP.directory 热门 | Terraform provider 文档、模块规范、基础设施协作 | 适合 IaC 团队；操作生产资源前必须有人审查 |
| 火山引擎 ECS MCP | 火山引擎市场 | 云服务器实例和镜像管理 | 适合火山云用户；权限必须最小化 |
| 火山引擎云助手 MCP | 火山引擎市场 | 向云服务器发送并执行命令 | 高风险工具，只应给 DevOps 专用 Agent，禁止默认开放 |
| 火山引擎 TOS MCP | 火山引擎市场 | 对象存储资源管理和数据探索 | 适合使用 TOS 的项目 |
| 火山引擎 TLS MCP | 火山引擎市场 | 日志分析、可观测 | 适合线上排障和日志分析 |
| 火山引擎 RDS MySQL / veDB MySQL MCP | 火山引擎市场 | 数据库资源查询和管理 | 对生产数据库必须只读优先，写操作需人工审批 |

### 5.6 支付与业务平台类

| MCP | 推荐来源 | 作用 | 使用建议 |
|---|---|---|---|
| 抖音支付 MCP | 火山引擎市场 | 交易创建、查询、退款等 | 高风险业务能力，必须专用 Agent、最小权限、人工确认 |
| 巨量千川 MCP | 火山引擎市场 | 广告账户关系和报表查询 | 适合投放/数据分析；注意账号权限和商业数据安全 |

---

## 6. MCP.directory 中的热门 MCP 与 Skills

MCP.directory 自称是 MCP Servers 和 Agent Skills 目录，首页显示：

1. 2002 个 servers。
2. 9436 个 skills。
3. 1653 个 publishers。
4. 9 个 AI clients。

其热门 MCP Servers 包括：

| 名称 | 发布方 | 说明 | 适合场景 |
|---|---|---|---|
| Atlassian Jira & Confluence | Atlassian | 官方远程 MCP，连接 Jira 和 Confluence | 产品研发协作、需求/任务/知识库查询 |
| Context7 | Upstash | 实时 API 文档上下文 | 编码、库文档查询、技术调研 |
| Sequential Thinking | Anthropic | 复杂问题分解和结构化思考 | 架构方案、复杂任务分析 |
| DuckDuckGo | Community | Web 搜索 | 资料检索，需注意来源质量 |
| Playwright Browser Automation | Microsoft | 浏览器自动化测试 | E2E 测试、网页验证 |
| HashiCorp Terraform | HashiCorp | Terraform 文档和模块信息 | IaC、云基础设施 |

热门 Skills 包括：

| Skill | 说明 | 可借鉴点 |
|---|---|---|
| flutter-development | Flutter/Dart 跨平台移动开发 | 技术栈专用 Skill 可沉淀框架范式和常见坑 |
| drawio-diagrams-enhanced | 生成 draw.io 图表，覆盖流程图、UML、BPMN、项目管理图 | 文档型项目可引入图表生成 Skill |
| ui-ux-pro-max | UI/UX 设计智能，覆盖多种技术栈、组件和风格 | 前端/UI 类 Agent 可配套使用 |
| godot | Godot 项目开发、文件格式、架构模式、CLI 工作流 | 典型“项目/技术栈专属 Skill” |
| pdf-to-markdown | 将 PDF 转换为结构化 Markdown | 适合文档输入、需求资料转换 |
| nano-banana-pro | 图像生成和编辑 | 设计资产生成场景，需注意外部 API 和版权 |

---

## 7. Rules、Skills、MCP 与 Agent 的组合模式

### 7.1 浏览器测试组合

| 层 | 建议配置 |
|---|---|
| Rule | 只有涉及网页测试时调用该 Agent/Skill；不要在普通开发任务中默认开启浏览器 MCP |
| Skill | 网页自动化测试 SOP、POM 结构、断言规范、截图保存规范 |
| MCP | Playwright |
| Agent | 网页测试助手 / API Test Pro |

适合任务：

1. 验证页面交互。
2. 截图回归。
3. 生成 E2E 测试。
4. 检查控制台错误。

### 7.2 设计稿转代码组合

| 层 | 建议配置 |
|---|---|
| Rule | 不得擅自改设计；Token 不落库；生成后必须可预览验证 |
| Skill | UI 还原规范、响应式规范、组件拆分规范、资源下载规范 |
| MCP | Figma AI Bridge |
| Agent | Figma 助手 / UI Designer |

适合任务：

1. 从 Figma 设计稿生成页面。
2. 下载设计稿图片资源。
3. 对比设计稿进行 UI 修正。

### 7.3 文档与知识管理组合

| 层 | 建议配置 |
|---|---|
| Rule | 项目事实源优先级、文档更新日志要求、禁止把临时记忆当事实源 |
| Skill | 文档写作标准、知识库同步流程、资料摘要模板 |
| MCP | Context7、Atlassian/Confluence、Lark、PDF 处理类 Skill |
| Agent | Documentation Agent / 产品经理助手 |

适合任务：

1. 技术文档调研。
2. 外部资料整理。
3. 需求文档和更新日志维护。
4. 知识库同步。

### 7.4 云资源与运维组合

| 层 | 建议配置 |
|---|---|
| Rule | 生产环境写操作必须人工确认；密钥不落库；默认只读 |
| Skill | 变更审批流程、只读优先策略、回滚预案、日志分析 SOP |
| MCP | Terraform、ECS、TOS、TLS、RDS、云助手等 |
| Agent | DevOps Architect |

适合任务：

1. 查询云资源。
2. 分析日志。
3. 生成 Terraform 配置。
4. 辅助排障。

### 7.5 项目管理组合

| 层 | 建议配置 |
|---|---|
| Rule | 需求文档与 task-base 等事实源边界；状态变更规则 |
| Skill | 需求拆解、任务状态流转、会议纪要、验收清单 |
| MCP | Jira/Confluence、Lark、日历任务类 MCP |
| Agent | Project Manager Agent / 产品经理助手 |

适合任务：

1. 从需求生成任务。
2. 同步项目状态。
3. 生成验收报告。
4. 整理会议纪要。

---

## 8. 通用推荐清单

### 8.1 个人开发者 / 小项目

建议常备：

1. 一份极简项目 Rule：项目身份、禁止事项、启动构建、验证命令。
2. Context7：查实时文档。
3. Sequential Thinking：复杂问题分析。
4. Playwright 或 Puppeteer：网页验证二选一。
5. 少量自建项目 Skill：项目结构、开发流程、检查命令。
6. 1-2 个自定义 Agent：例如 Frontend Architect、Documentation Agent。

不建议：

1. 同时启用大量 MCP。
2. 把数据库、云服务、支付 MCP 默认开放给通用 Agent。
3. 用 Memory 类 MCP 替代项目文档事实源。
4. 一个 Agent 承担所有角色。

### 8.2 前端 / UI 项目

建议：

1. 设计系统 Rule。
2. Figma AI Bridge。
3. Playwright。
4. UI/UX Skill。
5. 组件规范 Skill。
6. UI Designer 和 Frontend Architect。

### 8.3 后端 / API 项目

建议：

1. API 风格与安全 Rule。
2. Context7。
3. 数据库 MCP（只读优先）。
4. API 测试 Skill。
5. OpenAPI / 契约测试相关工具。
6. Backend Architect 和 API Test Pro。
7. 日志分析 MCP（如 TLS）按需启用。

### 8.4 文档 / 产品管理项目

建议：

1. 事实源边界 Rule。
2. Context7。
3. Lark / Confluence 类 MCP，若团队使用对应平台。
4. PDF-to-Markdown Skill。
5. draw.io / diagram Skill。
6. 需求整理、任务验收、备忘写入等项目专属 Skills。
7. Documentation Agent 或 Project Manager Agent。

### 8.5 企业项目

建议：

1. 优先选择官方 MCP 或可信供应商。
2. 统一管理 Token 和授权。
3. 将高风险 MCP 绑定到专用 Agent。
4. 使用 Rule 规定审批、人类确认、只读优先。
5. 对项目级 `.trae/mcp.json` 进行代码审查。
6. 对自定义 Agent Prompt 和 MCP 配置建立分享前脱敏流程。

---

## 9. 风险与反模式

### 9.1 反模式：所有 MCP 全部启用

问题：

1. 触发 40 工具上限。
2. 工具描述超过 8000 字符被裁剪。
3. Agent 不知道哪些工具可用。
4. 工具误调用风险上升。

建议：按 Agent 分配 MCP，按任务阶段启用。

### 9.2 反模式：用 Memory MCP 替代项目事实源

问题：

1. Memory 内容可能过期。
2. 难以审计。
3. 与项目文档、任务库冲突。
4. 不适合承载强约束和正式状态。

建议：Memory 只用于辅助偏好和临时上下文，正式事实源仍应在项目文件中。

### 9.3 反模式：高风险 MCP 给通用 Agent

高风险 MCP 包括：

1. 云助手命令执行。
2. 生产数据库写操作。
3. 支付退款。
4. 云资源删除。
5. 文件系统广泛写入。

建议：必须使用专用 Agent、专用 Rule、最小权限，并要求人工确认。

### 9.4 反模式：把复杂 SOP 写进 Rule

问题：Rule 始终加载，会增加上下文压力，也容易与其他规则冲突。

建议：Rule 只写“什么时候必须调用哪个 Skill/Agent”，复杂 SOP 放 Skill。

### 9.5 反模式：自定义 Agent 过度全能化

问题：Agent Prompt 越长、工具越多、职责越广，越容易发生工具误用、上下文污染和输出不稳定。

建议：按角色拆分自定义 Agent，并让 SOLO Agent 或主控 Agent 负责编排。

---

## 10. 信息来源

1. Trae 官方论坛：`https://forum.trae.cn/t/topic/8191`
2. Trae 官方论坛 FAQ：`https://forum.trae.cn/t/topic/65`
3. MCP.directory：`https://mcp.directory/`
4. Trae Skills 官方文档：`https://docs.trae.ai/ide/skills?_lang=zh`
5. Trae Agent 官方文档：`https://docs.trae.ai/ide/agent?_lang=zh`
6. Trae Rules 官方文档：`https://docs.trae.ai/ide/rules?_lang=zh`
7. Trae SOLO Agent 官方文档：`https://docs.trae.ai/ide/solo-coder?_lang=zh`
8. Trae Playwright MCP 教程：`https://docs.trae.ai/ide/tutorial-mcp-playwright?_lang=zh`
9. Trae Figma MCP 教程：`https://docs.trae.ai/ide/tutorial-mcp-figma?_lang=zh`
10. 火山引擎 MCP 市场：`https://www.volcengine.com/mcp-marketplace`
11. Trae 官方最佳实践入口：`https://forum.trae.cn/t/topic/57`
12. 社区 AGENTS.md / Rules 实践：`https://forum.trae.cn/t/topic/9519`
13. 社区智能体优化讨论：`https://forum.trae.cn/t/topic/833`
