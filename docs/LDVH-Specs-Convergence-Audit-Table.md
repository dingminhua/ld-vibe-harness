# LDVH Specs 收敛审计表

日期：2026-07-08

## 0. 文档性质

本文是 specs 收敛审计表，不是正式 specs、不是事实源实例、不是行动授权，也不替代 Human Gate。

本文只整理当前已经暴露的 specs 收敛问题：哪些规则已经有归口，哪些仍需 specs-first 收敛，哪些只是 Code 或 tests 实现欠账。任何正式规则修改仍必须回到对应 specs 或附件，并按对应 Human Gate 要求执行。

## 1. 判断锚点

1. `specs/00-理念与构成.md` 是最高价值锚点，当前不修改；除非 Human 明确同意，否则不得把执行细节塞回 `00`。
2. 规则、契约、职责、语义边界类问题必须 specs-first 或 specs/code 同步；只有“实现没有遵守既有 specs”的问题才允许 code-first 修复。
3. Action Guide、Hook、runtime receipt、diagnostic、测试输出和安装检测都是保障与衔接手段，不是规则源、事实源或授权器。
4. V2 不再作为日常规则入口；本地 V2 是否可彻底删除由 `workcase-0024` 的删除准备度收口判断。
5. 当前整理只处理 V3 文件中已经暴露的问题，不从 V2 或 Git history 主动反推迁移清单。

## 2. 当前总判断

当前不能说 LDVH V3 specs 已经全局收敛完成。

已经基本收敛的部分：

| 范围 | 判断 |
|---|---|
| 环境插件薄引用边界 | 已由 `01`、`33`、`33.Att.01` 和共享 classifier 实现方向承接 |
| repo-local shim 与真实 integrated 区分 | 已由 `10`、`30`、`33` 和安装验证输出承接 |
| 管辖范围、no-op、unknown/gated、target-scoped blocking | 已由 `10`、`07`、`09` 和 runtime/code tests 承接 |
| repair lane 基础语义 | 已由 `01`、`07`、`09` 承接，仍需和自锁恢复设计一起复核 |
| verification_plan 基础选择模型 | 已由 `09` 和 test runner 本地承接，仍需检查开发过程是否按该模型使用 |

还不能算全局完成的部分：

| 范围 | 判断 |
|---|---|
| Action Guide 完整职责 | 归口已有，但需要确认 Code builder 前的输入、输出和非规则源边界是否足够可执行 |
| 能力匹配模型 | `01/10/33` 已有基础，但缺一个“LDVH 想做什么 / 环境能做什么 / 做不到如何交还”的统一规格入口 |
| 自锁 / repair / unknown-gated | 局部规则已有，但需要从“事实源写坏后如何受控修复、不全局锁死”这一真实事故重新做整体复核 |
| V2 收口 | `workcase-0024` 尚未关闭，03/05/06 和 `spark-0039` 仍是删除准备度硬项 |
| specs 职责边界 | 单篇边界大体清楚，但跨 `01/07/09/10/30/33` 的责任分配还需要一张稳定对照表，避免后续互相抢规则源 |

## 3. 六类收敛问题总表

