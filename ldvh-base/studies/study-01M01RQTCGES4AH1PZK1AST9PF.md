---
title: WC-A/B/C 完成后的 Helper 证据与事实库后续分流审计
status: active
report_kind: internal_audit
research_question: 在 WC-A、WC-B、WC-C 已分别完成 CLI 机械辅助、WorkCase strict item_event 与固定模型 2×2 对照后，当前 35 份 Study、82 个 Spark 和 124 个 closed WorkCase 中，哪些后续问题仍具有独立、可行动或需条件触发的研究价值，哪些已完成、被否定或已由更窄对象承接，以及如何形成不重复既有通用价值审计、也不越过 Human Gate 的后续分流基线？
abstract: 本内部审计在 2026-08-15 当前 Working Tree 全量通读 35 份 Study 与 82 个 Spark，并对 124 个 closed WorkCase 的 outcome、criterion、residual、route、suggestion 与 validation 线索做结构化扫描和命中深读。当前事实池为 Study 24 active/11 retired、Spark 6 open/60 implemented/16 discarded、WorkCase 124 closed/0 open。WC-A 已交付 --request/--example/--fields 与署名/footer 骨架；WC-B 的 strict item_event 将窄任务 raw request 平均减少 1935.75 bytes，但不替代通用 prepare-update；WC-C 的 40-session 固定模型配对结果显示 Phase 1 invalid_request 降低但 Helper command chars 增加 151.1/session、direct calls 不变，残差只达到 behavior-consistent 的 significant。审计将后续收敛为四层：P1 知识预检与服务质量复验；P2 prepare-update/CAS 与证据驱动的读写契约候选，FileAsset 完整退出已由后继 WorkCase 完成而不再构成 residual；P3 67 项 direct-basis 语义复核与窄测试债；真实需求触发的跨项目、平台、外部工具与 Phase3/09 判断。报告不创建实现授权，不把 host-received 不可观察或 significant 推导成 MCP 必要性。
research_intent: Human 在 WC-A/B/C 连续完成后要求通读全部 Study、Spark，并从 WorkCase 中提取仍有价值的残留问题，建立一个后续工作依据。项目已有通用过度设计、根规范兑现度和周期价值审计，但没有一份以这三项新结果为观察断点、对完整当前事实池做去重并把旧推荐重分类为已完成/可判断/证据门槛/触发门槛的窄报告。若不形成该报告，后续会重复读取 117 个 Study/Spark、把 terminal 历史误当 backlog，或把 WC-C narrow residual 越界为 Phase3 授权。
recommendation_summary: P1：以 open Spark「ADR、Pitfall 与 Study 的作用强化」和「LDVH 面向 AI 的服务质量评估」为既有承载，先做真实任务中的知识预检/复用效用与 WC-C 证据复验，不新建重复 Spark。P2：将「受控写入优化」校正为 WC-A 已完成署名/footer 机械骨架后仍待证据判断的 prepare-update/CAS；P2-2 统一成功信号仅在出现第二个独立 duplicate-create/解析失败样本时立项；FileAsset 早期 Gate 1 漏项已由后继完整范围 WorkCase 吸收并完成，不再立项。P3：按既有 Study 建议逐项复核 67 项 direct-basis 必要性，并只在真实触发下补 projection-table source-contract、fixture source identity、termination race/Web propagation 或 F1 delta。普通实现是否强制进入 approved WorkCase、条款日落及其它平台/MCP 方向由 Human 单独决定，不进入当前实现。
input_refs:
- kind: specification
  locator: specs/00-理念与构成.md（根规则 §8.1/§8.2）；specs/24-Study-研究报告.md（全文）；specs/31-事实对象判定与受控创建行动模板.md §5
  version: 1735ca5f606581944099105abc096fd3cfbf6953
  observed_at: '2026-08-15T03:37:07Z'
