# 事实模型编号重排 Spec

## Why

当前 LDVH 事实模型编号中，Task（31）和 Evidence（28）与它们在对象分类中的核心程度不匹配：Task 是最小执行实体，应排在前面；Evidence 是支撑记录，应排在 TaskSet 之后；Risk 当前为 deferred-field，不占用核心编号。用户要求按对象重要性重排编号，使编号顺序更直观地反映对象层级。

## What Changes

- **BREAKING**: 将 Task 从 31 重编号为 27
- **BREAKING**: 将 TaskSet 从 27 重编号为 28
- **BREAKING**: 将 Evidence 从 28 重编号为 29
- **BREAKING**: 将 Risk 从 29 重编号为 31
- 重命名所有受影响的 specs 文件（主规范 + 6 个子文档 × 2 个对象 = 14 个文件）
- 更新所有文件内部对旧编号的引用
- 更新索引文档、evals 文档、Skill 文档、ldvh-base README 中的交叉引用

## Impact

- Affected specs:
  - `specs/27-Task-任务.md`（原 31）
  - `specs/28-TaskSet-任务集.md`（原 27，待创建）
  - `specs/29-Evidence-验证证据.md`（原 28）
  - `specs/31-Risk-风险.md`（原 29，待定）
  - 所有 27.01-27.06、28.01-28.06、29.01-29.06 子文档
- Affected code:
  - `specs/20-事实模型集合索引.md`
  - `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
  - `specs/evals/14-Gstack照搬进入Trae环境可行性评估.md`
  - `specs/evals/15-LDVH对Trae-Plan与Spec功能的利用评估.md`
  - `specs/evals/16-specs-v2内容价值评估.md`
  - `ldvh-base/evidence/README.md`
  - `ldvh-base/tasks/README.md`
  - `.trae/skills/ldvh-close/SKILL.md`
  - `.trae/skills/ldvh-intake/SKILL.md`

## ADDED Requirements

### Requirement: 事实模型编号重排

系统 SHALL 将以下事实模型编号进行重排：

| 旧编号 | 旧对象 | 新编号 | 新对象 |
|---|---|---|---|
| 31 | Task / 任务 | 27 | Task / 任务 |
| 27 | TaskSet / 任务集 | 28 | TaskSet / 任务集 |
| 28 | Evidence / 证据 | 29 | Evidence / 证据 |
| 29 | Risk / 风险 | 31 | Risk / 风险 |

#### Scenario: 文件重命名完成

- **WHEN** 重排执行完成
- **THEN** 以下文件已被重命名：
  - `31-Task-任务.md` → `27-Task-任务.md`
  - `31.01-Rules.md` → `27.01-Rules.md`
  - `31.02-Skill.md` → `27.02-Skill.md`
  - `31.03-Agent.md` → `27.03-Agent.md`
  - `31.04-Tools.md` → `27.04-Tools.md`
  - `31.05-Web.md` → `27.05-Web.md`
  - `31.06-Contract.md` → `27.06-Contract.md`
  - `28-Evidence-验证证据.md` → `29-Evidence-验证证据.md`
  - `28.01-Rules.md` → `29.01-Rules.md`
  - `28.02-Skill.md` → `29.02-Skill.md`
  - `28.03-Agent.md` → `29.03-Agent.md`
  - `28.04-Tools.md` → `29.04-Tools.md`
  - `28.05-Web.md` → `29.05-Web.md`
  - `28.06-Contract.md` → `29.06-Contract.md`

#### Scenario: 文件内部引用更新完成

- **WHEN** 重排执行完成
- **THEN** 所有被重命名文件内部的旧编号引用已更新为新编号

#### Scenario: 交叉引用更新完成

- **WHEN** 重排执行完成
- **THEN** 以下文件中对旧编号的引用已全部更新：
  - `specs/20-事实模型集合索引.md`
  - `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
  - `specs/evals/14-Gstack照搬进入Trae环境可行性评估.md`
  - `specs/evals/15-LDVH对Trae-Plan与Spec功能的利用评估.md`
  - `specs/evals/16-specs-v2内容价值评估.md`
  - `ldvh-base/evidence/README.md`
  - `ldvh-base/tasks/README.md`
  - `.trae/skills/ldvh-close/SKILL.md`
  - `.trae/skills/ldvh-intake/SKILL.md`

#### Scenario: 文档检查通过

- **WHEN** 重排执行完成
- **THEN** `python3 tools/check_03_specs_doc_standard.py` 不因本次变更引入新的编号错误
- **AND** `python3 tools/check_03_01_specs_docs.py` 不因本次变更引入新的引用错误
