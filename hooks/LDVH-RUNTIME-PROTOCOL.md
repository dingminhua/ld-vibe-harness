# LDVH Runtime Protocol Entry

文件状态：hook protocol entry。本文是 V3 放在 `hooks/` 下的 Runtime Protocol 可见入口。

本文只写三类内容：

1. 入口身份：`hook_protocol_entry`；
2. 权威回指：`specs/01-保障与衔接.md`、`01.Att.01`、`01.Att.05`、`specs/07-Code确定性执行规范.md`；
3. 当前 Code 入口：`code/runtime_adapter.py` 的三个 lifecycle event。

## Code 入口

| 生命周期语义 | canonical event | 当前 Code 入口 |
|---|---|---|
| 会话开始或上下文恢复 | `session_start` | `python3 code/runtime_adapter.py session-start --format json` |
| 写入、编辑、提交前检查 | `pre_tool_use` | `python3 code/runtime_adapter.py pre-tool-use --format json` |
| 完成声明、交还或关闭前检查 | `completion_claim` | `python3 code/runtime_adapter.py completion-claim --format json` |
