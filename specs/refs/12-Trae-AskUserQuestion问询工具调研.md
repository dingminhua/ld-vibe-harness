# Trae AskUserQuestion 调研

> 创建日期：2026-06-01
> 来源：基于 Trae 官方文档、社区深度分析和平台实际验证
> 定位：外部资料引用与平台机制调研，不直接成为 LDVH 强制规则

---

## 1. 结论摘要

AskUserQuestion 是 Trae IDE 提供给 AI 的交互式问询工具，用于在关键决策点暂停 AI 执行，通过 UI 弹窗向用户展示选择题，用户点击选项后，选择结果作为 `toolcall_result` 返回给 AI，直接影响后续执行路径。

| 维度 | 核心结论 |
|---|---|
| 工具性质 | 平台内置工具，非所有 AI 模型都具备此能力；是 Trae IDE 本地执行环境的一部分 |
| 调用方 | AI（assistant 角色）通过工具调用请求发起，Trae IDE 本地渲染 UI 弹窗 |
| 用户交互 | 弹窗展示问题标题、描述、选项（单选/多选），用户点击选择后提交 |
| 返回值 | 用户选择结果作为 tool 角色的消息返回给 AI，进入下一轮 HTTP 请求 |
| 与 requires_approval 的关系 | `RunCommand` 设置 `requires_approval: true` 时，底层通过 AskUserQuestion 实现用户确认流程 |

---

## 2. 参数契约

