# LD Vibe Harness 项目规则

> 最后更新：2026-06-01
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness
> 生效方式：始终生效
> 规范来源：`specs/11.01-Rules机制规范.md`、`specs/03.01-Specs文档索引规范.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`
> 维护边界：本文件只作 LDVH 项目入口、项目专属硬约束和 L2 引导，不替代 specs 正式规范

## 项目入口

LDVH 定位见 `specs/00-LD-Vibe-Harness理念与纲要.md`。项目目录事实源见 `specs/01-LDVH目录说明.md`。术语见 `specs/02-LDVH术语规范.md`。specs 文档骨架和引用纪律见 `specs/03-Specs文档规范.md`。specs 文档索引和章节定位见 `specs/03.01-Specs文档索引规范.md`。

读取 specs 时可用 03.01 索引辅助定位 `specs/*.md`，但必须读取原文作判断；`specs/evals/` 与 `specs/refs/` 只有用户明确指定或任务明确要求时读取。

## 项目硬约束

不自动 commit、push、tag、release。新增或修改项目文档、Rules、规范或事实实例后，在 `ldvh-base/changes/` 记录 Change。Human Gate 由 AskUserQuestion 实现，入口见 `specs/05-Trae-Solo AskUserQuestion使用规范.md`。

## L2 引导

编辑 specs Markdown 时进入 `.trae/rules/ldvh-l2-specs-rules.md`。编辑 `ldvh-base/` YAML 时进入工作区 L0 事实模型规则。新增、修改或审计 L0/L1/L2 Rules 时，先读 `specs/11.01-Rules机制规范.md` §7，并从 `specs/*.md` 根目录正式文档反向发现 Rules 需求。

## 压缩保护

LDVH项目 | 不自动push | 改文档写Change | specs索引见03.01 | evals/refs需指定 | specs编辑进L2 | ldvh-base进事实模型L0 | Rules审计读11.01§7 | 读原文作判断
