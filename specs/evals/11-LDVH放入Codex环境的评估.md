# LD Vibe Harness 放入 Codex 环境的评估

> 创建日期：2026-06-01
> 定位：LD Vibe Harness 整体迁移到 OpenAI Codex 环境的适应性评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/11-LDVH-AI协作规范.md`、`specs/11.01-Rules机制规范.md`、`specs/11.02-Skill机制规范.md`、`specs/11.03-Agent机制规范.md`、`specs/12-LDVH工具基础规范.md`、`specs/14-LDVH工作流基础规范.md`、`specs/51-multi-role-thinking-多角色思考.md`

---

## 1. 本文解决的问题

本文评估将 LD Vibe Harness 整体放入 OpenAI Codex 环境后，LDVH 五类构成要素分别在哪些维度会获得能力提升，哪些要素需要做适应性改动，以及哪些改动会触及 LDVH 的核心定位与架构假设。

本文基于对 OpenAI Codex（CLI `v0.118.0`、Cloud、IDE Extension、Desktop App，截至 2026 年 5 月）实际产品能力的调研撰写，不再使用推测性描述。

本文是内部调研，不直接构成强制规则；调研结论进入 00-79 正式规范区间或 ADR 后才成为稳定规则。

---

## 2. Codex 环境事实概览

### 2.1 产品形态

OpenAI Codex 是 OpenAI 推出的 AI 软件工程 Agent 产品家族，包含四个主要入口：

| 入口 | 形态 | 关键特征 |
|---|---|---|
| **Codex CLI** | 终端工具（Rust，Apache 2.0 开源） | 本地运行，交互式 TUI + 非交互 `codex exec`；OS 级沙箱（macOS Seatbelt / Linux Landlock+seccomp） |
| **Codex Cloud** | 云端 Agent（chatgpt.com/codex） | 每个任务在独立云端沙箱容器中运行；可并行派发多任务；自动生成 PR |
| **Codex IDE Extension** | VS Code / JetBrains 插件 | 编辑器侧边栏实时交互；共享 CLI 的 Skills 和配置 |
| **Codex App** | 桌面客户端 | Worktrees 多分支并行；Automations 定时任务；Memory 跨会话记忆 |

所有入口通过 ChatGPT 账号统一认证，约 400 万周活跃用户（2026 年 4 月数据）。

### 2.2 模型与上下文

| 项目 | 事实 |
|---|---|
| 当前默认模型 | GPT-5.4（CLI 默认），GPT-5.3-Codex（Cloud 默认） |
| 默认上下文窗口 | 272K tokens |
| 最大可配置上下文 | 1M tokens（通过 `model_context_window` 配置） |
| 模型演进路径 | codex-1 → gpt-5-codex → gpt-5.2-codex → gpt-5.3-codex → gpt-5.4 |
| 推理强度 | 可配置 low / medium / high（`reasoning_effort`） |

### 2.3 核心机制能力

| 能力 | Codex 实现 | 对标 LDVH 中的概念 |
|---|---|---|
| **项目指令** | `AGENTS.md` — 分层 Markdown 文件，从 `~/.codex/` → Git root → 子目录逐层叠加，32KB 默认上限 | L0/L1/L2 Rules + specs |
| **可复用工作流** | `SKILL.md` — Agent Skills 开放标准，YAML front matter + Markdown，渐进式披露，存储在 `.codex/skills/` | Skill |
| **审批/人机交互** | `approval_policy`: `untrusted`（每步审批）/ `on-request`（Codex 自行判断）/ `never`；交互式 TUI 中每步操作可审批 | Human Gate |
| **沙箱/安全** | `sandbox_mode`: `read-only` / `workspace-write` / `danger-full-access`；网络访问可配置（`network_access`）；OS 内核级隔离 | LDVH 没有对等机制 |
| **外部工具** | 完整 MCP 支持（client + server），`config.toml` 中配置，支持 stdio/HTTP/UDS transport，工具按 `mcp__<server>__<tool>` 命名空间隔离 | MCP（LDVH 已定义 MCP 使用边界） |
| **会话分叉** | `/fork` 命令从历史会话创建新分支 | Agent 调度 / 多角色思考中的子 Agent 模式 |
| **云端多任务** | Codex Cloud 并行派发多个独立任务 | LDVH 没有对等能力 |
| **自动化** | Codex App 的 Automations：定时/事件触发任务；`codex exec` 用于 CI/CD | LDVH 没有对等能力 |
| **记忆** | Codex App Memory（预览版）：跨会话记住偏好、修正和经验 | LDVH 的 Pitfall / Change / Evidence 沉淀机制 |
| **配置** | `config.toml`（TOML），分层：`/etc/codex/` → `~/.codex/` → `.codex/`（项目级）→ CLI `-c` 覆盖 | LDVH 没有统一配置层 |

---

## 3. LDVH 与 Codex 的关键差异对比

| 维度 | LDVH（基于 Trae Solo） | OpenAI Codex |
|---|---|---|
| 运行位置 | 本地 IDE + Trae 云端 Agent | CLI 本地 / Cloud 远程容器 / IDE 插件 / Desktop App |
| 上下文窗口 | 受 Trae 限制（具体数值未公开） | 272K 默认，最大 1M tokens |
| 规则机制 | `.trae/rules/` — L0/L1/L2 分层，`alwaysApply`/`globs`/`description` 生效方式 | `AGENTS.md` — 分层 Markdown，从用户目录到子目录逐层叠加，无内置生效方式区分 |
| Skill 机制 | Trae Skill — 项目 `.trae/skills/` 目录 | SKILL.md 开放标准 — `.codex/skills/`，渐进式披露（name+desc → body → scripts/refs） |
| Agent 机制 | Trae Agent — LDVH 在其上自建调度规则 | `/fork` 会话分叉 + Cloud 并行任务 + MCP 多 Agent 编排 |
| Human Gate | AskUserQuestion（Trae 特有工具） | `approval_policy`（untrusted/on-request/never）+ TUI 交互式审批 |
| 安全沙箱 | 依赖 Trae 平台 | OS 内核级沙箱（Apple Seatbelt / Landlock+seccomp）+ `sandbox_mode` |
| MCP | Agent 的外部工具来源 | 原生支持 MCP client + server，`codex mcp add` CLI 命令管理 |
| 配置系统 | 无统一配置层 | `config.toml` 分层配置 + Profiles 多环境切换 |
| 自动化/CI | 无 | `codex exec` 非交互模式 + GitHub Action + Codex App Automations |
| 多人协作 | 无 | Codex Cloud 共享 + Slack/Linear 集成 |

---

## 4. LDVH 在 Codex 环境中会获得的提升

以下每条提升都基于 Codex 的已确认能力。

### 4.1 上下文能力：从"精打细算"到"按需取用"

Codex 的 272K 默认上下文窗口（最大 1M）远大于 Trae Solo。LDVH 当前为此设计的严格读取策略可以放宽。

| LDVH 当前约束 | Codex 下的变化 | 依据 |
|---|---|---|
| "不得全文读取超过 200 行的规范文档" | 可以放宽，AI 不会因读一个 500 行的 specs 而过载 | 272K tokens ≈ 约 200K 英文词，单个 LDVH spec 最大约 500 行，远在窗口内 |
| "先搜标题再按行读取" | 保留为良好实践，但不再是硬约束 | Codex 会自动读取 AGENTS.md 和项目文件，不需要 LDVH 规范指令它"如何读" |
| "压缩保护段" | 不再需要 | Codex 使用 Compaction（语义摘要）而非截断压缩，压缩保护段的机制基础不存在 |

结论：**LDVH 的 Context 组织规范可以简化约 60%。** 核心的"最小可行动上下文"原则仍建议保留（防止上下文垃圾污染），但实现方式从"指令 AI 如何读"变为"在 AGENTS.md 中声明优先级"。

### 4.2 Agent 编排：从"自建调度"到"交棒原生"

| LDVH 当前做法 | Codex 下的变化 | 依据 |
|---|---|---|
| 自定义 Agent 调度规则（`specs/11.03`） | 大部分可删除 | Codex Cloud 原生并行多任务；`/fork` 原生会话分叉；MCP 可编排多 Agent |
| 手动判断"何时需要子 Agent" | 保留判断逻辑，但执行交棒 | Codex 会自行决定是否 `/fork` 或派发 Cloud 任务 |
| Agent 权限边界、生命周期管理 | 删除 | Codex 的 `sandbox_mode` + `approval_policy` 原生覆盖 |

结论：**`specs/11.03-Agent机制规范.md` 可以删减约 80%。** 只保留"何时需要独立上下文/并行"的判断逻辑。

### 4.3 安全沙箱：从"无"到"OS 内核级"

这是 LDVH 在 Codex 中获得的全新能力。Trae Solo 环境下 LDVH 没有沙箱机制，只能靠 Human Gate 阻止危险操作。Codex 提供：

| Codex 沙箱能力 | 对 LDVH 的价值 |
|---|---|
| `read-only` 模式 | AI 只能读不能写——安全地探索陌生代码库 |
| `workspace-write` 模式（默认） | AI 只能修改当前项目目录——天然满足 LDVH 事实源边界原则 |
| `danger-full-access` 模式 | 明确的高风险入口——降低 AI 无意中越界的概率 |
| OS 内核级隔离（Seatbelt/Landlock） | AI 无法通过"话术"绕过——比应用层校验更可靠 |
| 网络访问控制（`network_access`） | 可以禁止 AI 在沙箱中访问外部 API |

### 4.4 MCP 集成：从"可选"到"原生一等公民"

LDVH 的 MCP 使用评估（`specs/evals/06`）将 MCP 定位为"Agent 的可选工具能力来源"。在 Codex 中，MCP 是原生一等公民：

| Codex MCP 能力 | 对 LDVH 的价值 |
|---|---|
| `codex mcp add` CLI 管理 | 一行命令添加 MCP Server |
| `config.toml` 中 `[mcp_servers]` 配置 | 项目级和全局级 MCP Server，可 Git 版本化 |
| 支持 stdio / HTTP / UDS transport | 灵活接入各种 MCP Server |
| Codex 自身可作为 MCP Server（`codex mcp-server`） | 其他 Agent 可以通过 MCP 调用 Codex |
| 工具命名空间隔离（`mcp__<server>__<tool>`） | 多 MCP Server 工具不冲突 |

### 4.5 当前两个 MCP 服务在 Codex 的可用性

LDVH 当前使用的两个 MCP 服务均已在 Codex 中得到确认支持：

**Sequential Thinking**：✅ 直接可用

```bash
# Codex CLI 一行命令添加
codex mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

