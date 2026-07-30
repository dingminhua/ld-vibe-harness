# LDVH 接入 WorkBuddy 环境分析报告

- 日期：2026-07-30
- 执行环境 = 目标环境：WorkBuddy 桌面版（macOS，darwin），用户目录 `~/.workbuddy/`，本报告全部观察在该环境当次会话内完成（二者同一，识别依据：本会话由 WorkBuddy 运行，日志 `~/.workbuddy/logs/2026-07-30/ld-vibe-harness-v4__6790957b*.log` 与本会话时间线吻合）。
- 依据文件：README.md、specs/09-环境接入规范.md（§5、§6）、specs/attachments/09.Att.01-环境接入面.md、ldvh-base/sparks/spark-0039.yaml。
- 本报告是临时说明材料（置于根级 docs/，按 09 §6.2 不作为任何验证输入）。

---

## 1. 环境机制支持情况（逐项证据与层级）

证据层级约定：**静态存在 < CLI 直调可用 < 真实自动触发 < 已验证**，各层互不冒充。

### 1.1 Skill / 指令文件 —— 已验证（用户级技能清单注入）

| 项 | 结论 | 证据 |
|---|---|---|
| 用户级 Skill 目录 | 已验证 | `~/.workbuddy/skills/` 实际存在多个技能（web-access、excalidraw-diagram 等）；**本会话上下文中确实注入了这些技能的清单**（含 name/description/location），属于当次真实自动注入，不是推测 |
| 加载机制 | 已验证（清单注入层）| 每个技能为 `<skill-dir>/SKILL.md`（YAML frontmatter：name/description 等）；frontmatter 摘要随会话启动注入"可用技能清单"，全文由 AI 按需显式加载 |
| 项目级 Skill（`<workspace>/.workbuddy/skills/`） | 未验证 | 产品文档声明支持，本工作区无项目级技能，无当次观察 |
| 局限 | — | 技能是"AI 可见的说明书"，是否在正确时机被加载取决于模型行为，**无机械保证**；这与 spark-0039 对信息层的定位一致 |

注意：`~/.workbuddy/skills/ldvh-fenxi-zhuanjia` 是一个与 LDVH 无关的文档协作技能（OpenSpecDocTeam，`disable: true`），仅命名撞车；新技能应避免混淆命名。

### 1.2 生命周期 Hook —— 引擎已验证；LDVH 自身触发未验证

官方资料：CodeBuddy Hook 参考（https://www.codebuddy.cn/docs/cli/hooks ，2026-07-30 抓取）。该文档主体面向 CodeBuddy Code CLI（路径写 `~/.codebuddy/settings.json`）；WorkBuddy 为同源产品，本机实际目录为 `~/.workbuddy/`。跨产品差异不可照搬，以下按本机实际观察分级：

| 能力 | 状态 | 证据 |
|---|---|---|
| Hook 引擎存在并实时执行 | **已验证** | 本会话日志：`[SessionHookManager] executeSessionStartHooks source=startup ...total=168ms`（12:56:47，正是本会话冷启动时刻）；另有 `source=resume` 与 `executeStopHooks` 记录 |
| 插件 hooks.json 被消费 | **已验证（他插件）** | `[HookExtensionLoader] Loaded hooks configuration from extension: tencent-pptx@workbuddy-builtin`、`1 hook(s)`；该插件声明 `PreToolUse` matcher `Skill` |
| SessionStart 区分 startup/resume/clear/compact | 已验证（startup/resume 两值实测出现）| 同上日志 + 官方文档 matcher 定义 |
| PreToolUse 可阻断（exit 2 / `permissionDecision: deny`、`modifiedInput`）| **未验证（文档级支持）** | 官方文档明确定义；本机未做真实阻断实测 |
| UserPromptSubmit / SubagentStart / PreCompact / SessionEnd 等 | 未验证 | 文档列出 27+ 事件；本机仅观察到 SessionStart/Stop/Notification 查询痕迹 |
| settings.json 用户级 `hooks` 字段 | 未验证 | 文档声明支持；本机 `~/.workbuddy/settings.json` 当前无 hooks 字段，未实测 |
| payload | 文档级 | stdin JSON：公共字段 `session_id / transcript_path / cwd / permission_mode / hook_event_name`；SessionStart 附 `source`；PreToolUse 附 `tool_name / tool_input`。**与 `ldvh-work-context` 核心期望字段（hook_event_name、source、cwd）语义吻合，无需补造** |
| LDVH 自身 hook 在 WorkBuddy 真实触发 | **未验证** | 本机存在 V3 遗留插件 `ldvh@ldvh-local`（`~/.workbuddy/plugins/marketplaces/ldvh-local/`，声明 SessionStart/PreToolUse/Stop），但 `settings.json` 中 `"ldvh@ldvh-local": false`（已禁用），且其指向 V3 shim 并**携带整套 V3 specs 副本**——违反 09 §5.2 薄引用/不复制规则正文，属待清理残留，不可复用为 v4 接入单元 |

