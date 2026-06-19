# Git 提交规范

```yaml
ldvh_doc:
  doc_id: "10"
  doc_kind: "formal_spec"
  title: "Git 提交规范"
  status: "active"
  canonical_path: "specs/10-Git提交规范.md"
  created: "2026-06-19"
  updated: "2026-06-20"
  parent_doc: ""
  relation: ""
  positioning: "定义 LDVH 自身项目及所有管辖项目的 Git 提交格式、提交语言、Code/Web 可解析字段和派生追溯边界"
  scope: "LDVH 自身项目及所有接入 LDVH 且需要通过 Git commit records 追踪文件事实源修改的管辖项目"
  basis:
    - "specs/00-LD-Vibe-Harness理念与纲要.md"
    - "specs/09-事实源边界与承载规范.md"
  related_specs:
    - "specs/01-目录说明.md"
    - "specs/07-Code确定性执行实现规范.md"
    - "specs/08-Web信息同步实现规范.md"
    - "specs/11-测试基础规范.md"
  code_consumption:
    - "doc_metadata"
    - "relations"
    - "structure"
    - "landing_requirements"
```

---
## 1. 本文解决的问题

本文解决整个 LDVH 管辖项目的 Git commit message 应如何格式化书写、AI 和 Human 如何利用 Git 历史理解变更、Code 如何校验提交格式、Web 如何解析和展示提交记录派生视图，以及工作对象是否需要手写关联提交字段的问题。

Git 提交记录不是 LDVH 工作对象，不进入 20-39 工作模型集合，不创建 `ldvh-base/changes/`，也不具备 YAML 状态机。它是事实源修改的 Git 层追溯证据，服务 `specs/09-事实源边界与承载规范.md` 定义的 Git 可追踪原则。

---
## 2. 与 09 和工作模型的关系

09 定义最终事实源必须是 Git 可追踪文件。本文承接 09，专门定义修改这些文件时 Git commit message 应如何写，确保 Git commit records 可读取、可审查、可校验、可被 Code/Web 解析和派生展示。

Git 提交记录与工作模型的边界如下：

| 内容 | 权威位置 |
|---|---|
| 工作对象状态、字段、验收和关闭判断 | 对应 `ldvh-base/` YAML 或 Study Markdown 实例 |
| 工作对象字段契约和状态机 | 20-39 具体工作模型规范 |
| 事实源修改的提交证据 | Git commit records |
| Git 提交格式与派生追溯规则 | 本文 |
| 提交记录的列表、筛选、关联和详情展示 | Code/Web 派生视图，不替代 Git |

工作对象不得手写维护 `related_changes` 这类提交清单字段。需要查看某个对象相关提交时，应由 Code 或 Web 根据 Git 历史、文件路径、对象 ID、提交正文自然文本和必要索引实时派生。派生结果可以展示为“关联提交”或“提交记录”，但不得回写为新的对象事实字段。

---
## 3. 适用范围

以下修改应通过符合本文契约的 Git commit 留痕：

1. 修改 specs 正式规范、规则入口、能力资产、Code、Web、测试或配置；
2. 修改 `ldvh-base/` 下的工作对象事实源；
3. 修改 Study Markdown、docs 正文、docs/studies、docs/sources 或经授权沉淀的项目文档；
4. 修改会影响 Human Gate、状态流转、事实源边界、校验逻辑、Web 呈现或 AI 入口的文件；
5. 完成 WorkPlan、ADR、Memo、Study、Pitfall、WorkArea 等对象的创建、关键字段改写、状态变化、归档或删除；
6. 回退、修正或补充之前已提交的事实源修改。

未进入 Git 的临时实验、构建产物、缓存或本地草稿不形成正式提交记录；一旦提交，就应尽量符合本文格式。

---
## 4. commit message 格式

LDVH 使用 Conventional Commits 1.0.0（约定式提交规范）作为 Git commit message 标准，外部标准链接为 <https://www.conventionalcommits.org/en/v1.0.0/>。提交信息必须在可解析的首行、必要正文和可选 footer 中说清楚本次做了什么。LDVH 不发明与行业规范冲突的提交格式，也不把 `Human-Gate:`、`Verification:`、`Risk:` 这类私有 trailer 定义为标准必填字段。

标准格式如下：

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

