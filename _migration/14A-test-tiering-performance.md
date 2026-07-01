# 14A 测试性能与分层优化

文件状态：阶段 14 记录。本文只记录 V3 主线后续测试分层补强，不改变测试语义，不降低完成声明的验证责任。

## 背景

阶段 12 和 13 的 `tests/code` 目标验证显示，慢项主要集中在 runtime、preflight、manual adapter 和 e2e rehearsal 相关测试，单次 `tests/code` 全量约 5 分钟以上。日常小改如果默认跑完整 `tests/code`，反馈过慢；但直接跳过慢项又会隐藏 runtime/e2e 风险。

## 正式承接

本阶段做以下承接：

1. `specs/09-测试与验证规范.md` 增加 smoke、targeted、runtime、full 的分层契约；
2. `pyproject.toml` 注册 `slow`、`runtime`、`e2e` pytest markers；
3. `tests/code/conftest.py` 按测试名自动给 runtime/e2e 测试加 marker，避免逐个维护装饰器；
4. `code/test_runner.py` 新增 `runtime` profile；
5. `targeted` profile 新增 `--slow auto|skip|include`，默认按变更路径自动选择 runtime/e2e 层；
6. 根 `package.json` 和 `README.md` 增加 `test:runtime` 和 slow policy 用法。

## 边界

本阶段不删除任何慢测试，不改变 full regression 覆盖范围，不引入 pytest-sugar、xdist 或其它测试依赖，不默认并行化 slow 层。

`--slow skip` 只能用于目标验证和等价验证场景；完成声明必须说明 runtime/e2e 未验证范围。阶段收口、跨域迁移、runtime/环境入口变更和高风险回归仍应使用 `runtime` 或 `full`。

## 验证

阶段 14 需要至少运行：

1. `python3 code/test_runner.py smoke`；
2. `python3 code/test_runner.py targeted --slow skip --changed code/test_runner.py`；
3. `python3 code/test_runner.py runtime`；
4. `python3 -m pytest tests/code/test_ldvh_test_runner.py -q`；
5. `python3 code/specs_validate.py all --format text --fail-on-diagnostics`。

若验证通过，应同步 `reviews/formal/09-formal-review.yaml` 的 hash。
