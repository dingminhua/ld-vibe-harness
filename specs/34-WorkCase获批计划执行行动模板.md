# WorkCase 获批计划执行行动模板

```yaml
ldvh_spec:
  spec_key: "workcase-approved-plan-execution-action-template"
  spec_id: "34"
  spec_kind: "spec"
  title: "WorkCase 获批计划执行行动模板"
  status: "active"
  canonical_path: "specs/34-WorkCase获批计划执行行动模板.md"
  parent_spec: "action-template-foundation"
  relation: "refines"
  positioning: "组织已获 Human Gate 1 批准的 WorkCase 从当前执行快照开始，自动消费授权包完成工作项推进、结果复核和关闭交还的可恢复行动结构"
  scope: "仅适用于冻结 execution_authorization 基线已获 execution_approval 的 WorkCase 执行、检查点写回、包内调整、阻塞恢复、结果复核、关闭准备与上下文接续；不定义 WorkCase 字段、状态机、Helper API、调度器、spawn 能力或其它事实对象类型规则"
  basis:
    - "action-template-foundation"
    - "workcase-fact-type"
    - "fact-object-lifecycle-change-action-template"
  authorized_attachments: []
```

> 文件状态：`active`。本文只组织 21 已定义的执行期行动。模板存在不证明某个 WorkCase 已获批准、当前对象可读、Human Gate 已满足、Helper 写入可用、委派或 spawn 能力存在、工作项已开始或结果已完成；它不以模板步骤替代 AI 对当次来源、授权、事实、风险或完成的判断。

## 1. 价值判断

获批计划在实际执行时需要在“无中间状态的局部工作”与“跨检查点、可中断或需要交接的工作”之间保持如实的不同写回形状。本文把精确回读、Gate 1 授权消费、开始检查点、实施、阻塞/恢复、结果收敛、独立复核、Gate 2 和恢复交还组织为一条可重复结构，避免先实施后补造 `in_progress` 历史，也避免为极小同一检查点结果制造虚假的中间状态或在模板步骤间重复请求 Human 授权。

## 2. 规范依据

本文直接依据 06 对模板选择和交还的共同边界、21 对 WorkCase 执行批准/phase/work item/关闭的唯一类型规则，以及 32 对活动期 WorkCase 专属 CAS 路由和完整 after 回读的共同变更边界。20、22、23、24 的类型条件、05 的事实模型、07 的验证、Human 当前指令和实际工作对象按当次需要读取；本文不复制或改写它们。

## 3. 职责边界

本文负责组织获批 WorkCase 的执行顺序、稳定检查点、授权消费和恢复分支；不负责判断语义相关性、替 Human 批准计划或关闭、定义状态/phase/字段、生成 after、创建其它事实对象类型规则、实现调度器、声称 spawn/subagent 能力存在，或把测试通过解释为 WorkCase 完成。AI 仍依据计划、依赖和当前事实选择下一个工作项；需要委派时只调用环境当次实际可用的能力。每次事实变更仍必须经 32 路由到 21 的 `update-workcase`、`close-workcase` 或 `correct-closed-workcase`；本文不提供平行写入入口。

## 4. 适用范围

当前 WorkCase 已精确读取、Gate 1 已经完成，并有当前冻结 `execution_authorization`、`baseline_fingerprint` 匹配该基线且 `source_refs` 可回指真实 Human 输入的 `execution_approval` 时，本文可在 `executing`、包内 `plan_revising`、Controller/独立结果复核、关闭准备和 Gate 2 等 21 允许的后续阶段组织执行与收敛。approval 的 `subject_version` 记录 Gate 1 当时版本；包内 PlanΔ 可以形成新的当前 `plan_version` 与 fresh current plan review，不要求或允许把 approval 改写成当前版本。Human 尚在审阅 Gate 1 材料、当前对象/指纹/授权包/批准不可确定，或工作实质是普通只读调查时，不使用执行分支。授权包逐项列明的事实对象创建、事实变更或本地 Git commit 仍分别由 31、32、30 承接，但不因此离开本模板的 WorkCase 执行组织或重复请求授权。模板候选、approval 字段存在或行动模板 key 都不单独代表适用、能力或授权覆盖。

## 5. WorkCase 获批计划执行行动模板定义

### 行动模板声明

| template_key | summary | definition_ref |
|---|---|---|
| `workcase-approved-plan-execution` | 组织已获 Gate 1 批准 WorkCase 的精确读取、授权消费、按真实检查点写回、包内调整、实施、阻塞/恢复、结果复核、Gate 2 与上下文恢复；不复制 21 状态机、不成为调度器也不声称 spawn 能力 | `workcase-approved-plan-execution-action-template::5. WorkCase 获批计划执行行动模板定义` |

### 5.1 输入与前置条件

