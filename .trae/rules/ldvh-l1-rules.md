# LD Vibe Harness 项目规则

> 最后更新：2026-05-31
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness

## 项目定位

LD Vibe Harness 是面向 Vibe Coding 的工程化驾驭框架，简称 LDVH。定位与理念见 `specs/00-LD-Vibe-Harness理念与纲要.md`。

## 必读入口

进入本项目处理 specs、ldvh-base、references、tools、web 或项目规则相关事项时，优先读取：

1. `specs/00-LD-Vibe-Harness理念与纲要.md`
2. `specs/01-LDVH目录说明.md`
3. `specs/02-LDVH术语规范.md`
4. `specs/03-Specs文档规范.md`

处理内部调研或规范迁移时，再按任务需要读取 `specs/evals/` 对应文档。

## 目录事实源边界

目录事实源性质声明见 `specs/01-LDVH目录说明.md` §3.2。本项目关键边界：

- `specs/` 承载 LDVH 规范体系和内部调研
- `ldvh-base/` 承载结构化生产对象实例和变更记录
- `specs/refs/` 承载外部资料引用，不能直接作为 LDVH 强制规则
- `specs-v2/` 是迁移和重构参考区，不自动替代 `specs/` 当前权威规范

## 项目专属硬约束

1. 不自动执行 commit、push、tag、release，除非用户明确要求
2. 编写或修改规范时，优先引用权威文档，不复制并维护同一规则（依据 `specs/03-Specs文档规范.md` §六）
3. 新增或修改项目文档、规则或规范后，必须在 `ldvh-base/changes/` 创建 Change YAML 记录（依据 `specs/10-事实源边界与承载规范.md` §七）

## L2 场景规则

- `ldvh-l2-specs-rules.md`：编辑 specs/ 目录下文档时生效
- `ldvh-l2-production-rules.md`：编辑 ldvh-base/ 目录下 YAML 实例时生效

## 压缩保护

LDVH项目 | 不自动push | 引用不复制 | 改文档写change | specs-v2不替代specs | L1引导L2
