# DeepSeek Harness WorkCaseRunController 运行时消费合同

> 状态：非权威实现合同（implementation handoff），不是 LDVH 规则、事实对象、平台状态或执行收据。
>
> WorkCase 的 `status`、`phase`、当前工作项、下一控制步骤及是否允许交还，始终以当前 WorkCase 的 fresh Helper 回读和投影为准。本文不定义、复制或补全其状态枚举与转换规则。

## 1. 权威来源与职责

| 事项 | 唯一来源 | Controller 只做什么 |
|---|---|---|
| WorkCase 生命周期、Gate、审核与写回 | `specs/21-WorkCase-工作项.md` | 把 AI 已完成的语义判断送入受控 Helper，并消费写后回读 |
| Gate 1 后执行、恢复、检查点与合法退出 | `specs/34-WorkCase获批计划执行行动模板.md` | 在每个检查点 fresh reread，不建立并行状态机 |
| 当前快照与交还判断 | Helper `read-fact-objects`、`check-workcase-handoff` 的当前结果 | 校验指纹后消费投影；不从聊天、缓存或平台事件猜测 |
| DeepSeek Harness 平台动作 | `specs/attachments/09.Att.05-DeepSeek-Harness平台机制事实.md` 与当次平台实际返回 | 建立或复用复核执行体、分派、接收报告；不解释 WC 语义 |
| 项目 Stop gate | `code/ldvh/hooks/workcase_stop.py` 及其来源规则 | 只作为已观察的平台保护；DeepSeek Harness 是否消费其 `.claude` 载体未验证（09.Att.05 §1），不把 fail-open/block 改写成 Controller 规则 |

本文中的流程图、表格和 trace 都是消费示例。若与上述当前来源或 Helper 结果冲突，停止使用本文对应内容并回到权威来源。

## 2. 最小运行绑定

Controller 可以保存的运行事实仅用于定位、关联、幂等与恢复：

```text
RunBinding
  controller_session_id          # DeepSeek Harness 当前会话 id（可观察时）
  workcase_ref                   # object_uid 或当前来源允许的精确引用
  last_source_fingerprint
  observed_plan_version
  observed_result_version?       # 仅当当前快照存在
  outstanding_dispatch?          # 执行体身份 + dispatch_correlation
                                 # continuable：childId + 当次 send_message 的 messageId
                                 # workflow：run id + agent 调用 seq（仅在该次前台调用存活期内有效）
  accepted_event_ids             # 有界幂等窗口；不是永久 receipt
```

约束：

- `RunBinding` 不是 LDVH 事实，不得承载或派生 WC `status`、`phase`、当前 item、next step、handoff 或完成结论。
- `last_source_fingerprint` 和版本只用于拒绝旧事件；每次可接受回调后仍必须 fresh reread Helper。
- `outstanding_dispatch` 只关联一次实际分派；报告被消费、取消或判旧后清除，不作为永久审计记录。workflow 前台调用的 dispatch 在调用返回时即完结，不得留下持久 outstanding。
- 平台卡（09.Att.05）不保存实例绑定、执行体当前状态、模型目录、review 结论或下一控制步骤。

## 3. 输入事件合同

DeepSeek Harness 当前可供 Controller 消费的输入形态如下。"受理/报告"两类在两条执行渠道上语义不同，不得混用（09.Att.05 §2 第 6 条）。

| 事件类 | DeepSeek Harness 实际形态 | 必需关联字段 | 接受前检查 | 接受后的唯一动作 |
|---|---|---|---|---|
| Human 输入到达 | 当前会话普通 user 消息 | controller session、WC ref、event id | session/WC 精确匹配；fresh reread 后确认当前控制步骤确实消费 Human 输入 | 由 AI 判断含义；需要写回时走 Helper CAS |
| 复核任务已受理（continuable） | `subagent` 调用返回 `subagentId`（inbox 接受即受理）；续轮 `send_message` 返回送达确认 | childId、messageId、event id | 与当前待分派动作匹配 | 记录短期 outstanding dispatch，然后 yield；不轮询 |
| 复核任务已受理（workflow） | 无独立受理事件：`agent()` 调用的返回即该轮复核完结（前台收集） | workflow run id、agent seq | 不适用（无异步窗口） | 直接消费返回值，不留 outstanding |
| 复核报告到达（continuable） | runtime 向父代理回合流递送的 settlement notice（含 stop reason 与最终 assistant 消息）；详细输出在子代理 Session transcript | childId、被审版本、实际 agent/model | 精确匹配 outstanding dispatch；版本/指纹未过期；实际模型/只读边界符合冻结 policy | fresh reread；由 Lead/Controller 处置报告并走 Helper 写回 |
| 复核报告到达（workflow） | `agent()` 返回值 / workflow 脚本 return 值 | 被审版本、实际 provider/model | 被审版本与当次分派一致 | 同上：fresh reread 后处置并写回 |
| session 恢复或接管 | DeepSeek Harness 会话恢复 / 上下文压缩后继续（会话经 `~/.dsh/sessions` 持久化） | controller session、WC ref、event id | 绑定可解析；不存在歧义绑定 | 丢弃缓存 next step，fresh reread Helper 后继续 |
| pre-yield / Stop | **未定位宿主原生事件**（09.Att.05 §1 相应行 unverified）；当前唯一可消费形态是 Controller 在交还前主动调用 `check-workcase-handoff` | controller session、WC ref | fresh `check-workcase-handoff` 成功且指纹绑定当前回读 | 只按 `handoff_allowed` 选择 yield/继续；Helper 不可用时遵守 34 §5.4 的既有安全策略 |

