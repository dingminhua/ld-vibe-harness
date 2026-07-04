# 环境Hook接入后验收行动模板

```yaml
ldvh_spec:
  spec_id: "31"
  spec_kind: "action_template_spec"
  title: "环境Hook接入后验收行动模板"
  status: "active"
  authority: "active"
  canonical_path: "specs/31-环境Hook接入后验收行动模板.md"
  parent_spec: "specs/06-行动模板基础规范.md"
  relation: "refines"
  positioning: "定义环境 Hook 安装检测通过后，Human 授权进入逐项验收、形成本次验收总结并复核当前验证结论的正式行动模板"
  scope: "环境 Hook 接入后验收、插件目录与 Hook trust 检查、重启后新窗口或新会话可见性探针、受控负例阻断、受控正例放行、统一安装验证和本次验收总结"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/06-行动模板基础规范.md"
    - "specs/09-测试与验证规范.md"
  related_specs:
    - "specs/07-Code确定性执行规范.md"
    - "specs/10-管辖项目配置规范.md"
    - "specs/30-LDVH安装初始化管辖项目配置行动模板.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "environment_hook_acceptance_action_template"
    - "post_install_environment_acceptance_flow"
    - "environment_hook_acceptance_test_matrix"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. 模板定位与来源"
      - "6. 验收前提与测试组"
      - "7. 逐项验收推进规则"
      - "8. Context、Scenario、Gate 与交还"
    assurance_measures: "9. 保障措施"
    verification_method: "10. 验证方法"
    human_gate: "11. Human Gate"
    stop_conditions: "12. Stop Conditions"
    next_queries: "13. 待补齐事项"
```

> 文件状态：active；本文是 V3 第二个独立正式行动模板，承接 30 安装完成后的环境 Hook 接入后验收。本文不安装、不升级、不禁用、不卸载环境插件或 Git Hook，不直接写入用户环境 Hook 系统文件，不恢复 Rules / Skill 顶层机制；本文只在 Human 明确授权进入验收后执行当次受控测试、复跑统一安装验证并交还本次验收总结。

## 1. 价值判断

本文存在的价值，是把“环境 Hook 已安装检测通过，但真实 lifecycle 还没有被用户侧验收”的情况变成当次可执行、可交还的验收流程。没有本模板时，AI 容易在 `environment_hook_integrated=false` 和“当前回合无法自证真实环境触发”之间反复绕圈；也容易反过来把插件可见、缓存存在、新对话看起来正常或用户一句笼统确认误写成 integrated。

31 的目标不是扩大安装权，而是减少验收负担：Human 只需要授权进入一组明确测试，AI 按顺序逐项判断，失败即停止，全部通过后复跑统一安装验证入口并交还本次验收总结。验收总结只代表本次运行输出，不写长期状态、不跨会话继承，也不替代后续重新检测。

## 2. 权威依据

本文承接 `specs/01-保障与衔接.md` 的环境入口、Hook 分类、插件 / 扩展包接入口径和 integrated 声明边界。

本文承接 `specs/06-行动模板基础规范.md` 的 Context、Scenario、Gate、执行、验证、回写和交还结构；承接 `specs/09-测试与验证规范.md` 的验证声明、失败阻断和 Human 验收边界。

本文承接 `specs/30-LDVH安装初始化管辖项目配置行动模板.md` 的安装检测与交还结果：30 负责安装、配置、Hook 写入方案和安装检测；31 负责安装检测通过后的真实环境 lifecycle 当次验收与当前验证结论交还。

若本文与 01、06、09、30 或 Human Gate 冲突，应回到上位规范和 Human Gate，不得由本模板自行覆盖。

## 3. 归口边界

本文归口定义环境 Hook 接入后验收行动：验收前提、逐项验收推进规则、逐项判断方式、失败停止、统一验证和本次交还格式。

本文不归口定义插件 manifest schema、插件安装器、Git Hook 安装器、管辖项目配置字段、runtime adapter 事件语义或真实用户环境配置。环境入口判定分类归 01，状态归口原则归 04，安装初始化归 30，Code 实现实践归 07 和 `code/docs/`，管辖项目配置归 10，验证声明归 09。

本文可以让 AI 在 Human 授权后执行受控测试和当前验证复核，但不得把测试组写成安装授权、环境插件升级授权、用户环境写入授权、事实源写入授权或长期验收状态写入授权。

## 4. 适用范围

