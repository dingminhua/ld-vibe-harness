# full-v4 Working Tree 证据生产与运行记录接入

## 状态、起点与来源

- 状态：current，实施前规划。
- 实现起点：Git commit `ddcff52a`。
- Working Tree 边界：本规划覆盖随后在同一 Working Tree 中形成的 C 实现变化；未提交、未跟踪、ignored、staged 或 committed 不改变规划或实现的当前有效性。并存的 WorkCase 载体不是本规划的 Code 语义来源，但只要命中固定纳入政策，full-v4 采集器必须按实际 bytes 纳入。
- 语义来源：`specs/07-Code 实践与测试规范.md` §11.2、`specs/attachments/07.Att.01-Working Tree 测试证据字段表.md`。
- 已有实现基础：`code/ldvh/testing/working_tree_evidence.py` 是政策投影、DTO 校验、canonical fingerprint 和 manifest 比较的唯一纯函数维护位置；`code/ldvh/testing/test_runs.py` 与 `tools/run_full_tests.py` 是当前耐久运行记录和唯一 full-v4 入口。

本增量的目标，是让 full-v4 的 `passed` 或 `failed` 严格绑定到同一实际管辖 Git worktree 在测试前后的完整、稳定内容。Git tracked、Index、HEAD、dirty、`.gitignore` 或提交状态不参与文件集合和有效性判断。

## 实现范围与明确排除

实现范围：

1. 在 `code/ldvh/testing` 增加政策感知的安全 manifest I/O 层；
2. 只为生产端消费补充 `working_tree_evidence.py` 的最小政策匹配接口，不复制 DTO 字段、枚举、指纹或比较规则；
3. 在 `test_runs.py` 编排治理身份、before checkpoint、步骤执行、after 观察、DTO 形成、耐久记录和 v1/v2 兼容；
4. `tools/run_full_tests.py` 只适配必要的 CLI 返回码和异常回读；
5. 在 `code/tests/testing` 建立风险对应的单元与集成测试。

明确排除：修改规则源；新增 Helper 操作；Web、Codex 或 Human 展示；把 DTO 变成事实对象字段；改变 full-v4 五个检查步骤及其测试语义；把 Git tracked、staged 或 committed 变成前置；实施 B、D、E；修改 Sparks；push 或 PR。

## 模块责任与依赖方向

### `working_tree_evidence.py`：唯一纯契约实现

负责固定政策投影、policy fingerprint、路径词法规范化、manifest fingerprint、DTO/片段校验和 before/after 的确定性比较。允许新增的生产接口仅暴露当前政策条目或回答一个已规范化相对路径是否应排除，返回值必须由同一 `_POLICY_RULES` 派生。

它不得读取文件系统、调用 Git 或 governance、运行进程、写记录，亦不得判断变化语义、测试充分性或 WorkCase 完成。

### `working_tree_capture.py`：副作用隔离层

新增模块，负责：

- 调用现有 governance resolver，形成唯一 `GovernedWorktreeBoundary`；
- 在已接受的实际 worktree root 下，按纯政策接口先剪枝再遍历；
- 不跟随 symlink/reparse，识别非普通条目；
- 完整读取普通文件原始 bytes，并在读取前后检查身份/元数据稳定性；
- 将安全观察转换为附件定义的 manifest、coverage gap 和诊断；
- 在 after 重新执行同等级治理身份确认，并把不一致交给纯 DTO 形成逻辑作为 `identity_mismatch`。

该模块只输出结构化观察，不写运行记录、不启动测试、不决定顶层 `passed/failed/unknown`。诊断只包含规范化相对路径、阶段、闭集 code 和必要系统错误类别；不记录文件内容。

### `test_runs.py`：耐久运行状态机与记录维护者

负责 run ID、record/output 路径、原子 JSON、worker 生命周期、固定步骤、v1/v2 reader、capture checkpoint、终态 DTO 嵌入和顶层状态矩阵。

允许依赖 `working_tree_capture.py`；后者允许依赖纯 `working_tree_evidence.py`、现有 governance 与 filesystem 原语。反向依赖禁止。`tools/run_full_tests.py` 只调用 `test_runs.py` 公开函数，不读取内部 checkpoint 或重算 DTO。

### `tools/run_full_tests.py`：薄 CLI

只解析 `start/status/wait/_worker` 参数、调用 `test_runs.py`、原样输出 JSON，并根据返回记录的实际顶层状态给出 CLI exit code。它不得自行遍历文件、解析 DTO 或基于 Git 状态改写结论。

## 唯一治理身份接受矩阵

full-v4 在第一个检查前只接受以下全部条件同时成立：

