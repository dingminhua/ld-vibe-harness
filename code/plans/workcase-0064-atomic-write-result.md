# macOS POSIX 原子写入结果模型简化

## 1. 目标、来源与实现起点

本规划承接 `workcase-0064` 与 `spark-0062`，依据 00 对 Code 确定性执行能力、来源边界和据实判断的要求，以及 07 的 Code Implementation Plan 与平台相关面纪律。目标是在不改变外部事实语义的前提下，消除 `AtomicWriteResult` 四个字段可任意组合的内部状态空间，并把事实写入的业务提交判断与平台后端可用性、同步证据、临时文件清理证据分开。

经并发工作收敛后，实现归因基线固定为 commit `70115a3207c68fc0f8118f74ab451f06f876f12d`，不改写历史。该提交主要承载 WC-0063，但已同时承载 WC-0064 在 `fact_creation_operation.py`、`fact_update_operation.py`、`workcase_update_operation.py` 及相应 Helper tests 中的平台能力符号和诊断迁移 hunk；这些 hunk 不再进入 WC-0064 的剩余提交。后续 commit `92af3846e` 仅关闭 WC-0063，作为当前 HEAD 的并发事实保留，不改变 WC-0064 的实现归因基线。本规划以当前 Working Tree 为实际输入，最终只提交 `70115a3` 之后尚未承载的 WC-0064 计划、核心实现、直接消费者与测试差异。

本增量不修改 Specs，不定义新的 Helper 或事实对象字段，不改变既有结果 status 枚举，不改变 Windows 是否允许公共事实写入，也不删除任何原子性或路径安全措施。若实现发现必须改变上述外部合同，停止本增量并另行形成来源决策。

## 2. 必须保持的安全内核

POSIX 创建、存储、条件替换与删除继续保持以下行为：

- 临时文件与目标位于同一目录，写入后先 `fsync` 文件，再执行 no-overwrite link 或原子 replace；
- 目录 `fsync` 保持 best-effort，并只作为当次 sync scope 证据，不被提升为绝对物理持久性保证；
- 继续使用 `dir_fd`、`O_NOFOLLOW`、regular-file 检查和受控相对路径，拒绝链接、reparse 或不稳定路径拓扑；
- 创建保持 no-overwrite，替换保持预读、二次比较和 CAS 冲突语义；
- 系统调用报错后继续回读命名空间，尤其保留 `_reconcile_replace`，区分 committed、not committed 与 uncertain；
- 写后回读、rollback 及 cleanup residue 诊断继续可观察。

这些项目是回归约束，不是本次简化对象。

## 3. 结果模型与模块责任

`filesystem.AtomicWriteResult` 继续作为跨模块内部接口，但实例只能由三个命名构造入口形成：

| 形状 | 允许的 outcome | 决策含义 | 可携带诊断 |
|---|---|---|---|
| committed | `created`、`replaced`、`stored`、`removed` | 操作语义已经进入目标命名空间 | sync scope、cleanup residue |
| not committed | `conflict`、`unavailable` | 已确认没有按请求提交 | cleanup residue |
| uncertain | `unavailable` | 观察不足，必须重新读取 | cleanup residue |

`namespace_state`、`durability` 与 `cleanup` 保留为只读兼容投影，使现有诊断与消费者可以小步迁移；它们不再是调用方可独立组合的构造参数。sync scope 只属于 committed 形状；not committed 与 uncertain 的兼容 durability 恒为 `unknown`。业务消费者仍只依据 outcome 与 commit state 判断 created/conflict/unavailable、rollback 或重读，sync/cleanup 仅进入 changes、verification、gaps 或测试证据。

`filesystem` 唯一维护结果形状、POSIX/portable 实现和平台后端能力探针。事实 application 负责领域流程、CAS 后回读及 rollback，不解释 sync scope。Helper operation 只映射领域结果并携带诊断，不取得文件系统结果或平台合同定义权。

## 4. 平台边界与直接消费者

现有 `durable_writes_enabled()` 更名为表达实现能力的 `native_atomic_fact_writes_supported()`（最终名称可在同义范围内调整）。它只回答当前平台是否具备已启用的公共事实写入后端：POSIX 为真，Windows 及未知平台为假。Windows 的公共写入仍在 mutation 前失败；portable file-only 候选路径和显式 `allow_file_only=True` 的底层测试能力不变。

直接消费者范围为：

- 结果决策：`facts.creation`、`facts.creation_application`、`facts.update_application`、`facts.workcase_update`、`facts.legacy_change_log_migration`；
- 平台能力与诊断映射：上述 application，以及 `helper.operations.fact_creation_operation`、`fact_update_operation`、`workcase_update_operation`、`legacy_change_log_migration_operation`；
- 内部类型转发：`facts.creation`、`facts.update` 与相应结果 DTO；
- 验证：`code/tests/facts/test_atomic_write.py`、直接 application/Helper tests 和 platform tests 中对旧构造入口或旧能力名称的引用。

不改动这些模块的公开 operation identity、请求字段、事实 Schema 或状态机。对已有脏文件只做精确符号替换和必要诊断措辞调整，提交前按 hunk 与 Index 核对，不能隔离时不得混入提交。

## 5. 错误、诊断、测试与回滚

系统调用异常继续降级为三种 commit shape；不能可靠观察时必须为 uncertain，不得把异常吞成成功。directory sync 失败仍返回 committed，并以 unknown sync scope 诊断；临时文件删除失败仍以 residue 诊断；这些证据不得阻止已经确认的业务提交，也不得被省略。

测试矩阵至少覆盖：正常创建/存储/替换/删除、创建冲突、替换 CAS 冲突、文件 sync 失败、directory sync 失败、cleanup residue、link/replace 提交后抛错的 reconciliation、链接路径拒绝、结果构造形状约束、POSIX 能力为真、Windows 能力为假且公共写入零变更。先运行原子写聚焦测试，再运行直接 facts/Helper/platform tests、Ruff 和适用的全量 Code tests；macOS 实机结果只证明当次平台与受测路径，Windows 由既有 portable/platform tests 保持行为证据，跨平台已验证声明按 07/09 的平台纪律据实收窄。

当前中间证据：聚焦及直接消费者回归 `262 passed, 2 skipped`；全量 Code 回归 `1452 passed, 10 skipped`，跳过项均为当前 macOS 无法实跑的 native Windows 用例。受影响文件的 Ruff check 已通过；format check 在四个同时含 WC-0063 并发内容的文件上报告非 WC-0064 hunk，不为了本案越界改写。首次 full-v4 记录 `run-c44c24a8800949cdb330016e9b4aa7c7` 因并发 WC-0063 差异的 code-lint 失败而未进入后续步骤；待当前合并树稳定后重跑并以新记录为准。

每一步用 Git diff 对照上述边界。若发现安全原语、CAS、reconciliation、写后回读或 Windows 行为变化，立即撤销本 WorkCase 对应 hunk；若无法把本次 hunk 与既有脏改动分离，保留工作树、停止提交并交还精确文件与恢复入口。