肯定不支持项：未发现。没有任何机制被证明"肯定不存在"，故本报告无 unsupported 结论，只有已验证/未验证。

### 1.3 Git hook —— 静态安装+管理归属已验证；真实触发未在本次取证

- 本 worktree `core.hooksPath=.githooks-v4`，`commit-msg` 存在（`ldvh-native-commit-msg-hook: v1 sha256:5560ebbb…`）。
- `ldvh-git-hook status --worktree …` 直调返回 "LDVH owns the current Git commit-msg Hook"（退出 0）。
- 本次未执行真实 commit，不以静态状态冒充真实触发。Git 机制本身环境无关，能力肯定存在。

### 1.4 LDVH CLI 直调 —— 可用，但有一个本环境陷阱（重要）

- **陷阱（当次实证）**：在本环境 shell 工具下，`ldvh capabilities` 不喂 stdin 时进程被 SIGKILL（退出码 137，无任何输出）；显式封闭/提供 stdin（`echo '' | …` 或管道 JSON）后正常。凡在 WorkBuddy 内调用 LDVH CLI，**必须显式提供 stdin**。此经验建议后续经 Helper 受控写入记录为 Pitfall（本报告遵守直写禁令，不写 ldvh-base/）。
- `echo '' | .venv/bin/ldvh capabilities` → `ldvh-helper-cli/2`，`outcome: partial`，发现 7 项领域公开操作。
- `echo '{"hook_event_name":"SessionStart","source":"startup","cwd":"<repo>"}' | .venv/bin/ldvh-work-context --helper-executable <abs>/.venv/bin/ldvh` → `ldvh-work-context/1`，rule delivery **ok**，facts `not_requested`，规则原文含来源行号回指。
- 六个 console entry 均静态存在于 `.venv/bin/`。

---

## 2. 三层框架在 WorkBuddy 的承载（推荐）

| 层 | 承载 | 理由 |
|---|---|---|
| 信息层 | **用户级薄引用 Skill**：`~/.workbuddy/skills/ldvh/SKILL.md` | 技能清单注入已在本会话验证为真实自动行为；符合 spark-0039 默认形态；零信任步骤（对比插件需 Human 在设置启用）；用户级作用域覆盖所有工作区，符合 09 §6.1"用户级范围"预期 |
| 自动触发层 | **暂不建**。升级时用 WorkBuddy 插件（`hooks/hooks.json`，SessionStart matcher `startup|resume|compact`；guardrail 场景加 PreToolUse）| spark-0039 的升级触发条件当前无一满足；且按 09.Att.01 入口选择第 7 条，新建 manifest/薄 adapter 必须**停止安装分支、另立独立 Code 计划**（在环境侧仓库，不在 LDVH 仓库）。本机 Hook 引擎已验证可用，故该路线技术上成立，只是证据未到 |
| 阻断层 | **原生 git commit-msg hook**（`ldvh-git-hook install`，按 worktree）| 与前两层选择无关；本 worktree 已装且归属可证；边界如 spark-0039 所述（--no-verify、多 clone、Human 直接操作 git） |

Skill 与插件不互斥的判断在本环境成立：Skill 解决"AI 知道 LDVH 存在与用法"，插件解决"注入必然性"；后者留待证据触发。

## 3. Skill 最小内容骨架（只指路，不抄规则）

位置：`~/.workbuddy/skills/ldvh/SKILL.md`。分发方式：spark-0039 倾向"Helper 生成式渲染本机路径"，该能力当前无公开入口（unverified）；现阶段只能静态手写，**绝对路径须写死**，升级发行物后人工同步。

