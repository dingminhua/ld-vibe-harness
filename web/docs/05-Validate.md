# Validate 校验

> 路由：`/validate`
> 源码：`web/src/pages/Validate.tsx`
> API：`GET /api/validate`

## 1. 页面目标

让用户快速了解 `ldvh-base/` 下所有 YAML 文件的校验结果，并看到 42 LDVH落地与检查、landing-report 和 Human Gate 证据消费的当前摘要。页面数据由 Code 工具 `python3 tools/specs_validate.py web-validate --format json` 生成，Web API 只负责调用并返回该合同。

## 2. 布局结构

```
┌─────────────────────────────────────────┐
│ 页面标题：校验 / Validation              │
├─────────────────────────────────────────┤
│ 摘要卡片（三列）                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │📄 已检查  │ │❌ 错误   │ │⚠️ 警告   │ │
│ │  12      │ │  2       │ │  3       │ │
│ │ 文件     │ │ 错误     │ │ 警告     │ │
│ └──────────┘ └──────────┘ └──────────┘ │
├─────────────────────────────────────────┤
│ LDVH 落地检查摘要                        │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │42 检查   │ │落地要求  │ │HumanGate │ │
│ │ open     │ │ 77 gaps  │ │ 0 records│ │
│ └──────────┘ └──────────┘ └──────────┘ │
│ 剩余缺口 / 能力缺口                      │
├─────────────────────────────────────────┤
│ 问题列表（按文件分组）                   │
│ ┌─────────────────────────────────────┐ │
│ │ tasks/task-0001.yaml                │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ ❌ MISSING_FIELD  错误 → status │ │ │
│ │ │ status 字段缺失                 │ │ │
│ │ └─────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ ⚠️ INVALID_STATUS 警告 → type   │ │ │
│ │ │ 状态值不在允许范围内             │ │ │
│ │ └─────────────────────────────────┘ │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 3. 区域详细设计

### 3.1 摘要卡片

- 三列等宽网格
- 已检查文件：FileWarning 图标 + 数字 + "已检查文件 / Files Checked"
- 错误：AlertCircle 红色图标 + 红色数字 + "错误 / Errors"
- 警告：AlertTriangle 黄色图标 + 黄色数字 + "警告 / Warnings"

### 3.2 问题列表

- 按文件路径分组
- 每组：文件路径（等宽字体，标题）+ 问题条目列表
- 每条问题：
  - 左侧：错误图标（红）/ 警告图标（黄）
  - 错误码（等宽加粗）
  - 级别标签（错误/警告，中英切换）
  - 字段路径（如有，`→ field_name`）
  - 问题描述

### 3.3 全部通过

- 条件：issues 为空
- 显示：CheckCircle 绿色大图标 + "所有校验通过" + "未发现错误或警告"

### 3.4 LDVH 落地检查摘要

- 42 检查：由 `web-validate` 合同中的 `reports.landingCheck` 提供，展示状态、剩余缺口数和检查项数量。
- 落地要求：由 `web-validate` 合同中的 `reports.landingReport` 提供，展示 open、degraded、needs_human_gate 和 gap total。
- Human Gate：由 `web-validate` 合同中的 `reports.humanGateReport` 提供，展示记录数、检查文件数和问题数。
- 剩余缺口和能力缺口只展示摘要、证据和建议回写位置，不展开全部规范落地要求。

## 4. 交互

| 操作 | 行为 |
|---|---|
| 语言切换 | 页面标题、摘要标签、级别标签跟随切换 |

## 5. API 数据结构

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
}
```

## 6. 已知问题与改进方向

- [ ] 缺少"重新校验"按钮
- [ ] 问题条目不可点击跳转到对象详情
- [ ] 缺少按级别筛选（只看错误/只看警告）
- [ ] 文件路径可考虑只显示相对路径（去掉 ldvh-base/ 前缀）
- [ ] 缺少校验规则的说明链接
- [ ] 42 派生报告目前只读展示，不执行受控写入
- [ ] Human Gate 记录数为 0 时只能说明当前项目内未发现记录，不能代表没有任何应触发 Gate 的历史场景
