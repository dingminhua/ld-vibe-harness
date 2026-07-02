# 33A 行动模板 30 正式承载

文件状态：migration evidence。本文记录 V3 将 LDVH 安装、初始化与管辖项目配置行动模板从 `06` 父规范正文示范迁出，正式落到 `specs/30-LDVH安装初始化管辖项目配置行动模板.md`；它不安装插件，不修改用户环境配置，不声明任何新的环境入口已 integrated。

## 背景

Human 指出：`LDVH 安装、初始化与管辖项目配置行动模板` 应该是 `30`，而不是长期留在 `06`。该判断成立：

1. `06` 是行动模板基础规范，应该定义 Context、Scenario、Gate、执行、验证、回写和交还结构；
2. 具体可执行模板应进入 30+ 成员文件；
3. 安装初始化配置是 V3 第一个独立正式行动模板，应编号为 `30`；
4. `06` 保留父层准入、候选筛选和结构边界，不承载具体模板全文。

## 本阶段处理

本阶段新增：

1. `specs/30-LDVH安装初始化管辖项目配置行动模板.md`；
2. `reviews/formal/30-formal-review.yaml`；
3. `code/ldvh_specs.py` 中 `30` 的短引用、模板解析和可消费检查；
4. `06` 中对 `30` 的父层准入说明；
5. 迁移记录、实现域文档和 README 索引的路径同步。

## 30 承载内容

`30` 承载：

1. V2 `33-ldvh-install-action` 的安装、初始化、首次管辖项目配置和验收交还闭环；
2. V2 `32-environment-entry-adaptation` 中可作为后续增强输入的插件 / 部署检查边界；
3. 用户告知清单；
4. Context、Scenario、Gate、执行、验证、回写和交还结构表；
5. Human Gate、Stop Conditions 和待补齐事项。

## 06 保留内容

`06` 保留：

1. 行动模板父层价值、权威依据、结构和准入；
2. 候选模板如何迁入 30+；
3. Git 提交行动和 WorkCase 最小手动行动的正文示范或手动等价结构；
4. 30 的父层准入说明；
5. 跨模板候选筛选和 31+ 成员准入判断。

`30` 的待补齐事项只登记 LDVH 安装、初始化与管辖项目配置模板自身的缺口。Git 提交、WorkCase 推进或其它 V2 30-36 候选是否进入 31+，统一回到 `06` 判断。

## 边界

本阶段不做：

1. 不安装、升级、禁用或卸载任何环境插件；
2. 不修改 `~/.codex`、IDE 配置、环境 Hook 系统文件或用户级配置目录；
3. 不创建或修改 `LDVH-GOVERNED-PROJECTS.yaml`；
4. 不声明 Codex、session start、pre tool use、completion claim 或其它环境 Hook 已 integrated；
5. 不恢复 `rules/` 或 `skills/` 顶层目录机制；
6. 不处理测试实现域中已有未提交改动。

## 验证

本阶段使用 targeted validation：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 -m pytest tests/code/test_formal_specs.py -q
git diff --check
```

这些验证只证明 30 正式文件、formal review hash gate 和 Code 可消费检查成立，不证明任何真实安装已经发生。
