# Claude Code MCP 模型上下文协议

> 创建日期：2026-06-08
> 来源：Anthropic 官方文档、Claude Code GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.anthropic.com/en/docs/claude-code | https://github.com/anthropics/claude-code

---

## 1. 结论摘要

Claude Code 完整支持 MCP，支持 stdio、HTTP 和 SSE 三种传输协议。MCP Server 可通过 CLI 命令管理，支持 user、local 和 project 三种作用域。工具描述上限为 2KB，结果大小可通过 maxResultSizeChars 注解允许最多 500K 字符。Claude Code 特有功能包括 MCP 资源引用（@github:issue://123）和工具名称语法（mcp__<server>__<tool>）。

## 2. MCP 服务器管理

```bash
# 添加 MCP Server
claude mcp add <name> -- <cmd>

# GitHub 集成
claude mcp add -s user github -- npx @modelcontextprotocol/server-github

# PostgreSQL 查询
claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb

# 列出已配置的 MCP 服务器
claude mcp list

# 移除 MCP 服务器
claude mcp remove <name>
```

## 3. MCP 作用域

| 标志 | 作用域 | 存储位置 |
|------|--------|----------|
| -s user | 全局（所有项目） | ~/.claude.json |
| -s local | 此项目（个人） | .claude/settings.local.json（已 gitignore） |
| -s project | 此项目（团队共享） | .claude/settings.json（git 跟踪） |

## 4. 支持的传输协议

| 传输方式 | 说明 |
|----------|------|
| stdio | 本地进程（最常用） |
| http | 远程服务器 |
| sse | 服务器发送事件（Server-Sent Events） |

## 5. 工具名称语法

在 --allowedTools / --disallowedTools 中引用 MCP 工具：

```
mcp__<server>__<tool>
```

## 6. MCP 限制与调优

- 工具描述：每个服务器的工具描述和服务器指令上限为 2KB
- 结果大小：默认有上限；使用 maxResultSizeChars 注解允许最多 500K 字符的大型输出
- 输出 token：export MAX_MCP_OUTPUT_TOKENS=50000 —— 限制 MCP 服务器的输出以防止上下文泛滥

## 7. 引用 MCP 资源

在对话中引用 MCP 资源：

```
@github:issue://123
```

## 8. Print/CI 模式中的 MCP

```bash
claude --bare -p 'Query database' --mcp-config mcp-servers.json --strict-mcp-config
```

--strict-mcp-config 忽略除 --mcp-config 以外的所有 MCP 服务器。

## 9. 与 Trae MCP 的关键差异

| 能力 | Trae MCP | Claude Code MCP |
|------|----------|-----------------|
| MCP 作用域 | 全局 + 项目级 | user + local + project 三级 |
| MCP 资源引用 | 不支持 | @server:resource 语法 |
| 工具描述限制 | 8000 字符 | 2KB |
| 结果大小控制 | 无明确控制 | maxResultSizeChars + MAX_MCP_OUTPUT_TOKENS |
| CI 模式 | 不适用 | --mcp-config + --strict-mcp-config |
| 配置格式 | JSON（mcp.json） | CLI 命令 + JSON settings |

## 10. 待进一步调研

1. MCP 资源引用的完整语法和支持的资源类型
2. maxResultSizeChars 的配置方式和默认值
3. --strict-mcp-config 的完整行为
