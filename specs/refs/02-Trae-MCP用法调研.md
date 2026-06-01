# Trae MCP 用法调研

> 创建日期：2026-05-26
> 来源：Trae 官方文档、Trae 官方论坛 FAQ
> 定位：外部资料引用，不直接成为 LDVH 强制规则

---

## 1. 结论摘要

Trae 中的 MCP（Model Context Protocol）用于把外部工具和服务连接到 Trae IDE。Trae 内的 Agent 作为 MCP Client，可按需向 MCP Server 发起请求，从而调用外部工具能力。

一句话理解：

```text
MCP 不是规则，也不是知识库；MCP 是给 Agent 增加“可调用工具”的协议层。
```

Trae 官方当前支持：

| 维度 | 结论 |
|---|---|
| MCP Server 类型 | stdio、本地/远程 HTTP |
| 传输方式 | stdio、SSE、Streamable HTTP |
| 添加方式 | MCP 市场添加、手动 JSON 配置、项目级 `.trae/mcp.json` |
| 使用位置 | 自定义 Agent 可配置 MCP Server；SOLO Agent 可编排自定义 Agent |
| 安全前提 | MCP Server 多为第三方提供，Trae 不审查或背书，用户需自行判断可信度 |
| 最新能力 | v3.5.51 支持 MCP Server 完整 OAuth 授权流程；v3.5.24/25 支持项目级 MCP |

---

## 2. MCP 的官方定义

Trae 官方说明：Model Context Protocol 是一种允许 LLM 访问自定义工具和服务的协议。Trae 中的智能体作为 MCP Client，可以向 MCP Server 发起请求，使用 MCP Server 暴露的工具。

官方同时强调：

1. MCP Server 由第三方构建和维护。
2. Trae 不审查或认可第三方 MCP Server。
3. Trae 不对 MCP Server 行为、调用失败或返回数据承担责任。
4. 某些 MCP Server 可能因法规、网络限制或服务策略在部分地区不可用。
5. 用户使用 MCP Server 时需自行确保合法合规。

因此，MCP 的引入应按“工具供应链”对待，而不是按普通文档或普通规则对待。

---

## 3. Trae 支持的 MCP Server 类型

| 类型 | 传输协议 | 执行环境 | 典型场景 |
|---|---|---|---|
| stdio | stdio | 本地 | 本地命令启动的 Node/Python MCP Server，例如通过 `npx` 或 `uvx` 启动 |
| HTTP | SSE | 本地 / 远程 | 老式或兼容型 HTTP + SSE 服务 |
| HTTP | Streamable HTTP | 本地 / 远程 | 独立远程 MCP 服务、多客户端连接场景 |

官方协议能力覆盖：

1. Messages：Requests、Responses。
2. Lifecycle：Timeouts。
3. Transports：stdio、Streamable HTTP、HTTP with SSE Backwards Compatibility。
4. Tools：Listing Tools、Calling Tools、List Changed Notification、工具定义与工具结果数据类型。
5. Utilities：Logging。

Trae 对工具定义支持的字段包括：`name`、`title`、`description`、`inputSchema`、`outputSchema`。

Trae 对工具运行结果支持：Text Content、Structured Content。

---

## 4. 添加 MCP Server 的方式

### 4.1 从 MCP 市场添加

官方推荐可以直接从 Trae 内置 MCP 市场添加 MCP Server。

流程：

1. 进入设置中心。
2. 选择 MCP。
3. 点击“添加 > 从市场添加”。
4. 在 MCP 市场选择需要的 MCP Server。
5. 点击右侧 `+`。
6. 在弹窗中填写 MCP Server 配置信息。
7. 点击确认。

注意事项：

1. 标记为 Local 的 MCP Server 通常需要本地已安装 `npx` 或 `uvx`。
2. 配置中的 `env` 信息，例如 API Key、Token、Access Key，需要替换为真实值。
3. 不应把密钥写入可提交的仓库文件。

### 4.2 手动添加

当市场中找不到目标 MCP Server，或需要使用自研 MCP Server 时，可以手动添加。

流程：

1. 进入设置中心。
2. 选择 MCP。
3. 点击“添加 > 手动添加”。
4. 填入 JSON 配置。
5. 确认后 MCP Server 被加入列表。

官方提示：优先使用 NPX 或 UVX 配置。

### 4.3 复用其他 IDE 的配置

如果已经在其他 IDE 配置过 MCP Server，可以点击“原始配置（JSON）”，将 MCP Server JSON 配置粘贴到 Trae 的 `mcp.json` 中。粘贴完成后，MCP 列表会自动添加对应 MCP Server。

---

## 5. 项目级 MCP

Trae 支持项目级 MCP Server。

