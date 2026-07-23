# 规范上下文组合读取实现规划

## 1. 目标与规则边界

本规划只实现 `specification-model-foundation` §§9.8–9.9 声明的
`read-specification-context`。它帮助 AI 对已经精确选择的根规范或普通规范一次取得机械标题导航、可选主规则原文及同一载体的边界伴随原文，降低渐进式阅读时漏读适用范围、验证要求、Human Gate 或 Stop Conditions 的风险。

本操作只组织现有 L1/L3 内容，不判断任务相关性、规则适用、Human Gate 或 Stop Conditions 是否命中，不产生行动许可、授权 receipt、长期通行证、事实对象或完成结论。没有调用本操作本身不阻断普通行动。`specs/00-理念与构成.md` 不在本实现变更范围。

实现起点 commit 固定为 `6e2b8669f7e52e6d8f0ec5c3ff36ef2519ad7e08`。开始本增量时，Working Tree 中与本实现直接相关但尚未提交的 Code 变化只有 `code/tests/specs/test_repository.py` 和 `code/tests/helper/test_cli_process.py` 对来源已声明但尚未实现 operation 的诚实发现断言；本规划承接这两处变化，并覆盖随后形成的 context request、reader、operation binding、registry 与专属 tests。其它既有未提交 Specs、事实、Web 和审计文档不由本规划覆盖，也不因 staged、tracked 或 committed 状态改变语义效力。

本规划与 `environment-neutral-enablement.md` 共同涉及发行物，但责任不重叠：本规划只负责该 operation 的来源声明绑定、实现模块随既有 package discovery 被纳入，以及 installed source projection 的专属回归；通用 `setup.py`、wheel/sdist 生命周期、entry point 和用户文档仍由环境无关启用规划维护。本规划只消费 `full-v4-working-tree-evidence.md` 定义的唯一 full-v4 runner 和耐久记录，不修改 runner、证据 DTO 或步骤计划；与其它当前规划没有共同实现责任。

## 2. 模块责任与依赖

依赖方向固定为：01/04 的公开契约 → 当前规则源 `RepositoryInspection` → 现有规范内容读取核心 → 上下文组合投影 → Helper 公共响应。

| 模块 | 责任 | 明确不负责 |
|---|---|---|
| `code/ldvh/helper/operations/specification_context_request.py` | 唯一维护 context request DTO；输入为共享 `CommonRequest`，输出已校验的 context tuple 或问题；校验字段闭集、数量、职责唯一性、标题路径格式及前缀重叠 | 读取仓库、推断规范或判断适用 |
| `code/ldvh/helper/operations/specification_content.py` | 继续承担精确目标解析、H2/H3 唯一性和 L3 原文机械切片 | 为上下文操作建立第二套 Markdown 解析 |
| `code/ldvh/helper/operations/specification_context.py` | 唯一维护领域 result DTO 与 `items/heading_outline/parts/guard_coverage` 投影；输入同一 `RepositoryInspection` 和已校验 request，输出完成/未完成范围、领域 items、来源、披露、验证、缺口与诊断 | 改写原文、静默截断、把 coverage 提升为语义结论 |
| `code/ldvh/helper/operations/specification_context_operation.py` | 维护 operation descriptor，复用 `OperationImplementation` 连接 capability check/call，并把领域结果交给共享响应 | 扩展公共共同请求对象或创建统一行动 envelope |
| `code/ldvh/helper/operations/__init__.py` | 只把 01 已声明的 operation key 绑定到上述实现 | 由 Code 自行创造公开操作、修改通用 packaging 或安装环境 Hook |
| `requests.py` / `responses.py` / `operation_runtime.py` / `service.py` | 继续分别唯一维护共同请求、共同响应、operation runtime 和 CLI/capabilities 编排；新操作仅消费这些接口 | 为 context 复制第二套共同 Schema 或错误协议 |

CLI、`capabilities`、当前 Working Tree 规则源和 installed release snapshot 是上述 operation descriptor 的消费者；同步方向只从 01/04 契约到 request/领域投影/descriptor，再由 registry 进入共享 service，不反向用 Code 定义规则。

## 3. 组合与去重算法

每个 context 保持为独立原子范围。实现先精确确认职责对应 `root|spec` 的当前合格载体；附件 key 在输入边界拒绝。标题导航直接使用该内存载体已经解析、排除代码围栏伪标题的 H2/H3 序列，并按现有 L3 边界计算 `start_line/end_line`。

普通规范的 companion 结构角色是 `适用范围`、`验证要求`、`Human Gate`、`Stop Conditions`；根规范只有后三者，`ldvh_spec.scope` 作为 L1 overview 单独交付。结构角色的精确标题由 01 已定义的当前文档结构取得，不根据任务或关键词相似性扩展。

主规则和 companion 都通过现有规范内容读取的精确 L3 核心取得。若主规则等于 companion H2 或位于其 H3 内，由完整 companion H2 覆盖；其余内容按文件行号排序、按来源范围去重。主规则职责不是 root/spec、精确标题不存在或不唯一，属于调用方精确选择不成立，整次请求返回 `invalid_request`；标题路径格式、重复或前缀重叠在仓库读取前同样返回 `invalid_request`。只有输入选择已经成立之后，必需 companion 缺失、重复、不可读，或来源资格、快照身份与执行无法形成时，整个 context 才进入未完成范围并可能与其它完成 context 组成 `partial`。两类失败不得互相包装。

