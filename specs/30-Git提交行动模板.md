# Git 提交行动模板

```yaml
ldvh_spec:
  spec_key: "git-commit-action-template"
  spec_id: "30"
  spec_kind: "spec"
  title: "Git 提交行动模板"
  status: "active"
  canonical_path: "specs/30-Git提交行动模板.md"
  parent_spec: "action-template-foundation"
  relation: "refines"
  positioning: "定义 Human 已明确授权创建本地新 Git commit 时，对目标变化与既有 Index 的隔离、规则与验证覆盖、实际创建、环境结果回读和目标残留交还的可复用行动结构"
  scope: "AI 在一个身份和目标范围可确定的 Git worktree 中准备、创建和验证本地新 commit；不包含 push、PR、amend、rebase、merge、tag、Git Hook 或 CI 变更"
  basis:
    - "action-template-foundation"
    - "work-object-governance-scope"
    - "source-of-truth-traceability"
  authorized_attachments: []
```

> 文件状态：`active`。本文已经完成独立复核、定点修改、通用声明解析 Code、风险匹配 tests 和激活检查；在其余当前规则源资格条件成立时进入当前规则源。`active` 和声明可解析只证明规范侧模板身份，不自行授予任何一次 Git 写入权限，也不证明 Git 执行封装、Helper 模板操作、Git Hook、Skill 或环境接入已经实现、可用或通过验证。

## 1. 价值判断

本文候选的价值，是在 Human 已经明确要求创建本地 Git commit 时，复用一套薄行动结构，把当次目标、实际 worktree、Working Tree、Index、适用项目规则、验证、真正进入 commit 的快照、提交后历史锚点和剩余变化联系起来，减少误提交无关变化、漏读规则、漏验、只凭命令成功声明完成以及把 commit 扩张成 push、PR 或上层工作完成的风险。

本文主要服务 V1 快速定位、V2 充分理解、V3 边界识别、V4 稳定推进、V5 据实判断、V6 工作接续和 V7 清晰沟通。V8 持续积累来自把重复行动结构维护在同一当前来源，而不是复制到 Skill、Agent、Git Hook、项目说明或 Code。01 和 03 已经定义 Index、`HEAD`、commit 与证明边界，06 已经定义模板共同规则；本文的独有价值只来自把 Human 目标、用户既有 Index、项目规则、范围匹配验证、既有 Git Hook 实际结果和提交后目标残留组织成同一个 Git 行动边界。该剩余结构不能成立时，本文应取消而不是扩写。

本文不把 Git 提交变成所有修改的必经步骤。没有本文、本文仍为草案、本文不适用或没有其它具体模板时，AI 仍按当前规则源和 Human 指令普通求解；具体模板不是行动可执行性、规则合规性或能力可用性的前置证明。

## 2. 规范依据

本文直接依据：

1. `action-template-foundation`：定义具体模板的准入、稳定身份、适用、授权、步骤、验证、回写和交还共同边界，并禁止模板复制领域规则或扩张行动授权；
2. `work-object-governance-scope`：定义工作对象、实际 Git worktree、管辖范围解析及其不产生行动授权的边界；
3. `source-of-truth-traceability`：定义 Working Tree、Index、`HEAD`、Git history、commit message 声明和提交结果的作用边界，并把具体提交行动留给经证明成立的模板或项目策略。

`code-engineering-practices`、具体领域规范、项目正式规则、Human 当前指令及实际 Git/测试能力按当次对象提供输入、验证和行动边界，但不是每次 Git 提交共同成立所必需的直接规范依据。本文不得把它们的字段、枚举、命令、测试集合、branch 策略、message 格式、Git Hook 或实现接口复制为自身规则。

未经当前规则源采纳的模板、附件、Skill、validator、Git Hook、WorkCase 和实例不取得当前效力。本文不自行恢复未被当前规则源定义的 Conventional Commit 契约、固定七结构、全局 validator/Git Hook、自动提交或文件类别触发的普遍 Human Gate；受管辖项目的共同拆分和 message 基线由 `source-of-truth-traceability` §9 定义，本文只组织消费。

