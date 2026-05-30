# LD Vibe Harness 项目规则

> 最后更新：2026-05-30
> 层级：L1 项目规则
> 适用项目：ld-vibe-harness

## 项目定位

LD Vibe Harness 是面向 Vibe Coding 的工程化驾驭框架，围绕 Git 文件事实源、AI 行动模型、Harness 生产对象、Human Gate 和工具辅助能力，帮助 AI 稳定读取、受控执行、留下证据并按边界回写项目事实。

## 必读入口

进入本项目处理 specs、ldvh-base、references、tools、web 或项目规则相关事项时，优先读取：

1. `specs/00-LD-Vibe-Harness理念与纲要.md`
2. `specs/01-specs文档结构规范.md`
3. `specs/02-LDVH目录说明.md`
4. `specs/03-事实源边界与承载规范.md`

处理内部调研、规范迁移或 Git 管理事项时，再按任务需要读取 `specs/evals/` 对应文档。

## 目录事实源边界

- `specs/` 承载 LD Vibe Harness 规范体系和内部调研。
- `ldvh-base/` 承载结构化生产对象实例和变更记录。
- `references/` 承载外部资料和第三方参考，不能直接作为 LD Vibe Harness 强制规则。
- `specs-v2/` 是迁移和重构参考区，不自动替代 `specs/` 当前权威规范。
- `web/` 与 `tools/` 是工具实现目录，工具输出不能替代 Git 文件事实源。

## specs 文档约束

- `00` 是总纲。
- `01-07` 是基础规范区。
- `10-39` 是 Harness 生产对象规范区。
- `40-69` 是 Harness 行动模型规范区。
- `70-89` 是内部调研可选编号段，当前项目评估文档统一放在 `specs/evals/`。
- `specs/evals/` 是项目评估区，不直接构成强制执行规则。
- `specs/refs/` 是外部资料引用区，不直接成为 LDVH 强制规则。
- 项目评估结论只有进入 `01-69` 正式规范区间或 ADR 后，才成为稳定规则。

## Human Gate

以下事项应暂停并提醒用户确认：

1. 改变 LD Vibe Harness 理念、价值标准、五类构成要素或基础规范权威领域；
2. 新增、删除、重命名或重排 specs 编号；
3. 将 `specs/evals/` 项目评估结论升级为正式规范或 ADR；
4. 改变事实源权威位置、目录事实源性质或对象承载位置；
5. 将 push、tag、release 等远程 Git 操作交由 AI 自动执行；
6. 新增、删除或改变项目规则、Skill、Agent 等 AI 行动入口。

## 变更记录要求

新增或修改项目文档、规则或规范后，必须在 `ldvh-base/changes/` 创建 Change YAML 记录。文件名使用 `YYYYMMDDHHmmss.yaml`，内容应包含变更摘要、原因、影响文件和验证结果。

## 执行注意事项

- 不依赖聊天记忆作为事实源。
- 不把工具缓存、命令输出、数据库派生视图或 UI 状态作为最终事实源。
- 不自动执行 commit、push、tag、release，除非用户明确要求。
- 编写或修改规范时，优先引用权威文档，不复制并维护同一规则。
