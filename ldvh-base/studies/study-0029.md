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
research_question: 当 AI 开发环境不提供可靠的 post-write 环境 Hook 时，行业如何在任意写入之后尽早检查结果规范；文件 watcher、稳定快照、验证 receipt、Git Hook 和远端门禁应如何分工，才能让 LDVH 放松写入过程约束而不削弱最终结果与提交边界？
abstract: 本报告于 2026-08-11 对照 Watchman、Node.js、Gradle、TypeScript、Chokidar、pre-commit、Git、GitHub 与 Bazel 的官方资料。行业主流不是把文件事件当成可靠写入证明，而是让 watcher 使旧结果失效并触发检查，让检查绑定稳定内容快照和可核对 receipt，让关键消费入口现场核对当前指纹；Git Hook 保留为实际 Index 与 commit message 的最后一道本地机械门禁，远端 required check 可选作合并门禁。没有环境 Hook 时无法保证每次任意写入后立刻检查，但可以保证未经当前快照验证的结果不被 LDVH 信任。当前未实现原型、性能基准或故障注入，且既有无效 WorkCase 会使整库审计保持 partial。
research_intent: Human 希望 LDVH 约束最终结果而非 AI 的具体写入方式，并要求写完后尽早由 Code 检查；目标环境没有可用的 post-write 环境 Hook，但 Git Hook 仍须保留。本研究为 watcher 的可信边界、与 Git Gate 的分工，以及事件丢失或进程未运行时的 fail-closed 行为提供可复读依据。
recommendation_summary: 建议保留 common-dir 级 Git Hook 与 Git Gate，并新增显式的 worktree 级 ldvh watch/check 过程能力。事件只使旧结果失效；debounce 后比较检查前后完整受管 manifest，只有同一快照通过 Code 才生成绑定 worktree、HEAD、规则与 checker 版本、内容哈希的 receipt。异常均撤销 valid 并全量重扫。可信消费入口现场核对 receipt；Git Hook 独立检查当次 Index。实施前由 ADR 澄清 watcher 是显式 Code/CLI 过程检查而非环境插件，再由 WorkCase 实现轮询 MVP 与故障验证。
change_log:
- signature:
    model_id: gpt-5
    agent_workbench: Cindy
  session_id: cindy-study-no-environment-hook-research-20260811
  at: '2026-08-10T23:54:37.152370Z'
  summary: Human 要求将无环境 Hook 条件下的行业处理方式、持续结果检查方案及保留 Git Hook 的修正结论写入 Study。
object_id: study-0029
fact_type_key: study
created_at: '2026-08-10T23:54:37.152370Z'
updated_at: '2026-08-10T23:54:37.152370Z'
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

项目启发：LDVH watcher 收到受管路径事件时，只能撤销旧验证结果并标记 dirty，不能据此声称完整观察了写入。watcher 未启动、崩溃、心跳过期、后端错误、目录重建或事件溢出时都必须进入 unknown/dirty，并全量重扫。

对后续项目工作的直接影响：Human 采纳后应创建 ADR 确认“事件只使 receipt 失效”的信任边界；实现 WorkCase 必须覆盖漏事件、溢出、重启和原子 rename。

### 发现二：稳定快照而非静默时间决定结果能否发布

外部观察：Gradle 在输入变化后等待 quiet period 再重跑；Chokidar 会归一化原子保存并可等待文件大小稳定；Watchman 也在 settle 后批量交付变化。quiet period 能减少半写状态和重复运行，但 size 稳定不证明内容没变。

项目启发：事件后等待约 300–500 ms，再计算检查前 manifest M1，执行 Code 验证并计算 M2。只有 M1 与 M2 完全一致且检查通过，才发布 valid；否则丢弃结果并重跑。manifest 应绑定排序后的受管路径和内容哈希，mtime/size 只作初筛。

对后续项目工作的直接影响：WorkCase 应验证连续写、同大小替换、多文件批次和检查中再次变化，确保旧结果不会发布。性能优化不能省略前后快照一致性。

### 发现三：轮询、全量对账和 receipt 共同补偿漏事件

外部观察：TypeScript 在原生 watcher 受限时提供 polling 回退；Watchman 在监控状态不可信时重新扫描。Bazel 缓存由明确输入和动作摘要寻址，而非只保存脱离输入的“曾经通过”；Watchman flush-subscriptions 还提供显式 barrier。

项目启发：首版可使用显式启动的 worktree 级轮询 watcher：mtime/size 初筛，变化后计算内容哈希，并定期全量 reconcile。receipt 至少绑定 worktree、HEAD、受管 manifest、规则指纹、checker 版本、验证范围、结果、时间和健康代次。阶段推进、事实消费或成功声明必须现场比较当前指纹，无法比较时返回未验证。

对后续项目工作的直接影响：ADR 应冻结“异常即失效、定期全扫、内容哈希定案、消费点重验”的语义；WorkCase 必须拒绝旧 worktree、旧 HEAD、旧规则和 stale heartbeat 的 receipt，并测量 CPU、扫描延迟与反馈时间。

