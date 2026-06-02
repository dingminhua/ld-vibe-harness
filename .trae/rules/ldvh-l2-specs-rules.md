# LDVH Specs 文档编辑规则

> 层级：L2 场景规则
> 适用项目：ld-vibe-harness
> 生效方式：globs — 编辑 specs/ 目录下 Markdown 文件时生效
> 规范来源：`specs/03-Specs文档规范.md`、`specs/03.01-Specs文档索引规范.md`、`specs/01-LDVH目录说明.md`、`specs/02-LDVH术语规范.md`、`specs/11.01-Rules机制规范.md`
> 维护边界：本文件只作 specs 编辑入口摘要，不替代 specs 正式规范

## 编辑入口

编辑 specs Markdown 时，文档骨架、章节编号、标题层级、引用纪律、机制落地关系和 refs/evals 边界以 `specs/03-Specs文档规范.md` 为准；编号分区以 `specs/01-LDVH目录说明.md` 为准；术语以 `specs/02-LDVH术语规范.md` 为准。

## 索引与读取

specs 文档索引依据 `specs/03.01-Specs文档索引规范.md`，默认只覆盖 `specs/*.md`。定位 specs 文档和章节时，先尝试使用 specs 索引程序或其输出定位候选文档和章节行号，再按索引中的路径和行号读取原文片段；索引缺失、过期或不可用时，回退到标题搜索和行范围读取。规范判断必须读取原文，不得只读索引而不读原文。`specs/evals/`、`specs/refs/` 只有用户明确指定时读取。

## 场景约束

不得设置“反向边界”章节。不得复制其他权威文档规则正文，只能引用权威文档章节。`specs/refs/` 不得引用 specs 目录内文件；refs 只承载外部资料客观事实。新增、修改或审计 Rules 时，依据 `specs/11.01-Rules机制规范.md` §7 从 `specs/*.md` 反向发现需求。

## 压缩保护

骨架引用03 | 索引优先定位 | 编号引用01 | 术语引用02 | 索引不可用才搜索回退 | 规范判断读原文 | refs不反向引用specs | evals/refs需指定 | Rules审计读11.01§7 | 只写入口不复制正文
