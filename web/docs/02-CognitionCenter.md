# 聚焦（内部概念：项目认知中心）

> 路由：`/`（已实现，由 CognitionCenter 服务，取代原 Dashboard）
> 状态：三期均已完成（2026-07-31）；当前页面包含「待决定事项」「推进中事项」「近期动态」「Spark 健康度」「近期提交热点关系」五个模块
> 目标源码：`web/src/pages/CognitionCenter.tsx`（取代 `web/src/pages/Dashboard.tsx`，原文件已移除）
> 目标 API：`GET /api/cognition`（新建，取代 `GET /api/dashboard`）
> 文件名说明：本文取代原 Dashboard 设计文档；文件名、`web/docs` 引用与相关测试契约的更名已在第一期实现中完成。

## 0. 变更决定记录（按 08 §9）

本次改动是有意改变可观察行为，不属于行为保持型重构。按 08 §9 记录决定要素：

| 要素 | 内容 |
|---|---|
| 变更对象 | 路由 `/` 页面及其聚合 API 的可观察行为、左侧导航第一项的名称与图标 |
| 变更前 | Dashboard 仪表盘：态势摘要行、对象统计网格、待推进、最近提交、最近活动 |
| 变更后 | 项目认知中心：待决定事项、推进中事项、近期动态、Spark 健康度、近期提交热点关系五个只读模块与全局信任标记 |
| 作用范围 | 路由 `/`、由 `GET /api/dashboard` 迁移到 `GET /api/cognition`、左侧导航第一项、由 `dashboard.*` 迁移到 `cognition.*` 的 i18n key；对象列表、对象详情、提交记录、ProjectFiles、右侧扩展阅读、复制语义与 i18n 规则不变 |
| 当前来源支持 | 00 §7 第 3 条（Web 交互协作帮助 Human 了解进展、作出决定、给予授权和验收结果）；08 §1；`web/docs/01-全局设计约束.md` §1.2.1（第一入口已确认，仍不写死其余入口） |
| Human 决定 | 2026-07-29 Human 在 AI 对话中明确决定：废弃仪表盘，以项目认知中心取代；设计细节以本文为准 |
| 验收依据 | 本文 §10 验收标准 + 范围匹配的 API、组件与代表性浏览器测试（08 §10 对应行） |
| 明确不变范围 | 五个基准模块（提交、研究、决策、火花、经验）与 WorkCase 阅读形态不因本变更改动；本变更不新增事实源、状态机、对象类型、写入白名单或 Human Gate 结论 |

### 0.1 2026-07-30 导航可见名与图标微调（Human 决定）

本次为有意的可见标签与图标变更，不改变路由、API、页面模块或内部概念名（仍为「项目认知中心」）。按 08 §9 记录：

| 要素 | 内容 |
|---|---|
| 变更对象 | 左侧导航第一项可见名（nav.cognition）、页面标题（cognition.title）、导航图标 |
| 变更前 | 可见名「项目认知中心 / Cognition Center / Project Cognition Center」，图标 `Compass` |
| 变更后 | 可见名「聚焦 / Focus」，图标 `LayoutDashboard`（换回 Dashboard 时期的图标） |
| 作用范围 | 仅 i18n 显示文案与 `Sidebar.tsx` 图标；路由 `/`、GET /api/cognition、页面模块、文档名 `02-CognitionCenter.md`、代码文件名 `CognitionCenter.tsx` 与内部概念名不变 |
| Human 决定 | 2026-07-30 Human 在 AI 对话中明确决定：导航可见名改为「聚焦」，图标换回 `LayoutDashboard` |
| 验收依据 | 切换 zh/en 后导航第一项与页面标题显示「聚焦 / Focus」，图标为 `LayoutDashboard`；其余页面与文档引用「认知中心」不变 |
| 明确不变范围 | 内部概念名、文档与代码文件名、API、页面模块、09 规范中「项目认知中心」的对象类型命名不变 |

### 0.2 2026-07-30 收件箱复用事实 Card 与次级阅读

