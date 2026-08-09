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

对 Human 而言，本文直接支持 HV2「授权执行受控可续」：Gate 1 已批准的对象、范围、风险和禁止动作在执行中保持为冻结基线，稳定检查点保存实际进展与接续入口，切换执行者或恢复上下文不重复索取同一授权。本文不承诺 AI 不犯错，也不把模板步骤、字段存在或回读成功解释为执行正确、结果完成或 Human 已验收。

## 2. 规范依据

本文直接依据 06 对模板选择和交还的共同边界、21 对 WorkCase 执行批准/phase/work item/关闭的唯一类型规则，以及 32 对活动期 WorkCase 专属 CAS 路由和完整 after 回读的共同变更边界。20、22、23、24 的类型条件、05 的事实模型、07 的验证、Human 当前指令和实际工作对象按当次需要读取；本文不复制或改写它们。

## 3. 职责边界

本文负责组织获批 WorkCase 的执行顺序、稳定检查点、授权消费和恢复分支；不负责判断语义相关性、替 Human 批准计划或关闭、定义状态/phase/字段、生成 after、创建其它事实对象类型规则、实现调度器、声称 spawn/subagent 能力存在，或把测试通过解释为 WorkCase 完成。AI 仍依据计划、依赖和当前事实选择下一个工作项；需要委派时只调用环境当次实际可用的能力。每次事实变更仍必须经 32 路由到 21 的 `update-workcase`、`close-workcase` 或 `correct-closed-workcase`；本文不提供平行写入入口。

## 4. 适用范围

当前 WorkCase 已精确读取、Gate 1 已经完成，并有当前冻结 `execution_authorization`、`baseline_fingerprint` 匹配该基线且 `source_refs` 可回指真实 Human 输入的 `execution_approval` 时，本文可在 `executing`、包内 `plan_revising`、Controller/独立结果复核、关闭准备和 Gate 2 等 21 允许的后续阶段组织执行与收敛。approval 的 `subject_version` 记录 Gate 1 当时版本；包内 PlanΔ 可以形成新的当前 `plan_version` 与 fresh current plan review，不要求或允许把 approval 改写成当前版本。Human 尚在审阅 Gate 1 材料、当前对象/指纹/授权包/批准不可确定，或工作实质是普通只读调查时，不使用执行分支。授权包逐项列明的事实对象创建、事实变更或本地 Git commit 仍分别由 31、32、30 承接，但不因此离开本模板的 WorkCase 执行组织或重复请求授权。模板候选、approval 字段存在或行动模板 key 都不单独代表适用、能力或授权覆盖。

**审核方法与保证边界**：本模板所引用的方案复核、结果复核及 Reviewer 第二视角，均遵循 21 §4.5。默认且保证更高的方法是实际委派只读 subagent；同一 AI 切换只读 Reviewer 视角不是 subagent、不是执行环境独立审核，也不得显示成与前者等价。Gate 1 后只有当前冻结 `execution_authorization.capability_limitations` 已覆盖当次 `plan_delta_review` 或 `result_review`、当次能力不可用证据仍然成立、保证差距已披露且停止条件评估为 `clear` 时，才可据实使用 `same-ai-switched-role-read-only`。Gate 1 前的 creation bootstrap 已由 21 的创建链承接，不由本获批计划模板补做、追认或改写。

## 5. WorkCase 获批计划执行行动模板定义

### 行动模板声明

| template_key | summary | definition_ref |
|---|---|---|
| `workcase-approved-plan-execution` | 组织已获 Gate 1 批准 WorkCase 的精确读取、授权消费、按真实检查点写回、包内调整、实施、阻塞/恢复、结果复核、Gate 2 与上下文恢复；不复制 21 状态机、不成为调度器也不声称 spawn 能力 | `workcase-approved-plan-execution-action-template::5. WorkCase 获批计划执行行动模板定义` |

### 5.1 前置精确读取