本文适用于：

1. 30 已完成安装检测，统一安装验证入口显示 `install_complete=true` 且 `environment_hook_install_verified=true`，但 `environment_hook_integrated=false`；
2. 用户要求确认环境 Hook 是否真正接入、是否能在新窗口或新会话中看到可复核的 LDVH runtime 证据；
3. 用户已完成或愿意完成插件页面启用、授权 / trust、重启 App 或重载插件宿主；
4. 后续逻辑明确要求确认环境自动接入是否已在本次运行中可验证，需要可复现验收路径；
5. 环境插件安装、升级或复核后，需要把用户侧冒烟检查变成当次可复核的 lifecycle 验收。

本文不适用于：

1. 环境插件尚未安装或安装检测未通过；
2. 目标环境、插件页面、授权状态或 LDVH 本体路径不清；
3. 目标环境确认不支持 Hook、`target_environment_supported=false` 或 `unsupported_target_environment`，31 不适用；按 01 的无自动环境 Hook 边界回到 30 的手动可用安装交还；
4. 用户要求安装、升级、禁用、卸载、迁移或覆盖插件 / Git Hook；
5. 管辖项目 Git Hook 未安装、非 Git worktree 或 `LDVH-GOVERNED-PROJECTS.yaml` 配置仍阻断；
6. 用户只是询问概念、边界或为何不能声明 integrated。

## 5. 模板定位与来源

本文是 30 之后的独立正式行动模板，编号为 `31`。31 由 30 交接调用：30 安装完成交还时，若环境 Hook 安装检测通过但真实自动接入尚未在当前运行中验证，应提示 Human 是否进入 31；Human 未授权进入 31 时，不得继续做受控写入测试。

31 不重复 30 的安装向导，不重新解释 LDVH 本体路径、目标工作区配置或管辖项目选择。31 只读取 30 的交还结果、当前目标环境、插件页面结果和统一安装验证结果。

31 的执行结果只可能是：本次验收通过并交还总结、验收失败并进入诊断、Human 停止验收、或因前提不足返回 30 / 安装修复流程。31 不得把“用户还没做完测试”写成失败，也不得把“用户看到了部分提示”写成全部通过。

## 6. 验收前提与测试组

31 的目标检查只从 30 安装净变化派生：安装或升级改变了什么，31 就只验这些变化是否在当前环境可复核。不得新增与安装变化无关的验收目标，也不得把未变化的历史背景重新展开成安装流程。

安装变化目标必须先归纳成下表，再逐项推进验收：

| 安装后变化 | 31 验收目标 | 证据入口 | 不满足时 |
|---|---|---|---|
| 目标工作区配置和管辖项目关系已写入或保留 | 统一安装验证仍显示 `governed_config_ok=true`，管辖项目 Git Hook 检查有明确项目范围 | `install_verification.py --format json` 的 `governed_config` 和 `git_hooks` | 返回 30 修复配置或管辖项目范围，不进入环境 lifecycle 测试 |
| 管辖项目 Git `commit-msg` Hook 已安装或升级 | 每个管辖项目 managed hook 可执行，正例提交消息放行，反例提交消息阻断 | `git_hooks[].summary`、正反例结果、`code/governed_hook_adapter.py verify` | 返回 30 修复 Git Hook，不声明本次验收通过 |
| 目标环境插件 / 扩展包 / package 已安装或升级 | 插件可见、已安装或启用，Hook 已 review / trust 或无待处理 trust，入口指向当前 V3 shim，无 stale V2 path 或旧路径 | 插件目录或插件管理器结果、CLI `/plugins` 和 `/hooks` 输出、`environment_entry_audit.py --format text`、`environment.summary` | 停止并回到插件安装 / 授权诊断 |
| 环境入口能看见当前 LDVH runtime | 新窗口或新会话只读可见性探针返回 `status=ok`、`event=session_start`、`receipt_id` 和 `Diagnostics: none` | `human_acceptance.visible_probe_command` 或等价只读探针输出 | 停止，不写验收通过 |
| 写入前检查通过环境 Hook 被触发 | harmless scratch target 的受控负例被阻断或返回明确 blocking diagnostic | PreToolUse 负例输出、scratch target 文件状态 | 停止；若意外写入，按 Human Gate 处理清理 |
| 授权的安全动作不会被误阻断 | Human 授权的 harmless scratch target 正例被放行且无 blocking diagnostic | PreToolUse 正例或等价安全动作输出 | 停止并诊断授权、payload 或失败处理 |
| 当前安装检测结论仍可复核 | 统一安装验证仍显示 `install_complete=true`、`environment_hook_install_verified=true`，并交还当前 `environment_hook_integrated` 检测输出 | `install_verification.py --format json` 当前输出 | 停止并交还本次未验证或返回安装修复流程 |

