# LDVH 接入 Claude Code 环境分析报告

> 报告生成时间：2026-07-30
> 执行环境：Claude Code（Anthropic 官方 CLI）
> 目标环境：当前 Claude Code 会话
> 验证范围：以 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4` 为当前 LDVH 发行物与工作对象

**重要区分**：本报告从 **Claude Code** 视角评估。同一机器上虽存在 `~/.codex` 目录与 `ldvh@personal` Codex 插件配置，但该插件属于 Codex 桌面应用生态，对当前 Claude Code 会话**不生效**。Claude Code 的接入单元是 `~/.claude/skills/` 下的 Skill 与 `settings.json` 中配置的 hook，而非 Codex 的 `hooks.json` / `config.toml` 插件体系。

---

## 1. 环境机制调查

### 1.1 技能 / 指令文件（Skill）

| 项目 | 状态 | 依据 |
|---|---|---|
| 支持定义 | ✅ 已验证 | Claude Code 支持通过 YAML frontmatter + Markdown body 的 `SKILL.md` 文件向模型注入技能指令 |
| 当前位置 | ✅ 已验证 | `~/.claude/skills/ldvh/SKILL.md` |
| 触发方式 | ✅ 已验证 | 通过 YAML `name` / `description` 语义匹配；当前会话可用技能列表中已出现 `ldvh` |
| 加载范围 | ✅ 已验证 | `~/.claude/skills/<name>/SKILL.md` 自动进入 `<skills_instructions>`；项目级 `.claude/skills/` 同样有效 |

**实测对象：**

```bash
# 技能文件存在且已加载
~/.claude/skills/ldvh/SKILL.md
```

**结论：** Skill 机制已就绪，是当前 Claude Code 环境下唯一已部署的 LDVH 信息层。但 Skill 内容需更新：它声称 "Claude Code 没有 SessionStart 自动注入插件"，实际上 Claude Code 支持 `settings.json` 的 `SessionStart` hook，只是当前**未配置** LDVH 的 SessionStart hook。

### 1.2 Claude Code 生命周期 Hook（settings.json）

| 项目 | 状态 | 依据 |
|---|---|---|
| 事件支持 | ✅ 已验证 | `settings.json` 支持 `SessionStart`、`SubagentStart`、`PreToolUse`、`PostToolUse`、`Stop`、`PreCompact`、`PostCompact`、`UserPromptSubmit` 等事件（详见 update-config skill 提供的 schema） |
| Hook 类型 | ✅ 已验证 | `command`（shell 命令）、`prompt`（LLM 评估）、`agent`（agent 验证）、`http`、`mcp_tool` |
| 输入承载 | ✅ 已验证 | command hook 从 stdin 接收 JSON，例如 `SessionStart` 可接收 `{ "session_id": "..." }`；具体字段以官方 schema 为准 |
| 输出承载 | ✅ 已验证 | 可返回 `systemMessage`、`hookSpecificOutput`（含 `additionalContext`）等 |
| 能否阻断工具调用 | ✅ 理论上支持 | `PreToolUse` hook 可返回 `permissionDecision: allow/deny/ask`；但当前**未配置**任何 LDVH `PreToolUse` guardrail |
| 当前 LDVH Hook 配置 | ❌ 未配置 | `~/.claude/settings.json` 不存在；LDVH 项目根目录无 `.claude/settings.json` 或 `.claude/settings.local.json` |
| 真实自动触发 | ❌ 未验证 | 当前无 LDVH SessionStart hook 配置，因此不存在可验证的自动触发 |

**实测对象：**

```bash
# 全局 settings.json 不存在
~/.claude/settings.json        -> 不存在
~/.claude/settings.local.json  -> 不存在