方式：在项目根目录 `.trae/` 目录中创建 `mcp.json`，声明一个或多个 MCP Server 配置。当需要调用相关能力时，Trae 会自动从该文件加载对应配置。

启用方式：

1. 前往“设置 > MCP”。
2. 打开“启用项目级 MCP”开关。
3. 在弹窗中确认。

官方警告：必须确保工作区内所有项目文件均可信，避免加载恶意 MCP 配置导致安全风险。

LDVH 视角下，项目级 MCP 是强能力入口，至少需要满足：

1. 配置文件不包含明文密钥。
2. 使用的命令和包来源可信。
3. 对外部 API 的权限最小化。
4. 对可写文件、可执行命令、网络访问能力保持审慎。
5. 在团队项目中应明确谁可以修改 `.trae/mcp.json`。

---

## 6. MCP Server 配置格式

### 6.1 stdio 类型

stdio 类型 MCP Server 通过标准输入和标准输出与客户端通信。

字段：

| 字段 | 是否必填 | 说明 |
|---|---|---|
| `command` | 是 | 启动 MCP Server 的可执行命令。必须在系统 PATH 中，或使用完整路径。命令中不能包含空格。 |
| `args` | 否 | 启动命令的参数列表，每个参数必须是字符串。 |
| `env` | 否 | 传递给 MCP Server 的环境变量，每个值必须是字符串。 |

示例：

```json
{
  "mcpServers": {
    "mcp_name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "API_Key": "value"
      }
    }
  }
}
```

### 6.2 HTTP 类型

HTTP 类型 MCP Server 通过 HTTP 或 HTTPS 访问远程服务。

字段：

| 字段 | 是否必填 | 说明 |
|---|---|---|
| `url` | 是 | 远程 MCP Server 的访问地址，需为合法 HTTP/HTTPS URL。 |
| `headers` | 否 | 自定义请求头，可用于鉴权等。 |

示例：

```json
{
  "mcpServers": {
    "mcp_name": {
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer xxxx-xxxxxxx"
      }
    }
  }
}
```

### 6.3 超时配置

Trae 官方 FAQ 提到默认启动和调用超时时间都是 10 分钟，包括 stdio 和 HTTP。

stdio 类型可通过 `env` 设置：

```json
{
  "env": {
    "START_MCP_TIMEOUT_MS": "60000",
    "RUN_MCP_TIMEOUT_MS": "60000"
  }
}
```

HTTP 类型可通过 `headers` 设置：

```json
{
  "headers": {
    "START_MCP_TIMEOUT_MS": "60000",
    "RUN_MCP_TIMEOUT_MS": "60000"
  }
}
```

### 6.4 变量引用

MCP Server 配置支持变量，目前官方说明仅支持 `${workspaceFolder}`。

示例：

```json
{
  "mcpServers": {
    "mcp_name": {
      "command": "node",
      "args": [
        "${workspaceFolder}/plugins/mcp.js"
      ]
    }
  }
}
```

启动时 `${workspaceFolder}` 会被替换为当前项目根目录实际路径。

---

## 7. 在 Agent 中使用 MCP Server

MCP Server 需要添加到 Agent 中，Agent 才能调用其中工具。

官方方式：

1. 在 MCP Server 列表中选择目标 MCP Server。
2. 点击右侧 `+`。
3. 勾选需要添加该 MCP Server 的 Agent。
4. 点击确认。

也可以在创建自定义 Agent 时配置 MCP Server。

自定义 Agent 的工具配置包括：

1. MCP Server。
2. 内置工具：阅读、文件系统、终端、联网搜索、预览。

建议原则：

```text
不要把所有 MCP Server 都加给所有 Agent。
只给某个 Agent 配置它完成职责真正需要的 MCP Server 和工具。
```

这可以减少工具描述占用，也可以降低误调用和安全风险。

---

## 8. MCP 使用限制与常见问题

### 8.1 工具描述和工具数量上限

Trae 官方论坛 FAQ 提到，受模型上下文窗口限制，Trae 为 MCP 信息预留固定空间，存在以下限制：

1. 所有 MCP Server 描述信息字符数上限：8000。
2. 所有 MCP Server 工具数量上限：40。
3. 触达任一上限时，会按工具粒度丢弃装不下的工具信息。

这会导致：

1. 已注册 MCP Server，但模型没有读到某些工具。
2. 即使用户指定调用某个工具，模型也可能无法调用，因为工具描述未进入上下文。

应对策略：

1. 每个 Agent 只启用必要 MCP。
2. 避免同时启用功能重叠的 MCP，例如 Puppeteer 和 Playwright 通常二选一。
3. 关闭低频工具。
4. 把“如何使用工具”的流程放到 Skill，不要依赖 MCP 工具描述承载全部说明。