```json
{
  "tool": "AskUserQuestion",
  "parameters": {
    "questions": [{
      "question": "发现冲突，请选择处理方式：",
      "header": "冲突解决",
      "multiSelect": false,
      "options": [
        {"label": "覆盖", "description": "用新代码覆盖现有代码"},
        {"label": "跳过", "description": "保留现有代码，跳过此修改"},
        {"label": "手动合并", "description": "弹出差异让我手动决定"}
      ]
    }]
  }
}
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `questions` | array | 是 | 问题列表，可包含 1-4 个问题 |
| `questions[].question` | string | 是 | 问题描述，以问号结尾 |
| `questions[].header` | string | 是 | 问题标签，显示为 chip/tag，最多 12 字符 |
| `questions[].multiSelect` | boolean | 否 | 是否允许多选，默认 false（单选） |
| `questions[].options` | array | 是 | 选项列表，2-4 个选项 |
| `questions[].options[].label` | string | 是 | 选项显示文本，1-5 词 |
| `questions[].options[].description` | string | 是 | 选项说明，解释选择该选项的后果 |

### 约束条件

| 约束 | 说明 |
|---|---|
| 问题数量 | 1-4 个问题 per call |
| 选项数量 | 每个问题 2-4 个选项 |
| 选项互斥 | `multiSelect: false` 时只能选一个 |
| header 长度 | 最多 12 字符 |
| label 长度 | 1-5 词 |

---

## 3. 用户交互流程

```
┌─────────────────────────────────────────────┐
│ 1. AI 决定需要用户输入                        │
│    → 调用 AskUserQuestion 工具                │
├─────────────────────────────────────────────┤
│ 2. Trae IDE 本地渲染弹窗                      │
│    → 展示问题标题、描述、选项                  │
├─────────────────────────────────────────────┤
│ 3. 用户点击选项并提交                         │
│    → IDE 捕获用户选择                        │
├─────────────────────────────────────────────┤
│ 4. IDE 将选择结果封装为 tool 消息              │
│    → 连同完整对话历史再次发送给 AI            │
├─────────────────────────────────────────────┤
│ 5. AI 根据用户选择继续执行                    │
│    → 不同选择导致不同执行路径                 │
└─────────────────────────────────────────────┘
```

### 返回值格式

用户选择后，IDE 将结果作为 tool 角色的消息返回：

```json
{
  "role": "tool",
  "tool_call_id": "call_xxx",
  "content": "{\"question\": \"发现冲突，请选择处理方式：\", \"answer\": \"覆盖\"}"
}
```

---

## 4. 使用场景

| 场景 | 示例 |
|---|---|
| 技术选型 | "选择前端框架：React / Vue / Angular" |
| 冲突解决 | "发现代码冲突，选择处理方式：覆盖 / 跳过 / 手动合并" |
| 方案确认 | "选择实现方案：方案 A（简单但性能差）/ 方案 B（复杂但性能好）" |
| 风险评估 | "此变更影响 5 个文件，是否继续？继续 / 暂停 / 查看影响详情" |
| 模式选择 | "选择执行模式：快速原型 / 生产级实现 / 仅做计划" |

### 与 RunCommand 的关联

`RunCommand` 工具设置 `requires_approval: true` 时，底层通过 AskUserQuestion 实现用户确认流程：

```json
{
  "tool": "RunCommand",
  "parameters": {
    "command": "npm run deploy",
    "requires_approval": true
  }
}
```

### 与 NotifyUser 的区别

| 工具 | 作用 | 是否有选项 | 是否有返回值 |
|---|---|---|---|
| `AskUserQuestion` | 向用户提问，等待用户选择 | 是 | 是，用户选择结果 |
| `NotifyUser` | 通知用户审阅结果，等待用户确认 | 否 | 是，用户确认信号 |

---

## 5. 平台适配性

| 平台 | 是否提供 AskUserQuestion | 替代方案 |
|---|---|---|
| Trae IDE | 提供 | 无 |
| Cursor | 不提供 | 对话询问 |
| GitHub Copilot | 不提供 | 对话询问 |
| Claude Desktop | 不提供 | 对话询问 |
| 其他 AI 编程工具 | 多数不提供 | 对话询问 |

---

## 6. 问题设计最佳实践

| 原则 | 说明 |
|---|---|
| 问题明确 | 以问号结尾，描述清晰，不含糊 |
| 选项互斥 | 各选项之间不重叠，用户能明确区分 |
| 后果说明 | 每个选项的 description 说明选择后果 |
| 数量适中 | 2-4 个选项，不超过 4 个 |
| 推荐标注 | 如需推荐某选项，在 label 末尾添加 "(推荐)" |

### 多问题批量询问

当需要同时确认多个独立决策时，可在一次调用中包含多个问题：

```json
{
  "tool": "AskUserQuestion",
  "parameters": {
    "questions": [
      {
        "question": "选择前端框架：",
        "header": "前端",
        "options": [
          {"label": "React", "description": "使用 React 18 + Hooks"},
          {"label": "Vue", "description": "使用 Vue 3 + Composition API"}
        ]
      },
      {
        "question": "选择状态管理方案：",
        "header": "状态",
        "options": [
          {"label": "Zustand", "description": "轻量级状态管理"},
          {"label": "Redux", "description": "成熟但复杂"}
        ]
      }
    ]
  }
}
```

---

## 7. 取消与超时处理

### 用户取消行为

实际验证发现：用户在 AskUserQuestion 弹窗中点击取消时，系统返回的 answer 为 `暂停`（对应取消操作），而非空值或 null。

| 用户行为 | 返回结果 |
|---|---|
| 点击选项 | `{"answer": "选项 label"}` |
| 点击取消 | `{"answer": "暂停"}` 或类似取消标识 |
| 超时未操作 | 取决于平台实现 |

### 取消后的降级建议

用户取消问询后，建议遵循以下规则：

| 策略 | 说明 |
|---|---|
| 不重复追问 | 用户已表达"不想选择"，不应再次弹出相同问询 |
| 进入默认路径 | 如有默认选项，自动执行默认路径 |
| 暂停等待指示 | 如无法确定默认路径，暂停并等待用户下一步指示 |

### 设计问询时的取消友好原则

| 原则 | 说明 |
|---|---|
| 选项覆盖完整 | 确保 2-4 个选项覆盖所有合理选择，减少用户取消动机 |
| 取消即暂缓 | 将取消行为理解为"暂缓执行，等待用户主动指示" |
| 避免二选一强迫 | 如果只有两个选项且用户都不想要，更容易触发取消 |

### 实际验证案例

验证场景：演示 AskUserQuestion 工具，提供"轻量模式 / Agent 模式 / 暂停"三个选项。

用户行为：点击取消。

系统返回：`answer: "暂停"`。

期望行为：AI 理解取消信号后，应暂停执行并等待用户下一步指示。

---

## 8. 调研信息来源

| 来源 | 类型 | 关键信息 |
|---|---|---|
| CSDN：理解Trae——从系统消息、工具调用到协作模式 | 社区深度分析 | AskUserQuestion 参数契约、工作原理、与 requires_approval 的关系、工具调用流程 |
| Trae IDE 工具定义（本系统） | 平台工具定义 | questions 数组、question/header/multiSelect/options 参数、1-4 问题、2-4 选项约束 |
| 平台实际验证 | 实践验证 | AskUserQuestion 弹窗交互、用户选择返回格式 |

---

## 9. 待进一步调研

1. AskUserQuestion 是否支持动态选项（根据上下文生成选项）
2. AskUserQuestion 是否支持图片、代码片段等多媒体内容嵌入问题描述
3. 多选模式下返回值的格式（数组还是逗号分隔字符串）
4. 子 Agent 是否可以调用 AskUserQuestion（还是只能由主控 AI 调用）
5. AskUserQuestion 是否有调用频率限制
