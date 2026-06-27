# git-commit-action-Git提交行动编排

```yaml
v2_spec:
  spec_id: "31"
  spec_kind: "member_spec"
  title: "git-commit-action-Git提交行动编排"
  status: "active"
  authority: "active"
  canonical_path: "specs/31-git-commit-action-Git提交行动编排.md"
  created: "2026-06-24"
  updated: "2026-06-24"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "定义 AI 准备、拆分、预检、创建和交还 LDVH Git commit 时的薄行动入口与能力资产编排"
  scope: "用户要求提交 LDVH 事实源或产品资产变更、修复提交消息、拆分 staged changes、执行提交预检、追溯提交行动证据时的 AI 行动流程"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/03-行动编排规范.md"
    - "specs/07-事实源边界与Git追溯规范.md"
  related_specs:
    - "specs/04-Code确定性执行规范.md"
    - "specs/05-Web信息同步规范.md"
    - "specs/06-运行时扩展规范.md"
    - "specs/08-测试基础规范.md"
    - "specs/attachments/03.Att.01-成员身份字段表.md"
    - "specs/attachments/03.Att.02-成员主文件骨架模板.md"
    - "specs/attachments/06.Att.02-固定运行时扩展登记表.md"
    - "specs/attachments/07.Att.02-Commit-Type枚举表.md"
    - "specs/attachments/07.Att.03-Commit-Scope允许枚举表.md"
    - "specs/attachments/07.Att.04-Commit-Body必填条件表.md"
    - "specs/attachments/07.Att.05-Commit-Message样例集.md"
    - "specs/attachments/07.Att.07-Git提交留痕范围表.md"
    - "specs/attachments/07.Att.08-Commit-Message字段表.md"
    - "specs/attachments/07.Att.09-关联提交派生优先级表.md"
  migration_sources:
    - "history/specs-v1/44-git-commit-orchestration-Git提交编排.md"
  active_fact_source:
    - "specs/31-git-commit-action-Git提交行动编排.md"
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "git_commit_action"
    - "assurance_takeover"
    - "capability_assets"
  migration_status: "partially_migrated"
```

```yaml
v2_action_member:
  spec_id: "31"
  kind: "action_process"
  name_en: "git-commit-action"
  name_zh: "Git提交行动编排"
  collection_status: "active"
  canonical_path: "specs/31-git-commit-action-Git提交行动编排.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover:
    - "source_spec=specs/03-行动编排规范.md; requirement=流程复用要求; scope=AI 准备、拆分、预检、创建和交还 Git commit 的可复用行动流程"
    - "source_spec=specs/07-事实源边界与Git追溯规范.md; requirement=Git 提交流程归口; scope=commit records 和 message 契约之外的执行责任、验证责任、证据位置和失败分流"
    - "source_spec=specs/06-运行时扩展规范.md; requirement=Skill/Hook/Rules 能力资产协作; scope=提交行动所需 Skill、Hook registry、Rules 入口和环境适配边界的流程映射"
    - "source_spec=specs/08-测试基础规范.md; requirement=验证声明边界; scope=提交前后验证命令、失败阻断和等价验证说明"
  capability_assets:
    - "type=rule; path=rules/LDVH-RUNTIME-PROTOCOL.md; purpose=LDVH 产品资产维护时定位 Git 提交行动入口; status=required"
    - "type=rule; path=rules/LDVH-RUNTIME-PROTOCOL.md; purpose=管辖项目 Git 追溯或提交准备时定位事实源与行动入口; status=required"
    - "type=skill; path=skills/ldvh-git-commit/SKILL.md; purpose=将 07 的提交契约转换为 AI 可执行的提交准备和预检流程; status=required"
    - "type=hook; path=hooks/ldvh-hooks.yaml; purpose=登记 git.commit-msg 统一事件和阻断命令; status=required"
    - "type=code; path=code/commit_validate.py; purpose=确定性检查 commit message 契约和提交正文质量; status=required"
    - "type=code; path=code/hook_dispatch.py; purpose=按统一 Hook registry 执行 git.commit-msg 事件; status=required"
    - "type=code; path=code/install_git_hooks.py; purpose=把 git.commit-msg 接入当前仓库 native commit-msg hook; status=conditional"
    - "type=web; path=web/docs/06-Changelog.md; purpose=Human-facing 展示 commit body、解析字段和提交详情; status=required"
    - "type=web; path=web/docs/05-ProjectFiles.md; purpose=工具页展示 Git status、diff、提交历史和提交详情; status=required"
    - "type=ci; path=future-ci/server-side-git-gate; purpose=本地 Hook 可绕过时的后续兜底方向; status=planned"
  code_consumption:
    - "action_member_identity"
    - "action_member_anchors"
    - "git_commit_action"
    - "assurance_takeover"
    - "capability_assets"
```