### 8.2 MCP 响应内容可能被裁剪

官方 FAQ 提到，MCP 工具响应内容大小会被动态裁剪，取决于：

1. 当前模型上下文窗口。
2. 当前对话已有上下文内容。
3. 已使用的 `#File`、`#Doc`、`#Folder` 等上下文。
4. 工具调用次数和历史工具响应内容。

如果空间不足，历史工具调用记录会优先被裁掉。

应对策略：

1. 让 MCP 工具输出摘要和结构化结果，而不是超长全文。
2. 对长结果分段查询。
3. 对重要结果落盘到项目文件，再由 AI 读取文件。
4. 对需要完整保留的数据使用项目事实源，而不是依赖对话历史。

### 8.3 环境依赖问题

常见依赖：

| 依赖 | 用途 | 注意 |
|---|---|---|
| Node.js / npx | 运行 Node 生态 MCP Server | Node 版本建议 >= 18；升级后需重启 Trae |
| Python / uvx | 运行 Python 生态 MCP Server | 需安装 Python 3.8+ 和 uv/uvx |
| Docker | 部分 MCP Server 需要容器隔离 | GitHub MCP Server 等可能需要 Docker |

常见问题：

1. `You must supply a command`：通常是 Node 版本太旧。
2. `cannot find module`、`EACCES`、`~/.npm/_npx` 错误：可能是 npm/npx 缓存损坏，可清理 npm 缓存和 `~/.npm/_npx`。
3. WSL 中只有 node 没有 npm：需要安装 npm，否则 npx 不可用。
4. Figma AI Bridge sharp 模块加载失败：可清理 npx 缓存、重新安装依赖、单独重装 sharp、重启 Trae。

---

## 9. 官方教程中的典型 MCP 场景

### 9.1 Figma AI Bridge

用途：将 Figma 设计稿转化为前端代码。

能力：

1. `get_figma_data`：获取 Figma 设计稿布局信息。
2. `download_figma_images`：下载设计稿中的 SVG/PNG 图像。

使用要点：

1. 需要 Figma Personal Access Token。
2. Token 账号需拥有设计稿访问权限。
3. 建议创建专用 Figma Agent，仅配置 Figma AI Bridge 和必要内置工具。
4. Prompt 中应明确“忠实还原设计稿，不擅自修改设计内容”。

### 9.2 Playwright

用途：网页自动化测试。

能力覆盖：页面导航、截图、点击、表单填写、选择、悬停、执行 JS、获取控制台日志、HTTP 请求、等待响应、获取可见文本/HTML、拖拽、按键、保存 PDF 等。

使用要点：

1. 本地需安装 Python 3、Playwright Python 包及浏览器。
2. 建议创建“网页测试助手”Agent，仅勾选 Playwright MCP。
3. 内置工具可按需开启阅读、编辑、终端、预览、联网搜索。
4. 测试需求应明确 URL 和操作目标。

### 9.3 高德地图 MCP

官方教程列表中包含“使用高德地图 MCP Server 规划行程”。本次抓取页面未获得完整教程正文，但可确定 Trae 官方将其作为 MCP 场景之一，用于地图、路线或行程规划类任务。

---

## 10. 最新版本相关信息

截至本次调研，Trae 官网更新日志中与 MCP 直接相关的变更包括：

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-05-19 | v3.5.59 | 提升终端命令执行稳定性与兼容性 |
| 2026-04-14 | v3.5.51 | MCP Server 支持完整 OAuth 授权流程，包括授权、运行、调用和解除授权 |
| 2026-01-23 | v3.5.24 / v3.5.25 | 支持项目级 MCP |
| 2025-11-11 | v3.0.0 | SOLO 模式全新升级，集成丰富工具，包括 Figma、数据库、AI 服务、部署、支付等 |

对 LDVH 的含义：

1. OAuth MCP 正在成为更正式的远程服务接入方式。
2. 项目级 MCP 可以纳入项目协作资产，但必须有安全边界。
3. 终端执行稳定性仍在持续优化，因此本地 stdio MCP 的失败策略要写清楚。

---

## 11. 信息来源

1. Trae MCP 概览：`https://docs.trae.ai/ide/model-context-protocol?_lang=zh`
2. Trae 添加 MCP Server：`https://docs.trae.ai/ide/add-mcp-servers?_lang=zh`
3. Trae Figma MCP 教程：`https://docs.trae.ai/ide/tutorial-mcp-figma?_lang=zh`
4. Trae Playwright MCP 教程：`https://docs.trae.ai/ide/tutorial-mcp-playwright?_lang=zh`
5. Trae 更新日志：`https://docs.trae.ai/ide/changelog?_lang=zh`
6. Trae 官方论坛 FAQ：`https://forum.trae.cn/t/topic/65`