执行者取得 Human 当前目标、当前 WorkCase 的完整回读与内容指纹、冻结 `execution_authorization`、`baseline_fingerprint` 和 Human `source_refs` 均准确的 `execution_approval`、当前 plan version 及 fresh current plan review、未完成 item 与依赖、适用规则和所需能力。执行前逐项核对授权包是否覆盖计划所需的文件/事实写入、对象变化、本地 commit、subagent/委派、独立结果复核、已知风险、允许副作用、禁止动作和超界收敛方式；Code 只校验 21 已定义的结构和绑定，不判断自然语言授权充分性。缓存、列表卡片、聊天记忆、旧摘要或已存在的模板候选都不能替代当前对象、授权包和批准读取。消费任何 item 前，AI 必须按 21 §4.3 复核其 goal、expected result、依赖与方法边界是否错误吸收 Controller 自检、独立结果复核、关闭准备、Human Gate 或其它 WorkCase 生命周期关口；这是一项语义检查，Code 不从关键词或字段形状替 AI 作出结论。需要跨对象共同生效时，仍按 32 的多对象能力边界停止，不把本模板当成调度、spawn 或原子能力。

### 5.2 执行与检查点

1. AI 先确定当前事项是否确实属于该获批计划及冻结授权包，以及其依赖和来源条件是否仍成立；并再次确认目标 item 是可实施并形成局部结果的工作，而非 21 §4.3 的生命周期关口或 Human Gate。不从 item 数组顺序、子任务返回或命令成功推定开始、授权或完成。
2. 若任一 item 错误吸收生命周期关口或 Human Gate，立即停止该 item 尚未发生的实施，不把它写成 `in_progress`、`blocked` 或伪完成。Controller 按 21 在 `plan_revising` 内形成移除或改写该 item 的包内候选计划，并完成 fresh current-plan 独立方案复核；调整没有改变 Gate 1 已批准的目标、scope、成功标准、授权动作、对象范围、副作用与风险上限时，保留当前批准的授权包并自动返回执行，不再次请求 Human。调整超出授权包时，不形成扩大计划或第三次 Gate，将受影响 item 据实取消并转入结果链。典型非法反例是 goal 为“全部实现完成后安排独立结果复核”的 item；独立结果复核必须在全部 item terminal 后由 phase 链承接。
3. 若工作存在跨稳定检查点推进、可能中断、委派、上下文压缩或恢复价值，在实质实施开始时形成完整 after：将目标 item 据实置为 `in_progress`，写已发生事实的 `current_summary` 与有界 `resume_from`，并使用 21 专属操作成功回读后再继续。授权包已逐项列明委派任务、输入、读写范围、允许影响和交还责任时，进入该步骤或切换到实际可用的 subagent/Reviewer 直接消费 Gate 1 授权，不重复确认；模板不选择平台、不创建调度器，也不证明环境具有 spawn 能力。不得预写未来工作或补造历史。
4. 只有局部结果确实在不需要持久化中间状态的同一稳定检查点形成时，才可按 21 的窄例外 `pending → completed`，写实际 `result_summary`；不得仅为规避开始检查点而使用该边。
5. 每个稳定中间结果、委派/交接、上下文压缩前和恢复后，更新并回读最近实际 `current_summary` / `resume_from`；整体跨 item 事实只有具有独立恢复价值时才进入顶层 summary。恢复只重新核对原 Gate 1 授权，不因上下文变化请求同一授权。
6. 普通可恢复的外部能力或依赖暂不可用时按 21 写合法 blocked 组合；阻塞解除后重新读取当前对象、依赖、授权包、批准和指纹，再按来源允许恢复。拒绝、CAS 冲突、能力缺口、不可读或未验证结果停在最后一个成功回读的检查点，不把计划写成事实。若继续所需动作未列明、范围或风险扩大、需要 push/PR/发布/外部消息等禁止副作用，或当前能力只能以超授权方式完成，则不进入 Human Gate、不扩大行动：保留已形成事实，据实取消受影响的未完成 item，并自动转入 Controller 结果检查。
7. 全部 item terminal 后按 21 自动进入 Controller 自检、完整结果投影、独立结果复核、Controller feedback 收敛、关闭提案和 Gate 2。独立结果复核及其必要 subagent/Reviewer 委派已由 Gate 1 授权包逐项列明时直接执行，不再确认；若实际独立能力暂不可用，只形成能力阻塞并等待或恢复，不让 Controller 冒充 Reviewer，也不请求 Human 放弃质量关口。Reviewer 结论、测试、工具成功和模板结束都不自动选择结果、推进 phase 或关闭 WorkCase；每个转换仍按 21、32 形成完整 after 并回读。

### 5.3 恢复与交还

