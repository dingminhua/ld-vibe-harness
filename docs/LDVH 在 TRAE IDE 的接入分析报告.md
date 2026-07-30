# LDVH 在 TRAE IDE 的接入分析报告

## 执行环境与目标环境

- **执行环境**：TRAE IDE（本机 macOS，运行 GLM-5.2 模型），工作目录 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4`
- **目标环境**：同一 TRAE IDE 实例
- **二者关系**：同一环境，可直接观察与验证

---

## 一、TRAE 环境实际支持的机制

### 1.1 技能/指令文件 — 已验证

| 项目 | 证据 |
|---|---|
| 机制 | TRAE 从 `~/.agents/skills/<name>/SKILL.md` 加载技能；用户意图匹配 description 时由 Skill 工具按需调用 |
| 已验证 | 本会话已成功调用 `ldvh` 技能，加载了 `~/.agents/skills/ldvh/SKILL.md`（实为符号链接 → `~/.claude/skills/ldvh/SKILL.md`） |
| 权威依据 | TRAE 官方技能机制（系统 Skill 工具描述 + TRAE-product-knowledge 技能确认） |
| 边界 | 技能是**按需调用**，不会在会话启动时自动注入——除非配合 SessionStart Hook |

### 1.2 生命周期 Hook — 已验证支持（官方文档），当前配置未验证真实触发

TRAE IDE 官方支持 6 类 Hook 事件（[通过 Hook 实现自动化](https://docs.trae.cn/ide_automate-actions-with-hooks)、[Hook 配置详解](https://docs.trae.cn/ide_hook-configuration-reference)）：

| 事件 | 触发时机 | 能否阻断 | stdin 关键字段 | stdout 控制字段 |
|---|---|---|---|---|
| **SessionStart** | 创建 Session 后、首对话前 | 否（退出码 2 不影响流程） | `session_id, hook_event_name, source:"startup", cwd, workspace_roots` | 纯文本或 `{hookSpecificOutput:{hookEventName, additionalContext}}` |
| **UserPromptSubmit** | 用户发消息后、智能体处理前 | 是（`decision:"block"`） | `session_id, hook_event_name, prompt` | `{decision:"block", reason, hookSpecificOutput:{additionalContext}}` |
| **PreToolUse** | 工具调用后、执行前 | **是（`permissionDecision:"deny"`）** | `session_id, hook_event_name, tool_use_id, tool_name, llm_tool_name, tool_input` | `{hookSpecificOutput:{permissionDecision:"allow"\|"deny"\|"ask", permissionDecisionReason, updatedInput, additionalContext}}` |
| **PostToolUse** | 工具执行完成后 | 是（`decision:"block"`，事后） | 同上 + `tool_response` | `{decision:"block", reason, hookSpecificOutput:{additionalContext}}` |
| **Stop** | 智能体准备结束 Query 时 | 是（`decision:"block"` 阻止停止） | `session_id, hook_event_name, stop_hook_active, loop_count, last_assistant_message` | `{decision:"block", reason}` |
| **Notification** | 异步，不阻塞 | 否 | `session_id, hook_event_name, notification_type, message` | — |

**配置文件位置（已验证）**：
- 全局：`~/.trae-cn/hooks.json`（macOS/Linux）
- 项目：`$PROJECT_FOLDER/.trae/hooks.json`
- 兼容读取 Claude Code：`~/.claude/settings.json`、`$PROJECT_FOLDER/.claude/settings.json`

**原生 TRAE 格式**（官方文档）：

```json
{
  "version": 1,
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "<shell command>",
        "timeout": 30
      }]
    }]
  }
}
```

**关键发现：当前 `~/.trae-cn/hooks.json` 格式不匹配**

当前文件使用的是 **Claude Code 格式**（`name`/`enabled`/`command`），而非 TRAE 原生格式（`hooks` 数组 + `type`/`command`/`timeout`）：

```json
{
  "hooks": {
    "SessionStart": [{
      "name": "ldvh-session-start",
      "enabled": true,
      "command": "/Users/dmh2002/.trae-cn/plugins/ldvh/1.0.0/bin/ldvh_hook.sh",
      "timeout": 60
    }],
    "SubagentStart": [{ ... }]
  }
}
```

问题：

1. `SubagentStart` **不是 TRAE 支持的事件**（TRAE 仅支持上述 6 类），该条目会被忽略
2. `name`/`enabled`/`command` 字段层级与 TRAE 原生格式的 `hooks` 数组不对应
3. TRAE 可从 `~/.claude/settings.json` 导入 Claude Code 格式，但该文件当前**不存在**
4. LDVH 插件**未注册**于 `installed-plugins.json`（仅 Lark 插件在其中），是手动放置的

**结论：真实自动触发状态 = 未验证**。格式不匹配 + 当前会话系统提示中未观察到 LDVH 规则引导注入，强烈提示 Hook 未实际触发。这符合 pitfall-0001 记录的模式（"插件已安装已注册但环境零实时触发"）。

### 1.3 Git Hook — 已验证支持（原生 Git 机制）

| 项目 | 证据 |
|---|---|
| 机制 | 原生 Git `commit-msg` hook，与 AI 环境无关 |
| CLI 入口 | `ldvh-git-hook`（管理安装）、`ldvh-git-commit-msg`（执行检查） |
| 当前状态 | **未安装**（doctor 报告 `config_status=missing`，工作区无管辖配置） |
| 权威依据 | Git 原生 + LDVH 09.Att.01 接入面 |

### 1.4 其它机制

| 机制 | 状态 | 用于 LDVH？ |
|---|---|---|
| MCP | 已验证可用（mcp_Sequential_Thinking、mcp_context7） | 否——无生命周期，与 shell 直调 CLI 等价（spark-0039 已决策） |
| Schedule（定时任务） | 已验证可用（cron，最小 10 分钟） | 否——cron 创建新会话，非会话启动触发 |
| 插件系统 | 已验证（Lark 插件通过 installed-plugins.json 注册） | LDVH 插件手动放置但未正式注册 |

---

## 二、三层框架承载推荐

### 信息层 → Skill（已存在，需修正内容）

**理由**：

- TRAE 技能机制已验证可用，按需调用，零副作用
- 符合 spark-0039 的"单一薄引用 Skill 默认接入"决策
- Skill 不复制规则正文，只指路（CLI 路径 + 调用命令 + 如实报告纪律）

**当前问题**：现有 `~/.agents/skills/ldvh/SKILL.md` 标注为"Claude Code 原生接入"，且写"Claude Code 没有 LDVH 的 SessionStart 自动注入插件"——这对 TRAE 不准确（TRAE 支持 SessionStart Hook）。内容需修正为 TRAE 视角。

### 自动触发层 → TRAE SessionStart Hook（可选，证据触发时增设）

**理由**：

- TRAE 官方支持 SessionStart 事件，可注入 `additionalContext`
- 按 spark-0039 决策，**默认不装**；仅在以下触发条件之一满足时增设：
  1. 再次发生直写 `ldvh-base/` 绕过且跨会话被消费
  2. 无人值守/多 Agent 链路开始写事实
  3. 决定上 PreToolUse guardrail
- **当前已有 hooks.json 但格式错误，应修正或移除**

**不推荐 PreToolUse guardrail**（除非触发条件成立）：PreToolUse 的 `permissionDecision:"deny"` 是覆盖不完整的 guardrail（`--no-verify`、Human 直接操作 git、多 clone 未装均可绕过），真终闸仍是 Git Gate。

### 阻断层 → 原生 Git `commit-msg` Gate（必装，与前两层无关）

**理由**：

- 符合 spark-0039："机械防线收敛到原生 git `commit-msg` Gate"
- Git Gate 是模型之外的机械机制，不依赖 AI 环境能力
- 当前 `ldvh-git-commit-msg` 只校验 spec 03 提交契约（message 结构/候选路径/管辖绑定/快照身份），**不校验事实对象内容**——这是已知缺口（spark-0039 待做工作第 1 项）

---

## 三、Skill 放置位置、加载机制、最小内容骨架

### 放置位置与加载机制（已验证）

- **位置**：`~/.agents/skills/ldvh/SKILL.md`
- **加载**：TRAE 启动时扫描 `~/.agents/skills/`，用户意图匹配 description 时由 Skill 工具调用
- **当前实现**：符号链接 → `~/.claude/skills/ldvh/SKILL.md`（与 Claude Code 共享）

### 最小内容骨架（只指路不抄规则）

```markdown
---
name: ldvh
description: 在当前 TRAE 会话里使用与自检 LDVH。当用户要求"跑/检查/验证
  LDVH""接入自检""交付 LDVH 工作上下文""ldvh-doctor"，或询问 LDVH 在本
  环境是否生效、想用 LDVH 的规范/事实对象/Helper 能力时使用。要求如实区分
  已验证/未验证/不支持。
