# LDVH v3 独立审计报告

> 审计时间：2026-07-02
> 审计性质：只读独立审计。未修改任何项目文件、未提交、未自动修复。
> 审计范围：`ld-vibe-harness-v3` worktree（v2 仓库的 git worktree）。

## 0. 审计方法与执行命令

以 `specs/00-理念与构成.md` 为最高价值锚点，逐项检查 v3 设计是否服务：AI 第一服务对象、事实源为判断依据、保障与衔接层为落地通道、五类构成要素、V1-V9 价值标准。

实际执行的命令与结果：

| 命令 | 结果 |
|---|---|
| `python3 code/test_runner.py smoke` | PASS（specs validator ok，formal hash tests 9 passed，1.2s） |
| `python3 -m pytest tests/code -q --durations=20` | **126 passed in 132.88s**（113 + 9 + 4） |
| `python3 code/environment_status.py --format text` | status ok，environment_integrated=partial，仅 git.commit-msg 自动 |
| `python3 code/environment_entry_audit.py --format text` | status ok，runtime 入口 deferred，Rules/Skill removed_top_level |
| `python3 -m pytest _migration/tests -q` | 19 passed |

> 注：`pytest tests/code` 首次以 Exit 137 (SIGKILL) 失败，原因是与其它重负载操作并行时 OOM。单独重跑后 126 passed。这是运行环境问题，非测试本身缺陷，但反映出全量测试对内存敏感（见 P1-1）。

---

## 1. 总体判断

**结论：v3 已完成升级，可作为主线使用，无阻断项（P0=0）。**

| 判断维度 | 结论 | 依据 |
|---|---|---|
| v3 是否可作为主线 | **是** | `environment_status.py` 输出 `switch_mode=commit_msg_hard_switch_minimal`、`environment_integrated=partial`；README 明确日常规则、事实对象、Web、commit 均以 v3 为准 |
| 是否已完成升级 | **是** | 阶段 0-11 全部完成；17 篇 active specs、16 个 active 附件、77 个事实实例、126 测试通过；formal review hash gate 已迁入 `reviews/formal/`（11G） |
| 是否只是进行中的升级 | **否** | 11B 已把所有正式 specs/附件从 candidate 激活为 active；不再是"00 active 其余 candidate"的 soft mainline |
| 是否存在阻断 | **否 P0** | 未发现 Human Gate 被绕过、未发现 manual-ready 被误写成 integrated、未发现 Web 依赖 Code 输出、未发现脱离 00 价值锚点的结构性偏离 |

**边界声明（v3 自身诚实记录的未完成项，非阻断）：**
- 仅 `git.commit-msg` 是真实自动入口；session_start / pre_tool_use / completion_claim / runtime_adapter 均为 manual-ready（`environment_entry_audit.py` 确认）
- 通用 Web 写入、完整 Confirm UI、非提交行动模板实例、稳定 receipt 存储均后置（有明确进入条件，见 11D/11F）
- 这些后置项不阻断主线判断，因为它们不影响规则判断、事实维护和提交校验的日常可用性

---

## 2. 对 v2 的增强点（每条附文件依据）

### 2.1 结构性增强：六类构成要素收口为五类构成要素
- **v2**：`specs/00-LDVH理念与价值标准.md` 定义"六类构成要素"，其中第六类是"运行时扩展"
- **v3**：`specs/00-理念与构成.md` §5 收口为"五类构成要素"，运行时扩展职责移入"保障与衔接层"（`specs/01-保障与衔接.md` §6 外部衔接）
- **判断**：这是真实结构整合，不是换术语。运行时扩展在 v2 中与五类要素并列导致归口模糊；v3 把它降为保障与衔接层的实现方式，使"规则/事实/行动/Code/Web"与"环境如何接入"的边界更清晰。`_migration/11A-human-gate-constitutional-remediation.md` 诚实记录了这一构成变更的 Human Gate 补救（不伪造早期确认）。

### 2.2 保障与衔接层成为显式三层模型
- **依据**：`specs/01-保障与衔接.md` §5 内部保障、§6 外部衔接、§7 行动指南
- **v2**：运行时扩展规则散落在 `06-运行时扩展规范.md`（39KB）等多处
- **v3**：01 统一定义保障链路（规则要求→保障需求→能力→承接机制→receipt/evidence→验证→回写/分流），消费时机闭集由 `01.Att.01` 承载，承接矩阵由 `01.Att.06` 承载
- **判断**：AI 负担真实降低——AI 不再需要从多文件拼凑"这条规则如何被保障"，01 提供统一链路和字段表

