# LDVH Runtime Protocol Entry

文件类型：`hook_protocol_entry`。本文是 LDVH Runtime Protocol 的可执行入口，不执行本文则未进入 LDVH 保障链路。
AI 读取本文后必须立即执行下方对应的 lifecycle event，否则不得进入写入、提交或完成声明。

## 权威回指

`specs/01-保障与衔接.md`、`01.Att.01`、`01.Att.05`、`specs/07-Code确定性执行规范.md`

## Code 入口 — 必须执行

| canonical event | 执行时机 | 当前 Code 入口 |
|---|---|---|
| `session_start` | 会话第一条回复，读取本文后立即执行 | `python3 code/runtime_adapter.py session-start --format json` |
| `pre_tool_use` | 每次写入、编辑或提交操作前执行 | `python3 code/runtime_adapter.py pre-tool-use --format json` |
| `completion_claim` | 声明完成、交还工作或关闭会话前执行 | `python3 code/runtime_adapter.py completion-claim --format json` |
