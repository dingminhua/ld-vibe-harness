# Cursor Agent 智能体机制

> 创建日期：2026-06-08
> 来源：Cursor 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.cursor.com/agent

---

## 1. 结论摘要

Cursor Agent 是 Cursor 的自主编程智能体，采用 ReAct（Reasoning + Acting）模式工作，能够理解复杂需求、规划执行步骤、调用工具和自主编辑代码。Agent 可调用 Read File、Write File、Edit File、Search、List Directory、Terminal Command 和 Browser 等内置工具。支持多步骤执行、跨文件操作和自主编辑能力。工具调用受安全机制约束，写操作和终端命令默认需用户确认。

## 2. 官方定位

Cursor Agent 是 Cursor 的自主编程智能体，能够理解复杂需求、规划执行步骤、调用工具、自主编辑代码。它是 Cursor 从"AI 辅助编辑器"向"AI 自主编程"演进的核心能力。

## 3. Agent 工作流程

Agent 采用 ReAct（Reasoning + Acting）模式：

1. **Reasoning**：分析当前状态，决定下一步行动
2. **Acting**：调用工具执行操作
3. **Observation**：观察工具返回结果
4. 循环直到任务完成或需要用户确认

## 4. Agent 工具调用

| 工具 | 功能 | 需确认 |
|------|------|--------|
| Read File | 读取文件内容 | 否 |
| Write File | 创建/覆盖文件 | 是（默认） |
| Edit File | 编辑文件部分内容 | 是（默认） |
| Search | 代码搜索（语义搜索 + 文本搜索） | 否 |
| List Directory | 列出目录内容 | 否 |
| Terminal Command | 执行终端命令 | 是（默认） |
| Browser | 浏览网页 | 否 |

## 5. 多步骤执行

- Agent 可以自主决定执行多少步骤
- 每一步可以选择不同的工具
- Agent 会根据前一步的结果调整后续计划
- 支持跨文件、跨目录的复杂操作
- 有最大步骤数限制（防止无限循环）

## 6. 自主编辑能力

- Agent 可以直接创建、修改、删除文件
- 支持同时编辑多个文件
- 编辑前会读取文件当前内容，确保基于最新状态操作
- 编辑后会验证语法（如 lint 检查）

## 7. 与 Trae Agent 的关键差异

| 能力 | Trae Agent | Cursor Agent |
|------|-----------|--------------|
| 自定义智能体 | 支持配置提示词和工具集 | 不支持自定义 Agent 定义 |
| 多智能体编排 | SOLO Agent 可调用自定义智能体 | 不支持多 Agent 编排 |
| Plan/Spec 模式 | 内置 Plan 和 Spec 工作流 | 不内置 |
| 内置工具 | 5 个（阅读/文件系统/终端/联网搜索/预览） | 7 个（含 Browser） |
| 工具确认机制 | requires_approval 参数 | Accept/Reject 按钮 |

## 8. 待进一步调研

1. Agent 的最大步骤数限制和配置方式
2. Agent 自主编排的决策算法
3. Browser 工具的完整能力和限制
