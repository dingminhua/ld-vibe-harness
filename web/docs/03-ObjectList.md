# ObjectList 对象列表

> 路由：`/objects/:type`
> 源码：`web/src/pages/ObjectList.tsx`
> API：`GET /api/objects/:type?status=xxx`
> 图标规范：[`09-图标语义规范.md`](./09-图标语义规范.md)

## 1. 页面目标

对象列表用于浏览单一对象类型下的事实对象，并通过状态筛选快速缩小范围。

对象类型切换由左侧主导航完成，本页不再提供顶部类型标签页。

对象列表页是主选择面，不承接详情页的右侧扩展阅读状态；进入 `/objects/:type` 时 App Shell 应主动关闭扩展阅读区。

## 2. 当前页面结构

```text
状态筛选（ObjectStatusFilter）
对象卡片自适应网格（ldvh-section-grid）
  通用卡片：ID + 复制路径图标 + 状态徽章 + 标题 + 信号标签 + 更新时间
  WorkArea 卡片：工作域自身信息 + 按状态分组的计划入口
  TaskPlan 卡片：计划自身信息 + 所属工作域 + 执行态势条 + 任务队列 + 关闭判断信号
加载态 / 错误态 / 空态
```

## 3. 区域详细设计

### 3.1 状态筛选

- 位于列表顶部。
- 由 `ObjectStatusFilter` 根据当前类型聚合状态数量。
- 展示“各状态 + 全部 + 数量”，“全部”固定在最后。
- 数据返回前先渲染稳定的筛选占位，数字位置使用轻量加载动画，避免对象卡片先出现、顶部筛选后插入造成页面跳动。
- 对有活跃态的主工作对象，URL 无 `status` 时默认视为 `active`；用户显式选择全部时写入 `?status=all`。
- 当前状态写入 URL query：`?status=review_needed`。
- 点击对象进入详情页时保留当前 query，使详情页返回路径与列表筛选一致。

### 3.2 对象卡片

- 使用 `ldvh-section-grid`，列数由容器宽度自动决定。
- 不使用表格视图，不使用顶部类型标签页。
- 通用卡片结构：
  - 左上：对象 ID，`ldvh-meta-muted`；
  - 右上：`CopyPathButton` + `StatusBadge`；
  - 中部：本地化标题，`ldvh-card-title`，放入轻量标题带，左侧使用状态语义短线突出，不通过放大字号突出；
  - 可选信号：priority、severity、repeatability、category 等短标签；
  - 底部：`formatDateTime(updated)`，格式为 `YYYY-MM-DD HH:mm`。
- 复制图标复制对象 YAML 文件完整路径，使用 API 返回的 `path`。
- 点击复制图标不得进入详情页；点击卡片其他区域进入详情页。
- hover 时边框变为 `border-ldvh-accent/40`，标题变 accent 色。
- 卡片标题不得超过全局 `ldvh-card-title` 字号；标题强调优先使用轻量背景、位置、留白、状态语义短线和 hover 反馈。

### 3.3 WorkArea 卡片

WorkArea 是“计划入口”卡片，帮助用户判断这个工作域下有哪些活跃/待关闭/已闭合计划，并快速进入仍需推进的计划。

- 保留通用卡片头部：ID、复制路径、状态、标题；标题行整行可点击进入 TaskPlan 详情，标题右侧加箭头作为可进入提示，卡片空白和内部信息区不触发计划跳转。
- 底部更新时间右对齐，工作域 ID 保持在左上角。
- 按计划状态分组展示：
  - 活跃计划组使用 `objectList.activePlanCount`，绿色背景，组标题使用 `ldvh-caption-strong`；
  - 待关闭计划组使用 `objectList.pendingClosePlanCount`，紫色背景，组标题使用 `ldvh-caption-strong`；
  - 已闭合计划只展示 `objectList.closedPlanCount` 汇总，不展开历史计划行，使用 `ldvh-caption-strong`。
- 活跃/待关闭组内每一行是一个计划入口，计划名使用 `ldvh-body`，计划 ID 使用 `ldvh-meta-muted`，并展示计划标题、计划 ID、复制路径按钮和进入箭头，不再重复展示状态标签。
- 计划行可展示一条 compact 任务态势条，复用 TaskPlan 的状态顺序和颜色：`已关闭 / 已验证 / 验证中 / 执行中 / 等待中`；态势条占满计划行宽度，态势段只用 hover / focus tooltip 显示数量，不在 WorkArea 卡片里展开任务或子任务。
- WorkArea 卡片内不得出现大于工作域标题 `ldvh-card-title` 的文字；计划组和汇总都低于工作域标题层级。
- 无计划时展示 `objectList.noPlans`。
- WorkArea 不展示计划内任务标题、子任务或关闭材料；任务拆解留给 TaskPlan 卡片与详情页。
- 点击计划行跳转 `/objects/taskplan/{id}`，不触发外层工作域卡片跳转。

