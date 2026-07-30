# Codex adapter 参考实现（已退役）

> **退役声明**：本目录的环境 adapter 形态已被 00 §8.2（commit f88694775）废除——LDVH 的环境接入形态只有薄 Skill 与 Git Gate，接入面不存在环境 Hook、插件或 adapter 层（09 §5.1）。本目录作为历史实现记录保留，不再作为接入参考实现；新接入形态见 [specs/09-环境接入规范.md](../../../specs/09-环境接入规范.md) §5 与 [specs/33-环境安装、部署、接入与验证行动模板.md](../../../specs/33-环境安装、部署、接入与验证行动模板.md)。目录内代码与下文中的 "thin adapter"、环境 Hook 等表述均为旧学说原文，本目录的整体去留待后续清理决定。

本目录是 LDVH 仓库附带的 Codex 环境 adapter 历史参考实现，曾演示如何按旧版 09 的薄引用规则，
把一个 AI 开发环境的原生生命周期事件接入 LDVH 环境无关核心。

本目录不随 LDVH 发行物分发（见 [setup.py](../../../setup.py) 排除规则），仅在
仓库内可见。它不是 LDVH 核心的组成部分，也不构成对 Codex 环境
的官方支持声明。

## 当前接入方式

为任何 AI 开发环境接入 LDVH，请按新学说部署薄 Skill（canonical 来源 [skill/SKILL.md](../../../skill/SKILL.md)），不要按本目录的 adapter 模式开发新实现：

1. 读 [specs/09-环境接入规范.md](../../../specs/09-环境接入规范.md) §5 与 §8
2. 读 [specs/attachments/09.Att.01-环境接入面.md](../../../specs/attachments/09.Att.01-环境接入面.md)
   了解可接入的 LDVH 核心入口
3. 按 [specs/33-环境安装、部署、接入与验证行动模板.md](../../../specs/33-环境安装、部署、接入与验证行动模板.md) 完成安装、部署、接入与验证

## 历史内容（旧学说原文，仅供理解本目录代码）

### 为其它 AI 环境开发 adapter（已废弃路径）

如果你要为 Trae、Cursor、Claude Code 或其它 AI 环境开发 LDVH adapter：

1. 读 [specs/09-环境接入规范.md](../../../specs/09-环境接入规范.md) §5.1-5.6 与 §8
2. 读 [specs/attachments/09.Att.01-环境接入面.md](../../../specs/attachments/09.Att.01-环境接入面.md)
   了解可接入的 LDVH 核心入口和参考实现位置说明
3. 参考本目录 `scripts/codex_context.py` 的薄引用结构：读 config → 调核心 →
   校验响应 → 输出环境特定格式
4. 在**你自己的仓库**建立独立 Code 计划，不在 LDVH 仓库提交

### 安装后操作（旧学说原文）

完成文件安装和插件注册后，环境 Hook **不会自动生效**。需要以下额外步骤：

1. **去 AI 环境设置开启 环境 Hook** — 在目标 AI 环境（如 Cursor、Trae 等）的设置中，确认 LDVH 插件已启用，且
   `SessionStart` 环境 Hook 已被信任或允许执行。仅完成文件部署和注册并不等于 环境 Hook 已实时触发。
2. **验证 环境 Hook 是否实时生效** — 启动一次新的 cold startup 会话（非 hydrate/恢复会话），检查以下内容：
   - 启动日志中是否有 `hook_run_started` 和 `hook_run_completed` 记录
   - 执行目录中是否有对应的 环境 Hook 执行产物
   - 会话中出现的 work-context 是否能与本次实时执行记录对应
   - 如果上述任一项缺失，说明 环境 Hook 未实时触发，需要排查 AI 环境对插件的信任/启用配置

> 注意：`work-context` 可能来自 hydrate（历史上下文恢复），不能作为实时触发证据。
> 只有同一轮 cold startup 中同时存在可回指的实时执行记录和预期结果，才能确认 环境 Hook 已生效。

## 维护

本参考实现的维护由 [code/plans/codex-context-recovery.md](../../plans/codex-context-recovery.md)
承接。Codex 厂商协议变化导致的适配调整不属于 LDVH 核心变更。
