# ObjectList 对象列表

> 路由：`/objects/:type`
> 源码：`web/src/pages/ObjectList.tsx`
> API：`GET /api/objects/:type?status=xxx`

## 1. 页面目标

对象列表用于浏览单一对象类型下的事实对象，并通过状态筛选快速缩小范围。

对象类型切换由左侧主导航完成，本页不再提供顶部类型标签页。

## 2. 当前页面结构

```text
状态筛选（ObjectStatusFilter）
对象卡片自适应网格（ldvh-section-grid）
  卡片：ID + 复制路径图标 + 状态徽章 + 标题 + 更新时间
加载态 / 错误态 / 空态
```

## 3. 区域详细设计

### 3.1 状态筛选

- 位于列表顶部。
- 由 `ObjectStatusFilter` 根据当前类型聚合状态数量。
- 展示“全部 + 各状态 + 数量”。
- 当前状态写入 URL query：`?status=review_needed`。
- 点击对象进入详情页时保留当前 query，使详情页顶部筛选和返回路径一致。

### 3.2 对象卡片

- 使用 `ldvh-section-grid`，列数由容器宽度自动决定。
- 不使用表格视图，不使用顶部类型标签页。
- 每张卡片结构：
  - 左上：对象 ID，`ldvh-meta`；
  - 右上：`CopyPathButton` + `StatusBadge`；
  - 中部：本地化标题，`ldvh-card-title`；
  - 底部：`formatDateTime(updated)`，格式为 `YYYY-MM-DD HH:mm`。
- 复制图标复制对象 YAML 文件完整路径，使用 API 返回的 `path`。
- 点击复制图标不得进入详情页；点击卡片其他区域进入详情页。
- hover 时边框变为 `border-ldvh-accent/40`，标题变 accent 色。

### 3.3 空态、加载态、错误态

- 加载态：居中旋转动画。
- 错误态：`common.loadFailed` + 错误信息。
- 空态：`objectList.noObjects`，不得拼 raw 中文句子。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 点击左侧导航类型 | 切换到对应 `/objects/:type` |
| 点击状态筛选 | 更新 URL query 并刷新列表 |
| 点击对象卡片 | 跳转到 `/objects/{type}/{id}`，保留当前 query |
| 点击复制路径图标 | 复制对象 YAML 文件完整路径，不改变当前页面 |
| 切换语言 | 状态、标题和空态文案同步切换 |

## 5. 实现约束

1. 不恢复顶部对象类型标签页；类型导航已经统一到左侧侧栏。
2. 不把列表改成表格；当前事实对象用卡片扫描。
3. 不展示 raw ISO 时间，统一使用 `formatDateTime()`。
4. 不在列表卡片里塞入长描述；列表只承载定位信息。
5. 对象卡片必须保留复制完整路径图标，方便把事实源路径交给 AI。

## 6. API 数据结构

```typescript
interface ObjectItem {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;
  path: string;
  updated: string;
}
```
