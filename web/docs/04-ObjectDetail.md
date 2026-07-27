# ObjectDetail 对象详情

> 路由：`/objects/:type/:id`
> 源码：`web/src/pages/ObjectDetail.tsx`
> 字段格式规则：`web/src/utils/fieldFormats.ts`

> 字段级读取边界：详情、对象预览、来源路径复制和正文入口先读取当前正式载体。`canonical_path`、`carrier` 和 `check_status` 来自该读取；候选列表、路由 `target` 和 object ID 不能代替它。可解析字段正常呈现，缺失或类型不符字段保留为空态，额外、旧或无法归类结构进入“未解析结构”；不读取 V2/V3 文件、旧 DTO 或兼容路径。
> API：`GET /api/objects/:type/:id`
> 全局设计语言：`web/docs/01-全局设计约束.md` §1.10
> 图标规范：[`09-图标语义规范.md`](./09-图标语义规范.md)

## 1. 页面目标

对象详情页是事实对象阅读器，不是载体文件查看器。页面按字段语义展示对象目标、边界、当前状态、结果、验证说明和关系；YAML 载体可以提供折叠的“YAML 数据”，其内容由精确读取后的事实对象字段重建并剥离读取 envelope，不是原始载体源码或字节级兜底。Markdown Study 的完整阅读只进入同一份正文的扩展阅读，不在主页面重建或伪装为 YAML。

## 2. 当前页面结构

```text
返回按钮
统一对象身份头部：类型标签 + 状态标签 + ID + 优先级字符徽标 + 标题 + 创建/更新时间 + 复制对象路径图标
内容区：
  WorkCase：目标与边界 + 当前快照 + 成功标准 + 工作项 + 当前复核、处置与 Human 批准 + 验证与关闭 + 关系
  ADR：问题 / 决策 / 范围 / 理由 / 影响 / 处置（终态时）/ 关联（存在时）
  Pitfall：现象 / 触发 / 范围 / 验证 / 根因 / 方案 / 规避 / 处置（终态时）/ 关联（存在时）
  Study：研究意图 / 摘要 / 建议摘要 / 正文进入扩展阅读 / 处置（终态且存在时）/ 关联
  Spark：意图 / 摘要 / 演变 / 分流、落实或废弃（终态时）/ 关联（存在时）
  其他对象：字段卡片布局
YAML 数据折叠区：由精确读取后的事实对象字段重建（Markdown Study 不显示第二份 YAML 正文）
右侧扩展阅读区（App Shell 提供，不属于本页卡片）
```

## 3. 头部与元信息

