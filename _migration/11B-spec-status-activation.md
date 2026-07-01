# 11B specs status 激活记录

阶段：11B

目的：解决 V3 主线已经日常使用，但下位 specs 仍大量停留在 `candidate` / `authority: candidate` 的状态不一致。

## 处理动作

1. `specs/` 下正式规范正文已统一调整为 `status: active`、`authority: active`；
2. `specs/attachments/` 下正式附件已统一调整为 `status: active`；
3. 新增 `specs/11-环境适配规范.md` 作为 active 正式规范；
4. 新增 11 的 4 个环境适配附件作为 active 正式附件；
5. formal review hash gate 从 `_migration/reviews/` 迁入 `reviews/formal/`，并重新同步 hash。

## 结论

V3 不再处于“00 active，其余 candidate”的 soft mainline 状态。当前正式 specs 和已迁入附件均按 active 进入主线。

## 边界

active 只表示这些规范和附件成为当前规则源，不表示所有运行时入口、Web 写入、外部 adapter 或非提交行动模板已经实现。
