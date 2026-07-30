---
title: addyosmani/agent-skills 工程工作流与 LDVH 吸收建议调研
status: active
urls:
- ref: https://github.com/addyosmani/agent-skills
  title: addyosmani/agent-skills repository
  summary: 用于确认项目定位、当前目录结构、24 个技能、8 个命令、4 个 persona、许可证和维护状态；流行度等数字只作为 2026-07-29 的观察快照，不作为质量证明。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/README.md
  title: Agent Skills README at observed revision
  summary: 用于确认项目自述的全生命周期组织、技能目录、命令入口、核心设计选择和支持环境；这是项目自身陈述，不能单独证明实际行为效果。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/skills/using-agent-skills/SKILL.md
  title: using-agent-skills meta-skill at observed revision
  summary: 用于分析目录路由、跨技能顺序、全局行为约束和完整生命周期链；其规则是模型应遵循的软约束，不等同于宿主强制执行。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/docs/skill-anatomy.md
  title: Skill Anatomy at observed revision
  summary: 用于确认技能 frontmatter、推荐章节、渐进式披露、脚本约定、500 行预算和共享引用设计，并确认单技能安装会丢失仓库根共享引用的已知权衡。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/evals/README.md
  title: Skill Evals at observed revision
  summary: 用于分析结构、触发/路由和行为三层评测；其中 Tier 2 明确是 stemmed TF-IDF 词法近似，Tier 3 需要模型调用且默认按需运行。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/docs/codex-setup.md
  title: Codex setup at observed revision
  summary: 用于确认 Codex 可直接消费根 skills 目录，但 Claude 专属 slash commands、personas 和 hooks 不会等价进入 Codex，支持范围存在明确降级。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/docs/agents.md
  title: Agent Personas at observed revision
  summary: 用于确认 skill、persona、command 三层职责和有限 fan-out 编排模式；这些 persona 的自动发现和运行方式主要面向 Claude Code。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/docs/adoption-guide.md
  title: Adoption Guide at observed revision
  summary: 用于确认项目对 greenfield 与 brownfield 的不同采用策略；该内容是项目给出的建议，不是独立比较实验。
- ref: https://github.com/addyosmani/agent-skills/blob/7829ffd90d973b6325f5f12f1b1226dcace74443/docs/comparison.md
  title: Project-authored comparison at observed revision
  summary: 用于理解作者如何定位本项目与 Superpowers、Matt Pocock skills 的差异；因属于项目自评，本报告只把它当定位材料，不把比较结论当独立证据。
- ref: https://github.com/addyosmani/agent-skills/issues/361
  title: 'Issue #361: npx packs only skills/'
  summary: 用于确认按单技能或仅 skills 目录安装时，根 references 中共享资料可能缺失的真实可移植性问题；截至观察时仍为 open。
- ref: https://api.github.com/repos/addyosmani/agent-skills
  title: GitHub repository metadata API
  summary: 用于记录 2026-07-29 观察时的仓库创建、最近推送、许可证、默认分支和规模快照；动态统计会变化，不用于判断工程质量。
research_intent: 深入研究 addyosmani/agent-skills 的实际架构、技能行为契约、验证机制、跨宿主适配和局限，判断 LDVH 应吸收哪些设计原语、应拒绝哪些直接移植方式，以及后续是否值得建立有界试点。
research_question: addyosmani/agent-skills 如何把软件工程实践组织成可发现、可执行、可验证的 AI agent 工作流？其真实优势、证据边界、跨环境限制和治理风险是什么？LDVH 可以有选择地吸收哪些机制而不混淆规则源、事实源、Helper 确定性能力与模型软约束？
abstract: 在 2026-07-29 对 main 分支 revision 7829ffd 的检查中，agent-skills 是一个以 24 个 Markdown 技能为核心、覆盖 Define—Plan—Build—Verify—Review—Ship 的工程工作流包，并辅以 8 个命令、4 个评审 persona、共享参考资料、宿主适配器和三层评测。其关键价值是把工程纪律写成“触发—步骤—反合理化—红旗—证据门禁”的行为契约，并对目录结构与路由进行机械评测；本次实际运行结构、命令和 Tier-2 路由检查均通过，路由 rank-1 为 86%。但这不证明真实任务质量：Tier 2 只是词法近似，Tier 3 默认按需且依赖模型；不同宿主只共享部分能力；单技能安装可能丢失共享引用；技能文本本身不能强制权限、Human Gate 或完成判断。
recommendation_summary: LDVH 不应整体复制该项目或把其技能内容提升为规则。最值得吸收的是五个可分离机制：明确的触发/排除契约、步骤与停止条件、反逃避信号、证据化完成门禁、结构/路由/行为分层评测；同时应保留 LDVH 的来源与职责边界，让 Helper/Code 只做确定性检查、Human 保留授权与取舍。建议后续仅在 Human 同意时建立一个小规模 WorkCase，用 3 个代表性行动模板做 A/B 试点，并以规则冲突、误触发、任务正确性、上下文成本和验证证据为验收指标。
object_id: study-0016
fact_type_key: study
created_at: '2026-07-29T00:21:07.200083+08:00'
updated_at: '2026-07-29T00:21:07.200083+08:00'
---

