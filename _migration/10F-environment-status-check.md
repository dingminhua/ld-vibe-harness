# 10F 环境接入状态检查记录

> 文件状态：temporary migration closure。本文记录 V3 当前环境接入状态检查入口；它不安装新的 Hook，不声明 session start、pre tool use、completion claim 或 runtime adapter 已自动触发。正式规则仍以 `specs/` 正文为准。

## 1. 目标

10A-10E 后，V3 已同时存在两类接入：

1. 真实自动入口：当前 worktree 的 `git.commit-msg` Hook；
2. manual / external adapter-ready 入口：`runtime_adapter.py`、`session_start.py`、`pre_tool_use.py`、`completion_claim.py`。

10F 的目标不是扩大接入范围，而是提供一个只读检查入口，让 AI、测试和 Human 能用同一个命令确认当前哪些入口真正自动接管、哪些只是可手动调用。

## 2. 新增入口

```bash
python3 code/environment_status.py --format text
python3 code/environment_status.py --format json
```

该入口读取：

| 项 | 来源 | 预期 |
|---|---|---|
| `git.commit-msg` | `core.hooksPath=hooks` 与 `hooks/commit-msg` managed marker | `integrated=true` |
| `manual.runtime_adapter` | `code/runtime_adapter.py` | `available=true`、`integrated=false` |
| `manual.session_start` | `code/session_start.py` | `available=true`、`integrated=false` |
| `manual.pre_tool_use` | `code/pre_tool_use.py` | `available=true`、`integrated=false` |
| `manual.completion_claim` | `code/completion_claim.py` | `available=true`、`integrated=false` |

若目标 repo 未安装 V3 managed `commit-msg` Hook，状态检查返回 blocking diagnostic：`ENV_COMMIT_MSG_HOOK_NOT_INSTALLED`。

## 3. 当前状态

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

`environment_status.py` 的输出是只读诊断，不授权写入、不替代 Human Gate，也不把 manual entrypoints 升级为自动入口。

## 4. 交付物

| 文件 | 作用 |
|---|---|
| `code/environment_status.py` | 统一环境接入状态检查 CLI |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖已安装 Hook 的 partial 状态和缺 Hook 阻断 |
| `README.md` | 增加统一状态检查命令 |
| `_migration/v3-migration-execution-plan.md` | 记录 10F 完成状态 |

## 5. 后续

若后续环境提供真实 session/tool/completion 触发点，应先让 `environment_status.py` 能识别其安装状态、payload 来源、失败处理和回滚方式，再更新 `*_integrated=true`。在此之前，当前唯一自动入口仍是 `git.commit-msg`。