新的、恢复的、压缩后或委派的上下文先取得规则引导；在目标明确需要时精确读取当前 WorkCase，而不恢复全部项目事实。交还应区分已回读的 item/status/phase/指纹、实际消费的 Gate 1 授权范围、完成/取消/阻塞、待从何处继续、已验证和未验证范围、超界后未执行的工作，以及是否已经到达唯一剩余的 Gate 2。本文不保存运行日志、receipt 或第二状态机。

## 6. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| 模板身份与边界 | 新建、修改或发现模板时 | 声明唯一、只组织执行、不复制 21/32 规则 | 06、21、32、本文 | 声明解析、来源回读 | 当前模板定义 | 修正来源，不消费模板 |
| item 与生命周期关口边界 | 计划获批后准备消费任一 item 时 | 每项都是可实施并形成局部结果的工作；没有 item 吸收 Controller 自检、独立结果复核、关闭准备或 Human Gate | 当前 WorkCase、21 §4.3、本文 | AI 逐 item 语义审核；契约测试只检查当前来源持续交付该边界 | 当次已读计划与来源文本；不证明 Code 能理解任意自然语言 | 停止受影响实施；包内移除或改写后 fresh current-plan review 并自动恢复，超包则取消受影响 item 并进入结果链，不再 Human 批准 |
| Gate 1 授权消费 | 每项行动、委派、事实写入和本地 commit 前 | 当前 `execution_authorization` 逐项覆盖准确对象、范围、副作用与风险，`execution_approval` 和来源回指有效；进入模板步骤、上下文恢复或切换执行者没有产生伪授权缺口 | 当前 WorkCase、21、30–32、Human Gate 1 来源 | AI 语义覆盖审核、21 结构/绑定校验和行动前回读 | 当次已读授权包与行动；Code 不证明自然语言授权充分，模板不证明 spawn 能力 | 未列明或超界行动不执行；取消/收敛受影响 item并进入结果链，不中途请求扩权 |
| 开始与直接完成边界 | 实施前后 | 跨检查点工作先真实回读 in_progress；同检查点结果才直接 completed | 当前 WorkCase、21、完整 after | WorkCase 转换测试与完整 after 回读 | 当次 item 转换 | 停在当前稳定检查点，重新判断 |
| 阻塞、恢复与阶段收敛 | 每个稳定检查点 | 合法 item/phase/authorization/approval/依赖形状与专属操作路由均成立；全部 item terminal 后自动进入 Controller、独立复核和关闭准备 | 21、32、Helper 回读 | 21 机械校验、Helper 回读 | 当次 WorkCase | 保持最后合法状态；可恢复能力阻塞等待条件，授权超界按结果链收敛，不新增 Human Gate |
| 接续与交还 | 压缩、委派或会话恢复时 | 可从当前事实恢复，未验证范围没有被掩盖 | 当前 WorkCase、交还内容 | 新上下文精确读取与交还审查 | 当前已读快照 | 更新当前摘要或保持未完成 |

## 7. Human Gate

本文不新增 Human Gate。当前 WorkCase 正常运行只消费 21 的 Gate 1 与 Gate 2：Gate 1 一次批准当前计划、`execution_authorization` 及其风险边界；Gate 2 判断最终关闭。Gate 1 后，授权包逐项列明的文件与事实写入、事实对象创建/变更、本地 commit、subagent/委派、独立方案复核和独立结果复核直接消费当前 `execution_approval` 与 Human 来源回指，不因进入模板步骤、切换执行者、上下文恢复或调用能力而重复确认。

Gate 1 不授权未列明行动、对象或影响，不授权范围/风险扩大，也不因一般实施授权扩张为 push、PR、发布、外部消息、破坏性历史操作或其它禁止副作用。执行中遇到这些情况时不得询问扩权；按 §5.2 取消或收敛受影响 item 后继续结果链。Human 主动撤回或改变目标仍按 21 处理，但正常模板不得主动制造第三次确认。

## 8. Stop Conditions

出现以下任一情况时停止受影响动作但不停止安全收敛：当前 WorkCase、指纹、授权包、批准或依赖不可确认；任一 item 吸收 Controller 自检、独立结果复核、关闭准备、Human Gate 或其它 WorkCase 生命周期关口；准备在实际开始前写入 `in_progress` 或在开始后补造它；以测试、子任务或模板步骤推定授权或完成；把 pending→completed 例外用于跨检查点工作；CAS 写后未回读；需要多对象共同生效但能力边界未满足；动作未列明、范围/风险扩大，或准备执行 push、PR、发布、外部消息等禁止副作用；准备以模板自动授权行动、实现调度/spawn 能力、让 Controller 冒充独立 Reviewer 或关闭 WorkCase。命中生命周期关口误建模时按 §5.2 在 `plan_revising` 中作包内修正并 fresh review 后自动恢复；超包与禁止动作零执行、取消或收敛受影响 item并进入结果链；其它恢复按 21、32 与 00 的当前规则进行。不得把任一 Stop Condition 转化为执行期追加 Human 授权请求。
