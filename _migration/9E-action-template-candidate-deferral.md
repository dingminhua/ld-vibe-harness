# 9E 行动模板候选后置记录

> 文件状态：temporary migration decision。本文记录阶段 9E 对非提交行动模板候选的后置结论，不授权正式行动模板实例、Hook 启用、Web 通用写入、Human Gate 自动完成或 V3 正式主线接管。正式规则仍以 `specs/` 正文为准。

## 1. 迁移目标

阶段 9E 的目标是把“暂不迁入的行动模板”正式收口，避免它们成为隐性缺口或被误写成已启用能力。

本阶段不建立新的正式行动模板实例。Git 提交行动仍是当前唯一已进入 `specs/06-行动模板基础规范.md` 正文的模板示范。

## 2. 后置候选清单

| 候选模板 | 来源或触发 | 后置结论 |
|---|---|---|
| WorkCase 创建 | 用户目标、Spark 分流、跨会话工作升格 | 后置。需要明确 WorkCase 创建字段、准入说明、Human Gate、Code/Web 写入和提交回写 |
| 方案审核 | `subagents_plan_reviewing` / `human_plan_confirming` | 后置。需要明确方案字段、独立审核输出、Human 方向确认和状态写回 |
| 执行推进 | `executing` 与执行项更新 | 后置。需要明确执行项字段闭集、状态更新粒度、失败分流和验证入口 |
| 结果自检与结果复核 | `result_self_checking` / `subagents_result_reviewing` | 后置。需要明确验证声明、复核输出、残留风险和关闭前证据回写 |
| 关闭确认 | `human_closure_confirming` -> `closed` | 后置。需要明确关闭结果、关闭证据、后续分流 / 收口结果和 Human 关闭确认 |
| Rules 同步审查 | V2 `30-rules-entry-sync-review` | 后置。需要等待环境入口、Rules 薄引用和 Hook/adapter 边界稳定 |
| 环境入口适配 | V2 `32-environment-entry-adaptation` | 后置。涉及安装、覆盖或启用环境入口时必须 Human Gate |

## 3. 后置理由

1. V3 当前未启用真实 Hook、runtime adapter 或通用环境入口；
2. 9D 只迁入 Spark quick create 这一最小 Web 轻写入，未启用通用 Web 写入或完整 Confirm UI；
3. WorkCase `21.Att.01-orchestration字段契约表` 尚未作为正式附件迁入，相关字段仍由实例 schema 和 Code/tests 承接；
4. 方案审核、结果复核和关闭确认直接影响 Human Gate，不能用纸面模板代替真实确认路径；
5. 在入口、字段、验证和回写尚未稳定前迁入正式模板，会增加 AI 负担，而不是减少 AI 负担。

## 4. 后续准入条件

非提交行动模板只有同时满足以下条件后，才能重新判断是否迁入正式模板：

1. 能说明减少的 AI 负担，并回指 `00/01/02/06` 与对应事实对象规范；
2. 具备完整 Context、Scenario、Gate、执行、验证、回写和交还结构；
3. 对应事实对象字段、状态和回写位置已由正式 specs、附件或 Code/tests schema 承接；
4. Code、Web API 或等价入口能提供稳定写入 / 回读 / source_refs / diagnostics；
5. 涉及授权、方向确认、风险接受、验收或关闭时，有明确 Human Gate 路径，不以模板步骤、按钮或测试通过替代 Human 决定；
6. 有目标测试或等价验证覆盖正例、负例、失败分流和未验证完成；
7. 若依赖 Hook、Rules、Skill、Agent 或环境入口，必须保持环境输出不成为第二规则源，并标明 `environment_integrated` 边界。

## 5. 主线切换影响

9E 完成后，非提交行动模板不阻断 V3 主线切换。主线切换前只需要保留以下事实：

1. Git 提交行动是当前唯一正式模板示范；
2. WorkCase 创建、方案审核、结果复核和关闭确认继续作为后置候选；
3. 这些候选可以被 Action Guide 提示或当前对话手动等价执行引用，但不得被描述为已启用模板；
4. Hook、完整 Confirm UI、通用 Web 写入和 runtime adapter 仍是 9F 或后续环境接入的独立边界。

## 6. 验证记录

本阶段属于正式规范边界和迁移文档更新，应使用目标验证，不需要运行慢速全量测试。

提交前应运行：

```text
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 -m pytest tests/code/test_formal_specs.py -q
python3 code/specs_validate.py commit-gate --format text --fail-on-diagnostics --message <planned commit message> ...
```
