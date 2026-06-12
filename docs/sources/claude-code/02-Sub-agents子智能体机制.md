# Claude Code Sub-agents 子智能体机制

> 创建日期：2026-06-08
> 来源：Anthropic 官方文档、Claude Code GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.anthropic.com/en/docs/claude-code | https://github.com/anthropics/claude-code

---

## 1. 结论摘要

Claude Code 支持三种子智能体定义方式：项目级（.claude/agents/）、CLI 标志（--agents）和用户级（~/.claude/agents/）。子智能体通过 Markdown 文件定义，可配置名称、描述、模型和工具集。支持多智能体编排和团队模式（tmux 隔离）。子智能体继承主智能体的工具集，但可在定义中限制，也可指定不同的模型。

## 2. Agent 定义方式

| 方式 | 位置 | 作用域 |
|------|------|--------|
| 项目级 | .claude/agents/ | 团队共享 |
| CLI 标志 | --agents '<json>' | 会话特定，动态 |
| 用户级 | ~/.claude/agents/ | 个人 |

位置优先级：.claude/agents/ > --agents CLI 标志 > ~/.claude/agents/

## 3. 创建 Agent

在 .claude/agents/security-reviewer.md 中定义：

```markdown
---
name: security-reviewer
description: Security-focused code review
model: opus
tools: [Read, Bash]
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication/authorization flaws
- Secrets in code
- Unsafe deserialization
```

调用方式：@security-reviewer review the auth module

## 4. 动态 Agent（通过 CLI）

```bash
claude --agents '{"reviewer": {"description": "Reviews code", "prompt": "You are a code reviewer focused on performance"}}' -p 'Use @reviewer to check auth.py'
```

## 5. Agent 编排

Claude 可以编排多个 agent 的协作流程，例如：

```
Use @db-expert to optimize queries, then @security to audit the changes.
```

## 6. Agent 团队模式

| 标志 | 效果 |
|------|------|
| --teammate-mode <mode> | agent 团队的显示方式：auto、in-process 或 tmux |
| --brief | 启用 SendUserMessage 工具用于 agent 间通信 |

## 7. 子智能体的能力范围

- 子智能体继承主智能体的工具集，但可在定义中通过 tools 字段限制
- 子智能体可指定不同的 model（如用 opus 做深度审查，haiku 做简单任务）
- 子智能体完成时触发 SubagentStop hook

## 8. 与 Trae Agent 的关键差异

| 能力 | Trae Agent | Claude Code |
|------|-----------|-------------|
| 自定义智能体 | 配置提示词和工具集 | Markdown 文件定义，支持模型选择 |
| 多智能体编排 | SOLO Agent 调用自定义智能体 | @agent 语法 + 自然语言编排 |
| 团队模式 | 不支持 | tmux 隔离 |
| 子智能体独立上下文 | 支持 | 支持 |
| 动态创建 | 不支持 | --agents CLI 标志 |

## 9. 待进一步调研

1. 子智能体的最大并发数和资源限制
2. tmux 团队模式的具体配置和使用方式
3. 子智能体间通信的完整协议