或写入 `config.toml`：

```toml
[mcp_servers.sequential-thinking]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]
```

**Context7**：✅ 直接可用，且被列为 Codex 推荐 MCP Server

```bash
# Codex CLI 一行命令添加
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

或写入 `config.toml`：

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
```

两者都是 stdio transport 的本地 MCP Server，Codex 原生支持。Context7 更是多个 Codex MCP 教程中列出的首推推荐 Server。

**关键差异**：

| 维度 | Trae Solo 中的 MCP | Codex 中的 MCP |
|---|---|---|
| 配置方式 | `.trae/mcp.json`（JSON） | `~/.codex/config.toml` 中 `[mcp_servers]`（TOML）或 `codex mcp add` CLI |
| 工具命名空间 | 按 Server 名直接暴露 | `mcp__<server_name>__<tool_name>` 命名空间隔离 |
| Server 管理 | IDE 界面手动添加 | CLI 命令 + config.toml 双重管理 |
| Agent 分配 | 手动为每个 Agent 勾选 | 全局生效（全部 Agent 可用） |
| 沙箱协商 | 无 | Codex 特有：向 MCP Server 通告 sandbox-state，Server 需确认遵守 |
| 审批集成 | 无 | MCP elicitation 可触发 AskForApproval UI |

**迁移成本**：极低。两个 Server 都只需一行命令添加，或复制配置到 `config.toml`。工具调用名称从原始名称变为 `mcp__sequential-thinking__sequentialthinking` / `mcp__context7__resolve-library-id` 等格式，LDVH 的 Skill 或 Action Model 中提到这些工具时需更新名称。