## 研究问题

本报告围绕一个外部项目回答四组问题：

1. `addyosmani/agent-skills` 到底是什么：提示词集合、技能目录，还是一套工程工作流框架；
2. 它如何把资深工程实践转成 agent 可执行的行为约束，又如何验证这些约束没有在目录扩张中失控；
3. 它的可移植性、评测证据和治理能力分别成立到什么边界；
4. LDVH 可以吸收哪些机制，同时不把外部项目的意见、模型软约束或宿主特性误写成自己的规则、事实或确定性能力。

本报告与现有 `study-0011`、`study-0014` 的分工不同：前者讨论 Vibe Coding 从 demo 到产品级所需的广义工程闭环，后者讨论 agent 输出组织；本报告聚焦一个具体外部技能库的内部机制、实际校验结果和 LDVH 吸收边界。

## 输入与边界

### 实际输入

观察时点为 2026-07-29（Asia/Shanghai）。本次克隆并检查了 `main` 分支 revision `7829ffd90d973b6325f5f12f1b1226dcace74443`，该 revision 比 tag `0.6.5` 多 5 个提交；最新提交时间为 2026-07-26。检查范围包括：

- README、贡献规则、技能 anatomy、采用指南、比较文档、Codex 与其他宿主接入说明；
- 24 个 `skills/*/SKILL.md` 的目录、frontmatter、章节和行数，并深读 meta-skill、spec-driven、incremental implementation、TDD、source-driven、doubt-driven 等代表性技能；
- 8 个命令、4 个 persona、共享 references、hooks、宿主 manifest；
- 24 组 eval cases、fixtures 和评测说明；
- 与可移植性和触发准确率相关的 issue；
- GitHub API 在观察时点提供的仓库元数据。

本次还在干净临时克隆上实际运行：

```text
node scripts/validate-skills.js
→ 24 skills checked, 0 errors, 0 warnings

node scripts/validate-commands.js
→ 8 commands checked, 0 errors

node scripts/run-evals.js --min-rank1 80
→ 124 checks passed
→ trigger rank-1 rate: 86% (65/76)
```

这些结果证明观察 revision 的结构、命令同步和确定性词法路由检查按项目自身实现通过。它们不证明每个技能在真实代码库、不同模型、不同宿主和长期任务中都能提高质量。

### 未覆盖与限制

- 未运行需要模型费用的 Tier-3 behavioral eval，因此没有独立复验 24 个技能对真实 agent 行为的改善幅度；
- 未在 Claude Code、Cursor、Gemini、OpenCode、Copilot 和 Codex 中逐一安装做端到端兼容测试；
- 未做与 Superpowers 或其他技能库的重复多轮基准；项目自带 comparison 只作为作者定位材料；
- 未审计全部 shell hook 的每一条安全性质，也未验证社区 star、fork 或 issue 数量的真实性；流行度不是质量证据；
- 项目更新很快，文档、标签、宿主命令和统计可能在本报告之后变化；需要采用时应固定 revision 并重新运行校验。

## 关键发现

### 1. 它是一套“共享技能核心 + 原生适配器”的轻量工程框架

