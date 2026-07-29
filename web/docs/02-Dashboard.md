# 项目认知中心（取代 Dashboard）

> 路由：`/`（实现完成前仍由原 Dashboard 服务）
> 状态：设计已确认（Human 2026-07-29），实现未开始
> 目标源码：`web/src/pages/CognitionCenter.tsx`（新建，取代 `web/src/pages/Dashboard.tsx`）
> 目标 API：`GET /api/cognition`（新建，取代 `GET /api/dashboard`）
> 文件名说明：本文取代原 Dashboard 设计文档；文件名、`web/docs` 引用与相关测试契约的更名随实现工作一并完成，设计阶段不提前改名。

## 0. 变更决定记录（按 08 §9）

本次改动是有意改变可观察行为，不属于行为保持型重构。按 08 §9 记录决定要素：

| 要素 | 内容 |
|---|---|
| 变更对象 | 路由 `/` 页面及其聚合 API 的可观察行为、左侧导航第一项的名称与图标 |
| 变更前 | Dashboard 仪表盘：态势摘要行、对象统计网格、待推进、最近提交、最近活动 |
| 变更后 | 项目认知中心：待决定事项、我离开期间、演进时间线、Spark 池健康、方向对照五个只读模块与全局信任标记 |
| 作用范围 | 路由 `/`、`GET /api/dashboard`、左侧导航第一项、`dashboard.*` i18n key；对象列表、对象详情、提交记录、ProjectFiles、右侧扩展阅读、复制语义与 i18n 规则不变 |
| 当前来源支持 | 00 §7 第 3 条（Web 交互协作帮助 Human 了解进展、作出决定、给予授权和验收结果）；08 §1；`web/docs/01-全局设计约束.md` §1.2.1（最前面入口未确认、不写死，本决定确认其中第一项） |
| Human 决定 | 2026-07-29 Human 在 AI 对话中明确决定：废弃仪表盘，以项目认知中心取代；设计细节以本文为准 |
| 验收依据 | 本文 §10 验收标准 + 范围匹配的 API、组件与代表性浏览器测试（08 §10 对应行） |
| 明确不变范围 | 五个基准模块（提交、研究、决策、火花、经验）与 WorkCase 阅读形态不因本变更改动；本变更不新增事实源、状态机、对象类型、写入白名单或 Human Gate 结论 |

## 1. 页面目标

项目认知中心是 LDVH 面向 Human 的项目认知入口，服务六项 Human 价值标准（下称 H1–H6）：

| 标准 | 名称 | 本页对应模块 |
|---|---|---|
| H1 | 项目认知接续 | 我离开期间、演进时间线、Spark 池健康 |
| H2 | 决定依据完备 | 待决定事项 |
| H3 | 决定负担有界 | 待决定事项 |
| H4 | 人机理解对齐 | 全局信任标记与复制摘要 |
| H5 | 项目方向锚定 | 方向对照 |
| H6 | 提及事项闭环 | Spark 池健康 |

H1–H6 当前记录于事实源 `ldvh-base/sparks/spark-0037.yaml`（mechanically_valid，候选框架，尚未进入规范源）。本文引用其名称作为设计目标与验收框架，不把它们登记为规范事实；H 标准后续修订时本文随之修订。

页面边界：LDVH 不代替 Human 产生认知、决定与对齐，只提供方法与工具。本页帮助 Human 形成并维持对项目过去、现在与未来的认知，提供快速、准确、全面的决定依据，并把"AI 的理解与人的理解是否一致"做成可核查的工作方式；认知、决定与方向判断本身仍由 Human 作出，决定的作出与回写只发生在 AI 对话与受控写入路径中。

## 2. 设计原则

1. H1–H6 是北极星与验收框架，不是功能清单。模块建造顺序由真实痛点驱动，待决定事项收件箱第一（§11）。
2. 默认只读。本页不提供批准、关闭、分流、处置或任何可能改变项目状态的控件；每条目只提供查看详情、复制引用、复制摘要。
3. 一切从既有字段派生。不新增事实字段、状态、对象类型；所有聚合、计数、筛选、排序与"未关联"检测都是派生信息，如实标注来源、观察时间、转换规则与遗漏范围。
4. 继承五个基准模块与 WorkCase 阅读形态的设计语言；新增组件使用同一套 `ldvh-*` 语义类、复制语义、扩展阅读与 i18n 契约，不另起视觉和信息秩序。