1. governance resolver 的 `scope_status` 精确为 `governed_single`；
2. 没有 technical non-completion，requested scope 与 completed scope 精确一致；
3. 恰好一个 `governed` resolution；
4. `governed_project_id`、`git_worktree_root`、`git_common_dir` 均非空且唯一；
5. 请求 `workspace.resolve()` 精确等于该 `git_worktree_root`。

实现调用现有 resolver 时，以请求 worktree 形成一个 explicit scope，并从其上层稳定发现治理配置；不得把项目 worktree root 错当成 `explicit_workspace_root`，因为当前配置位于管辖 workspace 上层。linked worktree 可以通过与已登记 main worktree 相同的 common-dir 成立，但实际 `git_worktree_root` 必须仍是本次请求的 linked root。

`non_governed`、`multiple_governed_projects`、`mixed_scope`、`scope_unknown`、配置 missing/invalid/conflict、Git 或配置技术失败、数量或字段不完整，全部在首命令前形成 v2 `unknown`、`evidence_complete: false`、`working_tree_evidence: null` 和结构化诊断，不启动 worker。禁止回退到 HEAD、dirty、目录名或单独 Git identity 推断项目身份。

after 再执行同一接受矩阵。项目、worktree root 或 common-dir 与 before 不一致，或 after 身份不再完整成立时，不比较 manifest；使用 before 已接受身份形成合法 `incomplete` DTO，`after` 为 `null`，coverage gap 使用 `stage=comparison`、`code=identity_mismatch`。

## 安全采集与失败闭合

1. 排除判断在目录下探前执行；`.git` 文件或目录及其它精确政策排除均不读取。
2. hidden、ignored、untracked、dirty 文件不会因此排除；命中纳入且未命中排除的普通文件全部按原始 bytes 读取。
3. symlink、reparse、非普通条目、枚举失败、读取失败、读取期路径变化和 NFC collision 都生成附件闭集 gap，并使 manifest/coverage `incomplete`。
4. incomplete manifest 可以保留确已安全读取的文件子集，但 `manifest_fingerprint` 必须为 `null`；不得从子集推断缺失路径不存在。
5. before 即使 incomplete，仍持久化 checkpoint、执行固定五步，并在 worker `finally` 尝试 after；顶层最终必为 `unknown`。
6. `.ldvh-test-runs`、本地环境、依赖目录、缓存和构建输出按附件精确排除，避免 runner 自指或测试生成物造成伪 stale。

实现优先复用现有安全路径/读取原语；若现有通用遍历无法在下探前应用政策，不以放宽政策换取复用，而在副作用层实现最小专用遍历。跨平台行为以显式分支和 test double 验证，不用单一平台的偶然 `stat` 行为证明 Windows reparse 语义。

## `ldvh-test-run/2` 唯一记录契约

`ldvh-test-run/2` 只用于新 full-v4。新 probe 继续产生 `ldvh-test-run/1`；reader 同时接受 v1/v2。消费者必须同时检查 `plan=full-v4`，probe 的 `passed` 永不表示产品或当前 Working Tree 验证。

新 full-v4 的 `runs_root` 固定为 `<workspace>/.ldvh-test-runs`，CLI 传入其它位置属于请求错误，在创建 run 前拒绝；不得把 runner 自己的 record/output 写入受测 worktree 内其它未排除位置。probe 保留自定义隔离 `runs_root` 的能力。

v2 复用 v1 已有 run、时间、路径、步骤和输出字段，并冻结以下新增/变化字段：

- `working_tree_evidence`：必填，运行态固定为 `null`，不得省略；正常 worker 终态替换为完整合法 DTO object。
- `working_tree_capture_checkpoint`：只允许在运行态或无法形成终态 DTO 的异常终态存在；它不是 DTO、不是完成证据。初始字段闭集为 `governed_project_id`、`git_worktree_root`、`git_common_dir`、`coverage`、`before`、`capture_diagnostics`；进入 after 前可以再增加唯一字段 `after_capture_started_at` 并先耐久写回。DTO 成功形成后必须移除。
- `evidence_complete`：只有 v2 顶层状态为 `passed` 或 `failed` 时为 `true`，其余为 `false`。
- `source`：v2 明确禁止该字段，不产生 v1 的 HEAD/dirty source；治理身份只来自 checkpoint/终态 DTO，Git revision 不参与有效性。
- `diagnostics`：v2 必填 array；成员字段闭集为 `stage`、`code`、`summary` 三个非空 string。它只记录运行、治理、采集、步骤、回读或终态形成的技术上下文，不复制 DTO gap，不携带文件内容。相同观察导致的降级必须幂等追加，不能在每次 status 回读中重复。
- `raw_output_path`：精确绑定到当前 record 所在 run directory 的 `output.log`，不得接受其它可读文件作为替代。
- `raw_output_size_bytes`、`raw_output_sha256`：v2 运行态禁止，worker 在关闭并完整回读 raw output 后于终态原子写入；前者为非负整数，后者为 64 位小写 SHA-256。`passed/failed` 必须同时具备并与固定路径实际 bytes 一致；`unknown` 只在确已形成时保留二者。

