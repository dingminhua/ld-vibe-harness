# ObjectDetail 对象详情

> 路由：`/objects/:type/:id`
> 源码：`web/src/pages/ObjectDetail.tsx`
> 字段格式规则：`web/src/utils/fieldFormats.ts`
> API：`GET /api/objects/:type/:id`
> 全局设计语言：`web/docs/01-全局设计约束.md` §1.10
> 图标规范：[`09-图标语义规范.md`](./09-图标语义规范.md)

## 1. 页面目标

对象详情页是事实对象阅读器，不是 YAML 文件查看器。页面应按字段语义展示对象目标、证据、引用、状态和产出，并把 YAML 源码作为折叠兜底。

## 2. 当前页面结构

```text
返回按钮
统一对象身份头部：类型标签 + 状态标签 + ID + 优先级字符徽标 + 标题 + 创建/更新时间 + 复制对象路径图标
内容区：
  WorkCase：执行态势 + 成功标准 / 验证证据 / 关闭证据 + 检查安排 + 目标 / 所属工作项 / 来源 + 文档 / 决策 / 火花 / 踩坑经验
  ADR：背景 / 决策 / 影响 / 关联
  Pitfall：现象 / 触发 / 根因 / 方案 / 验证 / 规避 / 范围 / 关联
  Study：意图 / 摘要 / 建议 / 正文 / 关联
  Spark：意图 / 摘要 / 演变 / 分流 / 关联
  其他对象：字段卡片布局
YAML 源码折叠区
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
- ID 使用 `ldvh-meta`，不做大号标题；右上角只提供 `CopyPathButton`，tooltip 为“复制对象路径”，复制 API 返回的 `data.path` / 对象 `path`，只有缺失时才使用 `target`，不得再放状态标签或其他对象身份信息。
- 如对象存在 `tags`，标签应在标题下方独立成行，并位于创建/更新时间之上；标签不与时间或其他辅助属性挤在同一行。Pitfall `tags` 展示事实源英文原值，不做中文翻译。
- 创建/更新时间在标签行下方以短标签展示，统一使用 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`；关闭时间或必要辅助属性可在同一元信息行弱化展示，不另起 MetaChip 行。
- 对象字段必须以对应事实模型主规范为准；只有该对象字段契约内定义的辅助属性才可在元信息行降权展示，不进入主阅读流。`priority` 只适用于 WorkCase 和 Spark，且在详情头部以字符徽标展示；importance 已由 priority 统一承载，不再作为独立字段。
- 右侧扩展阅读区中的对象头部应复用同一套身份头部的小号版本，字段顺序、类型/状态标签规则、复制入口和时间展示不得另起一套。

## 4. WorkCase 语义阅读布局

WorkCase 不使用普通字段卡片堆叠，而作为“一次目标的执行态势”展示。WorkCase 的设计语言必须先继承提交、研究、决策、火花、经验五个成熟模块的基线，新的专用表达只能围绕“工作项对象更复杂”来增加，不能另起一套视觉和信息秩序。执行项只作为 WorkCase 内部编排的只读态势呈现，不在本文定义独立字段契约、对象路由或长期事实源结构。

