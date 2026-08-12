---
name: ldvh
description: 项目待办/工作项/进展、技术决策/决策记录、踩坑经验、调研/研究报告、项目议题/火花、规范修订、受控提交、环境接入时使用——这些是 LDVH（LD Vibe Harness）管辖事项，对应事实对象 WorkCase、ADR、Pitfall、Study、Spark 的创建、更新与读取，或需要取得 LDVH 规则引导与行动模板时。本技能只负责把会话路由到 LDVH CLI；全部规则、模板与事实权威由 CLI 从当前规则源现取。
---

<!-- 修改保护：本文件受 specs/00-理念与构成.md §10.1 第 13 项保护——修改治理与 00 第 1–8 章同级。任何修改须经 Human Gate。详见 00。-->

# LDVH 接入（薄路由）

> Skill 版本：2026-08-13 00:01

LDVH 让长期项目"判断有据、行动可续、结果可验"。本文件不承载规则正文；固定能力边界只作路由提示。
权威只有一个：LDVH CLI 从当前规则源现取的结果。

## 职责（只有三件）

1. **身份**：当前项目可能受 LDVH 管辖。落入 LDVH 领域的事项（事实写入、规范
   修订、受控提交、环境接入）必须走 LDVH 流程，不得直写受管文件。

2. **规则引导**：会话开始、恢复或上下文压缩后继续时，经已解析的源码 Helper
   `read-specification-content` 精确读取根规范 `ldvh-root` 的 §8.1 与 §8.2，
   并如实报告所用路径与取得范围。该引导只交付规则，不恢复项目事实
   （facts 恒为 `not_requested`）。

3. **行动模板**：动手落入 LDVH 领域前，先
   经已解析的源码 Helper 调用 `read-action-template-candidates` 定位，再调用
   `read-action-template-content` 读取当次适用模板，照模板执行。
   不得凭记忆或本文件假设模板清单与内容。

当当前来源或当次行动模板要求实际操作携带环境署名时，AI 只可使用本次会话中按角色直接声明的信息；没有直接来源的角色如实标为不可得，不得在产品、模型与当前执行 Agent/运行时之间互相推导。每次 `change_log` 写入与每次 Git 提交前，都必须重新取得并判断三字段快照，不得复用先前动作的快照。创建受管辖 Git commit 时，提交方必须把当前契约要求的可观察署名显式写入完整 message，不得依赖环境变量或 Hook 自动注入；字段形状、入口与参数一律以 CLI 当次取得的契约为准。本段只约束 AI 观察与路由，不定义平台获取方式或 Code 行为。

## 能力边界（非职责）

下列固定表述只作能力边界路由提示，不增加第四项职责，不代替 CLI 当次现取的权威来源与实际验证：

薄 Skill 对事实写入的保护仅为劝告级：它只能将 AI 路由到 Helper 与行动模板，不能在模型之外机械阻断对 `ldvh-base/` 的直写。

承接 Git Gate 的 Git Hook 以 Git common-dir 为部署边界：一次部署覆盖共享该 common-dir 的主 worktree、现有 linked worktree 与后续新建 linked worktree；纳入当次完整接入目标的独立 clone 具有不同 common-dir，必须单独部署，未纳入目标时不为验收创建或部署。每个真实 Git 事件仍只绑定实际触发它的 worktree、当次 Index 与 commit message；未触发承接 Git Gate 的 Git Hook，或绕过 Git Gate 检查的行动不在覆盖范围。

项目 Stop gate（项目级 `.claude/settings.json` 的 `hooks.Stop` 与 `.claude/hooks/ldvh-workcase-stop.py`）只对环境变量或 `.ldvh-stop-bindings/<session_id>.json` 精确绑定的当前 WorkCase 生效：Controller-owned 快照阻止非法 Stop 并反馈下一控制步骤，安全出口放行，无绑定或任何异常 fail-open，且不得按唯一 open WorkCase 猜测绑定；它不写事实、不推进 phase、不选择 item，也不替代 AI 对语义、依赖、授权或完成的判断。

机械检查能够发现来源已定义的机械不合格，不能据此判断事实内容的语义真实性；即使 Schema 合法，语义污染风险仍然存在，未提交污染窗口只能压缩、不能消除。

## 禁止

- 不复制规则正文、规范章节、模板正文或事实 Schema 到本文件或会话产物；
- 不写死模板清单、Helper 操作清单、信封字段、参数或机器绝对路径——一律现取；
- 不断言任何环境的自动加载、触发或递达状态；
- 不把 `partial`、`unavailable`、未验证写成成功、生效或已保障。

