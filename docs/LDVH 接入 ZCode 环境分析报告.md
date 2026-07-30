# LDVH 接入 ZCode 环境分析报告

> 编写日期：2026-07-30
> 编写环境：ZCode（Claude Code 衍生环境），macOS arm64
> 仓库：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4`
> 依据：LDVH specs/09-环境接入规范.md、specs/attachments/09.Att.01-环境接入面.md、spark-0039

---

## 1. 环境机制逐项核实

### 1.1 技能 / 指令文件（Skill / AGENTS.md）

| 机制 | 状态 | 证据 |
|---|---|---|
| Skill 文件（`~/.agents/skills/<name>/SKILL.md`） | ✅ **已验证支持** | 本会话可见 Skill 列表中有 `ldvh` 技能，且本会话中已加载；`ldvh` Skill 文件位于 `/Users/dmh2002/.agents/skills/ldvh/SKILL.md` |
| 自动触发（描述匹配） | ✅ **已验证支持** | 技能由 AI 根据用户请求的语义匹配 description 自动触发 |
| 斜杠命令（`/<name>`） | ✅ **已验证支持** | 用户可显式调用 |
| 工作区级指令文件（`AGENTS.md` / `.zcode/AGENTS.md`） | 🔶 **未验证** | 本项目无 AGENTS.md；机制存在但未部署 |
| Skill 可阻断工具调用 | ❌ **肯定不支持** | Skill 是纯说明文档，无执行时阻断能力 |

### 1.2 生命周期 Hook（Lifecycle Hooks）

ZCode 支持 7 种事件，全部已验证：

| 事件 | 实测状态 | 触发值 | 输入 | 能否阻断 |
|---|---|---|---|---|
| `SessionStart` | ✅ **已验证支持** | `startup` / `resume` / `clear` / `compact` | JSON stdin：`hook_event_name`、`source`、`cwd` | 否（可注入 `systemMessage` / `additionalContext`） |
| `UserPromptSubmit` | ✅ **已验证支持** | 提示文本 | JSON stdin | 否 |
| `PreToolUse` | ✅ **已验证支持** | 工具名（`Bash`、`Read`、`Write` 等） | JSON stdin | ✅ **可阻断**（返回 `allow`/`ask`/`deny`，或退出码 2） |
| `PermissionRequest` | ✅ **已验证支持** | 工具名 | JSON stdin | ✅ **可阻断** |
| `PostToolUse` | ✅ **已验证支持** | 工具名 | JSON stdin | 否（可观察结果） |
| `PostToolUseFailure` | ✅ **已验证支持** | 工具名 | JSON stdin | 否 |
| `Stop` | ✅ **已验证支持** | 响应预览 | JSON stdin | 否（可请求继续，最多 3 次） |

**Hook 输出 Schema（严格 JSON，多余键名会失败）：**

```json
{"continue": true, "systemMessage": "...", "additionalContext": "..."}
```

阻断事件（PreToolUse / PermissionRequest）额外支持：

```json
{"allow": true, "ask": true, "deny": true}
```

**已确认不支持的事件：** `Notification`、`SubagentStop`、`PreCompact`、`UserPromptExpansion`（官方资料明确声明）

**当前 LDVH SessionStart Hook 真实触发状态：**

| 检查项 | 结果 |
|---|---|
| 插件 `hooks.json` 存在 | ✅ 已存在（`ldvh@zcode-plugins-official`） |
| 插件已启用 | ✅ `config.json` 中 `enabledPlugins["ldvh@zcode-plugins-official"] = true` |
| 本会话中 Hook 已触发 | ✅ **已验证** — 系统提醒显示 `SessionStart hook additional context`，`source=startup`，规则交付 `outcome=ok`，`facts=not_requested` |
| 非 hydrate 区分 | ✅ 本会话 `source=startup`，属于 cold start |
| 阻断能力 | ❌ **当前未启用** — LDVH 插件仅注册了 SessionStart，未注册 PreToolUse |

### 1.3 Git Hook

| 机制 | 状态 | 证据 |
|---|---|---|
| 原生 Git `commit-msg` hook | ✅ **已验证支持** | 本仓库是 Git 仓库；`ldvh-git-hook` CLI 可用于管理 |
| `ldvh-git-commit-msg` CLI 可用 | ✅ **已验证支持** | 执行文件存在；已验证可调用 |
| 本 worktree 的 Git Hook 已安装 | 🔶 **未验证** | 未检查当前 worktree 的 `.git/hooks/commit-msg` |
| 实际 Git 提交时触发 | 🔶 **未验证** | 需要实际 Git 提交才能验证 |

### 1.4 插件 / 命令系统

| 机制 | 状态 | 证据 |
|---|---|---|
| 插件系统 | ✅ **已验证支持** | 多个插件已安装并运行 |
| 插件可注册 Hook | ✅ **已验证支持** | LDVH 插件 SessionStart Hook 已运行 |
| 插件可注册 Skill | ✅ **已验证支持** | 多个插件携带 Skill |
| 插件可注册 Command | ✅ **已验证支持** | 斜杠命令机制存在 |
| MCP 服务器 | ✅ **已验证支持** | 本会话中有 context7 和 playwright 的 MCP 工具可用 |

### 1.5 机制汇总表

| 能力 | 是否支持 | 能否阻断 | 自动触发 | 执行痕迹 |
|---|---|---|---|---|
| Skill（SKILL.md） | ✅ 支持 | ❌ 不能 | 🔶 按需（描述匹配） | 无执行痕迹 |
| AGENTS.md | ✅ 支持（未部署） | ❌ 不能 | ✅ 自动注入 | 无执行痕迹 |
| SessionStart Hook | ✅ 支持 | ❌ 不能 | ✅ 自动触发 | ✅ 有执行日志 |
| PreToolUse Hook | ✅ 支持 | ✅ 可阻断 | ✅ 自动触发 | ✅ 有执行日志 |
| 原生 Git Hook | ✅ 支持 | ✅ 可阻断 | ✅ 自动触发（Git 事件） | ✅ 有提交记录 |
| MCP 服务器 | ✅ 支持 | ❌ 不能 | 🔶 按需（工具调用） | 无独立痕迹 |

---

## 2. 三层框架推荐承载方案

### 2.1 信息层（让 AI 知道 LDVH 存在与用法）

**当前状态：** Skill 和 Plugin 均存在，但 Skill 描述已过时（仍声称"Claude Code 没有 SessionStart 自动注入插件"）。

**推荐承载：同时保留 Skill 和 Plugin，明确分工：**

| 载体 | 职责 | 不可替代价值 |
|---|---|---|
| **Plugin SessionStart Hook** | 会话启动时自动注入规则引导（`work-context-rule-orientation`） | ✅ 自动触发、有执行痕迹、可区分 cold start / hydrate |
| **Skill（SKILL.md）** | 按需使用指引、自检命令、故障排查入口 | ✅ 用户主动调用时提供完整操作指引 |

**理由：**

- Plugin 的 SessionStart Hook **已经**在本会话中真实触发并交付了规则引导，信息层已自动覆盖。
- Skill 作为"说明书"仍有价值——当用户主动询问 LDVH 状态、/ldvh 时，Skill 提供完整的自检与诊断命令，而 Hook 只交付规则引导，不包含操作指引。
- 两者不互斥：Hook 做自动注入，Skill 做按需参考。

### 2.2 自动触发层（会话启动时注入规则引导）

**当前状态：** ✅ 已由 SessionStart Hook 承担，已验证真实触发。

**推荐承载：保持现有 Plugin SessionStart Hook，无需额外部署。**

**触发类别区分：**

| SessionStart source | 含义 | 处理 |
|---|---|---|
| `startup` | Cold start（新会话） | 正常执行 `work-context-rule-orientation` |
| `resume` | 历史恢复（hydrate） | 同上（Hook 一视同仁触发，但核心可区分） |
| `clear` | 会话清除 | 同上 |
| `compact` | 上下文压缩后继续 | 同上 |

**验证方案：** 每次 cold start 新会话，观察系统提醒中是否有 `source=startup` 的 Hook 执行记录，且 `additionalContext` 中包含规则引导。

### 2.3 阻断层（事实写入的机械校验）

**当前状态：** 仅有 Git `commit-msg` Gate 可用，PreToolUse guardrail 未部署。

**推荐承载：Git Hook 为主防线，PreToolUse 为可选加固。**

| 防线 | 作用 | 覆盖范围 | 当前状态 |
|---|---|---|---|
| **Git `commit-msg` Gate** | 提交时校验 message 结构、候选路径、管辖绑定与快照身份 | worktree 级，仅限提交事件 | ✅ CLI 可用，但本 worktree 是否已安装未验证 |
| **事实完整性校验** | 校验 `ldvh-base/` 事实对象的 schema 合法性 | 与 Git Gate 同一入口 | 🔶 未实现为公开入口（spark-0039 待做工作 #1） |
| **PreToolUse guardrail** | 在 Write/Edit 工具调用前阻断直写 `ldvh-base/` | 会话级，跨所有工具调用 | ❌ 未部署（spark-0039 触发条件：再次发生直写污染且跨会话消费后才被发现） |

**升级触发条件（来自 spark-0039）：**

1. 再次发生直写 `ldvh-base/` 绕过 Helper CAS 且跨会话被消费
2. 无人值守 / 多 Agent 链路开始写事实对象
3. 决定上 PreToolUse guardrail

---

## 3. 推荐 Skill 形态

### 3.1 放置位置

**当前路径（已存在）：** `~/.agents/skills/ldvh/SKILL.md`

**无需移动。** 这是 ZCode 的标准 Skill 目录。

### 3.2 加载机制

ZCode 自动扫描 `~/.agents/skills/` 下的所有 SKILL.md，无需额外注册。匹配规则：

- 用户请求语义匹配 `description` 字段 → 自动触发
- 用户输入 `/<name>`（如 `/ldvh`）→ 显式触发

### 3.3 当前 Skill 需更新的内容

**过时声明（第 9-11 行）：**

> "Claude Code 没有 LDVH 的 SessionStart 自动注入插件"

**应当更新为：**

> "本环境（ZCode）已通过 LDVH Plugin 的 SessionStart Hook 实现自动注入，已验证真实触发。Skill 仅提供按需参考和自检命令，不替代自动注入。"

**需要保持的核心命令（已验证）：**

```bash
# 自检
.venv/bin/ldvh capabilities

