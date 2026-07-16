# V4 Codex 环境接入安装与真实验证记录

> 记录性质：本文保存 09/33 首个 Codex 接入增量的当次环境基线、实际变化、证据和未验证范围，不是规则源。结论只覆盖本文明确记录的机器、用户、Codex 版本、插件版本、工作区、入口和事件。

§§1–8 保留 2026-07-15 初版候选的历史证据；2026-07-16 核心先行后继候选的当前安装与触发范围只由 §9 说明。两者不得相互借用版本、信任、事件或回滚结论。

## 1. 目标与结论

目标环境是本机当前用户的 Codex CLI/个人插件系统。接入单元来自仓库 `code/plugins/ldvh`，只覆盖 Codex `SessionStart` 的 `startup|resume`，通过显式安装配置调用本仓库 `.venv/bin/ldvh` 的 `resolve-governance-scope`。

2026-07-15 当次行动已经完成：旧同名 V3 插件保护性备份、V4 原位替换、cachebuster 重装、Hook 信任与启用、`PLUGIN_DATA` 配置、静态回读、真实成功触发、真实缺失配置降级、停用反例和恢复复测。当前可以声明本机 Codex 0.144.2、插件 `ldvh@personal` 版本 `0.1.0+codex.20260715021623`、本仓库 cwd、`startup|resume` 范围的环境接入成立；不得外推到其它用户、机器、Codex 版本、环境、事件或工作区。

本行动没有修改 `LDVH-GOVERNED-PROJECTS.yaml`，没有初始化事实源，没有提交 Git，没有删除历史 receipts，也没有把 fixture、Helper 直调或插件文件存在冒充为真实自动触发。

## 2. 安装前基线与保护对象

| 对象 | 安装前观察 |
|---|---|
| Codex CLI | `codex-cli 0.144.2` |
| 个人 marketplace | `/Users/dmh2002/.agents/plugins/marketplace.json`，名称 `personal` |
| 旧插件 | `ldvh@personal`，`installed, enabled`，版本 `0.1.0+codex.20260709033554` |
| 旧来源/缓存 | `/Users/dmh2002/plugins/ldvh`；`/Users/dmh2002/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260709033554` |
| 旧 Hook | `SessionStart startup|resume|clear|compact`，以及 `PreToolUse`、`PostToolUse`、`UserPromptSubmit`、`Stop`、`Notification` |
| 历史 receipts | `/Users/dmh2002/.codex/ldvh/session-receipts` 下 190 个文件 |

旧关键指纹：manifest `2865a2a07742381813341c572bdfb6de7b22430656eb096c94995638433d4dfc`，Hook 声明 `6cf0670047f8a91f248c521353e23da2fedfa61539a9cb914e26af777545a02b`，运行 shim `f86a02d9dd16615a9e151da89f73b26aa64ec2c7a19ad17daa6c725ab9fb7ab5`。

执行前创建了只读备份 `/Users/dmh2002/plugins/ldvh-v3-backup-20260715T020923Z`，其中包含旧 `source/`、`installed-cache/`、`codex-config.toml` 和 `marketplace.json`；复制后逐文件比较一致，再撤销写权限。备份根当前权限为 `dr-xr-xr-x`。marketplace 备份与行动后当前文件的 SHA-256 均为 `ce0bb15359d377cd41bf156b22ec1ff1b7251fce0f74a6107eec1e40bd3b4c81`。

## 3. 授权与实际变化

Human 先确认建立 09 和配套行动模板，并明确同意个人插件替换。授权范围覆盖当前用户的同名个人插件替换、Hook 信任/启用、显式配置、真实触发探针以及停用/恢复验证；不覆盖管辖配置修改、历史 receipt 删除、Git 提交、其它插件或其它环境。

实际变化按以下顺序完成：

