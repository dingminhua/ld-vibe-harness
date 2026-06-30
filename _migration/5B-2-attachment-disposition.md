# 5B-2 V2 附件分流清单

> 文件状态：temporary migration disposition。本文只记录 V2 附件进入 V3 的分流判断，不授权正式规则、附件、Code 行为、Hook、Web 行为或 Human Gate。

## 分流清单

| V2 附件 | 分流决策 | V3 归口 | 正文授权 | Code 消费方 | 未迁入去向 | 理由 |
|---|---|---|---|---|---|---|
| `02.Att.01-字段注册表` | 迁附件 | `05` | `specs/05-事实模型基础规范.md` -> `specs/attachments/05.Att.01-字段注册表结构.md` | `field_registry_contract` | 公共字段长表后置成员规范 | 只迁注册列结构、闭集和消费元数据，不迁成员完整字段表 |
| `02.Att.02-成员身份字段表` | 后置 | `05` | 无 | 后续成员规范 validator | 后置到 Spark/WorkCase/ADR/Pitfall/Study 成员规范 | 成员身份专属字段会定义成员规范边界，父层当前只保留迁移判断条件 |
| `02.Att.03-成员主文件骨架模板` | 后置 | `05` | 无 | 后续成员规范 tests | 后置到成员规范 | 模板和骨架属于成员规范，不进入 05 父层附件 |
| `02.Att.04-成员一致性辅助核对表` | 转Code/tests | `05` | 无 | 后续成员一致性诊断 | tests/code 或后续 fact validator | 核对项适合机械诊断，不作为正式附件规则 |
| `02.Att.05-成员双读映射矩阵` | 转Code/tests | `05` | 无 | 后续双读兼容诊断 | tests/code 或后续 migration validator | 映射矩阵是派生/兼容检查，不维护为附件 |
| `02.Att.06-字段矩阵诊断表` | 转Code/tests | `05` | 无 | 后续字段矩阵诊断 | tests/code 或后续 fact validator | 诊断矩阵应由 Code 从字段注册和成员规范派生 |
| `02.Att.07-清退登记表` | 留_migration | `05` | 无 | 无 | `_migration` 清退证据 | 清退对象记录是迁移过程材料，正式边界已由 05 Stop Conditions 承接 |
| `04.Att.01-Code需求记录字段表` | 后置 | `07` | 无 | 后续 Code 需求对象或诊断 | 后置到 Code 需求治理 | 当前 07 父层不承载 Code 需求记录表 |
| `04.Att.02-Code命令入口表` | 转Code/tests | `07` | 无 | CLI tests | `tests/code` | 命令入口由当前 CLI 和测试验证，不维护第二入口表 |
| `04.Att.03-Code结构化输出Schema表` | 转Code/tests | `07` | 无 | output schema tests | `tests/code` | 输出 schema 应由 Code 实现和测试闭环承接 |
| `04.Att.04-Code诊断码表` | 转Code/tests | `07` | 无 | diagnostic tests | `tests/code` | 诊断码闭集由 validator 代码和测试承接 |
| `04.Att.05-知识地图输入范围表` | 废弃 | `07` | 无 | 无 | legacy_alias：Action Guide | 知识地图已被 Action Guide / 行动指南取代 |
| `04.Att.06-知识地图投影Schema表` | 废弃 | `07` | 无 | 无 | legacy_alias：Action Guide | 知识地图投影不作为 V3 正式概念或附件 |
| `04.Att.07-受控写入前检查矩阵` | 转Code/tests | `07` | 无 | preflight tests | `tests/code` | preflight 矩阵属于 Code 诊断行为 |
| `04.Att.08-v1-v2-Code消费双读映射矩阵` | 留_migration | `07` | 无 | migration tests | `_migration` | 双读映射是迁移兼容材料 |
| `04.Att.09-Code回归入口表` | 转Code/tests | `07/09` | 无 | regression tests | `tests/code` | 回归入口由测试文件和命令验证 |
| `04.Att.10-Code参考实现文档边界清单` | 后置 | `07` | 无 | 后续 docs validator | 后置到 Code docs 边界 | 参考实现文档边界不在当前 5B-2 迁入范围 |
| `05.Att.01-DTO与API契约表` | 后置 | `08` | 无 | 后续 Web contract tests | 5B-5 | Web API 未进入当前阶段 |
| `05.Att.02-页面与API映射矩阵` | 后置 | `08` | 无 | 后续 Web contract tests | 5B-5 | Web 页面/API 映射后置到 Web 阶段 |
| `05.Att.03-轻写入白名单表` | 后置 | `08` | 无 | 后续 Web write tests | 5B-5 | 受控轻写入需要 Web/API/事实源闭环 |
| `05.Att.04-Confirm-UI字段表` | 后置 | `08` | 无 | 后续 Confirm UI tests | 5B-5 | Confirm UI 不替代 Human Gate，需 Web 阶段处理 |
| `05.Att.05-Gate与Validate阶段边界矩阵` | 后置 | `08/09` | 无 | 后续 Web/test boundary tests | 5B-5 | Web 阶段边界后置 |
| `05.Att.06-Human-facing态势语义表` | 后置 | `08` | 无 | 后续 Web display tests | 5B-5 | Human-facing 展示语义后置到 Web |
| `05.Att.07-提交记录展示矩阵` | 后置 | `08/03` | 无 | 后续 Web/Git display tests | 5B-5 | 展示矩阵不替代 Git 溯源规则 |
| `05.Att.08-缓存与同步状态矩阵` | 后置 | `08` | 无 | 后续 Web cache tests | 5B-5 | 缓存边界后置到 Web |
| `05.Att.09-Web回归矩阵` | 后置 | `08/09` | 无 | 后续 Web regression tests | 5B-5 | Web 回归入口后置 |
| `05.Att.10-Web差距审计模板` | 留_migration | `08` | 无 | 无 | `_migration` 审计材料 | 差距审计模板是一次性迁移/审计材料 |
| `05.Att.11-Web能力删除核对表` | 后置 | `08` | 无 | 后续 Web removal tests | 5B-5 | 删除核对后置到 Web 能力治理 |
| `07.Att.01-事实归属矩阵` | 转正文 | `03` | `specs/03-事实源与Git溯源规范.md` | `fact_source_boundaries` | 无 | 父层事实源边界已转写到 03 正文 |
| `07.Att.02-Commit-Type枚举表` | 迁附件 | `03` | `specs/03-事实源与Git溯源规范.md` -> `specs/attachments/03.Att.01-Commit-Message契约字段表.md` | `commit_message_contract_fields` | 无 | commit type 是机器可消费枚举 |
| `07.Att.03-Commit-Scope允许枚举表` | 迁附件 | `03` | `specs/03-事实源与Git溯源规范.md` -> `specs/attachments/03.Att.01-Commit-Message契约字段表.md` | `commit_message_contract_fields` | 无 | commit scope 是机器可消费枚举 |
| `07.Att.04-Commit-Body必填条件表` | 迁附件 | `03` | `specs/03-事实源与Git溯源规范.md` -> `specs/attachments/03.Att.01-Commit-Message契约字段表.md` | `commit_message_contract_fields` | 无 | body 条件是 commit 契约机器表 |
| `07.Att.05-Commit-Message样例集` | 转Code/tests | `03/09` | 无 | commit message parser tests | `tests/code` | 样例不进入附件，作为正反例测试材料 |
| `07.Att.06-过程输出回写核对表` | 转正文 | `03` | `specs/03-事实源与Git溯源规范.md` | `process_evidence_boundaries` | 无 | 回写边界已进入 03 正文 |
| `07.Att.07-Git提交留痕范围表` | 转正文 | `03` | `specs/03-事实源与Git溯源规范.md` | `git_traceability_rules` | 无 | 留痕范围属 Git 溯源父层规则 |
| `07.Att.08-Commit-Message字段表` | 迁附件 | `03` | `specs/03-事实源与Git溯源规范.md` -> `specs/attachments/03.Att.01-Commit-Message契约字段表.md` | `commit_message_contract_fields` | 无 | commit message 字段是机器契约 |
| `07.Att.09-关联提交派生优先级表` | 转Code/tests | `03/08` | 无 | 后续 Git/Web 派生 tests | tests 或 5B-5 | 派生优先级不作为事实源或规则源 |
| `07.Att.10-事实源读取策略核对表` | 转Code/tests | `03` | 无 | source_refs/read strategy tests | `tests/code` | 读取策略适合 Code 诊断 |
| `07.Att.11-非事实源排除清单` | 转正文 | `03` | `specs/03-事实源与Git溯源规范.md` | `fact_source_boundaries` | 无 | 非事实源排除已进入 03 §5 |
| `07.Att.12-事实承载介质选择表` | 后置 | `03/05` | 无 | 后续事实对象 validator | 后置到事实对象成员 | 介质选择需具体对象规范承接 |
| `08.Att.01-测试归属矩阵` | 转Code/tests | `09` | 无 | test ownership tests | `tests/code` | 测试归属由现有测试目录和 validator 维护 |
| `08.Att.02-验证声明字段表` | 迁附件 | `09` | `specs/09-测试与验证规范.md` -> `specs/attachments/09.Att.01-验证声明字段表.md` | `verification_claim_fields` | 无 | 验证声明字段是可解析闭集 |
| `08.Att.03-测试证据边界清单` | 转正文 | `09` | `specs/09-测试与验证规范.md` | `test_evidence_boundaries` | 无 | 测试证据边界已进入 09 正文 |
| `08.Att.04-同步触发矩阵` | 转Code/tests | `09` | 无 | sync trigger tests | `tests/code` | 同步触发适合测试覆盖 |
| `08.Att.05-Code完整验证入口表` | 转Code/tests | `09/07` | 无 | verification entry tests | `tests/code` | 完整验证入口由命令和测试承接 |
| `08.Att.06-Web回归入口表` | 后置 | `09/08` | 无 | Web regression tests | 5B-5 | Web 回归后置到 Web 阶段 |
| `08.Att.07-失败阻断核对表` | 转正文 | `09` | `specs/09-测试与验证规范.md` | `failure_blocking_rules` | 无 | 失败阻断已进入 09 正文 |
| `08.Att.08-等价验证适用表` | 转正文 | `09` | `specs/09-测试与验证规范.md` | `equivalent_verification_rules` | 无 | 等价验证口径已进入 09 正文 |

## 本轮正式迁入

| V3 附件 | 吸收来源 | 父规范授权 | Code 消费入口 |
|---|---|---|---|
| `specs/attachments/03.Att.01-Commit-Message契约字段表.md` | `07.Att.02`、`07.Att.03`、`07.Att.04`、`07.Att.08` | `specs/03-事实源与Git溯源规范.md` | `commit_message_contract_fields` |
| `specs/attachments/05.Att.01-字段注册表结构.md` | `02.Att.01` | `specs/05-事实模型基础规范.md` | `field_registry_contract` |
| `specs/attachments/09.Att.01-验证声明字段表.md` | `08.Att.02` | `specs/09-测试与验证规范.md` | `verification_claim_fields` |
