# LD Vibe Harness 参考项目 Web 设计调研

> 创建日期：2026-06-05
> 更新日期：2026-06-09
> 定位：LD Vibe Harness 对参考项目 Web 设计的项目级调研
> 调研边界：不直接构成强制规则
> 执行效力：无；规范规则需进入 docs/specs 正文区，决策或工作事实需进入对应工作对象后才生效
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/02-术语规范.md`、`docs/specs/01-目录说明.md`、`docs/specs/04-事实源边界与承载规范.md`
> 关联意图：intent-0006（Web展示管理）
> 来源任务：task-0034

---

## 1. 调研范围

| 项目 | 路径 | 技术栈类型 | 前端形态 |
|------|------|-----------|---------|
| gstack | `gstack/` | TypeScript + Bun | 浏览器扩展 + 欢迎页 |
| shrimp-task-viewer | `mcp-shrimp-task-manager/tools/task-viewer/` | React 19 + Vite 5 | SPA 任务查看器 |
| trae-pm-kit | `trae-pm-kit/pm-kit-web/` | 原生 HTML/CSS/JS | 多视图管理应用 |

---

## 2. gstack

### 2.1 技术栈

- **运行时**：Bun（非 Node.js）
- **语言**：TypeScript
- **前端形态**：Chrome 扩展（popup + sidepanel + content script）+ 欢迎页
- **无构建工具**：扩展 HTML/CSS/JS 直接部署，browse 模块通过 Bun 编译 TypeScript
- **字体**：DM Sans（正文）、Satoshi（标题）、JetBrains Mono（代码）

### 2.2 布局设计

- **欢迎页**：居中单栏布局，max-width 1060px，三列 feature 卡片网格
- **扩展 popup**：固定 240px 宽度，紧凑纵向布局
- **sidepanel**：侧边栏面板，与浏览器窗口联动
- **响应式**：900px 以下两列，600px 以下单列

### 2.3 主题系统

- **纯暗色主题**，无亮色切换
- CSS 变量体系：`--base: #0C0C0C`、`--surface: #141414`、`--border: #262626`
- **强调色**：Amber（`#F59E0B`/`#FBBF24`），用于按钮、代码高亮、状态指示
- 噪点纹理叠加（SVG feTurbulence，opacity 0.03）增加质感
- 状态色：绿色连接、红色错误、琥珀色重连

### 2.4 组件模式

- 扩展组件（popup/sidepanel/content script）之间通过 `chrome.runtime` 消息通信
- Feature 卡片：统一圆角 12px、1px 边框、surface 背景
- 交互反馈：hover 边框变色、脉冲动画（连接状态指示）
- 侧边栏引导气泡：固定定位 + 箭头动画

### 2.5 设计特色

- **极简暗色美学**：近乎纯黑背景 + 琥珀色强调，视觉层次分明
- **浏览器原生集成**：不追求独立 Web 应用感，而是融入浏览器环境
- **微交互**：logo 脉冲、箭头 nudge 动画、连接状态呼吸灯
- **信息密度低**：欢迎页以引导为主，不堆砌数据

---

## 3. shrimp-task-viewer

### 3.1 技术栈

- **框架**：React 19 + Vite 5
- **UI 库**：@headlessui/react（无样式组件）
- **表格**：@tanstack/react-table
- **Markdown**：@uiw/react-md-editor、react-syntax-highlighter
- **国际化**：i18next + react-i18next + i18next-browser-languagedetector
- **图片**：yet-another-react-lightbox
- **测试**：vitest + @testing-library/react
- **无 CSS 框架**：纯手写 CSS

### 3.2 布局设计

- **单栏居中布局**：max-width 1400px，padding 20px
- **顶部 Header**：居中标题 + 版本信息
- **双层 Tab 导航**：
  - 外层 Tab：projects / release-notes / readme / templates
  - 内层 Tab（projects 下）：tasks / history / settings
- **嵌套 Tab 组件**：NestedTabs 组件支持拖拽排序
- **无侧边栏**：纯 Tab 切换视图

### 3.3 主题系统

