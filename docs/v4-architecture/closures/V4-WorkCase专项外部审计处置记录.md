# V4 WorkCase 专项外部审计处置记录

> 处置日期：2026-07-14。审计输入为仓库根目录 `V4-Audit-Report-GLM5.2-2026-07-14.md`。本文记录意见核对和修正结果，不取得 WorkCase、字段或实现定义权；当前规则仍以 00、05、05.Att.01、06 和 21 为准。

## 1. 结论

外部审计给出“有条件通过，最高 P2”，肯定对象粒度、status/phase 正交、双 Human Gate、工作项边界、中断恢复和字段治理，并提出 3 个 P2 与 3 个 P3。逐项回读当前来源和实现后，没有一项原样保持 P2：一项降为清晰度修正，两项因当前来源或 Code/AI 边界已有明确答案而不成立；三个 P3 中一项转为标识清晰度修正，一项只增加图示说明，一项不成立。

处置过程中通过新增全 phase 有效快照测试发现审计未报告的实际冲突：`status=open/blocked` 的 Code 条件曾禁止关闭前结果包字段，而 `human_closure_confirming` phase 又要求这些字段，导致关闭前 Human Gate 无法形成有效对象。当前已把 status 限定为责任可推进性，把结果包字段条件归还 phase，并为七个 phase 建立有效对象回归。

## 2. 审计意见处置

| 审计项 | 处置 | 核对依据 | 当前动作 |
|---|---|---|---|
| P2-1 Human 退回后 plan_version 级联失效范围不明确 | 部分接受，降为 P3 清晰度 | 21 已分别定义计划覆盖内容、结果覆盖内容，并在转换表写明“若改计划/若改结果”；失败场景不应触发 plan_version | 增加明确否定规则：只改结果不得递增 plan_version、撤销仍有效计划审核/批准或重开未受影响 item；确需重新执行才退回 executing |
| P2-2 human_closure_confirming 的 waiting_on 不明确 | 拒绝 | 21 的字段定义要求 Human 确认阶段说明具体 Gate；转换表要求写 waiting_on；Code 对两个 Human phase 均 `_require(waiting_on)` | 不改变模型；新增缺少 waiting_on 的失败测试，防止未来漂移 |
| P2-3 Code 未检查 pass_with_followups 的逐项语义处置 | 拒绝作为实现缺陷 | controller_resolution 是自然语言 string；21 明确 AI 必须检查全部反馈是否处理，Code 不得判断反馈是否语义解决 | 不用编号/换行计数冒充语义覆盖；未来若确有机械消费者，必须先把逐项处置重构为已准入结构，不能解析自然语言猜测 |
| P3-1 completed 后未明确移除 current_summary/resume_from | 拒绝 | 工作项状态表已禁止 completed 携带两字段；紧随文字明确由结果与证据吸收并移除；validator 已拒绝禁止字段 | 不增加自动静默删除；未来受控更新必须要求调用者提交完整有效目标状态并回读，不能由 Code 猜测如何改写事实 |
| P3-2 F1 未授权 work_item_counts | 部分接受为命名清晰度 | 21 已授权 F1 返回工作项状态计数并允许 Helper 派生，但未写实现键名 | 在 F1 投影正文显式写 `work_item_counts`，明确它不是登记字段且不得写回对象 |
| P3-3 流程图缺少 blocked→closed | 接受为图示说明，不增加 phase 边 | blocked 是 status，图只表达 phase；文字已要求 blocked 也完整经过结果分类、独立审核和第二 Human Gate | 在图后说明 status 覆盖层与关闭路径，避免把 blocked 误读为 phase |

## 3. 额外发现与修正

### status 与 phase 条件冲突

原 validator 在 `status=open` 时禁止 validation_summary、closure_outcome、disposition_summary 和顶层 evidence_refs，在 `status=blocked` 时也禁止关闭结果字段；但 21 要求这些字段在 `human_closure_confirming` 时已经形成，而该 phase 在 Human 批准前仍只能是 open 或 blocked。结果是第二 Human Gate 没有任何可通过机械校验的对象快照。

修正后：

1. status 只决定 priority、blocking_summary、阻塞证据、closure_approval 和 closed_at 等责任状态条件；
2. phase 决定 result_version、controller_check_summary、result_reviews、最终验证/处置和 closure_approval 的出现时机；
3. human_plan_confirming、executing、controller_checking、independent_reviewing、closure_preparing、human_closure_confirming、closed 各有至少一个完整有效快照测试；
4. `human_closure_confirming` 缺少 waiting_on 有专门失败测试。

这是实现与来源内部一致性缺陷，不改变已经确认的 WorkCase 架构；修正使 status/phase 的正交声明真正可执行。

## 4. 后置验证边界

“Human 只改结果时 result_version 递增而 plan_version 不变”是一次前后对象转换性质，当前静态 validator 只能验证单个快照，不能证明版本单调性、字段失效和允许转换边。相应正向/负向测试必须作为事实对象受控更新/CAS 的准入测试，与以下能力一起实现：

- 读取并比较预期旧版本；
- 单对象原子 CAS；
- phase/status 允许边；
- plan/result 版本单调性和失效字段；
- 写后回读与失败不冒充成功。

在该入口成立前，不增加只匹配规范句子的伪转换测试，也不把静态对象校验描述为生命周期推进已经实现。

## 5. 当前 Gate

外部审计意见已完成逐项处置：

- 全量 tests：448 passed；
- Ruff lint 与 format check：passed；
- `git diff --check`：passed；
- 当前仓库检查：18 个当前规范文档、0 issues、implemented checks complete；
- 字段治理：5 个事实类型、8 个结构、81 个字段、0 issues。

WorkCase 类型 Gate 保持关闭，下一步恢复阶段 6 的“事实对象判定与受控创建”具体行动模板。受控更新、阶段推进和 Web 展示仍是后置能力，不因本次处置自动取得效力。
