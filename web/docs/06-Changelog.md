# 提交记录页

> 路由：`/changelog`
> 源码：`web/src/pages/Changelog.tsx`
> API：`GET /api/changelog?count=50|100|200`、`GET /api/changelog/:hash`

## 1. 页面目标

提交记录页用于查看 Git commit records，并在需要时通过右侧扩展阅读查看该提交的格式化改动统计。它是提交证据入口，不是工作对象列表，也不是完整 diff 浏览器。

## 2. 当前页面结构

```text
加载范围：最近 50 / 100 / 200
快速筛选：type + scope
顶部控制区：随页面滚动固定在顶部
提交卡片列表
  容器：与对象卡片一致使用 ldvh-section-grid，宽度足够时一行多个
  默认态：左上相对时间 · type · scope + 右侧复制/阅读入口 + 标题块（GitHub 剪影图标 + description）
  选中态：卡片高亮，右侧阅读入口切换为收起态，右侧扩展阅读展示格式化提交详情
右侧扩展阅读
  提交身份区 + 提交与时间 + 文件/新增/删除汇总 + 提交说明 + 改动文件 + 原始信息
```

## 3. 提交卡片

- 每条提交一个浅边框卡片。
- 列表容器使用与研究等对象列表一致的 `ldvh-section-grid`，宽度足够时一行多个卡片，窄屏自动回到单列。
- 默认态：
  - 顶部左侧展示相对时间、`category` 和 `scope`，使用与研究卡片顶栏一致的 `ldvh-meta-muted` 弱元信息样式，并以文字中点分隔，不使用背景 chip；`category` 和 `scope` 按当前语言展示本地化标签，`scope` 为空时不展示；
  - 顶部右侧固定放置复制提交上下文和扩展阅读入口；未打开时使用 `ChevronRight`，打开后使用 `ChevronLeft`；
  - 下方标题块参考研究等对象卡片：使用弱背景、内圈边框和左侧色条；色条按 commit type 取色；
  - 标题块内使用与侧栏提交入口一致的 GitHub 剪影作为提交记录识别图标；
  - 标题行展示完整 `description`，作为主阅读文本；无法解析时回退到完整 `message`；标题不截断，宽度不足时换行；
  - 列表卡片不展示 `shortHash`；hash 信息只进入复制上下文和详情审计信息；
- 选中态：
  - 卡片边框和背景轻微高亮；
  - 右侧扩展阅读入口切换为向左收起态；
  - 列表内不展开 diff stat；
  - 右侧扩展阅读展示格式化提交详情。

## 4. 加载范围与筛选

- 页面默认加载最近 50 条提交。
- 用户可在最近 50、100、200 条之间切换；后端 `count` 上限为 200。
- 加载范围、`type` 和 `scope` 控件使用全局 tab 样式：`ldvh-tab-list`、`ldvh-tab-button`、`ldvh-tab-button-active` 和 `ldvh-tab-button-idle`；该样式也是对象状态筛选和工具页视图切换的统一外观。
- `type` 和 `scope` 快速筛选只作用于当前加载范围，不表示全仓库全量检索。
- `type` 筛选和标签按 `specs/10-Git提交规范.md` §5 本地化展示；中文显示简体中文列，英文显示原始 type token。
- `scope` 筛选和标签按 `specs/10-Git提交规范.md` §6 本地化展示；未知 scope 回退显示原始 token。
- 切换加载范围时重新拉取提交列表，并清除当前卡片选中态。
- 加载范围和快速筛选控制区应与对象列表页一致，滚动时固定在页面顶部。

## 5. 提交详情

- 详情统一进入右侧扩展阅读，不在列表内展开。
- 右侧扩展阅读顶部栏不展示提交标题，只保留导航、拖拽和关闭控制。
- 主视图上半部分复用对象详情标准文件头组件和层级，不使用紧凑标题变体：
  - 第一行左侧固定为对象类型“提交 / Commit”，其后使用与提交卡片第一行一致的弱元信息串：相对时间、分类和范围，以文字中点分隔，不使用背景 chip；
  - 提交描述；
  - 对象类型固定显示“提交 / Commit”，不得用 Conventional Commit `category` 替代对象类型；
  - Conventional Commit `category` 不作为对象类型展示；破坏性标记可作为同层短标签保留；
  - 绝对时间作为正文头部元信息保留，供审计读取；
  - 右侧复制操作保留在标准文件头操作位，复制 commit hash；卡片上的复制操作继续复制面向 AI 定位的提交上下文；
