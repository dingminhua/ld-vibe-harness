# Codex CLI MCP 模型上下文协议

> 创建日期：2026-06-08
> 来源：OpenAI 官方文档、Codex CLI GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://openai.github.io/codex/ | https://github.com/openai/codex

---

## 1. 结论摘要

Codex CLI 完整支持 MCP，既是 MCP Client 又是 MCP Server。支持 stdio、HTTP/SSE 和 UDS（Unix Domain Socket）三种传输协议。MCP Server 可通过 CLI 命令或 config.toml 配置。Codex 特有机制包括：沙箱协商（向 MCP Server 通告 sandbox-state）、MCP Elicitation（MCP Server 可发起审批请求）和 Codex 作为 MCP Server 模式。

## 2. 官方定位

MCP（Model Context Protocol）是允许 LLM 访问自定义工具和服务的协议。Codex CLI 完整支持 MCP，可作为 MCP Client 调用外部工具，也可作为 MCP Server 暴露自身能力。

## 3. 配置 MCP Server

### 3.1 CLI 命令

```bash
# 添加 MCP Server
codex mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

# 添加 Context7
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

### 3.2 config.toml 配置

```toml
# stdio transport
[mcp_servers.sequential-thinking]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]

# HTTP transport
[mcp_servers.remote-api]
url = "https://mcp.example.com/mcp"
headers = { Authorization = "Bearer ***" }

# UDS transport
[mcp_servers.local-uds]
transport = "uds"
path = "/tmp/codex-mcp.sock"
```

## 4. 支持的传输协议

| 传输协议 | 配置方式 | 适用场景 |
|----------|----------|----------|
| stdio | command + args | 本地 MCP Server，最常用 |
| HTTP/SSE | url + headers | 远程 MCP Server |
| UDS | transport = "uds" + path | 本地 Unix Domain Socket |

## 5. 工具命名空间隔离

Codex 使用 mcp__<server_name>__<tool_name> 格式隔离不同 MCP Server 的工具：

```
mcp__sequential-thinking__sequentialthinking
mcp__context7__resolve-library-id
mcp__filesystem__read_file
```

## 6. Codex 作为 MCP Server

```bash
# 启动 MCP Server 模式
codex mcp-server
```

其他 Agent 可以通过 MCP 协议调用 Codex 的能力。

## 7. 沙箱协商

Codex 特有机制：向 MCP Server 通告 sandbox-state，Server 需确认遵守沙箱约束。这确保 MCP Server 的操作不会突破 Codex 的沙箱边界。

## 8. MCP Elicitation

MCP Server 可以发起审批请求（AskForApproval UI 组件），与 Codex 的审批机制集成。用户可在 MCP Server 请求时做出审批决策。

## 9. 与 Trae MCP 的关键差异

| 能力 | Trae MCP | Codex MCP |
|------|----------|-----------|
| MCP Server 模式 | 不支持 | 支持（codex mcp-server） |
| UDS 传输 | 不支持 | 支持 |
| 沙箱协商 | 不支持 | 支持 |
| MCP Elicitation | 不支持 | 支持 |
| 配置格式 | JSON（mcp.json） | TOML（config.toml） |
| 平台限制 | description 最多 8000 字符，最多 40 个工具 | 无明确平台限制 |

## 10. 待进一步调研

1. Codex MCP Server 模式暴露的具体工具和能力列表
2. MCP Elicitation 的完整协议细节
3. 沙箱协商的协议格式和 Server 响应要求