`working_tree_evidence: null` 的 v2 终态只允许三类情况：身份前置失败；worker 在写出终态前失踪；record 或 DTO 终态形成不可恢复。保留 checkpoint（若已形成）和诊断，不补造 DTO。

正常 worker 无论步骤全过、确定失败或步骤 unknown，都在 `finally` 尝试 after，并形成合法 DTO。DTO 形成后由 `working_tree_evidence.py` validator 再校验一次再原样写入 record。

## 顶层状态和 exit code 矩阵

| 步骤聚合 | Working Tree DTO | 顶层 status | evidence_complete | final_exit_code |
|---|---|---|---|---|
| 全部 passed | complete | passed | true | 0 |
| 至少一个确定 failed，之后可 not_run | complete | failed | true | 首个失败步骤的实际非零码 |
| 任一步 unknown | 任意 | unknown | false | null |
| 全部 passed | stale / incomplete / null / 非法 | unknown | false | 0 |
| 确定 failed | stale / incomplete / null / 非法 | unknown | false | 实际失败码 |
| 未形成可确定步骤聚合 | 任意 | unknown | false | null |

v2 公开状态只有 `running`、`passed`、`failed`、`unknown`；初始 record 直接为 `running`。步骤状态和每步 exit code始终保留，DTO 导致的 `unknown` 不抹掉已经确定的聚合 exit code。

v2 reader 必须锁定 full-v4 五个步骤的身份、顺序、cwd 和 argv，检查每步字段闭集、状态/时间/exit 组合以及 `passed* → running|failed|unknown? → not_run*` 的单调前缀结构。顶层 `passed/failed/unknown` 与步骤聚合及 `final_exit_code` 必须符合上表；record 可被读取不等于允许修复或忽略不一致。worker 捕获任何步骤编排、输出关闭或完整性形成异常时，顶层必须为 `unknown`，即使异常发生前内存步骤恰好已呈全 passed 或确定 failed；只保留仍可由步骤机械确定的 exit code。

同一 reader 还必须闭合记录内的交叉引用：`run_id` 精确等于 record 所在 run directory 名称；`record_path` 精确指向被读取的 `record.json`；`workspace` 精确等于运行态 checkpoint 及终态 DTO 的 `git_worktree_root`；五步 cwd/argv 由该同一 workspace 派生；`raw_output_path` 字段精确等于同一 run directory 的 `output.log`，不得因 `resolve()` 后指向相同 bytes 就接受 alias 路径。以上任一不一致都是非法 v2 record，不得组合不同 run 或 worktree 的步骤与证据。

v1 历史 `starting` 继续可读。v1 继续执行原有 worker 缺失和 raw output 不可读时降为 `unknown` 的规则，但绝不因为没有 DTO 被追溯改写、补造 DTO 或解释为当前 Working Tree 绑定。

## 耐久性、错误传播和诊断

- before checkpoint 必须在 worker 启动前原子写入 record；没有耐久 checkpoint 不启动有效 full-v4。
- parent 在 spawn 后写入 `worker_pid/worker_started_at` 是 worker 开始写 record 和执行步骤的持久 gate。worker 在 gate 中 PID 精确等于自身前不得更新步骤；parent 写入必须从当前 record 合并，禁止用 spawn 前旧 dict 覆盖。gate 超时或 parent 指派失败时零步骤执行并形成 `unknown`。这一协议同时可供 v1 worker 使用而不改变 v1 记录语义。
- 每个步骤开始、结束，after 尝试和终态均通过既有原子 JSON 路径写回；output 继续 fsync。
- worker 内异常进入统一 `finally`，优先保留已知步骤和 capture 信息，再尝试 after/DTO；无法形成时顶层 `unknown`。
- observer 不在 worker 已失踪后补做 after，因为那不再是测试窗口终点；它只把记录降为 `unknown` 并保留 checkpoint/诊断。
- raw output 在 `passed/failed` 后路径不等于当前 run directory 的固定 `output.log`，或缺失、不可读、长度/哈希不符时，observer 降为 `unknown`、`evidence_complete: false`，保留已形成 DTO和步骤结果，不声称输出完整。空文件只有在 worker 实际耐久记录的 size/hash 也精确对应且其它终态条件成立时才可能完整，不能仅凭“可读”成立。
- v2 observer 在 worker 失踪或 raw output 缺失时保留已能由步骤确定的聚合 `final_exit_code`；v1 继续原有置 `null` 行为。
- 记录读取拒绝未知 contract；v2 结构非法不得被修复或猜测，返回/持久化 `unknown` 的范围不得超过仍可安全识别的记录。

