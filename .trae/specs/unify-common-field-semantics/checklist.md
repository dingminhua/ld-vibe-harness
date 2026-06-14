# Checklist

- [x] 05.01 包含全局公共字段语义定义表（id, type, title, status, created, updated, description）
- [x] 05.01 包含部分公共字段语义定义表（source, status_history, acceptance, verification, closure_evidence, completion_evidence, closed_at, archive_reason, blocked_by, notes, related_*, source_*, superseded_by）
- [x] 05.01 明确 source_* 与 related_* 的引用语义边界
- [x] 05.01 定位说明已从"只定义字段内容格式"扩展为"定义公共字段语义和字段内容格式"
- [x] 各对象规范（21/23/24/25/26/27/28）公共字段引用 05.01，只保留对象特有字段完整定义
- [x] Task 实例 verification 字段不再包含"风险、约束和降级说明"，该内容已迁移到 description
- [x] 其他对象实例字段内容符合新的语义边界定义
- [x] fact_validate.py 对 verification 字段中包含风险说明的情况给出 warning
- [x] fact_cli.py 创建模板字段内容符合语义边界
- [x] specs、facts、code 和 Web 校验运行通过，或剩余问题已记录为明确后续任务
