# V4 Git 提交契约 Validator Code 实现规划

> 当前规划版本：2；形成时间：2026-07-15（Asia/Shanghai）；最近调整：2026-07-16（Asia/Shanghai）；实现起点 commit：`13bf510dfed89fd6aa9b0183c7d688123a841601`。本文是 07 定义的 Code 实现规划，不是规则源；具体项目的 Hook 安装、替换或移除仍须由 Human 当次授权。

## 1. 实现目标与来源

本增量依据 `source-of-truth-traceability` §§9.1–9.6，实现受管辖项目提交契约中可机械判断的纯校验能力；依据 `git-commit-action-template` 只约束未来行动如何在创建前消费校验结果，不实现行动本身。

本增量只实现：

1. 从当前有效 03 的结构化 type、scope、body 与 message 规则派生不可变 Code 投影和来源内容指纹；
2. 校验完整 message、完整规范化候选路径、唯一实际 worktree、`governed_single` 管辖结果、候选快照身份和 03 来源身份的输入完整性；
3. 机械检查换行/注释清理、header、type/scope、CJK 字符存在、description 句末、路径数量、`revert`/`!` 触发的 body 结构、固定小标题和列表；
4. 明确返回 passed、failed、unverifiable 的机械结果、诊断和未由 Code 判断的 AI 语义范围；
5. 用 V3 正反例与 V4 新增风险场景形成范围匹配 tests。

本增量不判断主要目的、简体中文语义、description 真实性、高影响语义、breaking 必要性、body 充分性、验证或风险真实性；不读取或修改 Git Index，不创建 commit，不实现 Helper 公开操作、Hook、安装器、Web DTO 或历史改写。

## 2. 来源结构前置

实现前先在 03 §9 内把机械闭集保持为单一结构化来源：type 使用现有语义表；scope 从自然语言枚举改为 token/语义表；body 条件增加稳定 trigger key、机械可判定标记和要求结构。该调整只结构化 03 已有含义，不新增附件，不让 Code 从散文猜规则。

Web 的当前合法 token 投影必须从同一 Code 投影生成或由来源指纹同步测试约束；历史或未知 token 仅进入显示 fallback，不得混入当前合法闭集。

## 3. 模块责任

新增 `ldvh.commits.contract_source`，只从已经通过当前规范检查的 `source-of-truth-traceability` 解析 §9 结构化表格，形成 `CommitContractProjection`、来源路径、观察内容和 SHA-256 指纹；它不解释自然语言条件，不读取 Git。

新增 `ldvh.commits.validation`，接收投影和显式 `CommitValidationInput`，规范化 message，检查输入完整性和机械契约，返回不可变 `CommitValidationResult`。该模块没有文件、进程、网络或 Git 写副作用。

未来 Git/Hook adapter 负责从实际 Index、worktree 和管辖解析取得输入，再调用中央 validator；adapter 读取失败必须保留为 `unverifiable`，不得折叠为空路径。Web 只消费投影或受同步测试约束的生成结果，不依赖 validator 反向定义标签。

## 4. 依赖与调用方向

允许方向为：消费方/tests → `ldvh.commits.validation` → `CommitContractProjection`；来源装配/tests → `ldvh.commits.contract_source` → 现有 specs repository/Markdown 数据。`ldvh.specs.repository`、governance resolver 和现有 Helper 操作不得反向依赖 commits 模块。

禁止 validator 自行运行 Git、扫描 cwd、读取 V3、读取 draft/retired 来源、维护手写第二枚举、猜测项目目录含义或安装 Hook。Git adapter、Web adapter 和 CLI 若后续成立，只能位于核心纯校验器外层。

## 5. 内部接口与结果边界

`CommitValidationInput` 至少包含：完整 message、相对 worktree 的候选路径序列、实际 worktree 身份、`governed_single` 管辖身份、非空候选快照身份、03 来源路径/观察时间/内容指纹。路径已由调用方从实际候选取得；核心仍拒绝空、重复、绝对、`.`、`..` 和越界表示。