待决定事项不是第二套对象摘要。收件箱使用 `ldvh-section-grid` 与其它事实对象一致地按容器宽度排成多列；每项直接复用其对象列表 Card 的身份、状态、标题和正文，不把完整事实字段改写为聚焦页专属材料，也不叠加聚焦页专属条目操作。聚焦页只在模块层新增待确认集合、观察信息和复制模块摘要；点击标题不跳转路由，而是在右侧（Compact 时底部）展开同源次级阅读。属对既有设计原则的收敛，不改变来源或只读边界。

模块默认展开；Human 可通过标题带右侧的折叠按钮收起整个待决定事项正文。收起态仍保留模块名、总数与复制模块摘要，使后续模块可继续阅读而不丢失当前待决规模。

## 1. 页面目标

聚焦页是 LDVH 面向 Human 的项目认知入口，内部概念和源码仍使用 Cognition Center，服务六项 Human 价值标准（下称 H1–H6）：

| 标准 | 名称 | 本页对应模块 |
|---|---|---|
| H1 | 项目认知接续 | 推进中事项、近期动态、Spark 健康度、近期提交热点关系 |
| H2 | 决定依据完备 | 待决定事项 |
| H3 | 决定负担有界 | 待决定事项 |
| H4 | 人机理解对齐 | 全局信任标记与复制摘要 |
| H6 | 提及事项闭环 | Spark 健康度 |

H1–H6 当前由 open Spark `ldvh-base/sparks/spark-0037.yaml` 承载，尚未进入规范源。本文引用其名称作为设计目标与验收框架，不把它们登记为规范事实；H 标准后续修订时本文随之修订。

页面边界：LDVH 不代替 Human 产生认知、决定与对齐，只提供方法与工具。本页帮助 Human 形成并维持对项目过去、现在与未来的认知，提供快速、准确、全面的决定依据，并把"AI 的理解与人的理解是否一致"做成可核查的工作方式；认知、决定与方向判断本身仍由 Human 作出，决定的作出与回写只发生在 AI 对话与受控写入路径中。

## 2. 设计原则

1. H1–H6 是北极星与验收框架，不是功能清单。模块建造顺序由真实痛点驱动，待决定事项收件箱第一（§11）。
2. 默认只读。本页不提供批准、关闭、分流、处置或任何可能改变项目状态的控件；每条目只提供查看详情、复制引用、复制摘要。
3. 一切从既有字段派生。不新增事实字段、状态、对象类型；所有聚合、计数、筛选、排序与"未关联"检测都是派生信息，如实标注来源、转换规则与遗漏范围。
4. 继承五个基准模块与 WorkCase 阅读形态的设计语言；新增组件使用同一套 `ldvh-*` 语义类、复制语义、扩展阅读与 i18n 契约，不另起视觉和信息秩序。

## 3. 页面结构

```text
页面标题：聚焦 / Focus + 页面说明
模块一 待决定事项（全宽主面板，置顶）
推进中事项（全宽主面板，紧随待决定事项）
模块二 近期动态 + 模块四 Spark 健康度（宽容器并列；窄容器单列）
模块三 近期提交热点关系（全宽主面板）
```

- 模块顺序固定，不按数据有无重排；未建设模块不显示占位（§11 分期）。
- 所有模块按真实内容高度收口；热点关系模块不得吸收剩余视口高度，也不得把关系簇或关系簇网格拉成空画布。内容不足一屏时，剩余区域只是不可滚动的页面背景；不得为了填满宽屏而放大节点间距、制造无信息占位或扭曲关系图。
- 待决定事项始终置顶，推进中事项紧随其后；其它模块只按通用容器网格的真实可用宽度自然换列，不维护 Compact 专属排列。
- 模块与待决定事项 Card 使用 `ldvh-section-grid` 容器宽度驱动列数，不以 `lg:` 视口断点作为唯一依据；右侧次级阅读打开时列数随容器收缩。
- 页面不设置"重新读取"控件；进入路由或切换语言触发新的直读请求，不复用旧 payload、对象 `updated_at` 或浏览器渲染时刻冒充新观察。

## 4. 模块规格

