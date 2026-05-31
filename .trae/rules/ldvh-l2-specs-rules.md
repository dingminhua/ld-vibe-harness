# LDVH Specs 文档编辑规则

> 层级：L2 场景规则
> 适用项目：ld-vibe-harness
> 生效方式：globs — 编辑 specs/ 目录下 Markdown 文件时生效
> 规范来源：`specs/03-Specs文档规范.md`、`specs/01-LDVH目录说明.md`、`specs/02-LDVH术语规范.md`、`specs/11.01-Rules机制规范.md`
> 维护边界：本文件只作为 specs 编辑入口摘要，不替代 specs/ 正式规范；本文与 specs 文档的机制关系依据 `specs/03-Specs文档规范.md` §六维护

## 文档骨架

编辑 specs/ 下正式规范文档时，头部必须包含：创建日期、定位、适用范围、上位依据。00 总纲可不声明上位依据。子文档须声明所属主文档和关系。依据 `specs/03-Specs文档规范.md` §五。

## 引用纪律

不得复制其他权威文档的规则正文，只能写"依据权威文档 §Y"。依据 `specs/03-Specs文档规范.md` §七。

## 编号分区

文档编号必须符合 `specs/01-LDVH目录说明.md` §四 的编号分区。新增或调整编号属于规范体系变更，应评估 Human Gate。

## 术语

使用机制英文专名 Rules、Skill、Agent、Tools、Web，不使用裸中文替代。中文"规则""技能""代理""智能体""程序""展示"等词不得裸用。依据 `specs/02-LDVH术语规范.md` §四、§五。

## 反向边界

不得设置"不进入本文""边界说明"等反向边界章节。依据 `specs/03-Specs文档规范.md` §五。

## refs 反向引用

specs/refs/ 下的文档不得引用 specs/ 目录内的任何文件，包括路径引用、关联规范声明和依据引用。依据 `specs/01-LDVH目录说明.md` §3.3.1。

## Rules 审计

新增、修改或审计 L0/L1/L2 Rules 时，必须依据 `specs/11.01-Rules机制规范.md` §七读取 `specs/*.md` 根目录正式文档，反向发现 Rules 需求；普通 specs 文档按 `specs/03-Specs文档规范.md` §六判断，事实模型和行动模型通过 NN.01-Rules.md 模型实践子文档承接。Rules 文件只保留入口摘要和权威 specs 引用，不复制 specs 正文。