`CommitValidationResult` 包含 outcome、机械 issues、规范化 header/body/footer、实际使用的来源身份，以及固定的 `semantic_checks_required`，后者明确列出仍需 AI 审核的范围。结果不包含 authorized、commit_created、hook_integrated、tests_passed 或 completed 等越权字段。

纯校验器可以接受明确的 rename/copy 新旧路径表示在外层展开后的路径集合；不解析 Git diff 状态。输入 Schema 是 Code 内部表示，不是 Helper 或环境公开契约。

## 6. 诊断与失败分层

来源结构缺失、重复、冲突或指纹不匹配时，来源投影不可用。message/path/worktree/governance/snapshot/source 任一必需输入缺失、路径读取失败由外层报告、或输入间身份不一致时返回 `unverifiable`。语法、闭集、必需 body 或列表结构不合规则返回 `failed`。只有全部机械条件满足时返回 `passed`，仍保留 AI 语义审核清单。

诊断必须定位输入字段和适用的 03 §9 规则，不回显不必要的完整文件内容，不把未知 scope 自动纠正成最相近 token，也不把 Web 历史 token加入合法集合。

## 7. 风险与测试映射

| 风险 | 测试检查范围 |
|---|---|
| Code 与 03 枚举漂移 | 从真实 03 解析投影；type/scope/body 表变更导致来源指纹和同步测试变化，不维护第二常量表 |
| Git 读取失败被当成空候选 warning | 显式缺失、空路径、外层读取失败均断言 `unverifiable`，不能返回 passed |
| message cleanup 改变真实语义 | CRLF/CR、开头空行、完整 `#` 注释、正文 `#`、尾随内容和空 message 正反例 |
| header 误判 | 所有 type、合法/省略/未知 scope、`!`、空格、英文 description、句末句号、`revert` body 条件 |
| 多路径 body 漏检 | 单路径、两路径、rename/copy 两端、delete、submodule、重复/绝对/越界路径 |
| body 结构被宽松接受 | 缺 `关键变更:`、空标题、无列表、`!` 缺 `影响边界:`、合法 footer 不替代 body |
| Code 越权声称语义合规 | passed 结果仍列出主要目的、中文语义、高影响、breaking、真实性、风险等 AI 检查 |
| 校验后输入漂移 | message、snapshot、governance 或 03 指纹任一改变时旧结果不能与新输入复用 |
| Web 合法与历史 token 混淆 | 当前闭集与历史/未知 fallback 分开；补 `runtime`，旧 `spec/rule/adr/studies/sources` 不进入当前闭集 |
| 引入 Git/文件副作用 | 核心 tests 不需要 Git repo；静态/行为测试确认 validator 不调用 subprocess 或写文件 |

## 8. 验证组合与已知缺口

实现增量至少运行 commits 新 tests、现有 specs 结构/身份/发现/行动模板相关 tests、Ruff check 和 format check。当前完整 specs/tests 仍受五类型准入记录旧路径夹具影响；必须如实区分该既有 setup error 与本增量断言，不用跳过或补造文件冒充全量通过。

Hook、真实 `commit-msg` lifecycle、用户既有 `core.hooksPath` 共存、安装/升级/回滚、Helper 公开操作、Git 写入封装和真实 Web 页面同步不在本增量完成声明内。核心 validator 和 tests 完成后，才重新判断最薄调用入口；不存在正式环境来源时停在纯库能力。

## 9. 与当前规划入口的关系

`active/V4-工作推进总纲.md` 决定当前顺序和完成边界；本文细化其中 Git 提交 validator 增量。实现、tests 和规划发生偏移时先更新本规划或修正实现。`V4-行动模板声明解析-Code实现规划.md` 继续只覆盖模板声明发现，不覆盖本增量。

