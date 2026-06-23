# LDVH v2 active 切换计划

```yaml
v2_activation_plan:
  status: draft_non_authoritative
  canonical_path: specs-v2/V2-ACTIVATION-PLAN.md
  active_fact_source: specs/
  purpose: "规划 v2 从写作区成为 active 正式规范前后的门禁、文件动作、入口切换、历史记录处理和回滚路径"
  rule: "本文只记录切换计划；不得被解释为 v2 已 active，不得替代 Human Gate，不得触发任何自动切换。"
  depends_on:
    - specs-v2/00-LDVH理念与价值标准.md
    - specs-v2/01-规范体系基础规范.md
    - specs-v2/MIGRATION-MAP.md
    - specs-v2/PLAN.md
```

> 文件状态：本文是 `specs-v2/` 写作区的切换计划文件，不是正式规范，不是事实源，不执行切换。
>
> 本文只回答“未来如何切换”。当前 active 正式规范事实源仍是 `specs/`。

## 1. 定位

v2 active 切换不是把 `specs-v2/` 目录整体改名为 `specs/` 这么简单。

切换必须同时处理五件事：

1. v2 规范正文成为新的 active 正式规范；
2. v1 `specs/` 退出 active 事实源并进入历史记录；
3. 切换前的事实源、工作对象、提交记录和派生材料不被直接继承为新 active 事实；
4. Rules、Skills、Agents、Hooks、Code、Web 的默认入口按顺序切换或明确后置；
5. 任何失败都能回滚到切换前状态。

本文只规划这些动作。实际执行必须另行经过 Human Gate。

## 2. 不执行事项

在 Human 明确批准 v2 active 切换前，禁止执行以下事项：

1. 不得把 `specs-v2/` 或其中任一文件作为 active 正式规范引用；
2. 不得移动、重命名或删除 active `specs/`；
3. 不得把 active `specs/` 归档到历史目录；
4. 不得把 `specs-v2/` 规范文件移动到 active `specs/`；
5. 不得修改 Rules、Skills、Agents、Hooks、Code 或 Web 的默认入口，使其默认消费 v2；
6. 不得把切换前事实源直接当作新 v2 事实源继续消费；
7. 不得建立落盘知识地图缓存或把知识地图输出当作事实源。

## 3. 前置条件

只有同时满足以下条件，才允许进入 v2 active 切换执行准备：

| 条件 | 要求 |
|---|---|
| v2 覆盖状态 | `MIGRATION-MAP.md` 中所有 v1 来源都有 `human_confirmed`、明确后置或明确废弃理由 |
| 行动编排边界 | v2 03 已定义行动编排如何由规范保障需求生成、登记、接管和回写；具体 30-59 可按后置计划处理 |
| v2 规范目录 | 00-08、20-29 已确认成员、授权附件和辅助控制文件边界稳定 |
| 身份与路径 | v2 规范身份、附件身份、canonical path、状态闭集和 active 身份块转换规则已经确认 |
| 事实源策略 | v1 退出 active 后的历史记录位置、命名、读取边界和提取顺序已经确认 |
| Code 检查 | active v1 全量检查与 v2 只读检查双跑通过，且无未解释诊断 |
| 入口切换方案 | Rules、Skills、Agents、Hooks、Code、Web 的默认入口切换顺序和回滚路径已列出 |
| Human Gate | Human 明确批准 v2 成为 active 正式规范事实源，并确认本计划的执行版本 |

## 4. Human Gate

v2 active 切换必须由 Human 明确确认，且确认内容至少包括：

1. 允许 v1 `specs/` 退出 active 规范事实源；
2. 允许指定 v2 规范正文成为新的 active `specs/`；
3. 允许切换前事实源进入历史记录；
4. 允许 Code、Rules、Skills、Agents、Hooks 和 Web 按计划逐步切换入口；
5. 确认回滚路径可接受；
6. 确认未迁移的行动编排成员继续后置，不阻塞 v2 active。

Human Gate 必须发生在实际文件移动、路径替换、入口切换和事实源历史化之前。

## 5. 文件切换方案