1. 用仓库候选替换个人插件来源中的旧 V3 文件；
2. 以 plugin-creator cachebuster 流程把版本改为 `0.1.0+codex.20260715021623`；
3. 执行 `codex plugin add ldvh@personal`，安装到 `/Users/dmh2002/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260715021623`；
4. 在 Codex `/hooks` 中核对唯一的 `SessionStart startup|resume`，确认来源 `Plugin - ldvh@personal`、命令 `python3 "$PLUGIN_ROOT/scripts/session_start.py"`、超时 30 秒，并保持 Trusted/Enabled；
5. 在 `/Users/dmh2002/.codex/plugins/data/ldvh-personal/ldvh.json` 写入且只写入 `config_version`、明确 Helper 绝对路径和明确工作区绝对路径；
6. 运行静态验证和真实 Codex 新会话探针；随后在 `/hooks` 中停用、验证无注入，再恢复并复测。

当前 Hook 信任哈希为 `sha256:ffd068d025ad230e3482e27f6f9a83884784a91e23eb26a6980aa8f236014d76`，最终 `enabled = true`。旧 V3 其它 Hook 状态项仍保持 `enabled = false`，没有被重新启用。

## 4. 安装与配置回读

| 对象 | 当前回读 |
|---|---|
| 插件登记 | 唯一 `ldvh@personal`，`installed, enabled` |
| 当前版本 | `0.1.0+codex.20260715021623` |
| 当前安装缓存 | `/Users/dmh2002/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260715021623` |
| manifest SHA-256 | `494f2cf1722a4f05732d2c02fbdc7819a77bf0a92e08dafc036a18fb427db114` |
| Hook 声明 SHA-256 | `290d3f05664a3767597362b0e5e7486fb119adb5d60f5826cc9f3dea004bc19b` |
| `session_start.py` SHA-256 | `6886dfc9f728b30d3224e5eabd6ee6d530762c906b2368a5cfdbd9601e695a76` |
| 配置 SHA-256 | `bef4e536b4510ceb381182c7d7cb9c3c45afad23eb6aef5af3d4d48f0957ff54` |
| 配置权限 | 目录 `drwxr-xr-x`，文件 `-rw-------` |
| Helper | `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh` |
| 工作区根 | `/Users/dmh2002/poker_hud_projects` |

个人来源与当前安装缓存逐文件一致。`configure.py check` 返回 `outcome: ok`；`verify` 调用 Helper `capabilities resolve-governance-scope`，返回契约 `ldvh-helper-cli/2`、退出码 0 和 `available_for_request`，并正确保留 `real_environment_trigger_verified: false`，没有用静态检查替代真实触发。

## 5. 真实环境触发证据

所有探针均由 `codex exec --ephemeral --json -s read-only` 在本仓库 cwd 启动新任务；提示明确禁止工具调用，只要求模型读取 SessionStart 已提供的上下文并返回紧凑 JSON。

| 路径 | Codex thread id | 实际结果 | 结论 |
|---|---|---|---|
| 正常配置成功 | `019f638f-df1e-7e60-a1c0-81fe2f614588` | `seen:true`，`SessionStart`，Helper 入口为本仓库 `.venv/bin/ldvh`，`helper_outcome:ok`，`config_status:valid`，`scope_status:governed_single` | 目标环境真实自动进入当前 Hook、调用同一 Helper 并把结果交给 AI |
| 临时缺失配置 | `019f6390-0d12-7470-8501-2c5f45e5d328` | `seen:true`，`adapter_status:unavailable`，明确配置缺失、没有注入治理结果，并要求按 governance scope unresolved 处理 | 主要失败路径不阻断 Codex、不伪造成功，AI 可见缺口和恢复要求 |
| `/hooks` 停用后 | `019f6390-e89d-7612-86d0-848eb24c51ee` | `/hooks` 为 Installed 1 / Active 0；新任务返回 `seen:false` | 停用后不再自动注入 |
| `/hooks` 恢复后 | `019f6391-88f0-7971-8643-e34877aca8af` | `/hooks` 为 Installed 1 / Active 1；新任务返回 `seen:true`、`helper_outcome:ok`、`scope_status:governed_single` | 恢复后连接重新成立 |

