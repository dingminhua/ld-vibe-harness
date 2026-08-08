# Changelog

本文件记录 LDVH 的对外发布版本变更。版本号遵循语义化版本（SemVer）。

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