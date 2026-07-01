# 10D completion_claim 手动入口记录

> 文件状态：temporary migration closure。本文记录 V3 `completion_claim` 的最小可用入口：提供手动/外部 adapter 可调用的完成声明前检查 CLI，不声明真实完成前 Hook 已自动接管。正式规则仍以 `specs/` 正文为准。

## 1. 接入结论

10D 审计后确认：V3 已具备 `build_runtime_event(event="completion_claim")`，可以阻断缺少验证证据、未验证范围或残留风险说明的完成声明。但当前协作环境没有已暴露的真实 completion hook，不能自动拦截 AI 的自然语言完成声明。

因此 10D 不做自动完成前拦截声明，只提供明确入口：

```bash
python3 code/completion_claim.py \
  --target-path "<目标路径>" \
  --verification-evidence "python3 code/specs_validate.py all --format text --fail-on-diagnostics"
```

该入口输出：

1. `completion_claim` runtime receipt；
2. verification evidence 列表；
3. diagnostics；
4. source refs；
5. `authorization=none`；
6. `environment_integrated=false`；
7. `integration_scope=manual.completion_claim`。

## 2. 交付物

| 文件 | 作用 |
|---|---|
| `code/completion_claim.py` | 专用 `completion_claim` CLI，输出 text/json 完成声明前检查和 stdout-only receipt |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖 CLI JSON 正例、缺 verification evidence 阻断和 manual integration scope |
| `README.md` | 增加手动 completion_claim 入口和当前环境边界 |
| `_migration/v3-migration-execution-plan.md` | 记录 10D 完成状态 |

## 3. 当前状态

```yaml
switch_mode: commit_msg_hard_switch_minimal
environment_integrated: partial
hook_integrated: git.commit-msg
session_start_entry: manual.session_start
session_start_integrated: false
pre_tool_use_entry: manual.pre_tool_use
pre_tool_use_integrated: false
completion_claim_entry: manual.completion_claim
completion_claim_integrated: false
authorization: none
```

10D 没有改变真实 Hook 范围：当前唯一自动拦截入口仍是 Git `commit-msg`。`completion_claim.py` 是手动入口或未来外部 adapter 的稳定调用面，不是完成声明已被自动拦截的证明。

## 4. 使用边界

`completion_claim.py` 的 receipt 是 stdout-only 过程输出，不写回事实源，不作为 Human Gate、验收、授权或持久 session 状态。

调用方必须显式传入 `--verification-evidence`。该值可以是已运行验证命令、未验证范围或残留风险说明；缺失时 CLI 返回阻断。

通过该入口只表示“完成声明前检查没有发现当前输入缺少验证证据”，不表示 Human 已验收，也不表示事实源已回写。

## 5. 后续

10B-10D 已形成 manual runtime 三件套：`session_start.py`、`pre_tool_use.py`、`completion_claim.py`。后续若继续推进，应评估真实 runtime adapter / 外部环境接入，判断是否能把这些 CLI 接入实际 session、tool 和 completion 事件；没有真实触发能力时不得声明自动接管。