| 字段 | 要求 | 说明 |
|---|---|---|
| `type` | 必填 | 提交类型，使用本文 §5 的英文枚举；type 是严格闭集，不得使用枚举外值 |
| `scope` | 可选 | 影响范围，优先使用本文 §6 推荐值；无合适值时可使用项目内稳定、名词性的扩展值 |
| `!` | 可选 | 破坏性变更标记，对应 Conventional Commits 的 breaking change |
| `description` | 必填 | 简体中文简短说明，推荐不超过 72 字符 |
| `body` | 条件必填 | 使用简体中文说明做了什么、为什么做、影响范围、关键取舍和必要上下文；是否必填按 §4.2 判断 |
| `footer` | 可选 | 遵守 Conventional Commits 和 git trailer 风格；可以使用 `BREAKING CHANGE:`、`Refs:`、`Co-authored-by:` 等行业兼容 footer，但不得替代 body 的语义清单 |

所有提交都遵守同一套格式。正文长短由变更复杂度决定，LDVH 不额外定义提交类别。复杂变更、规范变更、迁移、回退或跨多个事实源的修改，必须在正文用结构化语义清单说明变更内容和影响，不拆成 LDVH 私有固定 trailer 字段。

### 4.1 首行单主语义

首行只表达本次提交的主意图和主承载域，不表达 touched files 的全量分类。

`type` 只能有一个，表示本次提交的主变更意图或动作类别。一个提交如果同时包含多个彼此独立的意图，例如“新增 Web 展示能力”和“顺手重构无关 Code 模块”，应拆成多个提交。若一个原子闭环需要同时修改 specs、Code、Web 或 docs，应选择最能代表闭环目的的主 `type`，其他影响写入 body。

`scope` 最多一个，表示名词性的主承载域或最重要的事实源边界。scope 不是文件清单，不要求覆盖所有改动路径。一次提交可以跨多个目录完成同一闭环，但首行只选择主 scope；其他受影响范围、配套实现和文档同步写入 body。

首行不得使用多个 type、多个 scope、斜杠拼接、逗号拼接或“全都写上”的方式规避取舍。例如 `feat+docs(web/specs): ...`、`feat,fix(web): ...`、`feat(web,code): ...` 都不符合 LDVH 的单主语义。

### 4.2 提交正文硬性要求

commit body 是 Git 提交记录的人类语义清单层。Git 已经提供 hash、作者、时间、touched files、diff 和 stat；body 必须承载 Git 无法自动知道、但 Human 审查、Code 预检、Web 阅读和 AI 后续执行需要知道的语义信息。

以下提交必须包含非空 body：

1. 修改 specs、rules、Code、Web、测试、配置、AI 入口或能力资产；
2. 修改 `ldvh-base/` 工作对象事实源的状态、关键字段、归档、废弃、关闭或删除；
3. 一次提交涉及两个及以上文件，或同时影响两个及以上 scope；
4. 修改会影响 Human Gate、事实源边界、状态流转、字段契约、Web 呈现、校验逻辑、复制上下文或 AI 执行入口；
5. 有用户确认、设计取舍、残留风险、兼容性影响、验证证据或后续约束需要保留；
6. description 无法让不了解上下文的人判断本次提交的目的、边界和影响。

只有以下提交可以省略 body：

1. 单文件、低风险、语义完全由 description 表达清楚的 typo、格式、注释或微小文案修正；
2. 纯机械版本号、锁文件、生成物或等价维护变更，且不改变事实源语义、Web 行为或校验结果；
3. 回退提交的工具自动生成正文已经足够说明被回退提交，且没有额外人工取舍。

必须写 body 的提交，其正文应优先使用 Markdown 小标题或列表形成稳定清单，至少覆盖以下四项语义；可以使用自然段补充说明，但不得改用 footer 替代 body。推荐小标题为“动机”“关键变更”“影响边界”“验证结论”“风险与后续”：

1. 变更动机：为什么需要这次修改，解决了什么问题或收敛了什么偏差；
2. 关键变更：本次实际改变了哪些行为、契约、展示或事实源语义，不重复逐文件清单；
3. 影响边界：影响哪些对象、规范、Code/Web 能力、用户体验、AI 执行或后续维护；
4. 验证结论与风险：说明本次变更已经确认到什么程度、仍有什么未验证或残留风险；检查命令可以作为辅助证据出现，但不得替代验证结论。

