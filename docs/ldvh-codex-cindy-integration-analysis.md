# LDVH 接入 Codex (Cindy) 环境分析报告

> 报告生成时间：2026-07-30
> 执行环境：Cindy / Claude Code（同一机器上并存 Codex 配置于 `~/.codex`）
> 目标环境：Codex (Cindy) 会话环境
> 验证范围：以 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4` 为当前 LDVH 发行物与工作对象

---

## 1. 环境机制调查

### 1.1 技能 / 指令文件（Skill）

| 项目 | 状态 | 依据 |
|---|---|---|
| 支持定义 | ✅ 已验证 | 当前会话 `<skills_instructions>` 已加载 `ldvh` 技能；技能文件为 YAML frontmatter + Markdown body 格式，符合 Claude Code Skill 规范 |
| 当前位置 | ✅ 已验证 | `~/.claude/skills/ldvh/SKILL.md`（Claude Code 路径） |
| 触发方式 | ✅ 已验证 | 通过 YAML `name` / `description` 语义匹配；本会话可用技能列表中已出现 `ldvh` |
| Codex 用户技能路径 | ❓ 未验证 | `~/.codex/skills/` 下仅见 `.system/` 系统技能目录，未见用户技能目录；Codex 是否从 `~/.codex/skills/<name>/SKILL.md` 加载用户技能，当前无官方资料或实证 |

**实测对象：**

```bash
# 技能文件存在且已加载
~/.claude/skills/ldvh/SKILL.md

# 系统提示中可用技能列表包含 ldvh
```

**结论：** 当前 Cindy/Claude Code 环境支持 Skill；LDVH 技能已在位，但内容仍指向 "Claude Code 没有 SessionStart 自动注入插件"，与目标环境（Codex 插件已部署）不完全一致，需要更新。

### 1.2 生命周期 Hook

| 项目 | 状态 | 依据 |
|---|---|---|
| 事件支持 | ✅ 已验证配置存在 | Codex 插件 `ldvh@personal` 的 `hooks/hooks.json` 声明了 `SessionStart`（matcher: `startup|resume|clear|compact`）和 `SubagentStart` |
| Hook 类型 | ✅ 已验证 | `type: command`，运行 `codex_context.py`；输出可包含 `systemMessage` 与 `hookSpecificOutput` |
| 能否阻断工具调用 | ❌ 肯定不支持 | 当前 Codex hook 机制无 `PreToolUse deny` 语义；`ldvh@personal` 的 `pre_tool_use` hook state 为 `enabled = false`；`~/.codex/hooks.json` 全局 hooks 为空，亦无阻断配置 |
| 真实触发 | ❓ 未验证 | 本会话非 cold start，无法区分当前已加载的 LDVH 上下文来自实时 hook 还是 hydrate/历史恢复；需要新会话验证 |
| MCP 生命周期 | ❌ 肯定不支持 | MCP 仅为工具调用通道，无 session lifecycle / 自动注入语义 |

**实测对象：**

```bash
# 插件 hooks（已缓存）
~/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260722092023/hooks/hooks.json

# 全局 hooks（当前为空）
~/.codex/hooks.json  -> {"hooks": {}}

# 主配置中的启用状态
~/.codex/config.toml:
  [plugins."ldvh@personal"]
  enabled = true

  [hooks.state."ldvh@personal:hooks/hooks.json:session_start:0:0"]
  enabled = true

  [hooks.state."ldvh@personal:hooks/hooks.json:subagent_start:0:0"]
  enabled = true
```

**注意：** `~/.codex/config.toml` 中同时存在对全局 `~/.codex/hooks.json` 的 hook state 记录，但当前全局 `hooks.json` 内容为空；这些记录可能是历史残留，不代表当前全局 hook 生效。

### 1.3 Git Hook

| 项目 | 状态 | 依据 |
|---|---|---|
| 原生 git hook | ✅ 已验证 | 标准 git hook 机制不依赖 AI 环境；`ldvh-git-hook` 管理 CLI 可用 |
| LDVH commit-msg Gate | ✅ 已验证已安装 | 在 LDVH 工作树运行 `ldvh-git-hook status` 返回 `LDVH owns the current Git commit-msg Hook` |

**实测对象：**

```bash
$ /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh-git-hook \
    status --worktree /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4

