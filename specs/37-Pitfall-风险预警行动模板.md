# Pitfall 风险预警行动模板

```yaml
ldvh_spec:
  spec_key: "pitfall-risk-warning-action-template"
  spec_id: "37"
  spec_kind: "spec"
  title: "Pitfall 风险预警行动模板"
  status: "active"
  canonical_path: "specs/37-Pitfall-风险预警行动模板.md"
  parent_spec: "action-template-foundation"
  relation: "refines"
  positioning: "定义 AI 在遇到失败症状、进入已知触发条件或准备采用高风险方案时，如何召回已有 Pitfall、判断经验适用性、评估规避策略并调整行动的可复用行动结构"
  scope: "适用于遇到异常/失败/报错、执行与已有经验相似的操作、调查修复故障时查阅 Pitfall 的场景；不定义 Pitfall 类型语义、字段、Schema、状态机或 Helper API"
  basis:
    - "action-template-foundation"
    - "pitfall-fact-type"
    - "fact-model-foundation"
  authorized_attachments: []
```

> 文件状态：`active`。本文只组织 23 已定义的 Pitfall 风险预警行动。模板存在不证明当前失败已验证、Pitfall 存在、经验适用或规避方法已获授权；它不以模板步骤替代 AI 对当次症状、根因、环境适用性或验证边界的判断。

## 1. 价值判断

AI 在长期项目中会反复遇到相似的失败模式——环境配置错误、工具链异常、验证遗漏、接口变更。这些经验若只留在聊天记忆中，会导致重复踩坑、重复调试和上下文断裂。Pitfall 为此提供一个已解决、已验证且可复用的失败机制记录。

本文的价值，是把"遇到症状→召回经验→判断适用→调整行动"这一重复场景组织成可复用结构，避免忽略已有经验、跳过环境适用性核对、或在不适用场景错误采用规避结论。

对 Human 而言，本文直接支持 HV5「据实判断」：已有经验在验证边界内提供决策参考，但不替代当次环境的实际验证。本文不承诺 AI 不犯错，也不把模板步骤、召回成功或经验匹配解释为根因已确认或规避方法已获授权。

## 2. 规范依据

本文直接依据：

1. `action-template-foundation`（06）：规定模板准入、共同结构、适用判断、步骤与交还共同边界；
2. `pitfall-fact-type`（23）：定义 Pitfall 的类型语义、字段、状态、创建条件与消费时机；
3. `fact-model-foundation`（05）：规定事实模型共同边界、候选发现与受控创建操作。

02、03、04、07、Human 当前指令和管辖项目规则按当次对象提供管辖、来源、服务与授权输入。本文只组织这些输入的消费，不另行定义或改变其规则。

## 3. 职责边界

本文负责定义：

1. Pitfall 风险预警场景的适用、排除与信息不足边界；
2. Pitfall 召回、症状匹配、经验适用性判断与行动调整的稳定流程；
3. 消费分支与 31（受控创建模板，WC 现场 draft）的组合边界；
4. 消费结果的验证、失败分流与交还。

本文不负责定义：

1. Pitfall 的类型语义、字段、Schema、合法初态、状态转换或关系约束——由 23 定义；
2. Pitfall 的受控创建执行、草案准备、身份分配、CAS 与回读——由 31 承接；
3. Pitfall 的生命周期变更、状态转换、promote/discard——由 32 承接；
4. 其它事实类型的语义与操作；
5. Helper CLI 的请求、响应或错误语义——由 04 定义。

23 是 Pitfall 类型唯一权威；05 定义共同事实边界；04 定义共同服务 envelope；AI 负责语义判断、适用与授权审核。本文不改变这组责任。

## 4. 适用范围

**本文是每个 LDVH 管辖会话的必查入口**——不依赖 AI 判断"当前是否遇到失败"。每个会话在动手前必须先查全部 active Pitfall 的 F2 候选卡，读取后判断哪些经验适用于当前任务。新会话开始、会话恢复或上下文压缩后，必须重新执行本检查步骤。

以下情况仍适用本文：任何涉及执行操作（编码、配置修改、部署、测试、故障排查），无论是否已确认症状与已知经验匹配。

全部 active Pitfall 均纳入 F2 候选召回。draft 和 discarded Pitfall 不进入 F2 候选（这是 Helper 层的技术约束，不是 AI 可据以跳过 active Pitfall 召回的理由）。

