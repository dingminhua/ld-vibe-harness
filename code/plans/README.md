# 当前 Code 实现规划入口

本目录是 `specs/07-Code 实践与测试规范.md` 要求的当前 Code Implementation Plan 稳定入口。这里的规划只分配实现责任、依赖、接口、副作用、诊断和测试，不定义或覆盖规则源语义。

当前适用规划：

- [macOS POSIX 原子写入结果模型简化](workcase-0064-atomic-write-result.md)：约束原子写入结果形状、保留文件系统安全内核，并把平台后端可用性与 sync/cleanup 诊断从业务提交判断中分离。
- [WorkCase 投影规范到 Python 的精确漂移合同](workcase-presentation-source-contract.md)：覆盖 21 §9.3 非 blocked 六列表的严格 inline-code 语法、测试侧抽取、Python 常量全等比较与 mutation 负向漂移检测。
- [Cognition 行动事项收录与完整 Card](cognition-actionable-items.md)：覆盖 WorkCase 在既有待决定/推进中模块的唯一归属、blocked 非 Gate 呈现，以及 Pitfall draft 共享普通 Card。
- [WorkCase 关闭候选只读投影](workcase-closed-candidate-projection.md)：覆盖 proposal 到非托管 closed `fact_object` 的唯一纯投影、`close-workcase` 同源校验与只读候选 Helper 操作。

新增、替代或移动规划时，必须同步更新本入口；不在列表中的临时会话计划不承担当前 Code 实现规划责任。
