# LDVH V4

本仓库正在依据已经激活的 V4 规范重新建立 LDVH。V4 不以兼容迁移 V3 为目标；V3 规则、实现和测试均未自动获得 V4 身份。

## 当前入口

- [`00-理念与构成.md`](specs/00-理念与构成.md) 是 V4 根规范；[`specs/`](specs/) 中的 01–08 是当前已经完成审核并激活的普通规范。
- [`01-规范模型基础规范.md`](specs/01-规范模型基础规范.md) 定义正式规范及其授权附件的共同结构、关系、规则表达、渐进式披露和双语术语治理。
- [`01.Att.01-LDVH双语术语表.md`](specs/attachments/01.Att.01-LDVH双语术语表.md) 是 01 授权的当前双语术语登记。
- [`V4-工作推进总纲.md`](docs/v4-architecture/V4-工作推进总纲.md) 是唯一当前工作推进控制面，统一承担 V4 阶段、当前状态、Code/Web 实现规划、协作方式、Gate、验证证据、未完成边界和下一步；它不是规则源。
- [`docs/code/README.md`](docs/code/README.md) 和 [`docs/web/README.md`](docs/web/README.md) 只是各自的目录、运行和资料入口，不并行维护当前计划或状态。
- [`V4-架构重建基线.md`](docs/v4-architecture/V4-架构重建基线.md) 记录本轮重建范围、非继承边界和资产处置原则。
- [`V3 设计覆盖与 V4 下游审核清单`](docs/v4-architecture/V3-设计覆盖与V4下游审核清单.md) 保留尚未完成的 V3 设计内容审核入口。
- [`archive/v3/`](archive/v3/) 保存 V3 历史资产，不是 V4 规则源、实现或验收契约。

## 资产边界

- `web/` 和 `icons/` 作为既有产品资产保留；08 已定义其后续适配边界，但现有实现不因规范激活而自动符合 V4、取得写入权威或通过验证。
- V3 的 Code、tests、hooks、事实对象、技能材料和顶层运行配置已经整体移入 `archive/v3/`，只能用于调查和选择性重新设计。
- `archive/v4-seeds/` 与 `archive/v4-experiments/` 保存已经结束的定位校准、迁移种子和早期试验；二者都不具备规则效力，也不作为当前实施输入。
- `docs/v4-architecture/` 保存当前边界、下游审核入口及历史重建记录，不是规则源。

## 使用状态

当前 00–08 及三份授权附件已经激活；这只表示相应规则完成审核。V4 Code 已建立规范模型确定性基础、Helper CLI 基础契约，以及 `read-specification-candidates`、`read-specification-content` 和 `resolve-governance-scope` 三项公开操作；Web 已建立首批自有 API 特征测试和浏览器表现基线。自然语言规则的语义和适用性由 AI 依据当前来源判断；Code 不得解释规则，只执行来源已定义的结构化契约。当前仍没有具体事实类型、事实消费与回写、行动模板执行、环境接入或 V4 Web 适配完成声明；完整路线、当前并行边界和验证证据见 [工作推进总纲](docs/v4-architecture/V4-工作推进总纲.md)。
