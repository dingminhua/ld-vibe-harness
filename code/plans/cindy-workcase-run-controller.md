# Cindy WorkCaseRunController 运行时消费合同

> 状态：非权威实现合同（implementation handoff），不是 LDVH 规则、事实对象、平台状态或执行收据。
>
> WorkCase 的 `status`、`phase`、当前工作项、下一控制步骤及是否允许交还，始终以当前 WorkCase 的 fresh Helper 回读和投影为准。本文不定义、复制或补全其状态枚举与转换规则。

## 1. 权威来源与职责

| 事项 | 唯一来源 | Controller 只做什么 |
|---|---|---|
| WorkCase 生命周期、Gate、审核与写回 | `specs/21-WorkCase-工作项.md` | 把 AI 已完成的语义判断送入受控 Helper，并消费写后回读 |
| Gate 1 后执行、恢复、检查点与合法退出 | `specs/34-WorkCase获批计划执行行动模板.md` | 在每个检查点 fresh reread，不建立并行状态机 |
| 当前快照与交还判断 | Helper `read-fact-objects`、`check-workcase-handoff` 的当前结果 | 校验指纹后消费投影；不从聊天、缓存或平台事件猜测 |
| Cindy / Orca 平台动作 | `specs/attachments/09.Att.04-Cindy平台机制事实.md` 与当次 Orca 回执 | 建立或复用 Worker、分派、异步接收报告；不解释 WC 语义 |
| 项目 Stop gate | `code/ldvh/hooks/workcase_stop.py` 及其来源规则 | 只作为已观察的平台保护；不把 fail-open/block 改写成 Controller 规则 |

本文中的流程图、表格和 trace 都是消费示例。若与上述当前来源或 Helper 结果冲突，停止使用本文对应内容并回到权威来源。

## 2. 最小运行绑定

Controller 可以保存的运行事实仅用于定位、关联、幂等与恢复：

```text
RunBinding
  controller_session_id
  workcase_ref                 # object_uid 或当前来源允许的精确引用
  last_source_fingerprint
  observed_plan_version
  observed_result_version?     # 仅当当前快照存在
  outstanding_dispatch?        # worker_session_id + dispatch_correlation
  accepted_event_ids           # 有界幂等窗口；不是永久 receipt
```

约束：

- `RunBinding` 不是 LDVH 事实，不得承载或派生 WC `status`、`phase`、当前 item、next step、handoff 或完成结论。
- `last_source_fingerprint` 和版本只用于拒绝旧事件；每次可接受回调后仍必须 fresh reread Helper。
- `outstanding_dispatch` 只关联一次实际分派；报告被消费、取消或判旧后清除，不作为永久审计记录。
- 平台卡不保存实例绑定、Worker 当前状态、模型目录、review 结论或下一控制步骤。

## 3. 输入事件合同

正式实现需要由 Cindy 提供类型化、可关联的宿主事件。当前只冻结输入/输出要求，不宣称这些事件已经接线。

| 事件类 | 必需关联字段 | 接受前检查 | 接受后的唯一动作 |
|---|---|---|---|
| Human 输入到达 | controller session、WC ref、event id | session/WC 精确匹配；fresh reread 后确认当前控制步骤确实消费 Human 输入 | 由 AI 判断含义；需要写回时走 Helper CAS |
| Orca dispatch 已受理 | worker session、dispatch correlation、event id | 与当前待分派动作匹配；平台返回实际成功调度信号 | 记录短期 outstanding dispatch，然后 yield；不轮询 |
| Orca Worker 报告 | worker session、dispatch correlation、event id、被审版本 | 精确匹配 outstanding dispatch；版本/指纹未过期；实际 agent/model/只读边界符合冻结 policy | fresh reread；由 Lead/Controller 处置报告并走 Helper 写回 |
| session 恢复或接管 | controller session、WC ref、event id | 绑定可解析；不存在歧义绑定 | 丢弃缓存 next step，fresh reread Helper 后继续 |
| pre-yield / Stop | controller session、WC ref、event id | fresh `check-workcase-handoff` 成功且指纹绑定当前回读 | 只按 `handoff_allowed` 选择 yield/继续；Helper 不可用时遵守宿主已定义的安全策略 |

