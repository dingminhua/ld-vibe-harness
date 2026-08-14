# Changelog

本文件记录 LDVH 的对外发布版本变更。版本号遵循语义化版本（SemVer）。

## [v4.1.0] - 2026-08-14

> 完善阶段增量发布：完成署名体系落地、Spark 生命周期收敛、WorkCase 主动终止善后链、对象定位符体系统一、Skill/Hook 对齐检查基础设施，以及多项 Web 呈现优化与修复。
>
> **契约变化提示**：六位短引用（short ref）解析/搜索入口已退役。旧六位短引用不再被解析或搜索，仅历史事实正文保留；对象访问/复制统一使用 `项目ID@完整object_id` 定位符。依赖旧短引用调用需迁移。

### ⚠️ 需要更新 Skill

`skill/SKILL.md` 在 v4.0.1 后有 11 次变更，当前已接入环境若自 v4.0.1 以来未更新 Skill 部署副本，需告知 AI 重新部署。已对齐的环境无需额外操作。

### Added

- **署名体系**：建立三字段事实署名逐动作采集契约（agent_workbench / host_name / model_id），统一署名边界与归一化，退役自动注入，补齐历史署名修复流水线（涉及 190+ 次提交，覆盖 100+ 历史事实对象）。
- **Spark 生命周期收敛**：收紧状态迁移校验，拆分 `implemented` 为已落实/未闭环，限制当前关系写入，拒绝历史 Spark 变更，迭代状态筛选/终态统计/颜色/列表呈现。
- **WorkCase 终止善后链**：实现 WorkCase 主动终止事务、handoff 与停止处置承接、Web 终止善后前端呈现与 API 支持。
- **对象定位符体系**：引入并收敛 UUID 文件名编码，退役六位短引用，统一完整对象定位符格式与复制引用，新增事实对象 UID 身份校验。
- **Skill/Hook 对齐检查**：交付 `git-hooks-status` 公开操作与 `environment-sync` 环境同步 launcher，使 Skill 部署与 Git Hook 对齐检查成为一等公民。
- **DSH 会话可比性审计**：交付 `session_comparability` 模块，支持会话执行的可比性审计与证据回放。
- **WorkCase 受控恢复**：实现固定 WorkCase 历史受控恢复核心模式与注册入口。
- **Web 呈现**：对象列表恢复双时间排序，优化认知中心动态元数据展示，统一热点对象身份与 WorkCase 关系投影，搜索框悬浮展开，优化卡片标签与优先级视觉层级。
- **规则引导**：规则引导路由从双路径收敛为单一精确读取路径，提升 canonical Skill 修改保护级别。

### Changed

- 提交契约 footer 补齐 `Platform-Affected` / `Platform-Verified` 闭集，解除产品名与运行时名的机械混淆。
- 增强 `commit-msg` Git Gate：环境变量注入 footer 署名，覆盖 AI 自报值。
- 测试耗时优化：复用只读事实 Schema 与规则源快照，缩短测试运行时间。
- CI 配置完善：补 launcher venv 与 git 默认分支可移植性，修正 Web job 依赖路径。
- 关闭 34 号模板开始控制点，收敛 WorkCase 执行模板续跑纪律。

### Fixed

- 修复 WorkCase 关闭/终止场景的 NameError 与路由问题。
- 修复署名缺失时的非阻断分流与 unobserved_context 归一化。
- 修复 Web 搜索控件右对齐、关联行进入箭头、已废弃关联行视觉层级。
- 修复测试运行器子进程 PYTHONPATH 注入与 durability 移除后 17 处残留引用。
- 修复多个历史事实对象的 legacy 署名格式（涉及 10+ 个 WorkCase/Spark）。
- 修复 lint 与 Ruff 检查错误。

### Known

- 本版本仍为完善阶段，部分能力持续收敛中，后续版本将逐步提供稳定保证。

## [v4.0.1] - 2026-08-08

> 完善阶段增量发布：补强发布治理、工程验证与度量基础设施，无破坏性变更。

### Added
- 新增 GitHub Actions CI 工作流：push/PR 自动运行 Python 测试与 lint、Web 类型检查/测试/构建。
- 新增 `release` 提交类型与发布纪律契约（03 §9.10）：版本号、tag、CHANGELOG、发布授权边界与部署件变更标注。
- 扩展可审计的试验测量基础设施与事实变更度量。

### Changed
- 提交契约 footer 闭集补齐 `Platform-Affected` / `Platform-Verified`（与既有验证规则对齐）。
- 版本声明统一为 `v4.0.0`（对齐既有 tag），修复 `web/package-lock.json` 版本漂移。

### Fixed
- 修复既有测试 lint 问题（8 处：未用 import、`zip` 缺 `strict=`、超长行）。

### Known
- 本版本为完善阶段，部分能力未完全收敛，后续版本将逐步收敛并提供稳定保证。

## [v4.0.0] - 2026-08-07

> 首个公开发布。当前处于完善阶段：能力结构已建立，部分功能仍在收敛中，后续版本将逐步收敛并提供稳定保证。

### Added
- 初始发布，将 dev-v4 开发分支作为可下载的对外版本公开到 `main`。
- 已建立 LDVH 事实对象体系（spark / workcase / study），并声明 Windows 为已验证平台（study-0025）。
- 提供 `ldvh` launcher（Helper CLI / doctor / work-context）与 4 个 integration jobs。

### Changed
- 版本号自 `web/package.json` 的占位 `0.0.0` 校正为 `4.0.0`，并同步 `web/package-lock.json`。

### Known
- 本版本为完善阶段，部分能力未完全收敛，后续版本将逐步收敛并提供稳定保证。