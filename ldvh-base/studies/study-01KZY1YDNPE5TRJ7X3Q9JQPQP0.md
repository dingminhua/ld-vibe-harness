---
title: 规则精确读取三变体上下文合同评估方法试跑
status: active
report_kind: technical_assessment
research_question: 冻结的最小必要上下文合同与三变体盲评能否形成可执行且声明边界可靠的规则精确读取评估方法？
abstract: 完成了单一规则精确读取任务族的三任务九单元方法试跑。方法和隐私边界可以运行，但执行输出稳定性、样本规模与宿主递达证据不足，当前只能形成诊断性方法证据，不能形成因果效应或总体服务改善结论。
research_intent: 保存本次已完成方法试跑的输入边界、聚合结果、限制与分流，避免后续把运行证据基础、单次比例或输入引用误作 LDVH 已服务好 AI 的证据，并为是否值得以等价执行扩大样本提供稳定判断依据。
recommendation_summary: 保留三变体模块为方法原型；下一轮先统一模型和工具入口、机器化执行记录并增加重复样本。在此之前不接入日常合同检查，不建立健康分、遥测、Dashboard 或告警。
input_refs:
- kind: working_tree
  locator: ldvh-base/workcases/workcase-01KZXZPPZ6F9FSN83H4MAS8DE6.yaml
  observed_at: '2026-08-13T17:15:00Z'
- kind: working_tree
  locator: code/ldvh/testing/rule_read_contract.py
  observed_at: '2026-08-13T17:10:00Z'
- kind: working_tree
  locator: code/tests/testing/test_rule_read_contract.py
  observed_at: '2026-08-13T17:10:00Z'
- kind: generated
  locator: rule-read-contract:1f4fc351bbee0017133485fee614d5af1ef3ed12c95184ea4307a1ec7bbe16fe
  observed_at: '2026-08-13T17:00:00Z'
- kind: generated
  locator: WFPQDZ:3x3-aggregate
  observed_at: '2026-08-13T17:15:00Z'
relations:
- relation_key: inspired-by
  target:
    object_uid: 019ffb52-ebb5-74ea-a2f9-9f309e85d013
- relation_key: inspired-by
  target:
    object_uid: 019ffbfb-5be6-7a5f-9aa0-7125159435c6
change_log:
- signature:
    product_name: Cindy
    model_name: chatgpt/gpt-5.6-sol
    agent_runtime_name: claude-code
  at: '2026-08-13T17:15:30.864608Z'
  summary: 受控创建 technical_assessment：保存 WFPQDZ 三任务九单元方法试跑的聚合结果、证据层级、限制和后续分流；不保存 raw 交互。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: '2026-08-16T21:30:34.415045Z'
- at: '2026-08-17T13:05:52.121308Z'
  summary: 字段减法迁移：删除 action_relevance 字段（规范修订配套迁移）
  signature:
    product_name: WorkBuddy
    model_name:
    agent_runtime_name: codebuddy
object_uid: 019ffc1f-36b6-7175-891f-a3ba657b5ec0
object_id: study-01KZY1YDNPE5TRJ7X3Q9JQPQP0
fact_type_key: study
created_at: '2026-08-13T17:15:30.864608Z'
updated_at: '2026-08-17T13:05:52.121308Z'
---

## 研究问题

在单一规则精确读取任务族上，预先冻结最小必要上下文合同并进行完整交付、移除必要输入和增加无关输入三变体试跑，能否形成可重复、可盲评且声明边界清楚的服务质量评估方法？

## 输入与边界

评估输入为 `ldvh@WFPQDZ` 的获批计划、contract SHA-256 `1f4fc351bbee0017133485fee614d5af1ef3ed12c95184ea4307a1ec7bbe16fe`、三个冻结任务、26 项新模块测试、73 项复用边界回归，以及 3 个任务 × 3 个上下文变体的聚合结果。原始规则正文、执行提示和回答只进入身份绑定的受限临时根；提取聚合后，临时根经 realpath、类型和权限检查删除。本报告未获得宿主最终 Prompt 回执，因此 `host-received` 为 unavailable；执行输出由只读 subagent 产生，不等于真实目标宿主或模型群体的代表样本。

## 关键发现

- 新的三变体方法可以冻结合同、任务、rubric、来源 locator 和内容指纹，并把 condition key 与执行、评分载荷分离；聚焦与复用边界共 99 项测试通过，Ruff 通过。
- 九个执行单元按客观 rubric 汇总：完整合同 2/3、移除必要输入 1/3、增加无关输入 2/3。两名盲评者在一次明确的 R9 误读更正后，对最终九项 pass/fail 达成一致。
- 多个失败来自执行者没有严格遵守 JSON shape、hash 算法或 Helper CLI 入口要求；这说明当前协议可诊断“执行输出不稳定”，但样本太小且执行体不等价，不能把 2/3、1/3、2/3 的差异解释为必要输入有因果帮助或无关输入无害。
- `LDVH prepared` 与 `harness-delivered` 在本次 runner 边界内可观察；`host-received` 不可观察；`behavior-consistent` 只形成局部机制线索；`causal-effect` 未建立。不存在 LDVH 总体服务质量已经改善、统一健康分成立或应接入长期遥测的证据。

## 建议

保留当前模块作为方法原型，不把本次比例用于产品决策。下一轮如继续，应先消除执行载体差异：使用同一模型、同一工具入口、预注册的机器可校验返回协议，并增加重复样本；评分管线应直接消费机器记录而不是自然语言转述。只有在等价任务、稳定指纹、评分一致性和宿主证据边界成立时，才评估 required 缺失与 excluded 增加是否产生可重复且具有实际幅度的差异。

## 后续分流

- 当前结论保留为 Study；不更新或关闭上游 `ldvh@SFPVTZ`，其余任务族和长期治理仍保持 open。
- 新模块和测试由 `ldvh@WFPQDZ` 的结果链复核；本 Study 不替代 WorkCase Gate 2。
- 不创建统一健康分、长期遥测、Dashboard 或告警，也不修改 Helper、规则或行动模板。
- 若后续形成等价执行和足够样本的稳定信号，再由新的 WorkCase 承接复验；需要长期合同治理或产品化决定时再进入 ADR。
