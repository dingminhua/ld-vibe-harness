# Dashboard 仪表盘

> 路由：`/`
> 源码：`web/src/pages/Dashboard.tsx`
> API：`GET /api/dashboard`

## 1. 页面目标

仪表盘是 LDVH 的全局态势页，用于快速判断：

- 当前有哪些对象需要推进；
- 最近发生了哪些提交；
- 最近有哪些事实对象发生变化。

仪表盘不是营销首页，不使用 hero、介绍区或大面积装饰图形。

## 2. 当前页面结构

```text
页面标题：仪表盘
态势摘要行（如：1 个方案待确认，2 个执行中，1 个关闭待确认）
对象统计网格（workarea/workplan/adr/pitfall/spark/study）
待推进（含复制对象路径图标） + 最近提交
最近活动（含复制对象路径图标）
```

## 3. 关键区域

### 3.1 态势摘要

- 位于页面标题下方。
- 只展示非零关键状态。WorkPlan 使用当前状态机的关键节点：`subagents_plan_reviewing`、`human_plan_confirming`、`executing`、`result_self_checking`、`subagents_result_reviewing`、`human_closure_confirming`；历史 `review_needed` 和通用 `planned` 只作为兼容态势展示。
- 使用 `ldvh-caption`，不得做成大号 banner 或重复统计卡。

### 3.2 对象统计网格

- 使用 `ldvh-dashboard-stats-grid`。
- 固定顺序：workarea → workplan → adr → pitfall → spark → study。
- 每张卡片展示类型名称、总数和状态分布。
- 点击统计卡片跳转到 `/objects/{type}`。

### 3.3 待推进

- 位于第一组主面板左侧。
- 展示非终态对象，WorkPlan 当前状态机和历史待处理状态使用左侧 accent 边线。
- 点击条目打开右侧扩展阅读区，不直接离开仪表盘。
- 每条右侧提供复制对象路径图标，复制 API 返回的对象 `path`，不得触发扩展阅读。

### 3.4 最近提交

- 位于第一组主面板右侧。
- 每条展示提交分类标签、描述和相对时间。
- 点击条目进入 `/changelog`。

### 3.5 最近活动

- 位于第二组主面板。
- 每条展示对象类型、标题、状态和相对时间。
- 点击条目打开右侧扩展阅读区。
- 每条右侧提供复制对象路径图标，复制 API 返回的对象 `path`，不得触发扩展阅读。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击统计卡片 | 跳转到对应对象列表 |
| 点击待推进条目 | 打开右侧扩展阅读区预览对象 |
| 点击最近活动条目 | 打开右侧扩展阅读区预览对象 |
| 点击对象条目复制对象路径图标 | 复制对象事实源文件完整路径，不改变当前页面 |
| 点击最近提交条目 | 跳转到提交记录页 |
| 切换语言 | 页面框架、标签、状态、相对时间同步切换 |

## 5. 实现约束

1. 不把仪表盘改成卡片堆叠的营销首页。
2. 不把待推进和最近活动改回详情页直接跳转；当前主流程是右侧扩展阅读。
3. 不在仪表盘中展示 raw status、raw type 或 raw enum。
4. 不使用固定 `lg:grid-cols-*` 作为唯一布局依据；继续使用 `ldvh-dashboard-*` 自适应网格。
5. 不重复展示同一副标题或同一页面说明。
6. 待推进和最近活动中的工作对象必须保留复制对象路径入口。

## 6. API 数据结构

```typescript
interface DashboardData {
  stats: { type: string; total: number; byStatus: Record<string, number> }[];
  recentItems: { type: string; id: string; title: string; title_en?: string; title_zh?: string; status: string; path: string; relativeTime: string; typeColor: string }[];
  actionItems: { type: string; id: string; title: string; title_en?: string; title_zh?: string; status: string; path: string; relativeTime: string; typeColor: string }[];
  recentChanges: { hash: string; shortHash: string; message: string; body: string; category: string; scope: string; description: string; isBreaking: boolean; author: string; date: string; relativeTime: string }[];
}
```

`recentChanges` 复用 Changelog 的 commit DTO 和 parser；Dashboard 只选择其中少量字段展示，不单独解析 commit message。

项目画像类入口不属于当前 LDVH Dashboard 数据结构。`GET /api/dashboard` 不返回项目画像字段，Dashboard 不展示项目画像卡片，也不维护项目画像导航文案或相关 i18n；管辖项目配置如需展示，应按管辖配置自身语义另行设计。