## 3. 页面结构

```text
页面标题：项目认知中心 + 页面说明 + 观察时间标注
模块一 待决定事项（全宽主面板，置顶）
模块二 我离开期间 + 模块四 Spark 池健康（双列主面板）
模块三 演进时间线（全宽主面板）
模块五 方向对照（全宽主面板）
```

- 模块顺序固定，不按数据有无重排；未建设模块不显示占位（§11 分期）。
- Compact（≤599px）全部单列堆叠，待决定事项永远第一屏。
- 布局使用 `ldvh-dashboard-panel-grid` / `ldvh-section-grid` 容器宽度驱动列数，不以 `lg:` 视口断点作为唯一依据；右侧扩展阅读打开时列数随容器收缩。
- 页面不设置"重新读取"控件；进入路由或切换语言触发新的直读请求，不复用旧 payload、对象 `updated_at` 或浏览器渲染时刻冒充新观察。

## 4. 模块规格

### 4.1 模块一 待决定事项（H2 决定依据完备、H3 决定负担有界）

回答 Human 的问题：**现在有哪些事在等我决定？每个决定需要看什么？**

**收录规则（确定性派生，只使用既有字段）：**

| 待决类型 | 派生条件 | 决定依据区直读字段 |
|---|---|---|
| 待批准计划 | WorkCase `progress_group = plan_confirmation` | `goal` + `success_criterion_definitions[].statement`（与列表 Card 同一计划判断输入区，完整显示，不截断、不重新摘要） |
| 待确认关闭 | WorkCase `progress_group = closure_confirmation` | `goal` + 完整 `closure_proposal`（与"关闭待确认"Card 同一关闭判断输入区） |
| 已阻塞待处置 | WorkCase 来源 `status = blocked`（仅经 `source_status` 传递） | 实际存在的 `blocking_summary` / `waiting_on`，缺失时明确提示 |

- 排序：`priority`（P1→P3，仅 WorkCase 适用）→ `updated_at` 正序（等待最久在前）。排序是派生展示规则，不表达语义重要性结论。
- 待决类型是 UI 枚举，由（`progress_group`，来源阻塞）确定性映射，前端按 i18n 映射本地化；不新增第五进展分组，不建立第二状态模型。阻塞提示沿用 WorkCase Card 的琥珀/玫红语义色，不作为第四层整卡染色。
- 条目形态：对象类型 chip、标题、待决类型徽章、决定依据区、优先级弱信号、`formatDateTime()` 更新时间。点击标题打开右侧扩展阅读（复用 `WorkCaseReadingLayout`，与详情页同源）；标题以外区域不触发路由。
- 复制入口：精确读取取得可消费 `canonical_path` 的条目提供"复制对象路径"；每条目提供"复制决定摘要"——面向 AI 对话的多行文本，含对象稳定 ID、待决类型、决定依据要点，已精确读取时含 `canonical_path`。复制按钮 icon + tooltip，`stopPropagation()`。
- 决定在 AI 对话中作出，经 Helper 受控写入回写事实源；本模块不承载决定动作。
- 负担有界（H3）：默认完整展示全部待决条目；条目超出首屏时按上述排序截断，并在面板底部如实提示总数与未显示数量，不用分页掩盖待决规模。
- 空态：当前没有待你决定的事项（双语）。

### 4.2 模块二 我离开期间（H1 项目认知接续）

回答：**我上次看到现在，项目发生了什么？**

- 窗口起点 = Web 本地记录的上次访问时间（localStorage），属于 Web 本地派生状态，面板标题带如实标注"自你上次访问 YYYY-MM-DD HH:mm 以来"；无记录时回退为最近 7 天并如实说明回退依据。窗口起点不作为事实呈现。
- 内容：窗口内 Git 提交（复用 `web/api/services/git.ts` 的 commit DTO 与 Conventional Commits parser，不维护第二套）+ 窗口内 `updated_at` 发生变化的事实对象（按类型分组，对象行形态与扩展阅读入口同原"最近活动"）。
- 如实声明遗漏范围：本模块基于 commit 时间与 `updated_at`，不代表"全部变化"的完备清单；字段级变化细节留在提交记录页与对象详情。git 不可用时提交区单独显示实际不可用原因，对象区不受牵连。
- 面板同时标注本次观察时间（§5）。

### 4.3 模块三 演进时间线（H1）

回答：**项目这段时间是怎么走过来的？**