### 发现四：watcher 前移反馈，Git Hook 保留最后把关

外部观察：pre-commit 支持 Hook、手动检查和 CI 复用。Git Hook 属于本地事件，仍存在 no-verify 绕过边界；远端受保护分支可要求 status checks，但不保护本地未提交状态，也不能替代及时反馈。

项目启发：watcher 解决“发现太晚”，Git Hook 解决“真实提交前最后把关”。两者复用同一验证核心，但绑定不同输入视图：watcher/check 验证 Working Tree，Git Hook 验证实际 Index 与 commit message，CI 可选验证 commit。Hook 不应无条件相信 Working Tree receipt；除非 receipt 精确绑定当前 Index，否则独立重检。

对后续项目工作的直接影响：现有 common-dir 级 Hook 和 git-commit-msg gate 保持不变。WorkCase 必须证明 watcher 未运行、receipt 过期或 Working Tree 与 Index 不同时，Hook 仍按现有边界检查。

### 发现五：无环境 Hook 时不能声称每次任意写入都立即检查

外部观察：IDE/LSP 诊断、watcher 和常驻任务都依赖进程实际运行及事件递达；它们提供低延迟反馈，不是文件写许可协议。不拦截写系统调用、不控制编辑器也不要求包装器，就无法同步阻断任意工具写入。

项目启发：LDVH 可保证的是“未经当前快照验证的结果不被可信消费入口接受”，不是“每次任意写入后必然立刻检查”。ldvh watch 提供最佳努力的早期反馈；ldvh check 或 barrier 提供当前快照保证；Git Hook 提供提交边界保证。状态必须区分 unavailable、dirty、checking、invalid、valid。

对后续项目工作的直接影响：ADR 与文档必须使用可证明口径，不能把 watcher 描述为环境 Hook 或全局强制器。若 Human 要求 watcher 停止时也阻断所有写入，就必须改变“允许任意编辑方式”的前提。

## 建议

### 建议一：先创建 watcher 与 Git Gate 分层 ADR

目标对象类型与创建判断：Human 接受长期方向后创建 ADR；当前尚未创建。预期目标是决定保留 Git Hook 的前提下，ldvh watch/check 是否作为显式 Code/CLI 过程检查成立，以及它与 00 §8.2 禁止并行环境接入形态的兼容解释或必要修订。

验收条件：明确事件不可信、receipt 绑定、状态闭集、worktree 隔离、异常全扫、轮询回退、消费 barrier、Working Tree 与 Index 的不同视图、Git Hook 独立性，以及无法保证任意写入立即检查的边界；同时比较“不新增 watcher、继续每次显式 check”的替代方案。

### 建议二：ADR 通过后创建轮询 MVP WorkCase

目标对象类型与创建判断：仅在 ADR 批准后创建 WorkCase。预期目标是交付显式的 worktree 级 ldvh watch 与 ldvh check，共享当前 Code validator，不增加厂商环境 Hook、插件或 adapter。

验收条件：启动全量基线；变化立即 dirty；debounce；检查前后 manifest 一致；异常撤销 valid；定期 reconcile；receipt 绑定 worktree、HEAD、规则、checker 和内容哈希；验证原子 rename、连续写、同大小替换、检查中变化、进程重启、心跳过期和 linked worktree 隔离。

### 建议三：三个快照视图复用同一验证核心

目标对象类型与创建判断：纳入同一 WorkCase，不另建并行 validator。预期目标是形成 validate(snapshot) 核心，由 Working Tree、Index 和 commit 三种适配器提供明确输入。

验收条件：相同规范错误产生一致分类；每个结果回指实际快照；watcher 结果不能掩盖 Hook 对 Index 的失败；现有 Hook 部署与真实事件绑定不被削弱。远端门禁只在项目确有防本地绕过和跨机器合并需求时另行对象化。

## 后续分流

| 建议或未决问题 | 出现何种信号时创建或更新对象 | 继续无需对象化的条件 |
|---|---|---|
| watcher 与环境接入边界 | Human 接受结果门禁优先且准备改变长期架构时，创建 ADR | 继续要求行动模板显式 check，不新增常驻能力 |
| 轮询 watcher MVP | ADR 已批准且早期反馈收益值得实现时，创建 WorkCase | 写入频率低，显式 check 已足够及时 |
| 原生事件后端 | 轮询 CPU 或延迟实测不达标时，更新 WorkCase | 轮询满足资源和延迟目标 |
| receipt 消费门禁 | 阶段推进、成功声明或 Web 状态需要复用检查结果时，纳入 WorkCase | watcher 只显示临时诊断，不用于可信判断 |
| 远端 required check | 实际需要跨机器或防本地绕过的合并门禁时，按平台对象化 | 当前只要求本地 Git Gate |
| 任意写入同步强制 | Human 要求 watcher 停止时仍阻断所有写入时，重新决定受控写入或文件系统拦截 | 接受早期反馈为最佳努力、消费与提交点机械强制 |
