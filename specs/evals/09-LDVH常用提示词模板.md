# LDVH 常用提示词模板

> 创建日期：2026-06-01
> 更新日期：2026-06-01
> 定位：LD Vibe Harness 内部常用提示词模板集合，用于在临时对话中快速发起规范检查、调研、审查和多角色思考
> 编号归属：`specs/evals/` 项目评估与内部辅助文档，编号仅用于排序和引用便利，不属于 specs 正式规范编号体系
> 使用边界：本文提供可复制使用的提示词模板，不直接构成 LD Vibe Harness 强制规则；实际执行仍以 `specs/00-79`、项目 Rules 和 `ldvh-base/` 事实实例为准
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/01-LDVH目录说明.md`、`specs/02-LDVH术语规范.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`
> 相关规范：`specs/11-LDVH-Trae-Solo-环境规范.md`、`specs/50-LDVH工作流基础规范.md`、`specs/51-multi-role-thinking-多角色思考.md`、`specs/51.06-Contract.md`

---

## 1. 使用说明

本文收集可直接复制到 AI 对话中的常用提示词模板。模板优先服务临时执行入口，不替代 Rules、Skill、Agent、Tools、Web 或 specs 正式规范。

在 Markdown 中无法定义跨所有编辑器通用的原生复制按钮。为了尽量接近“复制后直接可用”，本文把每个提示词放入独立代码块；在 Trae、GitHub、VS Code 等常见 Markdown 预览环境中，代码块通常自带复制按钮或可一键选中复制。

---

## 2. 模板：specs 根目录规范一致性多角色检查

### 2.1 适用场景

当需要检查 `/Users/dmh2002/trae_projects/ld-vibe-harness/specs` 根目录下的正式规范文件是否符合自身规范要求时使用。该模板要求进入多角色思考，并至少覆盖产品价值、治理规范、需求规范、文档工程、验证证据、风险权限等视角。执行模式可由使用者临时决定：轻量模式适合快速扫描，并行子 Agent 模式适合高风险、跨文件或需要更完整证据的审查。

### 2.2 可复制提示词

```markdown
请对 `/Users/dmh2002/trae_projects/ld-vibe-harness/specs` 根目录下的 Markdown 文件执行一次“自身规范符合性”检查，不检查 `specs/evals/` 和 `specs/refs/` 子目录，除非它们被根目录文件引用且必须作为背景读取。

目标：判断 specs 根目录正式规范文件是否符合 LDVH 自身规范体系要求，并输出可执行的整改建议。不要直接修改文件，先只做审查报告；如发现必须修改的事项，请列为建议动作，等待我确认。

必须先读取并遵守以下入口：
1. `/Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules/ldvh-project-rules.md`
2. `/Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules/ldvh-specs-rules.md`
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
   - 如属于 20-49 或 50-79 区段，是否符合事实模型或工作流基础规范及其附件型实践子文档规则。
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

## 3. 模板：单文件规范自检

```markdown
请检查以下文件是否符合 LDVH specs 文档规范和它自身声明的上位依据：

文件：`在这里填写文件绝对路径`

要求：
1. 先读取项目规则和适用的场景规则。
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

## 4. 模板：变更前 Human Gate 判断

```markdown
请判断以下计划变更是否需要 Human Gate，并说明依据：

计划变更：
- 在这里填写计划修改的文件、对象或机制

请读取并依据：
1. 项目规则。
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

## 5. 模板：修改后 Change 记录生成

```markdown
请根据本次已经完成的文件修改，生成或补齐 `ldvh-base/changes/` 下的 Change YAML 记录。

要求：
1. 先读取项目规则、事实模型基础规范和 Change 相关规范或既有 Change YAML 示例。
2. 不要把 Change 当作普通配置文件随意写入。
3. Change 记录应准确反映已发生的事实源修改，不夸大、不记录纯过程聊天。
4. affects 必须列出实际受影响文件。
5. validation 必须写明已做的检查或未做检查的原因。
6. 如本次修改涉及 Human Gate，请记录 required、confirmed_by 和 confirmation_context。

输出或写入前请先说明拟创建的文件名和主要字段。
```

---

## 6. 模板：核心价值专项审查

### 6.1 适用场景

当需要审查 LDVH 规范体系和项目实践是否真正落实 `specs/00-LD-Vibe-Harness理念与纲要.md` 提出的 V1-V10 核心价值时使用。该模板从设计和实践两个层面进行全面审查，并对"精准获得上下文"（V1 稳定理解）做专项深审。

设计层审查关注：规范体系是否为 V1-V7 提供了充分的设计支撑——是否有定义、有机制、有入口、有边界。

实践层审查关注：实际 AI 执行中 V1-V7 是否真正落地——AI 是否真的在行动前获得了足够上下文、是否真的遵守了规则、是否真的识别了门禁、是否真的留下了证据。

