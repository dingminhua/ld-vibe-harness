# 10E runtime adapter 可行性与统一入口记录

> 文件状态：temporary migration closure。本文记录 V3 runtime adapter 的当前可行性、统一 payload 契约和未自动接管边界；不声明 session start、pre tool use 或 completion claim 已被真实环境自动触发。正式规则仍以 `specs/` 正文为准。

## 1. 可行性结论

当前仓库支持两类接入：

1. 真实 Hook 接入：仅 `git.commit-msg` 已通过当前 worktree 的 `core.hooksPath=hooks` 接管；
2. manual / external adapter-ready 接入：`session_start`、`pre_tool_use`、`completion_claim` 已有手动 CLI 和统一 runtime adapter payload 入口。

当前没有发现可安装的真实 session start hook、工具调用前置 hook 或 completion hook。因此 10E 不启用新的自动拦截，只新增统一 adapter 调用面：

```bash
python3 code/runtime_adapter.py session-start --task "<当前任务>" --target-path "<目标路径>"
python3 code/runtime_adapter.py pre-tool-use --target-path "<目标路径>" --acknowledged-path specs/00-理念与构成.md --acknowledged-path specs/01-保障与衔接.md --acknowledged-path specs/02-AI行为规范.md
python3 code/runtime_adapter.py completion-claim --target-path "<目标路径>" --verification-evidence "<验证证据>"
```

也可以用 JSON payload：

```bash
python3 code/runtime_adapter.py --payload-file runtime-payload.json --format json
```

## 2. Payload 契约

统一 adapter payload 至少包含：

| 字段 | 要求 |
|---|---|
| `event` | 必填；支持 `session_start` / `session-start`、`pre_tool_use` / `pre-tool-use`、`completion_claim` / `completion-claim` |
| `session_id` | 必填，可为空字符串 |
| `target_path` | 必填，可为空字符串；`pre_tool_use` 缺 target 会由 preflight 阻断 |
| `operation` | 必填，可为空字符串；adapter 会按事件传递给 runtime |
| `task` | 必填，可为空字符串 |
| `acknowledged_paths` | 必填 list；`pre_tool_use` 缺 00/01/02 会阻断 |
| `verification_evidence` | 必填 list；`completion_claim` 缺 evidence 会阻断 |

`trigger_source` 可选；未提供时默认为 `manual.runtime_adapter`。

## 3. 交付物

| 文件 | 作用 |
|---|---|
| `code/runtime_adapter.py` | 统一 payload/CLI adapter，转发到 manual 三件套 |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖三类事件转发、unknown event、缺 payload 字段和无授权语义 |
| `README.md` | 说明两类接入方式、统一 adapter 入口和当前边界 |
| `_migration/v3-migration-execution-plan.md` | 记录 10E 完成状态 |

## 4. 当前状态

```yaml
switch_mode: commit_msg_hard_switch_minimal
environment_integrated: partial
hook_integrated: git.commit-msg
runtime_adapter_entry: manual.runtime_adapter
runtime_adapter_integrated: false
session_start_entry: manual.session_start
session_start_integrated: false
pre_tool_use_entry: manual.pre_tool_use
pre_tool_use_integrated: false
completion_claim_entry: manual.completion_claim
completion_claim_integrated: false
authorization: none
```

`runtime_adapter.py` 是统一调用面，不是环境自动触发证明。它返回 `adapter_integrated=false`、`environment_integrated=false` 和 `authorization=none`。

## 5. 后续

10F 已先补环境状态检查入口，用于统一确认哪些入口真实接入、哪些仍是 manual-ready。若后续环境提供真实 session/tool/completion 触发点，应另起接入审计，对真实 adapter 安装、payload 来源、失败处理、回滚方式和 Human Gate 进行审计后再接入。没有真实触发能力时，不得声明自动接管。
