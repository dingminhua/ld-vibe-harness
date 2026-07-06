# 环境插件与 Hook 接入实现实践

本文是 Code 实现域文档，承接 `specs/01-保障与衔接.md` §6、`specs/04-Specs基础规范.md` 的状态归口原则、`specs/10-安装与配置规范.md` 的安装与配置机器契约、`specs/06-行动模板基础规范.md` 的行动模板父层边界、`specs/30-安装配置与验证行动模板.md` 的 Human-facing 安装行动编排边界、`specs/07-Code确定性执行规范.md` 和 `specs/09-测试与验证规范.md`。本文不定义新的规则源、事实源、Human Gate、环境入口判定分类或管辖项目配置契约；若与 specs 冲突，以 specs 为准。

本文只处理环境 Hook 的插件化实现实践。Git `commit-msg` shim 和外部管辖项目 Git Hook 实践见 `code/docs/01-Git-Commit-and-Hook-Practice.md`。

## 实施边界

所有支持 Hook 的协作环境，都应通过对应 LDVH 插件、扩展包或 package 安装环境 Hook。正式接入不直接写入环境 Hook 系统文件；直接写入环境 Hook 系统文件只能作为调试、探针或迁移验证，不得作为正式接入形态。

目标环境确认缺少可安装、可验证、可阻断的 AI lifecycle Hook 时，不另开独立验收模板，也不称为 integrated。该情况由 01、`01.Att.03`、`01.Att.04` 和环境审计结果判定；`specs/30-安装配置与验证行动模板.md` 只能把它作为安装阻断和后续实现缺口交还。正式 LDVH 接入必须先实装目标环境插件、扩展包、package 或 runtime adapter，并让真实 lifecycle Hook 回到 `code/runtime_adapter.py`。

环境插件状态对用户展示时必须先翻译，不把内部字段作为主问题：

| 内部状态或事件 | 用户主界面说法 | 使用边界 |
|---|---|---|
| `unsupported_target_environment` / `target_environment_supported=false` | 当前目标环境没有可安装、可验证、可阻断的 lifecycle Hook | 停止正式安装，先实现目标环境插件 / adapter |
| `environment_hook_integrated=false` 且安装检测通过 | 入口已检测，仍需断点后验证 | 由 30 引导重启 / 新会话后的 lifecycle 验证 |
| 01 判定为无 AI lifecycle Hook | 目标环境暂不属于 LDVH 支持范围 | 不生成替代安装写入；补插件 / adapter 后重新进入安装 |
| `PreToolUse` | 写入前检查 | 只有目标环境真实支持阻断时才可作为阻断入口 |
| `completion_claim_direct_nonblocking` | 完成声明检查只提示问题，不阻断环境关闭 | completion / Stop 类事件不得阻断环境关闭 |

面向用户的插件提示必须回答三件事：用户要打开哪个页面或入口，看到什么算正常，失败时把什么发给 AI。正常表现至少包括插件启用、已授权或无待授权、无错误、入口指向当前 V3 LDVH root / V3 shim；失败反馈至少包括截图、错误文本、插件状态和 AI 可复跑的诊断命令。

当前目标环境能力矩阵必须先给用户可理解结论，再给技术证据：

| 目标环境 | 是否支持 Hook | 是否可安装检测 | 断点后验证方式 | 失败时回到哪里 |
|---|---|---|---|---|
| Codex 样例 | 有 repo-local 样例 shim；真实环境仍需插件页面、授权和 lifecycle 证据 | 可检测 V3 shim、manifest、stale path 和 shim 正反输入 | 按 30 恢复入口运行新会话探针和真实工作流检查 | 插件安装 / 授权诊断，或 30 修复流程 |
| Trae / IDE / Agent runner | 只有实装对应插件 / 扩展包后才算支持 | 未实装前不可安装检测 | 通过插件 lifecycle Hook 汇聚到 runtime adapter receipt | 由 01 / 环境审计判定并回到 30 修复流程 |
| 未知环境 | 需先确认目标环境能力 | 不可直接检测 | 先确认是否存在可安装、可验证、可阻断的 lifecycle Hook | 30 路径确认和环境能力确认 |

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
| 证据检查 | 可判断 installed、enabled、trusted、target path、LDVH root 和 stale V2 path |
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

pre tool use 类事件只有在目标环境真实支持阻断、payload 可验证、失败处理可复现、安装与接入证据可检查、回滚路径明确时，才可以作为阻断型入口。否则只能输出 diagnostic，不得声明 integrated。

## 证据检查与 Stale 判定

接入前后应使用环境证据检查确认：

```bash
python3 code/environment_status.py --format text
python3 code/environment_entry_audit.py --environment-name <目标环境名> --format text
```

