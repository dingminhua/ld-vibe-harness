# LDVH Lifecycle Check Hook

## 定位

本 Hook 资产用于定义 LDVH 生命周期检查入口的最小文本能力资产，覆盖原生 Hook、Skill 模拟、Command 手动触发、CI 触发和人工检查清单等承载方式。

本文件不声明任何环境已经具备原生 Hook 完整支持（即使环境已支持，仍需现场实测验证），不启用自动写入，不替代 Code、Human Gate、事实源边界或主控 AI 判断。

> 注：Trae IDE 已于 2026 年 6 月支持原生 Hook 机制（`.trae/hooks.json`），提供 SessionStart、PreToolUse、PostToolUse、Stop 等事件。该机制已通过第三方项目实测验证。详情见 `docs/sources/trae/11-Trae-Hook机制.md`。但具体环境是否安装、启用或支持仍须现场确认。

## 触发阶段

以下阶段应考虑触发生命周期检查：

1. 开始修改 specs、rules、skills、agents、hooks、code、web 或 tests 前；
2. 完成文件修改后；
3. 运行验证前后；
4. 准备提交 Git 前；
5. 准备声明某环境能力完整支持前；
6. 准备关闭能力缺口、降级项或 Human Gate 项前。

## 承载方式

| 承载方式 | 含义 | 限制 |
|---|---|---|---|
| 原生 Hook | 环境提供生命周期触发能力（如 Trae `.trae/hooks.json`） | 必须有可查询配置、现场实测证据和配置来源说明，不能只凭描述或第三方报告声明支持 |
| Skill 模拟 | 由 Skill 在流程中提醒或执行检查 | 只能称为模拟或指令适配，不能声明原生 Hook 完整支持；当环境支持原生 Hook 时，应优先使用原生 Hook 而非 Skill 模拟 |
| Command 触发 | 由命令手动运行检查 | Command 不是第五类部署入口，不能替代 Hook 边界 |
| CI 触发 | 由 CI 或自动化检查执行部分验证 | CI 输出不是最终事实源，失败或权限变化仍需主控处理 |
| 人工检查清单 | 由主控 AI 或 Human 按清单逐项检查 | 属于人工降级，应记录残留风险和未自动化原因 |

## 检查清单

触发时至少检查：

1. 当前任务目标和目标项目是否清楚；
2. 是否涉及正式规范、入口资产、Code、Web、测试或工作对象事实源；
3. 是否改变 Rules、Skill、Agent、Hook、Code、Web、Command 或 Human Gate 边界；
4. 是否将 Command、Code、Web、CLI、MCP、CI 或文档误写成第五类部署入口；
5. 是否将 Skill 模拟 Hook 写成原生 Hook 完整支持；
6. 是否将 Hook 触发写成检查通过；
7. 是否需要运行 `python3 code/specs_validate.py all`；
8. 是否需要运行相关测试；
9. 是否需要执行 `git diff --check`；
10. 是否存在 Human Gate、STOP 点、降级证据或未决问题。

## STOP 点

以下情况必须暂停：

1. 目标项目、事实源或写入范围不清楚；
2. 需要 Human Gate 但尚未确认；
3. 验证失败且无法立即修复；
4. 要新增自动触发、危险权限或跨工作区写入；
5. 要声明环境能力完整支持但缺少可查询证据；
6. 要删除、重命名、移动或关闭关键入口资产。

## 输出

Hook 检查输出应包含：

1. 触发阶段；
2. 承载方式；
3. 检查结果；
4. 已运行验证；
5. Human Gate 或 STOP 点；
6. 降级方式和残留风险；
7. 后续交还对象。

## 交还规则

Hook 触发不等于检查通过。Hook 输出必须交还主控 AI 或 Human，并受 Code 验证、事实源边界、Human Gate 和降级记录约束。