---

# LDVH 技能（TRAE IDE 薄引用接入）

LDVH 帮助 AI 在长期项目里"判断有据、行动可续、结果可验"。本技能是 LDVH 在
TRAE IDE 里的薄接入：只指路（CLI 路径 + 调用命令），不复制规则正文。

## 核心可执行文件（稳定绝对路径）

LDVH=<仓库根>
HELPER=$LDVH/.venv/bin/ldvh
WORKCTX=$LDVH/.venv/bin/ldvh-work-context
DOCTOR=$LDVH/.venv/bin/ldvh-doctor

## 1. 自检（只读）
"$HELPER" capabilities

## 2. 交付工作上下文（核心动作）
printf '{"hook_event_name":"SessionStart","source":"startup","cwd":"%s"}' "$(pwd)" \
  | "$WORKCTX" --helper-executable "$HELPER"

## 3. 只读诊断（可选）
"$DOCTOR" --workspace-root "$(pwd)" --work-object-locator "$(pwd)" \
  --helper-executable "$HELPER"

## 4. 如实报告（必须）
- 已验证：本次实际跑通并有输出的
- 未验证：需要 cold-start 新会话才能证明的自动触发
- 不支持：环境缺少对应能力

不要把"命令存在""文件存在"或"本技能被调用"写成"hook 已实时生效"。
```

**关键变更点**（相对当前 SKILL.md）：

1. 标题从"Claude Code 原生接入"改为"TRAE IDE 薄引用接入"
2. 删除"Claude Code 没有 SessionStart 自动注入插件"的不准确表述
3. 补充说明：TRAE 支持 SessionStart Hook，但自动触发需另行配置与验证

---

## 四、插件/Hook 方案

### 4.1 事件清单与用途

| 事件 | 用途 | 优先级 |
|---|---|---|
| SessionStart | 自动注入 LDVH 规则引导（调 `ldvh-work-context`） | 可选——证据触发时增设 |
| PreToolUse（matcher: `Edit\|Write`） | 拦截直写 `ldvh-base/` 的工具调用 | 可选——guardrail，覆盖不完整 |
| PostToolUse（matcher: `Edit\|Write`） | 写后审计（对 ldvh-base 写入跑事实完整性校验） | 可选——待 spark-0039 第 1、2 项落地 |

### 4.2 SessionStart Hook payload 与安装

**stdin（TRAE 原生）**：

```json
{
  "session_id": "...",
  "hook_event_name": "SessionStart",
  "source": "startup",
  "cwd": "/path/to/workspace",
  "workspace_roots": ["/path/to/workspace"]
}
```

**stdout（成功时，TRAE 原生格式）**：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ldvh-work-context 返回的规则引导原文>"
  }
}
```