### 2.3 Web 与 Code 同源独立读取边界（新增硬约束）
- **依据**：`specs/08-Web信息同步规范.md` §6；`specs/07-Code确定性执行规范.md` §3 末段
- **v2**：未发现等价的"Web 不得依赖 Code 输出作为主数据源"硬约束
- **v3**：08 §6 明确"Web 页面/API 的数据路径必须由 Web 自行从 Git 文件事实源…读取；不得把 Code 输出、Code DTO、validator 内部对象…作为页面数据源"。Code 07 §3 对应反向边界
- **测试验证**：`test_web_sync_validator_rejects_code_output_as_page_data_source` 等负例测试存在并通过

### 2.4 环境入口状态闭集与审计 Code
- **依据**：`specs/11-环境适配规范.md` §5-§6；`code/environment_status.py`；`code/environment_entry_audit.py`
- **v2**：`32-environment-entry-adaptation`（32KB）散写环境适配，无统一状态闭集
- **v3**：11 定义 `available/manual_ready/integrated/deferred/removed_top_level/absent` 闭集；environment_status.py 和 environment_entry_audit.py 自动区分并审计
- **关键测试**：`test_environment_entry_audit_does_not_treat_agent_file_as_integration` 防止把 AGENTS.md 误判为已接入；`test_environment_status_blocks_missing_commit_hook` 防止缺 Hook 时误报 partial

### 2.5 Rules / Skill 顶层机制取消（有正式依据）
- **依据**：`specs/11-环境适配规范.md` §8；`_migration/11A`；`_migration/11D`；`environment_entry_audit.py` 输出 `rules.top_level_mechanism=removed_top_level`
- **判断**：这不是"丢失能力"。v2 Rules 的入口可见能力转为环境薄引用/repo instruction 候选；v2 Skill 的可复用工作流能力转为行动模板步骤/Action Guide/外部包装候选（`_migration/v2-runtime-capability-migration-notes.md` 有完整映射）。Rules/Skill 不作为后置入口，而是明确 removed_top_level，避免反复讨论恢复。

### 2.6 specs 正文明确为"规则源，不是事实源"
- **依据**：`specs/00-理念与构成.md` §3 末段；`specs/03-事实源与Git溯源规范.md` §5
- **判断**：v2 5B-0A 审计发现规则/事实混写问题，v3 已修正。00 和 03 均加入"`specs/` 正文是规则源，不是事实源"边界句，防止规范文件被误当作事实对象承载。

### 2.7 formal review hash gate 稳定化
- **依据**：`reviews/formal/README.md`；`_migration/11G`；`tests/code/test_formal_specs.py`
- **v2/早期 v3**：formal gate 读取 `_migration/reviews/*`
- **v3 当前**：gate 读取 `reviews/formal/*-formal-review.yaml`，`mapping_evidence.path` 可回指 `_migration` 但 gate 本身不依赖它。test_formal_specs.py 验证 target_sha256 等于当前文件内容 hash。
- **判断**：v3 主线不再依赖 `_migration` 执行 formal hash gate，降低了迁移层耦合。

### 2.8 行动模板去 Skill 化 + Git 提交为唯一正式示范
- **依据**：`specs/06-行动模板基础规范.md` §7；`_migration/11F`
- **判断**：Git 提交行动模板具备完整 Context/Scenario/Gate/执行/验证/回写/交还 结构并有 Code/tests 消费。非提交模板（WorkCase 创建/关闭等）合理后置，11F 记录了进入条件，避免"纸面模板与真实执行入口脱节"。

---

## 3. 对 v2 的能力缺口分类

依据 `_migration/11E-v2-v3-capability-coverage-matrix.md` 并独立核验：

| V2 能力 | 状态 | 核验依据 |
|---|---|---|
| 构成要素体系 | **已迁入** | `00` 五类构成 active |
| AI 行为保障 | **已迁入**（自动触发后置） | `02` + 8 项保障需求表；session/pre-tool/completion 按 11D 后置 |
| Commit message 契约 | **已迁入** | `03.Att.01` + `hooks/commit-msg`（已验证 executable + `core.hooksPath=hooks`） |
| 事实对象模型 | **已迁入** | `05`+`20-24` + `ldvh-base/` 77 实例 + validator 测试 |
| Web 展示和 facts API | **已迁入** | `08` + `web/` + 独立读取边界 + Spark quick create 轻写入 |
| 受管项目接入 | **已迁入** | `10` + `LDVH-GOVERNED-PROJECTS.yaml` + resolver + 测试 |
| 环境入口分类与状态 | **已迁入** | `11` + environment_status + environment_entry_audit |
| Rules 顶层机制 | **合理废弃** | removed_top_level，入口可见能力转为薄引用候选 |
| Skill 顶层机制 | **合理废弃** | removed_top_level，工作流能力转为行动模板步骤候选 |
| 知识地图 | **合理废弃** | legacy_alias，由 Action Guide 承接 |
| WorkCase 创建/关闭行动模板 | **明确后置** | 11F 记录进入条件（Confirm UI / 通用 Web 写入 / 自动 Hook / Human Gate 路径） |
| Hook 安装部署检查 | **部分迁入** | `11.Att.04` + install_git_hooks，当前只覆盖 commit-msg |
| V2 06 环境附件族 | **转归口** | 按 11 能力表迁入，未逐字搬运 |
| `_migration/reviews` hash gate | **已迁出** | 迁入 `reviews/formal/`（11G） |

