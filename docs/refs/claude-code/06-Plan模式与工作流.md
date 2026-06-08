# Claude Code Plan 模式与工作流

> 创建日期：2026-06-08
> 来源：Anthropic 官方文档、Claude Code GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.anthropic.com/en/docs/claude-code | https://github.com/anthropics/claude-code

---

## 1. 结论摘要

Claude Code 提供 Plan 模式（只读操作）和多种工作流管理命令。Plan 模式下 Claude 只执行只读操作（Read、Grep、Glob 等），不进行文件修改。工作流命令包括 /plan、/review、/security-review、/loop、/batch、/compact、/context、/rewind 和 /todos。支持 Git Worktree 隔离、会话续接和并行任务执行。

## 2. Plan 模式

通过 --permission-mode plan 或交互模式中 /plan [description] 进入。Plan 模式下 Claude 只执行只读操作（Read、Grep、Glob 等），不进行文件修改。

## 3. 工作流管理命令

| 命令 | 用途 |
|------|------|
| /plan [description] | 进入 Plan 模式并自动启动任务规划 |
| /review | 请求对当前更改进行代码审查 |
| /security-review | 对当前更改执行安全分析 |
| /loop [interval] | 在会话中安排定期任务 |
| /batch | 自动创建 worktree 用于大型并行更改（5-30 个 worktree） |
| /compact [focus] | 压缩上下文以节省 token |
| /context | 可视化上下文使用情况 |
| /rewind | 回退到对话或代码中的上一个检查点 |
| /todos | 列出对话中跟踪的待办事项 |

## 4. Git Worktree 隔离

```bash
# 在隔离的 git worktree 中运行
claude -w feature-x --tmux
```

在 .claude/worktrees/feature-x 创建隔离的 git worktree 并创建 tmux 会话。

## 5. 会话续接

```bash
# 继续最近的会话
claude -c

# 恢复特定会话
claude -r <session-id>

# 派生会话（新 ID，保留历史）
claude -p 'Try a different approach' --resume <id> --fork-session
```

## 6. 并行任务执行

可同时运行多个独立的 Claude 实例处理不同任务（通过 tmux 会话隔离）。

## 7. 上下文窗口健康管理

使用 /context 监控上下文使用情况：

- < 70% —— 正常运行，完整精度
- 70-85% —— 精度开始下降，考虑使用 /compact
- > 85% —— 幻觉风险显著上升，必须使用 /compact 或 /clear

## 8. 与 Trae Spec/Plan 的关键差异

| 能力 | Trae Spec/Plan | Claude Code |
|------|---------------|-------------|
| Spec 工作流 | 三阶段文档组（spec.md/tasks.md/checklist.md） | 不内置，需通过 CLAUDE.md 或 Skills 实现 |
| Plan 工作流 | 生成 plan.md 文档 | /plan 进入只读模式 |
| 代码审查 | 不内置 | /review 和 /security-review |
| 并行执行 | 不支持 | /batch 自动创建 worktree |
| 上下文管理 | 不支持 | /compact、/context、/rewind |
| 会话续接 | 不支持 | -c、-r、--fork-session |

## 9. 待进一步调研

1. /batch 的完整配置和 worktree 管理策略
2. /loop 的定时任务配置和限制
3. /rewind 的检查点粒度和回退范围
