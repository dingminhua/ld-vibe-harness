# git-commit-orchestration-Git提交编排

```yaml
ldvh_doc:
  doc_id: "44"
  doc_kind: "work_process_spec"
  title: "git-commit-orchestration-Git提交编排"
  status: "active"
  canonical_path: "specs/44-git-commit-orchestration-Git提交编排.md"
  created: "2026-06-22"
  updated: "2026-06-22"
  parent_doc: ""
  relation: ""
  positioning: "定义 Git 提交行动编排，用于控制 AI 在 LDVH 自身或管辖项目中准备、拆分、校验、创建和交还 Git commit 的执行过程，协调 specs/10、ldvh-git-commit Skill、commit_validate、Hook、Human Gate 和 Git commit records"
  scope: "LDVH 自身和管辖项目中由 AI 协助创建 Git commit、编写或修复 commit message、拆分 staged changes、运行提交预检、处理提交校验失败和交还提交结果的场景"
  basis:
    - "specs/06-行动编排基础规范.md"
  related_specs:
    - "specs/03.03-行动编排文档规范.md"
    - "specs/04.02-LDVH能力资产与保障机制规范.md"
    - "specs/04.03-环境入口适配与部署规范.md"
    - "specs/07-Code确定性执行实现规范.md"
    - "specs/09-事实源边界与承载规范.md"
    - "specs/10-Git提交规范.md"
  code_consumption:
    - "doc_metadata"
    - "relations"
    - "structure"
    - "member_consistency"
    - "workflow_collection"
```

```yaml
ldvh_member:
  spec_id: "44"
  kind: "work_process"
  name_en: "git-commit-orchestration"
  name_zh: "Git提交编排"
  collection_status: "active"
  canonical_path: "specs/44-git-commit-orchestration-Git提交编排.md"
  scenario_anchor: "§5"
  context_anchor: "§4"
  gate_anchor: "§7"
  execution_anchor: "§6"
  writeback_anchor: "§10"
  evidence_anchor: "§10"
  testability_anchor: "§12"
  assurance_takeover:
    - "source_spec=specs/10-Git提交规范.md; requirement=流程复用要求; scope=AI 创建 Git commit、修复提交消息、拆分 staged changes、运行提交预检和交还提交结果的流程编排"
    - "source_spec=specs/10-Git提交规范.md; requirement=提交门禁确定性执行要求; scope=提交前 message 预检、Hook 等价检查、失败处理和人工降级路径"
  capability_assets:
    - "type=skill; path=skills/ldvh-git-commit/SKILL.md; purpose=提交准备、拆分判断、消息编写、预检和交还的可复用执行外壳; status=required"
    - "type=hook; path=hooks/ldvh-hooks.yaml; purpose=统一登记 git.commit-msg 事件和等价提交前 message 校验入口; status=required"
    - "type=code; path=code/commit_validate.py; purpose=commit message canonical validator; status=required"
    - "type=code; path=code/hook_dispatch.py; purpose=统一 Hook dispatcher 和等价复跑入口; status=required"
  code_consumption:
    - "workflow_member_self_description"
    - "git_commit_orchestration_scenario"
    - "commit_validation_precheck"
    - "workflow_collection_diagnostics"
```

---
## 1. 行动定位与适用场景

Git 提交编排是 LDVH 对 AI 创建 Git commit 这一高频、高追溯价值行动的执行控制。它回答：AI 何时可以提交、提交前该读什么、如何判断是否拆分、如何使用已登记 Skill 和 Code 预检、何时必须暂停、提交后如何交还 hash、剩余状态和残留风险。

本流程不定义 commit message 格式、type/scope 枚举、body 必填条件、提交语言、关联提交派生或 Web 展示规则；这些规则由 `specs/10-Git提交规范.md` 承载。本流程也不替代 `ldvh-git-commit` Skill、`code/commit_validate.py`、`hooks/ldvh-hooks.yaml`、CI、Human Gate 或 Git commit records。它只负责把这些能力放入一次可执行、可暂停、可验证、可交还的提交行动闭环。

以下场景应进入本流程：