1. 工作项进度：页面主区域第一块，展示 WorkCase 自身推进阶段、成功标准完成度、执行项完成度、执行项状态分布和关闭材料记录状态。推进阶段直接消费当前 WorkCase 状态机：`subagents_plan_reviewing`、`human_plan_confirming`、`executing`、`result_self_checking`、`subagents_result_reviewing`、`human_closure_confirming`、`closed`；历史 `draft`、`active`、`review_needed` 只作为 legacy 兼容显示。该模块只消费确定性只读派生摘要，不写回事实源。
2. 执行态势：展示整体执行态势条，并按 Human 关注顺序展示执行项行：已阻塞、执行中、待执行、已跳过、已完成；区块标题只使用小圆点。
3. 成功标准、验证证据和关闭证据不再收进“关闭判断”总区块；分别作为同级模块展示 `success_criteria/verification_evidence/closure_evidence`。不展示额外顶部结论条，不单列待确认项或记录状态，未完成项由 checklist 或证据模块自身表达。成功标准是关闭判断依据，但不再用外层总模块包住。
4. `orchestration.plan_review` 和 `orchestration.result_review` 作为“检查安排”模块展示方案审核、结果自检、结果复核、主控处理和 Human 确认摘要。Web 只展示已有审核事实和关键摘要，不把审核记录改写成独立 Review 对象；完整事实仍以 WorkCase YAML 为准。历史 `orchestration.review` 仅作为 legacy fallback 展示主控自检、专业复检和 Human 关闭审查要求。
5. 定义事实不再收进“属性”总区块；目标、所属工作项、来源分别作为同级模块展示 `description/workcase/source`。`description` 是目标叙述，必须按 Markdown 正文渲染，不得用定义行拆分、短前缀标签或字段 chip 重排原文。所属工作项入口使用模块内对象引用值，显示 WorkCase 对象图标和工作项标题，不显示 ID 或状态徽章，点击只打开右侧辅助阅读，不切换主路由。
6. 执行项行在 WorkCase 详情中与 WorkCase card 的动作体验保持一致：复用状态色弱背景、左侧状态图标、执行项标题、内部编号、证据入口和辅助阅读入口；执行项不得使用 WorkCase 对象图标或 WorkCase 状态徽章。
7. 关联材料不再收进“关联材料”总区块；文档、决策、火花、踩坑经验按 `related_docs/related_adrs/related_sparks/related_pitfalls` 分别作为同级模块展示。材料来源只聚合 WorkCase 自身和已明确纳入 WorkCase 证据的引用，按 ID 或路径去重；不得从执行项派生出另一套对象级材料事实源。关联提交由 Git 历史、文件路径、对象 ID 和提交正文自然文本派生，不从对象字段手写维护。
8. WorkCase 详情页点击执行项行只打开右侧辅助阅读区，不切换主路由到独立对象详情；主路由跳转只属于对象列表卡片。

## 5. 非工作主线对象字段布局

当前已进入五个基准模块的非工作主线对象专用阅读方案为：

1. Pitfall / 踩坑经验：作为“可复用经验阅读页”展示；
2. ADR / 决策：作为“决策补丁阅读页”展示；
3. Study / 研究报告：作为“报告阅读界面”展示；
4. Spark / 火花：作为“待分流信息阅读页”展示。

上述四类方案作为后续非工作主线对象页面设计的参照，不再回退到普通字段卡片堆叠。提交详情不是工作对象详情，但它是五个基准模块之一，已经进入同一阅读语言族：标准身份头部、指标区、圆点正文节点和右侧扩展阅读都必须与这四类详情保持一致。

- Pitfall 不使用普通字段卡片堆叠，而作为“可复用经验阅读页”展示。主节点固定为“现象、触发、根因、方案、验证、规避、范围、关联”，节点标题栏整行可点击，默认全部打开，折叠图标规则与 Study 一致。
- ADR 不使用普通字段卡片堆叠，而作为“决策补丁阅读页”展示。主节点固定为“背景、决策、影响、关联”，节点标题栏整行可点击，默认全部打开，折叠图标规则与 Study 一致。
- ADR 的“影响”节点消费 `consequences` 字段。active ADR 必须按 `## 正向价值`、`## 逆向价值`、`## 实施成本`、`## 风险评估`、`## 注意事项` 五段式书写；有逆向价值时必须引用 V1-V10，无逆向价值时 `## 逆向价值` 填写 `当前决策无逆向价值`。Web 在节点内按 Markdown 分段展示，不把五段拆成独立工作对象字段。
- ADR 不展示“备选”节点，也不维护 `alternatives` 字段。未采纳方案若来自 Spark，应保留在 Spark 的演变记录或讨论上下文中；若只来自临时对话且未进入决策，不进入 ADR。
- ADR 不展示独立“承接”节点，也不维护 `affects` 字段。`related_rules`、`related_workcases`、`related_workcases`、`related_adrs`、`related_sparks` 等统一进入“关联”，按关联内容的通用行样式展示。关联提交由 Git 派生视图呈现。
- ADR 状态只显示 `active / archived / deprecated`。详情页不得展示或派生 `proposed`、`accepted`、`rejected`、`superseded` 或 `superseded_by` 旧生命周期语义。
- Pitfall `verification` 节点消费 05.02 四段式结构，但在 Pitfall 页面内渲染为轻量分段阅读，不使用表格左列重复“计划/记录/结果/结论”。验证节点内部按“验证计划、验证命令、验证结果、结论”顺序展示。
- Pitfall `root_cause`、`resolution`、`avoidance` 等经验节点应把 Markdown 列表渲染为清晰的条目阅读，而不是使用浏览器默认列表缩进。无序列表只使用灰色圆点；有序列表应保留 Markdown 原文的普通 `1.`、`2.`、`3.` 文本编号，不得额外渲染为徽标、强调色或状态标记。
- 未定义专用语义布局的对象使用普通字段卡片兜底；每个字段一个轻量卡片，字段标题用 `ldvh-caption-strong`。
- 普通字段卡片中的关联类字段可折叠；默认折叠长关联集合，避免压过主阅读路径。
- Pitfall、ADR、Spark、WorkCase 等长文本字段必须按 Markdown 渲染。
- WorkCase 已使用专用语义布局，不进入普通字段卡片路径。