# 项目级 settings 不存在
/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.claude/  -> 不存在
```

**与 Codex 的差异：**

| 维度 | Claude Code | Codex（同一机器上并存） |
|---|---|---|
| 配置文件 | `~/.claude/settings.json`、`.claude/settings.json`、`.claude/settings.local.json` | `~/.codex/config.toml`、`~/.codex/hooks.json` |
| 插件形态 | Skill + settings.json hook + 官方 marketplace plugin | `.codex-plugin` 插件包 |
| PreToolUse 阻断 | ✅ `permissionDecision` 可 deny/ask | ❌ 当前无 deny guardrail |
| 当前 LDVH 配置 | 仅有 Skill | `ldvh@personal` 插件已启用（但对 Claude Code 无效） |

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
- Claude Code 原生支持 Skill；`ldvh` 技能已在 `~/.claude/skills/ldvh/SKILL.md` 就位并加载。
- Skill 是零副作用、无需重启即可生效的信息层。
- 默认形态下，Skill 应承担"按需调用 + 自检"职责，不替代 git Gate。

**应做：**
1. 更新 `~/.claude/skills/ldvh/SKILL.md`：
   - 修正 "Claude Code 没有 SessionStart 自动注入插件" 的表述；
   - 改为 "Claude Code 支持 `settings.json` 的 `SessionStart` hook，但当前**未配置** LDVH 自动注入"。
2. 保持 Skill "只指路、不抄规则" 的边界。

### Layer 2 — 自动触发层：会话启动注入规则引导

**推荐：** 当前**不配置** `settings.json` 的 `SessionStart` hook；以 Skill 为默认信息层。

**理由：**
- spark-0039 的接入形态结论为：默认单一薄 Skill，环境 Hook 作为"证据触发的可选加固"。
- 升级到自动注入的证据触发条件（spark-0039）：
  1. 再次发生直写 `ldvh-base/` 绕过且跨会话消费后才被发现；
  2. 无人值守/多 Agent 链路开始写事实对象；
  3. 目标环境无技能机制但有生命周期 Hook；
  4. 或决定交付 PreToolUse guardrail。
- 当前为 Claude Code 环境，条件 3 不适用（Skill 机制存在）；其余条件未在本会话观察到。

**应做：**
- 维持现状：不新增 `settings.json` hook。
- 若未来触发上述条件，可在 `~/.claude/settings.json` 或项目 `.claude/settings.json` 中增加 `SessionStart` command hook，调用 `ldvh-work-context`。

### Layer 3 — 阻断层：事实写入的机械校验

**推荐：** 原生 Git `commit-msg` Gate

**理由：**
- 唯一真实阻断机制；已安装于 LDVH 工作树。
- 跨所有 AI 环境生效，不依赖 Claude Code。
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

项目级位置（若希望随仓库共享给团队）：

```
/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.claude/skills/ldvh/SKILL.md
```

### 3.2 加载机制

- Claude Code 启动时会扫描 `~/.claude/skills/` 与当前项目 `.claude/skills/` 下的 `SKILL.md`。
- 文件存在即自动进入 `<skills_instructions>`，无需 `enabled = true` 或额外注册。
- 加载顺序：用户级 → 项目级；后加载的同名 skill 可覆盖前者。

### 3.3 最小内容骨架（更新版）

```yaml
---
name: ldvh
description: 在当前 Claude Code 会话中使用与自检 LDVH（LD Vibe Harness）。当用户要求“跑/检查/验证 LDVH”“接入自检”“交付 LDVH 工作上下文”“ldvh-doctor”，或询问 LDVH 在本环境是否生效、想用 LDVH 的规范/事实对象/Helper 能力时使用。提供核心直调、工作上下文交付与只读诊断的标准命令，并要求如实区分已验证/未验证/不支持。
---

# LDVH 技能（Claude Code 原生接入）

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

## 关于 Claude Code 自动注入的说明

Claude Code 支持通过 `settings.json` 配置 `SessionStart` 等生命周期 hook，但当前**未配置** LDVH 的自动注入。因此：

- 本技能负责"按需调用 + 自检"。
- "会话启动即注入规则引导"目前不成立，除非 Human 显式在 `settings.json` 中添加 LDVH `SessionStart` hook 并经 cold start 验证。

## 如实报告要求

- **已验证** — 本次实际跑通并有输出的（核心直调、work-context 交付、git hook 安装）。
- **未验证** — 需要 cold-start 新会话或真实事件才能证明的（如 settings.json SessionStart hook 触发、git Gate 阻断行为）。
- **不支持** — 环境缺少对应能力（Claude Code 当前无默认 PreToolUse guardrail，但机制上支持配置）。