## 3. 职责边界

本文负责定义：

1. 创建一个本地新 Git commit 的候选进入条件、排除条件和不确定处理；
2. 当次目标、实际 worktree、Working Tree、Index、适用规则、验证和授权如何进入行动；
3. 目标变化与无关既有变化的隔离、提交候选快照核对、commit 创建、写后回读和失败分流的稳定关系；
4. commit 成功、部分结果、未提交、未验证和剩余变化的交还边界；
5. 本模板停止使用、被替代或无法适用时回到普通求解的边界。

本文不负责定义：

1. Git 对象模型、Working Tree、Index、`HEAD`、history 或 commit message 的一般语义；
2. 提交时机、提交拆分、message 格式、type/scope、签名、branch、Git Hook、CI 或测试门禁等领域或项目强制规则；
3. Human 是否已经授权当次提交，或者修改文件、验证通过、模板命中是否自动产生提交授权；
4. Git 命令、参数、暂存算法、锁、错误码、API、Code 模块、测试实现或环境工具映射；
5. push、PR、amend、rebase、merge、cherry-pick、tag、release、Git Hook/CI 安装或远端 ref 变更；
6. 把 commit 创建解释为事实正确、验证通过、Human Gate 完成、发布、部署、远端同步或上层工作完成；
7. 单次执行日志、模板运行状态、receipt 或新的事实对象 Schema。

项目正式规则负责项目强制政策；具体领域来源负责其对象与验证条件；Human 当前指令和实际来源负责授权；AI 负责理解目标、判断模板适用性、选择实际规则、区分目标与无关变化、形成 message 语义并审核结果；Git、Code 和 tests 只在实际可用范围内提供确定性观察、校验和状态变更。模板只组织这些责任，不取得其定义权。

## 4. 适用范围

本文候选只在以下条件同时成立时适用：

1. Human 当前指令已经明确授权创建本地新 Git commit，或当前 WorkCase 的 `execution_authorization` 已逐项列明该本地 commit、实际目标范围与风险边界且 `execution_approval` 正在准确消费该授权；实际适用的项目与领域规则还必须允许在相应条件下执行，项目或领域规则自身不得被推定为 Human 的当次写入授权；
2. 目标工作对象能够绑定到唯一实际 Git worktree；
3. 本次准备提交的目标变化范围能够依据 Human 目标、当前来源和实际差异确定；
4. 实际 Git 状态、必要差异和当次可能适用的项目规则与验证入口可以读取；
5. 不需要通过本模板实施 push、PR、amend、rebase、merge、tag、Git Hook/CI 安装或其它排除行为。

以下场景不适用：

1. Human 只要求查看 Git 状态、审查历史、解释规则、建议 message 或预估如何提交，没有要求创建 commit；
2. 修改已经完成，但既没有 Human 当前指令的直接提交授权，也没有当前 WorkCase 授权包逐项列明并已获批准的本地 commit；
3. 目标不是 Git worktree，或者 repo、worktree、目标变化范围无法唯一确定；
4. 目标主要是修订历史、同步远端、建立 PR、安装门禁或执行其它排除行为；
5. 另一当前模板具有更精确且已经成立的适用边界，当前行动应由该模板承接。

信息不足时，AI 可以继续只读检查 Git 状态、差异、来源规则和验证结果；不得为了套用模板而猜测目标范围、授权、项目政策或应提交内容。

## 5. Git 提交行动模板定义

### 行动模板声明

| template_key | summary | definition_ref |
|---|---|---|
| `git-commit` | 在已有明确授权和唯一目标 worktree 中，按当前来源组织本地新 commit 的范围核对、验证、创建、回读与交还 | `git-commit-action-template::5. Git 提交行动模板定义` |

### 5.1 输入与前置条件

