# Test Runner 实现实践

本文是 Tests 实现域文档，承接 `specs/09-测试与验证规范.md` 中不应写入 specs 正文的 runner 命令、slow policy 和维护实践。本文不定义新的验证标准；若与 specs 冲突，以 specs 为准。

## 分层入口

当前 V3 runner 使用以下 profile：

```bash
python3 code/test_runner.py smoke
python3 code/test_runner.py targeted --changed "<path>"
python3 code/test_runner.py targeted --slow skip --changed "<path>"
python3 code/test_runner.py runtime
python3 code/test_runner.py full
```

职责：

1. `smoke`：快速结构验证和 formal review hash gate；
2. `targeted`：根据变更路径选择目标测试；
3. `runtime`：覆盖 runtime facade、manual adapter、preflight、completion claim、环境入口和静态 e2e 演练；
4. `full`：阶段收口、跨域迁移、发布前验证或高风险回归。

## Slow Policy

`targeted` 支持：

```bash
python3 code/test_runner.py targeted --slow auto --changed "<path>"
python3 code/test_runner.py targeted --slow skip --changed "<path>"
python3 code/test_runner.py targeted --slow include --changed "<path>"
```

`--slow skip` 只表示本次跳过 slow/runtime/e2e 层，完成声明必须说明未验证范围和残留风险。`full` 仍保留 slow 层，不因为 targeted 快速验证而降低回归覆盖。

## 并行边界

慢速层不默认并行化。需要并行运行时，应先确认依赖、内存、临时目录、端口和外部服务隔离，否则并行可能造成 OOM、端口冲突或 flaky 结果。

## 迁移测试

当前 full profile 仍运行：

```bash
python3 -m pytest tests/code _migration/tests -q --durations=20
```

因此 `_migration/tests` 仍是稳定回归的一部分，不能在未替代前删除。
