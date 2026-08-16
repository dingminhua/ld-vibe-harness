---
title: 无环境 Hook 条件下的持续结果校验与 Git Gate 分层方案
status: active
report_kind: external_research
urls:
- ref: https://facebook.github.io/watchman/
  title: Watchman Documentation
  summary: 说明长期文件观察、settle 后交付变化与保守变化语义；用于比较 watcher 基本模型。
- ref: https://facebook.github.io/watchman/docs/troubleshooting
  title: Watchman Troubleshooting
  summary: 确认事件队列溢出或失去同步时执行 recrawl，并把不确定文件视为已变化。
- ref: https://facebook.github.io/watchman/docs/cookies
  title: Watchman Cookies
  summary: 评估事件同步栅栏及 macOS FSEvents 不能保证严格同步的限制。
- ref: https://facebook.github.io/watchman/docs/cmd/flush-subscriptions
  title: Watchman flush-subscriptions
  summary: 提供显式等待既有事件处理完成的 barrier 模式，启发 LDVH checkpoint。
- ref: https://nodejs.org/api/fs.html#fswatchfilename-options-listener
  title: Node.js fs.watch
  summary: 确认文件监听的跨平台、网络盘、虚拟化及 filename 缺失限制，说明事件不能成为正确性证明。
- ref: https://docs.gradle.org/current/userguide/continuous_builds.html
  title: Gradle Continuous Build
  summary: 说明输入变化后的 quiet period 与持续重跑，以及监听范围和触发限制。
- ref: https://www.typescriptlang.org/docs/handbook/configuring-watch.html
  title: TypeScript Configuring Watch
  summary: 比较原生事件与 polling 回退，说明成熟工具会提供保守路径。
- ref: https://github.com/paulmillr/chokidar
  title: Chokidar
  summary: 评估原子保存归一化、awaitWriteFinish、事件聚合和轮询回退；这些只适合调度，不能替代内容指纹。
- ref: https://pre-commit.com/
  title: pre-commit
  summary: 确认同一检查可由 Hook、手动全文件或指定文件运行，并在 CI 中复用。
- ref: https://git-scm.com/docs/githooks
  title: Git Hooks
  summary: 确认 Git Hook 的本地部署与 no-verify 绕过边界。
- ref: https://docs.github.com/en/repositories/configuring-branches-and-merges/managing-protected-branches/about-protected-branches
  title: GitHub Protected Branches
  summary: 说明 required status checks 可保护远端合并，但不解决本地反馈延迟。
- ref: https://bazel.build/remote/caching
  title: Bazel Remote Caching
  summary: 评估把结果绑定到明确输入和动作摘要的 content-addressed 模式，启发验证 receipt。
input_refs:
- kind: specification
  locator: specs/00-理念与构成.md §8.2 薄 Skill、Git Hook 与核心职责边界
  version: 5602766f790a25dd91f67e2ae7864382e49aea1d
  observed_at: '2026-08-10T23:54:36Z'
- kind: specification-attachment
  locator: specs/attachments/09.Att.01-环境接入面.md
  version: 5602766f790a25dd91f67e2ae7864382e49aea1d
  observed_at: '2026-08-10T23:54:36Z'
research_question: 当 AI 开发环境不提供可靠的 post-write 环境 Hook 时，行业如何在任意写入之后尽早检查结果规范；显式高频检查、文件 watcher、稳定快照、验证 receipt、Git Hook 和远端门禁应如何分工，才能让 LDVH 放松写入过程约束而不削弱最终结果与提交边界？
abstract: 本报告于 2026-08-11 对照 Watchman、Node.js、Gradle、TypeScript、Chokidar、pre-commit、Git、GitHub 与 Bazel 的官方资料。行业主流不是把文件事件当成可靠写入证明，而是把 watcher 用作失效或调度信号，把显式检查绑定当前输入，并由 Git Hook 保留提交前最后门禁。根据 Human 后续方向，本研究首期采纳低成本、高频、一次性的显式 ldvh check：它读取当前规则源与当前实际 worktree 的完整管辖事实库，保留原始子结果和 gaps；watcher、receipt 与 ADR 不在首期实现。当前未实现 watcher 原型、性能基准或故障注入。
research_intent: Human 希望 LDVH 约束最终结果而非 AI 的具体写入方式，并要求写完后尽早由 Code 检查；目标环境没有可用的 post-write 环境 Hook，但 Git Hook 仍须保留。本研究为显式检查的可信边界、与 Git Gate 的分工，以及 watcher 作为可选后续增强的条件提供可复读依据。
recommendation_summary: 首期保留 common-dir 级 Git Hook 与 Git Gate，并交付显式、一次性、只读的 ldvh check。它固定检查当前源码 worktree 的完整规则源与由实际 cwd 解析出的受管辖 Git worktree 的完整事实库，逐项保留规则与事实子检查的原始结果、gaps 和未完成范围；普通业务代码、构建产物和临时文件不进入输入。事实子检查非 complete、任一子检查 partial/unavailable/error 或合同定义的阻断 gap 时不得返回 passed。该能力补充而不替代每次事实写后的精确回读和完整性审计，也不替代 Git Hook/Gate。watcher、范围级 receipt 和 ADR 仅在显式检查被证明不足且 Human 另行要求更低延迟自动反馈时再研究。
action_relevance: 设计或评估无环境 Hook 条件下的持续校验方案时，确认 Git Gate 分层方案已覆盖事实完整性终闸
change_log:
- signature:
    model_id: gpt-5
    agent_workbench: Cindy
  session_id: cindy-study-no-environment-hook-research-20260811
  at: '2026-08-10T23:54:37.152370Z'
  summary: Human 要求将无环境 Hook 条件下的行业处理方式、持续结果检查方案及保留 Git Hook 的修正结论写入 Study。