| 问题域 | 要解决的问题 | 主归口 | 协作归口 | 当前状态 | 缺口判断 | 下一步 |
|---|---|---|---|---|---|---|
| Action Guide | 帮 AI 在行动前获得 read_plan、source_refs、stop conditions、validation guard 和项目事实源入口，但不能成为第二规则源或授权器 | `01` 定义保障衔接与行动指南；`07` 定义 Code 输出契约 | `06`、`10`、`09`、`02` | `00` 已定义行动指南是保障与衔接层职责；`06` 已定义行动模板不是规则源；`07` 已写 Action Guide governed project 链路；`10` 已定义管辖项目事实源入口 | 不是空白，但需要确认 Code builder 所需字段、缺口表达和多项目 read_plan 是否已经足够可执行 | 做一次 Action Guide builder 前 specs 对照：只确认来源、字段、缺口和停止条件，不写 builder 代码 |
| verification_plan / 测试分层 | 解决“开发过程测试过慢”和“什么时候跑什么测试”的判断问题 | `09` | `07`、`06`、tests 实现域 | `09` 已补 `verification_plan` 输出契约，明确其是测试选择说明，不是测试结果、事实源、授权、Human Gate 或完成证明；`07` 记录 test runner `verification_plan` 已补本地承接 | specs 口径已收敛到“最小稳定验证入口 + 未验证范围 / residual risk 明示”；后续风险主要是执行时没有按 plan 声明未覆盖范围 | 保持 `tests/code/test_ldvh_test_runner.py` 与 `tests/docs/01-Test-Runner-Practice.md` 作为实现域哨兵；新增验证入口或 profile 时先回到 `09` 判断是否改变语义 |
| 能力匹配模型 | 明确 LDVH 想做什么、环境 / 工具 / Git / Code 能做什么，做不到时如何交还，而不是把能力缺口伪装成已接入 | `01` | `07`、`10`、`30`、`33`、`09` | `01` 已定义 LDVH 能力、环境能力和能力缺口；`10` 定义 environment_strategy；`33` 定义插件要求和 capability_gap；`30` 定义安装验收交还 | 目前散落在多篇 specs；缺一个统一能力匹配表或附件，供 AI 判断“要求、能力、证据、不可验证、交还” | specs-first 设计能力匹配归口：优先考虑收敛到 `01` 或 `01` 授权附件，不先写 Code |
| 自锁 / repair / unknown-gated | LDVH 自己事实源写坏时，允许受控修复 primary target，但不能让坏对象全局阻断无关行动，也不能自动恢复或绕过 Human | `01` | `07`、`09`、`10`、`02`、事实模型成员规范 | `01/07/09` 已有 repair lane、target_primary、unrelated_global 和 final validation 口径；`10` 已有 scope_status 六类分流 | 局部规则已有，但还缺一个围绕真实事故的整体审计：事实源损坏、repair 目标归口、unknown/gated、Human 介入、失败后“已写未通过”的完整路径 | 先写自锁恢复设计审计，不动 runtime；确认需要补 `01/02/07/09/10` 哪些规则后再 specs patch |
| V2 收口 | 判断本地 V2 什么时候能彻底删除，不让 V3 active 文件继续引用 V2 作为后续迁移来源 | `workcase-0024` | `03`、`05`、`06`、相关事实对象 | README 已把 V2 降为历史来源；`workcase-0024` 仍 executing，明确 03/05/06 和 `spark-0039` 未收口前不得声明本地 V2 可删除 | 这是 V2 删除阻断，不是 Action Guide builder 的直接前置；但它影响 specs 自足性 | 按 `workcase-0024` 逐项完成 03/05/06、`spark-0039`、防回归检查和复审 |
| specs 职责边界 | 防止 `01/07/09/10/30/33` 互相抢规则源，尤其是安装、环境入口、验证、Code 输出、行动模板之间 | `04` 的结构治理 + 各单篇归口边界 | `01`、`07`、`09`、`10`、`30`、`33` | 单篇多数已写“本文归口 / 不归口”；30/33 也已声明只组织行动，不声明 integrated | 跨篇总览不足，后续 AI 仍可能把 30 写成机器规则源，把 33 写成安装验收源，或把 07 输出写成授权 | 建立职责边界对照表，作为 specs patch 前的 review checklist；必要时再补到对应单篇待补齐事项 |

## 4. 职责边界对照表