```yaml
ldvh_member:
  spec_id: "31"
  kind: work_process
  name_en: git-commit-action
  name_zh: Git提交行动编排
  collection_status: active
  canonical_path: specs/31-git-commit-action-Git提交行动编排.md
  code_consumption:
    - workflow_index
    - git_commit_action
  assurance_takeover:
    - "source_spec=specs/03-行动编排规范.md; requirement=流程复用要求; scope=AI Git 提交行动流程"
    - "source_spec=specs/07-事实源边界与Git追溯规范.md; requirement=Git 提交流程归口; scope=提交执行、预检、交还和证据留存"
  capability_assets:
    - "type=skill; path=skills/ldvh-git-commit/SKILL.md; purpose=AI 提交准备; status=required"
    - "type=hook; path=hooks/ldvh-hooks.yaml; purpose=commit-msg 统一事件; status=required"
    - "type=code; path=code/commit_validate.py; purpose=提交消息确定性预检; status=required"
```

> 文件状态：本文是 active 行动编排成员主文件。本文只接管 Git 提交行动的执行责任、验证责任、证据位置、失败分流和能力资产编排；commit message 本体规则、Git records 追溯性质和关联提交派生规则仍以 `specs/07-事实源边界与Git追溯规范.md` 及其授权附件为准。

## 1. 本文解决的问题

本文定义 AI 在 LDVH 场景中如何准备、拆分、预检、创建和交还一次 Git commit。

本文解决：

1. 用户要求“提交”“先提交”“修复提交信息”时，AI 进入哪个行动入口；
2. AI 如何读取最小 Context，避免只靠记忆或聊天约定提交；
3. Skill、Code validator、Hook registry、Web 展示和环境适配各自如何协作；
4. 何时必须暂停、拆分、回到 Human Gate 或记录问题原因；
5. 提交行动过程如何留下可追溯证据，尤其是 Skill runtime 调用与手动等价执行的区别。

本文不定义 commit message 格式、type/scope/body 闭集、提交语言、Git records 的事实源追溯性质、Web 页面布局、Hook 资产登记、环境安装方式或 CI 实现。上述内容分别由 07、05、06、08 和后续环境适配或 CI 工作承接。

## 2. 上位依据

本文承接 `specs/03-行动编排规范.md` 的成员机制、Context、Scenario、Gate、执行、问题分流、回写和证据原则。

本文承接 `specs/07-事实源边界与Git追溯规范.md` 的事实源、Git 追溯和 commit message 契约边界。07 定义“提交记录应该长什么样”和“提交记录如何作为追溯证据”；本文定义“AI 如何完成一次提交行动”。

本文承接 `specs/06-运行时扩展规范.md` 的 Rules、Skill、Hook 和环境适配边界。本文可以调度固定能力资产，但不得声明用户环境已经安装或原生支持这些资产。

## 3. 构成要素归属与价值判断

本文属于六类构成要素中的行动编排。

正向价值判断：

| 价值 | 本文如何服务 |
|---|---|
| V1 快速定位 | 用户要求提交时，AI 能直接定位 31、07、Skill 和 validator |
| V2 可行动理解 | 把提交行动拆成 Context、Scenario、Gate、执行和交还 |
| V3 正确判断 | 让 AI 区分规则权威、执行入口、能力资产和环境安装状态 |
| V7 证据沉淀 | 要求记录验证命令、预检结果、commit hash 和 Skill 调用方式 |
| V8 可靠回写 | 事实源修改最终通过真实 Git commit records 追溯 |

反模式：

| 反模式 | 本文必须阻止 |
|---|---|
| 把 Skill 文件当成已调用 | 未发生 runtime 调用时，必须说明是手动等价执行 |
| 把 Hook registry 当成已安装 | `hooks/ldvh-hooks.yaml` 存在不等于环境已接入 |
| 把 31 写成提交规则 | 提交格式和 message 契约只能回到 07 |
| 为了通过提交而混入无关文件 | 无关 staged changes 必须暂停或拆分 |
| 用私有 trailer 代替语义正文 | 提交正文应按 07 写自然语言语义说明 |