1. 用户明确要求 AI 创建 Git commit、提交当前变更、修复提交消息或准备提交；
2. 用户要求 AI 判断 staged changes 是否应拆成多个 commit；
3. `code/commit_validate.py`、Hook 或 CI 报告 commit message 格式、body、语言、私有 trailer 或语义质量问题；
4. AI 完成事实源修改后，需要通过 Git commit records 留下追溯证据；
5. WorkCase、ADR、Spark、Pitfall、Study、specs、Code、Web、Rules、Skill、Agent、Hook 或环境入口修改完成后，需要提交前预检和提交结果交还；
6. 用户要求解释、修复或复跑提交预检失败；
7. 用户要求回退、amend、改写历史、强推、删除分支或其它 Git 操作，且需要先判断是否属于普通提交行动或必须暂停。

以下场景不应由本流程直接承接：

1. 只查询 Git 历史、提交列表或关联提交；该事项由 Git、Code 或 Web 派生视图承接；
2. 审核 `specs/10-Git提交规范.md` 的规范质量；该事项由 42 承接；
3. 审核 `ldvh-git-commit` Skill 是否登记合格；该事项由 04.02、43 或后续能力资产审核流程承接；
4. 修改 Git 提交格式、门禁规则、Hook 注册方式或关联派生规则；该事项应回到 10、07、08、04.02、04.03 和对应实现；
5. 创建长期“提交对象”或 `ldvh-base/changes/`；Git commit records 已是事实源修改追溯证据；
6. 在用户未要求提交、未确认范围或工作区存在无关改动时静默提交。

---
## 2. 准入条件

进入本流程前，应满足以下条件之一：

1. 用户明确要求提交、准备提交、修复提交消息、拆分提交或解释提交校验失败；
2. 当前已有 staged changes，且用户目标指向创建 commit；
3. 当前已有可提交的事实源修改，并且用户要求 AI 完成到 Git commit；
4. 已有 commit message 候选、message 文件、Hook 失败输出或 `commit_validate.py` 诊断；
5. 当前任务的关闭条件明确要求提交 hash 或 Git commit records 追溯。

不满足以上条件时，不得因为工作区存在修改就自动提交。若修改范围、提交边界、Human Gate 或验证状态不清，应先作为过程输出说明需要确认的事项。

---
## 3. 事实源边界

本流程的权威规则来自以下事实源：

| 内容 | 权威位置 |
|---|---|
| Git 提交事实源定位、message 格式、AI 写提交顺序、Human Gate 与风险 | `specs/10-Git提交规范.md` |
| 行动编排通用规则、主控调度、过程输出、回写和证据 | `specs/06-行动编排基础规范.md` |
| 行动编排文档骨架、成员自描述和可测试性锚点 | `specs/03.03-行动编排文档规范.md` |
| 能力资产、Skill、Hook、Agent 和环境能力边界 | `specs/04.02-LDVH能力资产与保障机制规范.md` |
| 环境入口、Hook 适配、部署和禁止声明 | `specs/04.03-环境入口适配与部署规范.md` |
| Code 输出、受控写入前检查和派生索引边界 | `specs/07-Code确定性执行实现规范.md` |
| Git 文件事实源、过程输出和工具输出回写边界 | `specs/09-事实源边界与承载规范.md` |
| 提交流程 Skill | `../skills/ldvh-git-commit/SKILL.md` |
| 提交 message 校验器 | `code/commit_validate.py` |
| Hook 事件登记 | `hooks/ldvh-hooks.yaml` |
| 最终提交证据 | Git commit records |

`git status`、`git diff`、`git log`、Code 输出、Hook 输出、Skill 输出、CI 输出和聊天分析只能作为导航、诊断、候选建议或过程输出。最终事实源修改追溯以 Git commit records 为准；工作对象不得手写维护提交清单字段。

---
## 4. Context 要求

执行本流程前，AI 应按最小可行动原则准备以下 Context：

