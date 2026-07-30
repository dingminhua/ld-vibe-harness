# Codex Desktop 环境 接入LDVH

> 调查时间：2026-07-30  
> 执行环境与目标环境：同一台 macOS 本地 Codex Desktop；本机 `codex-cli 0.146.0-alpha.3.1`。

## 结论

LDVH 在 Codex Desktop 中应采用三层组合：**薄 Skill 作为默认信息层、Codex 插件 Hook 负责已证据支持的自动触发、原生 Git `commit-msg` Hook 负责机械 Gate**。三者不互斥；Skill 不能替代自动触发或 Git Gate。

当前环境已存在并启用 LDVH 个人插件，当前会话也取得了 `SessionStart` / `startup` 的工作上下文交付。仍应补建 Codex 官方位置的薄 Skill；Git Gate 保留，但不得称其为事实对象完整性终闸。

## 能力与当前证据

| 机制 | Codex / Git 能力 | 当前观察 | 状态与边界 |
| --- | --- | --- | --- |
| Skill | Codex 支持独立 `SKILL.md`，按名称与 description 渐进式加载 | 本会话读取过 LDVH Skill；文件位于 `~/.claude/skills/ldvh/SKILL.md` | **已验证可用**；该路径不是 Codex 官方稳定发现位置，应迁移 |
| 生命周期 Hook | 支持 `SessionStart`、`SubagentStart`、`PreToolUse` 等 | `ldvh@personal` 启用，`SessionStart`、`SubagentStart` 已信任；本会话收到 `SessionStart` / `source=startup` / `outcome=ok` | **本会话 SessionStart 实际触发已验证**；SubagentStart 未实测 |
| PreToolUse guardrail | 可观察本地工具，且可阻断或改写调用 | 当前插件实际 hooks 文件未注册 PreToolUse | 环境能力**已验证支持**；当前 LDVH 部署**未接入**，不应称作 guardrail |
| Git `commit-msg` | Git 原生支持非零退出中止提交 | `core.hooksPath=.githooks-v4`；`ldvh-git-hook status` 确认当前 Hook 由 LDVH 管理 | **静态安装已验证**；真实提交事件未实测 |
| 事实写入完整性终闸 | Git 可承载机械检查 | 当前 `ldvh-git-commit-msg` 只检查提交契约 | 对事实 schema 的 Git 终闸为**当前未交付 / 不支持** |

`ldvh capabilities` 已返回 15 个公开 Helper 操作。`ldvh-doctor` 在仓库根运行时为 `attention`（缺少治理配置）；以父级工作区运行时为 `unavailable`（Helper capabilities 为 `partial`）。两者都不能证明目标环境已集成或通过真实验证。

## 三层接入方案

### 1. 信息层：薄 Skill（默认）

推荐将 Skill 放置在下列位置之一：

- 仓库范围：`<REPO_ROOT>/.agents/skills/ldvh/SKILL.md`；本仓库为 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.agents/skills/ldvh/SKILL.md`。
- 用户范围：`$HOME/.agents/skills/ldvh/SKILL.md`，适用于本机所有项目。

优先仓库范围；若 LDVH 要服务多个受管项目，再使用用户范围。不要把 `~/.claude/skills` 当作 Codex 的稳定发布位置。

Skill 只承担路由和边界说明，最小骨架如下：

```md
---
name: ldvh
description: 在需要读取、操作或验证 LDVH 项目规则、事实对象或 Git Gate 时使用。
---

1. 先运行 `ldvh capabilities` 确认可用入口。
2. 新工作上下文若尚未收到 Hook 规则引导，调用 `ldvh-work-context`；已收到时不重复注入。
3. 只有 Human 目标明确需要项目事实时，才按来源调用 `ldvh call ...`
   或 `ldvh-context-recovery`。
4. 写事实、Git 提交、安装或启用环境对象前，定位对应行动模板和 Human Gate。

