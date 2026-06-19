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
  通用卡片：ID + 复制路径图标 + 状态徽章 + 优先级字符徽标 + 标题 + 信号标签 + 更新时间
  WorkArea 卡片：工作域自身信息 + 按状态分组的计划入口
  WorkPlan 卡片：计划自身信息 + 执行态势条 + 关闭判断信号
加载态 / 错误态 / 空态
```

## 3. 区域详细设计

### 3.1 状态筛选

- 位于列表顶部。
- 状态筛选及同层任务态势图例属于列表切换控制区，必须固定在主滚动容器顶部；对象卡片列表在其下方滚动。
- 由 `ObjectStatusFilter` 根据当前类型聚合状态数量。
- 展示“各状态 + 全部 + 数量”，“全部”固定在最后。
- 状态筛选使用全局 tab 样式：`ldvh-tab-list`、`ldvh-tab-button`、`ldvh-tab-button-active` 和 `ldvh-tab-button-idle`，与提交记录页加载范围、type、scope 筛选保持一致。
- 数据返回前先渲染稳定的筛选占位，数字位置使用轻量加载动画，避免对象卡片先出现、顶部筛选后插入造成页面跳动。
- 对有活跃态的主工作对象，URL 无 `status` 时默认视为 `active`；用户显式选择全部时写入 `?status=all`。
- 当前状态写入 URL query：`?status=review_needed`。
- 点击对象进入详情页时保留当前 query，使详情页返回路径与列表筛选一致。

### 3.2 对象卡片

- 使用 `ldvh-section-grid`，列数由容器宽度自动决定。
- 不使用表格视图，不使用顶部类型标签页。
- 所有对象卡片一律按 `updated` 时间倒序排列，最近发生变化的对象在最前；状态只用于筛选、徽章和卡片内容表达，不参与排序。
- 通用卡片结构：
  - 左上：对象 ID，`ldvh-meta-muted`；
  - 右上：`CopyPathButton` + `StatusBadge`；
  - 中部：本地化标题，`ldvh-card-title`，放入轻量标题带，左侧使用状态语义短线突出，不通过放大字号突出；标题必须允许换行完整显示，不得用截断省略代替阅读；
  - 优先级字符徽标：WorkPlan 和 Memo 如存在 `priority`，在标题行最前面展示 `P0` / `P1` / `P2` / `P3` 字符徽标，随后才是 `ObjectTypeIcon(obj.type)` 和标题；徽标使用颜色、轻量边框和 tooltip 表达优先级，不作为错误或阻塞状态；
  - 可选信号：仅当对应对象的字段契约定义该字段时展示；`priority` 只适用于 WorkPlan 和 Memo，不得为 WorkArea、ADR、Pitfall 或 Study 杜撰 priority、importance、category 或 tags；Memo 不维护 category；Pitfall 不维护 repeatability；importance 字段已由 priority 统一承载，不作为独立字段使用
  - 非活跃原因：当对象状态不是 `active` 且事实源存在 `archive_reason`、`deprecated_reason`、`discard_reason` 或 `closure_evidence` 时，卡片标题下展示完整原因说明；原因必须弱于对象 ID、状态、标题和更新时间，不得使用醒目的外框、左侧强线或 section 样式。说明标签单独一行，使用“弱圆点 + 原因标签”，标签文字与正文使用同一弱阅读颜色；正文另起一行，使用小号阅读文本但仍弱于标题，保留换行、项目符号和数字顺序，不得压缩为单行标签，也不得截断为两行。`archived`、`deprecated`、`discarded` 和 `closed` 卡片如缺少对应原因字段，应展示“原因缺失”异常提示，但仍应弱于标题主视觉。
  - Pitfall 状态筛选只认 `active / archived`，不得展示 `draft`、`superseded` 或“已替代”入口；Pitfall 卡片不展示 `tags`，也不展示“已解决/未解决”等冗余解决态；Pitfall 标签是事实源索引和详情页辅助信息，不作为列表卡片信号或二层筛选 tab。
  - 底部：只展示更新时间，使用 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`，样式为弱化元信息 `ldvh-meta-muted`；更新时间行使用 `mt-auto` 贴近卡片下边距，避免不同标题行数或中部内容高度导致时间上浮；对象列表以更新时间排序，创建时间留在详情页身份区展示。
