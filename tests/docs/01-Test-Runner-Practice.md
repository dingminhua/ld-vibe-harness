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

1. `smoke`：快速结构验证和 formal specs 结构检查；
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

## 断言维护边界

测试应验证稳定契约、结构边界、负例诊断和关键哨兵样本，不应把持续增长的仓库现状写成固定答案。

事实对象、正式 specs、附件、review 收据等会随日常工作增长的对象，测试不得要求 AI 手动同步当前总数、分类数量或完整清单。应优先使用以下断言：

1. summary 数量与解析结果自洽，例如 `summary == len(parsed_items)`；
2. 对象类型、字段、状态和引用由 validator/schema 逐项校验；
3. 关键迁移基线或高风险样本使用少量哨兵路径防丢失；
4. formal specs、附件和文件集合使用动态枚举覆盖；
5. 只有 specs 正文、附件或 Code 明确定义闭集时，才允许测试完整闭集值。

新增 Spark、Study、WorkCase、ADR、Pitfall、正式 spec 或附件时，不应仅为同步当前数量而修改测试。若确实需要新增完整清单断言，必须能说明该清单是稳定契约而不是仓库现状快照。

管辖项目配置测试应覆盖默认从 LDVH 本体向父级工作区发现 `LDVH-GOVERNED-PROJECTS.yaml`，但不得把某台机器当前工作区的完整项目清单写成固定答案。应使用临时目录测试精确发现规则，用少量哨兵断言确认当前 LDVH 本体可被解析为管辖项目。

## 交互规格回归

当 specs 新增或修改 Human-facing 交互流程时，测试应覆盖可回归的关键契约，而不是只检查文档存在。

最小同步要求：

1. 在对应 validator 中列出关键术语、边界或必需行；
2. 在 `tests/code/test_ldvh_specs_validate.py` 增加正例和至少一个负例，证明删除关键要求会产生 diagnostic；
3. 若交互涉及选择、确认或写入边界，负例应覆盖开放文本替代选择控件、把后置项放入主选项、最终确认前写入等高风险退化；
4. 测试仍不得固定会随仓库增长的事实对象数量。

例如 LDVH 安装向导的五步状态、`👉` 当前步骤、`✅` 已完成步骤、`决策 / 结果` 列、路径和检查结果图标、LDVH 本体发现、目标工作区根目录确认、配置固定在工作区根目录、带编号和管辖状态的当前配置项目清单、不改或按编号设置管辖项目的两选项、拟写入项目清单、配置正确性结论、配置层级冲突阻断、环境插件未安装时安排安装、插件过时或 stale V2 path 时安排升级、最终确认两个主选项和最终确认前不写入，都属于稳定交互契约，应由 validator 和正反测试共同覆盖。

环境入口审计测试应同时覆盖 stale V2 path 阻断和 V3 Codex shim 可见但未验证 integrated 的状态；仅发现插件 hook 指向 V3 shim，不足以把 Codex runtime 自动入口声明为 integrated。

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