- **纯暗色主题**，无亮色切换
- 背景色：`#0a0e27`（深蓝黑）
- 渐变标题：`linear-gradient(135deg, #4fbdba, #7b68ee)`（青绿→紫色）
- 链接色：`#ffff00`（黄色，高可见度）
- 无 CSS 变量体系，颜色直接硬编码

### 3.4 组件模式

- **40+ 组件**，功能丰富：TaskTable、TaskDetailView、TaskEditView、TemplateManagement、AgentViewer、ChatAgent 等
- **URL 状态同步**：`urlStateSync` 工具将 Tab/视图状态写入 URL，支持浏览器前进后退
- **自动刷新**：可配置刷新间隔，localStorage 持久化
- **Toast 通知**：ToastContainer 组件
- **拖拽交互**：Tab 可拖拽排序

### 3.5 设计特色

- **功能密集型**：任务管理、模板编辑、Agent 查看、聊天、历史记录等
- **国际化完整**：i18next 全覆盖，含语言选择器
- **URL 驱动**：视图状态与 URL 同步，可分享/书签
- **无设计系统**：缺乏统一的设计变量和组件规范，颜色硬编码

---

## 4. trae-pm-kit

### 4.1 技术栈

- **无框架**：原生 HTML + CSS + JavaScript（~2300 行 app.js）
- **Markdown 渲染**：marked.js（CDN）
- **图表**：mermaid（CDN）
- **字体**：Fira Sans（正文）、Fira Code（代码），Google Fonts CDN
- **无构建工具**：直接部署静态文件
- **后端**：Node.js 服务，端口管理通过 start.sh

### 4.2 布局设计

- **单栏居中布局**：max-width 1480px，padding 24px 32px
- **顶部健康栏**（health-bar）：产品名称 + 描述 + 刷新按钮
- **Tab 导航**：总览 / 任务 / 任务集 / 产品 / 备忘 / 设置
- **Dashboard 网格**：
  - 任务指标预览：6 列 metric-card 网格
  - 健康仪表盘：7 列网格
  - 双列布局：任务+备忘、需求进度+最近变化
- **看板视图**：Kanban 布局，支持拖拽状态流转
- **滑出面板**：任务详情侧滑面板
- **命令菜单**：键盘快捷键 Cmd+K 唤起全局搜索

### 4.3 主题系统

- **纯暗色主题**，无亮色切换
- **完整的 CSS 变量体系**（32 个变量）：
  - 背景层级：`--bg: #020617` → `--panel: #0c1222` → `--card: #0f172a` → `--soft: #111827`
  - 边框：`--border: #1e3a5f`、`--border-hover: #3b82f6`
  - 文字层级：`--text: #f1f5f9` → `--muted: #94a3b8` → `--dim: #64748b`
  - 语义色：green/blue/cyan/orange/red/purple/yellow
  - 强调色：`--accent-1: #6366f1`、`--accent-2: #8b5cf6`
  - 辉光效果：`--glow-blue/green/cyan/purple`
  - 圆角系统：`--radius-sm(8px)` → `--radius-2xl(24px)`
  - 过渡系统：`--transition-fast(0.15s)` → `--transition-slow(0.35s)`
- **毛玻璃效果**：`backdrop-filter: blur(16px)` + 半透明背景
- **渐变背景**：三色径向渐变（indigo/cyan/purple），fixed 定位
- **卡片顶部渐变线**：hover 时显示 `linear-gradient(90deg, blue, cyan)`

### 4.4 组件模式

- **Pill 标签**：状态标签系统（done/current/next/blocked/waiting/review），各有独立配色
- **Timeline 步骤**：三列网格（时间 + 内容 + 状态），hover 右移效果
- **Metric 卡片**：居中指标展示，hover 上浮 + 顶部渐变线
- **文档卡片**：三列网格，hover 上浮 + cyan 辉光
- **看板**：拖拽排序 + 状态流转
- **模态框**：统一圆角 + 毛玻璃背景
- **搜索输入**：暗色背景 + 圆角 + focus 边框变色

### 4.5 响应式策略

- 980px 以下：网格降为单列，看板降为两列
- 600px 以下：看板降为单列
- 支持 `prefers-reduced-motion`：禁用动画
- 自定义滚动条：6px 宽度，暗色 thumb