- 数据来源：Git commit records（复用 parser）+ 事实对象 `created_at` / `updated_at`。
- 视图：按日分组，最近 14 天，可向前加载更早日期；加载不到更早数据时如实显示到达可提供的最早范围，不伪造"无更早历史"。
- 每日内容：提交条目（分类 chip + 描述，行形态同提交卡片）与对象标记。对象标记只展示两类可确定事件：`created_at` 落在当日 → "创建"；`updated_at` 落在当日 → "更新"（如实标注为更新，不表达状态变化）。
- 诚实边界：当前事实源不保存状态变化事件历史，除"创建/更新"外不从 `updated_at` 推断状态变化时刻，不展示伪造的状态流转时间线；WorkCase 关闭报告等内容留在对象详情与提交记录。
- 与提交记录页的关系：本模块是"对象标记 + 提交"的联合时间线；纯提交证据流仍在 `/changelog`。

### 4.4 模块四 Spark 池健康（H1、H6 提及事项闭环）

回答：**我提过的事有没有被接住？Spark 池是不是在积压？**

**派生指标（全部标注为派生视图；阈值是 Web 展示参数，不是事实）：**

| 指标 | 派生规则 |
|---|---|
| open 总数与优先级分布 | `status = open`，按 `priority` 分组计数（priority 仅 Spark 适用） |
| 静默数 | `open` 且 `updated_at` 距今 ≥ 静默阈值（默认 5 天，前端常量，UI 如实标注） |
| 收敛情况 | 终态（`routed` / `implemented` / `discarded`）数 / 总数 |
| 近 30 天流动 | `created_at` 落在近 30 天的新增数 vs 同期 `updated_at` 更新且当前为终态的对象数（后者如实标注为"当前终态且近期有更新"，不冒充分流时刻） |

- 指标使用 `StatsCard` 数字档位（`text-xl` / `text-2xl`），不使用告警色块；`open` 按 20 显示为"待处理"。
- 静默 P1 列表：逐条列出对象行（标题、优先级弱信号、`updated_at`），点击打开右侧扩展阅读。
- 本模块不生成"应当分流到何处"的建议；H6 的承接判断由 Human 在 AI 对话中显式委托（Spark 承接语义见 spark-0037），页面只保证"被提及、未被接住"的事项如实可见。
- 空态：Spark 池当前没有静默积压。

### 4.5 模块五 方向对照（H5 项目方向锚定）

回答：**现在做的事和项目方向对不对得上？**

**内容（全部派生对照，不产生结论）：**

1. 方向锚点列表：非终态 WorkCase 的 `goal` 直读 + 生效中 ADR（状态闭集见 ADR 类型规范）的标题行；均为只读引用行，整行打开右侧扩展阅读，已精确读取的行提供"复制对象路径"。
2. 未关联方向锚点清单：当前在办对象（非终态 WorkCase 的当前工作项、`open` Spark）经对象自身已声明 `relations` 无法映射到任何非终态 WorkCase 或生效中 ADR 时列入。检测只使用对象已声明的正式关系；映射缺失如实呈现为"未关联"，不做语义相关性推断，不表达"方向偏离"结论。

- 本模块不是项目画像卡片；管辖项目配置的展示不属于本页，按管辖配置自身语义另行设计。
- 是否偏离方向由 Human 判断；需要调整方向、立 ADR 或发起 WorkCase 时，在 AI 对话中进行。

## 5. 全局信任标记（H4 人机理解对齐）

H4 的工作机制：Web 给 Human 看的派生视图，与 AI 经 Helper 精确读取的事实源，必须可互相核查。本页通过以下统一标记实现：

1. 每个模块标题带右侧标注：`派生视图` 弱标签 + 本次观察时间。观察时间统一取 API 响应的 `generatedAt`（服务端响应生成时刻的 RFC3339），按 `formatDateTime()` 显示；不用对象 `updated_at` 或浏览器时刻冒充观察时间。
2. 模块级降级：某一数据来源不可用（git 失败、某类型列表读取失败、字段问题）时，对应模块或分区如实显示实际不可用范围与原因，其它模块正常呈现；只有管辖范围解析失败才整页失败。
3. 每个模块标题带提供"复制模块摘要"：面向 AI 对话的多行文本，含模块名、观察时间、关键计数与条目稳定 ID 列表（不含未精确读取的路径）。Human 粘贴到 AI 对话后，AI 经 Helper 精确读取复核同一对象——页面与 AI 各走 00 §8.3 定义的读取路径，互查而非互替。
4. 事实、派生、诊断、未知范围可区分：直读字段按来源呈现；派生指标带转换说明；本地窗口起点、静默阈值等 Web 展示参数如实标注；读取问题与未解析结构在对应消费位置就地显示。