边界：不复制 Specs、事实 Schema 或 Helper 字段；不因启动、cwd 或任务文字读取事实；
不把 CLI 可调用或文件存在写成自动触发已验证；不绕过既有 CLI 入口直写 `ldvh-base/`。
```

Codex 先加载 Skill 元数据，只有选中后才读取完整说明，故这种薄 Skill 与 LDVH 的渐进式披露一致。[Codex Build skills](https://learn.chatgpt.com/docs/build-skills)

### 2. 自动触发层：保留现有 Codex 插件 Hook

当前安装缓存：

`/Users/dmh2002/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260722092023`

插件配置数据：

`/Users/dmh2002/.codex/plugins/data/ldvh-personal/ldvh.json`

其中以绝对路径指定既有 `ldvh` 与 `ldvh-work-context` 入口。当前 `hooks/hooks.json` 注册：

| 事件 | matcher | 调用 | 当前结果 |
| --- | --- | --- | --- |
| `SessionStart` | `startup|resume|clear|compact` | `scripts/codex_context.py` | 已在本会话验证 `startup` |
| `SubagentStart` | 全部 | 同一脚本 | 静态启用，真实触发未验证 |

适配器只把 Codex 实际 stdin JSON 传给 `ldvh-work-context`，不构造事实请求。其核心使用 `hook_event_name`，并透传 `source` 与 `cwd`；输出映射为 `hookSpecificOutput.hookEventName` 与 `hookSpecificOutput.additionalContext`。失败时仍以 `continue: true` 加 `systemMessage` 如实交还，因此 SessionStart 不承担阻断职责。

Codex Hook 的共享输入包括 `session_id`、`transcript_path`、`cwd`、`hook_event_name`、`model`；相关事件还包含 `permission_mode`。`SessionStart` matcher 的启动来源可区分 `startup`、`resume`、`clear`、`compact`。插件 Hook 需单独审查并信任当前 hash。[Codex Hooks](https://learn.chatgpt.com/docs/hooks)

**PreToolUse 不应默认接入。** 只有出现以下证据之一才建立独立的 adapter Code 计划：再次发生直写 `ldvh-base/` 且跨会话消费、无人值守/多 Agent 链路开始写事实，或 Human 明确决定交付 guardrail。即使接入，PreToolUse 也只是覆盖不完整的 guardrail，不能替代 Git Gate。

### 3. 阻断层：每个 worktree 的 Git `commit-msg` Gate

当前 worktree 的有效 Hook 为：

`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.githooks-v4/commit-msg`

它调用既有 `ldvh-git-commit-msg`。`ldvh-git-hook status --worktree /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4` 已返回“LDVH owns the current Git commit-msg Hook”。

此 Gate 的真实覆盖范围仅为提交契约：提交消息、候选路径、管辖绑定与快照身份。根据 `spark-0039`，它**不**检查事实对象 schema，因此 schema-invalid 的直接写入在消息合规时仍可能通过。`--no-verify`、未安装的 clone/worktree 和 Git 之外的写入也是残留边界。

Git 的 `commit-msg` Hook 接收提交消息文件；非零退出会中止提交，但 Git 明确允许 `--no-verify` 绕过。[Git githooks](https://git-scm.com/docs/githooks)

## 安装、部署、接入、验证

| 层次 | 技术动作 | 必须由 Human 完成的事项 |
| --- | --- | --- |
| 安装 | 固定 LDVH pip 版本；运行 `ldvh capabilities` | 批准安装的版本与范围 |
| 部署 | 放入 `.agents/skills/ldvh/SKILL.md`；通过 marketplace 安装插件；配置 `PLUGIN_DATA/ldvh.json` 的绝对 CLI 路径 | 批准用户目录、插件或配置写入 |
| 接入 | 启用 `ldvh@personal`；信任当前 Hook hash；确认项目受信任；按 worktree 管理 Git Hook | 接受插件/Hook 信任；确认 Git Hook 安装与覆盖范围 |
| 验证 | 进行静态检查、CLI 直调、真实事件和回滚/缺口检查 | 新开 cold-start 任务；需要时重启应用；返回只有 UI 可见的原始结果 |

## Cold start 与 hydrate 的区分和验收

1. 先记录插件版本、Hook hash、`ldvh.json` 内容、时间与目标 worktree。
2. 关闭当前任务；新建指向同一 worktree 的本地 Codex 任务，不使用“继续/恢复”。
3. 验收首个环境事件为 `SessionStart` 且 `source=startup`，并包含本次 `ldvh-work-context/1` 规则交付及 `facts=not_requested`。
4. 创建一个子代理，验收 `SubagentStart` 也得到同类规则引导。
5. 记录一个故意缺少输入或核心不可用的路径，确认其 `unavailable`/缺口未被吞成成功。
6. 单独进行一次受控 Git 提交，验证真实 `commit-msg` allow/block；`ldvh-git-hook status` 或 CLI 直调不能替代该证据。

本会话的 `source=startup` 是正向实时触发证据，但尚未进行独立控制的重启/升级后复测；因此“本会话启动触发”可称已验证，“跨重启持续有效”仍应标为未验证。

## 依据与未交付范围

- LDVH 核心接入面与入口选择：[环境接入面](../specs/attachments/09.Att.01-环境接入面.md)。
- 安装、部署、接入、验证不可互相替代：[环境接入规范 §6](../specs/09-环境接入规范.md)。
- 既定形态、事实完整性 Gate 缺口和插件升级条件：[spark-0039](../ldvh-base/sparks/spark-0039.yaml)。
- Codex 插件的目录、生命周期 Hook、缓存、信任与安装机制：[Build plugins](https://developers.openai.com/plugins/build/plugins)。

本报告不改写任何 LDVH 核心入口契约；所有建议调用均经现有的六个 console entry point。