进入 31 前必须满足以下前提：

| 前提 | 要求 | 不满足时 |
|---|---|---|
| 安装检测 | 统一安装验证入口显示 `install_complete=true`、`environment_hook_install_verified=true` | 返回 30 或安装修复流程 |
| 当前验证结论 | 当前验证输出仍为 `environment_hook_integrated=false`，需要当次 lifecycle 验收补齐证据 | 若已为 true，只做复核交还 |
| Human 授权 | Human 明确选择开始验收测试 | 停止，不执行受控测试 |
| 目标环境 | 目标环境名称、插件页面或插件管理器入口清楚 | 暂停并要求补充 |
| Hook 支持 | 目标环境支持 Hook 且环境 Hook 安装检测已经通过 | 若目标环境确认不支持 Hook、`target_environment_supported=false` 或 `unsupported_target_environment`，31 不适用；按 01 的无自动环境 Hook 边界回到 30 的手动可用安装交还 |
| 测试安全 | 受控负例和正例只使用 harmless scratch target，不写事实源、specs、用户环境或外部项目 | 暂停并重拟测试 |

验收测试组必须覆盖以下项目：

| 编号 | 测试项 | 判断标准 | 失败处理 |
|---|---|---|---|
| 1 | 插件目录与 Hook trust 检查 | Codex App Plugins 中能看到目标插件已安装或启用；CLI `/plugins` 输出能看到插件；CLI `/hooks` 没有待 review / trust 的 LDVH Hook，或 Human 已按提示完成 review / trust | 停止并回到插件安装 / 授权诊断 |
| 2 | 重启后新会话可见性探针 | 重启 App 或重载插件宿主后，在新窗口或新会话中输入可见性探针文本；结果至少包含 `status=ok`、`event=session_start`、`receipt_id` 和 `Diagnostics: none`；若目标环境能提供真实 SessionStart 触发证据，应一并回读 | 停止，不写验收通过 |
| 3 | 当前会话可见性复核 | 当前会话中需要复核时，AI 运行同等只读 LDVH 可见性探针并返回结果表；结果至少包含 `status=ok`、`event=session_start`、`receipt_id` 和 `Diagnostics: none` | 停止，不写验收通过 |
| 4 | 受控负例阻断 | 对 harmless scratch target 发起应阻断的写入类操作时，PreToolUse 负例被阻断或返回明确 blocking diagnostic | 停止；若意外写入，只记录失败并按 Human Gate 处理清理 |
| 5 | 受控正例放行 | 对 Human 授权的 harmless scratch target 或等价安全操作发起正例时，操作被放行且无 blocking diagnostic | 停止并诊断授权、payload 或失败处理 |
| 6 | 统一安装验证 | 统一安装验证入口仍显示安装检测通过，并列出 Git Hook 正反例通过 | 停止并回到安装修复流程 |
| 7 | 当前验证复核 | 统一安装验证入口仍显示安装检测通过、Git Hook 正反例通过，且未依赖历史过程输出改变结论 | 停止并交还诊断 |

受控 scratch target 必须是临时、可识别、可清理的测试路径，由实现域或运行时输出给出具体位置。不得用正式 specs、事实对象、外部用户文件、管辖项目业务文件、用户环境配置或插件系统文件做正反例写入目标。

31 的主界面必须使用简洁验收提示表达每一步，不得把 raw diagnostic 当作主问题。验收提示至少包含 `用户要做什么`、`正常表现` 和 `失败时给 AI 什么`。技术字段可以放入附录，但主界面不得裸露 raw diagnostic；`environment_hook_integrated=false` 应写成“自动接入待验收”，`target_environment_supported=false` 和 `unsupported_target_environment` 应写成“当前目标环境没有可用 Hook 接入，31 不适用，回到 30 手动可用安装交还”，`PreToolUse` 应写成“写入前检查”。具体卡片、表格、图标、编号、只读可见性探针命令和 scratch 文件名归 `code/docs/02-Environment-Plugin-Practice.md` 或运行时输出，不得在本文形成新的验收状态闭集。

