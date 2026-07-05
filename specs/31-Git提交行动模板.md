# Git提交行动模板

```yaml
ldvh_spec:
  spec_id: "31"
  spec_kind: "action_template_spec"
  title: "Git提交行动模板"
  status: "active"
  authority: "active"
  canonical_path: "specs/31-Git提交行动模板.md"
  parent_spec: "specs/06-行动模板基础规范.md"
  relation: "refines"
  positioning: "定义 Git 提交行动的 Context、Scenario、Gate、执行、验证、回写和交还边界"
  scope: "Git 工作区读取、提交范围判断、提交拆分、commit message 契约引用、验证声明、提交后交还和阻断分流"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
    - "specs/06-行动模板基础规范.md"
    - "specs/09-测试与验证规范.md"
  related_specs:
    - "specs/07-Code确定性执行规范.md"
    - "specs/10-安装与配置规范.md"
  migration_sources:
    - "v2:specs/31-git-commit-action"
    - "skills/ldvh-git-commit/SKILL.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "git_commit_action_template"
    - "git_commit_scope_gate"
    - "commit_message_contract_reference"
    - "commit_verification_handoff"
    - "commit_writeback_boundary"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. 模板定位与来源"
      - "6. Git 提交行动边界"
      - "7. Context、Scenario、Gate 与交还"
    assurance_measures: "8. 保障措施"
    verification_method: "9. 验证方法"
    human_gate: "10. Human Gate"
    stop_conditions: "11. Stop Conditions"
    next_queries: "12. 待补齐事项"
```

> 文件状态：active；本文承接 Git 提交行动编排能力。本文只组织一次 Git 提交行动如何按既有规则执行，不定义 commit message 字段闭集、type / scope 枚举、body 条件、验证声明字段、Hook 安装或 commit gate 实现。

## 1. 价值判断

本文存在的价值，是把 Git 提交这类高频、高影响、易遗漏验证和风险说明的行动沉淀成可复用模板，让 AI 在提交前能稳定判断范围、拆分边界、验证证据、Human Gate 和交还内容，减少把过程输出、未验证结论或错误范围写进 Git records 的风险。

Git 提交行动主要服务 V2、V3、V4、V6、V7、V8 和 V9：它让 AI 快速读取工作区、确认提交意图、判断是否需要拆分、引用 commit message 契约、执行匹配验证、按事实源边界回写风险和缺口，并在完成后交还 commit hash、验证摘要和残留风险。Git commit records 只溯源文件事实源修改，不替代事实源正文、事实对象、Human Gate 或验证声明。

## 2. 权威依据

本文承接 `specs/06-行动模板基础规范.md` 的 Context、Scenario、Gate、执行、验证、回写和交还结构。行动模板不是规则源，也不是授权器；本文的职责是把来源规则、当前 Git 工作区、Code 输出、验证证据、Human Gate 和提交后交还组织为可复用行动路径。

本文承接 `specs/03-事实源与Git溯源规范.md` 的 Git 溯源与提交契约父层规则，承接 `specs/attachments/03.Att.01-Commit-Message契约字段表.md` 的 commit message 字段闭集、type / scope 枚举、body 条件和小标题闭集，承接 `specs/09-测试与验证规范.md` 与 `specs/attachments/09.Att.01-验证声明字段表.md` 的验证声明边界。

本文可以引用 `code/docs/01-Git-Commit-and-Hook-Practice.md` 的实现实践和 commit validator 入口，但不得复制其命令样例、Hook 安装方式或 parser 规则形成第二规则源。若本文与 03、03.Att.01、06、09、09.Att.01 或 Human Gate 冲突，应回到来源规则和 Human Gate，不得由本模板自行覆盖。

## 3. 归口边界

本文归口定义 Git 提交行动的步骤组织、提交范围 Gate、验证和交还边界。

本文不归口定义 commit message 字段闭集、type / scope 枚举、body 条件、验证声明字段定义、测试治理、Hook 安装、commit gate 实现、Git 命令实践、Code 输出 schema 或 CI 规则。这些分别由 03、03.Att.01、09、09.Att.01、01、07、10、Code 和 tests 承接。

本文可以组织“读取工作区、判断范围、必要时拆分、形成提交说明、验证、提交、交还”的行动顺序，也可以把 commit validator、Hook 或测试输出作为过程证据交还主控 AI 判断；但不得把工具通过写成 Human Gate 已完成、不得把 Git commit records 写成事实对象、不得把未验证范围隐藏在提交说明外。

## 4. 适用范围

本文适用于：

1. 用户明确要求提交当前变更；
2. 用户要求修复、重写或复核提交消息；
3. 用户要求提交前预检、拆分已暂存变更或确认提交范围；
4. AI 已完成文件事实源修改，需要按 Git records 溯源；
5. commit validator、Git Hook 或等价提交门禁返回阻断，需要按来源规则分流。

