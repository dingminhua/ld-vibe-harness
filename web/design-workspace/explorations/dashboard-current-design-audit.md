# LDVH v3 Web Dashboard 当前设计还原与加强方向

> 工作区文件：`web/design-workspace/explorations/dashboard-precise-restoration.html`
> 目标：基于源码事实还原当前 Dashboard，并为后续设计加强提供共同讨论基础。

## 1. 已核对的源码范围

| 模块 | 文件 | 关键事实 |
|---|---|---|
| App Shell | `web/src/components/Layout.tsx` | 整体为 `flex h-screen min-w-[375px] overflow-hidden bg-ldvh-bg`，结构是左侧 Sidebar + 中间 Main + 右侧 ReadingPanel。 |
| Sidebar | `web/src/components/Sidebar.tsx` | `sm` 以下隐藏；展开宽度 `186px`，折叠宽度 `56px`；底部含语言、主题、折叠三个工具按钮。 |
| Dashboard | `web/src/pages/Dashboard.tsx` | 主内容 `p-4 sm:p-6`；PageHeader 后接 summary、Stats Grid、Panel Grid、Recent Activity。 |
| StatsCard | `web/src/components/StatsCard.tsx` | 卡片为 `border rounded-lg bg-panel p-4 gap-3`；包含 icon/label/count、状态分布条、状态标签。 |
| ReadingPanel | `web/src/components/ReadingPanel.tsx` | 桌面右侧面板默认 `380px`；doc/web 类型默认 `680px`；移动端 `<768px` 为底部抽屉，高度默认 `50vh`。 |
| i18n | `web/src/i18n/locales.ts` | 支持 zh/en；导航、Dashboard 标题、对象类型、状态、提交类别等均有翻译。 |
| Theme | `web/src/hooks/useTheme.ts` + `index.css` | 支持 `light / dark / system`，通过 `document.documentElement.classList.toggle('dark')` 生效。 |
| Status Colors | `web/src/utils/statusColors.ts` | 状态色分 light/dark；Dashboard 的状态条和 StatusBadge 依赖这些语义颜色。 |
| Category Colors | `web/src/utils/categoryColors.ts` | 对象类型和提交类别有独立色彩系统。 |

## 2. 当前设计的真实布局规则

### 桌面 / 宽屏

- 左侧 Sidebar 可折叠：
  - 展开：`186px`
  - 折叠：`56px`
- 主内容区为可滚动区域。
- 右侧 ReadingPanel 关闭时宽度为 `0`；打开时默认 `380px`。
- Dashboard 信息顺序：
  1. PageHeader
  2. 态势摘要行
  3. 5 张 StatsCard
  4. Action Items + Recent Commits 两列面板
  5. Recent Activity 区域

### 窄屏 / 平板宽度

- `sm` 以上仍显示 Sidebar，但可占据较大比例。
- Stats Grid 使用 `auto-fit + minmax(min(100%, 12rem), 1fr)` 自动换行。
- Panel Grid 使用 `auto-fit + minmax(min(100%, 22rem), 1fr)`，窄屏下会从双列变单列。

### 手机 / 375px 最小宽度

- App Shell 设置 `min-w-[375px]`。
- Sidebar 在 `sm` 以下直接隐藏。
- ReadingPanel 在 `<768px` 不再是右侧面板，而是底部抽屉。
- 底部抽屉默认高度 `50vh`，带顶部拖拽 handle。

## 3. 当前设计的优点

1. **信息层级稳定**：Dashboard 从态势总览 → 待推进 → 最近变化 → 最近活动，结构清晰。
2. **语义色彩体系完整**：对象类型、状态、提交类别均有独立颜色，不是随意配色。
3. **国际化基础较完整**：导航、标题、状态、类型、类别均已进入 locale。
4. **窄屏规则不是事后补丁**：源码中明确有 `min-w-[375px]`、`sm` Sidebar 隐藏、ReadingPanel 移动端底部抽屉。
5. **阅读面板架构价值高**：对象/文档/Web 预览统一进入右侧阅读区，适合 Human 快速核查上下文。

## 4. 当前设计的主要风险

### 4.1 Dashboard 首屏行动优先级不够强

当前 Stats Grid 位于最上方，Action Items 与 Recent Commits 等权重并列。对于 Human 来说，最重要的可能不是“系统有多少对象”，而是：

- 哪些需要我确认？
- 哪些阻塞了推进？
- 哪些已经可关闭？
- 哪些风险最高？

