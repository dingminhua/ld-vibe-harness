# 10B session_start 手动入口记录

> 文件状态：temporary migration closure。本文记录 V3 `session_start` 的最小可用入口：提供手动/外部 adapter 可调用的 read_plan CLI，不声明真实会话启动 Hook 已自动接管。正式规则仍以 `specs/` 正文为准。

## 1. 接入结论

10B 审计后确认：当前仓库已具备 `build_runtime_event(event="session_start")` 和 Action Guide read_plan 生成能力，但当前协作环境没有类似 Git `commit-msg` 的可安装真实 session start hook。

因此 10B 不做自动拦截声明，只提供明确入口：

```bash
python3 code/session_start.py --task "<当前任务>" --target-path "<目标路径>"
```

该入口输出：

1. `session_start` runtime receipt；
2. P0/P1 `task_read_plan`；
3. stop conditions；
4. source refs 和 diagnostics；
5. `authorization=none`；
6. `environment_integrated=false`；
7. `integration_scope=manual.session_start`。

## 2. 交付物

| 文件 | 作用 |
|---|---|
| `code/session_start.py` | 专用 `session_start` CLI，输出 text/json read_plan 和 stdout-only receipt |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖 CLI JSON 输出、manual integration scope、receipt 边界和 00/01/02 read_plan |
| `README.md` | 增加手动 session_start 入口和当前环境边界 |
| `_migration/v3-migration-execution-plan.md` | 记录 10B 完成状态 |

## 3. 当前状态

```yaml
switch_mode: commit_msg_hard_switch_minimal
environment_integrated: partial
hook_integrated: git.commit-msg
session_start_entry: manual.session_start
session_start_integrated: false
authorization: none
```

10B 没有改变 10A 的真实 Hook 范围：当前唯一自动拦截入口仍是 Git `commit-msg`。`session_start.py` 是手动入口或未来外部 adapter 的稳定调用面，不是环境自动触发证明。

## 4. 使用边界

`session_start.py` 的 receipt 是 stdout-only 过程输出，不写回事实源，不作为 Human Gate、授权、完成证明或持久 session 状态。

AI 或外部 wrapper 可以读取该输出并据此消费 00/01/02，但如果外部环境没有把该 CLI 接到真实会话启动事件，就不得写成 `session_start` 已自动接管。

## 5. 后续

后续若要继续推进，应进入 10C `pre_tool_use`。该阶段风险更高，因为它需要真实写入/工具调用前置拦截；若环境没有可接入 hook，应只实现 adapter/facade 和测试，不声明自动阻断。
