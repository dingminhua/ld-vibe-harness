# V3 迁移执行计划

> 文件状态：temporary migration plan；本文只记录 V3 迁移执行节奏，不授权 specs、Code 行为、Action Guide 输出、Human Gate 决策、环境支持声明或事实源变更。正式规则仍以 `specs/` 正文为准。

## 1. 计划定位

本文用于回答：V2 的大量 specs、Code、Hook、外部工作流包装、事实对象和治理能力应按什么顺序进入 V3。

本文不定义新规则，不替代 `specs/00-理念与构成.md`、`specs/01-保障与衔接.md`、`specs/04-Specs基础规范.md` 或 `specs/02-AI行为规范.md`。若本文与正式 specs 冲突，以正式 specs 为准，并应更新本文或废弃对应计划项。

## 2. 总原则

大量 specs 迁移不是最后整批搬运，也不是当前一次性导入。每批迁移必须绑定一个可消费闭环：

```text
specs 迁入
  -> Code 可解析
  -> tests 覆盖
  -> Action Guide / preflight / runtime / 事实源 能消费
```

没有明确消费方的 V2 specs，应继续留在 `_migration` 作为候选证据，不进入正式 `specs/`。

迁移时只迁移 V2 能力和必要规则，不复制 V2 的目录权威、命名权威、Hook 安装方式、Skill 资产身份或派生知识地图事实层。V3 不保留 Skill 作为 LDVH 顶层机制；V2 Skill 中仍有价值的工作流能力，应进入行动模板、Action Guide、环境适配或测试。

阶段 5 之前必须先完成 V2 来源吸收清单。该清单用于判断每项 V2 specs、附件、Code、Hook registry、Skill 资产和测试在 V3 中是吸收、改名、废弃还是后置，不得跳过清单直接重写 Hook / Commit / 行动模板代码。

## 3. 阶段计划

| 阶段 | 目标 | 先迁入的 specs 能力 | Code / tests 交付 | 不做事项 |
|---|---|---|---|---|
| 0. 当前基线 | 固化 00/01/02/03 与迁移计划 | 不新增大量 specs，只稳定保障、衔接、AI 行为和 Specs 基础规则 | 现有 formal specs 测试通过 | 不迁移 Hook、行动模板、事实对象大块内容 |
| 1. Specs 解析与校验 | 让 V3 Code 能直接消费 Markdown specs | 仅补足解析所需字段、保障消费时机、AI 行为保障表 | `code/specs_validate.py`、spec parser、diagnostics、CLI、对应 tests | 不生成运行时拦截，不安装 Hook |
| 2. Action Guide / read_plan | 迁移 V2 知识地图的只读导航能力 | 迁移任务导航、读取计划、停止条件、影响摘要相关规则 | Action Guide/read_plan 输出、source refs、capability gap tests | 不把派生图谱变成事实源 |
| 3. Preflight 门禁 | 写入前识别规则读取、Human Gate 和缺口分流 | 迁移写入门禁、规范变更、附件边界、Human Gate 判断相关规则 | preflight CLI、blocking/warning/follow_up diagnostics tests | 不把 Code 输出当授权或放行 |
| 4. Runtime facade | 承接消费时机和 receipt / diagnostic | 迁移 Runtime Protocol、canonical event、trigger source、receipt 边界规则 | 本地 runtime CLI、receipt 结构、事件测试 | 不声称环境已经完整支持 LDVH |
| 5. Hook / Commit / 行动模板适配 | 接入外部环境触发和可复用工作流 | 先完成 V2 吸收清单，再迁移 Git commit、Hook、行动模板和环境入口相关规则 | 吸收清单、正式 specs 候选、adapter/dispatcher、commit gate、行动模板适配 tests | 不跳过吸收清单直接重写代码；不让 Hook、外部包装或行动模板成为独立规则源 |
| 6. 事实源与工作对象 | 承接真实行动状态和长期证据 | 迁移 workcase、spark、ADR、pitfall、study 等事实对象规则 | fact validator/CLI、对象状态测试、回写边界测试 | 不直接复制 v2 `ldvh-base` 结构为权威 |
| 7. 受管项目接入 | 让 V3 判断当前工作归属和项目事实源 | 迁移项目治理、项目发现、跨项目边界规则 | governed projects 配置、项目解析、越界测试 | 不让项目索引替代用户事实源 |
| 8. 端到端闭环 | 用真实流程验证机制是否减少 AI 负担 | 只补缺口 specs | session start -> read plan -> preflight -> 修改 -> tests -> commit -> receipt -> closure 流程测试 | 不继续堆无消费方机制 |
| 9. 产品化与迁移层清理 | 收束 alpha/beta 边界 | 把仍有效迁移决定吸收到正式 specs/tests/docs | 清理 `_migration` 条件、用户文档、可选 Web/dashboard | 不保留 `_migration` 作为长期事实源 |