用户只是询问提交契约、验证规则或 Hook 实现时，只回答 03、03.Att.01、09、09.Att.01、01、07 和实现域边界，不创建提交。

## 5. 模板定位与来源

本文是 06 之后的第二个独立正式行动模板，编号为 `31`。它不是 06 父规范的正文示范，也不是 commit validator 或 Git Hook 的实现文档；它是可被 AI 直接引用的 Git 提交行动模板成员。

本文承接 Git 状态读取、diff 判断、验证证据、提交后交还和失败分流能力。历史 Skill 或外部包装只能作为来源线索和包装候选，不恢复 Skill 顶层机制；即使后续存在外部包装，行动结果仍必须交还主控 AI 判断。

当前最小闭环包括：读取用户目标和工作区、判断 staged / unstaged / untracked 范围、必要时拆分、引用 03.Att.01 形成提交说明、执行匹配验证或说明未验证范围、运行 commit validator 或等价提交消息检查、创建提交、交还结果和残留风险。Hook 安装、commit gate 部署、CI 配置和环境入口接入不由本文授权。

## 6. Git 提交行动边界

提交行动必须先确认本次提交只有单一主意图和主承载域。多个独立目的、相互无关的文件事实源修改、已暂存范围与用户目标不一致、或验证范围不能共同说明时，应暂停并拆分或进入 Human Gate。

提交说明只引用 03.Att.01 的字段和小标题契约，不复制 type / scope 枚举、body 条件表或字段定义。验证说明只引用 09.Att.01 的字段名，不复制字段定义、类型、完整条件或禁止写法。

Code、Hook、测试或外部包装输出只能作为过程证据。commit validator 通过只说明提交消息格式和机器可检查条件当前通过，不替代 AI 对事实源、验证范围、Human Gate 和残留风险的判断。测试通过只支持验证声明，不替代 commit message 契约或 Human Gate。

本文不得安装、升级、禁用或卸载 Git Hook，不得修改 `core.hooksPath`，不得绕过 commit validator、失败测试或 Human Gate。需要安装或修复 Git Hook 时，应回到 01、10、30、Code 实现实践和 Human Gate。

## 7. Context、Scenario、Gate 与交还

| 结构 | 最小要求 |
|---|---|
| Context | 读取用户提交目标、当前 Git repo、工作区摘要、staged / unstaged / untracked 范围、必要 diff、changed paths、source_refs，并回指 `specs/03-事实源与Git溯源规范.md`、`specs/attachments/03.Att.01-Commit-Message契约字段表.md`、`specs/06-行动模板基础规范.md`、`specs/09-测试与验证规范.md`、`specs/attachments/09.Att.01-验证声明字段表.md`、`specs/07-Code确定性执行规范.md` 和 `code/docs/01-Git-Commit-and-Hook-Practice.md`。 |
| Scenario | 用户明确要求提交、修复提交消息、拆分已暂存变更、提交前预检、提交门禁阻断分流或文件事实源修改需要 Git records 溯源时适用；用户只是询问提交规则、验证规则或 Hook 实现时，只回答 03/09/01/07 边界，不创建提交。 |
| Gate | 已暂存变更与用户目标不一致、存在 unstaged / untracked 变更且范围不清、提交拆分边界不清、需要破坏性 Git 操作、需要绕过 commit validator 或 Git Hook、关键测试失败、缺少验证证据、存在 Human Gate 风险、跨管辖 / 非管辖 target 混合、需要安装或修复 Hook / commit gate / 环境入口时，必须暂停、拆分或进入 Human Gate。 |
| 执行 | 检查 Git 工作区摘要和必要 diff；只 stage 本次范围内文件；判断是否拆分；按 `03.Att.01` 形成提交说明和必要 body 小标题；按影响范围运行匹配验证或说明未验证范围；运行 commit validator 或等价提交消息检查；通过后才创建 commit；不安装 Hook、不修改 commit gate、不配置 CI、不把工具输出直接写成完成结论。 |
| 验证 | 验证入口按 `specs/09-测试与验证规范.md` 选择自动化测试、命令校验、等价验证或 Human 验收；验证声明回指 `09.Att.01`，至少说明验证目标、验证方式、验证入口、输入范围、关键输出、结论、残留风险和证据回指；失败、未运行或不可复现时不得声明完整验证。 |
| 回写 | Git 提交流程输出默认是过程输出；需要长期追溯的验证结论、失败诊断、残留风险、缺口或经验按 03/05/09 分流到对应事实源、事实对象、实现域文档或后续工作项；Git commit records 只溯源文件修改和提交说明，不替代事实对象、验证声明或 Human Gate。 |
| 交还 | 提交成功后交还 commit hash、提交 message 摘要、changed paths、验证摘要、残留风险、剩余 Git 工作区摘要、source_refs 和执行方式；未提交时交还阻断原因、未验证范围、缺少证据、建议拆分或后续分流。 |

