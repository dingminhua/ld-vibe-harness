# Cursor Composer 与编辑模式

> 创建日期：2026-06-08
> 来源：Cursor 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.cursor.com/agent

---

## 1. 结论摘要

Cursor Composer 是多文件 AI 编辑界面，支持 Agent 模式和 Normal 模式。Agent 模式下 AI 自主规划、多步骤执行、可调用所有工具；Normal 模式下按用户指令单步操作，仅支持代码生成/编辑。两种模式都支持多文件编辑，以 diff 形式展示修改。上下文管理分为自动上下文（Agent 模式）和手动上下文（Normal 模式，通过 @files 等引用）。

## 2. Composer 概述

Composer 是 Cursor 的多文件 AI 编辑界面，支持在同一个会话中对多个文件进行 AI 辅助编辑。它是 Cursor 的核心编辑功能入口。

## 3. 两种模式

| 维度 | Agent 模式 | Normal 模式 |
|------|-----------|-------------|
| 自主性 | 高：自主规划、多步骤执行 | 低：按用户指令单步操作 |
| 工具调用 | 可调用所有工具（文件、终端、搜索等） | 仅代码生成/编辑 |
| 多文件编辑 | 支持，自主决定编辑哪些文件 | 支持，但需用户指定 |
| 终端访问 | 可以执行命令 | 不可以 |
| 上下文理解 | 深度：可搜索、读取项目文件 | 浅层：依赖用户提供的上下文 |
| 适用场景 | 复杂任务、跨文件重构、新功能开发 | 简单修改、单文件编辑、代码补全 |
| 确认机制 | 每步操作可确认（Yolo 模式除外） | 直接生成 diff |

## 4. 多文件编辑

- Composer 支持在单个会话中编辑多个文件
- Agent 模式下，Agent 自主决定需要编辑哪些文件
- Normal 模式下，用户通过 @files 引用或手动添加文件
- 每个文件的修改以 diff 形式展示
- 支持逐文件 Accept/Reject

## 5. 上下文管理

### 5.1 自动上下文（Agent 模式）

- Agent 自主搜索和读取相关文件
- 通过语义搜索理解代码库结构
- 自动加载匹配的 Project Rules

### 5.2 手动上下文（Normal 模式）

| 引用方式 | 描述 |
|----------|------|
| @files | 引用特定文件 |
| @folders | 引用整个目录 |
| @code | 引用代码片段 |
| @docs | 引用文档 |
| @web | 引用网页内容 |

### 5.3 上下文窗口

- Cursor 使用长上下文模型
- 过多上下文可能影响响应质量
- 建议只引用必要的内容

## 6. 与 Trae 编辑模式的对比

| 能力 | Trae | Cursor |
|------|------|--------|
| 多文件编辑 | Agent 模式支持 | Composer 支持 |
| 编辑确认 | Apply/Reject 按钮 | Accept/Reject 按钮 |
| 上下文引用 | #File/#Folder/#Doc 等 | @files/@folders/@code 等 |
| Normal 模式 | Chat 智能体 | Composer Normal 模式 |
| Agent 模式 | Agent/SOLO Agent | Composer Agent 模式 |

## 7. 待进一步调研

1. Composer 的上下文窗口大小和限制
2. Agent 模式与 Normal 模式的模型选择差异
3. @docs 引用的文档索引机制
