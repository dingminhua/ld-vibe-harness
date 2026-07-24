# LDVH V4

LDVH（LD Vibe Harness）是帮助 AI 在长期项目中保持判断有据、行动可续、结果可验的工具集。它以规范模型、事实模型和行动模板为三类语义构成要素，通过 Helper CLI、环境 Hook 和 Web 三种方式交付价值。

## 安装 LDVH 核心

AI 在新环境中接入 LDVH 的完整流程：获取 → 安装 → 配置 → 接入 → 验证。

交给新环境时，应提供固定的发行版本或 Git commit、LDVH 的绝对路径，以及目标工作区和工作对象的绝对路径；不得以含未提交改动的工作目录作为交付版本。

在该固定版本的项目目录中安装 LDVH 核心：

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ldvh capabilities          # 查看当前可用公开操作
```

## 只读诊断已有工作区

`ldvh-doctor` 必须显式传入管辖配置所在工作区、目标项目或 worktree，以及 Helper 可执行文件的绝对路径：

```bash
.venv/bin/ldvh-doctor \
  --workspace-root "<管辖配置所在工作区的绝对路径>" \
  --work-object-locator "<目标项目或 worktree 的绝对路径>" \
  --helper-executable "<LDVH_ROOT>/.venv/bin/ldvh"
```

Doctor 只诊断当前发行物、显式工作区和已交付入口的静态状态；它不扫描目标 AI 环境，也不证明环境已经接入、自动触发或完成真实验证。

AI 在新环境中接入 LDVH 的完整流程见 [`specs/33-环境接入安装与验证行动模板.md`](specs/33-环境接入安装与验证行动模板.md)。当前发行物的环境无关入口清单见 [`specs/attachments/09.Att.01-环境接入面.md`](specs/attachments/09.Att.01-环境接入面.md)。

## 给 AI：接入新的开发环境

应在目标开发环境中向 AI 发出本提示。若 LDVH 当前规则源不在该工作区，必须向 AI 提供其绝对路径或当前已安装发行物的位置；不得假定目标工作区就是规则源。

当 Human 明确要求“将 LDVH 接入当前开发环境”时：

除非 Human 明确指定不同的目标环境或工作区，AI 应把当前可观察的运行环境和工作区作为目标，先通过只读观察、当前环境资料和实际安装对象取得环境名称、版本、运行位置、现有配置与用户资产；不得先要求 Human 转述这些可观察的信息。

1. 先读取[环境接入面](specs/attachments/09.Att.01-环境接入面.md)，确认当前已经交付的 LDVH 入口；
2. 再读取[环境接入规范](specs/09-环境接入规范.md)与[环境接入安装与验证行动模板](specs/33-环境接入安装与验证行动模板.md)；
3. 调查目标环境当前版本的官方或实际权威资料，确认原生事件、实际输入、结果反馈、安装位置、可触发会话范围、权限与已有用户资产；
4. 只有原生机制能够如实映射到既有 LDVH 入口时，才形成安装方案，并在 Human 授权后实施；
5. 若必须新增 manifest、启动脚本或 adapter，停止安装分支，先按目标环境资料和 Code 规范独立设计、实现与验证；不得改写既有 Hook；
6. 分别验证静态安装、LDVH 核心直调和真实环境触发；不能承接时，如实报告 `unverified` 或 `unsupported` 的范围。

跨工作区安装只表示范围内会话会取得基础规则引导，不表示项目已纳入管辖或项目事实已被读取。不要把文件存在、手工调用成功或静态检查通过写成环境已自动触发；不要预先注册暂未得到目标环境实际支持的事件或 Hook。

只有目标不可观察或无法识别、Human 指定不同目标，或者需要选择安装范围、授权写入、接受权限或信任、处理冲突时，才向 Human 请求相应信息或决定。

## 规范架构

- [`specs/00-理念与构成.md`](specs/00-理念与构成.md) — 根规范，定义存在理由、设计理念、三类构成要素、V1-V8 价值标准
- [`specs/`](specs/) — 01–09 基础规范、20+ 事实类型与行动模板规范

## 资产边界

- `code/` — LDVH 确定性执行层（Helper CLI、Hook、Git Gate）
- `web/` — 面向 Human 的交互呈现层
- `ldvh-base/` — V4 事实对象载体目录

## 使用状态

当前 00–09、Spark、WorkCase、ADR、Pitfall、Study、四份行动模板及五份授权附件声明为 `active`。Helper CLI v2 契约已实现 13 项公开操作，支持 `compact` 和 `diagnostic` 两种响应档。09 与 33 已定义环境接入规则和安装验证行动，首个 Codex 薄 adapter 已在 macOS Codex 0.144.2 完成真实触发验证。

## 本地构建

```bash
python3.12 -m pip install -e '.[dev]'
python3.12 -m build --sdist --wheel
```
