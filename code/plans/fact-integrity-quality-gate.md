# 事实对象完整性与质量 Gate

## 范围与来源

本增量修复当前工程质量 Gate，并将“当前事实库是否可被完整机械消费”纳入 full-v4 的固定检查计划。直接消费 `00` 的 V1、V3、V5、V6、V8 与验证边界，`05` 的事实对象候选发现、partial coverage 和机械校验边界，`07` 的实现规划、风险驱动测试和 full-v4 运行记录要求，以及 `20` 的 Spark 状态与关系规则。

不新增事实类型、关系、Helper 领域操作或 AI 行动分类；不让 Code 从对话判断 Spark 相关性、对象化必要性、Human 授权或工作完成；不自动修改任何现有事实对象。

实现起点：`ac304af7`；规划覆盖当前 Working Tree 尚未提交的实现变化。

## 目标

1. 让 full-v4 在现有 lint、Code tests、Web typecheck/tests/build 之外，以实际 Helper 读取边界检查当前管辖项目事实对象是否可完整机械消费。
2. 使无效、不可读或非 canonical 的事实对象导致 Gate 明确失败，而不是仅在某次创建前 F2 查询中偶然暴露。
3. 清除当前 Ruff 报告的实现和测试质量错误，恢复已有全量质量 Gate 的可执行性。

## 模块与责任

| 模块 | 责任 | 不承担 |
|---|---|---|
| `code/ldvh/testing/fact_integrity.py` | 在当前实际 worktree 中解析管辖边界、调用既有事实读取/候选发现能力或其共享机械层，返回可机读的完整性结果 | 不判断自然语言语义、授权或重复对象 |
| `code/ldvh/testing/test_runs.py` | 将该检查作为 full-v4 固定步骤记录其 argv、输出、状态和退出码 | 不解释检查失败为工作完成或事实真实 |
| `tools/run_full_tests.py` | 继续只启动和回读 durable full-v4 运行记录 | 不自行扫描或补造事实结论 |
| `code/tests/testing/` | 覆盖完整、invalid、unavailable 和 runner 计划/记录同步 | 不依赖本仓库事实库偶然状态作为唯一 fixture |
| 既有 lint 问题所在模块/测试 | 仅做行为保持的 import、格式和未使用变量修正 | 不借清理改变领域行为 |

事实完整性检查应复用 `05` 已定义的 canonical 载体、schema、关系和 project validation；它只能报告当前可证明的 `complete` / `partial` / `unavailable` 范围。AI 仍负责据此判断当前候选是否语义相关，以及能否创建或更新对象。

## 接口与副作用

该检查是只读 Code/test 入口。它不新增 Helper CLI 公开操作，不变更事实对象 Schema，也不写入 allocator、事实文件、Git 或缓存。full-v4 仅新增一个固定外部进程步骤，继续由既有 durable runner 记录；任何非零退出码使该次运行失败并保留原始输出。

## 风险与测试映射

| 风险 | 检查 |
|---|---|
| 无效对象被静默排除，创建前错误声称无重复 | fixture 中构造 invalid Spark，断言完整性 Gate 失败且保留对象路径/问题 |
| 不可读或 noncanonical 载体被误报为完整 | fixture 中构造 unavailable/非 canonical 载体，断言 Gate 不通过 |
| Gate 只查 Spark、漏查其它四类对象 | 五类对象混合 fixture 与全类型请求断言 |
| runner 新步骤破坏 durable record 的固定顺序/聚合 | 更新 `test_test_runs.py` 的计划、状态与失败前缀断言 |
| lint 清理改变运行时行为 | 对受影响公开入口运行聚焦测试及 Ruff |

验证选择：本次改变 full-v4 固定步骤与共享事实读取消费边界，跨测试 runner 与事实校验两个模块，属于高影响范围；完成前需要聚焦 Code tests、Ruff、以及 durable full-v4。Web 本身未改，但 full-v4 仍作为完整运行记录执行。未验证范围：真实外部 AI 环境和 AI 对话语义判断，不由本增量声称覆盖。

## 演进与缺口

`spark-0026` 当前 routed 状态缺少 `routed-to` 关系。Gate 应将其揭示为失败；它不得自行推断承接对象或将其改为 discarded。该事实对象的修复须在 Human 明确其实际处置含义后，另行以受控更新和回读完成。

