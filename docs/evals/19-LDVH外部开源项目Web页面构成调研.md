# LDVH 外部开源项目 Web 页面构成调研

> 文档编号：22  
> 类型：evals  
> 关联意图：intent-0009  
> 关联任务：task-0051  
> 调研日期：2026-06-06  
> 调研范围：mcp-shrimp-task-manager、BMAD-METHOD、gstack、superpowers

## 1. 背景与目标

LDVH 当前已经形成以 Intent、Task、ADR、Change、Memo、Profile 等事实对象为核心的工作模型。后续若建设 Web 页面，需要同时支持三类需求：

1. 事实对象管理：展示、筛选、查看、编辑、状态流转和引用关系检查。
2. 规范文档浏览：让 specs、工作模型和操作指南形成可导航、可检索的信息架构。
3. 运行态辅助：展示当前 Core Loop、Human Gate、事实源校验、Change 记录和执行上下文。

本次调研聚焦工作区内已有的外部开源项目，从页面入口、导航结构、页面类型、组件模式和技术栈角度分析其 Web 页面构成，并提炼对 LDVH 页面构建的建议。

## 2. 调研对象总览

| 项目 | Web 类型 | 关键路径 | 对 LDVH 的主要参考价值 |
|---|---|---|---|
| mcp-shrimp-task-manager | React + Vite 管理后台 | `tools/task-viewer` | 事实对象列表、详情、编辑、多层 Tab、历史视图 |
| BMAD-METHOD | Astro + Starlight 文档站 | `website`、`docs` | 规范文档站、侧边栏、i18n、Diataxis 信息架构 |
| gstack | Chrome Extension Side Panel | `extension` | 执行态侧栏、连接状态、调试面板、Inspector |
| superpowers | 轻量 HTML/CSS 交互模板 | `skills/brainstorming/scripts/frame-template.html` | Human Gate、多方案卡片、ADR 对比、低依赖原型 |

## 3. mcp-shrimp-task-manager：事实对象管理后台参考

### 3.1 页面入口与技术栈

`mcp-shrimp-task-manager/tools/task-viewer` 是一个 React + Vite 的任务查看器，依赖 React、React DOM、Vite、TanStack React Table 和 react-i18next。入口结构简洁：`index.html` 提供 root 挂载点，`src/main.jsx` 挂载 React 应用，`src/App.jsx` 承担应用级状态、路由式视图状态和数据加载逻辑。

对 LDVH 的启发是：事实对象管理页可以采用轻量 SPA 形态，而不必一开始构建复杂后端驱动页面。LDVH 的事实源本身是结构化 YAML，因此 Web 页面可以先以“读取事实源 → 归一化对象模型 → 表格/详情/编辑视图”的方式组织。

### 3.2 页面构成

该项目的 Task Viewer 具备比较完整的后台页面结构：

- `TaskTable.jsx`：任务列表和表格视图。
- `TaskDetailView.jsx`：任务详情。
- `TaskEditView.jsx`：任务编辑。
- `HistoryView.jsx`、`HistoryTasksView.jsx`：历史任务与审计视图。
- `TemplateManagement.jsx`、`TemplateEditor.jsx`、`TemplatePreview.jsx`：模板管理。
- `GlobalSettingsView.jsx`：全局设置。
- `NestedTabs.jsx`：多层 Tab 导航。
- `Toast.jsx`、`ToastContainer.jsx`、`Spinner.jsx`、`Tooltip.jsx`：基础交互组件。

它的 App 层维护 profiles、selectedProfile、tasks、loading、error、autoRefresh、selectedOuterTab、templates、historyData、toasts、currentTask 等状态。这种结构说明其页面不是单一列表，而是“项目/Profile → 对象域 Tab → 具体视图”的多层应用壳。

### 3.3 可迁移到 LDVH 的页面模式

LDVH 可借鉴如下映射：

| Shrimp Task Viewer | LDVH Web 可映射页面 |
|---|---|
| TaskTable | Task / Intent / ADR / Change 列表页 |
| TaskDetailView | 事实对象详情页，展示 YAML 字段、状态、引用、证据 |
| TaskEditView | 事实对象草案与编辑页，展示字段契约与校验结果 |
| HistoryView | Change / Record / closure_evidence 审计页 |
| NestedTabs | Intent、Task、ADR、Memo、Profile、Settings 多域导航 |
| TemplateManagement | 工作模型模板、对象骨架、规范片段管理 |
| GlobalSettingsView | 项目路径、事实源目录、校验命令、Web 配置 |