- kind: fact-objects
  locator: ldvh-base/studies/*.md 全量 35/35（lexicographic slices [0,18)+[18,35) 逐文件读取）；ldvh-base/sparks/*.yaml 全量 82/82（[0,41)+[41,82) 逐文件读取）；ldvh-base/workcases/*.yaml 全量 124 的 closure/result/residual/suggestion/route/validation 结构化扫描及命中深读；F3 深读 6 个 open Spark、study-01M014CFAVEZBBDYQ49G2XQ6NB、study-01KZZRT5G8FVQT183G0WYRS45A、study-01KZXN5TXNF7SBYR5AYF73SGTT、WC-A/B/C、workcase-01M016QVCXFM7ST88N6YKMJZPN 与 FileAsset 前后继 WorkCase
  version: 1735ca5f606581944099105abc096fd3cfbf6953
  observed_at: '2026-08-15T03:37:07Z'
- kind: helper-call-results
  locator: 本会话 find-fact-object-candidates F1/F2：Study 24 active/11 retired、Spark 6 open/60 implemented/16 discarded、WorkCase 124 closed，object_set_fingerprint=ae39a9ac16163acb8bdf0d351459fce0326b339482554eb92dc6a1056bddd449；残差/全量/后续/Helper/MCP 候选查重；ldvh check status=passed 并保留 2 类 gaps；check-fact-integrity complete/256/0
  observed_at: '2026-08-15T03:37:07Z'
- kind: working-tree-statistics
  locator: 当前 Working Tree 审计：WC-A/WC-B/WC-C 新事实与代码/规范改动未提交；docs/metrics/wc-c-* 为 docs/ ignore 下工作产物；spark-01KZXN5TXNEW3BMN9RWYY9P769.yaml 与 spark-01M004VQ0CE76R0VXNNJSPTW2Q.yaml 为审计前已有修改，按当前内容读取且未由本审计改写
  observed_at: '2026-08-15T03:37:07Z'
relations:
- relation_key: inspired-by
  target:
    object_uid: 01a00342-b1a9-7814-9827-8ac7b11fbd74
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-74e8-aac0-3cd3d73d15fc
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-74ea-a2f9-9f309e85d013
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-75f4-888d-2d7c6df0e8e2
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-7706-ba55-38e7bc9b1cc9
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-78ee-91ba-bcfad658463e
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-7ea7-8303-b58b6d99eccd
action_relevance: 评估 WC 完成后的证据与事实库分流策略时，确认后续责任已按类型归口到正确对象，不遗留未承接的审计发现
change_log:
- signature:
    product_name: DeepSeek Harness
    model_name: gpt-5.6-sol
    agent_runtime_name: deepseek-harness
  at: '2026-08-15T03:51:35.016614Z'
  summary: 受控创建本 internal_audit Study：完成 WC-A/B/C 后 35 Study、82 Spark 与 124 closed WorkCase residual 全库审计、查重与后续分流；经两轮 fresh native subagent creation review，修正 FileAsset 后继完成事实并补齐建议验收边界。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
object_uid: 01a0038b-e990-7648-a886-df98559d26cf
object_id: study-01M01RQTCGES4AH1PZK1AST9PF
fact_type_key: study
created_at: '2026-08-15T03:51:35.016614Z'
updated_at: '2026-08-16T21:42:45.620720Z'
---

## 研究问题

### 审计问题

WC-A/B/C 改变了 Helper 交互与证据基线后，完整当前事实池中哪些后续问题仍值得承接，应该进入既有 Spark、形成新 WorkCase、等待新证据，还是明确不启动？

### 与既有审计的区分

本报告不是第四份 LDVH 通用价值或过度设计评估。既有 study-0022、study-0023 与 v4.1.0 根规范评估继续承载总体设计/兑现度；open「LDVH 价值审计」继续承载周期 retain/simplify/replace/exit 判断。本报告只审计 2026-08-15 WC-A/B/C 后的事实池与 Helper 后续分流。

## 输入与边界

### 覆盖与方法

- 以 lexicographic basename 无重叠分片逐文件读取 35/35 Study 与 82/82 Spark；状态总数与 F1 manifest 交叉核对。
- 对 124/124 closed WorkCase 扫描 closure outcome、not_satisfied/not_verified、residual responsibilities、routes、spark suggestions 与 validation unknowns；深读命中项及 WC-A/B/C、65-session baseline 链。WorkCase 不是逐个写历史摘要，只有当前仍有价值且未被后继事实吸收的 residual 进入发现。
- 以 F2「残差、全量、后续、Helper、MCP」召回做查重；F3 深读六个 open Spark、65-session Study/WorkCase、WC-A/B/C、两份相邻通用审计和当前 gap 来源。
- 所有结论基于 HEAD `1735ca5f606581944099105abc096fd3cfbf6953` 加观察时 Working Tree。两份审计前已存在的 Spark diff 均按 Working Tree 当前内容计入对象状态与语义：其中 `spark-01M004VQ0CE76R0VXNNJSPTW2Q` 已由 open 变为 implemented，`spark-01KZXN5TXNEW3BMN9RWYY9P769` 仍为 open 且摘要已更新；本审计未改写二者。因两项均未提交，HEAD 单独不能重建该状态快照。

### 排除与声明边界

不重开 11 个 retired Study、60 个 implemented Spark、16 个 discarded Spark 或已由后继 WorkCase 完成的旧 residual。历史 external Study 的 source currentness 不在本轮重查。未执行新的外部研究、跨环境真实事件、Web 运行、Windows 复验或 Git commit。WC-C 只证明固定任务包中的 harness-delivered/behavior-consistent paired estimate；host-received 仍 unavailable，broad causal-effect、MCP 必要性和 09 修订授权均未成立。

## 关键发现

### 事实池已从广泛议题收敛为六个 open Spark

当前 35 Study 为 24 active/11 retired；82 Spark 为 6 open/60 implemented/16 discarded；124 WorkCase 全部 closed。六个 open Spark 分别是知识预检、AI 服务质量、Helper 只读交互、受控写入、多项目聚合和 LDVH 价值审计。大量 active Study 保存条件性方向或历史评估，并不等于 24 项当前 backlog。

### WC-A/B/C 完成了原 Phase 1 与 WorkCase 专属减负，但没有消灭全部结构摩擦

WC-A 已交付 --request、--example、--fields 以及三字段 null 骨架/Git trailer 排列；因此受控写入 Spark 的「署名/footer 第一层机械帮助」已经有稳定承接，旧摘要将其写为 remaining 已被后续事实推进。WC-B 的 strict item_event 是 update-workcase 专属闭集事件输入，不是 generic patch，也不等于 Study 原 P2-1 prepare-update/CAS。WC-C 40/40 comparable、0 state-changing calls：Phase 1 invalid_request hits 22→0，但 heredoc 两组均为 0、direct Helper calls 差 0、Helper command chars +151.1/session；Phase 2 item_event raw request bytes -1935.75，validity 未显著改善。由此 significant 只表示窄任务结构残差，支持继续判断，不直接支持 Phase3。

### Helper 后续应先补一体化与真实任务证据，而不是继续增加孤立 flags

Study 的 P2-1 仍有独立语义：一次 prepare-update 候选应绑定当前对象、fingerprint、排除托管字段的 after skeleton 与 stale/no-op 边界，目标是把真实 CAS 往返由 3–4 次降至 2 次。WC-B 只覆盖 WorkCase item transition，未覆盖 Study/Spark/ADR/Pitfall 或 WorkCase 非 item 字段。P2-2 固定成功字段虽然仍与 create/update 现有异形 result 有差距，但原 Study 已冻结第二独立 duplicate-create 或诊断需求门槛；本轮没有新独立样本，不能直接立项。只读优化同样只在具体 operation 出现实证过量时启动，不能 blanket trim。

### 知识复用与服务质量是两个 P1，但需要同一证据纪律

全量通读本身显示：对象多不等于积累效用可见，执行者若只能全库重读会产生新的上下文成本。知识 Spark 已给出 ADR Review/Pitfall Scan/Study Review 三段预检；下一步应评估候选命中、F3 适用判断、coverage、首次合法行动与避免重复研究，而不是把「已读」当作「理解」。服务质量 Spark 已具 session comparability，WC-C 又提供一轮平衡 replay；下一轮应转向代表性真实任务与跨模型/宿主可推广边界，仍分开 prepared/delivered/received/behavior/causal。

### WorkCase residual 中有一类可直接承接债、四类条件债，并有一项已被后继事实吸收

可直接承接债：67 项 direct basis 可经其它路径到达，既有根规范 Study 已建议 P3 逐项语义复核。条件债：WorkCase projection table→Python source-contract test 要在真实 inline-code grammar 下新 Gate；FactSchema fixture source identity 只在测试仓库与 imported package 可分离时启动；termination inbound-race/Web propagation 等待 operation-specific branch 或稳定 real-Helper fixture；F1 per-object delta 等待可比较的跨会话定位成本。已吸收项：早期 FileAsset 退役 WorkCase 因 Gate 1 漏四个消费者而取消，但后继完整范围 WorkCase 已纳入遗漏消费者并满足全部退役标准，当前产品面已完整退出 FileAsset；该历史只作为「旧 residual 已由后继事实吸收」的样本，不再形成 WorkCase。

### 其余方向保持触发式或 Human-only，而非当前路线

多项目聚合在单项目隔离仍充分时只是 P2 future direction；Windows 声明、跨平台再验证、并行/team orchestration、agent-skills pilot、外部 code index/Obsidian 和产品级演进均已有独立输入或否定边界。普通实现是否必须进入 approved WorkCase、还是接受 advisory 约束加事后审计，以及规范条款日落，属于 Human 治理选择。只有出现各自真实需求、平台变化或 Human 决定时再进入 Study/ADR/WorkCase；不把本报告变成全项目实施总表。

## 建议

### P1：更新既有知识预检与服务质量 Spark，先验证知识被使用以及 Helper 改动是否产生实际服务价值

目标对象类型为两个既有 open Spark：「ADR、Pitfall 与 Study 的作用强化及触发事件」和「LDVH 面向 AI 的服务质量评估与持续改进」，不创建第七个重复 Spark。预期目标是用真实但只读或可回放任务判断 F2→F3 预检能否提高候选命中后的适用判断质量、减少重复研究或错误选择，并复验 WC-C 结果能否跨代表性任务维持。验收条件至少包括：预注册任务族、固定模型/入口与 exclusion；分别报告 prepared、harness-delivered、host-received、behavior-consistent 和 causal-effect 层级；记录候选命中、F3 展开、首次合法行动、重复研究或错误选择，以及 command chars、calls、invalid、payload 和可观察的 latency/cache；未取得 host/provider 回执时继续标记 host-received unavailable。创建/更新判断为：先更新两个既有 Spark；只有形成边界明确、需执行且不能由既有 WorkCase 无损承接的评估任务时，另经 Gate 1 创建 WorkCase。

65-session historical baseline 只作历史上下文，不充当 control；WC-C 40-session contemporaneous replay 是当前唯一平衡 estimate。扩样不能把 behavior-consistent 写成 broad causal-effect。

### P2：对 prepare-update/CAS 做窄评估；其余读写候选继续受证据门槛约束

P2-1 的目标对象类型为新 WorkCase。预期目标是让一次候选准备返回当前对象、fingerprint 和排除 Code 托管字段的 after skeleton，同时保留完整对象发布主干；优先覆盖 Study/Spark 普通更新与 WorkCase 非 item 更新。验收条件为：不引入 generic patch；stale、no-op、非法字段和验证失败均零写入；继续经过 full-object validation、CAS、atomic replace、exact reread 与 integrity audit；在预注册真实配对任务中验证 read/update 往返是否由 3–4 次降至 2 次，并如实报告没有改善的结果。创建判断为：目标类型与 paired evidence 设计冻结后另经 creation review 与 Gate 1；本 Study 不提供实施授权。

P2-2 success signal、其它 read output 收缩和 F1 delta 保持 evidence gate。只有出现第二个独立 duplicate-create/结果解析失败样本、具体 operation 的实证过量，或可比较的跨会话定位成本时，才建立范围匹配的 WorkCase；信号不存在时继续无需对象化。

受控写入 Spark 应按当前 Working Tree 中 WC-A 后事实重新分类：署名/footer 机械骨架已完成；剩余候选是 Helper 是否可从同一 observed_context 形成最新 `change_log.signature`，以及 P2-1 prepare-update。任何候选都不得降低 fresh observation、三字段不可跨角色推导、完整 CAS、写后回读或 Git 显式 footer 边界。

FileAsset 早期 Gate 1 漏项已由后继完整范围 WorkCase 吸收并完成，当前无需创建对象；只有未来重新引入 FileAsset 产品能力的独立需求出现时，才按新产品方向重新判断，而不能恢复旧退役 residual。

### P3 与 Human-only

67 项 direct-basis 语义复核的目标对象类型为新 WorkCase。预期目标是逐项判定「有意保留的直接依据」或「可精简冗余」。验收条件为：67 项全部有可回读判定记录；可精简项经相应规范授权处置；保留项说明直接边的独立必要性；最终相应 check gap 收敛，或未收敛项均有明确保留理由。只有 Human 批准该方向并完成独立 Gate 1 后才可执行；本 Study 不授权修改规范。

projection-table source-contract、fixture source identity、termination race/Web propagation 与 F1 delta 只在各自已列真实触发条件成立时进入窄 WorkCase。普通实现强制进入 WorkCase、条款日落与 Phase3/MCP 均由 Human 单独判断；Phase3 还必须先取得 P2-1 与代表性实测后仍存在实质残差的证据，再由 09 所保留的 Human Gate 判断是否形成新接入层。本报告不给出选择、MCP 必要性、09 修订或实现授权。

## 后续分流

| 分流类别 | 当前依据 | 进入条件与下一步 |
|---|---|---|
| 更新既有 P1 Spark | 知识预检、AI 服务质量 | 吸收 WC-C 与本审计；按 P1 验收条件形成真实任务评估设计，不新建 Spark。 |
| P2-1 窄 WorkCase | source Study P2-1；WC-B 只覆盖 item_event | 冻结目标类型、paired evidence 与完整发布验收后，fresh creation review/Gate1；禁止 generic patch。 |
| 已完成并由后继事实吸收 | 早期 FileAsset 退役 WorkCase 漏四个消费者后安全取消；后继完整范围 WorkCase 已满足全部退役标准 | 不创建对象；仅在未来出现重新引入 FileAsset 产品能力的独立需求时重新判断。 |
| P2-2/只读/F1 delta | 现有信号不足 | 第二独立 failure sample、具体 operation 过量或可比较跨会话成本出现后再立项。 |
| direct-basis P3 | 67 项 current check gap + existing Study recommendation | 按 P3 验收条件逐项语义判定；保留项说明理由，精简项另经授权。 |
| Human 治理选择 | 普通实现授权缺口、条款日落 | Human 明确选择后再判断 ADR/规范/WorkCase；本审计不代替选择。 |
| 多项目/平台/外部工具/并行 | 各自 active Study 或 open Spark | 真实规模、平台变化或 Human 明确方向触发；不由本审计统一启动。 |
| Phase3/09 | WC-C narrow significant residual | 在 P2-1 与代表性实测后仍有显著残差，才提交 Human 判断是否形成 09 议题；无自动授权。 |
| 不创建对象 | retired/implemented/discarded 与已完成 WC-A/B/C | 作为历史证据消费，不恢复为 backlog。 |
