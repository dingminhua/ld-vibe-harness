# 31A 环境插件最小包结构样例

文件状态：implementation-domain package skeleton。本文记录 V3 对环境插件最小包结构的 repo-local 样例处理；它不安装插件，不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录，不声明任何新的环境入口已 integrated。

## 背景

30A 已把环境插件实践边界放入 `code/docs/02-Environment-Plugin-Practice.md`。31A 继续把“所有支持 Hook 的协作环境通过 LDVH 插件、扩展包或 package 接入”的要求落成一个可审计样例结构。

Codex 是当前可审计样例，但不是总规则。其它环境后续必须按自身插件、扩展包或 package 机制建立独立样例。

## 本阶段处理

本阶段新增：

| 路径 | 作用 |
|---|---|
| `code/environment_plugins/README.md` | 环境插件样例目录的通用边界 |
| `code/environment_plugins/codex-ldvh-v3/.codex-plugin/plugin.json` | Codex plugin manifest 样例 |
| `code/environment_plugins/codex-ldvh-v3/hooks/hooks.json` | Codex lifecycle hook 配置样例 |
| `code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py` | 只调用 V3 runtime adapter 的薄 shim |
| `code/environment_plugins/codex-ldvh-v3/README.md` | Codex 样例包安装前确认项和不做事项 |

## 设计口径

1. manifest 不声明 Rules / Skill 顶层机制；
2. manifest 不写 unsupported `hooks` 字段，Hook 配置放 `hooks/hooks.json`；
3. shim 只做 payload 读取、event 映射、LDVH root 解析和 runtime adapter 调用；
4. LDVH root 通过 `LDVH_ROOT`、payload、cwd 或 shim 路径解析，不写死旧仓库路径；
5. 找不到 LDVH root 时输出 diagnostic 并允许通过，避免未安装样例误伤真实环境；
6. `SessionStart` 映射 `session_start`，`PreToolUse` 映射 `pre_tool_use`，`Stop` 映射 `completion_claim`；
7. 只有 `PreToolUse` 样例保留阻断返回码；`Stop` 默认 diagnostic-only，不替代 Human 验收。

## 与真实安装的边界

本阶段没有做以下事项：

1. 不安装到 Codex；
2. 不修改 `~/.codex/config.toml`、`~/.codex/hooks.json` 或插件 cache；
3. 不创建 marketplace entry；
4. 不把 `codex.ldvh-plugin` 声明为 V3 integrated；
5. 不删除或修改旧 `ldvh@personal` 插件；
6. 不恢复 `rules/` 或 `skills/` 顶层目录机制；
7. 不修改测试实现域。

## 后续进入条件

若后续要真实安装或升级 Codex LDVH V3 插件，必须先进入 Human Gate 并确认：

1. 插件安装来源位置；
2. `hooks/hooks.json` 命令是否按插件根目录解析；
3. 若目标环境不支持插件相对路径，安装器如何渲染指向插件缓存内 shim 的绝对路径；
4. `LDVH_ROOT` 或等价配置如何指向当前 V3 根目录；
5. 三类事件的真实 payload 样例；
6. PreToolUse 是否可阻断；
7. status、stale V2 path、positive、negative 和 rollback 验证；
8. 卸载后如何确认环境不再自动触发 LDVH。

## 验证

本阶段使用静态和轻量 smoke 验证：

```bash
python3 /Users/dmh2002/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py code/environment_plugins/codex-ldvh-v3
python3 -m json.tool code/environment_plugins/codex-ldvh-v3/hooks/hooks.json >/dev/null
python3 -m py_compile code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py
printf '{"hook_event_name":"SessionStart","session_id":"31A-smoke","cwd":"."}' | python3 code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py >/dev/null
git diff --check
```

这些验证只证明 repo-local manifest、Hook 配置和 shim 可被静态检查，不证明 Codex 已加载、信任或触发该插件。
