# 11G 迁移层依赖独立记录

阶段：11G

目的：降低 V3 主线对 `_migration` 的稳定运行依赖，尤其是 formal review hash gate。

## 已处理

1. 新增 `reviews/formal/` 作为正式 review hash gate ledger；
2. `tests/code/test_formal_specs.py` 改为读取 `reviews/formal/*-formal-review.yaml`；
3. `_migration/reviews/` 不再是稳定 formal gate 的读取位置；
4. `_migration/` 继续保留历史迁移证据、迁移测试和 mapping evidence；
5. README 已把 `_migration/` 从“formal review hash gate”改为历史迁移证据和迁移测试材料。

## 仍保留的迁移依赖

1. `reviews/formal/*` 的 `mapping_evidence.path` 仍可回指 `_migration/` 历史材料；
2. `code/test_runner.py full` 仍运行 `_migration/tests`；
3. 迁移期 source_ref 仍可引用 `_migration/` 作为历史证据。

## 结论

V3 主线不再依赖 `_migration/reviews` 执行 formal hash gate，但 `_migration` 尚不删除。删除条件仍是：迁移测试、mapping evidence、历史 source_ref 和后续审计材料都有稳定替代或经 Human Gate 同意归档。
