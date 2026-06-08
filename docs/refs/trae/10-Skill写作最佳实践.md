# Trae Skill 写作最佳实践

> 创建日期：2026-06-05
> 来源：Trae 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.trae.cn/ide/best-practice-for-how-to-write-a-good-skill | https://docs.trae.cn/ide/top-10-recommended-skills-for-development-scenarios

---

## 1. 结论摘要

Trae 官方将 Skill 定义为一份清晰、严谨、可执行的指令文档，用于告诉模型在什么条件下使用、按哪些步骤执行、产出什么结果。写好 Skill 的关键不是把 Prompt 写长，而是把一个稳定可复用的任务能力工程化：通过精准元数据提升触发命中率，通过明确边界避免误触发，通过结构化输入输出降低歧义，通过可执行步骤和失败策略提升稳定性，通过渐进式披露控制上下文消耗，并通过评测驱动持续迭代。

研发场景推荐 Skill 体现了同一原则：优秀 Skill 往往围绕单一研发任务建立明确能力边界，例如前端设计、代码审查、Web 应用测试、PR 创建、Lint 修复、文档更新或 Skill 查找。它们不是泛化的万能助手，而是把某一类高频工作流、项目约定、参考资料、脚本和输出结构封装成可复用能力。

---

## 2. Skill 的本质定位

Trae 官方文档强调，Skill 不是一次性 Prompt，也不是写给人阅读的说明文章，而是面向模型执行的长期能力模块。

一个 Skill 应回答三个问题：

| 问题 | 含义 | 写作重点 |
|---|---|---|
| When | 什么时候使用 | 触发条件、非触发条件、任务边界 |
| How | 如何执行 | 工作流、步骤、检查清单、脚本调用方式 |
| What | 产出什么 | 输出结构、验收标准、失败结果 |

因此，Skill 的写作目标不是让内容显得完整，而是让模型在正确场景下稳定触发、按预期步骤执行，并输出可验证结果。

---

## 3. 常见认知误区

### 3.1 Skill 不等于 Prompt

Prompt 偏向临时性、探索性和即兴交互；Skill 偏向长期复用、稳定执行和工程化维护。把一次对话中的长 Prompt 直接保存为 Skill，通常会导致职责过宽、边界模糊、触发不稳定。

更好的做法是从真实任务中提炼稳定流程，只保留可复用的触发条件、执行步骤、输入输出和失败策略。

### 3.2 Skill 不是写给人看的知识文档

Skill 的主要读者是模型。文档应使用模型可解析的结构化语言，少写背景解释，多写可执行指令。

不推荐写法：

```markdown
这个 Skill 主要帮助用户更好地理解项目，并在适当的时候给出专业建议。
```

推荐写法：

```markdown
Use this skill when:
- 用户请求审查本地代码变更。
- 用户请求评估 PR 的正确性、安全性或可维护性。

Do NOT use this skill when:
- 用户只是要求解释语法。
- 用户明确要求直接修改代码而非先审查。
```

### 3.3 Skill 不是越复杂越强

模型上下文窗口有限，每个被加载的 Skill 都会竞争上下文资源。过于复杂的 Skill 会降低命中率，增加执行分支，让模型难以判断重点。

更优原则是单一职责：一个 Skill 只解决一个明确问题，对应一个核心动作。

---

## 4. 元数据写作最佳实践

Skill 的 `name` 和 `description` 是模型发现 Skill 的入口，直接影响自动触发准确率。

### 4.1 name

`name` 应简洁、唯一、可识别。官方建议使用小写字母、数字和连字符，推荐动名词或动作型名称，长度不超过 64 个字符。

推荐示例：

```yaml
---
name: reviewing-code
description: Review code for correctness, maintainability, security risks, and edge cases. Use when the user asks for code review, PR feedback, implementation assessment, or potential bug analysis.
---
```

不推荐示例：

```yaml
---
name: helper-v2
description: Helps with things.
---
```

问题在于名称缺乏语义，描述没有说明能力范围和触发时机。

### 4.2 description

`description` 应从模型视角描述 Skill 能做什么、何时使用，并包含关键触发词。它不应使用第一人称，也不应只写泛化能力。

推荐结构：

```text
{核心能力}. Use when {触发场景、用户请求、任务类型}.
```

例如：

```yaml
description: Update project documentation based on source code changes. Use when reviewing pull requests, adding new APIs, changing behavior, or when the user asks whether docs need to be updated.
```

---

## 5. 边界写作最佳实践

Trae 官方强调，模型最容易犯的错误不是不知道怎么做，而是不知道什么时候该做。因此，好的 Skill 必须同时声明正向触发条件和负向排除条件。