### 4.6 设计特色

- **最完整的设计系统**：CSS 变量覆盖颜色、圆角、过渡、辉光
- **视觉层次丰富**：背景渐变 + 毛玻璃 + 辉光 + 卡片顶部渐变线
- **交互反馈细腻**：hover 上浮、边框变色、辉光效果、步骤右移
- **Pill 状态标签**：6 种状态 6 种配色，信息密度与可读性兼顾
- **命令面板**：Cmd+K 全局搜索，提升操作效率
- **无框架约束**：纯原生实现，灵活但维护成本高

---

## 5. 对 LDVH Web 的可借鉴要点

### 5.1 主题系统 → 借鉴 trae-pm-kit

trae-pm-kit 的 CSS 变量体系最完整，LDVH 已有的 RGB 通道变量方案更优（支持 Tailwind 透明修饰符），可补充：

| 借鉴点 | 来源 | LDVH 适配建议 |
|--------|------|--------------|
| 背景层级变量 | pm-kit `--bg/--panel/--card/--soft` | 已有，保持 |
| 辉光效果变量 | pm-kit `--glow-*` | 可选引入，用于卡片 hover |
| 圆角系统变量 | pm-kit `--radius-sm~2xl` | 已有 Tailwind radius，保持 |
| 过渡时间变量 | pm-kit `--transition-fast/base/slow` | 可引入，统一动画节奏 |
| Pill 状态标签 | pm-kit 6 种状态配色 | 已有 STATUS_LOCALES，可增强视觉 |
| 卡片顶部渐变线 | pm-kit metric-card::before | 可借鉴，增加视觉层次 |

### 5.2 布局模式 → 综合借鉴

| 借鉴点 | 来源 | LDVH 适配建议 |
|--------|------|--------------|
| 双层 Tab 导航 | shrimp-task-viewer | LDVH 已有侧边栏+顶部导航，无需双层 Tab |
| 命令面板 (Cmd+K) | trae-pm-kit | 可引入，提升对象搜索效率 |
| 看板视图 | trae-pm-kit | Task 列表可增加看板视图选项 |
| 滑出详情面板 | trae-pm-kit | ObjectDetail 可用滑出面板替代页面跳转 |
| URL 状态同步 | shrimp-task-viewer | 已有，保持 |

### 5.3 交互模式 → 借鉴 gstack + pm-kit

| 借鉴点 | 来源 | LDVH 适配建议 |
|--------|------|--------------|
| 微交互动画 | gstack 脉冲/nudge | 可选择性引入，避免过度动画 |
| 拖拽排序 | shrimp-task-viewer | Tab/列表可支持拖拽 |
| 自动刷新 + 可配置间隔 | shrimp-task-viewer | Dashboard 可引入 |
| 毛玻璃卡片 | trae-pm-kit | 已有 backdrop-filter，保持 |
| prefers-reduced-motion | trae-pm-kit | 应引入，无障碍支持 |

### 5.4 不建议借鉴

| 要点 | 来源 | 原因 |
|------|------|------|
| 纯暗色无亮色切换 | 三个项目均如此 | LDVH 已支持亮暗切换，不应回退 |
| 颜色硬编码 | shrimp-task-viewer | LDVH 已有 CSS 变量体系，不应硬编码 |
| 原生 JS 无框架 | trae-pm-kit | LDVH 已用 React + Tailwind，不应回退 |
| 黄色链接 | shrimp-task-viewer | 视觉突兀，不符合 LDVH 设计语言 |

---

## 6. 总结

三个参考项目各有侧重：

- **gstack**：极简暗色美学 + 浏览器扩展集成，适合借鉴微交互和视觉克制
- **shrimp-task-viewer**：功能密集型 React SPA，适合借鉴 URL 状态同步和国际化
- **trae-pm-kit**：最完整的设计系统（CSS 变量 + Pill 标签 + 命令面板），是 LDVH 最直接的参考

LDVH Web 当前在主题系统（RGB 通道变量 + 亮暗切换）和国际化方面已领先参考项目，可重点从 trae-pm-kit 借鉴辉光效果、Pill 状态标签增强、命令面板和看板视图。