### 4.6 自动化与 CI/CD：从"无"到"完整流水线"

| Codex 能力 | 对 LDVH 的价值 |
|---|---|
| `codex exec` 非交互模式 | LDVH 可以将审计、校验、事实源检查等任务脚本化 |
| GitHub Action（PR Review） | AI 自动审查 PR，按 `AGENTS.md` 中 `## Review guidelines` 规则执行 |
| Codex App Automations | 定时触发审计任务、依赖更新检查、Pitfall 扫描 |

### 4.7 Codex App Memory：从"Pitfall + Change"到"原生记忆"

LDVH 的 Pitfall 和 Change 机制是用结构化 YAML 记录经验和变更。Codex App 的 Memory 功能（预览版）提供了补充：

| Codex Memory | 与 LDVH 的关系 |
|---|---|
| 记住用户偏好和修正 | 减少需要在 AGENTS.md 中手动维护的个人偏好 |
| 跨会话保留上下文 | 补充 LDVH 的事实源沉淀机制（LDVH 写 Git 文件，Memory 写云端记忆） |
| 自动学习模式 | 可能减少 Pitfall 的手动录入需求 |

**注意**：Codex Memory 是云端存储，不能替代 Git 文件事实源。两者是互补关系。

---

## 5. LDVH 放入 Codex 环境需要的具体改动

以下按五类构成要素逐一分析，每条改动都基于 Codex 的实际机制。

### 5.1 介质（Medium）：不需要改动

YAML、Markdown、Python 等介质是行业标准，Codex 完全支持。不需要任何改动。

### 5.2 环境机制：这是改动最大的区域

#### 5.2.1 Rules → AGENTS.md + config.toml

**Trae Rules 机制**：`.trae/rules/*.md`，通过 `alwaysApply`/`globs`/`description` 控制生效方式。

**Codex 对等机制**：`AGENTS.md` 分层 Markdown。

**具体对比**：

| LDVH Rules 概念 | Codex 对等实现 | 适配方案 |
|---|---|---|
| L0 工作区规则（始终生效） | `~/.codex/AGENTS.md`（全局，始终加载） | 将 L0 内容写入 `~/.codex/AGENTS.md` |
| L0 事实模型规则（globs：编辑 ldvh-base/ YAML 时生效） | 无直接对等机制。AGENTS.md 没有"按文件类型触发"的能力 | ① 在对应子目录放 `AGENTS.md`（如 `ldvh-base/AGENTS.md`）；② 或在项目根 `AGENTS.md` 中声明"编辑 ldvh-base/ 下 YAML 时的规则" |
| L1 项目规则（始终生效） | 项目根 `AGENTS.md`（Codex 自动从 Git root 向上扫描到 CWD） | 将 L1 内容写入项目根 `AGENTS.md` |
| L2 场景规则（globs / description） | `SKILL.md`（通过 description 匹配触发）+ 子目录 `AGENTS.md`（就近生效） | 将 L2 规则改写为：① 子目录 `AGENTS.md`（如果是"特定文件类型"约束）；② 或 `SKILL.md`（如果是"特定操作流程"） |
| 压缩保护段 | 不再需要。Codex 使用 Compaction（语义摘要）而非截断 | 删除所有压缩保护段 |

**关键差异**：

1. Trae Rules 的 `globs` 按文件类型自动触发——Codex 的 AGENTS.md **没有**这个能力。Codex 是"按目录分层加载"，不是"按文件类型过滤"。LDVH 的 L2 globs 规则需要改为在目标文件所在目录放置 `AGENTS.md`。

2. Trae Rules 的 `description` 智能生效——Codex 的 SKILL.md 有类似的 `description` 匹配触发机制，但 SKILL.md 是工作流而非约束规则。如果需要"按场景触发约束"，建议用 SKILL.md 包装。

3. AGENTS.md 有 32KB 默认上限——如果 LDVH 的 specs 规范内容较多，需要拆分到子目录的 AGENTS.md 中。

**适配结论**：LDVH 的 Rules 体系需要从"L0/L1/L2 分层 + Trae 生效方式映射"改为"AGENTS.md 目录分层 + SKILL.md 场景触发"。约束语义不变，承载形式变化。

