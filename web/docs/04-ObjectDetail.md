# ObjectDetail 对象详情

> 路由：`/objects/:type/:id`
> 源码：`web/src/pages/ObjectDetail.tsx`
> 字段格式规则：`web/src/utils/fieldFormats.ts`
> API：`GET /api/objects/:type/:id`
> 全局设计语言：`web/docs/01-全局设计约束.md` §1.10

## 1. 页面目标

对象详情页是事实对象阅读器，不是 YAML 文件查看器。页面应按字段语义展示对象目标、证据、引用、状态和产出，并把 YAML 源码作为折叠兜底。

## 2. 当前页面结构

```text
返回按钮
对象头部：类型标签 + 标题 + ID + 类型说明 + 复制路径图标 + 状态徽章 + 状态提示
元信息行：创建时间、更新时间、关闭时间、辅助属性
内容区：
  WorkArea：计划态势 + 属性 + 关联材料
  Task / SubTask：语义阅读布局
  其他对象：字段卡片布局
TaskPlan 聚合产出/文档（仅 TaskPlan）
YAML 源码折叠区
右侧扩展阅读区（App Shell 提供，不属于本页卡片）
```

## 3. 头部与元信息

- 返回按钮优先回到进入详情页前的来源界面（`location.state.from`），用于支持从 WorkArea 卡片进入 TaskPlan、从 TaskPlan 卡片进入 Task 等跨对象类型跳转；直接打开详情页且没有来源时，兜底回到 `/objects/{type}` 并保留当前 query。返回目标是对象列表页时，右侧扩展阅读区必须主动关闭，避免把详情页上下文残留到主选择面。
- 详情页不展示对象列表的状态筛选；状态筛选只属于列表页，详情页第一视觉层应是当前对象。
- 类型标签使用对象类型颜色，显示本地化类型名。
- 标题优先使用 `title_zh/title_en`，回退 `title`，再回退 ID。
- ID 使用 `ldvh-meta`，不做大号标题。
- 头部右侧提供 `CopyPathButton`，复制对象详情 API 返回的 `target`。
- 状态徽章使用 `StatusBadge`；状态提示来自 `getStatusHint()`。
- 元信息行使用 `MetaChip`，时间统一 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`。
- priority、severity、repeatability、category、tags 等辅助属性在元信息行降权展示，不进入主阅读流。
- WorkArea 使用专用身份区：`工作域 + ID + 标题 + 状态 + 创建/更新时间` 合并展示；状态只保留 `活跃/已归档` 事实徽章，不显示“进行中”等通用解释文案，创建/更新时间不再作为独立 chip 行。

## 4. WorkArea 语义阅读布局

WorkArea 不使用普通字段卡片堆叠，而作为“工作域入口”展示：

1. 计划态势：页面主区域第一块，按活跃、待关闭、已闭合分组展示关联计划；不额外展示顶部数量汇总。
2. 活跃/待关闭计划默认展开，每行作为进入 TaskPlan 的入口；已闭合计划默认折叠。
3. 计划行展示计划标题、计划 ID、更新时间、状态、compact 任务态势条、复制路径和辅助阅读入口图标；态势条占满计划行宽度；计划标题使用 `ldvh-body`，不使用 `ldvh-card-title`，避免越过组标题和区块标题层级；成功标准、完成证据等计划关闭材料留在 TaskPlan 详情中表达。辅助阅读图标不是占位，未展开时表示打开右侧阅读，当前计划已展开时切换为关闭方向。
4. WorkArea 详情页点击计划行只打开右侧辅助阅读区，不切换主路由到 TaskPlan 详情；主路由跳转只属于对象列表卡片。
5. 属性：按目标、来源、范围、约束展示 `description/source/scope/constraints`，不把 `scope` 放进顶部元信息 chip；标题使用与计划态势一致的图标+标题样式。
6. 关联材料：只有 `related_docs/related_adrs/related_memos/related_pitfalls` 非空时显示。

## 5. Task 语义阅读布局

Task 不使用普通字段卡片堆叠，而使用固定阅读主线：

1. 任务目标：Task 使用 `description` + `source` + `taskplan`，SubTask 使用 `description` + `source` + `task`。
2. 验收标准：`acceptance`，用 `ChecklistCard` 展示进度和每项状态。
3. 验证方式与关闭证据：`verification`、`closure_evidence`，用 `EvidenceBlock` 展示 Markdown、命令和路径。
4. 产出与文档：`deliverables`、`related_docs`、`affected_docs`，用 `DocPreviewLink`。
5. 前置依赖：`blocked_by`，用 `ReferenceCard`。
6. 其他字段：按 `fieldFormats.ts` 继续语义化渲染。

## 6. 非 Task 对象字段布局

- 每个字段一个轻量卡片，字段标题用 `ldvh-caption-strong`。
- 关联类字段可折叠；TaskPlan 的关联字段默认展开，其他类型默认折叠。
- Pitfall、ADR、Memo、WorkArea、TaskPlan 等长文本字段必须按 Markdown 渲染。
- TaskPlan 的 `aggregated_deliverables` 和 `aggregated_docs` 作为聚合区域显示，不混入普通字段卡片。
- TaskPlan 后续应从普通字段卡片升级为语义阅读布局，按全局设计语言围绕“计划目标、关闭判断、任务拆解、证据/产出、关联材料”组织，而不是直接展开工作域属性或任务细节。

## 7. 字段渲染规则

字段分类由 `web/src/utils/fieldFormats.ts` 统一维护，详情页和右侧扩展阅读区必须共同消费同一套规则。

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

## 8. 右侧扩展阅读区

- 由 App Shell 的 `ReadingPanel` 提供。
- 触发来源：对象引用、文档引用、Dashboard / Changelog 的对象条目。
- 顶部只保留上一个访问对象、下一个访问对象和关闭按钮。
- 不展示对象列表式导航。
- 同一对象或文档入口再次点击关闭扩展阅读区；点击不同入口才切换右侧预览内容。
- 对象预览按对象类型展示关键字段，并复用 `fieldFormats.ts`。
- 对象预览头部提供复制完整路径图标，复制对象详情 API 返回的 `target`。
- Markdown 文档预览使用 `MarkdownPreview` + `github-markdown-css`，不是手写 Markdown 标签样式。
- Markdown 正文基准字号为 14px；表格横向滚动，代码块、引用块、任务列表由全局 Markdown 样式统一控制。

## 9. YAML 源码

- 默认折叠。
- 展开后使用 `react-syntax-highlighter` + YAML + oneDark。
- 显示行号，最大高度 400px。
- YAML 源码是事实完整性兜底，不作为主阅读体验。

## 10. 实现约束

1. 不把关联任务显示成只有 ID 的标签；对象引用必须可点击并能在扩展区查看详情。
2. 不把 Markdown 字段当纯文本展示。
3. 不把文档产出只显示路径；本地 Markdown 文档必须可在扩展区预览。
4. 不把辅助属性提升为主阅读流大字段。
5. 不恢复右侧“关联对象列表导航”；右侧只做访问历史前进/后退。
6. 不把详情页内关联对象入口做成重复点击仍保持打开；重复点击当前入口必须收起扩展阅读。
7. 不在业务组件里新增另一套字段格式判断；新增字段先更新 `fieldFormats.ts` 和 `05.01`。
8. 对象详情头部、对象引用卡片和扩展区对象预览必须保留复制完整路径入口。

## 11. API 数据结构

```typescript
interface ObjectDetail {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status: string };
  data: Record<string, unknown>;
}
```
