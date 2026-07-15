# V4 原生 Windows 基础 Code 实现规划

## 1. 目的与当前状态

本文把三份独立审计和 Windows 专项前置审核中的阻塞项转成可独立审核、验证、提交的实现切片。

当前状态仅为“开始构造 Windows 候选兼容基础”，不等于“Windows 已通过”。原生 Windows 支持结论必须来自 Windows 11 或 Windows Server 2022、Python 3.12、Git for Windows 和 NTFS 上的真实证据。

## 2. 不变边界

- 普通 wheel/sdist 安装已闭合的语义不得回退。
- Web 表现层不得修改；V4 Spark 创建是允许的唯一新增 Web 写入意图。
- LDVH 只验证和修改被明确管辖的项目，不把被管辖项目纳入 LDVH 自身 CI。
- POSIX 上现有安全性、原子性和耐久性不得因 Windows 适配而下降。
- macOS 模拟、mock、WSL 或 Wine 只能形成候选证据，不能替代原生 Windows 结论。
- 核心 CLI 与 Codex 适配器的 Windows 支持分别给出结论；不以修改 Web 表现层或建立 CI 作为本阶段前提。

## 3. 已知阻塞与主要风险

1. `facts.creation` 顶层导入 `fcntl`，Windows 连 `ldvh capabilities` 都无法导入。
2. 创建、读取和更新路径直接依赖 `O_DIRECTORY`、`O_NOFOLLOW`、`dir_fd` 及目录 `fsync`。
3. 多处仅拒绝符号链接，没有统一拒绝 Windows junction/reparse point。
4. update 只承诺同一 common-dir、同一类型锁内的 LDVH 受控入口跨进程单赢家；不承诺对外部编辑器或跨 clone 的线性化 CAS，需分别固化证据与披露。
5. Windows 的目录耐久性、共享冲突、盘符/UNC/大小写和 Git linked worktree 尚无原生证据。
6. Codex hook 固定使用 `python3` 与 POSIX shell，不能自动纳入核心 CLI 的 Windows 结论。

## 4. 平台边界

生产代码先集中下列接口，再迁移调用点：

- 平台选择的独占文件锁；
- symbolic link 与 Windows reparse point 的统一识别；
- 安全读取、原子创建、条件替换及耐久性能力；
- 明确区分“完整耐久”“降级耐久”和“拒绝执行”，不得伪造成功。

实现依据以官方文档为准：