### 4.1 模块一 待决定事项（H2 决定依据完备、H3 决定负担有界）

回答 Human 的问题：**现在有哪些事在等我决定？每个决定需要看什么？**

**收录规则（确定性派生，只使用既有字段）：**

| 待决类型 | 派生条件 | 决定依据区直读字段 |
|---|---|---|
| 待批准计划 | WorkCase `progress_group = plan_confirmation` | 与对象列表相同的紧凑 Gate 1 Card：`goal`、成功标准、执行授权边界 |
| 待确认关闭 | WorkCase `progress_group = closure_confirmation` | 与对象列表相同的关闭确认 Card：`goal`、`closure_proposal` 与实际 contributed Pitfall |
| 待确认经验 | Pitfall `status = draft` | 与对象列表相同的 Pitfall Card；完整经验字段在同源次级阅读中展开 |

- 排序：有合法 `priority` 的 WorkCase（P0→P3）→ 无优先级条目（含 Pitfall draft）→ `updated_at` 正序（等待最久在前）。排序是派生展示规则，不表达语义重要性结论。
- 待决类型是 UI 枚举：WorkCase 只由两个 Human Gate 的 `progress_group` 映射；Pitfall 只由类型专属 `draft` 映射为待确认。`status=blocked` 仍在对象列表和详情如实显示，但不是 Human Gate，不进入收件箱。
- 条目形态直接复用对象列表 Card；聚焦页不新增对象正文。点击标题打开右侧扩展阅读（复用同源对象阅读布局）；标题以外区域不触发路由。
- 复制入口只位于模块标题带：“复制模块摘要”面向 AI 对话，含各待确认类型计数与条目稳定 ID。条目本身保持与对象列表 Card 相同的复制与交互，不因进入聚焦页增加按钮；近期动态的当前时间范围由高亮的快捷按钮表达，不重复显示范围说明。
- 决定在 AI 对话中作出，经 Helper 受控写入回写事实源；本模块不承载决定动作。
- 负担有界（H3）：默认完整展示全部待决条目；条目超出首屏时按上述排序截断，并在面板底部如实提示总数与未显示数量，不用分页掩盖待决规模。
- 空态：当前没有待你决定的事项（双语）。

#### 4.1.1 推进中事项（H1 项目认知接续）

回答 Human 的问题：**哪些 WorkCase 正在行动，它们当前推进到哪里？**

- 只收纳由当前 `status + phase` 确定派生为 `progress_group = progressing` 的 WorkCase；它与 `plan_confirmation`、`closure_confirmation` 两个 Human Gate 互斥，不和待决定事项重复。
- `progressing` 包含计划修订、执行项执行、控制器自检、独立复核和控制器综合/关闭准备。`status = blocked` 但仍处于上述推进链的 WorkCase继续保留，并在同源 Card 内显示阻塞说明与等待对象。
- 条目直接复用对象列表的进行中 WorkCase Card：目标、当前推进轨迹和当期执行项均来自 `projectWorkCaseCard` 投影；聚焦页不另写行动摘要，也不新增状态推断。
- 模块使用 `ldvh-section-grid` 随容器宽度自动排成多列，默认展开并支持整块折叠；标题带保留总数和复制模块摘要。
- 点击标题不跳转聚焦页路由，而是在右侧（窄容器时底部）打开同源次级阅读。模块只读，不提供推进、阻塞解除或关闭操作。
- 排序与待决定事项保持同一确定规则：合法优先级 P0→P3、更新时间正序、稳定 ID；超过首屏阈值时如实显示已展示和未展示数量。
- 空态：当前没有推进中的 WorkCase（双语）。

### 4.2 模块二 近期动态（H1 项目认知接续）

回答：**这个明确时间范围内，哪些事实对象有可观察到的新建或更新？**

