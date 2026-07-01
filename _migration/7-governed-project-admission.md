# 阶段 7 受管项目接入完成记录

> 文件状态：temporary migration decision。本文记录阶段 7 对 V2 受管项目机制的迁移范围、静态接管能力和后置项；它不授权 Hook 安装、commit gate、Web 写入、真实实例迁移或 Human Gate 决策。正式规则仍以 `specs/` 正文为准。

## 1. 迁移结论

阶段 7 已完成 V3 静态受管项目接管能力。V3 现在可以读取 `LDVH-GOVERNED-PROJECTS.yaml`，校验配置字段，解析 target/cwd/Git common-dir 归属，并识别同项目、多项目、受管/非受管混合和 no-op 场景。

本阶段不是重新发明 V2 机制，而是迁移 V2 已实现的受管项目登记、target-first governance、worktree Git common-dir 和多目标边界。V2 知识地图、Hook 安装、Rules 顶层语义和 runtime receipt 持久化不迁入阶段 7。

## 2. 正式迁入

| 对象 | 处理 |
|---|---|
| V2 `LDVH-GOVERNED-PROJECTS.yaml` | 迁入 V3 根目录配置，当前登记 `ldvh-v3` 自身 |
| V2 `code/spec_checks/governed_projects.py` | 迁入为 V3 `ldvh_specs.py` 中的配置 parser、validator 和 resolver |
| V2 WorkCase 0014/0015 | 吸收 target-first、Git common-dir、worktree、多 target、no-op 和 unknown target 规则 |
| V2 知识地图 governed_projects 输入范围 | 不恢复知识地图；只保留项目登记和事实源入口边界 |
| V2 Hook/Rules dispatcher 运行时能力 | 后置到 Hook / commit gate / 环境入口接入，阶段 7 只实现静态解析和测试 |

## 3. V3 产物

| 产物 | 内容 |
|---|---|
| `specs/10-管辖项目配置规范.md` | 管辖项目配置、工作对象判定、多目标边界、事实源入口和环境引用边界 |
| `specs/attachments/10.Att.01-管辖项目配置字段表.md` | 配置根字段、项目字段、Git 字段和 target resolution 字段 |
| `LDVH-GOVERNED-PROJECTS.yaml` | V3 当前工作树自登记 |
| `code/ldvh_specs.py` | 受管项目配置解析、字段校验、target-first resolver、preflight 辅助输出 |
| `tests/code/test_ldvh_specs_validate.py` | 配置契约、缺失/重复/越界负例、target-first、no-op、多 target、worktree 和 CLI 测试 |

## 4. 后置项

1. 不安装 Hook，不声明真实环境拦截已生效；
2. 不迁移真实 `ldvh-base/` 实例；
3. 不建立 Web 写入或 Web 依赖 Code 输出的数据路径；
4. 不恢复 V2 知识地图；
5. 不迁入 formal action template instances；
6. 后续 Hook / commit gate 接入时必须复用 V3 resolver，不得恢复 cwd-only 或并行判定逻辑。

## 5. 验证声明

| 验证目标 | 验证方式 | 验证入口 | 输入范围 | 关键输出 | 结论 | 残留风险 | 证据回指 |
|---|---|---|---|---|---|---|---|
| 阶段 7 管辖项目静态解析能力 | 自动化测试与 specs validator | `python3 -m pytest tests/code _migration/tests -q`；`python3 code/specs_validate.py all --format text --fail-on-diagnostics` | V3 specs、附件、根配置、Code parser/resolver、迁移测试 | 配置契约、target-first、worktree、多 target 和正式 specs review gate 均通过 | 通过 | Hook、commit gate、Web 写入和真实实例迁移仍后置 | 本文、`specs/10-管辖项目配置规范.md`、`tests/code/test_ldvh_specs_validate.py` |