未知事件类型、未知 WC、session 不匹配、dispatch correlation 不匹配、重复 event id、旧 fingerprint、旧 plan/result version 均不得写回 WorkCase。实现应保留有界的"未处理原因"诊断，但不得把它写成 WC 状态。

## 4. 单步处理协议

每次回调只执行一个可验证的控制步：

1. 校验事件形态、精确 session↔WC binding、event id 与 dispatch correlation。
2. 通过 Helper fresh reread 精确 WorkCase；读取失败时不猜测、不写回。
3. 比较 source fingerprint 和适用的 plan/result version；过期回调标记为 stale 后结束。
4. 由 AI 结合 Human 目标、当前规则、完整授权包和当前事实作语义判断；Code 不选择 item、不判断语义完成。
5. 若需事实变更，提交一个完整 after + expected fingerprint 给对应 Helper 专属操作。
6. 只有 CAS、写后精确回读和独立事实完整性审计全部成功，才更新运行绑定。
7. 再次消费 fresh Helper 投影；继续执行或仅在 Helper 当前判定允许交还时 yield。

禁止用轮询、定时扫描 open WC、唯一候选猜测、聊天摘要或平台卡代替第 2、6、7 步。workflow 的"前台收集"不是轮询豁免：它是同步等待该轮复核返回，不产生异步事件，也不得被解释为 settlement notice。

## 5. 幂等与乱序

| 场景 | 合同级期望 |
|---|---|
| 同一 `event_id` 重复到达 | 第二次及以后 no-op；不重复 dispatch、不重复写回 |
| 同一 correlation 的两个执行体报告 | 只接受首个仍匹配当前 result/plan subject 的报告；其余标记 duplicate/stale |
| 旧 fingerprint 回调晚到 | no-op；fresh reread 后记录 stale 原因 |
| 未知 correlation 或 childId | no-op；不得把报告绑定到"看起来唯一"的任务 |
| CAS fingerprint stale | 不自动重放原 after；fresh reread 后由 AI 重新判断 |
| Controller 重启 / 会话恢复 | 只恢复最小 binding；丢弃缓存状态，从 Helper 当前快照重建下一动作；continuable 子代理经 cold resume 恢复 |
| continuable dispatch 受理后 Lead yield | 正常路径；等待 settlement notice 异步唤醒，不轮询子代理 |
| workflow 调用期间会话中断 | run 无 journaling/resume，按未完成的当次复核处理：fresh reread 后重新分派 |

## 6. 合同级 trace（synthetic / LDVH-observed）

以下 trace 只验证输入/输出合同，不证明 DeepSeek Harness 正式事件投递或真实 E2E：

| Trace | 证据级别 | 输入 | 预期 |
|---|---|---|---|
| T1 fresh resume | LDVH-observed（观察会话多次实际执行） | 精确 binding；Helper 返回 fresh fingerprint 与投影 | 继续当前控制步，不交还 Human |
| T2 duplicate report | synthetic | 相同 event id 与 correlation 重放 | 第二次 no-op，无 Helper 写回 |
| T3 expired report | synthetic | 报告绑定旧 result/plan version 或旧 fingerprint | stale，无 Helper 写回 |
| T4 unknown callback | synthetic | 未知 WC/session/correlation | 拒绝关联，无 Helper 写回 |
| T5 successful review callback（workflow 通道） | LDVH-observed（观察会话的只读探针与一次真实创建方案复核均经 workflow agent() 经 deepseek-official/deepseek-v4-flash 实际分派并返回报告） | 匹配的只读 Reviewer 报告 | fresh reread → Controller feedback 处置 → Helper CAS |
| T6 pre-yield | LDVH-observed（观察会话在 Gate 1 前实际消费 `handoff_allowed=true / gate1_waiting` 投影并合法等待） | `check-workcase-handoff` / 当前投影返回允许/不允许交还 | 只消费当前布尔 verdict；不从 phase 名称自行判断 |
| T7 restart | synthetic | 只恢复最小 binding，不恢复 cached next step | fresh reread 后重新判断 |
| T8 continuable settlement notice 端到端 | unverified | 分派后 Lead yield，等待异步唤醒 | 平台文档声明的机制；观察会话未实测 |