- 复制图标复制对象 YAML 文件完整路径，使用 API 返回的 `path`。
- 点击复制图标不得进入详情页；点击卡片外层空白、标题带、ID、状态徽章或更新时间进入对象详情页。
- hover 时边框变为 `border-ldvh-accent/40`，标题变 accent 色。
- 卡片标题不得超过全局 `ldvh-card-title` 字号；标题强调优先使用轻量背景、位置、留白、状态语义短线和 hover 反馈。

### 3.3 ADR 卡片

ADR 是“已确认但尚未完全吸收到 specs/rules/code/web/skill/agent/workflow 的决策补丁”。列表卡片只帮助用户定位当前补丁，不在卡片内展示补丁影响范围。

- ADR 状态筛选只认 `active / archived / deprecated`。`active` 是当前有效补丁，`archived` 是已被稳定载体吸收，`deprecated` 是已废弃。
- ADR 卡片使用通用卡片结构：ID、复制路径、状态、完整标题、非活跃原因、更新时间。
- ADR 标题就是最好的摘要；除通用非活跃原因阅读块外，卡片不展示 `context`、`decision`、`related_rules` 或未采纳备选摘要。
- ADR 卡片标题必须允许换行完整显示，避免用截断标题替代决策识别。
- ADR 卡片不展示 `related_rules` chip，也不展示 `superseded_by`、`proposed`、`accepted`、`rejected`、`superseded`、`alternatives` 或 `affects` 等旧生命周期和旧字段信息。

### 3.4 WorkArea 卡片

WorkArea 是“计划入口”卡片，帮助用户判断这个工作域下有哪些活跃/待关闭/已闭合计划，并快速进入仍需推进的计划。

- 保留通用卡片头部：ID、复制路径、状态、标题；外层卡片可点击进入 WorkArea 详情，标题右侧加箭头作为对象入口提示；计划分组框本身不响应点击。
- 底部更新时间右对齐，工作域 ID 保持在左上角。
- 按计划状态分组展示：
  - 活跃计划组使用 `objectList.activePlanCount`，文案为“活跃计划”，绿色背景，组标题使用 `ldvh-caption-strong`，标题前只用小圆点；
  - 待关闭计划组使用 `objectList.pendingClosePlanCount`，文案为“待关闭计划”，紫色背景，组标题使用 `ldvh-caption-strong`，标题前只用小圆点；
  - 已闭合计划组使用 `objectList.closedPlanCount`，文案为“已闭合计划”，默认折叠；标题行折叠时展示向下展开箭头，展开后展示向上收起箭头，点击后展开历史计划行，使用 `ldvh-caption-strong`，标题前只用小圆点。
- 活跃/待关闭/已闭合组内每一行是一个计划入口，计划名使用 `ldvh-body`；计划如存在 `priority`，在计划标题行最前面展示 `P0` / `P1` / `P2` / `P3` 字符徽标，随后才是 WorkPlan 对象图标和标题；计划 ID 使用 `ldvh-meta-muted`，并展示计划标题、计划 ID、复制路径按钮和进入箭头，不再重复展示状态标签；右侧复制和进入箭头默认保持中性，复制按钮只有自身 hover 时切到该组背景对应的状态色。
- 各计划组内部的计划入口按 `updated` 时间倒序排列，最近变化的计划在组内最前。
- 计划行可展示一条 compact 执行态势条，复用 WorkPlan 的状态顺序和颜色：`已关闭 / 已验证 / 验证中 / 执行中 / 待执行 / 等待前置`；态势条占满计划行宽度，态势段只用 hover / focus tooltip 显示数量，不在 WorkArea 卡片里展开执行项。
- WorkArea 卡片内不得出现大于工作域标题 `ldvh-card-title` 的文字；计划组和汇总都低于工作域标题层级。
- 无计划时展示 `objectList.noPlans`。
- WorkArea 不展示计划内执行项标题或关闭材料；执行编排留给 WorkPlan 卡片与详情页。
- 点击计划行跳转 `/objects/workplan/{id}`，不触发外层工作域卡片跳转。

### 3.5 WorkPlan 卡片

WorkPlan 是“计划执行态势”卡片，帮助用户从计划判断当前执行处在哪个阶段、是否存在前置等待，以及关闭判断材料是否齐备。