因此后续可考虑将 Action Items 变成更强的首屏任务区。

### 4.2 国际化后的英文长度风险

英文文案如 `Plan Confirmation`、`Result Review`、`Human Closure Confirmation` 明显长于中文。风险点：

- StatsCard 状态标签拥挤。
- Action Item 右侧 StatusBadge 压缩标题空间。
- 窄屏下英文更容易溢出。

建议后续设计需要专门做英文视图验收，不只看中文。

### 4.3 手机端缺少主导航替代入口

源码当前逻辑是 `sm` 以下隐藏 Sidebar，但当前 Dashboard 页面本身没有明显移动端主导航入口。用户在手机尺寸下可能能看当前页，但难以切换到 Files / Spark / WorkCase / ADR 等页面。

这不是还原原型的问题，而是当前产品设计可以加强的地方。

### 4.4 ReadingPanel 的发现性不足

右侧阅读面板是核心能力，但 Dashboard 页面里用户不一定知道哪些项可以打开阅读面板，哪些只是跳转列表或详情。

建议后续强化：

- 对可预览对象增加明确 affordance。
- 在 Hover / Focus 时显示“预览”语义。
- 关键 Action Item 支持右侧快速预览而不是只进入详情。

## 5. 推荐的加强方向

### 方向 A：行动优先 Dashboard

将 Dashboard 首屏从“统计优先”调整为“行动优先”：

1. 顶部 Summary 改成 3-4 个强语义状态 pill：
   - 待 Human 确认
   - 阻塞 / 需处理
   - 执行中
   - 可关闭
2. Action Items 提升到 Stats Grid 之前或与 Stats Grid 并列左大右小。
3. Highlight 项不只用左边框，而增加优先级、原因、下一步动作。

### 方向 B：国际化安全布局

1. StatsCard 内状态标签允许更自然换行。
2. 英文长状态使用短标签 + tooltip / readable title。
3. Action Item 在窄屏下右侧 metadata 下沉到第二行，避免挤压标题。
4. 每个关键页面都需要 zh/en 双语截图验收。

### 方向 C：手机端导航补位

1. 手机端增加顶部 compact header：Logo + 当前页 + 菜单按钮。
2. 菜单按钮打开移动端 navigation sheet。
3. 保留 ReadingPanel 底部抽屉，但避免和导航抽屉冲突。

### 方向 D：ReadingPanel 显性化

1. 列表项中增加预览 icon 或右侧 preview affordance。
2. Hover 时提示“在阅读区预览”。
3. 支持 Command/Ctrl 点击与普通点击的不同语义：预览 vs 跳转。
4. Dashboard Action Items 默认可在右侧快速展开上下文。

## 6. 下一步建议

建议下一轮不要再只做“还原”，而是基于当前还原文件开一个加强分支：

- `dashboard-enhancement-action-first.html`：行动优先版 Dashboard。
- `dashboard-enhancement-mobile-nav.html`：手机导航补位版。
- `dashboard-enhancement-i18n-safe.html`：国际化安全版。

三版可以并列对比，最后再决定是否进入真实代码实现。

## 7. 已补齐的三条设计分支

### 7.1 行动优先版

文件：`web/design-workspace/explorations/dashboard-enhancement-action-first.html`

设计目的：把“待 Human 确认 / 阻塞 / 执行中 / 可关闭”提升为首屏判断入口，弱化纯统计总数的首屏权重。该版本保留桌面、窄屏、手机视图切换，以及语言、主题、侧栏、阅读面板交互。

### 7.2 手机导航补位版

文件：`web/design-workspace/explorations/dashboard-enhancement-mobile-nav.html`

设计目的：补齐 `sm` 以下 Sidebar 隐藏后缺少主导航入口的问题。该版本提供 mobile topbar、底部四入口 rail、更多导航 sheet，并与阅读底部抽屉保持分层，避免导航抽屉与阅读抽屉语义冲突。

### 7.3 国际化安全版

文件：`web/design-workspace/explorations/dashboard-enhancement-i18n-safe.html`

设计目的：专门压测英文长状态、长标题、窄屏换行和 metadata 下沉。该版本将关键状态 badge 改为可换行，列表标题使用 `overflow-wrap`，并避免右侧状态区域挤压正文标题。

### 7.4 最小验证

已通过静态文件检查确认三个 HTML 文件均存在，并包含对应关键交互与结构标记：视图切换、语言切换、主题切换、阅读预览、移动导航或国际化换行策略。
