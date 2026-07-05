# Codex LDVH V3 Hook 样例包

本文档属于 LDVH Hook 资产说明。本文只说明 repo-local Codex 样例包结构，不安装插件、不修改 `~/.codex`、不写 marketplace、不声明 Codex lifecycle Hook 已 integrated。

## 包结构

| 路径 | 职责 |
|---|---|
| `plugin.json` | 目标环境插件 manifest 源资产；不包含 Rules / Skill 顶层机制，不在 manifest 中声明 unsupported `hooks` 字段 |
| `assets/ldvh-plugin-icon-128.png` | manifest `composerIcon`；来自 V2 `icons/` 的 LDVH 图标资产 |
| `assets/ldvh-plugin-icon-512.png` | manifest `logo`；来自 V2 `icons/` 的 LDVH 图标资产 |
| `hooks/hooks.json` | Codex lifecycle hook 配置样例；实际安装前必须确认命令路径解析方式 |
| `hooks/ldvh_runtime_shim.py` | 薄 shim；读取 stdin payload，解析 LDVH root，并按事件需要转调 V3 `code/runtime_adapter.py`；默认不写事实源 |

本目录是 LDVH 仓库内的 Hook 资产来源，不是 Codex 用户环境插件安装目录。真实安装或升级必须在 Human Gate 后把目标环境需要的插件包写入目标环境位置；不得把本目录存在写成插件已安装。

## Hook 映射

| Codex event | V3 runtime event | 当前样例处理 |
|---|---|---|
| `SessionStart` | `session_start` | 调用 runtime adapter，输出 read plan / diagnostic，不声明 integrated |
| `PreToolUse` | `pre_tool_use` | 调用 runtime adapter；只有目标环境真实支持阻断且通过安装验证后，才可作为阻断入口 |
| `PostToolUse` | 无稳定 runtime event | 当前静默返回，不做审计结论 |
| `UserPromptSubmit` | 无稳定 runtime event | 当前静默返回，不做输入分流结论 |
| `Stop` | `completion_claim` | 作为完成声明邻近候选；默认 diagnostic-only，不替代 Human 验收 |
| `Notification` | 无稳定 runtime event | 当前静默返回，不做通知治理结论 |

研究采样默认关闭，真实 hook 验收不得写入 `ldvh-base/`、Spark 或其它正式事实源。只有显式设置 `LDVH_HOOK_SPARK_CAPTURE=1`、`true`、`yes` 或 `on` 时才启用采样；启用时必须用 `LDVH_HOOK_SPARK_DIR` 指向临时目录或其它非正式事实源目录，不得把运行时 hook 采样直接写入 `spark-0046`。

## LDVH Root 解析

shim 按以下顺序解析 LDVH root：

1. `LDVH_ROOT` 环境变量；
2. payload 中的 `ldvh_root` / `ldvhRoot`；
3. payload `cwd` 或当前进程 cwd 的父目录；
4. shim 文件自身所在路径的父目录。

命中条件是存在 `code/runtime_adapter.py` 和 `specs/00-理念与构成.md`。找不到时，shim 输出 `LDVH_CODEX_SHIM_ROOT_NOT_FOUND` diagnostic 并允许通过，避免样例包误伤真实环境。

## 安装前必须确认

真实安装或升级前必须经 Human Gate 确认：

1. 插件来源位置和安装目标；
2. `hooks/hooks.json` 中命令是否会按插件根目录解析；若目标环境不支持插件相对路径，安装器必须渲染指向插件缓存内 shim 的绝对路径；
3. `LDVH_ROOT` 或等价配置如何指向当前 V3 根目录；
4. `SessionStart`、`PreToolUse`、`PostToolUse`、`UserPromptSubmit`、`Stop`、`Notification` 的真实 payload 样例；
5. PreToolUse 是否可阻断，以及失败时是否会影响普通只读工具；
6. status、stale V2 path、positive、negative 和 rollback 验证；
7. 卸载后确认环境不再自动触发 LDVH。

## 不做事项

本样例包不做：

1. 不安装到 Codex；
2. 不修改 `~/.codex/config.toml`、`~/.codex/hooks.json` 或插件 cache；
3. 不创建 marketplace entry；
4. 不声明 `codex.ldvh-plugin` 已指向 V3；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制。

## 本地验证

本样例包可做安装前静态检查：

```bash
python3 -m json.tool hooks/environment-plugins/codex-ldvh-v3/plugin.json >/dev/null
python3 -m json.tool hooks/environment-plugins/codex-ldvh-v3/hooks/hooks.json >/dev/null
python3 -m py_compile hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py
python3 -m pytest tests/code/test_environment_plugins.py -q --tb=short
python3 -m pytest tests/code/test_install_verification.py -q --tb=short
python3 code/test_runner.py targeted --changed hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py --dry-run
```

这些检查只证明 repo-local 包结构、manifest 图标资产、shim 语法、payload 透传、六类事件 opt-in 临时采样、PreToolUse 阻断返回、Stop 非阻断降级和安装验收入口的只读行为可用，不证明 Codex 已加载或触发该包。`code/test_runner.py targeted` 必须能为 `hooks/environment-plugins/` 变更选择环境插件测试，防止样例包路径调整后漏跑回归。