- 时间窗口只由 Human 显式选择：最近 1 天、最近 3 天、最近 1 周、最近 2 周；默认最近 1 天。窗口以本次 API `generatedAt` 向前计算，不维护 Web 上次访问时间，也不使用“我离开期间”这一抽象概念。
- 内容只包含当前受管项目内五类事实对象的可确定时间标记：`created_at` 落在窗口内标为“新建”，`updated_at` 落在窗口内且不同于 `created_at` 标为“更新”。事实源没有字段级或状态流转事件历史，因此不从更新时间伪造更多动作类型。每行第一行依次呈现相对时间、以低强调颜色区分的行为、弱化的对象 ID、存在时的合法优先级、当前状态与复制对象 ID；第二行呈现类型图标与完整标题。点击标题打开同源次级阅读。
- 本模块不是提交列表，也不把提交消息改写成对象动态。提交及其文件级证据仍只在 `/changes` 与 `/changelog` 阅读；字段级 diff 仍在对象详情与提交记录中核对。
- 如实声明遗漏范围：当前事实源不保存字段变化或状态流转事件历史，因此“更新”只表示 `updated_at` 落入窗口，不推断更新了哪个字段、也不推断状态在何时变化。无有效时间戳的对象不收入该时间标记。
- 切换时间窗口时不触发浏览器整页导航或重载，保留原有页面与动态列表，并在近期动态模块内显示更新状态；`GET /api/cognition` 的新快照成功返回后原位替换当前聚焦页快照。单一类型读取失败时就地显示模块级降级，不影响其它类型的动态。

### 4.3 模块三 近期提交热点关系（H1）

回答：**这个明确时间范围内，哪些事实对象被可回指的提交持续触及，它们通过哪些正式关系相连？**

- 时间范围与模块二完全共用：最近 1 天、最近 3 天、最近 1 周、最近 2 周。切换范围只更新当前聚焦页快照，不把“近期”解释为 Human 离开期间。
- 热点中心至少来自一条当前窗口内、可确定回指的提交。唯一允许的回指规则是：提交修改该对象**当前** canonical fact 文件，或提交 subject/body 显式出现该对象的稳定 ID。路径必须精确相等；ID 必须对应当前受管项目内真实对象。
- 热点首先按可回指提交数、最近提交时间排序；只有两者相同时，非终态 WorkCase 才作为稳定阅读顺序的兜底。每个关系簇的首项就是当前主热点，页面以更大的节点、对象图标和更强的标题层级表达主次，不重复显示“主热点”标签；必须优先呈现它的完整标题与可回指提交数，不能把事实类型、优先级或关系数量误当成热度。
- 每个热点中心展开**入边和出边**各一跳的已声明正式 `relations`，边保留原始 `relation_key`，例如 `related-to`、`routed-to`、`informs`。因此无提交、但与热点有正式关系的对象可以作为周边“相关工作”；有提交的相邻对象标为次级热点，但仍从属于当前主热点的阅读上下文。
- 有可回指提交但没有正式关系的对象不进入本模块，也不为凑图而连线；完整提交仍可在 `/changelog` 阅读。对象多时按现有正式关系拆成小簇；每簇只作确定布局阅读，不表达关系强度、优先级、重要性、方向正确性或执行建议。
- 顶部将提交数、热点/关系计数与图例合并为一条信息带；图例以提交图标说明热点、以对象图标和名称说明事实类型，并以**箭头方向 + 线型 + 颜色 + 本地化名称**共同说明本期每种 `relation_key`，不得只靠颜色区分。连线上不重复渲染文字，避免密集关系中标签重叠。
- 关系簇使用与事实对象一致的容器宽度驱动网格：宽容器可一行多个，窄容器自动回落单列；簇内绘图区直接消费当下可用宽度并在上限内调整节点间距，不维护固定画布宽度，画布顶边紧接簇说明、底边按最后一行节点的实际边界收口。单列时节点应主动使用更多可用宽度；多列时才收敛到适合并排的宽度。标题最多显示两行，完整标题可通过原生标题提示和同源次级阅读继续取得；稳定 ID、优先级和当前状态在仍有空间时完整显示，不得因固定窄节点提前截断。簇内采用“主热点在上、围绕它展开的工作在下”的确定布局，关系树只在自身实际画布内水平居中，不按视口剩余高度作垂直拉伸；各节点内容沿自身高度居中，主热点与相关工作均以左右等宽槽位保证标题和元信息沿卡片中心线对齐。正式关系直接以带方向的圆滑连线表达，不在图下重复一份节点、关系和提交详情。点击任一节点进入同源右侧次级阅读。对象 ID、优先级、当前状态只作为识别辅助信息，优先级不参与热点或布局计算。
- 明确不做全局图、多跳展开、标题/关键词/相近文件匹配、AI 语义连线、重要性评分或隐藏的“方向”判断。提交无法按以上规则回指时不进入图；关系读取失败时模块就地降级，不把缺口表达为无关系。
- 与近期动态的分工：近期动态表达事实对象 `created_at` / `updated_at` 的时间标记；本模块表达提交证据与正式关系。与 `/changelog` 的分工：本模块只给出精确回指入口，不取代完整提交记录、文件差异或提交正文阅读。

