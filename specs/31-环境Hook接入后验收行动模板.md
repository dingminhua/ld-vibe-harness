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
  relation: "action_template_member"
  positioning: "定义环境 Hook 安装检测通过后，Human 授权进入逐项验收、记录 lifecycle 验收并复核 integrated 结论的正式行动模板"
  scope: "环境 Hook 接入后验收、插件页面状态确认、重启后状态确认、新窗口或新会话触发确认、受控负例阻断、受控正例放行、lifecycle 验收记录和 integrated 复核"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/06-行动模板基础规范.md"
    - "specs/09-测试与验证规范.md"
  related_specs:
    - "specs/07-Code确定性执行规范.md"
    - "specs/10-管辖项目配置规范.md"
    - "specs/30-LDVH安装初始化管辖项目配置行动模板.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "environment_hook_acceptance_action_template"
    - "post_install_lifecycle_acceptance_flow"
    - "environment_hook_acceptance_test_matrix"
    - "lifecycle_acceptance_record_handoff"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. 模板定位与来源"
      - "6. 验收前提与测试组"
      - "7. 验收测试组状态机"
      - "8. Context、Scenario、Gate 与交还"
    assurance_measures: "9. 保障措施"
    verification_method: "10. 验证方法"
    human_gate: "11. Human Gate"
    stop_conditions: "12. Stop Conditions"
    next_queries: "13. 待补齐事项"
