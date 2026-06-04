# LDVH 规范即机制 — Rules 与 Skill 自动生成评估

> 创建日期：2026-06-04
> 定位：项目评估文档，评估 Rules 和 Skill 从 specs 自动生成的可行性、收益和前提条件
> 适用范围：LD Vibe Harness Rules/Skill 自动生成机制的设计评估
> 上位依据：`specs/11.01-Rules机制规范.md`、`specs/11.02-Skill机制规范.md`

---

## 1. 核心思想

**specs 是唯一权威源，Rules/Skill 是派生产物。**

当前 LDVH 的规则和技能是手工从 specs 翻译到 Trae Rules 和 Trae Skill 的"副本"。副本和原件之间没有同步机制，翻译过程中容易遗漏或走样，导致"规范写了但执行跳过"（Pitfall-0004/0005）。

解决方案：建立两个生成 Skill，从 specs 自动生成 Rules 和 Skill。文档改对，生成自然对；文档改错，生成自然错。问题收敛到 specs 一个维度。

---

## 2. 两个生成 Skill

### 2.1 ldvh-gen-rules

从 specs 自动生成 Trae Rules 文件（`.trae/rules/`）。

**输入**：
- `specs/NN-对象名.md`（主文档）
- `specs/NN.01-Rules.md`（Rules 子文档）
- `specs/11.01-Rules机制规范.md`（Rules 机制规范）
- `ldvh-base/profiles/`（项目配置，确定项目路径和 ldvh-base 路径）

**输出**：
- `.trae/rules/ldvh-l0-fact-model-rules.md`（L0 事实模型规则，含所有对象关键规则入口）
- `.trae/rules/ldvh-l1-rules.md`（L1 项目规则，如项目有独立 L1）

**生成逻辑**：
1. 扫描所有 active 状态的 fact model 主文档和 Rules 子文档
2. 提取每个对象的关键规则（状态变更规则、关闭条件、Human Gate 场景）
3. 按层级（L0/L1）组装 Rules 文件
4. L0 承载跨项目通用规则入口，L1 承载项目特定规则

### 2.2 ldvh-gen-skills

从 specs 自动生成 Trae Skill 文件（`.trae/skills/`）。

**输入**：
- `specs/NN-对象名.md`（主文档）
- `specs/NN.02-Skill.md`（Skill 子文档）
- `specs/11.02-Skill机制规范.md`（Skill 机制规范）
- `tools/`（PyTools 命令清单，确定 Skill 可调用的命令）

**输出**：
- `.trae/skills/ldvh-intake/SKILL.md`
- `.trae/skills/ldvh-close/SKILL.md`
- `.trae/skills/ldvh-adr/SKILL.md`
- `.trae/skills/ldvh-commit/SKILL.md`
- `.trae/skills/ldvh-gen-rules/SKILL.md`
- `.trae/skills/ldvh-gen-skills/SKILL.md`

**生成逻辑**：
1. 扫描所有 active 状态的 fact model 主文档和 Skill 子文档
2. 提取每个 Skill 的流程步骤、PyTools 调用点、Human Gate 场景
3. 按生命周期阶段组装 Skill 文件
4. Skill 只放流程骨架和 PyTools 调用点，详细内容引用 specs

---

## 3. 好处

### 3.1 一致性保证

- specs 是唯一权威源，不存在"规范写了执行跳过"的问题
- 文档改对，生成自然对；问题收敛到 specs 一个维度
- 消除 specs、Rules、Skill 三方维护的同步负担

### 3.2 初始化简化

- 新项目接入 LDVH，运行两个 Skill 即可生成全部 Rules 和 Skills
- 不需要逐个手动创建 Rules 和 Skill 文件
- Profile 配置作为生成参数，自动适配项目路径

### 3.3 动态更新

- specs 变更后重新生成，无需手动同步
- 生成前后 diff 对比，容易发现 specs 变更的影响范围
- 避免"改了 specs 忘了改 Rules/Skill"的问题

### 3.4 审计友好