#### 5.2.2 Skill → SKILL.md

**Trae Skill 机制**：项目 `.trae/skills/` 目录下的 Markdown 文件。

**Codex 对等机制**：SKILL.md 开放标准——`.codex/skills/` 或 `~/.codex/skills/`。

**具体对比**：

| 维度 | Trae Skill | Codex SKILL.md |
|---|---|---|
| 文件格式 | 纯 Markdown | YAML front matter（name, description）+ Markdown body |
| 存储位置 | `.trae/skills/` | `.codex/skills/`（项目级）/ `~/.codex/skills/`（用户级） |
| 触发方式 | 规则匹配或手动调用 | 隐式（description 匹配）或显式（`$skill-name`） |
| 上下文加载 | 全量加载 | 渐进式披露：先加载 name+description，激活后才加载 body，需要时才加载 scripts/refs |
| 资源支持 | Markdown 内嵌 | `scripts/` + `references/` + `assets/` 子目录 |
| 跨平台 | Trae 专用 | 开放标准，Claude Code、Codex、Cursor、Copilot 等均支持 |

**适配方案**：

1. 为每个 LDVH Skill 创建 `SKILL.md`，添加 YAML front matter（name, description）；
2. 将 LDVH Skill 的流程步骤写入 SKILL.md body；
3. 如果 Skill 需要辅助脚本，放入 `scripts/` 子目录；
4. 如果 Skill 需要引用 LDVH 规范，在 `references/` 中放入链接或摘要；
5. Skill 的触发条件写在 `description` 字段中（这是 Codex 匹配的关键）。

**适配成本**：每个 Skill 约 10-20 分钟的改写工作。内容基本可以复用，主要工作是添加 YAML front matter 和拆分资源文件。

#### 5.2.3 Agent → /fork + Cloud + MCP

**Trae Agent 机制**：LDVH 在 Trae 的 Agent 能力上自建调度规则。

**Codex 对等机制**：

| Codex 机制 | 对标 LDVH 的什么 |
|---|---|
| `/fork` | 从当前会话分叉出新会话 → 等同于"子 Agent 独立上下文" |
| Codex Cloud 并行任务 | 同时派发多个独立任务 → 等同于"多 Agent 并行" |
| MCP 多 Agent 编排 | 通过 MCP 连接其他 Agent → 等同于"Agent 调度" |
| `codex exec` | 非交互式执行 → 等同于"Agent 后台任务" |

**适配结论**：**`specs/11.03-Agent机制规范.md` 可以删除约 80%。** 只保留"何时应 `/fork` 或派发 Cloud 任务"的判断逻辑。

### 5.3 工具（Tools）：局部适配

#### 5.3.1 Web 信息同步层

LDVH 的 Web Tools（`specs/12.02-Web信息同步规范.md`）在 Codex CLI 中无法直接运行 Web 服务——CLI 是终端 TUI，不承载 Web 界面。

**三种替代方案**：

| 方案 | 适用场景 | 实现方式 |
|---|---|---|
| 退化为 TUI 结构化输出 | 交互式使用 | Codex 在 TUI 中展示 diff、状态摘要、任务列表 |
| Codex App 内置浏览器 | Desktop 使用 | Codex App 支持内置浏览器，可以打开 localhost Web 页面 |
| 外部部署 | 团队共享 | 将 Web Tools 部署到外部服务器，通过 URL 接入 |

**适配建议**：LDVH 的 Web 信息同步层在 Codex CLI 下应退化为结构化输出 + AGENTS.md 中的状态摘要规范。如果目标是 Desktop 场景，Web Tools 可保留。

#### 5.3.2 Tools 辅助层

Tools 辅助层（Python 脚本）在 Codex 中可以直接运行（Codex 支持执行任意 shell 命令，受沙箱约束）。不需要改动。

**一个增强点**：Tools 辅助层可以封装为 MCP Server。例如，LDVH 的 YAML 校验脚本可以写成一个 MCP Server，Codex 通过 `mcp__ldvh-validator__validate_task` 调用。

### 5.4 事实模型（Production Objects）：不需要改动

Intent、Task、Memo、ADR、Evidence、Change、Pitfall 的 YAML 字段契约、状态机、事实源边界完全不变。

#### 5.4.1 Linear 不能替代 LDVH Task

Codex 原生集成了 Linear。一个自然会产生的想法是：既然 Codex 已经能操作 Linear Issue，是否可以用 Linear Issue 替代 LDVH Task？

**结论：不能。Linear 只能作为辅助视图，不能替代 Git 文件事实源。**

| 维度 | LDVH Task（Git YAML） | Linear Issue（云端数据库） | 判断 |
|---|---|---|---|
| 事实源原则 | Git 文件，可追溯、可审计 | Linear 云端，不在 Git 中 | Linear 违反 LDVH 核心原则 |
| 状态机 | LDVH 自定义状态机，含 Human Gate 节点 | Linear 自定义 Workflow，无 Human Gate 概念 | 不兼容 |
| 关联关系 | `source_intent` → Intent、`related_adr` → ADR、`blocked_by` → Task/Dependency | 有 Issue 关联，但无 Intent/ADR/Dependency 对象概念 | LDVH 关系更丰富 |
| 关闭证据 | `closure_evidence` 结构化字段，Git 可追溯 | 无结构化证据要求 | LDVH 更严格 |
| 变更审计 | 每次变更写 `ldvh-base/changes/` | Linear 活动日志不在 Git | LDVH 更可审计 |
| 离线可用 | ✅ Git 本地 | ❌ 依赖 Linear 服务 | LDVH 更可靠 |
| AI 读取 | 直接读 YAML，上下文消耗确定 | 通过 API/MCP 查询，增加不确定性 | LDVH 更可控 |