项目的共享核心是 24 份 Markdown 技能。它们按 Define、Plan、Build、Verify、Review、Ship 六个阶段组织，由 `using-agent-skills` 负责把自然语言任务映射到相应技能。围绕核心还有四层配套：

| 层 | 作用 | 当前实现 |
|---|---|---|
| Skill | 定义如何做，包含步骤与退出条件 | 24 个 `SKILL.md` |
| Command | 提供用户可见的生命周期入口并组合技能 | 8 个命令 |
| Persona | 提供单一专业视角和输出格式 | 4 个评审 persona |
| Adapter / Hook | 让不同宿主发现技能、命令或会话提示 | Claude、Codex、Gemini 等各自目录 |
| Eval | 检查目录结构、路由和实际行为 | 结构、词法路由、行为三层 |

因此，它比“提示词合集”更接近一个不自带统一运行时的流程框架：控制面主要由 Markdown 契约构成，执行面借用宿主 agent 的读写、命令、浏览器和子代理能力。直接影响是，文本可以广泛迁移，但自动发现、并行 persona、hook、权限和命令体验不会自动等价迁移。

对 LDVH 的直接影响：可借鉴“共享核心—宿主薄适配”的分层，但必须继续如实报告每个环境实际交付了哪些能力；不能因为同一 `SKILL.md` 可读，就宣称整个工作流已经在该环境生效。若未来没有真实的跨环境适配需求，无需创建对象；若出现多个 adapter 对同一能力交付不一致，应建立 WorkCase 检查能力矩阵。

### 2. 最有辨识度的设计是把工程常识写成行为契约

大多数技能采用相似骨架：

```text
触发条件 / 排除条件
        ↓
具体步骤与决策点
        ↓
常见合理化借口及反驳
        ↓
可观察 Red Flags
        ↓
带证据的 Verification
```

例如 TDD 不只说“要测试”，而是要求先发现仓库真实测试栈，再执行 RED—GREEN—REFACTOR；bug fix 必须先用失败测试复现；结束前运行完整测试集。Incremental implementation 把实现限制为小的垂直切片，并把“连续两次运行未变化的相同验证命令”列为红旗。Source-driven 要求识别依赖版本、读取官方文档、标出未验证范围。Doubt-driven 则把非平凡判断显式化为 CLAIM，并用新上下文进行反证式检查。

“Common Rationalizations”不是装饰性写作，而是针对 agent 常见的过程逃逸：先写代码后补测试、认为任务太简单不需要 spec、把重新运行命令当作额外证据、借机清理范围外代码。这一机制把抽象价值观转为可审查的失败信号，是该项目比普通 checklist 更强的地方。

对 LDVH 的直接影响：可以把“适用条件—不适用条件—步骤—停止条件—证据—典型逃逸信号”作为行动模板设计检查项，但这些内容必须由相应来源准入。外部技能中的价值判断不能直接成为 LDVH 规则；尤其“每个增量都 commit”“每次 doubt 都提供跨模型选择”等意见只能作为候选实践。若未来新建或修改行动模板，可在同一 WorkCase 中评估该骨架是否减少越权、漏验和假完成。

### 3. 全生命周期覆盖带来一致性，也带来组合复杂度

目录从模糊需求一直覆盖到发布、可观测性和弃用，能为团队建立共同语言。Meta-skill 还给出了一个最多 16 步的完整顺序，并允许一个任务串联多个技能。这对大型功能很有价值，但也会产生三个成本：

1. 多个宽触发技能可能同时适用，路由和顺序需要模型判断；
2. 每个技能自己的强规则叠加后，可能形成过度仪式化；
3. 不同技能重复要求 scope discipline、tests、build、commit、review，若没有主从关系会出现重复行动或冲突。

项目通过“canonical source + cross-skill reference”缓解重复，并在 adoption guide 中区分 greenfield 与 brownfield；但最终仍依赖 agent 正确判断“当前需要哪些技能”，而不是由运行时证明。小修复若机械走完整链，会比问题本身更昂贵。