- 生成的文件标记 `AUTO-GENERATED` 和 specs 版本/commit hash
- 对比两次生成的 diff，可以精确追踪 specs 变更对运行时行为的影响
- 生成验证确保覆盖了 specs 中的关键规则

### 3.5 维护成本降低

- 只维护 specs，不需要同时维护 specs + Rules + Skill 三套文档
- 规范变更的传播路径从"specs → 人工翻译 → Rules/Skill"简化为"specs → 自动生成"
- 减少 Pitfall-0004/0005 类问题的复发

### 3.6 Dogfood 自身

- 用 LDVH 的机制来管理 LDVH 的机制
- 生成 Skill 本身也是 LDVH 的 Skill，遵循 LDVH 的规范
- 生成过程暴露 specs 的结构化问题，驱动 specs 质量提升

---

## 4. 需要注意和配合的地方

### 4.1 specs 文档结构化要求（最关键的前提）

当前 specs 是 Markdown，AI 可以理解但程序难以精确解析。要让生成可靠，specs 必须满足：

1. **章节编号和标题固定**：便于程序定位和提取
2. **状态枚举使用固定表格格式**：`| 状态 | 含义 |`，便于解析
3. **流转矩阵使用固定表格格式**：`| 当前状态 | 可流转至 |`，便于解析
4. **字段契约使用固定表格格式**：`| 字段名 | 类型 | 必填 | 说明 |`，便于解析
5. **Human Gate 场景使用固定列表格式**：`1. 场景描述`，便于提取
6. **Rules/Skill 子文档章节结构固定**：便于模板化生成

**当前差距**：部分 specs 文档的表格格式不统一（如 27.06-Contract 流转矩阵刚从三列改为两列），需要统一。

### 4.2 生成模板设计

Rules 和 Skill 的生成模板需要精心设计：

1. **Rules 模板**：
   - L0 事实模型规则：从各 NN.01-Rules.md 提取关键规则，组装为入口提醒
   - L1 项目规则：从 Profile 和项目配置提取项目特定规则
   - 模板应支持"最小集 + 引用"模式：只放关键约束，详细内容引用 specs

2. **Skill 模板**：
   - 生命周期 Skill：从各 NN.02-Skill.md 提取流程步骤
   - Skill 只放流程骨架和 PyTools 调用点
   - Human Gate 场景自动映射为 AskUserQuestion 调用

### 4.3 人工定制处理

生成的文件可能需要人工微调（如项目特定的规则补充）。处理方案：

1. **AUTO-GENERATED 标记**：生成的文件头部标记来源和版本
2. **Override 机制**：人工定制通过 `.trae/rules/override/` 或 `.trae/skills/override/` 目录存放
3. **生成时不覆盖 override**：全量重新生成时跳过 override 目录
4. **Override 冲突检测**：生成后检查 override 是否与生成的规则冲突

### 4.4 生成验证

AI 生成是非确定性的，同样的 specs 两次生成可能产出略有不同的 Rules/Skill。需要验证机制：

1. **覆盖度检查**：生成的 Rules/Skill 是否覆盖了 specs 中的关键规则
2. **格式校验**：生成的文件是否符合 Trae Rules/Skill 格式要求
3. **引用完整性**：生成的文件中引用的 specs 路径是否有效
4. **Fact Validator**：生成后运行 `check_fact_model.py` 校验
5. **Diff 审计**：对比生成前后的 diff，确认变更符合预期

### 4.5 跨项目适配

不同项目的 ldvh-base/ 路径不同，Profile 配置不同。生成时需要：

1. 读取 Profile 中的项目路径和 ldvh-base 路径
2. 生成的 Rules/Skill 中的路径引用使用 Profile 配置
3. 支持多项目生成（一个工作区多个管辖项目）

### 4.6 生成时机

1. **手动触发**：用户执行 `ldvh-gen-rules` 或 `ldvh-gen-skills`
2. **specs 变更后自动触发**：ldvh-commit 或 ldvh-close 检测到 specs 变更时自动触发
3. **初始化时触发**：新项目接入 LDVH 时触发

建议先实现手动触发，验证稳定后再考虑自动触发。