1. 当前用户提交目标、是否明确要求创建 commit、是否只要求预检或消息修复；
2. `git status --short`，必要时读取 staged files、unstaged files 和 untracked files 的边界；
3. 已 staged 的文件清单；若没有 staged changes，应确认是否需要 staging，且不得自动 stage 无关用户改动；
4. 目标变更对应的事实源、工作对象、规范、Code、Web、Rules、Skill、Hook 或环境入口范围；
5. `specs/10-Git提交规范.md` 中 message 格式、body 必填、AI 写提交顺序、Human Gate 与风险、Code 消费规则；
6. `../skills/ldvh-git-commit/SKILL.md` 中 workflow、边界和停止条件；若当前环境未加载该 Skill，应按 10 和本流程手动执行等价步骤；
7. 必要时运行或准备运行 `python3 code/commit_validate.py --check-message-file <message-file>`、`python3 code/commit_validate.py --check-message '<message>'` 或 `python3 code/hook_dispatch.py run git.commit-msg --message-file <message-file>`；
8. 与本次提交范围相匹配的验证证据或未验证原因；
9. 是否存在 Human Gate、长期降级、破坏性 Git 操作、提交拆分争议或工作区无关改动。

若无法定位仓库、无法读取 Git 状态、无法判断 staged changes 是否属于用户目标，或提交会包含无关用户改动，应暂停并说明缺口。

---
## 5. Scenario 识别

AI 遇到以下信号时，应识别为 Git 提交编排场景：

1. 用户说“提交”“commit”“帮我提交”“写提交信息”“修复 commit message”“预检提交”；
2. 当前任务完成后，用户要求给出 commit hash 或完成 Git 记录；
3. `commit_validate.py`、Hook、CI 或用户指出提交消息不合格；
4. 工作区有多个 staged 或 unstaged 修改，用户要求判断是否拆提交；
5. 当前变更涉及 specs、ldvh-base、Rules、Skill、Agent、Hook、Code、Web、环境入口或跨文件事实源修改，需要提交前 body 和风险说明；
6. 用户要求 amend、rebase、reset、force push、删除分支、批量回退或其它可能破坏历史的 Git 操作。

多个场景同时命中时，应先判断是否存在破坏性 Git 操作或 Human Gate。普通提交、消息修复和预检进入本流程；破坏性 Git 操作只在 Human 明确确认影响范围后继续。

---
## 6. 执行流程

Git 提交编排按以下步骤执行：

1. **确认提交意图**：确认用户是要求真实创建 commit、只写 message、只做预检、修复失败，还是判断拆分边界；
2. **确认入口与能力**：若当前环境可发现 `ldvh-git-commit` Skill，应优先用该 Skill 承接具体提交 SOP；若不可发现，按本流程和 10 手动执行等价步骤；
3. **读取 Git 状态**：运行或读取 `git status --short`，区分 staged、unstaged、untracked 和可能无关的用户改动；
4. **确认提交范围**：只纳入用户目标覆盖的文件；不得 stage、unstage、删除、覆盖或提交无关改动；
5. **判断拆分提交**：若 staged changes 包含多个独立目的，应暂停并建议拆分；若属于同一原子闭环，可保留在同一 commit，并在 body 说明跨域影响；
6. **确认 Human Gate**：检查是否涉及破坏性 Git 操作、绕过预检、改变事实源边界、状态机、字段契约、AI 入口、长期降级或用户环境入口；
7. **选择 message 结构**：按 10 选择单一 type、零个或一个 scope、简体中文 description，并判断 body 是否必填；
8. **编写 body 语义清单**：需要 body 时，说明动机、关键变更、影响边界、验证结论、风险与后续；不得用私有 trailer 替代正文语义；
9. **运行提交预检**：使用 `commit_validate.py` 或 `hook_dispatch.py run git.commit-msg` 检查候选 message；错误必须修复，warning 必须处理、解释或触发 Human 判断；
10. **执行匹配验证**：根据 changed surface 运行必要验证；不能验证时，在 message 或过程输出中说明未验证原因和残留风险；
11. **创建 commit**：只有提交范围清楚、必要 Gate 满足、预检 error 清零后，才执行 `git commit`；
12. **交还结果**：提交后报告 commit hash、提交首行、预检结果、验证摘要、剩余 `git status --short` 和任何残留风险；
13. **失败降级**：若无法提交，说明阻塞原因、已完成的预检、未满足条件和建议下一步，不得把预检通过或 message 生成说成已提交。

---
## 7. Gate 触发条件

