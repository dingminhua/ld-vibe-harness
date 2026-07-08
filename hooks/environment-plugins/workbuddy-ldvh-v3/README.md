# WorkBuddy LDVH V3 Hook 样例包

本文档属于 LDVH Hook 资产说明。本文只说明 repo-local WorkBuddy 样例包结构，不安装插件、不修改 `~/.workbuddy`、不写 marketplace、不声明 WorkBuddy lifecycle Hook 已 integrated。

## 包结构

| 路径 | 职责 |
|---|---|
| `.codebuddy-plugin/plugin.json` | WorkBuddy 插件 manifest；声明 `hooks` 字段指向 `./hooks/hooks.json` |
| `assets/ldvh-plugin-icon-128.png` | manifest `composerIcon`；来自 LDVH `icons/` 的图标资产 |
| `assets/ldvh-plugin-icon-512.png` | manifest `logo`；来自 LDVH `icons/` 的图标资产 |
| `hooks/hooks.json` | WorkBuddy lifecycle hook 配置样例；使用 `${CODEBUDDY_PLUGIN_ROOT}` 路径变量 |
| `hooks/ldvh_runtime_shim.py` | 薄 shim；读取 stdin payload，解析 LDVH root，按事件需要委托 V3 `code/action_classifier.py` 和 `code/runtime_adapter.py`；默认不写事实源 |

本目录是 LDVH 仓库内的 Hook 资产来源，不是 WorkBuddy 用户环境插件安装目录。真实安装或升级必须在 Human Gate 后经 30 安装流程把目标环境需要的插件包写入目标环境位置；不得把本目录存在写成插件已安装。

## Hook 映射

| WorkBuddy event | LDVH canonical event | 当前样例处理 |
|---|---|---|
| `SessionStart` | `ldvh.session_start` | 调用 runtime adapter，输出 read plan / diagnostic，不声明 integrated |
| `PreToolUse` | `ldvh.pre_tool_use` | 只读 / 写入副作用分类委托 shared classifier；写入类调用 runtime adapter；只有目标环境真实支持阻断且通过安装验证后，才可作为阻断入口 |
| `Stop` | `ldvh.completion_claim` | 作为完成声明邻近候选；默认 diagnostic-only，不替代 Human 验收 |

与 Codex 样例包的差异：本包只注册 LDVH 核心三事件（SessionStart + PreToolUse + Stop），不注册 PostToolUse、UserPromptSubmit、Notification 等暂未映射到稳定 runtime 事件的环境事件。

研究采样默认关闭，真实 hook 验收不得写入 `ldvh-base/`、Spark 或其它正式事实源。只有显式设置 `LDVH_HOOK_SPARK_CAPTURE=1`、`true`、`yes` 或 `on` 时才启用采样；启用时必须用 `LDVH_HOOK_SPARK_DIR` 指向临时目录或其它非正式事实源目录。

## LDVH Root 解析

shim 按以下顺序解析 LDVH root：

1. `LDVH_ROOT` 环境变量；
2. payload 中的 `ldvh_root` / `ldvhRoot`；
3. payload `cwd` 或当前进程 cwd 的父目录；
4. shim 文件自身所在路径的父目录。

命中条件是存在 `code/runtime_adapter.py` 和 `specs/00-理念与构成.md`。找不到时，shim 输出 `LDVH_WORKBUDDY_SHIM_ROOT_NOT_FOUND` diagnostic 并允许通过，避免样例包误伤真实环境。

## 安装前必须确认

真实安装或升级前必须经 Human Gate 确认：

1. 插件来源位置和安装目标；
2. `hooks/hooks.json` 中 `${CODEBUDDY_PLUGIN_ROOT}` 是否在安装后正确解析为插件缓存目录；
3. `LDVH_ROOT` 或等价配置如何指向当前 V3 根目录；
4. `SessionStart`、`PreToolUse`、`Stop` 的真实 payload 样例；
5. PreToolUse 是否可阻断，以及失败时是否会影响普通只读工具；
6. 只读 / 写入副作用分类是否由 `code/action_classifier.py` 统一承接，shim 中不得维护独立分类规则；
7. status、stale V1 path、positive、negative 和 rollback 验证；
8. 卸载后确认环境不再自动触发 LDVH。

## 与 V1 插件的差异

| 项目 | V1 插件 | V3 样例包 |
|---|---|---|
| 命令路径 | 绝对路径指向 V1 `ld-vibe-harness/code/hook_adapter.py` | `${CODEBUDDY_PLUGIN_ROOT}/hooks/ldvh_runtime_shim.py` |
| 事件集 | SessionStart + PreToolUse（缺 Stop） | SessionStart + PreToolUse + Stop |
| shim 架构 | 直接调 V1 `hook_adapter.py`（单体） | 薄 shim → V3 `code/action_classifier.py` / `code/runtime_adapter.py` |
| matcher | `Write|Edit|MultiEdit|Bash`（PreToolUse） | 同 V1（保持不变） |
| manifest | `.codebuddy-plugin/plugin.json` | 同 V1（结构不变，内容更新） |

## 不做事项

本样例包不做：

1. 不安装到 WorkBuddy；
2. 不修改 `~/.workbuddy/settings.json` 或用户级 hooks 配置；
3. 不创建或修改 marketplace entry（经 30 安装流程部署）；
4. 不声明 `workbuddy.ldvh-plugin` 已指向 V3；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制。

## 本地验证

本样例包可做安装前静态检查：

```bash
python3 -m json.tool hooks/environment-plugins/workbuddy-ldvh-v3/.codebuddy-plugin/plugin.json >/dev/null
python3 -m json.tool hooks/environment-plugins/workbuddy-ldvh-v3/hooks/hooks.json >/dev/null
python3 -m py_compile hooks/environment-plugins/workbuddy-ldvh-v3/hooks/ldvh_runtime_shim.py
```

这些检查只证明 repo-local 包结构、manifest 图标资产、shim 语法、payload 透传、shared classifier parity、环境 PreToolUse 映射到 `ldvh.pre_tool_use` 后的阻断返回、Stop 非阻断降级和安装验收入口的只读行为可用，不证明 WorkBuddy 已加载或触发该包。
