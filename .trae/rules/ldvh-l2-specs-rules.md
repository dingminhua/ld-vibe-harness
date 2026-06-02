# LDVH Specs 文档编辑规则

> 层级：L2 场景规则
> 适用项目：ld-vibe-harness
> 生效方式：globs — 编辑 specs/ 目录下 Markdown 文件时生效
> 规范来源：`specs/03-Specs文档规范.md`、`specs/03.01-Specs文档索引规范.md`、`specs/01-LDVH目录说明.md`、`specs/02-LDVH术语规范.md`、`specs/11.01-Rules机制规范.md`、`specs/22-Change-变更记录.md`、`specs/22.01-Rules.md`
> 维护边界：本文件只作 specs 编辑入口摘要，不替代 specs 正式规范

## 编辑入口

编辑 specs Markdown 时，文档骨架、章节编号、标题层级、引用纪律、机制落地关系和 refs/evals 边界以 `specs/03-Specs文档规范.md` 为准；编号分区以 `specs/01-LDVH目录说明.md` 为准；术语以 `specs/02-LDVH术语规范.md` 为准。

## 索引与读取

specs 文档质量检查依据 `specs/03.01-Specs文档索引规范.md`，默认只覆盖 `specs/*.md`。定位 specs 文档和章节时，通过搜索 Markdown 标题定位候选文档和章节行号，再按行范围读取原文片段。规范判断必须读取原文，不得间接判断。`specs/evals/`、`specs/refs/` 只有用户明确指定时读取。

## 场景约束

不得设置"反向边界"章节。不得复制其他权威文档规则正文，只能引用权威文档章节。`specs/refs/` 不得引用 specs 目录内文件；refs 只承载外部资料客观事实。新增、修改或审计 Rules 时，依据 `specs/11.01-Rules机制规范.md` §7 从 `specs/*.md` 反向发现需求。编辑 specs 后属于 22 §3.3 准入变更，按 22.01 §5 完成提交准备后执行 commit。

## 压缩保护

骨架引用03 | 搜索标题定位 | 编号引用01 | 术语引用02 | 按行范围读原文 | refs不反向引用specs | evals/refs需指定 | Rules审计读11.01§7 | 只写入口不复制正文 | specs编辑后按22§3.3+22.01§5提交