精准获得上下文专项审查关注：LDVH 体系中最基础的价值——AI 进入项目后能否精准获得最小可行动上下文——在设计上有无定义、在实践上有无落地、在验证上有无证据。

### 6.2 可复制提示词

```markdown
请对 LD Vibe Harness 的核心价值实现状况执行专项审查，紧紧围绕 `specs/00-LD-Vibe-Harness理念与纲要.md` 提出的 V1-V7 价值标准，从设计层和实践层两个层面全面审查，并对"精准获得上下文"做专项深审。

目标：判断 LDVH 规范体系和项目实践是否真正落实了核心价值，输出可执行的改进建议。不要直接修改文件，先只做审查报告；如发现必须修改的事项，请列为建议动作，等待我确认。

必须先读取并遵守以下入口：
1. `/Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules/ldvh-project-rules.md`
2. `/Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules/ldvh-specs-rules.md`
3. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/00-LD-Vibe-Harness理念与纲要.md`
4. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/01-LDVH目录说明.md`
5. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/02-LDVH术语规范.md`
6. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/03-Specs文档规范.md`
7. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/10-事实源边界与承载规范.md`
8. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/11-LDVH-Trae-Solo-环境规范.md`
9. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/13-LDVH事实模型基础规范.md`
10. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/50-LDVH工作流基础规范.md`
11. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/51-multi-role-thinking-多角色思考.md`
12. `/Users/dmh2002/trae_projects/ld-vibe-harness/specs/51.06-Contract.md`

请进入多角色思考。角色选择必须依据 `51.06-Contract.md` 的 RoleSelectionOutput 契约说明选择理由。至少包含：
- `product-value-reviewer`：从产品价值角度审查 V1-V7 是否被规范体系设计支撑，是否存在为机制而机制、价值标准被弱化或被替代指标替换的问题。
- `context-precision-reviewer`：专项审查"精准获得上下文"——AI 进入项目后能否精准获得最小可行动上下文。审查范围包括：Context 是否有定义、最小可行动上下文是否可度量、Rules 入口是否引导 AI 读取必要上下文、事实模型实例是否为 AI 提供了项目事实上下文、行动模型是否定义了场景识别和上下文加载流程、是否存在上下文过载或不足、AI 是否仍依赖聊天记忆而非文件事实源。
- `governance-reviewer`：审查事实源边界、单一事实源、Rules / Skill / Agent / Tools / Web 边界是否支撑核心价值，尤其是 V1（上下文来自文件事实源而非聊天记忆）和 V5（事实回写）。
- `verification-evidence-reviewer`：审查实践层——V1-V7 在实际执行中是否有可验证的落地证据，是否存在"规范写了但执行中没有证据"的空转问题。
- `ai-collaboration-architect`：审查行动模型（Context、Scenario、Gate、Rules 适用、Skill 进入、Agent 调度、事实源回写）对核心价值的设计支撑是否完整，尤其是 Context 定义是否覆盖所有场景、Scenario 识别是否可操作、Gate 触发条件是否明确。

如发现涉及工具、Web 或审计，也请按 `51.06-Contract.md` 追加对应角色。

审查维度分三层：

**第一层：设计层——规范体系对 V1-V7 的设计支撑**

对每个价值标准逐一审查：

| 价值标准 | 审查要点 |
|---|---|
| V1 稳定理解 | 是否有 Context 定义？最小可行动上下文是否可度量？Rules 入口是否引导 AI 读取必要上下文？事实模型是否为 AI 提供了项目事实上下文？行动模型是否定义了场景识别和上下文加载流程？ |
| V2 受控执行 | 行动模型是否定义了执行约束？Rules 是否覆盖关键场景？事实源边界是否约束 AI 修改范围？ |
| V3 门禁识别 | Human Gate 是否有明确定义和触发条件？行动模型是否规定了 AI 何时必须暂停？ |
| V4 证据沉淀 | 是否有 Evidence、Change 等事实模型对象？执行结果是否有可追溯的承载形式？ |
| V5 事实回写 | 事实源边界是否清晰？回写规则是否定义？工具是否提供受控写入入口？ |
| V6 人类确认质量 | Web Tools 是否提供确认界面？确认信息是否包含状态、风险、证据和影响？ |
| V7 持续改进 | Pitfall、Memo 等是否支持经验沉淀？失败是否能回到事实源改善后续行动？ |

对每个价值标准，判断：
- 是否有规范定义（有 / 部分 / 无）
- 是否有落地机制（Rules / Skill / Agent / Tools / Web / 事实模型实例）
- 是否有验证路径（如何证明已落地）
- 设计缺口是什么

**第二层：实践层——V1-V7 在实际执行中的落地情况**

审查实际项目执行中 V1-V7 是否真正落地：
- AI 执行任务时是否真的在行动前读取了必要上下文（而非依赖聊天记忆）？
- AI 是否真的遵守了 Rules 和事实源边界？
- Human Gate 是否被正确触发和执行？
- 事实实例是否被正确创建、维护和回写？
- 工具是否实际降低了维护成本，还是增加了复杂度？
- 人是否能基于事实源和证据完成验收？
- 同类失败是否进入了 Pitfall 或规范改进？

