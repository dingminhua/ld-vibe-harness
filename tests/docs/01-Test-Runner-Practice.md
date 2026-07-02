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

## 反馈链路

runner 必须让 AI 能在长测试期间持续判断当前进度：

1. 每个 stage 开始前输出 `[n/total] stage name` 和实际命令；
2. 每个 stage 结束后输出 `ok` 或 `failed`，并带耗时；
3. 所有 stage 结束后输出 summary，列出每个 stage 的结果和总耗时；
4. pytest stage 必须带 `--tb=short`，让失败时优先显示短 traceback 摘要；
5. pytest stage 应保留 `--durations`，用于定位慢测试和后续分层优化。

`tests/code/test_ldvh_test_runner.py::test_all_pytest_stages_use_short_tracebacks` 覆盖 `--tb=short` 防回归。新增或改名 pytest stage 时，必须先让该测试通过。

## CLI 测试包装

Python CLI 测试应统一走 `tests/code/test_ldvh_specs_validate.py` 中的 `_run_cli` 包装，而不是直接 `subprocess.run([sys.executable, ...])`。

`_run_cli` 的职责：

1. 默认捕获 stdout/stderr；
2. 默认设置 timeout；
3. `TimeoutExpired` 时打印已捕获 stdout/stderr；
4. 保持 `check=True/False` 的调用语义，便于正反例测试。

直接 `subprocess.run` 只用于非 Python CLI 场景，例如 Git 命令、直接执行已安装 Hook 文件或检查 Git 配置；这类调用也应设置合理 timeout。

## 共享 Fixture

高成本构建结果应使用 session 级 fixture 缓存，避免同一测试文件内反复构建导致静默期过长。

当前共享 fixture：

1. `validation_result`：缓存 `ldvh_specs.build_validation(ROOT)`；
2. `e2e_rehearsal_result`：缓存 `ldvh_specs.build_e2e_rehearsal(...)`。

调用方不得修改 fixture 返回值。fixture 已使用 `copy.deepcopy` 防御，但测试仍应按只读消费编写。

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
python3 -m pytest tests/code _migration/tests -q --durations=20 --tb=short
```

因此 `_migration/tests` 仍是稳定回归的一部分，不能在未替代前删除。
