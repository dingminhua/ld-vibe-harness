# Claude Code CLAUDE.md 与配置机制

> 创建日期：2026-06-08
> 来源：Anthropic 官方文档、Claude Code GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.anthropic.com/en/docs/claude-code | https://github.com/anthropics/claude-code

---

## 1. 结论摘要

Claude Code 通过 CLAUDE.md 文件实现项目上下文持久化，支持全局（~/.claude/CLAUDE.md）、项目（./CLAUDE.md）和本地（.claude/CLAUDE.local.md）三级层级，优先级为本地 > 项目 > 全局。规则目录（.claude/rules/*.md）提供模块化规则管理。自动记忆功能将项目上下文存储在 ~/.claude/projects/<project>/memory/ 中（限制 25KB 或 200 行）。设置优先级从高到低为 CLI 标志 > 本地项目 > 项目 > 用户。

## 2. 官方定位

CLAUDE.md 是 Claude Code 的记忆文件，为 AI 提供项目上下文、编码规范和特殊指令。Claude Code 在会话启动时自动加载相关层级的 CLAUDE.md，并在交互中通过 # 前缀快速添加记忆。

## 3. CLAUDE.md 文件层级

| 层级 | 路径 | 作用域 | Git 状态 |
|------|------|--------|----------|
| 全局 | ~/.claude/CLAUDE.md | 所有项目 | 个人 |
| 项目 | ./CLAUDE.md | 当前项目 | git 跟踪，团队共享 |
| 本地 | .claude/CLAUDE.local.md | 当前项目 | gitignore，个人覆盖 |

优先级：本地 > 项目 > 全局（更具体的覆盖更通用的）。

## 4. 规则目录

对于规则较多的项目，使用规则目录替代单一庞大的 CLAUDE.md：

- 项目规则：.claude/rules/*.md —— 团队共享，git 跟踪
- 用户规则：~/.claude/rules/*.md —— 个人，全局

每个 .md 文件作为额外上下文加载。

## 5. 自动记忆

Claude 自动将学到的项目上下文存储在 ~/.claude/projects/<project>/memory/ 中：

- 限制：每个项目 25KB 或 200 行
- 与 CLAUDE.md 分开，是 Claude 自己关于项目的笔记，跨会话积累

## 6. 快速添加记忆

在交互模式中使用 # 前缀快速添加到 CLAUDE.md：

```
# Always use 2-space indentation
```

## 7. 设置优先级

1. CLI 标志 —— 覆盖所有设置
2. 本地项目：.claude/settings.local.json（个人，已 gitignore）
3. 项目：.claude/settings.json（共享，git 跟踪）
4. 用户：~/.claude/settings.json（全局）

## 8. .claude/ 目录结构

```
.claude/
├── CLAUDE.local.md          # 个人项目覆盖
├── settings.json            # 项目共享设置（权限、hooks、MCP）
├── settings.local.json      # 个人项目设置
├── rules/                   # 模块化规则目录
│   ├── coding-standards.md
│   └── testing-rules.md
├── commands/                # 自定义斜杠命令
│   └── deploy.md
├── agents/                  # 自定义子 agent 定义
│   └── security-reviewer.md
├── skills/                  # 自然语言触发的技能
│   └── database-migration.md
└── worktrees/               # 隔离的 git worktree
    └── feature-x/
```

## 9. 与 Trae Rules 的关键差异

| 能力 | Trae Rules | Claude Code CLAUDE.md |
|------|-----------|----------------------|
| 始终生效 | alwaysApply: true | 默认行为 |
| 按文件类型触发 | globs 字段 | 不支持——需用 rules 目录或 skills |
| 按场景触发 | description 字段 | 不支持——需用 skills 的自然语言匹配 |
| 个人覆盖 | 不支持 | CLAUDE.local.md |
| 自动记忆 | 不支持 | 支持（25KB/200 行限制） |
| 模块化规则 | 子目录嵌套 | .claude/rules/ 目录 |

## 10. 待进一步调研

1. .claude/rules/ 中规则文件的加载顺序和优先级
2. 自动记忆的触发条件和更新策略
3. CLAUDE.md 与 .claude/rules/ 的内容冲突处理机制