以下 body 不合格：

1. 只写“更新”“优化”“完善”“调整样式”“按要求修改”等无法判断语义的空泛表述；
2. 只重复文件名、diff stat、命令输出或 changed files；
3. 只堆 `npm run web:check`、`python3 code/specs_validate.py ...`、`git diff --check` 等命令，而不说明验证结论、动机、关键变更和影响边界；
4. 把 Git 提交伪装成工作对象记录，用 `Human-Gate:`、`Verification:`、`Risk:` 等 LDVH 私有 trailer 替代 body 语义清单；
5. 为了满足格式而堆砌模板句，实际没有提供 Human 可审查的信息。

Footer 是行业规范的一部分，只用于承载 Conventional Commits 或 git trailer 风格的尾部信息。`BREAKING CHANGE:`、`Refs:`、`Co-authored-by:` 等 footer 可以存在；LDVH 不要求 AI 为追溯、Human Gate、验证或风险固定补写 trailer。若这些信息对理解本次提交有语义价值，应优先写入 body 清单，footer 只作为兼容行业工具和平台的附加信息。

Web 应把 body 作为“提交说明”优先展示给 Human；Code 应在提交前预检中尽可能根据 staged touched files 和 message 内容判断 body 是否缺失或明显空泛。无法机械判断语义质量时，应至少给出 warning，并由 Human 审查兜底。

### 4.3 AI 写提交时的执行顺序

AI 生成 commit message 时必须按以下顺序决策，避免把 LDVH 要求误解为文件分类、命令清单或私有 trailer：

1. 判断是否应拆提交：若 staged changes 包含多个互相独立的目的，应先拆提交；若是一个原子闭环，可以跨 specs、Code、Web、docs 或测试文件保留在同一提交；
2. 选择单一 `type`：只表达本次提交的主变更意图或动作类别，不用多个 type 描述所有改动文件；
3. 选择零个或一个 `scope`：只表达名词性的主承载域，优先使用推荐枚举，不用 scope 覆盖全部 touched files；
4. 写 description：用一句简体中文说明本次提交的核心结果，不写“更新”“优化”“完善”这类空泛词；
5. 判断 body 是否必填：命中 §4.2 必填条件时必须写 body；不确定时宁可写 body；
6. 写 body 语义清单：优先使用 `动机:`、`关键变更:`、`影响边界:`、`验证结论:`、`风险与后续:` 小标题和 Markdown 列表；
7. 删除重复信息：body 中不得把 Git 已经提供的文件列表、diff stat、hash、作者、时间作为主要内容；
8. 改写检查命令：若需要说明验证，不堆命令清单，应写验证结论，例如“已确认 Web 类型检查和 specs 结构检查通过，未发现提交详情 DTO 漂移”；
9. 处理 footer：只有需要兼容 Conventional Commits 或平台工具时才写 footer，例如 `BREAKING CHANGE:`、`Refs:`、`Co-authored-by:`；不得用 `Human-Gate:`、`Verification:`、`Risk:` 替代 body 清单。

AI 不应为了满足格式而制造虚假验证、虚假风险或虚假引用。未实际验证时，应在 `验证结论` 或 `风险与后续` 中明确写“未验证”及原因。

---
## 5. type 枚举

| type | 简体中文 | English | 含义 |
|---|---|---|---|
| `feat` | 新增功能 | Feature | 新增功能、能力或用户可见对象 |
| `fix` | 问题修复 | Fix | 修复缺陷、错误或不符合预期的行为 |
| `docs` | 文档修改 | Documentation | 修改文档、规范、规则入口或其他文档性事实源 |
| `style` | 格式调整 | Style / formatting | 代码格式、空白、排版等不影响语义的修改 |
| `refactor` | 代码重构 | Refactor | 重构，不改变外部行为 |
| `perf` | 性能优化 | Performance | 性能优化 |
| `test` | 测试修改 | Tests | 测试相关修改 |
| `build` | 构建系统 | Build | 构建系统、依赖或打包相关修改 |
| `ci` | 持续集成 | Continuous integration | CI 配置或流水线修改 |
| `chore` | 维护杂项 | Chore / maintenance | 辅助维护、杂项或难以归入其他类型的非功能变更 |
| `revert` | 回退变更 | Revert | 回退之前的提交 |

