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
工作对象头部：类型标签 + ID + 优先级字符徽标 + 标题 + 创建/更新时间 + 复制路径图标
非工作对象元信息行：创建时间、更新时间、关闭时间、辅助属性
内容区：
  WorkArea：活跃计划 / 待关闭计划 / 已闭合计划 + 目标 / 范围 / 约束 / 来源 + 文档 / 决策 / 备忘 / 踩坑经验
  TaskPlan：任务队列 + 成功标准 / 完成证据 + 目标 / 所属工作域 / 来源 + 文档 / 决策 / 备忘 / 踩坑经验 / 关联变更
  Task：任务状态 + 子任务态势 + 验收标准 + 验证方式 + 目标 / 所属计划 / 来源 + 关闭证据 + 产出物 / 关联文档 / 影响文档 / 决策 / 关联变更
  SubTask：任务状态 + 验收标准 + 验证方式 + 目标 / 所属任务 / 来源 + 关闭证据
  其他对象：字段卡片布局
YAML 源码折叠区
右侧扩展阅读区（App Shell 提供，不属于本页卡片）
```

## 3. 头部与元信息

- 返回按钮优先回到进入详情页前的来源界面（`location.state.from`），用于支持从 WorkArea 卡片进入 TaskPlan、从 TaskPlan 卡片进入 Task 等跨对象类型跳转；直接打开详情页且没有来源时，兜底回到 `/objects/{type}` 并保留当前 query。返回目标是对象列表页时，右侧扩展阅读区必须主动关闭，避免把详情页上下文残留到主选择面。
- 详情页不展示对象列表的状态筛选；状态筛选只属于列表页，详情页第一视觉层应是当前对象。
- 类型标签使用对象类型颜色，显示本地化类型名。
- 标题优先使用 `title_zh/title_en`，回退 `title`，再回退 ID；工作对象和普通对象标题前均使用 `ObjectTypeIcon(obj.type)` 识别对象身份。
- TaskPlan 和 Memo 如存在 `priority`，在标题行最前面展示 `P0` / `P1` / `P2` / `P3` 字符徽标，随后才是 `ObjectTypeIcon(obj.type)` 和标题；徽标使用颜色和 tooltip 表达优先级，不在头部或元信息行重复展示 priority 文字 chip。
- ID 使用 `ldvh-meta`，不做大号标题。
- 头部右侧提供 `CopyPathButton`，复制对象详情 API 返回的 `target`。
- 非工作对象状态徽章使用 `StatusBadge`；WorkArea、TaskPlan、Task、SubTask 头部不显示状态 chip，状态只在计划组、任务队列或任务状态等语义模块中表达，避免顶部事实状态和正文语义状态形成两套口径。
- 非工作对象元信息行使用 `MetaChip`，时间统一 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`。
- 对象字段必须以对应工作模型主规范为准；只有该对象字段契约内定义的辅助属性才可在元信息行降权展示，不进入主阅读流。`priority` 只适用于 TaskPlan 和 Memo，且在详情头部以字符徽标展示；importance 已由 priority 统一承载，不再作为独立字段。Task 当前只允许 `assignee` 作为辅助元信息；Task / SubTask 不得把 `priority`、`importance`、`category`、`tags` 写入测试夹具或事实源。
- WorkArea、TaskPlan、Task、SubTask 使用统一工作对象身份区：`类型 + ID + 标题 + 创建/更新时间` 合并展示；不在头部显示状态徽章或“进行中”等通用解释文案，创建/更新时间不再作为独立 chip 行。

## 4. WorkArea 语义阅读布局

WorkArea 不使用普通字段卡片堆叠，而作为“工作域入口”展示：

