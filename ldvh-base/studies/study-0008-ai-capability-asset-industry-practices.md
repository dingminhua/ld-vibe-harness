---
id: study-0008
type: study
title: AI 能力资产行业最佳实践调研
status: active
created: '2026-06-20T10:25:42+08:00'
updated: '2026-06-20T10:25:42+08:00'
summary: |
  本报告补齐 workplan-0080 中此前缺失的外部行业最佳实践输入。调研对照 Anthropic / Claude Code 的 Skills、subagents、hooks、best practices，OpenAI Agents SDK 的 agent、guardrail、human-in-the-loop，MCP 工具暴露规范和 Git hook 官方文档，形成对 LDVH Rules、Skill、Agent、Hook 固定能力资产的可吸收规则：能力资产应保持上下文经济、渐进披露、明确发现条件、权限和工具边界、可验证输出、确定性优先、Human 审批和主控回收。
user_intent: 用户指出 workplan-0080 中“最佳实践”目前只是 LDVH 内部规则，缺少行业最佳实践内容，要求先补齐 memo / WorkPlan 相关规范基础。
conclusion: |
  行业实践并不支持把 Rules、Skill、Agent、Hook 写成厚重的第二规范；更一致的方向是：长期入口保持短而可维护，领域流程按需加载，代理角色隔离上下文并限制工具，Hook 优先承接确定性检查，涉及副作用或风险的动作必须有审批、可观测证据和可恢复状态。LDVH 04.02 应把这些结论吸收为规则，而外部 URL 只保留在 Study 中作为调研依据。
urls:
  - ref: https://code.claude.com/docs/en/best-practices
    title: Claude Code Best Practices
    summary: 用于对照上下文管理、先探索再计划再实现、可验证检查、hooks、skills、subagents 和权限配置等实践。
  - ref: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
    title: Skill authoring best practices
    summary: 用于对照 Skill 应保持简洁、按需加载、描述清晰、渐进披露、真实场景测试和可验证中间产物。
  - ref: https://code.claude.com/docs/en/skills
    title: Claude Code Skills
    summary: 用于说明 Skills 适合承接反复粘贴的流程、清单或多步程序，并通过元信息和按需加载降低上下文负担。
  - ref: https://code.claude.com/docs/en/sub-agents
    title: Claude Code Subagents
    summary: 用于说明 subagents 的上下文隔离、工具权限限制、描述驱动委派、并行研究和主对话回收边界。
  - ref: https://code.claude.com/docs/en/hooks-guide
    title: Claude Code Hooks Guide
    summary: 用于说明 hooks 适合确定性自动化和项目规则执行，判断型 hooks 应区别于命令型确定性检查。
  - ref: https://code.claude.com/docs/en/hooks
    title: Claude Code Hooks Reference
    summary: 用于说明 agent hooks 仍带实验性，生产工作流应优先命令 hooks，并区分阻塞与异步执行。
  - ref: https://developers.openai.com/api/docs/guides/agents
    title: OpenAI Agents SDK Guide
    summary: 用于对照应用拥有编排、工具执行、审批、状态和可观测性时的 agent SDK 分层。
  - ref: https://openai.github.io/openai-agents-python/guardrails/
    title: OpenAI Agents SDK Guardrails
    summary: 用于对照输入、输出和工具 guardrails 的触发边界、tripwire、阻塞执行和副作用控制。
  - ref: https://openai.github.io/openai-agents-python/human_in_the_loop/
    title: OpenAI Agents SDK Human-in-the-loop
    summary: 用于对照敏感工具调用的暂停、审批、拒绝、状态序列化和恢复机制。
  - ref: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
    title: MCP Tools Specification
    summary: 用于对照工具暴露应具备元信息、schema、变更通知、安全提示和 Human 可拒绝调用的交互边界。
  - ref: https://git-scm.com/docs/githooks
    title: Git githooks Documentation
    summary: 用于对照 Git hook 的触发时机、参数、退出码、可绕过性和 commit-msg hook 的标准行为。
related_memos:
  - memo-0017
related_workareas:
  - workarea-0012
related_workplans:
  - workplan-0080
  - workplan-0074
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/04.02-LDVH能力资产与落地保障规范.md
  - specs/10-Git提交规范.md
archive_reason:
---

# AI 能力资产行业最佳实践调研

## 研究问题

本报告回答：

1. 外部 AI 工程生态中，类似 Rules、Skill、Agent、Hook 的能力资产通常如何设计；
2. 哪些实践可以吸收到 LDVH 固定能力资产登记制；
3. 这些实践对 `workplan-0080` 和 `specs/04.02-LDVH能力资产与落地保障规范.md` 的关闭条件有什么影响。

## 输入与边界

本次调研范围限定为公开官方或准官方资料，访问时间为 2026-06-20：

- Anthropic / Claude Code：best practices、Skills、subagents、hooks guide、hooks reference；
- Anthropic Claude API：Skill authoring best practices；
- OpenAI：Agents SDK guide、Guardrails、Human-in-the-loop；
- Model Context Protocol：Tools specification；
- Git：githooks 官方文档。

本报告不把外部资料原文复制为 LDVH 规范。外部资料只用于提炼可复用设计原则；正式约束应吸收到 `specs/04.02-LDVH能力资产与落地保障规范.md`，并按 LDVH 自身术语和事实源边界表达。

