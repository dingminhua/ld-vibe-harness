本夹具覆盖 Web 对工作对象字段契约、TaskPlan / Task / SubTask 层级聚合、路径字段语义和信号字段展示边界的最小测试数据。

设计原则：

- TaskPlan 和 Memo 维护 `priority`。
- `importance` 已由 `priority` 统一承载，不再作为独立字段维护。
- Task / SubTask 不维护 `priority`、`importance`、`category` 或 `tags`。
- Task 的 `deliverables`、`related_docs`、`affected_docs` 分别表示结果物、参考输入文档和完成后需同步检查的文档。
- SubTask 只承载局部执行字段，不承载文档、ADR、Memo、产出物或关联变更。