## 4. 行动定位与适用场景

本文定位为 Git 提交行动的薄入口。它只管理一次稳定 AI 行动如何进入、读什么、调度哪些能力、何时暂停、如何验证、如何交还和如何留证。

适用场景：

1. 用户明确要求提交当前 LDVH 变更；
2. 用户要求先提交、修复提交信息、拆分提交或检查提交规范；
3. AI 完成事实源、规范、Code、Web、Rules、Skill、Hook 或测试修改后，需要通过 Git records 追溯；
4. commit validation 失败，需要解释、修正并重新预检；
5. 需要判断当前提交行动是否由 Skill runtime 执行，或只能按 Skill 文件手动等价执行。

进入本文的第一道判断不是 commit message，而是本次处理内容是否命中管辖项目。AI 在准备提交前必须先以 staged paths、显式 target 或 repo root 运行等价的管辖判定；若命中管辖项目，本文和 `ldvh-git-commit` Skill 成为必经行动入口。不得只因为最终 `commit-msg` hook 通过，就宣称已完成 Git 提交行动编排。

## 5. 准入条件

进入本文前必须满足：

1. 当前目录位于 Git 仓库中；
2. 用户目标包含提交、提交准备、提交修复、提交预检或事实源修改追溯；
3. AI 能读取 `git status --short`，并能区分 staged 与 unstaged 变化；
4. 本次提交目标可被描述为一个原子意图，或可拆分为多个原子意图；
5. 若要修改环境安装、native Git hook、IDE、Codex settings 或 CI，必须把该部分排除出本文，另行走 06 的环境适配边界。

不满足准入条件时，AI 应停留在当前任务、事实源回写或临时核对动作中，不得冒充已进入提交流程。

## 6. 事实源边界

事实源边界如下：

| 内容 | 权威归口 |
|---|---|
| commit message 契约、type/scope/body、语言和关联提交派生 | 07 及其授权附件 |
| AI 提交准备、拆分、预检、提交和交还流程 | 本文 |
| Skill 执行说明和运行时承载物自描述 | `skills/ldvh-git-commit/SKILL.md` 与 06 |
| Hook 事件登记和 dispatcher 调用 | `hooks/ldvh-hooks.yaml`、`code/hook_dispatch.py` 与 06 |
| commit message 确定性检查 | `code/commit_validate.py` 与 04 |
| native Git hook 安装器 | `code/install_git_hooks.py` 与 04/06 |
| commit 展示、最近提交、提交详情和 ProjectFiles 提交历史 | 05 与 Web docs/实现 |
| 环境安装、native hook、用户 hook manager、IDE 或 CI 接入 | 06 环境适配，不由本文默认声明 |

本文产生的检查摘要、提交草稿、命令输出和行动说明默认是过程输出。只有写入对应事实源并经 Git commit records 追溯后，才成为稳定事实。

## 7. Context 要求

AI 进入本文时应最小读取或查询：

1. `git status --short --untracked-files=all`；
2. staged files 和必要 diff；
3. `skills/ldvh-git-commit/SKILL.md`，确认当前 Skill 工作流和边界；该 SKILL.md 已提炼 07 的核心规则，常态提交可直接按此执行，无需回读 07 原文；
4. 当 SKILL.md 未覆盖边界、校验失败原因不明或上下文不足以判断时，回读 `specs/07-事实源边界与Git追溯规范.md` 中 Git 追溯和 commit message 契约相关段落；
5. `code/commit_validate.py --show-format` 或等价帮助；
6. 若通过 Hook registry 验证，读取 `hooks/ldvh-hooks.yaml` 和 `code/hook_dispatch.py` 调用方式；
7. 与本次变更面匹配的验证命令和测试证据。

AI 不应为了提交默认全文读取所有 specs、全部工作对象或完整 Git history。需要追溯历史时，应按 07 使用 Git 原生命令按需展开。

## 8. Scenario 识别

以下信号进入本文：

| 信号 | 处理 |
|---|---|
| 用户说“提交”“先提交”“按规范提交” | 进入提交行动，先检查 status 和 staged files |
| 用户要求修复 commit message | 读取 07 和 validator 输出，修正消息并复验 |
| 事实源或能力资产已修改且需要追溯 | 进入提交准备，判断是否需要拆分 |
| validator 或 hook_dispatch 失败 | 作为 blocking 处理，修正后复跑 |
| 环境 hook 是否安装不明 | 不阻断提交，但必须说明 `not_claimed` 或当次观察，不宣称安装 |

