# LDVH V4

LDVH（LD Vibe Harness）是帮助 AI 在长期项目中保持判断有据、行动可续、结果可验的工具集。它以规范模型、事实模型和行动模板为三类语义构成要素，通过 Helper CLI、环境 Hook 和 Web 三种方式交付价值。

## 快速开始

AI 在新环境中接入 LDVH 的完整流程：获取 → 安装 → 配置 → 接入 → 验证。

在项目目录中安装并启动：

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ldvh capabilities          # 查看当前 13 个公开操作
.venv/bin/ldvh-doctor                # 诊断当前环境状态
```

AI 在新环境中接入 LDVH 的完整流程见 [`specs/33-环境接入安装与验证行动模板.md`](specs/33-环境接入安装与验证行动模板.md)。当前发行物的环境无关入口清单见 [`specs/attachments/09.Att.01-环境接入面.md`](specs/attachments/09.Att.01-环境接入面.md)。

## 给 AI：接入新的开发环境

当 Human 明确要求“将 LDVH 接入当前开发环境”时：

1. 先读取[环境接入面](specs/attachments/09.Att.01-环境接入面.md)，确认当前已经交付的 LDVH 入口；
2. 再读取[环境接入规范](specs/09-环境接入规范.md)与[环境接入安装与验证行动模板](specs/33-环境接入安装与验证行动模板.md)；
3. 调查目标环境当前版本的官方或实际权威资料，确认原生事件、实际输入、结果反馈、安装位置、可触发会话范围、权限与已有用户资产；
4. 只有原生机制能够如实映射到既有 LDVH 入口时，才形成安装方案，并在 Human 授权后实施；
5. 若必须新增 manifest、启动脚本或 adapter，停止安装分支，先按目标环境资料和 Code 规范独立设计、实现与验证；不得改写既有 Hook；
6. 分别验证静态安装、LDVH 核心直调和真实环境触发；不能承接时，如实报告 `unverified` 或 `unsupported` 的范围。

跨工作区安装只表示范围内会话会取得基础规则引导，不表示项目已纳入管辖或项目事实已被读取。不要把文件存在、手工调用成功或静态检查通过写成环境已自动触发；不要预先注册暂未得到目标环境实际支持的事件或 Hook。

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