## 接口维护与兼容

内部接口由本规划维护，语义仍来自 07 与附件：

- `resolve_capture_boundary(...) -> boundary | diagnostics`
- `capture_manifest(boundary, stage) -> manifest + coverage gaps + diagnostics`
- `finalize_working_tree_evidence(checkpoint, after observation) -> validated DTO`
- `start_run/observe_run/wait_for_run/run_worker` 保持 CLI 调用责任，但新增 v2 分支。

接口可以在实现中用 dataclass 或明确 JSON object 表示；不得在多个模块各自维护 DTO Schema。v2 是 Code 内部耐久记录演进，不改变 Helper 公共响应契约。没有批量迁移旧 record；v1/v2 通过 reader 分支共存。

## 风险与测试映射

| 风险 | 主要检查 |
|---|---|
| 政策复制或排除漂移 | 纯政策接口与附件已有 contract tests；采集器精确纳入/排除测试 |
| untracked/ignored 被漏掉 | 隔离 Git repo 中创建 ignored/untracked 文件，断言 manifest 包含及变化触发 stale |
| symlink/reparse/特殊条目或 TOCTOU 被当完整 | test double 与平台可用 fixture 触发闭集 gap、null fingerprint、incomplete |
| NFC collision 与排序不稳定 | 构造观察路径碰撞、非 ASCII 排序和重复路径负向测试 |
| 错误治理身份启动测试 | 覆盖全部 scope/config/technical 拒绝矩阵，断言零步骤启动；linked worktree 正向核对 root/common-dir |
| after 身份漂移仍比较 | after identity mismatch 测试断言 `after:null`、identity gap、顶层 unknown |
| stale 被误报 failed/passed | 测试窗口内修改纳入文件，断言完整 changes、DTO stale、顶层 unknown且保留 exit code |
| incomplete 或非法 DTO 扩大结论 | 捕获失败/validator 失败测试断言 unknown、evidence_complete false |
| 步骤失败/unknown 与 DTO 组合错误 | 完整状态矩阵参数化测试，包括 failed 后 not_run |
| worker/output/record 耐久失败 | worker 丢失、raw output 错误路径、空/截断/篡改、size/hash 缺失、终态形成失败和 wait/status 回读测试 |
| 异常与步骤记录扩大结论 | passed/failed 后抛出编排异常强制 unknown；固定五步身份、字段、前缀、时间/exit 与顶层矩阵篡改负测 |
| run/worktree/output 跨引用拼接 | run_id/record directory、workspace/checkpoint/DTO root、步骤 cwd/argv、raw output 精确字段路径的逐项篡改与 symlink alias 负测 |
| parent/worker 启动竞态 | PID gate 并发测试：gate 前 worker 零写，parent 从当前 record 合并后才允许步骤，旧快照不得回退状态 |
| v1 被追溯改义、probe 冒充产品 | v1 starting/terminal/原降级测试；probe contract/plan 与 full-v4 v2 分离测试 |
| runner 输出自造 stale | full-v4 非固定 runs-root 请求拒绝测试；probe 自定义 runs-root 保持测试 |
| CLI 与真实组合偏移 | `tools/run_full_tests.py` start/status/wait 集成测试；最终实际 full-v4 dogfood 回读 DTO |

聚焦测试先于 full-v4 dogfood。最终全量运行必须回读合法 v2 record、`working_tree_evidence.status=complete`、固定五步成功，并检查 manifest 确实包含当时命中纳入政策的未提交或未跟踪载体。该结果随后作为 `workcase-0003` 缺失证据的输入；C 自身生命周期不构成测试证明。

## 已知缺口与重新评估条件

- 本增量不提供 DTO 的 Human 展示；D 只能原样消费终态 DTO。
- v2 不迁移 v1。未来移除 v1 reader 前必须另有明确兼容决策和历史记录处置。
- 若附件政策、DTO contract 或 full-v4 步骤计划升级，必须先更新来源，再同步本规划、纯函数、采集器与 tests；不得静默复用 `/2` 表达不同语义。
- 若安全读取在目标平台无法稳定识别 reparse 或路径变化，相应观察必须保持 incomplete，不以平台限制改成 complete。