### 3.4 TaskPlan 卡片

TaskPlan 是“计划执行态势”卡片，帮助用户从计划判断任务当前处在哪个阶段、是否存在前置等待，以及关闭判断材料是否齐备。

- 保留通用卡片头部：ID、复制路径、状态、标题。
- 展示所属工作域行，左侧保留工作域对象类型图标，只显示工作域标题；不显示工作域 ID，把空间留给 title。
- 执行态势条归入任务队列区域，不再作为独立卡片；任务队列标题下直接展示整体态势条，态势段 hover / focus 时显示状态和数量。
- Task 状态图例在列表顶部右侧展示，卡片任务行只保留图标和颜色，不重复状态文字。
- Task `review_needed` 在 Web 展示为“已验证”，表示已通过验证但尚未 `closed`；Plan 的 `review_needed` 仍表示待关闭审查。
- TaskPlan 卡片态势按“已关闭 / 已验证 / 验证中 / 执行中 / 等待中”从左到右排列，越接近完成越靠左。
- TaskPlan 卡片态势中，`planned` 统一归入“等待中”；若同时存在未关闭 `blocked_by`，这是 Web 基于前置关系派生的等待原因，不额外拆成第二个态势类别。
- 仅当计划处于 `review_needed` 或已关闭计划缺少关闭字段时，展示关闭判断 / 收口异常区域。
- 展示任务队列区域：
  - 标题为 `objectList.planTaskQueue`；
  - 默认展示最多 10 个任务，排序与态势条空间方向对应：态势条最右侧的状态在队列最上方，最左侧的状态在队列最下方；
  - 任务行包含任务标题、任务 ID、主任务状态图标、同色弱背景、复制路径按钮和进入箭头，任务 ID 使用 `ldvh-meta-muted`；
  - 有子任务的任务行只在行内下方展示 compact 子任务态势条，态势段 hover / focus 时显示状态和数量；
  - 不展示子任务行、子任务标题、子任务 ID 或数量标签；子任务明细属于 Task 详情页或右侧辅助阅读层，不在 TaskPlan 卡片中展开；
  - 任务行整行可点击跳转 `/objects/task/{id}`；标题右侧加箭头作为可进入提示，卡片背景和态势条区域不触发用户无关的路由跳转。工作域行同理，整行可点击跳转工作域详情。

### 3.5 空态、加载态、错误态

- 加载态：居中旋转动画。
- 错误态：`common.loadFailed` + 错误信息。
- 空态：`objectList.noObjects`，不得拼 raw 中文句子。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击左侧导航类型 | 切换到对应 `/objects/:type` |
| 点击状态筛选 | 更新 URL query 并刷新列表 |
| 点击卡片内标题行（对象/计划行/任务行/工作域行）整行 | 跳转到对应对象详情页，保留当前 query，并把当前列表 URL 记录为详情页返回来源 |
| 点击卡片空白、区块标题、态势条、ID、状态徽章或普通信息区域 | 不触发主路由跳转 |
| 从详情页返回对象列表 | 主内容回到 `/objects/:type`，并主动关闭右侧扩展阅读区 |
| 点击复制路径图标 | 复制对象 YAML 文件完整路径，不改变当前页面 |
| 切换语言 | 状态、标题和空态文案同步切换 |

## 5. 实现约束

1. 不恢复顶部对象类型标签页；类型导航已经统一到左侧侧栏。
2. 不把列表改成表格；当前事实对象用卡片扫描。
3. 不展示 raw ISO 时间，统一使用 `formatDateTime()`。
4. 不在列表卡片里塞入长描述；WorkArea 和 TaskPlan 只展示关系、状态、数量、进度和关闭材料信号。
5. 对象卡片必须保留复制完整路径图标，方便把事实源路径交给 AI。
6. Task 和 SubTask 不作为一级导航 tab，但详情路由和关联跳转仍保留。
7. 卡片容器不做整卡点击；导航入口必须绑定到可见对象标题，并在标题后提供箭头和 hover/focus 反馈。内部对象行同理，避免“任务队列”等区块标题或行空白触发外层对象跳转。

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

interface RelatedObjectSummary {
  id: string;
  type: string;
  title: string;
  status: string;
  path: string;
  updated: string;
  blockedBy?: string[];
  openBlockers?: RelatedObjectSummary[];
  subtasks?: RelatedObjectSummary[];  // TaskPlan 下的 Task 可携带 SubTask 摘要
}
```

这些字段只由 `GET /api/objects/workarea` 和 `GET /api/objects/taskplan` 返回，属于 Express API 根据事实对象关系派生的只读摘要；事实源 YAML 不因列表渲染发生写入。