31 不得要求 Human 观察没有明确入口的“重启后状态”，也不得把“重启后用户肉眼看到启动提示”作为正常标准。目标环境不稳定展示 Hook stdout、启动提示或后台诊断时，必须改用重启后的新会话只读可见性探针，让 AI 在用户可见输出中返回 `status`、`event`、`receipt_id` 和诊断结论。只读可见性探针只能证明新会话能够看见 LDVH runtime，不得替代后续受控负例阻断、受控正例放行和当前验证复核。

## 7. 逐项验收推进规则

31 必须逐项推进验收。交互输出应表达当前验收项、已完成判断和未发生事项；尚未发生事项应保持空白或不展示噪音占位。每一步只问一个判断，并使用闭集确认；如果需要用户补充截图、错误文本或插件页面结果，应作为失败后的诊断输入，不作为第三个主选项。具体验收展示表格、图标、编号和按钮文案归实现域。

主界面不得要求 Human 自行理解专业“通过 / 失败”。AI 应把问题写成“你是否看到 X”或“请贴出当前页面状态 / 错误文本”，再由 AI 根据本文判断通过、失败或暂停诊断；Human 不确定时按失败或暂停诊断处理，不继续后续步骤。编号选项只用于收集 Human 对当前观察的确认，不替代 AI 判断；按钮或选项不得写成 `1 通过` / `2 失败`，应写成类似 `1 我看到了上述正常表现` / `2 没看到或有错误，停止验收`。

每个判断必须说明本步测试目标、预期正常表现、实际观察和下一步。AI 不得连续抛出一串专业问题让 Human 自行判断；AI 必须把可自动检查的部分自己运行，把必须 Human 观察的部分压缩成一句清楚问题。

受控正反例必须在用户主界面写成具体测试动作，至少说明 harmless scratch target、预期阻断动作、预期放行动作、不会触碰的文件范围和测试后清理方式；具体 scratch 文件名归实现域或运行时输出。若目标环境无法执行等价安全动作，31 必须暂停并重新设计 harmless scratch target，不得用正式文件替代。

正常情况下，31 的交互应是逐项推进：Human 授权开始后，AI 先检查可自动读取的安装检测输出；需要 Human 操作时，只要求 Human 完成当前一步并确认是否看到了正常表现；失败时立即停止后续测试，交还失败项和诊断入口。

31 失败交还必须输出失败信息包，至少包含：目标环境名称和版本、失败步骤编号、用户看到的插件页面结果或错误文本、`install_verification.py --format json` 完整输出、`environment_entry_audit.py --format text` 输出、是否发生实际写入、scratch target 路径和文件状态。缺少任一项时写“未取得”，不得用聊天印象替代。

### 本次验收最终交还

31 收尾必须有独立的最终交还，不得直接复用统一安装验证入口的用户下一步提示，也不得在本次验收通过后再次提示“进入 31”。最终交还必须交还：通过项、失败项、未验证项、本次自动接入验收判断、当前安装检测复核摘要、不可跨会话继承说明、推荐行动和 source_refs。若证据不足，写本次未验证，不强行转换。

最终交还的推荐行动必须只列用户接下来要做的具体动作，不列“不建议”或反向提醒。需要用户在目标环境输入内容时，必须给出可直接复制到输入框的文本；不得只写“让 AI 运行只读可见性探针”“授权执行受控正反例”等抽象动作。需要用户观察插件页面时，必须说明要打开哪个页面、看哪些文字或状态、把什么结果发回。需要受控正反例时，必须说明 scratch target、预期阻断动作、预期放行动作和用户要在输入框输入的测试请求。

31 的最终交还不得把 `environment_hook_integrated=false` 作为用户主结论或“状态”展示。该字段只允许出现在技术附录或安装检测复核摘要中，用于说明当前统一安装验证入口尚未形成长期 integrated 证据；31 的主结论只能表达本次验收通过、本次验收失败或本次未验证。

31 最终交还不得写成“技术检查通过，但 `environment_hook_integrated=false`，所以仍是自动接入待验收”或等价句式。若技术检查通过但缺少插件目录、CLI `/plugins`、CLI `/hooks`、Hook trust 或重启后新会话可见性探针证据，主结论必须写成“本次未验证”，并在未验证项中逐项列出缺少的用户侧证据。统一安装验证输出中的 `User-facing status`、`Hook status blocks`、`下一步` 或“可进入 31”提示不得复制到 31 最终交还正文。

