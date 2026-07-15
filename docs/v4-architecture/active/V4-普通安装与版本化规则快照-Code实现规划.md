# V4 普通安装与版本化规则快照 Code 实现规划

> 记录性质：本文是普通 sdist/wheel 自包含安装增量的 Code Implementation Plan。它不替代 01、04、07、09 或 33，不使构建、安装、升级、卸载、Helper 调用或环境接入自动成立。
>
> 当前状态：2026-07-15 已完成实施前只读审核和失败基线；先同步规则源契约，再分阶段实现资源构建、运行时定位和干净环境验证。

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