1. 计划组：页面主区域第一组内容，按活跃、待关闭、已闭合分组展示关联计划；不再额外包一层“计划态势”区块，不展示顶部数量汇总。
2. 活跃/待关闭计划默认展开，每行作为进入 TaskPlan 的入口；已闭合计划默认折叠。组标题文案只写“活跃计划 / 待关闭计划 / 已闭合计划”，不显示数量。活跃/待关闭组标题只作为静态组 header，不表现为按钮；只有可折叠的已闭合组展示折叠按钮状态。
3. 计划组标题只使用小圆点，不使用 TaskPlan 对象图标；计划行展示优先级字符徽标、TaskPlan 对象图标、计划标题、计划 ID、更新时间、compact 任务态势条、复制路径和辅助阅读入口图标，不重复展示状态徽章；态势条占满计划行宽度；计划标题使用 `ldvh-body`，不使用 `ldvh-card-title`，避免越过组标题和区块标题层级；成功标准、完成证据等计划关闭材料留在 TaskPlan 详情中表达。复制路径图标默认和 hover 都保持中性 ghost；辅助阅读图标默认中性，在计划行 hover 或当前右侧阅读已打开时才使用该计划组状态色。
4. WorkArea 详情页点击计划行只打开右侧辅助阅读区，不切换主路由到 TaskPlan 详情；主路由跳转只属于对象列表卡片。
5. 定义事实不再收进“属性”总区块；目标、范围、约束、来源分别作为同级模块展示 `description/scope/constraints/source`，不把 `scope` 放进顶部元信息 chip。模块标题使用小圆点，降低装饰负担；多行内容渲染为语句列表，`包含` / `不包含` 等短前缀渲染为语义标签。
6. 关联材料不再收进“关联材料”总区块；文档、决策、备忘、踩坑经验按 `related_docs/related_adrs/related_memos/related_pitfalls` 分别作为同级模块展示，只有对应字段非空时显示。
7. 关联材料模块内部使用 plain 引用行，不带状态色背景，也不再套小卡片边框；右侧复制路径和扩展阅读图标保持中性 ghost 表现，左侧对象类型图标、ID 或短标签承担对象类型识别。

## 5. TaskPlan 语义阅读布局

TaskPlan 不使用普通字段卡片堆叠，而作为“一次目标的执行态势”展示：

1. 任务队列：页面主区域第一块，展示整体 Task 态势条，并按与列表一致的队列顺序展示 Task 行；队列顺序与态势条空间方向对应，态势条最右侧状态在上，最左侧状态在下；区块标题只使用小圆点。
2. 成功标准和完成证据不再收进“关闭判断”总区块；分别作为同级模块展示 `success_criteria/completion_evidence`。不展示额外顶部结论条，不单列待确认项或记录状态，未完成项由两个 checklist 自身表达。成功标准是关闭判断依据，但不再用外层总模块包住。
3. 定义事实不再收进“属性”总区块；目标、所属工作域、来源分别作为同级模块展示 `description/workarea/source`。所属工作域入口使用模块内对象引用值，显示 WorkArea 对象图标和工作域标题，不显示 ID 或状态徽章，点击只打开右侧辅助阅读，不切换主路由。
4. Task 行在 TaskPlan 详情中与 WorkArea card 的动作体验保持一致：复用状态色弱背景、左侧状态图标、Task 对象图标、任务标题、ID、复制路径和辅助阅读入口；右侧操作图标默认中性，辅助阅读入口可随行 hover 切到该行背景对应的状态色，复制按钮只有自身 hover 时变色。有 SubTask 时只展示 compact 子任务态势条，不在 TaskPlan 详情展开子任务行。
5. 关联材料不再收进“关联材料”总区块；文档、决策、备忘、踩坑经验、关联变更按 `related_docs/related_adrs/related_memos/related_pitfalls/related_changes` 分别作为同级模块展示。材料来源仍聚合计划自身和计划内 Task，按 ID 或路径去重；不把 Task 的 `deliverables/affected_docs` 混入计划材料。
6. TaskPlan 详情页点击 Task 行只打开右侧辅助阅读区，不切换主路由到 Task 详情；主路由跳转只属于对象列表卡片。

## 6. Task 语义阅读布局

Task / SubTask 不使用普通字段卡片堆叠，而使用固定阅读主线。它们与 WorkArea / TaskPlan 共用同一条设计语言：不使用“属性”“关联材料”“上下文”“产出与引用”等外层聚合框，而是按事实语义拆成独立模块。这样主详情页和右侧扩展阅读区都能在狭长视口中逐块阅读。

