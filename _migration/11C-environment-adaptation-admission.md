# 11C 环境适配规范迁入记录

阶段：11C

目的：补齐 01 中长期悬空的环境适配归口，承接 Rules 薄引用、Hook、插件、Runtime Protocol、canonical event、trigger source、receipt 和环境适配边界。

## 正式迁入

1. 新增 `specs/11-环境适配规范.md`；
2. 新增 `specs/attachments/11.Att.01-环境入口类型表.md`；
3. 新增 `specs/attachments/11.Att.02-环境接入状态表.md`；
4. 新增 `specs/attachments/11.Att.03-runtime-payload字段表.md`;
5. 新增 `specs/attachments/11.Att.04-环境安装回滚检查表.md`。

## 吸收范围

11 正文吸收以下 V2 / 迁移期能力：

1. 环境入口分类；
2. 自动 Hook 与 manual-ready 入口分界；
3. runtime payload 和 stdout-only receipt 边界；
4. Rules / Skill 顶层机制取消后的 legacy/removed_top_level 口径；
5. 安装、回滚、状态检查和受管项目 target-first 边界。

## 当前状态

后续归口调整：独立 `specs/11-环境适配规范.md` 不再作为正式 spec 保留，其规则已吸收到 `specs/01-保障与衔接.md` §6；原 11 附件已改为 `01.Att.03-06` 并继续作为 01 的授权附件。

当前 worktree 只有 `git.commit-msg` 是 integrated 自动入口。`manual.runtime_adapter`、`manual.session_start`、`manual.pre_tool_use` 和 `manual.completion_claim` 均是 manual-ready，不是自动触发证明。

## 后置项

真实 session start、pre tool use、completion claim、外部 runtime adapter、repo instruction 或插件入口，只有在真实触发、稳定 payload、失败处理、安装状态、回滚方式和测试证据齐备后，才能升级。