### 4.4 模块四 Spark 健康度（H1、H6 提及事项闭环）

回答：**我提过的事有没有被接住？Spark 池是不是在积压？**

**派生指标（全部标注为派生视图；阈值是 Web 展示参数，不是事实）：**

| 指标 | 派生规则 |
|---|---|
| open 总数与优先级分布 | `status = open`，按 `priority` 分组计数（priority 仅 Spark 适用） |
| 静默数 | `open` 且 `updated_at` 距今 ≥ 静默阈值（当前由 Web API 常量 `SPARK_SILENT_THRESHOLD_DAYS = 5` 提供，并通过 `silentThresholdDays` 返回；UI 如实标注） |
| 收敛情况 | 终态（`routed` / `implemented` / `discarded`）数 / 总数 |
| 池的当前拆分 | 当前全部有效 Spark = 终态（`routed` / `implemented` / `discarded`）+ `open`；以一条满宽比例条显示两个数量 |

- 标题带以弱辅助文字显示静默数量与阈值；比例条内仅居中显示终态与待处理数量，条下按两侧居中展示各自的终态/优先级构成。它表达当前结构，不表示告警、成功或处置建议。
- 静默列表按完整静默天数倒序、优先级、更新时间、ID 排序；默认显示前三项，其余由局部展开入口显示。每条列出标题、优先级弱信号、静默天数与复制 ID，点击标题打开右侧扩展阅读。
- 本模块不生成"应当分流到何处"的建议；H6 的承接判断由 Human 在 AI 对话中显式委托（Spark 承接语义见 spark-0037），页面只保证"被提及、未被接住"的事项如实可见。
- 空态：Spark 池当前没有静默积压。

## 5. 全局信任标记（H4 人机理解对齐）

H4 的工作机制：Web 给 Human 看的派生视图，与 AI 经 Helper 精确读取的事实源，必须可互相核查。本页通过以下统一标记实现：

1. 页面不显示“观察时间”。API `generatedAt` 仅用于后端计算近期动态窗口的统一上界，不以对象 `updated_at` 或浏览器时刻替代该计算锚点。
2. 模块级降级：某一数据来源不可用（git 失败、某类型列表读取失败、字段问题）时，对应模块或分区如实显示实际不可用范围与原因，其它模块正常呈现；只有管辖范围解析失败才整页失败。
3. 每个模块标题带提供"复制模块摘要"：面向 AI 对话的多行文本，含模块名、关键计数与条目稳定 ID 列表（不含未精确读取的路径）。Human 粘贴到 AI 对话后，AI 经 Helper 精确读取复核同一对象——页面与 AI 各走 00 §8.3 定义的读取路径，互查而非互替。
4. 事实、派生、诊断、未知范围可区分：直读字段按来源呈现；派生指标带转换说明；近期动态的显式时间窗口、静默阈值等 Web 展示参数如实标注；读取问题与未解析结构在对应消费位置就地显示。

### 5.1 事实变化交付与延迟边界