明确未验证：continuable settlement notice 的真实端到端时序（T8）、cold resume 在真实中断后的行为、宿主 pre-yield/Stop 事件的存在性（09.Att.05 §1）、DeepSeek Harness 是否消费项目 `.claude` Stop gate 载体、宿主崩溃恢复以及生产环境行为。

## 7. 当前可实现性观察

### 已验证（观察会话，2026-08-14）

- 当前 LDVH Helper 能精确回读 WorkCase，投影携带 source fingerprint 与 `handoff_allowed` / `handoff_reason`；观察会话在 Gate 1 前实际消费 `gate1_waiting` 投影并合法等待。
- workflow `agent()` 的 per-call `provider`/`model` 路由实际可用：只读探针（deepseek-official/deepseek-v4-flash）返回探针文本；同一通道实际承载了一次真实 WorkCase 创建方案复核（只读、返回完整复核报告、Controller 处置后完成受控创建）。
- LDVH 薄 Skill 在 DeepSeek Harness 真实加载（`~/.agents/skills` 根），规则引导、Helper capabilities、规范读取、受控创建与 CAS 更新在观察会话全部实际跑通。
- 委派子代理权限语义（沙箱继承、approval never、不可升级）有权威 README 依据；观察会话运行时上下文确认为 workspace-write + ask。

### 未验证

- continuable subagent 的 settlement notice 端到端、cold resume 真实中断恢复、`list_agents`/`interrupt_agent` 的真实行为（文档与工具面可观察，未实测）。
- 宿主 pre-yield/Stop 事件：公开 README 检索零命中，保持 unverified（未定位≠不存在）。
- DeepSeek Harness 是否消费 `.claude` 项目 Stop gate 载体；当前 worktree 的 Git Hook 实际部署状态（未在观察会话经 `git-hooks-status` 核验）。
- 真实多视角并行复核（`max_perspectives=2`）、workflow 并发上限行为、token 上限与模型故障路径。

## 8. 本次合同级验证记录

观察日期：2026-08-14（UTC）。该记录只说明当次观察会话的实际覆盖范围，不是可复用的平台保证。

- workflow 只读探针运行 `reviewer-route-probe`：1 个子代理经 deepseek-official/deepseek-v4-flash 返回 `PROBE_OK`。
- workflow 创建复核运行 `wc-creation-review`：1 个只读子代理（同一路由）返回 `changes_required` 与 6 条反馈；Controller 处置后 WorkCase 经受控创建实际落盘（写后回读与独立完整性审计均 passed）。
- Gate 1 批准写回：`update-workcase` CAS 成功，`phase=executing`，写后回读与独立完整性审计 passed；`baseline_fingerprint` 经 `code/ldvh/facts/workcase_projection.py` 的 `approval_baseline_fingerprint` 复算一致。
- 合同初次写盘；最终 SHA-256 以本文件写后回读为准，记录在所属 WorkCase 的验证材料中。
- 未验证范围保持 §6 末尾与 §7"未验证"所列，不因本记录缩减。

## 9. 后续 DeepSeek Harness 实现 WorkCase handoff

后续 WorkCase 只有在 Gate 1 前补齐下列输入，才应承诺实现：

| 类别 | 必须取得的前置 |
|---|---|
| 宿主事件 | continuable settlement notice、send_message 受理、session 恢复的真实事件形态、payload 与递达时机；pre-yield/Stop 事件的存在性结论（存在则精确类型与注册位置，不存在则以肯定证据升级为 supported 边界声明） |
| 部署事实 | 当前 worktree 的 Git Hook 部署状态（`git-hooks-status`）、LDVH 薄 Skill 在目标会话范围的递达证据、DeepSeek Harness 是否消费 `.claude` 项目配置的结论 |
| 写路径 | 若需要项目级配置或插件侧承接，具体允许路径闭集与逐项 Human 授权（本合同与 09.Att.05 均未授权任何部署动作） |
| 复核通道 | 冻结 reviewer policy 所选模型路由的当次可用性证据（只读探针或等价观察）；多视角并行与故障路径的行为证据 |
| 回滚 | 任何部署/配置写入的撤销步骤；未完成 dispatch 与 outstanding binding 的清理 |
| 测试矩阵 | T1–T8 的实测化（尤先 T8）；真实 Gate1→执行→Reviewer→Gate2 端到端；重复/乱序/重启/Helper unavailable/CAS stale 负例 |

后续实现不得把 DeepSeek Harness 的部署级权限预设或委派策略解释为 WorkCase 写授权，不得增加外部轮询 daemon、LDVH adapter 或第二状态机。若宿主事件仍不可定位，应把对应责任写为 blocked/unverified，而不是用 synthetic trace 宣称实现成功。