出现以下情况时，AI 必须暂停继续提交，并说明原因、影响范围和需要 Human 确认的事项：

1. 用户未明确要求创建 commit，但 AI 准备执行 `git commit`；
2. staged changes 包含多个互相独立的目的，且拆分边界不清；
3. 工作区存在与本次目标无关的 staged 或 unstaged 改动，可能被误提交或误改；
4. 需要 stage、unstage、删除、移动或覆盖用户未授权的文件；
5. 需要 amend、rebase、reset、cherry-pick、revert、force push、删除分支或改写已共享历史；
6. 需要绕过 `commit_validate.py`、Hook、CI 或提交前预检 error；
7. 需要接受长期降级、跳过关键验证或把未验证内容写成已验证；
8. 本次提交会改变事实源边界、对象状态机、字段契约、规范编号、AI 入口、环境入口、受控写入、安全能力或 Human Gate 条件；
9. commit message 需要记录 Human 确认，但确认范围、约束或证据不清。

Git commit records 本身不额外触发 Human Gate；Gate 由被修改事实源、破坏性 Git 操作、验证降级或环境写入等影响来源触发。

---
## 8. Skill 和 Agent 调度

本流程默认由主控 AI 执行，并优先复用已登记的 `ldvh-git-commit` Skill。该 Skill 只承接提交准备、拆分判断、message 编写、预检和交还的执行转换；不得新增提交规则、替代 10、绕过 Code 校验或替代 Human Gate。

Agent 通常不需要参与普通提交。以下情况可以由主控调度只读 Agent 辅助判断：

1. 提交拆分边界存在争议，且涉及多个事实源或多个工作对象；
2. 提交 body 需要独立复核是否准确覆盖影响边界和风险；
3. 大型迁移或高影响规范变更需要独立确认提交说明是否误导；
4. 预检 warning 涉及语义质量，主控无法可靠判断是否可接受。

Skill 和 Agent 输出均为过程输出，必须交还主控。Agent 不得直接创建 commit，不得 stage 文件，不得改写 message 后直接生效。

---
## 9. Code 与命令入口协作适配

本流程使用 Code 和 Git 命令完成确定性检查和提交动作：

| 能力 | 作用 | 边界 |
|---|---|---|
| `git status --short` | 发现工作区和 staged 边界 | 不替代用户提交范围确认 |
| `git diff --cached` / 文件清单 | 判断 staged changes 语义和拆分边界 | 不应把完整 diff 复制进 message |
| `code/commit_validate.py` | 校验 commit message 可机械检查部分 | 不判断所有语义质量，不授权绕过 Gate |
| `code/hook_dispatch.py run git.commit-msg` | 通过统一 Hook 事件做等价预检 | Hook 触发不等于环境已部署或完整支持 |
| `git commit` | 创建 Git commit record | 只能在范围、Gate、预检和验证条件满足后执行 |
| Git 历史查询 | 提供最终提交 hash 和后续派生关联 | 不回写为工作对象提交清单字段 |

常用命令包括：

```bash
git status --short
python3 code/commit_validate.py --check-message-file <message-file> --files <staged-files>
python3 code/hook_dispatch.py run git.commit-msg --message-file <message-file>
git commit -F <message-file>
```

命令输出只作为过程证据和诊断。提交消息契约、Git 事实源定位和 Web 展示规则变化时，应回到 10、07、08、Code、Hook 和测试同步。

---
## 10. 事实源回写与证据留存

本流程执行后的过程输出应至少说明：

1. 提交对象和提交意图；
2. staged changes 或目标文件范围；
3. 是否使用 `ldvh-git-commit` Skill，或采用了等价手动流程；
4. 是否需要拆分提交，以及拆分判断依据；
5. 是否触发 Human Gate；
6. 候选或最终 commit message 的首行和 body 是否必填；
7. 运行的预检命令和结果；
8. 与 changed surface 匹配的验证结论或未验证原因；
9. commit hash、提交首行和剩余工作区状态；
10. 残留风险和下一步分流。

稳定事实回写规则如下：