31 的最终交还必须把“技术检查结果”和“用户侧验收缺口”分开展示：技术检查结果只说明已通过的命令、探针和受控 scratch 测试；用户侧验收缺口只说明还缺插件目录或 `/plugins` 结果、`/hooks` trust 结果、重启后新会话探针或真实 lifecycle 触发证据中的哪几项。推荐行动必须紧跟缺口逐项给出，不得让用户自行从技术状态推断下一步。

最终交还结论只能使用 `本次验收通过`、`本次验收失败` 或 `本次未验证`；统一安装验证入口只作为技术复核来源，其 `下一步`、`user_next_steps` 或进入 31 的提示不得作为 31 的最终行动建议。`--require-environment-integrated` 不是 31 收尾通过条件，只能用于当前审计已经能直接证明环境自动接入时的严格技术检查。

## 8. Context、Scenario、Gate 与交还

| 结构 | 最小要求 |
|---|---|
| Context | 读取用户目标、目标环境、30 交还结果、安装变化目标、统一安装验证入口当前输出、`environment_hook_integrated=false` 当前检测输出、插件页面或插件管理器入口、Human 授权状态和 source_refs，并回指 `specs/01-保障与衔接.md`、`specs/06-行动模板基础规范.md`、`specs/09-测试与验证规范.md`、`specs/30-LDVH安装初始化管辖项目配置行动模板.md` 和本文。 |
| Scenario | 30 安装检测通过后进入环境 Hook 接入后验收、用户要求验证真实 lifecycle、用户完成插件授权后要求验收、需要当次 lifecycle 冒烟结论、或要求只回答 01/06/09/30/31 边界时适用。 |
| Gate | 开始验收、执行受控负例阻断测试、执行受控正例放行测试、接受插件目录或 `/plugins` 结果、接受 `/hooks` trust 结果、声明本次自动接入验收判断、处理意外 scratch 写入或清理测试文件，均必须有 Human Gate 或明确用户授权。 |
| 执行 | 先把 30 安装净变化归纳为安装变化目标，再逐项推进验收，一次只判断一项，使用闭集确认；先运行只读安装检测，再要求 Human 检查插件目录或 `/plugins`、检查 `/hooks` 是否有待 review / trust、重启 App 后执行新会话只读可见性探针，再执行受控 scratch target 的负例和正例；不得安装、不得升级、不得卸载、不得修改用户环境；失败即停止，不进入后续步骤。 |
| 验证 | 按安装变化目标使用统一安装验证入口、插件目录或 `/plugins` 结果、`/hooks` trust 结果、重启后新会话只读可见性探针、SessionStart 真实触发证据（若目标环境可提供）、PreToolUse 受控负例阻断、受控正例放行和 Git Hook 正反例复核；失败、缺证或 Human 未确认时不得声明 `environment_hook_integrated`。 |
| 回写 | 本文不回写长期验收状态；验收过程输出只在当前对话交还。不得写事实源、不得写 specs。若长期溯源确有必要，必须按 03/09 分流为正式事实源或验证声明，不得写 `.ldvh-runtime` 过程输出替代。 |
| 交还 | 交还验收结果表、通过项、失败项、未验证项、本次自动接入验收判断、统一安装验证摘要、回滚或诊断入口、scratch target 处理状态、推荐行动、source_refs、残留风险和不可跨会话继承说明；阻断时交还当前停止步骤和下一步诊断建议。用户主结论不得展示 `environment_hook_integrated=false`，该字段只可作为技术附录。 |

## 9. 保障措施

