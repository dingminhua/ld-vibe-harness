# 10G 外部环境入口与 legacy Rules/Skill 审计记录

> 文件状态：temporary migration closure。本文记录 V3 对 tool hook、completion hook、Codex repo 指令、外部 runtime adapter 以及 legacy Rules/Skill 顶层机制的真实接入审计；它不安装新入口，不声明 manual entrypoints 已自动触发，也不恢复 `rules/` 或 `skills/` 顶层目录机制。正式规则仍以 `specs/` 正文为准。

## 1. 审计目标

10G 用于回答：当前仓库是否已经存在可复现证据，证明 V3 runtime 入口会被环境自动加载、触发、阻断或回滚；同时确认 V2 Rules / Skill 是否仍作为 V3 顶层机制存在。

判断标准：

| 条件 | 要求 |
|---|---|
| 触发事件 | 能说明何时自动调用，如 `git commit`、tool call 前、completion 前 |
| payload | 能提供稳定输入字段，如 target、operation、acknowledged paths、verification evidence |
| 失败处理 | 失败时能阻断、报告或清晰退出 |
| 安装状态 | 能由 Code 检查当前 repo 是否启用 |
| 回滚方式 | 能撤销或关闭，不破坏用户环境 |

缺少任一关键条件时，只能记录为 available、deferred 或 absent，不得声明 integrated。已经明确取消的 V2 顶层机制必须记录为 `removed_top_level`，不得写成待启用入口。

## 2. 新增入口

```bash
python3 code/environment_entry_audit.py --format text
python3 code/environment_entry_audit.py --format json
```

该入口会读取 10F 的环境状态，并额外审计：

| 候选 | 当前结论 | 理由 |
|---|---|---|
| `git.commit-msg` | integrated | 当前 worktree 已通过 `core.hooksPath=hooks` 启用 managed `hooks/commit-msg` |
| `codex.ldvh-plugin` | available / absent | Codex lifecycle Hook 是当前可审计样例；通用原则是所有支持 Hook 的环境都必须通过对应 LDVH plugin / extension 安装，旧插件或旧仓库路径不能证明 V3 接入 |
| `runtime.session_start.auto` | deferred | Codex 提供 SessionStart 生命周期 Hook 机制；V3 需按通用环境 Hook 口径通过对应 LDVH plugin / extension 安装并验证 |
| `runtime.pre_tool_use.auto` | deferred | Codex 提供 PreToolUse 生命周期 Hook 机制；V3 需按通用环境 Hook 口径通过对应 LDVH plugin / extension 安装并验证 |
| `runtime.completion_claim.auto` | deferred | Codex 提供 Stop 生命周期 Hook 可作为完成声明邻近候选；V3 尚未通过对应环境插件定义和验证 |
| `runtime.adapter.auto` | deferred | `code/runtime_adapter.py` 已存在，但没有 V3 环境插件 / 扩展包的真实触发、安装状态、失败处理和回滚证据 |
| `rules.top_level_mechanism` | removed_top_level | V3 已取消 Rules 资产体系和独立规则权威；无 Hook fallback 只能归为环境薄引用或 repo instruction，不恢复 `rules/` 目录机制 |
| `skills.top_level_mechanism` | removed_top_level | V3 已取消 Skill 顶层机制、Skill registry 和 Skill 执行闭环；可复用工作流能力只能进入行动模板、Action Guide 或外部包装候选 |
| `codex.repo-instructions` | absent | 未发现 `AGENTS.md`、`.codex` 或 repo-local Codex 配置入口 |

## 3. 当前状态

```yaml
integrated_entrypoints:
  - git.commit-msg
rules_entry_integrated: false
skill_entry_integrated: false
tool_hook_integrated: false
completion_hook_integrated: false
session_start_integrated: false
codex_plugin_entry_integrated: false
codex_environment_entry_integrated: false
removed_top_level_entrypoints:
  - rules.top_level_mechanism
  - skills.top_level_mechanism
authorization: none
```

10G 的结论已更新：所有支持 Hook 的协作环境都必须通过对应 LDVH plugin / extension / package 安装环境 Hook，而不是直接写入环境 Hook 系统文件；Codex lifecycle Hook 机制只是当前可审计样例。旧插件、旧仓库路径、直接写入的环境 Hook 文件或历史 trust 记录不能证明 V3 已接入。除 `git.commit-msg` 外，当前 repo 没有可复现证据证明 tool hook、completion hook 或 Codex 生命周期入口已按 V3 自动触发。Rules / Skill 顶层机制不是后置项，而是已取消机制；原初始骨架中的 `rules/.gitkeep` 与 `skills/.gitkeep` 已删除。

## 4. 交付物

| 文件 | 作用 |
|---|---|
| `code/environment_entry_audit.py` | 审计 LDVH 环境插件样例、Codex repo 指令、runtime auto hook、external adapter 候选和 legacy Rules/Skill 顶层机制 |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖非提交入口后置、Rules/Skill removed_top_level，以及 AGENTS.md 仅 available 不 integrated 的边界 |
| `README.md` | 增加审计命令和当前结论 |
| `_migration/v3-migration-execution-plan.md` | 记录 10G 完成状态 |
| `rules/.gitkeep`、`skills/.gitkeep` | 删除早期骨架占位，避免误解为待启用顶层机制 |

## 5. 后续

后续只有在出现真实可验证入口时才继续接入，例如：

1. 目标环境对应的 LDVH V3 plugin / extension / package 已构建、安装或升级；
2. 插件或扩展 Hook 指向 V3 runtime adapter，而不是 V2 路径或旧仓库；
3. session start、tool call 前或 completion-adjacent 触发点能传稳定 payload；
4. 失败处理和退出码可阻断或明确报告；
5. 安装状态、trust 状态和回滚方式可由 Code 检查；
6. 用户明确同意启用会改变真实工作流的入口。

在这些条件满足前，tool hook、completion hook、Codex repo 指令和外部 runtime adapter 都保持后置。Rules / Skill 顶层机制保持取消状态；若未来需要入口可见或外部包装，只能用环境薄引用、repo instruction、行动模板、Action Guide 或外部 adapter 的名义重新审计，不得恢复独立 Rules/Skill 权威。
