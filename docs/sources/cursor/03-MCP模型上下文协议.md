# Cursor MCP 模型上下文协议

> 创建日期：2026-06-08
> 来源：Cursor 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.cursor.com/context/model-context-protocol

---

## 1. 结论摘要

Cursor 原生支持 MCP，是首批集成 MCP 的 IDE 之一。支持 stdio 和 SSE 两种传输协议。MCP 配置支持项目级（.cursor/mcp.json）和全局级（Settings 或 ~/.cursor/mcp.json），项目级覆盖全局同名配置。MCP 服务器提供的工具会自动出现在 Agent 的可用工具列表中，调用同样受安全机制约束。

## 2. 官方定位

MCP（Model Context Protocol）是 Anthropic 提出的开放标准协议，允许 AI 模型通过标准化接口与外部工具和数据源交互。Cursor 原生支持 MCP。

## 3. 项目级 MCP 配置

文件位置：项目根目录 .cursor/mcp.json

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "xxx"
      }
    },
    "remote-api": {
      "url": "https://mcp.example.com/sse"
    }
  }
}
```

## 4. 全局 MCP 配置

- 配置位置：Cursor Settings > MCP（或 ~/.cursor/mcp.json）
- 格式与项目级相同
- 对所有项目生效

## 5. 支持的传输协议

| 协议 | 配置方式 | 说明 |
|------|----------|------|
| stdio | command + args | 本地进程通信，最常用 |
| SSE (Server-Sent Events) | url | 远程 HTTP 服务器，通过 SSE 长连接通信 |

stdio 配置示例：

```json
{
  "mcpServers": {
    "my-tool": {
      "command": "python3",
      "args": ["-m", "my_mcp_server"],
      "env": {"API_KEY": "xxx"}
    }
  }
}
```

SSE 配置示例：

```json
{
  "mcpServers": {
    "remote-tool": {
      "url": "https://api.example.com/mcp/sse"
    }
  }
}
```

## 6. 项目级 vs 全局 MCP

| 维度 | 项目级 .cursor/mcp.json | 全局 Settings |
|------|--------------------------|---------------|
| 作用域 | 仅当前项目 | 所有项目 |
| 团队共享 | 可提交到 Git，团队共享 | 仅本地 |
| 典型用途 | 项目特定工具 | 通用工具 |
| 优先级 | 项目级覆盖全局同名配置 | - |

## 7. MCP 工具在 Agent 中的使用

- MCP 服务器提供的工具会自动出现在 Agent 的可用工具列表中
- Agent 可以像调用内置工具一样调用 MCP 工具
- MCP 工具调用同样受安全机制约束（可能需要用户确认）

## 8. 与 Trae MCP 的关键差异

| 能力 | Trae MCP | Cursor MCP |
|------|----------|------------|
| 传输协议 | stdio + HTTP+SSE + Streamable HTTP | stdio + SSE |
| 配置格式 | JSON（mcp.json） | JSON（mcp.json） |
| 项目级配置 | .trae/mcp.json | .cursor/mcp.json |
| 全局配置 | Settings | Settings 或 ~/.cursor/mcp.json |
| Streamable HTTP | 支持 | 不支持 |
| 平台限制 | description 最多 8000 字符，最多 40 个工具 | 无明确平台限制 |

## 9. 待进一步调研

1. Cursor 是否已支持 Streamable HTTP 传输协议
2. MCP 工具在 Agent 中的权限控制细节
3. 项目级与全局 MCP 的合并策略