新的、恢复的、压缩后或委派的执行上下文先取得规则引导，再经 Helper 精确读取当前 WorkCase 的完整对象、`content_fingerprint` 和 `current_snapshot_projection`。执行者只消费 `resolution=resolved` 且 `source_content_fingerprint` 与本次读取内容指纹精确相同的投影；缺失、不匹配、stale 或 unresolved 时先重新精确读取，重复读取后仍不能形成 current 投影则只保留读取缺口，不猜测相邻位置、下一动作或交还话术。

执行者同时读取当前 plan、未完成 item 与依赖、fresh creation review、每项 review 据实记录的 `actual_method` 与条件性保证披露、冻结 `execution_authorization` 及其中实际存在的 capability limitations，以及 baseline fingerprint 和 Human `source_refs` 均准确的 `execution_approval`，逐项核对当前行动是否仍处于目标、影响、风险、能力与禁止项边界内。`status + phase` 是当前活动位置的事实，`status=blocked` 是覆盖层，closed 对象没有 phase；投影只是 21 基于刚回读快照形成的非持久派生合同。21 定义全部字段、phase、转换、quality gate 与投影语义，32 组织受控写回；本文不重述其闭集或成立条件。

### 5.2 执行循环

每次成功回读后，AI Controller 根据 Human 目标、当前事实、来源规则和冻结授权重新判断语义相关性、item 依赖、能力可用性、行动允许与实际完成情况。`next_required_control_step` 只指出结构上下一必经控制步骤，不自动选择 item、不解除 blocked、不证明能力或授权，也不允许 Code 推进 phase 或断言完成。

存在当前合法下一控制步骤时，Controller 继续消费已批准责任，不以聊天总结、工具成功、测试通过、子任务返回或 item 的 `current_summary` / `resume_from` 代替事实转换。item 的开始、直接完成、阻塞、解阻、完成、取消、计划返修、结果形成与质量链只按 21 的当前规则执行；需要跨对象共同生效时仍服从 32 的能力边界。

**Gate 1 后统一 pre-yield 控制点：** Gate 1 获批后，`plan_revising`、`executing`、`controller_checking`、`independent_reviewing` 与 `closure_preparing` 均处于同一条 Controller-owned 收敛链，`status=blocked` 仅作为任一合法活动 phase 上的覆盖层。每个稳定检查点、委派或交接、恢复以及每个结果链控制步骤，都必须先完成完整 after、CAS、精确回读与独立事实完整性审计；Controller 只消费 `resolution=resolved` 且 `source_content_fingerprint` 与刚回读 `content_fingerprint` 相同的 fresh projection。只要刚回读快照仍为 `status=open`、投影仍指向 Controller-owned 结构步骤且尚未形成 §5.4 的合法交还出口，Controller 就继续处理该步骤；AI 仍负责授权、依赖、能力、语义相关性和具体 item 的判断，Code 与 projection 不替 AI 作决定。

以下均只是统一控制点覆盖的中间里程碑，不是普通合法交还点：`plan_revising` 中形成 current plan 或 fresh creation review；`executing` 中 item 为 `in_progress`、单项进入 `completed` / `cancelled` 或全部 item terminal；`controller_checking` 中形成完整 canonical result projection；`independent_reviewing` 中 Reviewer 返回或 feedback 已处置；进入 `closure_preparing` 或形成完整 closure proposal。每个里程碑写回后仍须按 fresh fingerprint-matched projection 继续，直至真实 Gate 2、真实外部/能力 blocked、持续 exact-read unresolved 或 closed。

Gate 1 后出现新的 Human 决策需求，不构成 blocked 或 unresolved，也不得新增 Human Gate、写入 Human waiting 或请求第三次确认。若发生在 `executing`，停止未获授权动作，将受影响 item 及无法继续的依赖 item 据实记为 `cancelled`，保留已有结果、未执行范围与超界原因；全部 item terminal 后继续结果链。若在 items 已 terminal 后才发现，不重开或新增 item，而在结果、验证以及 closure proposal 的 residual decision 中据实记录未做/未验证范围并继续到 Gate 2。`cancelled` 不得写成 `completed`，也不自动决定 closure outcome；Controller 不得代替 Human 作出该 residual decision。