未知事件类型、未知 WC、session 不匹配、dispatch correlation 不匹配、重复 event id、旧 fingerprint、旧 plan/result version 均不得写回 WorkCase。实现应保留有界的“未处理原因”诊断，但不得把它写成 WC 状态。

## 4. 单步处理协议

每次回调只执行一个可验证的控制步：

1. 校验事件 envelope、精确 session↔WC binding、event id 与 dispatch correlation。
2. 通过 Helper fresh reread 精确 WorkCase；读取失败时不猜测、不写回。
3. 比较 source fingerprint 和适用的 plan/result version；过期回调标记为 stale 后结束。
4. 由 AI 结合 Human 目标、当前规则、完整授权包和当前事实作语义判断；Code 不选择 item、不判断语义完成。
5. 若需事实变更，提交一个完整 after + expected fingerprint 给对应 Helper 专属操作。
6. 只有 CAS、写后精确回读和独立事实完整性审计全部成功，才更新运行绑定。
7. 再次消费 fresh Helper 投影；继续执行或仅在 Helper 当前判定允许交还时 yield。

禁止用轮询、定时扫描 open WC、唯一候选猜测、聊天摘要或平台卡代替第 2、6、7 步。

## 5. 幂等与乱序

| 场景 | 合同级期望 |
|---|---|
| 同一 `event_id` 重复到达 | 第二次及以后 no-op；不重复 dispatch、不重复写回 |
| 同一 correlation 的两个 Worker 报告 | 只接受首个仍匹配当前 result/plan subject 的报告；其余标记 duplicate/stale |
| 旧 fingerprint 回调晚到 | no-op；fresh reread 后记录 stale 原因 |
| 未知 correlation 或 Worker session | no-op；不得把报告绑定到“看起来唯一”的任务 |
| CAS fingerprint stale | 不自动重放原 after；fresh reread 后由 AI 重新判断 |
| Controller 重启 | 只恢复最小 binding；丢弃缓存状态，从 Helper 当前快照重建下一动作 |
| dispatch 成功后 Lead yield | 正常路径；等待 Cindy 异步唤醒，不轮询 Worker |

## 6. 合同级 trace（synthetic / LDVH-observed）

以下 trace 只验证输入/输出合同，不证明 Cindy 正式事件投递或真实 E2E：

| Trace | 证据级别 | 输入 | 预期 |
|---|---|---|---|
| T1 fresh resume | LDVH-observed + synthetic | 精确 binding；Helper 返回 fresh fingerprint 与 Controller-owned 投影 | 继续当前控制步，不交还 Human |
| T2 duplicate report | synthetic | 相同 event id 与 correlation 重放 | 第二次 no-op，无 Helper 写回 |
| T3 expired report | synthetic | 报告绑定旧 result/plan version 或旧 fingerprint | stale，无 Helper 写回 |
| T4 unknown callback | synthetic | 未知 WC/session/correlation | 拒绝关联，无 Helper 写回 |
| T5 successful review callback | synthetic | 匹配的只读 Reviewer 报告 | fresh reread → Controller feedback 处置 → Helper CAS |
| T6 pre-yield | LDVH-observed | `check-workcase-handoff` 当前返回允许/不允许交还 | 只消费当前布尔 verdict；不从 phase 名称自行判断 |
| T7 restart | synthetic | 只恢复最小 binding，不恢复 cached next step | fresh reread 后重新判断 |

明确未验证：Cindy event delivery、Lead 自动唤醒、session lifecycle hook 接线、真实 dispatch/report 端到端时序、宿主崩溃恢复以及生产环境行为。

## 7. 当前可实现性观察

### 已验证

