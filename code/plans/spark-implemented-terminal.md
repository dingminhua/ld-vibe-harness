# Spark `implemented` 终态纵切

## 目标与边界

为 Spark 增加专属终态 `implemented`：它只表示该 Spark 限定的信息需求已被规则或实现边界直接落实、且没有剩余事实责任对象；它不表示项目、规则、代码、Git 提交或下游工作已经完成。它不建立跨类型泛化“完成”状态，也不把 Spec、代码路径、Git 提交或 Web 页面伪装成事实关系目标。

本纵切直接服务 `00` 的 V1、V3、V5、V6、V8，并服从 `00` §8.1 的 F0–F4 渐进式披露、§10 Human Gate 与 §11 Stop Conditions。`implemented` 的依据在 AI 准备处置或追溯时按需通过 F4 展开；不新增 Spark 事实字段、Spec 关联字段、关系类型或 Hook 自动判定。Spark 仅保留现有 `disposition_summary` 作为终态处置记录，最后一次有效记录时间使用 `updated_at`。

初始范围包含 `spark-0026` 的历史终态更正。Human 已授权在规则、机械边界和验证条件均满足后直接实施该更正；该授权不放宽其它对象的创建、更新或状态推进条件。

## 规则设计

`20-Spark-火花` 将状态闭集从 `open/routed/discarded` 扩展为 `open/routed/implemented/discarded`：

- 正常转换增加 `open → implemented`；`implemented` 是不可直接重开的终态。
- `implemented` 禁止 `priority` 与 `routed-to`；要求既有终态字段，且处置说明如实说明落实范围与无剩余责任。
- `routed` 继续只用于同项目当前事实对象承接，Spec 绝不成为关系目标。
- `discarded` 继续只用于否定处置，不能承载“已落实”的含义。
- 新 `open` Spark 可以通过既有 `supersedes` 指向任一旧终态（包括 `implemented`）。
- F4 是 AI 核对处置依据的读取层；Helper、Code、Hook 与 Web 不从文本、文件变更或测试结果自行判定 `implemented`。

`32-事实对象生命周期变更与承接处置行动模板` 只增加所需的生命周期分支：F3 当前对象、按需 F4、AI 判断、Human 当前授权、完整 after、CAS、回读、机械与语义验证范围分离。模板不得复制 Spark 状态机或产生授权。

## 历史无效对象更正

现有 `spark-0026` 是不含 `routed-to` 的 `routed`，不能作为普通 `routed → implemented` 转换处理。普通状态边仍不得增加这一边。

受控写入只在“当前载体可解析、稳定身份和预期内容指纹可确认，但当前机械校验不成立”的修复条件下允许形成一个完全机械有效的 after snapshot。该路径是同一对象的历史记录更正，不是 Code 的语义分类或批量迁移：

- 必须使用精确稳定引用和 CAS 指纹；
- after 必须完整通过 Schema、关系和状态检查并写后回读；
- Code 不根据错误文本推断处置结论；AI 与 Human 对该结论负责；
- 不增加正常 `routed → implemented` 转换，不自动扫描或修复其它对象；
- 若 before 无法解析稳定身份、after 不成立、指纹变化或规则/Human Gate 不满足，则零写入。

为支持这一受限修复，需要调整 `05` 的单对象更新前置与共享写事务实现，使其区分“正常更新要求 before mechanically valid”与“来源明确允许的历史无效记录更正”。

## 实现面

| 面 | 改动 |
|---|---|
| 规范与登记 | 更新 20 的状态/转换/验证/Human Gate；更新 32 的执行分支；仅在必要处更新 05 的无效前态受控修复契约 |
| `code/ldvh/facts/contracts.py` | Spark status 闭集加入 `implemented` |
| `transitions.py` / `update_application.py` | 正常 `open → implemented`；仅在来源允许的 invalid-before repair 路径绕开普通状态边，并保留全量 after 校验与 CAS |
| `relations.py` | `implemented` 可被新 open Spark `supersedes`；不得出现 `routed-to` |
| Helper | F2 默认候选仍只含 `open`；精确 F3、更新和失败范围保持可观察 |
| Web | DTO、筛选、文案、颜色、终态详情与历史兼容均识别 `implemented`，但不渲染分流目标 |
| `spark-0026` | 仅在以上规则/实现和验证通过后，以完整目标快照更正为 `implemented` |

## 验证与风险

| 风险 | 验证 |
|---|---|
| 把“已落实”误作“工作完成” | 20、32、Web 文案正反例；终态卡不显示完成或分流目标 |
| Spec 被误作事实关系 | relation validator 正反例；`implemented` 携带 `routed-to` 必须无效 |
| Code 擅自判断落实 | 只校验闭集、转换、CAS 与 after；测试证明文本和测试结果不派生状态 |
| 无效旧对象绕过受控写入 | invalid-before repair 的可解析身份、精确指纹、after 有效、写后回读、零写入反例 |
| 误放宽正常终态转换 | `routed → implemented` 在有效 before 上仍被拒绝；仅 source-authorized repair 可更正无效 before |
| 终态未能被历史替代 | `supersedes → implemented` 与环、跨项目、非 open source 的正反例 |
| Web/Helper 漏消费新状态 | DTO、筛选、列表、详情、F2 默认候选和历史精确读取 tests |

验证先执行规则/解析与 facts/Helper/Web 聚焦测试，再运行 Ruff、完整 Code tests、Web checks/tests/build 与 full-v4。当前工作区的 Study 迁移改动与本纵切相邻但不属于本计划；其失败必须与本纵切结果区分并如实报告。