**单项终结控制点：** `item terminal ≠ WorkCase execution terminal`。任一 item 进入 `completed` 或 `cancelled` 并完成完整 after、CAS、精确回读与独立事实完整性审计后，刚回读且指纹匹配的 resolved projection 必须成为下一轮 Controller 输入；仍有非 terminal item 时，Controller 继续按当前授权、依赖和能力判断并消费可执行责任；全部 item terminal 时，则按 21 进入 `controller_checking` 并继续既有结果链。该控制点不表示 phase 一律返回 `executing`，也不授权 Code、Helper 或结构提示选择 item、推进 phase 或断言完成。

**开始控制点：** 跨检查点、可能中断或需恢复的工作项在实施前，必须先完成 `pending → in_progress` 写回，同事务写入非空 `current_summary` 与有界 `resume_from`，经 CAS、精确回读与独立事实完整性审计后，才允许执行实际行动。真实行动不得发生在 `in_progress` 写回之前。同一稳定检查点内可直接 `pending → completed` 的小动作不受此限，但不得用于跨检查点工作。

错误吸收生命周期关口或 Human Gate 的 item——例如 goal 为“全部实现完成后安排独立结果复核”——按 21 作基线内 PlanΔ 或据实取消；基线内修正保留当前批准的授权包并自动返回执行，不再次请求 Human，超界时将受影响 item 据实取消并转入结果链。Gate1 后才发现 success criterion 要求独立结果复核、feedback 处置、关闭提案或 Gate2 / Human 确认等未来关口证明自身——例如“独立结果复核确认本 WorkCase 未引入来源语义削弱”——时，冻结验收基线不得改写，也不重开或新增 item、增加递归复核或建立第三次 Human Gate；Controller 将该 criterion 据实写为 `not_verified`，在 validation 与 closure proposal 的 residual decision 中说明边界，并继续既有结果链至 Gate2。该判断由 AI 承担，Code 不从关键词或字段形状替 AI 作出结论。

### 5.3 稳定检查点

每个稳定中间结果、委派或交接、上下文压缩前后，以及每个结果链控制步骤，均以刚回读指纹为 CAS before，经 21 专属 Helper 操作写入完整 after，再精确回读受影响对象并执行当前来源定义的独立事实完整性审计。只有该链全部成功后，新指纹和投影才能成为下一轮输入；聊天内容、旧摘要和工具输出不是替代依据。检查点写回与 Git commit 粒度相互独立，不要求每次事实转换形成单独 commit。

全部 item terminal 后，Controller 按 21/32 连续形成 Controller 检查、完整结果投影、实际结果复核、feedback 处置、关闭提案与 Human 关闭确认。结果复核默认委派只读 subagent；只有冻结限制、当前证据、审核类别和停止条件共同允许时才可使用并如实记录低保证 fallback。Reviewer pass 只是一项实际 review 输入，不等于 Gate 2：Controller 不得跳过其反馈处置责任；需要修正或返工时按 21 返回 `controller_checking`，投影不变且 feedback 已处置时按 21 的合法边进入 `closure_preparing`。无论采用哪条 21 允许的边，都必须继续形成完整 after、CAS、精确回读与完整性审计，直至真实快照进入 Human 关闭确认；不能只输出聊天总结。

### 5.4 合法退出

本模板只允许在刚回读当前快照支持下退出当前执行循环：对象已经 closed；`status=blocked` 且已写入真实外部/能力阻塞与恢复条件；连续精确读取后投影仍 unresolved 而只能交还读取缺口；或 `status=open`、`phase=human_closure_confirming` 的 resolved 投影明确给出 `handoff_narrative_key=gate2_waiting` 与 `next_required_control_step=human_gate_2`。Gate 1 后其它 phase 不构成 Human 交还点。命中授权上限、禁止动作或能力只能超授权完成时，不询问扩权：零执行受影响动作，按 §5.2 与 21 据实取消受影响 item，或在 items 已 terminal 后写入结果、验证和 closure proposal residual decision，并继续结果链，直到前述合法退出之一真实形成。