```markdown
---
name: ldvh
description: LDVH（规范驱动 AI 工作框架）接入指引。当工作涉及
  /Users/dmh2002/poker_hud_projects/... 下受 LDVH 管辖的项目、或需读写
  ADR/Pitfall/Spark/Study/WorkCase 事实、或提交受管仓库代码时必须先加载本技能。
---
# LDVH 接入指引（薄引用，不含规则正文）

LDVH_ROOT: /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4
HELPER: <LDVH_ROOT>/.venv/bin/ldvh

## 会话开始（形成工作上下文时）
echo '{"hook_event_name":"SessionStart","source":"startup","cwd":"<当前绝对cwd>"}' \
  | <LDVH_ROOT>/.venv/bin/ldvh-work-context --helper-executable <HELPER>
按返回的规则原文与来源行事；facts 默认 not_requested，不自动恢复事实。

## 动手落入 LDVH 领域前
先 echo '' | <HELPER> capabilities 发现当次公开操作，再经 ldvh call 取行动模板；
不猜测 Helper 字段，不复制模板正文。

## 纪律（指路，不复述规则）
- 本环境调用任何 LDVH CLI 必须显式提供 stdin（否则进程被杀，exit 137）。
- 禁止直写 ldvh-base/**；一切事实写入经 Helper 受控操作。
- 明确进入事实消费分支后才可用 ldvh-context-recovery（需 4 个显式参数）。
- 提交受管 worktree 前可用 Helper 预检；commit-msg Gate 的 block 以其 stderr 诊断为准。
```

## 4. 插件/Hook 层（仅在升级触发时执行）

- 事件：`SessionStart`（matcher `startup|resume|compact`）→ 薄 shim 原样转发 stdin JSON 给 `ldvh-work-context`，stdout 以 `additionalContext` 返回；guardrail 需求成立时另加 `PreToolUse`（matcher `Write|Edit|Bash`，`permissionDecision: deny` 阻断直写 `ldvh-base/`）。
- payload：见 §1.2 表（cwd/source/hook_event_name 均由环境实供，无需补造）。
- 安装位置：本地 marketplace `~/.workbuddy/plugins/marketplaces/<name>/plugins/ldvh/`（`.codebuddy-plugin/plugin.json` + `hooks/hooks.json` + 薄 shim），随后在 `settings.json.enabledPlugins` 置 true——**该启用为 Human 在设置界面完成**。
- 前置：先按 09.Att.01 第 7 条另立独立 Code 计划（环境侧仓库）；同时处置 V3 遗留 `ldvh@ldvh-local`（含规则副本，须清理，进 Human Gate）。
- cold start 与 hydrate 区分（本环境已有可用判据）：
  1. 真实触发：`~/.workbuddy/logs/<日期>/<workspace>__<hash>.log` 中出现与本轮时间吻合的 `executeSessionStartHooks source=startup`，且 shim 自身落盘执行痕迹（receipt）与会话内注入内容可互相回指；
  2. hydrate 伪装：`source=resume` 或会话内出现 work-context 但当轮无执行记录（pitfall-0001 的教训在本环境同样适用）。

## 5. 安装 / 部署 / 接入 / 验证四层

| 层 | 内容 | 当前状态 | Human-only |
|---|---|---|---|
| 安装 | `.venv` + 6 入口 + `capabilities` 直调 | **已成立**（本报告 §1.4 实测） | — |
| 部署 | 写入 `~/.workbuddy/skills/ldvh/SKILL.md`；git hook 已在本 worktree 就位；其它受管 worktree 逐个 `ldvh-git-hook install` | Skill 未部署 | 授权安装 Skill（本环境安装新技能须先过安全审计并确认）；`--confirm-human-gate` 授权每个 worktree 的 git hook 安装 |
| 接入 | 信息层的"接入"= 技能清单在新会话上下文中实际出现（机制已验证，对 ldvh 技能本身尚未发生）；插件层不做 | 待部署后成立 | 若走插件层：设置界面启用/信任插件 |
| 验证 | ① 冷启动新会话，确认清单含 ldvh 技能且 AI 据其调 CLI（调用痕迹可回查）；② 一次真实 commit（含一个应被拒的反例）验证 Gate 的 allow/block；③ 失败路径：故意缺 stdin 复现 137、缺字段观察 work-context 返回 unavailable | 未开始 | 冷启动新会话的动作本身；观察会话 UI 中技能清单 |

## 6. 缺口与如实声明

1. `unverified`：PreToolUse 真实阻断、UserPromptSubmit 等其余事件、settings 级 hooks、项目级技能注入、Skill 生成式分发、git hook 真实 commit 触发、LDVH 技能被 AI 按时机加载的行为稳定性。
2. `unsupported`：无（未发现任何"肯定不存在"证据）。
3. 残留风险：Skill 属劝告级，直写污染窗口仅由 git Gate + 模板强制项压缩（与 spark-0039 一致）；本机 V3 遗留插件含规则副本，未清理前是第二权威隐患。
4. 本报告未改动任何 LDVH 入口契约，全部调用经既有 6 个 console entry。