对 LDVH 的直接影响：不应建立一个默认恢复全部行动模板的总路由器。应继续按 Human 目标和当前信息渐进式选择；组合多个模板时要明确主模板、辅助模板、共享验证和停止条件，避免把目录关系误表达为语义适用结论。若没有出现实际组合冲突，无需建立专门对象；一旦试点中出现重复门禁或冲突，应把它作为 WorkCase 验收失败，而不是继续扩充路由规则。

### 4. 三层 eval 是项目最值得复用的工程机制

评测分层如下：

| 层 | 检查内容 | 优点 | 证据边界 |
|---|---|---|---|
| Tier 1 | frontmatter、命名、必需章节、命令同步 | 免费、稳定、适合 CI | 只证明结构成立 |
| Tier 2 | 正向触发、负向排除、技能描述碰撞 | 免费、目录级、能发现描述词汇缺口 | stemmed TF-IDF 词法近似，不理解语义 |
| Tier 3 | agent 执行轨迹是否满足 expectations | 能观察工具调用和行为结果 | 依赖模型、权限、fixture、grader 和 token；默认按需 |

本次 Tier 1、命令同步和 Tier 2 均通过。86% rank-1 表明 76 个正向 prompt 中有 65 个把目标技能排第一；这高于项目 80% 的 CI floor，但也意味着 11 个样例的首选路由仍不是目标技能。项目自己明确承认 Tier 2 不是语义判断，这种诚实边界很重要。

Tier 3 的设计也有成熟之处：execution case 在临时 Git 仓库中运行，dialogue case 单独建模；执行轨迹按不可信数据处理；fixture、expectations、超时和 JSON grader 输出都有约束。不过每个技能最低只需一个 behavioral eval，且它不是默认 CI 的免费门禁，仍不足以推出“生产级”这一宽泛结论。

对 LDVH 的直接影响：非常适合吸收“结构契约测试—候选/路由测试—行为结果测试”的分层，但必须分别声明可证明范围。LDVH 的 Helper 可以机械证明结构与确定性投影；AI/Human 才能判断自然语言相关性、规则适用和研究质量。若后续建立 WorkCase，验收应包含至少一个压力样例和一组负向路由样例，而不只验证 happy path。

### 5. 渐进式披露做得好，但包级共享与单技能可移植性存在张力

项目把技能名和 description 留在启动上下文，只有命中后才加载完整 `SKILL.md`；技能建议不超过 500 行，长资料下沉到 supporting files，脚本优先于大段内联代码。24 个技能实际都低于 500 行。这个做法能控制首次上下文成本。

但多个技能共用的测试、安全、性能、可访问性和 Definition of Done 被放在仓库根 `references/`。整包安装时这是单一来源；只复制某个 `skills/<name>/` 时，跨目录引用会失效。项目在 skill anatomy 中主动记录了这一权衡，issue #361 也展示了真实安装问题。

对 LDVH 的直接影响：应继续坚持稳定来源引用和渐进式展开，但任何“可单独分发”的单元都必须显式声明依赖闭包、已交付范围和缺口。不能同时声称共享资料只有一个权威副本，又声称任意单技能目录天然自包含。若未来做外部模板包安装，WorkCase 的验收应覆盖整包和单包两种安装形态。

### 6. 跨宿主兼容是“语法共享”，不是“能力等价”

Codex manifest 直接指向同一个根 `skills/`，避免复制；这是很好的单一来源设计。但 Codex setup 明确说明 Claude 的 slash commands 和 personas 没有原生等价物，Codex hook 还被置为空以避免加载 Claude-oriented hook。因此在 Codex 中实际获得的是 24 个技能文本及自动/显式选择能力，而不是 README 所展示的完整 `/spec → /plan → /build → /ship` 产品体验。其他宿主也分别依赖自己的路径、命令或规则文件。

这揭示了一个普遍规律：Markdown 契约的可读性可以跨平台，触发语义、工具权限、Human Gate、subagent isolation、hook 生命周期和输出 UI 都是宿主能力。项目已部分如实说明这些差异，但“支持多个平台”不等于每个平台获得同一运行语义。

对 LDVH 的直接影响：这与“环境 Hook 是薄引用、核心演进不得被旧 Hook 冒充”的边界一致。若吸收任何外部技能，应建立 capability matrix：可发现、可读取、可执行、可验证、可并行、可阻止越权分别是什么状态。没有被宿主实际交付的能力必须写成未交付，不得用旧行为或自然语言近似替代。

