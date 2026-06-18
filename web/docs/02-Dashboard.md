# Dashboard 仪表盘

> 路由：`/`
> 源码：`web/src/pages/Dashboard.tsx`
> API：`GET /api/dashboard`

## 1. 页面目标

仪表盘是 LDVH 的全局态势页，用于快速判断：

- 当前有哪些对象需要推进；
- 最近发生了哪些变更；
- 校验和 42 落地检查是否存在缺口；
- 规范落地要求、能力状态和 Human Gate 是否处于健康状态。

仪表盘不是营销首页，不使用 hero、介绍区或大面积装饰图形。

## 2. 当前页面结构

```text
页面标题：仪表盘
态势摘要行（如：1 个工作计划待关闭，6 个备忘待处理）
可选校验错误横幅
LDVH 落地引导卡片
对象统计网格（workarea/workplan/adr/pitfall/memo/study）
待推进（含复制路径图标） + 最近变更
最近活动（含复制路径图标） + 校验状态
规范落地要求合规 + LDVH 落地健康度
LDVH 能力资产摘要
```

## 3. 关键区域

### 3.1 态势摘要

- 位于页面标题下方。
- 只展示非零关键状态，例如 executing、verifying、review_needed、planned 和校验错误。
- 使用 `ldvh-caption`，不得做成大号 banner 或重复统计卡。

### 3.2 LDVH 落地引导

- 处于 `ldvh-dashboard-lead-grid`。
- 展示 42 落地检查、规范落地要求和 Human Gate 的能力状态。
- 使用细进度条区分 closed / degraded / open。
- 主操作按钮进入 `/validate`。

### 3.3 对象统计网格

- 使用 `ldvh-dashboard-stats-grid`。
- 固定顺序：workarea → workplan → adr → pitfall → memo → study。
- 每张卡片展示类型名称、总数和状态分布。
- 点击统计卡片跳转到 `/objects/{type}`。

### 3.4 待推进

- 位于第一组主面板左侧。
- 展示非终态对象，重点状态使用左侧 accent 边线。
- 点击条目打开右侧扩展阅读区，不直接离开仪表盘。
- 每条右侧提供复制完整路径图标，复制 API 返回的对象 `path`，不得触发扩展阅读。

### 3.5 最近变更

- 位于第一组主面板右侧。
- 每条展示提交分类标签、描述和相对时间。
- 点击条目进入 `/changelog`。

### 3.6 最近活动

- 位于第二组主面板左侧。
- 每条展示对象类型、标题、状态和相对时间。
- 点击条目打开右侧扩展阅读区。
- 每条右侧提供复制完整路径图标，复制 API 返回的对象 `path`，不得触发扩展阅读。

### 3.7 校验状态

- 位于第二组主面板右侧。
- 展示通过/未通过、错误数、警告数。
- 数字和状态必须使用统一语义排版类，不使用页面级大标题字号。

### 3.8 规范落地要求合规与落地健康度

- 位于页面底部的总结区。
- 合规摘要展示落地要求数量、已达成、降级、待处理等状态。
- 健康度区展示 42 / landing-report / Human Gate 等能力状态。
- 该区域只展示派生态势，不替代 Git 文件事实源。

### 3.9 LDVH 能力资产摘要

- 展示 04.02 定义的 Rules、Skill、Agent、Hook、Code、Web 等 LDVH 能力资产、位置、资产职责、使用场景、降级方式和 Code 检查状态。
- 数据来源优先指向 `specs/04.02-LDVH能力资产与落地保障规范.md`、Rules 入口分层和 Code 的 LDVH 能力资产检查结果。
- 页面必须明确该区域是只读派生展示，不是用户可选配置，不代表当前外部 AI 开发环境已经安装、启用或原生完整支持这些能力资产。
- 不展示 Code、Web、CLI、MCP、Command、CI 或文档为与 Rules、Skill、Agent、Hook 同级的文本能力资产类型；这些能力如出现，只能作为能力资产、支撑、检查、降级或展示来源说明。
- 若 04.02 能力资产定义缺失、资产类型不齐、资产路径不存在、Rules 未引用 04.02 或 Code 检查失败，应展示错误态或降级提示，并引导 Human 回到 Validate、Code 输出或 Git 文件事实源查看详情。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击统计卡片 | 跳转到对应对象列表 |
| 点击待推进条目 | 打开右侧扩展阅读区预览对象 |
| 点击最近活动条目 | 打开右侧扩展阅读区预览对象 |
| 点击对象条目复制路径图标 | 复制对象 YAML 文件完整路径，不改变当前页面 |
| 点击最近变更条目 | 跳转到变更日志 |
| 点击落地引导按钮 | 跳转到校验页 |
| 查看 LDVH 能力资产摘要 | 只读查看能力资产和检查状态；如需处理问题，跳转或提示到 Validate / Code 输出 / Git 文件事实源 |
| 切换语言 | 页面框架、标签、状态、相对时间同步切换 |

## 5. 实现约束

1. 不把仪表盘改成卡片堆叠的营销首页。
2. 不把待推进和最近活动改回详情页直接跳转；当前主流程是右侧扩展阅读。
3. 不在仪表盘中展示 raw status、raw type 或 raw enum。
4. 不使用固定 `lg:grid-cols-*` 作为唯一布局依据；继续使用 `ldvh-dashboard-*` 自适应网格。
5. 不重复展示同一副标题或同一页面说明。
6. 待推进和最近活动中的工作对象必须保留复制完整路径入口。
7. LDVH 能力资产摘要不得设计成开关、安装向导、可选配置表或环境完整支持声明；只能作为 Human-facing 只读态势展示。

## 6. API 数据结构

```typescript
interface DashboardData {
  landing?: {
    totalRequirements: number;
    gapTotal: number;
    gapByArea: Record<string, number>;
    capabilityStatus: Record<string, string>;
    humanGateStatus: string;
    validationPlanStatus: Record<string, string>;
  } | null;
  stats: { type: string; total: number; byStatus: Record<string, number> }[];
  recentItems: { type: string; id: string; title: string; title_en?: string; title_zh?: string; status: string; path: string; relativeTime: string; typeColor: string }[];
  actionItems: { type: string; id: string; title: string; title_en?: string; title_zh?: string; status: string; path: string; relativeTime: string; typeColor: string }[];
  recentChanges: { hash: string; shortHash: string; message: string; description: string; category: string; author: string; date: string; relativeTime: string }[];
  validation: { ok: boolean; errors: number; warnings: number };
}
```

Profile 是历史残留概念，不属于当前 LDVH Dashboard 数据结构。后续 Web 实现应删除 `GET /api/dashboard` 的 `profile` 字段、Dashboard Profile card、`nav.profiles` 文案和相关 i18n，不得把管辖项目配置展示为项目画像卡片。