- 保留通用卡片头部：ID、复制路径、状态、标题。
- 不展示所属工作域行；归属信息留在详情页属性区，列表卡片优先保留计划标题、关闭判断和执行态势。
- 执行态势条归入执行态势区域，不再作为独立卡片；区域标题下直接展示整体态势条，态势段 hover / focus 时显示状态和数量。
- 执行项状态图例在列表顶部右侧展示，卡片执行项行只保留图标和颜色，不重复状态文字。
- WorkPlan `review_needed` 表示待关闭审查；执行项的派生态势不得反向定义 WorkPlan 状态机。
- WorkPlan 卡片态势按“已关闭 / 已验证 / 验证中 / 执行中 / 待执行 / 等待前置”从左到右排列，越接近完成越靠左。
- WorkPlan 卡片态势遵守 `specs/08-Web信息同步实现规范.md` §5.5 的派生态势原因语义规则。`planned` 且不存在未关闭前置项时展示为“待执行”；`planned` 且存在未关闭前置关系时展示为“等待前置”。
- 仅当计划处于 `review_needed` 或已关闭计划缺少关闭字段时，展示关闭判断 / 收口异常区域。
- 展示执行态势区域：
  - 标题为 `objectList.planExecutionQueue`；
  - 标题前只使用小圆点，不使用独立对象图标；执行项不是一级工作对象；
  - 默认展示最多 10 个执行项，排序与态势条空间方向对应：态势条最右侧的状态在队列最上方，最左侧的状态在队列最下方；
  - 执行项行包含标题、内部编号、状态图标、同色弱背景和辅助阅读入口；执行项不得拥有独立对象详情路由；
  - 执行态势区域、态势条和普通信息区域不响应主路由跳转，避免误触外层卡片。

### 3.6 Memo 卡片

Memo 是“待分流信息”卡片，列表态用于快速定位每条备忘，并在已经分流或废弃时提示闭环事实；待处理卡片不展开来源、意图或长正文。

- Memo 卡片保留通用头部、标题、优先级字符徽标、状态和更新时间。
- Memo 卡片不使用通用非活跃原因块；卡片中部只由 Memo 闭环状态驱动。
- Memo 卡片中部状态内容必须使用与 Pitfall 归档原因一致的弱说明表达：弱圆点、小号标签、小号正文，无彩色外框、无大面积状态底色、无 section 标题级强调。
- `pending` 且没有分流闭环事实时，卡片中部不展示 `source`、`source_detail` 或 `description`；来源和意图留在 Memo 详情页的正文节点中阅读。
- `resolved` 或存在 `resolved_to` / `resolved_at` 时，卡片中部展示“已分流”区域，消费 `resolved_to` 和 `resolved_at`：`resolved_to` 显示分流目标，`resolved_at` 显示分流时间。不得只用状态徽章表达已解决。
- `discarded` 或存在 `discard_reason` 时，卡片中部展示“已废弃”区域，消费 `discard_reason`；缺少原因时展示原因缺失提示。不得再同时展示通用非活跃原因块造成重复。
- Memo 卡片内部信息区域只用于阅读，不响应主路由跳转；点击外层卡片仍进入 Memo 详情页。

### 3.7 空态、加载态、错误态

- 加载态：居中旋转动画。
- 错误态：`common.loadFailed` + 错误信息。
- 空态：`objectList.noObjects`，不得拼 raw 中文句子。

### 3.8 趋近定稿对象列表基线

研究、决策、备忘、经验四个对象列表已经趋近定稿，应作为非工作主线对象卡片的统一基线。

- 四类对象都使用同一外层卡片框架：浅边框、`ldvh-panel` 背景、`p-4`、`gap-3`、hover/focus 轻微 accent 边框反馈。
- 顶部区域统一为左侧对象 ID、右侧复制完整路径和状态徽章；不得把状态移到标题带右侧，也不得在右侧操作区加入与复制不相关的强视觉按钮。
- 标题带统一使用弱背景、内圈边框、左侧语义短线、对象类型图标、完整标题和右侧进入箭头；标题使用 `ldvh-card-title`，必须允许换行完整显示。
- 更新时间统一放在卡片底部右侧，使用 `formatDateTime()` 和 `ldvh-meta-muted`；列表排序统一按 `updated` 倒序，最近发生变化的对象在最前。
- 研究、决策、备忘和经验在列表态只展示对象定位所需信息，不展开长正文；备忘列表态只在已分流或已废弃时展示闭环事实，并使用弱说明表达，不升级为强状态模块。
- 非活跃原因表达在决策和经验中保持一致：弱圆点、小号标签、小号正文，不使用醒目外框、大面积状态底色或标题级强调。
- 四类对象必须继续使用同一 `ObjectStatusFilter` tab 视觉；状态数量数字使用 `ldvh-tab-count`，不得在单个对象页局部改大、改粗或拉开间距。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击左侧导航类型 | 切换到对应 `/objects/:type` |
| 点击状态筛选 | 更新 URL query 并刷新列表 |
| 点击对象卡片外层空白、标题带、ID、状态徽章或更新时间 | 跳转到当前对象详情页，保留当前 query，并把当前列表 URL 记录为详情页返回来源 |
| 点击计划行 | 跳转到对应 WorkPlan 详情页，保留当前列表 URL 作为返回来源 |
| 点击卡片内部信息框、区块标题、态势条或普通信息区域 | 不触发路由跳转，不表现为独立可点控件 |
| 从详情页返回对象列表 | 主内容回到 `/objects/:type`，并主动关闭右侧扩展阅读区 |
| 点击复制路径图标 | 复制对象 YAML 文件完整路径，不改变当前页面 |
| 切换语言 | 状态、标题和空态文案同步切换 |

