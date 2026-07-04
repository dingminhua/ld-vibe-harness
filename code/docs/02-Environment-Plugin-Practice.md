# 环境插件与 Hook 接入实现实践

本文是 Code 实现域文档，承接 `specs/01-保障与衔接.md` §6、`specs/04-Specs基础规范.md` 的状态归口原则、`specs/06-行动模板基础规范.md` 的行动模板父层边界、`specs/30-LDVH安装初始化管辖项目配置行动模板.md` 的 LDVH 安装初始化配置行动模板、`specs/07-Code确定性执行规范.md` 和 `specs/09-测试与验证规范.md`。本文不定义新的规则源、事实源、Human Gate、环境入口判定分类或管辖项目配置契约；若与 specs 冲突，以 specs 为准。

本文只处理环境 Hook 的插件化实现实践。Git `commit-msg` shim 和外部管辖项目 Git Hook 实践见 `code/docs/01-Git-Commit-and-Hook-Practice.md`。

## 实施边界

所有支持 Hook 的协作环境，都应通过对应 LDVH 插件、扩展包或 package 安装环境 Hook。正式接入不直接写入环境 Hook 系统文件；直接写入环境 Hook 系统文件只能作为调试、探针或迁移验证，不得作为正式接入形态。

目标环境确认不支持 Hook 时，不进入环境插件安装或 31 验收，也不称为 integrated。该情况由 01、`01.Att.03`、`01.Att.04` 和环境审计结果判定，`specs/30-LDVH安装初始化管辖项目配置行动模板.md` 只消费该判定并组织手动可用安装交还：AI 只能交还 `repo instruction`、`manual entrypoint`、`thin reference` 或外部 adapter 候选承接形态，环境接入判定分类仍使用 `manual_ready`、`available`、`deferred` 或 `absent` 等 01.Att.04 分类，验证薄引用和手动入口可用，并明确这些入口不会自动阻断写入或完成声明。

环境插件状态对用户展示时必须先翻译，不把内部字段作为主问题：

| 内部状态或事件 | 用户主界面说法 | 使用边界 |
|---|---|---|
| `unsupported_target_environment` / `target_environment_supported=false` | 当前目标环境没有可用 Hook 接入 | 回到 30 手动可用安装交还，不进入 31 |
| `environment_hook_integrated=false` 且安装检测通过 | 自动接入待验收 | 安装完成；可进入 31 lifecycle 验收 |
| 01 判定为无自动环境 Hook | 手动可用，或可用但不自动拦截 | 不安排插件页面授权、重启 App 或写入前拦截测试 |
| `PreToolUse` | 写入前检查 | 只有目标环境真实支持阻断时才可作为阻断入口 |
| `completion_claim_direct_nonblocking` | 完成声明检查只提示问题，不阻断环境关闭 | completion / Stop 类事件不得阻断环境关闭 |

面向用户的插件提示必须回答三件事：用户要打开哪个页面或入口，看到什么算正常，失败时把什么发给 AI。正常表现至少包括插件启用、已授权或无待授权、无错误、入口指向当前 V3 LDVH root / V3 shim；失败反馈至少包括截图、错误文本、插件状态和 AI 可复跑的诊断命令。

当前目标环境能力矩阵必须先给用户可理解结论，再给技术证据：