**hooks.json（TRAE 原生格式，修正后）**：

```json
{
  "version": 1,
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/dmh2002/.trae-cn/plugins/ldvh/1.0.0/bin/ldvh_hook.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

**安装位置**：`~/.trae-cn/hooks.json`（全局）或 `$PROJECT_FOLDER/.trae/hooks.json`（项目级）

**当前适配器脚本状态**：`ldvh_hook.sh` 调用 `codex_context.py`，后者正确调用 `ldvh-work-context` 并输出 `hookSpecificOutput.additionalContext`——**成功路径输出格式匹配 TRAE**。但失败路径使用 `systemMessage` 字段，TRAE 不识别该字段，会静默丢弃错误信息。

### 4.3 信任/启用步骤

1. Human 在 TRAE IDE 中进入 **设置 > Hooks**
2. 点击"创建"按钮，选择全局或项目 Hook
3. 在安全警示面板中阅读提示，点击"启用"
4. TRAE 创建 `hooks.json`，编辑为上述 TRAE 原生格式
5. 设置 Hook 命令运行方式（沙箱或本地自动）

### 4.4 cold start 区分真实触发与历史恢复（hydrate）

| 观察 | 真实触发 | hydrate 伪装 |
|---|---|---|
| **新会话系统提示** | 包含 LDVH 规则引导原文（specs/00 §8.1/§8.2） | 无，或只有模糊提及 |
| **CLI 调用痕迹** | 新会话启动时 Hook 进程有执行日志 | 无执行记录 |
| **source 字段** | work-context 核心收到 `source:"startup"` | 可能缺失或为其它值 |
| **可复现性** | 每次新会话均触发 | 仅偶尔出现（来自缓存/恢复） |
| **验证方法** | 开新会话 → 检查系统提示是否含规则引导 → 回查 Hook 进程日志 | — |

**pitfall-0001 的教训**：hydrated 上下文可伪装成已注入。唯一可靠验证是 cold start：关闭当前会话 → 开新会话 → 观察是否自动出现 LDVH 规则引导。

---

## 五、安装/部署/接入/验证四层方案

### 5.1 安装（已由 Human 完成）

| 步骤 | 状态 | 谁做 |
|---|---|---|
| `python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'` | 已完成 | Human |
| 验证 `.venv/bin/ldvh capabilities` 返回 `outcome=ok` | 已验证（15 操作） | AI |
| LDVH 插件文件放置于 `~/.trae-cn/plugins/ldvh/1.0.0/` | 已存在（手动放置） | Human |