- [Python 3.12 `os`](https://docs.python.org/3.12/library/os.html)
- [Python 3.12 `msvcrt.locking`](https://docs.python.org/3.12/library/msvcrt.html#msvcrt.locking)
- [Microsoft `LockFileEx`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex)
- [Microsoft `CreateFileW`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
- [Microsoft reparse point operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-operations)
- [Microsoft `ReplaceFileW`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)

## 5. 实现切片与提交门禁

每个切片开始前进行一次只读 subagent 审核，先处置 blocker/major；完成后运行相称验证并创建单独本地提交。

1. **候选级已完成**：建立平台文件系统边界，延迟加载 `fcntl`，集中锁和 reparse 判定。
2. **候选级已完成**：迁移安全读取路径，统一拒绝 link/reparse，并建立 fail-closed 行为。
3. **候选级已完成**：迁移 ID 分配锁，证明 POSIX 不回退并构造 Windows 候选并发语义。
4. **候选级已完成**：分离 POSIX/Windows 原子创建与条件替换，定义目录耐久性边界。
5. **候选级已完成**：建立 Windows 路径、进程、Git linked worktree 的候选测试矩阵。
6. 单独审核 Codex 适配器的解释器与 shell 边界；未闭合前不得宣称适配器支持 Windows。
7. 在原生 Windows 上执行并固化证据。
8. 发布前再建立 LDVH 自身的三平台 CI 与开源发布资料。

第 1 切片的当前证据：静态检查通过；文件系统与 Markdown 定向测试 26 个通过；CLI 创建、更新与进程边界定向测试 42 个通过；完整测试集 593 个通过。该证据只证明 macOS 上的 POSIX 行为未回退并形成 Windows 候选兼容基础，不构成原生 Windows 通过结论。

第 2 切片的当前证据：POSIX 继续使用逐级 `openat`/`dir_fd` 与 `O_NOFOLLOW`；portable 分支覆盖 root、中间目录、最终文件、打开句柄与读取后拓扑复核；缺失稳定身份与 UNC 均 fail-closed；事实候选、关系、规格发现和安装快照不进入 link/reparse。静态检查通过，定向测试 79 个通过，完整测试集 608 个通过。该证据仍只是 macOS 上的 POSIX 保持性与 Windows 候选证据。

第 3 切片的当前证据：POSIX 上 4 个独立解释器的临界区保持单并发，持锁进程被终止后锁可恢复；6 个并发 allocator 形成连续且唯一的 ID，main/linked worktree 共用 Git common-dir counter；损坏 counter fail-closed。fake `msvcrt` 证明 offset 0、固定 1-byte、`LK_LOCK`/`LK_UNLCK` 及 descriptor 异常清理。静态检查通过，定向测试 33 个通过，完整测试集 616 个通过。Windows CRT `LK_LOCK` 固定约 10 秒重试上限及当前通用错误映射仍须原生验证；锁目录安全打开、counter 替换和目录耐久性归入第 4 切片。空 lock 文件按官方语义允许锁定 EOF 之后的字节，文件保持持久且不截断、不替换、不删除。

第 4 切片的当前证据：lock/counter/fact 父路径和最终文件统一拒绝 link/reparse；POSIX 保留 `openat`、`O_NOFOLLOW`、hard-link no-overwrite、原子 replace、文件与目录 `fsync`。新建事实目录保持 `0755`，allocator 私有状态目录保持 `0700`；每级新目录 entry 均先同步其父目录，create 的最终目录同步覆盖“目标发布 + 临时名清理”，因此只有完成该边界才报告 `file_and_directory`。写结果显式记录 namespace 提交点、耐久等级与 cleanup residue，提交后同步或清理失败不再误报“未写入”。独立进程 update 在同一 LDVH 类型锁内形成单赢家；外部不协作写入仍不宣称线性化 CAS。Windows 候选分支绕开 `dir_fd`/`O_DIRECTORY`/`O_NOFOLLOW` 及 POSIX read backend，以本地同目录 hard-link/replace 形成 `file_only` 候选；公开 Windows 写入在 Human 接受该降级前于创建锁状态之前 fail-closed。静态检查通过，定向测试 56 个通过，独立进程单赢家连续 20 次重复通过，完整测试集 644 个通过。原生 NTFS 的 hard-link、replace、sharing violation、ACL/ADS 和终止恢复仍待验证。

第 5 切片的当前证据：测试侧统一按平台定位 `ldvh`/`ldvh.exe`，不再假定无后缀 console script；Git 身份与事实读取的路径输出改为 bytes 后按 ASCII/UTF-8 责任严格解码，CRLF 可接受，非法编码形成 `git_output`/`unavailable` 而不冒泡。Windows 路径策略允许本地盘符绝对路径和普通相对路径，拒绝依赖当前驱动器状态的 drive-relative/root-relative 路径；UNC 与 device namespace 在 governance locator/workspace/config project、规格发现、commit observe/prepare/execute/discard 和事实 Git 入口于文件观察、临时目录探测或启动 Git 前 fail-closed。argv 保持 `shell=False`，Git canonical selected path 继续使用 `/`，`GIT_INDEX_FILE` 继续作为单一文件路径。macOS 候选矩阵覆盖空格/中文 workspace、linked worktree、事实读取、allocator common-dir、临时 Index 与 linked branch 隔离；独立定向复核 235 个、完整测试集 679 个通过，Ruff 与 133 个 Python 文件格式检查通过。该证据不证明 Windows 路径大小写别名、Git for Windows 中文输出、`ldvh.exe`、NTFS 或 `%TEMP%` 的原生/fallback 行为；这些仍须第 7 切片原生验证。

## 6. 验证矩阵

### 6.1 当前 macOS 可验证

- 不存在 `fcntl` 时 CLI 模块仍可导入；
- POSIX 锁正常互斥且异常路径释放 descriptor；
- POSIX 写入的 namespace 提交点、目录耐久性和 cleanup 失败可区分；
- reparse 属性由统一函数识别；
- 现有事实创建、读取、更新、普通安装和全量回归不退化；
- 用 fake/mock 构造 Windows 分支只能标记为候选证据。

### 6.2 原生 Windows 必须验证

- wheel 与 sdist 生命周期、`ldvh.exe` 和十个操作；
- 盘符、大小写、含空格/中文路径；UNC 若不支持则明确 fail-closed；
- junction/reparse point，以及权限允许时的 symlink；
- Git for Windows linked worktree 与临时 index；
- 多进程 ID 分配、无覆盖创建、条件更新单赢家；
- sharing violation、失败清理及可恢复性；
- Codex hook 仅在其独立边界闭合后纳入。

## 7. 后续需要 Human 决策

这些决策不阻塞前几个候选兼容切片，但必须在原生验证或发布结论前确定：

- 首发只承诺本地 NTFS，还是同时承诺 UNC；当前默认 UNC 无证据即 fail-closed。
- 首发 Windows 范围只含核心 CLI，还是同时含 Codex 适配器。
- 原生 Windows runner/VM 的来源与授权。
- 是否接受 Windows 无目录 `fsync` 时明确披露的 `file_only` 耐久性降级；作出决定前 Windows 事实写入保持 fail-closed。
- 最终发布矩阵与三平台 CI 的触发策略。
