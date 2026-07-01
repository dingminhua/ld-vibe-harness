# 16A receipt 存储判断

文件状态：阶段 16 记录。本文只记录当前 receipt 留存判断，不新增事实对象类型，不创建 dedicated receipt 事实源，不改变 runtime 输出形态。

## 判断目标

阶段 16 用于判断 stdout-only runtime receipt 是否需要长期事实源回写，以及如果需要留存，应写到哪里、保留哪些字段、如何清理。

正式依据：

1. `specs/03-事实源与Git溯源规范.md`：runtime receipt 证明某个消费动作发生过，不证明规则满足、授权完成或事实稳定；
2. `specs/11-环境适配规范.md`：stdout-only receipt 只能作为当次过程输出；如需稳定存储，必须先补事实源回写规则、字段 schema、清理策略和测试；
3. `specs/09-测试与验证规范.md`：验证声明必须说明证据回指、未验证范围和残留风险。

## 当前决策

V3 当前不建立独立 receipt 事实源，也不创建 `ldvh-base/runtime-receipts/` 或等价目录。

原因：

1. 当前除 `git.commit-msg` 外没有 runtime 自动入口 integrated；
2. manual receipt 主要用于当次 AI 判断和诊断，不具备长期事实源价值；
3. raw receipt 长期保存会制造第二事实源、隐私/噪音和清理负担；
4. 当前稳定事实已经有更合适的位置承接：WorkCase、验证声明、commit records、迁移记录或后续事实对象。

## 留存分流

如 receipt 内容需要长期保留，应先由 AI 定性，只保留被采纳的结论、证据或缺口，不保存整份 raw receipt。

| 留存内容 | 目标位置 | 最小字段 | 保留策略 |
|---|---|---|---|
| 完成声明或测试证据 | `verification_evidence`、验证声明或对应测试记录 | 验证入口、关键输出、结论、未验证范围、证据回指 | 随对应事实对象或提交记录保留 |
| WorkCase 关闭判断 | `closure_evidence`、`human_closure_confirmation`、`residual_risks`、`followup_refs` | 关闭结果、Human 判断、残留风险、后续分流 | 随 WorkCase 生命周期保留 |
| Git 提交证据 | Git commit records 与 commit message | 变更摘要、验证摘要、read_plan 消费证据、残留风险 | 随 Git 历史保留 |
| 环境接入缺口 | `_migration/*` 或后续环境适配事实对象 | 入口类型、状态、缺口、验证命令、后续条件 | 迁移期间保留，归档需 Human Gate |
| 可复用经验 | Spark、Pitfall、Study 或 ADR | 被采纳结论、适用条件、验证证据 | 按对应事实对象规则保留 |

## 后续进入条件

只有同时满足以下条件，才重新评估 dedicated receipt storage：

1. 至少一个非 Git runtime 自动入口 integrated；
2. receipt 需要跨会话恢复，而现有事实对象无法承接；
3. 字段 schema、事实源位置、保留期限和清理策略已定义；
4. raw payload 中的敏感信息、路径、命令输出和上下文噪音有过滤策略；
5. 有自动化测试覆盖写入、回读、清理和不得替代事实源；
6. Human Gate 同意新增事实源或存储目录。

## 验证

本阶段验证入口：

1. `python3 code/test_runner.py smoke`；
2. `python3 code/environment_entry_audit.py --format json`；
3. `python3 code/environment_status.py --format json`；
4. `python3 -m pytest tests/code/test_ldvh_specs_validate.py::test_runtime_session_start_generates_stdout_receipt tests/code/test_ldvh_specs_validate.py::test_runtime_completion_claim_requires_verification_evidence -q`；
5. `git diff --check`。
