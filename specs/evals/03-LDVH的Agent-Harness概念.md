# LD Vibe Harness 的 Agent Harness 概念

> 创建日期：2026-05-30
> 状态：内部调研
> 编号归属：70-89 内部调研
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 01-69 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-specs文档结构规范.md`、`specs/02-LDVH目录说明.md`、`specs/03-事实源边界与承载规范.md`

---

## 一、本文解决的问题

本文在 LD Vibe Harness 语境下重新解释 Agent Harness 概念，明确 Harness 在 Vibe Coding 场景下的含义、组成、价值，以及对 LD Vibe Harness 规范体系的启发。本文是内部调研，不直接构成强制规则；调研结论进入 01-69 正式规范区间或 ADR 后才成为稳定规则。

---

## 二、一句话说清

在 Vibe Coding 语境下，Harness 就是套在 LLM 外面的"工程约束 + 执行框架"，把随性的 AI 写代码变成可控、可复用、可验证、能上线的工程流程。

公式：

```text
Agent = LLM + Harness
```

也可以更口语地说：模型是脑子，Harness 是身子；LLM 负责理解和生成，Harness 负责约束、执行、验证和沉淀。

---

## 三、先理解 Vibe Coding

Vibe Coding 指的是：人用自然语言描述需求，AI 按"感觉"快速生成代码，人主要负责验收、调方向和做关键判断，而不是亲手写每一行代码。

它的优势很明显：

- 快，适合快速原型和创意验证
- 自由，用户可以用口语直接表达想法
- 低门槛，不需要一开始就写完整规格或技术方案

但它也有天然风险：

- **非确定性**：同样的需求，不同时间可能产出不同结果
- **幻觉**：AI 可能编造不存在的函数、库、参数或业务事实
- **无记忆**：容易反复踩同一个坑，不稳定遵守历史约定
- **弱约束**：可能越过架构边界，引入不合适依赖，破坏代码风格
- **难维护**：原型很爽，但项目变大后容易堆积技术债，不敢上生产

所以，Vibe Coding 本质上是一种"随性迭代"。它很适合起步，但如果没有 Harness，很难长期稳定交付。

---

## 四、Vibe Coding 里的 Harness 是什么

Harness 直译是"挽具、马具"。这个词很形象：

- LLM 像一匹强但野的马，能跑得很快
- Harness 像缰绳、马鞍、护栏、刹车和导航
- 人仍然是骑手，负责目标、方向、验收和关键决策

放到 AI 编程里，Harness 指围绕 LLM 构建的一整套"非模型"的工程化系统。它不只是提示词，也不只是某个工具，而是规则、上下文、工具、流程、验证和记忆的组合。

一句话：Harness 是把"AI 瞎写一通"的 Vibe Coding，改造成"有纪律、能检查、可复用、可追溯"的工程能力。

---

## 五、Harness 的四层核心含义

### 5.1 约束体系：Rules

约束体系告诉 AI 什么能做、什么不能做、应该按什么风格做。

常见内容包括：

- 项目架构和目录结构
- 命名规范、编码风格、格式要求
- 安全红线、依赖约束、禁用 API 清单
- 事实源边界、文档写入规则、任务状态规则
- `.trae/rules/`、`specs/` 这类 AI 工作手册

它解决的问题是：限制 AI 随意发挥，避免风格混乱、架构越界、安全漏洞和重复踩坑。

### 5.2 执行环境：Runtime / Sandbox

执行环境保证 AI 的每次行动发生在统一、可控、可复现的上下文里。

常见内容包括：

- 工作区、项目路径和权限边界
- 沙箱、超时、回滚和高危操作确认
- 依赖版本、运行环境、配置读取方式
- 会话状态、任务状态和断点续做能力

它解决的问题是：AI 不只是"说代码"，而是在受控环境里"做事情"，并且做错了可以发现、停止和修正。

### 5.3 工具链：Tooling

工具链让 AI 能调用外部能力，而不是只靠聊天生成文本。

常见工具包括：

- 文件读写、搜索、代码编辑
- Shell、Git、Docker、curl、数据库、浏览器
- 格式化、静态检查、单元测试、集成测试、安全扫描
- CI/CD、版本回滚、API 调用和日志查看

它解决的问题是：AI 可以真正完成"读取 → 修改 → 运行 → 检查 → 修复"的闭环，而不是只给建议。

### 5.4 工作流：Workflow

工作流把聊天式即兴编程，变成标准化工程流水线。

典型流程包括：

```text
意图输入 → 规格定义 → 任务拆分 → 编码 → 测试 → 修复 → Review → Human Gate → 关闭 → 复盘沉淀
```

它解决的问题是：避免 AI 在多步骤任务里状态混乱、漏步骤、重复工作或陷入死循环。

---

## 六、Harness 的实战组件清单

从工程落地看，一个可用的 Vibe Coding Harness 至少应包含以下组件：

| 组件 | 作用 | LD Vibe Harness 对应 |
|---|---|---|
| Ruleset | 约束 AI 行为 | specs/、.trae/rules/ |
| Context Manager | 管理输入给 AI 的上下文 | 事实源边界、最小可行动上下文 |
| Tool Router | 连接 AI 与外部工具 | 文件、Shell、Git、浏览器、API |
| Runtime / Sandbox | 控制执行环境 | 权限、隔离、超时、回滚、高危操作拦截 |
| Test Harness | 自动验证结果 | lint、typecheck、测试、覆盖率门禁 |
| Guardrails | 防止越界和事故 | Human Gate、密钥扫描、敏感文件保护 |
| Feedback Loop | 形成迭代闭环 | 错误捕获、自动修复、复测、Pitfall 沉淀 |
| Memory Store | 沉淀长期知识 | ADR、Task、Memo、Pitfall、Change |
| Skill System | 复用标准工作流 | Trae Solo Skill、标准流程模板 |

这些组件合在一起，才让 AI 从"会聊天的模型"变成"能干活的 Agent"。

---

## 七、为什么 Vibe Coding 必须配 Harness

Vibe Coding 原生的痛点，正好对应 Harness 的价值。

| Vibe Coding 痛点 | Harness 的回应 |
|---|---|
| 非确定性 | 用规则、测试和流程降低随机性 |
| 幻觉 | 用事实源、代码搜索和验证命令校正输出 |
| 无记忆 | 用 ADR、Pitfall、Change、Memo 等长期事实源沉淀经验 |
| 缺乏约束 | 用 Ruleset、Human Gate 管住边界 |
| 难维护 | 用规格、任务、Review、测试和变更记录保证可追溯 |
| 不敢上线 | 用自动化检查、安全扫描和人工确认降低生产风险 |

Harness 的核心价值不是让 AI"更会猜"，而是让 AI 的工作变得更可控、更可审计、更能反复执行。

换句话说：Harness 不是消灭 Vibe Coding 的自由感，而是给自由感加上工程底线。

---

## 八、Harness vs Framework vs Prompt Engineering

| 维度 | Harness | Framework（如 LangChain） | Prompt Engineering |
|---|---|---|---|
| 定位 | 面向交付的工程底座 | 搭建 AI 应用的开发框架 | 单次或局部对话技巧 |
| 形态 | 规则、工具、流程、验证、记忆的整车系统 | 可组合的积木和库 | 提示词模板和表达技巧 |
| 面向目标 | 长期工程化、生产可用、团队协作 | 快速实现特定 AI 应用 | 提升某次生成效果 |
| 可持续性 | 高，可复用、可追溯、可治理 | 中，需要持续自定义维护 | 低，容易失效和遗忘 |
| 对 Vibe Coding 的作用 | 把随性迭代纳入工程闭环 | 提供部分能力组件 | 改善单轮交互质量 |

简单说：

- Prompt Engineering 是"怎么跟 AI 说话"
- Framework 是"怎么搭 AI 应用"
- Harness 是"怎么让 AI 在真实工程项目里稳定干活"

---

## 九、Vibe Coding、Spec Coding 与 Harness Engineering

这三个概念不是互相替代，而是逐层增强。

| 阶段 | 核心特征 | 适合场景 | 主要风险 |
|---|---|---|---|
| Vibe Coding | 体感和灵感驱动，快速生成 | MVP、原型、创意探索 | 随机、幻觉、难维护 |
| Spec Coding | 规格契约先行，按明确接口实现 | 独立模块、生产功能、多人协作 | 前期需要更多梳理 |
| Harness Engineering | 搭建系统级工程底座 | 复杂系统、长期运维、团队规模化使用 AI | 需要持续治理和沉淀 |

更准确的关系是：

```text
Vibe Coding 提供速度
Spec Coding 提供清晰契约
Harness Engineering 提供长期稳定性
```

没有 Harness，Vibe Coding 容易停留在原型阶段；有了 Harness，Vibe Coding 才有机会进入生产级工程交付。

---

## 十、对 LD Vibe Harness 的启发

### 10.1 LD Vibe Harness 本身就是 Harness 的实践

从 Agent Harness 的视角看，LD Vibe Harness 不是简单的规范文档集合，也不是单纯的任务管理工具，而是一套为 Vibe Coding + Trae Solo 场景设计的 Harness 系统。

| Harness 组成 | LD Vibe Harness 对应实现 |
|---|---|
| Ruleset | specs/01-07、.trae/rules/ |
| Context Manager | 事实源边界规范、最小可行动上下文、按需读取机制 |
| Workflow | Task 状态机、Human Gate、验收关闭 |
| Guardrails | AI 协作规范、高危操作确认、密钥与依赖约束 |
| Memory Store | ldvh-base/tasks/、ldvh-base/adrs/、ldvh-base/pitfalls/、ldvh-base/changes/、ldvh-base/memos/ |
| Skill System | Trae Solo Skill、标准工作流模板 |
| Feedback Loop | 检查命令、局部验证、Change 记录、Pitfall 沉淀 |

LD Vibe Harness 的真正定位是：帮助项目把"和 AI 聊天做事"变成"有事实源、有边界、有流程、有验收、有沉淀"的长期协作系统。

### 10.2 LD Vibe Harness 的独特定位：不是 Framework，而是 Harness

LD Vibe Harness 的设计哲学与 Harness 理念高度契合：

- 它不是 Lego 积木式 Framework，而是开箱即用的工程协作底座
- 它不是单次 Prompt 技巧，而是长期可追溯的事实源体系
- 它强调强约束，但允许通过 specs 做项目级扩展
- 它面向"人主 AI 辅"，不是完全放任 AI 自主行动
- 它坚持事实源优先，而不是依赖模型记忆或聊天上下文

### 10.3 对 LD Vibe Harness 未来发展的启发

基于 Harness 视角，LD Vibe Harness 可以继续强化以下方向：

1. **增强执行循环的自主性**
   - 让 Skill 更主动识别常见模式
   - 在安全边界内自动完成规划、检查、修复和复测

2. **提升记忆持久化的结构化程度**
   - 除 Task、ADR、Pitfall、Change、Memo 外，可探索决策上下文快照、最佳实践库、常见问题库
   - 让 AI 更容易在执行前命中相关历史经验

3. **增强上下文管理的智能性**
   - 按任务类型智能加载文档
   - 减少无关上下文，提高关键事实召回率

4. **完善 Skill 生态**
   - 建立更多标准 Skill，覆盖意图澄清、风险识别、发布准备、审计复盘等场景
   - 明确每个 Skill 的触发条件、输入、输出和停止规则

5. **加强护栏自动化**
   - 增加更多自动化检查、格式检查、安全扫描和事实源一致性校验
   - 让人能把注意力集中在真正需要判断的事项上

### 10.4 对使用 LD Vibe Harness 的项目的启示

接入 LD Vibe Harness 的项目应该意识到：

1. **LD Vibe Harness 是 Harness，不只是工具**
   - 不要只把它当成任务看板，而要把它当作 AI 工程化协作底座

2. **事实源建设是核心**
   - ldvh-base/ 不是杂物目录，而是项目记忆和协作状态的核心载体

3. **specs 要体现项目特色**
   - 不要重复基础规范，应补充项目特有约束、检查命令和业务边界

4. **Skill 是可复用肌肉**
   - 常见工作流应逐步沉淀成 Skill，而不是每次靠临场提示

5. **Human Gate 是底线**
   - 不宜为了速度绕过确认点；真正的生产级 AI 协作建议保留人的关键判断

---

## 十一、常见误解

### 11.1 Harness 不是把 AI 管死

Harness 不是让 AI 失去创造力，而是让创造力发生在安全边界内。没有边界的自由很快会变成技术债和事故。

### 11.2 Harness 不是 Prompt 模板合集

Prompt 只是 Harness 的一小部分。真正的 Harness 还包括工具、权限、状态、验证、记忆和流程。

### 11.3 Harness 不是只给大团队用

个人项目也需要 Harness。哪怕只是固定检查命令、记录踩坑、维护任务状态，也是在建立最小 Harness。

### 11.4 Harness 不是完全自动化

在 Vibe Coding 场景下，Harness 的目标不是让人退出，而是让人从盯过程变成把方向、做验收、守底线。

---

## 十二、LD Vibe Harness 版口诀

```text
LD Vibe Harness 是 Harness；
specs 是骨架；
ldvh-base 是记忆；
Skill 是肌肉；
Human Gate 是护栏；
Change 是足迹；
Pitfall 是免疫系统；
行动模型是神经系统。
```

---

## 十三、Human Gate 与检查要求

本文是内部调研，不直接触发 Human Gate。

当本文结论需要进入 01-69 正式规范区间或创建 ADR 时，应评估 Human Gate。

调研检查至少包括：

| 检查项 | 标准 |
|---|---|
| 上位依据 | 已声明上位依据 |
| 调研边界 | 明确不直接构成强制规则 |
| 与 00 总纲一致性 | 不违背 LD Vibe Harness 理念和五类构成要素 |
| 与事实源边界一致性 | 不定义新的事实源规则，只讨论体验优化方向 |
| 升级路径 | 明确结论进入正式规范或 ADR 的路径 |

---

## 十四、待补齐事项

1. 本文结论如何进入 04 Trae Solo 环境机制规范（Skill / Agent / Rules 设计）待机制规范稳定后确定；
2. 本文结论如何影响 10-39 生产对象规范（如 Memory Store 结构化）待对象规范稳定后确定；
3. 本文结论如何影响 40-69 行动模型规范（如执行循环、上下文管理）待行动模型规范稳定后确定。
