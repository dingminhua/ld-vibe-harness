# ObjectDetail 对象详情

> 路由：`/objects/:type/:id`
> 源码：`web/src/pages/ObjectDetail.tsx`
> API：`GET /api/objects/:type/:id`

## 1. 页面目标

让用户完整查看一个事实对象的所有信息，包括元数据、内容字段和 YAML 源码。

## 2. 布局结构

```
┌─────────────────────────────────────────┐
│ ← 返回                                  │
│ [类型标签]  标题                    状态  │
│             ID                           │
├─────────────────────────────────────────┤
│ 元信息行                                 │
│ [创建时间: xxx] [更新时间: xxx] [关闭时间]│
├─────────────────────────────────────────┤
│ 内容字段（每个字段一个卡片）              │
│ ┌─────────────────────────────────────┐ │
│ │ 📄 描述 / Description               │ │
│ │ Markdown 渲染内容...                │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 📄 验收标准 / Acceptance            │ │
│ │ ☑ 条件1  ☐ 条件2                   │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 📄 前置依赖 / Blocked By            │ │
│ │ [task-0001] [task-0003]             │ │
│ └─────────────────────────────────────┘ │
│ ...                                     │
├─────────────────────────────────────────┤
│ ▶ YAML 源码 / YAML Source              │
│ ┌─────────────────────────────────────┐ │
│ │ 1 | id: intent-0001                 │ │
│ │ 2 | title: ...                      │ │
│ │ （语法高亮，可滚动，最大高度400px）   │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 3. 区域详细设计

### 3.1 头部

- 返回按钮：`← 返回 / ← Back`，点击回到列表
- 类型标签：带颜色背景（20% 透明度），中英双语
- 标题：中英切换（优先 title_en/title_zh，回退 title）
- ID：等宽小字
- 状态徽章：右侧，md 尺寸

### 3.2 元信息行

- 横向排列，flex-wrap
- 每个元信息为 MetaChip：标签（小字灰色）+ 值（等宽小字）
- 固定显示：创建时间、更新时间
- 条件显示：关闭时间（仅 closed_at 存在时）
- 标签文案中英切换

### 3.3 内容字段

每个字段一个卡片，字段名中英双语。

**字段渲染规则**：

| 值类型 | 渲染方式 |
|---|---|
| Markdown 字段 | react-markdown + remark-gfm 渲染 |
| Checklist 字段 | GFM 渲染（含复选框） |
| 长文本（含换行或 >200 字） | Markdown 渲染 |
| 短文本 | 纯文本 |
| 布尔值 | 绿色/红色标签（true/false） |
| 数字 | 等宽 accent 色 |
| 字符串数组 | 标签列表（圆角边框小标签） |
| 对象数组 | 每个对象一个嵌套卡片 |
| 对象 | 键值对列表，键名也用 FIELD_LABEL_LOCALES 国际化 |
| null/undefined | 灰色斜体 "—" |

**Markdown 字段列表**：description, success_criteria, constraints, acceptance, verification, notes, rationale, context, consequences, observation, analysis, mitigation, resolution

**Checklist 字段列表**：acceptance, blocked_by

**元信息字段（不显示在内容区）**：id, type, status, created, updated, closed_at, title, title_en, title_zh

### 3.4 YAML 源码

- 折叠/展开按钮：Code2 图标 + "YAML 源码" + 箭头
- 展开后：react-syntax-highlighter 渲染，YAML 语法 + oneDark 主题
- 显示行号
- 最大高度 400px，可滚动
- 源码由 `objectToYaml()` 函数从对象数据生成（非 JSON.stringify）

## 4. 字段名国际化映射

### 4.1 类型标签

| 类型 | 中文 | 英文 |
|---|---|---|
| intent | 意图 | Intent |
| task | 任务 | Task |
| adr | ADR | ADR |
| pitfall | BUG | Bug |
| memo | 备忘 | Memo |
| profile | 画像 | Profile |
| change | 变更 | Change |

### 4.2 字段名（29 个已映射）

| 字段键 | 中文 | 英文 |
|---|---|---|
| description | 描述 | Description |
| success_criteria | 成功标准 | Success Criteria |
| constraints | 约束 | Constraints |
| acceptance | 验收标准 | Acceptance |
| verification | 验证方式 | Verification |
| notes | 备注 | Notes |
| rationale | 理由 | Rationale |
| context | 背景 | Context |
| consequences | 影响 | Consequences |
| observation | 观察 | Observation |
| analysis | 分析 | Analysis |
| mitigation | 缓解措施 | Mitigation |
| resolution | 解决方案 | Resolution |
| blocked_by | 前置依赖 | Blocked By |
| source_intent | 来源意图 | Source Intent |
| parent_task | 父任务 | Parent Task |
| closure_evidence | 关闭证据 | Closure Evidence |
| transition_reasons | 流转记录 | Transition Reasons |
| options | 选项 | Options |
| decision | 决策 | Decision |
| related_tasks | 关联任务 | Related Tasks |
| related_adrs | 关联 ADR | Related ADRs |
| scope | 范围 | Scope |
| impact | 影响范围 | Impact |
| severity | 严重程度 | Severity |
| category | 分类 | Category |
| tags | 标签 | Tags |
| path | 路径 | Path |
| changes | 变更列表 | Changes |

未映射的字段回退为：`field_key` → `Field Key`（下划线替换+首字母大写）

## 5. 交互

| 操作 | 行为 |
|---|---|
| 点击返回 | 回到 `/objects/{type}` |
| 点击 YAML 折叠按钮 | 展开/收起 YAML 源码 |
| 语言切换 | 类型标签、字段名、元信息标签、YAML 按钮文案跟随切换 |

## 6. API 数据结构

```typescript
interface ObjectDetail {
  summary: { id: string; type: string; status: string };
  data: Record<string, unknown>;  // 完整 YAML 内容
}
```

## 7. 已知问题与改进方向

- [ ] 缺少编辑入口（当前只读）
- [ ] 缺少对象间导航（如从 task 跳转到 blocked_by 的 task）
- [ ] YAML 源码缺少复制按钮
- [ ] 长页面缺少目录/锚点导航
- [ ] 嵌套对象的键名宽度不统一，可考虑对齐
- [ ] 布尔值 true/false 可考虑中英双语（是/否 / Yes/No）
- [ ] 空数组显示 "empty" 未国际化
