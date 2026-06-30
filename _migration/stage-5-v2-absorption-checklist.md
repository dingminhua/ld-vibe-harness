# Stage 5 V2 内容吸收清单

> 文件状态：temporary migration checklist。本文只作为第 5 阶段开始前的吸收、映射和测试设计证据，不授权正式 specs、Code 行为、Hook 安装、commit gate、行动模板或环境支持声明。正式规则仍以 `specs/` 为准。

## 1. 当前判断

第 5 阶段不能直接进入 Hook / Commit / 行动模板适配代码。V2 已有 active specs、代码、Hook registry、Skill 资产和测试；V3 当前 runtime 仍是只读 facade，明确 `environment_integrated=false`、`authorization=none`。因此下一步是先吸收 V2 事实源，判断每项能力在 V3 的归口、保留方式、废弃内容、后置条件和测试入口。

吸收顺序：

1. 先做来源清单和语义映射；
2. 再决定哪些内容进入正式 specs 或附件；
3. 再补 Code 可消费结构和测试；
4. 最后才实现 hook adapter、commit gate 或行动模板适配。

## 2. 吸收清单

| V2 来源 | 当前状态 | V3 归口 | 保留能力 | 废弃/后置内容 | Skill 语义转换 | 必须先有的 specs | 必须补的 tests | 是否触发 Human Gate |
|---|---|---|---|---|---|---|---|---|
| `specs/03-行动编排规范.md` | active | 行动模板、Action Guide、runtime 消费边界 | Context、Scenario、Gate、执行中分流、能力输出交还主控 | V2 的 30-59 成员机制不能整体复制为 V3 目录权威 | Skill 只作为能力输出来源，转换为行动模板步骤或 Action Guide 提示 | V3 行动模板总规则、能力输出交还边界 | 行动模板读取计划、Gate 分流、能力输出不得成为事实源 | 改变行动模板准入或 Gate 时触发 |
| `specs/06-运行时扩展规范.md` | active | 环境入口、Hook 映射、runtime adapter 边界 | canonical event、payload 透传、read_plan 消费证据、环境接入声明边界 | V2 Rules/Skills/Agents/Hooks 类型体系不能作为 V3 顶层构成要素原样继承 | Skill 转为外部环境承载或行动模板包装，不恢复 `skills/` 顶层权威 | V3 环境入口与 runtime adapter 规则 | canonical event 映射、payload_present、read_plan evidence、环境未接入 fallback | 安装、覆盖用户入口、扩大权限或声明环境支持时触发 |
| `specs/07-事实源边界与Git追溯规范.md` | active | 事实源边界、Git commit records、commit message 契约 | commit type/scope/body/message 字段、Git 追溯、过程输出回写边界 | V2 Git 派生展示和 Web 关联视图后置 | Skill 中提交步骤只保留为行动模板提示，契约回到 specs/附件 | V3 事实源与 commit 契约规则 | commit message parser、body 条件、过程输出不得替代事实源 | 改变事实源、commit 契约或风险接受时触发 |
| `specs/30-rules-entry-sync-review-Rules入口同步审查.md` | active action member | Rules 入口影响评估、行动模板候选 | specs 变化后评估入口、最小读取、STOP、工具导航是否要同步 | 不恢复 V2 Rules 资产作为第二规则源 | 无 Skill 顶层语义；转为行动模板中的同步审查流程 | V3 Rules/入口表达边界、行动模板成员规则 | Rules 影响诊断、无需同步/建议同步/Human Gate 三类输出 | 修改入口边界、STOP、source refs 时触发 |
| `specs/31-git-commit-action-Git提交行动编排.md` | active action member | Git 提交行动模板、commit preflight | status/diff 读取、原子提交判断、验证证据、commit hash 交还 | 不把 `skills/ldvh-git-commit` 当作已调用事实 | Skill 工作流转为行动模板步骤；若环境真实调用再记录 runtime evidence | V3 commit 行动模板、commit message 契约、验证声明边界 | commit action plan、validator、runtime `git_commit_msg` read_plan evidence | 拆分提交、无关 staged、破坏性 Git 或高影响变更时触发 |
| `specs/32-environment-entry-adaptation-环境入口落地与适配检查.md` | draft candidate | 环境入口适配候选、后置行动模板 | 保障要求投影、薄引用、部署检查、禁止声明 | 候选状态不能默认执行；环境状态不能写成长期事实 | Skill 仅为可发现/可手动等价执行的环境承载项 | V3 环境适配字段、薄引用、部署检查规则 | candidate 不自动执行、环境检查证据、未接入不得声明完成 | 写入用户入口、安装 Hook、声明支持时触发 |
| `specs/attachments/06.Att.02-固定运行时扩展登记表.md` | active attachment | 外部承载物登记候选 | 固定资产自描述、source specs、验证方式 | 不能作为 V3 顶层资产清单权威长期手写维护 | Skill 登记转换为外部适配候选或历史证据 | V3 承载物自描述字段和登记边界 | 登记一致性、未登记资产不得声称固定能力 | 新增/删除固定承载物时触发 |
| `specs/attachments/06.Att.15-环境Hook事件映射表.md` | active attachment | canonical event 映射 | 环境原生事件到 LDVH canonical event 的映射 | 不复制环境私有 Hook 语义为核心协议 | 与 Skill 无直接顶层关系 | V3 runtime event mapping 附件或表格 | mapping 闭集、未知事件阻断、payload 透传 | 新环境映射或原生 Hook 覆盖时触发 |
| `specs/attachments/07.Att.02/07.Att.03/07.Att.04/07.Att.08` | active attachments | commit message 契约附件 | type、scope、body 条件、message 字段 | 样例和展示后置；不混入提交流程 | Skill 只能引用契约，不能改写契约 | V3 commit 契约正文和授权附件 | type/scope/body/message 字段正反例 | 改变闭集、body 条件或字段契约时触发 |
| `code/hook_dispatch.py` | active code | runtime dispatcher / adapter 后置实现来源 | canonical event 处理、read_plan evidence、receipt、diagnostics | 不能直接复制 V2 管辖项目逻辑到 V3，需先有 specs | Skill plan 输出转为行动模板提示或 adapter hint | V3 runtime adapter 输入输出 Schema | dispatcher 单元测试、unknown event、read_plan missing、receipt boundary | 接入真实环境或阻断写入前触发 |
| `code/hook_adapter.py` | active code | 环境 adapter 后置实现来源 | stdin payload 解析、target 恢复、trigger_source | 未确认环境映射前不迁入实现 | 无 Skill 顶层语义 | V3 环境 Hook payload Schema | payload_present、target recovery、fallback diagnostics | 新环境接入或 payload 语义改变时触发 |
| `code/commit_validate.py` | active code | commit validator 优先吸收 | message parse、type/scope/body 中文质量、diagnostics | 与 V2 专用枚举绑定的实现需等 V3 附件稳定 | Skill 调用 validator 的步骤转为行动模板调用 validator | V3 commit 契约附件 | validator 正反例、CLI、hook 调用 | 改变 commit 契约时触发 |
| `code/install_git_hooks.py` | active code | 安装器后置 | native Git hook 安装检查、备份、卸载 | 第 5 阶段早期不安装、不写用户环境 | 无 Skill 顶层语义 | V3 环境安装授权和回滚规则 | dry-run、backup、uninstall、no overwrite | 写入 `.git/hooks` 或覆盖用户 hook 时触发 |
| `hooks/ldvh-hooks.yaml` | active registry | Hook registry 候选 | canonical event、命令入口、severity、diagnostics policy | registry 存在不等于环境安装 | Skill 不通过 registry 成为规则源 | V3 hook registry Schema | registry parse、event closed set、command target | 改变阻断策略或环境入口时触发 |
| `skills/ldvh-git-commit/SKILL.md` | active asset | 行动模板材料、外部环境包装候选 | Git 提交流程步骤、验证提示、失败处理 | 不作为 V3 顶层机制，不作为规则权威 | 转为行动模板步骤；若保留文件，只是外部环境可读包装 | V3 行动模板和外部包装边界 | 手动等价执行提示、不得声称 runtime invoked | 声称 Skill runtime、安装 Skill 或改变提交 Gate 时触发 |
| V2 相关 tests | active tests | V3 回归测试来源 | hook dispatch、adapter、commit validate、install hooks、runtime projection | 测试名和 fixtures 可改写，不保留 V2 目录权威 | Skill 测试改为行动模板或包装边界测试 | 对应 V3 specs/Schema 稳定后 | 负例优先：缺 evidence、未知 event、契约失败、环境未接入 | 测试改变 Human Gate 语义时触发 |

## 3. 第 5 阶段准入条件

进入第 5 阶段代码实现前，必须同时满足：

1. 已确认 V3 不恢复 Skill 顶层机制；
2. 已确定 commit 契约、runtime event、Hook registry、行动模板和环境入口分别归口；
3. 已决定哪些 V2 specs/附件进入正式 `specs/`，哪些留在 `_migration`；
4. 已补充对应 Code 可消费字段或 Schema；
5. 已有失败用例覆盖授权语义、read_plan 消费证据、completion verification、未知事件、payload 缺失和环境未接入；
6. 计划输出仍保持 `authorization=none`，不得把 Code、Hook、Skill、Action Guide 或测试结果写成 Human Gate 替代。

## 4. 当前结论

当前可以继续做第 5 阶段的吸收清单、正式 specs 候选和测试设计；暂停 hook adapter、commit gate、行动模板适配代码实现，直到上面的准入条件满足。