## 6. 交互

| 操作 | 行为 |
|---|---|
| 点击待决条目标题 | 打开右侧扩展阅读预览对象（再次点击当前条目关闭） |
| 点击对象标记 / 静默 Spark 行 / 锚点引用行 | 打开右侧扩展阅读 |
| 点击提交条目 | 跳转 `/changelog` |
| 点击复制对象路径 | 复制精确读取返回的 `canonical_path`（仅已精确读取条目显示） |
| 点击复制决定摘要 / 复制模块摘要 | 复制面向 AI 对话的多行摘要文本 |
| 切换语言 | 页面框架、模块标题、待决类型、状态、相对时间与观察时间同步切换 |

## 7. 实现约束

1. 不把本页做成营销首页、 hero 区或卡片堆叠的装饰页；面向重复阅读与判断，优先信息密度与扫描效率。
2. 不提供批准、关闭、分流、处置、优先级编辑或任何写入口；占位按钮、禁用按钮也不出现。
3. WorkCase 统计只使用 `byProgressGroup`，WorkCase 条目只使用 `progress_group`；不得把派生进展分组放入名为 `status` 或 `byStatus` 的字段。收件箱条目确需区分来源阻塞时，只能另设 `source_status`，不得复用 `status`。
4. 不新增事实字段、状态、对象类型、第五进展分组或第二状态模型；待决类型、静默阈值、窗口起点均为 UI 层派生，如实标注。
5. 决定依据区直读 `goal`、`success_criterion_definitions`、`closure_proposal`、`blocking_summary` / `waiting_on`，与 WorkCase 列表 Card 和详情页同源消费，不在本页另写摘要逻辑；缺失或类型不符按字段级解析规则如实呈现。
6. Git 提交必须复用 `web/api/services/git.ts` 的 commit message 拆分与 parser。
7. 复制语义按 01 §5；候选条目不用 `path`、`target` 或对象 ID 伪造 `canonical_path`；新增"复制决定摘要""复制模块摘要"两个语义，tooltip 按内容语义命名。
8. i18n 全量双语；事实正文（goal、提案、commit message 等）不翻译；英文长文案允许换行，不以截断替代阅读。
9. 扩展阅读与详情页复用同一身份头部与 `WorkCaseReadingLayout`，不维护第二套对象摘要。
10. 颜色遵守 01 §1.10：Human 待确认紫色系、阻塞/风险警示色、类型色只用于识别；不以单一色相支配页面。
11. 本页确认最前面入口的第一项为"项目认知中心"；其余入口的名称、顺序与信息架构仍按 01 §1.2.1 保持不写死，本页实现不得反向固定它们。

## 8. API 数据结构

`GET /api/cognition?locale=` 聚合返回（类型命名仅为契约描述，实现以 TS 类型为准）：

```typescript
type CognitionObjectType = 'workcase' | 'adr' | 'pitfall' | 'spark' | 'study';
type WorkCaseProgressGroup = 'plan_confirmation' | 'progressing' | 'closure_confirmation' | 'closed';
type InboxKind = 'plan_confirmation' | 'closure_confirmation' | 'blocked';

interface CognitionFactItem {
  type: CognitionObjectType;
  id: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  relativeTime: string;
  typeColor: string;
  // workcase 条目只携带 progress_group；其余类型携带 status
  progress_group?: WorkCaseProgressGroup;
  status?: string;
}

interface CognitionInboxItem extends CognitionFactItem {
  type: 'workcase';
  progress_group: WorkCaseProgressGroup;   // 展示分类
  inboxKind: InboxKind;                    // UI 枚举：待决类型，前端 i18n 映射
  source_status?: string;                  // 仅 blocked 条目需要，不复用 status 语义
  priority?: string;
  updatedAt: string;
}

interface CognitionData {
  generatedAt: string;                     // 观察时间，RFC3339
  scope: { governedProjectId: string };
  inbox: { items: CognitionInboxItem[]; total: number };
  whileAway: {
    windowStart: string;
    windowStartSource: 'last_visit' | 'fallback_7d';
    commits: CommitEntry[];                // 复用 Changelog commit DTO
    updatedObjects: CognitionFactItem[];
    commitsIssue?: { code: string; message: string };
  };
  timeline: { days: { date: string; commits: CommitEntry[]; objectMarks: (CognitionFactItem & { mark: 'created' | 'updated' })[] }[]; earliestReachable?: string };
  sparkHealth: {
    openTotal: number;
    byPriority: Record<string, number>;
    silentThresholdDays: number;           // 展示参数
    silentCount: number;
    silentP1: CognitionFactItem[];
    terminalTotal: number;
    total: number;
    recent30d: { created: number; terminalRecentlyUpdated: number };
  };
  direction: {
    anchors: { workcaseGoals: CognitionFactItem[]; activeAdrs: CognitionFactItem[] };
    unanchored: CognitionFactItem[];
  };
  issues?: { section: string; code: string; message: string }[];  // 模块级降级
}
```