## 6. 字段渲染规则

字段分类由 `web/src/utils/fieldFormats.ts` 统一维护，详情页和右侧扩展阅读区必须共同消费同一套规则。字段分类只决定 Web 如何阅读和渲染字段，不定义字段是否存在、是否必填或适用于哪些对象；字段契约以 `specs/20-29` 对应事实模型主文件为准；公共字段语义以 `specs/05.01-字段定义与语义规范.md` 为准；内容格式以 `specs/05.02-字段内容与格式规范.md` 为准；字段注册与消费语义以 `specs/05.03-字段注册与消费规范.md` 为准。

同名字段在不同工作对象详情页中必须使用同一套标题、组件和基础视觉权重。例：`description` 统一显示为“目标”，`source` 统一显示为普通定义文本，`related_docs` 统一显示为“文档”材料模块。对象层级差异只允许体现在字段顺序、是否聚合派生数据和是否出现对象特有字段上，不允许同名字段在 WorkCase 与其他工作对象中换标题、降权或换交互样式。

详情页专用阅读布局已经由 `DetailSection` 提供外层卡片边界；`verification`、`verification_evidence`、`closure_evidence` 等证据字段在这些模块内必须使用 embedded 证据渲染，不再额外套一层证据色边框。证据色边框只用于没有外层详情模块的独立证据块。证据字段应消费 `specs/05.02-字段内容与格式规范.md` §3.3 的四段式结构：`验证计划 / 验证命令 / 验证结果 / 结论`；Web 可以兼容存量旧格式，但不得鼓励或新增无结构验证段落。

| 字段类型 | 渲染组件 | 当前行为 |
|---|---|---|
| 叙述说明 / 决策 / 过程记录 | `SummaryText` | Markdown 渲染，长内容按段落摘要/展开 |
| 检查清单 | `ChecklistCard` | 进度条 + 勾选/未勾选图标 + inline Markdown |
| 兼容检查清单字段 | `ChecklistCard` 或 `SummaryText` | 只有内容包含 `- [ ]` / `- [x]` 时才按检查清单渲染 |
| 验证证据 | `EvidenceBlock` | Markdown 渲染，命令、路径和代码突出显示；按 05.02 四段式二级标题派生为分段证据视图 |
| 对象 ID 引用 | `ReferenceCard` | 点击在右侧扩展阅读区打开对象；卡片内提供复制对象路径图标 |
| 文档路径 / URL | `DocPreviewLink` | 本地 Markdown 文档和外部 URL 均优先在右侧扩展阅读区预览；复制 tooltip 分别为“复制文档路径”和“复制链接”；外部 URL 在扩展阅读区提供新标签备用入口 |
| 路径文本 | `PathText` | 等宽、可换行的路径标签 |
| 其他短文本 | `ldvh-body` | 普通文本 |

当前可点击对象引用仅覆盖 Web 支持的工作对象类型：WorkCase、ADR、Pitfall、Spark、Study。未进入当前对象路由的引用只作为普通引用文本展示，不跳转到无效详情页。

路径类字段应按字段语义区分：`related_docs` 指向关联文档，`urls` 只指向报告正文提炼出的外部 `http(s)` 网址及用途摘要，`related_rules` 指向关联规范、Rules、Skill、Agent、Code 或 Web 路径。Web 可预览本地 Markdown 或展示路径，但不得把可预览路径集合解释为所有路径字段的合法范围。

带章节后缀的本地 Markdown 引用应区分展示文本与加载路径：列表行保留完整引用文本，例如 `specs/07-Code确定性执行实现规范.md §4.7`；点击整行或扩展阅读图标时，只用规范化后的 Markdown 文件路径加载右侧阅读区，例如 `specs/07-Code确定性执行实现规范.md`，不得把章节后缀拼入文件读取 API。