- 返回按钮优先回到进入详情页前的来源界面（`location.state.from`），用于支持从 WorkCase 卡片进入 WorkCase 等跨对象类型跳转；直接打开详情页且没有来源时，兜底回到 `/objects/{type}` 并保留当前 query。返回目标是对象列表页时，右侧扩展阅读区必须主动关闭，避免把详情页上下文残留到主选择面。
- 详情页不展示对象列表的状态筛选；状态筛选只属于列表页，详情页第一视觉层应是当前对象。
- 对象详情头部身份区必须固定在主滚动容器顶部，确保返回、复制对象路径、状态/身份和对象标题在长正文滚动后仍可见；正文内容在该头部下方独立滚动。
- 所有对象详情页必须使用同一套对象身份头部，不得按 WorkCase 和 ADR/Spark/Study/Pitfall 分维护两套头部。
- 头部第一行统一为 `类型标签 + 当前状态标签 + object-id`；类型标签和状态标签使用相同尺寸、圆角和文本权重，但颜色分别来自对象类型色和状态语义色。
- 类型标签使用对象类型颜色，显示本地化类型名；状态标签显示本地化状态名，不放在右上操作区。
- 标题优先使用 `title_zh/title_en`，回退 `title`，再回退 ID；工作对象和普通对象标题前均使用 `ObjectTypeIcon(obj.type)` 识别对象身份。
- WorkCase 和 Spark 如存在 `priority`，在标题行最前面展示 `P0` / `P1` / `P2` / `P3` 字符徽标，随后才是 `ObjectTypeIcon(obj.type)` 和标题；徽标使用颜色和 tooltip 表达优先级，不在头部、元信息行、正文模块或其他字段区重复展示 priority 文字 chip / 字段。
- ID 使用 `ldvh-meta`，不做大号标题；右上角只提供 `CopyPathButton`，tooltip 为“复制对象路径”。所有当前类型都须由字段级精确读取返回 `check_status: readable` 和 `canonical_path` 后才显示；复制值必须等于该路径。不得使用 `data.path`、对象 ID 或路由 `target` 猜测路径，也不得再放状态标签或其他对象身份信息。
- 如对象存在 `tags`，标签应在标题下方独立成行，并位于创建/更新时间之上；标签不与时间或其他辅助属性挤在同一行。Pitfall `tags` 展示事实源英文原值，不做中文翻译。
- 创建/更新时间在标签行下方以短标签展示，统一使用 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`；必要辅助属性可在同一元信息行弱化展示，不另起 MetaChip 行。
- 对象字段必须以对应事实模型主规范为准；只有该对象字段契约内定义的辅助属性才可在元信息行降权展示，不进入主阅读流。`priority` 只适用于 WorkCase 和 Spark，且在详情头部以字符徽标展示；importance 已由 priority 统一承载，不再作为独立字段。
- 右侧扩展阅读区中的对象头部应复用同一套身份头部的小号版本，字段顺序、类型/状态标签规则、复制入口和时间展示不得另起一套。

## 4. WorkCase 状态无关阅读契约

WorkCase 详情页用于完整理解同一项当前工作责任，不复刻外部 Card。`plan_confirmation / progressing / closure_confirmation / closed` 只服务列表和 Dashboard 的注意力分配；详情页不得根据这些进展分组或推进环节切换、隐藏、重排字段，也不得为不同状态维护四套阅读结构。`human_plan_confirming`、`plan_revising`、`executing`、`controller_checking`、`independent_reviewing`、`closure_preparing`、`human_closure_confirming` 与 `closed` 全部复用同一阅读顺序。当前契约允许省略的字段不存在时不渲染相应节点；机械必填字段缺失时对象应在 API 读取边界进入 `invalid`，详情页不补“未完成”或“缺少记录”占位。

详情页只以 21 当前 WorkCase 字段为事实契约。读取顺序围绕以下八个问题组织；分区名称、折叠粒度和具体组件仍可在后续 Human 讨论后细化，但任何视觉方案都不得丢失这些内容：

1. **这项工作是什么**：身份头部读取 `object_id`、`fact_type_key`、`title`、`status`、`priority`（活动期存在时）、`created_at` 与 `updated_at`。
2. **目标和边界是什么**：完整读取 `goal` 与 `scope`，不把 Card 摘要或标题改写成目标，不把范围压成覆盖/排除标签后丢失原文。
3. **现在实际处在哪里**：读取精确 `phase`、当前 `summary`，以及实际存在的 `waiting_on`、顶层 `blocking_summary` 和 `resume_from`。这些字段共同形成当前快照；页面不得从 phase 自动补写等待、阻塞或下一步。
4. **按什么判断结果**：读取 `success_criterion_definitions`；结果已经形成时，同屏读取与当前定义逐项对应的 `success_criterion_results`。定义和结果必须能按 `criterion_id` 对照，不能用完成比例替代陈述与当前结论。
5. **当前计划和阶段结果是什么**：完整读取 `work_items`。每项至少保留 `item_id`、`goal`、`expected_result`、`status`，并按实际存在呈现依赖、方法边界、模板偏离、`current_summary`、item `resume_from`、item `blocking_summary` 与 `result_summary`。工作项以无序圆点显示为并列集合；渲染顺序和 `item_id` 都不表示线性执行顺序。
6. **当前复核、处置与批准是什么**：活动期读取 `plan_version`、当前 `creation_reviews`、`execution_approval`，以及已经形成时的 `result_version`、`controller_check_summary` 和当前 `result_reviews`。详情必须把 Reviewer 的复核、Controller 处置与 Human 执行批准分别呈现，不能把其中任一项改写成另一方的决定；关闭决定由专属事务消费，不作为 approval 收据保存在对象中。
7. **验证和关闭如何判断**：活动期读取实际存在的 `validation_summary` 与 `closure_proposal`；终态读取 `validation_summary`、`closure_outcome`、`disposition_summary` 与 `residual_responsibilities`。关闭内容说明当前工作在自身身份下如何停止推进以及仍适用责任的去向，不等于成功、已提交或下游已经完成；closed 不具有 phase、关闭 approval 或关闭时间字段。
8. **还应回到哪些来源或承接对象**：读取 `urls` 与 `relations`。关系按其正式 kind 和目标身份展示；导航标题、路径解析或 Git 提交可以帮助继续阅读，但不得被写成新的 WorkCase 关系事实。

上述顺序是状态无关的信息架构，不要求所有阶段都出现同样多的内容。条件字段不存在时，Web 不制造空复核、空处置、空批准、空结果或空关闭模块；字段存在时，又不能因为当前 Card 分组“不需要”就把它隐藏。详情不读取列表的工作项计数、active 项、进展分组或推进环节，也不生成标准完成比例；这些 Card 派生值不能替代原始目标、标准、工作项、复核、处置、批准或验证说明。

当前 `WorkCaseReadingLayout` 已直接按 21 单一当前字段族实现以下固定节点顺序：目标与边界 → 当前情况 → 成功标准 → 当前计划与工作项 → 独立方案复核 → 执行批准 → 结果与验证 → 主控自检 → 独立结果复核 → 关闭提案 → 终态处置 → 正式关系 → 外部网址。节点只按对应字段实际存在显示。成功标准定义与三值结果按 `criterion_id` 对照；Reviewer、Controller、Human 执行批准、Controller 关闭提案和终态处置保持独立节点；关系显示正式 `relation_key`。详情与右侧扩展阅读复用同一组件和同一投影，不存在历史字段、列表回退或状态分支。

## 5. 非工作主线对象字段布局

当前已进入五个基准模块的非工作主线对象专用阅读方案为：

1. Pitfall / 踩坑经验：作为“可复用经验阅读页”展示；
2. ADR / 决策：作为“当前决策阅读页”展示；
3. Study / 外部内容调研：作为“外部调研报告阅读界面”展示。摘要层依次读取研究意图、摘要、建议摘要；研究问题留在唯一 Markdown 报告，完整正文和外部资料按需展开；
4. Spark / 火花：作为“待分流信息阅读页”展示。

上述四类方案作为后续非工作主线对象页面设计的参照，不再回退到普通字段卡片堆叠。提交详情不是工作对象详情，但它是五个基准模块之一，已经进入同一阅读语言族：标准身份头部、指标区、圆点正文节点和右侧扩展阅读都必须与这四类详情保持一致。

四类对象的固定节点与字段映射如下；字段不存在时不渲染空节点，关联不存在时不渲染“关联”。所有节点默认展开、标题整行可点击，详情与右侧扩展阅读复用同一布局。

| 对象 | 阅读顺序 | 终态呈现 | 不得回退为 |
|---|---|---|---|
| ADR | 问题 `decision_question` → 决策 `decision` → 范围 `applicability` → 理由 `rationale` → 影响 `consequences` → 关联 | `retired` 时在“影响”后显示处置 `disposition_summary` | “背景”“选择”“备选”“承接”或旧生命周期节点 |
| Pitfall | 现象 `symptoms` → 触发 `trigger_conditions` → 范围 `applicability` → 验证 `validation_summary` → 根因 `root_cause` → 方案 `resolution` → 规避 `avoidance` → 关联 | `retired` 时在“规避”后显示处置 `disposition_summary` | 把没有日志等观察写成已经证明的运行时机制，或把经验做成缺陷状态卡 |
| Study | 研究意图 `research_intent` → 摘要 `abstract` → 建议 `recommendation_summary` → 正文入口 `report_body` → 关联 | 终态存在 `disposition_summary` 时按同一阅读顺序作为补充说明显示 | 在主详情重组第二份 Markdown 正文，或用摘要替代报告原文 |
| Spark | 意图 `intent` → 摘要 `summary` → 演变 `evolution` → 关联 | `routed` 显示“分流”、`implemented` 显示“落实”、`discarded` 显示“废弃”；三者内容均只读 `disposition_summary` 与 `updated_at` | 用旧 `source_detail`、`description`、`resolved_to`、`resolved_at`、`discard_reason` 字段，或在 `open` 状态制造终态占位 |

- ADR 状态只显示 `active / retired`；Pitfall 状态只显示 `active / retired`。两者的 retired 处置只说明对象不再作为当前入口的原因与去向，不生成额外的“退出理由”标签或退出时间。
- Spark 的 `evolution` 以最近条目优先的短卡片呈现，每项只显示事实中的 `at` 和 `summary`。Spark 终态只说明该信息对象的处置类别与事实正文；不能由终态处置推导目标对象已经完成。
- Study 正文入口仅在精确读取是 Markdown carrier 时可打开；`research_question` 留在该正文内部。外部资料和正式关系进入同一“关联”阅读区，不被解释为研究结论或规则。
- Pitfall 的验证、根因、方案和规避必须保留正文中的已确认、未确认与不适用边界；Markdown 列表按正常条目阅读，不用状态徽标替代原意。
- 未定义专用语义布局的对象使用普通字段卡片兜底；每个字段一个轻量卡片，字段标题用 `ldvh-caption-strong`。
- 普通字段卡片中的关联类字段可折叠；默认折叠长关联集合，避免压过主阅读路径。
- Pitfall、ADR、Spark、WorkCase 等长文本字段必须按 Markdown 渲染。
- WorkCase 已使用专用语义布局，不进入普通字段卡片路径。

## 6. 字段渲染规则

字段分类由 `web/src/utils/fieldFormats.ts` 统一维护，详情页和右侧扩展阅读区必须共同消费同一套规则。字段分类只决定 Web 如何阅读和渲染字段，不定义字段是否存在、是否必填或适用于哪些对象；字段契约以 `specs/20-29` 对应事实模型主文件为准；公共字段语义以 `specs/05.01-字段定义与语义规范.md` 为准；内容格式以 `specs/05.02-字段内容与格式规范.md` 为准；字段注册与消费语义以 `specs/05.03-字段注册与消费规范.md` 为准。

同名字段在不同工作对象详情页中必须使用同一套标题、组件和基础视觉权重。例如 `scope` 统一表达对象适用边界，`urls` 统一表达外部网址，`relations` 统一表达正式对象关系。对象层级差异只允许体现在字段顺序、是否出现对象特有字段和阅读问题上，不允许同名字段在 WorkCase 与其他工作对象中换标题、降权或改变语义。

详情页专用阅读布局已经由 `DetailSection` 提供外层卡片边界；WorkCase 的 `validation_summary` 与其它对象已登记的验证说明在模块内使用 embedded Markdown 渲染，不再额外套一层强提示边框。Web 必须忠实保留事实正文中的验证覆盖、实际结果和未验证范围，不得把自然语言说明自动改写成通过证明或结构化证据包。

| 字段类型 | 渲染组件 | 当前行为 |
|---|---|---|
| 叙述说明 / 决策 / 过程记录 | `SummaryText` | Markdown 渲染，长内容按段落摘要/展开 |
| 检查清单 | `ChecklistCard` | 进度条 + 勾选/未勾选图标 + inline Markdown |
| 兼容检查清单字段 | `ChecklistCard` 或 `SummaryText` | 只有内容包含 `- [ ]` / `- [x]` 时才按检查清单渲染 |
| 验证说明 | `EvidenceBlock` 或对象专用正文节点 | Markdown 渲染；只按来源已有结构突出命令、路径、实际结果与未验证范围，不补造结论 |
| 对象 ID 引用 | `ReferenceCard` | 点击在右侧扩展阅读区取得精确读取并打开对象；只有精确读取返回可消费 `canonical_path` 时提供复制对象路径图标 |
| 文档路径 / URL | `DocPreviewLink` | 本地 Markdown 文档和外部 URL 均优先在右侧扩展阅读区预览；复制 tooltip 分别为“复制文档路径”和“复制链接”；外部 URL 在扩展阅读区提供新标签备用入口 |
| 路径文本 | `PathText` | 等宽、可换行的路径标签 |
| 其他短文本 | `ldvh-body` | 普通文本 |

对象引用只可打开已经实际接入的 V4 原生读取器；Study 已读取当前 V4 原生载体，且不得回退到历史兼容页面、旧字段或第二份正文结构。

当前事实对象不使用按目标类型拆分的 `related_*` 或本地路径引用字段。`urls` 只承载带标题和用途摘要的外部 `http(s)` 网址；`relations` 只承载关系语义和稳定对象目标，不复制目标标题、状态或内容。对象规范路径属于 machine 精确读取元数据，只能在读取成功后提供复制入口，不能写入事实正文或由对象 ID 推测。

带章节后缀的本地 Markdown 引用应区分展示文本与加载路径：列表行保留完整引用文本，例如 `specs/07-Code确定性执行实现规范.md §4.7`；点击整行或扩展阅读图标时，只用规范化后的 Markdown 文件路径加载右侧阅读区，例如 `specs/07-Code确定性执行实现规范.md`，不得把章节后缀拼入文件读取 API。

V4 Study 阅读器读取当前 Study 的 `research_intent`、`research_question`、`abstract`、`recommendation_summary`、Markdown 正文与 `urls`。首级详情与对象预览按“研究意图 → 摘要 → 建议 → 正文入口 → 关联”组织；`research_question` 留在报告“研究问题”段，正文只通过同一精确读取的 Markdown carrier 进入扩展阅读。终态对象若实际带有 `disposition_summary`，在正文入口之后如实显示该补充说明；不得读取或投影旧版兼容 DTO。

关联区块内的可读工作对象引用显示对象类型图标、已解析标题、稳定对象编号与当前状态；对象编号帮助 Human 回指事实，不能替代标题或被表现为对象名称。尚未解析或跨项目引用只如实显示已知稳定身份，不猜测标题、状态或来源路径。

关联区块内每个具体条目必须使用统一行结构：左侧为语义图标和标题/路径/网址文本，右侧提供扩展阅读入口；对象引用只有在该行完成精确读取并获得可消费 `canonical_path` 时才增加复制入口。整行必须可点击并触发扩展阅读；复制入口只执行复制，不触发扩展阅读。对象引用、文档路径和外部 URL 不得各自使用不同的卡片、文字按钮或标签样式。行内语义图标、标题文本、复制入口和扩展阅读入口必须垂直居中；复制和扩展阅读入口使用同一 28px 操作容器，长标题截断或出现摘要次行时也不得让右侧操作图标下坠或上浮。

V4 Study 阅读器从 `urls` 展示外部资料，并显示资料自身的标题和用途摘要。界面不得把 URL 转换为规则，或把内部路径呈现为外部研究对象。

V4 Study 详情页不按普通字段卡片表达主内容。报告正文节点只是同一文件的进入行：仅在精确读取的 `carrier: markdown` 和 `canonical_path` 可用时，才可在右侧扩展阅读区打开完整正文；正文保留其原有 H2、H3、表格、链接和段落，主页面不按 H2 拆开、复制或重组。`research_question` 仅在正文“研究问题”中展开，同时可保留给机器候选消费，但不属于详情摘要层。资料只可来自同一 V4 原生 Study 文件，不提供 V2/V3 兼容字段或双读。

Spark 不使用普通字段卡片堆叠。Spark 是“待分流信息对象”，页面目标是说明当前信息如何继续被理解或已经如何处置，而不是证明结论、沉淀经验或呈现报告。意图读取 `intent`，摘要读取 `summary`，演变读取 `evolution` 并以倒序的 `at + summary` 短卡片显示。`open` 不显示终态节点；`routed`、`implemented`、`discarded` 分别显示“分流”“落实”“废弃”，都只读取 `disposition_summary` 和对象 `updated_at`。Web 只读展示，不提供状态修改、分流或废弃按钮，也不从终态处置推断被关联对象的完成状态。

Spark 节点标题栏应与 ADR / Pitfall / Study 保持一致：整行可点击，默认全部打开，折叠图标使用 `ChevronDown` / `ChevronUp`。详情页和右侧扩展阅读区必须复用同一套 Spark 阅读布局。

Pitfall、ADR、Study 和 Spark 等非工作主线对象的长文本阅读组织应向固定主节点思路靠拢：优先依据 05.01 字段语义和 05.02 内容格式形成稳定阅读节点，而不是把 YAML 字段原样散成难以扫描的卡片。`verification` 等证据字段的节点顺序由 05.02 定义；具体对象页面只决定这些节点在对象详情中的位置和折叠行为。已定义专用阅读布局的对象必须在详情页和右侧扩展阅读区共用同一套节点、顺序、折叠行为和关联渲染。

## 7. 右侧扩展阅读区

- 由 App Shell 的 `ReadingPanel` 提供。
- 触发来源：对象引用、文档引用、Dashboard / 提交记录页的对象条目。
- 顶部只保留上一个访问对象、下一个访问对象和关闭按钮。
- 扩展阅读区顶部控制区必须固定在面板顶部，正文在面板内部独立滚动，避免长文档或对象详情滚动后无法切换历史对象或关闭面板。
- 不展示对象列表式导航。
- 同一对象或文档入口再次点击关闭扩展阅读区；点击不同入口才切换右侧预览内容。
- 对象预览不是“摘要卡片”，而是对象详情页阅读内容的右侧视口；同一个对象在详情页和扩展阅读区必须使用同一套字段顺序、字段标签、字段过滤和字段渲染。
- WorkCase、Pitfall、ADR、Study 和 Spark 必须复用详情页导出的专用阅读布局。
- WorkCase、Pitfall、ADR、Study 和 Spark 的扩展阅读头部复用详情页身份区，清楚展示 `类型 + 类型状态词 + ID + 标题 + 创建/更新时间`；读取失败时不显示领域状态，而显示实际读取状态与未读取范围。
- Spark 必须复用详情页专用 Spark 阅读布局，不得在 `ReadingPanel` 中维护另一套 `PREVIEW_FIELD_ORDER`、字段 label map、关联分组或独立字段渲染器。
- 对象预览头部只在该类型的字段级精确读取返回 `check_status: readable` 与 `canonical_path` 时提供复制对象路径图标；所有当前类型使用同一可消费状态。`target` 仅用于导航，绝不作为路径回退。
- Markdown 文档预览使用 `MarkdownPreview` + `github-markdown-css`，不是手写 Markdown 标签样式。
- Markdown 正文基准字号为 14px；表格横向滚动，代码块、引用块、任务列表由全局 Markdown 样式统一控制。

## 8. YAML 数据

- 只对声明 `carrier: yaml` 的精确可读对象显示，默认折叠；Markdown Study 不显示由字段重组出的 YAML 版本。
- 显示内容是 Web 对当前事实对象字段的 YAML 重组，不是事实载体的原始 bytes 或源码；重组前必须剥离 machine envelope、`object_ref`、路径、载体、读取状态、指纹、观察时间和问题等读取元数据。
- 展开后使用 `react-syntax-highlighter` + YAML + oneDark。
- 显示行号，最大高度 400px。
- 折叠图标与详情页主节点保持一致：收拢状态使用 `ChevronDown`，表示可以向下打开；打开状态使用 `ChevronUp`，表示可以向上收起。
- YAML 数据只帮助核对当前事实对象字段，不证明原始载体内容或事实完整性，也不作为主阅读体验。

## 9. 实现约束

1. 不把关联对象显示成只有 ID 的标签；对象引用必须可点击并能在扩展区查看详情。
2. 不把 Markdown 字段当纯文本展示。
3. 不把文档产出只显示路径；本地 Markdown 文档必须可在扩展区预览。
4. 不把辅助属性提升为主阅读流大字段。
5. 不恢复右侧“关联对象列表导航”；右侧只做访问历史前进/后退。
6. 不把详情页内关联对象入口做成重复点击仍保持打开；重复点击当前入口必须收起扩展阅读。
7. 不在业务组件里新增另一套字段格式判断；新增字段先更新 `fieldFormats.ts`，并按性质同步 05.01 字段语义、05.02 内容格式或 05.03 注册消费规则。
8. 详情头部、对象引用卡片和扩展区对象预览只在各自完成精确读取且有 `canonical_path` 时保留复制对象路径入口；候选列表不承诺或复制源路径。
9. 不把扩展阅读对象内容实现成详情页之外的第二套摘要；右侧对象内容必须从详情页阅读布局或详情页字段组件派生。
10. 项目画像类入口不属于当前 LDVH 工作对象、管辖配置或 Web 对象路由；ObjectDetail 不维护此类字段顺序、字段标签、详情路由、引用卡片或扩展阅读支持。

## 10. API 数据结构

```typescript
interface ObjectDetail {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status?: string; check_status?: 'readable' | 'unreadable' };
  data: Record<string, unknown>;
}
```

精确可读详情的 `data` 同时带回 `canonical_path`、`carrier`、`check_status`、`field_issues` 与 `unparsed_structures`；这些结果不构成机械校验结论。读取失败返回 `fact_read_failure: true`、预期路径、声明载体、读取状态和问题，但不返回可消费正文或领域状态。WorkCase 的 `summary.status` 只返回 `open / blocked / closed` 责任状态；列表/仪表盘是候选发现，不能以其 `path`、ID 或 `target` 作为源路径。

WorkCase 详情契约直接读取精确返回的 `data` 中由 21 定义的当前字段；列表 API 的 `progress_group`、`progress_step`、计数和 active 项不驱动详情结构。缺失或类型不符的页面消费字段按字段问题呈现为空；旧字段、额外字段和无法归类嵌套结构进入未解析结构，既不构成 `invalid`，也不阻断其它字段。Web 不在 Node 复制 21、Schema 或 phase presence 形成第二机械契约。

当前 WorkCase 与其它当前类型统一经过 `localFactReader` 的字段级直读。Web 只调用 Helper 的 `resolve-governance-scope` 确认管辖范围，随后直接读取已确认 worktree 中的正式载体；不启动 Python machine、不做完整机械校验、不扫描关系稳定化链路。身份不一致、字段缺失和字段类型不符均作为字段问题保留，未消费结构进入 `unparsed_structures`；只有载体 I/O 或 YAML/frontmatter 无法解析时才为 `check_status: unreadable`。详情 API 不从列表补字段，也不把字段级可解析表述成校验通过。

该边界的定向验证运行 `cd web && npm run test:web:api && npm run check`，覆盖字段级读取、未解析结构、API 契约与页面消费；不再保留 Web Python 读取编排测试。
