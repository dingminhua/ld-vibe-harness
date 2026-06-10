# LDVH Landing Check 派生报告 Spec

## Why

42 LDVH落地与检查要求消费管辖项目配置、41 landing-report、运行投影漂移、Human Gate 证据、事实源和规范校验结果，但当前这些能力分散在多个命令中。AI 可以人工串联，但 42 缺少一个可复现的 Code 派生报告入口来表达“当前范围满足什么、仍有哪些 open/degraded/blocked 缺口、报告不是事实源”。

本阶段在不扩大过多范围、不写用户级目录、不处理旧 `.trae` 删除、不修改 `LDVH-GOVERNED-PROJECTS.yaml` 的前提下，补齐最小 `ldvh-landing-check` 报告。该报告只读取项目内 Git 文件和显式工作区根，消费已有 governed-projects、landing-report、runtime-projection、human-gate、fact/spec 校验结果，并保持输出为派生诊断。

## What Changes

- 在 `tools/specs_validate.py` 中新增 `ldvh-landing-check` 报告构建与 CLI 输出。
- 报告消费 `governed-projects`、`landing-report`、`runtime-projection`、`human-gate-report`、spec 文档结构/引用/落地要求校验和工作对象 YAML 事实校验的最小结果。
- 报告输出 metadata、summary、checks 和 remaining_gaps，状态为 `open`、`degraded` 或 `closed`。
- 报告默认只读取项目内 docs/specs、ldvh-base、运行投影和显式 `--workspace-root` 下的 `LDVH-GOVERNED-PROJECTS.yaml`。
- 更新测试覆盖成功、管辖配置缺失、事实校验失败和 CLI JSON 输出。
- 更新 `task-0061`，记录本阶段验证结果和仍不能关闭 41/42 的剩余缺口。

## Impact

- Affected code: `tools/specs_validate.py`
- Affected tests: `tests/test_specs_validate.py`
- Affected task: `ldvh-base/tasks/task-0061-landing-orchestration-closure-loop.yaml`
- New spec artifacts: `.trae/specs/add-ldvh-landing-check-report/`

## ADDED Requirements

### Requirement: LDVH landing check report
The system SHALL provide a Code-level `ldvh-landing-check` report that aggregates existing LDVH landing diagnostics for the current project scope.

#### Scenario: Existing checks are consumable
- **WHEN** `ldvh-landing-check` runs in a project with readable governed-projects config, specs, facts, runtime projection, and Human Gate sources
- **THEN** it includes each consumed check with status, evidence, issue count, and source area

#### Scenario: Governed projects config is invalid or missing
- **WHEN** the governed-projects check reports issues
- **THEN** `ldvh-landing-check` marks the governed-projects check as open and includes a remaining gap for the configuration boundary

#### Scenario: Fact or spec validation reports issues
- **WHEN** fact/spec validation reports issues
- **THEN** `ldvh-landing-check` includes corresponding open remaining gaps and does not report the whole landing check as closed

### Requirement: LDVH landing check consumes derived subreports
The system SHALL consume landing-report, runtime-projection, and human-gate-report summaries instead of duplicating their detection logic.

#### Scenario: Runtime projection or Human Gate evidence remains degraded
- **WHEN** the consumed runtime projection or Human Gate report status is degraded
- **THEN** `ldvh-landing-check` preserves degraded status and lists the residual risk as a remaining gap

### Requirement: LDVH landing check scope safety
The system SHALL avoid user-level directory reads/writes and avoid modifying governed-projects config.

#### Scenario: Default report execution
- **WHEN** `ldvh-landing-check` runs without explicit paths
- **THEN** it only reads project-local facts/specs/runtime projections and the explicit workspace root governed-projects config, and it writes no files

## MODIFIED Requirements

### Requirement: 42 Code consumption boundary
42 SHALL be able to consume a single derived Code report for governed-projects, landing-report, runtime-projection, Human Gate, facts, and specs, while preserving that the report is not a source of truth and does not prove all Human Gates, runtime projections, Web/Human-facing views, or field execution paths are fully covered.

### Requirement: task-0061 closure boundary
Task 0061 SHALL record that `ldvh-landing-check` has minimum Code support after implementation, but SHALL NOT close 41/42 until real 42 field consumption, broader runtime projection coverage, Web/Human-facing consumption, and lifecycle trigger evidence are proven.

## REMOVED Requirements

None.