#### 5.4.2 为什么目的相同却不能替代：消费者不同

Linear Issue 和 LDVH Task 目的确实一样——都是任务追踪。但决定数据模型设计的不是"目的是什么"，而是 **"谁来消费这个数据"**：

| | Linear Issue | LDVH Task |
|---|---|---|
| **第一消费者** | 人 | **AI 执行者** |
| **核心问题** | "这个任务谁在做、什么时候做完" | "AI 进入项目后，该读什么、做什么、何时停下、留下什么证据" |
| **信息密度** | 标题 + 描述 + 评论（人写给队友看） | 完整执行上下文包：`source_intent` + `related_adr` + `dependencies` + `acceptance` + `closure_evidence`（人写给 AI 执行） |
| **状态流转** | 人手动拖拽 | AI 按状态机自动判断 + Human Gate 暂停 |
| **证据要求** | 几乎没有（"Done" 就算完成） | 关闭必须有结构化 `closure_evidence` 回写 Git |
| **典型使用** | 人打开 Linear 看板 → 拖一张卡到 "In Progress" → 写完代码 → 拖到 "Done" | AI 读取 Task YAML → 获得 source_intent 和 related_adr → 按 dependencies 顺序执行 → 触发 Human Gate → 回写 closure_evidence → 关闭 |

如果放弃 LDVH Task、只用 Linear Issue，会发生什么：

1. AI 每次执行任务，需要人把"该读什么 specs、关联哪个 ADR、依赖哪些前置任务、关闭需要什么证据"这些信息口头告诉它；
2. 又回到了 Vibe Coding 的"聊天记忆驱动"模式——而这正是 LDVH 要解决的问题；
3. AI 关闭任务时没有证据约束，"Done" 就是 Done，无法审计"凭什么说做完了"。

所以不是说 LDVH 在重复造轮子，而是**造的是不同用途的轮子**：Linear 管人怎么看任务，LDVH Task 管 AI 怎么执行任务。两者不冲突，互补。

**Linear 的合理定位**：

```text
LDVH Task（Git YAML） ← 权威事实源，AI 和人都以此为准
        ↕ 单向或双向同步（辅助，非强制）
Linear Issue          ← 人的可视化工作台，项目管理体验层
```

Codex 的 Linear 集成可以让开发者在 Linear 面板中看到 LDVH Task 的状态，甚至可以从 Linear 触发操作。但：
- Task 的创建、状态变更、证据回写必须发生在 Git YAML 中
- Linear 中的状态与 Git YAML 冲突时，以 Git YAML 为准
- Linear 不得成为 Task 状态、证据或审计的唯一来源