所有 `related_*`、`aggregated_related_*` 和 Study `urls` 字段在对象详情中应统一收进上层“关联”区块，不得按字段名散落在正文、证据或其他字段之间。关联区块内部先展示工作对象关联，并按事实模型编号排序：Spark 20、WorkCase 21、ADR 22、Pitfall 23、Study 24；非工作对象关联再按字段英文名排序，例如 `related_docs`、`urls`、`related_rules`。提交记录不是工作对象关联字段，应从 Git 提交记录视图派生。

关联区块内的工作对象引用不直接展示对象编号。对象编号属于打开后的对象详情、复制路径或 YAML 源码中的定位信息；列表态只展示对象类型图标、对象标题和必要操作图标，降低重复元信息对阅读的干扰。

关联区块内每个具体条目必须使用统一行结构：左侧为语义图标和标题/路径/网址文本，右侧固定提供复制入口和扩展阅读入口。整行必须可点击并触发扩展阅读；复制入口只执行复制，不触发扩展阅读。对象引用、文档路径和外部 URL 不得各自使用不同的卡片、文字按钮或标签样式。行内语义图标、标题文本、复制入口和扩展阅读入口必须垂直居中；复制和扩展阅读入口使用同一 28px 操作容器，长标题截断或出现摘要次行时也不得让右侧操作图标下坠或上浮。

`urls` 必须展示在“关联”区块下的“网址”分组。每个条目必须来自结构化网址对象；列表主行显示 `title`，没有 `title` 时显示 `ref`，次行必须显示中文 `summary`，复制和扩展阅读仍作用于 `ref`。Web 不把 URL 摘要派生为事实；摘要必须来自 Study frontmatter 或其他权威事实源。

Study 详情页的 `urls` 分组标题显示为“网址”。字段名保持 `urls`，用于承载报告正文提炼出的外部 URL 及其用途摘要；UI 标题应避免使用“引用”这种过宽泛表达。

Study 详情页是报告阅读界面，不按普通字段卡片表达主内容。中文主节点标题固定为“意图、摘要、建议、正文、关联”，分别对应 `user_intent`、`summary`、`conclusion`、`report_body` 和关联区。`user_intent`、`summary`、`conclusion` 和 `report_body` 必须与“关联”使用同一层级的节点标题样式：标题前使用小圆点，标题字号和权重与关联区标题一致，内容区颜色低于标题。`report_body` 不在主页面直接铺开全文；“正文”节点下只展示当前 Study 文件名入口，点击整行或扩展阅读图标后在右侧扩展阅读区渲染正文 Markdown。结构化 `urls.summary` 是引用用途提示，应比 Study 主内容再弱一级，不承担正文结论表达。

Study 主节点标题栏整行可点击，不再在内容内部放“展开/收起”文字按钮。`user_intent`、`summary`、`conclusion`、`report_body` 和“关联”统一使用两态：默认全部打开，点击标题栏在 `expanded` 与 `collapsed` 之间切换。图标表达当前可执行动作：收拢状态使用 `ChevronDown`，表示可以向下打开；打开状态使用 `ChevronUp`，表示可以向上收起。

Study 必须抽为独立 `StudyReadingLayout` 并同时供详情页和右侧扩展阅读区复用；不得继续依赖 `ContentField` 对 Study 字段做兜底特判。`ContentField` 只处理专用布局之外的额外字段。

Spark 不使用普通字段卡片堆叠。Spark 是“分流前的信息对象”，页面目标不是证明结论、沉淀经验或呈现报告，而是帮助 Human 和 AI 判断这条信息当前应继续 pending、追加演变、分流到目标事实源，还是废弃。Spark 作为“待分流信息阅读页”展示，基础主节点固定为“意图、摘要、演变、关联”；“分流”是闭环事实节点，不是 pending 状态说明节点：