**结论**：未发现"丢失且未说明"的 v2 能力。所有缺口要么已迁入、要么有明确后置条件和归口。

---

## 4. 是否脱离 `00` 价值锚点

### 4.1 符合点

| 00 要求 | 符合证据 |
|---|---|
| AI 第一服务对象 | 所有 specs 的 §1 价值判断均回指 00 §2；02 定义主控责任；01 行动指南明确"AI 每次行动前最终拿到什么" |
| 事实源为判断依据 | 03 §5 事实源边界 + 非事实源排除表；validator 测试 `test_fact_source_validator_reports_chat_as_fact_source_gap` 等 |
| 保障与衔接层为落地通道 | 01 三层模型 + 11 环境适配实现；environment_status/audit Code 落地状态闭集 |
| 五类构成要素 | 00 §5 + 04-08 + 05/20-24 分别承接规范/事实/行动/Code/Web |
| V1-V9 | 00 §6 定义；01 §5.3 保障需求字段回指 V 项；各 spec 保障措施表回指 |
| Human Gate | 00 §8 + 各 spec Human Gate 章节；11A 诚实补救构成变更；测试验证无授权泄漏 |

### 4.2 疑似偏离点（经核验不构成偏离）

| 疑似点 | 核验结论 |
|---|---|
| 六类→五类构成要素变更是否削弱 00 | **不偏离**。运行时扩展未消失，而是降为保障与衔接层实现方式（01 §6），更符合 00 §4"保障与衔接层不是新增构成要素"。11A 记录 Human Gate 补救。 |
| Rules/Skill 取消是否丢失入口可见 | **不偏离**。00 §4 保障与衔接层本就涵盖环境衔接；11 §8 明确 legacy 边界，能力转为薄引用/行动模板候选，非删除能力。 |
| 行动模板只有 Git 提交正式化是否不足 | **不偏离**。06 §7 + 11F 说明非提交模板后置是因为入口/验证/写入闭环不足时不应早产模板，符合 00 V4 稳定执行和 V6 强制验证。 |

**结论**：未发现脱离或违背 00 价值锚点的设计。

---

## 5. 风险分级

### P0（必须解决，否则不能称为升级）
**无。**

### P1（影响实际落地能力）

**P1-1：全量测试内存敏感，并行运行时 OOM**
- 现象：`pytest tests/code` 与其它重负载并行时 Exit 137 (SIGKILL)；单独运行 126 passed 但耗时 132.88s，最慢单测 17.10s
- 依据：`/tmp/ldvh_v3_testout.txt`；`test_ldvh_specs_validate.py` 82KB / 113 测试函数
- 影响：CI 或常规开发中若并行跑测试可能假失败，降低验证可信度
- 建议：评估测试内存优化或分片；e2e_rehearsal 相关测试（4 个 >12s）可考虑隔离

**P1-2：非提交行动模板全部后置，WorkCase 完整生命周期无法正式执行**
- 现象：WorkCase 创建/方案审核/结果复核/关闭确认均为后置候选（11F）
- 依据：`specs/06-行动模板基础规范.md` §7；`_migration/11F`
- 影响：虽有事实对象状态机（05/21），但缺少正式行动模板意味着 AI 推进 WorkCase 状态时无稳定步骤、验证入口和交还方式
- 判断：这是合理的后置（入口/Confirm UI/写入闭环不足时不早产模板），但确实限制了 v3 作为"完整工作流主线"的能力。进入条件已明确记录。

### P2（待补齐但不阻断主线）

**P2-1：session_start / pre_tool_use / completion_claim 仅 manual-ready**
- 依据：`environment_status.py` 输出 `manual_entrypoints` + `integrated=false`
- 影响：AI 必须自觉手动运行这些入口，环境不会自动拦截。这与 00 V5 门禁确认、V6 强制验证存在张力——保障链路存在但非自动触发
- 判断：已诚实记录为 deferred（11D），进入条件明确（真实触发点+稳定 payload+失败处理+安装状态+回滚+测试+Human Gate）。不阻断主线因为规则判断和事实维护不依赖自动触发。