执行者必须取得并区分：

1. Human 当前明确给出的本地新 commit 目标和授权范围，或当前 WorkCase 中逐项列明该 commit、目标变化、允许副作用、风险边界与禁止动作的 `execution_authorization` 及其有效 `execution_approval`；项目规则、模板命中、修改完成或测试通过不能替代该授权；
2. 目标工作对象、实际 Git worktree 及需要时的管辖解析结果；
3. 当前 branch/`HEAD` 状态（包括 detached、unborn、无首个 commit 或不可解析状态）、Working Tree、Index、未跟踪内容和足以判断目标范围的实际差异；
4. 当次实际检查过的项目提交政策、领域规则、验证要求和能力入口，以及各自作用范围、未检查、不可读取或身份不清的缺口；
5. 已经执行的验证及其对象、版本、范围、结果和未验证部分；
6. 可能属于用户、其它事项、其它执行者或其它提交的既有变化；
7. 对受管辖目标，03 定义的 `precheck-git-commit` 当次是否可用，以及准备直接传入该操作的完整 message。

静态文件名、过期模板、工具安装、缓存结果、旧 status/diff、另一 worktree 的结果或 AI 记忆不得替代当前输入。只在实际检查范围内未发现项目特定 message、拆分、branch 或 Git Hook 规则时，只能报告该有限结果及未检查或不可读取范围；不得扩大为项目不存在规则，也不得用过期契约、行业惯例或自身偏好补造全局要求。

### 5.2 参与者、能力与授权

1. AI 执行者负责模板召回、适用判断、来源选择、范围和差异语义审核、验证覆盖判断、message 语义、失败分流和最终交还；
2. Human 只承担当前来源保留的提交授权、目标取舍、破坏性历史操作、无法安全隔离的混合变化取舍或风险接受；清楚的直接授权已经存在，或当前 WorkCase Gate 1 已通过准确 `execution_approval` 批准逐项列明的本地 commit 时，不重复请求；
3. `precheck-git-commit` 只对受管辖目标的当前真实 Index 与完整 message 提供机械预检；其 `passed` 不承担 AI 语义审核、Human 授权、项目验证、commit 创建或原生 Git Gate 结果；
4. Git、Code、tests 和环境工具只提供实际支持的状态读取、差异、暂存、验证、commit 创建和回读能力；静态存在不证明当次可用；目标仓库中已经生效的 Git Hook 可能由 Git 自动执行，属于实际环境条件；
5. 本模板不安装、修改、禁用、绕过或定义 Git Hook，也不要求特定 Skill、Agent、validator、Git 子命令或平台接口。未来薄接入只能调用同一当前模板和相应能力，不得复制正文或项目规则；
6. 模板命中、Helper 预检或测试通过、文件已经修改或存在待提交变化都不授予 commit、push 或其它行动权限。WorkCase approval 只有在 `execution_authorization` 已逐项列明本地 commit 及其范围时才授权该 commit，不得从一般“执行计划”措辞推定，更不得扩张为 push、PR、发布、外部消息或其它远端副作用。

### 5.3 行动步骤与分支

#### A. 建立当次提交边界

1. 根据 Human 目标定位唯一实际 Git worktree；
2. 读取当前 Git 状态和必要差异，分别识别 Working Tree、Index、未跟踪内容和当前历史锚点；
3. 将准备提交的目标变化与无关、来源不明、属于其它事项或尚未获准的变化分开；
4. 定位并读取实际适用的共同提交契约、项目提交政策、领域规则和验证要求，记录实际检查来源、作用范围及未检查、不可读取或身份不清的缺口；`governed_single` 目标必须消费 `source-of-truth-traceability` §§9.1–9.6，明确 `non_governed` 时不因该契约不适用而阻断普通求解；
5. 如果目标、授权、worktree 或变化归属无法确认，暂停状态变更，只交还已观察范围和需要补充的决定。

#### B. 形成可提交候选

