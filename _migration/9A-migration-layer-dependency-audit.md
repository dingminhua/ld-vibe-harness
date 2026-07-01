# 9A 迁移层依赖审计

> 文件状态：temporary migration audit。本文记录阶段 9A 对 `_migration` 依赖的审计结论；它不授权删除迁移材料、移动 review gate、启用 Hook、迁移真实实例或声明 V3 正式接管。正式规则仍以 `specs/` 正文为准。

## 1. 审计结论

阶段 9A 结论：

1. 稳定 `code/` 没有 import `_migration` 模块；
2. 稳定 `code/` 仍有少量 `_migration` 路径引用，用于迁移材料 target 分类、迁移 target 的 read_plan 和阶段 8 e2e source_refs；
3. 稳定 `tests/code/test_formal_specs.py` 仍依赖 `_migration/reviews/*-formal-review.yaml` 作为正式 specs 和附件的 review hash gate；
4. `_migration/tests` 仍依赖 `_migration/code`、fixtures、schemas、inventory 和 V2 源仓库，用于迁移原型和迁移 gate 回归；
5. 当前没有 tracked `_migration` 文件可以直接删除；只允许清理未跟踪的 `__pycache__` 等生成物；
6. 9A 之后可以进入 9B，但 9F 前不得删除 `_migration/reviews`、`_migration/tests`、`_migration/code` 或被 review receipt 引用的迁移证据。

## 2. 活跃依赖

| 依赖方 | 被依赖对象 | 依赖类型 | 当前处理 |
|---|---|---|---|
| `tests/code/test_formal_specs.py` | `_migration/reviews/*-formal-review.yaml` | 正式 review hash gate | 保留。后续若迁移，应先建立正式 review ledger 或等价验证 |
| `_migration/reviews/*-formal-review.yaml` | `_migration/5B-*`、`_migration/6A-*`、`_migration/6B-*`、`_migration/7-*`、inventory 等 evidence | 映射证据和 review receipt | 保留。不得在 review gate 替代方案前删除 |
| `_migration/tests/test_md_spec_extractor.py` | `_migration/code/md_spec_extractor.py`、V2 specs | 迁移原型回归 | 保留到 9F；若 Action Guide 解析已完全由正式 Code 承接，可转为历史归档或删除 |
| `_migration/tests/test_spec_bloat_scan.py` | `_migration/code/spec_bloat_scan.py`、V2 specs | 迁移审计回归 | 保留到事实对象和行动模板后置项清楚后 |
| `_migration/tests/test_migration_gate.py` | `_migration/code/migration_gate`、fixtures、CLI | 候选材料分类回归 | 保留到 9F；若阶段 9 不再接受未分类候选，可归档或删除 |
| `code/ldvh_specs.py` | `_migration/v3-migration-execution-plan.md` | 迁移 target read_plan / e2e source_ref | 短期保留。9F 前应改为正式用户文档或移除运行时 source_ref |
| `code/ldvh_specs.py` | `_migration/` 路径前缀 | target 分类边界 | 保留。它用于防止迁移材料被误写成正式事实源或规则源 |
| `specs/03`、`specs/05`、`specs/06`、`specs/07` | `_migration` 文字边界 | 正式规则中的边界说明 | 保留。不是文件系统依赖 |

## 3. 分类结果

| 类别 | 文件或目录 | 结论 |
|---|---|---|
| 必须保留到 9F | `_migration/reviews/` | 正式 review hash gate 仍依赖 |
| 必须保留到 9F | `_migration/tests/`、`_migration/code/`、`_migration/fixtures/`、`_migration/schemas/` | 迁移回归仍依赖 |
| 必须保留到 9F | `_migration/5B-*`、`_migration/6A-*`、`_migration/6B-*`、`_migration/7-*`、`_migration/8-*`、`_migration/9-*` | review evidence、阶段完成记录和后续范围依据 |
| 必须保留到 9F | `_migration/inventory/` | review receipts 和历史映射仍引用 |
| 可立即清理 | 未跟踪 `__pycache__`、临时测试缓存 | 已清理；不得提交 |
| 不建议当前删除 | tracked `_migration` 文件 | 当前没有安全删除对象 |

## 4. 后续吸收路径

| 迁移层能力 | 长期去向 | 前置条件 |
|---|---|---|
| formal review receipts | 正式 review ledger、稳定 tests 或 Code 派生校验 | 明确新路径、迁移 hash gate、同步 tests |
| Markdown extractor 原型 | 正式 Code parser tests 或删除 | Action Guide / specs parser 已覆盖等价能力 |
| spec bloat scan | 正式 docs/tests 或删除 | 事实对象完整迁移、行动模板后置边界稳定 |
| migration gate classifier | 归档或转正式候选准入工具 | 阶段 9 是否继续接收候选迁移材料 |
| V2 inventory | 归档或删除 | 所有 V2 内容已迁入、废弃或后置登记完成 |
| `_migration/v3-migration-execution-plan.md` 运行时引用 | 正式用户文档或移除 | 9F 用户文档和 V3 主线切换声明完成 |

## 5. 风险

1. 如果提前删除 `_migration/reviews`，formal specs review hash gate 会失败；
2. 如果提前删除 `_migration/tests` 或 `_migration/code`，迁移回归测试会失败；
3. 如果提前删除 inventory 或阶段记录，已有 review receipt 的 mapping evidence 可能失效；
4. 如果让正式 runtime 长期引用 `_migration/v3-migration-execution-plan.md`，V3 主线切换后仍会残留迁移层依赖；
5. 如果把 `_migration` 当事实源或规则源继续使用，会违反 03/05/07 的边界。

## 6. 9A 完成声明

9A 已完成依赖审计，但不删除 tracked 迁移材料。下一步进入 9B 最小提交入口，完成 Git 提交行动和 commit gate / Hook 的 V3 接入设计与验证。