## 5. 实现约束

1. 不恢复顶部对象类型标签页；类型导航已经统一到左侧侧栏。
2. 不把列表改成表格；当前事实对象用卡片扫描。
3. 不展示 raw ISO 时间，统一使用 `formatDateTime()`。
4. 不在列表卡片里塞入长描述；WorkArea 和 WorkPlan 只展示关系、状态、数量、进度和关闭材料信号。
5. 对象卡片必须保留复制完整路径图标，方便把事实源路径交给 AI。
6. 执行项不作为一级导航 tab，也不拥有独立详情路由。
7. 对象卡片外层可作为当前对象入口，提供统一 hover/focus 反馈；内部信息框必须显式阻止外层点击并使用默认光标。只有复制按钮、计划行等明确通向另一处的内部控件可以单独响应。

## 6. API 数据结构

对象列表 API 返回的字段分为事实源字段和只读派生摘要。`priority`、`importance` 等信号字段只应来自对象 YAML 自身且必须符合对应工作模型字段契约；WorkArea 和 WorkPlan 列表项中的计划与执行态势字段属于 Express API 根据 Git 文件事实源关系派生的只读摘要，不写回事实源，也不作为对象字段契约来源。

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
  priority?: string;                  // WorkPlan / Memo 信号字段，只读展示
  plans?: RelatedPlanSummary[];       // WorkArea 列表项
  planTotal?: number;
  planClosed?: number;
  planReviewNeeded?: number;
  planActive?: number;
  planRisk?: number;
  planByStatus?: Record<string, number>;
  executionItems?: RelatedObjectSummary[]; // WorkPlan 列表项；字段名待 API 契约稳定
  executionItemTotal?: number;
  executionItemDone?: number;
  executionItemBlocked?: number;
  executionItemOpen?: number;
  hasSuccessCriteria?: boolean;
  hasReviewRequestedAt?: boolean;
  hasVerificationEvidence?: boolean;
  hasClosureEvidence?: boolean;
  hasClosedAt?: boolean;
  archive_reason?: string;             // 非活跃归档原因，卡片完整原因说明展示
  deprecated_reason?: string;          // 非活跃废弃原因，卡片完整原因说明展示
  discard_reason?: string;             // 非活跃废弃原因，卡片完整原因说明展示
  closure_evidence?: string;           // closed WorkPlan 关闭原因来源，卡片完整原因说明展示
  source?: string;                      // Memo 来源，详情页正文节点展示，pending 卡片不展示
  source_detail?: string;               // Memo 意图，详情页正文节点展示，pending 卡片不展示
  resolved_to?: string | { type?: string; ref?: string }; // Memo 分流目标，resolved 卡片展示
  resolved_at?: string;                 // Memo 分流时间，resolved 卡片展示
}

interface RelatedObjectSummary {
  id: string;
  type: string;
  title: string;
  status: string;
  path: string;
  updated: string;
  priority?: string;                  // WorkPlan 信号字段，只读展示
  role?: string;
  mode?: string;
  expectedOutput?: string;
  resultSummary?: string;
  blockingReason?: string;
  inputRefs?: string[];
  evidenceRefs?: string[];
}
```

这些字段只由 WorkArea 和 WorkPlan 列表接口返回，属于 Express API 根据事实对象关系派生的只读摘要；事实源 YAML 不因列表渲染发生写入。执行项字段名在 WorkPlan 数据结构稳定前只作为概念占位，不构成最终 API 契约。