- 文件数、新增数、删除数汇总保留提交详情专用的三项指标卡设计；
- 主视图后续格式化呈现：
  - `提交说明` 节点；
  - `改动文件` 节点；
  - `原始信息` 节点。
- 有 commit body 时展示 `提交说明` 节点并默认展开；没有 body 时不显示该节点。
- `提交说明`、`改动文件` 和 `原始信息` 使用与对象正文一致的圆点标题、右侧折叠箭头和节点卡片样式；`改动文件` 和 `原始信息` 默认收起；原始 `git diff --stat` 或 `git show --stat` 文本只作为折叠审计信息保留，不作为主阅读界面。

## 6. 复制上下文

- 提交卡片的复制能力面向“快速与 AI 定位沟通”，不是只复制给人眼阅读的短哈希。
- 复制内容必须包含足够上下文，使 AI 能直接判断这是 LDVH Web 中的一条 Git commit record。
- 复制内容使用稳定多行文本，至少包含：
  - 固定标题：`LDVH Commit`;
  - `hash`：完整 commit hash；
  - `shortHash`：短哈希；
  - `type`：Conventional Commit 类型；
  - `scope`：提交范围，缺失时用 `-`；
  - `description`：提交描述，缺失时回退到完整 message；
  - `date`：使用页面统一绝对时间格式；
  - `body`：存在 commit body 时保留完整正文。
- 复制内容中的 `type` 和 `scope` 必须保留 Git 原始 token，不使用本地化显示名。
- 复制操作不打开、不关闭右侧扩展阅读。

## 7. 提交信息

- commit message 按 Git 事实内容原样展示。
- API 应返回完整 commit body，并按 Conventional Commits 解析 `category`、`scope`、`description` 和 `isBreaking`，供列表、仪表盘、提交详情和后续派生视图使用。
- 页面不解析 `Refs:`、`Human-Gate:`、`Verification:`、`Risk:` 为固定字段。
- 对象相关提交如需展示，应由后续专门的派生查询能力基于 Git 历史、文件路径、对象 ID 和自然文本实现，不在提交记录页内联解析。

## 8. 日期格式

- 卡片主信息优先使用 API 返回的 `relativeTime`。
- 需要展示绝对时间时使用 `formatDateTime(entry.date)`。
- 不使用浏览器 locale 自动格式，不显示秒或毫秒。

## 9. 交互

| 操作 | 行为 |
|---|---|
| 点击最近 50 / 100 / 200 | 重新加载对应数量的最近提交，并清除当前选中态 |
| 点击 type / scope 筛选 | 在当前加载范围内按 type 或 scope 快速过滤 |
| 点击提交卡片 | 打开右侧扩展阅读展示该提交的格式化详情，并高亮当前卡片 |
| 点击右侧复制图标 | 复制提交定位上下文，不打开或关闭详情 |
| 点击右侧详情图标 | 打开或收起右侧扩展阅读 |
| 切换语言 | 筛选、加载和错误文案同步切换 |

## 10. 实现约束

1. 页面不展示大标题或说明性副标题；提交页是证据流工具页，交互由筛选和卡片结构表达。
2. 不在卡片内展开 diff stat；提交详情统一进入右侧扩展阅读。
3. 不把提交记录页改成完整 diff 查看器；当前只展示 stat。
4. 不展示 raw ISO 时间；卡片优先展示相对时间，必要时使用 `formatDateTime()`。
5. 不把 commit message 强行翻译；它是 Git 事实内容。
6. 不把原始 `git show --stat` 文本作为详情主界面；主界面必须先格式化统计和文件列表，文件列表与原始信息都应位于默认收起的正文节点中。
7. 提交卡片操作区应与对象列表保持方向一致：复制和扩展阅读入口在右侧；提交没有对象状态，不展示状态徽标。
8. 复制内容必须服务 AI 定位沟通，不得退化为只复制短哈希或完整 hash。
9. 提交记录页不是全量搜索页；所有快速筛选均以当前加载的最近 50 / 100 / 200 条为边界。
10. 加载范围、type 和 scope 控制区必须使用 sticky 顶部固定表现，保持与对象列表页筛选区一致。
11. 提交页可本地化展示 type 和 scope 标签，但复制上下文、API 字段和筛选状态必须保留原始 token。

## 11. API 数据结构

```typescript
interface ChangelogEntry {
  hash: string;
  shortHash: string;
  message: string;
  body: string;
  category: string;
  scope: string;
  description: string;
  isBreaking: boolean;
  author: string;
  date: string;
  relativeTime: string;
}

interface ChangelogDetail {
  hash: string;
  stat: string;
  body: string;
  entry: ChangelogEntry;
}
```
