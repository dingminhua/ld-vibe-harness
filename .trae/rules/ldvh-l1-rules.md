# LD Vibe Harness 项目规则

> 最后更新：2026-06-01
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness
> 生效方式：始终生效
> 规范来源：`specs/11.01-Rules机制规范.md`、`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/01-LDVH目录说明.md`、`specs/03-Specs文档规范.md`、`specs/10-事实源边界与承载规范.md`
> 维护边界：本文件只作为 LDVH 项目入口、项目专属硬约束和 L2 引导，不替代 specs 正式规范

## 项目定位

LD Vibe Harness 是面向 Vibe Coding 的工程化驾驭框架，简称 LDVH。定位与理念见 `specs/00-LD-Vibe-Harness理念与纲要.md`。

## 必读入口

进入本项目处理 specs、ldvh-base、references、tools、web 或项目规则相关事项时，优先读取：

1. `specs/00-LD-Vibe-Harness理念与纲要.md`
2. `specs/01-LDVH目录说明.md`
3. `specs/02-LDVH术语规范.md`
4. `specs/03-Specs文档规范.md`

处理 L0/L1/L2 Rules 新增、修改或审计时，必须读取 `specs/11.01-Rules机制规范.md`，并按 §七从 `specs/*.md` 根目录正式文档反向发现 Rules 需求。

处理内部调研或规范迁移时，再按任务需要读取 `specs/evals/` 对应文档。

## 目录事实源边界

目录事实源性质声明见 `specs/01-LDVH目录说明.md` §3.2。本项目关键边界：

- `specs/` 承载 LDVH 规范体系和内部调研
- `ldvh-base/` 承载结构化事实实例和变更记录
- `specs/refs/` 承载外部资料引用，不能直接作为 LDVH 强制规则
- `specs-v2/` 是迁移和重构参考区，不自动替代 `specs/` 当前权威规范

## 项目专属硬约束

1. 不自动执行 commit、push、tag、release，除非用户明确要求
2. 编写或修改规范时，优先引用权威文档，不复制并维护同一规则（依据 `specs/03-Specs文档规范.md` §七）
3. 新增或修改项目文档、规则或规范后，必须在 `ldvh-base/changes/` 创建 Change YAML 记录（依据 `specs/10-事实源边界与承载规范.md` §七）

## L2 场景规则

- `ldvh-l2-specs-rules.md`：编辑 specs/ 目录下文档时生效；L1 只负责引导该 L2，具体关联关系由 `specs/03-Specs文档规范.md` §六维护；审计 Rules 时依据 `specs/11.01-Rules机制规范.md` §七反向发现 specs 根目录文档中的 Rules 需求

事实实例编辑规则已提升至 L0 层级（`ldvh-l0-fact-model-rules.md`），适用于所有管辖项目，不在本项目 L2 中维护。

## 压缩保护

LDVH项目 | 不自动push | 引用不复制 | 改文档写change | specs-v2不替代specs | L1引导L2 | Rules审计读11.01并反向发现specs根文档 | 事实模型规则在L0