### 5.1 目标目录

推荐切换目标如下：

| 对象 | 切换前 | 切换后 |
|---|---|---|
| active v1 规范 | `specs/` | `history/specs-v1/` |
| v2 正式规范正文 | `specs-v2/{00-08,20-29}.md` 和授权附件 | `specs/` |
| v2 写作区辅助控制文件 | 迁移期写作区入口、`PLAN.md`、`MIGRATION-MAP.md`、`V1-UNDERSTANDING-GATE.md`、`V2-ACTIVATION-PLAN.md` | `history/specs-v2-migration/` |
| v2 未处理草案 | `specs-v2/` 中未被 Human 确认的文件 | 不进入 active `specs/`，按 Human Gate 决定归档或保留 |

`specs-v2/` 不能整体原样改名为 `specs/`。只有已核对、已确认、具备 active 身份转换规则的规范正文、成员主文件和授权附件可以进入新的 active `specs/`。

### 5.2 active 身份转换

进入新 `specs/` 的文件必须完成身份转换：

1. `canonical_path` 从 `specs-v2/...` 改为 `specs/...`；
2. `status` 从 draft 或未 active 状态改为 active 状态；
3. `active_fact_source` 不再指向旧 `specs/`；
4. `migration_status`、`migration_sources` 等迁移写作字段按 01 规则处理为 active 可保留字段、历史字段或移除字段；
5. 所有内部引用从 `specs-v2/...` 改为 active `specs/...`；
6. 辅助控制文件不得随规范正文进入 active 规范目录，除非 Human 明确把某个文件改造为正式规范或正式附件。

### 5.3 建议提交拆分

实际切换时应拆为多个可回滚提交：

| 提交 | 动作 | 要求 |
|---|---|---|
| A | 切换前冻结检查 | 记录检查命令、结果和 Human Gate 结论，不移动目录 |
| B | 归档 v1 `specs/` | 把 v1 active 规范移入历史记录位置，保留 Git 追溯 |
| C | 建立新 active `specs/` | 移入已确认 v2 正式规范正文、成员主文件和授权附件 |
| D | 身份和引用规范化 | 更新 canonical path、状态、内部引用和目录登记 |
| E | Code 双读到默认读取切换 | Code 默认入口切到新 `specs/`，保留必要历史读取能力 |
| F | Rules/Skills/Agents/Hooks 入口切换 | 运行时扩展入口改读新 active 规范 |
| G | Web 后置或切换记录 | Web 若不切换，记录后置；若切换，必须有独立回归 |

不得把归档、替换、Code 默认入口切换和运行时扩展入口切换塞进一个不可分割提交。

## 6. 事实源历史化

v2 active 后，切换前事实源进入历史记录。历史记录不是新的 active 事实源。

历史化对象包括：

1. v1 `specs/`；
2. 切换前 `ldvh-base/` 工作对象事实；
3. 切换前 Git commit records 中对旧事实源的追溯；
4. 切换前 Code、Web、Rules、Skills、Agents、Hooks 的入口和检查结果；
5. 切换前 docs/studies、docs/sources 等仍有保留价值的材料。

历史记录只能用于追溯、审计和价值提取，不得直接驱动新 v2 工作对象状态、关闭判断或默认执行入口。

## 7. 历史记录价值提取顺序

新事实源不得直接继承旧事实源状态。应按以下顺序提取仍有价值的内容：

| 顺序 | 动作 | 输出 |
|---|---|---|
| 1 | 建立历史记录清单 | 历史来源、路径、时间、归属和读取边界 |
| 2 | 识别仍有价值内容 | 需求、决策、证据、经验、风险、未完成事项和长期上下文 |
| 3 | 判定 v2 归属 | 映射到 Spark、WorkCase、ADR、Pitfall、Study 或后置行动编排候选 |
| 4 | 重写为 v2 事实 | 按 v2 事实模型字段契约创建或更新新事实源 |
| 5 | 保留来源追溯 | 记录来自哪个历史对象和 Git 提交，不复制旧状态为新状态 |
| 6 | 运行 Code 检查 | 校验字段、状态、引用、事实源边界和 Git 追溯 |
| 7 | Human Gate | 对高影响事实、争议事实、关闭判断和长期经验进行确认 |

