# 环境插件与 Hook 接入实现实践

本文是 Code 实现域文档，承接 `specs/01-保障与衔接.md` §6、`specs/06-行动模板基础规范.md` 的行动模板父层边界、`specs/30-LDVH安装初始化管辖项目配置行动模板.md` 的 LDVH 安装初始化配置行动模板、`specs/07-Code确定性执行规范.md` 和 `specs/09-测试与验证规范.md`。本文不定义新的规则源、事实源、Human Gate、环境入口状态闭集或管辖项目配置契约；若与 specs 冲突，以 specs 为准。

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
| 展示资产 | manifest 引用的 icon / logo / composerIcon 等资产必须在插件包内存在并可被静态校验 |
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
2. 插件页面、扩展页面或插件管理器是否能显示该条目，且无待处理授权或错误；
3. manifest 与 Hook 配置是否存在；
4. Hook 命令是否指向当前 V3 LDVH root；
5. 是否仍指向旧仓库、旧 `code/hook_adapter.py`、旧 Rules/Skill 资产或 stale V2 path；
6. 重启 App 或重载插件宿主后状态是否保持；
7. runtime event 是否真实触发；
8. 失败是否按预期阻断或返回 diagnostic；
9. uninstall 后是否不再自动触发 LDVH。

只有同时具备真实触发、稳定 payload、失败处理、安装状态、回滚方式和测试证据，才可把对应环境入口升级为 integrated。文件存在、插件缓存存在、历史 trust 记录或旧路径命中，都不得声明 integrated。安装检测和 integrated 证明必须分开：插件可见、必需 lifecycle Hook manifest 齐全、指向 V3 shim、旧路径诊断为 0、repo-local shim 直测通过且 Git Hook 正反例通过时，可以作为安装检测通过；真实 lifecycle 尚未回读时，只是不声明 integrated，不应单独阻断安装完成。

若后续逻辑显式要求 integrated，必须使用可关闭的 lifecycle 验收路径，而不是让 AI 永久停在不可验证声明。Human 在目标环境完成插件页面启用、重启 App、新窗口或新会话、授权 / trust、SessionStart 可见、PreToolUse 负例阻断和正例放行后，可以要求 AI 记录 lifecycle 验收。AI 只能在 Human 明确确认后运行 `environment_lifecycle_acceptance.py record --confirm-human-gate`，并复跑 `install_verification.py`；只有安装检测仍通过且 `environment_lifecycle_acceptance_valid=true` 时，才能把 `environment_hook_integrated` 转为 `true`。该记录是 repo-local 过程证据，不替代插件页面、真实 payload 或失败处理诊断。

安装审计结果必须以当前命令输出为准。当前 worktree 只有通过 `governed_hook_adapter.py verify` 证明的 `git.commit-msg` 可以作为 integrated 入口；Codex 样例插件即使命中缓存，也只能在 Hook 命令指向 `hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py` 且完成真实 lifecycle、payload、失败阻断 / 降级、授权 / trust 和回滚证据后，才可改变 integrated 结论。若审计发现 Hook 命令仍指向旧 `code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py`，该状态属于已废弃 repo-local 插件资产路径，必须按环境插件升级或重装处理，不得写成已安装或 integrated。

## 安装与卸载边界

本文不安装、升级、禁用或卸载任何真实环境插件。

后续真实安装或升级必须先进入 Human Gate，并明确：

1. 目标环境和插件包位置；
2. 插件页面、扩展页面或插件管理器入口；
3. 写入或修改的配置文件；
4. 是否影响用户级、工作区级或项目级入口；
5. 会触发哪些 lifecycle event；
6. 哪些事件可阻断，哪些只能 diagnostic；
7. 重启 App 或重载插件宿主、授权 / trust 和新窗口或新会话测试要求；
8. 回滚命令和回滚后状态检查；
9. 验证命令、输入范围、正常判断标准、残留风险和 source_refs。

卸载时只能移除或禁用 LDVH 自己写入的插件、扩展包、shim 或指针，不得静默删除原有用户 Hook、其它插件配置、用户事实源或非 LDVH 资产。卸载后必须验证环境不再自动触发 LDVH。

## 仓库内正反测试

当前可在仓库内验证的插件样例测试覆盖：

