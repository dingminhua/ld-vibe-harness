# Git Commit 与 Hook 实现实践

本文是 Code 实现域文档，承接 `specs/06-行动模板基础规范.md` 和 `specs/11-环境适配规范.md` 中不应写入 specs 正文的命令、安装和回滚实践。本文不定义新的规则源、事实源、Human Gate 或状态闭集；若与 specs 冲突，以 specs 为准。

## Git 提交实践

Git 提交行动执行时，AI 应按当前目标读取：

1. 用户提交目标和本次影响范围；
2. 当前 Git 仓库；
3. `git status --short --untracked-files=all`；
4. staged / unstaged / untracked 状态；
5. 必要 diff；
6. source_refs、验证证据和残留风险。

提交前应只 stage 本次范围内文件，判断是否需要拆分提交，并按 `specs/attachments/03.Att.01-Commit-Message契约字段表.md` 选择单一 type 和零个或一个 scope。提交正文在触发 body 条件时应包含 `读取依据:` 和 `关键变更:`。

提交前可运行：

```bash
python3 code/commit_validate.py --check-message-file "<message-file>" --repo "<repo>"
```

真实 Git `commit-msg` Hook 会调用同一 validator，并带 `--hook-integrated` 标记。

## 当前 Worktree Hook

当前 LDVH V3 worktree 使用 worktree-local hooks path：

```bash
git config --worktree core.hooksPath hooks
```

状态检查：

```bash
python3 code/install_git_hooks.py status --repo .
python3 code/environment_status.py --format text
python3 code/environment_entry_audit.py --format text
```

当前预期状态是：`git.commit-msg` 为 integrated；`manual.runtime_adapter`、`manual.session_start`、`manual.pre_tool_use` 和 `manual.completion_claim` 为 manual-ready 或 deferred。

## 底层安装器边界

`code/install_git_hooks.py` 是当前 LDVH worktree 本地 Hook 安装器，也是 `code/governed_hook_adapter.py` 的底层 backend。它不负责外部受管项目解析，也不负责 Human Gate 判断。

直接 CLI 使用只适合当前 LDVH worktree：

```bash
python3 code/install_git_hooks.py status --repo .
python3 code/install_git_hooks.py install --repo .
python3 code/install_git_hooks.py uninstall --repo .
```

外部受管项目不得直接用底层安装器安装或卸载 Hook。外部 repo 必须使用 governed adapter：

```bash
python3 code/governed_hook_adapter.py status --repo "<repo>" --governance-root "<ldvh-root>"
python3 code/governed_hook_adapter.py install --repo "<repo>" --governance-root "<ldvh-root>" --confirm-human-gate
python3 code/governed_hook_adapter.py uninstall --repo "<repo>" --governance-root "<ldvh-root>" --confirm-human-gate
```

测试或 adapter backend 需要调用底层安装器处理外部临时 repo 时，必须显式使用 `--backend-allow-external` 或直接调用 backend 函数；该标记不得作为 Human Gate 替代，也不得面向普通外部项目操作。
