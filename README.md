# LDVH V4

本仓库正在建立 LDVH V4 的全新架构与规范基线。V4 不以兼容迁移 V3 为目标；当前资产是否属于 V4，必须以 V4 规则、实现与当次验证证据为准。

## 当前入口

- [`specs/`](specs/) 是 V4 当前规则源；根规范从 [`00-理念与构成.md`](specs/00-理念与构成.md) 开始。
- [`V4-架构重建基线.md`](docs/v4-architecture/V4-架构重建基线.md) 记录本轮重建范围、非继承边界和资产处置原则。
- [`archive/v3/specs/`](archive/v3/specs/) 是 V3 Specs 的历史参考，不是 V4 规则源。

## 资产边界

- 现有 `code/`、`tests/`、`hooks/`、`ldvh-base/` 以及 package 配置仍属于 V3 参考实现。它们可以用于研究问题和候选设计，但不能证明任何能力已在 V4 中 `available`、`integrated` 或 `completed`。
- `web/` 作为现有产品资产冻结保留，不在本轮 V4 架构重建范围内，也不因仓库进入 V4 而自动获得 V4 验证结论。
- 除 `archive/v3/specs/` 外，仓库中仍可能存在 V3 路径、字段或行为假设；在完成 V4 重新裁决前，均不得视为 V4 契约。

## 使用状态

当前 README 不提供旧 CLI 命令作为 V4 使用说明。V4 Helper CLI、Code 和 tests 只有在依据 V4 规范重新实现、接入并验证后，才能按实际证据声明相应状态。