| 要求 | 机制 | 触发 | 证据 | 缺口处理 |
|---|---|---|---|---|
| 验收授权要求 | 进入测试组和执行受控写入类测试前必须 Human 授权；由本文、01、06、09 保障 | 用户要求确认环境 Hook 接入后 | §6 前提表 Human 授权记录、当前测试步骤、source_refs | 未授权时停止验收，不执行受控测试 |
| 逐项判断要求 | AI 必须一次只判断一项，并给出预期、实际和判断；由本文、09、tests 保障 | 执行 31 测试组时 | §6 测试组验收结果表、通过项、失败项、未验证项 | 步骤混杂或证据不清时暂停，回到当前步骤重新判断 |
| 安全测试目标要求 | 正反例只能使用 harmless scratch target，不得触碰 specs、事实源、用户环境或业务文件；由本文、07、09 保障 | 执行受控写入类测试时 | §6 scratch target 路径、写入前检查输出、测试后文件状态 | 目标不安全时停止测试，重新设计 harmless scratch target |
| integrated 声明要求 | 只有当前安装检测、插件证据、真实触发、payload 和失败处理证据都可复核时，才可在本次交还中声明 integrated；由本文、01、30、Code audit、tests 保障 | `environment_hook_integrated=false` 需要验收时 | §6 测试组第 1-5 项结果、统一安装验证摘要、§7 本次验收最终交还 | 缺少任一证据时交还本次未验证或本次验收失败，不写长期状态 |
| 失败停止要求 | 任一必需测试失败、缺少 Human 确认或诊断不可复现时，必须停止后续步骤；由本文、09 保障 | 测试失败或缺证时 | §7 失败信息包、失败步骤编号、诊断输出、scratch target 状态 | 停止后续测试，交还失败项和下一步诊断入口 |

## 10. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 结构检查 | 是否具备 Context、Scenario、Gate、执行、验证、回写和交还结构，并能被 Code 解析 | 不得作为正式行动模板执行 |
| 测试组检查 | 是否覆盖插件目录或 `/plugins` 结果、`/hooks` trust 结果、重启后新会话可见性探针、受控负例阻断、受控正例放行、统一安装验证和当前验证复核 | 不得交还本次验收通过 |
| Gate 检查 | 是否在开始验收、受控写入测试和声明本次自动接入验收判断前获得 Human Gate | 停止验收或回到用户确认 |
| 过程输出边界检查 | 是否避免写入或消费长期 lifecycle 过程输出，是否避免用历史过程输出改变 integrated 结论 | 停止验收并清理错误输出 |
| 边界检查 | 是否避免安装、升级、卸载、修改用户环境或写事实源 | 停止执行并回到 30 或环境修复流程 |

## 11. Human Gate

以下情况必须进入 Human Gate：

1. Human 要求从 30 交还结果进入 31 环境 Hook 接入后验收；
2. 接受插件页面启用、授权 / trust、无错误或重启后结果；
3. 执行受控负例阻断测试或受控正例放行测试；
4. 处理意外 scratch 写入、清理测试文件或接受测试残留；
5. 声明或接受本次自动接入验收通过结论；
6. 失败后继续诊断、重新执行某一步或返回 30 修复流程。

## 12. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 30 安装检测未通过，或 `environment_hook_install_verified` 不是 true；
2. 目标环境、插件页面、授权状态或 LDVH 本体路径不清；
3. 目标环境确认不支持 Hook、`target_environment_supported=false` 或 `unsupported_target_environment`，31 不适用；必须按 01 的无自动环境 Hook 边界回到 30 的手动可用安装交还，不得继续 31；
4. Human 未明确授权开始验收测试；
5. 任一必需测试失败、缺少实际观察、缺少插件页面结果、缺少新会话只读可见性探针结果，或缺少受控正反例证据；
6. 受控负例没有阻断，或受控正例没有放行；
7. 统一安装验证失败、Git Hook 正反例失败，或当前验收证据无法支撑本次自动接入验收通过结论；
8. 测试需要写入 specs、事实源、用户环境、插件系统文件、外部项目业务文件或其它非 scratch target；
9. AI 试图用聊天印象、缓存、旧 trust、插件可见、repo-local shim 直测、历史验收 JSON 或只读可见性探针替代完整 lifecycle 验收。

## 13. 待补齐事项

1. 本模板当前定义验收行动与 Code 可消费结构，不提供独立交互式 wizard CLI；若未来新增 CLI，必须完整承接本文逐项验收推进规则、Human Gate、失败停止和交还格式；
2. 不同目标环境的插件页面名称、授权 UI 和真实写入类工具行为可能不同；环境特定实现应进入 `code/docs/02-Environment-Plugin-Practice.md` 或对应插件文档，不写回本文；
3. 受控正反例测试的 scratch target 默认不进入事实源；若未来需要长期保存验收证据，应先定义事实对象或验证声明承接边界；
4. 卸载后验收、禁用后验收和跨环境批量验收仍后置；启用前必须新增模板或扩展本文并重新进入 Human Gate、Code 校验和测试闭环；
5. 本模板不得替代 30 的安装初始化配置流程，也不得绕过 01 的环境入口 integrated 声明边界。
