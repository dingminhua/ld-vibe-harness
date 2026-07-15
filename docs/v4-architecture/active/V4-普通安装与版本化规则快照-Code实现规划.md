# V4 普通安装与版本化规则快照 Code 实现规划

> 记录性质：本文是普通 sdist/wheel 自包含安装增量的 Code Implementation Plan。它不替代 01、04、07、09 或 33，不使构建、安装、升级、卸载、Helper 调用或环境接入自动成立。
>
> 当前状态：2026-07-15 四个切片已经全部完成；普通发行安装闭合当前 macOS/Python 3.12 范围，下一平台 Gate 为原生 Windows，不外推公共索引发布、环境 adapter 或三平台支持。

## 1. 目标与保持边界

本增量使普通安装的 `ldvh` 在脱离源码 checkout、editable install 和 `PYTHONPATH` 后，仍能从与自身发行版本绑定的完整规则快照发现同一批公开操作、读取规则内容，并继续对实际管辖项目执行事实与 Git 相关能力。

必须保持：

1. 源码运行与 editable install 继续读取导入 Code 所属同一 Git Working Tree 的当前 `specs/`；未提交变化不能被安装快照覆盖；
2. 普通 wheel 只读取同一发行物内部的版本化规则快照，不搜索 `cwd`、同名目录、管辖项目、环境变量、缓存或其它 checkout；
3. 两种来源视图不得混合、拼接或在校验失败后互相回退；
4. Helper 公开命令、请求/响应顶层契约、十项当前操作身份和领域语义保持不变；
5. 规则快照只是同一正式规则源的发行表示，不是可在安装目录中编辑的第二权威；
6. Codex 插件仍按独立环境接入单元交付，不把残缺的 `plugins`/`scripts` namespace 冒充普通 Python 包能力。

## 2. 已观察失败基线

当前 `pyproject.toml` 构建的 wheel 不包含任何 `specs/*.md` 或授权附件。干净 Python 3.12 venv 安装后，在临时目录、无源码 `PYTHONPATH` 情况下执行 `ldvh capabilities`，实际得到：

- 退出码 `5`；
- `outcome: unavailable`；
- 缺口为导入的 Code 未与可定位的 LDVH Working Tree 规则源共置。

当前 setuptools namespace 自动发现还把顶层 `plugins` 与 `scripts` 打入 wheel，但没有携带完整 Hook manifest 和安装对象，形成残缺的伪插件交付面。

## 3. 规则快照与清单

构建时从根级 `specs/` 当前单一规则源和其中机器声明的非规则机械证据生成包内资源，不在 Git 中维护第二份 Markdown 副本。目标资源逻辑位置为 `ldvh/_rule_snapshot/**`，并带机器清单：

| 字段 | 要求 |
|---|---|
| `format` | 固定为 `ldvh-rule-snapshot/1` |
| `distribution` | 固定当前 Python distribution 名称 |
| `version` | 与构建产物 metadata 完全一致 |
| `algorithm` | 固定 `sha256` |
| `files` | 按 `role`、canonical path 升序；成员字段闭集为 `path`、`role`、`size`、`sha256`；`role` 只允许 `rule_candidate` 或 `mechanical_evidence` |
| `snapshot_sha256` | 对不含本字段的规范化 manifest payload 计算的集合摘要 |

manifest 顶层字段闭集固定为上表六项。规范化 payload 使用除 `snapshot_sha256` 外的五项，`files` 先按 `role` 再按 `path` 升序；随后用 Python JSON 等价规则执行 `sort_keys=true`、`ensure_ascii=false`、`separators=(",", ":")`，不附加换行，并对 UTF-8 字节计算 SHA-256。最终 `manifest.json` 使用相同 canonical JSON 序列化并只在文件末尾增加一个 LF。`path` 必须唯一、使用 POSIX 分隔符，不得为绝对路径、包含空段、`.`、`..` 或反斜杠；`rule_candidate` 必须匹配 01 §6.1 的两个候选位置，`mechanical_evidence` 必须由当前规则源的机器表以稳定 record key、canonical path 和 H2 namespace 唯一声明且不得匹配候选位置；`size` 为非负 integer；两个摘要均为 64 位小写十六进制。未知字段、重复 path、重复或非法证据映射、非规范排序、算法大小写变化或字段类型错误都使快照不可用。

