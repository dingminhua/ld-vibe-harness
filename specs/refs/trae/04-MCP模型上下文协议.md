# Trae MCP 模型上下文协议

> 创建日期：2026-06-04
> 来源：Trae 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.trae.cn/ide/model-context-protocol | https://docs.trae.cn/solo/mcp-overview

---

## 1. 结论摘要

MCP（Model Context Protocol）是一种允许 LLM 访问自定义工具和服务的协议。Trae 中的智能体作为 MCP 客户端，可向 MCP Server 发起请求使用其提供的工具。MCP Server 支持 stdio、HTTP+SSE、Streamable HTTP 三种传输协议，可通过市场添加、手动添加和项目级 mcp.json 三种方式配置。SOLO 独立端区分全局/项目级 MCP 和本地/云端运行环境。平台限制为：单个 MCP Server description 最多 8000 字符，最多暴露 40 个工具。

## 2. 官方定位

MCP（Model Context Protocol）是一种协议，允许大型语言模型（LLMs）访问自定义的工具和服务。Trae 中的智能体作为 MCP 客户端，可向 MCP Server 发起请求以使用其提供的工具。用户可自行添加 MCP Server，并添加到自定义的智能体中使用。

## 3. MCP Server 类型

| 类型 | 传输协议 | 执行环境 |
|---|---|---|
| stdio | stdio | 本地 |
| HTTP | SSE | 本地 / 远程 |
| HTTP | Streamable HTTP | 本地 / 远程 |

## 4. 添加 MCP Server

支持以下三种方式：

1. **从 MCP 市场添加**：设置 > MCP > 添加 > 从市场添加，在市场中找到所需 Server 并点击 + 安装
2. **手动添加**：设置 > MCP > 添加 > 手动添加，填入 JSON 配置内容；也可点击"原始配置（JSON）"按钮，将配置粘贴至 mcp.json 文件
3. **项目级 MCP**：在项目根目录 `.trae/` 下创建 `mcp.json` 文件声明 MCP Server 配置，Trae 会在需要时自动加载

## 5. stdio 类型配置格式

| 字段 | 是否必填 | 描述 |
|---|---|---|
| command | 是 | 启动 MCP Server 的可执行命令，须位于系统 PATH 或使用完整路径；不能包含空格 |
| args | 否 | 启动命令的参数列表，每个参数须为字符串 |
| env | 否 | 传递给 MCP Server 的环境变量，每个值须为字符串 |

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "API_Key": "value"
      }
    }
  }
}
```

## 6. HTTP 类型配置格式

| 字段 | 是否必填 | 描述 |
|---|---|---|
| url | 是 | 远程 MCP Server 的访问地址，须为合法 HTTP/HTTPS URL |
| headers | 否 | 自定义 HTTP 请求头，如鉴权信息等 |

```json
{
  "mcpServers": {
    "server-name": {
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer xxxx-xxxxxxx"
      }
    }
  }
}
```

## 7. 超时配置

stdio 类型通过 `env` 字段设置，HTTP 类型通过 `headers` 字段设置：

- `START_MCP_TIMEOUT_MS`：启动 MCP Server 的超时时间（单位 ms）
- `RUN_MCP_TIMEOUT_MS`：调用 MCP Server tools 的超时时间（单位 ms）

## 8. 变量引用

配置支持 `${workspaceFolder}` 变量，启动时自动替换为当前项目的实际根目录路径：

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${workspaceFolder}/plugins/mcp.js"]
    }
  }
}
```

## 9. 在智能体中使用 MCP

创建自定义智能体时，可在"工具"配置中添加一个或多个 MCP Server。智能体在处理需求时可调用 MCP Server 提供的工具。

## 10. MCP 协议能力

| 类别 | 功能 | 描述 |
|---|---|---|
| Messages | Requests | 客户端或服务器发起操作的请求 |
| Messages | Responses | 回复请求，包含结果或错误信息 |
| Lifecycle | Timeouts | 为请求设置超时机制，防止连接挂起 |
| Transports | stdio | 通过 stdin/stdout 交换 JSON-RPC 2.0 消息 |
| Transports | Streamable HTTP | HTTP POST/GET 请求，可选 SSE 流式发送 |
| Transports | HTTP+SSE Backwards Compatibility | 向后兼容已弃用的 HTTP+SSE 传输 |
| Tools | Listing Tools | 客户端发送 tools/list 请求发现可用工具，支持分页 |
| Tools | Calling Tools | 客户端发送 tools/call 请求调用工具 |
| Tools | List Changed Notification | 工具列表变化时服务器发送通知 |
| Tools | Data Types | 标准化工具能力及结果的描述方式 |
| Utilities | Logging | 服务器向客户端发送结构化日志消息 |

## 11. 工具定义字段

- **name**：工具名称
- **title**：工具标题
- **description**：工具描述
- **inputSchema**：输入参数 Schema
- **outputSchema**：输出结果 Schema

## 12. 工具运行结果类型

- **Text Content**：文本内容
- **Structured Content**：结构化内容

## 13. SOLO 独立端特性

| MCP 类型 | 适用范围 | 适用客户端 |
|---|---|---|
| 全局 MCP | 可在所有项目与任务中使用 | SOLO 网页版、桌面版 |
| 项目级 MCP | 仅可在当前项目中使用，仅对本地任务生效 | SOLO 桌面版 |

| 运行环境 | 适用任务 | 适用客户端 |
|---|---|---|
| 本地 | 仅对本地任务生效 | SOLO 桌面版 |
| 云端 | 仅对云端任务（及从 GitHub 拉取的项目）生效 | SOLO 网页版、桌面版 |

## 14. 平台限制

- MCP Server description 字段最多 8000 字符
- 单个 MCP Server 最多暴露 40 个工具