对每个价值标准，判断：
- 实践中是否有落地证据（有 / 部分 / 无）
- 落地证据在哪里（文件路径、Change 记录、执行日志）
- 实践缺口是什么

**第三层：专项层——精准获得上下文（V1）深审**

这是本次审查的重点。围绕以下问题逐一深审：

1. **Context 定义完整性**：行动模型是否为每种场景定义了 AI 行动前应获得的最小可行动上下文？是否存在场景缺少 Context 定义？
2. **上下文来源精准性**：AI 的上下文是否来自 Git 文件事实源，而非聊天记忆、工具缓存或派生数据？是否符合 `specs/10-事实源边界与承载规范.md`？
3. **上下文加载机制**：Rules 入口是否引导 AI 按场景加载必要上下文？工作区规则 → 项目规则 → 场景规则的读取链路是否完整？是否存在跳过读取直接执行的情况？
4. **上下文充分性**：AI 获得的上下文是否足够执行当前任务？是否存在反复询问已有事实、误读项目边界或遗漏关键约束的情况（V1 不满足时的表现）？
5. **上下文精简性**：AI 获得的上下文是否存在过载？是否读取了与当前任务无关的大量文件？最小可行动上下文是否可度量？
6. **场景识别与上下文匹配**：AI 是否能正确识别当前任务场景并加载对应上下文？Scenario 定义是否可操作？
7. **反向判断验证**：对照 `specs/00-LD-Vibe-Harness理念与纲要.md` §4.2 反向判断第1条——AI 是否仍需依赖聊天记忆才能继续项目？如果是，说明精准获得上下文未落实。

对每个深审问题，判断：
- 设计上有无定义（有 / 部分 / 无）
- 实践上有无落地（有 / 部分 / 无）
- 差距是什么
- 建议改进动作

五类构成要素与精准获得上下文的关系也需审查：

| 构成要素 | 对精准获得上下文的贡献 | 审查要点 |
|---|---|---|
| 介质 | YAML/Markdown 是否为 AI 提供了可解析、可读取的上下文 | 结构化承载是否优先用于高频读取场景 |
| Trae Solo 环境机制 | Rules/Skill/Agent 是否为 AI 提供了场景识别和上下文加载入口 | Rules 入口是否完整、Skill 是否有上下文前置要求 |
| 工具 | 工具是否辅助 AI 聚合和读取上下文 | 工具是否降低了上下文获取成本，还是增加了复杂度 |
| 事实模型 | 事实实例是否为 AI 提供了项目生产事实上下文 | 事实实例是否完整、是否可被 AI 直接读取和理解 |
| 行动模型 | Context 是否定义了最小可行动上下文 | Context 定义是否覆盖所有场景、是否可度量 |

执行模式由你先给出建议，但最终采用哪种由我临时决定：
1. 主上下文轻量模式：适合先做快速扫描和价值定位。
2. 多角色子 Agent 模式：适合对设计层和实践层并行深审，或当你判断单一上下文可能遗漏跨规范风险时使用。

请先输出 RoleSelectionOutput，包含：
- selected_roles
- excluded_roles
- mode_recommendation
- mode_reason
- human_gate_required
- human_gate_reason

然后等待我确认采用轻量模式还是并行子 Agent 模式，再继续执行。

输出报告请遵守 `51.06-Contract.md` 的 MultiRoleReport 契约，至少包含：
- applicability
- summary
- role_results
- alignment
- risk_summary
- execution_order
- write_back_suggestion
- human_gate

报告主体按三层维度组织：

**第一层：设计层审查结果**
- V1-V7 每个价值标准的设计支撑状况
- 设计缺口清单

**第二层：实践层审查结果**
- V1-V7 每个价值标准的实践落地状况
- 实践缺口清单

**第三层：精准获得上下文专项审查结果**
- 7 个深审问题的逐一结论
- 五类构成要素对精准获得上下文的贡献审查结论
- 反向判断验证结论

整改建议请按优先级分组：
- P0：核心价值未落实或被弱化的问题，尤其是精准获得上下文未落实、AI 仍依赖聊天记忆、上下文来源不符合事实源边界。
- P1：设计有定义但实践无证据的空转问题，或设计缺口影响核心价值闭环的问题。
- P2：可优化上下文精简性、可度量性或工具辅助效率的问题。

报告中每个发现都应包含：
- 价值标准编号（V1-V7）
- 审查层级（设计层 / 实践层 / 专项层）
- 问题摘要
- 依据的规范文件或章节
- 风险等级
- 建议动作
- 是否需要 Human Gate
- 是否建议写入 Change、Task、Risk、Evidence、Memo 或 ADR
```