`environment_entry_audit.py` 按目标环境生成候选项；只有 `--environment-name Codex` 时才审计 `codex.ldvh-plugin` 样例并识别旧插件指向 V2 路径。其它目标环境必须显示自身插件、扩展包或 adapter 的缺口，不得复用 Codex 插件状态。

证据检查至少应覆盖：

1. 插件或扩展包是否 installed、enabled、trusted；
2. 插件页面、扩展页面或插件管理器是否能显示该条目，且无待处理授权或错误；
3. manifest 与 Hook 配置是否存在；
4. Hook 命令是否指向当前 V3 LDVH root；
5. 是否仍指向旧仓库、旧 `code/hook_adapter.py`、旧 Rules/Skill 资产或 stale V2 path；
6. 重启 App 或重载插件宿主后状态是否保持；
7. runtime event 是否真实触发；
8. 失败是否按预期阻断或返回 diagnostic；
9. uninstall 后是否不再自动触发 LDVH。

当次 integrated 验收建议按以下清单收集证据：

| 验收项 | 正常证据 | 不能替代它的内容 |
|---|---|---|
| 安装启用 | 插件 / 扩展包 / package 已启用、已授权或无待授权，Hook 命令指向当前 V3 shim 或 `runtime_adapter.py` | repo-local 样例包存在 |
| `SessionStart` | 新会话、恢复或等价事件自动输出 `event=session_start`、read_plan 或 receipt | 手动运行 `runtime_adapter.py session-start` |
| `PreToolUse` 负例 | 写入类工具在缺 read_plan、target unknown 或等价负例时被目标环境 deny / 阻断 | 只打印 warning 或命令行负例 |
| `PreToolUse` 正例 | 已满足 target 和 read_plan 条件的正例或只读动作不被误阻断 | 只测试负例 |
| `Stop` / completion | Stop 或完成邻近事件输出 completion check、验证缺口或残留风险提示，且不阻断环境正常停止 | 完成后手动运行检查命令 |
| payload / target | payload 可回读 event、session、cwd、target、operation、acknowledged_paths 或 verification_evidence，缺字段有 diagnostic | 用户口头说明目标 |
| 回滚 | 禁用或卸载后新会话 / 等价触发不再进入 LDVH，cache 已清理或过期不采信 | 删除 repo-local 样例文件 |

只有当次验收同时具备真实触发、稳定 payload、失败处理、安装与接入证据、回滚方式和测试证据，才可把对应环境入口判定为 integrated。该结论只对当次目标环境、LDVH root、插件配置和触发证据成立，不写成长期安装状态。文件存在、插件缓存存在、历史 trust 记录或旧路径命中，都不得声明 integrated。安装检测和 integrated 证明必须分开：插件可见、必需 lifecycle Hook manifest 齐全、指向 V3 shim、旧路径诊断为 0、repo-local shim 直测通过且 Git Hook 正反例通过时，可以作为安装检测通过；真实 lifecycle 尚未回读时，只是不声明 integrated，不应单独阻断安装完成。

跨环境不能直接验收真实 lifecycle。Codex 会话只能审计 WorkBuddy 样例包或 WorkBuddy 回传的当次证据，不能自行判定 WorkBuddy integrated；WorkBuddy 会话也不能替代 Codex 真实触发验收。目标环境不可在当前环境触发时，应输出不可在当前环境验收、候选资产存在或缺失的结论。

若后续逻辑显式要求 integrated，必须使用当次可执行的 lifecycle 验证路径，而不是让 AI 永久停在不可验证声明。30 负责交还恢复入口语、可复制新会话探针、真实工作流检查和失败信息包；AI 逐项判断插件页面启用、重启 App、新会话只读可见性探针、授权 / trust、PreToolUse 负例阻断和正例放行。目标环境能提供真实 SessionStart lifecycle 证据时应一并回读；目标环境不稳定展示 Hook stdout 时，不得让 Human 去猜启动提示是否出现。全部通过后，AI 复跑 `install_verification.py` 做技术复核并交还本次验证总结；不得复用命令输出里的旧式下一步提示。验证总结不写长期状态，不替代插件页面、真实 payload 或失败处理诊断。

断点后 lifecycle 验证只适用于已实装目标环境插件、扩展包、package 或 runtime adapter 的路径。目标环境暂不支持可阻断 lifecycle Hook 时，不进入正式安装验证；AI 应交还“先实现目标环境 Hook adapter”的缺口，再重新运行安装向导。

