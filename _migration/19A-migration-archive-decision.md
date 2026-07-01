# 19A `_migration` 归档判断

文件状态：阶段 19 记录。本文只记录 `_migration` 是否可以归档、删除或继续保留的判断，不授权删除历史迁移证据、迁移测试、mapping evidence 或 formal review 回指材料。

## 读取依据

1. `specs/00-理念与构成.md`
2. `specs/01-保障与衔接.md`
3. `specs/02-AI行为规范.md`
4. `specs/03-事实源与Git溯源规范.md`
5. `specs/04-Specs基础规范.md`
6. `specs/09-测试与验证规范.md`
7. `reviews/formal/README.md`
8. `tests/code/test_formal_specs.py`
9. `code/test_runner.py`

## 审计结果

阶段 19A 审计时，`_migration` 仍有以下稳定依赖：

1. `reviews/formal` 中 24 份 formal review 的 `mapping_evidence.path` 仍回指 `_migration/`；
2. `tests/code/test_formal_specs.py` 要求 formal review 的 mapping evidence 路径存在，且必须以 `_migration/` 开头；
3. `code/test_runner.py` 的 full profile 仍运行 `tests/code` 和 `_migration/tests`；
4. `code/test_runner.py` 的 targeted profile 仍会在 `_migration/code`、`_migration/tests`、`_migration/fixtures` 或 `_migration/schemas` 变化时运行 migration pytest；
5. `code/ldvh_specs.py` 的 read plan 和 preflight 逻辑仍识别 `_migration/` target，并回指 `_migration/v3-migration-execution-plan.md` 等历史计划；
6. `_migration/tests` 仍有 3 个测试文件，当前运行结果为 19 passed；
7. `_migration` 仍保存 V2 到 V3 的吸收索引、附件分流、阶段记录、旧 review ledger、fixtures、schemas 和迁移工具。

## 判断

`_migration` 当前不能整体归档、删除或移出仓库。

原因：

1. 它仍是 formal review mapping evidence 的物理回指位置；
2. 它仍承载迁移测试和迁移工具的回归输入；
3. 它仍被 Code preflight/read plan 作为迁移类 target 的上下文入口；
4. 删除或移动会破坏 formal hash gate、测试 runner 和历史 source_ref；
5. 归档属于历史证据位置变化，必须 Human Gate，不应由 AI 单方面执行。

## 可清理项

阶段 19A 只允许清理无迁移价值的本地噪声，例如 ignored 的 `.DS_Store`。这类文件不进入 Git 提交，也不改变迁移证据。

不应清理：

1. `_migration/*.md` 阶段记录；
2. `_migration/inventory/`；
3. `_migration/reviews/`；
4. `_migration/tests/`；
5. `_migration/fixtures/`；
6. `_migration/schemas/`；
7. `_migration/code/` 和迁移 CLI；
8. 被 `reviews/formal/*.yaml` 引用的任何路径。

## 后续归档条件

未来若要归档 `_migration`，至少要先满足：

1. `reviews/formal` 不再要求 mapping evidence 物理位于 `_migration/`，或所有 mapping evidence 已迁入新的稳定 evidence 目录并更新 hash gate；
2. `_migration/tests` 的覆盖被稳定测试替代，且 `code/test_runner.py` 不再依赖 `_migration/tests`；
3. `code/ldvh_specs.py` 的 migration target read plan 有正式替代入口；
4. 所有 formal review、README、迁移计划、source_refs 和历史索引的路径回指已重写并验证；
5. Human Gate 明确确认归档、删除或移动策略；
6. 完成 `python3 code/test_runner.py full` 或等价收口验证。

## 结果

阶段 19A 完成口径：

1. `_migration` 继续保留；
2. `_migration` 仍不是正式规则源、事实源或日常维护入口；
3. `_migration` 是历史迁移证据、mapping evidence、迁移测试和迁移工具承载区；
4. 当前 V3 主线不因 `_migration` 保留而退回 V2；
5. 本阶段不删除 tracked 迁移材料，不移动目录，不重写 formal review evidence。
