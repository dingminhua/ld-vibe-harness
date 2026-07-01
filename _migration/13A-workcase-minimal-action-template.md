# 13A WorkCase 最小行动模板

文件状态：阶段 13 记录。本文只记录 V3 主线后续补强过程，不授权自动环境入口、Web 写入或完整 Confirm UI 已经接入。

## 背景

阶段 9E 把 WorkCase 创建、执行推进、结果复核和关闭确认作为后置行动模板候选。阶段 12 后，specs 与实现域边界已明确，允许把 WorkCase 的最小手动行动结构吸收到 `06`，同时继续把自动触发、Web 写入、完整 Confirm UI 和字段表细化放在后续阶段。

## 正式承接

本阶段做以下承接：

1. `specs/06-行动模板基础规范.md` 新增 `workcase_minimal_action_template` Code 消费入口；
2. `06` 在“模板候选与迁移边界”中新增 WorkCase 最小行动模板，覆盖 Context、Scenario、Gate、执行、验证、回写和交还；
3. `specs/21-WorkCase-工作项.md` 明确 WorkCase 最小手动行动模板由 `06` 承接，本文仍只定义事实对象状态、证据、关闭口径和 Human Gate；
4. `code/ldvh_specs.py` 增加 `parse_workcase_action_template` 和 `validate_workcase_action_template`；
5. `tests/code/test_ldvh_specs_validate.py` 增加 WorkCase 模板正例和缺 Human Gate、缺交还、缺手动边界负例。

## 边界

WorkCase 最小行动模板只支持 `manual_equivalent_execution`。它不启用 Web 写入，不安装 Hook，不声明 runtime 自动触发，不创建完整 Confirm UI，不批量迁移状态，不补完整字段表，也不得替代 Human Gate。

后续若要启用 Web 写入、自动触发、外部环境接入或通用 Confirm UI，必须进入后续阶段、Human Gate、测试和环境适配边界判断。

## 验证

阶段 13 需要至少运行：

1. `python3 code/specs_validate.py all --format text --fail-on-diagnostics`；
2. `python3 -m pytest tests/code/test_ldvh_specs_validate.py -q`；
3. `python3 code/test_runner.py targeted --changed specs/06-行动模板基础规范.md --changed specs/21-WorkCase-工作项.md --changed code/ldvh_specs.py --changed tests/code/test_ldvh_specs_validate.py`。

若验证通过，应同步 `reviews/formal/06-formal-review.yaml` 和 `reviews/formal/21-formal-review.yaml` 的 hash。