```

> 文件状态：active；本文是 V3 第二个独立正式行动模板，承接 30 安装完成后的环境 Hook 接入后验收。本文不安装、不升级、不禁用、不卸载环境插件或 Git Hook，不直接写入用户环境 Hook 系统文件，不恢复 Rules / Skill 顶层机制；本文只在 Human 明确授权进入验收并逐项通过后，允许记录 repo-local lifecycle 验收并复跑统一安装验证。

## 1. 价值判断

本文存在的价值，是把“环境 Hook 已安装检测通过，但真实 lifecycle 还没有被用户侧验收”的状态变成可关闭流程。没有本模板时，AI 容易在 `environment_hook_integrated=false` 和“当前回合无法自证真实环境触发”之间反复绕圈；也容易反过来把插件可见、缓存存在、新对话看起来正常或用户一句笼统确认误写成 integrated。

31 的目标不是扩大安装权，而是减少验收负担：Human 只需要授权进入一组明确测试，AI 按顺序逐项判断，失败即停止，全部通过后才记录 lifecycle 验收并复跑 `install_verification.py`。这让 integrated 结论既不会凭空出现，也不会因为当前回合一开始不可自证而永久无法转换。

## 2. 权威依据

本文承接 `specs/01-保障与衔接.md` 的环境入口、Hook 分类、插件 / 扩展包接入口径和 integrated 声明边界。

本文承接 `specs/06-行动模板基础规范.md` 的 Context、Scenario、Gate、执行、验证、回写和交还结构；承接 `specs/09-测试与验证规范.md` 的验证声明、失败阻断和 Human 验收边界。

本文承接 `specs/30-LDVH安装初始化管辖项目配置行动模板.md` 的安装检测与交还结果：30 负责安装、配置、Hook 写入方案和安装检测；31 负责安装检测通过后的真实环境 lifecycle 验收与 integrated 复核。

若本文与 01、06、09、30 或 Human Gate 冲突，应回到上位规范和 Human Gate，不得由本模板自行覆盖。

## 3. 归口边界

本文归口定义环境 Hook 接入后验收行动：验收前提、测试组状态机、逐项判断方式、失败停止、lifecycle 验收记录、复跑统一验证和交还格式。

本文不归口定义插件 manifest schema、插件安装器、Git Hook 安装器、管辖项目配置字段、runtime adapter 事件语义或真实用户环境配置。环境入口状态闭集归 01，安装初始化归 30，Code 实现实践归 07 和 `code/docs/`，管辖项目配置归 10，验证声明归 09。

本文可以让 AI 在 Human 授权后执行受控测试和 repo-local 验收记录，但不得把测试组写成安装授权、环境插件升级授权、用户环境写入授权或事实源写入授权。

## 4. 适用范围

本文适用于：

1. 30 已完成安装检测，`install_verification.py` 显示 `install_complete=true` 且 `environment_hook_install_verified=true`，但 `environment_hook_integrated=false`；
2. 用户要求确认环境 Hook 是否真正接入、是否能从新窗口或新会话自动触发；
3. 用户已完成或愿意完成插件页面启用、授权 / trust、重启 App 或重载插件宿主；
4. 后续逻辑明确要求 `environment_hook_integrated=true`，需要可复现验收路径；
5. 环境插件安装、升级或复核后，需要把用户侧冒烟检查变成可记录、可复跑的 lifecycle 验收。

本文不适用于：

1. 环境插件尚未安装或安装检测未通过；
2. 目标环境、插件页面、授权状态或 LDVH 本体路径不清；
3. 目标环境确认不支持 Hook、`target_environment_supported=false` 或 `unsupported_target_environment`，只能走 30 无 Hook 环境分支；
4. 用户要求安装、升级、禁用、卸载、迁移或覆盖插件 / Git Hook；
5. 管辖项目 Git Hook 未安装、非 Git worktree 或 `LDVH-GOVERNED-PROJECTS.yaml` 配置仍阻断；
6. 用户只是询问概念、边界或为何不能声明 integrated。

## 5. 模板定位与来源

本文是 30 之后的独立正式行动模板，编号为 `31`。31 由 30 交接调用：30 安装完成交还时，若环境 Hook 安装检测通过但 integrated 尚未成立，应提示 Human 是否进入 31；Human 未授权进入 31 时，不得继续做受控写入测试或记录 lifecycle 验收。

31 不重复 30 的安装向导，不重新解释 LDVH 本体路径、目标工作区配置或管辖项目选择。31 只读取 30 的交还结果、当前目标环境、插件页面状态、统一安装验证结果和 lifecycle 验收记录状态。

31 的执行结果只可能是：验收通过并记录 lifecycle 验收、验收失败并进入诊断、Human 停止验收、或因前提不足返回 30 / 安装修复流程。31 不得把“用户还没做完测试”写成失败，也不得把“用户看到了部分提示”写成全部通过。

## 6. 验收前提与测试组

进入 31 前必须满足以下前提：

| 前提 | 要求 | 不满足时 |
|---|---|---|
| 安装检测 | `install_verification.py` 显示 `install_complete=true`、`environment_hook_install_verified=true` | 返回 30 或安装修复流程 |
| integrated 状态 | 当前仍为 `environment_hook_integrated=false`，需要 lifecycle 验收转换 | 若已为 true，只做复核交还 |
| Human 授权 | Human 明确选择开始验收测试 | 停止，不执行受控测试 |
| 目标环境 | 目标环境名称、插件页面或插件管理器入口清楚 | 暂停并要求补充 |
| Hook 支持 | 目标环境支持 Hook 且环境 Hook 安装检测已经通过 | 若目标环境确认不支持 Hook、`target_environment_supported=false` 或 `unsupported_target_environment`，返回 30 无 Hook 环境分支 |
| 测试安全 | 受控负例和正例只使用 harmless scratch target，不写事实源、specs、用户环境或外部项目 | 暂停并重拟测试 |

验收测试组必须覆盖以下项目：

| 编号 | 测试项 | 判断标准 | 失败处理 |
|---|---|---|---|
| 1 | 插件页面状态 | 插件或扩展包可见、启用、已授权或无待授权、无错误 | 停止并回到插件页面诊断 |
| 2 | 重启后状态 | 重启 App 或重载插件宿主后插件仍启用且无新增错误 | 停止并回到插件安装 / 授权诊断 |
| 3 | 新窗口或新会话触发 | 新窗口或新会话能看到 LDVH 启动提示、诊断输出或可回读的 SessionStart 真实触发证据 | 停止，不记录 lifecycle 验收 |
| 4 | 受控负例阻断 | 对 harmless scratch target 发起应阻断的写入类操作时，PreToolUse 负例被阻断或返回明确 blocking diagnostic | 停止；若意外写入，只记录失败并按 Human Gate 处理清理 |
| 5 | 受控正例放行 | 对 Human 授权的 harmless scratch target 或等价安全操作发起正例时，操作被放行且无 blocking diagnostic | 停止并诊断授权、payload 或失败处理 |
| 6 | 统一安装验证 | `install_verification.py` 仍显示安装检测通过，并列出 Git Hook 正反例通过 | 停止并回到安装修复流程 |
| 7 | lifecycle 验收记录 | `environment_lifecycle_acceptance.py record --confirm-human-gate` 成功，复跑显示 `environment_lifecycle_acceptance_valid=true` | 停止，不声明 integrated |
| 8 | integrated 复核 | `install_verification.py --require-environment-integrated` 显示 `environment_hook_integrated=true` 且无阻断诊断 | 若失败，交还诊断，不强行转换 |

受控 scratch target 必须是临时、可识别、可清理的测试路径，例如 `.ldvh-runtime/acceptance-probe/` 下的文件。不得用正式 specs、事实对象、外部用户文件、管辖项目业务文件、用户环境配置或插件系统文件做正反例写入目标。

## 7. 验收测试组状态机

31 必须使用测试组状态机。状态表只显示当前步骤和已完成判断；尚未发生的步骤保持空白。每一步只问一个判断，选项只允许 `1 通过` 和 `2 失败，停止验收`；如果需要用户补充截图、错误文本或插件页面状态，应作为失败后的诊断输入，不作为第三个主选项。

示例形态：

| 状态 | 步骤 | 判断 / 结果 |
|---|---|---|
| 👉 | 1/8 🧭 验收授权 |  |
|  | 2/8 🔌 插件页面状态 |  |
|  | 3/8 🔁 重启后状态 |  |
|  | 4/8 💬 新会话触发 |  |
|  | 5/8 ⛔ 受控负例阻断 |  |
|  | 6/8 ✅ 受控正例放行 |  |
|  | 7/8 🧪 统一安装验证 |  |
|  | 8/8 🧾 记录验收与复核 |  |

每个判断必须说明本步测试目标、预期正常表现、实际观察和下一步。AI 不得连续抛出一串专业问题让 Human 自行判断；AI 必须把可自动检查的部分自己运行，把必须 Human 观察的部分压缩成一句清楚问题。

正常情况下，31 的交互应是逐项推进：Human 授权开始后，AI 先检查可自动读取的安装状态；需要 Human 操作时，只要求 Human 完成当前一步并回答通过或失败；失败时立即停止后续测试，交还失败项和诊断入口。

## 8. Context、Scenario、Gate 与交还

| 结构 | 最小要求 |
|---|---|
| Context | 读取用户目标、目标环境、30 交还结果、`install_verification.py` 当前输出、`environment_hook_integrated=false` 状态、插件页面或插件管理器入口、Human 授权状态、lifecycle 验收记录状态、source_refs，并回指 `specs/01-保障与衔接.md`、`specs/06-行动模板基础规范.md`、`specs/09-测试与验证规范.md`、`specs/30-LDVH安装初始化管辖项目配置行动模板.md` 和本文。 |
| Scenario | 30 安装检测通过后进入环境 Hook 接入后验收、用户要求验证真实 lifecycle、用户完成插件授权后要求验收、需要 lifecycle 冒烟转换 integrated、或要求只回答 01/06/09/30/31 边界时适用。 |
| Gate | 开始验收、执行受控负例阻断测试、执行受控正例放行测试、记录 lifecycle 验收、接受插件页面状态、接受授权 / trust 状态、声明 `environment_hook_integrated`、处理意外 scratch 写入或清理测试文件，均必须有 Human Gate 或明确用户授权。 |
| 执行 | 使用测试组状态机逐项推进，一次只判断一项，选项固定为通过 / 失败；先运行只读安装检测，再要求 Human 检查插件页面、重启 App、新窗口或新会话，再执行受控 scratch target 的负例和正例；不得安装、不得升级、不得卸载、不得修改用户环境；失败即停止，不进入后续步骤。 |
| 验证 | 使用 `install_verification.py`、`environment_lifecycle_acceptance.py`、插件页面状态、重启 App、新窗口或新会话、SessionStart 真实触发证据、PreToolUse 受控负例阻断、受控正例放行、Git Hook 正反例、`environment_lifecycle_acceptance_valid=true` 和 `environment_hook_integrated=true` 复核；失败、缺证或 Human 未确认时不得声明 integrated。 |
| 回写 | 仅在全部必需测试通过且 Human Gate 明确后，写入 `.ldvh-runtime/environment-lifecycle-acceptance.json` 或指定 lifecycle 验收记录；记录必须通过 `environment_lifecycle_acceptance.py record --confirm-human-gate` 或等价入口生成，source note 写逐项验收摘要；不得写事实源、不得写 specs、不替代插件页面、不得把聊天观察替代插件页面或真实 payload 证据。 |
| 交还 | 交还验收结果表、通过项、失败项、未验证项、`environment_hook_integrated` 最终状态、`environment_lifecycle_acceptance_valid` 状态、统一安装验证摘要、回滚或诊断入口、scratch target 处理状态、source_refs 和残留风险；阻断时交还当前停止步骤和下一步诊断建议。 |

## 9. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 验收授权要求 | 进入测试组、执行受控写入类测试和记录 lifecycle 验收前必须 Human 授权 | 本文、01、06、09 | 验收治理 | 用户要求确认环境 Hook 接入后 |
| 逐项判断要求 | AI 必须一次只判断一项，并给出预期、实际和结论 | 本文、09、tests | 交互治理 | 执行 31 测试组时 |
| 安全测试目标要求 | 正反例只能使用 harmless scratch target，不得触碰 specs、事实源、用户环境或业务文件 | 本文、07、09 | 写入治理 | 执行受控写入类测试时 |
| integrated 转换要求 | 只有安装检测通过、测试组全部通过、lifecycle 验收记录有效且复跑验证通过时才可声明 integrated | 本文、01、30、Code audit、tests | 环境治理 | `environment_hook_integrated=false` 需要转换时 |
| 失败停止要求 | 任一必需测试失败、缺少 Human 确认或诊断不可复现时，必须停止后续步骤 | 本文、09 | 验证治理 | 测试失败或缺证时 |

## 10. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 结构检查 | 是否具备 Context、Scenario、Gate、执行、验证、回写和交还结构，并能被 Code 解析 | 不得作为正式行动模板执行 |
| 测试组检查 | 是否覆盖插件页面状态、重启后状态、新窗口或新会话、受控负例阻断、受控正例放行、统一安装验证和验收记录复核 | 不得声明 lifecycle 验收完成 |
| Gate 检查 | 是否在开始验收、受控写入测试、记录验收和声明 integrated 前获得 Human Gate | 停止验收或回到用户确认 |
| 转换检查 | 是否通过 `environment_lifecycle_acceptance.py` 记录并复跑 `install_verification.py --require-environment-integrated` | 不得把 `environment_hook_integrated` 写成 true |
| 边界检查 | 是否避免安装、升级、卸载、修改用户环境或写事实源 | 停止执行并回到 30 或环境修复流程 |

## 11. Human Gate

以下情况必须进入 Human Gate：

1. Human 要求从 30 交还结果进入 31 环境 Hook 接入后验收；
2. 接受插件页面启用、授权 / trust、无错误或重启后状态；
3. 执行受控负例阻断测试或受控正例放行测试；
4. 处理意外 scratch 写入、清理测试文件或接受测试残留；
5. 记录 lifecycle 验收；
6. 声明或接受 `environment_hook_integrated=true`；
7. 失败后继续诊断、重新执行某一步或返回 30 修复流程。

## 12. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 30 安装检测未通过，或 `environment_hook_install_verified` 不是 true；
2. 目标环境、插件页面、授权状态或 LDVH 本体路径不清；
3. 目标环境确认不支持 Hook、`target_environment_supported=false` 或 `unsupported_target_environment`，必须返回 30 无 Hook 环境分支，不得继续 31；
4. Human 未明确授权开始验收测试；
5. 任一必需测试失败、缺少实际观察、缺少插件页面状态或缺少真实 lifecycle 触发证据；
6. 受控负例没有阻断，或受控正例没有放行；
7. `environment_lifecycle_acceptance.py record --confirm-human-gate` 失败；
8. 复跑 `install_verification.py --require-environment-integrated` 仍返回 blocked / review_required；
9. 测试需要写入 specs、事实源、用户环境、插件系统文件、外部项目业务文件或其它非 scratch target；
10. AI 试图用聊天印象、缓存、旧 trust、插件可见或 repo-local shim 直测替代真实 lifecycle 验收。

## 13. 待补齐事项

1. 本模板当前定义验收行动与 Code 可消费结构，不提供独立交互式 wizard CLI；若未来新增 CLI，必须完整承接本文测试组状态机、Human Gate、失败停止和交还格式；
2. 不同目标环境的插件页面名称、授权 UI 和真实写入类工具行为可能不同；环境特定实现应进入 `code/docs/02-Environment-Plugin-Practice.md` 或对应插件文档，不写回本文；
3. 受控正反例测试的 scratch target 默认不进入事实源；若未来需要长期保存验收证据，应先定义事实对象或验证声明承接边界；
4. 卸载后验收、禁用后验收和跨环境批量验收仍后置；启用前必须新增模板或扩展本文并重新进入 Human Gate、Code 校验和测试闭环；
5. 本模板不得替代 30 的安装初始化配置流程，也不得绕过 01 的环境入口 integrated 声明边界。
