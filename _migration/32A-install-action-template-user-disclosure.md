# 32A 安装初始化行动模板用户告知清单补强

文件状态：migration evidence。本文记录 V3 对 LDVH 安装、初始化与管辖项目配置行动模板的用户告知清单补强；33A 后该具体模板由 `specs/30-LDVH安装初始化管辖项目配置行动模板.md` 承载，`specs/06-行动模板基础规范.md` 只保留父层准入和结构边界。本文不安装插件，不修改用户环境配置，不声明任何新的环境入口已 integrated。

## 背景

Human 指出：安装部署时有大量必须告知用户的信息，这些信息应写入行动模板，而不是只散落在实现域文档或样例包 README 中。

本次复核确认：

1. `06` 当时已有 `LDVH 安装、初始化与管辖项目配置行动模板` 正文示范；
2. 该模板已有 Gate、执行、验证、回写和交还结构；
3. 但缺少显式的“用户告知清单”要求，容易导致真实安装前只说明“要装插件”，没有完整告知写入位置、影响范围、阻断边界、验证和回滚。

## 本阶段处理

本阶段先在 `06` 的 LDVH 安装初始化配置模板中补入，33A 后迁入 `30`：

1. 安装、部署、初始化、配置或卸载前必须形成用户告知清单；
2. 告知清单必须交给 Human 确认；
3. 清单至少覆盖写入对象、写入位置级别、受影响项目、Hook / lifecycle event、阻断与 diagnostic 边界、旧插件 / stale V2 path 处理、验证方式、回滚或卸载入口、未 integrated 能力、残留风险和下一步 Human Gate；
4. 缺少告知清单时，不得安装、部署、初始化、写入配置、声明接入或要求 Human 验收；
5. `code/ldvh_specs.py` 同步把用户告知清单纳入 `30` 可消费检查。

## 边界

本阶段不做：

1. 不安装、升级、禁用或卸载任何环境插件；
2. 不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录；
3. 不创建或修改 `LDVH-GOVERNED-PROJECTS.yaml`；
4. 不声明 Codex、session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制。

## 验证

本阶段使用 targeted validation：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
git diff --check
```

这些验证只证明模板可消费和静态边界成立，不证明任何真实安装已经发生。