1. “意图”消费 `source_detail`，使用与 Study “意图”一致的主节点样式表达这条 Spark 的来源意图、问题触发或对话背景；不得再以“来源说明”字段卡片或来源子字段表达。
2. “摘要”消费 `description`，展示当前问题焦点、保留价值和阶段性收敛方向；这是 Spark 主阅读节点，不得被压在普通字段卡片中。
3. “演变”消费 `evolution`，按倒序展示关键语义转折；每条展示 `at` 和 `summary`，`at` 拆成日期与时间两行展示，不做聊天流水账样式，不额外创建时间线事实源。
4. “分流”只在 `status` 为 `resolved` / `discarded`，或存在 `resolved_to`、`resolved_at`、`discard_reason` 任一真实闭环事实时渲染；`pending` 且没有上述事实时不得渲染“分流”节点，不得用固定提示文案占位。节点内消费 `status`、`resolved_to`、`resolved_at`、`discard_reason`：`resolved` 显示分流目标引用和分流日期；`discarded` 显示废弃原因。Web 只读展示，不提供状态修改、分流或废弃按钮。
5. `source` 不进入正文节点，必须作为对象头部弱元信息展示在“更新”之后，表达方式与创建/更新元信息一致。
6. “关联”统一收纳 `related_workcases`、`related_workcases`、`related_adrs`、`related_studies` 和 `related_docs`，按关联区通用行样式展示；Spark 当前字段契约没有 `related_sparks` 或 `related_pitfalls`，Web 不得为 Spark 杜撰这两类字段。

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
- WorkCase、Pitfall、ADR、Study 和 Spark 的扩展阅读头部同样不显示状态 chip；右侧面板按详情页身份区顺序展示 `类型 + ID + 标题 + 创建/更新时间 + 复制对象路径入口`，状态由复用的语义阅读布局表达。
- Spark 必须复用详情页专用 Spark 阅读布局，不得在 `ReadingPanel` 中维护另一套 `PREVIEW_FIELD_ORDER`、字段 label map、关联分组或独立字段渲染器。
- 对象预览头部提供复制对象路径图标，复制 API 返回的 `data.path` / 对象 `path`，只有缺失时才使用 `target`。
- Markdown 文档预览使用 `MarkdownPreview` + `github-markdown-css`，不是手写 Markdown 标签样式。
- Markdown 正文基准字号为 14px；表格横向滚动，代码块、引用块、任务列表由全局 Markdown 样式统一控制。

## 8. YAML 源码

- 默认折叠。
- 展开后使用 `react-syntax-highlighter` + YAML + oneDark。
- 显示行号，最大高度 400px。
- 折叠图标与详情页主节点保持一致：收拢状态使用 `ChevronDown`，表示可以向下打开；打开状态使用 `ChevronUp`，表示可以向上收起。
- YAML 源码是事实完整性兜底，不作为主阅读体验。

## 9. 实现约束

1. 不把关联对象显示成只有 ID 的标签；对象引用必须可点击并能在扩展区查看详情。
2. 不把 Markdown 字段当纯文本展示。
3. 不把文档产出只显示路径；本地 Markdown 文档必须可在扩展区预览。
4. 不把辅助属性提升为主阅读流大字段。
5. 不恢复右侧“关联对象列表导航”；右侧只做访问历史前进/后退。
6. 不把详情页内关联对象入口做成重复点击仍保持打开；重复点击当前入口必须收起扩展阅读。
7. 不在业务组件里新增另一套字段格式判断；新增字段先更新 `fieldFormats.ts`，并按性质同步 05.01 字段语义、05.02 内容格式或 05.03 注册消费规则。
8. 对象详情头部、对象引用卡片和扩展区对象预览必须保留复制对象路径入口。
9. 不把扩展阅读对象内容实现成详情页之外的第二套摘要；右侧对象内容必须从详情页阅读布局或详情页字段组件派生。
10. 项目画像类入口不属于当前 LDVH 工作对象、管辖配置或 Web 对象路由；ObjectDetail 不维护此类字段顺序、字段标签、详情路由、引用卡片或扩展阅读支持。

## 10. API 数据结构

```typescript
interface ObjectDetail {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status: string };
  data: Record<string, unknown>;
}
```

WorkCase 详情页可以额外消费 WorkCase 只读派生摘要，用于展示推进阶段、成功标准进度、执行态势、关闭材料完备性、阻塞关系和对象路径。当前 Web API 可派生 `executionItems`、`executionItemTotal`、`executionItemDone`、`executionItemBlocked`、`executionItemOpen`、`executionItemByStatus`、`successCriteriaTotal`、`successCriteriaDone`、`hasPlanConfirmedAt`、`hasClosureRequestedAt`、`hasVerificationEvidence`、`hasClosureEvidence` 和 `hasClosedAt`；历史 `review_requested_at` 可兼容为 `hasClosureRequestedAt`。派生摘要仍来自 Git 文件事实源的确定性读取，不写回事实源，也不作为第二事实源。