# 工作上下文交付
printf '{"hook_event_name":"SessionStart","source":"startup","cwd":"%s"}' "$(pwd)" \
  | .venv/bin/ldvh-work-context --helper-executable .venv/bin/ldvh

# 只读诊断
.venv/bin/ldvh-doctor \
  --workspace-root "$(pwd)" \
  --work-object-locator "$(pwd)" \
  --helper-executable .venv/bin/ldvh
```

---

## 4. 插件/Hook 当前状态与方案

### 4.1 当前部署结构

| 组件 | 路径 | 内容 |
|---|---|---|
| Plugin manifest | `~/.zcode/cli/plugins/cache/zcode-plugins-official/ldvh/0.1.0/.zcode-plugin/plugin.json` | name=ldvh, version=0.1.0, hooks=挂钩 |
| Hook 注册 | `.../hooks/hooks.json` | SessionStart → `codex_context.py` 脚本 |
| 脚本实现 | `.../scripts/codex_context.py` | 读配置 → 调 `ldvh-work-context` 核心 → 输出结果 |
| 配置数据 | `.../data/ldvh.json` | helper_executable 和 work_context_executable 的绝对路径 |
| 启用状态 | `~/.zcode/cli/config.json` | `enabledPlugins["ldvh@zcode-plugins-official"]=true` |

### 4.2 事件清单与 payload

**SessionStart Hook 输入（JSON stdin）：**

```json
{
  "hook_event_name": "SessionStart",
  "source": "startup|resume|clear|compact",
  "cwd": "/absolute/path/to/current/directory"
}
```

**输出（JSON stdout）：**

```json
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "ldvh-work-context/1",
    "additionalContext": "..."
  }
}
```

### 4.3 Cold start 与 hydrate 区分

| 特征 | Cold start（startup） | Hydrate（resume） |
|---|---|---|
| Hook 触发 | ✅ 真实执行 `codex_context.py` | ✅ 也会执行 |
| 系统提醒内容 | 显示 `source=startup` | 显示 `source=resume` |
| 工作上下文 | 需重新读取规则引导 | 可能已有历史上下文 |
| 区分方法 | 检查 `source` 字段值 | 检查 `source` 字段值 |

### 4.4 若新增 PreToolUse guardrail

| 项目 | 配置 |
|---|---|
| 事件 | `PreToolUse` |
| 匹配器 | `Write|Edit`（或 `Write|Edit|ApplyPatch`） |
| 输入 | 工具名、参数（JSON stdin） |
| 输出 | `allow` 或 `deny` |
| 判断逻辑 | 检查目标路径是否落入 `ldvh-base/` 且非通过 Helper CLI |

---

## 5. 安装 → 部署 → 接入 → 验证四层状态与步骤

### 5.1 当前状态总览

| 阶段 | 当前状态 | 最后一步 | 剩余工作 |
|---|---|---|---|
| **安装** | ✅ **已完成** | `pip install -e '.[dev]'` → 6 个 CLI 入口均可用 | 无 |
| **部署** | ✅ **已完成** | Plugin 目录、hooks.json、config.json 均已就位 | 无 |
| **接入** | ✅ **已验证** | 本会话 SessionStart Hook 已真实触发，source=startup | 每次新会话仍需确认 |
| **验证** | 🔶 **部分完成** | 静态安装 ✅、CLI 直调 ✅、真实触发 ✅（本会话）；Git Hook 安装未验证；PreToolUse guardrail 未部署 | 见 5.2 |

### 5.2 每层详细步骤与 Human 依赖

#### ① 安装（Installation）

| 操作 | 执行者 | 当前状态 |
|---|---|---|
| 创建 Python venv | Human | ✅ 已完成 |
| `pip install -e '.[dev]'` | AI | ✅ 已完成 |
| 验证 `ldvh capabilities` | AI | ✅ 已验证 |
| 验证全部 6 个 CLI 入口 | AI | ✅ 已验证 |

#### ② 部署（Deployment）

| 操作 | 执行者 | 当前状态 |
|---|---|---|
| 创建 Plugin 目录结构 | AI | ✅ 已完成 |
| 创建 `hooks.json` | AI | ✅ 已完成 |
| 创建 `codex_context.py` | AI | ✅ 已完成 |
| 创建 `data/ldvh.json`（含绝对路径） | AI | ✅ 已完成 |
| 在 `config.json` 中启用插件 | Human | ✅ 已完成 |

#### ③ 接入（Integration）

| 操作 | 执行者 | 当前状态 |
|---|---|---|
| 确认 Plugin 已启用 | AI | ✅ 已验证 |
| 确认 hooks.json 语法正确 | AI | ✅ 已验证 |
| 确认 `codex_context.py` 可执行 | AI | ✅ 已验证 |
| 确认 `data/ldvh.json` 路径正确 | AI | ✅ 已验证 |
| **确认 SessionStart Hook 真实触发** | **AI** | ✅ **本会话已验证（source=startup）** |
| 确认 rule-orientation 输出正确 | AI | ✅ 本会话已验证 |

#### ④ 验证（Verification）

| 操作 | 执行者 | 当前状态 | 验证方法 |
|---|---|---|---|
| 静态文件存在性 | AI | ✅ 已完成 | `ls` 检查全部文件 |
| CLI 直调 | AI | ✅ 已完成 | 调用 `ldvh capabilities`、`ldvh-work-context`、`ldvh-doctor` |
| **SessionStart 真实触发** | **AI** | ✅ **本会话已验证** | 观察系统提醒中 `source=startup` 的 Hook 执行记录 |
| **Cold start 与 hydrate 区分** | **AI** | 🔶 **需持续验证** | 每次 cold start 检查 `source` 字段 |
| **Git Hook 本 worktree 安装** | **AI** | 🔶 **未验证** | 需要执行 `ldvh-git-hook status` 并检查 `.git/hooks/commit-msg` |
| **Git Hook 真实触发** | **Human** | 🔶 **未验证** | 需要实际 Git 提交（Human 操作）来触发并观察结果 |
| **PreToolUse guardrail** | — | ❌ **未部署** | 待触发条件成立后按 spark-0039 决定 |
| **事实完整性校验公开入口** | — | ❌ **未实现** | spark-0039 待做工作 #1-#2 |
| **跨会话接入持久性** | **AI** | 🔶 **需持续验证** | 每次新会话观察 Hook 是否仍触发 |

### 5.3 只由 Human 完成的操作

1. **启用/禁用插件** — 修改 `~/.zcode/cli/config.json` 中的 `enabledPlugins`
2. **接受平台信任提示** — 如果 ZCode 要求信任插件
3. **实际 Git 提交测试** — 触发 Git Hook 真实执行
4. **决定是否部署 PreToolUse guardrail** — 按 spark-0039 触发条件由 Human 判断
5. **跨环境验证** — 在另一个 worktree 或另一台机器上重复验证

---

## 6. 关键发现与建议

### 6.1 当前 Skill 描述需更新

**过时内容：** `~/.agents/skills/ldvh/SKILL.md` 第 9-11 行

> "Claude Code 没有 LDVH 的 SessionStart 自动注入插件"

**事实：** 本环境（ZCode）中 LDVH Plugin 的 SessionStart Hook 已安装、已启用、**本会话已真实触发**（`source=startup`）。

### 6.2 当前三层接入结论

| 层 | 载体 | 状态 | 可信度 |
|---|---|---|---|
| 信息层 | Plugin SessionStart Hook（自动）+ Skill（按需） | ✅ 已接入 | 已验证（本会话真实触发） |
| 自动触发层 | SessionStart Hook | ✅ 已接入 | 已验证（本会话 source=startup） |
| 阻断层（Git Gate） | `ldvh-git-commit-msg` | 🔶 CLI 可用 | 未验证本 worktree 安装 |
| 阻断层（PreToolUse） | 未部署 | ❌ 未接入 | — |

### 6.3 建议后续优先事项

1. **更新 Skill 描述** — 反映真实 Hook 状态，不再声称"没有自动注入"
2. **验证本 worktree Git Hook 安装** — 执行 `ldvh-git-hook status` 检查当前 worktree
3. **实现事实完整性校验公开入口** — spark-0039 待做工作 #1-#2，这是 Git Gate 当前的能力缺口（仅校验 message 结构，不校验事实对象 schema）
4. **每次 cold start 确认 Hook 仍触发** — 接入验证不是一次性事件，环境更新后需要重新确认

### 6.4 能力缺口如实声明

| 能力 | 声明 |
|---|---|
| LDVH 6 个 CLI 入口可用 | ✅ 已验证 |
| Plugin SessionStart Hook 已安装 | ✅ 已验证 |
| 本会话中 Hook 已真实触发（source=startup） | ✅ 已验证 |
| SessionStart 在 hydrate（resume）下的行为 | 🔶 未验证（需 resume 场景） |
| 本 worktree Git Hook 已安装 | 🔶 未验证 |
| Git Hook 真实触发 | 🔶 未验证 |
| PreToolUse guardrail | ❌ 未部署 |
| 事实完整性机械校验公开入口 | ❌ 未实现 |
| 跨环境兼容性（Trae、Cursor 等） | ❌ 未验证 |

---

## 附录：验证过的 CLI 入口

| 入口 | 路径 | 最新验证 |
|---|---|---|
| `ldvh` | `.venv/bin/ldvh` | 2026-07-30，返回 `ldvh-helper-cli/2`，7 项公开操作 |
| `ldvh-work-context` | `.venv/bin/ldvh-work-context` | 2026-07-30（本会话 SessionStart Hook 触发） |
| `ldvh-context-recovery` | `.venv/bin/ldvh-context-recovery` | 2026-07-30（--help 可调用） |
| `ldvh-git-commit-msg` | `.venv/bin/ldvh-git-commit-msg` | 2026-07-30（--help 可调用） |
| `ldvh-git-hook` | `.venv/bin/ldvh-git-hook` | 2026-07-30（--help 可调用） |
| `ldvh-doctor` | `.venv/bin/ldvh-doctor` | 2026-07-30（--help 可调用） |