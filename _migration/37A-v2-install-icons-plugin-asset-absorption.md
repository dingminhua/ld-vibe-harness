# 37A V2 安装图标资产与插件包展示资产吸收

文件状态：implementation-domain absorption record。本文记录 V3 对 V2 安装实现中图标资产的仓库内吸收；本文不安装插件，不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或外部项目 Hook，不声明任何环境入口 integrated。

## 背景

Human 指出 V2 已经实现了安装相关能力，并且存在 `icons/` 目录。复核 V2 后确认：

1. V2 `icons/` 提供 `ldvh-plugin-icon` 多尺寸 PNG 资产；
2. V2 Web `public/` 和 `dist/` 已消费这些图标；
3. V2 安装行动 `specs/33-ldvh-install-action-LDVH安装行动编排.md` 已定义插件方式、Rules 方式、Git Hook 安装和验证；
4. V2 仓库内未发现 `.codex-plugin/plugin.json` 形态的 Codex 插件包，具体插件发布和安装机制在 V2 仍属于待对接。

V3 已有 repo-local Codex 样例包，但缺少包内展示资产；Web 图标存在不等于插件包图标存在。

## 本阶段处理

本阶段新增或更新：

| 路径 | 处理 |
|---|---|
| `icons/` | 吸收 V2 `icons/ldvh-plugin-icon*.png` 作为 V3 共享图标资产目录 |
| `code/environment_plugins/codex-ldvh-v3/assets/` | 放置 Codex 样例包 manifest 实际引用的 `composerIcon` 和 `logo` 图标 |
| `code/environment_plugins/codex-ldvh-v3/.codex-plugin/plugin.json` | 通过 `interface.composerIcon` 和 `interface.logo` 消费包内资产 |
| `code/environment_plugins/README.md` | 补充环境插件样例包展示资产边界 |
| `code/environment_plugins/codex-ldvh-v3/README.md` | 补充 Codex 样例包资产说明和验证口径 |
| `code/docs/02-Environment-Plugin-Practice.md` | 将展示资产纳入最小插件包契约 |
| `tests/code/test_environment_plugins.py` | 增加 manifest 图标路径和 PNG 尺寸验证 |

## 边界

本阶段不做：

1. 不安装、升级、禁用或卸载真实 Codex 插件；
2. 不创建或修改 marketplace entry；
3. 不写 `~/.codex/config.toml`、`~/.codex/hooks.json` 或插件 cache；
4. 不修改 IDE、Agent runner、CI 或其它环境配置；
5. 不声明 Codex lifecycle、PreToolUse 或 Stop 已 integrated；
6. 不恢复 V2 `rules/` 或 `skills/` 顶层机制。

## 验证

应运行：

```bash
python3 /Users/dmh2002/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py code/environment_plugins/codex-ldvh-v3
python3 -m pytest tests/code/test_environment_plugins.py -q --tb=short
```

这些验证只证明 repo-local 插件包 manifest、展示资产和 shim 行为在仓库内可检查，不证明真实环境已安装、trusted 或自动触发。
