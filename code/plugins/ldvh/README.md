# Codex adapter 参考实现

本目录是 LDVH 仓库附带的 **Codex 环境 adapter 参考实现**，演示如何按
[specs/09-环境接入规范.md §5.2](../../../specs/09-环境接入规范.md) 的薄引用规则，
把一个 AI 开发环境的原生生命周期事件接入 LDVH 环境无关核心。

本目录不随 LDVH 发行物分发（见 [setup.py](../../../setup.py) 排除规则），仅在
仓库内可见。它是参考实现，不是 LDVH 核心的组成部分，也不构成对 Codex 环境
的官方支持声明。

## 为其它 AI 环境开发 adapter

如果你要为 Trae、Cursor、Claude Code 或其它 AI 环境开发 LDVH adapter：

1. 读 [specs/09-环境接入规范.md](../../../specs/09-环境接入规范.md) §5.1-5.6 与 §8
2. 读 [specs/attachments/09.Att.01-环境接入面.md](../../../specs/attachments/09.Att.01-环境接入面.md)
   了解可接入的 LDVH 核心入口和参考实现位置说明
3. 参考本目录 `scripts/codex_context.py` 的薄引用结构：读 config → 调核心 →
   校验响应 → 输出环境特定格式
4. 在**你自己的仓库**建立独立 Code 计划，不在 LDVH 仓库提交

## 维护

本参考实现的维护由 [code/plans/codex-context-recovery.md](../../plans/codex-context-recovery.md)
承接。Codex 厂商协议变化导致的适配调整不属于 LDVH 核心变更。