### 3.4 对 LDVH 的建议

LDVH 的第一阶段 Web 管理后台应优先实现“事实对象列表 + 对象详情 + 状态/引用提示”，不要过早进入复杂可视化。推荐页面层级：

```text
LDVH App Shell
├── Project/Profile Selector
├── Object Domain Tabs
│   ├── Intents
│   ├── Tasks
│   ├── ADRs
│   ├── Changes
│   ├── Memos
│   └── Profiles
└── Current Object Workspace
    ├── List View
    ├── Detail View
    ├── Edit/Draft View
    └── Validation/History View
```

其中 Task 页面应作为首个 MVP，因为 Task 同时连接 Intent、ADR、Change、closure_evidence 和执行状态，最能验证 LDVH Web 的对象关系模型。

## 4. BMAD-METHOD：规范文档站与信息架构参考

### 4.1 页面入口与技术栈

BMAD-METHOD 的 Web 站点位于 `website`，使用 Astro + Starlight 构建文档站。其 `astro.config.mjs` 将站点标题、社交链接、lastUpdated、自定义 CSS、i18n 和 sidebar 集中配置。文档内容位于 `docs`，并按 `tutorials`、`how-to`、`explanation`、`reference`、`zh-cn` 等目录组织。

这类结构很适合 LDVH 的 specs 文档，因为 LDVH 当前的规范文档既有操作性内容，也有模型解释、引用规范和对象契约。

### 4.2 页面构成

BMAD-METHOD 的文档站核心构成包括：

- 顶部 Header：站点标题、搜索、社交链接、主题选择、语言选择。
- Banner：全局提示或强调信息。
- Sidebar：按 Diataxis 结构组织 Tutorials、How-To Guides、Explanation、Reference。
- Content Collections：由 Starlight 管理文档内容。
- i18n：通过 locale 配置和翻译字段支持多语言。
- Custom CSS：用于品牌化和局部样式调整。

`astro.config.mjs` 中的侧边栏配置特别值得 LDVH 借鉴：目录可以自动生成，同时允许在关键入口手工配置 label、slug、translation、collapsed 等属性。

### 4.3 可迁移到 LDVH 的页面模式

LDVH specs 可以拆成类似的信息架构：

| BMAD 文档区 | LDVH 可映射内容 |
|---|---|
| Welcome | LDVH 总览、项目入口、当前事实源说明 |
| Roadmap | LDVH 演进路线、阶段目标、已知限制 |
| Tutorials | 新用户上手：创建 Intent、执行 Task、记录 Change |
| How-To Guides | 操作指南：Human Gate、ADR 决策、Task 关闭、提交纪律 |
| Explanation | 概念说明：Core Loop、事实模型、状态机、事实源回写 |
| Reference | 工作模型规范：Intent、Task、ADR、Change、Memo、Profile |

### 4.4 对 LDVH 的建议

LDVH Web 不应只做事实对象后台，也应提供“规范文档站模式”。建议将 Web 分为两个互补入口：

1. Workbench：面向执行，处理事实对象、状态和校验。
2. Docs：面向理解，展示 specs、工作模型索引和操作指南。

如果两者合并在一个应用中，页面上应明确分区，避免“管理后台”和“文档站”互相干扰。一个可行结构是顶部主导航提供 Workbench / Docs / Settings，Docs 内部再使用 Starlight 式侧边栏。

## 5. gstack：运行态侧栏与调试面板参考

### 5.1 页面入口与技术栈

`gstack/extension` 是 Chrome Extension 结构，`manifest.json` 声明 `side_panel.default_path` 为 `sidepanel.html`。它的 UI 由 side panel、popup、content script、background service worker 和 inspector 组成。虽然不是传统 Web App，但它对 LDVH 的“执行态辅助面板”很有价值。

### 5.2 页面构成

`sidepanel.html` 包含以下运行态界面：

- `security-shield`：安全状态指示。
- `conn-banner`：连接状态和重连操作。
- `browser-tabs`：浏览器标签栏。
- `tab-terminal`：主终端面板。
- `tab-activity`：活动日志。
- `tab-refs`：引用列表。
- `tab-inspector`：元素 Inspector，包括 Box Model、Matched Rules、Computed、Quick Edit。
- `footer` 与 debug tabs：底部状态与调试面板切换。