安装审计结果必须以当前命令输出为准。当前 worktree 只有通过 `governed_hook_adapter.py verify` 证明的 `git.commit-msg` 可以作为 integrated 入口；Codex 样例插件即使命中缓存，也只能在 Hook 命令指向 `hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py` 且完成真实 lifecycle、payload、失败阻断 / 非阻断诊断、授权 / trust 和回滚证据后，才可改变 integrated 结论。若审计发现 Hook 命令仍指向旧 `code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py`，该状态属于已废弃 repo-local 插件资产路径，必须按环境插件升级或重装处理，不得写成已安装或 integrated。

## 断点后 lifecycle 验证引导

30 写入完成后，用户可能需要重启 App、重载插件宿主或新开会话。该断点不是独立行动模板，而是 30 验证的一部分。用户回来后，AI 应先复跑只读 `install_verification.py` 重建上下文，再按下面的卡片逐项引导。

| 步骤 | 用户要做什么 | 正常表现 | 失败时给 AI 什么 |
|---|---|---|---|
| 1/4 恢复入口 | 在新会话粘贴“我重启了，继续 LDVH lifecycle 验证” | AI 识别为继续 30 验证，不重新启动安装向导 | 当前会话完整输出 |
| 2/4 新会话可见性探针 | 让 AI 运行“可见性探针输入文本” | 输出包含 `status=ok`、`event=session_start`、`receipt_id` 和 `Diagnostics: none` | 完整命令输出或错误文本 |
| 3/4 真实工作流检查 | 按引导逐项触发 Git `commit-msg` 正反例、`SessionStart`、`PreToolUse` 负例、`PreToolUse` 正例或只读放行、`Stop` / completion 检查；需要 scratch target 时明确路径和清理 | 入口真实触发；负例被阻断，正例放行；completion 检查可见且不阻断环境正常停止；scratch 文件状态符合预期 | AI 输出、Hook 输出、scratch 路径、文件状态、completion 输出 |
| 4/4 验证总结 | AI 复跑统一安装验证并交还结论 | 本次验证通过 / 失败 / 未验证、推荐行动和残留风险清楚 | 总结遗漏项、复核命令输出 |

逐项验证可以用 `👉` 标记当前步骤，用 `✅` 标记已完成步骤；尚未发生的步骤保持空白。选项建议只保留 `1 我看到了上述正常表现` 和 `2 没看到或有错误，停止验证`。Human 不选择“通过 / 失败”；AI 根据用户观察和本文规则判断通过、失败或暂停诊断。

新会话可见性探针优先使用以下只读命令模板；运行时用当前 LDVH 本体路径和目标路径替换占位符：

```bash
python3 code/runtime_adapter.py session-start \
  --root "<ldvh-root>" \
  --session-id "lifecycle-verify-probe" \
  --target-path "<target-path>" \
  --task "LDVH lifecycle verification probe" \
  --operation read \
  --trigger-source "hook.lifecycle-verify-probe" \
  --format text
```

正常输出至少应包含：

```text
LDVH v3 runtime adapter
- status: ok
- event: session_start
- receipt_id: <receipt-id>
Diagnostics: none
```

该探针证明新会话里 LDVH runtime 可见；完整 lifecycle 验证还需要真实工作流检查和统一安装验证复核。受控正反例默认使用 `.ldvh-runtime/acceptance-probe/` 下的 scratch 文件。默认动作是：先只运行写入前检查验证 `.ldvh-runtime/acceptance-probe/blocked.txt` 预期阻断；再验证 `.ldvh-runtime/acceptance-probe/allowed.txt` 预期放行；不碰 specs、事实源或业务文件；测试后按 Human Gate 清理 scratch 文件。目标环境无法执行等价安全动作时，先重新设计 harmless scratch target。

用户操作必须给出可复制输入文本。默认输入文本如下；运行时替换 `<ldvh-root>`、`<governance-root>` 和 `<target-path>`：

```text
我重启了，继续 LDVH lifecycle 验证。请只读运行下面命令，并把完整输出原样返回：

python3 <ldvh-root>/code/runtime_adapter.py session-start --root <ldvh-root> --config-root <governance-root> --session-id lifecycle-verify-probe --target-path <target-path> --task "LDVH lifecycle verification probe" --operation read --trigger-source hook.lifecycle-verify-probe --format text
```

```text
请继续 LDVH 受控负例阻断测试。scratch target 使用 <target-path>/.ldvh-runtime/acceptance-probe/blocked.txt。请只运行写入前检查，不要实际写文件；预期结果是阻断，并确认 blocked.txt 没有被创建。
```

```text
请继续 LDVH 受控正例放行测试。scratch target 使用 <target-path>/.ldvh-runtime/acceptance-probe/allowed.txt。请先确认已读取 00/01/02 和 30 的必读依据，再只运行写入前检查；预期结果是放行，诊断为空，不需要实际写文件。
```