## 5. Pitfall 风险预警行动模板定义

### 行动模板声明

| template_key | summary | activation_hint | definition_ref |
|---|---|---|---|
| `pitfall-risk-warning` | 每个会话必查：召回全部 active Pitfall、判断经验适用性、评估规避策略、在对话中显式输出预警并调整行动；不定义 Pitfall 类型规则 | 每个 LDVH 管辖会话必须先读取全部 active Pitfall 的 F2 候选卡；命中时在对话中输出踩坑预警并据此调整行动。 | `pitfall-risk-warning-action-template::5. Pitfall 风险预警行动模板定义` |

### 5.1 行动步骤与分支

#### A. 全量召回（强制前置，不判断是否需要）

每个 LDVH 管辖会话必须先执行 B 步骤（不判断"是否需要检查"）。B 步骤是强制前置——全部 active Pitfall 通过 Helper F2 候选发现取得，AI 读完后再判断哪些经验适用于当前任务。

#### B. F2 候选发现与初步匹配

1. 经 Helper `find-fact-object-candidates`（card_layer=F2, fact_type_keys=["pitfall"]）发现**全部** active Pitfall 候选；
2. 按 23 定义的 F2 投影字段评估：object_uid, object_id, title, status, symptoms, trigger_conditions, scope_of_impact, applicability, validation_summary, updated_at；
3. 按症状、触发条件、环境、版本或 applicability 与当前情形的可能相容性缩小候选范围；
4. 默认候选只包含 active Pitfall；draft 和 discarded 不进入普通经验召回；
5. Helper 在 F2 卡附加 `trigger_reason`、`matched_fields` 与 `anchor_type`：`anchor_type` 为 `observed_symptom` 时表示失败已发生、经验可直接参考；为 `potential_risk` 时表示即将执行有风险的操作、需评估当前情形是否落入触发条件。若 `anchor_type` 为空（仅非触发字段命中），则不触发经验消费，保留为参考但不调整行动。

#### C. F3 展开与经验核对

1. 对相容候选展开 F3 完整对象；
2. 逐项核对：symptoms 是否与当前失败匹配、trigger_conditions 是否命中、root cause 判断是否与当前症状相容、resolution 和 avoidance 是否适用于当前环境、validation summary 的验证边界是否覆盖当前情形；
3. 重新核对对象实际记录的环境、版本或观察时点与当前环境的差异；
4. 确认 recall 不等于根因证明——对象被召回只表示经验候选相容，不表示根因已在当次重现。

#### D. 适用性评估与行动调整

1. **经验适用**：当前症状、环境、版本与 Pitfall 声明范围相容时，评估 avoidance 和 resolution 的适用前提、成功信号及不命中边界；将规避策略整合到当前行动计划中；
2. **经验部分适用**：当前情形与经验有交集但环境/版本/根因不完全匹配时，提取可参考的判断框架，明确不适用范围，不直接采用规避结论；
3. **经验不适用**：症状不匹配或环境已变化时，保留该经验为参考但不调整当前行动；
4. **需要新经验**：当前失败是全新机制或已有经验均不覆盖时，判断是否应在当前行动解决后创建新 Pitfall（走 31 的 fact-object-controlled-creation）；
5. **WC 执行中 draft**：仅在 23 §6 的 WC 现场保留边界内——失败确在 WC 推进中实际发生、已解决和验证、draft 满足全部准入——才可由执行者创建 draft Pitfall。

D.1 **风险预警声明输出**。当某个 Pitfall 在本次会话中首次被判定为适用时（经验适用或部分适用），AI 必须在对话中显式输出该预警，格式如下：
   > **⚠️ 踩坑经验命中**：检测到相关踩坑经验 [Pitfall title]。
   > 已知症状：[symptoms 简述]。
   > 建议规避：[avoidance 简述]。
   > 验证环境：[validation_summary 简述]。
   > 当前行动将据此调整。

   当某个 Pitfall 首次被检查但判定为不适用时，也应简要说明：
   > **📋 风险检查**：[Pitfall title] 不适用于当前情境，原因：[简述]。

   此预警的作用：让 Human 看到 AI 确实在查阅踩坑经验并据此调整行动，而非重复已知错误。预警后若实际行为违反 avoidance，Human 可直接审计。

#### E. 形成实际结果与交还

