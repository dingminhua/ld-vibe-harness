# 强化 41 触发保障 Spec

## Why
41 规范落地统筹已经定义了触发场景，但当前触发保障仍主要依赖 AI 识别、统一入口、40 索引、基础 Code 报告和 42 消费检查，尚未形成足够稳定的闭环。后续工作需要围绕“41 何时必须被触发、由什么机制提醒、如何验证触发没有丢失”展开，避免正式规范、运行投影或 Code/Web/Skill/Agent/Hook/CI 变化后未进入 41。

## What Changes
- 明确 41 触发保障的分层机制，包括入口路由、规范 Scenario、40 集合索引、Code 检查、42 消费检查、运行投影、Hook/CI 或人工降级。
- 补齐 41 触发保障的规范表达，使“触发条件”和“保障机制”不只停留在 41 自身声明。
- 扩展 Code 检查能力，使工具能够发现应触发 41 但缺少承接、验证或消费路径的情况。
- 让 42 在 LDVH 落地与检查中稳定检查 41 触发保障是否存在、是否被消费、是否存在未闭环缺口。
- 对用户级/系统级入口、Rules / Instructions、Skill、运行投影漂移和 Human Gate 证据建立抽象检查口径，不维护具体实体清单。

## Impact
- Affected specs: `docs/specs/41-landing-orchestration-规范落地统筹.md`, `docs/specs/42-ldvh-landing-check-LDVH落地与检查.md`, `docs/specs/04.02-环境适配与运行投影规范.md`, `docs/specs/04.04-LDVH落地特别要求规范.md`, `docs/specs/04.07-Trae-Solo适配清单.md`, `docs/specs/04.08-Codex适配清单.md`, `docs/specs/07-Code实现规范.md`, `docs/specs/10-运行闭环测试规范.md`, `LDVH-AI-ENTRY.md`
- Affected code: `tools/specs_validate.py`, related tests or command-line validation paths if present

## ADDED Requirements

### Requirement: 41 触发保障分层
The system SHALL define layered safeguards for triggering 41 landing orchestration when formal specs, landing requirements, runtime projections, Code/Web/Skill/Agent/Hook/CI boundaries, or LDVH landing checks change.

#### Scenario: Formal spec changes require 41 consideration
- **WHEN** a formal spec is added, modified, renamed, deleted, or its landing requirements change
- **THEN** the system identifies that 41 should be considered or explicitly records why the change is out of scope

#### Scenario: Runtime projection changes require 41 consideration
- **WHEN** Rules / Instructions, Skill, Agent, Hook, CI, Web, Code, platform entry, or equivalent runtime projection changes
- **THEN** the system checks whether 41 should aggregate landing requirements and assess projection drift

### Requirement: 42 consumes 41 trigger state
The system SHALL make 42 consume or verify 41 trigger safeguards during LDVH landing checks.

#### Scenario: 41 is active but not closed-loop
- **WHEN** 42 checks LDVH landing status
- **THEN** it does not treat 41 `active` status as closed-loop evidence, and reports missing trigger, consumption, evidence, or drift-check capability as an open or degraded gap

### Requirement: Code detects missing 41 trigger support
The system SHALL provide Code-level checks or reports that identify whether 41 trigger conditions, landing requirement aggregation, and 42 consumption are supported.

#### Scenario: Tooling cannot verify trigger support
- **WHEN** current tools cannot determine whether 41 should have been triggered or whether its output was consumed
- **THEN** the report marks the capability as missing or degraded instead of treating the requirement as closed

### Requirement: Abstract mechanism boundary
The system SHALL check trigger support by abstract capability type rather than maintaining fixed lists of specific Skills, platform entries, Hooks, CI jobs, Web pages, or Code commands.

#### Scenario: A new Skill is added
- **WHEN** a new Skill is added or renamed
- **THEN** 41/42 checks evaluate whether relevant landing requirements need Skill support and whether the support is valid, without requiring 41 or 42 to add that Skill name to a fixed list

## MODIFIED Requirements

### Requirement: 41 lifecycle trigger requirement
41 SHALL state not only the lifecycle trigger conditions, but also the expected safeguard layers that can remind, verify, or escalate those triggers, including AI entry routing, 40 active workflow indexing, Code checks, 42 consumption checks, runtime projection checks, and Human Gate fallback.

### Requirement: 42 landing check input
42 SHALL verify whether 41 trigger safeguards are present and whether 41 aggregation results are available for the current check scope. If unavailable, 42 SHALL report a 41/42 linkage gap rather than substituting its own fixed entity checklist.

### Requirement: LDVH AI entry routing
LDVH-AI-ENTRY SHALL keep 41 visible for formal spec changes, landing requirement changes, runtime projection drift, platform adaptation, Code/Web/Skill/Agent/Hook/CI boundary changes, and LDVH landing checks.

## REMOVED Requirements

### Requirement: Fixed trigger entity checklist
**Reason**: A fixed list would require changing 41 or 42 whenever a Skill, Hook, entry, CI job, Web page, or Code command is added, renamed, or removed.
**Migration**: Use abstract capability checks derived from formal spec landing requirements, platform adaptation specs, runtime projection evidence, and 41 aggregation output.
