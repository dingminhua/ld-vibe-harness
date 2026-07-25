# Codex 工作上下文核心与稳定薄引用实现规划

## 1. 规划身份与来源

本规划承接 `workcase-0007`，覆盖 Codex 的新会话、恢复、压缩后继续与子代理工作上下文。它取代“生命周期事件即默认恢复项目事实”的旧实现取向：00 §8.1 规定先交付规则引导；01 §9.10 定义 profile `work-context-rule-orientation`；04 定义既有 Helper 读取操作；05 §8.1 定义仅在 AI 已理解 Human 目标并明确需要项目事实时进入的事实消费分支；09 定义环境 Hook、共享投影与 adapter 的边界；07 定义风险匹配测试。

规则权威单向流动为：00 → 01/04/05/09 → LDVH 工作上下文核心与共享事实恢复 Code → Codex adapter。实现不得反向以事件名、任务文字、cwd、工作对象、缓存或父上下文定义规则选择、事实相关性、规则适用、授权或完成。

本规划同时承担 Codex adapter 作为 LDVH 仓库参考实现的维护责任。Codex adapter 不是 LDVH 核心的组成部分；其它 AI 开发环境的 adapter 不在本规划范围内，由处理该目标环境的 AI 在该环境自己的仓库按 09 §5.2 薄引用规则独立开发，不在 LDVH 仓库收纳或维护。

## 2. 目标与明确排除

本增量使 Codex `SessionStart(startup|resume|clear|compact)` 与 `SubagentStart` 都通过同一个冻结的薄引用调用 `ldvh-work-context`。核心执行来源定义的规则引导 profile，只向 AI 交付 `ldvh-root` 的 `8. 系统级运行架构` / `8.1 工作上下文的信息交付顺序与渐进式披露` 及 `8.2 环境 Hook 的薄引用与核心职责边界` 两个当前 L3 选择。Human Gate、Stop Conditions 和其它规则在目标明确后按需读取，不再作为每次工作上下文进入的固定负载。

无论 profile 的实际 outcome 为 `ok`、`partial`、`rejected`、`unavailable` 或 `error`，核心都必须如实保留已取得的原文及其来源、未完成范围和 gap，并形成可由 adapter 原样承载的结果；默认结果明确 `facts: not_requested`。这不表示事实为空、无效、已经完整恢复或与当次工作无关。

本增量不新增 Helper operation、披露层级、会话状态、规则适用引擎、任务相关性算法、授权 receipt 或通用行动编排。它新增环境无关的 `ldvh-work-context/1` 核心入口，不删除 `ldvh-context-recovery/1`，但把后者保留为 AI 已明确进入事实消费分支后的显式共享能力；不由 Codex 生命周期默认调用，也不作为核心失败或不兼容时的替代路径。

## 3. 模块责任与依赖

| 模块 | 责任 | 明确不负责 |
|---|---|---|
| `01` 的 profile | 定义固定、可审阅的最小规则选择与失败语义 | 判断任务相关性、规则适用或事实需要 |
| `read-specification-content` | 在同一当前规则源视图中按精确 key/标题路径读取 L3 原文 | 按 cwd、任务或事实选择规则 |
| `ldvh.work_context` / `ldvh-work-context` | 接收原生事件对象，执行当前规则源定义的 profile，校验 Helper 契约/exit code，并形成规则原文、来源、缺口和 `facts:not_requested` 的核心结果 | 管辖解析、事实发现/读取、筛选事实、语义判断或修改规则正文 |
| `code/plugins/ldvh/scripts/codex_context.py` | 原样传递 Codex 原生 JSON，调用固定的 `ldvh-work-context`，并将核心结果承载为 Codex Hook 输出 | profile、标题选择、规则/事实读取、结果解释或任何兜底策略 |
| `ldvh.hooks.context_recovery` | 在已被上层明确请求时组织 F0–F4 的确定性事实恢复投影 | 作为默认会话启动器，或判断何时应进入事实分支 |
| plugin configuration / packaging | 显式保存并验证固定 `ldvh-work-context` 与 Helper 身份，分发薄 adapter | 从配置或安装路径推断项目、任务或规则选择，或以旧事实恢复配置替代核心 |

