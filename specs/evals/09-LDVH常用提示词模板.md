# LDVH 常用提示词模板

> 创建日期：2026-06-01
> 更新日期：2026-06-01
> 定位：LD Vibe Harness 内部常用提示词模板集合，用于在临时对话中快速发起规范检查、调研、审查和多角色思考
> 编号归属：`specs/evals/` 项目评估与内部辅助文档，编号仅用于排序和引用便利，不属于 specs 正式规范编号体系
> 使用边界：本文提供可复制使用的提示词模板，不直接构成 LD Vibe Harness 强制规则；实际执行仍以 `specs/00-79`、项目 Rules 和 `ldvh-base/` 事实实例为准
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/01-LDVH目录说明.md`、`specs/02-LDVH术语规范.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`
> 相关规范：`specs/11-LDVH-AI协作规范.md`、`specs/11.01-Rules机制规范.md`、`specs/14-LDVH行动模型基础规范.md`、`specs/51-multi-role-thinking-多角色思考.md`、`specs/51.06-Contract.md`

---

## 一、使用说明

本文收集可直接复制到 AI 对话中的常用提示词模板。模板优先服务临时执行入口，不替代 Rules、Skill、Agent、Tools、Web 或 specs 正式规范。

在 Markdown 中无法定义跨所有编辑器通用的原生复制按钮。为了尽量接近“复制后直接可用”，本文把每个提示词放入独立代码块；在 Trae、GitHub、VS Code 等常见 Markdown 预览环境中，代码块通常自带复制按钮或可一键选中复制。

---

## 二、模板：specs 根目录规范一致性多角色检查

### 2.1 适用场景

当需要检查 `/Users/dmh2002/trae_projects/ld-vibe-harness/specs` 根目录下的正式规范文件是否符合自身规范要求时使用。该模板要求进入多角色思考，并至少覆盖产品价值、治理规范、需求规范、文档工程、验证证据、风险权限等视角。执行模式可由使用者临时决定：轻量模式适合快速扫描，并行子 Agent 模式适合高风险、跨文件或需要更完整证据的审查。

### 2.2 可复制提示词

```markdown
请对 `/Users/dmh2002/trae_projects/ld-vibe-harness/specs` 根目录下的 Markdown 文件执行一次“自身规范符合性”检查，不检查 `specs/evals/` 和 `specs/refs/` 子目录，除非它们被根目录文件引用且必须作为背景读取。

目标：判断 specs 根目录正式规范文件是否符合 LDVH 自身规范体系要求，并输出可执行的整改建议。不要直接修改文件，先只做审查报告；如发现必须修改的事项，请列为建议动作，等待我确认。

