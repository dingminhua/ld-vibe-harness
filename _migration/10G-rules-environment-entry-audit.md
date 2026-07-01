# 10G Rules / 外部环境入口审计记录

> 文件状态：temporary migration closure。本文记录 V3 对 Rules、tool hook、completion hook、Codex repo 指令和外部 runtime adapter 的真实接入审计；它不安装新入口，不声明 manual entrypoints 已自动触发。正式规则仍以 `specs/` 正文为准。

## 1. 审计目标

10G 用于回答：当前仓库是否已经存在可复现证据，证明 V3 规则或 runtime 入口会被环境自动加载、触发、阻断或回滚。

判断标准：

| 条件 | 要求 |
|---|---|
| 触发事件 | 能说明何时自动调用，如 `git commit`、tool call 前、completion 前 |
| payload | 能提供稳定输入字段，如 target、operation、acknowledged paths、verification evidence |
| 失败处理 | 失败时能阻断、报告或清晰退出 |
| 安装状态 | 能由 Code 检查当前 repo 是否启用 |
| 回滚方式 | 能撤销或关闭，不破坏用户环境 |

缺少任一关键条件时，只能记录为 available、deferred 或 absent，不得声明 integrated。

## 2. 新增入口

```bash
python3 code/environment_entry_audit.py --format text
python3 code/environment_entry_audit.py --format json
```

该入口会读取 10F 的环境状态，并额外审计：

| 候选 | 当前结论 | 理由 |
|---|---|---|
| `git.commit-msg` | integrated | 当前 worktree 已通过 `core.hooksPath=hooks` 启用 managed `hooks/commit-msg` |
| `runtime.session_start.auto` | deferred | 未发现真实 session start 触发点；仅有 `code/session_start.py` 手动入口 |
| `runtime.pre_tool_use.auto` | deferred | 未发现工具调用前置 Hook 或可阻断 payload 通道；仅有 `code/pre_tool_use.py` 手动入口 |
| `runtime.completion_claim.auto` | deferred | 未发现完成声明前置 Hook；仅有 `code/completion_claim.py` 手动入口 |
| `runtime.adapter.auto` | deferred | `code/runtime_adapter.py` 已存在，但没有真实外部事件源、安装状态、失败处理和回滚证据 |
| `rules.thin-reference` | deferred | 当前 `rules/` 只有 `.gitkeep`，没有可加载规则文件或安装状态证据 |
| `skills.external-wrapper` | deferred | 当前 `skills/` 只有 `.gitkeep`，且 Skill 不作为 V3 顶层机制 |
| `codex.repo-instructions` | absent | 未发现 `AGENTS.md`、`.codex` 或 repo-local Codex 配置入口 |

## 3. 当前状态

```yaml
integrated_entrypoints:
  - git.commit-msg
rules_entry_integrated: false
tool_hook_integrated: false
completion_hook_integrated: false
session_start_integrated: false
codex_environment_entry_integrated: false
authorization: none
```

10G 的结论是：除 `git.commit-msg` 外，当前 repo 没有可复现证据证明 Rules、tool hook、completion hook 或 Codex 生命周期入口已自动触发。因此这些能力正式后置，不再按已接入处理。

## 4. 交付物

| 文件 | 作用 |
|---|---|
| `code/environment_entry_audit.py` | 审计 Rules、Skill、Codex repo 指令、runtime auto hook 和 external adapter 候选 |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖非提交入口后置，以及 AGENTS.md 仅 available 不 integrated 的边界 |
| `README.md` | 增加审计命令和当前结论 |
| `_migration/v3-migration-execution-plan.md` | 记录 10G 完成状态 |

## 5. 后续

后续只有在出现真实可验证入口时才继续接入，例如：

1. 环境提供 session start、tool call 前或 completion 前触发点；
2. 触发点能传稳定 payload；
3. 失败处理和退出码可阻断或明确报告；
4. 安装状态和回滚方式可由 Code 检查；
5. 用户明确同意启用会改变真实工作流的入口。

在这些条件满足前，Rules、tool hook、completion hook、Codex repo 指令和外部 runtime adapter 都保持后置。
