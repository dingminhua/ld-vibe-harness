# Codex CLI Instructions 指令机制

> 创建日期：2026-06-08
> 来源：OpenAI 官方文档、Codex CLI GitHub 仓库
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://openai.github.io/codex/ | https://github.com/openai/codex

---

## 1. 结论摘要

Codex CLI 使用 AGENTS.md 作为项目指令的核心载体，采用分层 Markdown 文件机制。支持全局（~/.codex/AGENTS.md）、项目根和子目录三级层级，通过渐进式发现自动加载子目录指令。单个 AGENTS.md 有 32KB 默认上限。与 Trae Rules 的关键差异：不支持 globs 按文件类型触发和 description 按场景触发，需改为在目标目录放 AGENTS.md 或使用 SKILL.md 的 description 匹配。

## 2. 官方定位

AGENTS.md 是 Codex CLI 的项目上下文文件，为 AI 提供项目架构、约定和特殊指令。Codex 在会话启动时自动加载项目根目录的 AGENTS.md，并在 Agent 导航进入子目录时渐进式发现并注入该子目录的 AGENTS.md。

## 3. 指令文件层级

| 层级 | 路径 | 作用范围 | 说明 |
|------|------|----------|------|
| 全局 | ~/.codex/AGENTS.md | 所有项目 | 始终加载 |
| 项目根 | 项目 Git root 的 AGENTS.md | 当前项目 | Codex 自动从 Git root 向上扫描到 CWD |
| 子目录 | 各子目录下的 AGENTS.md | 对应子目录 | 渐进式发现 |

## 4. 渐进式发现

会话启动时加载根目录 AGENTS.md；当 Agent 导航进入子目录时，自动发现并注入该子目录的 AGENTS.md。按目录分层加载，不是按文件类型过滤。

## 5. 兼容的上下文文件

Codex 还支持识别以下上下文文件（优先级从高到低）：
- .hermes.md
- AGENTS.md
- CLAUDE.md
- .cursorrules

每个会话仅加载一种项目上下文类型，先匹配先生效。

## 6. 大小限制

单个 AGENTS.md 文件有 32KB 默认上限，内容较多时需拆分到子目录。

## 7. 全局指令 vs 项目指令

| 维度 | 全局指令 | 项目指令 |
|------|----------|----------|
| 路径 | ~/.codex/AGENTS.md | 项目根 AGENTS.md + 子目录 AGENTS.md |
| 加载时机 | 始终加载 | 进入项目时加载 |
| 作用范围 | 所有 Codex 会话 | 仅当前项目 |
| 可 Git 版本化 | 否 | 是 |
| 典型内容 | 个人偏好、通用编码风格 | 项目架构、约定、特殊指令 |

## 8. 与 Trae Rules 的关键差异

| 能力 | Trae Rules | Codex AGENTS.md |
|------|-----------|-----------------|
| alwaysApply（始终生效） | 支持 | 始终生效（默认行为） |
| globs（按文件类型触发） | 支持 | 不支持——需改为在目标目录放 AGENTS.md |
| description（按场景触发） | 支持 | 不支持——需改用 SKILL.md 的 description 匹配 |
| 按目录分层 | 不支持 | 支持（渐进式发现） |
| 大小限制 | 无明确限制 | 32KB 默认上限 |

## 9. AGENTS.md 示例

```markdown
# Project Context

This is a Next.js 14 web application with a Python FastAPI backend.

## Architecture
- Frontend: Next.js 14 with App Router in /frontend
- Backend: FastAPI in /backend, uses SQLAlchemy ORM

## Conventions
- Use TypeScript strict mode for all frontend code
- Python code follows PEP 8, use type hints everywhere

## Review guidelines
- All PRs must pass type checking before merge
```

## 10. 最佳实践

- 保持简洁，远低于 32KB 上限
- 用 ## 分区组织（Architecture / Conventions / Important Notes）
- 包含具体示例（代码模式、API 形状、命名约定）
- 明确说明"不要做什么"
- 列出关键路径和端口
- 随项目演进更新——过时的上下文比没有上下文更糟

## 11. 待进一步调研

1. AGENTS.md 32KB 上限是否可配置
2. 子目录 AGENTS.md 的嵌套深度限制
3. 多个兼容上下文文件同时存在时的精确优先级规则