若用户只是询问提交规则，应回答 07 规则和本文边界，不创建提交。

## 9. 执行流程

执行流程如下：

1. 确认用户目标、当前仓库和 `git status --short --untracked-files=all`，并先运行 `python3 code/hook_dispatch.py run commit-preflight --cwd <repo-root>` 或等价入口，记录 staged paths 是否命中管辖项目。
2. 判断 staged / unstaged / untracked 文件是否属于本次提交范围；必要时只 stage 本次范围内文件，不 stage 无关用户变更。
3. 判断是否需要拆分提交。独立目的应拆分；同一原子闭环可以跨 specs、Code、Web、Rules、Skill、Hook 和测试文件。
4. 读取 07 的 message 契约和 `ldvh-git-commit` Skill。若运行环境真实加载了 Skill，记录为 Skill runtime 调用；若只是按 Skill 原文执行，记录为手动等价执行。执行后必须运行 `python3 code/hook_dispatch.py run acknowledge-commit-action --cwd <repo-root> --execution-mode <skill_runtime_invoked|manual_equivalent_execution>`，把本次 staged scope 的提交行动执行凭证写入 receipt。
5. 选择单一 type 和零个或一个 scope，按 07 写简体中文 description。type 和 scope 必须命中 07 授权枚举；若无精确匹配的 scope，选择最接近的已有 scope，并把“建议新增 scope 枚举”的提示留到提交后交还 Human。
6. 按 07 判断是否必须写 body；涉及 specs、rules、code、tests、web、hooks、skills、agents、配置、多文件或 Human Gate 时通常需要 body。
7. 使用 `code/commit_validate.py` 或 `code/hook_dispatch.py run git.commit-msg` 预检。
8. 运行与变更面匹配的验证命令；无法运行或部分失败时，按 08 记录失败原因、残留风险或阻断。
9. 修复全部 error。warning 必须处理为改写正文、说明残留风险或暂停等待 Human。
10. 用已验证消息创建 commit。
11. 提交后报告 commit hash、验证摘要、剩余 `git status --short` 和本次 Skill 使用方式。若提交时发现现有 scope 枚举无法精确覆盖本次主承载域，应显式告知 Human，建议评估是否补充 `07.Att.03` scope 枚举。

## 10. 执行中问题分流与失败暂停

问题分流遵守 03 的闭集：

| 问题 | 分流 |
|---|---|
| commit message error、Hook 阻断、validator 失败 | `blocking`，修正后复验 |
| staged files 混入无关变更 | `blocking` 或拆分，必要时暂停给 Human |
| 拆分边界不清 | Human Gate |
| Web/API 或测试旁路失败但不影响本次提交目标 | `follow_up`，在提交正文或 WorkCase 中说明 |
| Skill/Hook/Rules 资产文本存在低风险漂移且修复成本低 | `opportunistic_fix`，纳入当前原子闭环并验证 |
| 发现可复用提交流程经验或误用模式 | `pitfall_candidate` 或 Spark 分流 |

不得用“看起来没问题”替代 validator、Hook dispatcher 或测试证据。

## 11. Human Gate

以下情况必须暂停：

1. 要提交的 staged changes 与用户目标不一致；
2. 需要执行 destructive Git 操作；
3. 需要绕过 commit validator、Hook 阻断或失败测试；
4. 要修改 native Git hook、用户 hook manager、IDE、Codex settings、CI 或环境安装状态；
5. 提交会改变 07 的 commit message 契约、事实源追溯语义或本文行动边界；
6. 拆分策略会丢弃、重排或合并用户未授权的变更；
7. 无法确认事实源修改是否经过必要 Human Gate。

Git 提交记录本身不额外触发 Human Gate；Gate 由被修改的事实源、行动边界、环境适配、失败阻断或破坏性 Git 操作触发。

## 12. Skill 和 Agent 调度

`ldvh-git-commit` Skill 是本文的固定 Skill 能力资产。AI 应优先使用运行时可用的 Skill；若当前环境没有真实 Skill 调用机制，AI 可以按 Skill 原文手动等价执行，但必须在过程说明或 WorkCase 证据中区分：

1. `skill_runtime_invoked`：运行时确实加载并执行 `ldvh-git-commit`；
2. `manual_equivalent_execution`：主控读取 Skill 原文并按其步骤执行；
3. `skill_unavailable`：Skill 文件不可读或不适用，只能按 07 和临时核对动作执行。

