# ObjectList 对象列表

> 路由：`/objects/:type`
> 源码：`web/src/pages/ObjectList.tsx`
> API：`GET /api/objects/:type`；WorkCase 使用 `?progress=<progress_group>`，其它对象按各自契约使用 `?status=<status>`
> 图标规范：[`09-图标语义规范.md`](./09-图标语义规范.md)

## 1. 页面目标

对象列表用于浏览单一对象类型下的事实对象，并通过该对象类型的浏览分类快速缩小范围。WorkCase 使用 Web 派生的“进展分组”，不能把它写成事实状态或生命周期。

对象类型切换由左侧主导航完成，本页不再提供顶部类型标签页。

对象列表页是主选择面，不承接详情页的右侧扩展阅读状态；进入 `/objects/:type` 时 App Shell 应主动关闭扩展阅读区。

## 2. 当前页面结构

```text
浏览筛选（WorkCase 使用 WorkCaseProgressFilter；其它对象使用 ObjectStatusFilter）
对象卡片自适应网格（ldvh-section-grid）
  通用卡片：ID + 复制对象路径图标 + 状态徽章 + 优先级字符徽标 + 标题 + 信号标签 + 更新时间
  WorkCase 卡片：对象身份 + 进展分组 + 已确认分组的专属正文
加载态 / 错误态 / 空态
```

## 3. 区域详细设计

### 3.1 浏览筛选

- 位于列表顶部。
- 浏览筛选及同层任务态势图例属于列表切换控制区，必须固定在主滚动容器顶部；对象卡片列表在其下方滚动。
- WorkCase 由 `WorkCaseProgressFilter` 展示 `plan_confirmation / progressing / closure_confirmation / closed` 四个进展分组及“全部”，数量读取 API 的 `progressOptions`；四个值的显示顺序固定，“全部”放在最后。
- WorkCase 筛选写入 `?progress=<progress_group>`；没有 `progress` 时展示全部 WorkCase。原始 `status` 或 `phase` 不成为 WorkCase 列表的另一套同级筛选。
- 其它对象由 `ObjectStatusFilter` 根据各自状态契约展示“各状态 + 全部 + 数量”，并把选择写入 `?status=<status>`。
- 两类筛选都使用全局 tab 样式：`ldvh-tab-list`、`ldvh-tab-button`、`ldvh-tab-button-active` 和 `ldvh-tab-button-idle`，与提交记录页加载范围、type、scope 筛选保持一致。
- 数据返回前先渲染稳定的筛选占位，数字位置使用轻量加载动画，避免对象卡片先出现、顶部筛选后插入造成页面跳动。
- 无法形成合法 `progress_group` 的 WorkCase 仍属于“全部”的读取范围，但不能被猜入四个分组；界面应如实保留其不可判定状态，不能用 legacy 显示词补造分组。
- 点击对象进入详情页时保留当前 query，使详情页返回路径与列表筛选一致。

### 3.2 对象卡片

