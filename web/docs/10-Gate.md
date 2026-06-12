# Gate 确认台

> 路由：`/gate`
> 源码：`web/src/pages/Gate.tsx`
> API：`GET /api/gate`

## 1. 页面目标

确认台用于展示 Human Gate 报告，让用户判断当前项目是否存在确认记录缺失、结构问题或需要人工决策的场景。它是只读检查面，不执行确认写入。

## 2. 当前页面结构

```text
页面标题：Human Gate 确认台
副标题：需要人类决策的确认节点——基于 Code 提供的 Human Gate 报告
生成时间
状态横幅
指标网格：已检查 / Gate 记录 / 结构问题 / 总体状态
确认面板（存在 issue 或 open 时）
需要人工决策提示（degraded 或记录数为 0 时）
全部通过态（closed 时）
```

## 3. 状态横幅

- 使用 `StatusBanner`。
- `closed` 显示全部通过语义。
- `open` 显示需要确认语义。
- 其他状态按 degraded 语义处理。
- 横幅只展示当前派生状态，不写回事实源。

## 4. 指标网格

- 使用 `ldvh-metric-grid` 和 `MetricCard`。
- 四项：
  - 已检查文件数；
  - Gate 记录数；
  - 结构问题数；
  - 总体状态。
- 总体状态通过 `getStatus()` 本地化。

## 5. 确认面板

- 条件：`issueCount > 0` 或 `status === 'open'`。
- 按 issue code 分组。
- 每组展示 code、数量、来源文件、行号和 message。
- “确认”和“暂缓”按钮当前是 disabled 占位，不产生写入。

## 6. 需要人工决策提示

- 条件：`status === 'degraded'` 或记录数为 0，且不显示确认面板时。
- 展示 Gate 记录、检查文件和总体状态。
- 用于提示用户是否需要补录历史 Human Gate 记录。

## 7. 交互

| 操作 | 行为 |
|---|---|
| 进入页面 | 拉取 `/api/gate` 并展示报告 |
| 点击确认/暂缓占位按钮 | 无操作，保持 disabled |
| 切换语言 | 页面标题、状态、指标标签和提示文案同步切换 |

## 8. 实现约束

1. 不把确认台做成可写表单，除非已有 Human Gate 写入合同和确认流程。
2. 不把记录数为 0 解释为“无需 Human Gate”；只能解释为当前项目内未发现记录。
3. 不翻译 Code 输出的 issue message；它属于派生证据内容。
4. 不绕过 Git 文件事实源创建 Web-only 确认状态。