| 目标环境 | 是否支持 Hook | 是否可安装检测 | 是否可进入 31 | 失败时回到哪里 |
|---|---|---|---|---|
| Codex 样例 | 有 repo-local 样例 shim；真实环境仍需插件页面、授权和 lifecycle 证据 | 可检测 V3 shim、manifest、stale path 和 shim 正反输入 | 安装检测通过后可进入 31 | 插件安装 / 授权诊断，或 30 修复流程 |
| Trae / IDE / Agent runner | 只有实装对应插件 / 扩展包后才算支持 | 未实装前不可安装检测 | 未实装前不可进入 31 | 由 01 / 环境审计判定；支持 Hook 则先做插件方案，无可用 Hook 则回到 30 手动可用安装交还 |
| repo instruction / manual entrypoint | 不支持环境自动 Hook | 只检测薄引用或 manual CLI | 不进入 31 | 30 手动可用安装交还 |
| 未知环境 | 需先确认目标环境能力 | 不可直接检测 | 不进入 31 | 30 路径确认和环境能力确认 |

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
python3 code/environment_entry_audit.py --format text
```

`environment_entry_audit.py` 当前可审计 `codex.ldvh-plugin` 样例，并能识别旧插件指向 V2 路径。Codex 只是当前可审计样例，不是环境插件总规则。

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

只有同时具备真实触发、稳定 payload、失败处理、安装与接入证据、回滚方式和测试证据，才可把对应环境入口升级为 integrated。文件存在、插件缓存存在、历史 trust 记录或旧路径命中，都不得声明 integrated。安装检测和 integrated 证明必须分开：插件可见、必需 lifecycle Hook manifest 齐全、指向 V3 shim、旧路径诊断为 0、repo-local shim 直测通过且 Git Hook 正反例通过时，可以作为安装检测通过；真实 lifecycle 尚未回读时，只是不声明 integrated，不应单独阻断安装完成。

若后续逻辑显式要求 integrated，必须使用当次可执行的 lifecycle 验收路径，而不是让 AI 永久停在不可验证声明。Human 可以按 `specs/31-环境Hook接入后验收行动模板.md` 授权进入逐项验收；AI 逐项判断插件页面启用、重启 App、新会话只读可见性探针、授权 / trust、PreToolUse 负例阻断和正例放行。目标环境能提供真实 SessionStart lifecycle 证据时应一并回读；目标环境不稳定展示 Hook stdout 时，不得让 Human 去猜启动提示是否出现。全部通过后，AI 只能复跑 `install_verification.py` 做技术复核并交还本次验收总结；不得复用该命令输出里的“进入 31”下一步提示。本次总结不写长期状态，不替代插件页面、真实 payload 或失败处理诊断，也不得被后续对话消费为 integrated 依据。

31 只适用于目标环境支持 Hook、环境插件安装检测已经通过且 `environment_hook_integrated=false` 的情况。目标环境确认不支持 Hook 时，31 不适用；应按 01 的无自动环境 Hook 边界回到 30 手动可用安装交还，交还 01.Att.04 分类和承接形态说明。

安装审计结果必须以当前命令输出为准。当前 worktree 只有通过 `governed_hook_adapter.py verify` 证明的 `git.commit-msg` 可以作为 integrated 入口；Codex 样例插件即使命中缓存，也只能在 Hook 命令指向 `hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py` 且完成真实 lifecycle、payload、失败阻断 / 非阻断诊断、授权 / trust 和回滚证据后，才可改变 integrated 结论。若审计发现 Hook 命令仍指向旧 `code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py`，该状态属于已废弃 repo-local 插件资产路径，必须按环境插件升级或重装处理，不得写成已安装或 integrated。

## 31 验收交互实践

31 的用户主界面使用验收卡片时，卡片固定显示 `用户要做什么`、`正常表现` 和 `失败时给 AI 什么`。建议内容如下：

| 步骤 | 用户要做什么 | 正常表现 | 失败时给 AI 什么 |
|---|---|---|---|
| 1/8 验收授权 | 选择开始逐项验收 | AI 只开始本测试组，不安装、不升级、不卸载 | 停止验收即可，不需要解释技术原因 |
| 2/8 插件目录与授权检查 | 在 Codex App 打开 **Plugins**，找到 LDVH 插件；CLI 用户可输入 `/plugins` 查看插件，并输入 `/hooks` 查看是否有待 review / trust 的 Hook | 插件可见且已安装 / 已启用；`/hooks` 没有待 trust 的 LDVH Hook；如有待 trust，按提示 review / trust 后再继续 | 插件页面截图或 `/plugins`、`/hooks` 输出，包含插件名称、启用状态、待授权或错误文本 |
| 3/8 重启后新会话探针 | 重启 Codex 或重载插件宿主后，新开当前目标环境窗口或会话，在输入框粘贴本文下方“可见性探针输入文本” | 结果表显示 `status=ok`、`event=session_start`、存在 `receipt_id`，且诊断为空；若目标环境同时提供真实 SessionStart 触发证据，应一并展示 | 新会话里 AI 的完整输出、无法运行的错误文本 |
| 4/8 当前会话可见性复核 | 在当前会话需要复核时，粘贴“可见性探针输入文本”或让 AI 运行同等只读命令 | 结果表显示 `status=ok`、`event=session_start`、存在 `receipt_id`，且诊断为空 | AI 的完整输出、无法运行的错误文本 |
| 5/8 受控负例阻断 | 在输入框粘贴本文下方“受控负例输入文本” | 写入前检查阻断，scratch 文件未被错误写入 | AI 输出、scratch 路径、文件是否被写入 |
| 6/8 受控正例放行 | 在输入框粘贴本文下方“受控正例输入文本” | 操作成功，没有 blocking diagnostic | AI 输出、错误文本、scratch 路径 |
| 7/8 统一安装验证 | 等 AI 运行命令，用户只看结论 | `install_verification.py` 显示安装检测通过，Git Hook 正反例仍通过 | AI 输出摘要或完整命令输出 |
| 8/8 本次验收总结 | 确认 AI 交还本次验收结果和推荐行动 | 通过项、失败项、未验证项、本次验收通过 / 失败 / 未验证、推荐行动和不可跨会话继承说明完整；不再提示进入 31；用户主结论不展示 `environment_hook_integrated=false` | 总结遗漏项、复核命令输出 |

逐项验收表可以用 `👉` 标记当前步骤，用 `✅` 标记已完成步骤；尚未发生的步骤保持空白。选项建议只保留 `1 我看到了上述正常表现` 和 `2 没看到或有错误，停止验收`，失败后的截图、错误文本或插件页面结果作为诊断输入，不作为第三个主选项。Human 不选择“通过 / 失败”；AI 根据用户观察和本文规则判断通过、失败或暂停诊断。

31 新会话可见性探针优先使用以下只读命令模板；运行时用当前 LDVH 本体路径和目标路径替换占位符：

```bash
python3 code/runtime_adapter.py session-start \
  --root "<ldvh-root>" \
  --session-id "31-visible-probe" \
  --target-path "<target-path>" \
  --task "LDVH 31 visible probe" \
  --operation read \
  --trigger-source "manual.31-visible-probe" \
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