推荐结构：

```markdown
## Use this skill when

- 用户请求执行某一类明确任务。
- 当前上下文包含该任务必需的目标对象。
- 用户希望获得该类任务的标准化输出。

## Do NOT use this skill when

- 用户只是询问概念，不要求执行。
- 用户请求的是相邻但不同的任务。
- 缺少关键输入且无法从上下文推断。
```

边界越清晰，自动触发越稳定。尤其是研发场景中，代码审查、测试执行、PR 创建、部署、文档更新等 Skill 必须明确区分“查看状态”“解释问题”和“执行操作”。

---

## 6. 输入输出结构化

Trae 官方建议用类似函数签名的方式定义 Input 和 Output。结构化输入输出可以降低歧义，让模型知道需要收集什么信息，以及最终应交付什么结果。

示例：

```yaml
Input:
  - target_files: string[]
  - user_goal: string
  - review_scope?: correctness | security | maintainability | performance | all

Output:
  - summary: string
  - findings: Finding[]
  - risk_level: low | medium | high
  - recommended_actions: string[]
```

对于需要执行命令或调用脚本的 Skill，还应声明脚本输入参数、成功输出和失败输出，避免模型在缺少参数时自行猜测。

---

## 7. 步骤必须明确可执行

Skill 的核心是可执行步骤，而不是抽象原则。复杂任务应拆成顺序明确的 Workflow，并在关键节点设置检查。

不推荐写法：

```markdown
检查项目情况，必要时运行测试，然后给出建议。
```

推荐写法：

```markdown
## Workflow

1. Identify target changes: determine whether the user wants to review local changes, a specific file, or a PR.
2. Inspect context: read relevant diffs, files, PR description, or user-provided snippets.
3. Check correctness: identify logic errors, missing edge cases, and inconsistent behavior.
4. Check maintainability: compare implementation with local conventions and existing patterns.
5. Check security: identify unsafe input handling, secret exposure, permission risks, or injection risks.
6. Produce report: group findings by severity and include concrete recommendations.
```

每一步都应是模型能实际执行的动作。

---

## 8. 失败策略必须完备

模型在失败场景下容易自由发挥。Skill 应显式声明失败路径，让模型知道何时停止、何时询问、何时降级、何时重试。

推荐结构：

```markdown
## Failure handling

- If required input is missing, ask the user for the missing field before proceeding.
- If a target file cannot be read, report the exact path and stop.
- If a command fails, summarize the failing command, exit code, key error output, and next recommended action.
- If validation fails, do not mark the task as complete.
- If the request is outside this skill's scope, explain the mismatch and do not continue with this skill.
```

对于带脚本的 Skill，脚本输出应自解释。好的脚本输出不仅说明发生了什么，还说明为什么失败以及下一步怎么做。

---

## 9. 渐进式披露与文件组织

Trae 官方建议 `SKILL.md` 应作为入口和导航，而不是包罗万象的大文件。详细参考资料、示例、模板和脚本应拆分到独立文件中。

推荐结构：

```text
skill-name/
├── SKILL.md
├── examples/
│   ├── input.md
│   └── output.md
├── templates/
│   └── report-template.md
└── resources/
    └── style-guide.md
```

关键实践：

1. `SKILL.md` 保持简洁，只保留必要触发条件、流程、输入输出和失败策略。
2. 详细规则拆到引用文件，避免主文件过长。
3. 引用深度尽量保持一层，避免 A 引 B、B 再引 C 的链式读取。
4. 长参考文件应增加目录，帮助模型快速定位内容。
5. 不要把 Skill 写成知识库全集。

---

## 10. 评测驱动与失败优先

Trae 官方推荐以评测驱动 Skill 构建，并从失败点开始设计。

推荐流程：

1. 建立无 Skill 基线：先让模型在没有 Skill 的情况下执行真实任务，观察不稳定、误解、遗漏和误触发。
2. 定义评测用例：针对失败点设计 3 到 5 个可复现用例，并明确通过和失败标准。
3. 编写最小化 Skill：只写刚好能解决当前评测问题的最小规则集合。
4. 补充边界和示例：在最短成功路径稳定后，再扩展边界条件、输入输出和示例。
5. 回归评测：任意修改 Skill 后，都应验证已有评测没有回退。
6. 真实使用校准：把误触发、漏触发、遗漏上下文等真实问题转化为新的评测用例。

这个流程的核心是：先找到模型真实失败点，再用 Skill 固化修正路径，而不是凭想象提前写复杂规则。

---

## 11. 从研发推荐 Skill 看优秀 Skill 的共同特征