- 使用 `ldvh-section-grid`，列数由容器宽度自动决定。
- 不使用表格视图，不使用顶部类型标签页。
- 所有对象卡片一律按 `updated` 时间倒序排列，最近发生变化的对象在最前；状态只用于筛选、徽章和卡片内容表达，不参与排序。
- 通用卡片结构：
  - 左上：对象 ID，`ldvh-meta-muted`；
  - 右上：`CopyPathButton` + `StatusBadge`；
  - 中部：本地化标题，`ldvh-card-title`，放入轻量标题带，左侧使用状态语义短线突出，不通过放大字号突出；标题必须允许换行完整显示，不得用截断省略代替阅读；
  - 优先级字符徽标：WorkCase 和 Spark 如存在 `priority`，在标题行最前面展示 `P0` / `P1` / `P2` / `P3` 字符徽标，随后才是 `ObjectTypeIcon(obj.type)` 和标题；徽标使用颜色、轻量边框和 tooltip 表达优先级，不作为错误或阻塞状态；
  - 可选信号：仅当对应对象的字段契约定义该字段时展示；`priority` 只适用于 WorkCase 和 Spark，不得为 ADR、Pitfall 或 Study 杜撰 priority，也不得为任何对象杜撰 importance、category 或 tags；Spark 不维护 category；Pitfall 不维护 repeatability；importance 字段已由 priority 统一承载，不作为独立字段使用
  - 终态处置：ADR、Pitfall 与 Spark 不复用泛化的“非活跃原因”字段。它们在各自终态卡片中只读取 `disposition_summary`，用弱圆点与小号正文承载，不另造“退出理由”“关闭时间”“分流时间”标签；缺失时如实显示处置缺失提示，仍不得压过标题、状态和更新时间。
  - Pitfall 状态筛选只认 `active / retired`，不得展示 `draft`、`superseded` 或“已替代”入口；Pitfall 卡片不展示 `tags`，也不展示“已解决/未解决”等冗余解决态；Pitfall 标签是事实源索引和详情页辅助信息，不作为列表卡片信号或二层筛选 tab。
  - 底部：只展示更新时间，使用 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`，样式为弱化元信息 `ldvh-meta-muted`；更新时间行使用 `mt-auto` 贴近卡片下边距，避免不同标题行数或中部内容高度导致时间上浮；对象列表以更新时间排序，创建时间留在详情页身份区展示。
- 复制图标展示“复制对象路径”，复制对象事实源文件完整路径，使用 API 返回的 `path`。
- 点击复制图标不得进入详情页；点击卡片外层空白、标题带、ID、状态徽章或更新时间进入对象详情页。
- hover 时边框变为 `border-ldvh-accent/40`，标题变 accent 色。
- 卡片标题不得超过全局 `ldvh-card-title` 字号；标题强调优先使用轻量背景、位置、留白、状态语义短线和 hover 反馈。

### 3.3 ADR 卡片

ADR 是“已确认但尚未完全吸收到 specs/rules/code/web/skill/agent/workflow 的决策补丁”。列表卡片只帮助用户定位当前补丁，不在卡片内展示补丁影响范围。

- ADR 状态筛选只认 `active / retired`。`active` 是当前有效补丁；`retired` 表示不再作为当前决策入口。
- ADR 卡片使用通用卡片结构：ID、复制对象路径、状态、完整标题、更新时间；`retired` 时在标题之后以弱处置正文展示 `disposition_summary`。
- ADR 标题就是最好的摘要；除 retired 的处置正文外，卡片不展示 `decision_question`、`decision`、`applicability`、`rationale`、`consequences`、关联或未采纳备选摘要。
- ADR 卡片标题必须允许换行完整显示，避免用截断标题替代决策识别。
- ADR 卡片不展示 `related_rules` chip，也不展示 `superseded_by`、`proposed`、`accepted`、`rejected`、`superseded`、`alternatives` 或 `affects` 等旧生命周期和旧字段信息。

### 3.4 WorkCase 卡片

WorkCase 卡片帮助 Human 识别当前工作责任所处的进展分组，并按各分组真正需要关注的信息继续阅读。它首先区分“仍在推进”与“稳定停留”，不能把等待 Human 或已经关闭的 WorkCase 画成仍有自动推进。

- 保留通用卡片头部：ID、复制对象路径、状态、标题。
- 不显示虚构的“所属工作责任”归属行；Card 标题识别 WorkCase 自身，内部 work item 只在“推进中”按本节规则呈现当前 active 项。
- WorkCase Card 和列表筛选只使用四个进展分组：`plan_confirmation`（方案待确认）、`progressing`（推进中）、`closure_confirmation`（关闭待确认）、`closed`（已关闭）。界面分类轴命名为“进展分组”，不得显示为“生命周期”。创建前计划复核时尚无正式 WorkCase，不提供 Card 或筛选项。
- 每张 Card 必须直接显示自己的进展分组，不能要求 Human 只靠顶部筛选位置推断；来源 phase 不再作为与四个分组同级的 Card 主状态。
- “方案待确认”Card 在通用身份、标题和进展分组之外只显示“目标”和“成功标准”：目标直接读取 `goal`；`control-contract-v1` 与 `control-contract-v2` 的成功标准读取 `success_criterion_definitions[].statement`，legacy 读取 `success_criteria`。两项必须完整显示，不截断、不折叠、不限制标准条数，也不生成摘要。“覆盖”和“排除”属于 `scope` 中的技术边界，留在同源详情读取；Card 不展示内部工作项、执行步骤、创建前计划复核详情、执行统计或关闭报告与分流建议，完整计划批准仍进入详情完成。
- “方案待确认”Card 使用四级排版层级：对象标题使用 16px 强调卡片标题，两个判断区标题使用 13px 卡片判断项标题，事实原文使用 12px 卡片判断项正文，ID、数量和时间使用元信息。判断项正文仍是事实正文，不得使用弱色或 mono 把它降成辅助信息；不得在业务组件内用临时字号制造层级。
- 成功标准没有先后关系，统一使用圆点无序列表；不得因数组位置、criterion ID 或当前显示顺序使用数字序号。只有来源明确规定步骤、优先级、排名或依赖顺序的内容才使用编号。
- “推进中”Card 保留“目标”，并把第二个区域从“成功标准”替换为“当前进展”：目标继续完整读取 `goal`；当前进展显示由 `progress_step` 指定的四环节当前位置、`work_items` 支撑的“已完成 N/T”与 active 项，以及事实中实际存在的等待或阻塞。Card 不显示成功标准、scope、依赖、方法、完整工作项计划、态势条、验证安排、Reviewer 复核、Controller 处置、Human 批准或关闭报告与分流建议。
- “当前进展”以当前环节为主信息，在同一摘要层显示工作项完成数，不显示返回次数、复核次数或其它过程计数。四个环节使用一条 1–4 的连续结构轨迹，只有当前位置使用强调色和轻微动态信号；轨迹线及其它位置保持中性，不借颜色、连线或勾选暗示前序环节已经完成或对象不会返回。窄屏允许当前环节与完成数换行，但不得改变它们的阅读先后或把四环节拆成 2×2 宫格。
- 工作项完成数对 `control-contract-v1` 与 `control-contract-v2` 只计 `completed`，`cancelled` 单独显示；active 项按对象内的事实顺序列出全部 `in_progress` 和 `blocked` 项的稳定 item_id、完整 goal 与当前状态，blocked 项同时显示已记录的阻塞说明。active 项使用无序圆点，`item_id` 和状态作为元信息，完整目标作为事实正文。两种 control-contract profile 的 work item 投影必须先确认完整结构、唯一稳定 ID、目标、状态条件和依赖图均有效；任一成员不成立时，完成数和 active 项整组显示“工作项进展不可判定”，但不隐藏仍可由 phase 确定的当前环节。不得丢弃错误成员后计算部分总数，也不得用数组位置、title 或 ID 生成替代身份/目标。只有 21 已定义的 legacy 对象允许旧字段 fallback；缺 profile、未知 profile 或无法确定 legacy 身份的对象不得补造 `execution-item-N`。不得把 item ID 尾号解释成执行顺序，也不得在并行项中挑一个冒充唯一当前项。
- Web 同时识别 `control-contract-v1` 和 `control-contract-v2` 为结构化 WorkCase profile；`2026-07-26T12:45:00+08:00` 起新建对象必须使用 v2，边界后的 v1 不得借 Web fallback 冒充 current 对象。v2 work item 的 `approach_summary` 可缺省；v1 仍按其自身结构要求消费。
- `item_execution` 没有 active 项但仍有 pending 项时，以弱化正文显示“尚无进行中工作项”；全部项都已完成或取消时显示环节与状态不一致。主控自检、独立复核和主控收敛不为预期为空的 active 项生成噪声；如仍有 pending 或 active 项，则显示环节与状态不一致。
- 四个推进环节存在确定顺序，可以使用 1–4 编号；编号只表达环节次序，不能根据当前位置把前序环节标成已完成或生成经过历史。当前位置缺失时明确显示“当前环节不可判定”。
- `waiting_on` 实际存在时完整显示，不根据当前环节自动补造等待文案。`status=blocked` 是推进位置上的独立异常信号；Card 保留当前推进环节，并在“当前进展”区域完整显示 `blocking_summary`，缺失时明确提示。等待与阻塞同时存在时均保留，Web 不作语义去重。
- “推进中”可用轻微、遵守减弱动态偏好的动效提示当前位置；方案待确认、关闭待确认和已关闭不显示脉冲或推进轨迹。两个 Human 确认关口必须保持为不同进展分组。
- 进展分组直接显示在通用卡片头部；正文中的推进环节只表达当前浏览语义。status、phase 与授权的事实含义仍以事实源和详情阅读为准。
- 内部 `closure_preparing` 投影为“推进中 / 主控收敛”：此时 Controller 正在吸收当前结果复核并形成关闭报告与分流建议，尚未向 Human 提交关闭请求。只有事实 phase 实际进入 `human_closure_confirming` 后才显示“关闭待确认”，不得提前制造 Human 待办。
- “关闭待确认”和“已关闭”Card 的正文仍待后续设计；在结论进入规范前不得自行套用旧执行态势布局。
- 现有 API 的 `hasPlanConfirmedAt`、`hasClosureRequestedAt`、`hasVerificationEvidence` 和 `hasClosureEvidence` 只为旧消费者及尚未重做的关闭诊断保留。尤其 `hasClosureRequestedAt` 只说明关闭 Human Gate 正在等待或已经完成，不表示存在请求时间。这些兼容诊断可以防止 v1/v2 对象被误报为材料缺失，但不构成“关闭待确认”或“已关闭”Card 的最终字段、内容优先级或视觉设计。

### 3.5 Spark 卡片

Spark 是“待分流信息”卡片，列表态用于快速定位每条火花，并在已经形成终态处置时提示闭环事实；待处理卡片不展开意图、摘要、演变或长正文。

- Spark 卡片保留通用头部、标题、优先级字符徽标、状态和更新时间。
- Spark 卡片不使用通用非活跃原因块；卡片中部只由 Spark 闭环状态驱动。
- Spark 卡片中部状态内容必须使用与 Pitfall 归档原因一致的弱说明表达：弱圆点、小号标签、小号正文，无彩色外框、无大面积状态底色、无 section 标题级强调。
- `open` 时，卡片中部不展示 `intent`、`summary` 或 `evolution`；这些内容留在详情页按阅读节点展开。
- `routed`、`implemented` 与 `discarded` 时，卡片中部只展示 `disposition_summary`。状态徽章说明终态类别，正文说明实际处置；不在卡片中显示承接目标、额外终态时间或旧的 `resolved_to` / `resolved_at` / `discard_reason` 投影。
- Spark 卡片内部信息区域只用于阅读，不响应主路由跳转；点击外层卡片仍进入 Spark 详情页。

### 3.6 Spark 创建边界

Spark 列表页保持只读；Web 不提供 Spark 创建、直接捕获、写入或由表单生成 Spark 的入口。Spark 的对象化、既有对象查重和受控创建只由 AI 按 20 与 31 的规则调用 Helper 完成；Web 只呈现当前事实源中的结果。

### 3.7 空态、加载态、错误态

- 加载态：居中旋转动画。
- 错误态：`common.loadFailed` + 错误信息。
- 空态：`objectList.noObjects`，不得拼 raw 中文句子。

### 3.8 五个基准模块中的对象列表基线

研究、决策、火花、经验四个对象列表已经进入五个基准模块，应作为非工作主线对象卡片的统一基线。提交列表不属于工作对象列表，但其卡片网格、标题带、右上复制入口和底部更新时间必须与这四类对象列表保持同一视觉语言。

- 四类对象都使用同一外层卡片框架：浅边框、`ldvh-panel` 背景、`p-4`、`gap-3`、hover/focus 轻微 accent 边框反馈。
- 顶部区域统一为左侧对象 ID、右侧复制对象路径和状态徽章；不得把状态移到标题带右侧，也不得在右侧操作区加入与复制不相关的强视觉按钮。
- 标题带统一使用弱背景、内圈边框、左侧语义短线、对象类型图标、完整标题和右侧进入箭头；标题使用 `ldvh-card-title`，必须允许换行完整显示。
- 更新时间统一放在卡片底部右侧，使用 `formatDateTime()` 和 `ldvh-meta-muted`；列表排序统一按 `updated` 倒序，最近发生变化的对象在最前。
- 研究、决策、火花和经验在列表态只展示对象定位所需信息，不展开长正文；ADR/Pitfall 的 `retired` 与 Spark 的 `routed` / `implemented` / `discarded` 才展示终态 `disposition_summary`，并使用弱说明表达，不升级为强状态模块。
- 终态处置在决策、经验和火花中保持一致：弱圆点、小号正文、无额外标签、无醒目外框、大面积状态底色或标题级强调。
- 四类对象必须继续使用同一 `ObjectStatusFilter` tab 视觉；状态数量数字使用 `ldvh-tab-count`，不得在单个对象页局部改大、改粗或拉开间距。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击左侧导航类型 | 切换到对应 `/objects/:type` |
| 点击浏览筛选 | WorkCase 更新 `progress` query；其它对象更新 `status` query；随后刷新列表 |
| 点击对象卡片外层空白、标题带、ID、状态徽章或更新时间 | 跳转到当前对象详情页，保留当前 query，并把当前列表 URL 记录为详情页返回来源 |
| 点击 WorkCase 关联行 | 跳转到对应 WorkCase 详情页，保留当前列表 URL 作为返回来源 |
| 点击卡片内部信息框、区块标题、态势条或普通信息区域 | 不触发路由跳转，不表现为独立可点控件 |
| 从详情页返回对象列表 | 主内容回到 `/objects/:type`，并主动关闭右侧扩展阅读区 |
| 点击复制对象路径图标 | 复制对象事实源文件完整路径，不改变当前页面 |
| 切换语言 | 状态、标题和空态文案同步切换 |

## 5. 实现约束

1. 不恢复顶部对象类型标签页；类型导航已经统一到左侧侧栏。
2. 不把列表改成表格；当前事实对象用卡片扫描。
3. 不展示 raw ISO 时间，统一使用 `formatDateTime()`。
4. 不在列表卡片里复述完整详情；WorkCase 只按 §3.4 展示当前已经确定的分组专属内容，关闭待确认和已关闭正文在 Human 完成设计前不扩张。
5. 对象卡片必须保留复制对象路径图标，方便把事实源路径交给 AI。
6. 执行项不作为一级导航 tab，也不拥有独立详情路由。
7. 对象卡片外层可作为当前对象入口，提供统一 hover/focus 反馈；内部信息框必须显式阻止外层点击并使用默认光标。只有复制按钮、WorkCase 关联行等明确通向另一处的内部控件可以单独响应；内部工作项不拥有独立详情路由。

## 6. API 数据结构

对象列表 API 返回的字段分为事实源字段和只读派生摘要。`priority`、`importance` 等信号字段只应来自对象 YAML 自身且必须符合对应事实模型字段契约；WorkCase 列表项中的工作项与执行态势字段属于 Express API 根据 Git 文件事实源关系派生的只读摘要，不写回事实源，也不作为对象字段契约来源。

```typescript
interface ObjectItem {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;                    // 当前兼容显示状态，不是 progress_group
  responsibilityStatus?: string;     // 事实对象的责任状态
  phase?: string;                    // 事实源精确 phase
  progress_group?: 'plan_confirmation' | 'progressing' | 'closure_confirmation' | 'closed';
  progress_step?: 'item_execution' | 'controller_self_check' | 'independent_review' | 'controller_synthesis';
  goal?: string;                     // WorkCase 事实字段，Card 必须原样消费
  scope?: string;                    // WorkCase 事实字段，当前 Card 不展示
  waiting_on?: string;               // WorkCase 当前等待；存在时原样展示
  blocking_summary?: string;         // WorkCase 当前阻塞；存在时原样展示
  path: string;
  updated: string;
  priority?: string;                  // WorkCase / Spark 信号字段，只读展示
  executionItems?: RelatedObjectSummary[]; // WorkCase 全部 work item 的只读投影
  executionItemsProjectionValid?: boolean;
  executionItemTotal?: number;
  executionItemDone?: number;
  executionItemCancelled?: number;
  executionItemBlocked?: number;
  executionItemOpen?: number;
  executionItemsInProgress?: RelatedObjectSummary[];
  executionItemsActive?: RelatedObjectSummary[]; // 保持事实数组顺序的 in_progress / blocked 项
  successCriteria?: string[];         // 当前标准陈述；方案待确认 Card 完整显示
  hasSuccessCriteria?: boolean;       // 兼容诊断，不定义 Card 正文
  hasPlanConfirmedAt?: boolean;       // 兼容诊断
  hasClosureRequestedAt?: boolean;    // 兼容诊断：Human 关闭关口正在等待或已经完成；不表示时间戳
  hasVerificationEvidence?: boolean;  // 兼容诊断，不是 current WorkCase 字段
  hasClosureEvidence?: boolean;       // 兼容诊断，不是 current WorkCase 字段
  disposition_summary?: string;         // ADR/Pitfall/Spark 的终态弱处置正文
  intent?: string;                      // Spark 详情节点；列表不展开
  summary?: string;                     // Spark 详情节点；列表不展开
  evolution?: Array<{ at?: string; summary?: string }>; // Spark 详情节点；列表不展开
  research_intent?: string;             // Study 详情节点；列表不展开
  abstract?: string;                    // Study 详情节点；列表不展开
  recommendation_summary?: string;      // Study 详情节点；列表不展开
}

interface RelatedObjectSummary {
  id: string;
  type: string;
  title: string;
  status: string;
  path: string;
  updated: string;
  priority?: string;                  // WorkCase 信号字段，只读展示
  expectedOutput?: string;           // current work item 的 expected_result 投影
  resultSummary?: string;            // current work item 的 result_summary 投影
  blockingReason?: string;           // current work item 的 blocking_summary 投影
  role?: string;                     // legacy 兼容
  mode?: string;                     // legacy 兼容
  inputRefs?: string[];              // legacy 兼容
}
```

`progress_group`、`progress_step`、工作项计数和 `executionItemsActive` 是 Express API 从当前事实对象确定性派生的只读摘要；`goal`、`scope`、`waiting_on` 和 `blocking_summary` 是同一响应保留的事实字段。两类内容都不因列表渲染写回 YAML，但界面必须区分“事实原文”和“派生摘要”。上面明确标注为兼容诊断或 legacy 兼容的字段只服务迁移期消费者，不得反向成为 v1/v2 WorkCase 契约或后续 Card 设计依据。