## 10. 实现与验证结果

本增量已经完成：

1. 03 §9.3 的 scope 与 §9.4 的 body trigger 已结构化为唯一表格来源；
2. `ldvh.commits.contract_source` 只在 active 03 的 §9 H2 范围内派生 type、scope、机械 trigger 和整份 03 SHA-256 内容指纹；同表头出现在 §9 外不会进入投影；
3. `ldvh.commits.validation` 以不可变显式输入执行纯机械校验，区分 `passed`、`failed` 与 `unverifiable`，不读取文件、Git 或进程；
4. commits 风险 tests 共 23 项通过；与结构、身份、发现和行动模板组合共 101 项通过；新增/修改 commits Code 的 Ruff check 与 format check 通过；
5. Web 当前 type/scope 已与 03 表格同步，`runtime` 已补齐，历史或未知 token 保持原样 fallback；Web API/契约 tests 8 项及 TypeScript check 通过；
6. 当前全量 Code tests 为 359 passed、46 failed、102 errors；失败与错误数量保持既有五类型准入记录路径漂移基线，本增量新增 23 项均通过；
7. 全量 Ruff check 通过；全量 format check 仍指出既有未修改文件 `code/ldvh/specs/action_templates.py` 需要格式化，本增量文件全部通过；
8. `git diff --check` 通过。

因此纯 Validator、来源投影、风险 tests 和 Web token 同步范围已经实现。该首个增量完成时尚未实现 Git Index/worktree 输入 adapter；后续 Adapter 增量及结果见 §§11–12。Helper 公开操作、真实 commit 创建封装、Hook lifecycle、安装/共存/回滚，以及使用该流程改写任何既有 commit 仍不在该完成声明内。

## 11. 只读 Git 输入 Adapter 增量

下一增量新增 `ldvh.commits.git_adapter`，只负责把一个已经取得当前 `GovernanceScopeResult` 的目标 locator 绑定到唯一实际 Git worktree，并用隔离环境运行只读 Git 命令，形成 `CommitValidationInput`。它不读取或生成 message 内容，只接收调用方提供的完整 message；不负责 AI 语义审核。