## 关键发现

### 上下文经济是能力资产的第一约束

Claude Code best practices 和 Skill authoring best practices 都把上下文窗口视为需要主动管理的资源。长期入口文件应短、清晰、可维护；只有普遍适用的命令、风格、工作流规则和常见陷阱适合进入默认加载入口。领域知识、长流程、API 细节和偶发任务更适合按需 Skill、引用文件或工具读取。

对 LDVH 的吸收结论是：Rules 资产应继续保持薄入口定位；Skill、Agent、Hook 不能通过复制 specs 正文来提高“完整性”，而应通过稳定 ID、清晰描述、输入输出、验证入口和回指来源规范来提高可执行性。

### Skill 是按需加载的流程与知识包，不是第二规范

Claude Skills 的实践强调：

- 描述字段要说明“做什么”和“何时使用”，否则难以被正确发现；
- `SKILL.md` 应简洁，复杂资料拆到补充文件并按需读取；
- 脆弱、必须一致的任务应降低自由度，给出明确脚本、命令或检查顺序；
- 复杂任务应提供顺序工作流、反馈循环和可验证中间产物；
- Skill 需要用真实场景和目标模型测试，不应只靠作者直觉。

对 LDVH 的吸收结论是：固定 Skill 必须有明确触发条件、可复用工作流、验证入口和主控交还方式。它可以把 specs 转成执行清单，但不能新增字段、状态机或 Human Gate 条件。

### Agent 是隔离上下文和专业权限的运行期角色

Claude Code subagents 和 OpenAI Agents SDK 都把 agent 视为带角色、工具、状态、审批和编排边界的执行单元。Claude Code 强调 subagent 用于隔离会污染主上下文的搜索、日志、文件阅读和专项审查，并可限制工具。OpenAI Agents SDK 将复杂工作拆到 specialists、handoffs、state、guardrails 和 human review。

对 LDVH 的吸收结论是：Agent 资产应声明角色边界、上下文输入、允许工具、输出格式、证据回写和主控复核责任。Agent 输出不能直接成为事实源；主控或 Human 必须完成整合、验证和回写。

### Hook 优先承接确定性检查，判断型 Hook 需要降级边界

Claude Code hooks 明确适合“每次都必须发生”的确定性控制，例如格式化、验证命令和项目规则执行；其 hooks reference 也提示 agent hooks 仍具实验性，生产工作流应优先命令 hooks。Git githooks 文档则给出更底层的契约：不同 hook 有明确触发点、参数和退出码；`commit-msg` 接收提交消息文件路径，非零退出会中止提交，但可被 `--no-verify` 绕过。

对 LDVH 的吸收结论是：Hook 资产必须写清触发事件、参数、退出码语义、阻塞或异步行为、可绕过性、输出去向和降级方式。Hook 不能被写成“检查已经通过”的证据，更不能替代 CI、Code 校验、Human 授权或事实源回写。

### Guardrails、HITL 和 MCP 提醒能力资产必须有审批与可观测边界

OpenAI Agents SDK 的 guardrails 将输入、输出和工具调用检查分层，并区分阻塞执行和并行执行；HITL 机制让敏感工具调用暂停、由人审批或拒绝，并通过 run state 恢复。MCP tools 规范要求工具有名称、schema、能力声明和安全交互边界，并建议应用清楚展示哪些工具暴露给模型、何时调用工具、何时需要用户确认。

对 LDVH 的吸收结论是：能力资产登记不应只检查文件存在，还应检查权限、审批、可观测证据、失败处理和可恢复状态。涉及写入、提交、外部系统调用、长期配置或风险动作时，Human Gate 与 Code/Web 证据必须保持优先级。

## 建议

1. `workplan-0080` 初次进入 `review_needed` 时不应关闭，因为此前“行业实践”只作为口头审查维度存在，没有形成外部调研事实源；本 Study 形成后，该缺口可以作为已补齐项重新提交关闭审查。
2. `specs/04.02` 的 §2.2 已明确行业实践来源被提炼为 LDVH 规则，并补充上下文经济、渐进披露、触发描述、权限审批、可观测证据、确定性优先和 Hook 可绕过性等规则。
3. 后续设计 `ldvh-git-commit` Skill 和 `commit-msg` Hook 时，应直接消费本 Study 的结论：
   - Skill 承接可复用流程和验证入口；
   - Hook 只承接确定性门禁；
   - 两者都不替代 `specs/10-Git提交规范.md`、`commit_validate.py` 或 Git 提交事实源。
4. 外部资料不进入 specs 正文作为裸 URL；Study 的 `urls` 字段保留调研依据，specs 只保留吸收后的稳定规则。

## 后续分流

- `workplan-0080`：已新增行业实践调研吸收项，并可在补齐后重新进入关闭审查。
- `specs/04.02-LDVH能力资产与落地保障规范.md`：已吸收本报告的稳定规则。
- `workplan-0074`：后续实现 `ldvh-git-commit` Skill 和 `commit-msg` Hook 时，引用本 Study 作为设计输入之一。
- `memo-0017`：无需复制本报告正文，只需继续保留多 WorkPlan 分流关系。
