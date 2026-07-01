# 10A commit-msg 最小 hard switch 记录

> 文件状态：temporary migration closure。本文记录 V3 在当前 worktree 接管真实 Git `commit-msg` Hook 的最小 hard switch 结果；不授权 session start、pre tool use、completion claim、Rules、runtime adapter、通用 Web 写入或 Human Gate 自动完成。正式规则仍以 `specs/` 正文为准。

> 后续纠偏：10A 曾把提交正文 `读取依据:` 作为 read_plan 消费证据的最小自举折中；该做法已撤回。当前 `commit-msg` Hook 只校验 V2 对齐的 commit message 契约，read_plan 消费证据归 runtime receipt、外部运行时入口或显式校验入参承接，不进入 commit body 要求。

## 1. 接入目标

10A 只解决一个问题：真实 `git commit` 不再由父仓库 V2 Hook 校验，而由当前 V3 的 commit gate 校验。

最小接入范围：

1. 当前 worktree 使用 `core.hooksPath=hooks`；
2. `hooks/commit-msg` 调用 `code/commit_validate.py --hook-integrated`；
3. commit gate 不再从提交正文提取 read_plan 消费路径；
4. 提交正文按 V2 commit body 契约执行，body 必填时必须包含 `关键变更:`；
5. V3 Hook 输出仍保持 `authorization=none`，不替代 Human Gate 或事实源。

## 2. 关键决策

默认 Git hook 目录位于 common `.git/hooks`，会影响同一 Git common-dir 下的其它 worktree。10A 不覆盖 common hook，而是通过 worktree-local 配置接入：

```text
git config extensions.worktreeConfig true
git config --worktree core.hooksPath hooks
```

这样当前 V3 worktree 会使用 tracked `hooks/commit-msg`，父仓库或其它 worktree 不会因为 common hook 被覆盖而被 V3 校验器误拦截。

10A 初版曾新增如下可解析小标题：

```text
读取依据:
- specs/00-理念与构成.md
- specs/01-保障与衔接.md
- specs/02-AI行为规范.md
```

该段后续已废止，不再作为 commit gate 的 read_plan 消费证据；session receipt、pre_tool_use 或 completion_claim 的接管状态仍不得由 commit body 声明。

## 3. 交付物

| 文件 | 作用 |
|---|---|
| `hooks/commit-msg` | V3 tracked commit-msg Hook 模板 |
| `code/install_git_hooks.py` | 当前 worktree Hook 状态、安装和回滚入口 |
| `code/commit_validate.py` | 支持 `--hook-integrated`，供真实 Hook 调用 |
| `code/ldvh_specs.py` | 校验 V2 对齐的 commit message 契约；read_plan 证据仅在显式外部入参要求时检查 |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖 V2 commit body、Hook 集成标记、worktree-local hooksPath 和 message-body read_plan 不再生效 |
| `specs/attachments/03.Att.01-Commit-Message契约字段表.md` | 承接 V2 对齐的 commit body 小标题契约，不登记 `读取依据` |

## 4. 当前状态

```yaml
switch_mode: commit_msg_hard_switch_minimal
environment_integrated: partial
hook_integrated: git.commit-msg
authorization: none
```

仍未接入：

1. session start；
2. pre tool use；
3. completion claim；
4. Rules / runtime adapter；
5. 通用 Web 写入和 Human Gate 自动记录；
6. 外部受管项目 Hook adapter。

## 5. 操作与回滚

状态检查：

```bash
python3 code/install_git_hooks.py status --repo .
```

安装 / 修复：

```bash
python3 code/install_git_hooks.py install --repo .
```

回滚当前 worktree Hook 接管：

```bash
python3 code/install_git_hooks.py uninstall --repo .
```

回滚只撤销当前 worktree 的 `core.hooksPath`，不删除 tracked `hooks/commit-msg`，也不改 common `.git/hooks/commit-msg`。

## 6. 验证声明

10A 完成时应验证：

1. `python3 -m pytest tests/code/test_ldvh_specs_validate.py -q`；
2. `python3 -m pytest tests/code/test_formal_specs.py -q`；
3. `python3 code/specs_validate.py all --format text --fail-on-diagnostics`；
4. `python3 code/install_git_hooks.py status --repo .`；
5. 真实提交由 V3 `hooks/commit-msg` 调用 `code/commit_validate.py --hook-integrated`。

## 7. 后续

下一阶段如果继续推进环境接入，应单独处理 session start、pre tool use、completion claim 和 runtime adapter。不得因为 10A 已接入 commit-msg，就默认其它环境入口已经具备阻断能力。