允许的 Git 观察只包括：解析实际 worktree 身份、读取 Index 条目、读取相对 `HEAD` 的 staged name-status，以及读取当前 `HEAD` tree 身份；初始无 `HEAD` 使用明确 sentinel。环境复用 governance 的 Git 隔离边界并增加 `GIT_OPTIONAL_LOCKS=0`，阻断 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE` 和配置注入。不得调用 `git add`、`write-tree`、`commit`、`update-index` 或其它写命令。

snapshot identity 使用当前 `HEAD` tree 身份与完整 `git ls-files --stage -z` 原始字节的 SHA-256；候选路径从 `git diff --cached --name-status -z --find-renames --find-copies` 取得，rename/copy 展开新旧两端。Adapter 在路径读取前后各读取一次 snapshot；两次不同即返回 drift，不形成可验证输入。调用方在真正写入前必须重新调用 Adapter，并确认 snapshot、message、管辖结果和 03 指纹与已审核结果一致。

Adapter 返回 `observed`、`unverifiable` 或 `drifted`，保留阶段化诊断；空候选仍形成显式输入并由纯 Validator 返回 unverifiable。Git 缺失、超时、非 UTF-8 路径、异常输出、目标与 governance worktree 不一致都不得折叠为非管辖或空候选。

风险 tests 使用真实临时 Git 仓库，覆盖已有 HEAD、初始无 HEAD、新增/删除/rename、linked worktree、空 Index、环境重定向、Git 失败和两次读取间 Index 漂移。测试还必须证明观察前后 status 与 Index 原始字节不变；本增量不建立 Helper 公开接口或 Hook。

## 12. 只读 Adapter 实现与验证结果

本增量已经完成：

1. 新增 `ldvh.commits.git_adapter`，只接受已经形成的单一 `governed_single` 管辖结果，并再次解析实际 locator 的 Git worktree 身份；两者不一致时返回 `unverifiable`，不读取其它仓库的候选；
2. Git 子进程复用隔离环境并显式设置 `GIT_OPTIONAL_LOCKS=0`，只调用 `rev-parse`、`ls-files` 和 `diff --cached`；实现中没有暂存、提交、Index 更新、worktree 管理或文件写入入口；
3. 候选快照绑定 `HEAD` tree（无 `HEAD` 时使用明确 sentinel）与完整 Index stage 原始字节；路径读取前后快照不一致时返回 `drifted`，不形成 `CommitValidationInput`；
4. staged name-status 使用 NUL 分隔读取，rename/copy 展开新旧两端；Git 缺失、超时、输出异常、非 UTF-8 路径或管辖身份缺失均保留为阶段化 `unverifiable`，空候选交由纯 Validator 判为不可验证；
5. 真实临时仓库 tests 8 项覆盖普通新增、无 `HEAD`/空候选、删除与 rename、linked worktree 独立 Index、Git 环境重定向、管辖 worktree 不一致、观察期漂移和 Git 读取失败；commits 模块合计 31 项、与结构/身份/发现/行动模板的相关组合 109 项通过，相关文件 Ruff check 与 format check 通过；
6. 普通观察测试比较观察前后的 porcelain status 与完整 Index stage 字节，确认 Adapter 本身不改变候选。

增量后的全量 Code tests 为 368 passed、46 failed、102 errors；失败与错误仍由已登记的五类型准入记录旧路径漂移触发，数量相对 Adapter 实现前没有增加，新增 Adapter tests 全部通过。全量 Ruff check 通过。

本结果只建立内部只读输入边界，不代表 Helper 公开操作、行动模板执行器、AI 语义审核、Git 写入封装、Hook lifecycle、安装/共存/回滚或任何真实 commit 已经完成。下一步只能先以该 Adapter 对当前真实候选做只读预检，并把同一 snapshot、message、管辖结果和 03 指纹交给纯 Validator 与 AI 审核；任何 Git 写入仍须另行满足 30 的 Human Gate 与创建前重检。

## 13. 真实预检与最薄写入封装规划

2026-07-15 已对当前 V4 worktree 运行一次真实只读预检。管辖结果为 `governed_single`，Adapter 成功绑定真实 worktree 与 Index，snapshot 为 `sha256:7d750def86335cc99cfb079aa83097c2e59898c649fc27c162710166649237e1`；由于当前没有 staged paths，纯 Validator 返回 `unverifiable/candidate_paths_empty`。这证明当前 Adapter 只把实际 Index 视为候选，不会把 Working Tree 改动或拟议路径伪装成已形成的提交快照。

下一 Code 增量应把“候选形成”和“commit 创建”作为两个相邻但不同的写入阶段，不把 `git add` 偷藏进只读 Adapter：

1. AI 先依据 Human 已授权目标和实际 diff 给出 worktree 相对路径闭集；路径内存在目标与无关 hunks 混合而无法安全按整文件归属时停止，由 Human 取舍或回到普通求解；
2. Code 捕获实际 `HEAD`、用户真实 Index 原始身份和既有 staged paths；目标路径与既有 staged paths 重叠时停止，不覆盖或重新解释用户已有候选；
3. Code 创建自己拥有的临时 Index，以当前 `HEAD` tree 为基线、unborn 时以空树为基线，并只对显式 literal 路径执行候选装配；临时 Index 的位置、生命周期和清理责任必须可验证，外部 `GIT_INDEX_FILE` 仍不得注入；
4. 只读观察器显式读取该受控临时 Index，形成 candidate snapshot 和完整 paths；纯 Validator 校验机械契约，AI 另行审核主要目的、语义、拆分、验证覆盖和风险，Code 不把调用方布尔值伪装成 Human 授权事实；
5. 创建前再次核对 worktree、`HEAD`、真实 Index、临时 candidate、message、管辖结果、03 指纹和验证身份；任何漂移都取消创建并重新形成候选；
6. 使用临时 Index 调用正常 Git commit lifecycle，不绕过现有 Hook、签名或项目配置。Hook 拒绝时不得创建；Hook 改写 message 或 candidate 时必须由创建后回读识别，不得沿用创建前 passed 结论；
7. commit 成功后回读新 `HEAD`、parent、tree、实际 message、实际路径及剩余状态。只有真实 Index 原始身份仍未被其它执行者改变且目标路径创建前无既有 staged 重叠时，才把真实 Index 中这些目标路径对齐到新 `HEAD`；其它既有 staged 条目的 stage/blob 身份必须保持；
8. commit 已产生但 message/tree/parent 不匹配、真实 Index 无法安全对齐或回读失败时返回部分结果，不自动 reset、amend 或改写历史；只清理本次明确拥有且身份可验证的临时资产。

实现接口至少要区分 `prepared`、`blocked`、`not_created`、`created` 与 `partial`，并把新 commit 身份、实际 tree/message/paths、真实 Index 前后身份、剩余 staged/unstaged/untracked、Hook/进程诊断和未执行范围交还。首轮 tests 应覆盖 clean/unborn/linked worktree、add/delete/rename、既有无关 staged 保留、目标 staged 重叠阻断、所有创建前漂移、Hook 拒绝、Hook 改写、commit 成功回读、真实 Index 对齐失败和临时资产清理。该规划仍不定义 Helper 公开 Schema、Hook 安装或 push/PR。

## 14. 全量回归基线恢复

进入写入封装实现前，已先修复独立于 commits 模块的五类型准入记录路径漂移：运行时唯一常量 `ADMISSION_AUDIT_PATH` 与 `current_specs_repository` fixture 同步指向实际的 `docs/v4-architecture/active/V4-五类型全局归并封闭记录.md`，不恢复旧路径、不复制审计文件，也不放宽资格检查。路径修复使原 46 failures 与 102 setup errors 全部消失。

随后发现一个非级联断言仍保留 30 激活前的有效规范计数，已把相应受损来源场景的期望从 16 更新为 17。修复后全量 `code/tests` 为 516 passed，相关 Ruff check/format check 通过。后续临时 Index 与 Git 写入 Code 必须以该全绿基线为准；若新增失败，不得再归因于旧路径漂移。

## 15. 候选形成与 commit 执行实现结果

写入封装已经按 §13 分成两个内部模块：

1. `ldvh.commits.candidate_index` 从明确、规范化的 worktree 相对路径闭集形成进程私有且带所有权标记的临时 Index；它先绑定 `governed_single`、真实 `HEAD` 和真实 Index，拒绝目标路径与既有 staged paths 重叠，并要求临时候选实际 paths 与调用方闭集完全一致；
2. 临时 Index 以确定的 `HEAD` tree 或 unborn 空树为基线，`git add` 和 `write-tree` 会向目标仓库对象库写入尚未被 ref 引用的 blob/tree；这属于候选形成的明确 Git 写入，不改变用户真实 Index、Working Tree 或 ref，也不再被描述成只读 Adapter；
3. `ldvh.commits.execution` 把 Human 授权、AI 语义审核和验证覆盖作为调用方显式 guard，但不把这些布尔断言包装成授权证据；机械 Validator 必须现场返回 passed；
4. 创建前重新核对临时 Index snapshot/tree、真实 `HEAD` commit/tree、真实 Index、目标 Working Tree、管辖结果、message 和 03 指纹；任一漂移均清理受控临时资产并在 commit 前停止；
5. commit 使用显式临时 Index 调用正常 Git lifecycle，阻断仓库身份环境重定向，同时保留实际用户/项目 Git 配置、Hook、签名与身份政策；不使用 `--no-verify`，不调用 push、amend、reset history 或远端操作；
6. 创建后从实际 commit object 回读 tree、parents、UTF-8 message 和 diff paths；Hook 拒绝返回 `not_created`，Hook 改写 message/tree/paths、parent 不一致、回读失败或 Index 无法安全对齐返回 `partial`，不自动改写已经产生的历史；
7. 只有实际 tree/paths 与候选一致、真实 Index 仍保持候选形成时身份，才对齐本次目标 paths 到新 `HEAD`；对齐前后比较非目标 stage/blob records，既有无关 staged 条目必须保持。该边界能检测协作式 Git 写入造成的漂移，但尚未声称对不遵守 Git Index lock 的外部写入具备跨工具线性化保证；
8. 临时资产仅在目录前缀、系统临时目录位置、Index 路径和随机所有权标记同时匹配时清理；不匹配时保留并返回 `unsafe`，不扩大删除。

候选形成新增 14 项、执行新增 13 项风险 tests；commits 模块合计 58 项通过，覆盖 clean/unborn/linked worktree、add/delete/rename、既有 staged 保留、重叠和路径扩张阻断、HEAD/Index/Working Tree 漂移、环境重定向、所有权清理、Hook 拒绝、Hook message/tree 扩张、真实 Index 对齐失败及 commit 回读。全量 Code tests 为 543 passed，全量 Ruff check 和本增量 format check 通过。

本结果建立内部 Code 能力，不等于 Helper 公开操作、环境 Hook 安装、跨进程持久候选、push/PR 或任意一次真实 commit 已经完成。真实使用仍必须由 AI 依据 30 取得 Human 当前授权、确定路径闭集、完成语义与验证审核，再以同一候选调用内部执行能力。

## 16. 首次真实 dogfood 结果

Human 已在当前连续任务中明确授权提交并要求按计划推进。AI 将 Git 提交机制、统一契约、Web token 同步和恢复本增量全量验证所必需的路径修复判断为一个共同主要目的，显式选择 22 个目标路径，并排除工作树中既有的 `V4-Audit-Report-GLM5.2-2026-07-14.md` 删除与 `05-06-基础规范边界专项审计.md` 未跟踪文件。

临时 Index 候选、机械 Validator、AI 语义审核、验证覆盖 guard 和创建前全部身份重检通过。内部执行能力创建 commit `9d462a7e6f031f4609e3d55e86198b295099032b`，parent 为 `13bf510dfed89fd6aa9b0183c7d688123a841601`，tree 为 `a613fa5a4fd4f9044f0d64f614d6b141e67aa6b0`；回读的 22 个路径、规范化 message、parent 和 tree 与候选一致，真实 Index 对齐完成，临时资产清理结果为 `discarded`，执行结果为 `created` 且无 issues。

提交后真实 Index 为空；上述外部审计报告删除仍为 unstaged，05/06 专项审计仍为 untracked，没有被静默纳入、丢弃或改写。该结果证明内部 Code 闭环在当前实际仓库成立，不外推 Helper 公开操作、Hook 安装、push/PR 或其它环境已经集成。

## 17. 原生 `commit-msg` Hook 最小接入规划

09 §5.1 已为来源已独立定义的原生阻断型机械 Gate 建立唯一窄例外：它可以绕过 Helper 直达唯一核心 Code，但只接收真实事件输入、绑定同一实际候选/来源/管辖/Index 身份并返回 allow/block 与诊断。03 §9 是本增量的唯一机械合格条件来源；30 继续不定义 Hook；33 继续只组织一次安装与验证行动。本增量不新增 Git 专用 Spec、Helper 操作、Helper 字段、第二份 Schema、登记册或状态机。

共享 runner `ldvh.hooks.commit_msg` 必须从同一已分发规则源解析 03 投影，读取 Git 提供的完整 message 文件，解析 02 管辖并以 Git 实际 commit 使用的 Index 观察候选，最后调用既有纯 Validator。`passed` 才返回零；`failed`、`unverifiable`、来源缺失、管辖未完成、候选读取失败或观察漂移均返回非零。它不写 message、Index 或 Git 历史，也不判断本地最小增量、主要目的、语义、授权、验证充分性或完成。

Git 侧只允许一个 POSIX 薄 adapter：它从当前 `commit-msg` 事件取得 worktree、message 文件和可选的 Git `GIT_INDEX_FILE`，再把这些值及安装时显式固定的 runner/workspace 原样传给共享 runner。adapter 不保存提交 type/scope/body 规则、管辖逻辑、AI 判断或 Helper Schema。对 LDVH 内部临时 Index 的创建提交，runner 必须显式消费 Git 事件提供的该 Index，而不能退回读取用户默认 Index。

本地管理入口只提供 `status`、`install`、`uninstall`。安装或卸载必须显式确认 Human Gate；任何已有 `core.hooksPath`、既有 `commit-msg`、符号链接、未知文件或 effective hooks directory 位于当前 worktree 外时一律停止、零写入，不设置、修改、合并或清除 Git 配置。只有默认 Hook 目录中的精确 LDVH 自有 regular file 才能更新或删除；linked worktree 的 common-dir 默认 Hook 目录保持不支持，避免一次授权影响兄弟 worktree。

最小 tests 只固定独立失败价值：真实 `git commit` 的机械正反例（失败时 HEAD/Index 不前进）、内部临时 Index 的同一候选观察、非管辖/不可验证 fail closed、已有用户 Hook/`core.hooksPath`/shared common-dir 的零写入、以及 Human Gate 后仅删除自有 wrapper。既有 Validator 风险 tests 继续唯一覆盖格式规则，不重复 AI 语义。当前 V4 worktree 已显式设置 `.githooks-v4`，因此属于安装器应停止并交还的现状；隔离仓库验证完成后，是否迁移或授权当前项目的 Hook 仍由 Human 另行决定。该能力只覆盖正常本地 Git lifecycle；`--no-verify`、远端导入和服务端创建提交不因本入口获得约束。

## 18. 原生 Hook 实现与验证结果

本增量已经完成：09 §5.1 只增加原生阻断型机械 Gate 的窄例外；`ldvh.hooks.commit_msg` 从当前规则源取得 03 投影、解析 02 管辖、读取 Git message 与显式 Git Index 后调用纯 Validator；`ldvh.git_hooks.commit_msg` 只渲染 POSIX 薄 adapter，并提供受 Human Gate 保护的 `status`/`install`/`uninstall`。adapter 本身不保存规则或 Helper Schema；Hook 的自有文件以正文 SHA-256 识别，用户后来改动、符号链接和未知文件均不被覆盖或删除。

真实隔离 Git 生命周期 tests 证明：不合格 message 阻断且 HEAD/Index 保持，合格 message 正常创建提交；内部临时 Index 经过 Git 事件显式传入并被同一 Gate 观察；非管辖项目 fail closed；既有用户 Hook、任意 `core.hooksPath`、linked worktree 共享目录和被修改的伪自有文件均零写入；未确认 Human Gate 不卸载，确认后只移除完整自有 wrapper。wheel/sdist 生命周期同时验证两个新 console entry point 存在且卸载后退出。

独立 POST 审核确认 09 例外未扩大为新的语义或状态权威，五组 tests 均有独立失败价值。最终快照完成全量 `code/tests`：`799 passed, 10 skipped`；全库 Ruff check 和 format check 均通过，`git diff --check` 通过。当前 V4 worktree 的 `core.hooksPath` 仍为 `.githooks-v4`，目录仍只有既有 `README.md`；本增量没有安装、替换或移除当前项目 Hook，也没有修改其 Git 配置。实际项目接入仍等待 Human 另行授权。
