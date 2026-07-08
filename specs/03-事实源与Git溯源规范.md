# 事实源与Git溯源规范

```yaml
ldvh_spec:
  spec_id: "03"
  spec_kind: "spec"
  title: "事实源与Git溯源规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/03-事实源与Git溯源规范.md"
  parent_spec: "specs/00-理念与构成.md"
  relation: "refines"
  positioning: "定义事实源边界、非事实源排除、过程输出与证据回写、Git 溯源和 commit 契约的 V3 基础规则"
  scope: "事实源、Git 可追踪文件事实源、过程输出、证据、receipt、evidence、diagnostic、Git commit records、commit message 契约和事实源读取回写边界"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/04-Specs基础规范.md"
  related_specs:
    - "specs/05-事实模型基础规范.md"
    - "specs/06-行动模板基础规范.md"
    - "specs/07-Code确定性执行规范.md"
    - "specs/08-Web信息同步规范.md"
    - "specs/09-测试与验证规范.md"
    - "specs/attachments/03.Att.01-Commit-Message契约字段表.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "fact_source_boundaries"
    - "process_evidence_boundaries"
    - "git_traceability_rules"
    - "commit_contract_boundaries"
    - "commit_message_contract_fields"
    - "source_ref_requirements"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. 事实源边界"
      - "6. 过程输出、证据与回写"
      - "7. Git 溯源与提交契约"
    assurance_measures: "8. 保障措施"
    verification_method: "9. 验证方法"
    human_gate: "10. Human Gate"
    stop_conditions: "11. Stop Conditions"
    next_queries: "12. 待补齐事项"
```

> 文件状态：active；本文吸收 V2 事实源与 Git 溯源父层规则。本文不定义事实对象字段、行动模板步骤、Code parser 细节、Web 页面展示、Hook 安装或测试实现。

## 1. 价值判断

本文存在的价值，是让 AI 在读取、判断、回写、验证和提交时知道哪个位置才是稳定事实，哪些输出默认只是过程输出，以及一次 Git 文件事实源修改如何被溯源。

本文主要服务 V3、V6 和 V7，并支撑 V1、V2 和 V9：AI 需要据此判断事实源边界和过程输出边界，关键结论需要经过验证后按事实模型和来源证据受控回写到 Git 文件事实源，长期缺口、经验或残留风险不能停留在聊天、工具输出、Code 诊断、Web 状态、运行时 receipt 或迁移材料中。

## 2. 权威依据

本文承接 `specs/00-理念与构成.md` 的事实源边界、`specs/01-保障与衔接.md` 的 receipt/evidence/diagnostic 边界、`specs/02-AI行为规范.md` 的过程输出和证据处理责任，以及 `specs/04-Specs基础规范.md` 的 spec 结构规则。

若本文与 00 的事实源原则冲突，以 00 为准。若本文与 01 的保障消费语义冲突，应回到 01 和 Human Gate。若 Code、Web、测试、review 或迁移材料与本文冲突，以本文和上位规范为准。

## 3. 归口边界

本文归口定义事实源、非事实源排除、过程输出与证据回写、Git 溯源和 commit 契约的基础规则。

本文不归口定义事实模型字段、行动模板流程、Code 输出 schema、Web 页面、环境入口、Hook 安装、测试用例或具体 commit validator 实现。相邻规则应分别进入 05、06、07、08、09 或 01。

## 4. 适用范围

本文适用于 LDVH 自身和后续接入项目中的：

1. 事实对象、行动状态、验证结论、决策、经验和缺口的稳定事实承载判断；规范正文的规则承载与修改溯源按规则源和 Git 溯源边界处理。
2. AI、Code、Web、测试、Hook、子 Agent、命令和迁移材料产生的过程输出和证据判断；
3. Git 文件事实源修改后的溯源说明；
4. commit message 契约、提交范围说明和提交后回查。

## 5. 事实源边界

事实源的有效承载形态是 Git 可追踪文件。一个事实只有写入其对应权威文件位置，并可通过 Git 历史溯源，才可能成为稳定事实。

以下内容默认不是事实源：

| 内容 | 边界 |
|---|---|
| 聊天和 AI 推理 | 只能作为当前上下文或候选判断，稳定结论必须回写。 |
| Code 输出和测试输出 | 只能作为诊断、验证证据或过程输出，不替代正文规则和事实对象。 |
| Web 页面状态和缓存 | 只能展示或辅助 Human 判断，不成为事实源。 |
| runtime receipt | 证明某个消费动作发生过，不证明规则满足、授权完成或事实稳定。 |
| 历史迁移材料 | 已从工作树删除；Git history 只能作为审计追溯、争议复核或历史取证的备份渠道，不授权正式规则、实现行为、验收通过或未迁内容承接。 |
| Git commit records | 溯源文件事实源修改，不替代被修改的事实源文件。 |

同一稳定事实只能有一个权威位置。其它位置可以引用、摘要、展示或派生，但不得复制维护为第二事实源。

`specs/` 正文是规则源，不是事实源；规范文件的修改可以被 Git 溯源，但规范正文不得作为事实对象或稳定事实承载。

V3 删除准备度和当前主线验收必须以当前工作树自足为准。若某项内容只存在于已删除的 V2 历史中，它在当前 V3 中默认没有规则效力；需要继续使用时，必须进入当前 V3 specs、事实对象、实现域文档或明确的后续 WorkCase，而不能以“Git history 可查”作为已迁入、已验收或可日常使用的依据。

状态归口受 `specs/04-Specs基础规范.md` 约束。除 specs / attachments 自身生命周期状态外，只有进入 Git 可追踪事实源的事实对象业务状态可以成为稳定状态；Code 输出、环境审计、安装检测、Web 展示、测试结果和 CLI summary 中的 `status`、`state` 或“状态”只能作为过程输出、验证证据或展示输出，不得被本文写成事实源。