价值提取完成前，不能宣称旧事实源已经被完整吸收。

## 8. 入口切换顺序

默认入口切换应按以下顺序推进：

| 顺序 | 对象 | 切换要求 |
|---|---|---|
| 1 | Code 只读检查 | 先支持新 `specs/` active 读取，同时保留历史目录只读追溯 |
| 2 | Code 默认检查 | `all`、`index`、`assurance-report` 等默认入口改读新 active 规范 |
| 3 | Rules | `LDVH-WORKSPACE-ENTRY.md`、`LDVH-MAINTAINER-ENTRY.md` 改读新 active 规范 |
| 4 | Skills | Skill 流程改读新 active 规范和新 Code 输出 |
| 5 | Agents | 子 Agent 入口、审查提示和并行审查规则改读新 active 规范 |
| 6 | Hooks | 阻断、提示、提交前检查等 Hook 改读新 active 规范 |
| 7 | Web | Web 暂可后置；若切换，必须按 05 和 08 完成 DTO/API/页面回归 |

任何一步失败，应停止后续切换，并按 §10 回滚或降级。

## 9. 后置事项

以下事项不阻塞 v2 active，但必须在切换后单独规划：

1. 行动编排候选计划：根据 v2 各规范提出的保障需求，生成 30-59 候选行动编排，不按 v1 30/41/42/43/44 直接迁移；
2. 新事实源建立：从历史记录提取仍有价值内容后，按 v2 事实模型重新进入事实源；
3. 知识地图完整运行：在 v2 active、新事实源稳定、Code 默认入口切换后，再推进知识地图运行时能力；
4. Web 接入：在 DTO、API、Confirm UI、轻写入白名单、提交记录展示和图谱展示契约稳定后再接入；
5. 历史记录审计：确认 v1 退出 active 后仍可追溯，但不会被默认消费。

## 10. 回滚方案

每个切换阶段都必须能够回滚。

最低回滚要求：

1. 切换前创建可追溯 Git 提交或标签；
2. 每个阶段单独提交，避免不可拆分大提交；
3. 保留 v1 `specs/` 历史目录完整内容；
4. 保留 v2 辅助控制文件历史；
5. Code、Rules、Skills、Agents、Hooks、Web 的入口切换必须有反向修改路径；
6. 回滚后必须重新运行 active v1 检查；
7. 不得使用破坏性 Git 命令回滚，除非 Human 明确授权具体命令和范围。

如果切换失败但 v1 `specs/` 尚未归档，可以直接停止，不执行后续步骤。如果 v1 已归档但新 `specs/` 未通过检查，应把历史目录中的 v1 规范恢复为 active `specs/`，并恢复 Code 与运行时扩展默认入口。

## 11. 完成标准

只有同时满足以下标准，才可以宣称 v2 active 切换完成：

1. 新 `specs/` 中只包含已确认的 active 正式规范、成员主文件和授权附件；
2. v1 `specs/` 已进入历史记录位置，且不再被默认入口消费；
3. Code active 检查通过；
4. v2 只读迁移检查不再作为默认 active 判断入口；
5. Rules、Skills、Agents、Hooks 的默认入口已切换或有明确后置记录；
6. Web 切换或后置状态已记录；
7. 切换前事实源历史化完成；
8. 历史记录价值提取计划已经建立；
9. 回滚路径仍可执行；
10. Human 明确确认切换完成。

## 12. 待补齐事项

1. 确认 v1 历史记录最终目录名是否采用 `history/specs-v1/`；
2. 确认 v2 写作区辅助控制文件最终归档目录名是否采用 `history/specs-v2-migration/`；
3. 确认 active 身份块转换后的字段闭集；
4. 确认切换执行时需要的 Code 专项检查命令；
5. 确认 Rules、Skills、Agents、Hooks、Web 每个入口的具体修改清单；
6. 确认新事实源初始化和历史价值提取的首批对象范围。