LDVH Git commit-msg Hook managed: LDVH owns the current Git commit-msg Hook
worktree: /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4
hook: /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.githooks-v4/commit-msg
```

**边界：** 当前 `ldvh-git-commit-msg` 仅校验提交契约（message 结构、管辖绑定等），**不校验事实对象 Schema**（见 `spark-0039` 待做 #1）。因此 "提交终闸" 对事实完整性当前不成立。

---

## 2. 三层框架推荐方案

### Layer 1 — 信息层：让 AI 知道 LDVH 存在与用法

**推荐：** Skill（薄引用技能）

**理由：**
- 当前环境已支持并加载 Skill；`ldvh` 技能已在 `~/.claude/skills/ldvh/SKILL.md`。
- Skill 与 Codex 环境 Hook 在信息投递层效果等价（spark-0039 结论），但 Skill 更轻量、无需平台信任/重启。
- 当前插件 Hook 的 "必然注入" 尚未经 cold start 验证，不能作为默认信息层。

**应做：**
1. 更新 `~/.claude/skills/ldvh/SKILL.md`：移除 "Claude Code 没有 SessionStart 自动注入插件" 的局限性表述；改为 "Codex 插件 `ldvh@personal` 已部署，但真实自动触发需 cold start 验证"。
2. 若目标明确为纯 Codex 环境，可将 Skill 复制/迁移到 `~/.codex/skills/ldvh/SKILL.md`；**注意**：`~/.codex/skills/` 用户技能加载路径当前未经验证，迁移后需在新的 Codex 会话中确认加载。
3. 不将规则正文、模板清单、Helper 字段硬编码进 Skill；只指路，不抄规则。

### Layer 2 — 自动触发层：会话启动注入规则引导

**推荐：** 保留当前 `ldvh@personal` 插件 Hook 配置，但标记为 **未验证**，暂不升级为 "默认自动注入"。

**理由：**
- 插件 manifest、hooks、config 均已部署并启用（`session_start` / `subagent_start`）。
- 但 `spark-0039` 与 `pitfall-0001` 均指出：插件已安装不等于环境实时触发；hydrate 可伪装成已注入。
- 升级到 "自动注入为默认" 的证据触发条件（spark-0039）：再次发生直写污染且跨会话消费、无人值守/多 Agent 链路写事实、或决定交付 PreToolUse guardrail。当前无一成立。

**应做：**
- 维持 `ldvh@personal` 插件启用状态不变。
- Human 执行 cold start 新会话验证，观察 `hook_run_started` / `hook_run_completed` 日志与 `hookSpecificOutput` 产物。
- 验证通过前，信息层仍以 Skill 为主。

### Layer 3 — 阻断层：事实写入的机械校验

**推荐：** 原生 Git `commit-msg` Gate

**理由：**
- 唯一真实阻断机制；已安装于 LDVH 工作树。
- 跨所有 AI 环境生效，不依赖 Codex/Cindy。
- 当前缺口：`ldvh-git-commit-msg` 尚未校验事实对象 Schema（spark-0039 待做 #1）。

**应做：**
- 保持当前 Git hook 安装。
- 待 spark-0039 #1 落地后，更新 Git Gate 并重新验证事实完整性校验。

---

## 3. Skill 实施细节

### 3.1 放置位置

当前已生效位置：

```
~/.claude/skills/ldvh/SKILL.md
```

候选 Codex 用户技能位置（迁移后需验证加载）：

```
~/.codex/skills/ldvh/SKILL.md
```

system 级位置（需更高信任，当前不推荐）：

```
~/.codex/skills/.system/ldvh/SKILL.md
```

### 3.2 加载机制

- Claude Code / Cindy：将 `SKILL.md` 置于 `~/.claude/skills/<name>/SKILL.md`，会话启动时自动进入 `<skills_instructions>`。
- Codex（待验证）：若支持用户技能，路径可能为 `~/.codex/skills/<name>/SKILL.md`；当前仅确认 `.system/` 系统技能被加载。

### 3.3 最小内容骨架

```yaml
---
name: ldvh
description: 在当前 Codex / Cindy 会话中使用与自检 LDVH（LD Vibe Harness）。当用户要求“跑/检查/验证 LDVH”“接入自检”“交付 LDVH 工作上下文”“ldvh-doctor”，或询问 LDVH 在本环境是否生效、想用 LDVH 的规范/事实对象/Helper 能力时使用。提供核心直调、工作上下文交付与只读诊断的标准命令，并要求如实区分已验证/未验证/不支持。
---

# LDVH 技能（Codex / Cindy 原生接入）

——本文件只指路，不抄规则。全部规则和契约在 LDVH 仓库规范中，AI 踩到对应步骤时按规范入口读取。

## 核心可执行文件

```
LDVH=/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4
HELPER=$LDVH/.venv/bin/ldvh
WORKCTX=$LDVH/.venv/bin/ldvh-work-context
DOCTOR=$LDVH/.venv/bin/ldvh-doctor
```

用 `ldvh capabilities` 验证核心可用。

## 交付工作上下文（本技能核心动作）

普通入口：

