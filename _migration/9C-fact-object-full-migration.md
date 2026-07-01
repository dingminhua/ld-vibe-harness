# 9C 事实对象完整迁移

> 文件状态：temporary migration record。本文记录阶段 9C 对 V2 真实事实对象实例和字段 schema 的迁移结果；它不授权 Web 写入、Hook 启用、行动模板实例创建或 V3 正式接管声明。正式规则仍以 `specs/` 正文为准，真实事实以 `ldvh-base/` 为准。

## 1. 迁移目标

9C 采用用户校正口径：

1. Spark、WorkCase、ADR、Pitfall、Study 的真实事实对象需要全部进入 V3；
2. 编号可以按 V3 重构，不照搬 V2 旧编号权威；
3. Web 表现层不重做，9C 只处理事实源、schema、Code/tests；
4. 除 Git 提交行动外，其他行动模板实例继续后置；
5. 知识地图旧形态不恢复，相关历史对象只作为事实实例内容或 legacy 来源保留。

## 2. 来源与结果

| 对象 | V2 来源数量 | V3 原有数量 | 9C 后 V3 数量 | 处理 |
|---|---:|---:|---:|---|
| Spark | 39 | 1 | 40 | V2 `spark-0001` 至 `spark-0039` 重编号为 V3 `spark-0002` 至 `spark-0040` |
| WorkCase | 21 | 1 | 22 | V2 `workcase-0001` 至 `workcase-0021` 重编号为 V3 `workcase-0002` 至 `workcase-0022` |
| ADR | 0 | 0 | 0 | 建立 `ldvh-base/adrs/` 空目录，保留字段 schema；无实例可迁入 |
| Pitfall | 1 | 0 | 1 | V2 `pitfall-0001` 保持为 V3 `pitfall-0001` |
| Study | 14 | 0 | 14 | V2 Study 编号保持为 V3 `study-0001` 至 `study-0014` |

最终 V3 事实实例总数为 77 个，不包含 `.gitkeep` 或空目录。

## 3. 编号与引用重写

编号重构规则：

1. 保留 V3 已存在的 `spark-0001` 和 `workcase-0001`；
2. V2 Spark 与 WorkCase 采用追加编号，避免覆盖 V3 已有事实；
3. Pitfall 和 Study 没有 V3 既有冲突，保留原编号；
4. ADR 当前无 V2 实例，只建立目录和 schema；
5. 所有事实对象引用同步重写，覆盖 `input_refs`、`related_*`、`source_sparks`、`source_objects` 和 `followup_refs`。

迁移后已检查旧 V2 引用和临时占位符未残留在 `ldvh-base/`。

## 4. 字段 schema 与 validator

9C 在正式 Code 中新增事实实例消费能力：

| 能力 | 位置 | 说明 |
|---|---|---|
| 实例布局 | `code/ldvh_specs.py` `FACT_INSTANCE_LAYOUT` | 定义 20-24 对应目录、后缀和 spec_id |
| 字段 schema | `code/ldvh_specs.py` `FACT_INSTANCE_FIELD_SCHEMAS` | 定义每类实例的允许字段、必填字段和 legacy 禁用字段 |
| 实例解析 | `parse_fact_instances` | 读取 YAML 实例和 Study Markdown frontmatter |
| 实例校验 | `validate_fact_instances` | 校验目录、解析、id/文件名一致性、重复 id、type、status、必填字段、未知字段、legacy 字段、Study 正文骨架和对象关系 |
| CLI 输出 | `code/specs_validate.py all` | text summary 输出 `fact_instances` 数量 |
| 负例测试 | `tests/code/test_ldvh_specs_validate.py` | 覆盖 id 不一致、未知字段、缺必填字段、legacy 字段、缺引用和 Study 正文缺标题 |

字段 schema 由 Code/tests 承接，不把 20-24 完整字段长表写入正式 specs 正文。正式 specs 只保留对象规则、状态边界、Human Gate 和事实源边界，避免正文变成第二套实现字段清单。