它的核心思路是：主工作区只保留最关键操作界面，调试信息默认折叠在 debug 区域，需要时展开。

### 5.3 可迁移到 LDVH 的页面模式

LDVH 的运行态侧栏可以映射为：

| gstack 页面元素 | LDVH 可映射页面元素 |
|---|---|
| security-shield | Human Gate / 高风险操作 / 写入事实源状态 |
| conn-banner | 项目连接、事实源路径、校验服务状态 |
| tab-terminal | Core Loop 执行日志、当前任务执行摘要 |
| tab-activity | 最近事实源变更、工具调用、状态流转历史 |
| tab-refs | 引用完整性：source_intent、related_adrs、blocked_by、sub_tasks |
| tab-inspector | 对象字段契约、状态机合法性、acceptance/closure_evidence 检查 |
| debug tabs | 事实源校验、Change 检查、诊断输出 |

### 5.4 对 LDVH 的建议

LDVH Web 应有一个紧凑的执行态面板，用于在用户执行任务时保持上下文可见。推荐结构：

```text
Runtime Panel
├── Current Intent / Task
├── Current Core Loop Stage
├── Human Gate Status
├── Fact Validation Status
├── Recent Changes
└── Debug
    ├── References
    ├── State Machine
    ├── Contract Fields
    └── Validator Output
```

这类面板可以作为 IDE 侧栏、浏览器侧栏或主应用右侧栏存在。重点是降低用户在“规范、事实源、当前任务、验证结果”之间来回切换的成本。

## 6. superpowers：Human Gate 与低依赖交互原型参考

### 6.1 页面入口与技术栈

`superpowers/skills/brainstorming/scripts/frame-template.html` 是一个轻量 HTML/CSS 页面模板，不依赖 React 或复杂构建链。它提供固定 header、可滚动内容区、底部 indicator bar、浅色/深色主题变量、选项组、卡片、mockup、split view、pros/cons 等基础结构。

### 6.2 页面构成

模板中的关键 UI 模式包括：

- Header：显示页面标题和状态。
- Main Content：承载动态内容。
- Indicator Bar：显示当前选择或确认状态。
- Options：多选项方案列表。
- Cards：设计方案或对象卡片。
- Mockup：页面原型容器。
- Split View：左右对比。
- Pros / Cons：取舍分析。
- Theme Variables：基于 CSS 变量的浅色/深色适配。

### 6.3 可迁移到 LDVH 的页面模式

LDVH 中最适合借鉴 superpowers 的场景是 Human Gate 和 ADR 方案选择：

| superpowers 模式 | LDVH 可映射场景 |
|---|---|
| options | Human Gate 选项：确认、取消、需要修改 |
| cards | ADR 备选方案、Task 拆解方案、Web 页面原型方案 |
| indicator-bar | 当前选择、等待确认、已确认状态 |
| pros-cons | ADR 决策取舍、架构方案比较 |
| mockup | LDVH 页面原型展示 |
| split | 当前实现 vs 建议实现、规范要求 vs 实际事实源 |

### 6.4 对 LDVH 的建议

LDVH 的 Human Gate 不应只是文本问答，也可以被设计成稳定的交互页面：上方是背景与风险摘要，中间是可选方案卡片，下方是当前选择与确认状态。对于 ADR，这种页面还能展示每个方案的取舍、影响范围和状态机约束。

## 7. LDVH 页面构建总体建议

### 7.1 建议采用三层页面体系

综合四个项目，LDVH Web 建议拆成三层：

```text
LDVH Web
├── Workbench：事实对象管理后台
│   ├── Intent / Task / ADR / Change / Memo / Profile 列表
│   ├── 对象详情、编辑、状态流转、引用关系
│   └── 校验结果、历史记录、closure_evidence
├── Docs：规范文档站
│   ├── specs 文档浏览
│   ├── 工作模型索引
│   ├── 操作指南 / 概念说明 / 参考规范
│   └── 搜索、主题、多语言
└── Runtime Panel：运行态辅助侧栏
    ├── 当前 Core Loop 阶段
    ├── Human Gate 状态
    ├── 事实源校验与引用检查
    └── 最近 Change / 执行日志 / 调试信息
```

这三层对应的主要参考来源分别是：

