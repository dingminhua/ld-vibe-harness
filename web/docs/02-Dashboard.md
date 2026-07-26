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
态势摘要行（按 WorkCase 进展分组汇总，如：1 个方案待确认，2 个推进中，1 个关闭待确认）
对象统计网格（workcase/adr/pitfall/spark/study）
待推进 + 最近提交
最近活动
```

## 3. 关键区域

### 3.1 态势摘要

- 位于页面标题下方。
- 只展示非零关键状态。WorkCase 只使用四个进展分组：`plan_confirmation`、`progressing`、`closure_confirmation`、`closed`；Dashboard 不输出原始 phase 或历史显示状态作为 WorkCase 的聚合键。创建前方案审核尚无正式 WorkCase，不进入 Dashboard。
- 使用 `ldvh-caption`，不得做成大号 banner 或重复统计卡。

### 3.2 对象统计网格

- 使用 `ldvh-dashboard-stats-grid`。
- 固定顺序：spark → workcase → adr → pitfall → study。
- 每张卡片展示类型名称、总数和当前分类分布：WorkCase 使用进展分组，其它事实类型使用各自状态。
- 点击统计卡片跳转到 `/objects/{type}`。

### 3.3 待推进

- 位于第一组主面板左侧。
- 展示当前非终态对象；WorkCase 条目只消费由当前 `status` / `phase` 确定的四个进展分组，需要 Human 关注的当前条目可使用左侧 accent 边线。
- 点击条目打开右侧扩展阅读区，不直接离开仪表盘。
- Dashboard 条目属于候选/派生信息，不承诺 `canonical_path`，因此不显示复制对象路径入口。打开扩展阅读后，只有新的精确读取已取得可消费 `canonical_path` 时，预览身份区才可提供复制入口。

### 3.4 最近提交

- 位于第一组主面板右侧。
- 每条展示提交分类标签、描述和相对时间。
- 点击条目进入 `/changelog`。

### 3.5 最近活动

- 位于第二组主面板。
- 每条展示对象类型、标题、当前分类和相对时间；WorkCase 的当前分类是进展分组，其它事实类型的当前分类是状态。
- 点击条目打开右侧扩展阅读区。
- Dashboard 条目本身不显示复制对象路径入口；精确读取后的预览遵守与待推进区相同的条件。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击统计卡片 | 跳转到对应对象列表 |
| 点击待推进条目 | 打开右侧扩展阅读区预览对象 |
| 点击最近活动条目 | 打开右侧扩展阅读区预览对象 |
| 点击最近提交条目 | 跳转到提交记录页 |
| 切换语言 | 页面框架、标签、状态、相对时间同步切换 |

## 5. 实现约束

1. 不把仪表盘改成卡片堆叠的营销首页。
2. 不把待推进和最近活动改回详情页直接跳转；当前主流程是右侧扩展阅读。
3. 不在仪表盘中展示 raw status、raw type 或 raw enum。
4. 不使用固定 `lg:grid-cols-*` 作为唯一布局依据；继续使用 `ldvh-dashboard-*` 自适应网格。
5. 不重复展示同一副标题或同一页面说明。
6. 待推进和最近活动不得用 `path`、`target` 或对象 ID 伪装精确事实源路径；复制对象路径只在后续精确读取结果中成立。

## 6. API 数据结构

```typescript
type DashboardObjectType = 'workcase' | 'adr' | 'pitfall' | 'spark' | 'study';
type WorkCaseProgressGroup = 'plan_confirmation' | 'progressing' | 'closure_confirmation' | 'closed';

interface DashboardItemBase {
  id: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  relativeTime: string;
  typeColor: string;
}

type DashboardFactItem =
  | DashboardItemBase & { type: 'workcase'; progress_group: WorkCaseProgressGroup; status?: never }
  | DashboardItemBase & { type: Exclude<DashboardObjectType, 'workcase'>; status: string; progress_group?: never };

type DashboardStat =
  | { type: 'workcase'; total: number; byProgressGroup: Partial<Record<WorkCaseProgressGroup, number>>; byStatus?: never }
  | { type: Exclude<DashboardObjectType, 'workcase'>; total: number; byStatus: Record<string, number>; byProgressGroup?: never };

interface DashboardData {
  stats: DashboardStat[];
  recentItems: DashboardFactItem[];
  actionItems: DashboardFactItem[];
  recentChanges: { hash: string; shortHash: string; message: string; body: string; category: string; scope: string; description: string; isBreaking: boolean; author: string; date: string; relativeTime: string }[];
}
```

WorkCase 统计只使用 `byProgressGroup`，WorkCase 条目只使用 `progress_group`；三个非终态分组由来源 `phase` 确定，`closed` 分组由来源 `status=closed` 确定。Dashboard 不得把派生进展分组放入名为 `status` 或 `byStatus` 的字段。当前 Dashboard 不对外输出 WorkCase 事实源状态；将来若有独立消费需求，只能另设 `source_status`，不得复用 `status`。其它事实类型仍使用 `status` / `byStatus`，不得带 `progress_group` / `byProgressGroup`。

`recentChanges` 复用 Changelog 的 commit DTO 和 parser；Dashboard 只选择其中少量字段展示，不单独解析 commit message。

项目画像类入口不属于当前 LDVH Dashboard 数据结构。`GET /api/dashboard` 不返回项目画像字段，Dashboard 不展示项目画像卡片，也不维护项目画像导航文案或相关 i18n；管辖项目配置如需展示，应按管辖配置自身语义另行设计。
