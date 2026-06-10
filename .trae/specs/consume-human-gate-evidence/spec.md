# Human Gate 证据消费检查 Spec

## Why

41/42 已经把 Human Gate 证据消费识别为关键能力缺口，且已有 Human Gate 最小证据结构检查命令，但 landing-report 仍只通过正式规范关键词把该能力标记为 degraded，不能消费实际 Human Gate 记录检查结果。这会导致 42 只能知道“需要 Human Gate 证据”，却不能获得可复现的证据结构诊断输入，也不能区分当前证据不存在、证据结构有误、或结构检查通过但仍不能证明闭环的情况。

本阶段需要在不写用户级目录、不处理旧 `.trae` 删除、不修改 `LDVH-GOVERNED-PROJECTS.yaml` 的前提下，将 Human Gate 证据结构检查转化为可被 landing-report 消费的派生报告，并继续保持该输出不是最终事实源。

## What Changes

- 在 `tools/specs_validate.py` 中增加 Human Gate 证据检查报告构建能力，复用现有 Human Gate 最小证据结构检查。
- 将 Human Gate 证据检查摘要接入 `landing-report` 的 metadata、summary、capability_gaps 和明细输出。
- 当检查未发现项目内 Human Gate 记录或检查通过时，landing-report 仍保持该能力为 degraded，因为结构检查不能证明所有高影响写入、长期降级、关键缺口关闭或通过声明均已有 Human Gate。
- 当 Human Gate 证据结构检查发现问题时，landing-report 将 Human Gate 证据消费能力标记为 open。
- 更新测试覆盖 Human Gate 证据报告、landing-report 接入与文本输出。
- 更新 `task-0061`，记录本阶段验证结果和仍不能关闭 41 的剩余缺口。

## Impact

- Affected code: `tools/specs_validate.py`
- Affected tests: `tests/test_specs_validate.py`
- Affected task: `ldvh-base/tasks/task-0061-landing-orchestration-closure-loop.yaml`
- New spec artifacts: `.trae/specs/consume-human-gate-evidence/`

## ADDED Requirements

### Requirement: Human Gate evidence report
The system SHALL provide a Code-level Human Gate evidence report that summarizes project-local Human Gate evidence structure checks.

#### Scenario: No Human Gate evidence records are found
- **WHEN** the Human Gate evidence report checks project-local Markdown sources
- **AND** no Human Gate record is found
- **THEN** it reports a degraded status rather than treating Human Gate evidence consumption as closed

#### Scenario: Human Gate evidence record is incomplete
- **WHEN** a Human Gate record is found
- **AND** required evidence fields are missing or empty
- **THEN** the report includes open issues with source path, line, issue code, and message

#### Scenario: Human Gate evidence record has complete structure
- **WHEN** Human Gate records are found
- **AND** all required evidence fields are present and non-empty
- **THEN** the report marks the structure check as closed while preserving that it is derived evidence and not the final fact source

### Requirement: landing-report consumes Human Gate evidence report
The system SHALL include Human Gate evidence report summary in landing-report output.

#### Scenario: Human Gate evidence has open issues
- **WHEN** landing-report is generated
- **AND** the Human Gate evidence report status is open
- **THEN** the Human Gate evidence consumption capability gap is open and references the evidence report result

#### Scenario: Human Gate evidence structure check passes or has no records
- **WHEN** landing-report is generated
- **AND** the Human Gate evidence report status is closed or degraded
- **THEN** landing-report still marks the capability as degraded unless actual 42 field consumption and all relevant Gate coverage are proven

### Requirement: Human Gate evidence scope safety
The system SHALL limit default Human Gate evidence consumption checks to project-local Git file facts.

#### Scenario: User-level platform entry exists outside the project
- **WHEN** Human Gate evidence report runs with default settings
- **THEN** it does not read or write user-level directories and only checks project-local or explicitly provided Markdown paths

## MODIFIED Requirements

### Requirement: 41/42 Human Gate evidence capability
41/42 SHALL be able to consume Human Gate evidence structure check output as Code evidence, while preserving the boundary that the output is derived diagnostics rather than proof that all required Human Gates were performed.

### Requirement: task-0061 closure boundary
Task 0061 SHALL record that Human Gate evidence consumption has minimum Code support after implementation, but SHALL NOT close 41 until real 42 field consumption, broader Gate coverage, runtime projection coverage, and Web/Human-facing consumption are proven.

## REMOVED Requirements

None.