1. 在不丢弃、覆盖、回退、隐藏或静默改写无关变化和用户既有 Index 的前提下，形成只覆盖当次已授权目标的提交候选快照；若能力需要临时改变 Index，只能改变本模板当次引入、可明确归属且可验证的内容，并保留改变前依据；
2. 受管辖目标按 `source-of-truth-traceability` §9.2 判断一个可共同说明、验证和回退的主要目的；普通拆分由 AI 依据该来源判断，需要 Human 决定时只按 `source-of-truth-traceability` §12(6) 进入 Human Gate；项目来源要求更细拆分、目标范围无法共同说明、验证不能共同覆盖或候选无法安全隔离时，按实际来源拆分或缩小范围；模板不自行建立拆分政策；
3. 执行来源要求且与候选快照匹配的验证。验证失败、未运行、过期、对应其它 worktree 或不能覆盖目标时，按来源规则修正、缩小声明或暂停；只有来源明确把风险接受保留给 Human 时，Human 才能决定是否在相应范围继续；不可绕过的门禁不能由确认替代；
4. 根据候选快照、Human 目标、受管辖目标适用的 `source-of-truth-traceability` §§9.3–9.4、项目附加 message 规则和实际验证形成提交说明。明确非受管辖且没有项目格式规则时，提交说明仍必须据实描述实际变化，不得声称未发生的验证、Git Gate 结果、完成、push 或发布；
5. 目标为 `governed_single` 且 `precheck-git-commit` 当次可用时，必须把完整 message 直接作为 `arguments.message` 调用该公开操作；只有 Helper 外层 `outcome` 为 `ok` 且提交机械预检结果为 `passed`，才继续机械合规路径。`failed`、`unverifiable`、`unavailable` 或调用错误按 03 分流并保留诊断；Helper 不可用时如实记录能力缺口，并按实际来源判断能否继续，不得把未调用改写为通过；
6. AI 必须独立审核主要目的、拆分、简体中文语义、description 真实性、body 充分性以及验证与风险是否据实，不得把 Helper 机械结果、测试通过或 Human 授权当作语义审核；
7. 完整 message 默认只保留在当前进程内并直接交给 Helper 和 Git，不得在 Git Working Tree 内创建 `.codex-commit-msg.tmp`、`COMMIT_EDITMSG` 副本或其它临时提交消息文件。确有外部工具只接受文件路径时，只能使用 Working Tree 外的系统临时文件并在调用后清理；
8. 按 `source-of-truth-traceability` §9.5 在创建 commit 前重新核对实际候选快照、目标路径、完整 message、管辖结果、03 来源身份和验证范围；任何变化都使先前 Helper 结果和 AI 结论失效，必须回到本阶段重新预检和审核，不得以最初计划替代当前快照。

#### C. 创建、回读与验证

1. 只有授权、目标快照、来源要求、必需验证、适用的 Helper 预检和 AI 语义审核均达到实际允许执行的范围后，才使用与预检相同的完整 message 直接调用当次可用的 Git/Code 能力创建一个本地新 commit；目标仓库已经生效的原生 Git Gate 仍由该真实 Git 事件重新检查实际 message、Index 与 worktree，Helper 结果不得替代 Git Gate；
2. 失败、拒绝、无变化、Git Hook 修改或拒绝、部分结果、结果不可观察或 `source-of-truth-traceability` §9.6 所述不合规时，保留实际 Git 状态和诊断，不得重试破坏性操作、扩大路径、禁用既有 Git Hook 或绕过门禁；
3. commit 返回成功后，为核对 `source-of-truth-traceability` §§9.3–9.6，重新读取实际 `HEAD`、新 commit 的完整 message 与内容范围，以及剩余 Working Tree 与 Index；
4. 只有新历史锚点存在、实际提交快照与已授权目标一致，并且回读结果支持相应声明时，才报告本地 commit 创建成功；
5. 提交后仍存在目标相关变化、验证缺口、无关变化或其它未完成事项时，分别交还，不把它们隐藏在成功结论中。