- Workbench：mcp-shrimp-task-manager。
- Docs：BMAD-METHOD。
- Runtime Panel：gstack。
- Human Gate / ADR 交互构件：superpowers。

### 7.2 MVP 页面优先级

建议 LDVH Web MVP 按以下顺序构建：

1. Task 列表页：展示 status、source_intent、blocked_by、acceptance 摘要、updated。
2. Task 详情页：展示 description、acceptance、verification、related_adrs、affected_docs、deliverables。
3. Intent 详情页：展示 goal、success_criteria、related_tasks 和完成度。
4. Fact Validation 面板：展示 fact_validate 输出、对象错误定位、历史错误与本次错误区分。
5. Change / Record 视图：展示事实源变更、状态流转、证据。
6. Docs 入口页：按工作模型索引展示 specs。
7. Human Gate 页面：以方案卡片形式支持确认、取消、修改。
8. Runtime Panel：显示当前任务、当前阶段、Human Gate、校验状态。

### 7.3 信息架构建议

LDVH Web 的主导航可采用：

```text
Overview | Workbench | Docs | Runtime | Settings
```

Workbench 内部对象域：

```text
Intents | Tasks | ADRs | Changes | Memos | Profiles
```

每个对象域内部统一三段式：

```text
List | Detail | Validation/History
```

这样可以保证不同事实对象之间的页面结构一致，降低用户理解成本。

### 7.4 组件模式建议

建议抽象以下通用组件：

| 组件 | 用途 |
|---|---|
| ObjectTable | 所有事实对象列表的通用表格 |
| ObjectDetail | YAML 字段详情展示 |
| StatusBadge | planned / executing / blocked / verifying / closed 等状态 |
| ReferenceList | source_intent、related_tasks、related_adrs、blocked_by 等引用展示 |
| AcceptanceChecklist | acceptance 检查列表展示与完成态提示 |
| ValidationPanel | fact_validate 结果展示 |
| ChangeTimeline | Change / Record / 状态流转历史 |
| HumanGateOptions | 确认、取消、修改、多方案选择 |
| AdrDecisionCard | ADR 备选方案、取舍、影响范围 |
| RuntimeBanner | 当前项目、事实源、Human Gate、校验状态提示 |

### 7.5 技术路线建议

从调研对象看，LDVH Web 可以分阶段选择技术路线：

1. 若优先做管理后台：采用 React + Vite 风格，参考 mcp-shrimp-task-manager。
2. 若优先做规范站：采用 Astro + Starlight 风格，参考 BMAD-METHOD。
3. 若优先做 IDE/浏览器侧栏：采用轻量 HTML/CSS/JS 或 Extension Side Panel 风格，参考 gstack。
4. 若只做 Human Gate 原型：采用无构建 HTML 模板，参考 superpowers。

推荐先以 React + Vite 做 Workbench MVP，同时保留 Docs 可以由 Astro/Starlight 独立构建。两者不必在第一阶段强行合并。

## 8. 风险与注意事项

1. 不要把 LDVH Web 做成普通 YAML 编辑器。它应体现状态机、Human Gate、引用完整性、Change 记录等 LDVH 规则。
2. 不要让 Docs 与 Workbench 页面职责混乱。Docs 用于理解规范，Workbench 用于执行与管理。
3. 不要在第一阶段实现过多对象编辑能力。编辑事实源会触发规则、状态机和 Human Gate，复杂度高于只读展示。
4. 不要忽略历史错误与本次错误的区分。Fact Validation 面板应能显示“既有错误”和“本次新增错误”。
5. 不要把 proposed ADR 或未关闭 blocked_by 的 Task 当作可执行依据。Web 页面应显式提示这些状态约束。

## 9. 结论

本次调研显示，LDVH Web 最适合采用“管理后台 + 文档站 + 运行态侧栏”的组合，而不是单一页面形态。

最直接可落地的路径是：先参考 mcp-shrimp-task-manager 建设 Task/Intent 管理后台 MVP；再参考 BMAD-METHOD 建设 specs 文档站；随后参考 gstack 增加运行态辅助侧栏；最后参考 superpowers 将 Human Gate 和 ADR 方案选择做成可视化交互组件。

这一组合既能服务 LDVH 的事实对象管理，也能服务规范理解和执行过程监督，符合 LDVH 以事实源、状态机、Human Gate 和 Change 记录为核心的工作模型。