```bash
printf '{"hook_event_name":"SessionStart","source":"startup","cwd":"%s"}' "$(pwd)" \
  | "$WORKCTX" --helper-executable "$HELPER"
```

- `facts` 恒为 `not_requested`；本调用只交付规则引导。
- 使用前确保当前会话不在 recover/hydrate 路径。

## 事实恢复（AI 已进入事实消费分支时）

需要事实对象时，用 `ldvh-context-recovery` 或 `$HELPER call <operation_key>`（按 09 入口选择 §2）。

## 只读诊断

```bash
"$DOCTOR" \
  --workspace-root "$(pwd)" \
  --work-object-locator "$(pwd)" \
  --helper-executable "$HELPER"
```

`doctor` 只查发行物/Helper/配置静态存在性，不证明真实触发。

## 如实报告要求

- **已验证** — 本次实际跑通并有输出的（核心直调、work-context 交付、git hook 安装）。
- **未验证** — 需要 cold-start 新会话才能证明的"自动触发"（SessionStart hook 真实触发）。
- **不支持** — 环境缺少对应能力（如 Codex 无 PreToolUse guardrail）。

不要把"命令存在""文件存在"或"本技能被调用"写成"hook 已实时生效"。
```

---

## 4. Plugin Hook 相关

### 4.1 事件清单（`hooks.json`）

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [{
          "type": "command",
          "command": "python3 -X utf8 \"${PLUGIN_ROOT}/scripts/codex_context.py\"",
          "commandWindows": "py -3.12 -X utf8 \"${PLUGIN_ROOT}\\scripts\\codex_context.py\"",
          "timeout": 60,
          "statusMessage": "Loading LDVH rule context"
        }]
      }
    ],
    "SubagentStart": [{
      "hooks": [{
        "type": "command",
        "command": "python3 -X utf8 \"${PLUGIN_ROOT}/scripts/codex_context.py\"",
        "commandWindows": "py -3.12 -X utf8 \"${PLUGIN_ROOT}\\scripts\\codex_context.py\"",
        "timeout": 60,
        "statusMessage": "Loading LDVH rule context"
      }]
    }]
  }
}
```

### 4.2 安装位置

| 对象 | 路径 |
|---|---|
| 插件 manifest | `code/plugins/ldvh/.codex-plugin/plugin.json`（LDVH 仓库参考实现） |
| 插件 hooks | `code/plugins/ldvh/hooks/hooks.json`（LDVH 仓库参考实现） |
| adapter 脚本 | `code/plugins/ldvh/scripts/codex_context.py`（LDVH 仓库参考实现） |
| 已安装缓存 | `~/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260722092023/` |
| 插件数据配置 | `~/.codex/plugins/data/ldvh-personal/ldvh.json` |
| 启用配置 | `~/.codex/config.toml`：`[plugins."ldvh@personal"]` `enabled = true` |

### 4.3 信任 / 启用步骤

当前已观察到的状态：

1. `~/.codex/config.toml` 中 `plugins."ldvh@personal"` 已 `enabled = true`。
2. `hooks.state."ldvh@personal:hooks/hooks.json:session_start:0:0"` 已 `enabled = true`。
3. `hooks.state."ldvh@personal:hooks/hooks.json:subagent_start:0:0"` 已 `enabled = true`。

如果未来需要重新启用或首次启用，Human 需在 Codex 设置/插件管理中：
- 启用 `ldvh@personal` 插件；
- 信任/允许 `SessionStart` 与 `SubagentStart` hook 执行。

### 4.4 Cold start 验证方法

区分真实触发与 hydrate 的关键：

1. 关闭当前所有 Codex 会话。
2. 启动全新 Codex 会话（新窗口 / 新 terminal），cwd 为 LDVH 管辖项目。
3. 观察启动日志中是否有 `hook_run_started` + `hook_run_completed` 记录。
4. 检查是否有 `hookSpecificOutput` 或 `systemMessage` 来自 LDVH 的注入。
5. 查看 `~/.codex/` 对应位置是否有 hook 执行产物。
6. 关键区分：如果 work-context 内容出现在会话中但无法回指到本次 hook 执行记录，则可能来自 hydrate，不能确认真实触发。

---

## 5. 安装 → 部署 → 接入 → 验证四层

### 第一层：安装（获取核心）

| 步骤 | 执行者 | 当前状态 |
|---|---|---|
| pip 安装 LDVH 包 | 命令行 | ✅ 已完成（`.venv` 存在） |
| 验证 6 个 CLI 入口可用 | AI / 命令行 | ✅ `ldvh capabilities` 返回 `ldvh-helper-cli/2` |
| 安装后执行 `ldvh capabilities` | AI | ✅ 已跑通（outcome=`partial`，列出 7 项公开操作） |

### 第二层：部署（放置既有单元）

