# 10C pre_tool_use 手动入口记录

> 文件状态：temporary migration closure。本文记录 V3 `pre_tool_use` 的最小可用入口：提供手动/外部 adapter 可调用的写入前检查 CLI，不声明真实工具调用前置 Hook 已自动接管。正式规则仍以 `specs/` 正文为准。

## 1. 接入结论

10C 审计后确认：V3 已具备 `build_runtime_event(event="pre_tool_use")` 和 `build_preflight`，可以检查 read_plan 消费证据、target 归口、Human Gate 风险和诊断边界。但当前协作环境没有已暴露的真实工具调用前置 hook，不能自动拦截 `apply_patch`、Edit、Write 或 shell 写入。

因此 10C 不做自动阻断声明，只提供明确入口：

```bash
python3 code/pre_tool_use.py \
  --target-path "<目标路径>" \
  --operation write \
  --acknowledged-path specs/00-理念与构成.md \
  --acknowledged-path specs/01-保障与衔接.md \
  --acknowledged-path specs/02-AI行为规范.md
```

该入口输出：

1. `pre_tool_use` runtime receipt；
2. read_plan 消费证据检查；
3. target preflight 诊断；
4. required read plan；
5. Human Gate risks；
6. `authorization=none`；
7. `environment_integrated=false`；
8. `integration_scope=manual.pre_tool_use`。

## 2. 交付物

| 文件 | 作用 |
|---|---|
| `code/pre_tool_use.py` | 专用 `pre_tool_use` CLI，输出 text/json 写入前检查、preflight 和 stdout-only receipt |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖 CLI JSON 正例、缺 read_plan 消费证据、缺 target 阻断和 manual integration scope |
| `README.md` | 增加手动 pre_tool_use 入口和当前环境边界 |
| `_migration/v3-migration-execution-plan.md` | 记录 10C 完成状态 |

## 3. 当前状态

```yaml
switch_mode: commit_msg_hard_switch_minimal
environment_integrated: partial
hook_integrated: git.commit-msg
session_start_entry: manual.session_start
session_start_integrated: false
pre_tool_use_entry: manual.pre_tool_use
pre_tool_use_integrated: false
authorization: none
```

10C 没有改变真实 Hook 范围：当前唯一自动拦截入口仍是 Git `commit-msg`。`pre_tool_use.py` 是手动入口或未来外部 adapter 的稳定调用面，不是工具调用已被自动拦截的证明。

## 4. 使用边界

`pre_tool_use.py` 的 receipt 是 stdout-only 过程输出，不写回事实源，不作为 Human Gate、授权、完成证明或持久 session 状态。

调用方必须显式传入已消费的 `--acknowledged-path`。入口不会自动补齐 00/01/02，因为自动补齐会把未消费的 read_plan 伪装成已消费。

若未提供 target、未提供 read_plan 消费证据、target 触发 Human Gate 风险或 preflight 有阻断诊断，CLI 会返回非零或 review_required 状态；这些输出仍是诊断，不是授权。

## 5. 后续

后续若继续推进，应进入 10D `completion_claim` 手动入口，用于任务结束前检查验证证据、未验证范围和残留风险。真实工具前置拦截仍需单独环境 adapter 才能声明接入。
