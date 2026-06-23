# Code 归档与性能审计

> 版本：0.1
> 更新：2026-06-23
> 范围：active `code/` 路径、历史辅助脚本归档和 CLI 启动性能审计
> 上位规范：[`specs/04-Code确定性执行规范.md`](../../specs/04-Code确定性执行规范.md)、[`specs/08-测试基础规范.md`](../../specs/08-测试基础规范.md)

## 0. 文件性质

本文是 `code/docs/` 下的 Code 参考实现审计记录，不是正式规范、命令授权表、测试治理规则或事实源边界。

本文只记录当前 Code 归档判断、性能观察和后续实施顺序。若归档、删除或恢复任一 Code 能力会改变 active 命令、测试入口、事实源写入行为、Hook/Skill 调用或 Web 调用，应回到对应 specs 附件和 Code 结构文档同步。

## 1. 审计结论

当前 active `code/` 路径应只保留稳定 CLI、兼容包装入口和当前可测试能力域模块。

| 对象 | 结论 | 依据 |
|---|---|---|
| `code/specs_validate.py` | active | specs 综合检查、v2-check、preflight、deployment-entries 等 CLI 兼容入口 |
| `code/fact_cli.py` | active | 工作对象查询入口，Rules 和 Web 仍消费 |
| `code/fact_validate.py` | active | 工作对象事实源校验入口，package script 仍消费 |
| `code/commit_validate.py` | active | Git commit message 校验入口，Skill 和 Hook 仍消费 |
| `code/hook_dispatch.py` | active | Hook 统一 dispatcher，`hooks/ldvh-hooks.yaml` 仍消费 |
| `code/spec_checks/` | active | specs 校验、知识地图、preflight 和派生报告能力域 |
| `code/fix_block_scalar.py` | 已归档 | 无 active 命令、测试、Rules、Skill、Hook 或 Web 引用；属于历史写入型辅助脚本 |

## 2. 已归档对象

| 原位置 | 归档位置 | 归档原因 | 恢复条件 |
|---|---|---|---|
| `code/fix_block_scalar.py` | `history/code-archive/fix_block_scalar.py` | 一次性 YAML block scalar 修复脚本；当前无 active 消费，且具备写入行为 | 需要重新使用时，必须先登记为 active Code 能力、补 preflight/测试和事实源边界说明 |

`history/code-archive/` 不属于 active Code 路径。默认测试、CLI、Web、Rules、Skills、Hooks 不应直接调用该目录下文件。

## 3. 性能观察

本次审计确认，单纯归档未被 import 的脚本不会明显改善 CLI 启动性能；真正的启动成本来自 `code/specs_validate.py` 顶部一次性 import 多个 `spec_checks` 模块。

一次 `python3 -X importtime code/specs_validate.py preflight ...` 观察显示，即使只运行 preflight，也会加载 `doc_structure`、`deployment_entries`、`consistency`、`field_registry`、`human_gate`、`index`、`ldvh_assurance`、`web_validate`、`v2` 等模块。

这不改变功能正确性，但会让轻量命令承担不相关检查域的启动成本。当前已为直接执行的 `preflight`、`v2-check`、`governed-projects`、`deployment-entries`、`runtime-projection`、`human-gate`、`human-gate-report`、`field-registry`、`doc`、`refs` 和 `assurance` 子命令增加脚本级 fast path，使这些命令不再加载完整 specs 检查聚合入口；通过导入 `specs_validate.py` 后调用 wrapper 的测试兼容路径仍保持不变。

## 4. 后续优化顺序

| 顺序 | 工作 | 约束 |
|---|---|---|
| 1 | 为直接执行的 `preflight`、`v2-check`、`governed-projects`、`deployment-entries`、`runtime-projection`、`human-gate`、`human-gate-report`、`field-registry`、`doc`、`refs` 和 `assurance` 增加脚本级 fast path | 已完成；不改变输出结构、exit code 或诊断码 |
| 2 | 为 `specs_validate.py` 增加懒加载模块 helper | 必须保留现有 CLI、测试 wrapper 和模块归属断言 |
| 3 | 再让 `consistency`、`assurance-report`、`ldvh-assurance-check` 和 `web-validate` 等聚合或报告命令按能力域延迟加载依赖 | 不改变输出结构、exit code 或诊断码 |
| 4 | 再清理只为历史兼容暴露的常量 alias | 需先查 tests、Rules、Skills、Hooks、Web 是否仍引用 |
| 5 | 最后评估长期不再使用的兼容子命令是否降级、归档或删除 | 必须同步 04.Att.02、04.Att.09、08.Att.05 和 `code/docs/01` |

懒加载优化应单独提交，不与归档、命令语义变化或输出结构变化混合。