必须先读取并遵守以下入口：
1. `/Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules/ldvh-l1-rules.md`
2. `/Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules/ldvh-l2-specs-rules.md`
3. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/00-LD-Vibe-Harness理念与纲要.md`
4. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/01-LDVH目录说明.md`
5. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/02-LDVH术语规范.md`
6. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/03-Specs文档规范.md`
7. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/10-事实源边界与承载规范.md`
8. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/51-multi-role-thinking-多角色思考.md`
9. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/51.06-Contract.md`

请进入多角色思考。角色选择必须依据 `51.06-Contract.md` 的 RoleSelectionOutput 契约说明选择理由。至少包含：
- `product-value-reviewer`：检查规范是否服务 LDVH 价值目标，是否存在为机制而机制、范围膨胀或投入产出不清。
- `governance-reviewer`：检查事实源边界、编号规范、引用纪律、单一事实源、Rules / Skill / Agent / Tools / Web / Contract 边界。
- `requirement-spec-reviewer`：检查文档目标、范围、验收标准、事实源归属是否清晰。
- `documentation-engineer`：检查文档结构、头部元数据、引用路径、编号命名、索引同步、可读性。
- `verification-evidence-reviewer`：检查是否有可验证的完成标准、检查项、关闭证据和后续验收路径。
- `risk-permission-reviewer`：检查是否涉及 Human Gate、权限边界、不可逆变更或跨项目影响。

如发现涉及行动模型、Agent、Tools、Web 或审计，也请按 `51.06-Contract.md` 追加对应角色，例如：
- `ai-collaboration-architect`
- `tooling-architect`
- `webtools-product-reviewer`
- `audit-reviewer`

执行模式由你先给出建议，但最终采用哪种由我临时决定：
1. 主上下文轻量模式：适合先做快速抽样、结构扫描和风险定位。
2. 多角色子 Agent 模式：适合对多个文件并行深审，或当你判断单一上下文可能遗漏跨文件风险时使用。

请先输出 RoleSelectionOutput，包含：
- selected_roles
- excluded_roles
- mode_recommendation
- mode_reason
- human_gate_required
- human_gate_reason

然后等待我确认采用轻量模式还是并行子 Agent 模式，再继续执行。

审查范围要求：
1. 只检查 `specs` 根目录下的 `*.md` 文件。
2. 区分正式规范、集合索引、事实模型规范、行动模型规范、附件型实践子文档和契约子文档。
3. 对每个文件至少检查：
   - 头部元数据是否符合其文档类型要求。
   - 编号和路径是否符合 `01-LDVH目录说明.md`。
   - 术语是否符合 `02-LDVH术语规范.md`。
   - 是否存在复制维护其他权威文档规则正文的问题。
   - 是否存在反向边界章节或不符合 `03-Specs文档规范.md` 的结构问题。
   - 是否存在事实源边界不清、第二事实源、引用路径失效或索引未同步。
   - 如属于 20-49 或 50-79 区段，是否符合事实模型或行动模型基础规范及其附件型实践子文档规则。
4. 不要把 `specs/refs/` 的外部资料当作强制规则来源。
5. 不要把工具缓存、聊天过程或 Agent 输出当作事实源。

输出报告请遵守 `51.06-Contract.md` 的 MultiRoleReport 契约，至少包含：
- applicability
- summary
- role_results
- alignment
- risk_summary
- execution_order
- write_back_suggestion
- human_gate

整改建议请按优先级分组：
- P0：明显违反强约束或可能制造第二事实源的问题。
- P1：影响规范一致性、引用完整性或索引同步的问题。
- P2：可读性、结构清晰度或后续工具化检查可优化的问题。

报告中每个发现都应包含：
- 文件路径
- 问题摘要
- 依据的规范文件或章节
- 风险等级
- 建议动作
- 是否需要 Human Gate
- 是否建议写入 Change、Task、Risk、Evidence、Memo 或 ADR
```

---

## 三、模板：单文件规范自检

```markdown
请检查以下文件是否符合 LDVH specs 文档规范和它自身声明的上位依据：

文件：`在这里填写文件绝对路径`

要求：
1. 先读取项目 L1 Rules 和适用的 L2 Rules。
2. 读取该文件头部声明的上位依据和相关规范。
3. 判断文档类型：普通规范、索引、事实模型、行动模型、附件型实践子文档或契约子文档。
4. 检查头部元数据、编号归属、术语、引用纪律、事实源边界、Human Gate、Change 记录要求。
5. 不要直接修改，先输出问题清单和建议修改方案。
6. 如建议修改 specs 或 Rules，请说明是否需要同步创建或更新 `ldvh-base/changes/` Change 记录。

输出：
- 结论：通过 / 部分通过 / 不通过
- 高风险问题
- 中低风险问题
- 建议修改顺序
- 需要我确认的事项
```

---

## 四、模板：变更前 Human Gate 判断

```markdown
请判断以下计划变更是否需要 Human Gate，并说明依据：

计划变更：
- 在这里填写计划修改的文件、对象或机制

请读取并依据：
1. 项目 L1 Rules。
2. 与该文件或对象相关的 specs 权威规范。
3. 如涉及多角色思考，请读取 `specs/51-multi-role-thinking-多角色思考.md` 和 `specs/51.06-Contract.md`。

输出：
- 是否需要 Human Gate：true / false
- 触发原因
- 影响范围
- 建议确认项
- 未确认前允许做的只读检查
- 确认后允许执行的写入动作
```

---

## 五、模板：修改后 Change 记录生成

```markdown
请根据本次已经完成的文件修改，生成或补齐 `ldvh-base/changes/` 下的 Change YAML 记录。

要求：
1. 先读取项目 L1 Rules、事实模型基础规范和 Change 相关规范或既有 Change YAML 示例。
2. 不要把 Change 当作普通配置文件随意写入。
3. Change 记录应准确反映已发生的事实源修改，不夸大、不记录纯过程聊天。
4. affects 必须列出实际受影响文件。
5. validation 必须写明已做的检查或未做检查的原因。
6. 如本次修改涉及 Human Gate，请记录 required、confirmed_by 和 confirmation_context。

输出或写入前请先说明拟创建的文件名和主要字段。
```