type 是严格闭集，不得使用枚举外内容。不得使用 `improve`、`update`、`完善`、`优化` 这类含义不稳定的 type。所谓“完善”必须按实际变更目的落入明确类型：新增能力用 `feat`，修复问题用 `fix`，规范、规则或 ADR 文本修改用 `docs`，代码结构整理用 `refactor`，维护性调整用 `chore`。

---
## 6. scope 推荐值

| scope | 简体中文 | English | 含义 |
|---|---|---|---|
| `specs` | Specs | Specs | specs 规范文档 |
| `docs` | 文档 | Docs | docs 正文或项目文档 |
| `rules` | 规则 | Rules | Rules / Instructions |
| `code` | Code | Code | Code / 工具实现 |
| `web` | Web | Web | Web 实现 |
| `tests` | Tests | Tests | 测试代码 |
| `config` | 配置 | Config | 项目配置 |
| `workarea` | 工作域 | WorkArea | WorkArea 实例 |
| `workplan` | 计划 | WorkPlan | WorkPlan 实例 |
| `adr` | 决策 | ADR | ADR 实例 |
| `memo` | 备忘 | Memo | Memo 实例 |
| `study` | 研究 | Study | Study 实例 |
| `pitfall` | 经验 | Pitfall | Pitfall 实例 |
| `studies` | 研究材料 | Studies | docs/studies 相关修改 |
| `sources` | 来源材料 | Sources | docs/sources 相关修改 |

scope 为推荐值，应优先使用上表枚举。没有合适枚举时，AI 可以基于项目语义选择一个简短、稳定、名词性的 scope；扩展 scope 不得创造新的工作对象类别，不得使用斜杠、逗号或多个词拼接规避主承载域取舍。LDVH 自身反复出现的新 scope，应回补到本文推荐值和 Web 展示标签。

---
## 7. 关联提交派生

工作对象、规范、Code 和 Web 需要“关联提交”时，应按以下优先级派生：

1. commit touched files 与对象事实源路径、规范路径、Code/Web 文件路径的匹配；
2. commit description 或 body 中自然出现的对象 ID、规范编号、规范路径或文件路径；
3. Git 提交时间线、相邻提交、分支上下文和人工审查结论；
4. 必要时由用户或 AI 在当前分析中临时筛选，但不得回写为手填提交字段。

对象 ID、规范编号或路径可以出现在 description 或 body 中，但不得要求 AI 为了追溯而补写固定 `Refs:` 字段。Git 变更由 Git 自身的 hash、文件路径、diff 和时间线追踪。

---
## 8. 提交语言要求

LDVH 自身项目的提交说明必须使用简体中文表达主要人类可读内容。`description` 和 `body` 应使用简体中文；`type`、`scope`、路径、命令、对象 ID、英文专名和代码标识可以保留英文或原文。

Code 可机械检查 commit message 是否包含中文字符、是否符合首行格式、type 是否属于枚举、description 是否为空；简体中文与繁体中文的细分判断若无法可靠机械化，应由 Human 审查兜底。

---
## 9. Human Gate 与风险

Git 提交记录本身不额外触发 Human Gate。Human Gate 由被修改的事实源、对象、规范、Code、Web、工作流程或破坏性 Git 操作触发。

以下场景应在提交正文或对应事实源中用自然语言说明确认情况，但不使用 `Human-Gate:` trailer：

1. 修改事实源边界、对象状态机、字段契约、规范编号、目录归属或 AI 入口；
2. 删除、迁移或重命名工作对象事实源；
3. 执行破坏性 Git 操作，例如改写已共享历史、强推、删除分支或批量回退；
4. 修改受控写入、校验、Human Gate、Web 编辑或安全相关能力；
5. 用户明确确认某个高影响方向、迁移策略或验收结论。

需要说明残留风险、未验证内容或兼容性影响时，应写入提交正文或对应工作对象事实源，不使用 `Risk:` trailer。不得用“应该没问题”替代风险说明。

---
## 10. Code 消费规则

Code 可以实现以下能力：

