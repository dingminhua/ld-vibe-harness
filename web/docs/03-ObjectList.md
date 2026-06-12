# ObjectList 对象列表

> 路由：`/objects/:type`
> 源码：`web/src/pages/ObjectList.tsx`
> API：`GET /api/objects/:type?status=xxx`

## 1. 页面目标

对象列表用于浏览单一对象类型下的事实对象，并通过状态筛选快速缩小范围。

对象类型切换由左侧主导航完成，本页不再提供顶部类型标签页。

## 2. 当前页面结构

```text
状态筛选（ObjectStatusFilter）
对象卡片自适应网格（ldvh-section-grid）
  通用卡片：ID + 复制路径图标 + 状态徽章 + 标题 + 信号标签 + 更新时间
  WorkArea 卡片：工作域自身信息 + 关联计划摘要 + 计划关闭进度
  TaskPlan 卡片：计划自身信息 + 关联任务摘要 + 任务关闭进度 + 关闭证据信号
加载态 / 错误态 / 空态
```

## 3. 区域详细设计

### 3.1 状态筛选

- 位于列表顶部。
- 由 `ObjectStatusFilter` 根据当前类型聚合状态数量。
- 展示“全部 + 各状态 + 数量”。
- 当前状态写入 URL query：`?status=review_needed`。
- 点击对象进入详情页时保留当前 query，使详情页顶部筛选和返回路径一致。

### 3.2 对象卡片

- 使用 `ldvh-section-grid`，列数由容器宽度自动决定。
- 不使用表格视图，不使用顶部类型标签页。
- 通用卡片结构：
  - 左上：对象 ID，`ldvh-meta`；
  - 右上：`CopyPathButton` + `StatusBadge`；
  - 中部：本地化标题，`ldvh-card-title`；
  - 可选信号：priority、severity、repeatability、category 等短标签；
  - 底部：`formatDateTime(updated)`，格式为 `YYYY-MM-DD HH:mm`。
- 复制图标复制对象 YAML 文件完整路径，使用 API 返回的 `path`。
- 点击复制图标不得进入详情页；点击卡片其他区域进入详情页。
- hover 时边框变为 `border-ldvh-accent/40`，标题变 accent 色。

### 3.3 WorkArea 卡片

WorkArea 是“计划入口”卡片，帮助用户从工作域判断该范围下有哪些计划、计划大致状态如何，并快速进入计划。

- 保留通用卡片头部：ID、复制路径、状态、标题。
- 展示计划总数、进行中、待关闭、风险等摘要 chip。
- 展示计划状态分布 chip，使用本地化状态名。
- 展示关联计划区域：
  - 标题为 `objectList.relatedPlans`；
  - 关闭进度显示为 `{closed}/{total}`；
  - 进度条表示已关闭计划占比；
  - 默认展示最多 4 个计划，按“待关闭 / 执行中 / 风险 / 计划中 / 已关闭”优先级排序；
  - 计划行包含计划标题、计划 ID、计划自身状态、计划内任务关闭进度、复制路径按钮和进入箭头；
  - 点击计划行跳转 `/objects/taskplan/{id}`，不触发外层工作域卡片跳转。

### 3.4 TaskPlan 卡片

TaskPlan 是“任务进度”卡片，帮助用户从计划判断任务拆解、关闭程度和关闭材料是否齐备。

- 保留通用卡片头部：ID、复制路径、状态、标题。
- 展示任务总数、进行中、待关闭、风险等摘要 chip。
- 展示成功标准和完成证据是否已记录。
- 展示任务状态分布 chip，使用本地化状态名。
- 展示关联任务区域：
  - 标题为 `objectList.relatedTasks`；
  - 关闭进度显示为 `{closed}/{total}`；
  - 进度条表示已关闭任务占比；
  - 默认展示最多 5 个任务，按“待关闭 / 执行中 / 风险 / 计划中 / 已关闭”优先级排序；
  - 任务行包含任务标题、任务 ID、任务状态、复制路径按钮和进入箭头；
  - 点击任务行跳转 `/objects/task/{id}`，不触发外层计划卡片跳转。

### 3.5 空态、加载态、错误态

- 加载态：居中旋转动画。
- 错误态：`common.loadFailed` + 错误信息。
- 空态：`objectList.noObjects`，不得拼 raw 中文句子。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击左侧导航类型 | 切换到对应 `/objects/:type` |
| 点击状态筛选 | 更新 URL query 并刷新列表 |
| 点击对象卡片 | 跳转到 `/objects/{type}/{id}`，保留当前 query |
| 点击 WorkArea 卡片内计划行 | 跳转到 `/objects/taskplan/{id}` |
| 点击 TaskPlan 卡片内任务行 | 跳转到 `/objects/task/{id}` |
| 点击复制路径图标 | 复制对象 YAML 文件完整路径，不改变当前页面 |
| 切换语言 | 状态、标题和空态文案同步切换 |

## 5. 实现约束

1. 不恢复顶部对象类型标签页；类型导航已经统一到左侧侧栏。
2. 不把列表改成表格；当前事实对象用卡片扫描。
3. 不展示 raw ISO 时间，统一使用 `formatDateTime()`。
4. 不在列表卡片里塞入长描述；WorkArea 和 TaskPlan 只展示关系、状态、数量、进度和关闭材料信号。
5. 对象卡片必须保留复制完整路径图标，方便把事实源路径交给 AI。
6. Task 和 SubTask 不作为一级导航 tab，但详情路由和关联跳转仍保留。

## 6. API 数据结构

```typescript
interface ObjectItem {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;
  path: string;
  updated: string;
  plans?: RelatedPlanSummary[];       // WorkArea 列表项
  planTotal?: number;
  planClosed?: number;
  planReviewNeeded?: number;
  planActive?: number;
  planRisk?: number;
  planByStatus?: Record<string, number>;
  tasks?: RelatedObjectSummary[];     // TaskPlan 列表项
  taskTotal?: number;
  taskClosed?: number;
  taskReviewNeeded?: number;
  taskActive?: number;
  taskRisk?: number;
  taskByStatus?: Record<string, number>;
  hasSuccessCriteria?: boolean;
  hasCompletionEvidence?: boolean;
}
```

这些字段只由 `GET /api/objects/workarea` 和 `GET /api/objects/taskplan` 返回，属于 Express API 根据事实对象关系派生的只读摘要；事实源 YAML 不因列表渲染发生写入。