sdist 必须包含根级 Specs、附件、由当前规则机器声明的机械证据、构建逻辑和必要说明；由 sdist 再构建的 wheel 必须得到相同资源集合与集合摘要。运行时必须先证明当前导入包实际属于清单 distribution，再核对版本、两类文件闭集、角色、长度、逐文件摘要和集合摘要，然后只解析 `rule_candidate`；`mechanical_evidence` 只通过专用 loader 交给声明它的机械检查。额外候选只检查 §6.1 两个目录和文件形状，不把 manifest 或机械证据误判为候选。任何缺失、额外、篡改、清单错误、包归属或版本不一致都返回 `unavailable`，不得回退其它来源。

## 4. 来源选择与身份

运行时按固定顺序选择且只选择一种来源视图：

1. 若导入的 `ldvh` 精确位于某 Git Working Tree 的 `code/ldvh`，立即且无条件选择 `working_tree`；根级 `specs/` 缺失、损坏或不可读属于随后检查失败，不得尝试安装快照；
2. 否则只检查同一已安装 distribution 的 `installed_release_snapshot`；
3. 两者均不能可信成立时返回规则源不可用。

`working_tree` 来源继续不带发行 `version`，并在详情中携带 `git_worktree_root`。`installed_release_snapshot` 必须携带 distribution version 与 `snapshot_sha256`，详情中不伪造 `git_worktree_root`。两者都使用 Specs canonical path 和精确行范围，使 AI 能区分“当前开发工作树”与“当前安装版本所带快照”。

## 5. 模块责任

| 位置 | 责任 |
|---|---|
| 构建配置/构建扩展 | 限定 Python 包发现；从根 Specs 生成 wheel 资源与清单；保证 sdist→wheel 可重复承载 |
| `ldvh.helper.rule_source` | 只负责确定唯一来源视图、验证快照身份并形成检查输入 |
| `ldvh.specs.discovery` | 分开实现 Working Tree 候选发现与清单约束的快照候选发现，不把快照伪装成 Git worktree |
| `ldvh.specs.repository` | 对两种可信候选视图复用同一身份、结构、关系、字段和公开操作机械检查；通过视图专用 loader 读取已声明机械证据，不对安装视图执行 Git 查询 |
| 中央规则来源引用构造器 | 为 capabilities、十项操作的 contract/declaration/qualification/gap/diagnostic/verification 及规范/模板读取统一形成 locator、version、details 和来源视图身份；禁止裸规则引用或混合身份 |
| 实现来源引用构造器 | 源码模式回指实际 Code 路径；安装模式至少绑定 distribution/version，不把不可定位的源码路径冒充无版本实现证据 |
| `code/tests/packaging/` | 承担构建产物内容、干净安装、篡改/缺失和生命周期 smoke tests |

## 6. 实施与提交切片

1. **契约与规划**：同步 01 的两种规则源视图、L0–L4 来源回指和 04 的缓存/版本观察语义；提交本规划；
2. **快照构建与定位**：新增构建生成、清单校验、包发现收紧、导入包归属证明、来源选择、可移植安全普通文件读取和单元/失败测试；
3. **Helper 来源投影**：让 capabilities、十项操作的全部规则引用、规范候选/内容和行动模板读取按来源视图返回正确 evidence；全量回归；
4. **干净安装矩阵**：验证直接 wheel、sdist→wheel、无源码 cwd、安装/强制重装/升级模拟/卸载、CLI 与十项公开操作；同步 README 与总纲。

每个切片开始前由 subagent 只读审核 blocker/major，完成后验证并创建独立本地 Git commit。

## 7. 风险匹配验证

至少覆盖：

1. source/editable 未提交 Specs 变化优先于任何包内快照；
2. 普通 wheel 中规则文件、附件和已声明机械证据集合完整、角色分离，且不出现顶层 `plugins`/`scripts` 伪包；
3. 快照文件缺失、额外、内容篡改、角色篡改、清单篡改、导入包不属于 distribution、distribution/version 不一致和集合摘要不一致均 fail closed；
4. cwd 中伪造 `specs/`、环境变量、管辖项目内同名目录和相邻 checkout 不改变来源选择；源码 worktree 中 `specs/` 缺失或损坏仍不得回退快照；
5. `ldvh capabilities` 发现十项已绑定操作，L2/L3/L4 和四份行动模板读取可用；
6. 事实候选/读取/创建/更新仍只作用于请求解析出的实际管辖项目，不把规则快照当事实项目；
7. wheel 与 sdist→wheel 的快照集合摘要一致；
8. 安装、强制重装、不同版本替换和卸载后没有旧快照被新入口继续读取；
9. Python 3.12 干净环境中 stdout 仍只有单一 JSON 响应，退出码和错误边界保持现有契约；
10. 后续 Linux、macOS、原生 Windows 使用同一安装矩阵，当前 macOS 结果不外推为 Windows 通过。
11. 递归检查十项操作响应中的全部 `kind: rule` 来源都具有同一实际视图身份；安装模式没有裸 `specs/...` 或 `git_worktree_root`，源码模式没有 distribution 快照身份；安装模式的 `kind: implementation` 证据至少绑定实际 distribution/version。