## CLI 定位与调用

先读取环境接入面附件（`environment-integration-surface`），只使用其中标记为
已交付、且解析到当前已确认 LDVH 源码仓库的入口。默认不构建或安装 LDVH
wheel、sdist、editable distribution，也不以 pip 安装 LDVH 本体。源码入口
不可得、未解析到已确认源码或状态不符时如实交还"CLI 不可定位"或迁移缺口，不猜路径或改投
不明 PATH/安装副本。Helper 操作信封与参数以其 capabilities 及 Helper 服务规范
（04）的当次内容为准；独立入口的信封以环境接入面附件对应入口行的当次内容为准。
所有公开入口都必须让 stdin 到达 EOF；无 tty 场景使用 `< /dev/null` 或闭合管道，入口挂起时先排查 stdin 未闭合。已确认源码根后，可先用 `capabilities </dev/null` 发现当次公开操作；当前规则源与当前 worktree 的一次性机械检查使用 `ldvh check </dev/null`。该快捷入口是零输入检查，不应猜测或注入 `workspace_root`。

事实写入后的精确回读仍是必需步骤；在 merge/pull 后或需要当前完整事实库机械结论时，再按当次 capabilities 与来源契约调用 `check-fact-integrity`。它不是独立 shell 子命令，必须经 `ldvh call check-fact-integrity`，并按当次契约提供实际 worktree locator。`ldvh check`、`check-fact-integrity` 和精确回读的结果只用于各自机械边界，不互相替代。

消费检查结果时至少保留外层 `outcome`、领域 `result.status`、`scope.completed`/`scope.not_completed`、`gaps` 和实际规则源/事实源范围；不得从 `ok`、`passed`、文件存在或命令成功退出推导事实语义正确、Human 授权、Git Gate 已验证、Skill 已递达或完整环境接入。

需要 `governed_project_id` 时，从当前目录向其父目录逐级向上查找
`LDVH-GOVERNED-PROJECTS.yaml`（管辖配置）读取项目 `id`；不得用目录名或仓库名
猜测。操作参数不确定时，先以
最小请求试调一次并读响应 `gaps`/`diagnostics` 中的契约问题，或经已解析的
源码 Helper 调用 `read-specification-content` 精确读取 04 及其授权附件的字段表；
不得反复盲猜参数。

## Helper 调用参数纪律

调用任何 LDVH Helper 公开操作（`resolve-governance-scope`、`prepare-fact-object-draft`、
`create-fact-object`、`read-fact-objects`、`update-workcase` 等）时，**一律不提供
`arguments.workspace_root`**。依赖规范 02 §6.2 与 §10.1 定义的自动发现机制：
不传时，CLI 以 cwd（应在实际 Git worktree 内）作为定位符，从该 worktree 根沿父
目录链向上查找 `LDVH-GOVERNED-PROJECTS.yaml`，跳过仓库内同名文件，遇第一个
候选即停；不从定位符子路径、`cwd`、Git common-dir 或平行目录另开查找路径。

下列情形才可传 `workspace_root`：
- Human 在当次会话中明确指定了一个工作区根路径；
- 传值时只在该路径下读取配置，不向上查找，也不从其它来源增加发现路径。

AI 不得自行猜测或传递路径。若自动发现返回 `missing`，如实报告给 Human，由 Human
决定是否显式指定工作区根，AI 不得另猜路径重试。

此纪律不改变 Code 行为，只约束 AI 调用方式。违反纪律会关闭自动发现并造成
配置 miss，其故障根因在调用方而非 Code；审计追溯由 02 §6.2-5 强制返回实际
选定配置与依据兜底。

## WorkCase 创建路由纪律

当 AI 将要调用 `create-fact-object` 创建一个 WorkCase（fact_type_key=workcase）时，
在提交 Human Gate 1 之前，必须经 Helper 读取规范 21 §4.3 与 §4.4，及当次适用
行动模板的 Stop Conditions，照其逐项审核 work items 与 success_criterion_definitions
是否吸收生命周期关口或 Human Gate；不得凭本文件概括替代规范与模板原文。

此纪律不改变 Code 行为，只约束 AI 审核责任；机械测试无法替代。

## 如实报告

区分并报告：**已验证**（当次实际跑通并有输出）、**未验证**（需要真实会话或
真实事件才能证明的，如自动加载）、**不支持**（权威资料或范围匹配观察肯定证明
无此能力）。不要把"文件存在""技能已启用"或"shell 直调成功"写成"已接入"。