1. 最终提交证据由 Git commit records 承载；
2. 工作对象状态、关闭证据、验证证据或 Human Gate 记录需要长期追溯时，回写对应 `ldvh-base/` 对象字段，而不是手写提交清单；
3. 提交规范、提交门禁、关联派生或 Web 展示规则变化时，回写 `specs/10-Git提交规范.md`、Code、Hook、Web 或测试；
4. 提交流程缺口或后续改进进入 WorkCase、Spark、ADR、Pitfall 或 docs；
5. 只生成 message、只跑预检或提交失败时，应明确其为过程输出，不得表述为 Git 事实已经形成。

不得把聊天中的“已准备提交”“预检看起来可以”当作 commit 证据；只有 `git commit` 成功并产生 hash 后，才形成 Git commit record。

---
## 11. 环境适配边界

本流程可被 Rules 入口、`ldvh-git-commit` Skill、Code validator、Hook、CI、Web 提交记录页或人工降级步骤辅助，但这些能力不得替代本流程正文、10 的提交规范、Human Gate 或 Git commit records。

环境适配边界如下：

1. Rules 入口只提示何时读取 10、30 和 Skill，不复制提交规范全文；
2. Skill 只封装执行步骤，不新增提交格式、Gate 或事实源规则；
3. Hook 可以提供提交前 message 校验入口，但 Hook 登记不等于当前环境已安装或启用；
4. CI 或 server-side gate 可以补充远端检查，但不得与 canonical validator 维护独立规则副本；
5. Web 可以展示提交记录派生视图，不维护第二事实源；
6. 非 Codex 环境或用户自有 hook 系统只能按 04.03 自助适配，不得写成 LDVH 官方完整支持；
7. 缺少 Skill、Hook 或 CI 时，应执行等价手动预检并说明残留风险。

---
## 12. 行动特有可测试性锚点

本流程的关键行为应能通过正例、反例、Gate 场景、回写场景和命令验证进行检查。

正向场景：

1. 用户明确要求提交，staged changes 属于单一原子闭环，AI 读取 10、使用 Skill 或等价流程，预检通过后创建 commit 并交还 hash；
2. 用户只要求写 commit message，AI 生成符合 10 的候选 message 并运行预检，但不执行 `git commit`；
3. `commit_validate.py` 报告 body 缺失，AI 补写语义清单并复跑预检；
4. 当前环境未加载 Skill，AI 按 10 和本流程手动完成等价提交步骤。

负向场景：

1. 用户未要求提交，AI 因工作区有修改而自动 commit；
2. AI 把多个独立目的混入一个 commit，且未说明原子闭环；
3. AI 提交了无关用户改动；
4. AI 用 `Human-Gate:`、`Verification:` 或 `Risk:` 私有 trailer 替代 body；
5. AI 把 Hook registry 存在写成当前环境 Hook 已启用；
6. AI 在预检 error 未修复时提交。

Gate 场景：

1. 提交需要改写历史、强推、删除分支或批量回退；
2. staged changes 边界不清或包含无关改动；
3. 需要跳过提交预检、跳过关键验证或接受长期降级；
4. 本次提交改变事实源边界、状态机、字段契约、AI 入口、环境入口或 Human Gate 条件。

回写场景：

1. 成功提交后，Git commit records 承载最终追溯证据；
2. 提交失败但发现提交规范、Skill、Hook 或 validator 缺口时，分流到 WorkCase 或 Spark；
3. 提交过程形成长期决策或可复用经验时，分别回写 ADR 或 Pitfall；
4. 只生成过程 message 或预检报告时，不回写为稳定事实。

修改本流程、10、Skill、Hook 或 validator 后，至少应按影响范围运行：

```bash
python3 code/specs_validate.py index
python3 code/specs_validate.py doc specs
python3 code/specs_validate.py refs specs
python3 code/specs_validate.py assurance specs
python3 code/specs_validate.py all
python3 code/commit_validate.py --show-format
```

涉及 Code、Hook、Web 或测试实现时，应补充对应测试命令。无法运行自动化校验时，应说明人工检查方式和残留风险。

---
## 13. 规范保障要求

