# Claude Code Hooks 与扩展机制

> 创建日期：2026-06-08
> 来源：Anthropic 官方文档、Claude Code GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.anthropic.com/en/docs/claude-code | https://github.com/anthropics/claude-code

---

## 1. 结论摘要

Claude Code 提供 8 种 Hook 类型，覆盖从会话启动到子智能体完成的完整生命周期。PreToolUse Hook 支持通过 updatedInput 修改工具输入参数，并可通过 permissionDecision 控制权限决策（allow/deny/ask/defer）。多 Hook 并发运行时，权限决策优先级为 deny > ask > allow > defer。还支持自定义斜杠命令（.claude/commands/）和自然语言触发的 Skills（.claude/skills/）。

## 2. 全部 8 种 Hook 类型

| Hook | 触发时机 | 常见用途 |
|------|----------|----------|
| UserPromptSubmit | Claude 处理用户 prompt 之前 | 输入验证、日志记录 |
| PreToolUse | 工具执行之前 | 安全门控、阻止危险命令 |
| PostToolUse | 工具完成之后 | 自动格式化代码、运行 linter |
| Notification | 权限请求或等待输入时 | 桌面通知、告警 |
| Stop | Claude 完成响应时 | 完成日志记录、状态更新 |
| SubagentStop | 子 agent 完成时 | Agent 编排 |
| PreCompact | 上下文记忆被清除之前 | 备份会话转录 |
| SessionStart | 会话开始时 | 加载开发上下文 |

## 3. Hook 配置

在 .claude/settings.json（项目）或 ~/.claude/settings.json（全局）中：

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write(*.py)",
      "hooks": [{"type": "command", "command": "ruff check --fix $CLAUDE_FILE_PATHS"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'rm -rf'; then echo 'Blocked!' && exit 2; fi"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "echo 'Claude finished a response' >> /tmp/claude-activity.log"}]
    }]
  }
}
```

## 4. Hook 环境变量

| 变量 | 内容 |
|------|------|
| CLAUDE_PROJECT_DIR | 当前项目路径 |
| CLAUDE_FILE_PATHS | 正在修改的文件 |
| CLAUDE_TOOL_INPUT | 工具参数（JSON 格式） |

## 5. PreToolUse Hook 的高级能力：updatedInput

PreToolUse hook 可以通过 stdout 返回 JSON 来修改工具输入：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "auto-decided by preference",
    "updatedInput": {},
    "additionalContext": "optional context for Claude"
  }
}
```

permissionDecision 值：

- allow —— 继续，可选附带 updatedInput
- deny —— 阻止（反馈给 Claude）
- ask —— 升级给用户
- defer —— 让权限流程继续

## 6. 多 Hook 并发

所有匹配的 hook 并行运行，permissionDecision 优先级为 deny > ask > allow > defer（最严格的胜出）。

## 7. Matcher 语法

matcher 字段支持 JS 正则语法（当包含正则元字符时）。纯字母/下划线为精确匹配。覆盖原生 + MCP 变体的写法：

```
"matcher": "(AskUserQuestion|mcp__.*__AskUserQuestion)"
```

## 8. 自定义斜杠命令

创建 .claude/commands/<name>.md（项目共享）或 ~/.claude/commands/<name>.md（个人）：

```markdown
# .claude/commands/deploy.md
Run the deploy pipeline:
1. Run all tests
2. Build the Docker image
3. Push to registry
4. Update the $ARGUMENTS environment (default: staging)
```

用法：/deploy production —— $ARGUMENTS 被用户输入替换。

## 9. Skills（自然语言触发）

与斜杠命令不同，.claude/skills/ 中的 skill 是 markdown 指南，当任务匹配时 Claude 通过自然语言自动调用：

```markdown
# .claude/skills/database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```

## 10. 与 Trae 机制的关键差异

| 能力 | Trae | Claude Code |
|------|------|-------------|
| Hook 机制 | 不支持 | 8 种 Hook 类型 |
| 工具输入修改 | 不支持 | PreToolUse updatedInput |
| 权限决策 Hook | 不支持 | permissionDecision (allow/deny/ask/defer) |
| 自定义命令 | Commands 斜杠命令 | .claude/commands/ + $ARGUMENTS |
| 自然语言技能 | Skills（SKILL.md） | .claude/skills/ |

## 11. 待进一步调研

1. Hook 命令的完整环境变量列表
2. updatedInput 的 shallow-merge 行为细节
3. Skills 的自动触发匹配机制和优先级