失败探针只把 `ldvh.json` 原子移到同目录临时名称，并使用 shell trap 无条件恢复；探针后确认临时文件不存在、配置 SHA-256 未变且 `check` 再次返回 `ok`。该探针发现 Codex 的 `systemMessage` 是 Hook 警告而不是模型上下文，因此实现修正为：受支持的 SessionStart 失败同时产生界面警告和 `additionalContext`；不受支持事件仍不伪造成 SessionStart。修正后 17 项 adapter tests 和真实缺失配置探针均通过。

## 6. 用户资产、回滚与残留

- 历史 receipts 行动前后均为 190 个，没有读取语义、修改或删除；
- marketplace 文件与备份指纹一致，没有改变其它插件登记；
- 管辖配置和项目事实源没有变化；
- 无删除的主要回滚入口已经以 `/hooks` 停用和恢复真实验证；
- 若以后需要恢复 V3，当前只读备份保存了旧来源、安装缓存和配置基线，但本次没有执行 V3 恢复，因为 V4 安装及全部主要验证均成功；
- 永久卸载、V3 恢复、Codex 0.144.2 之外版本、其它用户/机器/工作区、`clear|compact` 及其它 Hook 事件均未验证，不属于本次完成声明。

## 7. 最终证据矩阵

| 要求 | 当次依据 | 结论 |
|---|---|---|
| 09/33 身份与责任 | 当前 Specs、准入调查、Helper 精确读取 | 已成立 |
| 插件结构与最小范围 | plugin validator、精确 manifest/Hook tests、安装后回读 | 已成立 |
| 用户资产保护 | 只读 V3 备份、marketplace 指纹、receipt 前后计数 | 已成立于当次观察范围 |
| 显式配置与 Helper 直调 | plan/apply/check/verify、权限与指纹、Helper 实际响应 | 已成立 |
| Human 授权与 Hook 信任 | 当前指令、`/hooks` Trusted/Enabled 和配置回读 | 已成立 |
| 真实成功与主要失败路径 | 两个新 Codex task 的自动 SessionStart 结果 | 已成立于当前版本/入口/事件 |
| 停用与恢复 | `/hooks` Active 0/1 及对应新任务反例/复测 | 已成立 |
| 完整卸载或 V3 回滚 | 未执行 | 不属于本次必要完成边界；不得声明 |

因此，本次 09/33 的首个 Codex 环境接入增量已经闭合。后续若升级 Codex、改变插件代码/Hook、Helper 入口、工作区、用户或环境，必须按 33 重新检查受影响范围；本记录不能替代未来当次证据。

## 8. 后续仓库候选变化的证据边界

Windows 第 6 切片随后修改了仓库内 Hook 命令和 adapter UTF-8 transport，但没有修改个人 marketplace、已安装 cache、配置或 Hook 信任状态。本记录中的版本、SHA-256、thread id、成功/失败触发与停用/恢复结论仍是当时有效的 macOS 历史证据，只对应 `0.1.0+codex.20260715021623` 的旧安装内容。

因此，仓库新候选不得复用本记录宣称 source↔cache 一致、已 trusted 或真实触发。未来在 macOS 重装或进行原生 Windows 验证时，必须按 33 使用新 cachebuster、重新回读逐文件指纹、重新审核 trust hash，并产生新的 startup/resume 与失败/停用/恢复证据；在此之前，仓库候选、旧安装缓存和原生 Windows 支持是三个不同结论层级。

## 9. 2026-07-16 核心先行后继候选

本节记录提交 5baef8aa 之后的当前候选，不重写 §§1–8 的历史事实。共享恢复实现已从插件 bundle 移至 ldvh.hooks.context_recovery，并由明确的 ldvh-context-recovery 入口调用；Codex 脚本只投影本机原生事件、读取显式配置、以 argv 调用核心并原样返回非空 exchanges。

### 9.1 实际安装与配置回读