## 4. Specs 迁移节奏

大量 specs 迁移贯穿阶段 2 到阶段 7：

| 迁移批次 | 进入时机 | 进入条件 |
|---|---|---|
| Action Guide / 知识地图相关 specs | 阶段 2 前 | 已有 parser 能读身份、章节和保障表；有 Action Guide 输出测试 |
| preflight / Human Gate / 写入门禁相关 specs | 阶段 3 前 | 能判断目标路径、规则影响、阻断类型和缺口分流 |
| Runtime Protocol / event / receipt / diagnostic 相关 specs | 阶段 4 前 | 消费时机闭集和 diagnostic 分类已经可由 Code 校验 |
| Git commit / Hook / 行动模板适配相关 specs | 阶段 5 前 | runtime facade 和 preflight 已稳定；`_migration/stage-5-v2-absorption-checklist.md` 已区分环境入口、行动模板、Hook、commit 契约、Skill 语义转换与规则事实源 |
| 事实对象 / 项目治理相关 specs | 阶段 6-7 | 有正式事实源边界、状态机校验、受管项目解析和回写测试 |

每批 specs 进入正式 `specs/` 前，都必须留下迁移证据、Code 验证命令、测试结果和 unresolved warning 的处理去向。

## 5. 当前下一步

阶段 1 已完成：正式 `code/specs_validate.py` 已能解析 `ldvh_spec`、`ldvh_attachment`、H2 章节、`role_sections`、`code_consumption`、保障消费时机表和 02 AI 行为保障表，并由 `tests/code/` 覆盖。

阶段 2 已完成最小只读 Action Guide：Code 已能基于正式 specs 输出 `task_read_plan`、`next_queries`、`stop_conditions`、`validation_guard`、`missing_fields`、`capability_gap`、`impact_summary` 和 `source_refs`。该输出只作为过程指导，不成为独立事实源，也不声称运行时拦截、receipt 写入、Hook 或提交门禁已经生效。

阶段 3 已完成只读 preflight：Code 已能基于 Action Guide 和正式 specs 判断 target 类型、影响等级、必要读取、Human Gate 风险和 blocking/warning/follow_up/unverifiable 诊断分流。preflight 输出只作为诊断和阻断建议，不输出授权或 Human Gate 替代结论；无诊断时使用 `diagnostic_clear`，避免被误读为授权语义。

阶段 4 已完成最小 runtime facade：Code 已能按消费时机闭集承接 `session_start`、`acknowledge_read_plan`、`pre_tool_use`、`git_commit_msg`、`human_facing_output`、`external_output_intake`、`diagnostic_disposition` 和 `completion_claim`，生成 stdout-only receipt，并联动 Action Guide 与 preflight。`pre_tool_use` 与 `git_commit_msg` 缺少 read_plan 消费证据时阻断，`completion_claim` 缺少验证证据时阻断。该能力不声明 Hook、Rules、插件或环境已经完整接入。

当前进入阶段 5A：V2 内容吸收与语义映射。当前清单为 `_migration/stage-5-v2-absorption-checklist.md`，正式编号归口由 `_migration/v3-formal-spec-numbering-decision.md` 和 `_migration/v3-specs-absorption-index.md` 共同记录。

1. 按吸收清单逐项确认 V2 来源、当前状态、V3 归口、保留能力、废弃或后置内容、Skill 语义转换、前置 specs、前置 tests 和 Human Gate；
2. 先按吸收索引创建 `03/05/06/07/08/09` 的正式基础规范，确保每篇都有来源归口、保障措施、验证方法、Human Gate 和 Stop Conditions；
3. 再补 Code 可消费结构和负例测试，使 validator 能识别新正式 specs，而不把新增 docs 当作未验证空壳；
4. 只有在上述闭环完成后，才设计 Hook / Commit / 行动模板适配层；
5. 适配层只能调用 runtime/preflight/action-guide，不重新定义规则；
6. 明确环境未接入时的 fallback 行为和 diagnostic；
7. 为 commit gate、hook adapter、行动模板适配和环境缺口补齐回归测试。

## 6. 停止条件

出现以下情况时，暂停迁移并回到正式 specs 或 Human Gate：

1. 计划要求与 `specs/00-理念与构成.md`、`specs/01-保障与衔接.md`、`specs/04-Specs基础规范.md` 或 `specs/02-AI行为规范.md` 冲突；
2. 新增 specs 没有明确 Code、Action Guide、preflight、runtime 或事实源消费方；
3. Code 输出被用作授权、放行、Human Gate 或最终事实源；
4. Hook、外部工作流包装、Rules 或项目索引开始形成第二规则源；
5. 迁移材料无法说明减少了什么 AI 负担，或无法说明事实源边界和验证方式。