该探针只证明新会话里 LDVH runtime 可见，不证明目标环境 lifecycle 已自动 integrated。integrated 仍必须通过插件目录与授权检查、重启后的新会话探针、受控负例阻断、受控正例放行和统一安装验证在本次验收中闭合。31 收尾不得使用 `install_verification.py --require-environment-integrated` 作为通过条件；该参数只用于当前审计已经能直接证明环境自动接入时的严格技术检查。

受控正反例默认使用 `.ldvh-runtime/acceptance-probe/` 下的 scratch 文件。默认动作是：先尝试写 `.ldvh-runtime/acceptance-probe/blocked.txt`，预期被写入前检查拦截；再写 `.ldvh-runtime/acceptance-probe/allowed.txt`，预期放行；不碰 specs、事实源或业务文件；测试后清理 scratch 文件。目标环境无法执行等价安全动作时，先重新设计 harmless scratch target。

用户操作必须给出可复制输入文本。默认输入文本如下；运行时替换 `<ldvh-root>`、`<governance-root>` 和 `<target-path>`：

```text
请继续 LDVH 31 新会话可见性探针。只读运行下面命令，并把完整输出原样返回：

python3 <ldvh-root>/code/runtime_adapter.py session-start --root <ldvh-root> --config-root <governance-root> --session-id 31-visible-probe --target-path <target-path> --task "LDVH 31 visible probe" --operation read --trigger-source manual.31-visible-probe --format text
```

