# 30A 环境插件实现域准备

文件状态：implementation-domain plan。本文记录 V3 对环境插件化接入的实现域准备；它不安装环境插件，不修改用户级环境配置，不声明任何新的环境 Hook 已 integrated，也不恢复 `rules/` 或 `skills/` 顶层机制。

## 背景

Human 已确认 V3 不再保留 `rules/` 和 `skills/` 顶层目录机制，同时要求所有支持 Hook 的协作环境都以插件、扩展包或 package 方式安装 LDVH 环境 Hook，而不是直接写入环境 Hook 系统文件。

当前 V3 已有：

1. `specs/01-保障与衔接.md` 的环境入口和 Hook 分类；
2. `specs/06-行动模板基础规范.md` 的行动模板父层边界和 `specs/30-LDVH安装初始化管辖项目配置行动模板.md` 的 LDVH 安装、初始化与管辖项目配置行动模板；
3. `code/runtime_adapter.py`、`code/session_start.py`、`code/pre_tool_use.py`、`code/completion_claim.py` 的 manual-ready 入口；
4. `code/environment_status.py` 与 `code/environment_entry_audit.py` 的状态审计；
5. `code/docs/01-Git-Commit-and-Hook-Practice.md` 的 Git commit-msg Hook 实践。

缺口是：环境插件本身的实现实践需要进入 Code 实现域，而不是继续散落在 README、迁移记录或 specs 正文。

## 本阶段处理

本阶段新增 `code/docs/02-Environment-Plugin-Practice.md`，明确：

1. 所有支持 Hook 的协作环境必须通过 LDVH 插件、扩展包或 package 承载环境 Hook；
2. 插件只做薄 shim，核心逻辑留在 LDVH Code；
3. shim 只调用 V3 `code/runtime_adapter.py` 或稳定 Code 入口；
4. 状态检查必须识别 installed、enabled、trusted、target path、LDVH root 和 stale V2 path；
5. 只有真实触发、稳定 payload、失败处理、安装状态、回滚方式和测试证据齐备时，才可声明 integrated；
6. 卸载只能移除或禁用 LDVH 自己写入的指针，并保留用户原有配置和非 LDVH 资产；
7. 当前不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录。

## 与 specs 的边界

本阶段不新增 formal spec，也不修改构成要素、环境入口状态闭集、事实对象字段、管辖项目配置契约或 Human Gate 规则。

`code/docs/02-Environment-Plugin-Practice.md` 是实现域文档，只承接 specs 已定义的需求和边界。若后续发现 specs 需求或契约不足，应另走 specs 变更和 Human Gate，不得由 Code 文档反向改写 specs。

## 后续进入条件

后续要进入真实环境插件实装前，必须先满足：

1. Human 指定目标环境和写入位置；
2. 明确插件包、manifest、Hook 配置和 shim 文件；
3. 明确 lifecycle event 到 V3 runtime event 的 payload 映射；
4. 明确安装、trust、禁用、卸载和回滚步骤；
5. 明确可阻断事件和 diagnostic-only 事件；
6. 提供 status、正例、负例和 rollback 测试；
7. 通过 Human Gate 后再安装或升级真实插件。

## 本阶段不做

1. 不创建真实插件包；
2. 不安装、升级、禁用或卸载任何环境插件；
3. 不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录；
4. 不声明 session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制；
6. 不修改现有管辖项目配置文件位置策略。

## 验证

本阶段使用 targeted validation：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 -m pytest tests/code/test_ldvh_specs_validate.py -q -k "environment_plugin_practice or current_specs_validate"
git diff --check
```

这些验证只证明文档边界、正式 specs 诊断和新增测试通过，不证明真实环境插件已安装或自动触发。