本文通过以下规范保障要求说明相关要求的同步、检查或审计触发条件。

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | Git 提交编排应承接 10 的提交规范、09 的事实源追溯原则、06 的行动编排规则和 04.02 的能力资产边界，不重复定义提交格式 | 本文、10、09、06、04.02、Human Gate | 行动编排治理 | 提交流程、提交格式、事实源边界或能力资产边界变化时 |
| 入口可见要求 | AI 准备提交、修复提交消息或处理提交预检失败时应能定位本文、10 和 `ldvh-git-commit` Skill | Rules 入口、Skill 描述、Code 帮助、Web 提交记录页 | AI 执行入口提示 | 提交、提交预检、Skill 触发描述或 Rules 入口变化时 |
| 工作流程接管要求 | 本流程接管 10 中 AI 创建 Git commit 的流程编排和提交前预检执行责任；10 继续维护格式、事实源和派生规则 | 本文、10、Skill、Code validator、Hook、人工降级检查 | 行动编排治理 | 创建 commit、修复 message、调整提交契约或调整 Skill/Hook/validator 时 |
| 流程复用要求 | `ldvh-git-commit` Skill 可以封装本流程的高频执行步骤，但必须交还主控且不新增规则 | Skill SOP、主控交还、人工降级检查 | 流程复用 | 提交流程反复执行、Skill 描述变化或 Skill 校验失败时 |
| 确定性执行要求 | commit message 可机械检查部分应由 `commit_validate.py`、Hook dispatcher、CI 或等价命令预检 | `code/commit_validate.py`、`code/hook_dispatch.py`、测试或人工降级检查 | 校验实现 | 提交 message、validator、Hook 或 CI 规则变化时 |
| Human 交互要求 | 破坏性 Git 操作、跳过预检、长期降级、无关改动混入或高影响事实源修改应触发 Human Gate | Human Gate、提交正文或对应事实源 | 人工确认 | §7 任一 Gate 场景发生时 |
| 生命周期触发要求 | 本流程、10、Skill、Hook、validator、Web 提交展示或 Rules 入口变化后，应检查相关资产和测试是否同步 | specs 校验、Skill 校验、Code 测试、Web 检查、人工降级检查 | 触发保障 | 提交行动、提交格式、预检命令、Hook 事件或提交展示变化时 |

---
## 14. 检查要求

Git 提交编排至少包括：

| 检查项 | 标准 |
|---|---|
| 场景匹配 | 用户明确要求提交、message 修复、预检或拆分判断；未要求提交时不自动 commit |
| 提交范围 | staged changes 与用户目标一致，无关用户改动未被纳入 |
| 拆分判断 | 独立意图已拆分或已说明原子闭环 |
| 上位规范承接 | 未复制或重定义 10 的格式规则、09 的事实源规则、04.02 的能力资产规则或 07 的 Code 边界 |
| Skill 使用 | 可发现 `ldvh-git-commit` Skill 时优先使用；不可发现时执行等价手动流程 |
| Gate | 破坏性 Git 操作、跳过预检、长期降级、高影响事实源修改和范围不清时暂停 |
| Message | type、scope、description、body 和 footer 符合 10；不使用私有 trailer 替代 body |
| 预检 | 相关 `commit_validate.py` 或 Hook dispatcher 预检已运行；error 已修复，warning 已处理 |
| 验证 | 与 changed surface 匹配的验证已执行，或未验证原因和残留风险已说明 |
| 事实源边界 | 成功提交以 Git commit records 为最终证据，不创建提交工作对象或手写提交清单 |
| 交还 | 提交后报告 hash、首行、预检结果、验证摘要、剩余工作区状态和风险 |

---
## 15. 待补齐事项

1. 评估是否需要让 `ldvh-git-commit` Skill 输出更结构化的主控交还摘要，便于后续 Web 或 Code 展示；
2. 评估 `code/commit_validate.py` 是否需要输出更适合本流程消费的结构化诊断；
3. 评估 `hooks/ldvh-hooks.yaml` 是否需要增加更多提交前后事件，或继续只登记 `git.commit-msg`；
4. 评估 Web 提交详情页是否需要展示“本次提交是否由 44 流程完成”的过程摘要；该摘要不得成为第二事实源；
5. 本流程实际执行后发现的重复误判，应按事实源边界分流到 Pitfall、Spark、WorkCase、ADR、Code 需求或本文修订。