不要把"命令存在""文件存在"或"本技能被调用"写成"hook 已实时生效"。
```

---

## 4. settings.json Hook 相关（Claude Code 原生机制）

### 4.1 事件清单

Claude Code `settings.json` 中与 LDVH 接入最相关的事件：

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "printf '{\"hook_event_name\":\"SessionStart\",\"source\":\"startup\",\"cwd\":\"'\"$(pwd)\"'\"}' | /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh-work-context --helper-executable /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh",
        "timeout": 60,
        "statusMessage": "Loading LDVH rule context"
      }]
    }],
    "SubagentStart": [{
      "hooks": [{
        "type": "command",
        "command": "printf '{\"hook_event_name\":\"SubagentStart\",\"cwd\":\"'\"$(pwd)\"'\"}' | /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh-work-context --helper-executable /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh",
        "timeout": 60,
        "statusMessage": "Loading LDVH rule context"
      }]
    }]
  }
}
```

**注意：** 上述配置仅为示例，当前**未部署**。实际部署前需经 Human Gate 确认，并按 `ldvh-work-context` 的真实输入契约调整 `cwd`、source 等字段。

### 4.2 安装位置

| 文件 | 作用域 | 是否提交到 git | 适用场景 |
|---|---|---|---|
| `~/.claude/settings.json` | 用户全局 | 否 | 个人所有项目生效 |
| `.claude/settings.json` | 项目级 | 是 | 团队共享 |
| `.claude/settings.local.json` | 项目级本地覆盖 | 否（应加入 .gitignore） | 个人本地覆盖 |

推荐：若决定启用自动注入，优先写入项目级 `.claude/settings.json`，使接入随仓库共享；个人覆盖用 `.claude/settings.local.json`。

### 4.3 信任 / 启用步骤

Claude Code 的 `settings.json` hook 不需要像 Codex 插件那样在 UI 中"启用"，但属于用户配置变更，需经 Human Gate：

1. Human 决定启用 `SessionStart` 自动注入。
2. AI 读取目标 `settings.json`，合并新增 hook，保留已有设置。
3. 使用 `jq` 验证 JSON 语法与 hook 路径。
4. 使用 pipe-test 验证 command 可正常执行。
5. Human 执行 cold start 新会话，验证 hook 真实触发。

### 4.4 Cold start 验证方法

区分真实触发与 hydrate：

1. 关闭当前所有 Claude Code 会话。
2. 启动全新 Claude Code 会话，cwd 为 LDVH 管辖项目。
3. 观察启动时 spinner/日志中是否出现 `Loading LDVH rule context` 或 hook 执行痕迹。
4. 检查会话中是否出现来自 LDVH 的 `additionalContext`。
5. 若出现上下文但无 hook 执行痕迹，则可能来自 hydrate，不能确认真实触发。

---

## 5. 安装 → 部署 → 接入 → 验证四层

### 第一层：安装（获取核心）

| 步骤 | 执行者 | 当前状态 |
|---|---|---|
| pip 安装 LDVH 包 | 命令行 | ✅ 已完成（`.venv` 存在） |
| 验证 6 个 CLI 入口可用 | AI / 命令行 | ✅ `ldvh capabilities` 返回 `ldvh-helper-cli/2` |
| 安装后执行 `ldvh capabilities` | AI | ✅ 已跑通 |

### 第二层：部署（放置既有单元）

| 步骤 | 执行者 | 当前状态 |
|---|---|---|
| 创建/更新 Skill 文件 | AI | ⚠️ 文件存在但内容需更新（修正 Claude Code 无 SessionStart 的表述） |
| 检查 settings.json hook 配置 | AI | ✅ 确认不存在；当前无配置 |
| Git hook 安装 | Human Gate / AI 观察 | ✅ 已安装；`ldvh-git-hook status` 确认 LDVH 拥有 commit-msg hook |

### 第三层：接入（连接原生事件）

| 步骤 | 执行者 | 当前状态 |
|---|---|---|
| Skill → AI 知道 LDVH 存在与用法 | 自动（Skill 在 skills 目录即加载） | ✅ 当前会话已加载 |
| settings.json SessionStart → 自动注入 | 环境 + Human Gate | ❌ 未配置；因此无自动触发 |
| Git Hook → commit-msg Gate 阻断 | 原生 git | ✅ 已安装，待实际提交测试 |