| 步骤 | 执行者 | 当前状态 |
|---|---|---|
| 创建/更新 Skill 文件 | AI | ⚠️ 文件存在但内容需更新（移除 Claude Code 局限性表述，补充 Codex 插件状态） |
| 检查 Plugin manifest + hooks 完整性 | AI | ✅ 已存在，已验证 |
| 检查 Plugin 是否在 `config.toml` 中启用 | Human 确认 / AI 观察 | ✅ `ldvh@personal` 已 `enabled = true` |
| Git hook 安装 | Human Gate / AI 观察 | ✅ 已安装；`ldvh-git-hook status` 确认 LDVH 拥有 commit-msg hook |

### 第三层：接入（连接原生事件）

| 步骤 | 执行者 | 当前状态 |
|---|---|---|
| Skill → AI 知道 LDVH 存在与用法 | 自动（Skill 在 skills 目录即加载） | ✅ 当前会话已加载 |
| Plugin Hook → SessionStart 自动注入 | 环境 | ❓ 未验证——需 cold start 验证 |
| Git Hook → commit-msg Gate 阻断 | 原生 git | ✅ 已安装，待实际提交测试验证阻断行为 |

### 第四层：验证（逐事件证明）

| 验证项 | 方法 | 当前状态 |
|---|---|---|
| 静态存在 — Skill/Plugin/Hook 文件在预期位置 | `ls` / `cat` | ✅ 已验证 |
| CLI 直调可用 — 手动调用 CLI 可得预期输出 | `ldvh-work-context` 传 stdin | ✅ 已验证（`ldvh capabilities` 可运行） |
| 真实自动触发 — 新会话启动时 hook 自动运行 | Cold start + 日志检查 | ❌ 未验证 |
| Git Gate 生效 — 不合规 commit 被阻断 | 实际测试 | ❌ 待实际提交测试（虽安装未经验证阻断行为） |

---

## 6. 能力缺口清单

| 能力 | 状态 | 说明 |
|---|---|---|
| Skill 信息投递 | ✅ 已验证支持 | `ldvh` 技能已加载；内容需更新 |
| SessionStart Hook 自动注入 | ❓ 未验证 | 插件与配置已就绪，但无 cold start 证据 |
| SubagentStart Hook 自动注入 | ❓ 未验证 | 配置已启用，同样需 cold start 证据 |
| PreToolUse 阻断 | ❌ 肯定不支持 | Codex 当前 hook 机制无 deny guardrail；`ldvh@personal` 的 `pre_tool_use` 未启用 |
| MCP 生命周期 Hook | ❌ 肯定不支持 | MCP 无 session lifecycle 语义 |
| Git commit-msg Gate | ✅ 已安装 | 已安装于 LDVH 工作树；实际阻断行为待测试 |
| 事实 Schema 机械校验 | ⚠️ 存在但非公开入口 | spark-0039 #1 未完成；当前 Gate 不校验事实对象内容 |
| 直写 `ldvh-base/` 防绕 | ⚠️ 无机械验证 | 未提交污染窗口只能压缩不能消除 |

---

## 7. 待执行步骤

1. **AI**：更新 `~/.claude/skills/ldvh/SKILL.md` 内容，移除 "Claude Code 无 SessionStart 插件" 表述，改为如实区分已验证/未验证/不支持。
2. **Human**：新建 cold start Codex/Cindy 会话，验证 `SessionStart` hook 是否真实触发（检查启动日志、hook 产物、回指记录）。
3. **Human/AI**：在 LDVH 工作树进行一次测试提交，验证 `commit-msg` Gate 对合规/不合规 message 的阻断行为。
4. **AI**：待 `spark-0039` #1 落地后（事实 Schema 校验进入 git Gate），更新 Skill 与报告中的验证结论。
5. **可选**：若目标环境明确为纯 Codex，尝试将 Skill 复制到 `~/.codex/skills/ldvh/SKILL.md` 并在新会话验证加载；当前不推荐迁移到 `.system/`。

---

## 8. 当前四层声明

| 声明 | 状态 |
|---|---|
| ⚪ 静态文件存在 | ✅ 已验证 |
| ⚪ CLI 直调可用 | ✅ 已验证（`ldvh capabilities` 可运行） |
| ⚪ 真实自动触发 | ❌ 未验证 |
| ⚪ Git Gate 阻断行为 | ❌ 未经验证（已安装，待实际提交测试） |
| ⚪ 接入整体声明 | ❌ 不成立——未通过 SessionStart 真实触发验证与 Git Gate 行为验证 |

---

*本报告依据 LDVH `specs/09-环境接入规范.md`、`specs/attachments/09.Att.01-环境接入面.md`、`ldvh-base/sparks/spark-0039.yaml` 及当前环境实际观察生成。*
