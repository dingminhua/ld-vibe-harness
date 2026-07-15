# V4 Codex 环境接入 Code 实现规划

> 记录性质：本文保存 09 首个具体环境接入增量的 Code 边界和实现结果，不是规则源，也不自行授予插件安装、Hook 信任、环境配置或真实接入效力。实际安装与环境证据见 `V4-Codex环境接入-安装与真实验证记录.md`。

## 1. 目标与来源

本增量为 Codex 提供一个最小薄接入单元，在 `SessionStart` 的 `startup|resume` 范围内把 Codex 当前 `cwd` 和安装时显式配置的 `workspace_root` 投影给现有 Helper `resolve-governance-scope`，并把 Helper 原始机械结果作为额外上下文交给 AI。

直接规则来源：

1. `environment-integration`：单一接入单元、显式配置、输入/结果忠实映射、静态安装与真实触发区分；
2. `work-object-governance-scope`：`workspace_root`、工作对象 locator 和管辖解析语义；
3. `helper-cli-service-contract`：Helper 公开调用与共同响应；
4. `code-engineering-practices`：模块责任、错误、tests 和证据边界。

具体环境资料使用当前官方 Codex Hooks 与插件文档，重点是：插件默认发现 `hooks/hooks.json`；命令 Hook 从 stdin 接收 JSON；插件 Hook 获得 `PLUGIN_ROOT`、`PLUGIN_DATA`；`SessionStart` 支持 `startup|resume` matcher，并可通过 `hookSpecificOutput.additionalContext` 提供上下文；非托管 Hook 安装后仍须由 Human 审核信任。

## 2. 当前增量边界

纳入：

1. `code/plugins/ldvh/` 中一个合法 Codex 插件包；
2. 一个只匹配 `SessionStart: startup|resume` 的命令 Hook；
3. 插件数据目录中的显式安装配置 `ldvh.json`；
4. 配置的只读检查、方案、原子写入和静态验证入口；
5. Hook 输入校验、Helper 子进程调用、结果忠实映射和失败诊断；
6. manifest、配置、成功、失败和部分结果 tests；
7. 插件结构校验、手工 Hook 直测和后续 Codex 真实新任务触发证据。

不纳入：

1. `PreToolUse`、`PermissionRequest`、`PostToolUse` 或 `Stop`；当前 Helper 没有来源定义的对应判断操作；
2. 规则适用、模板选择、行动授权、事实写入或完成声明；
3. 自动发现工作区、从 `cwd` 猜父目录、扫描任意配置或使用隐藏环境变量替代安装配置；
4. 自动安装到个人 marketplace、自动信任 Hook、重启 Codex 或替 Human 操作 UI；
5. 管辖项目配置写入、事实源初始化或其它环境 adapter；
6. 把手工脚本直测表述为 Codex 已真实触发。

## 3. 资产与责任

| 资产 | 责任 |
|---|---|
| `code/plugins/ldvh/.codex-plugin/plugin.json` | 插件身份和 Human 可见元数据；不声明 Hook 已安装或可信 |
| `hooks/hooks.json` | 只注册 Codex 当前支持的 `SessionStart` matcher 和薄命令入口 |
| `scripts/session_start.py` | 读取 Hook stdin 与 `PLUGIN_DATA/ldvh.json`，调用同一 Helper，映射结果 |
| `scripts/configure.py` | 对显式 Helper 路径、工作区根和插件数据目录执行 check/plan/apply/verify |
| `code/tests/environment/` | 验证 manifest、Hook 声明、配置副作用、输入投影、结果映射和失败边界 |

插件脚本不导入 LDVH 内部 Python 模块；它只通过已存在的 `ldvh call resolve-governance-scope` 外部契约连接 Helper。这样插件更新不复制内部实现，普通 wheel、editable install 或其它部署只要提供明确 Helper 可执行文件即可使用同一入口。

## 4. 安装配置契约

配置文件固定为 `$PLUGIN_DATA/ldvh.json`，字段闭集：

