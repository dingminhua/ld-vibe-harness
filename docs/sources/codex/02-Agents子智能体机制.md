# Codex CLI Agents 子智能体机制

> 创建日期：2026-06-08
> 来源：OpenAI 官方文档、Codex CLI GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://openai.github.io/codex/ | https://github.com/openai/codex

---

## 1. 结论摘要

Codex CLI 提供会话分叉（/fork）、Codex Cloud 并行任务、MCP 多 Agent 编排和非交互式执行（codex exec）四种子智能体协作方式。/fork 从当前会话创建独立分支；Codex Cloud 支持多任务并行沙箱执行并自动生成 PR；Codex 可同时作为 MCP Server 和 Client 实现跨 Agent 调度；codex exec 支持后台执行和会话恢复。Codex 还支持原生插件系统，可安装 Linear、GitHub 等集成。

## 2. 会话分叉：/fork

- 从当前会话的历史创建新分支
- 分叉出的会话继承当前会话的上下文，但后续独立运行
- 适用于多角色思考中"每个角色独立分析"的场景

## 3. Codex Cloud 并行任务

- 支持同时派发多个独立任务
- 每个任务在独立云端沙箱容器中运行
- 可并行派发多任务
- 自动生成 PR

## 4. MCP 多 Agent 编排

- Codex 自身可作为 MCP Server（codex mcp-server），其他 Agent 可以通过 MCP 调用 Codex
- Codex 也可作为 MCP Client 调用其他 Agent 提供的工具
- 工具命名空间隔离：mcp__<server_name>__<tool_name>

## 5. 非交互式执行：codex exec

| 命令 | 说明 |
|------|------|
| codex exec "prompt" | 单次执行，完成后退出 |
| codex exec --full-auto "prompt" & | 后台执行 |
| codex exec resume <session-id> "prompt" | 恢复之前的会话 |

- 支持 --json 输出 JSONL 事件流，用于解析推理轨迹和工具调用
- 支持 resume 恢复之前的会话，保持上下文连续性

## 6. 原生插件系统

```bash
# 添加插件市场
codex plugin marketplace add openai-curated

# 安装插件
codex plugin install <plugin-name>
```

已支持的插件包括：Linear、GitHub、Gmail、Google Calendar、Outlook、Canva 等。

## 7. 与 Trae Agent 的关键差异

| 能力 | Trae Agent | Codex CLI |
|------|-----------|-----------|
| 自定义智能体 | 支持配置提示词和工具集 | 不支持自定义 Agent 定义 |
| 多智能体编排 | SOLO Agent 可调用自定义智能体 | 通过 MCP 和 /fork 实现协作 |
| Plan/Spec 模式 | 内置 Plan 和 Spec 工作流 | 不内置，需通过 AGENTS.md 或 MCP 实现 |
| 子智能体独立上下文 | 支持 | /fork 创建独立上下文 |

## 8. 待进一步调研

1. /fork 分叉会话的上下文继承深度和限制
2. Codex Cloud 并行任务的最大并发数
3. 插件系统的扩展 API 和自定义插件开发方式