- signature:
    product_name: Cindy
    model_name:
    agent_runtime_name: codex
  at: '2026-08-12T07:07:10.333487Z'
  summary: Human 要求补充并收窄 Study 0029：验证按对话/任务声明范围及必要依赖闭包隔离，无关文件变化不影响该范围 receipt。
- signature:
    product_name: Cindy
    model_name:
    agent_runtime_name: codex
  at: '2026-08-12T07:11:17.573523Z'
  summary: Human 澄清 Study 0029 的监测对象：当前规范源与由工作对象管辖解析出的事实源；普通业务或任意非事实文件不进入 receipt。
- signature:
    product_name: Cindy
    model_name:
    agent_runtime_name: codex
  at: '2026-08-12T08:18:57.934902Z'
  summary: Human 批准显式高频检查方向后，将首期建议更新为 ldvh check；watcher、receipt 与 ADR 改为可选后续研究。
- signature:
    product_name: Cindy
    model_name: chatgpt/gpt-5.6-sol
    agent_runtime_name: claude-code
  at: '2026-08-12T16:11:11.630084Z'
  summary: 建立 informs → spark-0018 关系：本研究关于无环境 Hook 下显式结果检查与 Git Gate 分层的发现和建议应影响该 Spark 的后续判断；不改变研究正文、结论或状态。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:29.764446Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
relations:
- relation_key: informs
  target:
    object_uid: 019ffb52-ebb5-7d9e-b5cc-17beecdc5303
object_id: study-01KZXN5TXNEME80GDTJAXEDHXW
object_uid: 019ffb52-ebb5-751c-8041-ba92bae6c7bc
fact_type_key: study
created_at: '2026-08-10T23:54:37.152370Z'
updated_at: '2026-08-16T21:42:45.620720Z'
---

## 研究问题

当前项目希望把规范约束从写入过程转向写入结果：AI 可以使用方便的文件编辑方式，但写完后应尽快由 Code 检查，避免直到 Git 提交才发现大段文本或事实载体不合格。目标环境没有可靠的 post-write 环境 Hook，无法依赖宿主在每次工具写入后同步调用 LDVH；Human 同时明确 Git Hook 仍须保留。

本报告实际回答：行业怎样在没有统一写后 Hook 的情况下组织持续校验；文件事件为什么不能直接证明结果正确；watcher、稳定快照、验证 receipt、显式检查入口、Git Hook 与远端 CI 各自能保证什么；LDVH 应如何新增早期反馈而不把 Git Gate 替换掉。

## 输入与边界

本报告于 2026-08-11（Asia/Shanghai）实际读取 Watchman、Node.js、Gradle、TypeScript、Chokidar、pre-commit、Git、GitHub 与 Bazel 的官方文档或官方仓库资料，并回读当前 Working Tree 的 00 §8.2 与环境接入面。资料覆盖文件事件可靠性、持续构建、轮询回退、原子保存、检查复用、本地 Hook、远端 required check 与内容寻址缓存。

研究没有实现 watcher 原型，没有测量扫描耗时，也没有执行事件溢出、进程崩溃、网络文件系统或休眠恢复故障注入。GitHub protected branch 只是可选参考，不假设当前项目使用 GitHub。当前规则要求 Git Hook 作为完整接入的 Git 原生入口，并禁止新增并行环境插件或 adapter；因此报告只提出待决架构，不把 watcher 写成已获准或已实现的能力。