步骤只规定语义关系，不要求固定 Git 命令或线性实现。安全且来源允许的读取和验证可以并行；目标快照最终核对、commit 创建和写后回读必须保持因果顺序。

### 5.4 输出、验证、回写与交还

当次交还至少应使消费方能够区分：

1. 实际目标 repo/worktree 和提交范围；
2. commit 是否实际创建；创建时的新 commit 身份和实际内容范围；
3. 实际执行的验证、对应对象和范围、通过、失败、未运行与不可观察部分；
4. 受管辖目标实际调用 Helper 时的原始请求与结果、AI 语义审核结论，以及原生 Git Gate 的实际结果或当次未安装/未触发范围；
5. 提交说明所依据的项目规则、实际检查过的来源与作用范围，以及未检查、不可读取或身份不清的缺口；只在该有限范围内报告未发现额外格式规则；
6. commit 前后 Working Tree 内临时提交消息文件的检查结果，以及外部系统临时文件的清理结果（如有）；
7. commit 后剩余的 staged、unstaged、untracked 和无关变化；
8. 被拒绝、未执行、部分完成或需要 Human 决定的内容；
9. push、PR、发布及其它排除行动仍未由本模板执行；
10. 可以继续普通求解、修正、重试或保持暂停的入口；普通非 WorkCase 行动需要时可以另行授权，已获 Gate 1 批准的 WorkCase 则按 §7 收敛而不在执行期询问扩权。

交还形式按当前消费方调整，不建立固定机器字段或 Helper 响应 Schema。Git commit 和当次输出默认只承担历史锚点与过程结果；确需把验证结论、风险、决定或经验长期写入项目事实源时，必须由相应来源规则及需要时事实模型另行准入、写入和回读。本模板不创建运行记录事实类型。

### 5.5 变更、退出与普通求解

本模板的适用条件、核心步骤关系、失败分流、验证或交还发生稳定变化时，必须重新执行 06 的准入和复核；单次使用的命令、临时测试、message、路径或人员不修改模板。

重复价值消失、现有规范或普通求解能够以更低成本承接、模板开始复制项目政策，或者未来更准确的模板承接本责任时，应缩减、替代或退出本模板。模板不存在、仍为草案、不可发现、不适用或能力不可用时，AI 继续按 Human 指令和当前规则源普通求解，不得把模板缺失解释为 Git 提交被禁止或相关规则失效。