**P2-2：receipt 仅 stdout-only，无稳定存储**
- 依据：`specs/11-环境适配规范.md` §7；`specs/01-保障与衔接.md` §5.6
- 影响：长期溯源能力受限——receipt 证明动作发生过但不持久化
- 判断：11 §7 明确"若后续需要稳定 receipt 存储，必须先补事实源回写规则"，已记录为待补齐

**P2-3：Confirm UI 不完整**
- 依据：`specs/08-Web信息同步规范.md` §7；`_migration/9D`
- 影响：Human Gate 的 Web 呈现质量受限，Human 只能凭部分信息验收
- 判断：08 §7 定义了 Confirm UI 应呈现的 7 项最小要求作为规则，但实现后置

### P3（文档清晰度或后续优化）

**P3-1：`_migration/reviews/` 仍保留旧 formal review yaml**
- 依据：`ls _migration/reviews/` 显示 24 个旧 yaml 文件仍存在
- 判断：`reviews/formal/README.md` 已说明 gate 不再依赖 `_migration/reviews/`，但旧文件未删除可能误导读者。11G 记录了删除条件（迁移测试/mapping evidence/历史 source_ref 有稳定替代或 Human Gate 同意归档）。

**P3-2：v3 是 v2 的 git worktree，非独立仓库**
- 依据：`.git` 文件内容 `gitdir: .../ld-vibe-harness/.git/worktrees/ld-vibe-harness-v3`
- 判断：这不影响 v3 功能，但意味着 v3 的 git 历史与 v2 共享。如果后续要让 v3 完全独立，需要处理 worktree 关系。当前 README 和 specs 未提及这一拓扑关系。

---

## 6. 最终结论

### 一句话判断

**v3 已完成升级并可作为主线使用：价值锚点稳固、v2 能力无丢失、Human Gate 未被绕过、环境边界诚实声明；主要待补齐的是非提交行动模板、自动环境触发和稳定 receipt 存储，这些均有明确进入条件且不阻断当前主线。**

### 下一步最值得做的 3 项工作

1. **优先补齐 WorkCase 行动模板最小闭环**（对应 P1-2）：当前事实对象状态机已存在（05/21），但 AI 无法正式推进状态。建议先补 WorkCase 创建→执行→关闭的最小行动模板，绑定 manual 入口（已有 session_start/pre_tool_use/completion_claim 三件套），在 Confirm UI 不完整时用 Human Gate 显式确认替代。这是释放 v3 工作流价值的最关键缺口。

2. **解决全量测试内存/性能问题**（对应 P1-1）：132s 运行时间 + 并行 OOM 会侵蚀"验证可信度"。建议把 e2e_rehearsal 相关 4 个慢测试（各 >12s）隔离为独立 tier，或优化 `build_e2e_rehearsal` 的重复加载。smoke 已足够日常使用，但 full 应可靠可重复。

3. **评估 session_start 自动触发的真实环境路径**（对应 P2-1）：当前三件套均 manual-ready，AI 必须自觉运行。如果目标协作环境（如 CodeBuddy/Claude Code/Codex）提供 session lifecycle hook，应评估接入可行性——这是把保障链路从"AI 自觉"升级为"环境拦截"的最小可行步骤，直接服务 00 V5 门禁确认和 V6 强制验证。进入条件已在 11D 列明（7 项），缺的主要是真实触发点。

---

## 附录：审计证据索引

| 证据 | 路径/命令 |
|---|---|
| 价值锚点 | `specs/00-理念与构成.md` |
| 保障与衔接 | `specs/01-保障与衔接.md` |
| 事实源边界 | `specs/03-事实源与Git溯源规范.md` §5 |
| Web/Code 分离 | `specs/08-Web信息同步规范.md` §6 |
| 环境适配 | `specs/11-环境适配规范.md` |
| 构成变更补救 | `_migration/11A-human-gate-constitutional-remediation.md` |
| 能力覆盖矩阵 | `_migration/11E-v2-v3-capability-coverage-matrix.md` |
| 行动模板后置 | `_migration/11F-action-template-minimal-closure.md` |
| formal gate 迁移 | `_migration/11G-migration-dependency-independence.md` |
| 环境状态 | `python3 code/environment_status.py --format text` |
| 环境审计 | `python3 code/environment_entry_audit.py --format text` |
| 测试结果 | `python3 -m pytest tests/code -q` → 126 passed |
| commit-msg hook | `hooks/commit-msg` (executable) + `git config core.hooksPath` = `hooks` |
| formal review gate | `reviews/formal/*-formal-review.yaml` + `tests/code/test_formal_specs.py` |
