# WorkCase Controller 续跑与行动模板收敛

## 覆盖与起点

本规划覆盖 `workcase-0042` 批准的增量：把行动模板使用期的最小临时工件卫生归入 `specs/06-行动模板基础规范.md`，把 `specs/34-WorkCase获批计划执行行动模板.md` 收敛为前置精确读取、执行循环、稳定检查点、合法退出和恢复交还五段内核，并以 clean source-contract tests 约束 Controller 对当前 WorkCase 投影的消费纪律。

`specs/21-WorkCase-工作项.md` 继续唯一负责 `status`、`phase`、字段、转换、quality gate、结果链和 `current_snapshot_projection` 语义；`specs/32-事实对象生命周期变更与承接处置行动模板.md` 继续组织受控写回。本文不把这些语义复制到 34，也不修改二者。

实现起点为 `cc63ff06d77b88fda7ed83661174ddffe8dbe46c`。创建前已有的未跟踪 `workcase-0036` 至 `workcase-0039` 不属于本增量；`specs/00-理念与构成.md` 也不在修改、暂存或提交范围。

## 实现目标与明确排除

本增量交付：

- 06 中一份跨行动模板共用的最小临时工件卫生边界；
- 34 中五段执行内核，以及基于刚精确回读快照和 current projection 的 Controller 循环；
- Reviewer pass 后逐步形成完整 after、Helper CAS、精确回读与完整性审计的连续收敛纪律；
- 对 executing 检查点、blocked 覆盖层、stale/unresolved 投影、提前 Gate 2 叙述和 Reviewer 后聊天总结停止的 source-contract 回归。

明确排除：

- 不新增或修改 production Code、公开 Helper 操作、Web、Web tests 或生成契约；
- 不持久化 `continuation_required`、`execution_stalled`、下一必经动作、投影指纹或 Web 进展分组；
- 不让 Code 判断自然语言授权、能力可用、行动允许、工作完成或下一 item；
- 不实现 AI 自由文本拦截器、调度器、Hook、MCP 或环境 adapter；
- 不修改 00、03、07、21、30、31、32，也不把测试通过表述为 AI 跨回合行为保障。

## 规范与实现责任

### `specs/06-行动模板基础规范.md`

在共同交还边界附近增加最小卫生规则：临时工件优先位于 Working Tree 外；确需落入 Working Tree 时，只有本次可确认归属、当前授权覆盖且无继续或恢复价值的工件可清理。执行前已存在、属于其它事项、归属不明或仍有恢复价值者必须保留并交还。Working Tree 非空本身不表示行动未闭环。

06 不承接 WorkCase 的逐检查点、phase 或关闭准备细节，也不新增通用 clean-working-tree 要求。

### `specs/34-WorkCase获批计划执行行动模板.md`

定义五段稳定内核：

1. 前置精确读取：读取当前 WorkCase、内容指纹、resolved current projection、冻结授权和批准；指纹或投影不 current 时重新读取。
2. 执行循环：AI 依据当前事实重新判断语义、依赖、授权和能力；`next_required_control_step` 只提供结构提示。
3. 稳定检查点：发生跨检查点工作时先形成真实 item after；每次事实写回使用 Helper CAS、精确回读和完整性审计。
4. 合法退出：只有 Human Gate、closed、真实 blocked、重复读取后仍 unresolved 的读取缺口，或已按结果链收敛的超界范围可以退出。普通 executing 检查点不是完成出口。
5. 恢复交还：交还只能描述刚回读 snapshot；只有 resolved `gate2_waiting` 才能说等待 Gate 2。

Reviewer pass 只是一项输入。Controller 必须从真实 `independent_reviewing` 开始，按 21/32 逐步完成 Controller 检查、关闭准备和 Human 关闭确认；每一步形成完整 after 并回读，不能只写聊天总结。34 不复制 phase 表、字段组合、quality gate 内容或 transition 条件。

### Tests

新增 `code/tests/specs/test_workcase_controller_continuation_contract.py`，只对 06/34 当前源文本和既有 deterministic projection/transition 能力形成 source contract：

- 34 五段内核均可定位，且明确回指 21/32；
- 34 不持久化 Spark 原提案中的两个派生字段，也不把 Code 写成自动语义判断者；
- executing 检查点不能成为完成交还；blocked 不被视为自动续跑；
- stale/unresolved projection 先重读，仍失败时只交还读取缺口；
- `independent_reviewing`、`closure_preparing` 不得生成 Gate 2 结论；
- Reviewer pass 后要求逐步受控写回，不能以聊天总结停止；
- 06 承接最小通用卫生，34 不再复制其详细规则。

只有审计证明既有 projection 或 transition 回归缺少直接覆盖时，才修改获批列名的现有测试。本增量优先复用现有 `test_workcase_presentation.py` 与 `test_transitions.py`，不为自然语言合同新增 production parser。

## 依赖与调用方向

允许方向：

```text
specs/21 WorkCase 事实与投影语义
  -> 既有 projection / transition Code
  -> Helper 精确读取与受控写回
  -> specs/34 Controller 行动组织

specs/06 模板共同边界
  -> specs/34 具体模板引用

specs/06 + specs/34
  -> clean source-contract tests
```

禁止 34 反向定义 21，禁止 tests 反向成为规则，禁止 Code 从 phase 自动选择行动或推进事实。

## 失败与诊断

- 当前 WorkCase、指纹或 projection 无法 current：重新精确读取；仍 unresolved 时交还读取缺口，不猜 phase 或话术。
- `status=blocked`：保留 lifecycle position，但 Controller 不把结构提示当成可执行许可。
- Reviewer 不可用：按 21 保持真实质量关口阻塞；Controller 不冒充 Reviewer。
- Reviewer 要求修改：只在冻结授权范围内返工；超界项据实取消并进入结果链。
- 白名单外路径、production Code 或 Web 才能完成：零执行受影响部分，不请求 Gate 1 后扩权。
- source-contract test 只能证明当前文本与既有 deterministic interface 的约束；不能证明某个 AI 在未来会话中实际遵从。

## 风险与验证映射

| 风险 | 检查 |
|---|---|
| 34 继续复制 21 状态机 | source-contract 断言五段流程回指 21/32，不出现 phase 规则表或字段组合副本；人工 diff 审核 |
| `independent_reviewing` / `closure_preparing` 提前表述 Gate 2 | 复用 presentation 负矩阵，并在 source contract 固定只消费 resolved `gate2_waiting` |
| Reviewer pass 后只输出聊天总结 | source contract 断言完整 after、CAS、精确回读、完整性审计和逐步收敛语义 |
| blocked 被误作自动续跑 | source contract 与既有 blocked projection matrix |
| stale projection 被继续消费 | source contract 断言指纹匹配和重新读取分流；既有 unresolved projection tests |
| 临时工件规则被过度上移 | 06/34 diff 审核与 source contract 只接受最小归属、授权、恢复价值边界 |
| 测试被误报为 AI 行为保障 | 计划、34 和测试注释明确可证明范围；Reviewer 复核交还声明 |
| 混入用户工作 | Index、路径白名单和受保护文件前后 hash 对比；`git diff --check` |

目标验证为行动模板精确读取、`code/tests/specs/test_workcase_controller_continuation_contract.py`、既有 WorkCase presentation/transition tests、必要的 repository specs tests、`git diff --check`、路径白名单检查、Helper 精确回读与全量事实完整性审计。Web 迁移和 Web tests 不在本增量。