### 4.7 生成粒度

1. **全量重新生成**：所有 Rules/Skill 全部重新生成，简单可靠
2. **按对象类型增量生成**：只重新生成变更对象相关的 Rules/Skill

建议：默认全量重新生成，避免增量同步遗漏。支持 `--type <object_type>` 参数按对象类型增量生成。

### 4.8 对现有 specs 的影响

实现自动生成需要对现有 specs 进行调整：

1. **11.01-Rules机制规范**：增加"Rules 生成规范"章节，定义生成源、生成模板、生成验证
2. **11.02-Skill机制规范**：增加"Skill 生成规范"章节，定义生成源、生成模板、生成验证
3. **04-LDVH模型子文档规范**：增加子文档结构化标记要求（固定章节标题、固定表格格式）
4. **各 NN.01/N.02 子文档**：统一章节结构，确保可被模板化生成
5. **20-事实模型集合索引**：增加对象类型到 Rules/Skill 模板的映射关系

### 4.9 AI 生成的非确定性问题

AI 生成不是确定性编译，同样的输入可能产出不同的输出。缓解方案：

1. **模板约束**：生成模板尽量结构化，减少 AI 自由发挥空间
2. **关键规则锚定**：从 specs 提取的关键规则使用原文，不重新表述
3. **生成 + 验证闭环**：生成后验证覆盖度，不覆盖则重新生成
4. **版本标记**：生成的文件标记 specs commit hash，便于追溯

### 4.10 循环依赖风险

ldvh-gen-rules 和 ldvh-gen-skills 自身也是 Skill，它们的 SKILL.md 是否也由自己生成？

1. **初始版本手工创建**：两个生成 Skill 的 SKILL.md 手工创建
2. **稳定后自举**：生成 Skill 稳定后，可以尝试用自身生成自己的 SKILL.md
3. **自举验证**：对比手工版本和生成版本，确认自举可行

---

## 5. 实施路径建议

### 阶段一：specs 结构化

1. 统一所有 NN.01-Rules.md 和 NN.02-Skill.md 的章节结构
2. 统一状态枚举、流转矩阵、字段契约的表格格式
3. 为 specs 文档增加结构化标记（如 YAML front matter）

### 阶段二：生成 Skill 实现

1. 实现 ldvh-gen-rules（先支持全量重新生成）
2. 实现 ldvh-gen-skills（先支持全量重新生成）
3. 生成验证机制（覆盖度检查 + 格式校验）

### 阶段三：集成和自举

1. specs 变更后自动触发重新生成
2. 生成 Skill 自举（用自己的规范生成自己的 SKILL.md）
3. Override 机制和冲突检测

---

## 6. 与现有机制的关系

| 现有机制 | 与生成机制的关系 |
|---|---|
| NN.01-Rules.md | 生成源，ldvh-gen-rules 从中提取关键规则 |
| NN.02-Skill.md | 生成源，ldvh-gen-skills 从中提取流程步骤 |
| NN.06-Contract.md | 生成源，提供字段契约和状态机定义 |
| L0/L1 Rules | 生成目标，ldvh-gen-rules 的输出 |
| Trae Skills | 生成目标，ldvh-gen-skills 的输出 |
| PyTools | 生成 Skill 的调用对象，Skill 中引用 PyTools 命令 |
| Fact Validator | 生成验证工具，生成后运行校验 |
| ldvh-commit | 可能触发重新生成（检测 specs 变更时） |

---

## 7. 开放问题

1. 生成 Skill 是否应该用 PyTools 实现而非 AI Skill？PyTools 确定性更高，但解析 Markdown 的能力有限
2. 是否需要"半自动"模式：AI 生成 + 人工审核 + 确认写入？
3. 生成的 Rules/Skill 是否应该提交到 git？还是作为运行时生成物不提交？
4. 多项目场景下，共享的 Skill（如 ldvh-commit）和项目特定的 Skill（如 ldvh-gen-rules）如何区分？
5. specs 结构化标记的粒度：YAML front matter 够用，还是需要更细粒度的标记（如 HTML 注释标记可提取区域）？
