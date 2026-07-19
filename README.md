# LDVH V4

本仓库依据已经激活的 V4 规范建设 LDVH。当前行为、数据模型和验证结论均以 V4 规则源、当前工作树和当次验证为准。

## 当前入口

- [`00-理念与构成.md`](specs/00-理念与构成.md) 是 V4 根规范；[`specs/`](specs/) 中的 01–09 是当前已经完成审核并激活的基础普通规范。
- [`01-规范模型基础规范.md`](specs/01-规范模型基础规范.md) 定义正式规范及其授权附件的共同结构、关系、规则表达、渐进式披露和双语术语治理。
- [`01.Att.01-LDVH双语术语表.md`](specs/attachments/01.Att.01-LDVH双语术语表.md) 是 01 授权的当前双语术语登记。
- `code/`、`web/` 与各自的 tests 仅实现和验证当前 Specs 定义的边界；它们不构成规则源或并行事实源。

## 资产边界

- `web/` 和 `icons/` 作为既有产品资产保留；08 已定义其后续适配边界，但现有实现不因规范激活而自动符合 V4、取得写入权威或通过验证。
- `ldvh-base/` 是当前 V4 事实对象的唯一载体目录；对象必须按 05 和具体类型规范经受控能力创建、读取或更新。

## 使用状态

当前 00–09、Spark、WorkCase、ADR、Pitfall、Study、四份具体行动模板及四份授权附件声明为 `active`，并通过当前已实现的机械结构检查；这不替代 01 对其它变更要求的语义审核和独立复核。阶段 4 与阶段 5 已关闭；事实服务已经提供候选发现、精确读取、草案准备、单对象受控创建和完整目标 CAS 更新。V4 Code 已建立规范模型确定性基础、Helper CLI v2 契约和十项当前公开操作；默认 `compact` 响应聚合同范围重复证据，`diagnostic` 档保留逐项审计信息，L3 按精确标题边界返回原文切片。普通 wheel 与 sdist 已自包含同一发行版本绑定的规则快照；直接 wheel、无 Git 的 sdist→wheel、真实版本替换、强制重装、卸载和十项操作进程矩阵已在 macOS、Python 3.12 临时环境验证。09 与 33 已分别定义环境接入规则和安装验证行动；首个 Codex `SessionStart startup|resume` 薄 adapter 已在本机当前用户的 Codex 0.144.2 中完成安装、信任、显式配置、真实成功/失败触发及停用/恢复验证，结论不外推到其它环境或事件。

当前管辖、能力发现、F0/F1 和规则来源已经完成组合验证：能够确定项目、十项能力及当前事实范围，但不证明真实责任 resume，原样响应也不宜无条件全部注入。当前待推进事项及其状态只以 `ldvh-base/` 中的事实对象为准。

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