## 6. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| 独立规范责任与模板准入 | 准备把本文从 `draft` 改为 `active` 时 | 01 §13.5 要求的记录已经由独立复核者主动比较 02、03、06、07、项目规则、Code 和普通求解；重复价值、独立失败和净价值仍成立 | 准入调查、独立复核意见、主执行者处置和代表性场景 | 对照 01、06 和调查记录审核 | 本规范责任和 `git-commit` 模板准入 | 保持 `draft`；缩减、合并到现有来源或取消候选 |
| 模板身份与声明 | 新建、移动、改名或替代模板时 | `template_key` 唯一、未改派；声明结构和 `definition_ref` 精确指向本 H2；规范身份与路径一致 | 本文、06、当前规则源候选扫描 | 规范结构与声明解析检查 | 当次规范与模板身份 | 不发现或消费模板；修正身份和声明 |
| 规则与模板边界 | 修改步骤、Git Gate、验证或交还时 | 本文只组织来源读取、行动关系和失败分流，没有定义 message、branch、拆分、测试、Git Hook 或实现政策 | 本文、02、03、06、07、项目规则和差异审核 | 来源逐项对照和正反场景走查 | 当次修改及直接相邻责任 | 移除复制内容，回到正确来源定义；保持 `draft` 或暂停受影响模板 |
| 适用与授权 | 准备使用模板或创建 commit 时 | Human 当前指令已直接授权本地新 commit，或当前 WorkCase 的 `execution_authorization` 已逐项列明且有效 `execution_approval` 覆盖该 commit；实际来源未禁止且相应限制已经满足，repo/worktree 和目标范围唯一，排除行为未被隐含纳入 | Human 当前指令，或当前 WorkCase 授权包与批准；管辖/工作对象结果、Git 状态和适用来源 | AI 适用判断与来源回读 | 当次 repo、目标范围和本地 commit | 不执行状态变更；普通行动补充输入或缩小范围，获批 WorkCase 中未授权或超界的 commit 按本文 Human Gate 收敛 |
| 提交候选范围 | 形成候选及创建 commit 前 | 候选快照只包含已授权目标；用户既有 Index 及无关或来源不明变化未被丢弃、覆盖、隐藏或静默纳入；临时 Index 变化仅属本次且可回读撤销 | 改变前后 status、必要 diff、候选快照、Human 目标和来源 | Git 只读观察及 AI 差异审核 | 当次候选快照与可归属临时变化 | 取消创建；只撤销本次可归属且可验证的临时变化并回读；不能安全撤销时保持实际状态并交还，不重置用户既有 Index |
| 验证与 message 声明 | 准备创建及交还时 | 实际来源要求的验证已按当前候选执行；受管辖且 Helper 可用时，完整 message 已直接通过 `precheck-git-commit` 取得 `passed`；AI 语义审核独立完成；message 与完成声明没有超出实际变化、验证和 Git Gate 结果 | 项目/领域规则、实际测试结果、候选快照、Helper 原始请求/结果、AI 审核和 message | 来源规定的验证入口、Helper 直接调用及 AI 对照审核 | 当次已执行机械预检、语义审核、验证和声明 | 修正、缩小声明、标记未验证或暂停；不得绕过来源门禁或用 Helper 替代 AI 审核 |
| 提交消息交付边界 | 形成 message 至 commit 返回后 | 完整 message 直接传给 Helper 与 Git；Working Tree 内没有临时提交消息文件；外部工具确需文件时只使用系统临时目录且调用后已清理 | 提交前后状态、临时文件检查、Helper 请求和实际 commit message | Working Tree 回读、系统临时文件回读及 Git message 回读 | 当次 worktree、message 交付和确有使用的外部临时文件 | 不创建 commit 或不声明闭环；删除本次可归属的外部临时文件并回读，Working Tree 内出现消息文件时先停止并按实际归属处置 |
| commit 创建与回读 | Git 返回后准备声明成功时 | 新 commit 实际存在，身份、实际 message 与内容范围已回读，和已授权目标一致；既有原生 Git Gate 只在真实 Git 事件中复检，其拒绝、修改或其它可观察结果及剩余 Working Tree/Index 已纳入判断 | 实际 Git 结果、`HEAD`、commit 内容、Git Gate/Git Hook 可观察诊断和提交后状态 | 当次 Git/Code 入口及只读回读 | 当次本地新 commit、环境结果与已观察剩余变化 | 不声明成功或完整完成；报告拒绝、修改、部分结果、实际残留和可安全继续入口 |

本文所涉模板发现、Git/Code、Skill、Git Hook 与环境能力声明，按 00 §9 及上表对应验证对象判断。

## 7. Human Gate

本文不因普通只读检查、模板召回、规则定位和已有明确授权下的安全提交步骤新增重复 Human Gate。普通非 WorkCase 行动出现以下情况时，必须进入实际来源保留给 Human 的决定：

