# Changelog

本文件记录 LDVH 的对外发布版本变更。版本号遵循语义化版本（SemVer）。

## [v4.0.0-alpha] - 2026-08-07

> 首个公开发布。当前处于完善阶段：能力结构已建立，部分功能仍在收敛中，尚不完全视为稳定。

### Added
- 初始发布，将 dev-v4 开发分支作为可下载的对外版本公开到 `main`。
- 已建立 LDVH 事实对象体系（spark / workcase / study），并声明 Windows 为已验证平台（study-0025）。
- 提供 `ldvh` launcher（Helper CLI / doctor / work-context）与 4 个 integration jobs。

### Changed
- 版本号自 `web/package.json` 的占位 `0.0.0` 校正为 `4.0.0`。

### Known
- 本版本为完善阶段（alpha），部分能力未完全收敛，后续版本将逐步收敛并提供稳定保证。