| 对象 | 当次观察 |
|---|---|
| 仓库提交 | 5baef8aa feat(v4): establish core-first hook recovery |
| 个人来源与当前缓存 | /Users/dmh2002/plugins/ldvh；/Users/dmh2002/.codex/plugins/cache/personal/ldvh/0.1.0+codex.20260716090757 |
| 当前插件版本 | ldvh@personal 0.1.0+codex.20260716090757，CLI 回读为 installed, enabled |
| 核心入口 | /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4/.venv/bin/ldvh-context-recovery，以显式 Helper、工作区、工作对象 locator 和 Helper cwd 调用 |
| 配置 | 旧 v1 仅通过显式 --replace 整体替换为 v2；v2 包含 helper_executable、context_recovery_executable 与 workspace_root 的绝对路径 |
| source↔cache | cachebuster 后逐文件比较一致；个人来源和安装缓存均通过 plugin validator；缓存中的 configure.py check 返回 outcome: ok |

本轮先以本地 editable 安装使核心 console entrypoint 可用，再同步个人来源、运行 cachebuster、执行 codex plugin add ldvh@personal。没有手改 marketplace、没有推导核心入口、没有修改管辖配置、事实源或生产 Helper。Human 随后在 /hooks 完成授权；自动触发输出是授权生效的当次证据，本文不把 CLI 的 installed, enabled 表述为独立的 Hook 信任结论。

### 9.2 原生成功路径

当前线程 019f671a-eb74-7b62-a365-450290894556 产生两份 Hook 原始输出。两者均来自已安装 adapter，包含实际 Helper 请求、进程退出码和未修改的 Helper 响应：

| 原生路径 | 当次输出 | 可观察结果 |
|---|---|---|
| SessionStart/resume | a2da92be-a5e3-40a9-8dbc-626514091865.txt | 自动进入共享恢复；依次为 resolve-governance-scope、find-fact-object-candidates；均为 outcome: ok，所有 changes 为空 |
| SubagentStart | c59d4bec-ddab-4c40-8a65-c4a84827e237.txt | 自动进入同一共享恢复；操作集合、ok 结果和零变化与前项一致；启动后的独立子代理也确认收到该恢复上下文及“Code 未作语义判断”的说明 |

两条路径都先得到唯一受管辖项目 ldvh，才读取 F1；没有调用 capabilities、规则全文、F3/F4、写入操作、行动模板或任何 receipt/状态机。此处只证明这两个当次原生成功路径；它们不证明 AI 已恢复真实责任或完成了端到端 dogfood。

### 9.3 降级、未验证范围与结论

已安装缓存还做过一次无配置 direct probe：以不存在的 PLUGIN_DATA 调用 SubagentStart 映射时，adapter 返回 continue: true、明确的 unresolved context 与 hookSpecificOutput，没有伪造治理或事实结果。该结果只证明已安装 adapter 的非阻塞失败交还，不是新的目标环境自动失败触发。

本轮没有重新取得 SessionStart/startup、clear、compact、停用/恢复、Human 可见名称或图标展示的真实证据，也没有验证其它 Codex 版本、用户、机器、工作区或第二个环境。这些范围继续未验证；旧版本的停用/恢复和失败证据不能填补它们。

因此，当前可声明的范围是：本机当前用户、上述插件版本和工作区中，核心先行共享恢复通过 Codex 薄 adapter 已在 SessionStart/resume 与 SubagentStart 自动触发，并忠实交还两项来源定义的只读 Helper 结果。完整 Tests、POST 审核和实现边界见 V4-Codex环境接入-Code实现规划.md §9.6；下一主线 Gate 仍是 Human 选择真实工作后的纵向 dogfood。

### 9.4 Git worktree Gate 未安装范围

本记录中的 Codex Hook 只覆盖上下文恢复。当前没有为本机 Codex Local Environment 写入 setup script，也没有在任何真实项目或 Codex-managed worktree 安装 `commit-msg` wrapper；因此不声明工作树创建会自动安装 Git Hook。后续若 Human 授权一个具体项目×环境 setup，必须以当时的 `ldvh-git-hook bootstrap`、工作树内路径回读和真实环境创建证据另行记录，不能借用本节的 SessionStart/SubagentStart 触发证据。