Helper 成功写入并回读后，浏览器没有可被 Helper 直接调用的写入通知通道；列表、详情、右侧扩展阅读与认知中心不提供应用内重新读取或刷新入口。Human 需要取得新快照时使用浏览器自身的重新加载；页面在路由进入、语言切换等既有读取时机读取各自 API 当前快照，并由 `status` / `phase` 派生 `progress_group`，不写回 YAML、不做乐观迁移。

浏览器重新加载最多表示“下一次成功读取后展示最新可观察快照”，不把文件变化或页面重载表达为 Helper 写入成功。网络、服务、管辖解析或字段读取失败时，保留已存在的成功内容只作视觉占位并在对应页面显示加载失败/模块 issue；不把旧快照标作新观察，也不伪造断连期间的进展变化。页面不在后台或重新可见时自行读取，因此不承诺实时性、自动交付或固定延迟。

## 6. 交互

| 操作 | 行为 |
|---|---|
| 点击待决条目标题 | 打开右侧扩展阅读预览对象（再次点击当前条目关闭） |
| 点击近期动态对象标题 / 静默 Spark 行 / 提交热点对象标题 | 打开右侧扩展阅读 |
| 点击复制模块摘要 | 复制面向 AI 对话的模块观察摘要 |
| 切换语言 | 页面框架、模块标题、待决类型、状态与相对时间同步切换 |

## 7. 实现约束

1. 不把本页做成营销首页、 hero 区或卡片堆叠的装饰页；面向重复阅读与判断，优先信息密度与扫描效率。
2. 不提供批准、关闭、分流、处置、优先级编辑或任何写入口；占位按钮、禁用按钮也不出现。
3. WorkCase 统计只使用 `byProgressGroup`，WorkCase 条目只使用 `progress_group`；不得把派生进展分组放入名为 `status` 或 `byStatus` 的字段。blocked 不进入待决定收件箱，也不得借 `source_status` 重新引入。
4. 不新增事实字段、状态、对象类型、第五进展分组或第二状态模型；待决类型、近期动态时间窗口、静默阈值均为 UI 层派生，如实标注。
5. 收件箱正文直接复用对象列表 Card：计划确认显示 Gate 1 紧凑入口，关闭确认显示关闭判断输入区与后续贡献，Pitfall `draft` 使用其普通 Card。完整同源事实在标题打开的次级阅读中展开；模块摘要只提供当前收件箱的观察信息与对象索引。缺失或类型不符必须在对应消费位置如实降级，不能过滤坏成员后拼成看似完整的批准材料。
6. 近期动态不读取或展示 Git 提交；模块三仅为“近期提交热点关系”读取提交，并且只能由提交修改对象自身的 canonical fact 文件、或提交正文显式出现稳定对象 ID 回指。不得由标题、关键词、相近文件或语义推断映射；完整提交阅读仍进入现有提交页面。
7. 复制语义按 01 §5；候选条目不用 `path`、`target` 或对象 ID 伪造 `canonical_path`；本模块只增加“复制模块摘要”，tooltip 按内容语义命名。
8. i18n 全量双语；事实正文（goal、提案、commit message 等）不翻译；英文长文案允许换行，不以截断替代阅读。
9. 扩展阅读与详情页复用同一身份头部与 `WorkCaseReadingLayout`，不维护第二套对象摘要。
10. 颜色遵守 01 §1.10：Human 待确认紫色系、阻塞/风险警示色、类型色只用于识别；不以单一色相支配页面。
11. 本页确认最前面入口的可见名为“聚焦 / Focus”，内部概念、API 与源码仍使用 Cognition Center；其余入口的名称、顺序与信息架构仍按 01 §1.2.1 保持不写死，本页实现不得反向固定它们。

## 8. API 数据结构

`GET /api/cognition?locale=&window=1d|3d|7d|14d` 聚合返回（类型命名仅为契约描述，实现以 TS 类型为准）：

