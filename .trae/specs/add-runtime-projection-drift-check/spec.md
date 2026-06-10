# 增加运行投影漂移检查 Spec

## Why

现有 landing-report 能把“运行投影漂移检查”识别为能力缺口，但只能通过正式规范关键词判断该能力是否被声明，不能读取项目中的实际运行投影，也不能把入口、Skill、Hook、CI、Web 或 Code 投影与正式规范引用关系做最小比对。这会导致 42 LDVH落地与检查只能看到抽象缺口，无法获得可复现的漂移诊断输入。

本阶段需要在不写用户级目录、不处理旧 `.trae` 删除、不修改 `LDVH-GOVERNED-PROJECTS.yaml` 的前提下，补齐最小 Code 检查能力，并接入 landing-report，让 41/42 能消费“运行投影检查已可执行但仍为派生启发式”的结果。

## What Changes

- 在 `tools/specs_validate.py` 中增加 runtime-projection 检查能力，用于扫描项目内授权范围的运行投影文件。
- 检查运行投影是否存在权威来源引用、是否复制正式规范正文、是否指向缺失的正式规范路径，并输出 open / degraded / closed 风格的派生诊断。
- 将 runtime-projection 检查汇总接入 `landing-report` 的 metadata、summary 和 capability gaps，使 42 可从报告中消费检查结果。
- 更新正反样例测试，覆盖运行投影缺少权威来源、引用缺失规范、复制正文和接入 landing-report 的情况。
- 更新 `task-0061`，记录本阶段验证结果和仍不能关闭 41 的剩余缺口。

## Impact

- Affected code: `tools/specs_validate.py`
- Affected tests: `tests/test_specs_validate.py`
- Affected task: `ldvh-base/tasks/task-0061-landing-orchestration-closure-loop.yaml`
- New spec artifacts: `.trae/specs/add-runtime-projection-drift-check/`

## ADDED Requirements

### Requirement: Runtime projection drift check command
The system SHALL provide a Code-level runtime projection drift check for project-local runtime projections.

#### Scenario: Runtime projection misses authority reference
- **WHEN** a project-local runtime projection file is checked
- **AND** it does not reference docs/specs authority or an explicit degradation source
- **THEN** the check reports an open issue instead of treating the projection as closed

#### Scenario: Runtime projection points to missing formal spec
- **WHEN** a runtime projection references a docs/specs path that does not exist
- **THEN** the check reports an open issue with the missing path

#### Scenario: Runtime projection copies formal spec body
- **WHEN** a runtime projection appears to copy substantial formal spec body text instead of thin routing or summary
- **THEN** the check reports a degraded issue because projection text may drift from the source of truth

### Requirement: landing-report consumes runtime projection drift check
The system SHALL include runtime projection drift check summary in landing-report output.

#### Scenario: Runtime projection drift check is executable
- **WHEN** landing-report is generated
- **THEN** it includes runtime projection check metadata, status counts, and capability evidence

#### Scenario: Runtime projection drift remains heuristic
- **WHEN** runtime projection drift check has no issue for currently scanned files
- **THEN** landing-report still marks the capability as degraded unless formal specs and runtime projections can be proven fully covered

### Requirement: Runtime projection scope safety
The system SHALL limit the default runtime projection check to project-local authorized paths.

#### Scenario: User-level platform entry exists outside the project
- **WHEN** runtime projection drift check runs with default settings
- **THEN** it does not read or write user-level directories and only reports project-local or explicitly provided paths

## MODIFIED Requirements

### Requirement: 41/42 Code evidence
41/42 SHALL be able to consume runtime projection drift check output as Code evidence, while preserving the boundary that the output is derived diagnostics rather than source of truth.

### Requirement: task-0061 closure boundary
Task 0061 SHALL record that runtime projection drift check has minimum Code support after implementation, but SHALL NOT close 41 until real 42 field consumption, Human Gate evidence consumption, and broader projection coverage are proven.

## REMOVED Requirements

None.
