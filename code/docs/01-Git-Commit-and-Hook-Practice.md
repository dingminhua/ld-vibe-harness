# Git Commit 与 Hook 实现实践

本文是 Code 实现域文档，承接 `specs/06-行动模板基础规范.md` 和 `specs/01-保障与衔接.md` §6 中不应写入 specs 正文的命令、安装和回滚实践。本文不定义新的规则源、事实源、Human Gate 或状态闭集；若与 specs 冲突，以 specs 为准。

## Git 提交实践

Git 提交行动执行时，AI 应按当前目标读取：

1. 用户提交目标和本次影响范围；
2. 当前 Git 仓库；
3. `git status --short --untracked-files=all`；
4. staged / unstaged / untracked 状态；
5. 必要 diff；
6. source_refs、验证证据和残留风险。

提交前应只 stage 本次范围内文件，判断是否需要拆分提交，并按 `specs/attachments/03.Att.01-Commit-Message契约字段表.md` 选择单一 type 和零个或一个 scope。提交正文在触发 body 条件时应包含 `关键变更:`；read_plan 消费证据由 runtime receipt、外部运行时入口或显式校验入参承接，不写入 commit body 要求。

读取计划确认可使用手动入口：

```bash
python3 code/acknowledge_read_plan.py --acknowledged-path specs/00-理念与构成.md --acknowledged-path specs/01-保障与衔接.md --acknowledged-path specs/02-AI行为规范.md --format json
```

该入口只生成 stdout-only receipt，不写入 session 存储，不替代 `pre_tool_use`、commit gate、验证声明或 Human Gate。`runtime_adapter.py` 仍只暴露环境 lifecycle 三件套：`session_start`、`pre_tool_use`、`completion_claim`。

提交前可运行：

```bash
python3 code/commit_validate.py --check-message-file "<message-file>" --repo "<target-repo>" --ldvh-root "<ldvh-root>"
```

`--repo` 表示目标 Git 仓库，用于读取 staged paths；`--ldvh-root` 表示 LDVH 根目录，用于读取 specs、附件和校验契约。真实 Git `commit-msg` Hook 会调用同一 validator，并带 `--hook-integrated` 标记。

## 当前 Worktree Hook

当前 LDVH V3 worktree 使用 worktree-local hooks path：

```bash
git config --worktree core.hooksPath hooks
```

证据检查：

```bash
python3 code/install_git_hooks.py status --repo .
python3 code/environment_status.py --format text
python3 code/environment_entry_audit.py --format text
```

当前预期判定是：`git.commit-msg` 为 integrated；`manual.runtime_adapter`、`manual.session_start`、`manual.acknowledge_read_plan`、`manual.pre_tool_use` 和 `manual.completion_claim` 为 manual-ready 或 deferred。

## 底层安装器边界

`code/install_git_hooks.py` 是当前 LDVH worktree 本地 Hook 安装器，也是 `code/governed_hook_adapter.py` 的底层 backend。它不负责外部管辖项目解析，也不负责 Human Gate 判断。

直接 CLI 使用只适合当前 LDVH worktree：

```bash
python3 code/install_git_hooks.py status --repo .
python3 code/install_git_hooks.py install --repo .
python3 code/install_git_hooks.py uninstall --repo .
```

外部管辖项目不得直接用底层安装器安装或卸载 Hook。外部 repo 必须使用 governed adapter：

```bash
python3 code/governed_hook_adapter.py status --repo "<repo>" --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>"
python3 code/governed_hook_adapter.py install --repo "<repo>" --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>" --confirm-human-gate
python3 code/governed_hook_adapter.py uninstall --repo "<repo>" --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>" --confirm-human-gate
```

governed adapter 安装外部 repo 时只写入 LDVH managed `commit-msg` 薄 shim，并把 LDVH 根目录嵌入为默认 validator 位置。外部 repo 的 shim 放在 Git 本地目录 `.git/ldvh-hooks/commit-msg`，避免把 Hook 文件写入业务工作树；LDVH 自身仍使用仓库内 `hooks/commit-msg` 作为模板和本仓库 Hook。卸载时只应取消由 LDVH managed active hook 占用的 worktree-local `core.hooksPath`，并删除外部 repo 中由 LDVH 管理的 shim；如果 active hook 不是 LDVH managed，不得静默关闭用户自己的 `core.hooksPath`，已有用户 Hook 或备份资产不得被静默删除。

LDVH 安装向导执行完整安装时，已选择管辖项目的 Git `commit-msg` Hook 是必检、必计划、确认后必执行的入口。安装或升级后必须回读 `governed_hook_adapter.py status`，确认 `core.hooksPath`、active hook、managed marker 和可执行位，并直接执行已安装 hook 文件验证有效 commit message 放行、无效 commit message 阻断。推荐使用统一只读安装验证入口一次性完成这些检查：

```bash
python3 code/install_verification.py --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>" --environment-name "<当前 AI 运行环境名称>"
python3 code/governed_hook_adapter.py verify --all-projects --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>"
python3 code/governed_hook_adapter.py verify --repo "<repo>" --governance-root "<workspace-root>" --ldvh-root "<ldvh-root>"
```

`install_verification.py` 不安装、不卸载、不修改管辖项目或用户环境；它调用 `governed_hook_adapter.py verify` 读取当前 active hook，执行有效 commit message 和无效 commit message 两个样例，并用退出码判断放行和阻断，同时汇总环境入口审计的不可验证范围。未完成这些验证时，不得声明该管辖项目 Git Hook 安装完成。

已选择管辖项目必须是有效 Git worktree。`governed_hook_adapter.py` 发现目标不是 Git 仓库时必须返回 blocking diagnostic，不得执行安装、不得隐式 `git init`，并应提示 Human 先把目标项目变成 Git 仓库后再继续安装。

测试或 adapter backend 需要调用底层安装器处理外部临时 repo 时，必须显式使用 `--backend-allow-external` 或直接调用 backend 函数；该标记不得作为 Human Gate 替代，也不得面向普通外部项目操作。