```typescript
type CognitionObjectType = 'workcase' | 'adr' | 'pitfall' | 'spark' | 'study';
type WorkCaseProgressGroup = 'plan_confirmation' | 'progressing' | 'closure_confirmation' | 'closed';
type InboxKind = 'plan_confirmation' | 'closure_confirmation' | 'pitfall_confirmation';

interface CognitionInboxItemBase {
  id: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  relativeTime: string;
  typeColor: string;
  inboxKind: InboxKind;
  read_status: string;
  card: CognitionInboxCard;                // 与对象列表 Card 同源的内联投影
  priority?: string;
  updatedAt?: string;
  canonical_path?: string;                 // 仅字段级直读成立时出现
  field_issues?: FieldIssue[];
  unparsed_structures?: UnparsedStructure[];
  read_issues?: Record<string, unknown>[];
}

type CognitionInboxItem =
  | (CognitionInboxItemBase & {
      type: 'workcase';
      progress_group: 'plan_confirmation' | 'closure_confirmation';
      inboxKind: 'plan_confirmation' | 'closure_confirmation';
    })
  | (CognitionInboxItemBase & {
      type: 'pitfall';
      status: 'draft';
      inboxKind: 'pitfall_confirmation';
    });

interface CognitionRecentActivityItem {
  id: string;
  type: CognitionObjectType;
  title: string;
  title_en?: string;
  title_zh?: string;
  activity: 'created' | 'updated';
  occurredAt: string;
  relativeTime: string;
  typeColor: string;
  priority?: string;
  progress_group?: WorkCaseProgressGroup;
  status?: string;
  read_status: string;
  field_issues?: FieldIssue[];
  unparsed_structures?: UnparsedStructure[];
}

interface CognitionData {
  generatedAt: string;                     // 近期窗口计算上界，RFC3339（不在页面显示）
  scope: { governedProjectId: string };
  inbox: { items: CognitionInboxItem[]; total: number };
  recentActivity: {
    window: '1d' | '3d' | '7d' | '14d';
    windowStart: string;
    items: CognitionRecentActivityItem[];
    total: number;
  };
  commitHotspots: {
    window: '1d' | '3d' | '7d' | '14d';
    totalCommits: number;
    hotspotTotal: number;
    relationTotal: number;
    clusters: {
      nodes: {
        type: CognitionObjectType;
        id: string;
        title: string;
        title_en?: string;
        title_zh?: string;
        progress_group?: WorkCaseProgressGroup;
        status?: string;
        priority?: string;
        read_status: string;
        typeColor: string;
        commitRefs: {
          hash: string;
          shortHash: string;
          date: string;
          relativeTime: string;
          mapping: 'canonical_path' | 'explicit_id' | 'both';
        }[];
      }[];
      edges: { source: string; target: string; relationKey: string }[];
    }[];
  };
  sparkHealth?: {
    openTotal: number;
    terminalTotal: number;
    terminalByStatus: { routed: number; implemented: number; discarded: number };
    openByPriority: Record<string, number>;
    silentThresholdDays: number;           // 展示参数
    silentCount: number;
    total: number;
    silentItems: {
      type: 'spark'; id: string; title: string; title_en?: string; title_zh?: string; priority?: string;
      updatedAt: string; silentDays: number; typeColor: string; read_status: string;
      field_issues?: FieldIssue[]; unparsed_structures?: UnparsedStructure[];
    }[];
  };
  issues?: { section: string; code: string; message: string; object_ref?: string }[];
}
```

- WorkCase 聚合遵守 §7 第 3 条命名纪律；其它类型不使用 `progress_group` / `byProgressGroup`。
- 待决定条目首屏内联复用各自对象列表 Card 的投影；完整事实在点击标题后的同源次级阅读中展开。模块摘要只保留当前收件箱的观察信息与对象索引，不另造事实或写回摘要。
- 本端点是派生视图服务，不成为事实权威；读取限定在当前唯一管辖项目与实际 worktree。
- 已实现注记（2026-07-31）：`GET /api/cognition` 返回 `{ generatedAt, scope, inbox, recentActivity, sparkHealth, commitHotspots, issues }`。inbox 收录 plan_confirmation / closure_confirmation WorkCase 与 draft Pitfall，按 `priority → updated_at` 正序排序；近期动态读取五类对象，按 `occurredAt` 倒序返回窗口内的创建或更新标记；Spark 健康从当前 Spark 的 `status`、`priority` 和 `updated_at` 派生终态/待处理比例、静默计数与静默列表；近期提交热点关系复用同一时间窗口，只展示经 canonical fact path 或稳定对象 ID 精确回指且至少具有一条正式关系的热点；关系簇以提交数与最近提交确定主热点，并以有向曲线直接连接围绕它展开的工作；无正式关系的提交对象留在 Changelog，节点打开同源次级阅读；blocked 保留在对象列表/详情，不进入 inbox。原规划中的演进时间线与方向对照不再提供字段或页面占位。

