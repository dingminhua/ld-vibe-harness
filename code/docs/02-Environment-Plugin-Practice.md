# 环境插件与 Hook 接入实现实践

本文是 Code 实现域文档，承接 `specs/01-保障与衔接.md` §6、`specs/06-行动模板基础规范.md` 的 LDVH 安装初始化配置行动模板、`specs/07-Code确定性执行规范.md` 和 `specs/09-测试与验证规范.md`。本文不定义新的规则源、事实源、Human Gate、环境入口状态闭集或管辖项目配置契约；若与 specs 冲突，以 specs 为准。

本文只处理环境 Hook 的插件化实现实践。Git `commit-msg` shim 和外部管辖项目 Git Hook 实践见 `code/docs/01-Git-Commit-and-Hook-Practice.md`。

## 实施边界

所有支持 Hook 的协作环境，都应通过对应 LDVH 插件、扩展包或 package 安装环境 Hook。正式接入不直接写入环境 Hook 系统文件；直接写入环境 Hook 系统文件只能作为调试、探针或迁移验证，不得作为正式接入形态。

环境插件只承担薄 shim 职责：

1. 接收目标环境的 lifecycle event 和原始 payload；
2. 保留并透传 payload，不复制 specs、事实对象、行动模板或 Human Gate 判断；
3. 定位 LDVH 根目录和已确认的管辖项目配置；
4. 调用 LDVH `code/runtime_adapter.py` 或对应稳定 Code 入口；
5. 将 stdout、stderr、exit code 和阻断结果按目标环境约定返回。

核心逻辑必须留在 LDVH Code 中。插件、扩展包或 package 不维护第二套规则源、字段契约、状态机、事实源或完成判断。

## 最小插件包契约

一个环境插件包至少应包含：

| 项目 | 最小要求 |
|---|---|
| manifest | 说明插件身份、版本、目标环境、LDVH 兼容版本、Hook 入口和卸载方式 |
| Hook 配置 | 映射目标环境 lifecycle event 到 V3 runtime event，且不得覆盖无关用户 Hook |
| shim 命令 | 只调用 LDVH Code 入口，不内嵌规则判断 |
| LDVH root 解析 | 明确从插件配置、工作区配置或显式参数解析 LDVH 根目录 |
| payload 透传 | 保留目标环境原始 payload，并补充 trigger source、target path、cwd 等上下文 |
| 状态检查 | 可判断 installed、enabled、trusted、target path、LDVH root 和 stale V2 path |
| 回滚入口 | 可禁用或卸载 LDVH 指针，并保留原有用户配置和非 LDVH 资产 |

插件包不得复制 specs、`ldvh-base/` 事实实例、`LDVH-GOVERNED-PROJECTS.yaml` 或 Human Gate 记录。需要读取时只指向 LDVH 根目录下的稳定入口。

## Shim 调用边界

环境 shim 调用 runtime adapter 时，应按事件类型选择稳定入口：

```bash
python3 code/runtime_adapter.py session-start --task "<task>" --target-path "<target>"
python3 code/runtime_adapter.py pre-tool-use --target-path "<target>" --operation write
python3 code/runtime_adapter.py completion-claim --target-path "<target>" --verification-evidence "<evidence>"
```

目标环境的 `SessionStart`、`PreToolUse`、`Stop` 或同类事件可以映射到 V3 `session_start`、`pre_tool_use`、`completion_claim` 邻近入口。具体名称由目标环境决定，V3 只要求映射后回到同一套保障消费语义。

pre tool use 类事件只有在目标环境真实支持阻断、payload 可验证、失败处理可复现、安装状态可检查、回滚路径明确时，才可以作为阻断型入口。否则只能输出 diagnostic，不得声明 integrated。

## 状态检查与 Stale 判定

接入前后应使用环境状态检查确认：

```bash
python3 code/environment_status.py --format text
python3 code/environment_entry_audit.py --format text
```

`environment_entry_audit.py` 当前可审计 `codex.ldvh-plugin` 样例，并能识别旧插件指向 V2 路径。Codex 只是当前可审计样例，不是环境插件总规则。

状态检查至少应覆盖：

1. 插件或扩展包是否 installed、enabled、trusted；
2. manifest 与 Hook 配置是否存在；
3. Hook 命令是否指向当前 V3 LDVH root；
4. 是否仍指向旧仓库、旧 `code/hook_adapter.py`、旧 Rules/Skill 资产或 stale V2 path；
5. runtime event 是否真实触发；
6. 失败是否按预期阻断或返回 diagnostic；
7. uninstall 后是否不再自动触发 LDVH。

只有同时具备真实触发、稳定 payload、失败处理、安装状态、回滚方式和测试证据，才可把对应环境入口升级为 integrated。文件存在、插件缓存存在、历史 trust 记录或旧路径命中，都不得声明 integrated。

## 安装与卸载边界

本文不安装、升级、禁用或卸载任何真实环境插件。

后续真实安装或升级必须先进入 Human Gate，并明确：

1. 目标环境和插件包位置；
2. 写入或修改的配置文件；
3. 是否影响用户级、工作区级或项目级入口；
4. 会触发哪些 lifecycle event；
5. 哪些事件可阻断，哪些只能 diagnostic；
6. 回滚命令和回滚后状态检查；
7. 验证命令、输入范围、残留风险和 source_refs。

卸载时只能移除或禁用 LDVH 自己写入的插件、扩展包、shim 或指针，不得静默删除原有用户 Hook、其它插件配置、用户事实源或非 LDVH 资产。卸载后必须验证环境不再自动触发 LDVH。

## Codex 样例进入条件

Codex 样例后续进入实装前，至少要补齐：

1. repo-local 或用户确认位置下的 LDVH Codex plugin package；
2. manifest 和 lifecycle Hook 配置；
3. 只调用 V3 `code/runtime_adapter.py` 的薄 shim；
4. `SessionStart`、`PreToolUse`、`Stop` 到 V3 runtime event 的 payload 映射；
5. install、status、trust、disable、uninstall 的可复现步骤；
6. stale V2 plugin 路径检测和升级前阻断；
7. status / positive / negative / rollback 测试。

旧 `ldvh@personal`、旧仓库路径、旧 `code/hook_adapter.py` 或历史 trust 记录不能复用为 V3 integrated 证据。

## 不做事项

本阶段明确不做：

1. 不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录；
2. 不生成、安装或升级真实插件包；
3. 不创建新的规则源、事实源、Human Gate 或环境入口状态；
4. 不声明 session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制。

## 下一步

后续若 Human 明确要求进入某个目标环境的实装，应先按本文生成 repo-local 插件包方案和状态检查计划，再进入 Human Gate。真实安装、升级、禁用或卸载只能在 Human 明确确认目标环境、写入位置和回滚方式后执行。