## 5. 迁移修正

V2 `spark-0018-web-color-governance-spec10.yaml` 含有临时字段 `规范10`。该字段不适合作为 V3 Spark schema 字段名，也不应让 Spark 事实实例直接授权 Web 颜色规则。

9C 的处理方式：

1. V3 文件重编号为 `ldvh-base/sparks/spark-0019-web-color-governance-spec10.yaml`；
2. `规范10` 字段移除；
3. 原内容归并进 `key_findings`，并明确为候选治理要点，不作为正式规则授权；
4. `FACT_INSTANCE_FIELD_SCHEMAS["spark"]["forbidden"]` 禁用 `规范10` 字段，防止后续复发。

该处理保留事实内容，同时避免把 V2 临时字段升级为 V3 schema。

## 6. 正式 specs 同步

9C 同步更新：

1. `specs/05-事实模型基础规范.md`：移除“真实实例仍后置”的旧口径，明确真实 `ldvh-base/` 实例和 Code 字段 schema 已迁入；
2. `specs/20-Spark-火花.md`：明确真实 Spark 实例已在 `ldvh-base/sparks/`；
3. `specs/21-WorkCase-工作项.md`：明确真实 WorkCase 实例已在 `ldvh-base/workcases/`；
4. `specs/22-ADR-决策.md`：明确 `ldvh-base/adrs/` 已建立，但 V2 当前无 ADR 实例；
5. `specs/23-Pitfall-踩坑经验.md`：明确真实 Pitfall 实例已在 `ldvh-base/pitfalls/`；
6. `specs/24-Study-研究报告.md`：明确真实 Study 实例已在 `ldvh-base/studies/`。

这些更新不改变 Hook、Web 写入、行动模板实例或 V3 正式接管边界。

## 7. Human Gate 判断

9C 未触发必须暂停的 Human Gate：

1. 没有丢弃事实实例；V2 75 个实例全部迁入，叠加 V3 原有 2 个实例；
2. 编号重构按阶段 9 已确认口径执行；
3. 引用同步重写并由 validator 校验；
4. `规范10` 只做字段归并，事实内容保留，且避免把 Spark 写成规则源；
5. 未启用 Hook、未修改 Web 写入、未声明 V3 正式接管。

## 8. 验证声明

| 验证目标 | 验证方式 | 验证入口 | 关键输出 | 结论 | 残留风险 |
|---|---|---|---|---|---|
| 事实实例可消费 | 命令校验 | `python3 code/specs_validate.py all --format text --fail-on-diagnostics` | `fact_instances: 77`，diagnostics 0 | 通过 | 无 |
| 字段 schema 负例 | 自动化测试 | `python3 -m pytest tests/code _migration/tests -q` | 覆盖未知字段、缺必填字段和 legacy 字段 | 通过 | 单次全量测试耗时约 4 分 30 秒 |
| 端到端闭环 | 命令校验 | `python3 code/specs_validate.py e2e --target-path tests/code/test_ldvh_specs_validate.py --format text --fail-on-diagnostics` | stages 7，diagnostics 0 | 通过 | environment_integrated 仍为 false |
| commit gate | 命令校验 | `python3 code/specs_validate.py commit-gate ... --fail-on-diagnostics` | status ok，diagnostics 0 | 通过 | 真实 Git Hook 未启用 |
| 全量回归 | 自动化测试 | `python3 -m pytest tests/code _migration/tests -q` | 122 passed | 通过 | `_migration` 仍在 9F 前保留 |

## 9. 后续

9C 完成后，阶段 9 下一步进入 9D Web 数据契约迁移：

1. 保留既有 Web 表现层；
2. 检查 Web DTO/API 是否独立读取 V3 specs、事实对象和 Git 文件事实源；
3. 对齐来源回指、缓存同步、Confirm UI 边界和轻写入白名单；
4. 补 Web 数据契约回归测试；
5. 不让 Web 依赖 Code 输出作为主数据源。