本文不要求固定 Agent。高风险提交、跨规范争议、提交失败原因不明或涉及环境安装时，可以安排独立 Agent 审查，但 Agent 输出必须交还主控，不能替代 Human Gate 或 Code validator。

## 13. Code、命令和 Web 协作适配

Code 和命令协作：

| 能力 | 用途 |
|---|---|
| `python3 code/commit_validate.py --show-format` | 查看当前 07 派生的提交格式说明 |
| `python3 code/commit_validate.py --check-message '<message>' --files <files>` | 直接检查提交消息和文件范围 |
| `python3 code/commit_validate.py --check-message-file <message-file> --files <files>` | 检查 message 文件 |
| `python3 code/hook_dispatch.py run commit-preflight --cwd <repo-root>` | 提交前只读判定 staged paths 是否命中管辖项目，并输出 31 / `ldvh-git-commit` 行动入口 |
| `python3 code/hook_dispatch.py run acknowledge-commit-action --cwd <repo-root> --execution-mode manual_equivalent_execution` | 写入本次 staged scope 已执行 `ldvh-git-commit` 的提交行动凭证 |
| `python3 code/hook_dispatch.py run git.commit-msg --message-file <message-file>` | 通过统一 Hook registry 执行等价事件 |
| `python3 code/install_git_hooks.py install` | 为当前或指定 Git 仓库安装 native `commit-msg` hook |
| `python3 code/specs_validate.py deployment-entries` | 检查固定运行时扩展登记一致性 |
| `python3 code/specs_validate.py capability-environment` | 查看固定能力资产与环境保障矩阵，不声明安装 |

Web 负责展示提交记录、body、解析字段、关联提交和 ProjectFiles 工具页上下文。Web 不创建提交、不替代 Git records、不维护第二套提交事实源。

## 14. 事实源回写与证据留存

提交行动完成后，至少应在过程输出中交还：

1. commit hash；
2. 提交 message 摘要；
3. 预检命令和结果；
4. 变更面匹配的验证命令和结果；
5. 剩余 `git status --short`；
6. Skill 使用方式：runtime 调用、手动等价执行或不可用原因；
7. 未覆盖验证、失败、warning 或 residual risk。

对管辖项目提交，过程输出还应能回指 `commit-preflight` 的管辖判定和 `acknowledge-commit-action` 写入的 `commit_action_execution` 凭证。缺少该凭证时，不能只用 `commit-msg` hook 通过证明已执行本文行动编排。

若本次提交属于 WorkCase 执行，应把稳定证据写入 WorkCase 的执行项、`verification_evidence`、`closure_evidence` 或相关字段。若形成长期规则、经验、缺口或后续动作，应分流为 specs、Spark、Pitfall、ADR、Study、WorkCase 或 Git commit records。

不得在工作对象中手写维护提交清单。对象、规范、Code 和 Web 的关联提交仍按 07 从 Git history、路径、对象 ID 和正文自然文本派生。

## 15. 环境适配边界

本文不声明任何环境已经安装 LDVH Hook 或 Skill。环境状态只能来自当次检查或 06 授权的适配记录。

允许的边界：

1. 仓库内维护权威资产：Skill、Hook registry、Code validator、Web docs；
2. 当前环境手动运行 validator 或 dispatcher；
3. 在过程输出中说明 Hook registry 可被环境接入；
4. 把 CI / server-side gate 记录为 planned 兜底方向。

不允许的边界：

1. 仅因 `hooks/ldvh-hooks.yaml` 存在就宣称 Git native hook 已安装；
2. 未经用户明确要求修改 `.git/hooks`、IDE、Codex settings、全局 hook manager 或 CI；
3. 把一次本地观察写成长期环境支持结论；
4. 用第三方 hook manager 替代 LDVH 对环境概念和统一 Hook registry 的描述。

## 16. 行动特有可测试性锚点

本文至少应能被以下方式验证：

| 锚点 | 检查方式 |
|---|---|
| 成员身份 | `python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text` |
| 固定资产登记 | `python3 code/specs_validate.py deployment-entries` 和 `python3 code/specs_validate.py capability-environment` |
| message validator | `python3 -m pytest tests/code/test_commit_validate.py -q` |
| Hook dispatcher | 使用临时 message 文件运行 `python3 code/hook_dispatch.py run git.commit-msg --message-file <message-file>` |
| native Git hook | `python3 code/install_git_hooks.py status`，并用真实 `git commit` smoke 确认不合规 message 会被阻断 |
| Skill 自描述 | `python3 /Users/dmh2002/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ldvh-git-commit` 或等价临时核对动作 |
| Web commit DTO | `npm --prefix web run check` 和 commit DTO 相关 API 测试 |
| 行动边界 | AI 回读核对本文没有复制 07 的 commit message 本体规则，也没有声明环境安装状态 |