这个结论与 [01-LDVH对Linear的借鉴评估](file:///Users/dmh2002/trae_projects/ld-vibe-harness/specs/evals/01-LDVH对Linear的借鉴评估.md) 一致：LDVH 不应是 Linear clone，Linear 值得学的是体验（速度感、清晰度、多视图），不是数据模型。

### 5.5 行动模型（Action Model）：简化为主

#### 5.5.1 Context 组织

| LDVH 当前 | Codex 下 |
|---|---|
| 严格行数限制 | **删除**。272K 窗口内，LDVH 全部 specs + ldvh-base 都装得下 |
| 先搜标题再按行读取 | **删除**。Codex 自动读取项目文件，不需要 LDVH 指令它"怎么读" |
| "不得全文读取超过 200 行" | **删除** |
| 压缩保护段 | **删除**。Codex 使用语义摘要（Compaction），不是截断 |

**保留**："最小可行动上下文"原则作为设计理念保留，但实现方式从"指令约束"变为"AGENTS.md 中声明优先级"。

#### 5.5.2 Scenario 识别

不需要改动。Scenario 识别逻辑是平台无关的。

#### 5.5.3 Human Gate

**Trae**：AskUserQuestion 工具 —— 特定 API 调用，暂停等待用户响应。

**Codex**：

| Codex 机制 | 行为 |
|---|---|
| `approval_policy = "untrusted"` | 每次文件写入和命令执行都需人工审批 |
| `approval_policy = "on-request"` | Codex 自行判断何时需要审批 |
| `approval_policy = "never"` | 永不审批（全自动） |
| TUI 交互审批 | 每次操作显示 diff，用户确认/拒绝/修改 |
| MCP elicitation | MCP Server 可以发起审批请求（`AskForApproval` UI 组件） |

**适配方案**：

LDVH 的 Human Gate 触发条件（"什么情况下需要人确认"）不变。实现方式从"调用 AskUserQuestion"改为：

1. 在 `AGENTS.md` 中声明"以下场景必须暂停等待确认"；
2. 将 `approval_policy` 设为 `on-request`（让 Codex 自行判断 + LDVH 规则引导）；
3. 对高风险操作，建议用户使用 `untrusted` 模式启动 Codex。

**关键差异**：Codex 的审批机制比 Trae 的 AskUserQuestion 更灵活——支持三级审批粒度（每步/自行判断/全自动），且审批 UI 直接嵌入 TUI 工作流。

#### 5.5.4 多角色思考

| LDVH 当前 | Codex 下 |
|---|---|
| 主上下文轻量模式（单 AI 按序多视角） | 保留。272K 窗口下更从容 |
| 子 Agent 模式（启动多个子 Agent） | 用 `/fork` 替代：fork 多个会话，每个以不同角色视角分析，然后汇总 |

**适配建议**：多角色思考的**触发条件**和**分析框架**不变。执行方式：主上下文轻量模式保留；子 Agent 模式用 `/fork` + Codex Cloud 并行任务替代。

---

## 6. 不应该改变的核心

| 核心 | 原因 |
|---|---|
| 第一服务对象是 AI 执行者 | LDVH 的存在理由 |
| Git 文件是唯一事实源 | Codex 的云端存储、Memory、Linear 集成都不能替代 Git 文件事实源 |
| 五类构成要素分工 | 分工关系不因平台变化而混淆 |
| V1-V10 价值实现标准 | LDVH 的工程标尺 |
| Human Gate 原则 | 人必须能在关键节点确认 |
| 事实源闭环 | 起点可以是对话，终点必须是 Git 文件 |
| 受控执行 | AI 不能绕过规则、状态机、Human Gate |
| 事实模型（字段契约、状态机） | 平台无关 |
| specs 文档结构和编号分区 | 平台无关 |
| 介质使用要求 | 平台无关 |

---

## 7. 改动汇总

### 7.1 需要改的

| 改动项 | 改动量 | 工作量估计 |
|---|---|---|
| L0/L1/L2 Rules 重写为 AGENTS.md 分层 + SKILL.md | 大 | 需要逐一映射每个 Rule 到 Codex 机制 |
| Skill 迁移到 SKILL.md | 中 | 每个 Skill 添加 YAML front matter，拆分资源文件 |
| Agent 调度规范大幅简化 | 中 | 删除约 80% 内容 |
| Human Gate 实现从 AskUserQuestion 改为 Codex approval_policy | 中 | 重写 Gate 实现章节 |
| Context 组织规范删除约 60% | 小 | 删除过时约束 |
| Web 信息同步层适配（CLI 下退化为 TUI 输出） | 中 | 需要重新设计展示方案 |
| 多角色思考子 Agent 模式改为 /fork | 小 | 只改执行方式 |

### 7.2 不需要改的

- 事实模型（Intent、Task、Memo、ADR、Evidence、Change、Pitfall）
- 事实源边界
- 价值实现标准（V1-V10）
- 行动模型触发逻辑（Scenario、Gate 条件、回写规则）
- specs 文档结构和编号分区
- 介质使用要求
- Tools 辅助层（Python 脚本）

### 7.3 可以删除的

- 所有"压缩保护段"
- "不得全文读取超过 200 行"
- "先搜标题再按行读取"（从硬约束降级为建议）
- Agent 生命周期管理规范
- Agent 权限边界规范（被 Codex sandbox 替代）

---

## 8. 迁移路径建议

### 8.1 第一阶段：最小可用（约 1-2 天）

目标：LDVH specs + ldvh-base 在 Codex 中可被 AI 读取和遵守。

1. 创建项目根 `AGENTS.md`，将 L1 规则核心内容写入；
2. 在 `ldvh-base/` 下创建 `AGENTS.md`，将 L0 事实模型规则写入；
3. 在 `specs/` 下创建 `AGENTS.md`，声明 specs 文档的读取优先级；
4. 保持 `codex` 默认的 `workspace-write` + `on-request` 审批策略；
5. 不迁移 Skill，不修改 Agent 调度，不用 Web Tools。

验证标准：对 Codex 说"帮我创建一个 Task"，它应该先读 ldvh-base 的现有结构，然后按 LDVH 规范创建 YAML。

### 8.2 第二阶段：能力对齐（约 1 周）

目标：LDVH 在 Codex 中的体验不弱于 Trae Solo。

1. 将每个 LDVH Skill 改写为 SKILL.md；
2. 将 L2 globs 规则改为子目录 AGENTS.md 或 SKILL.md；
3. 配置 MCP Server（如 Context7、Sequential Thinking）；
4. 将 Human Gate 触发逻辑写进 AGENTS.md；
5. 验证 Codes 辅助层在 Codex 沙箱中正常运行。

### 8.3 第三阶段：能力增强（约 2-4 周）

目标：利用 Codex 特有优势增强 LDVH。

1. 多角色思考改为 `/fork` + 并行分析；
2. 利用 Codex Cloud 并行任务实现多 Agent 审计；
3. 将 LDVH 校验脚本封装为 MCP Server；
4. 设置 Codex App Automation 做定时 Pitfall 扫描；
5. 配置 GitHub Action 实现 PR 自动审计。

---

## 9. 到底值不值得从 Trae Solo 切换到 Codex？

以上都是从 LDVH 规范体系的角度分析"如果迁移需要改什么"。本节从 **LDVH 使用者的实际体验** 角度回答：到底值不值得换？

### 9.1 两平台事实对比

| 维度 | Trae Solo | OpenAI Codex | 谁赢 |
|---|---|---|---|
| **产品形态** | AI-native IDE（VS Code fork） | CLI（Rust）+ Cloud + IDE Extension + Desktop App | 各有优势 |
| **默认模型** | Claude 3.5 Sonnet / GPT-4o / Doubao-1.5-pro / DeepSeek（多模型自由切换） | GPT-5.4（CLI）/ GPT-5.3-Codex（Cloud） | Trae（模型选择更多） |
| **上下文窗口** | 受限（MCP 被限制为 8000 字符描述 + 40 工具上限，说明上下文窗口较紧张） | 272K 默认，最大 1M tokens | **Codex 大幅领先** |
| **Rules 机制** | `.trae/rules/`，4 种生效方式（alwaysApply / globs / description / #Rule），3 层嵌套 | `AGENTS.md` 分层 Markdown，无生效方式区分，无 globs 触发 | **Trae 大幅领先** |
| **Skill 机制** | `.trae/skills/`，兼容 Agent Skills 标准 | `.codex/skills/` SKILL.md 开放标准，渐进式披露 | 基本持平（同标准） |
| **Agent 机制** | 自定义 Agent（Prompt + MCP + 工具），SOLO Agent 编排，最多 20 并发云端任务 | `/fork` 会话分叉 + Cloud 并行任务 + MCP 多 Agent | 基本持平 |
| **Human Gate** | AskUserQuestion（专用 API，暂停等待） | approval_policy（untrusted / on-request / never）+ TUI 交互审批 | **Codex 更灵活** |
| **沙箱安全** | 无明显沙箱能力 | OS 内核级（Seatbelt/Landlock）+ read-only / workspace-write / danger-full-access | **Codex 独有** |
| **MCP** | stdio / SSE / Streamable HTTP；8000 字符描述上限 + 40 工具上限 | stdio / HTTP / UDS；无已知硬限制 | **Codex 更宽松** |
| **自动化/CI** | 无 | `codex exec` + GitHub Action + Automations | **Codex 独有** |
| **跨会话记忆** | 无 | Codex App Memory（预览版） | **Codex 独有** |
| **中文支持** | 99% 中文指令理解准确率，国内技术栈深度优化 | 无中文专项优化 | **Trae 大幅领先** |
| **定价** | Free 永久免费（无调用次数限制）；Pro $10/月 | 免费含 ChatGPT Plus/Pro 订阅；API 按量付费 | **Trae 更便宜** |
| **用户规模** | 600 万+ 注册（2025 年底） | 400 万周活（2026 年 4 月） | 接近 |
| **开源** | 否（VS Code fork，闭源增强） | CLI 完全开源（Apache 2.0，Rust） | **Codex 更透明** |
| **数据隐私** | 代码不用于训练（opt-out） | 代码不上传（本地执行） | 接近 |
| **LDVH 现状** | ✅ 已深度集成 | ❌ 需从零迁移 | **Trae 零成本** |

### 9.2 对 LDVH 使用者而言：Trae 赢的维度更重要

上面的对比如果只看数量——Codex 在更多维度上领先。但对于 **用 LDVH 做 AI 驱动工程治理** 这个具体场景，赢在哪个维度比赢了多少个维度更重要。

**Trae 赢的维度，恰好是 LDVH 最核心的依赖：**

| Trae 优势 | 对 LDVH 的意义 |
|---|---|
| **Rules 机制的 4 种生效方式** | LDVH 的 L0/L1/L2 规则体系深度依赖 globs（按文件类型触发）和 description（按场景触发）。Codex 的 AGENTS.md 完全没有这些能力——这是迁移的最大硬伤 |
| **中文支持** | 你所有的 specs、eval 文档、Rules 都是中文写的。Codex 没有中文专项优化，指令理解准确率会下降 |
| **零迁移成本** | LDVH 已经在 Trae 上跑通了全部机制。切到 Codex 需要重写 Rules、迁移 Skill、重构 Agent 调度、重新对接 Human Gate |
| **永久免费** | 无调用次数限制的免费 tier，对个人项目的长期运行很重要 |

**Codex 赢的维度，对 LDVH 更多是"锦上添花"而非"雪中送炭"：**

| Codex 优势 | 对 LDVH 的实际价值 |
|---|---|
| **272K-1M 上下文** | 这是 Codex 最大的真实优势。Trae 的上下文约束导致 LDVH 花了大量精力设计"最小可行动上下文"策略。但——这个约束目前还没到"不可用"的程度，只是"需要谨慎" |
| **OS 级沙箱** | 很好，但 LDVH 通过 Human Gate + Rules 已经做到了"AI 不会擅自执行危险操作"。沙箱是更强的保障，但不是必需品 |
| **自动化/CI** | LDVH 目前没有自动化需求。如果有，可以用 GitHub Action 独立配置，不需要依赖 AI IDE |
| **Memory** | 和 LDVH 的 Pitfall/Change 互补，但 LDVH 自己的沉淀机制已经够用 |
| **Codex Cloud 并行** | Trae SOLO 也支持最多 20 并发云端任务（Ultra 版） |

### 9.3 判断

**不建议现在切换。** 理由按重要性排序：

1. **Rules 机制是硬伤**。Codex 的 AGENTS.md 无法替代 Trae 的 globs / description / #Rule 触发方式。LDVH 的 L2 规则（按文件类型和场景生效）在 Codex 中会退化为"永远生效"——这会让 AI 的上下文被不相关的规则污染，反而降低执行质量。这不是"适配成本"的问题，是"能力缺失"的问题。

2. **迁移成本 > 当前收益**。LDVH 在 Trae 上已经完整跑通。切到 Codex 需要大量适配工作，而目前没有遇到"非换不可"的痛点（如 Trae 上下文窗口严重阻塞实际工作）。

3. **中文是你的工作语言**。所有 specs 都用中文写，Trae 的中文优化是实际价值。

4. **Codex 还在快速迭代**。AGENTS.md 将来可能增加更精细的触发机制。等一等可能更好。

**什么情况下应该重新评估：**

| 触发条件 | 原因 |
|---|---|
| Trae 上下文窗口严重阻塞实际工作 | 这是 Codex 最大的差异化优势 |
| Codex 的 AGENTS.md 增加了类似 globs 的触发机制 | 消除了迁移的最大阻点 |
| Trae 开始收费或大幅限制免费额度 | 改变了性价比计算 |
| 你需要 CI/CD 集成或定时自动化 | Codex 在这方面独有优势 |

### 9.4 折中方案：双轨使用

如果对 Codex 的某些能力（如大上下文、沙箱）确实有需求，不一定要全面切换：

```text
Trae Solo（主力）               Codex CLI（辅助）
├─ 日常 LDVH 驱动开发             ├─ 需要大上下文的任务（如全量 specs 审计）
├─ Rules / Skill / Agent 机制     ├─ 需要 OS 级沙箱隔离的试验性代码生成
├─ Human Gate（AskUserQuestion）   ├─ 定时自动化（codex exec + cron）
└─ 所有 LDVH 规范治理             └─ PR 自动审查（GitHub Action）
```

两个平台共享同一套 Git 事实源（specs/、ldvh-base/）。Codex 不取代 Trae，只补充 Trae 能力短板。

---

## 10. 产品原则沉淀

> LDVH 放入 Codex 后，内核不变，底座替换，能力增强。

具体而言：

1. **内核不变**：事实模型、事实源边界、价值标准、Human Gate 原则、受控执行——这些都是平台无关的；
2. **底座替换**：Rules → AGENTS.md + SKILL.md；Skill → SKILL.md；Agent → `/fork` + Cloud；Human Gate → `approval_policy`；
3. **能力增强**：OS 级沙箱、272K-1M 上下文、原生 MCP、自动化/CI、云端并行、Memory；
4. **简化而非膨胀**：Codex 的多项原生能力（沙箱、审批、上下文管理）直接替代了 LDVH 中自行设计的机制，LDVH 规范可以瘦身；
5. **事实源不妥协**：Git 文件是唯一事实源，Codex 云端存储、Memory、Linear 集成都不能替代。

### 10.1 LDVH 不应开发工具已具备的能力

这是判定 LDVH 边界的一个关键原则。无论面向 Trae Solo 还是 Codex，判断某项能力是否应由 LDVH 自己实现时，先问一个问题：**平台/工具是否已经提供了这项能力？**

| 能力 | Trae 已提供？ | Codex 已提供？ | LDVH 应做什么 |
|---|---|---|---|
| 规则约束机制 | ✅ Rules 4 种生效方式 | ✅ AGENTS.md（但无 globs/description） | 定义约束**内容**（specs），不重新实现规则加载引擎 |
| 可复用工作流 | ✅ Skill | ✅ SKILL.md | 定义工作流**内容**，不重新实现 Skill 执行引擎 |
| Agent 调度 | ✅ SOLO Agent + 自定义 Agent | ✅ `/fork` + Cloud + MCP | 定义**何时**需要 Agent，不重新实现 Agent 运行时 |
| Human Gate | ✅ AskUserQuestion | ✅ approval_policy + TUI | 定义**什么场景**必须触发 Human Gate，不重新实现审批 UI |
| 任务管理 | ❌ 无 | ❌ 无（Linear 不算，原因见 §5.4.1） | LDVH Task 属于"工具没有的能力"——这不是重复造轮子 |
| 决策记录 | ❌ 无 | ❌ 无 | ADR 属于 LDVH 独有——工具不提供 |
| 经验沉淀 | ❌ 无 | ⚠️ Memory（但不满足 LDVH 的审计和 Git 事实源要求） | Pitfall / Change 仍需要，Memory 作为补充 |
| 安全沙箱 | ❌ 无 | ✅ sandbox_mode（OS 内核级） | **不需要 LDVH 自建**——直接使用 Codex 沙箱 |
| MCP 工具协议 | ✅ MCP client | ✅ MCP client + server | 定义**哪些 MCP 用于哪些场景**，不重新实现 MCP 协议 |
| 自动化/CI | ❌ 无 | ✅ codex exec + GitHub Action | **不需要 LDVH 自建**——直接使用 Codex 自动化 |

核心规则：

```text
LDVH 负责的：工具没有的（事实模型、治理规则、行动流程定义）
LDVH 不负责的：工具已有的（规则引擎、沙箱、审批 UI、自动化运行时）
LDVH 桥接的：工具已有但需要 LDVH 语义的（告诉工具"何时用"、"怎么配"）
```

这个原则反过来也意味着：如果将来某个平台提供了一项 LDVH 当前自建的能力（且满足 LDVH 的 Git 事实源和审计要求），LDVH 应该**删除自建实现，改用平台能力**。这不是退化，是瘦身——LDVH 的价值在于工程治理规范，不在于运行时基础设施。

---

## 11. 待补齐事项

1. 在实际 Codex CLI 环境中验证 AGENTS.md 分层加载行为（特别是子目录 AGENTS.md 是否如预期生效）；
2. 测试 LDVH 的 YAML 事实源在 Codex 工作流中的读写体验；
3. 验证 SKILL.md 的渐进式披露是否适合 LDVH 的长流程 Skill（如多角色思考、ADR 创建）；
4. 评估 Codex Cloud 的并行任务是否能满足 LDVH 的 Agent 调度需求；
5. 如果决定迁移，创建对应的迁移 ADR。
