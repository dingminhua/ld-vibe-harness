# LD Vibe Harness 项目规则

> 最后更新：2026-06-01
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness
> 生效方式：始终生效
> 规范来源：`specs/11.01-Rules机制规范.md`、`specs/03.01-Specs文档索引规范.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`
> 维护边界：本文件只作 LDVH 项目入口、项目硬约束和 L2 引导，不替代 specs 正式规范

## 入口

LDVH 定位见 00，目录见 01，术语见 02，specs 骨架和引用纪律见 03，specs 索引和章节定位见 03.01。读取 specs 先搜索 Markdown 标题并按行范围读原文，可用 03.01 辅助定位 `specs/*.md`；evals/refs 仅在用户明确指定或任务明确要求时读取。

## 硬约束

不自动 commit、push、tag、release。新增或修改项目文档、Rules、规范或事实实例后，在 `ldvh-base/changes/` 记录 Change。Human Gate 由 AskUserQuestion 实现，入口见 05。

## L2 引导

编辑 specs Markdown 时进入 `.trae/rules/ldvh-l2-specs-rules.md`。编辑 `ldvh-base/` YAML 时进入工作区 L0 事实模型规则。新增、修改或审计 L0/L1/L2 Rules 时，先读 11.01 §7，并从 `specs/*.md` 反向发现 Rules 需求。

## 压缩保护

LDVH | 不自动push | 改文档写Change | specs标题搜索+03.01辅助 | evals/refs需指定 | specs进L2 | ldvh-base进事实模型L0 | Rules审计读11.01§7 | 读原文判断