核心的唯一 Helper 请求使用 `ldvh call read-specification-content`、`requested_disclosure: L3`、`response_profile: compact`、空 `observed_context` 和上述唯一精确 selection。规则引导只验证 Helper 和规则源读取所需条件；`cwd` 只作为 Helper 子进程的真实进程环境，不能进入请求选择或投影为项目身份。历史事实恢复 runner、管辖 workspace 或项目事实配置不是 Codex Hook 配置的一部分；它们缺失、失效或不可用时不得触发替代调用。

## 4. 交付投影与失败边界

核心只接受与 Helper `ldvh-helper-cli/2` 合同、请求身份、operation key 以及 outcome/exit code 相互一致的一份 JSON 响应。对于已验证的 `ok`、`partial`、`rejected`、`unavailable` 或 `error`，核心如实交付已完成 L3 parts 和 gaps；零个完成 part 不伪造原文。响应结构、编码、身份或退出码不可信时，核心形成规则引导未交付、事实仍为 `not_requested` 的结果，并保留从当前规则源直接读取的入口。adapter 只验证该核心结果的承载结构，不重新解释其内容。

投影不得静默截断原文，也不得把 Helper 原始 JSON 整体作为正常上下文注入。每个交付 part 保留 locator、heading path 和原文；gap 保留为可审阅的结构化摘要。核心结果应说明环境薄引用未执行管辖、事实读取、适用、授权或完成判断，并提示 AI 在理解 Human 目标后继续使用相应规则或事实读取能力。

## 5. 显式事实分支的保留

AI 在规则引导后，根据 Human 目标和当前信息明确需要项目事实，或需要复核精确稳定事实引用时，才可调用 `ldvh-context-recovery` 或其它来源定义的事实读取。进入后仍遵守 02 的管辖、05 的 F0–F4/F1 coverage 与 partial 规则、21 的 WorkCase binding 规则及 09 的有界投影规则。

父摘要、cwd、Hook event、项目候选、精确引用或唯一机械候选均不自动证明事实已经恢复、当前适用或行动获授权。规则交付状态、事实 Helper coverage 和环境 `delivery_coverage` 分开表达；默认分支中的事实状态固定为 `not_requested`。

## 6. 测试与验证映射

| 风险 | 主要检查 |
|---|---|
| Hook 留存业务逻辑 | 插件源码 negative test：不存在 profile、标题选择、Helper operation、规则/事实读取或结果渲染；五种事件均只调用固定核心 |
| profile 漂移或任务/cwd 影响选择 | 对所有声明事件、不同 cwd 的核心请求字节级断言唯一固定 selection 相同；01 profile 与实现选择语义回读 |
| 核心部分/失败被伪装为成功 | `ok`/`partial`/无结果、合同错误和 exit code 不一致的核心与 adapter 承载 tests |
| 原文、来源或 gap 被丢弃 | Fixture 断言核心结果中的 L3 content、locator、heading、outcome、缺口与 `facts:not_requested` 原样进入 additionalContext |
| 事实恢复能力被误删或变成兜底 | 保留 `context_recovery` 的独立 contract/coverage/partial tests，并断言它不属于默认核心或 adapter 调用 |
| 根规范编号或 profile 选择漂移 | repository、规范内容/组合读取、工作上下文核心与引用一致性 tests |

实现后至少运行相关 specs/helper/adapter/context-recovery tests 与 Ruff。发布、doctor 用户文档、具体 Codex 安装、真实触发、Windows 与其它环境仍由各自来源和规划验证；它们不因本地 adapter test 通过而变为已验证。

## 7. 明确排除

本规划不恢复旧的固定 byte budget，不要求所有环境必须具备同样 Hook 事件，不决定子代理的具体任务或父引用格式，不为事实分支建立自动触发词或关键词，也不修改 Git Gate、Web、事实写入、公共发布、commit、push 或 PR。