| Spec | 主职责 | 不应承担 |
|---|---|---|
| `00` | 定义 LDVH 存在理由、AI 第一服务对象、事实源边界、保障与衔接层、五类构成要素、V1-V9 | 具体流程、runtime 细节、环境插件细节、测试命令、字段 schema |
| `01` | 定义保障需求、消费时机、能力 / 能力缺口、环境入口上位语义、canonical event、receipt / evidence / diagnostic、repair lane | 具体 Code 模块、具体测试文件、插件 manifest、安装步骤、事实对象字段 |
| `07` | 定义 Code 能力边界、结构化输出、diagnostic、Action Guide 输出、preflight、runtime facade 实现边界 | 授权、Human Gate、事实源、Web 数据契约、安装验收、环境 integrated 声明 |
| `09` | 定义验证方式分层、验证声明、失败阻断、测试证据边界和验证入口选择 | 具体测试框架、每个测试文件职责、Code 输出 schema、行动步骤、事实对象字段 |
| `10` | 定义管辖项目配置、target-first、scope_status、多目标/no-op、install_plan 机器契约和环境策略 | 环境 integrated 判定、插件要求全文、Human-facing 安装流程、事实对象字段 |
| `30` | 组织安装、配置、验证、断点恢复和 Human-facing 交还的行动模板 | 机器核心安装规则、target resolver、环境 integrated 判定、插件编写要求、Code 输出字段 |
| `33` | 定义环境插件必须满足的要求，以及编写 / 更新插件或 adapter 的行动模板 | 安装验收闭环、真实 integrated 声明、共享分类逻辑、target 归口逻辑、diagnostic 分流 |

## 5. 对 Code builder 的影响

当前不应直接继续推进完整 Code builder。应先完成以下最小 specs 对照：

1. Action Guide builder 的输入来源是否只来自 `01/07/10/09` 和事实源，不从模板或 docs 复制规则。
2. 输出是否只包含 read_plan、source_refs、stop_conditions、validation_guard、missing_fields、capability_gap、unverifiable、residual risk 等过程辅助信息，不表达授权或完成。
3. 对 `governed_single`、`declared_multi_governed`、`non_governed`、`scope_unknown`、`governed_target_unknown`、`mixed_scope` 的输出是否分别符合 `10`。
4. 项目事实源入口是否只来自 resolver 输出的 `governed_project_path/ldvh-base/`，不得 fallback 到 LDVH 本体 facts、cwd 或对话记忆。
5. 测试选择是否按 `09` 的 `verification_plan` 输出契约和最小覆盖原则执行，并说明未验证范围与 residual risk。

上述五项通过后，Action Guide builder 才能作为实现欠账推进；如果任何一项需要新增语义，必须先回到 specs。

## 6. 建议执行顺序

| 顺序 | 工作 | 原因 | 输出 |
|---|---|---|---|
| 1 | 确认本文六类问题和归口是否成立 | 先统一问题框架，避免继续绕到 Code 或 Hook 单点 | Human/AI 对本文的确认或修改意见 |
| 2 | 做自锁 / repair / unknown-gated 设计审计 | 这是已经真实发生过的卡死问题，影响事实源维护主线可靠性 | 一份聚焦审计，列出需要补哪篇 specs |
| 3 | 做 Action Guide builder 前 specs 对照 | builder 是后续 Code 的关键入口，必须防止成为第二规则源 | builder 输入/输出/缺口/测试前置表 |
| 4 | 做 verification_plan / 测试分层执行对照 | 解决开发过程测试过慢，同时避免未验证完成声明 | 已补 `09` 的 `verification_plan` 输出契约；runner 对照由 tests 哨兵继续保障 |
| 5 | 做能力匹配模型 specs-first 草案 | 统一 LDVH 目标、环境能力、Code 能力和交还口径 | `01` 或 `01` 附件候选 patch 方案 |
| 6 | 按 `workcase-0024` 收口 V2 删除准备度 | 解除本地 V2 删除阻断 | 03/05/06、`spark-0039`、防回归检查和复审 |

## 7. 当前不做

1. 不修改 `00`。
2. 不直接继续写 Code builder。
3. 不把本文内容当作正式规则使用。
4. 不从 V2 或 Git history 生成新的迁移 checklist。
5. 不把环境插件样例、runtime 输出、测试输出或审计表写成 integrated、授权或验收完成。