候选查重中，Study 类型的 Hook、watch、监听与持续检查查询未发现同问题报告；study-0014、study-0017 与 study-0025 只在其它问题中提到 Hook。整库 F1/F2 因 workcase-0092 与 workcase-0093 的既有机械问题返回 partial，不能把整库覆盖表述为完全无缺口。

## 关键发现

### 发现一：文件事件只适合使旧结果失效

外部观察：Node.js 明确说明 fs.watch 在平台、网络文件系统和虚拟化环境中可能不一致，filename 也不保证提供。Watchman 遇到事件队列溢出或失去同步时会 recrawl，并把不确定文件保守地视为已变化。编辑器原子保存还可能表现为 unlink/add 或 rename。

项目启发：每次 watch/check 的监测对象只能是当前规范源，以及由该对话或任务所给工作对象定位、经管辖解析得出的事实源范围；必要关系闭包只在这些事实源内展开。普通业务代码、任意非事实文件和未落入该管辖范围的事实不进入 receipt。LDVH watcher 收到规则源或该事实源范围内事件时，只能撤销受影响范围的旧验证结果并标记 dirty，不能据此声称完整观察了写入；范围外变化不得触发或撤销它的 receipt。watcher 未启动、崩溃、心跳过期、后端错误、目录重建或事件溢出时，受影响规则或事实范围必须进入 unknown/dirty 并重扫。

对后续项目工作的直接影响：Human 采纳后应创建 ADR，确认“事件只使受影响规范源或管辖事实源范围的 receipt 失效”及关系闭包的信任边界；实现 WorkCase 必须覆盖漏事件、溢出、重启、原子 rename，以及两个并行对话在不相交管辖事实源范围内工作时互不干扰。

### 发现二：稳定快照而非静默时间决定结果能否发布

外部观察：Gradle 在输入变化后等待 quiet period 再重跑；Chokidar 会归一化原子保存并可等待文件大小稳定；Watchman 也在 settle 后批量交付变化。quiet period 能减少半写状态和重复运行，但 size 稳定不证明内容没变。

项目启发：事件后等待约 300–500 ms，再计算检查前 manifest M1，执行 Code 验证并计算 M2。只有 M1 与 M2 完全一致且检查通过，才发布 valid；否则丢弃结果并重跑。manifest 应绑定排序后的受管路径和内容哈希，mtime/size 只作初筛。

对后续项目工作的直接影响：WorkCase 应验证连续写、同大小替换、多文件批次和检查中再次变化，确保旧结果不会发布。性能优化不能省略前后快照一致性。

### 发现三：轮询、全量对账和 receipt 共同补偿漏事件

外部观察：TypeScript 在原生 watcher 受限时提供 polling 回退；Watchman 在监控状态不可信时重新扫描。Bazel 缓存由明确输入和动作摘要寻址，而非只保存脱离输入的“曾经通过”；Watchman flush-subscriptions 还提供显式 barrier。

项目启发：首版可使用显式启动的 worktree 级轮询 watcher：mtime/size 初筛，变化后计算范围内容哈希，并定期对已登记范围及其依赖闭包 reconcile。receipt 至少绑定 worktree、HEAD、范围定位器与范围快照、依赖闭包快照、规则指纹、checker 版本、结果、时间和健康代次。阶段推进、事实消费或成功声明必须现场比较当前范围及闭包指纹，无法比较时返回未验证。整库 manifest 审计可以作为独立项目健康检查，不得把无关对象的问题混入某一范围的 receipt。

对后续项目工作的直接影响：ADR 应冻结“异常即使受影响范围失效、范围/闭包定期对账、内容哈希定案、消费点重验”的语义；WorkCase 必须拒绝旧 worktree、旧 HEAD、旧规则、过期依赖闭包或 stale heartbeat 的 receipt，并测量 CPU、扫描延迟与反馈时间。

### 发现四：watcher 前移反馈，Git Hook 保留最后把关

外部观察：pre-commit 支持 Hook、手动检查和 CI 复用。Git Hook 属于本地事件，仍存在 no-verify 绕过边界；远端受保护分支可要求 status checks，但不保护本地未提交状态，也不能替代及时反馈。

项目启发：watcher 解决“发现太晚”，Git Hook 解决“真实提交前最后把关”。两者复用同一验证核心，但绑定不同输入视图：watcher/check 验证 Working Tree，Git Hook 验证实际 Index 与 commit message，CI 可选验证 commit。Hook 不应无条件相信 Working Tree receipt；除非 receipt 精确绑定当前 Index，否则独立重检。

对后续项目工作的直接影响：现有 common-dir 级 Hook 和 git-commit-msg gate 保持不变。WorkCase 必须证明 watcher 未运行、receipt 过期或 Working Tree 与 Index 不同时，Hook 仍按现有边界检查。

