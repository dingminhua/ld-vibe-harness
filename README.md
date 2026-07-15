# LDVH V4

本仓库正在依据已经激活的 V4 规范重新建立 LDVH。V4 不以兼容迁移 V3 为目标；V3 规则、实现和测试均未自动获得 V4 身份。

## 当前入口

- [`00-理念与构成.md`](specs/00-理念与构成.md) 是 V4 根规范；[`specs/`](specs/) 中的 01–09 是当前已经完成审核并激活的基础普通规范。
- [`01-规范模型基础规范.md`](specs/01-规范模型基础规范.md) 定义正式规范及其授权附件的共同结构、关系、规则表达、渐进式披露和双语术语治理。
- [`01.Att.01-LDVH双语术语表.md`](specs/attachments/01.Att.01-LDVH双语术语表.md) 是 01 授权的当前双语术语登记。
- [`V4-工作推进总纲.md`](docs/v4-architecture/active/V4-工作推进总纲.md) 是唯一当前工作推进控制面，统一承担 V4 阶段、当前状态、Code/Web 实现规划、协作方式、Gate、验证证据、未完成边界和下一步；它不是规则源。
- [`docs/code/README.md`](docs/code/README.md) 和 [`docs/web/README.md`](docs/web/README.md) 只是各自的目录、运行和资料入口，不并行维护当前计划或状态。
- [`V4-架构重建基线.md`](docs/v4-architecture/active/V4-架构重建基线.md) 记录本轮重建范围、非继承边界和资产处置原则。
- [`V3 设计覆盖与 V4 下游审核清单`](docs/v4-architecture/investigations/V3-设计覆盖与V4下游审核清单.md) 保留 V3 历史设计问题索引，供 Human 选择具体来源时回读。
- [`archive/v3/`](archive/v3/) 保存 V3 历史资产，不是 V4 规则源、实现或验收契约。

## 资产边界

- `web/` 和 `icons/` 作为既有产品资产保留；08 已定义其后续适配边界，但现有实现不因规范激活而自动符合 V4、取得写入权威或通过验证。
- V3 的 Code、tests、hooks、事实对象、技能材料和顶层运行配置已经整体移入 `archive/v3/`，只能用于调查和选择性重新设计。
- `archive/v4-seeds/` 与 `archive/v4-experiments/` 保存已经结束的定位校准、迁移种子和早期试验；二者都不具备规则效力，也不作为当前实施输入。
- `docs/v4-architecture/` 保存当前边界、下游审核入口及历史重建记录，不是规则源。

## 使用状态

当前 00–09、Spark、WorkCase、ADR、Pitfall、Study、四份具体行动模板及四份授权附件声明为 `active`，并通过当前已实现的机械结构检查；这不替代 01 对其它变更要求的语义审核和独立复核。阶段 4 与阶段 5 已关闭；事实服务已经提供候选发现、精确读取、草案准备、单对象受控创建和完整目标 CAS 更新。V4 Code 已建立规范模型确定性基础、Helper CLI v2 契约和十项当前公开操作；默认 `compact` 响应聚合同范围重复证据，`diagnostic` 档保留逐项审计信息，L3 按精确标题边界返回原文切片。普通 wheel 与 sdist 已自包含同一发行版本绑定的规则快照；直接 wheel、无 Git 的 sdist→wheel、真实版本替换、强制重装、卸载和十项操作进程矩阵已在 macOS、Python 3.12 临时环境验证。09 与 33 已分别定义环境接入规则和安装验证行动；首个 Codex `SessionStart startup|resume` 薄 adapter 已在本机当前用户的 Codex 0.144.2 中完成安装、信任、显式配置、真实成功/失败触发及停用/恢复验证，结论不外推到其它环境或事件。

三份 2026-07-15 独立审计完成合并处置后，当前主线已经校正为：先组合已有能力建立低成本启动/恢复入口，再由 Human 选择真实工作完成跨会话 dogfood；V3 的 92 个历史事实对象只保留为可回读库存，未来仅按 Human 选定的具体来源、当前价值和用途选择性吸收，不再要求全量承接。dogfood 后再依据实测决定必要的简化，并在发布前恢复 Web V4 bridge、原生 Windows、LDVH 自身 CI 和发布准备。其它事实类型的 Web 写入 API 暂不建设。普通发行安装现已闭合当前 macOS/Python 3.12 范围；Git 跟踪的 V4 事实实例仍为 0，原生 Windows、三平台 CI、V4 Web 和首个完整 dogfood 均未完成。完整路线、当前边界、审计处置和验证证据见 [工作推进总纲](docs/v4-architecture/active/V4-工作推进总纲.md)。

## 本地构建与普通安装

仓库当前没有声明已经发布到公共 Python 包索引。要验证本地源码生成的普通发行物：

```bash
python3.12 -m pip install -e '.[dev]'
python3.12 -m build --sdist --wheel
python3.12 -m venv /tmp/ldvh-install
/tmp/ldvh-install/bin/python -m pip install dist/ld_vibe_harness-*.whl
cd /tmp
/tmp/ldvh-install/bin/ldvh capabilities
```

普通安装的 Helper 从同一 Python distribution 内已经验证的不可变规则快照读取规则，不搜索当前目录、管辖项目或相邻 checkout。事实与 Git 操作仍只作用于请求解析出的实际管辖项目。以上命令只是 POSIX 形式的本地构建示例；当前验证证据不证明 PyPI 发布、Linux、原生 Windows、环境 adapter 自动接入或三平台 CI 已完成。