| 字段 | 要求 |
|---|---|
| `config_version` | 固定为 `1` |
| `helper_executable` | 安装时明确选择的绝对可执行文件路径 |
| `workspace_root` | 安装时明确选择的绝对工作区根；其下必须存在 02 定义的配置文件 |

配置不保存管辖项目副本、规则路径、模板、状态、验证结论、环境版本或永久 receipt。`apply` 只有在显式确认参数存在时原子写入；覆盖已有不同配置前必须在方案中报告变化，真实执行仍受 Human Gate。`verify` 只检查当前文件、路径和 Helper 直调，不声明 Codex 真实自动触发。

## 5. Hook 映射

输入必须是 JSON object，且：

1. `hook_event_name` 精确为 `SessionStart`；
2. `source` 为 `startup` 或 `resume`；
3. `cwd` 为非空绝对目录；
4. `PLUGIN_DATA` 为非空绝对目录，且其中配置通过当前检查。

形成的 Helper 请求固定为 compact：

```json
{
  "work_object_locators": ["<cwd>"],
  "arguments": {"workspace_root": "<configured workspace_root>"},
  "response_profile": "compact"
}
```

脚本不解释 `scope_status`。Helper 返回合法且与退出码一致的 JSON 时，不论结果是 `ok`、`partial`、拒绝或不可用，都作为带明确来源说明的 `additionalContext` 原样交给 AI。退出码/结果不一致、无 JSON、超时、进程启动失败或配置缺失时，不伪造 Helper 结果；对 manifest 实际支持的 SessionStart，适配器同时形成不阻断启动的 `systemMessage` 和 `additionalContext`，使 Human 界面与 AI 都明确知道没有取得治理结果且必须按范围未决处理。非支持事件或 source 只报告输入错误，不伪造成 SessionStart 上下文。

## 6. 风险与测试

| 风险 | 检查范围 |
|---|---|
| 插件结构不被 Codex 接受 | plugin-creator validator 与 manifest 精确断言 |
| Hook 注册了未支持事件或扩大 matcher | `hooks.json` 精确快照测试 |
| 从 cwd 猜工作区 | 缺配置、相对路径和错误工作区反例 |
| 覆盖用户配置或非原子写入 | plan 无副作用、确认要求、临时文件替换和既有配置变化测试 |
| Hook 输入被补造或覆盖 | 缺字段、相对 cwd、未知 source 测试 |
| Helper 部分/拒绝被改成成功 | 非零退出且合法 JSON、`partial` 原样映射测试 |
| Helper 崩溃或输出无效 JSON | 启动失败、超时/无效输出诊断测试 |
| 直测冒充真实 Codex 触发 | 文档和输出明确区分；真实新任务证据单列 |

## 7. 完成条件

本 Code 增量只有同时满足以下条件才完成：

1. 插件 manifest、Hook 和脚本通过结构校验及范围匹配 tests；
2. 配置入口完成 plan/apply/verify 正反例，且没有隐式写管辖配置；
3. Hook 手工 fixture 直测证明输入投影和 Helper 结果映射；
4. 插件经 Human 授权安装并审核信任后，在 Codex 新任务或恢复事件真实自动触发；
5. 真实触发结果能回指目标 Codex 版本、插件、事件、cwd、Helper 请求和返回上下文；
6. 失败/卸载或至少禁用路径取得对应证据；
7. 总纲分别报告静态实现、直接验证和真实环境接入范围，不互相替代。

## 8. 当前实现与验证证据

2026-07-15 当前工作树已形成：

1. `code/plugins/ldvh/.codex-plugin/plugin.json`；
2. 只声明 `SessionStart`、只匹配 `startup|resume` 的 `hooks/hooks.json`；
3. `PLUGIN_DATA/ldvh.json` 的显式配置、原子 apply、check/plan/verify；
4. 只调用 `ldvh call resolve-governance-scope` 的 `session_start.py`；
5. `code/tests/environment/test_codex_plugin.py` 的 17 项范围匹配测试。

