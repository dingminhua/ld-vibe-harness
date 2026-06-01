# Trae @SOLO Coder 斜杠命令 + 上下文工具 完整使用手册

> 创建日期：2026-05-14
> 来源：Trae 官方文档
> 定位：外部资料引用，不直接成为 LDVH 强制规则

---

## 1. 基础概念

| 符号 | 作用 | 示例 |
|------|------|------|
| `/` 斜杠命令 | 控制 AI 行为（计划、规范、调试、解释等） | `/plan 实现边池计算` |
| `#` 上下文工具 | 给 AI 喂参考资料（文件、文档、报错、网页等） | `#File:lib/main.dart` |

**最佳实践**：`/命令` + 需求 + `#上下文` 组合使用。

---

## 2. 斜杠命令 / 完整用法

### /plan — 先做计划再写代码（最常用）

列出修改文件、步骤、风险，不乱改代码。

```
/plan 帮我实现 Flutter 上拉加载更多列表
```

### /spec — 生成规范文档（严谨开发）

生成 spec.md 规范、接口定义、任务清单、验收标准。

```
/spec 设计用户登录模块
```

### /continue — 继续中断的任务

AI 卡住、停止、断网后继续执行。

```
/continue
```

### /cancel — 取消当前任务

AI 跑偏时立即停止所有操作。

```
/cancel
```

### /debug — 自动排查错误

读取报错、定位原因、自动修复。

```
/debug 列表滑动卡顿
```

### /explain — 解释代码

解释选中代码或文件逻辑。

```
/explain
```

### /docs — 生成项目文档

生成 README、API 文档、注释。

```
/docs 生成项目 README
```

### /lint — 代码规范检查与修复

格式化、命名规范、const 优化。

```
/lint 格式化 lib 目录
```

### /clear — 清空上下文

新开任务，避免旧对话干扰。

```
/clear
```

### /help — 查看所有命令

查看内置命令帮助。

```
/help
```

---

## 3. 上下文工具 # 完整用法

| 工具 | 作用 | 示例 |
|------|------|------|
| `#File` | 指定单个文件 | `#File:lib/main.dart` |
| `#Folder` | 指定文件夹 | `#Folder:lib/network` |
| `#Doc` | 使用内置文档库 | `#Doc:Flutter/Dart API` |
| `#Problems` | 引入编辑器报错 | `#Problems` |
| `#Web` | 引用网页内容 | `#Web:https://docs.flutter.dev` |
| `#Code` | 引用代码片段 | `#Code` |
| `#Workspace` | 全项目上下文 | `#Workspace` |
| `#Rule` | 使用自定义规则 | `#Rule` |
| `#PastChats` | 引用历史对话 | `#PastChats` |

---

## 4. 命令组合模板

### 模板1：新功能开发（最稳流程）

```
/spec 开发用户列表页面 #Doc:Flutter/Dart API
/plan 按 spec 实现页面 #Folder:lib/user
/continue 开始写代码
/lint 格式化代码 #Folder:lib/user
```

### 模板2：现有功能迭代（安全修改）

```
/plan 给列表添加下拉刷新 #File:lib/user/list.dart
/continue 实现功能
/lint 检查规范 #File:lib/user/list.dart
```

### 模板3：Bug 快速修复

```
/debug 修复报错 #File:lib/network/dio.dart #Problems
/explain 解释修复原因 #File:lib/network/dio.dart
```

### 模板4：代码审查 + 优化

```
/explain 分析代码 #File:lib/provider/todo.dart
/lint 优化规范 #File:lib/provider/todo.dart
/plan 进一步性能优化 #File:lib/provider/todo.dart
```

### 模板5：一键生成完整文档

```
/docs 生成 README + API 文档 #Workspace
/lint 统一所有文档格式 #Workspace
```

---

## 5. MCP 快捷调用

### Sequential Thinking（链式思考）

```
@Builder with MCP
请使用 Sequential Thinking 分步解决：
问题：XXX
```

详细模板见 [01-Sequential-Thinking使用模板.md](01-Sequential-Thinking使用模板.md)。

### Context7（官方最新文档）

```
请使用 context7 查 Flutter 最新文档
```

> ⚠️ Context7 需网络通畅，详见 00号文档 §2.4。

---

## 6. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Cmd/Ctrl + Shift + M` | 打开 MCP 设置 |
| `Cmd/Ctrl + K` | 选中代码快速提问 |
| `Cmd/Ctrl + I` | 行内 AI 编辑 |
| `Cmd/Ctrl + Enter` | 发送对话 |

---

## 7. 最佳实践规则

1. 任何任务先 `/plan` 或 `/spec`
2. 写代码必带 `#File` / `#Folder`
3. 查官方文档用 `#Doc` 或 context7
4. 报错必用 `#Problems`
5. 任务中断直接 `/continue`
6. AI 跑偏立即 `/cancel`