1. 任务状态：页面主区域第一块，展示当前任务/子任务的态势图标与语义状态；`planned + blocked_by` 表达为等待中，但不在状态模块里展开等待对象。状态本身用独立状态块表达，不再伪装成普通字段行。
2. Task 如果存在 SubTask，子任务态势必须紧跟任务状态展示：整体 SubTask 态势条 + SubTask 行；SubTask 行只打开右侧辅助阅读，不切换主路由。
3. 验收标准和验证方式紧跟子任务态势展示，先回答“是否满足”和“如何验证”，再进入目标与来源背景。
4. 验收标准：`acceptance`，用 `ChecklistCard` 展示进度和每项状态。
5. 验证方式：`verification` 内容为 GFM checklist 时与验收标准保持同样的 `ChecklistCard` 样式；内容为命令、结论或证据段落时使用 embedded `EvidenceBlock`。关闭证据 `closure_evidence` 作为独立证据模块展示，且只有在事实源存在非空内容时显示，不用“尚未记录”占位模块暗示验证中对象已经具备关闭证据。
6. 定义事实不再收进“任务目标”或“上下文”总区块；目标、所属计划或所属任务、来源分别作为同级模块展示，来源放在父对象引用之后。`source` 字段本身就是来源，不在字段内容里再写“来源：”或“用途：”二级标签；用途、测试目的等说明应进入目标或验收/验证字段。所属计划/任务入口使用模块内对象引用值，点击只打开右侧辅助阅读。
7. Task 的产出与文档不再收进“产出与文档”总区块；产出物、关联文档、影响文档按 `deliverables/related_docs/affected_docs` 分别作为同级模块展示。`deliverables` 表示可追溯结果物路径；`related_docs` 表示任务参考输入文档路径；`affected_docs` 只表示任务完成后需要同步检查的文档路径，应指向 `docs/`、`web/docs/` 或 `specs/` 下的 Markdown 文档，不得放入 `web/src/` 等实现源码路径。
8. Task 的关联材料不再收进“关联材料”总区块；决策、关联变更按 `related_adrs/related_changes` 分别作为同级模块展示。材料只收纳当前 Task 自己的材料，不复制上层 TaskPlan 或 WorkArea 的材料。SubTask 字段契约当前不定义产出物、关联文档、影响文档、决策或关联变更；测试夹具不得为 SubTask 杜撰这些字段。
9. 其他字段：只显示非空字段，避免把空数组、空关联或空产出提升到主阅读流；如果 Task / SubTask 经常出现“其他字段”，应优先回到字段规范和专用布局收敛，而不是把它视为正常主模块。
10. Task / SubTask 详情页内的父计划、父任务和子任务行只打开右侧辅助阅读区，不切换主路由。
11. Task / SubTask 不继承上层对象的完整详情：Task 只回指所属 TaskPlan，SubTask 只回指所属 Task。WorkArea 的范围、约束和 TaskPlan 的成功标准、完成证据只在对应对象详情中阅读。

## 7. 非工作主线对象字段布局

- 每个字段一个轻量卡片，字段标题用 `ldvh-caption-strong`。
- 关联类字段可折叠；默认折叠长关联集合，避免压过主阅读路径。
- Pitfall、ADR、Memo、WorkArea、TaskPlan 等长文本字段必须按 Markdown 渲染。
- TaskPlan、Task 和 SubTask 已使用专用语义布局，不进入普通字段卡片路径。

## 8. 字段渲染规则

字段分类由 `web/src/utils/fieldFormats.ts` 统一维护，详情页和右侧扩展阅读区必须共同消费同一套规则。字段分类只决定 Web 如何阅读和渲染字段，不定义字段是否存在、是否必填或适用于哪些对象；字段契约以 `specs/20-39` 对应工作模型主文件和 `specs/05.01-工作字段内容格式规范.md` 为准。

同名字段在不同工作对象详情页中必须使用同一套标题、组件和基础视觉权重。例：`description` 统一显示为“目标”，`source` 统一显示为普通定义文本，`related_docs` 统一显示为“文档”材料模块。对象层级差异只允许体现在字段顺序、是否聚合派生数据和是否出现对象特有字段上，不允许同名字段在 TaskPlan 与 Task 中换标题、降权或换交互样式。

详情页专用阅读布局已经由 `TaskSection` 提供外层卡片边界；`verification`、`closure_evidence`、`completion_evidence` 等证据字段在这些模块内必须使用 embedded 证据渲染，不再额外套一层证据色边框。证据色边框只用于没有外层详情模块的独立证据块。

| 字段类型 | 渲染组件 | 当前行为 |
|---|---|---|
| 叙述说明 / 决策 / 过程记录 | `SummaryText` | Markdown 渲染，长内容按段落摘要/展开 |
| 检查清单 | `ChecklistCard` | 进度条 + 勾选/未勾选图标 + inline Markdown |
| 兼容检查清单字段 | `ChecklistCard` 或 `SummaryText` | 只有内容包含 `- [ ]` / `- [x]` 时才按检查清单渲染 |
| 验证证据 | `EvidenceBlock` | Markdown 渲染，命令、路径和代码突出显示 |
| 对象 ID 引用 | `ReferenceCard` | 点击在右侧扩展阅读区打开对象；卡片内提供复制完整路径图标 |
| 文档路径 / URL | `DocPreviewLink` | 本地 Markdown 文档在右侧扩展阅读区预览；外部 URL 新窗口打开 |
| 路径文本 | `PathText` | 等宽、可换行的路径标签 |
| 其他短文本 | `ldvh-body` | 普通文本 |