每个 part 的 `content_sha256` 从原始 UTF-8 content 计算，`source_content_sha256` 从同一内存文档的完整 UTF-8 原文计算。摘要只作为读取与漂移证据。

## 4. 响应与失败分类

`scope.requested/completed/not_completed` 原样使用 `{responsibility_key, primary_heading_paths}`，保持请求顺序。至少一项完成且至少一项未完成时返回 `partial`；零项完成时沿用现有规范内容读取的 `error > rejected > unavailable` 聚合优先级。输入闭集、数量、重复、附件职责、未知或不唯一的精确职责/标题路径及路径前缀重叠返回整请求 `invalid_request`。

`heading_outline` 不进入 `disclosure.parts`。每个 overview scope 对应一个 L1 disclosure part，精确回指同一 YAML scope 字段；每个原文 part 对应一个 L3 disclosure part。`compact` 只聚合重复的验证或缺口元数据，不删除、截断或改写完成项原文。

共同 `requested_disclosure` 固定为 `L3`，`observed_context` 固定为空；合法出现的 `task`、`work_object_locators` 和 `authorization_reference` 由共享 parser 保留但不得改变职责、标题或 companion 选择。零完成固定 `result=null`，读取操作固定 `changes=[]`、`scope.governance_resolution=null`。未由 Code 自动证明的规则源资格条件对完成项继续保留 `qualification_unproven` gaps；`verification` 只记录真实执行并 passed 的身份、结构、边界、同源与摘要检查，不报告规则适用、授权或完成。

领域模块捕获并分类可预期的精确选择、来源资格和组合失败，把原始 context scope 与必要 source refs 绑定到 `gaps`，把实际结构/读取问题放入 `diagnostics`；operation adapter 只把请求错误转换为共享 `OperationRequestError`。共享 service 继续负责未预期异常的统一 error 处理。诊断不得复制不必要的完整规则原文、调用栈、凭据或环境秘密；原文只出现在契约要求的完成 item parts 中。

## 5. 测试与验证映射

| 风险 | 主要检查 |
|---|---|
| 形成第二套切片语义 | 同一 key/heading 与 `read-specification-content` 逐字、行范围和 source 差分 |
| root/spec profile 混淆 | 分别断言 scope L1、四项 coverage、三/四类 companion |
| 主规则覆盖 companion | H2 相等、H3 位于 companion、H2/H3 输入互为前缀反例 |
| 标题导航边界错误 | H2/H3、围栏内伪标题、最后章节的行范围测试 |
| 半成品冒充完成 | 缺失/重复结构角色、来源失败及多 context partial；不存在/不唯一主规则单独断言整请求 invalid |
| 快照漂移 | 检查后修改磁盘文件，断言输出仍来自原内存快照和原摘要 |
| 来源视图不一致 | Working Tree 与 installed release snapshot contract tests |
| 摘要越权 | 重算 SHA-256，并断言响应没有适用、授权、允许或完成声明 |
| 打包遗漏 | CLI capability/call、wheel/sdist 与 installed source projection tests |
| 共同请求误参与选择 | 固定 L3、非空 observed context 拒绝；task/locator/authorization 有无两次真实调用结果相同 |
| 共同响应偏移 | 复用 service/response contract tests 检查 `changes=[]`、governance null、零完成 result null、scope/disclosure/source refs |
| 资格 gap 或验证越权 | compact/diagnostic 均保留 qualification gaps；故障注入断言未执行/失败检查不产出 item，verification 只含 passed 机械检查 |

核心切片、root/spec、摘要、漂移和 partial tests 使用真实 `RepositoryInspection` 与真实 Markdown fixture；CLI/capabilities 使用真实子进程；installed projection 使用仓库既有已验证发行快照 fixture。只在制造重复/缺失结构、读取异常或 shared-service 未预期异常时使用局部故障注入/test double，并明确只证明失败传播，不冒充真实集成。共同响应形状复用现有 service/CLI contract tests，不复制另一套 validator。

本次新增公开 operation Schema 跨 request、runtime、CLI 与 installed projection，命中 07 §10.1 的跨模块公共接口与发行投影全量触发条件。实现后先运行聚焦 Helper/specs tests 与 Ruff，再通过 `tools/run_full_tests.py start --plan full-v4` 唯一入口取得全量耐久记录，并回读其终态和 Working Tree evidence；不以临时 pytest 输出替代该证据。只有实际 CLI 能力发现、调用、测试与发行投影均成立时，才声明该操作在相应范围可用。

## 6. 明确排除

本增量不修改 00，不改变 L0–L4，不新增或安装 SessionStart/SubagentStart 等环境 Hook，不引入通用 preflight、白名单、action envelope、receipt、token 或运行时许可状态机，不修改事实对象、Spark、WorkCase 或 Web。后续环境是否消费本操作，必须回到 09 的实际事件、封闭机械条件和 Human Gate 单独处理。