## 17. 规范保障要求

本节是 03 要求的成员一致性兼容章节，不生成新的规范保障要求。本文承接的来源要求见 `v2_action_member.assurance_takeover`；下表只记录来源要求承接与能力实践关联。本文必须通过来源规范路径、章节锚点和能力资产路径引用来源要求，不得复制 07 的 commit message 规则、06 的运行时扩展规则、04 的 Code 规则、05 的 Web 规则或 08 的测试规则原文。

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源承接：03 流程复用与行动成员要求 | 回指 `specs/03-行动编排规范.md` §5、§11、§12；本文只承接 Git 提交行动的执行闭环、证据、Gate 和能力映射 | 本文 `v2_action_member.assurance_takeover`、Context/Scenario/Gate/执行/证据章节、Human Gate | 行动编排治理 | 03 的成员机制、承接边界、骨架或 active 判定变化时 |
| 来源承接：07 Git 追溯和 commit 契约 | 回指 `specs/07-事实源边界与Git追溯规范.md` §9 及 07 授权附件；本文只编排执行，不复制 type/scope/body、语言或关联提交规则 | 07 原文、本文 §6/§7/§9、`code/commit_validate.py`、临时核对动作 | Git 提交行动 | 07 的提交契约、Git 追溯、关联提交派生或事实源回写边界变化时 |
| 来源承接：06 运行时扩展与环境边界 | 回指 `specs/06-运行时扩展规范.md` 与 `specs/attachments/06.Att.02-固定运行时扩展登记表.md`；本文只声明本行动需要哪些能力，不声明环境已安装 | `capability_assets`、`skills/ldvh-git-commit/SKILL.md`、`hooks/ldvh-hooks.yaml`、`capability-environment` | 能力资产编排 | Skill、Hook、Rules、环境适配、部署状态或固定资产登记边界变化时 |
| 来源承接：04/05/08 Code、Web 和测试本体 | 回指 04、05、08；本文只编排 validator、Hook dispatcher、Web commit DTO 和测试证据的使用方式，不复制实现契约 | `code/commit_validate.py`、`code/hook_dispatch.py`、Web commit DTO 测试、08 验证声明边界 | 能力协作与验证 | Code CLI、Web commit 展示、测试入口或验证声明规则变化时 |
| 行动 Gate 承接 | 回指 03 Human Gate 原则和 07/06 的事实源与环境边界；本文只列出 Git 提交行动中必须暂停的触发条件 | 本文 §11、Human Gate 记录、WorkCase 证据或过程输出 | Human 确认 | 拆分不清、绕过校验、环境安装变更、破坏性 Git 操作或事实源 Gate 不明时 |

## 18. 行动编排成员检查要求

检查本文至少包括：

| 检查项 | 标准 |
|---|---|
| 身份块 | 同时包含 `v2_spec`、`v2_action_member` 和兼容 `ldvh_member` |
| 状态分工 | `v2_spec.status` 与 `v2_action_member.collection_status` 均为 active |
| 锚点 | Scenario、Context、Gate、执行、问题分流、回写、证据和可测试性锚点可定位 |
| 来源承接 | `assurance_takeover` 回指 03、07、06、08 的执行和保障要求 |
| 能力映射 | `capability_assets` 只登记流程所需能力，不声明部署完成 |
| 边界 | 本文通过引用承接来源要求，不复制 07/06/04/05/08 原文，不替代 Skill/Hook/Code/Web/环境适配事实源 |
| Human Gate | 拆分不清、绕过校验、环境安装和破坏性 Git 操作均被阻断 |
| 证据 | 提交后交还 hash、验证、status 和 Skill 使用方式 |

## 19. 待补齐事项

1. 后续可补齐 Code 对 `git_commit_action` 成员锚点、`assurance_takeover` 和 `capability_assets` 的专项诊断；
2. CI / server-side commit gate 仍是 planned 兜底方向，尚未实现；
3. Web API 全量回归当前可能受事实对象夹具影响，commit DTO 应保持可独立验证；
4. 若环境适配形成真实安装记录，应回到 06，而不是修改本文声明安装状态。
