# 当前 Code 实现规划入口

本目录是 `specs/07-Code 实践与测试规范.md` 要求的当前 Code Implementation Plan 稳定入口。这里的规划只分配实现责任、依赖、接口、副作用、诊断和测试，不定义或覆盖规则源语义。

当前适用规划：

- [Codex startup/resume 有界责任候选恢复](codex-context-recovery.md)：覆盖 `code/ldvh/hooks/context_recovery.py` 的项目/WorkCase 候选、完整 coverage、有界恢复投影，以及 Codex 薄 adapter、打包和当前环境验证边界。
- [full-v4 Working Tree 证据生产与运行记录接入](full-v4-working-tree-evidence.md)：覆盖 `code/ldvh/testing` 中的 Working Tree manifest 采集、full-v4 耐久运行记录和 `tools/run_full_tests.py` 入口。
- [WorkCase 专属受控变更 Helper 操作](workcase-controlled-update.md)：覆盖共享单对象更新事务、统一事件时点、`update-workcase`、锁失败诊断、响应档位与 YAML 序列化。
- [环境无关启用、只读 doctor 与用户文档打包](environment-neutral-enablement.md)：覆盖 `ldvh.doctor`、`ldvh-doctor/1`、既有接入面投影、用户文档随包、发行物生命周期和环境无关验证边界。

新增、替代或移动规划时，必须同步更新本入口；不在列表中的临时会话计划不承担当前 Code 实现规划责任。