- 当前 LDVH Helper 能精确回读 WorkCase，并由 `check-workcase-handoff` 返回绑定 source fingerprint 的只读交还判定。
- 当前 `project-stop` 实现只接受显式 WC 绑定，消费 fresh Helper verdict；缺失绑定、解析失败、Helper 失败或异常时 fail-open，`stop_hook_active=true` 防止循环。
- 当前 Orca workspace 可回读 session 级 Worker，已有匹配的 `codex / gpt-5.6-luna / medium` Reviewer；成功分派后由平台异步回送，不以普通轮询等待。
- [Cindy 公开客户端仓库](https://github.com/makecindy/cindy) 可访问；README 将其描述为 desktop/mobile/shared packages 的 pnpm monorepo，并明确 backend 不在该仓库。

### 未验证

- 当前受管 LDVH worktree 与 `.cindy-worktrees` 没有可供本 WorkCase 修改或测试的 Cindy 源码 checkout。
- 未定位 Cindy 内部正式的 Human-message、dispatch-accepted、worker-report、session-resume、pre-yield/Stop 事件类型及注册位置。
- 未确认公开 client monorepo 是否包含 Orca server-side dispatch、持久队列、自动唤醒和 backend session 生命周期的完整实现；公开 README 明确 backend 在另一仓库。
- 未执行真实 Cindy/Orca 应用级 E2E、生产事件或宿主恢复测试。

## 8. 本次合同级验证记录

观察日期：2026-08-15。该记录只说明本次 WorkCase 实际覆盖范围，不是可复用的平台保证。

- `code/tests/helper/test_check_workcase_handoff_operation.py` 与 `code/tests/hooks/test_workcase_stop.py`：共 22 项通过。
- 对当前精确绑定 WorkCase 调用 `check-workcase-handoff`：返回 fresh source fingerprint，`handoff_allowed=false`、`handoff_reason=controller_owned`，下一结构步骤为继续当前工作项。
- 临时内存 trace：duplicate、expired、unknown binding、unknown correlation、valid report 与 restart 共 7 个断言通过；临时 trace 未写入仓库。
- 合同文件初次回读 SHA-256：`66e2cf5c9b2e3e2e9e1eafcc5a8025d725887d905ab9b9a64fc5b257c098af74`；本节补充后应以最终回读哈希为准。
- 未验证范围保持不变：真实 Cindy event delivery、自动唤醒、session lifecycle、真实 dispatch/report E2E、宿主崩溃恢复和生产行为。

## 9. 后续 Cindy 实现 WorkCase handoff

后续 WorkCase 只有在 Gate 1 前补齐下列输入，才应承诺实现：

| 类别 | 必须取得的前置 |
|---|---|
| repo locator | Cindy client/backend 的精确仓库身份、分支或隔离 worktree、治理归属 |
| 写路径 | Controller、session binding、事件 handler、Orca bridge、测试文件的具体允许路径闭集 |
| 正式事件 | Human 输入、dispatch 成功、Worker report、session restore、pre-yield/Stop 的真实类型、payload、ordering 与重放语义 |
| 授权 | 上述路径写入、Worker 建立/复用、真实 dispatch/report、宿主配置、依赖安装和外部服务副作用逐项授权 |
| 环境 | 非生产验证账号/服务、测试数据、临时绑定位置、日志隐私与清理边界 |
| 回滚 | 代码回退、事件注册撤销、binding/queue 清理、未完成 dispatch 的处置 |
| 测试矩阵 | T1–T7 单元/集成测试；真实 Gate1→执行→Reviewer→Gate2；重复/乱序/重启/Helper unavailable/CAS stale 负例 |

后续实现不得把 Worker 的 Full access 偏好解释为 WorkCase 写授权，不得逆向私有 API，不得增加外部轮询 daemon、LDVH adapter 或第二状态机。若正式事件或源码仍不可达，应把对应责任写为 blocked/unverified，而不是用 synthetic trace 宣称实现成功。