Trae 官方推荐的研发场景 Skill 覆盖前端设计、前端开发、全栈开发、前端代码审查、通用代码审查、Web 应用测试、PR 创建、Lint 修复、文档更新和 Skill 查找。这些案例体现出几个共同特征。

### 11.1 面向明确研发场景

优秀 Skill 通常围绕一个高频研发动作展开，例如：

- 创建高质量前端界面；
- 审查本地代码或 PR；
- 使用 Playwright 测试 Web 应用；
- 创建符合项目规范的 PR；
- 修复 lint 和格式问题；
- 根据代码变更更新文档；
- 搜索和安装合适的 Skill。

这些场景都有清晰目标、明确输入和可验证输出。

### 11.2 资源文件服务执行路径

推荐 Skill 中有些只有 `SKILL.md`，有些会附带参考文件、故障排查指南、代码示例或脚本。资源文件不是为了堆资料，而是服务执行路径。

例如：

- 前端代码审查 Skill 可把业务逻辑规则、代码质量规则和性能规则拆到 references 文件。
- Web 应用测试 Skill 可附带 Playwright 示例脚本和服务启动脚本。
- 文档更新 Skill 可附带代码到文档的映射关系和文档约定。

### 11.3 输出结构稳定

代码审查、PR 创建、测试、文档更新等研发 Skill 都需要稳定输出结构。结构化输出能让用户快速判断结果，也方便后续流程继续消费。

### 11.4 与工具互补而不是替代工具

Skill 描述如何完成任务，MCP Server、命令行工具或脚本提供可调用能力。优秀 Skill 会约定何时调用工具、如何解释工具输出、失败时如何处理，而不是把工具能力和流程说明混为一谈。

---

## 12. 推荐的 SKILL.md 模板

```markdown
---
name: reviewing-code
description: Review code for correctness, maintainability, security risks, and edge cases. Use when the user asks for code review, PR feedback, implementation assessment, or potential bug analysis.
---

# reviewing-code

## Purpose

Review code changes and provide structured feedback about correctness, maintainability, security risks, edge cases, and suggested improvements.

## Use this skill when

- The user asks to review code.
- The user asks whether an implementation is correct.
- The user asks for PR feedback.
- The user asks to identify bugs, risks, or edge cases.

## Do NOT use this skill when

- The user only asks for syntax explanation.
- The user asks to directly implement a new feature.
- The user asks for general programming advice without concrete code.

## Input

- target_files: string[]
- user_goal: string
- review_scope?: correctness | security | maintainability | performance | all

## Output

- summary: string
- findings: Finding[]
- risk_level: low | medium | high
- recommended_actions: string[]

## Workflow

1. Identify the review scope from the user request.
2. Inspect the relevant files, diffs, or code snippets.
3. Check correctness and edge cases.
4. Check maintainability and consistency with project conventions.
5. Check security-sensitive behavior.
6. Produce structured findings with severity and actionable recommendations.

## Failure handling

- If no code or file target is available, ask the user to provide the target.
- If the target file cannot be read, report the missing or inaccessible path.
- If the review scope is ambiguous, default to correctness and maintainability.
- Do not modify files unless the user explicitly asks for implementation changes.

## Output format

Summary:
- ...

Findings:
1. Severity:
   Location:
   Issue:
   Impact:
   Recommendation:

Risk level:
- ...

Recommended next actions:
- ...
```

---

## 13. 反模式检查清单

编写或审查 Skill 时，可以用以下清单快速检查风险：

- `name` 是否语义模糊、含版本号或不符合命名习惯。
- `description` 是否没有说明触发时机。
- 是否把一次性 Prompt 直接保存为 Skill。
- 是否同时处理多个核心动作。
- 是否只写了 Use this skill when，没有写 Do NOT use this skill when。
- 是否缺少结构化 Input 和 Output。
- 是否把原则当步骤，没有可执行 Workflow。
- 是否缺少失败策略。
- 是否把大量背景知识塞进 `SKILL.md`。
- 是否引用链过深，导致模型难以按需读取。
- 是否没有评测用例，无法判断修改是否提升稳定性。
- 是否和 Rules、MCP Server 或工具脚本职责混淆。

---

## 14. 待进一步调研

1. Trae Skill 在同名、同触发场景、多 Skill 同时相关时的具体选择排序规则。
2. Trae Skill 自动触发时对 `description` 的实际匹配权重和截断策略。
3. Trae SOLO 技能市场中高质量 Skill 的结构共性和失败案例。
4. `.agents/skills/` 开放生态 Skill 与 `.trae/skills/` 项目 Skill 的长期兼容实践。
