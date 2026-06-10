# ObjectDetail 对象详情

> 路由：`/objects/:type/:id`
> 源码：`web/src/pages/ObjectDetail.tsx`
> 字段格式规则：`web/src/utils/fieldFormats.ts`
> API：`GET /api/objects/:type/:id`

## 1. 页面目标

对象详情页是事实对象阅读器，不是 YAML 文件查看器。页面应按字段语义展示对象目标、证据、引用、状态和产出，并把 YAML 源码作为折叠兜底。

## 2. 当前页面结构

```text
状态筛选（与对象列表一致，保留 query）
返回按钮
对象头部：类型标签 + 标题 + ID + 类型说明 + 状态徽章 + 状态提示
元信息行：创建时间、更新时间、关闭时间、辅助属性
内容区：
  Task：语义阅读布局
  其他对象：字段卡片布局
Intent 聚合产出/文档（仅 Intent）
YAML 源码折叠区
右侧扩展阅读区（App Shell 提供，不属于本页卡片）
```

## 3. 头部与元信息

- 顶部状态筛选使用 `ObjectStatusFilter`，点击后回到同类型列表并带上对应状态 query。
- 返回按钮回到 `/objects/{type}`，保留当前 query。
- 类型标签使用对象类型颜色，显示本地化类型名。
- 标题优先使用 `title_zh/title_en`，回退 `title`，再回退 ID。
- ID 使用 `ldvh-meta`，不做大号标题。
- 状态徽章使用 `StatusBadge`；状态提示来自 `getStatusHint()`。
- 元信息行使用 `MetaChip`，时间统一 `formatDateTime()`，格式为 `YYYY-MM-DD HH:mm`。
- priority、severity、repeatability、category、tags 等辅助属性在元信息行降权展示，不进入主阅读流。

## 4. Task 语义阅读布局

Task 不使用普通字段卡片堆叠，而使用固定阅读主线：

1. 任务目标：`description` + `source` + `source_intent`。
2. 验收标准：`acceptance`，用 `ChecklistCard` 展示进度和每项状态。
3. 验证方式与关闭证据：`verification`、`closure_evidence`，用 `EvidenceBlock` 展示 Markdown、命令和路径。
4. 产出与文档：`deliverables`、`related_docs`、`affected_docs`，用 `DocPreviewLink`。
5. 前置依赖：`blocked_by`，用 `ReferenceCard`。
6. 其他字段：按 `fieldFormats.ts` 继续语义化渲染。

## 5. 非 Task 对象字段布局

- 每个字段一个轻量卡片，字段标题用 `ldvh-caption-strong`。
- 关联类字段可折叠；Intent 的关联字段默认展开，其他类型默认折叠。
- Pitfall、ADR、Memo、Intent 等长文本字段必须按 Markdown 渲染。
- Intent 的 `aggregated_deliverables` 和 `aggregated_docs` 作为聚合区域显示，不混入普通字段卡片。

## 6. 字段渲染规则

字段分类由 `web/src/utils/fieldFormats.ts` 统一维护，详情页和右侧扩展阅读区必须共同消费同一套规则。

| 字段类型 | 渲染组件 | 当前行为 |
|---|---|---|
| 叙述说明 / 决策 / 过程记录 | `SummaryText` | Markdown 渲染，长内容按段落摘要/展开 |
| 检查清单 | `ChecklistCard` | 进度条 + 勾选/未勾选图标 + inline Markdown |
| 兼容检查清单字段 | `ChecklistCard` 或 `SummaryText` | 只有内容包含 `- [ ]` / `- [x]` 时才按检查清单渲染 |
| 验证证据 | `EvidenceBlock` | Markdown 渲染，命令、路径和代码突出显示 |
| 对象 ID 引用 | `ReferenceCard` | 点击在右侧扩展阅读区打开对象 |
| 文档路径 / URL | `DocPreviewLink` | 本地 Markdown 文档在右侧扩展阅读区预览；外部 URL 新窗口打开 |
| 路径文本 | `PathText` | 等宽、可换行的路径标签 |
| 其他短文本 | `ldvh-body` | 普通文本 |

## 7. 右侧扩展阅读区

- 由 App Shell 的 `ReadingPanel` 提供。
- 触发来源：对象引用、文档引用、Dashboard / Workbench 的对象条目。
- 顶部只保留上一个访问对象、下一个访问对象和关闭按钮。
- 不展示对象列表式导航。
- 对象预览按对象类型展示关键字段，并复用 `fieldFormats.ts`。
- Markdown 文档预览使用 `MarkdownPreview` + `github-markdown-css`，不是手写 Markdown 标签样式。

## 8. YAML 源码

- 默认折叠。
- 展开后使用 `react-syntax-highlighter` + YAML + oneDark。
- 显示行号，最大高度 400px。
- YAML 源码是事实完整性兜底，不作为主阅读体验。

## 9. 实现约束

1. 不把关联任务显示成只有 ID 的标签；对象引用必须可点击并能在扩展区查看详情。
2. 不把 Markdown 字段当纯文本展示。
3. 不把文档产出只显示路径；本地 Markdown 文档必须可在扩展区预览。
4. 不把辅助属性提升为主阅读流大字段。
5. 不恢复右侧“关联对象列表导航”；右侧只做访问历史前进/后退。
6. 不在业务组件里新增另一套字段格式判断；新增字段先更新 `fieldFormats.ts` 和 `05.01`。

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