### 发现五：无环境 Hook 时不能声称每次任意写入都立即检查

外部观察：IDE/LSP 诊断、watcher 和常驻任务都依赖进程实际运行及事件递达；它们提供低延迟反馈，不是文件写许可协议。不拦截写系统调用、不控制编辑器也不要求包装器，就无法同步阻断任意工具写入。

项目启发：LDVH 可保证的是“未经当前快照验证的结果不被可信消费入口接受”，不是“每次任意写入后必然立刻检查”。ldvh watch 提供最佳努力的早期反馈；ldvh check 或 barrier 提供当前快照保证；Git Hook 提供提交边界保证。状态必须区分 unavailable、dirty、checking、invalid、valid。

对后续项目工作的直接影响：ADR 与文档必须使用可证明口径，不能把 watcher 描述为环境 Hook 或全局强制器。若 Human 要求 watcher 停止时也阻断所有写入，就必须改变“允许任意编辑方式”的前提。

## 建议

### 建议一：首期交付高频显式 `ldvh check`

首期不建立 ADR，不实现 watcher。新增一次性、只读的 `ldvh check`，使 AI 在处理当前规范源或事实源后可直接调用。命令固定检查当前源码 worktree 的完整规则源，以及由实际 `cwd` 解析出的受管辖 Git worktree 的完整事实库；普通业务代码、构建产物与临时文件不进入输入。

结果必须逐项保留规则与事实子检查的原始结果、范围、gaps、验证和诊断。只有规则检查完成、事实完整性结果为 `complete`，且没有合同定义的阻断 gap 时，组合结果才可报告 `passed`。事实 `partial`、不可用、错误或缺口不能被另一子检查的成功掩盖。

### 建议二：保留既有写后与提交兜底

显式检查只提供早期、方便的反馈，不替代事实写后的精确回读和 `check-fact-integrity`，也不替代真实 Git Hook/Gate 对 Index 与 commit message 的提交门禁。三个入口共享已存在的机械检查核心，但承担不同的时间点和输入视图；本次不修改 Hook 或 Gate。

### 建议三：watcher 仅作为可选后续增强

行业资料仍说明 watcher、稳定快照、receipt 与 reconcile 在需要自动低延迟反馈时的可信边界：事件只能用于失效或调度，不能单独证明结果正确。只有未来实测显示显式检查的反馈成本不足以满足需求、且 Human 明确要求常驻自动反馈时，才另行研究 watcher 的范围、性能、故障恢复和是否需要 ADR；本 Study 不把它们写成当前能力或既定计划。

## 后续分流

| 建议或未决问题 | 出现何种信号时创建或更新对象 | 继续无需对象化的条件 |
|---|---|---|
| watcher 与环境接入边界 | Human 接受结果门禁优先且准备改变长期架构时，创建 ADR | 继续要求行动模板显式 check，不新增常驻能力 |
| 轮询 watcher MVP | ADR 已批准且早期反馈收益值得实现时，创建 WorkCase | 写入频率低，显式 check 已足够及时 |
| 原生事件后端 | 轮询 CPU 或延迟实测不达标时，更新 WorkCase | 轮询满足资源和延迟目标 |
| receipt 消费门禁 | 阶段推进、成功声明或 Web 状态需要复用检查结果时，纳入 WorkCase | watcher 只显示临时诊断，不用于可信判断 |
| 远端 required check | 实际需要跨机器或防本地绕过的合并门禁时，按平台对象化 | 当前只要求本地 Git Gate |
| 任意写入同步强制 | Human 要求 watcher 停止时仍阻断所有写入时，重新决定受控写入或文件系统拦截 | 接受早期反馈为最佳努力、消费与提交点机械强制 |

### 范围隔离补充：首期监测当前规范源与完整管辖事实源

首期显式检查的基本单位不是对话任意改动的文件清单，也不是普通业务项目全量扫描。它固定由两部分组成：当前规则源，以及实际 `cwd` 所属唯一受管辖 Git worktree 的完整事实库。普通业务代码、构建产物、临时文件及其它非事实载体不属于 `ldvh check` 的输入；结果明确分别报告规则范围和完整事实范围。

因此，V1 不承诺“对话 A 只检查事实 A、与事实 B 完全隔离”的范围级 receipt。该更细粒度的分区、关系闭包、失效与 receipt 消费仍是 watcher 方向的后续研究课题。当前 `ldvh check` 只证明其当次规则和完整事实子检查的机械结果，不证明整个项目业务代码通过、规则适用、Human 授权或工作完成。