### 5.2 部署（部分完成，需修正）

| 步骤 | 状态 | 谁做 |
|---|---|---|
| Skill 放置于 `~/.agents/skills/ldvh/SKILL.md` | 已存在（符号链接） | Human/AI |
| Skill 内容修正为 TRAE 视角（去掉"Claude Code"标注） | **待做** | AI（编辑文件） |
| hooks.json 修正为 TRAE 原生格式 | **待做** | AI（编辑文件，Human 授权） |
| 移除不存在的 `SubagentStart` 事件 | **待做** | AI（编辑文件） |
| 修正适配器失败路径输出（`systemMessage` → TRAE 兼容格式） | **待做** | AI（在 LDVH 仓库 code/ 中修改） |
| Git `commit-msg` Gate 安装（`ldvh-git-hook install`） | **待做** | AI 执行，Human 授权 `--confirm-human-gate` |

### 5.3 接入（需 cold start 验证）

| 步骤 | 状态 | 谁做 |
|---|---|---|
| TRAE 识别 hooks.json 并在 SessionStart 触发 Hook | **未验证** | TRAE 运行时 |
| Hook 成功调用 `ldvh-work-context` 并返回规则引导 | CLI 直调已验证，自动触发未验证 | TRAE 运行时 |
| 规则引导注入到 AI 系统提示 | **未验证** | TRAE 运行时 |
| Git commit-msg Gate 在实际 commit 时触发 | **未验证**（未安装） | Git 运行时 |

### 5.4 验证（需 cold start + Human 观察）

| 验证对象 | 方法 | 谁做 |
|---|---|---|
| CLI 直调 | `ldvh capabilities` / `ldvh-work-context` / `ldvh-doctor` | AI（已完成） |
| Skill 加载 | Skill 工具调用 `ldvh` | AI（已完成） |
| SessionStart 真实触发 | **关闭当前会话 → 开新会话 → 检查系统提示是否含 LDVH 规则引导** | **Human**（只有 Human 能开新会话并观察） |
| Hook 执行痕迹 | 检查 Hook 进程日志或 work-context 调用痕迹 | Human/AI |
| Git Gate 真实触发 | 在受管 worktree 中执行 `git commit`，观察是否被 Gate 拦截 | Human/AI |
| 回滚验证 | 禁用 Hook 后开新会话，确认 LDVH 上下文不再注入 | Human |

### 5.5 只能由 Human 完成的步骤

1. **安装 LDVH pip 包**（已完成后无需重复）
2. **TRAE IDE 中启用 Hooks**（设置 > Hooks > 创建/启用，需在安全警示面板确认）
3. **设置 Hook 运行方式**（沙箱或本地自动——涉及安全决策）
4. **cold start 验证**（关闭当前会话、开新会话、观察系统提示——AI 无法自行开新会话）
5. **Git Gate 安装授权**（`ldvh-git-hook install --confirm-human-gate`）
6. **管辖项目配置**（`LDVH-GOVERNED-PROJECTS.yaml`——02 规范保留给 Human 的判断）

---

## 如实区分四层（总结）

| 层次 | 当前状态 | 证据 |
|---|---|---|
| 静态文件存在 | **已验证** | 6 个 CLI 入口 + 插件 + hooks.json + Skill 均存在 |
| CLI 直调可用 | **已验证** | `ldvh capabilities`→ok(15 ops)；`ldvh-work-context`→ok(规则引导)；`ldvh-doctor`→attention(5/5 surfaces) |
| 真实自动触发 | **未验证** | hooks.json 格式不匹配 TRAE 原生格式；`SubagentStart` 非有效事件；当前会话无 LDVH 注入痕迹；适配器失败路径输出字段不兼容 |
| 已验证（完整接入） | **否** | 无 cold start 证据；无 Git Gate 安装；无管辖配置 |

**能力缺口声明**：

- `unsupported`：无（TRAE 支持所需全部机制：Skill + SessionStart Hook + Git hook）
- `unverified`：SessionStart Hook 真实触发、Git Gate 真实触发、规则引导自动注入到 AI 上下文

---

## 参考资料

- [通过 Hook 实现自动化](https://docs.trae.cn/ide_automate-actions-with-hooks)
- [Hook 配置详解](https://docs.trae.cn/ide_hook-configuration-reference)
- [通过企业 Hook 实现自动化](https://docs.volcengine.com/docs/86677/2558676)
- [TRAE Release Notes](https://releasebot.io/updates/trae)