### 7. 技能是强意见的软约束，不能替代授权和确定性治理

许多技能包含有价值但并非普遍成立的意见：多文件变化应逐片 commit；框架相关决策都应查官方文档；非平凡判断要做 fresh-context doubt；互动式 doubt 每轮都要提供跨模型复核；小变更约 100 行；spec 阶段需要 Human 审阅。这些规则在合适团队中能提高纪律，但存在三类风险：

- 宿主或用户没有授权 commit、外部 CLI、浏览器访问或写入时，技能不能自行扩大权限；
- 既有仓库可能采用不同的分支、测试、review 和 release 规则；
- 同一强意见在简单任务上可能制造高于风险本身的成本。

项目本身也通过 when-not-to-use、brownfield adoption 和边界说明降低过度应用，但最终执行仍是 prompt compliance，不是强制状态机。它没有统一、不可绕过的运行时来证明 Human 已批准、验证真实发生或完成条件已经满足。

对 LDVH 的直接影响：外部技能只能作为行动方法候选，不能替代 Human 授权、来源规则、事实对象状态和 Helper 回读。若某技能建议与 LDVH 当前规则冲突，以当前适用规则与 Human 决定为准；冲突必须显式呈现，不能静默融合。只有在真实重复需求出现且完成规则准入后，某项候选方法才可能成为长期来源。

### 8. 安全意识明显，但技能供应链仍需宿主治理

值得肯定的安全细节包括：浏览器 DOM、console 和 network 输出被视为不可信数据；behavioral eval 的轨迹在 grader prompt 中被隔离；跨模型检查建议使用 read-only sandbox；shell 内容不直接插入命令参数。

但整个框架的核心仍是被注入 agent 上下文的 Markdown 指令。安装主分支、自动更新或引用第三方技能会引入指令供应链风险；技能可以要求运行命令、创建提交或访问外部工具，而宿主是否拦截取决于自己的权限系统。MIT 许可证允许复用，不代表内容经过安全认证。

对 LDVH 的直接影响：外部技能应固定 revision、审查差异、声明来源、隔离权限并在升级时重新验证。除非出现正式的外部技能安装需求，当前无需创建新对象；若进入试点，必须把“技能文本是不可信外部输入，不能覆盖 Human 目标和当前规则”写入验收边界。

### 9. 适用场景与不适用场景

更适合：

- 希望给团队建立共同的 spec、plan、build、test、review、ship 词汇；
- 新项目或重要功能，需要较完整的工程闭环；
- 已有 agent 宿主能力，愿意为质量门禁支付额外上下文和交互成本；
- 需要一个可 fork、可评测、可逐步定制的技能基线。

不宜直接整包启用：

- 单行修复、纯文档或一次性探索；
- 已有强约束开发流程且与本项目意见不同的成熟仓库；
- 需要可审计权限、确定性事务和正式事实状态，但宿主只能依赖 prompt compliance；
- 只安装单个技能却没有携带共享 references；
- 把“支持某平台”理解为命令、persona、hook 和并行行为完全等价。

对 LDVH 的直接影响：如果未来试用，应从少量高价值、低冲突模板开始，不应以 star 数或“production-grade”自称作为采用依据。

## 建议

### 建议一：吸收行为契约骨架，不复制 24 份内容

- 目标对象类型：只有在下一次真实新增或重构行动模板时，更新对应 WorkCase；不直接修改规范。
- 预期目标：验证行动模板是否能稳定表达适用/排除、步骤、Human Gate、Stop Conditions、可验证证据和典型逃逸信号。
- 验收条件：模板没有复制外部结论为规则；AI、Helper、Code、Hook、adapter 和 Human 的职责仍分离；至少一个负向场景能阻止误用；产物能回指当前来源。
- 创建/更新判断：若没有真实模板变更需求，当前无需对象化；当同类模板连续出现误触发、漏验或假完成时，再建立 WorkCase。

### 建议二：建立三层评测的有界试点