### 第四层：验证（逐事件证明）

| 验证项 | 方法 | 当前状态 |
|---|---|---|
| 静态存在 — Skill/Hook 文件在预期位置 | `ls` / `cat` | ✅ 已验证 |
| CLI 直调可用 — 手动调用 CLI 可得预期输出 | `ldvh-work-context` 传 stdin | ✅ 已验证（`ldvh capabilities` 可运行） |
| 真实自动触发 — 新会话启动时 hook 自动运行 | Cold start + 日志检查 | ❌ 不适用 — 当前无 SessionStart hook 配置 |
| Git Gate 生效 — 不合规 commit 被阻断 | 实际测试 | ❌ 待实际提交测试 |

---

## 6. 能力缺口清单

| 能力 | 状态 | 说明 |
|---|---|---|
| Skill 信息投递 | ✅ 已验证支持 | `ldvh` 技能已加载；内容需小幅更新 |
| settings.json SessionStart 自动注入 | ❌ 未配置 | Claude Code 机制支持，但当前未启用 |
| settings.json SubagentStart 自动注入 | ❌ 未配置 | 同 SessionStart |
| PreToolUse guardrail | ⚠️ 机制支持但未实现 | Claude Code 的 `PreToolUse` 可返回 `permissionDecision: deny/ask`；当前无 LDVH guardrail |
| MCP 生命周期 Hook | ❌ 肯定不支持 | MCP 无 session lifecycle 语义 |
| Git commit-msg Gate | ✅ 已安装 | 已安装于 LDVH 工作树；实际阻断行为待测试 |
| 事实 Schema 机械校验 | ⚠️ 存在但非公开入口 | spark-0039 #1 未完成；当前 Gate 不校验事实对象内容 |
| 直写 `ldvh-base/` 防绕 | ⚠️ 无机械验证 | 未提交污染窗口只能压缩不能消除 |

---

## 7. 待执行步骤

1. **AI**：更新 `~/.claude/skills/ldvh/SKILL.md` 内容，修正 "Claude Code 没有 SessionStart 自动注入插件" 的表述，改为如实说明 Claude Code 支持 `settings.json` hook 但当前未配置 LDVH 自动注入。
2. **Human 决策**：是否要在 `.claude/settings.json`（项目级）中启用 LDVH `SessionStart` hook。
   - 默认推荐：**不启用**，保持 Skill 为默认信息层，符合 spark-0039 形态结论。
   - 若触发 spark-0039 升级条件（直写污染跨会话消费、多 Agent 写事实、决定上 guardrail），再启用。
3. **Human/AI**：在 LDVH 工作树进行一次测试提交，验证 `commit-msg` Gate 对合规/不合规 message 的阻断行为。
4. **AI**：待 `spark-0039` #1 落地后（事实 Schema 校验进入 git Gate），更新 Skill 与报告中的验证结论。

---

## 8. 当前四层声明

| 声明 | 状态 |
|---|---|
| ⚪ 静态文件存在 | ✅ 已验证 |
| ⚪ CLI 直调可用 | ✅ 已验证 |
| ⚪ 真实自动触发 | ❌ 不成立 — 当前无 SessionStart hook 配置 |
| ⚪ Git Gate 阻断行为 | ❌ 未经验证（已安装，待实际提交测试） |
| ⚪ 接入整体声明 | ❌ 不成立 — 未通过 SessionStart 真实触发验证与 Git Gate 行为验证 |

---

## 附录：与 Codex 插件的区分说明

同一机器上 `~/.codex/plugins/ldvh@personal` 已启用并对 Codex 桌面应用有效，但：

- Claude Code 不读取 `~/.codex/config.toml` 或 `~/.codex/hooks.json`。
- Codex 插件的 `ldvh@personal` hook 状态不能倒推 Claude Code 的接入状态。
- 若用户同时使用 Codex 桌面应用与 Claude Code CLI，两者需分别验证。

*本报告依据 LDVH `specs/09-环境接入规范.md`、`specs/attachments/09.Att.01-环境接入面.md`、`ldvh-base/sparks/spark-0039.yaml` 及 Claude Code 官方 settings.json schema（经 update-config skill）生成。*