当前可点击对象引用仅覆盖 Web 支持的工作对象类型：WorkArea、TaskPlan、Task、SubTask、ADR、Pitfall、Memo。未进入当前对象路由的引用只作为普通引用文本展示，不跳转到无效详情页。

路径类字段应按字段语义区分：`related_docs` 指向引用文档，`affected_docs` 指向需同步检查的文档，`deliverables` 指向结果物，`related_rules` 指向规范、Rules、Skill、Agent、Code 或 Web 承接位置。Web 可预览本地 Markdown 或展示路径，但不得把可预览路径集合解释为所有路径字段的合法范围。

## 9. 右侧扩展阅读区

- 由 App Shell 的 `ReadingPanel` 提供。
- 触发来源：对象引用、文档引用、Dashboard / Changelog 的对象条目。
- 顶部只保留上一个访问对象、下一个访问对象和关闭按钮。
- 不展示对象列表式导航。
- 同一对象或文档入口再次点击关闭扩展阅读区；点击不同入口才切换右侧预览内容。
- 对象预览不是“摘要卡片”，而是对象详情页阅读内容的右侧视口；同一个对象在详情页和扩展阅读区必须使用同一套字段顺序、字段标签、字段过滤和字段渲染。
- WorkArea、TaskPlan、Task、SubTask 必须复用详情页导出的专用阅读布局：`WorkAreaReadingLayout`、`TaskPlanReadingLayout`、`TaskReadingLayout`。
- WorkArea、TaskPlan、Task、SubTask 的扩展阅读头部同样不显示状态 chip；右侧面板按详情页身份区顺序展示 `类型 + ID + 标题 + 创建/更新时间 + 复制路径入口`，状态由复用的语义阅读布局表达。
- ADR、Memo、Pitfall、Profile 等通用对象必须复用详情页导出的 `getObjectDetailContentEntries()` 和 `ContentField`；不得在 `ReadingPanel` 中维护另一套 `PREVIEW_FIELD_ORDER`、字段 label map 或独立字段渲染器。
- 对象预览头部提供复制完整路径图标，复制对象详情 API 返回的 `target`。
- Markdown 文档预览使用 `MarkdownPreview` + `github-markdown-css`，不是手写 Markdown 标签样式。
- Markdown 正文基准字号为 14px；表格横向滚动，代码块、引用块、任务列表由全局 Markdown 样式统一控制。

## 10. YAML 源码

- 默认折叠。
- 展开后使用 `react-syntax-highlighter` + YAML + oneDark。
- 显示行号，最大高度 400px。
- YAML 源码是事实完整性兜底，不作为主阅读体验。

## 11. 实现约束

1. 不把关联任务显示成只有 ID 的标签；对象引用必须可点击并能在扩展区查看详情。
2. 不把 Markdown 字段当纯文本展示。
3. 不把文档产出只显示路径；本地 Markdown 文档必须可在扩展区预览。
4. 不把辅助属性提升为主阅读流大字段。
5. 不恢复右侧“关联对象列表导航”；右侧只做访问历史前进/后退。
6. 不把详情页内关联对象入口做成重复点击仍保持打开；重复点击当前入口必须收起扩展阅读。
7. 不在业务组件里新增另一套字段格式判断；新增字段先更新 `fieldFormats.ts` 和 `05.01`。
8. 对象详情头部、对象引用卡片和扩展区对象预览必须保留复制完整路径入口。
9. 不把扩展阅读对象内容实现成详情页之外的第二套摘要；右侧对象内容必须从详情页阅读布局或详情页字段组件派生。

## 12. API 数据结构

```typescript
interface ObjectDetail {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status: string };
  data: Record<string, unknown>;
}
```

TaskPlan 和 Task 详情页会额外消费 `GET /api/objects/taskplan` 的只读派生摘要，用于展示 Task / SubTask 态势、阻塞关系和复制路径。TaskPlan 详情接口会派生 `aggregated_related_*` 字段，用于把计划自身和计划内 Task 的关联材料合并去重后展示。派生摘要仍来自 Git 文件事实源的确定性读取，不写回事实源，也不作为第二事实源。