1. 目标 repo、worktree、准备提交的变化归属或授权范围无法从当前输入和来源唯一确定，并且继续需要替 Human 选择；
2. 无法在不改变、覆盖、丢弃或混入无关既有变化的情况下形成目标提交快照；
3. 实际来源明确允许 Human 接受验证失败或未验证范围的风险；来源规定为不可绕过的强制门禁时，Human 不能使其通过，只能选择补充验证、修改目标、取消提交或按权威来源的变更规则另行修订规则；message 与实际候选不一致时只能修正 message、修改目标或取消提交，Human 不能使不实声明成立；
4. 实际行动需要 amend、rebase、reset、清理、覆盖用户既有 Index、Git Hook/CI 安装或修改、push、PR、远端 ref 或其它本模板排除的副作用；
5. 项目规则、Human 目标和当前 Git 状态冲突，来源关系无法决定应修改目标、拆分、保持现状还是放弃提交。

Human 决定的复用按 00 §10 执行；Human 当前指令已经授权相应行动，且适用于该行动的全部来源规则许可条件已经成立时，不重复请求同一决定。Human 决定不能使错误 repo、超范围快照、虚假 message、未执行 Git 命令或未回读 commit 自动成立，也不能把本地 commit 扩张为 push、PR 或工作完成。

当前 WorkCase 已经通过 Gate 1 时，上述情况不得在执行期转化为追加授权询问。只有逐项列明且仍位于 `execution_authorization` 边界内的本地 commit 可以继续；未列明、范围扩大、需要接受新风险、无法安全隔离，或实质变成 amend、rebase、reset、push、PR、发布、外部消息等排除行动时，不执行该 commit，并按 21 与 34 据实取消或收敛受影响 item，继续 Controller 自检、独立结果复核和 Gate 2。模板步骤、执行者切换或准备调用 Git 能力本身都不是新的 Human Gate。

## 8. Stop Conditions

出现以下任一情况时，必须暂停受影响的 commit 创建或相应成功声明：

1. 既没有 Human 当前指令的明确提交授权，也没有当前 WorkCase 中逐项列明并获批准的本地 commit，或者只因文件已修改、模板被发现、测试通过或存在 staged 变化就准备提交；
2. 目标 repo、实际 worktree、当前 Git 身份或准备提交范围无法唯一确定；
3. 未读取当前 status 和支持范围判断的必要差异，或者使用旧缓存、另一 worktree、Index/`HEAD` 旧内容替代当前观察；
4. 候选快照混入未获准、来源不明或属于其它事项的变化，或者为了形成候选准备丢弃、覆盖、回退、隐藏无关变化或用户既有 Index；
5. 项目或领域来源要求的验证未完成、失败或不覆盖当前候选，却准备绕过要求或声明完整验证；
6. message、验证或完成声明超出实际候选快照、来源、证据、Git Gate 或可观察结果；
7. commit 创建失败、被拒绝、部分完成或无法回读，却准备声明本地历史锚点已经形成；
8. 提交后没有核对新 commit 和剩余 Working Tree/Index，或者目标相关残留和无关变化准备被静默省略；
9. 准备通过本模板执行或暗示已经执行 push、PR、amend、rebase、merge、tag、发布、Git Hook/CI 安装、修改、禁用或绕过；目标仓库既有 Git Hook 随 Git 自动执行不属于模板安装或主动调用，但其实际结果必须回读；
10. 模板正文、Skill、Agent、Git Hook、Code 或项目说明正在复制另一来源的 message、branch、拆分、验证或授权规则，形成第二权威；
11. 本文仍为 `draft`、声明无效、定义来源冲突或具体模板不适用，却准备以其当前规则源效力约束行动；AI 的普通求解不因此停止。
12. 目标为受管辖项目且 `precheck-git-commit` 当次可用，却准备跳过 Helper 预检，或者候选、完整 message、worktree、管辖、来源、验证变化后仍复用旧结果；
13. 准备在 Git Working Tree 内创建临时提交消息文件，或者外部工具使用的系统临时文件没有清理与回读计划。

暂停范围与允许继续的行动按 00 §11 执行；对本模板，只有授权、目标身份、候选范围、来源要求、验证、commit 实际结果和回读达到对应成立条件，或声明缩小到现有依据实际支持的范围后，才能恢复受影响的路径、快照或声明。
