# 当前 Code 实现规划入口

本目录是 `specs/07-Code 实践与测试规范.md` 要求的当前 Code Implementation Plan 稳定入口。这里的规划只分配实现责任、依赖、接口、副作用、诊断和测试，不定义或覆盖规则源语义。

当前适用规划：

- [WorkCase Controller 续跑与行动模板收敛](workcase-controller-continuation.md)：覆盖 06 最小临时工件共同边界、34 五段执行内核、fresh snapshot projection 消费、Reviewer 后连续受控写回与对应 source-contract 回归。
- [WorkCase 当前快照确定性呈现投影](workcase-current-snapshot-presentation.md)：覆盖 21 权威语义的唯一 Code 维护点、Helper 精确读取投影、Web 字段级读取投影、Python 到 TypeScript 的单向生成、诊断与全状态矩阵验证。
- [Web 字段级事实读取迁移](web-field-level-reading.md)：覆盖经 Helper 管辖解析约束的 Web 当前事实直读、字段级问题与未解析结构呈现、WorkCase 统一读取、旧 V4 Python machine 退役及对应验证。

- [Study 重建事实契约](study-rebuild-fact-contract.md)：覆盖 v3 基线下的 Study 五段正文、`active / retired` 生命周期、共用 URLs 字段、Code/Web 派生面、历史对象退出与验证边界。
- [Spark 完整语义与分层阅读纵切](spark-reading-vertical-slice.md)：覆盖 Spark 完整 `summary`、Helper F2 有界原样摘录、Web 独立完整阅读、三字段 direct capture 提示与对应测试边界。
- [规范上下文组合读取](specification-context-reading.md)：覆盖 `read-specification-context` 的精确请求解析、同快照 L3 组合、标题导航、L1 scope 回指、摘要、partial 结果与发行快照验证。
- [Codex 工作上下文规则引导与显式事实恢复](codex-context-recovery.md)（**已退役**：adapter 形态已被 00 §8.2 废除，详见文内标注）：覆盖来源定义的规则引导 profile、显式事实恢复分支及其验证边界；`ldvh-work-context` 核心仍为 09 §5.4 首选入口。
- [full-v4 Working Tree 证据生产与运行记录接入](full-v4-working-tree-evidence.md)：覆盖 `code/ldvh/testing` 中的 Working Tree manifest 采集、full-v4 耐久运行记录和 `tools/run_full_tests.py` 入口。
- [事实对象完整性与质量 Gate](fact-integrity-quality-gate.md)：覆盖 full-v4 对当前事实库完整机械消费的只读检查，以及恢复既有 Ruff 质量 Gate。
- [Spark `implemented` 终态纵切](spark-implemented-terminal.md)：覆盖 Spark 内容直接落实的专属终态、F4 处置核对、无效历史终态的受控更正以及相应 Code、Helper、Web 与验证边界。
- [WorkCase 专属受控变更 Helper 操作](workcase-controlled-update.md)：覆盖共享单对象更新事务、统一事件时点、`update-workcase`、锁失败诊断、响应档位与 YAML 序列化。
- [环境无关启用、只读 doctor 与用户文档打包](environment-neutral-enablement.md)：覆盖 `ldvh.doctor`、`ldvh-doctor/1`、既有接入面投影、用户文档随包、发行物生命周期和环境无关验证边界。

新增、替代或移动规划时，必须同步更新本入口；不在列表中的临时会话计划不承担当前 Code 实现规划责任。
