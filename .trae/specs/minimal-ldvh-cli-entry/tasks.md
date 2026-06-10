# Tasks

- [x] Task 1: Define minimal LDVH CLI contract
  - [x] SubTask 1.1: Cover help, status, command tree, and exit code behavior
  - [x] SubTask 1.2: Document write guard sources for plan and Human Gate boundaries

- [x] Task 2: Implement unified CLI wrapper
  - [x] SubTask 2.1: Add status, landing, facts, and specs command groups
  - [x] SubTask 2.2: Delegate to existing fact_cli, fact_validate, and specs_validate capabilities
  - [x] SubTask 2.3: Keep landing apply and repair bound to required landing-plan inputs

- [x] Task 3: Update tests and task facts
  - [x] SubTask 3.1: Add tests for help, status, plan delegation, and failure paths
  - [x] SubTask 3.2: Update task-0072 acceptance, deliverables, and verification evidence

- [x] Task 4: Validate and commit related files only
  - [x] SubTask 4.1: Run focused tests and full pytest
  - [x] SubTask 4.2: Run CLI smoke checks and fact/spec validation
  - [x] SubTask 4.3: Commit only task-0072 related files

# Task Dependencies

- Task 2 depends on Task 1.
- Task 3 depends on Task 2.
- Task 4 depends on Tasks 2 and 3.