当次验证：

- plugin-creator `validate_plugin.py`：通过；
- adapter 与 environment tests：17 passed；
- Ruff：通过；
- 完整 `code/tests`：567 passed；
- 临时插件数据目录中，plan 报告 `create` 且无变化，apply 只创建 `ldvh.json`，verify 返回 Helper `available_for_request` 并明确 `real_environment_trigger_verified: false`；
- 使用当前真实 `.venv/bin/ldvh`、`/Users/dmh2002/poker_hud_projects` 和本仓库 cwd 手工调用 `session_start.py`，Helper 返回 `outcome: ok`、`config_status: valid`、`scope_status: governed_single`、无未完成对象和无 diagnostics。

新增反例还证明：损坏或含未知字段的既有配置、断链配置符号链接不会被当成缺失配置覆盖；Helper 当次不可用、可执行文件消失、相对 cwd、未知契约或 outcome/退出码不一致均不会被映射为有效上下文。Hook 上下文会明确回指实际 Helper 可执行入口、adapter 请求、退出码与原始结果。

失败路径的真实探针进一步确认：Codex 把 `systemMessage` 作为 Hook 警告，而不是模型上下文。实现据此增加受支持 SessionStart 失败的 `additionalContext`，17 项 adapter tests 继续通过；真实缺失配置任务能看到 adapter unavailable、没有治理结果及“按范围未决处理”的要求。

Human 授权后，候选已按个人插件 cachebuster 流程安装为 `ldvh@personal` 版本 `0.1.0+codex.20260715021623`；个人来源与安装缓存逐文件一致，Hook 为 Trusted/Enabled，显式配置 `check/verify` 通过。Codex 0.144.2 新任务已分别证明正常配置成功、缺失配置显式降级、`/hooks` 停用后无注入、恢复后再次成功。完成条件 §§7.4–7.6 已满足于当次版本、用户、入口、工作区和 `SessionStart startup|resume` 范围。

本实现不声明永久卸载、V3 恢复、其它 Codex 版本、用户、机器、工作区、环境或 Hook 事件已验证。详细基线、授权、指纹、thread id、结果和未验证范围见 `V4-Codex环境接入-安装与真实验证记录.md`。

### 8.1 Windows 仓库候选增量

后续 Windows 第 6 切片只更新仓库候选，不改写上述历史安装事实：

1. `hooks.json` 保留 POSIX `command`，增加 Codex schema 支持的 `commandWindows`；Codex CLI 0.144.2 对应实现会在 Windows 选择该 override，并通过 `%COMSPEC% /C` 执行，因此候选使用 `py -3.12 -X utf8` 和引用后的 `${PLUGIN_ROOT}\scripts\session_start.py`，不使用 PowerShell `$env:` 语法；
2. adapter 标准流与 Helper subprocess transport 固定为 UTF-8 strict，Helper 调用仍为 argv 且不启用 shell；
3. 测试 helper 按平台形成 POSIX shebang 或 Windows `.cmd` launcher，新增空格/中文路径、非法 UTF-8、stderr 不冒充 JSON、timeout 显式降级和 argv 边界检查；当前 macOS 上 plugin validator、22 项 adapter tests 与 684 项完整 tests 通过；
4. 这些结果只证明 repo candidate。已安装的 `0.1.0+codex.20260715021623` cache、既有 trust hash 和真实触发仍对应修改前内容，不能作为该 Windows 候选的安装或集成证据。

Windows 原生 gate 必须使用新 cachebuster 重新安装，逐文件回读 source↔cache，重新审核 Hook 信任，并分别验证 `commandWindows`、`py -3.12`、含空格/中文的 `PLUGIN_ROOT/PLUGIN_DATA/cwd/workspace`、普通安装后的 `ldvh.exe`、startup/resume 与失败/停用/恢复。核心 CLI Windows 结论与 Codex adapter Windows 结论继续分开；当前 Ruff、format 与 diff check 也已通过，但都不替代该原生 gate。
