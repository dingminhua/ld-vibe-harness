# LDVH V3

当前仓库处于 V3 commit-msg 最小 hard switch 状态：日常规则判断、事实对象维护和 Web 数据读取以 V3 为准；当前 worktree 的真实 Git `commit-msg` Hook 已由 V3 接管。Rules / Skill 顶层机制已取消；runtime adapter、session start、pre tool use、completion claim 和其它阻断型环境入口尚未强制接管。

## 当前主线

- `specs/`：规则源。Markdown specs 是正式规则权威，不是事实源。
- `ldvh-base/`：事实对象实例。当前承接 Spark、WorkCase、ADR、Pitfall、Study。
- `code/`：确定性解析、校验、诊断、commit gate 和 e2e rehearsal。
- `web/`：Human-facing 展示和 Web API。Web 独立读取 V3 `ldvh-base/`，不依赖 Code 输出作为主数据源。
- `tests/`：正式回归检查。
- `reviews/formal/`：正式 specs 和附件的 review hash gate 收据。
- `_migration/`：历史迁移证据和迁移测试材料；不作为日常规则源、事实维护入口或正式 review ledger。
- `hooks/`：当前 worktree 的 `commit-msg` Hook 模板已启用，用于真实提交前校验 V3 commit message 契约和 read_plan 消费证据。

V3 不保留 `rules/` 或 `skills/` 顶层目录机制。V2 Rules 的入口可见能力只作为环境薄引用或 repo instruction 候选承接；V2 Skill 的可复用工作流能力只进入行动模板、Action Guide 或外部包装候选。

## 环境边界

```yaml
switch_mode: commit_msg_hard_switch_minimal
environment_integrated: partial
hook_integrated: git.commit-msg
runtime_adapter_entry: manual.runtime_adapter
runtime_adapter_integrated: false
session_start_entry: manual.session_start
session_start_integrated: false
pre_tool_use_entry: manual.pre_tool_use
pre_tool_use_integrated: false
completion_claim_entry: manual.completion_claim
completion_claim_integrated: false
authorization: none
```

这意味着 V3 已是日常主线，并会通过当前 worktree 的 `core.hooksPath=hooks` 自动拦截真实 Git commit message。系统仍不会自动拦截所有 session start、pre tool use、completion claim 或其它环境操作。需要时应手动运行对应 Code 命令；Code、Web、测试或 commit gate 输出都不替代 Human Gate。

当前支持两种接入方式：

1. 真实 Hook：仅 `git.commit-msg` 已自动触发；
2. 手动 / 外部 adapter-ready：`session_start`、`pre_tool_use`、`completion_claim` 可通过独立 CLI 或统一 `runtime_adapter.py` 调用，但不会自动触发。

统一 runtime adapter 入口：

```bash
python3 code/runtime_adapter.py session-start --task "<当前任务>" --target-path "<目标路径>"
python3 code/runtime_adapter.py pre-tool-use --target-path "<目标路径>" \
  --acknowledged-path specs/00-理念与构成.md \
  --acknowledged-path specs/01-保障与衔接.md \
  --acknowledged-path specs/02-AI行为规范.md
python3 code/runtime_adapter.py completion-claim --target-path "<目标路径>" \
  --verification-evidence "<验证命令、未验证范围或残留风险说明>"
```

该入口输出统一 adapter 包装结果和对应 manual 事件结果；它是 `manual.runtime_adapter`，不是环境自动触发证明。

手动 session start 入口：

```bash
python3 code/session_start.py --task "<当前任务>" --target-path "<目标路径>"
```

该入口输出 P0/P1 read_plan 和 stdout-only receipt；它是 `manual.session_start`，不是环境自动触发证明。

手动 pre tool use 入口：

```bash
python3 code/pre_tool_use.py --target-path "<目标路径>" --operation write \
  --acknowledged-path specs/00-理念与构成.md \
  --acknowledged-path specs/01-保障与衔接.md \
  --acknowledged-path specs/02-AI行为规范.md
```

该入口输出写入前 preflight、required read plan 和 stdout-only receipt；它是 `manual.pre_tool_use`，不是工具调用已被自动拦截的证明。

手动 completion claim 入口：

```bash
python3 code/completion_claim.py --target-path "<目标路径>" \
  --verification-evidence "<验证命令、未验证范围或残留风险说明>"
```

该入口输出完成声明前检查和 stdout-only receipt；它是 `manual.completion_claim`，不是完成声明已被自动拦截或 Human 已验收的证明。

Hook 状态和回滚入口：

```bash
python3 code/install_git_hooks.py status
python3 code/install_git_hooks.py install --repo .
python3 code/install_git_hooks.py uninstall --repo .
```

统一环境接入状态检查：

```bash
python3 code/environment_status.py --format text
python3 code/environment_entry_audit.py --format text
```

该检查会同时报告真实 `git.commit-msg` Hook、manual runtime adapter、`session_start`、`pre_tool_use` 和 `completion_claim` 的可用/接入状态。当前预期结果是 `environment_integrated: partial`、`hook_integrated: git.commit-msg`，且三类 runtime 入口仍为 manual-ready、未自动触发。

`environment_entry_audit.py` 进一步审计 tool hook、completion hook、AGENTS/Codex repo 指令和外部 runtime adapter 候选，同时确认 Rules / Skill 顶层机制是 `removed_top_level`，不是待启用入口。当前结论是：除 `git.commit-msg` 外，没有可复现证据证明其它入口已自动触发。

真实提交如果触发 body 必填条件，正文至少包含 `读取依据:` 和 `关键变更:`：

```text
读取依据:
- specs/00-理念与构成.md
- specs/01-保障与衔接.md
- specs/02-AI行为规范.md

关键变更:
- ...
```

## 常用验证

优先使用分层测试入口。日常小改用 smoke 或 targeted，阶段收口、跨域迁移和高风险回归再跑 full：

```bash
python3 code/test_runner.py smoke
python3 code/test_runner.py targeted --changed specs/09-测试与验证规范.md
python3 code/test_runner.py full
```

等价 npm scripts：

```bash
npm run test:smoke
npm run test:targeted -- --changed web/api/app.ts
npm run test:full
```

底层验证命令仍可直接运行：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 code/specs_validate.py e2e --target-path tests/code/test_ldvh_specs_validate.py --format text --fail-on-diagnostics
python3 code/specs_validate.py commit-gate --format text --fail-on-diagnostics --message "<message>"
npm --prefix web run test:web:api
npm --prefix web run check
```

慢速全量测试适用于阶段收口、主线切换、跨域迁移或高风险回归：

```bash
python3 code/test_runner.py full
```

## 当前正式 specs 编号

- `00`：理念与构成
- `01`：保障与衔接
- `02`：AI 行为规范
- `03`：事实源与 Git 溯源规范
- `04`：Specs 基础规范
- `05`：事实模型基础规范
- `06`：行动模板基础规范
- `07`：Code 确定性执行规范
- `08`：Web 信息同步规范
- `09`：测试与验证规范
- `10`：受管项目接入规范
- `11`：环境适配规范
- `20`：Spark-火花
- `21`：WorkCase-工作项
- `22`：ADR-决策
- `23`：Pitfall-踩坑经验
- `24`：Study-研究报告
