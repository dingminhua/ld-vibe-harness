# LDVH v3 理念与价值标准

```yaml
v3_spec:
  spec_id: "00"
  spec_kind: "spec"
  title: "LDVH v3 理念与价值标准"
  status: "candidate"
  authority: "candidate"
  canonical_path: "specs/00-LDVH-v3理念与价值标准.md"
  parent_spec: ""
  relation: ""
  positioning: "定义 LDVH v3 的价值锚点、AI 第一服务对象、六类构成要素、事实源原则、Code 确定性边界和行动指南价值标准"
  scope: "v3 specs、code、schemas、attachments、Action Guide 以及后续迁移判断"
  basis:
    - "../ld-vibe-harness/specs/00-LDVH理念与价值标准.md"
  related_specs:
    - "specs/01-规范体系基础规范.md"
  code_consumption:
    - "v3_spec_metadata"
    - "value_principles"
    - "action_guide_value_gate"
```

> 文件状态：candidate；v3 正式化前不得反向改写 v2 active 规范。

## 1. 本文解决的问题

本文定义 v3 为什么成立，以及 v3 如何继续服务 LDVH 的最高目标：让 AI 在持续演进的 Vibe Coding 项目中少读、少猜、少漂移、能停止、能验证、能回写。

v3 的直接目标不是创建更多规范、更多附件或更多工具，而是解决 v2 暴露出的三类负担：

1. specs 正文存在结构性重复，AI 需要反复阅读通用 doctrine；
2. Code 消费规范时仍依赖较多手工约定，难以稳定生成任务导航；
3. “知识地图”容易被理解为图谱或轻量索引，不能充分表达 AI 行动所需的读取、影响、停止、验证和下一步查询。

## 2. 继承的最高价值

v3 继承 v2 00 的最高锚点：

1. LDVH 以 AI 执行者为第一服务对象；
2. LDVH 服务项目持续演进中的稳定衔接，而不是一次性输出；
3. AI 的概率性、上下文依赖和无状态风险必须由结构化规则、事实源、行动编排、Code、Web 和运行时扩展共同约束；
4. 新增机制必须说明减少 AI 哪类定位、理解、判断、执行、验证或回写负担；
5. 不能只是复制已有规则、制造新入口或增加阅读负担。

v3 不重定义 v2 00 的存在理由、AI 第一服务对象、六类构成要素或事实源底层原则。v3 只定义下一代 specs 与 Code 如何更精确地服务这些价值。

## 3. v3 的改进焦点

v3 第一阶段只聚焦 `specs/` 与 `code/`：

| 焦点 | v3 改进 |
|---|---|
| specs | 保持 Markdown 正文为规范事实源；通过父层规则、章节角色和附件契约减少重复正文 |
| Code | 直接解析 Markdown 的稳定结构，生成可复查 IR、诊断和行动指南 |
| Action Guide | 取代“知识地图”作为面向当前任务的行动导航投影 |

v3 第一阶段不改变 `rules/`、`hooks/`、`skills/`、Runtime、Web 或 `ldvh-base/` 的策略。后续整体迁移必须另行确认。

## 4. 六类构成要素边界

v3 继续使用六类构成要素：

| 构成要素 | v3 第一阶段关注点 |
|---|---|
| 规范体系 | 定义父层规则、Markdown 结构、附件边界和可解析契约 |
| 事实模型 | 暂不重构；后续按 02 承接 |
| 行动编排 | 暂不全量迁移；先由行动指南样板验证读取、停止和回写导航 |
| Code | 只读解析、校验、投影和诊断，不授权、不替 Human Gate |
| Web | 暂不重构；未来消费行动指南或 Code DTO |
| 运行时扩展 | 暂不重构；不得由 v3 specs 重构顺手改变 hooks / dispatcher |

## 5. 事实源原则

v3 中稳定规则仍必须回到 Git 可追踪 Markdown 文件。Code 输出、Action Guide、生成索引、调试 YAML、测试 fixture、缓存或对话结论，都不是最终事实源。

普通 spec 正文不得长期维护一个人工 YAML 孪生文件。若 Code 无法解析 Markdown，应先改进 Markdown 的稳定结构或 01 的格式约束，而不是新增第二事实源。

## 6. Action Guide 价值标准

Action Guide 是确定性 Code 面向当前任务生成的导航投影，不是事实源、授权器、缓存或第二 Runtime。

Action Guide 必须至少服务以下行动要素：

| 要素 | 作用 |
|---|---|
| relationships | 告诉 AI 当前对象和哪些规范、附件、事实对象、行动成员有关 |
| read_plan | 告诉 AI 先读什么、为什么读、读到哪里可以停 |
| impact_judgment | 帮助 AI 判断改动可能影响哪些上游、下游和同步对象 |
| stop_conditions | 暴露必须暂停、分流或 Human Gate 的条件 |
| next_queries | 在信息不足时给出下一步可展开查询 |
| verification | 提示可复查的验证入口和证据要求 |
| source_refs | 让每个行动相关判断能回指事实源 |

Action Guide 的目标不是单纯轻量，而是渐进、足量、可回指、可停止。

## 7. v3 准入判断

任何 v3 规范、附件、schema、Code 输出或迁移样板，进入正式设计前必须回答：

1. 它服务哪些 v2 V1-V10 价值；
2. 它减少 AI 哪类负担；
3. 它是否保持 Markdown 事实源权威；
4. 它是否可被 Code 确定性解析或验证；
5. 它是否会制造第二事实源、第二授权器或第二 Runtime；
6. 它是否保留 Human Gate、事实源边界和来源回指。

## 8. Human Gate

以下情况必须暂停并等待 Human 确认：

1. 改变 v2 00 的存在理由、AI 第一服务对象、六类构成要素、事实源原则或 V1-V10；
2. 将 Action Guide 升级为事实源、授权器、缓存或 Runtime 阻断器；
3. 将普通 spec 正文改成长期 YAML 双维护；
4. 删除本地 Human Gate、本地事实源边界或行动特有 delta；
5. 修改 Runtime、hook、dispatcher、rules、skills 或 Web 策略。

## 9. 待补齐事项

1. 01 需要定义 v3 Markdown spec 结构、附件边界和去冗余规则；
2. 02/03/04 需要分别承接事实模型、行动编排和 Code 的 v3 下位规则；
3. 旧 `specs/core/` 内容需要被 00/01/04/Action Guide 正式规范吸收或清退，避免形成并列权威层；
4. Code 需要支持 v3 identity block，并保持对 v2 Markdown 的迁移读取能力。
