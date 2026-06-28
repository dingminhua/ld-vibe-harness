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
  positioning: "给 AI 执行者、Code 和 Human 审核者提供 v3 的最高行动判断标准"
  scope: "v3 specs、code、schemas、attachments、Action Guide 以及后续迁移判断"
  basis:
    - "../ld-vibe-harness/specs/00-LDVH理念与价值标准.md"
  related_specs:
    - "specs/01-Specs基础规范.md"
  code_consumption:
    - "v3_spec_metadata"
    - "value_gate"
    - "stop_conditions"
    - "action_guide_value_gate"
```

> 文件状态：candidate；v3 正式化前不得反向改写 v2 active 规范。

## 1. 读者和使用方式

本文首先写给 AI 执行者，其次写给 Code，最后写给 Human 审核者。

AI 读本文时，只需要完成一个判断：当前 v3 设计、迁移或实现，是否真的让后续 AI 更容易行动。

Code 读本文时，只需要提取价值门、禁止项、停止条件和 Action Guide 质量要求。

Human 读本文时，只需要审核 v3 是否偏离 v2 00 的最高价值锚点。

## 2. AI 执行前价值门

AI 在推进任何 v3 specs 或 Code 工作前，必须先回答：

| 问题 | 不满足时的处理 |
|---|---|
| 这项工作减少 AI 哪类负担：定位、理解、判断、执行、验证或回写 | 停止，回到 Spark / WorkCase 澄清 |
| 这项工作是否仍以 Markdown 文件作为规范事实源 | 停止，不得建立第二事实源 |
| 这项工作是否能被 Code 确定性解析、校验或投影 | 若不能，先补结构或记录缺口 |
| 这项工作是否保留 Human Gate 和来源回指 | 停止，不得继续迁移 |
| 这项工作是否只是新增文档、附件或工具数量 | 停止，说明替代方案 |

不能通过价值门的内容，不进入 v3 正式 specs。

## 3. v3 当前只做什么

v3 当前只重构两件事：

| 对象 | 当前目标 |
|---|---|
| specs | 让 Markdown 规范更少重复、更可解析、更能指导 AI 行动 |
| Code | 从 Markdown 稳定结构生成诊断、索引和 Action Guide |

v3 当前不重构 `rules/`、`hooks/`、`skills/`、Runtime、Web 或 `ldvh-base/`。这些对象只能作为影响判断和后续迁移对象出现。

## 4. v3 不解决什么

AI 遇到以下目标时，不得把它们塞进当前 v3 specs + Code 工作：

1. 重新设计 LDVH 六类构成要素；
2. 修改 Runtime、hook、dispatcher、rules、skills 或 Web 策略；
3. 把普通 spec 正文改成长期 YAML 双维护；
4. 把 Action Guide 写成事实源、授权器、缓存或第二 Runtime；
5. 用一次性扫描结果直接删除 v2 正式规范内容；
6. 为了让 Code 好写而牺牲 Human 可读边界、Human Gate 或事实源回指。

## 5. 六类构成要素的 v3 边界

v3 继承 v2 00 的六类构成要素，不新增第七类。

| 构成要素 | v3 第一阶段处理方式 |
|---|---|
| 规范体系 | 写上位规则、父子规则、附件边界和去冗余方法 |
| 行为规则 | 由 02 承接 AI 通用行为边界 |
| 工作对象 | 由 03 承接 Spark、WorkCase、ADR、Pitfall、Study 等对象边界 |
| 行动编排 | 由 04 承接 Context、Scenario、Gate 和 Skill 承载边界 |
| Code | 只读解析、校验、投影和诊断 |
| Web | 暂不迁移；未来消费 Code 输出 |
| 运行时扩展 | 暂不迁移；不得顺手改 hook / dispatcher |

事实源仍是底层原则，不是第七类构成要素。

## 6. Action Guide 的价值门

Action Guide 是 Code 为当前任务生成的行动导航，不是知识库、图谱资产或事实源。

一个 Action Guide 只有在满足以下条件时才有价值：

| 条件 | AI 获得的帮助 |
|---|---|
| 有明确 target | 知道围绕哪个规范、附件、对象或行动判断 |
| 有 relationships | 知道上下游和影响范围 |
| 有 P0/P1 read_plan | 知道先读什么，不全文盲读 |
| 有 impact_judgment | 知道改动会影响谁 |
| 有 stop_conditions | 知道何时暂停、分流或 Human Gate |
| 有 next_queries | 信息不足时知道下一步问什么 |
| 有 verification | 知道如何验证而不是自述完成 |
| 有 source_refs | 每个行动相关判断可回到事实源 |

Action Guide 的质量目标是：渐进、足量、可回指、可停止。

## 7. Stop Conditions

AI 必须暂停并提交 Human 确认：

1. 需要改变 v2 00 的存在理由、AI 第一服务对象、六类构成要素、事实源原则或 V1-V10；
2. 需要改变 v3 当前范围，从 specs + Code 扩到 Runtime、hook、dispatcher、rules、skills 或 Web；
3. 需要删除本地 Human Gate、本地事实源边界或行动特有 delta；
4. 需要把 Action Guide 当作授权结论；
5. 需要让 Code 输出 `allowed`、`approved`、`unblocked` 等授权语义。

## 8. 下一步读取

AI 读完本文后：

1. 若要写或迁移 v3 spec，读 `specs/01-Specs基础规范.md`；
2. 若要判断附件怎么写，读 01 的附件；
3. 若要实现 Code，先等 04 或 Code 契约成立；
4. 若发现本文与 v2 00 冲突，停止并提交 Human Gate。
