# 执行期事实同步纪律修订材料

- WorkCase: workcase-01M00MNGVFFXW8AZG29T1JPRYN（plan_version=1）
- 来源 Spark: spark-01M00KTB0WEWDSY8N78KZS9SHQ
- Gate 1 批准：Human 于本会话批准 plan_version=1，含两处 specs/34 修订全文与完整 execution authorization baseline（baseline_fingerprint `76703b47cfd57c28b7c5cf0c862d9da014b17f3ceddd0a589311199d77f23729`）
- 修订对象：specs/34-WorkCase获批计划执行行动模板.md

## 1. Spark 四失败点 × 现行条文覆盖对照表

| # | Spark 记录失败点 | 现行覆盖条文 | 判断 |
|---|---|---|---|
| 1 | 4 个 work items 实施完成但 item status 未写回 | specs/34 §5.2 开始控制点（跨检查点工作须先 pending→in_progress 写回，真实行动不得发生在写回之前）；§5.2 单项终结控制点；§6 验证表「开始与直接完成边界」行 | 规则已覆盖，属执行违反 |
| 2 | 独立结果复核结论只留会话上下文，未写入 result_review | specs/34 §5.2 统一 pre-yield 控制点（Reviewer 返回是里程碑非完成出口，须继续事实写回至真实关闭确认）；§5.3 第三段「只有该链全部成功后，新指纹和投影才能成为下一轮输入」 | 规则已覆盖，属执行违反 |
| 3 | 一次 update-workcase 失败被静默跳过，未读 gaps 修复重试 | specs/34 §5.3 只要求「链全部成功」；§5.4 只定义四类合法退出；§8 Stop Conditions 仅含「CAS 写后未回读」；全文无「受控写入调用返回非成功结果」的显式处置条文 | **真实缺口 A：修订 1 承接** |
| 4 | 未回读事实源即宣称「处于 Gate 2」，且跨执行环境续接时 Stop gate 无绑定 fail-open | 阶段宣称话术已由 specs/34 §5.5 覆盖（仅 resolved gate2_waiting 投影可用 Gate2 话术）；但 Stop gate 机械阻断依赖 09 §5.8 的会话精确绑定，跨执行环境续接时绑定不存在 → fail-open 放行，机械纠正不可达 | 话术规则已覆盖（执行违反）；**机械阻断缺口 B：修订 2 承接** |

## 2. 修订前原文快照（回滚基线）

### §5.3 稳定检查点（修订前，全文）

> ### 5.3 稳定检查点
>
> 每个稳定中间结果、委派或交接、上下文压缩前后，以及每个结果链控制步骤，均以刚回读指纹为 CAS before，经 21 专属 Helper 操作写入完整 after，再精确回读受影响对象并执行当前来源定义的独立事实完整性审计。只有该链全部成功后，新指纹和投影才能成为下一轮输入；聊天内容、旧摘要和工具输出不是替代依据。检查点写回与 Git commit 粒度相互独立，不要求每次事实转换形成单独 commit。
>
> 终止善后中的每个稳定检查点同样先写完整 after、CAS、回读与完整性审计。检查点必须区分 retained、discarded、unverified 与 relationship impacts，并据实更新 cleanup summary/status；未执行的删除、回滚、验证或复核不得写成已完成。complete 前还要再次核对入向 `depends-on`，并以 criterion results 决定实际 closure outcome，而不是以 Human 要求中止推定结果分类。
>
> 全部 item terminal 后，Controller 连续形成自检、结果投影、结果复核、反馈处置、关闭提案与 Gate 2。结果复核先实际创建只读 Subagent；无法创建时，Controller 向 Human 披露保证差距后直接使用 same-AI 只读视角，并完整记录能力证据与披露。

### §5.5 恢复交还首段（修订前）

> 恢复与交还只能描述刚精确回读且指纹匹配的 `status + phase + current_snapshot_projection`，并区分实际完成、取消、阻塞、未执行、已验证、未验证和超界收敛范围。只有 resolved 投影的 `handoff_narrative_key=gate2_waiting` 才能表达“等待 Gate 2”“仅剩 Gate 2”或“关闭待确认”；`independent_reviewing`、`closure_preparing`、任何 blocked、stale 或 unresolved 快照均禁止这些结论。页面进展分组和结构上的下一必经动作同样由该投影派生，不以 AI 文案反向定义当前状态。

## 3. 批准修订文本逐字快照（Gate 1 呈现并获批的精确文本）

### 修订 1：§5.3「稳定检查点」末新增段落

受控写入调用的失败处置：任一 21 专属 Helper 写入操作返回 `invalid_request`、`rejected`、`unavailable` 或其它非成功外层结果时，Controller 必须当场读取该响应的 `gaps` 与 `diagnostics`，修正请求形状、指纹或内容后重试；无法修复、连续失败或写入结果不可观察时，停在最后合法状态，按 §5.4 只经真实 blocked 或读取缺口交还。不得静默跳过失败的写入并继续后续控制步骤、形成成功声明或任何 phase/status 宣称。修复与重试受 Gate1 冻结的 `allowed_adjustments` 约束，不构成扩权。

### 修订 2：§5.5「恢复交还」首段之后新增段落

续接绑定要求：跨执行环境、新会话或上下文恢复后继续消费当前 WorkCase 时，Controller 在首次精确回读后，应在宿主会话标识可观察且项目 Stop gate 已按 09 §5.8 部署时，按 09 §5.8 绑定形状为当前会话主动建立 Stop gate 精确绑定（`LDVH_WORKCASE_STOP_BINDING` 或 `.ldvh-stop-bindings/<session_id>.json`）；绑定不可建立、形状不满足或宿主不支持时如实记录该缺口，不伪造绑定、不按候选特征猜测，也不为此新增 Human 确认。本要求不改变 09 §5.8 的 fail-open 与禁止猜测设计。

## 4. specs/09 不修改的依据

09 §5.8 的 Stop gate 绑定判定采用三条安全设计：(1) 只对环境变量 `LDVH_WORKCASE_STOP_BINDING` 或 `.ldvh-stop-bindings/<session_id>.json` 精确绑定的当前 WorkCase 生效；(2) 无绑定或任何异常一律 fail-open 放行；(3) 明文禁止按唯一 open WorkCase 候选特征猜测绑定。这三条共同防止把 Stop gate 错误施加到未绑定的会话（误阻断），是防误绑的安全边界，不是缺口。

跨执行环境续接（WorkCase 由运行时 A 创建、运行时 B 执行）时绑定缺失导致的 fail-open，正确解法是让续接方 Controller 在续接时**主动建立精确绑定**（知道自己的 session 标识、知道正在消费的 WorkCase），而不是让 Stop gate 放宽判定或开始猜测。前者把责任放在有充分信息的执行方，后者把风险推给无信息的拦截方。因此修订落在 specs/34（执行行动模板，Controller 的行为规范），specs/09 保持零修改。

## 5. 边界

- 本材料文件是 workcase-01M00MNGVFFXW8AZG29T1JPRYN 的 item-material 交付物，不构成规范正文。
- 回滚方式：删除本文件；specs/34 修订按第 2 节原文快照精确恢复。