最终交还只列用户接下来要做的具体动作：本次验证通过则可结束；失败则停在失败步骤并补充失败信息包；未验证则补齐缺失的插件页面、新会话探针或真实工作流证据。

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
8. 回滚命令和回滚后证据检查；
9. 验证命令、输入范围、正常判断标准、残留风险和 source_refs。

卸载时只能移除或禁用 LDVH 自己写入的插件、扩展包、shim 或指针，不得静默删除原有用户 Hook、其它插件配置、用户事实源或非 LDVH 资产。卸载后必须验证环境不再自动触发 LDVH。

## 仓库内正反测试

当前可在仓库内验证的插件样例测试覆盖：

| 场景 | 仓库内验证 | 后置条件 |
|---|---|---|
| payload 透传 | 对 `hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py` 传入 Codex-like JSON，检查 `session_id`、target、task、`trigger_source=codex.ldvh-plugin` 进入 `runtime_adapter.py` | 不证明 Codex 已加载插件 |
| PreToolUse 阻断 | PreToolUse 缺少 `acknowledged_paths` 时 shim 返回 runtime adapter 非零退出并保留 blocking diagnostic | 真实环境还需验证该退出码确实阻断写入工具 |
| completion 非阻断诊断 | Stop / completion payload 缺少 `verification_evidence` 时输出 blocking diagnostic，但 shim 对 Stop 返回 0，避免样例包阻断环境关闭 | 真实环境接入前需确认 Stop 输出可见性和失败处理 |
| stale V2 path | `environment_entry_audit.py` 识别指向旧 `ld-vibe-harness` / `hook_adapter.py` / `hook_dispatch.py` 的 Codex plugin 命令，判定保持 `available` 而不是 integrated | 修复必须走插件升级 / reinstall Human Gate |
| install / uninstall / rollback | `governed_hook_adapter.py` 与 `install_git_hooks.py` 的临时 repo 测试覆盖 Git hook shim 安装、Human Gate 缺失阻断、卸载后状态回读 | 不等价于安装用户级环境插件 |

真实 Codex / IDE / Agent 环境插件的 positive、negative、status、disable、uninstall 和 rollback 测试仍 gated。安装完成前至少应能测试插件状态、Hook 配置指向 V3 shim、直接 shim 正反输入；若当前回合不能触发真实 lifecycle，必须交还用户侧冒烟检查步骤，不得声明 integrated。用户侧冒烟应按 30 的断点后 lifecycle 验证引导逐项执行；全部通过后，AI 只交还本次验证总结和复核命令输出，不写 `.ldvh-runtime` 过程状态，也不得让历史过程输出改变 integrated 结论。没有 Human 明确确认目标环境、写入位置、触发点、payload、失败处理和回滚方式前，不得写入用户环境或修改外部项目 Hook。

安装收尾可以使用统一只读验证入口：

```bash
python3 code/install_verification.py --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>" --environment-name "<当前 AI 运行环境名称>"
```

该命令会先使用 specs 10 的配置校验读取 `LDVH-GOVERNED-PROJECTS.yaml`，再验证每个管辖项目 Git `commit-msg` Hook 的 status、managed marker、正例放行和反例阻断。目标环境为 Codex 时，它会执行 repo-local Codex 样例 shim 的 SessionStart、PreToolUse 和 Stop 直测，并把插件页面、重启 App、授权 / trust、新会话只读可见性探针、真实 lifecycle、payload、失败处理和卸载后自动触发证据列为用户侧冒烟检查，同时输出正常判断标准。目标环境不是 Codex 时，该命令只能输出目标环境插件待实装 / 待验收结论，不运行 Codex 样例 shim，也不得暗示 Trae、IDE 或 Agent runner 已被支持。该命令不会安装、升级、禁用、卸载或写入用户环境；它输出 `complete` 且 `environment_hook_integrated=false` 时表示安装检测已通过但真实环境接入仍不能声明 integrated；它输出 `environment_hook_integrated=true` 时表示当前检测已具备环境 integrated 证据；它输出 `review_required` 时表示环境插件缺失、未启用、未指向 V3 shim 或目标环境没有当前验收入口支持。

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
3. 不创建新的规则源、事实源、Human Gate 或环境入口判定事实；
4. 不声明 session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制。

## 下一步

后续若 Human 明确要求进入某个目标环境的实装，应先按本文生成 repo-local 插件包方案和证据检查计划，再进入 Human Gate。真实安装、升级、禁用或卸载只能在 Human 明确确认目标环境、写入位置和回滚方式后执行。
