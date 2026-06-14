# Checklist

- [x] `05-工作模型基础规范.md` 明确定义 `priority`（优先级）和 `importance`（重要程度）的语义、枚举、判断标准和对象适用边界
- [x] `27-TaskPlan-任务计划.md` 包含 `priority`（优先级: P0/P1/P2/P3）和 `importance`（重要程度: high/medium/low）字段
- [x] `25-Memo-备忘.md` 使用 `importance`（重要程度）而不是 `priority`（优先级）
- [x] `26-Task-任务.md` 不包含 `risk_assessment`（风险判断）字段
- [x] `23-Pitfall-踩坑.md` 不包含 `severity`（严重程度）字段
- [x] `fact_validate.py` 和 `fact_cli.py` 的字段契约与更新后的规范一致
- [x] 现有 Memo、TaskPlan、Task、Pitfall YAML 实例已完成字段迁移或补齐
- [x] Web 展示、筛选或创建入口不再使用废弃字段口径
- [x] 相关 specs、facts、code 和 Web 校验命令运行通过，或剩余问题已记录为明确后续任务