1. 分别记录：召回触发原因、候选匹配结果、经验核对结论、适用性评估、行动调整（或不调整）；
2. 适用时，交还规避策略要点与当前行动计划的调整说明；
3. 不适用时，交还不适用原因与替代方案；
4. 建议新建 Pitfall 时，交还新建依据并转入 31。

## 6. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| F2 全量召回已执行 | 每个会话开始/恢复时 | 全部 active Pitfall 的 F2 候选卡已被 Helper 取得；不判断"是否需要召回"，本步骤为强制前置 | Helper 调用结果与候选数量 | F2 召回调用 | 当次已读全部 active Pitfall 候选 | 未召回全部时不得进入后续步骤或声明风险检查已完成 |
| F2 候选匹配 | 候选发现后 | 至少一个 active 候选的症状/触发/applicability 与当前可能相容 | Helper 候选结果与 AI 语义比较 | 候选走查与字段核对 | 当次候选集 | 无相容候选时交还无已知经验 |
| F3 经验核对 | 展开完整对象后 | symptoms/trigger/root cause/resolution/avoidance/applicability 与当前逐项核对 | 完整对象回读与 AI 语义审核 | 完整对象回读与环境核对 | 当次已展开对象与环境 | 不直接采用未核对的规避结论 |
| 环境适用性 | 采用规避策略前 | 当前环境/版本与 Pitfall 记录的验证边界相容 | 对象自有字段与当前环境对照 | 环境版本核对与 AI 适用判断 | 当次已核对的环境范围 | 缩小适用范围或重新验证 |
| 回读与审计 | 消费后建议创建时 | 按 31 的 C.7 执行精确回读与 check-fact-integrity | Helper 创建与读取结果 | 创建调用与完整性审计 | 当次创建范围 | 不声明创建成功 |



| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| F2 全量召回已执行 | 每个会话开始/恢复时 | 全部 active Pitfall 的 F2 候选卡已被 Helper 取得；不判断"是否需要召回"，本步骤为强制前置 | Helper 调用结果与候选数量 | F2 召回调用 | 当次已读全部 active Pitfall 候选 | 未召回全部时不得进入后续步骤或声明风险检查已完成 |
| F2 候选匹配 | 候选发现后 | 至少一个 active 候选的症状/触发/applicability 与当前可能相容 | Helper 候选结果与 AI 语义比较 | 无相容候选时交还"无已知经验"  | | |
| F3 经验核对 | 展开完整对象后 | symptoms/trigger/root cause/resolution/avoidance/applicability 与当前逐项核对 | 完整对象回读与 AI 语义审核 | 不直接采用未核对的规避结论  | | |
| 环境适用性 | 采用规避策略前 | 当前环境/版本与 Pitfall 记录的验证边界相容 | 对象自有字段与当前环境对照 | 缩小适用范围或重新验证  | | |
| 回读与审计 | 消费后建议创建时 | 按 31 的 C.7 执行精确回读与 check-fact-integrity | Helper 创建与读取结果 | 不声明创建成功  | | |

## 7. Human Gate

本文不新增统一 Human Gate。Pitfall 消费通常不需要额外 Human Gate——AI 基于症状匹配和环境适用性判断即可调整行动。但以下情况需 Human 决定：

1. 采用的规避策略涉及高影响或不可逆行动时；
2. 经验适用性判断存在不确定性，需要 Human 接受来源冲突或未覆盖风险时；
3. 判断需要新创建 Pitfall 但 Human 尚未确认经验值得保留时。

WC 执行中创建 draft Pitfall 的授权由 23 §6 和当前 `execution_authorization` 承接。

## 8. Stop Conditions

出现以下任一情况时，暂停 Pitfall 消费或经验采用：

1. 症状不明确或无法描述，却准备宣称命中已有经验；
2. draft 或 discarded Pitfall 被当作已确认规避经验采用；
3. 未核对当前环境、版本与 Pitfall 验证边界，却准备采用规避结论；
4. 根因判断与当前症状不相容，却准备沿用 resolution；
5. 验证边界被扩大到 Pitfall 未覆盖的环境或版本；
6. 召回被当作根因证明或行动授权；
7. 准备用普通文件能力直接写入 `ldvh-base/`，或未经 Helper 受控创建与回读；
8. WC 执行中创建 draft 但未满足 23 §6 的现场保留边界；
9. 采用的规避策略超出当前 Human 授权范围；
10. 将经验的存在解释为外部环境仍与验证时相同。

暂停期间允许的行动与恢复按 00 §11 执行。