- 目标对象类型：Human 同意后创建一个 WorkCase。
- 预期目标：选择 3 个代表性行动模板或工作流，建立结构检查、候选/路由检查、行为结果检查。建议覆盖“来源核对”“实现验证”“评审/交付”三类，而不是整包 24 类。
- 验收条件：包含正向与负向触发、至少一个时间/权限压力样例、实际结果证据、false trigger 统计、规则冲突记录、token/工具调用成本；各层分别写清可证明与不可证明范围。
- 创建/更新判断：只有 Human 希望把本研究转成实验时才创建；若只是保存研究结论，保持 Study 即可。

### 建议三：把跨环境能力矩阵作为适配验收，而不是宣传文案

- 目标对象类型：未来出现新的 LDVH 环境 adapter 或外部技能安装能力时，纳入该实现 WorkCase；必要的长期职责取舍再形成 ADR。
- 预期目标：逐项记录发现、读取、命令、hook、persona/subagent、权限、写入、验证和错误报告能力。
- 验收条件：每项能力都有当前环境的实际证据；未交付和不兼容范围可见；共享来源不被复制成多个漂移版本；单元分发时依赖闭包完整。
- 创建/更新判断：没有新 adapter 或安装能力时无需对象化；若需要决定“共享 references 与自包含包如何取舍”，再建立 ADR。

### 建议四：外部技能必须固定版本并作为不可信输入处理

- 目标对象类型：进入外部技能消费实现时更新相应 WorkCase；若形成长期供应链政策，再单独走规则或 ADR 准入。
- 预期目标：固定 Git revision，审查升级 diff，限制工具权限，禁止技能扩大 Human 授权，并在升级后重跑验证。
- 验收条件：可追溯到精确来源；技能文本不能覆盖当前规则和 Human 目标；外部命令、commit、浏览器、网络和跨模型调用仍由环境授权控制；失败与缺口不会被静默降级。
- 创建/更新判断：当前仅有研究、尚未安装，故不创建下游对象；真正安装或自动更新前必须建立受控工作。

### 建议五：用对照实验判断价值，不用目录规模或热度代替证据

- 目标对象类型：若 Human 要求评估采用价值，创建 WorkCase。
- 预期目标：在同一模型、同一 revision、同一任务集上比较 baseline 与精选技能。
- 验收条件：预注册任务正确性、漏验率、越权率、误触发、Human 中断次数、token/时间和修复轮数；至少多次重复；报告失败样例而非只报平均值；不把 Tier-2 rank 当作任务质量。
- 创建/更新判断：只有实际采用决策需要证据时开展；否则当前研究已经足够支持“不整体照搬、只选择性试点”的判断。

## 后续分流

| 分流类别 | 触发信号 | 下一步 | 继续无需对象化的条件 |
|---|---|---|---|
| WorkCase：精选机制 A/B 试点 | Human 明确希望验证 agent-skills 机制对 LDVH 工作质量的影响 | 选 3 个工作流建立结构、路由、行为三层测试，并记录成本与冲突 | 目前只需保留研究，尚无采用或实验目标 |
| WorkCase：外部技能受控安装 | LDVH 需要实际安装、更新或执行第三方技能 | 固定 revision、审查内容、建立权限边界与回滚，并验证依赖闭包 | 未发生外部技能运行需求 |
| WorkCase：跨环境 capability matrix | 新增或修改 Claude、Codex、Gemini 等 adapter，且宣称同一能力跨环境成立 | 逐项验证发现、读取、hook、命令、persona、权限与结果交付 | 没有新的 adapter 交付或兼容性声明 |
| ADR：共享引用与自包含分发取舍 | 真实安装场景反复出现根共享资料丢失，且需要长期统一方案 | 比较整包单一来源、每技能自包含和构建期打包三种方案 | 尚无 LDVH 外部模板包分发需求 |
| 规则/行动模板候选 | 多个真实 WorkCase 重复证明某种行为契约骨架能减少误触发、漏验和假完成 | 按相应来源完成准入，不从本 Study 直接升级 | 只有单次外部启发或尚无项目内证据 |
| 无需对象化 | 只是希望理解该项目或手工参考个别方法 | 保留本 Study，采用时重新核对上游 revision 和宿主能力 | 没有授权、没有实施目标、没有重复痛点 |
