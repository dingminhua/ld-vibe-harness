# Dashboard 仪表盘

> 路由：`/`
> 源码：`web/src/pages/Dashboard.tsx`
> API：`GET /api/dashboard`

## 1. 页面目标

让用户一眼掌握项目全局状态：对象统计、最近活动、最近变更、校验结果、待推进事项。

## 2. 布局结构

```
┌─────────────────────────────────────────┐
│ 页面标题：仪表盘 / Dashboard            │
├─────────────────────────────────────────┤
│ Profile 卡片（如有）                     │
│ ┌─────────────────────────────────────┐ │
│ │ 项目名 + ID          状态徽章       │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ 统计网格                                │
│ ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐  │
│ │意图││任务││ADR ││BUG ││备忘││画像│  │
│ └────┘└────┘└────┘└────┘└────┘└────┘  │
│ grid-cols-2 sm:3 md:4 lg:5 xl:7       │
├──────────────────┬──────────────────────┤
│ 最近活动         │ 最近变更             │
│ ┌──────────────┐ │ ┌──────────────────┐ │
│ │ 类型标签     │ │ │ 分类标签         │ │
│ │ 标题 状态 时间│ │ │ 描述      时间   │ │
│ │ ...          │ │ │ ...              │ │
│ └──────────────┘ │ └──────────────────┘ │
├──────────────────┼──────────────────────┤
│ 校验状态         │ 待推进               │
│ ┌────┬────┬────┐ │ ┌──────────────────┐ │
│ │状态│错误│警告│ │ │ 类型 标题 状态 时间│ │
│ └────┴────┴────┘ │ │ ...              │ │
│                   │ └──────────────────┘ │
└──────────────────┴──────────────────────┘
```

## 3. 区域详细设计

### 3.1 Profile 卡片

- 条件：仅当 `data.profile` 存在时显示
- 内容：项目标题（中英切换）+ ID + 状态徽章
- 样式：圆角边框卡片，左对齐标题，右对齐状态

### 3.2 统计网格

- 组件：`StatsCard`
- 固定顺序：intent → task → adr → pitfall → memo → profile
- 每张卡片：类型标签 + 计数 + 按状态分布
- 标题文字 `truncate`，数字 `shrink-0`
- 点击跳转：`/objects/{type}`
- 响应式列数：`grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7`

### 3.3 最近活动

- 标题图标：Activity
- 每条：类型标签（带颜色）+ 标题（中英）+ 状态徽章 + 相对时间
- 类型标签颜色：按 1.5 颜色体系
- 相对时间：双语，最小"1分钟前"
- 点击跳转：`/objects/{type}/{id}`
- 空态：`暂无最近活动 / No recent activity`

### 3.4 最近变更

- 标题图标：GitCommit
- 每条：分类标签（带颜色+双语）+ 描述 + 相对时间
- 不显示 hash
- 分类标签：conventional commit 类型，双语（如 功能/Feature）
- 点击跳转：`/changelog`
- 空态：`暂无最近变更 / No recent changes`

### 3.5 校验状态

- 标题图标：Shield
- 三列：状态（通过/未通过）+ 错误数 + 警告数
- 状态图标：CheckCircle（绿）/ AlertCircle（红）
- 数字使用大号等宽字体

### 3.6 待推进

- 标题图标：ArrowRightCircle
- 数据：所有非终态对象，按优先级排序
  - verifying > review_needed > executing > planned > active > proposed
- 每条：类型标签（带颜色）+ 标题（中英）+ 状态徽章 + 相对时间
- 最多显示 8 条
- 点击跳转：`/objects/{type}/{id}`
- 空态：`所有事项已完成 / All items completed`

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击统计卡片 | 跳转到对应类型列表 |
| 点击活动条目 | 跳转到对象详情 |
| 点击变更条目 | 跳转到变更日志 |
| 点击待推进条目 | 跳转到对象详情 |
| 语言切换 | 所有文案、标题、标签、时间跟随切换 |

## 5. API 数据结构

```typescript
interface DashboardData {
  profile: { id: string; title: string; title_en?: string; title_zh?: string; status: string } | null;
  stats: { type: string; total: number; byStatus: Record<string, number> }[];
  recentItems: { type: string; id: string; title: string; title_en?: string; title_zh?: string; status: string; relativeTime: string; typeColor: string }[];
  recentChanges: { hash: string; shortHash: string; message: string; description: string; category: string; author: string; date: string; relativeTime: string }[];
  validation: { ok: boolean; errors: number; warnings: number };
  actionItems: { type: string; id: string; title: string; title_en?: string; title_zh?: string; status: string; relativeTime: string; typeColor: string }[];
}
```

## 6. 已知问题与改进方向

- [ ] Profile 卡片信息量少，可考虑展示项目描述
- [ ] 统计卡片在手机端只有 2 列，信息密度低
- [ ] 校验状态区域可增加"立即校验"按钮
- [ ] 待推进区域缺少优先级视觉区分（如颜色深浅）