## 8. 当前未覆盖

本计划不实现 Web Spark POST、V3 事实迁移、bootstrap/resume、远端发布、分支保护或其它环境 adapter。普通安装完成也不证明 Codex 等环境已经安装或真实触发；环境接入继续按 09/33 独立验证。

## 9. 2026-07-15 切片 2 完成记录

切片 2 已完成快照构建、唯一来源定位和共同 repository 检查输入，保持 Helper 来源投影仍归切片 3：

1. `05.Att.01` 的“审计证据定位表”已经成为准入审计 record key、canonical path 与 namespace 的唯一机器映射；原 Code 三常量不再承担决策权；
2. 清单对 `rule_candidate` 与 `mechanical_evidence` 一并做闭集、长度、逐文件摘要和集合摘要校验，但只有前者进入规范发现；校验后的原始 bytes 直接供 Markdown 与机械证据解析，不在 hash 后重新打开；
3. Working Tree 只按导入包精确位于 Git 根的 `code/ldvh` 识别，不再以根规范健康为选择条件；普通安装则用 distribution 的 `files` 与 `locate_file()` 证明当前导入包、manifest 和每个快照资源由同一发行包实际认领；
4. POSIX 保留 `dir_fd + O_NOFOLLOW` 读取；portable 分支拒绝 symlink/reparse 并比较路径组件和文件句柄前后身份。此处只证明代码路径和单元反例，不能替代原生 Windows 实测；
5. setuptools 包发现只交付 `ldvh*`；直接 wheel 不再夹带顶层 `plugins/` 或 `scripts/`。sdist 创建时冻结同一已验证快照和精确源文件集合，无 `.git` 的 sdist→wheel 只复验并复用该快照。

实际验证：

- `ruff check code/ldvh code/tests`：通过；
- `.venv/bin/pytest -q`：577 passed；
- 直接 wheel：102 个归档条目，其中 25 个快照资源均进入 RECORD；无顶层 `plugins/` 或 `scripts/`；
- 干净 Python 3.12 venv 从直接 wheel 安装后，在 `/tmp`、无源码 `PYTHONPATH` 执行 `ldvh capabilities`：退出码 0、`outcome: ok`、发现 10 项操作；
- sdist 同时包含精确根 Specs、声明的机械证据和冻结快照；从无 `.git` 的 sdist 构建 wheel 成功，快照集合摘要与直接 wheel 同为 `15ff1160f97b80e1fbb3b5902feb9737997f443e140b03af1343e7934212e24b`，且同样没有伪插件包。

上述摘要绑定本次工作树内容；后续 Specs 或机械证据发生变化时应产生新的集合摘要，不得把该值写成长期常量。切片 2 完成时尚未覆盖的 Helper 来源投影现由下节切片 3 记录闭合。

## 10. 2026-07-15 切片 3 完成记录

切片 3 已完成 Helper 生成来源引用的统一身份投影；调用者或事实对象携带的普通字典不因恰好声明 `kind: rule` 而被重写：

1. Helper 内部生成的 `rule` 与 `implementation` 引用以不进入 JSON 的内部标记区分；复制仍保留标记，只对这类引用绑定当前 repository 的唯一来源身份；
2. Working Tree 规则引用带 `rule_source_view: working_tree` 与实际 `git_worktree_root`，不带发行版本；安装规则引用带 distribution、version、`snapshot_sha256` 与 `rule_source_view: installed_release_snapshot`，不暴露包内 `_rule_snapshot` 物理路径；
3. Working Tree 实现证据绑定实际工作树；安装实现证据只绑定 `implementation_source_view: installed_distribution`、distribution 与 version，不伪造 Git 根或把规则快照摘要误作实现身份；
4. 规范候选 compact 响应用一项 `specs/` 集合引用携带责任 key 与 canonical path 集合；精确 L3/L4 读取继续回指 canonical path、heading path 和行范围；
5. 只在 `sources`、`source_refs`、`evidence` 中按完整 canonical JSON 去重内部生成引用；没有可信 repository 身份时删去内部引用，不输出无版本、无视图的裸证据；
6. capabilities、规范候选/正文与行动模板候选/正文已经分别覆盖 Working Tree 和 installed snapshot 投影，旧 `working_tree_rule_set` 与作为规则来源的冗余 Working Tree observation 已退出。事实操作中描述实际管辖项目 Working Tree 的来源保持不变。

实际验证：