```text
请继续 LDVH 31 受控负例阻断测试。scratch target 使用 <target-path>/.ldvh-runtime/acceptance-probe/blocked.txt。请只运行写入前检查，不要实际写文件；预期结果是阻断，并确认 blocked.txt 没有被创建。
```

```text
请继续 LDVH 31 受控正例放行测试。scratch target 使用 <target-path>/.ldvh-runtime/acceptance-probe/allowed.txt。请先确认已读取 00/01/02 和 31 的必读依据，再只运行写入前检查；预期结果是放行，诊断为空，不需要实际写文件。
```

31 最终交还必须包含“推荐行动”，但只写下一步动作，不写“不建议”。按结论推荐：

| 最终结论 | 推荐行动写法 |
|---|---|
| 本次验收通过 | 本次可结束；后续如果重启、升级插件或切换工作区，再重新运行 31 当前验收。 |
| 本次验收失败 | 停在失败步骤；按失败信息包补充插件页面结果、错误文本、scratch target 状态或命令输出，再从失败步骤重试。 |
| 本次未验证 | 补齐缺失用户侧证据；优先给出插件目录与 `/hooks` 检查、重启后新会话输入文本、受控负例输入文本和受控正例输入文本。 |
 
`environment_hook_integrated` 是统一安装验证入口的技术字段，不是 31 的最终状态。31 主结论只使用本次验收通过、本次验收失败或本次未验证；若需要保留该字段，只放技术附录，写作“统一安装验证当前仍未形成长期 integrated 证据”，不得作为用户主结论。

技术检查全部通过但缺少用户侧证据时，31 收尾推荐使用下面的结构，不得把统一安装验证的 `User-facing status`、`Hook status blocks`、`下一步` 或“自动接入待验收”复制进最终交还：

```text
本次结论：本次未验证

已通过：
- 安装验证通过。
- 3 个管辖项目 Git Hook 正反例通过。
- 环境插件直测通过。
- 31 可见性探针通过。
- 受控负例按预期阻断，scratch 文件未创建。
- 受控正例按预期放行，scratch 文件未创建。

未验证：
- 还没有看到 Codex 插件目录或 `/plugins` 输出显示 LDVH 插件已安装 / 已启用。
- 还没有看到 `/hooks` 输出确认没有待 review / trust 的 LDVH Hook。
- 还没有看到重启 Codex 后新会话里的可见性探针输出。

推荐行动：
1. 在 Codex App 打开 **Plugins**，找到 LDVH 插件，把插件名称和是否已安装 / 已启用发回来；CLI 用户可输入 `/plugins`，把 LDVH 插件那一行发回来。
2. CLI 用户输入 `/hooks`，把是否存在待 review / trust 的 LDVH Hook 发回来；如果没有 CLI 入口，本项写“未取得”。
3. 重启 Codex 或重载插件宿主后，新开一个 Codex 会话，在输入框粘贴“可见性探针输入文本”，把新会话里的完整输出发回来。
```

如果可见性探针、受控负例和受控正例都已经在本次同一会话内通过，但插件目录、`/hooks` 或重启后新会话探针仍缺失，推荐行动只列缺失的用户侧观察项；不要要求用户重复已通过的命令。

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

真实 Codex / IDE / Agent 环境插件的 positive、negative、status、disable、uninstall 和 rollback 测试仍 gated。安装完成前至少应能测试插件状态、Hook 配置指向 V3 shim、直接 shim 正反输入；若当前回合不能触发真实 lifecycle，必须交还用户侧冒烟检查步骤，不得声明 integrated。用户侧冒烟应优先进入 31 的逐项验收测试组；全部通过后，AI 只交还本次验收总结和复核命令输出，不写 `.ldvh-runtime` 过程状态，也不得让历史过程输出改变 integrated 结论。没有 Human 明确确认目标环境、写入位置、触发点、payload、失败处理和回滚方式前，不得写入用户环境或修改外部项目 Hook。

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