普通 `in_progress` 检查点、单个 terminal item、pending item、全部 item terminal、完整结果投影、局部测试通过、一次本地 commit、Reviewer 返回或 feedback 处置、进入 `closure_preparing`、完整 closure proposal 或恢复入口存在，都不是完成出口。新 Human 决策需求同样不是 blocked/unresolved 出口。`status=blocked` 时投影保留生命周期位置只用于定位，Controller 不消费其中结构提示自动续跑；解除阻塞必须先按 21 写回并重新读取。

### 5.5 恢复交还

恢复与交还只能描述刚精确回读且指纹匹配的 `status + phase + current_snapshot_projection`，并区分实际完成、取消、阻塞、未执行、已验证、未验证和超界收敛范围。只有 resolved 投影的 `handoff_narrative_key=gate2_waiting` 才能表达“等待 Gate 2”“仅剩 Gate 2”或“关闭待确认”；`independent_reviewing`、`closure_preparing`、任何 blocked、stale 或 unresolved 快照均禁止这些结论。页面进展分组和结构上的下一必经动作同样由该投影派生，不以 AI 文案反向定义当前状态。

交还若发生在真实 blocked 或读取缺口，应说明最后成功回读的对象、phase、指纹、阻塞或缺口及恢复入口；若仍有合法下一控制步骤则回到 §5.2 继续，不把恢复说明本身当成停止信号。临时工件只按 06 §8.7 的最小共同边界处置和交还；本文不保存运行日志、receipt、续跑字段或第二状态机。

## 6. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| 模板身份与边界 | 新建、修改或发现模板时 | 声明唯一、只组织执行、不复制 21/32 规则 | 06、21、32、本文 | 声明解析、来源回读 | 当前模板定义 | 修正来源，不消费模板 |
| item、success criterion 与生命周期关口边界 | 计划获批后准备消费任一 item，以及形成 canonical result projection 前 | item 可实施并形成局部结果；criterion 可在 projection 形成前据实判断；两者均未吸收 Controller 自检、独立结果复核、feedback 处置、受控提交、关闭准备或 Human Gate | 当前 WorkCase、21 §4.3、本文 | AI 逐 item / criterion 语义审核；契约测试只检查当前来源持续交付该边界 | 当次已读计划与来源文本；不证明 Code 能理解任意自然语言 | Gate1 前返修；Gate1 后 item 按基线内 PlanΔ 或取消收敛，误建模 criterion 据实 `not_verified` 并经 validation、residual decision 与既有结果链继续到 Gate2；不新增 Human Gate |
| Gate 1 授权消费 | 每项行动、委派、事实写入和本地 commit 前 | 当前 `execution_authorization` 逐项覆盖准确对象、范围、副作用与风险，`execution_approval` 和来源回指有效；进入模板步骤、上下文恢复或切换执行者没有产生伪授权缺口；采用同一 AI fallback 时，冻结 limitation 覆盖当次类别且当前证据、保证差距与停止条件评估满足 21 | 当前 WorkCase、21、30–32、Human Gate 1 来源 | AI 语义覆盖与当前能力证据审核、21 结构/绑定校验和行动前回读 | 当次已读授权包、行动与实际 review 方法；Code 不证明自然语言授权充分、能力事实或 Reviewer 独立性 | 未列明或超界行动不执行；fallback 条件不成立时改用实际可用 subagent，否则停止当次 review；取消/收敛其它受影响 item 并进入结果链，不中途请求扩权 |
| 开始与直接完成边界 | 实施前后 | 跨检查点工作先按 §5.2 开始控制点完成 `pending → in_progress` 写回（含 `current_summary`、`resume_from`），再经 CAS、回读与完整性审计后才执行；同检查点结果才直接 `pending → completed` | 当前 WorkCase、21、完整 after | WorkCase 转换测试与完整 after 回读 | 当次 item 转换 | 停在当前稳定检查点，重新判断 |
| fresh 投影与执行循环 | 每次执行、恢复和事实写回后 | projection resolved 且 source fingerprint 匹配刚回读内容；AI 重新判断语义、依赖、授权和能力，Code 与结构提示不替代判断 | 当前 WorkCase、21、Helper 回读 | 指纹/投影负矩阵、source-contract 与 AI 对照审核 | 当次刚回读快照和结构提示；不证明 AI 跨会话遵从 | 重新精确读取；仍 unresolved 时只交还读取缺口，不猜测位置或行动 |
| 阻塞、稳定检查点与阶段收敛 | 每个稳定检查点 | 合法 item/phase/authorization/approval/依赖形状与专属操作路由均成立；每步有完整 after、CAS、精确回读和独立完整性审计；Reviewer pass 后继续至真实关闭确认位置 | 21、32、Helper 回读与完整性审计 | 21 机械校验、Helper 回读、全量事实完整性检查与 source-contract | 当次 WorkCase 写回链；不证明自然语言授权充分或结果正确 | 保持最后合法状态；blocked 等待真实恢复条件，授权超界按结果链收敛，不新增 Human Gate |
| 合法退出与恢复交还 | 稳定检查点、压缩、委派、会话恢复或关闭准备时 | 普通 executing 检查点不被当成完成出口；blocked、closed、重复读取后的缺口或真实 Human Gate 如实分流；只有 resolved `gate2_waiting` 使用 Gate 2 话术；临时工件服从 06 §8.7 | 当前 WorkCase、21、06、交还内容和实际路径观察 | 新上下文精确读取、投影负向检查、路径与 Working Tree 回读、交还审查 | 当前已读快照及本次实际检查的临时工件范围 | 继续消费合法下一步骤；保留既有、他项、归属不明或仍有恢复价值的工件，不把 Working Tree 非空写成未闭环 |