## 8. 保障措施

| 要求 | 机制 | 触发 | 证据 | 缺口处理 |
|---|---|---|---|---|
| 提交范围要求 | 提交前必须确认单一主意图、主承载域和 staged 范围；由本文、03、06 保障 | 用户要求提交或 AI 准备创建提交时 | Git 工作区摘要、changed paths、必要 diff、用户目标 | 范围不清时暂停，拆分或进入 Human Gate |
| commit 契约引用要求 | 提交说明必须引用 03.Att.01，不复制字段闭集、枚举和 body 条件表；由本文、03、03.Att.01 保障 | 生成或修改 commit message 时 | commit message、source_refs、commit validator 输出 | 缺少契约引用或字段不合规时停止提交，回到 03.Att.01 |
| 验证声明要求 | 提交前必须按影响范围运行匹配验证或说明未验证范围；由本文、09、09.Att.01 保障 | 声称可提交或已提交时 | 验证入口、关键输出、结论、残留风险、证据回指 | 未验证、失败或不可复现时不得声明完整验证，必要时进入 Human Gate |
| Human Gate 要求 | 高影响范围、拆分不清、验证缺口、风险接受或破坏性 Git 操作必须交给 Human 决定；由本文、02、03、06、09 保障 | 提交范围或风险不能由 AI 单独判断时 | Human 确认记录、阻断说明、残留风险 | 未确认时停止提交并交还阻断原因 |
| 能力输出交还要求 | Code、Hook、测试或外部包装输出必须交还主控 AI 判断；由本文、02、06、07 保障 | 使用 commit validator、Hook、测试或外部包装时 | 过程输出、诊断、source_refs 和主控结论 | 外部输出不得直接放行；回到主控判断或分流 |
| 提交后交还要求 | 提交成功后必须交还 commit hash、验证摘要、残留风险和剩余工作区摘要；由本文、03、09 保障 | Git commit 创建后 | commit hash、message 摘要、验证摘要、Git 工作区摘要 | 缺少交还时补交；发现残留风险时按 03/09 分流 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 结构检查 | 是否具备 Context、Scenario、Gate、执行、验证、回写和交还七结构 | 保持为候选，不作为正式提交行动模板 |
| 来源检查 | 是否回指 03、03.Att.01、06、09、09.Att.01、07 和实现实践，不复制字段闭集、枚举、判定顺序或命令样例 | 回到来源规范或模板重写 |
| 范围检查 | 是否要求读取 staged / unstaged / untracked、必要 diff、changed paths 和用户目标 | 停止提交，补齐范围判断 |
| Gate 检查 | 是否覆盖提交拆分、破坏性 Git 操作、验证缺口、Human Gate、Hook / commit gate 安装和跨 target 风险 | 停止提交或进入 Human Gate |
| 验证检查 | 完成声明是否有验证入口、关键输出、结论、残留风险和证据回指 | 按 09 写为未验证、部分覆盖或阻断 |
| 交还检查 | 提交成功或阻断时是否交还 commit hash 或阻断原因、验证摘要、残留风险、source_refs 和剩余工作区摘要 | 补交交还摘要，不声明闭环 |

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 需要创建提交但提交范围、拆分边界或用户目标不清；
2. 已暂存变更与用户目标不一致，或混入 unstaged / untracked 风险；
3. 需要破坏性 Git 操作、绕过 validator、绕过 Hook、跳过失败测试或接受未验证范围；
4. 提交影响正式 specs、Code、tests、Web、事实源边界、环境入口或 Human Gate；
5. 需要安装、升级、禁用、卸载或修复 Git Hook、commit gate、CI 或环境入口；
6. 需要 Human 接受残留风险、事实源冲突或未完成分流。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法确定当前 Git repo、工作区范围或 staged paths；
2. 用户目标与待提交文件事实源修改不一致；
3. 多个独立目的被写入同一提交且没有 Human 明确接受；
4. commit message 复制、改写或绕过 03.Att.01 契约；
5. 验证未运行、失败或不可复现，却准备声明完整验证或可提交；
6. commit validator、Hook、测试或外部包装输出被写成事实源、Human Gate 或完成结论；
7. 需要安装或修改 Hook / commit gate / 环境入口，却没有转入对应规则和 Human Gate。

## 12. 待补齐事项

1. 后续 Code 可继续把 31 的七结构、Gate 和交还字段做成更细粒度可解析 contract，但不得让 Code 反向定义提交行动规则；
2. 后续 tests 应覆盖提交范围不清、缺少验证声明、复制 03.Att.01 字段闭集、绕过 validator 和提交后未交还的负例；
3. 若未来新增 Git 提交 Web 展示或确认 UI，必须回到 08 的 Web 边界、03 的事实源边界和本文 Human Gate，不得把 Web 状态写成提交完成证明。
