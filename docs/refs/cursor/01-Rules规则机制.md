# Cursor Rules 规则机制

> 创建日期：2026-06-08
> 来源：Cursor 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则
> 官方地址：https://docs.cursor.com/context/rules

---

## 1. 结论摘要

Cursor Rules 支持用户级和项目级两级体系。项目规则存放在 .cursor/rules/ 目录下，使用 .mdc 文件格式（Markdown with Context），支持 Always、Auto Attached、Agent Requested 和 Manual 四种触发类型。.cursorrules 文件已废弃，推荐改用 .cursor/rules/ 目录。User Rules 在 Cursor Settings 中配置，跨所有项目生效。四种规则类型通过 alwaysApply、globs 和 description 字段组合控制触发方式。

## 2. 官方定位

Rules 用于为 AI 助手定义项目级或用户级的行为指令，控制代码生成风格、技术栈约束、架构决策等。这是 Cursor 区别于其他 AI IDE 的核心特性之一。

## 3. .cursorrules 文件（已废弃）

- 位置：项目根目录下的 .cursorrules 文件
- 格式：纯文本/Markdown，无特殊结构要求
- 作用域：整个项目，所有对话自动加载
- 状态：Cursor 官方已将其标记为 deprecated，推荐改用 .cursor/rules/ 目录下的 Project Rules
- 转换方式：将 .cursorrules 内容拆分为多个 .mdc 文件放入 .cursor/rules/ 目录

## 4. .cursor/rules/ 目录（Project Rules，当前推荐）

- 位置：项目根目录下 .cursor/rules/ 目录
- 文件格式：.mdc 文件（Markdown with Context），每个文件定义一条规则
- 文件结构：

```
.cursor/rules/
├── always-apply.mdc        # Always 类型
├── typescript-style.mdc    # Auto Attached 类型
├── database-expert.mdc     # Agent Requested 类型
└── debug-helper.mdc        # Manual 类型
```

## 5. .mdc 文件格式

```markdown
---
description: 描述这条规则的用途
globs: **/*.ts, **/*.tsx
alwaysApply: true
---

# 规则内容

这里写具体的规则指令，支持 Markdown 格式。
```

关键字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| description | string | 规则描述，Agent Requested 和 Manual 类型必填 |
| globs | string | 文件匹配模式（逗号分隔），Auto Attached 类型必填 |
| alwaysApply | boolean | 是否始终应用，Always 类型设为 true |

## 6. 四种规则类型

| 类型 | 触发方式 | alwaysApply | globs | description | 典型用途 |
|------|----------|-------------|-------|-------------|----------|
| Always | 每次对话自动加载 | true | 不需要 | 可选 | 项目全局规范、技术栈声明 |
| Auto Attached | 当编辑的文件匹配 globs 时自动加载 | false | 必填 | 可选 | 特定文件类型的风格规则 |
| Agent Requested | Agent 根据 description 判断是否需要时自动加载 | false | 不需要 | 必填 | 领域专家规则 |
| Manual | 用户通过 @rules 手动引用 | false | 不需要 | 必填 | 特定场景的调试/审查规则 |

详细说明：

- **Always**：类似旧版 .cursorrules，所有对话都会注入。适合放项目级强制规范。不宜过多，否则会占用上下文窗口。
- **Auto Attached**：根据文件路径/扩展名匹配。例如 `globs: **/*.py` 会在编辑 Python 文件时自动加载对应的 Python 编码规范。
- **Agent Requested**：Agent 在处理请求时，会扫描所有 Agent Requested 规则的 description，判断当前任务是否相关。如果相关则自动加载。
- **Manual**：不会自动加载，用户必须在对话中通过 @rules 明确引用才会生效。

## 7. User Rules（用户级规则）

- 配置位置：Cursor Settings > General > Rules for AI（文本框）
- 作用域：跨所有项目生效
- 格式：纯文本
- 典型用途：个人编码偏好

## 8. 规则加载优先级

1. User Rules（始终加载）
2. Always 类型 Project Rules（始终加载）
3. Auto Attached Project Rules（按文件匹配加载）
4. Agent Requested Project Rules（Agent 按需加载）
5. Manual Project Rules（用户手动引用）

## 9. 与 Trae Rules 的关键差异

| 能力 | Trae Rules | Cursor Rules |
|------|-----------|--------------|
| 文件格式 | .md（Markdown） | .mdc（Markdown with Context） |
| 触发类型 | 4 种（始终/指定文件/智能/手动） | 4 种（Always/Auto Attached/Agent Requested/Manual） |
| 智能触发 | description 字段 | description 字段（Agent Requested） |
| 文件匹配 | globs 字段 | globs 字段（Auto Attached） |
| 旧版兼容 | AGENTS.md / CLAUDE.md | .cursorrules（已废弃） |
| 子目录规则 | 支持 | 不支持 |

## 10. 待进一步调研

1. .mdc 文件的完整 frontmatter 字段列表
2. Agent Requested 规则的 description 匹配算法
3. 多条 Always 规则的加载顺序和上下文占用