1. 校验 commit message 首行格式、type 枚举、description 长度和中文要求；
2. 结合 staged touched files 或指定文件清单，按 §4.2 判断 body 是否必填；
3. 对必须写 body 但缺失 body 的提交给出 error；
4. 对 body 明显空泛、只重复文件清单、只写检查命令或缺少关键语义维度的提交给出 warning；
5. 检查 footer 是否明显不符合 Conventional Commits / git trailer 形式，并对 `Human-Gate:`、`Verification:`、`Risk:` 等 LDVH 私有 trailer 替代 body 的倾向给出 warning；
6. 基于 Git 历史、touched files、description/body 自然文本派生对象关联提交；
7. 为 Web 提供提交列表、提交详情、文件统计、完整 body 和必要的派生关联；
8. 对格式不稳定的提交给出 warning；
9. 检查对象事实源中是否仍出现需要清理的手写提交字段。

Code 输出只是派生诊断、导航或展示数据，不替代 Git commit records。commit message 格式规则变化后，应同步更新 `code/commit_validate.py`、相关测试和 Web API 解析契约。

---
## 11. Web 呈现规则

Web 可以展示 Git 提交记录列表、最近提交、提交详情、文件统计和对象相关提交。

Web 呈现必须遵守：

1. 页面和导航表达为“提交记录”“最近提交”或“Git 提交记录”，不得把它表达为独立工作对象；
2. `/changelog` 可作为路由名保留，但页面文案应表达为提交记录派生视图；
3. Dashboard、ProjectFiles 和 Changelog 应尽量共享同一 commit DTO 或解析契约；
4. 对象详情中的关联提交应由 Git 派生，不从对象 YAML 手写字段读取为权威事实；
5. Web 不把 `Human-Gate:`、`Verification:`、`Risk:` 展示为 LDVH 固定字段或标签；`Refs:`、`BREAKING CHANGE:`、`Co-authored-by:` 等行业兼容 footer 如存在，应作为 Git message 原文或后续 footer 派生信息展示；
6. Web 可按当前语言本地化展示 `type` 和推荐 `scope` 标签；中文展示应使用 §5 和 §6 中的简体中文列，英文展示应保留 type 原始 token，并使用 §6 中的 English scope 展示名；
7. 提交详情必须优先展示 body 派生的“提交说明”；有 body 时默认展开，没有 body 时不显示该节点；
8. 改动文件、文件统计和原始信息来自 Git 派生数据；改动文件和原始信息默认收起，不替代提交说明；
9. 复制给 AI 定位或用于审计的提交上下文应保留原始 `type`、`scope`、hash token 和 body，不得只复制本地化标签；
10. Web 缓存、页面状态、筛选状态和派生索引不得替代 Git commit records。

---
## 12. 示例

```text
docs(specs): 采用约定式提交规范

动机:
- 解决提交记录无法被 Code 和 Web 稳定解析的问题。

关键变更:
- 将 Git 提交首行统一为 Conventional Commits 格式。
- 固定 type、scope、breaking marker 和 description 的解析边界。
- 明确工作对象不得手写维护 related_changes。

影响边界:
- 影响 Git 提交预检、Web 提交记录页和后续对象关联提交派生。

验证结论:
- 已确认 specs 结构和章节引用没有因本次规则调整漂移。
- 后续需要同步 Code 校验和 Web DTO。
```

```text
fix(web): 修复提交记录分类解析

动机:
- 避免 breaking marker 提交被识别为 other。

关键变更:
- 支持 type(scope)!: description 格式。
- 让 Web API 解析 category、scope、description 和 isBreaking。
- Dashboard 和 Changelog 共用这些字段。

影响边界:
- 影响范围限于提交记录派生展示，不改变 Git commit records 本身。

验证结论:
- 已确认 Web 类型与 breaking marker 提交样例均能覆盖解析结果。
```

```text
feat(web)!: 调整提交记录接口字段

动机:
- 让前端统一消费提交记录结构化字段。

关键变更:
- 返回 category、scope、description 和 isBreaking 字段。
- 调整 Web API DTO。

影响边界:
- 影响 Dashboard 最近提交、Changelog 列表和提交详情。
- 旧的仅首行字符串消费方需要改为读取结构化 description。

验证结论:
- 已确认前端类型定义已同步。

BREAKING CHANGE: 旧的仅首行字符串消费方需要改为读取结构化 description。
```