## 6. 过程输出、证据与回写

过程输出包括 AI 输出、子 Agent 输出、Code 诊断、测试结果、命令输出、Web 展示、review 收据、runtime receipt 和迁移材料。过程输出必须先被 AI 定性，再决定是否记录为证据或回写。

过程输出满足以下条件之一时，应判断是否记录为证据或回写：

1. 形成长期规则、事实、决策、经验、风险或缺口；
2. 支撑完成声明、验证声明、关闭判断或 Human Gate；
3. 影响后续 AI 读取、Code 校验、Web 展示或测试回归；
4. 暴露事实源冲突、规则缺口、能力缺口或不可验证范围。

回写必须说明目标事实源、来源证据、采纳范围和验证方式。不能回写时，AI 必须说明原因、影响范围和后续承接位置，不得把“已输出”写成“已形成稳定事实”。

## 7. Git 溯源与提交契约

Git commit records 用于溯源文件事实源的修改。它们回答本次修改改了什么、为什么改、影响哪里、如何验证和后续风险是什么。

V3 保留 commit 契约的父层规则：

1. 提交首行应表达单一主意图和主承载域；
2. commit message 不得掩盖未验证、Human Gate 未决、事实源冲突或残留风险；
3. 多个独立目的应拆分提交；
4. 影响正式 specs、Code、tests、Web、事实源边界或环境入口的提交，应在正文说明关键变更、验证和风险；
5. Git 提交记录不替代事实源文件、事实对象、Human Gate 或验证声明。

具体 type、scope、body 条件和 message 字段由 `specs/attachments/03.Att.01-Commit-Message契约字段表.md` 承接；该附件只维护字段闭集、枚举和机器契约，不承载提交流程、Human Gate 或 Hook 实现。样例和 parser 规则由 Code 和 tests 承接。其它旧 V2 `07.Att.*` 仅保留为历史审计语境；未进入当前 V3 specs、附件、Code/tests 或明确 WorkCase 的条目不自动成为 V3 附件、当前规则或删除阻断。

## 8. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 事实源回指要求 | 结论、证据、完成声明和风险必须回指 Git 文件事实源或说明不可回写原因 | 本文、02、06、09、Code source_refs | 事实源治理 | AI 形成稳定结论、验证声明或提交说明时 |
| 非事实源排除要求 | 过程输出不得被写成事实源 | 本文、01 receipt 边界、08 证据边界 | 证据治理 | 使用 Code、Web、测试、review 或 runtime 输出时 |
| 状态归口要求 | 运行、验证、审计、交互或展示输出中的 status/state 不得被写成事实源状态 | 本文、04、05 | 事实源治理 | 使用 Code、Web、测试、环境审计或安装检测输出时 |
| Git 溯源要求 | 文件事实源修改应可通过 Git commit records 回查 | 本文、31 Git 提交行动模板、Code/tests | 溯源治理 | 提交正式 docs、Code、tests 或事实源修改时 |
| commit 契约要求 | 提交说明不得替代验证、Human Gate 或事实源正文 | 本文、31 Git 提交行动模板、09 验证声明 | 提交治理 | 生成 commit message 或提交前检查时 |

## 9. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 事实源边界检查 | 稳定结论是否写入或回指 Git 可追踪文件事实源 | 改为候选、过程输出或待回写缺口 |
| 非事实源排除检查 | 聊天、Code、Web、测试、review、receipt 或迁移材料是否被误写成事实源 | 停止完成声明并回到事实源边界 |
| 状态归口检查 | 只有 specs / attachments 生命周期状态和事实对象业务状态被记录为稳定状态，其它 status/state 是否只作为过程输出或验证证据 | 回到 04 状态归口原则或 05 事实对象规则 |
| 回写检查 | 过程输出被采纳时是否说明采纳范围、目标位置和验证方式 | 记录为 unverifiable 或 follow-up |
| Git 溯源检查 | 提交说明是否说明关键变更和验证，不掩盖风险 | 回到 commit 契约、行动模板或 Human Gate |

Code 可以检查路径、source_refs、commit message 格式和诊断结构；AI 必须判断事实源权威、采纳范围和残留风险；Human Gate 负责确认高影响事实源改变和风险接受。

## 10. Human Gate

以下情况必须进入 Human Gate：

1. 改变事实源边界或允许非 Git 文件成为事实源；
2. 接受过程输出无法回写但仍作为稳定事实使用；
3. 改变 commit 契约导致溯源能力下降；
4. 将 Git commit records 升级为事实对象或替代文件事实源；
5. 接受事实源冲突、不可验证证据或未完成回写的长期风险。

## 11. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 无法判断权威事实源位置；
2. commit message 掩盖未验证范围、Human Gate 未决或事实源冲突；
3. 需要接受事实源不一致或不可溯源风险但未获得 Human 确认。

## 12. 待补齐事项

1. V2 `07.Att.*` 删除准备度判定已收口：commit type、scope、body 条件和 message 字段由 `03.Att.01`、Code 和 tests 承接；非事实源排除、过程输出回写、读取策略和承载介质边界由本文、01、09 和 Code source_refs 承接。未进入当前 V3 specs、附件、Code/tests 或明确 WorkCase 的 V2 条目不作为当前规则、验收依据或删除阻断；后续发现缺漏时按 V3 00 新建 V3-owned 待办；
2. 后续 Code 应承接 commit message parser、source_refs 检查和过程输出回写诊断；
3. Git 提交行动、提交拆分、验证说明和提交后交还已由 `specs/31-Git提交行动模板.md` 承接；后续只在验证或回写闭环变化时修订 31；
4. 后续 Web 应承接提交记录展示和事实源证据展示边界。