- WorkCase 聚合遵守 §7 第 3 条命名纪律；其它类型不使用 `progress_group` / `byProgressGroup`。
- 决定依据区（`goal`、成功标准、`closure_proposal`、阻塞说明）不由本聚合端点重新摘要：收件箱条目点击后走与对象列表/详情同源的字段级直读，本端点只提供定位与分类所需的字段。若实现证明首屏确需内联依据区，必须复用与列表 Card 相同的投影函数，并在实现文档中说明。
- 本端点是派生视图服务，不成为事实权威；读取限定在当前唯一管辖项目与实际 worktree。

## 9. 响应式与移动端

| 级别 | 行为 |
|---|---|
| Compact（375–599px） | 全部模块单列堆叠，待决定事项第一屏；指标卡 2 列；触摸目标 ≥44×44px |
| Medium（600–839px） | 收件箱全宽；模块二/四双列；时间线、方向对照全宽 |
| Expanded（≥840px） | 同 Medium；容器加宽时指标卡可 4 列，由容器宽度驱动 |

移动端遵守 01 §1.6 与 §1.6.1 全部已确认规则；扩展阅读切换为底部抽屉。

## 10. 验收标准

1. Human 打开 `/` 后第一屏看到全部当前待决定事项（当前真实基线：3 项），每项能看到决定类型与决定依据入口。
2. 完成一次真实闭环：收件箱"复制决定摘要"→ 粘贴到 AI 对话 → AI 经 Helper 精确读取同一对象 → Human 作出决定 → 受控写入回写事实源 → 重新进入本页后收件箱反映新状态。
3. 每个模块可见派生身份与观察时间；git 不可用、某类型读取失败时模块级降级并如实标注，不整页失败、不沿用旧数据。
4. 双语切换：无 raw status / raw enum / raw 字段名；事实正文不翻译；英文布局不溢出。
5. 测试按 08 §10 对应行执行：派生内容（来源、观察时间、转换、过期可复核）、来源与判断边界呈现、Web 行为保持与变更（本表 §0 决定 + 范围匹配的 API/组件/代表性浏览器测试）。
6. i18n、复制语义、扩展阅读同源、字段级解析与未解析结构呈现遵守 01 全部硬约束。

## 11. 分期建设顺序（痛点驱动，收件箱第一）

| 期 | 模块 | 服务标准 | 说明 |
|---|---|---|---|
| 第一期 | 模块一 待决定事项 + §5 全局信任标记 | H2 / H3 / H4 | 直接对准"决定慢、依据散"的真实痛点；含 API、页面、复制摘要与模块级降级 |
| 第二期 | 模块二 我离开期间 + 模块四 Spark 池健康 | H1 / H6 | 接续认知与"提过的事有没有被接住" |
| 第三期 | 模块三 演进时间线 + 模块五 方向对照 | H1 / H5 | 长期演进认知与方向锚定 |

- 每期独立可验收（§10 对应条目）；未建设模块不在页面上显示占位空壳或"即将上线"文案。
- 第一期实现时同步完成：路由与导航替换（`CognitionCenter.tsx`、`nav.cognition`、图标按 09 语义规范选定）、`GET /api/cognition` 取代 `GET /api/dashboard`、`dashboard.*` i18n key 清理、本文文件名与测试契约引用更名、原 Dashboard 资产移除。原 Dashboard 的对象统计网格不再保留为首页模块；对象类型导航由左侧主导航承担。
