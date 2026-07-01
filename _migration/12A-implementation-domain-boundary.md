# 12A 实现域实践边界补强

文件状态：阶段 12 记录。本文只记录 V3 主线后续补强过程，不授权新实现能力已经接入。

## 背景

V2 已经形成一个核心分工：specs 定义需求、规则、契约和边界；Code、Web 和 tests 各自完成实践实现。V3 主体迁移后需要把该分工写入正式 specs，避免后续把实现语言、框架、模块拆分、页面组件、测试文件清单或性能实践写入 specs 正文。

## 正式承接

本阶段做以下承接：

1. `specs/04-Specs基础规范.md` 增加实现域实践边界，声明 specs 只定义需求、规则、契约、边界、Human Gate、Stop Conditions 和验证要求；
2. `specs/07-Code确定性执行规范.md` 声明 Code 实践由 `code/` 和 `code/docs/` 承接；
3. `specs/08-Web信息同步规范.md` 声明 Web 实践由 `web/` 和 `web/docs/` 承接；
4. `specs/09-测试与验证规范.md` 声明测试实践由 `tests/` 和对应实现域承接，V3 不强制要求 `tests/docs/`；
5. `code/ldvh_specs.py` 增加 `validate_implementation_domain_boundaries`；
6. `tests/code/test_ldvh_specs_validate.py` 增加实现域边界正例和 04/07/08/09 负例。

## 边界

本阶段不新增 Code、Web、tests 的具体实践文档，不改造 Web 页面，不调整测试分层，不声明 runtime、Hook 或环境入口能力变化。

如果后续实践经验需要形成稳定规则，应回到对应 specs 或附件；如果只是实现经验、命令说明、模块说明或测试维护方法，应留在对应实现域文档或测试中，不进入 specs 正文。

## 验证

阶段 12 需要至少运行：

1. `python3 code/specs_validate.py all --format text --fail-on-diagnostics`；
2. `python3 -m pytest tests/code/test_ldvh_specs_validate.py tests/code/test_formal_specs.py -q`；
3. `python3 code/test_runner.py targeted --changed specs/04-Specs基础规范.md --changed specs/07-Code确定性执行规范.md --changed specs/08-Web信息同步规范.md --changed specs/09-测试与验证规范.md --changed code/ldvh_specs.py --changed tests/code/test_ldvh_specs_validate.py`。

若验证通过，应同步 `reviews/formal/04-formal-review.yaml`、`reviews/formal/07-formal-review.yaml`、`reviews/formal/08-formal-review.yaml` 和 `reviews/formal/09-formal-review.yaml` 的 hash。