---
## 13. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 事实源修改应通过 Git 提交记录留下可追溯证据，不再把提交记录建模为工作对象 | 09、本文、06、Human Gate | 事实源治理 | 修改 Git 文件事实源、工作对象状态、规范、Code、Web 或入口资产时 |
| 入口可见要求 | AI 准备提交、审计提交历史或追溯对象相关提交时应能定位本文 | Rules 入口摘要、commit_validate 帮助、Web 提交记录页 | AI 执行入口提示 | 提交、回退、审计、关闭 WorkPlan 或查询关联提交时 |
| 确定性执行要求 | commit message 可机械校验的部分由 Code 检查，关联提交由 Git 派生 | `code/commit_validate.py`、Git 查询、测试夹具 | 校验实现 | 提交契约或关联派生规则变化时 |
| 确定性执行要求 | LDVH 自身仓库应提供或启用提交前 message 校验入口；未启用 Git hook 时，AI 提交前必须手动运行等价预检 | `commit-msg` hook、`code/commit_validate.py --check-message`、CI 或人工降级检查 | 触发保障 | 创建 Git commit、修改提交契约、调整 hook/CI 或迁移仓库入口时 |
| 确定性执行要求 | 必须写 body 的提交应由 Code 基于 staged touched files 和 message 内容做提交前预检，缺失 body 视为 error，明显空泛正文视为 warning | `code/commit_validate.py --check-message`、staged diff、测试夹具 | 校验实现 | 修改 specs、rules、Code、Web、测试、配置、AI 入口、能力资产或跨文件事实源时 |
| 入口可见要求 | Web 提交详情应把 commit body 作为“提交说明”默认展开，把改动文件和原始信息作为默认收起的派生证据节点 | Web API commit DTO、`/changelog` 详情、Web 类型检查 | 展示实现 | Web 展示提交详情、复制提交上下文或提交 DTO 变化时 |
| Human 交互要求 | 高影响事实源修改和破坏性 Git 操作必须记录或触发 Human Gate | Human Gate、提交正文或对应事实源 | 人工确认 | 修改事实源边界、状态机、字段契约、入口资产或执行破坏性 Git 操作时 |
| 生命周期触发要求 | 本规范变化后，应同步检查 01、05、05.01、05.02、05.03、06、07、08、Code、Web 和测试 | specs 检查、Code 测试、Web 类型检查、残留搜索 | 触发保障 | 提交格式、关联派生或 Web 展示规则变化时 |

---
## 14. Human Gate 与检查要求

以下情况应评估 Human Gate：

1. 改变 Git 提交记录的事实源定位；
2. 改变 commit message 必填字段、提交语言、提交门禁或破坏性 Git 操作边界；
3. 把提交记录重新建模为工作对象或创建 `ldvh-base/changes/`；
4. 把 Web 缓存、数据库索引或对象 YAML 字段提升为提交记录事实源；
5. 删除 Code 校验或降低高影响事实源修改的追溯要求。

检查至少包括：

| 检查项 | 标准 |
|---|---|
| 事实源边界 | 提交记录由 Git commit records 承载，不创建工作对象实例 |
| 格式契约 | commit message 首行、type、scope、breaking marker 和 description 可被解析 |
| 语言要求 | LDVH 自身提交主要人类可读内容使用简体中文 |
| 提交门禁 | LDVH 自身仓库存在 `commit-msg` hook、CI 或等价预检入口；未启用时提交执行者必须在提交前运行 `code/commit_validate.py --check-message` |
| 派生关联 | 对象关联提交由 Git 历史、文件路径、对象 ID 和正文自然文本派生，不手写维护 |
| Code 边界 | Code 只校验、解析和聚合，不替代 Git |
| Web 边界 | Web 只展示派生视图，不替代 Git |

---
## 15. 待补齐事项

1. 应补齐 LDVH 自身仓库的 `commit-msg` hook 或 CI 提交信息检查，并明确哪些 warning 升级为 error；
2. 若未来支持多仓库管辖项目，应补齐跨仓库提交记录查询和 Web 聚合边界；
3. 若未来需要自动派生对象关联提交，应优先基于 touched files、对象 ID、规范编号和正文自然文本实现，不恢复手写字段或专用 trailer。