## 7. Human Gate

本文不新增 Human Gate。当前 WorkCase 正常运行只消费 21 的 Gate 1 与 Gate 2：Gate 1 一次批准当前计划、`execution_authorization` 及其风险边界，并在 capability limitation 实际存在时同时接受或拒绝其 Gate 1 后 fallback policy 与保证差距；Gate 2 判断最终关闭。Gate 1 后，授权包逐项列明的文件与事实写入、事实对象创建/变更、本地 commit、subagent/委派和实际方案/结果复核直接消费当前 `execution_approval` 与 Human 来源回指，不因进入模板步骤、切换执行者、上下文恢复或调用能力而重复确认；但冻结 fallback policy 不能替代每次 review 对当前能力证据和停止条件的重新判断。

Gate 1 不授权未列明行动、对象或影响，不授权范围/风险扩大，也不因一般实施授权扩张为 push、PR、发布、外部消息、破坏性历史操作或其它禁止副作用。执行中遇到这些情况时不得询问扩权；按 §5.2 取消或收敛受影响 item 后继续结果链。Human 主动撤回或改变目标仍按 21 处理，但正常模板不得主动制造第三次确认。

## 8. Stop Conditions

出现以下任一情况时停止受影响动作但不停止安全收敛：当前 WorkCase、指纹、授权包、批准或依赖不可确认；任一 item 或 success criterion 吸收 Controller 自检、结果复核、feedback 处置、受控提交、关闭准备、Human Gate 或其它 WorkCase 生命周期关口；准备在实际开始前写入 `in_progress` 或在开始后补造它；以测试、子任务或模板步骤推定授权或完成；把 pending→completed 例外用于跨检查点工作；CAS 写后未回读；需要多对象共同生效但能力边界未满足；动作未列明、范围/风险扩大，或准备执行 push、PR、发布、外部消息等禁止副作用；准备以模板自动授权行动、实现调度/spawn 能力、让 Controller 冒充 Reviewer 或关闭 WorkCase；实际 review 方法未知或被错误标成 subagent；同一 AI fallback 缺少冻结 limitation、当前证据、当次类别、相同 assurance gap 或清晰停止条件评估。命中生命周期关口误建模时按 §5.2 处理：Gate1 前返修；Gate1 后 item 在 `plan_revising` 中作包内修正并 fresh review 后自动恢复，超包 item 零执行、取消或收敛；Gate1 后误建模 criterion 不改写基线，而以 `not_verified`、validation 与 residual decision 沿既有结果链收敛。review 方法条件不成立时优先改用实际可用的只读 subagent，否则停止当次 review；其它恢复按 21、32 与 00 的当前规则进行。全程不得新增第三个 Human Gate，也不得把任一 Stop Condition 转化为执行期追加 Human 授权请求。
