# Trae Hook 机制

> 创建日期：2026-06-16
> 来源：Trae 官方文档（实测验证）、OODER A2UI 团队 Trae Hooks 实测报告（2026-06-15）
> 定位：外部资料引用和机制对照，不直接成为 LDVH 强制规则
> 官方地址：https://docs.trae.cn/ide/rules | https://docs.trae.cn/ide/skills | https://docs.trae.cn/ide/auto-run-and-security
> 重要更新：本文替代旧版 `11-Trae无Hook模拟CodexHook模板问题.md`。Trae 已于 2026 年 6 月正式支持原生 Hook 机制。

---

## 1. 结论摘要

Trae 现已支持原生 Hook 机制，通过 `.trae/hooks.json` 配置文件定义。与旧版文档（2026-06-10）的"Trae 无 Hook"判断不同，当前 Trae 提供了与 Codex lifecycle hooks 等价的生命周期事件能力，包括 `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`Stop` 和 `Notification` 六种事件类型。

Hook 的核心价值在于将"AI 自觉遵守规范"升级为"系统强制执行规范"。实测表明，PreToolUse 可成功拦截危险操作（deny），Stop 可阻止虚假汇报（block），PostToolUse 可发出语法警告（exit code 2）。

但需注意：Trae Hook 与 Codex Hook 在事件完整性、脚本灵活性和安全模型上仍有差异。Trae 当前无 `SubagentStart/Stop`、`PreCompact/PostCompact` 等高级事件，且 Hook 脚本主要依赖平台支持的脚本语言（PowerShell、Bash 等），而非任意可执行文件。

## 2. Hook 配置方式

### 2.1 配置文件

Trae Hook 使用 `.trae/hooks.json` 作为配置文件，位于项目根目录。

### 2.2 配置格式

```json
{
  "hooks": {
    "EventName": [
      {
        "name": "hook-name",
        "enabled": true,
        "matcher": "ToolName|Pattern",
        "command": "bash script.sh",
        "loop_limit": 3
      }
    ]
  }
}
```

### 2.3 配置字段说明

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `name` | 是 | string | Hook 名称，用于标识和错误日志 |
| `enabled` | 是 | boolean | 是否启用该 Hook |
| `matcher` | 否 | string | 工具名匹配模式，`\|` 分隔多工具。空字符串或缺失表示匹配所有 |
| `command` | 是 | string | 要执行的脚本命令 |
| `loop_limit` | 否 | number | Stop 事件专用，阻止停止的最大次数，防止无限循环 |

### 2.4 支持的 Hook 脚本语言

Trae Hook 支持运行系统支持的脚本语言，包括但不限于：
- Bash/Shell（macOS/Linux）
- PowerShell（Windows）
- Python
- Node.js
- 任意系统可执行命令

## 3. 事件类型

### 3.1 Trae 当前支持的 Hook 事件

| 事件 | 触发时机 | 典型用途 | matcher 过滤对象 | 输出语义 |
|---|---|---|---|---|
| `SessionStart` | 会话创建后、首轮对话前 | 注入项目上下文、检测环境状态、写入环境变量 | 不使用 matcher | stdout 注入模型上下文 |
| `UserPromptSubmit` | 用户提交 Prompt 后、模型处理前 | 扫描 Prompt 意图、补充上下文、预处理输入 | 不使用 matcher | 可阻断或附加上下文 |
| `PreToolUse` | 工具调用前 | 检查危险操作、保护关键文件、阻断违规修改 | 工具名（如 `Edit\|Write`、`Bash`） | 返回 JSON 决定 allow/deny |
| `PostToolUse` | 工具调用后 | 审查输出质量、语法验证、统计变更 | 工具名（如 `Edit\|Write`） | exit code 2 警告不阻断、exit code 1 错误阻断 |
| `Stop` | AI 准备结束一轮回答前 | 最终验收、完整性检查、防止虚假汇报 | 当前不使用 matcher | 返回 JSON 决定 block/continuation |
| `Notification` | 特定通知事件 | 构建通知、错误报警 | 工具名模式 | 信息性通知 |

### 3.2 与 Codex Hook 事件对比

| 事件 | Trae | Codex | 说明 |
|---|---|---|---|
| `SessionStart` | 支持 | 支持 | 均支持 matcher: startup/resume/clear/compact |
| `UserPromptSubmit` | 支持 | 支持 | Codex 当前不使用 matcher；Trae 实测可用 |
| `PreToolUse` | 支持 | 支持 | 均支持 deny 语义和 matcher 过滤 |
| `PermissionRequest` | 不支持 | 支持 | Trae 无此独立事件，权限控制通过自动运行设置实现 |
| `PostToolUse` | 支持 | 支持 | 均支持 exit code 2 警告 |
| `Stop` | 支持 | 支持 | 均支持 block/continuation；Trae 额外支持 loop_limit |
| `SubagentStart` | 不支持 | 支持 | Trae 当前无子智能体生命周期事件 |
| `SubagentStop` | 不支持 | 支持 | Trae 当前无子智能体生命周期事件 |
| `PreCompact` | 不支持 | 支持 | Trae 当前无上下文压缩事件 |
| `PostCompact` | 不支持 | 支持 | Trae 当前无上下文压缩事件 |
| `Notification` | 支持 | 不支持 | Trae 独有事件，用于信息通知 |

## 4. Hook 输出语义详解

### 4.1 PreToolUse 输出

PreToolUse Hook 脚本可通过 stdout 返回 JSON 决定是否允许工具调用：

```json
{
  "permissionDecision": "deny",
  "reason": "Detected dangerous pattern: 'bypassBuild'. This operation is not allowed."
}
```

| 字段 | 值 | 含义 |
|---|---|---|
| `permissionDecision` | `"deny"` | 阻断工具调用，拒绝理由写入 stderr 并附加到模型上下文 |
| `permissionDecision` | 其他值或未返回 | 放行工具调用 |

实测中，PreToolUse 成功拦截了：
- 绕过核心构建流程的替代方法
- 直接编辑受保护文件
- 路径越界操作

### 4.2 Stop 输出

Stop Hook 脚本可通过 stdout 返回 JSON 决定是否阻挡停止：

```json
{
  "decision": "block",
  "reason": "Code generation incomplete: Missing Repository interface file. Please fix these issues before completing the task."
}
```

| 字段 | 值 | 含义 |
|---|---|---|
| `decision` | `"block"` | 阻止 AI 结束本轮回答，理由写入模型上下文 |
| `decision` | 其他值或未返回 | 放行停止 |

`loop_limit` 参数控制最大阻止次数。实测中 `loop_limit: 3` 能有效防止无限循环，同时在结构性修复困难时及时放行。

### 4.3 PostToolUse exit code 机制

| exit code | 含义 | 行为 |
|---|---|---|
| 0 | 正常 | 无特殊处理 |
| 1 | 错误 | 阻断操作，stderr 传递给模型 |
| 2 | 警告 | 不阻断操作，但 stderr 传递给模型作为附加上下文 |

exit code 2 特别适合语法验证等场景——既不阻止修改（可能只是部分修改），又让 AI 知晓有问题并立即修复。

### 4.4 SessionStart 上下文注入

SessionStart Hook 脚本可通过两种方式传递上下文给模型：

1. **stdout 输出纯文本**：输出内容自动注入模型作为会话附加上下文
2. **环境变量注入**：通过 `$TRAE_ENV_FILE`（Trae 内置环境变量文件）写入环境变量，后续 Hook 脚本和 RunCommand 均可读取

实测中 SessionStart 成功注入了：
- 项目模块结构
- 服务运行状态（端口检测）
- 工具链可用性（Maven 等）
- API 端点列表

## 5. 重要行为差异与注意事项

### 5.1 PreToolUse 覆盖范围

PreToolUse 的 `matcher` 精准度直接影响性能：
- `matcher: "*"` 或缺失：匹配所有工具调用，性能开销较大
- `matcher: "Edit|Write"`：只匹配文件编辑/写入工具，效率显著提升

注意：PreToolUse 不能覆盖所有 shell 调用、WebSearch 或非 shell/非 MCP 工具。

### 5.2 PostToolUse 不能撤销副作用

PostToolUse 虽然可审查工具输出，但不能撤销已经发生的文件修改或副作用。其警告（exit code 2）只能让 AI 知晓问题并尝试后续修复。

### 5.3 SessionStart 环境变量持久性

通过 `$TRAE_ENV_FILE` 写入的环境变量在整个会话中有效，且在 RunCommand 工具调用中生效。

### 5.4 loop_limit 防止死循环

Stop 事件的 `loop_limit` 是关键的防死循环机制。如果代码生成存在结构性缺陷，AI 可能无法在有限的尝试次数内修复，此时 loop_limit 会放行而非无限阻塞。

### 5.5 与自动运行设置的关系

Trae Hook 与"自动运行 MCP / 自动运行命令"是**独立但互补**的机制：
- Hook：生命周期事件触发，用于检查、阻断和验证
- 自动运行：控制 MCP 工具和命令是否需要人工审批
- Hook 脚本中的命令是否需要审批，仍然受自动运行设置约束

## 6. Hook vs Skill 的区别

| 维度 | Skill（SKILL.md） | Hook（hooks.json） |
|---|---|---|
| 触发方式 | AI 助手主动读取 | 事件自动触发 |
| 执行力 | 建议性（AI 可忽略） | 强制性（可 deny/block） |
| 上下文注入 | 需 AI 主动查询 | 自动注入（SessionStart） |
| 验证时机 | AI 自行决定 | 固定时机（Stop/PostToolUse） |
| 保护能力 | 无（纯文档） | 有（PreToolUse deny） |

Skill 与 Hook 是互补关系：Skill 定义"应该做什么"（规范），Hook 确保"必须这样做"（执行）。

## 7. LDVH 对 Trae Hook 的使用建议

### 7.1 适用范围

Trae Hook 适合以下 LDVH 场景：

1. **会话启动上下文注入**：SessionStart Hook 自动加载项目结构、服务状态和工具链信息，替代手动初始化。
2. **高危操作保护**：PreToolUse Hook 拦截对敏感文件、关键配置或权限文件的直接修改。
3. **修改后质量验证**：PostToolUse Hook 自动检查输出质量（语法、引用、格式）。
4. **任务完成验收**：Stop Hook 在 AI 准备结束任务前执行完整性检查，防止虚假汇报。
5. **构建/通知提醒**：Notification Hook 传递构建状态或错误通知。

### 7.2 限制与不可模拟能力

1. Trae Hook 不支持 `SubagentStart/Stop` 事件，无法自动包裹子智能体生命周期。
2. Trae Hook 不支持 `PreCompact/PostCompact` 事件，无法监听上下文压缩。
3. Trae Hook 不支持 `PermissionRequest` 事件，无法用脚本替代审批决策。
4. PreToolUse 不能覆盖所有 shell 调用，不完全等同于 Codex 的 tool-use guardrail。
5. SessionStart 的 stdout 注入内容有长度限制，过长可能被截断。

### 7.3 安全建议

1. **不建议为 Hook 启用"始终自动运行"**：Hook 脚本中的命令执行仍受自动运行设置约束，开启始终自动运行会跳过所有安全检查。
2. **Hook 脚本来源必须可信**：恶意 Hook 脚本可能导致数据泄露或系统损坏。
3. **实测验证**：配置 Hook 后应实测验证事件是否按预期触发、输出是否被正确处理。
4. **loop_limit 应设置合理上限**：避免因结构性缺陷导致无限循环。

### 7.4 与无 Hook 降级模板的关系

对于 Trae 不支持的 Hook 事件（Subagent、Compact 等），LDVH 仍应使用"无 Hook 降级模板"：用入口规则触发、用 Skill 或 Command 承接步骤、用 checklist 驱动、用 Human Gate 和校验命令收口。

## 8. 实测验证数据参考

参考 OODER A2UI 团队的实测数据（2026-06-15）：

| Hook 名称 | 触发次数 | 拦截/阻止 | 误拦截 | 结果 |
|---|---|---|---|---|
| session-start | 1（每次会话） | 0 | 0 | 通过 |
| nlp-intent-guard | 12 | 0（全部 allow） | 0 | 通过 |
| protect-aggbuilder | 28 | 1 | 0 | 通过 |
| protect-cls-files | 28 | 1 | 0 | 通过 |
| verify-ftl-change | 6 | 1（exit 2 警告） | 0 | 通过 |
| nlp-loop-validation | 3 | 2（block） | 0 | 通过 |
| build-notify | 5 | 0 | 0 | 通过 |

## 9. 待跟踪事项

1. Trae 是否能监听到 `SubagentStart/Stop`、`PreCompact/PostCompact` 等更多事件；
2. Trae Hook 事件的 matcher 精确匹配规则（是否支持 glob、正则或更复杂的模式）；
3. Trae Hook 在不同 Trae 版本（CN 版 vs 国际版）及 SOLO 模式下的事件覆盖范围差异；
4. Trae Hook 脚本的 stdout/stderr 长度限制和截断行为；
5. Trae 官方是否会推出 `/ide/hooks` 专用文档页面。