| 场景 | 仓库内验证 | 后置条件 |
|---|---|---|
| payload 透传 | 对 `hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py` 传入 Codex-like JSON，检查 `session_id`、target、task、`trigger_source=codex.ldvh-plugin` 进入 `runtime_adapter.py` | 不证明 Codex 已加载插件 |
| PreToolUse 阻断 | PreToolUse 缺少 `acknowledged_paths` 时 shim 返回 runtime adapter 非零退出并保留 blocking diagnostic | 真实环境还需验证该退出码确实阻断写入工具 |
| completion 降级 | Stop / completion payload 缺少 `verification_evidence` 时输出 blocking diagnostic，但 shim 对 Stop 返回 0，避免样例包阻断环境关闭 | 真实环境接入前需确认 Stop 输出可见性和失败处理 |
| stale V2 path | `environment_entry_audit.py` 识别指向旧 `ld-vibe-harness` / `hook_adapter.py` / `hook_dispatch.py` 的 Codex plugin 命令，状态保持 `available` 而不是 integrated | 修复必须走插件升级 / reinstall Human Gate |
| install / uninstall / rollback | `governed_hook_adapter.py` 与 `install_git_hooks.py` 的临时 repo 测试覆盖 Git hook shim 安装、Human Gate 缺失阻断、卸载后状态回读 | 不等价于安装用户级环境插件 |

真实 Codex / IDE / Agent 环境插件的 positive、negative、status、disable、uninstall 和 rollback 测试仍 gated。安装完成前至少应能测试插件状态、Hook 配置指向 V3 shim、直接 shim 正反输入；若当前回合不能触发真实 lifecycle，必须记录用户侧冒烟检查步骤，不得声明 integrated。用户侧冒烟通过后，AI 可在 Human Gate 下写入 `.ldvh-runtime/environment-lifecycle-acceptance.json` 或指定的验收记录路径，并由 `install_verification.py` 读取为 `environment_lifecycle_acceptance_valid`；验收记录缺失、环境名称不匹配或 Human Gate 缺失时不得转换 integrated。没有 Human 明确确认目标环境、写入位置、触发点、payload、失败处理和回滚方式前，不得写入用户环境或修改外部项目 Hook。

安装收尾可以使用统一只读验证入口：

```bash
python3 code/install_verification.py --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>" --environment-name "<当前 AI 运行环境名称>"
```

该命令会先使用 specs 10 的配置校验读取 `LDVH-GOVERNED-PROJECTS.yaml`，再验证每个管辖项目 Git `commit-msg` Hook 的 status、managed marker、正例放行和反例阻断。目标环境为 Codex 时，它会执行 repo-local Codex 样例 shim 的 SessionStart、PreToolUse 和 Stop 直测，并把插件页面、重启 App、授权 / trust、新窗口或新会话、真实 lifecycle、payload、失败处理和卸载后自动触发状态列为用户侧冒烟检查，同时输出正常判断标准。目标环境不是 Codex 时，该命令只能输出目标环境插件待实装 / 待验收状态，不运行 Codex 样例 shim，也不得暗示 Trae、IDE 或 Agent runner 已被支持。该命令不会安装、升级、禁用、卸载或写入用户环境；它输出 `complete` 且 `environment_hook_integrated=false` 时表示安装检测已通过但真实环境接入仍不能声明 integrated；它输出 `environment_hook_integrated=true` 和 `environment_lifecycle_acceptance_valid=true` 时表示安装检测与 Human-confirmed lifecycle 验收都通过；它输出 `review_required` 时表示环境插件缺失、未启用、未指向 V3 shim 或目标环境没有当前验收入口支持。

## Codex 样例进入条件

Codex 样例后续进入实装前，至少要补齐：

1. `hooks/environment-plugins/` 下的 repo-local LDVH Codex plugin package，或用户确认位置下的目标环境插件包；
2. manifest 和 lifecycle Hook 配置；
3. manifest 实际引用的插件展示图标资产；
4. 只调用 V3 `code/runtime_adapter.py` 的薄 shim；
5. `SessionStart`、`PreToolUse`、`Stop` 到 V3 runtime event 的 payload 映射；
6. install、status、trust、disable、uninstall 的可复现步骤；
7. stale V2 plugin 路径检测和升级前阻断；
8. status / positive / negative / rollback 测试。

旧 `ldvh@personal`、旧仓库路径、旧 `code/hook_adapter.py` 或历史 trust 记录不能复用为 V3 integrated 证据。

根目录 `icons/` 只作为 LDVH 通用图标资产来源和历史吸收结果；它不是环境插件安装源。实际 manifest 引用的展示资产必须位于对应插件包目录内，例如 `hooks/environment-plugins/codex-ldvh-v3/assets/`，并由静态测试确认存在和尺寸有效。

## 不做事项

本阶段明确不做：

1. 不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录；
2. 不生成、安装或升级真实插件包；
3. 不创建新的规则源、事实源、Human Gate 或环境入口状态；
4. 不声明 session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制。

## 下一步

后续若 Human 明确要求进入某个目标环境的实装，应先按本文生成 repo-local 插件包方案和状态检查计划，再进入 Human Gate。真实安装、升级、禁用或卸载只能在 Human 明确确认目标环境、写入位置和回滚方式后执行。