- `ruff check code/ldvh code/tests`：通过；
- `.venv/bin/pytest -q`：587 passed；
- 直接 wheel 与无 `.git` sdist→wheel 的 manifest 内 24 项资源成员集合摘要一致，均为 `15ff1160f97b80e1fbb3b5902feb9737997f443e140b03af1343e7934212e24b`；两者另各含一个 `manifest.json`；
- 在 `/tmp` 的干净 Python 3.12 venv 安装直接 wheel 后，`capabilities` 及规范候选、规范正文、行动模板候选、行动模板正文五类进程级调用全部 `outcome: ok`；递归检查到的内部规则/实现引用分别为 71、10、10、16、7 项，全部绑定 `ld-vibe-harness==0.1.0` 的安装身份，未出现 `_rule_snapshot`、`git_worktree_root` 或 `working_tree_rule_set`；
- 在另一干净 venv 安装 sdist→wheel 后，`ldvh capabilities` 退出码 0、发现 10 项操作，且同时出现安装规则快照与安装实现身份，不含 Working Tree 身份。

这些结果完成来源表达；切片 3 完成时尚未覆盖的强制重装、版本替换、卸载残留、全部公开操作进程矩阵和 README/总纲收口现由下节切片 4 闭合。Linux 与原生 Windows 仍不由本计划的当前证据外推。

## 11. 2026-07-15 切片 4 完成记录

切片 4 已把一次性手工 smoke test 提升为默认执行、无静默跳过的发行物生命周期回归：

1. 构建只发生在隔离临时源码副本；直接 wheel、sdist 和版本替换模拟不写共享 checkout，也不复用其 build、egg-info 或快照目录；构建前端与 backend 工具进入 `dev` 依赖；
2. 当前 direct wheel 与无 `.git` sdist 解包目录再构建的 wheel 使用完全相同的 manifest；24 项清单成员加 `manifest.json` 合计 25 项快照资源，避免把两种计数混写；
3. 临时 `0.0.0` 旧发行包带一个只属于旧 RECORD 的 Python 成员和不同快照摘要；升级到当前 `0.1.0` 后只剩当前 dist-info，旧成员、版本与快照身份全部退出；
4. 当前安装的 manifest 被篡改后，`ldvh capabilities` 以 `unavailable`、退出码 5 fail closed；同一 wheel `--force-reinstall` 后恢复原始资源和安装身份；
5. direct wheel 与 sdist-derived wheel 分别在独立 venv、无 LDVH 源码 `PYTHONPATH` 的进程中，对十项公开操作逐项执行有效 `capabilities <key>`、有效 `call <key>` 和操作专属无效请求；每次 stdout 都是一个 canonical UTF-8 JSON 加单个 LF，stderr 为空，invalid request 为退出码 2；
6. prepare/create/read/update 按一个隔离受管辖 Git 项目串行执行；全项目非 Git 文件树与 Git status/index 指纹证明 capabilities、prepare 和 invalid request 无持久副作用，有效 create/update 只改变预期 canonical 事实文件且不改变 Git index。规则与实现引用始终绑定 installed distribution，governance/facts/Git 始终回指临时项目 Working Tree，安装快照前后摘要不变，也没有在安装目录生成管辖配置、事实实例或 Git metadata；
7. 卸载后只检查 LDVH 自有 console script、package、dist-info、快照和旧 RECORD 成员消失；`ruamel.yaml` 等依赖留存不被误报为 LDVH 残留；
8. README 与工作推进总纲只声明本地构建和当次 macOS/Python 3.12 普通 distribution 证据；没有宣称 PyPI 发布、Linux/Windows 通过、三平台 CI 或环境 adapter 自动接入。生命周期矩阵以 `--no-deps` 安装 LDVH wheel，并从开发环境复制已声明的 `ruamel.yaml` 到独立依赖路径，以便离线验证 LDVH 自有安装对象；它不覆盖 pip 依赖解析。切片 2 的正常依赖安装 smoke 与本矩阵分别证明依赖安装可达和 LDVH 生命周期边界。

最终验证：

- 发行生命周期定向回归：2 passed；
- `.venv/bin/pytest -q`：589 passed；
- `ruff check code/ldvh code/tests`：通过；
- `ruff format --check code/ldvh code/tests`：123 files already formatted；
- `git diff --check`：通过。

普通安装当前增量至此完成。后续原生 Windows 阶段仍须处理跨平台锁、安全路径遍历与 reparse point、原子创建/替换、目录持久化降级、盘符/UNC/大小写和解释器启动，并取得真实 Windows 机器证据；该工作不重新打开本增量已经固定的双规则源与发行生命周期语义。