## 9. 响应式与移动端

本页不维护移动端专属业务结构。所有宽度使用同一标题、间距和信息层级；待决定事项与关系簇继续使用通用 `auto-fit` 容器网格，近期动态与 Spark 健康继续使用同一 `22rem` 最小面板网格，由真实可用宽度自然决定列数。窄屏只继承 App Shell 的两项结构变化：左侧导航自动成为图标栏，次级阅读切换为底部抽屉；抽屉内为拖动和触摸保留的控制尺寸属于该壳层变化，不得扩散为页面或业务组件的 Compact 变体。

## 10. 验收标准

1. Human 打开 `/` 后第一屏看到两个 WorkCase Human Gate 类型与 draft Pitfall 形成的全部待决定事项；blocked 对象不混入该收件箱。每项复用自身 Card，标题可直接打开同源次级阅读。
2. 完成一次真实闭环：收件箱模块摘要或对象稳定 ID → 粘贴到 AI 对话 → AI 经 Helper 精确读取同一对象 → Human 作出决定 → 受控写入回写事实源 → 重新进入本页后收件箱反映新状态。
3. 每个模块可见派生身份；某类型读取失败时模块级降级并如实标注，不整页失败。近期动态切换窗口时保留旧列表，成功返回后原位替换。
4. 双语切换：无 raw status / raw enum / raw 字段名；事实正文不翻译；英文布局不溢出。
5. 测试按 08 §10 对应行执行：派生内容（来源、转换、过期可复核）、来源与判断边界呈现、Web 行为保持与变更（本表 §0 决定 + 范围匹配的 API/组件/代表性浏览器测试）。
6. i18n、复制语义、扩展阅读同源、字段级解析与未解析结构呈现遵守 01 全部硬约束。

## 11. 已完成分期与维护边界

| 期 | 模块 | 服务标准 | 说明 |
|---|---|---|---|
| 第一期 | 模块一 待决定事项 + §5 全局信任标记 | H2 / H3 / H4 | 直接对准"决定慢、依据散"的真实痛点；含 API、页面、复制摘要与模块级降级 |
| 第二期 | 模块二 近期动态 + 模块四 Spark 健康度 | H1 / H6 | 近期对象变化的接续认知与“提过的事有没有被接住” |
| 第三期 | 模块三 近期提交热点关系 | H1 | 在当前时间范围内，用可回指提交与正式关系形成小簇阅读 |

- 三期均已完成并可按 §10 独立回归；后续维护不得恢复占位空壳、"即将上线"文案或已取消的旧模块。
- 第一期实现时同步完成：路由与导航替换（`CognitionCenter.tsx`、`nav.cognition`、图标按 09 语义规范选定）、`GET /api/cognition` 取代 `GET /api/dashboard`、`dashboard.*` i18n key 清理、本文文件名与测试契约引用更名、原 Dashboard 资产已移除。原 Dashboard 的对象统计网格不再保留为首页模块；对象类型导航由左侧主导航承担。
- 第二期已完成模块二「近期动态」与模块四「Spark 健康度」：近期动态按 Human 显式时间范围显示对象新建/更新，不显示“我离开期间”或提交流；Spark 健康度展示当前池的收敛/待处理比例与静默待处理对象。
- 第三期已完成模块三「近期提交热点关系」：不使用全局图、多跳展开、语义自动连线或重要性评分；每个关系簇以最活跃对象为主热点，只保留热点及其一跳正式 relation，并把周边节点表述为围绕热点展开的工作；无正式关系的提交对象不进入本模块。
