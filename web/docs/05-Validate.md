# Validate 校验

> 路由：`/validate`
> 源码：`web/src/pages/Validate.tsx`
> API：`GET /api/validate`、`GET /api/landing-plan`

## 1. 页面目标

校验页用于展示事实源校验、42 LDVH 落地检查、landing-report、Human Gate 证据消费和落地计划分组视图。页面只展示 Code 派生结果，不执行受控写入。

## 2. 当前页面结构

```text
页面标题：校验
右侧分段控制：校验视图 / 落地计划

校验视图：
  摘要指标：已检查文件 / 错误 / 警告
  LDVH 落地检查：42 检查 / 落地要求 / Human Gate
  剩余缺口 + 能力缺口
  全部通过状态或按文件分组的问题列表

落地计划：
  摘要指标：落地要求总数 / 未关闭缺口 / 来源文件 / HG 缺口
  写入需求提示（如存在）
  按承接区域分组的缺口卡片
  验证计划状态
```

## 3. 校验视图

### 3.1 摘要指标

- 使用 `ldvh-metric-grid`。
- 三项：已检查文件、错误、警告。
- 数字使用 `MetricCard`，错误使用红色 tone。

### 3.2 LDVH 落地检查

- 三张卡片：
  - 42 检查：状态、剩余缺口、检查项、生成时间。
  - 落地要求：open / degraded / needs_human_gate 和 gap total。
  - Human Gate：记录数、检查文件数、问题数。
- 报告失败时使用 `ReportError`，不让页面整体崩溃。

### 3.3 剩余缺口与能力缺口

- 使用双列自适应面板。
- 只展示摘要、证据和建议回写位置。
- 不展开全部规范落地要求正文。

### 3.4 事实校验问题列表

- issues 为空时展示绿色通过态。
- issues 非空时按文件路径分组。
- 每条问题展示级别图标、错误码、级别标签、字段路径和 message。
- message 属于 Code 输出事实，不翻译。

## 4. 落地计划视图

- 数据来自 `/api/landing-plan`。
- 按 `owner_area` 分组展示 proposed actions。
- 每个分组包含：
  - 承接区域标签；
  - gap count；
  - 建议回写目标；
  - 状态分布条；
  - 子类别；
  - remediation 类型（如存在）。
- 底部展示 validation plan 状态。

## 5. 交互

| 操作 | 行为 |
|---|---|
| 点击“校验视图” | 显示事实校验与 LDVH 检查摘要 |
| 点击“落地计划” | 显示按承接区域分组的落地计划 |
| 切换语言 | 页面框架、状态、owner_area、类别、回写目标同步切换 |

## 6. 实现约束

1. 不新增“立即校验”按钮，除非后端提供明确的受控执行合同。
2. 不把派生报告当作事实源；写回只能通过后续 WorkPlan / Human Gate / Git 文件完成。
3. 不展示 raw `owner_area`、`remediation`、`writeback_targets`，必须走本地化映射。
4. 不把校验页拆成多个路由；当前是同一路由内的双视图。

## 7. API 数据结构

```typescript
interface ValidationData {
  summary: { files: number; errors: number; warnings: number };
  issues: ValidationIssue[];
  reports?: {
    landingCheck?: LdvhLandingCheckReport | LdvhReportError;
    landingReport?: LdvhLandingReport | LdvhReportError;
    humanGateReport?: LdvhHumanGateReport | LdvhReportError;
  };
}

interface ValidationIssue {
  level: 'error' | 'warning';
  code: string;
  message: string;
  path: string;
  field?: string;
  suggestion?: string;
}
```
