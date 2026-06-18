# 提交记录页

> 路由：`/changelog`
> 源码：`web/src/pages/Changelog.tsx`
> API：`GET /api/changelog?count=50`、`GET /api/changelog/:hash`

## 1. 页面目标

提交记录页用于查看 Git commit records，并在需要时展开查看该提交的 `git diff --stat`。它是提交证据入口，不是工作对象列表，也不是完整 diff 浏览器。

## 2. 当前页面结构

```text
页面标题：提交记录
副标题：Git 提交记录，点击查看详情
提交卡片列表
  折叠态：箭头 + shortHash + commit message + 作者 + YYYY-MM-DD HH:mm + GitCommit 图标
  展开态：分隔线 + diff stat
```

## 3. 提交卡片

- 每条提交一个浅边框卡片。
- 折叠态：
  - 左侧 `ChevronRight`；
  - `shortHash` 使用 `ldvh-meta text-ldvh-accent`；
  - commit message 使用 `ldvh-body truncate`；
  - 作者和时间使用 `ldvh-caption`；
  - 右侧 `GitCommit` 图标。
- 展开态：
  - 箭头变为 `ChevronDown`；
  - 加载中显示旋转动画和 `common.loading`；
  - 成功后使用 `pre.ldvh-meta` 展示 `git diff --stat`。

## 4. Refs 行引用

- commit message 中的 `Refs:` 行会被解析。
- 形如 `workarea-0001`、`workplan-0006`、`adr-0006`、`memo-0005`、`pitfall-0001`、`study-0001` 的当前对象 ID 变成可点击文本。
- 点击对象 ID 在右侧扩展阅读区打开对应对象预览，不替换当前提交记录页。
- 非对象 ID 的文本原样展示。

## 5. 日期格式

- 使用 `formatDateTime(entry.date)`。
- 所有语言下统一显示为 `YYYY-MM-DD HH:mm`。
- 不使用浏览器 locale 自动格式，不显示秒或毫秒。

## 6. 交互

| 操作 | 行为 |
|---|---|
| 点击提交卡片 | 展开/收起该提交的 diff stat |
| 点击 Refs 对象 ID | 在右侧扩展阅读区打开对象预览 |
| 切换语言 | 页面标题、副标题、加载和错误文案同步切换 |

## 7. 实现约束

1. 不重复显示页面副标题。
2. 不把提交记录页改成完整 diff 查看器；当前只展示 stat。
3. 不展示 raw ISO 时间，统一使用 `formatDateTime()`。
4. 不把 commit message 强行翻译；它是 Git 事实内容。

## 8. API 数据结构

```typescript
interface ChangelogEntry {
  hash: string;
  shortHash: string;
  message: string;
  description: string;
  category: string;
  author: string;
  date: string;
  relativeTime: string;
}
```
