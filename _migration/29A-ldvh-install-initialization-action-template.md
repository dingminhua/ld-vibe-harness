# 29A LDVH 安装初始化配置行动模板吸收

文件状态：migration evidence。本文记录 V3 对 V2 `33-ldvh-install-action-LDVH安装行动编排` 的受控吸收；它不安装环境插件，不修改用户级环境配置，不声明任何新的环境入口已 integrated。

## 来源

本次吸收读取并采用以下 V2 客观内容：

1. `specs/33-ldvh-install-action-LDVH安装行动编排.md`：安装、验证、首次管辖项目配置、Human Gate 和交还闭环；
2. `specs/32-environment-entry-adaptation-环境入口落地与适配检查.md`：环境落地投影、部署检查和禁止声明边界；
3. `specs/06-运行时扩展规范.md`：插件方式 / Rules 方式、canonical event、payload 透传和安装验收边界；
4. `hooks/ldvh-hooks.yaml`：环境插件 / wrapper 必须保留并透传原始 payload 给 dispatcher 的责任。

## V3 约束

吸收时按 V3 现行归口重写，而不是复制 V2：

| V3 归口 | 本次如何受约束 |
|---|---|
| `01` 保障与衔接 | 环境入口类型、安装、回滚、integrated 声明和插件 / 扩展包口径仍归 01；行动模板不得授权安装或声明生效 |
| `06` 行动模板 | 只承接 Context、Scenario、Gate、执行、验证、回写和交还结构 |
| `10` 管辖项目配置 | `LDVH-GOVERNED-PROJECTS.yaml` 字段、target-first、Git common-dir、多目标和 no-op 边界仍归 10 |
| `07` Code | 具体命令、adapter、状态检查和安装器实现属于 Code / code/docs |
| `09` 测试与验证 | 验证声明字段、完整验证边界和失败阻断仍归 09 |

## 已落账改动

1. `specs/06-行动模板基础规范.md` 新增 `ldvh_install_initialization_action_template` Code 消费入口；
2. `06` 在模板候选与迁移边界中确认 V2 `33` 可转为正式行动模板，但必须受 V3 01 / 10 / Human Gate 制约；
3. `06` 新增“LDVH 安装、初始化与管辖项目配置行动模板”，覆盖安装方式判断、初始化检查、配置位置选择、管辖项目登记、验证、回写和交还；
4. `code/ldvh_specs.py` 新增解析和负例校验；
5. `tests/code/test_ldvh_specs_validate.py` 新增可消费正例和缺 Gate / 缺插件边界 / 缺用户级候选后置的负例。

## 边界

本次明确不做：

1. 不安装、升级、禁用或卸载任何环境插件；
2. 不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录；
3. 不创建新的 `LDVH-GOVERNED-PROJECTS.yaml`；
4. 不声明 session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 V3 `rules/` 或 `skills/` 顶层机制；
6. 不把用户级配置目录候选写成当前 Code 已支持的解析能力。

## 后续

后续若要进入真实安装或配置生成，必须先按本模板触发 Human Gate，并继续满足：

1. 配置生成位置三选一：工作区根目录（推荐，默认 LDVH 安装目录上一级）、用户级 LDVH 配置目录、当前项目根目录；
2. 用户级配置目录若仍未被 `10` 和 Code resolver 支持，只能记录为后置候选；
3. 环境 Hook 必须通过对应 LDVH 插件 / 扩展包 / package 安装；
4. 真实 integrated 声明必须由自动触发、失败阻断、安装状态复现和回滚证据共同证明。
